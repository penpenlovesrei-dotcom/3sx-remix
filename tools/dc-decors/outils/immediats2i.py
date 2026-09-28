# -*- coding: utf-8 -*-
"""LES SPAWNERS QUI N'ONT PAS DE BLOC — ceux qui écrivent des CONSTANTES dans l'objet.

POURQUOI CET OUTIL EXISTE
-------------------------
`spawners2i.analyser` ne sait lire qu'un chargeur qui PARCOURT un bloc (`mov.w @rM+`). Or
une partie des objets de décor n'a pas de bloc du tout : leur routine pose la position, la
palette, le plan et les drapeaux en dur, instruction par instruction. Chez Yun, ce sont les
cages, la charrette et le fumeur — `8C02936E`, `8C02912C`, `8C02962E`, pour lesquels
`analyser` rend `None`.

C'est un trou qui coûte cher, et Frédéric l'a vu à l'écran avant moi :

  * « les cages sont derrière le personnage qui fume » et « problème de profondeur entre
    les cages et l'étal jaune » — je n'avais NI plan NI drapeaux pour ces trois objets,
    donc rien pour les ordonner ;
  * « où sont les oiseaux animés dans les cages ? » — le script 7 n'a qu'une image ; leur
    animation vient forcément d'un objet qu'aucun chargeur à bloc ne crée.

CE QU'IL FAIT
-------------
Il rejoue la fonction instruction par instruction en suivant deux choses : la valeur
constante de chaque registre, et quels registres pointent dans l'objet. Chaque écriture
d'une constante à un offset connu est relevée. Rien n'est déduit : une valeur inconnue est
rendue `None` et affichée comme telle.

    python immediats2i.py 0x8C02936E
    python immediats2i.py --decor 3        tous les spawners sans bloc de Yun
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import chargeurs2i as CH
import spawners2i as SP

u16 = SP.u16

# Le tireur du tas : il rend le nouvel objet dans r0. Tous les spawners a immediats
# l'appellent, et c'est le seul appel dont on connaisse la valeur de retour.
ALLOCATEUR = 0x8C0217E4

# Les offsets d'objet deja etablis par les chargeurs a bloc. Ils servent de signature :
# un `@(r0,rN)` dont le r0 est l'un d'eux designe l'objet, quel que soit rN.
OFFSETS = {6, 8, 32, 38, 68, 84, 86, 88, 102, 106, 118, 148, 150, 152, 364, 456,
           552, 554, 556, 558, 560}

# Ce que chaque offset est, pour le journal. Les noms viennent du chantier, pas d'un en-tête.
NOMS = {32: "champ0", 38: "?38", 68: "?68", 84: "?84", 86: "?86", 88: "palette",
        102: "x", 106: "y", 118: "?118", 148: "?148", 150: "script repos",
        152: "script action", 456: "script", 554: "drapeaux", 556: "?556", 558: "plan"}


def analyser(f, plafond=0x400):
    """Les constantes que cette fonction écrit dans un objet, en DEUX PASSES.

    Rend `{offset: valeur}` -- `None` en valeur quand le registre source n'était pas une
    constante connue -- plus la liste des fonctions qu'elle appelle.

    POURQUOI DEUX PASSES. La base de l'objet se reconnaît à un `@(r0,rN)` dont le `r0` est
    un offset connu ; tout ce que la fonction écrit AVANT ce premier repère est donc perdu.
    C'est ainsi que `8C02936E` ne rendait ni son `work_id` (+6) ni son **id** (+8), qui
    s'écrivent en tête -- et l'id est la clé de la routine de l'objet, donc de sa machine à
    états. La première passe ne sert qu'à trouver les registres de base ; la seconde relit
    tout en les connaissant d'entrée.
    """
    bases = _passe(f, plafond, None)[3]
    return _passe(f, plafond, bases)[:3]


def _passe(f, plafond, bases_connues):
    fin = SP.fin_de_fonction(f, plafond)
    saut = SP.pools(f, fin)
    val = {}                     # registre -> constante, ou None
    obj = {4: 0}                 # registre -> offset dans l'objet
    ecrits = {}
    appels = []
    depuis_jsr = 99
    bases = set(bases_connues or ())
    # EN SECONDE PASSE, UNE BASE CONNUE NE SE PERD PLUS. Sans ça un `mov r0,r14` anodin
    # la retirait avant meme les ecritures de tete -- c'est ce qui faisait manquer le
    # `work_id` (+6) et l'**id** (+8) de `8C02936E`.
    fixes = set(bases_connues or ())

    for b in bases:
        obj[b] = 0

    c = f
    while c < fin:
        if c in saut:
            c += 2
            continue

        op = u16(c)
        n = (op >> 8) & 0xF
        m = (op >> 4) & 0xF
        depuis_jsr += 1

        if (op >> 12) == 0xD:                            # mov.l @(disp,PC),rN
            val[n] = SP.litteral_l(c)
            if n not in fixes:
                obj.pop(n, None)

        elif (op >> 12) == 0x9:                          # mov.w @(disp,PC),rN
            val[n] = SP.litteral_w(c)
            if n not in fixes:
                obj.pop(n, None)

        elif (op & 0xF000) == 0xE000:                    # mov #imm,rN
            v = op & 0xFF
            val[n] = v - 256 if v > 127 else v
            if n not in fixes:
                obj.pop(n, None)

        elif (op & 0xF000) == 0x7000:                    # add #imm,rN
            v = op & 0xFF
            v = v - 256 if v > 127 else v
            val[n] = None if val.get(n) is None else val[n] + v
            if n in obj:
                obj[n] += v

        elif (op & 0xF00F) == 0x6003:                    # mov rM,rN
            val[n] = val.get(m)
            if m in obj:
                obj[n] = obj[m]
            elif n not in fixes:
                obj.pop(n, None)
            # LE NOUVEL OBJET REVIENT DANS r0. Un `mov r0,rN` juste apres un `jsr` designe
            # donc l'objet fraichement tire du tas : c'est LUI la base, pas r4.
            if m == 0 and depuis_jsr <= 3:
                obj[n] = 0
                val[n] = None

        # UNE LECTURE MEMOIRE DETRUIT LA CONSTANTE. Sans ça, un registre gardait la valeur
        # qu'il portait avant d'aller lire un enregistrement, et l'outil annonçait comme
        # « constante » ce qui venait du bloc -- il donnait 0x17E4 pour `my_priority` de
        # `8C02356A`, qui est en fait le bas de l'adresse de l'allocateur.
        elif (op & 0xF00F) in (0x6000, 0x6001, 0x6002,   # mov.b/w/l @rM,rN
                               0x6004, 0x6005, 0x6006):  # mov.b/w/l @rM+,rN
            val[n] = None
            if n not in fixes:
                obj.pop(n, None)

        elif (op & 0xF000) in (0x5000,):                 # mov.l @(disp,rM),rN
            val[n] = None
            if n not in fixes:
                obj.pop(n, None)

        elif (op & 0xFF00) in (0x8400, 0x8500):          # mov.b/w @(disp,rM),r0
            val[0] = None
            obj.pop(0, None)

        elif (op & 0xF00F) in (0x000C, 0x000D, 0x000E):  # mov.b/w/l @(r0,rM),rN
            val[n] = None
            if n not in fixes:
                obj.pop(n, None)

        elif (op & 0xF0FF) == 0x400B:                    # jsr @rN
            if val.get(n):
                appels.append(val[n])
            depuis_jsr = 0
            # LE TIREUR DU TAS REND L'OBJET DANS r0. C'est le seul appel dont on sache la
            # valeur de retour, et le marquer ici vaut mieux que le deviner a la fenetre :
            # `8C02936E` ne rendait AUCUNE ecriture parce que son `mov r0,rN` tombait hors
            # des trois instructions que je regardais.
            if val.get(n) == ALLOCATEUR:
                obj[0] = 0
                val[0] = None

        # --- ecritures dans l'objet ---------------------------------------------------
        elif (op & 0xF00F) in (0x0004, 0x0005, 0x0006):  # mov.b/w/l rM,@(r0,rN)
            # L'OFFSET IDENTIFIE LA BASE. Suivre le registre qui porte l'objet depuis son
            # allocation echoue des que la fonction le range ailleurs -- `8C02936E` le met
            # dans r14 par un chemin que le suivi perd, et ne rendait AUCUNE ecriture.
            # Mais un `@(r0,rN)` dont le r0 vaut 558, 554 ou 102 ne peut viser que l'objet :
            # ce sont des offsets qu'on a lus dans les chargeurs a bloc. On adopte donc rN
            # comme base, et les ecritures suivantes suivent.
            if n not in obj and val.get(0) in OFFSETS:
                obj[n] = 0
                bases.add(n)

            if n in obj and val.get(0) is not None:
                ecrits.setdefault(obj[n] + val[0], val.get(m))

        elif (op & 0xF00F) in (0x2000, 0x2001, 0x2002):  # mov.b/w/l rM,@rN
            if n in obj:
                ecrits.setdefault(obj[n], val.get(m))

        elif (op & 0xFF00) in (0x8000, 0x8100):          # mov.b/w r0,@(disp,rN)
            rb = (op >> 4) & 0xF
            d = (op & 0xF) * (2 if (op & 0xFF00) == 0x8100 else 1)
            if rb in obj:
                ecrits.setdefault(obj[rb] + d, val.get(0))

        elif (op & 0xF000) == 0x1000:                    # mov.l rM,@(disp,rN)
            if n in obj:
                ecrits.setdefault(obj[n] + (op & 0xF) * 4, val.get(m))

        c += 2

    return ecrits, appels, fin, bases


def decrire(f):
    ecrits, appels, fin = analyser(f)
    print("SPAWNER A IMMEDIATS %08X   (jusqu'a %08X)" % (f, fin))

    if not ecrits:
        print("   aucune ecriture d'objet reconnue")
    for off in sorted(ecrits):
        v = ecrits[off]
        print("   +%-5d %-14s %s" % (off, NOMS.get(off, ""),
                                     "inconnue" if v is None else
                                     ("%d  (0x%04X)" % (v, v & 0xFFFF))))
    if appels:
        print("   appelle : %s" % " ".join("%08X" % a for a in appels))


def main():
    args = sys.argv[1:]

    if "--decor" in args:
        decor = int(args[args.index("--decor") + 1], 0)
        b2d = CH.bande_vers_decor()
        vus = set()

        for deb, fin, bande in CH.scripts_detage():
            if b2d.get(bande) != decor:
                continue

            import blocs2i
            for g, _arg in blocs2i.arbre(deb, fin):
                if g in vus:
                    continue
                vus.add(g)
                try:
                    a = SP.analyser(g)
                except Exception:
                    a = None
                if a is not None:
                    continue          # celui-la lit un bloc : ce n'est pas notre affaire
                decrire(g)
                print()
        return

    for a in args:
        decrire(int(a, 0))
        print()


if __name__ == "__main__":
    main()
