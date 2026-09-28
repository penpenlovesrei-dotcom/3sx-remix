# -*- coding: utf-8 -*-
"""Toutes les images d'un objet anime, en couleur, sur une planche. Pour identifier.

    python images_animes.py 0x8C17E918 8      un bloc d'enregistrements
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw

import annuaire_animes as AA
import assemblage as A
import bases
import poser2i as P
import sh4

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(RACINE, "rendus")

DECOR = 9
BG = "bg0a"
CASE = 128


def images(bg, decor, e):
    """[(rgba, sprite)] de toutes les images du script de l'enregistrement."""
    ims = AA.script_images(decor, e["script"]) or []
    a, tuiles = P.asset(bases.ASSETS[bg])
    lo = a["index_global"][0]
    offs = sorted({r[4] for r in a["anims"]})
    b = bases.BASES_2I[bg]
    out = []

    for g, _duree in ims:
        if not lo <= g < lo + len(a["anims"]):
            continue

        rec = a["anims"][g - lo]
        n = offs.index(rec[4])
        pose = A.poser_couleur(a["sprites"][n], tuiles, P.banque_des_palettes(),
                               b[min(b)], b)

        if pose is None:
            continue

        out.append((pose[0], n))

    return out


def main():
    deb, nb = int(sys.argv[1], 0), int(sys.argv[2])
    lignes = []

    for k in range(nb):
        e = AA.lire(deb + k * 16)
        lignes.append((e, images(BG, DECOR, e)))

    larg = max(len(l[1]) for l in lignes)
    img = Image.new("RGBA", (CASE * larg, CASE * len(lignes)), (32, 32, 40, 255))
    dess = ImageDraw.Draw(img)

    for j, (e, ims) in enumerate(lignes):
        for i, (rgba, n) in enumerate(ims):
            h, w = rgba.shape[:2]
            c = Image.fromarray(rgba, "RGBA")
            img.alpha_composite(c, (i * CASE + max(0, (CASE - w) // 2),
                                    j * CASE + max(0, (CASE - h) // 2)))
            dess.text((i * CASE + 2, j * CASE + 2), "sp%d" % n, fill=(255, 255, 0, 255))

        dess.text((2, j * CASE + CASE - 12),
                  "%03X s%d x%d y%d" % (e["adresse"] & 0xFFF, e["script"], e["x"], e["y"]),
                  fill=(0, 255, 255, 255))

    chemin = os.path.join(SORTIE, "oro-images-%03X.png" % (deb & 0xFFF))
    img.save(chemin)
    print(chemin)


if __name__ == "__main__":
    main()
