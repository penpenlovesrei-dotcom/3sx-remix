# -*- coding: utf-8 -*-
"""A QUI APPARTIENT CHAQUE BLOC D'OBJETS DE DECOR — lu dans le code, pas devine.

C'est l'outil qui remplace toutes les recherches de motif du chantier. Il suit la seule
chaine qui dise la verite, et elle est entierement dans le binaire :

    0x8C1D3FB4[decor]          le script d'etage du decor
        dedans : jsr <chargeur>  avec  mov #arg,r4
    <chargeur> :
        nombre = u16 [tableA + arg*2]
        bloc   = u32 [tableB + arg*4]
        puis une suite de `mov.w @r14+` qui donne le FORMAT

POURQUOI IL A FALLU EN VENIR LA
-------------------------------
L'epreuve qui servait jusqu'ici -- « le script de l'enregistrement se resout dans l'asset
du decor, avec des palettes dans sa plage » -- ne discrimine **rien**. Mesure faite sur
cinq blocs : chacun se resout a 100 % dans le decor que le code lui donne ET a 100 % dans
Oro. Six sur six, dix sur dix, huit sur huit, des deux cotes. C'est ainsi que le bloc de
YANG s'est retrouve pose sur l'etage d'Oro pendant tout le chantier.

**Seul l'appelant du chargeur dit a qui un bloc appartient.**

ET LE FORMAT N'EST PAS UNIQUE
-----------------------------
Chaque chargeur range ses enregistrements a sa facon. Deux mesures :

    0x8C02E1FE   16 octets, x a l'octet 4, y a l'octet 6
    0x8C025A9A   16 octets, x a l'octet 6, y a l'octet 8   (un champ de plus en tete)
    0x8C02AA7C   38 octets  -- et la table le confirme : ses ecarts valent nb x 38

Donc on ne suppose plus la taille : on la lit dans la boucle, et on la recoupe avec la
contiguite de la table (pointeur[i] + nombre[i]*taille == pointeur[i+1]).

    python chargeurs2i.py            l'attribution des dix-sept decors
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sh4

D, B = sh4.D, sh4.BASE
u16o = lambda o: struct.unpack_from('<H', D, o)[0]
u16 = lambda a: u16o(a - B)
u32 = lambda a: struct.unpack_from('<I', D, a - B)[0]

TABLE_SCRIPTS = 0x8C1D3FB4
NB_DECORS = 17
FIN_SCRIPTS = 0x8C0DF400

# L'INDEX DE `0x8C1D3FB4` EST LA **BANDE**, PAS LE DECOR -- 01/09/2026.
#
# Cet outil a longtemps appele « decor » l'index de cette table, et c'est ce qui produisait
# le fameux « decalage d'index a partir de l'etage 10 » que la doc constatait sans jamais
# l'expliquer. La table `0x8C1D591C` donne `(decor*3 + aire) -> bande`, et elle dit que le
# decor 8 porte les bandes 8, 9 et 9 : au-dela, bande = decor + 1.
#
# LA MESURE QUI TRANCHE (17 blocs, les deux lectures mises en concurrence) : combien
# resolvent 100 % de leurs images dans l'asset du decor suppose ?
#
#     lecture « index = decor »  ->  14 / 17
#     lecture « index = bande »  ->  16 / 17
#
# Et elle ne fait pas que gagner aux points, elle redresse les deux echecs :
#
#     index 13 : lu comme decor 13 (Urien)  ->   0/19   -- rien ne se resout
#                lu comme bande 13 -> decor 12 (Sean) -> 46/46
#     index 11 : lu comme decor 11 (Ken)    ->   0/0
#                lu comme bande 11 -> decor 10 (Yang) ->  8/8 et 4/4
#
# Enfin l'index 10 passe de 4/4 et 8/8 a 16/16 et 82/82 : c'est le critere « beaucoup
# d'images » que `accorder2i.py` emploie deja pour departager deux tables de scripts. Et
# ca confirme par le calcul ce que Frederic avait tranche a l'ecran -- le bloc
# `0x8C17E918` est bien celui d'Oro, appele depuis la BANDE 10.
BANDE_VERS_DECOR = None  # rempli par `bande_vers_decor()`, une seule fois


def bande_vers_decor():
    """{bande: decor}, lu dans `0x8C1D591C` -- `(decor*3 + aire) -> bande`."""
    global BANDE_VERS_DECOR

    if BANDE_VERS_DECOR is None:
        BANDE_VERS_DECOR = {}
        for d in range(NB_DECORS):
            for aire in range(3):
                bd = u16(0x8C1D591C + (d * 3 + aire) * 2)
                BANDE_VERS_DECOR.setdefault(bd, d)

    return BANDE_VERS_DECOR

FIN_BIN = B + len(D)

# **Le binaire s'arrete avant 0x8C700000**, et une table lue au-dela leve une exception au
# lieu de dire non. Toutes les bornes passent donc par `lisible`.
lisible = lambda a, n=4: B <= a and a + n <= FIN_BIN
CODE = lambda v: 0x8C010000 <= v < 0x8C120000
DONNEES = lambda v: 0x8C120000 <= v < FIN_BIN


def scripts_detage():
    """[(debut, fin, bande)] tries par adresse -- la table n'est PAS dans cet ordre.

    Le troisieme membre est la **BANDE**, pas le decor : voir `BANDE_VERS_DECOR` en tete.
    """
    t = sorted((u32(TABLE_SCRIPTS + k * 4), k) for k in range(NB_DECORS))
    out = []

    for i, (ad, d) in enumerate(t):
        fin = t[i + 1][0] if i + 1 < len(t) else FIN_SCRIPTS
        out.append((ad, fin, d))

    return out


def fin_de_fonction(deb, plafond=0x200):
    """Fin d'une fonction appelee : son premier `rts` (0x000B) et le delay slot.

    UNE FENETRE FIXE DONNE DE FAUSSES ATTRIBUTIONS, et ca s'est verifie ici le
    01/09/2026. La profondeur 2 balayait `cible .. cible + 0x200` en aveugle ; quand la
    fonction appelee est plus courte, la fenetre deborde sur la SUIVANTE et ramasse ses
    appels. Les scripts d'etage de 2nd Impact se suivent en memoire (340 a 1672 octets),
    donc deborder d'un cran suffit a donner a un decor les blocs de son voisin.
    """
    fin = min(deb + plafond, FIN_BIN - 2)

    for c in range(deb, fin, 2):
        if u16(c) == 0x000B:  # rts
            return min(c + 4, fin)

    return fin


def decor_du_site(site):
    """Le decor dont la routine d'etage contient `site`, ou None s'il est hors zone.

    Second garde, independant du premier : meme si une fenetre deborde, un site qui
    tombe dans la routine d'un AUTRE decor ne peut pas etre attribue a celui-ci.
    """
    if site is None:
        return None

    for deb, fin, d in scripts_detage():
        if deb <= site < fin:
            return d

    return None


def litteral(pc):
    """La valeur chargee par un `mov.l @(disp,PC),rN` place en `pc`, ou None."""
    op = u16(pc)

    if (op >> 12) != 0xD:
        return None

    pool = (pc & ~3) + 4 + (op & 0xFF) * 4
    return u32(pool) if 0 <= pool - B < len(D) - 4 else None


def appels(deb, fin):
    """[(site, cible, arg)] des `jsr`/`jmp @rN` du bloc, avec la constante mise dans r4.

    La constante arrive souvent dans le DELAY SLOT, juste apres le saut -- c'est le piege
    du SH-4, et l'oublier fait rater la moitie des appels.
    """
    charge = {}
    out = []

    for c in range(deb, min(fin, FIN_BIN - 2), 2):
        op = u16(c)

        # mov.l @(disp,PC),rN
        if (op >> 12) == 0xD:
            v = litteral(c)

            if v is not None:
                charge[(op >> 8) & 0xF] = v

        # jsr @rN (0x4n0B) / jmp @rN (0x4n2B)
        elif (op & 0xF0FF) in (0x400B, 0x402B):
            n = (op >> 8) & 0xF
            cible = charge.get(n)

            if cible is None or not CODE(cible):
                continue

            arg = None

            # le delay slot d'abord, puis les six instructions d'avant
            for p in [c + 2] + [c - 2 * k for k in range(1, 7)]:
                o = u16(p)

                if (o & 0xFF00) == 0xE400:      # mov #imm,r4
                    arg = o & 0xFF
                    break

            out.append((c, cible, arg))

    # Les tables de dispatch chargees ici : leurs entrees sont autant de fonctions du
    # script, atteintes sans qu'aucun `jsr` ne les nomme.
    for v in set(charge.values()):
        for cible in table_de_dispatch(v):
            out.append((None, cible, None))

    return out


def table_de_dispatch(v, mini=2, maxi=8):
    """[cibles] si `v` pointe sur une petite table de pointeurs de CODE, sinon [].

    **C'est l'angle mort qu'il fallait lever.** Un script d'etage n'appelle pas ses phases
    par un litteral : il copie une table de pointeurs sur la pile et fait
    `jsr @[r15 + etat*4]`. Rien de tout ca ne ressemble a un appel, et la moitie du script
    -- celle qui cree les objets -- restait donc invisible. Oro en a deux, `0x8C1D6130`
    (trois etats) et `0x8C1D613C` (deux).
    """
    if not DONNEES(v) or not lisible(v, maxi * 4):
        return []

    out = []

    for k in range(maxi):
        c = u32(v + k * 4)

        if not CODE(c):
            break

        out.append(c)

    return out if len(out) >= mini else []


def chargeur(f):
    """(tableA, tableB) si `f` est un chargeur de bloc, sinon None.

    Le modele : un index passe en r4, double pour lire un u16 (le nombre) et quadruple
    pour lire un u32 (le pointeur). On repere les deux tables par les pools charges dans
    r0 juste avant chaque acces indexe.
    """
    r0 = None
    tA = tB = None

    for c in range(f, min(f + 0x80, FIN_BIN - 2), 2):
        op = u16(c)

        if (op >> 12) == 0xD and ((op >> 8) & 0xF) == 0:
            r0 = litteral(c)

        # MOV.W @(R0,Rm),Rn = 0000nnnnmmmm1101 -> le NOMBRE, lu sur 16 bits
        elif (op & 0xF00F) == 0x000D and r0 is not None and tA is None:
            tA = r0

        # MOV.L @(R0,Rm),Rn = 0000nnnnmmmm1110 -> le POINTEUR, lu sur 32 bits
        elif (op & 0xF00F) == 0x000E and r0 is not None and tB is None:
            tB = r0

        if tA is not None and tB is not None:
            break

    if tA is None or tB is None or not DONNEES(tA) or not DONNEES(tB):
        return None

    return tA, tB


BLOCS = lambda v: 0x8C120000 <= v < 0x8C1A0000


def spawner_en_dur(f):
    """(bloc, nb_de_champs) si `f` porte son bloc EN DUR, sinon None.

    C'est le cas de `bg00` : son spawner `0x8C04AE04` fait `mov.l <0x8C183DC8>,r14` puis
    lit le bloc en `mov.w @r14+`. Aucune table, aucun index -- donc invisible pour la
    recherche par appelant, et c'est pour ca qu'il fallait le chercher a part.
    """
    bloc = None
    lus = 0

    for c in range(f, min(f + 0x200, FIN_BIN - 2), 2):
        op = u16(c)

        if (op >> 12) == 0xD:
            v = litteral(c)

            if v is not None and BLOCS(v) and bloc is None:
                bloc = v

        # mov.w @rM+,rN = 0110nnnnmmmm0101
        elif (op & 0xF00F) == 0x6005:
            lus += 1

    return (bloc, lus) if bloc is not None and lus >= 4 else None


def taille_enregistrement(tA, tB, n=10):
    """La taille qui rend la table contigue : pointeur[i] + nombre[i]*T == pointeur[i+1]."""
    best = (0, None)

    for T in (8, 16, 24, 32, 38, 40, 48):
        ok = 0

        for k in range(n):
            if not lisible(tB + (k + 1) * 4) or not lisible(tA + k * 2, 2):
                continue

            p, q, c = u32(tB + k * 4), u32(tB + (k + 1) * 4), u16(tA + k * 2)

            if not (DONNEES(p) and DONNEES(q)) or c > 200:
                continue

            if c and p + c * T == q:
                ok += 1

        if ok > best[0]:
            best = (ok, T)

    return best[1], best[0]


def main():
    print("Les dix-sept scripts d'etage, et les chargeurs de blocs qu'ils appellent.")
    print("L'appelant est la SEULE preuve d'appartenance d'un bloc.\n")

    vus = {}
    lignes = []
    durs = []

    for deb, fin, d in scripts_detage():
        # PROFONDEUR 2 : le script appelle des fonctions qui appellent les chargeurs.
        # A la profondeur 1 seul `bg00` repondait, et c'est ce qui a fait croire si
        # longtemps que « les autres decors ne joignent que des fonctions partagees ».
        vues = set()
        aplat = list(appels(deb, fin))

        for _s, cible, _a in list(aplat):
            if cible in vues:
                continue

            vues.add(cible)
            aplat += appels(cible, fin_de_fonction(cible))

        for site, cible, arg in aplat:
            # SECOND GARDE. Un site qui tombe dans la routine d'un AUTRE decor ne lui
            # appartient pas, quelle que soit la fenetre qui l'a ramasse. Hors zone des
            # scripts d'etage (une fonction partagee), on ne peut pas trancher ainsi et
            # on laisse passer.
            proprio = decor_du_site(site)

            if proprio is not None and proprio != d:
                continue

            # Un chargeur porte AUSSI sa table de nombres comme litteral : sans cette
            # exclusion, chacun d'eux ressort comme un faux spawner en dur.
            dur = None if chargeur(cible) else spawner_en_dur(cible)

            if dur is not None and (d, dur[0]) not in [(x[0], x[1]) for x in durs]:
                durs.append((d, dur[0], cible, dur[1]))

            f = chargeur(cible)

            if f is None or arg is None:
                continue

            tA, tB = f

            if not lisible(tA + arg * 2, 2) or not lisible(tB + arg * 4):
                continue

            nb = u16(tA + arg * 2)
            bloc = u32(tB + arg * 4)

            if not DONNEES(bloc) or not (0 < nb <= 200):
                continue

            if (d, bloc) in [(l[0], l[4]) for l in lignes]:
                continue

            vus.setdefault(cible, (tA, tB))
            lignes.append((d, cible, arg, nb, bloc, site))

    print("%-6s %-10s %-4s %-4s %-10s %s"
          % ("bande", "chargeur", "arg", "nb", "bloc", "appele en"))

    for d, cible, arg, nb, bloc, site in sorted(lignes):
        b2d = bande_vers_decor()
        print("  %2d %-7s %08X   %-4d %-4d %08X   %08X"
              % (d, "-> d%d" % b2d[d] if d in b2d else "-> ?", cible, arg, nb, bloc, site))

    print("\nLes chargeurs rencontres, leurs tables et la taille de leurs enregistrements :")

    for f, (tA, tB) in sorted(vus.items()):
        T, ok = taille_enregistrement(tA, tB)
        print("   %08X   nombres %08X   pointeurs %08X   %s octets (%d entrees contigues)"
              % (f, tA, tB, T, ok))

    # Une fonction appelee par beaucoup de decors est GENERIQUE : le bloc qu'elle porte
    # n'appartient a aucun d'eux en particulier. Seules celles d'un ou deux decors sont
    # des spawners DEDIES, comme celui de `bg00`.
    combien = {}

    for _d, _bloc, f, _lus in durs:
        combien[f] = combien.get(f, 0) + 1

    propres = [x for x in durs if combien[x[2]] <= 2]

    if propres:
        print("\nSpawners DEDIES, qui portent leur bloc en dur :")

        for d, bloc, f, lus in sorted(propres):
            b2d = bande_vers_decor()
            print("   bande %2d -> decor %-3s %08X porte %08X   (%d champs lus)"
                  % (d, str(b2d.get(d)), f, bloc, lus))

    partages = sorted({(f, b) for _d, b, f, _l in durs if combien[f] > 2})

    if partages:
        print("\nFonctions partagees par plus de deux decors -- ce n'est PAS une "
              "attribution :")

        for f, b in partages:
            print("   %08X porte %08X   appelee par %d decors" % (f, b, combien[f]))

    manquants = sorted({d for _a, _b, d in scripts_detage()}
                       - {l[0] for l in lignes} - {x[0] for x in propres})
    print("\nDecors sans aucun bloc trouve : %s"
          % (", ".join(str(d) for d in manquants) or "aucun"))


if __name__ == "__main__":
    main()
