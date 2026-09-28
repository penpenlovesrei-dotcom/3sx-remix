# -*- coding: utf-8 -*-
"""L'ECRAN D'UN ETAGE DE NEW GENERATION, tel que le port le compose -- 19/09/2026.

Ni sprite du disque, ni supposition : les PAGES sont celles que le lanceur deploie
(`CrowdedStreet-3SX\\resources\\tex_remix\\stage<N>`), les OBJETS sont les tuiles de
`decor_objets_data.c`, et le DEFILEMENT est celui de `bg_sub.c` :

    plan de base (bgw[1])   x = camera, bornee par `limit_tbl3` (ETAGESNG_LIMIT)
    autres plans            x = 0x200 + (vitesse * (camera - 0x200)) >> 16
    ecran                   scene x = x - 192 + colonne, repli sur 1024 (NG boucle)
                            scene y = 800 - v + ligne (la page porte les lignes 512..1023)
    objet de famille f      ecran x = X - (x du plan f-1 - 192), ecran y = 224 + v - Y

La profondeur : un z plus grand est plus loin (`stage_priority`, `position_z`). Les
combattants ne sont pas dessines ; leur z est note `Z_COMBATTANTS` pour dire ce qui passe
devant eux.

    python ecran_ng.py 40                  Ryu, camera au milieu, aux deux butees
    python ecran_ng.py 40 --camera=314     une camera donnee
    python ecran_ng.py 40 --variante=2     les objets d'une variante
    python ecran_ng.py 40 --image=3        l'image 3 des objets animes

Sortie : `rendus/ecran-<etage>-<camera>.png` (x2), et la liste des colonnes d'ecran que
rien ne couvre.
"""
import io
import os
import pickle
import re
import struct
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
sys.path.insert(0, ICI)

import numpy as np
from PIL import Image

RESSOURCES = r"C:\Users\frede\OneDrive\Bureau\SEPTEMBRE\SF3\CrowdedStreet-3SX\resources\tex_remix"
INC = r"C:\Temp3sx\src\port\video\etagesng_plans.inc"
DATA = r"C:\Temp3sx\src\port\video\decor_objets_data.c"
SORTIE = os.path.join(RACINE, "rendus")
Z_COMBATTANTS = 40


def lire_tex(chemin):
    """Les pixels d'une page, version 1 (couleur pleine) ou 2 (indices + palette).

    Depuis le 25/09/2026 nos pages sont en HUIT BITS, comme celles du jeu : l'entete est
    suivie de 256 entrees de quatre octets, puis d'un indice par pixel. La version 1
    reste lue -- une page de plus de 256 couleurs la garderait.
    """
    d = open(chemin, "rb").read()
    _m, v, w, h = struct.unpack_from("<IIII", d)
    if v == 2:
        pal = np.frombuffer(d, np.uint32, 256, 16)
        idx = np.frombuffer(d, np.uint8, w * h, 16 + 1024)
        a = pal[idx].view(np.uint8).reshape(h, w, 4).copy()
    else:
        a = np.frombuffer(d, np.uint8, w * h * 4, 16).reshape(h, w, 4).copy()
    a[:, :, [0, 2]] = a[:, :, [2, 0]]
    return a


def lire_liste(etage, liste, dossier=None):
    """La page 1024 x 512 d'une liste (lignes 512..1023 de la scene), ou None."""
    dossier = dossier or os.path.join(RESSOURCES, "stage%d" % etage)
    page = np.zeros((512, 1024, 4), np.uint8)
    vu = False
    for i in range(32):
        f = os.path.join(dossier, "%d-%d.tex" % (liste, liste + i))
        if os.path.exists(f):
            px, py = (i & 7) * 128, (i >> 3) * 128
            page[py:py + 128, px:px + 128] = lire_tex(f)
            vu = True
    return page if vu else None


def _macro(texte, nom):
    m = re.search(r"#define %s \\\n(.*?)\n\n" % nom, texte, re.S)
    return m.group(1) if m else ""


