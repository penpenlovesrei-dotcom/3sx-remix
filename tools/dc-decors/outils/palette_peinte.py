# -*- coding: utf-8 -*-
"""Identifie un sprite peint dans une page SANS connaitre sa palette, et la deduit.

`peints.py` compare des couleurs ; il ne trouve donc que ce dont la base de palette est
deja juste. Or celle d'Oro n'est etablie que pour le groupe de drapeaux 1 -- il en a un
second, le groupe 9, vingt-quatre morceaux, dont la base n'est nulle part. Et le piege
n. 7 de `SANS-ETAT.md` dit quoi faire : **chercher la palette validee dans la banque**.

Ici on ne suppose rien du tout. On pose l'image d'INDEX du sprite sur la page et on
demande si la page en est un recoloriage COHERENT :

  * les pixels opaques du sprite doivent l'etre dans la page -- pas l'inverse : la page
    est PLEINE, le sprite est decoupe ;
  * un meme index doit y donner partout la MEME couleur -- c'est ca, la preuve : un fond
    de grotte quelconque ne verifie pas une application ;
  * et deux index distincts doivent donner deux couleurs DISTINCTES, sinon un aplat
    passerait le test sans rien prouver ;
  * il faut assez d'index distincts pour que ce ne soit pas un hasard.

La palette lue se retrouve ensuite dans la banque du binaire, et son numero moins
l'offset du morceau donne LA BASE.

    python palette_peinte.py chats
    python palette_peinte.py perroquet
    python palette_peinte.py 380 450 880 935 196     une fenetre a la main
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import assemblage as A
import bases
import palettes
import poser2i as P
import situer_animes as S

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

BG = "bg0a"
ETAGE = 31
MINI_INDEX = 5          # moins de cinq index distincts, l'application ne prouve rien
MINI_PIXELS = 40

# Les deux figures qu'on cherche, reperees a l'oeil dans les pages cuites : leur boite,
# large, dans la liste ou elles sont peintes.
FENETRES = {
    "chats":     (370, 450, 880, 935, 196),
    "perroquet": (620, 700, 860, 915, 196),
    "chien":     (690, 800, 930, 985, 196),
}


def codes(page):
    """La page en couleurs codees sur un entier, transparent = -1."""
    c = (page[:, :, 0].astype(np.int64) << 16 | page[:, :, 1].astype(np.int64) << 8
         | page[:, :, 2].astype(np.int64))
    c[page[:, :, 3] == 0] = -1
    return c


def accord(idx, col, distinctes=False):
    """Combien de pixels suivent l'application index -> couleur la plus repandue.

    C'est la mesure, et elle se calcule d'un trait : on compte les couples (index,
    couleur), puis on garde pour chaque index le couple le plus frequent. Un sprite pose
    a sa vraie place rend 100 %.

    **MAIS UN APLAT LE REND AUSSI**, et c'est le piege : sur une plage d'une seule
    couleur, tous les index tombent sur cette couleur-la, l'application existe, et
    l'accord vaut 100 % sans rien prouver. Une premiere version sans ce garde-fou a
    « trouve » cent quarante sprites d'Oro peints dans ses pages, presque tous cales sur
    une ligne vide. Le nombre de COULEURS DISTINCTES est ce qui separe les deux : un vrai
    sprite en montre presque autant que d'index.

    `distinctes` rend le couple (pixels, couleurs distinctes) au lieu du seul compte.
    """
    cle = idx.astype(np.int64) << 32 | (col & 0xFFFFFF)
    _u, cpt = np.unique(cle, return_counts=True)
    par = np.zeros(64, np.int64)
    np.maximum.at(par, (_u >> 32).astype(np.int64), cpt)

    if not distinctes:
        return int(par.sum())

    garde = _u[np.isin(cpt, par[(_u >> 32).astype(np.int64)])]
    return int(par.sum()), int(len(np.unique(garde & 0xFFFFFF)))


def lire_palette(img, msk, sub):
    """(index distincts, palette lue) une fois l'accord parfait etabli.

    On ne re-teste rien ici : `accord` a deja dit que l'application existe. Deux index
    PEUVENT porter la meme couleur -- une palette a le droit de repeter une teinte -- donc
    on ne demande pas l'injectivite, qui rejetait la bonne reponse.
    """
    pal = np.full((64, 3), -1, np.int16)

    for v in np.unique(img[msk]):
        c = sub[:, :, :3][msk & (img == v)]
        pal[v] = c[0]

    return int((pal[:, 0] >= 0).sum()), pal


def dans_la_banque(pal):
    """[numeros] de la banque dont les couleurs coincident sur tous les index lus."""
    b = P.banque_des_palettes()
    vus = pal[:, 0] >= 0
    ok = (b[:, vus, :] == pal[vus]).all(2).all(1)
    return list(np.nonzero(ok)[0])


def main():
    args = sys.argv[1:]

    if args and args[0] in FENETRES:
        x0, x1, y0, y1, liste = FENETRES[args[0]]
    else:
        x0, x1, y0, y1, liste = (int(v) for v in args[:5])

    a, tuiles = P.asset(bases.ASSETS[BG])
    src = os.path.join(RACINE, "etages2i-sprites", "stage%d" % ETAGE)
    page = P.lire_liste(src, liste)
    col = codes(page)
    print("fenetre x %d..%d  y %d..%d  liste %d (%s)"
          % (x0, x1, y0, y1, liste, S.NOM[liste]))

    classement = []

    for n, sp in enumerate(a["sprites"]):
        pose = A.poser(sp, tuiles)

        if pose is None:
            continue

        img, msk, _sx, _sy = pose
        h, w = img.shape
        px = int(msk.sum())

        if h > 128 or w > 128 or px < MINI_PIXELS:
            continue

        idx = img[msk]
        best = (0, 0, 0)

        for by in range(y0, y1):
            for bx in range(x0, x1):
                if bx + w > 1024 or by + h > 1024:
                    continue

                sous = col[by:by + h, bx:bx + w][msk]

                if (sous < 0).any():
                    continue

                s = accord(idx, sous)

                if s > best[0]:
                    best = (s, bx, by)

        if best[0]:
            classement.append((best[0] / px, best[0], px, n, best[1], best[2]))

    classement.sort(reverse=True)

    for part, s, px, n, bx, by in classement[:8]:
        print("  sprite %3d  %4d px  accord %d/%d = %.3f  en %4d,%-4d"
              % (n, px, s, px, part, bx, by))

        if part < 0.999:
            continue

        img, msk, _sx, _sy = A.poser(a["sprites"][n], tuiles)
        h, w = img.shape
        nid, pal = lire_palette(img, msk, page[by:by + h, bx:bx + w])

        if nid < MINI_INDEX:
            continue

        nums = dans_la_banque(pal)
        offs = sorted({(m["drapeaux"], m["palette"])
                       for m in A.morceaux(a["sprites"][n])})
        print("      %d index lus, morceaux (drapeaux, offset) : %s" % (nid, offs))
        print("      palettes de la banque : %s"
              % (nums if len(nums) < 12 else "%d candidates" % len(nums)))

        for num in nums[:6]:
            for dr, off in offs:
                print("          si (drapeaux %d, offset %d) -> base %d"
                      % (dr, off, num - off))


if __name__ == "__main__":
    main()
