# -*- coding: utf-8 -*-
"""Compare le manifeste de tex_remix avant / apres une partie.

Les pages apparues pendant la partie sont celles de l'ecran qu'on vient de visiter.
Rend la liste, et une planche des vignettes pour les identifier a l'oeil.

    python dumpdiff.py            compare avec manifest-avant.txt
    python dumpdiff.py --avant    prend l'instantane de depart
"""
import sys, os, collections
from PIL import Image, ImageDraw

DUMP = os.path.join(os.environ.get('APPDATA', ''), 'CrowdedStreet', '3SX',
                    'resources', 'tex_remix', 'dump')
MANIF = os.path.join(DUMP, 'manifest.txt')
AVANT = os.path.join(DUMP, 'manifest-avant.txt')

def lignes(p):
    if not os.path.exists(p):
        return []
    return [l.rstrip('\n') for l in open(p, encoding='utf-8', errors='replace') if l.strip()]

def cle(l):
    c = l.split()
    return (c[0], c[5], c[7])          # empreinte, page, liste

def main():
    if '--avant' in sys.argv:
        open(AVANT, 'w', encoding='utf-8').write('\n'.join(lignes(MANIF)) + '\n')
        print('instantane pris : %d pages' % len(lignes(MANIF)))
        return
    av = {cle(l) for l in lignes(AVANT)}
    neuf = [l for l in lignes(MANIF) if cle(l) not in av]
    print('%d pages nouvelles depuis l\'instantane' % len(neuf))
    if not neuf:
        print("Rien de neuf : l'ecran n'a pas ete visite, ou ses pages etaient deja dans le dump.")
        return
    g = collections.defaultdict(list)
    for l in neuf:
        c = l.split()
        g[(c[7], c[9])].append((int(c[5]), c[0], c[1]))
    print()
    for (li, en), v in sorted(g.items(), key=lambda t: (int(t[0][0]), int(t[0][1]))):
        print('  liste %-4s entree %-4s : %d pages  %s' % (li, en, len(v), v[0][2]))
    open(os.path.join(DUMP, 'nouvelles.txt'), 'w', encoding='utf-8').write('\n'.join(neuf) + '\n')
    # planche
    vign = []
    for (li, en), v in sorted(g.items(), key=lambda t: (int(t[0][0]), int(t[0][1]))):
        for pg, f, sz in sorted(v):
            p = os.path.join(DUMP, f + '.pgm')
            if os.path.exists(p):
                vign.append(('l%s e%s p%d' % (li, en, pg), Image.open(p).convert('L')))
    if vign:
        T = 200; cols = 8
        rows = (len(vign) + cols - 1)//cols
        c = Image.new('RGB', (cols*(T+4), rows*(T+16)), (18, 18, 22))
        d = ImageDraw.Draw(c)
        for i, (nom, im) in enumerate(vign):
            x = (i % cols)*(T+4); y = (i//cols)*(T+16)
            c.paste(im.resize((T, T)).convert('RGB'), (x+2, y+14))
            d.text((x+2, y+2), nom, fill=(220, 220, 230))
        s = os.path.join(DUMP, 'nouvelles.png')
        c.save(s)
        print('\nplanche : %s  (%d vignettes)' % (s, len(vign)))
    print('liste    : %s' % os.path.join(DUMP, 'nouvelles.txt'))

if __name__ == '__main__':
    main()
