# -*- coding: utf-8 -*-
"""Planches des sprites assembles d'un asset F_ETCnn.

    python planche.py ../sprites/2i-b00-F_ETC41.bin 2i 827 ../rendus/gill.png
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import assemblage, palettes

def planche(chemin, banque_courte, base, sortie, bases=None, debut=0, nb=48, cols=8, ech=2):
    r, tu = assemblage.charger(chemin)
    ex, off, n = palettes.BANQUES[banque_courte]
    ici = os.path.dirname(os.path.abspath(__file__))
    B = palettes.lire(os.path.join(ici, '..', ex), off, n)
    ims = []
    for sp in r['sprites'][debut:debut+nb]:
        p = assemblage.poser_couleur(sp, tu, B, base, bases)
        if p is not None and p[0].size:
            ims.append(p[0])
    if not ims:
        print('rien a rendre'); return
    cw = max(i.shape[1] for i in ims) + 4
    ch = max(i.shape[0] for i in ims) + 4
    rows = (len(ims) + cols - 1)//cols
    c = np.zeros((rows*ch, cols*cw, 4), np.uint8)
    c[..., :3] = 32; c[..., 3] = 255
    for k, im in enumerate(ims):
        a = (k//cols)*ch; b = (k % cols)*cw
        s = c[a:a+im.shape[0], b:b+im.shape[1]]
        m = im[..., 3] > 0
        s[m] = im[m]
    Image.fromarray(c).resize((c.shape[1]*ech, c.shape[0]*ech), Image.NEAREST).save(sortie)
    print('%s : %d sprites' % (sortie, len(ims)))

if __name__ == '__main__':
    planche(sys.argv[1], sys.argv[2], int(sys.argv[3]), sys.argv[4])
