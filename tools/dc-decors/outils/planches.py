# -*- coding: utf-8 -*-
"""Les PLANCHES D'INVENTAIRE : tout ce que le port pose, rendu avec ses vraies couleurs.

POURQUOI CET OUTIL
------------------
Le chantier a longtemps corrige des positions et des couleurs sans jamais REGARDER
l'ensemble de ce qu'il produit. On voyait un decor a la fois, dans le jeu, apres une
compilation -- donc on ne comparait rien et on ne voyait pas ce qui manquait.

Ces planches rendent d'un coup :

    planches.py animes    les 247 sprites animes, groupes par etage
    planches.py stages    les plans de chaque etage et les elements poses dessus
    planches.py           les deux

Elles sortent dans `planches/`, une image par etage plus une vue d'ensemble.

CE QU'ELLES PERMETTENT DE JUGER, ET QU'AUCUN JOURNAL NE DIT
----------------------------------------------------------
* une palette fausse se voit tout de suite -- un sprite gris, noir ou fluo ;
* un sprite ABSENT se voit par son trou dans la serie ;
* un sprite mal assemble se voit a sa forme ;
* et les plans montrent ou chaque element est pose, donc si la chaine de position tombe
  juste ou non.

LES TUILES SONT ENTRELACEES (ordre de Morton, `y` sur les bits pairs). La permutation a
ete calibree sur l'acolyte de Gill, dont l'image est connue : les deux autres ordres
rendent du bruit.
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
DATA = r"C:\Temp3sx\src\port\video\decor_objets_data.c"
SORTIE = os.path.join(RACINE, "planches")

FOND = (24, 24, 30)
FOND2 = (34, 34, 42)
TEXTE = (230, 230, 235)
ALERTE = (255, 120, 120)


def morton(x, y):
    """L'ordre d'entrelacement des tuiles -- `y` sur les bits pairs."""
    v = 0
    for i in range(4):
        v |= ((y >> i) & 1) << (2 * i) | ((x >> i) & 1) << (2 * i + 1)
    return v


_MORTON = np.array([[morton(x, y) for x in range(16)] for y in range(16)])


def nombres(txt):
    return [int(v, 16) if v.lower().startswith("0x") else int(v)
            for v in re.findall(r"0[xX][0-9a-fA-F]+|-?\d+", txt)]


class Source:
    """`decor_objets_data.c`, lu une fois."""

    def __init__(self, chemin=DATA):
        self.txt = io.open(chemin, encoding="utf-8", errors="replace").read()

        # TOUS LES TABLEAUX SONT INDEXES EN UNE SEULE PASSE.
        #
        # La premiere version cherchait chaque tableau par une regex sur les 17 Mo du
        # fichier : 247 fiches x une cinquantaine de tuiles, plus de dix mille balayages
        # complets. L'outil ne rendait jamais la main. Un seul `finditer` suffit, et le
        # decoupage en nombres n'est fait qu'a la demande.
        self._tab = {}
        for m in re.finditer(r"\b(\w+)\[\d*\]\s*=\s*\{([^;]*?)\};", self.txt, re.S):
            self._tab.setdefault(m.group(1), m.group(2))

    def tableau(self, nom):
        v = self._tab.get(nom)

        if isinstance(v, str):
            v = nombres(v)
            self._tab[nom] = v

        return v

    def tuiles(self, prefixe):
        m = re.search(r"\b%s_tuiles\[\d*\]\s*=\s*\{(.*?)\n\};" % re.escape(prefixe),
                      self.txt, re.S)
        if m is None:
            return []
        return [(int(a), int(b), int(c), d) for a, b, c, d in
                re.findall(r"\{\s*(\d+)\s*,\s*(\d+)\s*,\s*(\d+)\s*,\s*(\w+)\s*\}", m.group(1))]

    def fiches(self):
        """Les entrees de `decor_animations`, dans l'ordre du tableau."""
        bloc = re.search(r"const DecorAnimation decor_animations\[\]\s*=\s*\{(.*?)\n\};",
                         self.txt, re.S).group(1)
        out = []
        for l in bloc.splitlines():
            # LES NOMS PORTENT DES CHIFFRES (`a22o0_tuiles`), donc on ne peut pas lire les
            # nombres apres eux sans les SAUTER explicitement : sinon la palette 871 se
            # lisait « 22 », celle du nom du tableau.
            m = re.match(r'\s*\{\s*"(\w+)",\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),'
                         r'\s*(\w+)_tuiles,\s*\w+,\s*\w+,', l)
            if not m:
                continue
            reste = nombres(l[m.end():].split("/*")[0])
            out.append(dict(nom=m.group(1), etage=int(m.group(2)),
                            nb_images=int(m.group(3)), nb_tuiles=int(m.group(4)),
                            cols=int(m.group(5)), ligs=int(m.group(6)),
                            prefixe=m.group(7),
                            palette=reste[0] if reste else 0,
                            x=reste[1] if len(reste) > 1 else 0,
                            y=reste[2] if len(reste) > 2 else 0,
                            famille=reste[3] if len(reste) > 3 else 0,
                            z=reste[4] if len(reste) > 4 else 0,
                            boucle=reste[5] if len(reste) > 5 else 0,
                            commentaire=(l.split("/*")[1].rstrip("*/ ")
                                         if "/*" in l else "")))
        return out

    def image(self, f, num=0):
        """(RGBA de l'image `num`, nombre de cases vides) -- desentrelacee et coloree."""
        pal = self.tableau(f["prefixe"] + "_palette") or [0] * 64
        h, w = f["ligs"] * 16, f["cols"] * 16
        idx = np.zeros((h, w), np.uint8)
        vides = 0
        for im, cx, cy, nom in self.tuiles(f["prefixe"]):
            if im != num:
                continue
            d = self.tableau(nom)
            if d is None:
                vides += 1
                continue
            t = np.array(d, np.uint8)[_MORTON]
            if cy + 16 <= h and cx + 16 <= w:
                idx[cy:cy + 16, cx:cx + 16] = t
        rgba = np.zeros((h, w, 4), np.uint8)
        for v in np.unique(idx):
            if v == 0 or v >= len(pal):
                continue
            c = pal[v]
            m = idx == v
            rgba[m] = ((c >> 10 & 31) * 255 // 31, (c >> 5 & 31) * 255 // 31,
                       (c & 31) * 255 // 31, 255)
        return rgba, vides


def vignette(rgba, zoom=1):
    im = Image.fromarray(rgba, "RGBA")
    if zoom != 1:
        im = im.resize((im.width * zoom, im.height * zoom), Image.NEAREST)
    return im


def planche_animes(src, etage, fiches, zoom=2, largeur=1500):
    """Une planche pour un etage : chaque objet, son image 0, et sa fiche en clair."""
    vignettes = []
    for f in fiches:
        rgba, vides = src.image(f)
        v = vignette(rgba, zoom)
        # TROIS LIGNES COURTES plutot qu'une longue : sur une seule, les etiquettes des
        # vignettes voisines se chevauchaient et devenaient illisibles.
        etiq = ["%s  %dx%d  %d img" % (f["prefixe"], f["cols"], f["ligs"], f["nb_images"]),
                "pal %d   (%d,%d)" % (f["palette"], f["x"], f["y"]),
                "fam %d  z %d  %s" % (f["famille"], f["z"],
                                      "boucle" if f["boucle"] else "FIGE")]
        vide = (rgba[:, :, 3] > 0).sum() == 0
        vignettes.append((v, etiq, vide or vides))

    marge, hetiq = 12, 12 * 3 + 4
    lignes, cur, larg_cur, haut_cur = [], [], marge, 0
    for v, etiq, souci in vignettes:
        lv = max(v.width, 170) + marge
        if larg_cur + lv > largeur and cur:
            lignes.append((cur, haut_cur))
            cur, larg_cur, haut_cur = [], marge, 0
        cur.append((v, etiq, souci, larg_cur))
        larg_cur += lv
        haut_cur = max(haut_cur, v.height)
    if cur:
        lignes.append((cur, haut_cur))

    H = marge + sum(h + hetiq + marge * 2 for _c, h in lignes) + 26
    img = Image.new("RGB", (largeur, max(H, 80)), FOND)
    d = ImageDraw.Draw(img)
    d.text((marge, 6), "ETAGE %d  --  %d objet(s) anime(s)" % (etage, len(fiches)),
           fill=TEXTE)
    y = 26
    for k, (cases, h) in enumerate(lignes):
        if k % 2:
            d.rectangle([0, y - 4, largeur, y + h + hetiq + marge], fill=FOND2)
        for v, etiq, souci, x in cases:
            img.paste(v, (x, y), v)
            for k, ligne in enumerate(etiq):
                d.text((x, y + h + 2 + k * 12), ligne, fill=ALERTE if souci else TEXTE)
        y += h + hetiq + marge * 2
    return img


# LES PAGES QUE LE JEU LIT VRAIMENT, pas celles du dossier de travail.
#
# `tex_remix.c` va les chercher dans `<resources>/tex_remix/stage<N>/`. Rendre celles de
# `dc-decors/` montrerait ce qu'on a genere, pas ce qui s'affiche -- et les deux ont deja
# diverge d'une journee entiere sans qu'on le voie.
RESSOURCES = os.path.join(os.environ.get("APPDATA", ""), "CrowdedStreet", "3SX",
                          "resources", "tex_remix")

LISTES = {132: "plan LOINTAIN", 196: "plan PROCHE", 260: "3e plan", 324: "4e plan"}


def lire_liste(dossier, liste):
    """Le 1024x1024 d'un plan, recompose depuis ses 32 pages de 128x128."""
    import struct

    out = np.zeros((1024, 1024, 4), np.uint8)
    vues = 0

    for i in range(32):
        f = os.path.join(dossier, "%d-%d.tex" % (liste, liste + i))

        if not os.path.exists(f):
            continue

        d = open(f, "rb").read()

        if len(d) < 16 + 128 * 128 * 4:
            continue

        a = np.frombuffer(d[16:16 + 128 * 128 * 4], dtype=np.uint8).reshape(128, 128, 4).copy()
        a[:, :, [0, 2]] = a[:, :, [2, 0]]
        px, py = (i & 7) * 128, 512 + (i >> 3) * 128
        out[py:py + 128, px:px + 128] = a
        vues += 1

    return out if vues else None


def planche_stage(etage, fiches, zoom=1):
    """Les plans d'un etage cote a cote, plus la liste de ce qui est pose dessus."""
    dossier = os.path.join(RESSOURCES, "stage%d" % etage)

    if not os.path.isdir(dossier):
        return None

    plans = []
    for liste, nom in LISTES.items():
        p = lire_liste(dossier, liste)
        if p is None:
            continue
        # seule la moitie basse porte le plan (`ecrire_liste` y ecrit les 32 pages)
        bas = p[512:]
        n = int((bas[:, :, 3] > 0).sum())
        plans.append((nom, liste, bas, n))

    if not plans:
        return None

    ech = 2  # une demi-banque fait 1024x512 : trop large a l'echelle 1
    larg = 1024 // ech
    haut = 512 // ech
    marge, hen = 12, 34
    W = marge + len(plans) * (larg + marge)
    H = hen + haut + 22 + marge

    img = Image.new("RGB", (W, H), FOND)
    d = ImageDraw.Draw(img)
    d.text((marge, 8), "ETAGE %d  --  %d plan(s), %d objet(s) anime(s)"
           % (etage, len(plans), len(fiches)), fill=TEXTE)

    x = marge
    for nom, liste, bas, n in plans:
        vue = np.zeros((haut, larg, 3), np.uint8)
        vue[:, :] = (12, 12, 16)
        sous = bas[::ech, ::ech]
        op = sous[:, :, 3] > 0
        vue[op] = sous[:, :, :3][op]
        img.paste(Image.fromarray(vue, "RGB"), (x, hen))
        d.text((x, hen - 14), "%s  (liste %d)  %d px" % (nom, liste, n), fill=TEXTE)
        x += larg + marge

    return img


def planche_asset(bg, zoom=1, largeur=1700, poses=()):
    """TOUS les sprites de l'asset d'un decor, numerotes, les poses encadres en vert.

    C'EST LA REPONSE A « OU SONT LES SPRITES MANQUANTS ». L'asset `F_ETC` contient
    l'integralite des sprites du decor -- 602 pour Yang, dont le port n'en pose que trois.
    Nul besoin d'une capture pour les retrouver : ils sont tous ici, il suffit de les
    regarder et de dire lesquels manquent a l'ecran.
    """
    import assemblage as A
    import bases as B
    import fetc
    import poser2i as PO

    chemin = os.path.join(RACINE, "sprites", B.ASSETS[bg])
    a = fetc.lire(open(chemin, "rb").read())
    tuiles = A.charger(chemin)[1]
    banque = PO.banque_des_palettes()
    base = B.BASES_2I[bg]
    resoudre = lambda dr, off: B.numero(bg, dr, off)

    vignettes = []
    for i, sp in enumerate(a["sprites"]):
        try:
            pose = A.poser_couleur(sp, tuiles, banque, base[min(base)], resoudre)
        except Exception:
            pose = None

        if pose is None:
            continue

        rgba = pose[0]

        if rgba.shape[0] < 4 or rgba.shape[1] < 4:
            continue

        if (rgba[:, :, 3] > 0).sum() < 24:
            continue

        vignettes.append((i, Image.fromarray(rgba, "RGBA")))

    if not vignettes:
        return None, 0

    marge, hetiq = 8, 12
    lignes, cur, x, h = [], [], marge, 0
    for i, v in vignettes:
        lv = max(v.width, 34) + marge
        if x + lv > largeur and cur:
            lignes.append((cur, h))
            cur, x, h = [], marge, 0
        cur.append((i, v, x))
        x += lv
        h = max(h, v.height)
    if cur:
        lignes.append((cur, h))

    H = 30 + sum(hh + hetiq + marge for _c, hh in lignes) + marge
    img = Image.new("RGB", (largeur, H), FOND)
    d = ImageDraw.Draw(img)
    d.text((marge, 8), "%s  --  %d sprites dans l'asset %s  (%d dessinables)"
           % (bg, len(a["sprites"]), B.ASSETS[bg], len(vignettes)), fill=TEXTE)

    y = 30
    for k, (cases, hh) in enumerate(lignes):
        if k % 2:
            d.rectangle([0, y - 3, largeur, y + hh + hetiq + marge - 3], fill=FOND2)
        for i, v, x in cases:
            img.paste(v, (x, y), v)
            d.text((x, y + hh + 1), str(i), fill=TEXTE)
        y += hh + hetiq + marge
    return img, len(vignettes)


# Les etages de 2nd Impact : les quinze d'origine plus les deux bandes montees a part.
# New Generation occupe 37 a 55, et on peut vouloir ne regenerer que l'un des deux jeux.
ETAGES_2I = set(range(22, 37)) | {56, 57}


def main():
    quoi = sys.argv[1] if len(sys.argv) > 1 else "animes"
    seul_2i = "2i" in sys.argv[1:]
    garde = (lambda e: e in ETAGES_2I) if seul_2i else (lambda e: True)
    os.makedirs(SORTIE, exist_ok=True)
    src = Source()
    fiches = src.fiches()
    print("%d fiches lues dans decor_objets_data.c" % len(fiches))

    par_etage = {}
    for f in fiches:
        par_etage.setdefault(f["etage"], []).append(f)

    if quoi in ("animes", "tout"):
        for etage in sorted(e for e in par_etage if garde(e)):
            img = planche_animes(src, etage, par_etage[etage])
            chemin = os.path.join(SORTIE, "animes-etage%02d.png" % etage)
            img.save(chemin)
            print("   etage %2d : %2d objets  ->  %s"
                  % (etage, len(par_etage[etage]), os.path.basename(chemin)))

    if quoi in ("stages", "tout"):
        print()
        manquants = []
        for etage in [e for e in range(22, 58) if garde(e)]:
            img = planche_stage(etage, par_etage.get(etage, []))

            if img is None:
                manquants.append(etage)
                continue

            chemin = os.path.join(SORTIE, "stage%02d.png" % etage)
            img.save(chemin)
            print("   etage %2d  ->  %s" % (etage, os.path.basename(chemin)))

        if manquants:
            print()
            print("   AUCUNE PAGE DEPLOYEE pour les etages : %s"
                  % ", ".join(str(e) for e in manquants))
            print("   (le jeu n'a donc rien a substituer sur ces etages-la)")

    if quoi in ("assets", "tout"):
        import bases as B

        print()
        for bg in sorted(B.ASSETS):
            try:
                img, n = planche_asset(bg)
            except Exception as exc:
                print("   %-5s : %s" % (bg, exc))
                continue

            if img is None:
                print("   %-5s : rien de dessinable" % bg)
                continue

            chemin = os.path.join(SORTIE, "asset-%s.png" % bg)
            img.save(chemin)
            print("   %-5s : %4d sprites dessinables  ->  %s"
                  % (bg, n, os.path.basename(chemin)))


if __name__ == "__main__":
    main()
