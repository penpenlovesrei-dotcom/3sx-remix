# -*- coding: utf-8 -*-
"""RELEVE MECANIQUE D'UN ENGENDREUR D'OBJET DE DECOR -- 29/09/2026.

Frederic : « *je me tue a te demander de decompiler TOUT ce qui touche aux decors* ». Le
defaut n'etait pas le courage, c'etait la methode : chaque engendreur etait desassemble a la
main, ce qui coute une demi-heure et ne passe pas a l'echelle de cent vingt appels.

Un engendreur a pourtant toujours la meme forme, et elle se releve toute seule :

    jsr 0x8C09AFA4 ; mov #genre,r4     alloue un work
    exts.w r4,rN ; shll8 ; shll2 ; shll  rN = index * 1024
    add rPool,rN                       rN = &work (table 0x8C554668)
    ... puis une suite d'ecritures `mov.b/mov.w/mov.l rS,@(offset, rN)`

Il suffit donc de suivre le registre qui porte le work et de relever chaque ecriture avec la
valeur du registre source, quand celle-ci vient d'un immediat (`mov #n,rS`), d'un mot de pool
(`mov.w 0x...,rS`) ou d'un long de pool (`mov.l 0x...,rS`). Les champs sont connus :

    +1   disp_flag (0 = l'objet nait INVISIBLE)      +364  la table de scripts
    +8   l'id                                        +456  le script
    +10  le miroir                                   +554  `col`
    +84  x & 1023        +102  x                     +556  la profondeur
    +86  y & 1023        +106  y                     +558  le plan
    +88  la palette                                  +812  le parent

    py -3 lire_engendreur.py 8C0A03CC 8C0A83E4 ...
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

CHAMPS = {1: "disp_flag", 4: "argument", 6: "+6", 8: "id", 10: "miroir", 32: "+32",
          36: "etat", 38: "sous-etat", 52: "+52", 54: "+54", 56: "+56", 68: "+68",
          72: "+72", 84: "x & 1023", 86: "y & 1023", 88: "palette", 100: "x (16.16 bas)",
          102: "x", 104: "y (16.16)", 106: "y", 118: "+118", 124: "vitesse x",
          128: "vitesse y", 132: "accel. x", 136: "accel. y", 148: "+148", 156: "+156",
          160: "+160", 162: "+162", 164: "+164", 364: "table de scripts", 456: "script",
          468: "drapeau du pas", 552: "+552", 554: "col", 556: "profondeur",
          558: "plan", 812: "parent"}


def s16(v):
    return v - 0x10000 if v & 0x8000 else v


def relever(a, D, BASE, portee=0x400, bavard=False):
    """[(offset du champ, valeur, comment)] -- les ecritures immediates de l'engendreur."""
    regs = {}                     # registre -> valeur connue
    work = None                   # le registre qui porte le work
    r0 = None
    out = []

    for off in range(a - BASE, min(a - BASE + portee, len(D) - 2), 2):
        w = struct.unpack_from("<H", D, off)[0]
        pc = off + BASE

        # mov #imm,rN
        if (w & 0xF000) == 0xE000:
            regs[(w >> 8) & 0xF] = w & 0xFF

            if ((w >> 8) & 0xF) == 0:
                r0 = w & 0xFF

            continue

        # mov.w @(disp,PC),rN  /  mov.l @(disp,PC),rN
        if (w & 0xF000) in (0x9000, 0xD000):
            n = (w >> 8) & 0xF
            long_ = (w & 0xF000) == 0xD000
            tgt = (((pc + 4) & ~3) + (w & 0xFF) * 4) if long_ else (pc + 4 + (w & 0xFF) * 2)

            if BASE <= tgt < BASE + len(D) - 4:
                v = (struct.unpack_from("<I", D, tgt - BASE)[0] if long_
                     else struct.unpack_from("<H", D, tgt - BASE)[0])
                regs[n] = v

                if n == 0:
                    r0 = v

            continue

        # add rM,rN  : on suit la construction du pointeur de work
        if (w & 0xF00F) == 0x300C:
            n, m = (w >> 8) & 0xF, (w >> 4) & 0xF

            if regs.get(m) == 0x8C554668 or work == m:
                work = n

            continue

        # exts.w rM,rN  et shll : le work vient de l'index, on garde la trace du registre
        if (w & 0xF00F) == 0x600F:
            n, m = (w >> 8) & 0xF, (w >> 4) & 0xF

            if work == m:
                work = n

            continue

        if work is None:
            continue

        # mov.b/mov.w/mov.l rS,@(disp,rN)   -- disp court, champs 0..60
        if (w & 0xF000) == 0x8000 and ((w >> 8) & 0xF) in (0x0, 0x1):
            taille = 1 if ((w >> 8) & 0xF) == 0 else 2
            n = (w >> 4) & 0xF
            d = (w & 0xF) * taille

            if n == work:
                out.append((d, regs.get(0), "mov.%s r0" % ("b" if taille == 1 else "w")))

            continue

        # mov.b/mov.w/mov.l rS,@(r0,rN)     -- champ dans r0
        if (w & 0xF00F) in (0x0004, 0x0005, 0x0006):
            n, m = (w >> 8) & 0xF, (w >> 4) & 0xF
            t = {4: "b", 5: "w", 6: "l"}[w & 0xF]

            if n == work and r0 is not None:
                out.append((r0, regs.get(m), "mov.%s r%d" % (t, m)))

            continue

        # mov.w rS,@rN   (champ 0)
        if (w & 0xF00F) == 0x2001 and ((w >> 8) & 0xF) == work:
            out.append((0, regs.get((w >> 4) & 0xF), "mov.w"))

    return out


def main():
    import routineng as RN          # bascule sur SF3_1ST.BIN
    import sh4ng as N

    cibles = [int(x, 16) for x in sys.argv[1:] if not x.startswith("--")]

    if not cibles:
        print(__doc__)
        return 1

    for a in cibles:
        print("\n=== %08X ===" % a)
        vu = {}

        for d, v, c in relever(a, N.D, 0x8C010000):
            if v is None:
                continue

            vu.setdefault(d, v)

        for d in sorted(vu):
            nom = CHAMPS.get(d, "+%d" % d)
            v = vu[d]
            sup = ""

            if d in (102, 106, 84, 86) and v > 0x8000:
                sup = "  (%d signe)" % s16(v)

            if d in (364, 812) or v > 0x8C000000:
                sup = "  -> %08X" % v

            print("   [+%-3d] %-18s = %-10d 0x%X%s" % (d, nom, v, v, sup))

    return 0


if __name__ == "__main__":
    sys.exit(main())
