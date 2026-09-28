# -*- coding: utf-8 -*-
"""Pose les objets ANIMES candidats d'un decor sur sa banque, pour que l'oeil tranche.

L'epreuve du binaire dit si un enregistrement se resout ; elle ne dit pas s'il appartient
au decor. Ce qui le dit, c'est OU il tombe : un objet du decor se pose sur le sol, sur la
plate-forme, dans l'arbre -- un intrus tombe dans le vide ou sur un combattant.

On ne cuit rien : on peint sur une COPIE de la banque nue, et on ecrit un PNG.

    python planche_animes.py                       la region d'Oro, bloc par bloc
    python planche_animes.py 0x8C17E918 8          un bloc precis
"""
import os
import struct
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

# Les blocs de la sixieme table qui tombent dans la region d'Oro, plus le sien.
BLOCS = [(0x8C17E7A8, 6), (0x8C17E808, 2), (0x8C17E828, 1), (0x8C17E838, 10),
         (0x8C17E8D8, 3), (0x8C17E908, 1), (0x8C17E918, 8), (0x8C17E998, 1),
         (0x8C17E9A8, 2)]


def poser_objet(bg, decor, e):
    """(rgba, bx, by, sprite) de l'image 0 de l'objet, ou None."""
    r = AA.resout(decor, e)

    if r is None:
        return None

    g, n = r
    a, tuiles = P.asset(bases.ASSETS[bg])
    lo = a["index_global"][0]
    rec = a["anims"][g - lo]
    sp = a["sprites"][n]
    b = bases.BASES_2I[bg]
    pose = A.poser_couleur(sp, tuiles, P.banque_des_palettes(), b[min(b)], b)

    if pose is None:
        return None

    rgba, x0, y0 = pose
    bx = (e["x"] + rec[1] + x0) & 0x3FF
    by = (P.sol(bg) - e["y"] + rec[2] + y0) & 0x3FF
    return rgba, bx, by, n


def main():
    args = [a for a in sys.argv[1:]]

    if len(args) >= 2:
        blocs = [(int(args[0], 0), int(args[1]))]
    else:
        blocs = BLOCS

    os.makedirs(SORTIE, exist_ok=True)
    fond = P.banque_nue(BG)
    plan = fond.copy()
    img = Image.fromarray(plan, "RGBA")
    dess = ImageDraw.Draw(img)
    print("sol de %s : %d" % (BG, P.sol(BG)))

    for deb, nb in blocs:
        for k in range(nb):
            e = AA.lire(deb + k * 16)
            r = poser_objet(BG, DECOR, e)

            if r is None:
                print("  %08X  script %2d  NE RESOUT PAS" % (e["adresse"], e["script"]))
                continue

            rgba, bx, by, n = r
            h, w = rgba.shape[:2]
            calque = Image.fromarray(rgba, "RGBA")
            img.alpha_composite(calque, (bx, by))
            dess.rectangle([bx, by, bx + w - 1, by + h - 1], outline=(255, 0, 255, 255))
            dess.text((bx + 1, by - 10), "%03X/s%d" % (e["adresse"] & 0xFFF, e["script"]),
                      fill=(255, 255, 0, 255))
            print("  %08X  plan %d  x %5d  y %3d  script %2d  sprite %3d  ->  banque %4d,%4d  %dx%d"
                  % (e["adresse"], e["plan"], e["x"], e["y"], e["script"], n, bx, by, w, h))

    chemin = os.path.join(SORTIE, "oro-animes.png")
    img.save(chemin)
    print("\n%s" % chemin)


if __name__ == "__main__":
    main()