def plans(etage):
    """{plan: (vitesse x, z)} et (borne gauche, borne droite) du plan de base."""
    t = io.open(INC, encoding="utf-8").read()
    k = etage - 37
    use = [int(v) for v in _macro(t, "ETAGESNG_USE_SCR").split(",")][k]
    prio = [int(v, 16) for v in _macro(t, "ETAGESNG_PRIORITY").split(",")][k]
    msp = re.findall(r"\{ \{ (0x[0-9A-F]+), (0x[0-9A-F]+) \}, \{ (0x[0-9A-F]+), (0x[0-9A-F]+) \}, "
                     r"\{ (0x[0-9A-F]+), (0x[0-9A-F]+) \} \}", _macro(t, "ETAGESNG_MSP"))[k]
    lim = re.findall(r"\{ \{ (0x[0-9A-F]+), (0x[0-9A-F]+), 0xF0, 0xF0 \}, \{ (0x[0-9A-F]+), "
                     r"(0x[0-9A-F]+), 0xF0, 0xF0 \}", _macro(t, "ETAGESNG_LIMIT"))[k]
    out = {}
    for p in range(use):
        out[p] = (int(msp[2 * p], 16), int(msp[2 * p + 1], 16), (prio >> (24 - 8 * p)) & 0xFF)
    return out, (int(lim[2], 16), int(lim[3], 16))


_CACHE = os.path.join(os.environ.get("TEMP", ICI), "ecran_ng_objets.pkl")


def objets(etage):
    """Les fiches de l'etage, decodees : [(fiche, {image: [(x, y, rgba 16x16)]})]."""
    import rendu_fiches as RF
    cle = os.path.getmtime(DATA)
    cache = {}
    if os.path.exists(_CACHE):
        try:
            cache = pickle.load(open(_CACHE, "rb"))
        except Exception:
            cache = {}
    if cache.get("cle") != cle:
        src, octets, palettes, cases = RF.charger()
        par_etage = {}
        for m in RF.FICHE.finditer(src):
            ch = [c.strip() for c in m.group(2).split(",")]
            if len(ch) < 15 or not m.group(1).startswith("ng"):
                continue
            e = int(ch[0])
            pal = palettes.get(ch[7])
            if pal is None or ch[5] not in cases:
                continue
            ims = {}
            for image, tx, ty, nom_px in cases[ch[5]]:
                plat = octets[nom_px][RF.DETABLE].reshape(16, 16)
                ims.setdefault(image, []).append((tx, ty, RF.rgba_de(plat, pal)))
            f = dict(nom=ch[5].replace("_tuiles", ""), cols=int(ch[3]), ligs=int(ch[4]),
                     x=int(ch[9]), y=int(ch[10]), famille=int(ch[11]), z=int(ch[12]),
                     boucle=int(ch[13]), variante=int(ch[14], 0), note=m.group(3).strip(),
                     suite=ch[15:])
            par_etage.setdefault(e, []).append((f, ims))
        cache = dict(cle=cle, etages=par_etage)
        pickle.dump(cache, open(_CACHE, "wb"))
    return cache["etages"].get(etage, [])


def poser(ecran, prof, rgba, x, y, z):
    """Pose `rgba` a l'ecran en (x, y) si z est plus pres que ce qui y est deja."""
    h, w = rgba.shape[:2]
    x0, y0 = max(0, x), max(0, y)
    x1, y1 = min(ecran.shape[1], x + w), min(ecran.shape[0], y + h)
    if x0 >= x1 or y0 >= y1:
        return
    src = rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    op = (src[:, :, 3] > 0) & (z <= prof[y0:y1, x0:x1])
    zone = ecran[y0:y1, x0:x1]
    zone[op] = src[op]
    prof[y0:y1, x0:x1][op] = z


