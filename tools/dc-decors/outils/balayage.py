# -*- coding: utf-8 -*-
"""Trouve TOUTES les palettes de sprite d'un decor, depuis une capture d'ecran.

Un asset F_ETCnn n'utilise pas une palette mais une **plage** : chaque figure a la
sienne. Ce balayage decoupe la capture en fenetres, et pour chacune :
  - ne garde que les couleurs **absentes du .pvc du decor** (donc appartenant a un
    sprite, pas au fond) ;
  - cherche la palette de la banque qui les contient exactement.

Les palettes de numero bas (< 500) sont en general celles des **combattants**, pas du
decor : elles sont signalees a part.
"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import appariement as AP

INV = {(v << 3) | (v >> 2): v for v in range(32)}

def balayer(capture, couleurs_decor, court='2i', fenetre=90, pas=45, mini=12, ncoul=16):
    exe, off, n = AP.BANQUES[court]
    P = AP.banque(exe, off, n)
    ens = [set(p.tolist()) for p in P]
    a = np.asarray(Image.open(capture).convert('RGB')).astype(int)
    h, w, _ = a.shape
    y0, y1 = int(h*0.20), int(h*0.88)      # bande de jeu, hors HUD
    trouve = collections.Counter()
    for y in range(y0, y1-fenetre, pas):
        for x in range(0, w-fenetre, pas):
            z = a[y:y+fenetre, x:x+fenetre]
            c = collections.Counter()
            for (r, g, b), m in collections.Counter(map(tuple, z.reshape(-1, 3).tolist())).items():
                if r in INV and g in INV and b in INV:
                    v = 0x8000 | (INV[r] << 10) | (INV[g] << 5) | INV[b]
                    if v not in couleurs_decor:
                        c[v] += m
            cols = [v for v, _ in c.most_common(ncoul)]
            if len(cols) < ncoul:
                continue
            best = max(((sum(1 for v in cols if v in ens[i]), i) for i in range(len(P))))
            if best[0] >= mini:
                trouve[best[1]] += 1
    return trouve
