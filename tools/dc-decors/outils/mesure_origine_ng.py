"""Pour chaque fiche NG, la banque brute a-t-elle un TROU ou une COPIE PEINTE sous l'objet,
a x (enroulement) ou a x+512 (origine au milieu, comme Ryu 2I) ?"""
import os, sys
sys.path.insert(0, r"C:\Users\frede\Downloads\3sx-outils\dc-decors\outils")
import numpy as np
import poser2i as P
import rendu_fiches as R

src, octets, palettes, cases = R.charger()
etages = [int(a) for a in sys.argv[1:]] or list(range(37, 56))


def couches(etage):
    d = os.path.join(R.RACINE, "etagesng-sprites", "stage%d" % etage)
    out = {}
    for l in sorted({int(n.split("-")[0]) for n in os.listdir(d)}):
        p = P.lire_liste(d, l)
        if p is not None:
            out[l] = p
    return out


def objet(ch):
    """(rgba 1024x1024 partiel sous forme de liste de (x, y, tuile rgba))"""
    ligs = int(ch[4]); x, y = int(ch[9]), int(ch[10])
    bank_y = 1024 - y - (ligs - 1) * 16
    pal = palettes.get(ch[7])
    out = []
    for im, tx, ty, px in cases.get(ch[5], ()):
        if im == 0 and pal:
            plat = octets[px][R.DETABLE].reshape(16, 16)
            out.append((x + tx, bank_y + ty, R.rgba_de(plat, pal)))
    return out


def masque(tuiles):
    x0 = min(x for x, y, t in tuiles); y0 = min(y for x, y, t in tuiles)
    x1 = max(x for x, y, t in tuiles) + 16; y1 = max(y for x, y, t in tuiles) + 16
    m = np.zeros((y1 - y0, x1 - x0), bool)
    rgb = np.zeros((y1 - y0, x1 - x0, 3), int)
    for x, y, t in tuiles:
        m[y - y0:y - y0 + 16, x - x0:x - x0 + 16] |= t[:, :, 3] > 0
        rgb[y - y0:y - y0 + 16, x - x0:x - x0 + 16][t[:, :, 3] > 0] = t[:, :, :3][t[:, :, 3] > 0]
    return x0, y0, m, rgb


def score(mq, page, dx, marge=4):
    """(n, iou du trou, part copiee)"""
    x0, y0, m, rgb = mq
    h, w = m.shape
    M = np.zeros((h + 2 * marge, w + 2 * marge), bool)
    M[marge:marge + h, marge:marge + w] = m
    xs = (np.arange(w + 2 * marge) + x0 - marge + dx) % 1024
    ys = np.arange(h + 2 * marge) + y0 - marge
    ok = (ys >= 512) & (ys < 1024)
    if not ok.any():
        return 0, 0, 0
    sub = page[np.ix_(ys[ok], xs)]
    Mm = M[ok]
    trou = sub[:, :, 3] == 0
    D = Mm.copy()
    for _ in range(3):
        E = D.copy()
        E[1:] |= D[:-1]; E[:-1] |= D[1:]; E[:, 1:] |= D[:, :-1]; E[:, :-1] |= D[:, 1:]
        D = E
    anneau = D & ~Mm
    sur_trou = (Mm & trou).sum() / max(Mm.sum(), 1)
    anneau_plein = (anneau & ~trou).sum() / max(anneau.sum(), 1)
    inter, union = sur_trou * anneau_plein, 1
    R_ = np.zeros(Mm.shape + (3,), int)
    R_[marge if ok[0] else 0:, :][:0] = 0
    rr = np.zeros(M.shape + (3,), int); rr[marge:marge + h, marge:marge + w] = rgb
    rr = rr[ok]
    diff = np.abs(sub[:, :, :3].astype(int) - rr).sum(axis=2)
    copie = (Mm & ~trou & (diff < 24)).sum()
    n = Mm.sum()
    return int(n), inter / max(union, 1), copie / max(n, 1)


for e in etages:
    bg = "ng%02x" % (e - 37)
    cs = couches(e)
    lignes = []
    tot = {0: [0, 0, 0], 512: [0, 0, 0]}
    for m in R.FICHE.finditer(src):
        ch = [c.strip() for c in m.group(2).split(",")]
        if m.group(1) != bg or int(ch[0]) != e:
            continue
        t = objet(ch)
        if not t:
            continue
        mq = masque(t)
        best = {}
        for dx in (0, 512):
            s_ = max((score(mq, p, dx) for p in cs.values()), key=lambda s: s[1] + s[2])
            best[dx] = s_
            tot[dx][0] += s_[0]; tot[dx][1] += s_[0] * s_[1]; tot[dx][2] += s_[0] * s_[2]
        n0, t0, c0 = best[0]
        n5, t5, c5 = best[512]
        if n0:
            lignes.append("   %-62s n %5d | x: iou %3.0f%% copie %3.0f%% | x+512: iou %3.0f%% copie %3.0f%%"
                          % (m.group(3).strip()[:62], n0, 100 * t0, 100 * c0, 100 * t5, 100 * c5))
    n0, t0, c0 = tot[0]; n5, t5, c5 = tot[512]
    print("ETAGE %d (%s)  x: iou %.0f%% copie %.0f%%   x+512: iou %.0f%% copie %.0f%%"
          % (e, bg, 100 * t0 / max(n0, 1), 100 * c0 / max(n0, 1), 100 * t5 / max(n5, 1), 100 * c5 / max(n5, 1)))
    if "-v" in os.environ.get("BAVARD", "") or len(etages) < 4:
        print("\n".join(lignes))
