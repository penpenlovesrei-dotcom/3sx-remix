# -*- coding: utf-8 -*-
"""Les bandes de contenu d'un atlas .pvc.

Un plan de Dreamcast est une banque de 1024x1024 qui boucle. Les banques ne sont pas
pleines : le contenu s'y range en **bandes horizontales** separees par du vide, une par
plan de decor. Ce fichier les mesure -- ou commence et finit chaque bande, sur quelle
largeur -- sans rien supposer des enregistrements de dessin.

    python bandes.py            # les 21 decors de 2nd Impact
    python bandes.py ng         # ceux de New Generation
"""
import glob, os, sys
import numpy as np
from PIL import Image

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RENDUS = os.path.join(RACINE, "rendus")


def bandes(chemin, creux=8):
    """[(y0, y1, x0, x1, remplissage)] pour chaque bande separee par >= `creux` lignes vides."""
    a = np.asarray(Image.open(chemin).convert("RGB"))
    plein = a.sum(2) > 0
    lignes = plein.any(1)
    out = []
    y = 0
    n = len(lignes)
    while y < n:
        if not lignes[y]:
            y += 1
            continue
        y0 = y
        vide = 0
        while y < n and vide < creux:
            vide = vide + 1 if not lignes[y] else 0
            y += 1
        y1 = y - vide
        bloc = plein[y0:y1]
        cols = bloc.any(0).nonzero()[0]
        out.append((y0, y1, int(cols[0]), int(cols[-1]) + 1, float(bloc.mean())))
    return out


def main():
    jeu = "ng" if "ng" in sys.argv[1:] else "2i"
    fichiers = sorted(glob.glob(os.path.join(RENDUS, f"{jeu}-b*-banque*.png")))
    for f in fichiers:
        b = bandes(f)
        if not b:
            print(f"{os.path.basename(f):26s} vide")
            continue
        print(f"{os.path.basename(f):26s} {len(b)} bande(s)")
        for y0, y1, x0, x1, r in b:
            print(f"     y {y0:4d}..{y1:4d} ({y1-y0:4d} px)   x {x0:4d}..{x1:4d}"
                  f" ({x1-x0:4d} px)   rempli a {100*r:5.1f} %")


if __name__ == "__main__":
    main()
