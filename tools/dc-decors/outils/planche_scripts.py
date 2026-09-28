# -*- coding: utf-8 -*-
"""UNE PLANCHE DE TOUS LES SCRIPTS D'UN DECOR — pour identifier ce qu'on pose, et ce qui manque.

POURQUOI CET OUTIL EXISTE
-------------------------
Frederic decrit ce qu'il voit -- « les 2 personnages devant le tram », « 3 jeunes punks »,
« le feu de signalisation orange » -- et la chaine, elle, ne connait que des NUMEROS de
script. Le seul moyen honnete de faire le lien est de REGARDER les sprites, au lieu de
deviner a partir des positions.

La planche rend la premiere image de chaque script du decor, avec son numero, son nombre
d'images et un marqueur si la chaine le pose deja. Ce qui manque saute alors aux yeux.

    python planche_scripts.py bg03 3        tous les scripts de Yun
    python planche_scripts.py bg04 4 --tous chaque script, meme ceux d'une seule image
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw

import animer2i as AM
import assemblage as A
import bases
import poser2i as P

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def rendre(a, tuiles, offs, banque, base0, resoudre, sc, decor, k=0):
    """La k-ieme image d'un script, en RGBA, ou None."""
    ims = AM.script_images(decor, sc)

    if not ims or k >= len(ims):
        return None

    lo, _hi = a["index_global"]
    idx = ims[k][0]

    if not lo <= idx < lo + len(a["anims"]):
        return None

    rec = a["anims"][idx - lo]
    n = offs.index(rec[4])
    r = A.poser_1555(a["sprites"][n], tuiles, banque, base0, resoudre)

    if r is None:
        return None

    img = r[0]
    h, w = img.shape
    out = np.zeros((h, w, 4), np.uint8)
    v = img.astype(np.uint32)
    out[..., 0] = ((v >> 10) & 31) * 255 // 31
    out[..., 1] = ((v >> 5) & 31) * 255 // 31
    out[..., 2] = (v & 31) * 255 // 31
    out[..., 3] = np.where(img != 0, 255, 0)
    return Image.fromarray(out, "RGBA")


def main():
    bg = sys.argv[1] if len(sys.argv) > 1 else "bg03"
    decor = int(sys.argv[2]) if len(sys.argv) > 2 else 3
    tous = "--tous" in sys.argv

    import annuaire2i as AN

    a, tuiles = P.asset(bases.ASSETS[bg])
    offs = sorted({r[4] for r in a["anims"]})
    banque = AM.banque_brute()
    base0 = bases.BASES_2I[bg][min(bases.BASES_2I[bg])]
    resoudre = lambda dr, off: bases.numero(bg, dr, off)

    _t, nb = AN.table_scripts(decor)
    poses = {o["script"] for o in AM.objets(bg)} if bg in AM.TABLES else set()

    vign = []
    for sc in range(nb):
        ims = AM.script_images(decor, sc)
        if not ims:
            continue
        if not tous and len(ims) < 2 and sc not in poses:
            continue
        im = rendre(a, tuiles, offs, banque, base0, resoudre, sc, decor)
        vign.append((sc, len(ims), sc in poses, im))

    if not vign:
        print("aucun script a rendre")
        return

    L = max((im.width for _s, _n, _p, im in vign if im), default=64)
    H = max((im.height for _s, _n, _p, im in vign if im), default=64)
    cols = 6
    lignes = (len(vign) + cols - 1) // cols
    CW, CH = L + 12, H + 28
    pl = Image.new("RGBA", (cols * CW, lignes * CH), (38, 38, 46, 255))
    d = ImageDraw.Draw(pl)

    for k, (sc, n, pose, im) in enumerate(vign):
        cx, cy = (k % cols) * CW, (k // cols) * CH
        if pose:
            d.rectangle([cx + 1, cy + 1, cx + CW - 3, cy + CH - 3], outline=(80, 200, 90, 255))
        if im:
            pl.alpha_composite(im, (cx + 6, cy + 22))
        d.text((cx + 5, cy + 5), "%d  (%d img)%s" % (sc, n, "  POSE" if pose else ""),
               fill=(160, 255, 170, 255) if pose else (255, 240, 170, 255))

    out = os.path.join(RACINE, "planche-scripts-%s.png" % bg)
    pl.save(out)
    print("ecrit %s   %dx%d, %d scripts" % (out, pl.size[0], pl.size[1], len(vign)))
    print()
    print("encadres en vert : deja poses par la chaine")


if __name__ == "__main__":
    main()
