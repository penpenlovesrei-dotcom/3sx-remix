# -*- coding: utf-8 -*-
"""Met le dump de cote pour forcer le jeu a tout reecrire, puis fait le releve.

    python dumpneuf.py --avant   met dump/ de cote sous dump-precedent/
    python dumpneuf.py           liste ce que la partie a ecrit, par liste
"""
import sys, os, shutil, collections

DUMP = os.path.join(os.environ.get('APPDATA', ''), 'CrowdedStreet', '3SX',
                    'resources', 'tex_remix', 'dump')
GARDE = DUMP + '-precedent'

def main():
    if '--avant' in sys.argv:
        if os.path.isdir(GARDE):
            shutil.rmtree(GARDE)
        if os.path.isdir(DUMP):
            os.rename(DUMP, GARDE)
        print('dump mis de cote sous %s' % os.path.basename(GARDE))
        return
    m = os.path.join(DUMP, 'manifest.txt')
    if not os.path.exists(m):
        print('aucun manifeste : le jeu n\'a rien ecrit.')
        return
    lignes = [l.split() for l in open(m, encoding='utf-8', errors='replace') if l.strip()]
    g = collections.defaultdict(set)
    for c in lignes:
        g[int(c[7])].add(int(c[5]))
    print('%d lignes ecrites, par liste :' % len(lignes))
    for li in sorted(g):
        p = sorted(g[li])
        print('  liste %-4d : %3d pages  %d..%d' % (li, len(p), p[0], p[-1]))
    print()
    print('boot et menus = listes 0, 590, 600, 601. Le reste est le decor.')

if __name__ == '__main__':
    main()
