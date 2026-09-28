# -*- coding: utf-8 -*-
"""Retrouve la palette d'un sprite a partir d'une capture d'ecran du jeu.

Methode validee deux fois (BONUS GAME -> 2317, feuillage de bg0b -> 1095).

L'emulateur etend les 5 bits de l'ARGB1555 par `(v << 3) | (v >> 2)`. Une capture
**a l'echelle native, sans lissage** porte donc les valeurs exactes : on les reconvertit
en 5 bits et on cherche la palette de la banque qui les contient, sans tolerance.

Les scanlines ne genent pas : elles assombrissent des lignes entieres, donc il reste
toujours des pixels a la vraie couleur. Un agrandissement bicubique, lui, est fatal.

    python depuiscapture.py capture.png 2i --vert
"""
import sys, os, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
import appariement as AP

INV = {(v << 3) | (v >> 2): v for v in range(32)}

def couleurs_capture(chemin, filtre=None, top=24):
    """Rend les couleurs ARGB1555 les plus frequentes de la capture.
    `filtre` : fonction (r,g,b) -> masque booleen, pour isoler l'element."""
    a = np.asarray(Image.open(chemin).convert('RGB')).astype(int)
    r, g, b = a[..., 0], a[..., 1], a[..., 2]
    m = filtre(r, g, b) if filtre else np.ones(r.shape, bool)
    cnt = collections.Counter()
    for (R, G, B), n in collections.Counter(map(tuple, a[m].tolist())).items():
        if R in INV and G in INV and B in INV:
            cnt[0x8000 | (INV[R] << 10) | (INV[G] << 5) | INV[B]] += n
    return [v for v, _ in cnt.most_common(top)]

def chercher(couleurs, court='2i'):
    """Classe les palettes de la banque par nombre de couleurs contenues exactement."""
    exe, off, n = AP.BANQUES[court]
    P = AP.banque(exe, off, n)
    ens = [set(p.tolist()) for p in P]
    return sorted(((sum(1 for v in couleurs if v in ens[i]), i) for i in range(len(P))), reverse=True)

# filtres tout prets
VERT = lambda r, g, b: (g >= r) & (g > 40)
VIF  = lambda r, g, b: (np.maximum(np.maximum(r, g), b) > 90)

if __name__ == '__main__':
    chemin = sys.argv[1]
    court = sys.argv[2] if len(sys.argv) > 2 else '2i'
    filtre = VERT if '--vert' in sys.argv else (VIF if '--vif' in sys.argv else None)
    cols = couleurs_capture(chemin, filtre)
    print(f'{len(cols)} couleurs retenues')
    for s, i in chercher(cols, court)[:8]:
        print(f'   palette {i:5d} : {s}/{len(cols)}')
