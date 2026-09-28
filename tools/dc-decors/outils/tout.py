# -*- coding: utf-8 -*-
"""Rend tous les decors des deux jeux depuis pvc-ng/ et pvc-2i/, plus une planche-contact."""
import sys, os, glob
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from PIL import Image, ImageDraw
import rendupvc, pvc

RAC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(RAC, 'rendus')
os.makedirs(SORTIE, exist_ok=True)
carte = rendupvc.carte_morton(rendupvc.SIDE)

vignettes = []
for court in ('ng', '2i'):
    for f in sorted(glob.glob(os.path.join(RAC, f'pvc-{court}', '*.pvc'))):
        nom = os.path.basename(f)[:-4]
        pages, used, st = pvc.decode(open(f, 'rb').read())
        for i, first in enumerate((0, 4096)):
            im = Image.fromarray(rendupvc.banque(pages, first, carte))
            im.save(os.path.join(SORTIE, f'{court}-{nom}-banque{i}.png'))
            if im.getbbox():
                vignettes.append((f'{court} {nom} b{i}', im.resize((256, 256), Image.LANCZOS)))
        print(f'  {court}/{nom}', flush=True)

cols = 8
rows = (len(vignettes) + cols - 1) // cols
pl = Image.new('RGB', (cols*256, rows*272), (18, 18, 18))
d = ImageDraw.Draw(pl)
for k, (t, im) in enumerate(vignettes):
    x = (k % cols)*256; y = (k // cols)*272
    pl.paste(im, (x, y+16)); d.text((x+4, y+3), t, fill=(210, 210, 210))
pl.save(os.path.join(SORTIE, 'planche.png'))
print('planche :', len(vignettes), 'vignettes')
