# -*- coding: utf-8 -*-
"""Releve d'un etat sauvegarde Flycast : plans, objets de fond, palettes.

    python etat.py "chemin/vers/etat.state"

Rend, pour l'etage fige dans l'etat :
  - le nombre d'objets de fond et leur position ;
  - la position et le defilement des huit plans ;
  - la correspondance **emplacement RAM -> palette de la banque de l'executable**,
    c'est-a-dire la regle `base + offset` mesuree au lieu d'etre deduite.

Les adresses viennent de FORMAT-PVC.md.
"""
import sys, os, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import flycast as F

ICI = os.path.dirname(os.path.abspath(__file__))
EXE = os.path.join(ICI, '..', 'SF3_2ND.BIN')

STRUCT   = 0x8C6AF304      # structure d'etat du jeu
OBJETS   = STRUCT + 84     # tableau d'objets, 144 octets par entree
NB_PLANS = STRUCT + 0x10   # nombre d'objets de fond
PLANS    = 0x8C84135C      # 8 x 16 octets : x, x_prec, y, y_prec en 16.16
DEFIL    = 0x8C7EFCCC      # 8 x {u16 x, u16 y} : ce que lit le dessin
CONFIG   = 0x8C84142C      # 8 x 10 octets par plan
PALRAM   = 0x8C7AFCCC      # palettes en RAM, 128 octets chacune

def banque(exe=EXE):
    d = open(exe, 'rb').read()
    n = (len(d) - 0x1D9AEC) // 128
    return np.frombuffer(d[0x1D9AEC:0x1D9AEC + 2715*128], dtype='<u2').reshape(2715, 64)

def releve(chemin, exe=EXE):
    ram, _ = F.lire_ram(chemin, exe)
    r = {}
    r['nb_objets'] = F.u16(ram, NB_PLANS)
    r['objets'] = [dict(n=k, x=F.s16(ram, OBJETS + k*144 + 10), y=F.s16(ram, OBJETS + k*144 + 12))
                   for k in range(max(r['nb_objets'], 0))]
    r['plans'] = [dict(n=k,
                       x=F.s32(ram, PLANS + k*16) / 65536.0,
                       y=F.s32(ram, PLANS + k*16 + 8) / 65536.0,
                       defil_x=F.u16(ram, DEFIL + k*4),
                       defil_y=F.u16(ram, DEFIL + k*4 + 2),
                       config=F.u16(ram, CONFIG + k*10 + 4))
                  for k in range(8)]
    B = banque(exe)
    cle = {}
    for i in range(len(B)):
        cle.setdefault(B[i].tobytes(), i)
    o = PALRAM - F.BASE_RAM
    couples = []
    for i in range(576):
        j = cle.get(ram[o + i*128 : o + i*128 + 128])
        if j is not None:
            couples.append((i, j))
    r['palettes'] = couples
    return r

def plages(couples, mini=3):
    """Regroupe les couples (emplacement, palette) en suites a ecart constant."""
    out = []
    for d, grp in itertools.groupby(sorted(couples, key=lambda c: (c[1]-c[0], c[0])),
                                      key=lambda c: c[1]-c[0]):
        g = [c[0] for c in grp]
        deb = g[0]; prec = g[0]
        for v in g[1:] + [None]:
            if v is None or v != prec + 1:
                if prec - deb + 1 >= mini:
                    out.append((d, deb, prec))
                if v is not None:
                    deb = v
            prec = v if v is not None else prec
    return sorted(out, key=lambda t: -(t[2]-t[1]))

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(1)
    r = releve(sys.argv[1])
    print('objets de fond : %d' % r['nb_objets'])
    for o in r['objets']:
        print('   objet %d  x=%6d  y=%6d' % (o['n'], o['x'], o['y']))
    print()
    print('plan   position x       y      defilement x     y    config')
    for p in r['plans']:
        actif = '' if (p['x'] or p['y']) else '   (inactif)'
        print('  %d   %10.3f %10.3f      %5d %5d    %04x%s'
              % (p['n'], p['x'], p['y'], p['defil_x'], p['defil_y'], p['config'], actif))
    print()
    print('palettes : %d emplacements RAM retrouves dans la banque' % len(r['palettes']))
    print('   suites (palette = base + emplacement) :')
    for d, a, b in plages(r['palettes'])[:12]:
        print('      base %5d   emplacements %3d a %3d   -> palettes %d a %d'
              % (d, a, b, a + d, b + d))
