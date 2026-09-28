# -*- coding: utf-8 -*-
"""LES SPAWNERS DEDIES DE 2nd IMPACT, LUS DANS LEUR CODE — format, tables, indexation.

CE QUE CET OUTIL CORRIGE
------------------------
`chargeurs2i.spawner_en_dur` appelait « spawner a bloc en dur » toute fonction qui porte
un litteral dans la plage des blocs et lit avec `mov.w @rM+`. C'est trop peu : le litteral
qu'il retenait n'est pas toujours un bloc.

**Mesure sur `0x8C036480`, le spawner de Hugo.** Il ne porte pas un bloc mais DEUX TABLES,
et il les indexe comme les lecteurs de New Generation :

    z        = u8  [0x8C6AF304 + 6]            le contexte, +6
    nombre   = u16 [0x8C17F54C + arg*8  + z*2]
    pointeur = u32 [0x8C5FA00C + arg*16 + z*4]

`0x8C17F54C` est donc la table des NOMBRES. La chaine la lisait comme un bloc
d'enregistrements, a `0x8C17F54C + 38`.

> **ET `z` EXISTE AUSSI EN 2nd IMPACT.** On le croyait propre a New Generation, ou
> `NEW-GENERATION.md` etablit que c'est un TIRAGE uniforme sur 0..3, refait a chaque
> entree d'etage, par un generateur a table dont la table est **identique octet pour
> octet dans les deux jeux**. Chaque couple (spawner, argument) porte donc QUATRE blocs,
> et on n'en voyait aucun.

COMMENT LE FORMAT EST LU, ET NON SUPPOSE
----------------------------------------
Le corps du spawner ecrit chaque champ a un offset d'objet donne en clair :

    mov   #102,r0          (ou `mov.w <litteral>,r0`, ou `add #-4,r0`)
    mov.w @r14+,r3         le champ suivant du bloc
    mov.w r3,@(r0,r4)      -> objet+102

On suit donc `r0` instruction par instruction et on apparie chaque `mov.w @rM+` avec
l'ecriture qui suit. La taille de l'enregistrement est le nombre de champs x 2 -- elle
n'est jamais devinee.

Les offsets d'objet sont les memes que partout ailleurs :

    +558 plan   +554 drapeaux   +102 x   +106 y   +88 palette   +456 script

    python spawners2i.py            tous les spawners, leur format et leurs blocs
    python spawners2i.py 8C036480   un seul, avec le detail de son indexation
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sh4

D, B = sh4.D, sh4.BASE
FIN_BIN = B + len(D)

u8 = lambda a: D[a - B]
u16 = lambda a: struct.unpack_from("<H", D, a - B)[0]
u32 = lambda a: struct.unpack_from("<I", D, a - B)[0]

CONTEXTE = 0x8C6AF304        # +4 decor, +5 aire, +6 z
lisible = lambda a, n=4: B <= a and a + n <= FIN_BIN
CODE = lambda v: 0x8C010000 <= v < 0x8C120000
DONNEES = lambda v: 0x8C120000 <= v < FIN_BIN

# LES OFFSETS D'OBJET CONNUS. Le rang d'un champ ne veut rien dire d'un lecteur a
# l'autre ; l'offset, si.
NOMS = {558: "plan", 554: "drapeaux", 102: "x", 106: "y", 88: "palette",
        456: "script", 32: "champ0", 68: "?68", 118: "?118", 52: "->blocB",
        62: "->blocA", 44: "table2"}


# --------------------------------------------------------------------------------------
# UN INTERPRETE SYMBOLIQUE MINIMAL
#
# On ne cherche pas a executer le SH-4 : on suit des expressions LINEAIRES de la forme
# `c + a*arg + b*z`, ce qui suffit a lire une indexation de table. Tout ce qui sort de ce
# cadre rend `None`, et le registre devient inconnu -- ce qui vaut mieux qu'une valeur
# fausse.
# --------------------------------------------------------------------------------------
def _c(v):
    return dict(k=v, arg=0, z=0)


def _add(x, y):
    if x is None or y is None:
        return None
    return dict(k=x["k"] + y["k"], arg=x["arg"] + y["arg"], z=x["z"] + y["z"])


def _mul(x, n):
    if x is None:
        return None
    return dict(k=x["k"] * n, arg=x["arg"] * n, z=x["z"] * n)


def _txt(x):
    if x is None:
        return "?"
    t = "0x%08X" % x["k"] if x["k"] > 0xFFFF else str(x["k"])
    for nom, c in (("arg", x["arg"]), ("z", x["z"])):
        if c:
            t += " + %s*%d" % (nom, c) if c != 1 else " + %s" % nom
    return t


def litteral_l(pc):
    """`mov.l @(disp,PC),rN` -> la valeur, ou None."""
    op = u16(pc)
    if (op >> 12) != 0xD:
        return None
    pool = (pc & ~3) + 4 + (op & 0xFF) * 4
    return u32(pool) if lisible(pool) else None


def litteral_w(pc):
    """`mov.w @(disp,PC),rN` -> la valeur sur 16 bits signes, ou None."""
    op = u16(pc)
    if (op >> 12) != 0x9:
        return None
    pool = pc + 4 + (op & 0xFF) * 2
    if not lisible(pool, 2):
        return None
    v = u16(pool)
    return v - 65536 if v > 32767 else v


def pools(deb, fin):
    """Les adresses qui sont des LITTERAUX, pas des instructions.

    LE PIEGE QUI A FAIT DIRE « BLOC EN DUR 24899 » — 02/09/2026
    ------------------------------------------------------------
    Le SH-4 pose ses litteraux **au milieu du code**, dans des trous que le flux
    d'instructions saute. Un balayage lineaire les decode comme des opcodes : une valeur
    quelconque peut ressembler a `mov.w @rM+,rN` (0x6nm5) et faire croire a un bloc, ou a
    `rts` (0x000B) et couper une fonction en deux.

    C'est exactement ce qui est arrive a `0x8C028792` : son pool est en plein milieu, et
    l'analyseur en a tire un « bloc en dur » de 24899 au lieu de ses deux tables.

    On releve donc d'abord les cibles de tous les `mov.l @(disp,PC)` et `mov.w @(disp,PC)`,
    et on les saute. Marquer un mot de trop est sans risque ; en decoder un est faux.
    """
    marques = set()

    for c in range(deb, fin, 2):
        op = u16(c)

        if (op >> 12) == 0xD:                       # mov.l @(disp,PC),rN
            t = (c & ~3) + 4 + (op & 0xFF) * 4
            marques.update((t, t + 2))
        elif (op >> 12) == 0x9:                     # mov.w @(disp,PC),rN
            marques.add(c + 4 + (op & 0xFF) * 2)

    return marques


def fin_de_fonction(deb, plafond=0x400):
    """La fin d'une fonction : le premier `rts` QU'AUCUN BRANCHEMENT N'ENJAMBE.

    DEUX PIEGES OPPOSES, ET LES DEUX ONT COUTE — 02/09/2026
    -------------------------------------------------------
    * une **fenetre fixe** deborde sur la fonction suivante et ramasse ses appels : c'est
      ce qui attribuait un meme site d'appel a deux decors ;
    * le **premier `rts`** n'est pas la fin. Le SH-4 sort tot. `0x8C0323F0`, le spawner
      d'Alex et de Dudley, teste l'allocation et rend `-1` en cas d'echec :

          8C032410  bf   0x8c03241a      -- si l'allocation a reussi, on saute plus loin
          8C032412  lds.l @r15+,pr
          8C032414  mov  #-1,r0
          8C032416  rts                  -- la sortie d'ECHEC
          8C03241A  ... le corps qui lit le bloc

      S'arreter la, c'est declarer que la fonction « ne lit aucun bloc » alors qu'elle
      lit onze champs vingt octets plus loin.

    La regle qui tient les deux bouts : on suit les branchements et on retient la cible
    la plus lointaine. Un `rts` place AVANT elle est enjambe, donc ce n'est pas la fin.
    """
    fin = min(deb + plafond, FIN_BIN - 2)
    saut = pools(deb, fin)
    plus_loin = deb
    c = deb

    while c < fin:
        if c in saut:                               # un litteral, pas une instruction
            c += 2
            continue

        op = u16(c)

        # bra / bsr : disp sur 12 bits signes
        if (op & 0xF000) in (0xA000, 0xB000):
            d = op & 0xFFF
            d = d - 0x1000 if d & 0x800 else d
            plus_loin = max(plus_loin, c + 4 + d * 2)

        # bt / bf / bt.s / bf.s : disp sur 8 bits signes
        elif (op & 0xFF00) in (0x8900, 0x8B00, 0x8D00, 0x8F00):
            d = op & 0xFF
            d = d - 0x100 if d & 0x80 else d
            plus_loin = max(plus_loin, c + 4 + d * 2)

        elif op == 0x000B and c >= plus_loin:       # rts, non enjambe
            return min(c + 4, fin)

        c += 2

    return fin


def analyser(f, plafond=0x300):
    """Lit un spawner : ses tables, son indexation, et sa carte champ -> offset d'objet.

    Rend un dict, ou None si la fonction ne lit pas de bloc (`mov.w @rM+`).
    """
    fin = fin_de_fonction(f, plafond)
    saut = pools(f, fin)     # les litteraux poses au milieu du code -- voir `pools`
    reg = {}                 # registre -> expression lineaire
    r0 = None                # la valeur courante de r0, pour les ecritures indexees
    champs = []              # [(rang, offset objet)] dans l'ordre de lecture
    charges = []             # [(expression, taille)] des `mov.w @rN` / `mov.l @rN`
    litteraux = []
    attente = None           # un `mov.w @rM+,rN` vu, on attend son ecriture
    source = None            # l'expression du pointeur de lecture du bloc
    lecteur = None           # le registre qui parcourt le bloc
    mots = 0                 # combien de mots l'enregistrement occupe
    indirect = False         # le bloc vient-il d'une table, ou est-il en dur ?
    boucle = False           # un branchement en arriere : plusieurs enregistrements
    tours = None             # le compte lu dans la comparaison de fin de boucle
    # UN CHAMP PEUT S'ECRIRE PAR UN REGISTRE, PAS SEULEMENT PAR `@(r0,r4)`.
    #
    #     mov  r4,r1 ; add #52,r1 ; ... ; mov.w r3,@r1     -> objet+52
    #
    # Les deux lecteurs sans script posent leur DOUZIEME champ ainsi, et mon premier
    # decodage l'a rate : il annoncait 22 et 20 octets pour des enregistrements de 24.
    # Lus au mauvais pas, les enregistrements suivants d'un bloc sortaient en bruit.
    obj = {4: 0}             # registre -> offset dans l'objet (r4 tient l'objet)

    # `arg` arrive en r4 ; `z` sera reconnu a sa lecture dans le contexte.
    reg[4] = dict(k=0, arg=1, z=0)

    c = f
    while c < fin:
        if c in saut:
            c += 2
            continue

        op = u16(c)
        n = (op >> 8) & 0xF
        m = (op >> 4) & 0xF

        # --- chargement de litteraux -------------------------------------------------
        if (op >> 12) == 0xD:                       # mov.l @(disp,PC),rN
            v = litteral_l(c)
            reg[n] = _c(v) if v is not None else None
            if v is not None:
                litteraux.append(v)
            if n == 0:
                r0 = v

        elif (op >> 12) == 0x9:                     # mov.w @(disp,PC),rN
            v = litteral_w(c)
            reg[n] = _c(v) if v is not None else None
            if n == 0:
                r0 = v

        elif (op & 0xF000) == 0xE000:               # mov #imm,rN
            v = op & 0xFF
            v = v - 256 if v > 127 else v
            reg[n] = _c(v)
            if n == 0:
                r0 = v

        elif (op & 0xF000) == 0x7000:               # add #imm,rN
            v = op & 0xFF
            v = v - 256 if v > 127 else v
            reg[n] = _add(reg.get(n), _c(v))
            if n in obj and n != 4:
                obj[n] += v
            if n == 0 and r0 is not None:
                r0 += v

        elif (op & 0xF00F) == 0x6003:               # mov rM,rN
            reg[n] = reg.get(m)
            if m in obj:
                obj[n] = obj[m]
            else:
                obj.pop(n, None)
            if n == 0:
                r0 = reg[n]["k"] if reg.get(n) and not reg[n]["arg"] \
                    and not reg[n]["z"] else None

        elif (op & 0xF00F) == 0x300C:               # add rM,rN
            reg[n] = _add(reg.get(n), reg.get(m))
            if n == 0:
                r0 = None

        elif (op & 0xF0FF) == 0x4000:               # shll rN
            reg[n] = _mul(reg.get(n), 2)
            if n == 0 and r0 is not None:
                r0 *= 2

        elif (op & 0xF0FF) == 0x4008:               # shll2 rN
            reg[n] = _mul(reg.get(n), 4)
            if n == 0 and r0 is not None:
                r0 *= 4

        elif (op & 0xF0FF) == 0x4018:               # shll8 rN
            reg[n] = _mul(reg.get(n), 256)
            if n == 0 and r0 is not None:
                r0 *= 256

        # `exts.w rM,rN` est 0110nnnnmmmm1111 : le masque porte sur le quartet BAS, pas
        # sur l'octet. Avec 0xF0FF il ne reconnaissait que `exts.w r0,rN`, et l'argument
        # -- qui passe toujours par un `exts.w` avant d'etre decale -- se perdait la.
        elif (op & 0xF00F) == 0x600F:               # exts.w rM,rN
            reg[n] = reg.get(m)

        # --- lectures de tables --------------------------------------------------------
        elif (op & 0xF00F) == 0x6000:               # mov.b @rM,rN
            e = reg.get(m)
            # `z` se reconnait a ceci, et a rien d'autre : un octet lu au contexte +6
            if e is not None and not e["arg"] and not e["z"] and e["k"] == CONTEXTE + 6:
                reg[n] = dict(k=0, arg=0, z=1)
            else:
                charges.append((e, 1))
                reg[n] = None

        elif (op & 0xF00F) == 0x6001:               # mov.w @rM,rN
            # LE DERNIER CHAMP SE LIT SANS POST-INCREMENT : la boucle n'a plus besoin
            # d'avancer le pointeur. Il occupe pourtant un mot de l'enregistrement.
            if source is not None and m == lecteur:
                mots += 1
                attente = n
            else:
                charges.append((reg.get(m), 2))
            reg[n] = None

        elif (op & 0xF00F) == 0x6002:               # mov.l @rM,rN
            charges.append((reg.get(m), 4))
            reg[n] = None

        elif (op & 0xF00F) == 0x6005:               # mov.w @rM+,rN  -- LE BLOC
            mots += 1
            lecteur = m
            if source is None:
                # D'OU VIENT LE BLOC. Si le registre de lecture porte encore une
                # expression connue, le bloc est EN DUR (eventuellement indexe par
                # l'argument : `0x8C17F2D8 + arg*24` chez Alex). S'il est inconnu, c'est
                # qu'il sort d'un `mov.l @rN` -- le pointeur vient d'une table.
                source = reg.get(m)
                indirect = source is None
            attente = n
            reg[n] = None

        # --- ecritures dans l'objet ----------------------------------------------------
        elif (op & 0xF00F) == 0x0005:               # mov.w rM,@(r0,rN)
            if attente is not None and m == attente and r0 is not None:
                champs.append((len(champs), r0))
                attente = None

        elif (op & 0xF00F) == 0x2001:               # mov.w rM,@rN
            if attente is not None and m == attente and n in obj:
                champs.append((len(champs), obj[n]))
                attente = None

        elif (op & 0xF000) == 0x8000 and ((op >> 8) & 0xF) == 1:   # mov.w r0,@(disp,rN)
            pass                                    # ecrit r0, pas un champ du bloc

        # un branchement EN ARRIERE : la fonction boucle, donc plusieurs enregistrements
        arriere = False

        if (op & 0xF000) in (0xA000, 0xB000):
            d = op & 0xFFF
            d = d - 0x1000 if d & 0x800 else d
            arriere = c + 4 + d * 2 <= c
        elif (op & 0xFF00) in (0x8900, 0x8B00, 0x8D00, 0x8F00):
            d = op & 0xFF
            d = d - 0x100 if d & 0x80 else d
            arriere = c + 4 + d * 2 <= c

        if arriere:
            boucle = True

            # COMBIEN DE TOURS : la comparaison qui precede le branchement arriere.
            #
            #     mov    #4,r3
            #     exts.w r10,r2
            #     cmp/ge r3,r2
            #     bf     <retour>
            #
            # Le compte d'un spawner a bloc EN DUR ne se lit nulle part ailleurs -- il
            # n'a pas de table de nombres. Le deduire du point ou les enregistrements
            # cessent d'etre plausibles marcherait souvent, et ce serait un pari.
            for p in range(c - 2, max(f, c - 16), -2):
                o = u16(p)
                if (o & 0xF00F) in (0x3003, 0x3007):        # cmp/ge, cmp/gt
                    rb = (o >> 4) & 0xF
                    e = reg.get(rb)
                    if e is not None and not e["arg"] and not e["z"] and 0 < e["k"] <= 64:
                        tours = e["k"]
                    break

        c += 2

    if not champs:
        return None

    # Les deux tables : la premiere lecture sur 16 bits est le NOMBRE, la premiere sur
    # 32 bits le POINTEUR. C'est le moule commun a tous les chargeurs des deux jeux.
    nombres = next((e for e, t in charges if t == 2 and e is not None
                    and DONNEES(e["k"])), None)
    pointeurs = next((e for e, t in charges if t == 4 and e is not None
                      and DONNEES(e["k"])), None)

    # LE PAS EST LE NOMBRE DE MOTS LUS, pas le nombre de champs reconnus. Un champ dont
    # on n'a pas su nommer la destination occupe quand meme sa place.
    return dict(adresse=f, champs=champs, pas=max(mots, len(champs)) * 2,
                nombres=nombres if indirect else None,
                pointeurs=pointeurs if indirect else None,
                bloc=None if indirect else source,
                boucle=boucle, tours=tours, litteraux=litteraux, fin=fin)


def blocs(a, arg, zmax=4):
    """[(z, nombre, pointeur)] pour cet argument, ou [] si l'indexation est inconnue.

    Un bloc EN DUR n'a pas de nombre : le spawner cree un objet par appel, sauf s'il
    boucle. On rend alors `None` comme nombre -- c'est a l'appelant de le dire, et
    l'inventer serait exactement l'erreur que ce chantier repete.
    """
    if a["bloc"] is not None:
        e = a["bloc"]
        p = e["k"] + e["arg"] * arg + e["z"] * 0

        if not DONNEES(p):
            return []

        return [(0, (a["tours"] if a["boucle"] else 1), p)]

    tn, tp = a["nombres"], a["pointeurs"]

    if tn is None or tp is None:
        return []

    out = []
    for z in range(zmax if (tn["z"] or tp["z"]) else 1):
        an = tn["k"] + tn["arg"] * arg + tn["z"] * z
        ap = tp["k"] + tp["arg"] * arg + tp["z"] * z

        if not lisible(an, 2) or not lisible(ap, 4):
            continue

        nb, p = u16(an), u32(ap)

        if 0 < nb <= 200 and DONNEES(p):
            out.append((z, nb, p))

    return out


def decrire(a):
    print("SPAWNER %08X" % a["adresse"])
    print("   enregistrement de %d octets, %d champs" % (a["pas"], len(a["champs"])))
    print("   champ  offset objet")
    for rang, off in a["champs"]:
        print("      %-3d  +%-4d %s" % (rang, off, NOMS.get(off, "")))
    if a["bloc"] is not None:
        print("   bloc EN DUR a [%s]%s"
              % (_txt(a["bloc"]),
                 ("  et il BOUCLE %s fois" % (a["tours"] if a["tours"] else "?"))
                 if a["boucle"] else "  un seul enregistrement par appel"))
    else:
        print("   nombres   u16 [%s]" % _txt(a["nombres"]))
        print("   pointeurs u32 [%s]" % _txt(a["pointeurs"]))


def main():
    import chargeurs2i as CH

    if len(sys.argv) > 1:
        f = int(sys.argv[1], 16)
        a = analyser(f)
        if a is None:
            print("%08X ne lit aucun bloc." % f)
            return
        decrire(a)
        print()
        for arg in range(8):
            for z, nb, p in blocs(a, arg):
                print("   arg %-2d z %d -> %-3s enregistrements a %08X"
                      % (arg, z, nb if nb is not None else "?", p))
        return

    # Les spawners dedies que `chargeurs2i` nomme, et leurs appelants.
    print("Les spawners dedies, leur FORMAT lu dans leur code, et leurs blocs.")
    print("`z` est un TIRAGE 0..3 refait a chaque entree d'etage, pas un round.\n")

    vus = {}

    for deb, fin, bande in CH.scripts_detage():
        aplat = list(CH.appels(deb, fin))
        vues = set()

        for _s, cible, _ar in list(aplat):
            if cible in vues:
                continue
            vues.add(cible)
            aplat += CH.appels(cible, CH.fin_de_fonction(cible))

        for site, cible, arg in aplat:
            proprio = CH.decor_du_site(site)
            if proprio is not None and proprio != bande:
                continue
            if CH.chargeur(cible) or arg is None:
                continue
            a = analyser(cible)
            if a is None or (a["nombres"] is None and a["bloc"] is None):
                continue
            vus.setdefault(cible, (a, []))
            if (bande, arg) not in vus[cible][1]:
                vus[cible][1].append((bande, arg))

    b2d = CH.bande_vers_decor()

    for f in sorted(vus):
        a, appelants = vus[f]
        decrire(a)
        print("   appele par :")
        for bande, arg in sorted(appelants):
            bs = blocs(a, arg)
            d = b2d.get(bande)
            if not bs:
                print("      bande %-3d (decor %-3s) arg %-3d -> aucun bloc"
                      % (bande, d, arg))
                continue
            for z, nb, p in bs:
                print("      bande %-3d (decor %-3s) arg %-3d z %d -> %-3s a %08X"
                      % (bande, d, arg, z, nb if nb is not None else "?", p))
        print()


if __name__ == "__main__":
    main()
