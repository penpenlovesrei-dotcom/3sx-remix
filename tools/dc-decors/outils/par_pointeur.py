# -*- coding: utf-8 -*-
"""LES ACTEURS DE DECOR QUI LISENT UN COMBATTANT PAR POINTEUR -- 23/09/2026.

`combattants.py` attrape ceux qui portent l'adresse d'un combattant en dur (`plw + champ`,
indexee par `muls.w`). Il en manque, et Frederic le demande : ceux qui passent par un
POINTEUR range dans leur propre fiche.

Les trois pointeurs de l'en-tete `WORK` (identique pour un combattant et pour un sprite de
decor, voir la carte du 23/09) :

    +12  void* target_adrs   la cible -- l'adversaire pour un combattant
    +16  void* hit_adrs      ce qui l'a touche
    +20  void* dmg_adrs      ce qui l'a blesse

On cherche donc, dans le code des acteurs, la suite

    mov.l @(3,rm),rn        ; rn = fiche->target_adrs     (disp 3 -> octet 12)
    ... puis une lecture a un offset de `rn`

et on nomme l'offset avec la carte de `combattants.py`. Un offset qui tombe sur un champ de
combattant -- `+102` le x, `+38` l'etat, `+68` le figement de coup, `+8` le personnage --
dit que l'acteur regarde un combattant.

    python par_pointeur.py          2I puis NG
    python par_pointeur.py ng       New Generation seulement
"""
import collections
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)

import combattants as C

POINTEURS = {3: "target_adrs", 4: "hit_adrs", 5: "dmg_adrs"}
FENETRE = 90          # instructions examinees apres la lecture du pointeur


def lectures(mod, rn, depart, fin):
    """Les offsets lus a partir du pointeur, en le SUIVANT.

    Le pointeur est rarement utilise sur place : il passe par `mov rm,rn`, il est range
    dans la pile (`mov.l rn,@(d,r15)`) puis relu. On tient donc un ensemble de registres et
    un ensemble de cases de pile qui portent le pointeur, et on les propage.
    """
    regs = {rn}
    pile = set()
    out = []
    cst = None

    for a in range(depart, fin, 2):
        w = mod.u16(mod.a2o(a))
        n, m, d = (w >> 8) & 15, (w >> 4) & 15, w & 15

        if (w & 0xFF00) == 0xE000 and n == 0:
            cst = w & 0xFF
            continue
        if (w & 0xFF00) == 0x9000 and n == 0:
            cst = mod.u16(mod.a2o(a + 4 + (w & 0xFF) * 2))
            continue

        # rangement dans la pile : mov.l rm,@(d,r15)  = 0001 nnnn mmmm dddd, n = 15
        if (w & 0xF000) == 0x1000 and n == 15:
            (pile.add if m in regs else pile.discard)(d)
            continue
        # relecture : mov.l @(d,r15),rn = 0101 nnnn 1111 dddd
        if (w & 0xF0F0) == 0x50F0:
            (regs.add if d in pile else regs.discard)(n)
            continue

        # mov rm,rn : propage
        if (w & 0xF00F) == 0x6003:
            (regs.add if m in regs else regs.discard)(n)
            continue

        # lectures indexees par r0
        if (w & 0xF00F) in (0x000C, 0x000D, 0x000E) and m in regs and cst is not None:
            out.append((a, cst))
            if n in regs and n != m:
                regs.discard(n)
            continue

        if (w & 0xFF00) == 0x8500 and n in regs:
            out.append((a, d * 2))
            continue
        if (w & 0xFF00) == 0x8400 and n in regs:
            out.append((a, d))
            continue

        if (w & 0xF000) == 0x5000 and m in regs and m != 15:
            out.append((a, d * 4))
            regs.discard(n)
            continue

        if (w & 0xF00F) in (0x6000, 0x6001, 0x6002) and m in regs:
            out.append((a, 0))
            regs.discard(n)
            continue

        # ecrasements : chargement d'un litteral, immediat, resultat
        if (w >> 12) in (0xD, 0xE, 0x9) and n in regs:
            regs.discard(n)
        if (w & 0xF00F) in (0x300C, 0x3008) and n in regs:   # add/sub rm,rn
            regs.discard(n)
        if not regs and not pile:
            break
    return out


def analyser(mod, nom, code):
    print("=" * 78)
    print("%s : les acteurs qui lisent par pointeur, region %08X..%08X"
          % (nom, code[0], code[1]))
    print("=" * 78)

    par_champ = collections.defaultdict(list)
    for a in range(code[0], code[1], 2):
        w = mod.u16(mod.a2o(a))
        if (w & 0xF000) != 0x5000:
            continue
        d = w & 15
        if d not in POINTEURS:
            continue
        # LA PILE N'EST PAS UN OBJET (corrige le 23/09/2026). `mov.l @(16,r15),r4` a la
        # meme forme que `mov.l @(16,rn),r4` : sans ce filtre, tout prologue qui relit son
        # r4 range en pile passait pour un acteur qui lit `hit_adrs`. C'est ce faux positif
        # qui m'a fait annoncer un receveur de coup dans l'id 19 de NG et l'id 13 de 2I --
        # les deux sites, `8C09EEF2` et `8C0266B6`, sont des relectures de pile.
        if ((w >> 4) & 15) == 15:
            continue
        n = (w >> 8) & 15
        for site, off in lectures(mod, n, a + 2, min(a + 2 * FENETRE, code[1])):
            par_champ[(POINTEURS[d], off)].append((a, site))

    connus = []
    autres = []
    for (ptr, off), sites in par_champ.items():
        nom_champ = C.nom_du_champ(off)
        (connus if nom_champ else autres).append((ptr, off, nom_champ, sites))

    print("\nCE QU'ILS VONT CHERCHER, quand le champ est nomme :")
    for ptr, off, nom_champ, sites in sorted(connus, key=lambda t: (t[0], t[1])):
        print("   %-12s +%-4d %-30s %2d site(s) : %s"
              % (ptr, off, nom_champ, len(sites),
                 " ".join("%08X" % s[0] for s in sites[:8])))

    print("\nLes offsets encore sans nom :")
    ligne = ["%s+%d(%d)" % (p, o, len(s)) for p, o, _n, s in
             sorted(autres, key=lambda t: (t[0], t[1]))]
    for i in range(0, len(ligne), 10):
        print("   " + " ".join(ligne[i:i + 10]))
    print()
    return par_champ


def main():
    quoi = (sys.argv[1] if len(sys.argv) > 1 else "tout").lower()
    import sh4
    import sh4ng
    if quoi in ("tout", "2i"):
        analyser(sh4, "2nd Impact", C.CODE["2I"])
    if quoi in ("tout", "ng"):
        analyser(sh4ng, "New Generation", C.CODE["NG"])


if __name__ == "__main__":
    main()
