# -*- coding: utf-8 -*-
"""Rend un .pvc en PNG. Deux banques de 1024x1024, texture PVR entrelacee.
Usage : python rendupvc.py <fichier.pk> <taille du pvc> <prefixe de sortie>
"""
import sys, os, struct
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import pvc

SIDE = 1024

def carte_morton(side):
    """Rend un tableau (side,side) donnant l'indice entrelace de chaque (y,x). Y sur les bits pairs (entrelacement PVR)."""
    bits = side.bit_length()-1
    xs = np.arange(side, dtype=np.uint32)
    sx = np.zeros(side, dtype=np.uint32); sy = np.zeros(side, dtype=np.uint32)
    for k in range(bits):
        sy |= ((xs >> k) & 1) << (2*k)
        sx |= ((xs >> k) & 1) << (2*k+1)
    return sy[:, None] + sx[None, :]

def banque(pages, first, carte):
    plat = np.zeros(SIDE*SIDE, dtype=np.uint16)
    for p in range(SIDE*SIDE//256):
        px = pages[first+p]
        if px is not None:
            plat[p*256:(p+1)*256] = np.asarray(px, dtype=np.uint16)
    img = plat[carte]
    r = ((img >> 10) & 31).astype(np.uint16)*255//31
    g = ((img >>  5) & 31).astype(np.uint16)*255//31
    b = ( img        & 31).astype(np.uint16)*255//31
    return np.dstack([r, g, b]).astype(np.uint8)

def rendre(path, taille, prefixe):
    buf = open(path, 'rb').read()[:taille]
    pages, used, st = pvc.decode(buf)
    assert used == taille, f"consomme {used} au lieu de {taille}"
    carte = carte_morton(SIDE)
    sorties = []
    for i, first in enumerate((0, 4096)):
        arr = banque(pages, first, carte)
        out = f"{prefixe}-banque{i}.png"
        Image.fromarray(arr).save(out)
        sorties.append(out)
    return sorties, st

if __name__ == '__main__':
    outs, st = rendre(sys.argv[1], int(sys.argv[2]), sys.argv[3])
    print(st)
    for o in outs: print('ecrit', o)
