# -*- coding: utf-8 -*-
"""Planche de choix : les tuiles d'un asset F_ETCnn sous chaque palette de son decor.

Une ligne par palette candidate, son numero a gauche. Il n'y a plus qu'a lire.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw
import appariement as AP, sprites as SP

def planche(asset, decor, court='2i', sortie=None, ntuiles=24, zoom=3):
    exe, off, n = AP.BANQUES[court]
    P = AP.banque(exe, off, n)
    RGB = np.dstack([((P >> 10) & 31)*255//31, ((P >> 5) & 31)*255//31, (P & 31)*255//31]).astype(np.uint8)
    lo, hi, idx = AP.plage(P, AP.couleurs_decor(f'pvc-{court}/{decor}'))
    if lo is None:
        return None, []
    ts = [t for t in SP.tuiles(f'sprites/{asset}') if len(np.unique(t)) >= 12][:ntuiles]
    if not ts:
        return None, []
    bande = np.concatenate(ts, axis=1)                     # 16 x (16*n)
    L, H = bande.shape[1]*zoom, 16*zoom
    marge = 64
    img = Image.new('RGB', (marge + L, len(idx)*(H+4)), (18, 18, 18))
    d = ImageDraw.Draw(img)
    for k, i in enumerate(idx):
        y = k*(H+4)
        im = Image.fromarray(RGB[i][bande]).resize((L, H), Image.NEAREST)
        img.paste(im, (marge, y))
        d.text((4, y + H//2 - 6), str(i), fill=(255, 230, 120))
    if sortie:
        img.save(sortie)
    return img, idx
