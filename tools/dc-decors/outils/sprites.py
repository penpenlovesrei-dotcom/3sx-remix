# -*- coding: utf-8 -*-
"""Sort les tuiles de sprite d'un asset F_ETCnn en PNG (valeurs d'index, en gris).

Usage : python sprites.py sprites/2i-b0e-F_ETC94.bin rendus/prefixe
Un bloc = 4096 octets = 16 tuiles de 16x16 en 8 bits, lues ligne par ligne.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import fetc, degonfle

def tuiles(chemin):
    """Rend la liste des tuiles 16x16 (tableaux numpy) d'un asset."""
    d = open(chemin, 'rb').read()
    r = fetc.lire(d)
    nb = len(r['blocs'])
    out = []
    for k, b in enumerate(r['blocs']):
        octets, _ = degonfle.degonfler(b, souple=(k == nb-1))
        a = np.frombuffer(octets, dtype=np.uint8)
        for t in range(16):
            out.append(a[t*256:(t+1)*256].reshape(16, 16))
    return out

if __name__ == '__main__':
    chemin, prefixe = sys.argv[1], sys.argv[2]
    ts = tuiles(chemin)
    cols = 16
    rows = (len(ts) + cols - 1) // cols
    img = np.zeros((rows*16, cols*16), dtype=np.uint8)
    for i, t in enumerate(ts):
        img[(i//cols)*16:(i//cols)*16+16, (i % cols)*16:(i % cols)*16+16] = t
    Image.fromarray((img.astype(np.uint16)*255//63).clip(0, 255).astype(np.uint8)).save(prefixe + '.png')
    print(f'{len(ts)} tuiles -> {prefixe}.png')
