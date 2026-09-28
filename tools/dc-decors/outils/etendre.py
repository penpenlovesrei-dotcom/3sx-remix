# -*- coding: utf-8 -*-
"""Etend un tableau C indexe par etage de [22] a [23] en dupliquant un element.

Analyse les accolades de premier niveau de l'initialiseur ; ne touche a rien d'autre.
"""
import re, sys

def elements(txt):
    """Decoupe l'initialiseur (sans les accolades exterieures) en elements de 1er niveau."""
    out, prof, deb = [], 0, 0
    for i, c in enumerate(txt):
        if c == '{': prof += 1
        elif c == '}': prof -= 1
        elif c == ',' and prof == 0:
            out.append(txt[deb:i]); deb = i + 1
    reste = txt[deb:]
    if reste.strip(): out.append(reste)
    return out

def etendre(chemin, nom, modele=5, avant=22, apres=23):
    s = open(chemin, encoding='utf-8').read()
    m = re.search(r'\b' + re.escape(nom) + r'\s*\[\s*%d\s*\]' % avant, s)
    if not m:
        return None, 'declaration [%d] introuvable' % avant
    s2 = s[:m.start()] + s[m.start():m.end()].replace(str(avant), str(apres)) + s[m.end():]
    m2 = re.search(r'\b' + re.escape(nom) + r'\s*\[\s*%d\s*\]' % apres, s2)
    # initialiseur eventuel
    j = s2.find('=', m2.end())
    k = s2.find(';', m2.end())
    if j == -1 or (k != -1 and k < j):
        return s2, 'declaration seule, etendue'
    d = s2.find('{', j)
    prof, i = 0, d
    while i < len(s2):
        if s2[i] == '{': prof += 1
        elif s2[i] == '}':
            prof -= 1
            if prof == 0: break
        i += 1
    corps = s2[d+1:i]
    els = elements(corps)
    if len(els) != avant:
        return None, '%d elements trouves, %d attendus' % (len(els), avant)
    copie = els[modele].strip()
    neuf = corps.rstrip()
    if neuf.endswith(','): neuf = neuf[:-1]
    neuf += ',\n    ' + copie + ' /* etage %d, copie de %d */\n' % (apres-1, modele)
    return s2[:d+1] + neuf + s2[i:], 'ok, %d -> %d elements' % (len(els), len(els)+1)

if __name__ == '__main__':
    chemin, nom = sys.argv[1], sys.argv[2]
    modele = int(sys.argv[3]) if len(sys.argv) > 3 else 5
    s, msg = etendre(chemin, nom, modele)
    print('%-24s %s' % (nom, msg))
    if s is not None:
        open(chemin, 'w', encoding='utf-8').write(s)
