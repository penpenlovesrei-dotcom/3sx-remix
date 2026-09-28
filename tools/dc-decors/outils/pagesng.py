# -*- coding: utf-8 -*-
"""Les ANIMATIONS DE PAGES de New Generation, servies en objets animes -- 17/09/2026.

Frederic : « Les 11 animations du decor lui-meme (cascades d'Ibuki, Ryu, Elena) ne sont pas
faites. » Elles sont lues dans le code (`descripteursng.ANIMATIONS`) : chaque pas choisit une
liste de rectangles de plus, et l'image d'un pas est la couche entiere telle que le Dreamcast
la dessine. On en tire un objet de NOTRE systeme, comme `animer2i` le fait pour 2I :

  * il ne couvre que les CASES QUI CHANGENT d'un pas a l'autre ; la page porte le pas 0 ;
  * une animation dont un pas laisse transparent ce que le pas 0 peint (le vent dans les
    arbres d'Ibuki) ne peut pas se poser par-dessus : ces cases sont RETIREES DE LA PAGE
    (`evidees`), et l'objet sert tous les pas -- `couchesng.py` lit la liste ;
  * il est coupe en morceaux d'au plus 64 cases (`CASES_MAX` de `decor_objets.c`) et 63
    couleurs (une palette par fiche), qui se rejoignent au pixel pres ;
  * il prend la famille et la profondeur de son plan, un cran devant (`animer2i.fiche_page`).

Le budget est celui de l'etage (`animerng.budget`) : les animations passent d'abord, par rang.
"""
import json
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)

import numpy as np

import animations as AN0
import descripteursng as D
import etagesng as E

CASES_MAX = 64
COULEURS_MAX = 63
VIE_MOTIF = 12
GARDEES = os.path.join(ICI, "pagesng_gardees.json")
FAMILLE_DE_LISTE = {132: 1, 196: 2, 260: 3}


def plan_de_couche(bande, couche):
    """(famille, z du plan) de la liste qui porte la couche, ou None."""
    f = E.fiche(bande)
    for i, liste in enumerate((132, 196, 260)):
        if liste in f["couches"] and f["couches"][liste][2] == couche:
            return FAMILLE_DE_LISTE[liste], f["z"][i]
    return None


def cases_qui_changent(ims):
    """(masque 32 x 64 des cases qui changent, cases a evider)."""
    base = ims[0][512:]
    c0 = base.reshape(32, 16, 64, 16, 4)
    diff = np.zeros((32, 64), bool)
    trous = np.zeros((32, 64), bool)
    for im in ims[1:]:
        c = im[512:].reshape(32, 16, 64, 16, 4)
        diff |= (c != c0).any(axis=(1, 3, 4))
        t = (c[..., 3] == 0) & (c0[..., 3] > 0)
        trous |= t.any(axis=(1, 3))
    return diff, trous


def couleurs(ims, masque, r0, r1, c0, c1):
    vus = set()
    for im in ims:
        z = im[512 + r0 * 16:512 + r1 * 16, c0 * 16:c1 * 16]
        m = np.repeat(np.repeat(masque[r0:r1, c0:c1], 16, 0), 16, 1) & (z[:, :, 3] > 0)
        px = z[:, :, :3][m]
        if len(px):
            vus.update(map(tuple, np.unique(px, axis=0).tolist()))
    return vus


def morceler(ims, masque):
    """Des rectangles de cases (r0, r1, c0, c1) d'au plus 64 cases et 63 couleurs."""
    out = []
    cols = np.nonzero(masque.any(axis=0))[0]
    c = int(cols.min()) if len(cols) else 64
    fin = int(cols.max()) + 1 if len(cols) else 0

    def lignes(c0, c1):
        rs = np.nonzero(masque[:, c0:c1].any(axis=1))[0]
        return (int(rs.min()), int(rs.max()) + 1) if len(rs) else None

    while c < fin:
        if not masque[:, c].any():
            c += 1
            continue
        w = 1
        while c + w < fin:
            r = lignes(c, c + w + 1)
            if (w + 1) * (r[1] - r[0]) > CASES_MAX:
                break
            if len(couleurs(ims, masque, r[0], r[1], c, c + w + 1)) > COULEURS_MAX:
                break
            w += 1
        r0, r1 = lignes(c, c + w)
        if len(couleurs(ims, masque, r0, r1, c, c + w)) <= COULEURS_MAX and w * (r1 - r0) <= CASES_MAX:
            out.append((r0, r1, c, c + w))
        else:
            # une seule colonne trop riche : on la coupe en hauteur
            r = r0
            while r < r1:
                h = 1
                while r + h < r1 and len(couleurs(ims, masque, r, r + h + 1, c, c + 1)) <= COULEURS_MAX:
                    h += 1
                out.append((r, r + h, c, c + 1))
                r += h
        c += w
    return out


def vivantes(durees):
    n = len(durees)
    pire = 1
    for depart in range(n):
        vus, ecart, k = 1, 1, depart - 1
        while vus < n and ecart <= VIE_MOTIF:
            vus += 1
            ecart += durees[k % n]
            k -= 1
        pire = max(pire, vus)
    return pire


def preparer(a):
    """L'animation `a` decoupee : dict(morceaux, cout, ...), ou None si rien ne bouge."""
    pl = plan_de_couche(a["bande"], a["couche"])
    if pl is None:
        return None
    ims, durees = D.images_animation(a)
    diff, trous = cases_qui_changent(ims)
    if not diff.any():
        return None
    evider = bool(trous.any())
    morceaux = morceler(ims, diff)
    cases = sum(int(diff[r0:r1, c0:c1].sum()) for r0, r1, c0, c1 in morceaux)
    viv = vivantes(durees)
    return dict(a, ims=ims, durees=durees, masque=diff, evider=evider, morceaux=morceaux,
                famille=pl[0], z=pl[1] - 1, cout=cases * viv, rangs=len(morceaux),
                motifs=len(morceaux) * viv)