def composer(etage, camera, v=0, variante=None, image=0, pages=None, sans_objets=False,
             seulement=None):
    """(ecran RGBA 224 x 384, profondeurs, calques) pour une camera donnee."""
    pl, _bornes = plans(etage)
    ecran = np.zeros((224, 384, 4), np.uint8)
    prof = np.full((224, 384), 255, np.int32)
    xs = {}
    for p, (sx, sy, _z) in pl.items():
        xs[p] = camera if p == 1 else 0x200 + ((sx * (camera - 0x200)) >> 16)
    vs = {p: (v if p == 1 else (pl[p][1] * v) >> 16) for p in pl}
    calques = []
    for p, (sx, sy, z) in pl.items():
        page = (pages or {}).get(p)
        if page is None:
            page = lire_liste(etage, 132 + 64 * p)
        if page is None:
            continue
        cols = (np.arange(384) + xs[p] - 192) % 1024
        ligs = np.arange(224) + 800 - vs[p] - 512
        ok = (ligs >= 0) & (ligs < 512)
        vue = np.zeros((224, 384, 4), np.uint8)
        vue[ok] = page[ligs[ok]][:, cols]
        calques.append((z, 0, "plan %d" % p, vue))
    if not sans_objets:
        for f, ims in objets(etage):
            if variante is not None and f["variante"] and not f["variante"] & (1 << variante):
                continue
            if seulement and not any(s in f["nom"] for s in seulement):
                continue
            p = f["famille"] - 1
            if p not in xs:
                continue
            vue = np.zeros((224, 384, 4), np.uint8)
            im = image if image in ims else 0
            if not f["boucle"]:
                im = 0
            hx = xs[p] - 192
            for tx, ty, rgba in ims.get(im, []):
                # la rangee `ty` de l'image : son haut est en Y + (ligs-1)*16 - ty (y moteur)
                sx_ = f["x"] + tx - hx
                sy_ = 224 + vs[p] - (f["y"] + (f["ligs"] - 1) * 16 - ty)
                poser(vue, np.full((224, 384), 255), rgba, sx_, sy_, 0)
            calques.append((f["z"], 1, f["nom"], vue))
    # du plus loin au plus proche ; a z egal, l'objet apres le plan
    for z, _o, nom, vue in sorted(calques, key=lambda c: (-c[0], c[1])):
        op = vue[:, :, 3] > 0
        ecran[op] = vue[op]
        prof[op] = z
    return ecran, prof, calques


def colonnes_vides(ecran):
    vides = np.nonzero(~(ecran[:, :, 3] > 0).any(axis=0))[0]
    if not len(vides):
        return []
    out, debut = [], vides[0]
    for a, b in zip(vides, list(vides[1:]) + [None]):
        if b is None or b != a + 1:
            out.append((debut, a))
            debut = b
    return out


def main():
    etage = int(sys.argv[1])
    opts = dict(a.lstrip("-").split("=") for a in sys.argv[2:] if "=" in a)
    variante = int(opts["variante"]) if "variante" in opts else None
    image = int(opts.get("image", 0))
    _pl, (g, d) = plans(etage)
    cameras = [int(opts["camera"])] if "camera" in opts else [g, (g + d) // 2, d]
    v = int(opts.get("v", 0))
    os.makedirs(SORTIE, exist_ok=True)
    for cam in cameras:
        ecran, prof, _c = composer(etage, cam, v, variante, image)
        vides = colonnes_vides(ecran)
        noirs = int((ecran[:, :, 3] == 0).sum())
        chemin = os.path.join(SORTIE, "ecran-%d-%d%s.png" % (etage, cam, "-v%d" % v if v else ""))
        fond = np.zeros_like(ecran)
        fond[:, :, 1] = 0
        fond[:, :, 3] = 255
        im = ecran.copy()
        im[ecran[:, :, 3] == 0] = (255, 0, 255, 255)
        Image.fromarray(im).resize((768, 448), Image.NEAREST).save(chemin)
        print("etage %d camera %d v %d : %d pixels vides, colonnes vides %s -> %s"
              % (etage, cam, v, noirs, vides or "aucune", chemin))


if __name__ == "__main__":
    main()
