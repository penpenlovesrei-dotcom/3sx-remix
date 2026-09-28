# -*- coding: utf-8 -*-
"""Archive tout ce que contiennent les etats Flycast, pour pouvoir les ecraser.

    python recolte.py            -> ../releves/  (un .json par etage + un resume)

Un emplacement de sauvegarde Flycast est une ressource rare (dix). Ce script vide
chaque etat de sa substance une fois pour toutes : identification de l'etage, plans,
objets de fond, et la carte complete emplacement RAM -> palette de la banque.
"""
import sys, os, glob, json, collections
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import etat as E

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, '..', 'releves')
DATA = r'C:\Users\frede\Documents\Dreamcast\data'

# base du bloc de palettes propre a chaque decor (transferts 0x1D4DBC)
BLOCS = {827:'bg00-gill', 927:'bg01-alex', 989:'bg02-ryu', 1043:'bg03-yun',
         1117:'bg04-dudley', 1169:'bg05-necro', 1219:'bg06-hugo', 1289:'bg07-ibuki',
         1319:'bg08-elena-r1', 1365:'bg09-elena-r2', 1429:'bg0a-oro', 1085:'bg0b-yang',
         1477:'bg0c-ken', 1519:'bg0d-sean', 1607:'bg0e-urien', 2144:'bg0f'}

def identifier(couples):
    """L'emplacement 64 porte la base du bloc du decor (etalonne sur bg08)."""
    sc = collections.Counter()
    for slot, ex in couples:
        b = ex - (slot - 64)
        if b in BLOCS:
            sc[b] += 1
    return sc.most_common(1)[0] if sc else (None, 0)

def main():
    os.makedirs(SORTIE, exist_ok=True)
    resume = []
    for ch in sorted(glob.glob(os.path.join(DATA, 'Street Fighter III - Double Impact*.state'))):
        r = E.releve(ch)
        base, n = identifier(r['palettes'])
        nom = BLOCS.get(base, 'inconnu')
        actifs = [p for p in r['plans'] if p['x'] or p['y']]
        fichier = os.path.join(SORTIE, '%s.json' % nom)
        k = 1
        while os.path.exists(fichier):
            fichier = os.path.join(SORTIE, '%s-%d.json' % (nom, k)); k += 1
        json.dump({'etat': os.path.basename(ch), 'decor': nom, 'base_bloc': base,
                   'confiance': n, 'nb_objets': r['nb_objets'], 'objets': r['objets'],
                   'plans': r['plans'], 'palettes': r['palettes']},
                  open(fichier, 'w', encoding='utf-8'), indent=1)
        resume.append('%-14s  %d objets  plans actifs : %s'
                      % (nom, r['nb_objets'],
                         ' '.join('%d(%.0f,%.0f)' % (p['n'], p['x'], p['y']) for p in actifs)))
        print('%-46s -> %s' % (os.path.basename(ch)[:46], os.path.basename(fichier)))
    open(os.path.join(SORTIE, 'resume.txt'), 'w', encoding='utf-8').write('\n'.join(resume) + '\n')
    print('\n' + '\n'.join(resume))

if __name__ == '__main__':
    main()
