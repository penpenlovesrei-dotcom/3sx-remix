# -*- coding: utf-8 -*-
"""L'ETAT DE LA DECOMPILATION DES DECORS DE 2nd IMPACT, EN CHIFFRES -- 29/09/2026.

Le pendant de `inventaire_decors.py`, qui fait la meme chose pour New Generation.

On balaie les seize routines d'etage de 2I (leurs bornes viennent de `routine2i.bornes`),
on releve CHAQUE cible d'appel, et on regarde si la chaine la connait -- c'est-a-dire si son
adresse apparait quelque part dans les sources de la chaine. C'est un crible grossier mais
honnete : une adresse qu'aucun de nos fichiers ne nomme n'a ete lue par personne.

Puis, comme pour NG, on separe ce qui ALLOUE un work de ce qui n'alloue rien.

    py -3 inventaire_2i.py
    py -3 inventaire_2i.py --detail
"""
import glob
import io
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ICI = os.path.dirname(os.path.abspath(__file__))
ALLOUEUR_2I = 0x8C09AFA4        # le meme dans les deux binaires (memes octets)

NOMS = {0: "GILL", 1: "ALEX", 2: "RYU", 3: "YUN", 4: "DUDLEY", 5: "NECRO", 6: "HUGO",
        7: "IBUKI", 8: "ELENA pont", 9: "ELENA", 10: "ORO", 11: "YANG", 12: "KEN",
        13: "SEAN", 14: "URIEN", 15: "AKUMA"}


def sources():
    """Le texte de toute la chaine, pour savoir quelles adresses sont deja nommees."""
    t = []

    for c in glob.glob(os.path.join(ICI, "*.py")):
        if os.path.basename(c).startswith("inventaire"):
            continue

        t.append(io.open(c, encoding="utf-8", errors="replace").read().upper())

    return "\n".join(t)


# LES ROUTINES D'ETAGE SE BRANCHENT SUR ELLES-MEMES -- et un `bsr` interne n'est pas un
# appel a decoder. La premiere version comptait les deux, annoncait 350 appels et 22 % de
# connus : un controle qui ment. Les seize routines vivent dans cette plage, on l'exclut.
ZONE_ETAGES = (0x8C0DB938, 0x8C0DF0C8)


def appels(deb, fin, D, BASE):
    """Les cibles d'appel EXTERIEURES de la plage."""
    out = set()

    for off in range(deb - BASE, min(fin - BASE, len(D) - 2), 2):
        w = struct.unpack_from("<H", D, off)[0]
        pc = off + BASE

        # mov.l @(disp,PC),rN : un pool qui porte du code est une cible d'appel probable
        if (w >> 12) == 0xD:
            tgt = ((pc + 4) & ~3) + (w & 0xFF) * 4

            if BASE <= tgt < BASE + len(D) - 4:
                v = struct.unpack_from("<I", D, tgt - BASE)[0]

                if (0x8C010000 <= v < 0x8C120000 and (v & 1) == 0
                        and not (ZONE_ETAGES[0] <= v < ZONE_ETAGES[1])):
                    out.add(v)

        # bsr disp
        elif (w >> 12) == 0xB:
            d = w & 0xFFF
            d = d - 0x1000 if d & 0x800 else d
            t = pc + 4 + d * 2

            if not (ZONE_ETAGES[0] <= t < ZONE_ETAGES[1]):
                out.add(t)

    return out


def alloue(a, D, BASE, portee=0x300):
    for off in range(a - BASE, min(a - BASE + portee, len(D) - 4), 2):
        w = struct.unpack_from("<H", D, off)[0]

        if (w >> 12) != 0xD:
            continue

        pc = off + BASE
        tgt = ((pc + 4) & ~3) + (w & 0xFF) * 4

        if BASE <= tgt < BASE + len(D) - 4:
            if struct.unpack_from("<I", D, tgt - BASE)[0] == ALLOUEUR_2I:
                return True

    return False


def main():
    import routine2i as R
    import sh4

    D, BASE = sh4.D, sh4.BASE
    src = sources()
    detail = "--detail" in sys.argv
    par_cible = {}

    print("%-4s %-11s %7s %6s   %s" % ("b.", "nom", "appels", "connus", "inconnus"))
    print("-" * 88)

    tot = con = 0

    for bande in range(16):
        b = R.bornes(bande)

        if not b:
            continue

        cibles = appels(b[0], b[1], D, BASE)
        inconnues = sorted(c for c in cibles if ("%08X" % c) not in src)
        tot += len(cibles)
        con += len(cibles) - len(inconnues)

        for c in inconnues:
            par_cible.setdefault(c, []).append(bande)

        print("%-4d %-11s %7d %6d   %s"
              % (bande, NOMS.get(bande, "?"), len(cibles), len(cibles) - len(inconnues),
                 " ".join("%08X" % c for c in inconnues)[:44]))

        if detail and inconnues:
            for c in inconnues:
                print("        %08X %s" % (c, "ALLOUE" if alloue(c, D, BASE) else "service"))

    print("-" * 88)
    print("APPELS DES ROUTINES D'ETAGE : %d connus sur %d  (%.0f %%)"
          % (con, tot, 100.0 * con / max(1, tot)))
    print()
    print("%d cibles distinctes inconnues :" % len(par_cible))

    creent = []

    for c in sorted(par_cible, key=lambda x: -len(par_cible[x])):
        a = alloue(c, D, BASE)
        print("   %08X  %d decors (%s)  %s"
              % (c, len(par_cible[c]),
                 ",".join(NOMS.get(b, "?")[:3] for b in par_cible[c])[:34],
                 "ALLOUE UN WORK" if a else "n'alloue rien"))

        if a:
            creent.append(c)

    print()
    print("A LIRE EN PRIORITE (elles creent quelque chose) : %s"
          % " ".join("%08X" % c for c in creent))
    return 0


if __name__ == "__main__":
    sys.exit(main())
