# -*- coding: utf-8 -*-
"""Retrouve un objet anime DANS LES PAGES CUITES, et dit sur quel plan il tombe.

`situer_objets.py` repond a « ou est-il », par la formule ; celui-ci repond a « ou
est-il VRAIMENT », par la mesure -- quand le decor porte deja une copie de l'objet.

C'est le cas dans la grotte d'Oro : plusieurs objets animes sont AUSSI peints dans la
demi-banque, a l'arret. On cherche donc l'image 0 de chaque objet, en couleur, dans les
trois listes de l'etage, et l'egalite pixel a pixel tranche -- de la meme facon que
`situer_objets.py` identifie un sprite : ce n'est pas une correlation.

Ce que ca donne, et qui ne se devine pas :

  * la liste ou l'objet est peint est SON PLAN. Le champ `plan` de l'enregistrement ne
    suffit pas -- l'objet 0x8C17E988, le petit edifice de pierre, porte `plan 2` et se
    trouve peint dans la grotte du FOND ;
  * la position mesuree se compare a celle de la formule, et l'ecart se lit.

    python situer_animes.py 0x8C17E918 8
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import annuaire_animes as AA
import assemblage as A
import bases
import couches2i as C
import poser2i as P

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

DECOR = 9
BG = "bg0a"
ETAGE = 31
LISTES = (132, 196, 260)

# Ce que chaque liste porte, pour Oro. Voir `couches2i.py`.
NOM = {132: "couchant", 196: "grotte proche", 260: "grotte du fond"}


def pages(origine=True):
    """Les trois plans de l'etage, dans le repere du moteur.

    **`origine=True` rend la BANQUE DU DISQUE, pas les pages cuites**, et c'est la seule
    reference qui vaille pour une mesure : les pages cuites portent deja ce que nos outils
    y ont pose -- les chats de `poser2i.py` y sont, avec la palette du jour ou on les a
    cuits. Y lire une position ou une palette, ce serait se relire soi-meme.

    Les pages cuites restent utiles pour voir ce que le jeu affiche ; `origine=False`.
    """
    if not origine:
        src = os.path.join(RACINE, "etages2i-sprites", "stage%d" % ETAGE)
        return {l: P.lire_liste(src, l) for l in LISTES}

    return {l: C.demi_banque(BG, bq, moitie)
            for l, (bq, moitie, _o) in C.COUCHES[BG].items()}


def image0(bg, decor, e):
    """(rgba, sprite, ancre, x0, y0) de l'image 0 de l'objet, ou None."""
    ims = AA.script_images(decor, e["script"]) or []
    a, tuiles = P.asset(bases.ASSETS[bg])
    lo = a["index_global"][0]

    if not ims or not lo <= ims[0][0] < lo + len(a["anims"]):
        return None

    offs = sorted({r[4] for r in a["anims"]})
    rec = a["anims"][ims[0][0] - lo]
    n = offs.index(rec[4])
    b = bases.BASES_2I[bg]
    pose = A.poser_couleur(a["sprites"][n], tuiles, P.banque_des_palettes(),
                           b[min(b)], b)

    if pose is None:
        return None

    return pose[0], n, (rec[1], rec[2]), pose[1], pose[2]


def chercher(rgba, page):
    """(score, bx, by, total) de la meilleure pose de l'image dans une page 1024x1024.

    Un balayage complet coute 1024x1024 comparaisons de l'image entiere : des minutes en
    Python. On passe donc par une ANCRE : le pixel opaque dont la couleur est la plus
    RARE dans la page. Il ne laisse que quelques centaines de poses a verifier, et il ne
    peut rien manquer -- si l'objet est peint, son pixel d'ancre y est.
    """
    h, w = rgba.shape[:2]
    op = rgba[:, :, 3] > 0
    total = int(op.sum())

    if page is None or total == 0 or h > 1024 or w > 1024:
        return 0, 0, 0, total

    pc = (page[:, :, 0].astype(np.uint32) << 16 | page[:, :, 1].astype(np.uint32) << 8
          | page[:, :, 2].astype(np.uint32))
    pc[page[:, :, 3] == 0] = 0xFFFFFFFF
    sc = (rgba[:, :, 0].astype(np.uint32) << 16 | rgba[:, :, 1].astype(np.uint32) << 8
          | rgba[:, :, 2].astype(np.uint32))

    ys, xs = np.nonzero(op)
    combien = {}

    for c in np.unique(sc[op]):
        combien[int(c)] = int((pc == c).sum())

    if not combien or min(combien.values()) == 0:
        return 0, 0, 0, total

    rare = min(combien, key=combien.get)
    i = next(k for k in range(len(ys)) if int(sc[ys[k], xs[k]]) == rare)
    ay, ax = int(ys[i]), int(xs[i])
    best = (0, 0, 0)

    for py, px in zip(*np.nonzero(pc == rare)):
        by, bx = int(py) - ay, int(px) - ax

        if not (0 <= bx <= 1024 - w and 0 <= by <= 1024 - h):
            continue

        sub = page[by:by + h, bx:bx + w]
        eq = (sub[:, :, :3] == rgba[:, :, :3]).all(2) & op & (sub[:, :, 3] > 0)
        s = int(eq.sum())

        if s > best[0]:
            best = (s, bx, by)

    return best[0], best[1], best[2], total


def main():
    deb, nb = int(sys.argv[1], 0), int(sys.argv[2])
    src = os.path.join(RACINE, "etages2i-sprites", "stage%d" % ETAGE)
    pages = {l: P.lire_liste(src, l) for l in LISTES}
    sol = P.sol(BG)

    print("%-9s %-4s %-4s  %-14s %-14s %s"
          % ("adresse", "plan", "spr", "formule", "mesure", "liste"))

    for k in range(nb):
        e = AA.lire(deb + k * 16)
        r = image0(BG, DECOR, e)

        if r is None:
            print("%08X  NE RESOUT PAS" % e["adresse"])
            continue

        rgba, n, ancre, x0, y0 = r
        bx = (e["x"] + ancre[0] + x0) & 0x3FF
        by = (sol - e["y"] + ancre[1] + y0) & 0x3FF
        trouve = []

        for l in LISTES:
            s, mx, my, tot = chercher(rgba, pages[l])
            trouve.append((s / tot if tot else 0, l, mx, my, s, tot))

        trouve.sort(reverse=True)
        part, l, mx, my, s, tot = trouve[0]
        verdict = ("%4d,%-4d  liste %d (%s)  %d/%d"
                   % (mx, my, l, NOM[l], s, tot)) if part >= 0.75 else \
                  ("pas peint (meilleur %d/%d en %d)" % (s, tot, l))
        print("%08X  %-4d %-4d  %4d,%-4d      %s"
              % (e["adresse"], e["plan"], n, bx, by, verdict))

        if part >= 0.75:
            print("            ecart formule -> mesure : dx %+d  dy %+d"
                  % (mx - bx, my - by))


if __name__ == "__main__":
    main()
