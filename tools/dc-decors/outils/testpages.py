# -*- coding: utf-8 -*-
"""Pages de test : une couleur unie et un numero par page, pour voir ou chaque page tombe.

Chaque page porte son **indice de bit** `i` (0..31), en gros, sur un fond dont la teinte
suit la colonne et la clarte la rangee. Une page qui n'apparait pas a l'ecran n'est pas
dans la fenetre visible ; une page qui apparait ailleurs qu'en
`x = (i & 7) * 128, y = 512 + (i >> 3) * 128` dit que la regle de placement est fausse.

    python testpages.py <dossier> [liste:gbix] [liste:gbix] ...
    python testpages.py ../test22plein 132:0xFFFFFFFF 196:0xFFFFFFFF
    python testpages.py ../test22uni  132:0xFFFFFFFF 196u:0xFFFFFFFF   # plan proche uni
"""
import os, struct, sys
import numpy as np
from PIL import Image, ImageDraw, ImageFont

MAGIC, VERSION = 0x58545333, 1
# Deux familles de couleurs, une par liste : sans ca, une page du plan lointain et
# celle du plan proche a la meme case ont la meme teinte, et on ne sait pas laquelle
# on regarde. Le plan lointain est gris-bleu et sombre, le plan proche est sature.
TEINTES = {
    132: [(150, 160, 170), (120, 135, 160), (100, 120, 150), (135, 145, 155),
          (110, 130, 165), (95, 110, 140), (125, 140, 170), (105, 125, 155)],
    196: [(230, 60, 60), (230, 140, 50), (225, 215, 60), (90, 200, 80),
          (70, 190, 200), (80, 110, 220), (160, 90, 210), (225, 100, 180)],
}


def page_unie(i, liste):
    """Rien qu'une couleur, sans un trait. Si un trou apparait quand meme, il ne vient
    pas de ce qu'on dessine."""
    col, rang = i & 7, i >> 3
    base = np.array(TEINTES.get(liste, TEINTES[196])[col], dtype=float) * (0.45 + 0.18 * rang)
    a = np.zeros((128, 128, 4), dtype=np.uint8)
    a[:, :, 0] = int(min(255, base[2]))       # rouge et bleu echanges, comme partout
    a[:, :, 1] = int(min(255, base[1]))
    a[:, :, 2] = int(min(255, base[0]))
    a[:, :, 3] = 255
    return a


def page(i, liste):
    col, rang = i & 7, i >> 3
    base = np.array(TEINTES.get(liste, TEINTES[196])[col], dtype=float) * (0.45 + 0.18 * rang)
    im = Image.new("RGBA", (128, 128), tuple(int(min(255, v)) for v in base) + (255,))
    d = ImageDraw.Draw(im)
    d.rectangle([0, 0, 127, 127], outline=(255, 255, 255, 255), width=2)
    try:
        f1 = ImageFont.truetype("arialbd.ttf", 54)
        f2 = ImageFont.truetype("arialbd.ttf", 20)
    except OSError:
        f1 = f2 = ImageFont.load_default()
    d.text((64, 54), str(i), fill=(255, 255, 255, 255), anchor="mm", font=f1)
    d.text((64, 100), f"L{liste} r{rang} c{col}", fill=(255, 255, 255, 255), anchor="mm", font=f2)
    # damier de 16 px dans le coin : un decalage de sous-page se voit tout de suite
    for k in range(4):
        if k % 2 == 0:
            d.rectangle([k*16, 0, k*16 + 15, 15], fill=(0, 0, 0, 255))
    a = np.asarray(im).copy()
    a[:, :, [0, 2]] = a[:, :, [2, 0]]        # rouge et bleu echanges, comme partout
    return a


def main():
    if len(sys.argv) < 3:
        print(__doc__); return
    sortie = sys.argv[1]
    os.makedirs(sortie, exist_ok=True)
    for a in sys.argv[2:]:
        liste, gbix = a.split(":")
        uni = liste.endswith("u")
        liste = int(liste.rstrip("u"), 0)
        gbix = int(gbix, 0)
        n = 0
        for i in range(32):
            if not (gbix & (0x80000000 >> i)):
                continue
            p = page_unie(i, liste) if uni else page(i, liste)
            with open(os.path.join(sortie, f"{liste}-{liste + i}.tex"), "wb") as f:
                f.write(struct.pack("<IIII", MAGIC, VERSION, 128, 128))
                f.write(p.tobytes())
            n += 1
        print(f"   liste {liste} : {n} pages{' (unies)' if uni else ''}")


if __name__ == "__main__":
    main()
