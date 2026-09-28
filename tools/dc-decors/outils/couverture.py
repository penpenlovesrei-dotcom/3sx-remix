# -*- coding: utf-8 -*-
"""Combien de la zone jouee resterait noire, decor par decor, sous un masque emprunte.

L'etage 22 emprunte le fichier de textures d'un autre etage, donc son masque de pages
`bgtex_stage_gbix`. Un decor de 2nd Impact n'y entre que si ses pixels tombent sur des
pages que le masque fournit. Ce fichier le mesure : pour chaque decor, la part de la
**zone jouee** -- les rangees 2 et 3, `y = 768..1023` -- qui resterait noire une fois les
deux plans empiles.

    python couverture.py              # sous le masque de Necro (etage 5), celui de l'etage 22
    python couverture.py 0xFFFFFFFF 0xFFFFFFFF   # sous un masque plein, pour comparer
"""
import glob, os, sys
import numpy as np
import pvc
from rendupvc import carte_morton, SIDE
from bande3sx import banque_rgba, RACINE

NECRO = (0x7E7E7E7E, 0x424FEFFF)


def couverture(decor, masques, carte):
    src = os.path.join(RACINE, "pvc-2i", decor + ".pvc")
    buf = open(src, "rb").read()
    pages, used, _ = pvc.decode(buf)
    if used != len(buf):
        return None
    arr, _ = banque_rgba(pages, 0, carte)
    vu = np.zeros((256, 1024), dtype=bool)          # rangees 2 et 3 du plan
    for (gbix, moitie) in zip(masques, ("haut", "bas")):
        dy = 0 if moitie == "haut" else 512
        for i in range(16, 32):                      # rangees 2 et 3
            if not (gbix & (0x80000000 >> i)):
                continue
            r, c = (i >> 3) - 2, i & 7
            a = arr[dy + (i >> 3)*128: dy + (i >> 3)*128 + 128, c*128: c*128 + 128, 3]
            vu[r*128:(r+1)*128, c*128:(c+1)*128] |= a > 0
    return 1.0 - vu.mean()


def main():
    masques = NECRO if len(sys.argv) < 3 else (int(sys.argv[1], 0), int(sys.argv[2], 0))
    carte = carte_morton(SIDE)
    res = []
    for p in sorted(glob.glob(os.path.join(RACINE, "pvc-2i", "bg??.pvc"))):
        d = os.path.basename(p)[:-4]
        try:
            t = couverture(d, masques, carte)
        except Exception as e:
            t = None
        if t is not None:
            res.append((t, d))
    print(f"masque {masques[0]:#010x} / {masques[1]:#010x}   -- part NOIRE de la zone jouee")
    for t, d in sorted(res):
        barre = "#" * int(60 * (1 - t))
        print(f"   {d}  {100*t:5.1f} % noir   |{barre:<60s}|")


if __name__ == "__main__":
    main()
