# -*- coding: utf-8 -*-
"""Un apercu de l'etage tel que le jeu l'assemble : les trois plans, plus les objets.

Ce n'est pas une capture -- le defilement et la parallaxe ne sont pas simules -- mais
c'est assez pour voir si un objet tombe sur le chien ou sur son perchoir, et ca coute une
seconde au lieu d'un aller-retour avec la manette.

Les fiches sont relues dans `decor_objets_data.c`, donc c'est bien ce qui est compile qui
est dessine, et non ce que le generateur croit avoir ecrit.

    python apercu_etage.py            l'etage 31
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw

import annuaire_animes as AA
import assemblage as A
import bases
import poser2i as P
import situer_animes as S

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(RACINE, "rendus")
DATA = r"C:\Temp3sx\src\port\video\decor_objets_data.c"

BG = os.environ.get("APERCU_BG", "bg0a")
DECOR = int(os.environ.get("APERCU_DECOR", "9"))
ETAGE = int(os.environ.get("APERCU_ETAGE", "31"))

# Du plus loin au plus pres -- l'ordre de dessin, celui des `z` de `couches2i.py`.
ORDRE = [int(v) for v in os.environ.get("APERCU_LISTES", "132,260,196").split(",")]
FAMILLE_LISTE = {3: 260, 2: 196, 1: 132, 0: 132}

# On ne compte plus les champs dans une expression : le jour ou la fiche en a gagne un
# -- `variante` -- l'ancienne expression a cesse de coller, SANS RIEN DIRE, et l'apercu
# rendait un etage vide comme s'il n'avait pas d'objets. On prend donc l'accolade entiere
# et on la decoupe, ce qui survit a l'ajout d'un champ.
FICHE = re.compile(r'\{\s*"(\w+)",([^}]*)\}\s*,\s*/\*([^*]*)\*/')

# Le rang de chaque champ apres le nom, tel que `DecorAnimation` les declare.
ETAGE_, IMAGES_, TUILES_, COLS_, LIGS_ = 0, 1, 2, 3, 4
PAL_, BX_, Y_, FAMILLE_, Z_, BOUCLE_, VARIANTE_ = 8, 9, 10, 11, 12, 13, 14

# `-1` rend toutes les variantes, superposees -- utile pour voir ce que le tableau porte ;
# 0 a 3 rend ce que le jeu montrerait sur ce tirage.
VARIANTE = int(os.environ.get("APERCU_VARIANTE", "-1"))


def fiches(etage):
    """Les fiches de l'etage, lues dans le C -- donc ce qui est compile."""
    src = io.open(DATA, encoding="utf-8", errors="surrogateescape").read()
    out = []

    for m in FICHE.finditer(src):
        ch = [c.strip() for c in m.group(2).split(",")]

        if len(ch) <= VARIANTE_ or int(ch[ETAGE_]) != etage:
            continue

        masque = int(ch[VARIANTE_], 0)

        if VARIANTE >= 0 and masque and not masque & (1 << VARIANTE):
            continue

        out.append(dict(cols=int(ch[COLS_]), ligs=int(ch[LIGS_]),
                        bx=int(ch[BX_]), y=int(ch[Y_]),
                        famille=int(ch[FAMILLE_]), z=int(ch[Z_]),
                        variante=masque, note=m.group(3).strip()))

    return out


def image_de(script):
    """L'image 0 du script, en couleur, ou None."""
    a, tuiles = P.asset(bases.ASSETS[BG])
    lo = a["index_global"][0]
    ims = AA.script_images(DECOR, script) or []

    if not ims or not lo <= ims[0][0] < lo + len(a["anims"]):
        return None

    offs = sorted({r[4] for r in a["anims"]})
    n = offs.index(a["anims"][ims[0][0] - lo][4])
    resoudre = lambda dr, off: bases.numero(BG, dr, off)
    b = bases.BASES_2I[BG]
    pose = A.poser_couleur(a["sprites"][n], tuiles, P.banque_des_palettes(),
                           b[min(b)], resoudre)
    return None if pose is None else pose[0]


def main():
    src = os.path.join(RACINE, "etages2i-sprites", "stage%d" % ETAGE)
    plans = {l: P.lire_liste(src, l) for l in ORDRE}
    calques = {l: Image.fromarray(plans[l].copy(), "RGBA") for l in ORDRE}
    dess = {l: ImageDraw.Draw(calques[l]) for l in ORDRE}

    # UN OBJET LARGE EST DECOUPE EN MORCEAUX, une fiche par tranche de colonnes, et
    # toutes portent le meme commentaire. Chacune ne peint que SES colonnes : si on
    # redessine le sprite entier a chaque fiche, on croit voir l'objet en double -- ce
    # qui m'a fait chercher longtemps un doublon qui n'existait pas.
    depart = {}

    for f in fiches(ETAGE):
        sc = int(re.search(r"script (\d+)", f["note"]).group(1))
        rgba = image_de(sc)

        if rgba is None:
            continue

        x0 = f["bx"] - depart.setdefault(f["note"], f["bx"])
        rgba = rgba[:, x0:x0 + f["cols"] * 16]

        if rgba.shape[1] == 0:
            continue

        by = 1024 - f["y"] - (f["ligs"] - 1) * 16
        liste = FAMILLE_LISTE.get(f["famille"], 196)
        h, w = rgba.shape[:2]
        calques[liste].alpha_composite(Image.fromarray(np.ascontiguousarray(rgba), "RGBA"),
                                       (f["bx"], by))
        dess[liste].rectangle([f["bx"], by, f["bx"] + w - 1, by + h - 1],
                              outline=(255, 0, 255, 255))
        dess[liste].text((f["bx"] + 1, by - 10), "s%d" % sc, fill=(255, 255, 0, 255))
        print("script %-3d  liste %d  banque %4d,%-4d  %dx%d" % (sc, liste, f["bx"], by,
                                                                 w, h))

    fond = Image.new("RGBA", (1024, 1024), (0, 0, 0, 255))

    for l in ORDRE:
        fond.alpha_composite(calques[l])

    os.makedirs(SORTIE, exist_ok=True)
    chemin = os.path.join(SORTIE, "apercu-%d.png" % ETAGE)
    fond.save(chemin)
    fond.crop((512, 768, 1024, 1024)).resize((1024, 512), Image.NEAREST).save(
        os.path.join(SORTIE, "apercu-%d-droite.png" % ETAGE))
    fond.crop((0, 768, 512, 1024)).resize((1024, 512), Image.NEAREST).save(
        os.path.join(SORTIE, "apercu-%d-gauche.png" % ETAGE))
    print("\n%s" % chemin)


if __name__ == "__main__":
    main()
