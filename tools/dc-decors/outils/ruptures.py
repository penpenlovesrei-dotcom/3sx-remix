# -*- coding: utf-8 -*-
"""CE QUI SE BRISE AU CONTACT D'UNE CHUTE -- 23/09/2026, a la demande de Frederic.

LE MODELE EST LE PONT D'ELENA, et il est lu. Deux acteurs, un mot de RAM entre eux :

    id 122 (`0x8C03CAD8`)  son etat 1 N'AVANCE PAS le script et attend `u16[0x8C6B0AA4] != 0`
    id 123 (`0x8C03CC98`)  ecrit ce mot a UN quand le pont tombe (`y` sous 40, `0x8C03CD2C`)

La signature est donc : **un mot de RAM qu'un acteur de decor ECRIT et qu'un autre LIT**,
les deux etant crees par la meme bande. Ce programme cherche cette figure partout.

Ce qu'on ecarte : le tas d'acteurs lui-meme, les fiches de combattant (`plw`), et les
adresses lues par tout le monde -- le gel de trame par exemple, que toute animation
consulte et qui ne declenche rien.

    py -3 ruptures.py            les deux jeux
    py -3 ruptures.py 2i         2nd Impact seulement
    py -3 ruptures.py --bande 3  une bande
"""
import collections
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)

import combattants as C
import dependances as DEP

# Le tas d'acteurs, a exclure : un acteur qui ecrit dans un autre objet n'est pas un
# declencheur global.
TAS = {"2I": (0x8C6466EC, 0x8C6866EC), "NG": (0x8C554668, 0x8C594668)}

# La RAM ou vivent les mots partages. En dehors : le code, les tables, les piles.
RAM = {"2I": (0x8C600000, 0x8C800000), "NG": (0x8C540000, 0x8C620000)}

# Les mots que TOUT LE MONDE consulte : ils ne declenchent rien.
BANALS = {
    0x8C69D314: "le gel de trame",
    0x8C6AF3E8: "bg_w, l'etage",
    0x8C545260: "le gel de trame",
    0x8C54527A: "la pause",
}

JEUX = {
    "2I": dict(etages=(0x8C1D3FB4, 17), acteurs=(0x8C179FDC, 196),
               code=(0x8C010000, 0x8C120000), plw=C.PLW["2I"]),
    "NG": dict(etages=(0x8C189178, 19), acteurs=(0x8C1AD9F8, 186),
               code=(0x8C010000, 0x8C0F0000), plw=C.PLW["NG"]),
}

NOMS = {
    "2I": {0: "Gill", 1: "Alex", 2: "Ryu", 3: "Yun", 4: "Dudley", 5: "Necro", 6: "Hugo",
           7: "Ibuki", 8: "Elena", 9: "?", 10: "Oro", 11: "Yang", 12: "Ken", 13: "Sean",
           14: "Urien", 15: "Akuma", 16: "Hugo bis"},
    "NG": {0: "Gill", 5: "Yun 1", 6: "Yun 2", 7: "Londres 1", 8: "Londres 2",
           14: "Elena 1", 15: "Elena 2", 16: "Oro", 17: "Yang 1", 18: "Yang 2"},
}


def acces(mod, debut, fin, ram, tas, plw):
    """Les mots de RAM que la routine lit et ecrit, par litteral.

    Un litteral seul ne dit rien : on regarde l'instruction qui s'en sert. `mov.w @rn,rm`
    et `mov.b @rn,rm` LISENT ; `mov.w rm,@rn` et `mov.b rm,@rn` ECRIVENT.
    """
    lus, ecrits = set(), set()
    base, taille = plw

    for a in range(debut, min(fin, debut + 0x1000), 2):
        w = mod.u16(mod.a2o(a))

        if w >> 12 != 0xD:
            continue

        n = (w >> 8) & 15

        try:
            v = mod.u32(mod.a2o(((a + 4) & ~3) + (w & 0xFF) * 4))
        except Exception:
            continue

        if not (ram[0] <= v < ram[1]):
            continue
        if tas[0] <= v < tas[1]:
            continue
        if base <= v < base + 2 * taille:
            continue

        # l'emploi du registre, dans les huit instructions qui suivent
        for k in range(1, 9):
            x = mod.u16(mod.a2o(a + 2 * k))

            if (x & 0xF00F) in (0x6000, 0x6001, 0x6002) and ((x >> 4) & 15) == n:
                lus.add(v)
                break
            if (x & 0xF00F) in (0x2000, 0x2001, 0x2002) and ((x >> 8) & 15) == n:
                ecrits.add(v)
                break
            # le registre est reecrit : on abandonne
            if (x >> 12) in (0xD, 0xE, 0x9) and ((x >> 8) & 15) == n:
                break

    return lus, ecrits


def analyser(nom, bande_voulue=None):
    import sh4
    import sh4ng
    mod = sh4 if nom == "2I" else sh4ng
    j = JEUX[nom]
    tab_a, nb_a = j["acteurs"]
    tab_e, nb_e = j["etages"]
    code = j["code"]

    acteurs = {i: DEP.u32(mod, tab_a + i * 4) for i in range(nb_a)}
    lim = DEP.bornes(acteurs.values(), code[1])
    ps = DEP.poses(mod, code)

    print("=" * 78)
    print("%s : un mot de RAM ecrit par un acteur et lu par un autre" % nom)
    print("=" * 78)

    for b in range(nb_e):
        if bande_voulue is not None and b != bande_voulue:
            continue

        ids = set()
        for c in DEP.cibles_par_outil(nom, b):
            if isinstance(c, tuple):
                ids.add(c[1])
                continue
            n = DEP.ids_de(ps, c, 0x120)
            if n:
                ids |= n
                continue
            for i, r in acteurs.items():
                if r <= c < lim.get(r, r):
                    ids.add(i)

        par_mot = collections.defaultdict(lambda: ([], []))
        for i in sorted(ids):
            if i not in acteurs:
                continue
            r = acteurs[i]
            lus, ecrits = acces(mod, r, lim.get(r, r + 0x400), RAM[nom], TAS[nom], j["plw"])
            for v in lus:
                par_mot[v][0].append(i)
            for v in ecrits:
                par_mot[v][1].append(i)

        lignes = []
        for v, (lus, ecrits) in sorted(par_mot.items()):
            if v in BANALS or not ecrits or not lus:
                continue
            if set(lus) == set(ecrits):        # l'acteur relit ce qu'il ecrit : pas un signal
                continue
            lignes.append("      %08X  ecrit par %s, lu par %s"
                          % (v, ", ".join("id %d" % x for x in sorted(set(ecrits))),
                             ", ".join("id %d" % x for x in sorted(set(lus) - set(ecrits)))))

        etat = "%d acteurs" % len(ids)
        print("   bande %2d %-10s %-14s %s"
              % (b, NOMS[nom].get(b, ""), etat, "" if lignes else "--"))
        for l in lignes:
            print(l)
    print()


def main():
    bande = None
    if "--bande" in sys.argv:
        bande = int(sys.argv[sys.argv.index("--bande") + 1])
    quoi = [a.lower() for a in sys.argv[1:] if not a.startswith("--") and not a.isdigit()]
    for nom in ("2I", "NG"):
        if not quoi or nom.lower() in quoi:
            analyser(nom, bande)


if __name__ == "__main__":
    main()
