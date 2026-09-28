# -*- coding: utf-8 -*-
"""Rattache chaque decor a sa plage de palettes dans la banque de l'executable.

Le test est objectif et ne regarde aucune image : on compte, pour chaque palette de
la banque, la proportion de ses 64 couleurs qui apparaissent **exactement** (valeur
ARGB1555 identique) dans le decor. Les palettes d'un decor sortent a ~100 % contre
8 % de moyenne, et elles forment une plage contigue.

Ce qui est mesure : la plage par decor.
Ce qui ne l'est pas : laquelle de ces palettes va avec quel sprite. L'index vient du
code et n'est reference par adresse nulle part dans le binaire.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import pvc

BANQUES = {'2i': ('SF3_2ND.BIN', 0x1D9AEC, 2715), 'ng': ('SF3_1ST.BIN', 0x1A8188, 2661)}

def banque(chemin, offset, n):
    d = open(chemin, 'rb').read()
    return np.frombuffer(d[offset:offset + n*128], dtype='<u2').reshape(n, 64)

def couleurs_decor(chemin_pvc):
    pages, _, _ = pvc.decode(open(chemin_pvc, 'rb').read())
    s = set()
    for p in pages:
        if p:
            s.update(p)
    return s

def plage(P, couleurs, seuil=0.80, mini_distinct=24):
    """Rend (lo, hi, indices) des palettes couvertes par le decor."""
    distinct = np.array([len(set(p.tolist())) for p in P])
    cov = np.array([[c in couleurs for c in pal] for pal in P]).mean(axis=1)
    idx = [i for i in range(len(P)) if distinct[i] >= mini_distinct and cov[i] >= seuil]
    return (min(idx), max(idx), idx) if idx else (None, None, [])