class Tuiles:
    """Les tableaux de 256 octets, emis une fois chacun."""

    def __init__(self, prefixe):
        self.prefixe = prefixe
        self.noms = {}
        self.lignes = []

    def nom(self, octets):
        n = self.noms.get(octets)
        if n is None:
            n = "%s_t%d" % (self.prefixe, len(self.noms))
            self.noms[octets] = n
            self.lignes.append("static const unsigned char %s[256] = { %s };"
                               % (n, ", ".join(str(v) for v in octets)))
        return n


def bloc_c(p, prefixe, tuiles, morceau):
    """Le C d'un morceau et sa fiche."""
    r0, r1, c0, c1 = morceau
    ligs, cols = r1 - r0, c1 - c0
    ims = p["ims"]
    msk = p["masque"]
    cle, pal = {}, [0] * 64
    for im in ims:
        z = im[512 + r0 * 16:512 + r1 * 16, c0 * 16:c1 * 16]
        m = np.repeat(np.repeat(msk[r0:r1, c0:c1], 16, 0), 16, 1) & (z[:, :, 3] > 0)
        for c in np.unique(z[:, :, :3][m], axis=0).tolist():
            c = tuple(c)
            if c not in cle:
                cle[c] = len(cle) + 1
                pal[cle[c]] = 0x8000 | ((c[0] >> 3) << 10) | ((c[1] >> 3) << 5) | (c[2] >> 3)
    assert len(cle) <= COULEURS_MAX
    table = {}
    L, cases = [], []
    for n, im in enumerate(ims):
        z = im[512 + r0 * 16:512 + r1 * 16, c0 * 16:c1 * 16]
        idx = np.zeros(z.shape[:2], np.uint8)
        op = (z[:, :, 3] > 0) & np.repeat(np.repeat(msk[r0:r1, c0:c1], 16, 0), 16, 1)
        for y, x in zip(*np.nonzero(op)):
            idx[y, x] = cle[tuple(int(v) for v in z[y, x, :3])]
        for lig in range(ligs):
            for col in range(cols):
                if not msk[r0 + lig, c0 + col]:
                    continue
                bloc = idx[lig * 16:lig * 16 + 16, col * 16:col * 16 + 16]
                if not bloc.any():
                    continue
                nom = tuiles.nom(bytes(AN0.entrelacer(bloc)))
                cases.append("    { %d, %d, %d, %s }," % (n, col * 16, lig * 16, nom))
    L.append("static const DecorTuile %s_tuiles[] = {" % prefixe)
    L.extend(cases)
    L.append("};")
    L.append("static const unsigned char %s_durees[%d] = { %s };"
             % (prefixe, len(ims), ", ".join(str(d) for d in p["durees"])))
    L.append("static const unsigned short %s_palette[64] = { %s };"
             % (prefixe, ", ".join("0x%04X" % v for v in pal)))
    L.append("")
    bande = p["bande"]
    by = 512 + r0 * 16
    y = 1024 - by - (ligs - 1) * 16
    fiche = ('    { "ng%02x", %d, %d, %d, %d, %d, %s_tuiles, %s_durees, %s_palette, 0, %d, %d, %d, %d, 1, 0xF },'
             '  /* page animee : %s, cases %d..%d x %d..%d%s */'
             % (bande, E.PREMIER_ETAGE + bande, len(ims), len(cases), cols, ligs, prefixe, prefixe,
                prefixe, c0 * 16, y, p["famille"], p["z"], p["quoi"], c0, c1, r0, r1,
                ", page evidee" if p["evider"] else ""))
    return "\n".join(L), fiche


def pour_bande(bande):
    """Les animations preparees de la bande, par rang."""
    out = []
    for a in D.ANIMATIONS:
        if a["bande"] != bande:
            continue
        p = preparer(a)
        if p is not None:
            out.append(p)
    out.sort(key=lambda p: p["rang"])
    return out


def reduire_gardees(gardees):
    """[(bande, couche, cases)] -- ce que `ecrire_gardees` garde d'une page animee.

    SEPARE DE L'ECRITURE LE 25/09/2026, pour le cache par bande : c'est cette forme-la,
    quelques entiers, qui se range dans `cache_decors` -- pas la page entiere avec ses
    images."""
    return [(p["bande"], p["couche"], np.argwhere(p["masque"]).tolist())
            for p in gardees if p["evider"]]


def ecrire_gardees_reduites(reduites):
    """{bande: [[couche, cases]]} pour `couchesng.py`."""
    out = {}
    for bande, couche, cases in reduites:
        out.setdefault(str(bande), []).append([couche, cases])
    json.dump(out, open(GARDEES, "w"), indent=0)


def ecrire_gardees(gardees):
    """{bande: [[couche, masque de cases a evider]]} pour `couchesng.py`."""
    ecrire_gardees_reduites(reduire_gardees(gardees))


def evidees(bande):
    """[(couche, [(ligne, colonne)])] : les cases a retirer de la page de la bande."""
    if not os.path.exists(GARDEES):
        return []
    d = json.load(open(GARDEES))
    return [(c, [tuple(x) for x in cases]) for c, cases in d.get(str(bande), [])]
