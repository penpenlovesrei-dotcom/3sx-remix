# -*- coding: utf-8 -*-
"""Rend une planche de sprites assembles pour chaque decor de 2nd Impact."""
import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bases
from planche import planche

ICI = os.path.dirname(os.path.abspath(__file__))
SPR = os.path.join(ICI, '..', 'sprites')
OUT = os.path.join(ICI, '..', 'rendus', 'sprites')
os.makedirs(OUT, exist_ok=True)

for dec, fichier in sorted(bases.ASSETS.items()):
    b = bases.BASES_2I[dec]
    for chemin in sorted(glob.glob(os.path.join(SPR, '2i-b%s-*.bin' % dec[2:]))):
        nom = os.path.basename(chemin)[:-4]
        planche(chemin, '2i', b[1], os.path.join(OUT, nom + '.png'),
                bases=b, nb=48, cols=8, ech=2)
