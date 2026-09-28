# -*- coding: utf-8 -*-
"""Quels sprites de l'asset d'un decor sont PEINTS dans ses pages, et ou.

C'est la piste retournee. Chercher un enregistrement puis regarder ou il tombe demande de
deviner d'abord quel bloc appartient au decor. On fait l'inverse : la page cuite montre
deja les chats et le perroquet d'Oro, a l'arret. Si un sprite de l'asset s'y retrouve
**pixel pour pixel**, on tient sa position vraie -- et de la, par le script qui l'emploie,
son enregistrement.

L'egalite est stricte : meme couleurs, memes pixels opaques. Une correlation ne suffirait
pas, un fond de grotte vert repond a tout.

    python peints.py                 tous les sprites d'Oro
    python peints.py 60 90           une tranche de numeros de sprite
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import assemblage as A
import bases
import poser2i as P
import situer_animes as S

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BG = "bg0a"
ETAGE = 31
SEUIL = 0.90
MINI = 24            # sous 24 pixels opaques, une egalite ne prouve rien


def main():
    a, tuiles = P.asset(bases.ASSETS[BG])
    offs = sorted({r[4] for r in a["anims"]})
    b = bases.BASES_2I[BG]
    # LES DEUX BANQUES, ET LA BANQUE DU DISQUE.
    #
    # Cette fonction a longtemps colorie avec `b[min(b)]` -- 1429, la banque de la grotte.
    # Les betes d'Oro en sortaient VERT FLUO, donc aucune ne pouvait coincider avec la
    # page, et l'outil concluait qu'aucune n'y etait peinte. C'etait l'outil qui avait
    # tort. `bases.numero` demele les deux banques.
    resoudre = lambda dr, off: bases.numero(BG, dr, off)
    pages = S.pages(True)

    deb = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    fin = int(sys.argv[2]) if len(sys.argv) > 2 else len(offs)
    print("%d sprites dans l'asset d'Oro, tranche %d..%d" % (len(offs), deb, fin))

    for n in range(deb, min(fin, len(offs))):
        pose = A.poser_couleur(a["sprites"][n], tuiles, P.banque_des_palettes(),
                               b[min(b)], resoudre)

        if pose is None:
            continue

        rgba = pose[0]

        if rgba.shape[0] > 256 or rgba.shape[1] > 256:
            continue

        for l in S.LISTES:
            s, bx, by, tot = S.chercher(rgba, pages[l])

            if tot >= MINI and s >= SEUIL * tot:
                print("  sprite %3d  %3dx%-3d  %4d px  ->  liste %d (%-14s) en %4d,%-4d"
                      "  %d/%d" % (n, rgba.shape[1], rgba.shape[0], tot, l, S.NOM[l],
                                   bx, by, s, tot))


if __name__ == "__main__":
    main()
