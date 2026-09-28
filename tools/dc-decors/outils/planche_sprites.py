# -*- coding: utf-8 -*-
"""Tous les sprites d'un asset sur des planches, pour les reconnaitre a l'oeil.

En COULEUR avec la base connue, et rien d'autre : on cherche une forme, pas une teinte.

    python planche_sprites.py            l'asset d'Oro, par planches de 96
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw

import assemblage as A
import bases
import poser2i as P

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(RACINE, "rendus")

BG = "bg0a"
CASE = 128
COLS = 12
PAR_PLANCHE = 96


def main():
    a, tuiles = P.asset(bases.ASSETS[BG])
    b = bases.BASES_2I[BG]
    os.makedirs(SORTIE, exist_ok=True)
    n = len(a["sprites"])

    for p0 in range(0, n, PAR_PLANCHE):
        lot = range(p0, min(p0 + PAR_PLANCHE, n))
        ligs = (len(lot) + COLS - 1) // COLS
        img = Image.new("RGBA", (CASE * COLS, CASE * ligs), (28, 28, 34, 255))
        dess = ImageDraw.Draw(img)

        for k, i in enumerate(lot):
            pose = A.poser_couleur(a["sprites"][i], tuiles, P.banque_des_palettes(),
                                   b[min(b)], b)
            cx, cy = (k % COLS) * CASE, (k // COLS) * CASE

            if pose is not None:
                rgba = pose[0][:CASE, :CASE]
                h, w = rgba.shape[:2]
                img.alpha_composite(Image.fromarray(rgba, "RGBA"),
                                    (cx + (CASE - w) // 2, cy + (CASE - h) // 2))

            dess.text((cx + 2, cy + 2), str(i), fill=(255, 255, 0, 255))

        chemin = os.path.join(SORTIE, "oro-sprites-%03d.png" % p0)
        img.save(chemin)
        print(chemin)


if __name__ == "__main__":
    main()
