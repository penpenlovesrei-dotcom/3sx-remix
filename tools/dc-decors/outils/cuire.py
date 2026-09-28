# -*- coding: utf-8 -*-
"""Cuit les sprites de decor dans le plan, puis decoupe les quinze etages pour 3SX.

C'est la suite directe de `elements.py`. Les plans de sprites qu'il rend sont dans le
**meme repere de 1024x1024** que la banque `.pvc` : il n'y a donc rien a recadrer, rien
a mettre a l'echelle, et surtout **rien a arbitrer entre le plan lointain et le plan
proche** -- c'est le `y` d'un sprite qui decide de quel cote de la coupe a `y = 512` il
tombe, exactement comme pour les pixels du fond.

    banque .pvc  ->  on y pose les sprites  ->  coupe a y = 512  ->  32 + 32 pages .tex

Les pages sortent dans `etages2i-sprites/stageNN`, a cote de `etages2i/stageNN` qui
reste intact : les deux jeux de decors cohabitent, et le lanceur choisit.

    python cuire.py             # les quinze etages
    python cuire.py bg03        # un seul
    lanceur : ..\\Le jeu avec decors et sprites.cmd
"""
import glob, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

import bande3sx
import elements as X
import pools as P
import pvc
from rendupvc import carte_morton, SIDE

ICI    = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
SORTIE = os.path.join(RACINE, "etages2i-sprites")

# etage, decor, banque du plan lointain. Le meme casting que `etages2i/`, releve dans
# RELAIS.md : quatre decors prennent leur lointain dans la banque 1, leur banque 0 etant
# une seule bande continue.
ETAGES = [
    (22, "bg00", 0), (23, "bg01", 0), (24, "bg02", 0), (25, "bg03", 0),
    (26, "bg04", 0), (27, "bg05", 0), (28, "bg06", 0), (29, "bg07", 1),
    (30, "bg09", 1), (31, "bg0a", 1), (32, "bg0b", 0), (33, "bg0c", 0),
    (34, "bg0d", 0), (35, "bg0e", 0), (36, "bg0f", 1),
]

# Le plan `j` prend les emplacements `j*64 + 132` : les listes se deduisent.
LISTE_LOINTAIN, LISTE_PROCHE, LISTE_TIERS, LISTE_QUATRE = 132, 196, 260, 324
PLEIN = 0xFFFFFFFF

# La bande REELLEMENT visible : les rangees de pages 2 et 3, mesurees deux fois dans le
# jeu (decor de Ken, puis pages colorees et numerotees de l'etage 22).
BANDE_VUE = 0x0000FFFF

# Quels plans de 2nd Impact partent sur le TROISIEME plan de 3SX.
#
# Ce sont les plans dont le coefficient n'est ni celui du ciel ni celui du sol. Pour
# `bg00` : le plan 3 (le temple d'horizon et les obelisques, objet 2, coefficient
# 0,875) et le plan 7 (le petit obelisque, objet 6, 0,625). Les poser sur le plan
# lointain, qui suit l'objet 0 a 0,25, les faisait deriver a gauche ; les cuire dans le
# plan proche les mettait au premier plan. Ils ont maintenant leur plan a eux --
# `bg220_speed_x_tiers` / `bg220_speed_y_tiers` dans `bg220.c`.
PLANS_TROISIEME = {
    "bg00": {3},
    "bg01": {3},
    "bg09": {3},
    "bg0e": {3},
}

# Et le QUATRIEME. Il n'existe que depuis que l'etage a sa propre archive : `scr_trans(3)`
# etait confisque par l'effet d'aube, dont le bit n'est mis que par `effd3.c`.
# Pour `bg00` c'est le plan 7 -- le petit obelisque gris, objet 6, 0,625 en x.
PLANS_QUATRIEME = {
    "bg00": {7},
}
TROISIEME = {}
QUATRIEME = {}


# Quels plans d'affichage partent dans la moitie LOINTAINE de la banque.
#
# Ce n'est PAS une regle : c'est une table remplie a l'oeil, decor par decor, sur ce
# qu'on voit dans le jeu. L'indice de plan n'ordonne pas la profondeur de la meme facon
# d'un decor a l'autre -- le pilier d'Urien est sur le plan 3 et il est au PREMIER plan,
# les immeubles d'Alex sont sur le plan 3 et ils sont au fond. La vraie mesure, qui
# reste a faire, est la correspondance plan d'affichage <-> objet de fond (les
# coefficients de parallaxe, 0,75 pour le lointain et 1,0 pour le proche).
#
# Ce qui est ici a ete constate dans le jeu :
#   bg01  le plan 3 porte les immeubles de la ville, qui sont derriere le toit
#   bg03  le plan 1 porte l'interieur sombre de la boutique, qui est derriere la rue
PLANS_LOINTAINS = {
    # Un plan de 2I dont le coefficient EGALE celui de l'objet 0 n'a pas besoin d'un
    # plan a lui : il va sur la moitie lointaine, contre le fond qui defile comme lui.
    # Calcule par `etages.py` depuis les coefficients du binaire, plus a l'oeil.
    #
    # bg01 en est SORTI : son plan 3 est a 0,8125 quand son objet 0 est a 0,625 --
    # il a donc son propre plan maintenant, et la ligne de sol bricolee de
    # `SOL_LOINTAIN` ne le concerne plus.
    "bg03": {1},
    "bg0a": {1},
}

# bg03 plan 1 (l'interieur sombre de la boutique) a ete essaye en lointain : il se
# retrouve en plein ciel, la ou la bande lointaine n'a plus d'art. Laisse au sol, ou il
# n'est qu'un rectangle sombre derriere les etals. A revoir quand la correspondance
# plan <-> objet de fond sera mesuree.


# La ligne du sol de la moitie LOINTAINE. Par defaut `sol(bas) - 512`, et c'est LU :
#
#   `decouper` envoie la rangee r d'une moitie sur la page r >> 7 de son plan, et
#   `scr_trans` pose la page i des DEUX plans au meme `y = 512 + (i >> 3) * 128`. La
#   rangee r de la moitie haute tombe donc au meme endroit de l'ecran que la rangee r
#   de la moitie basse. Une ligne de sol commune s'ecrit `g` dans l'une, `g - 512`
#   dans l'autre.
#
# Et elle est bien commune : `defil_y` vaut 766 pour les plans 1, 2, 3 et 7, de bg00
# comme de bg01. Le meme decalage vertical, donc la meme reference -- les sprites du
# plan lointain se posent sur le sol du plan proche, pas sur celui de leur propre art.
#
# `sol(d, "haut")`, la derniere ligne non vide de la moitie haute, ne decrit que l'art
# du FOND de cette bande. Pour bg00 elle rend 431 au lieu de 511 : quatre-vingts lignes
# trop haut, et c'est ce qui mettait le temple et les obelisques en haut de l'ecran.
SOL_LOINTAIN = {
    # bg01 garde la valeur avec laquelle ses immeubles ont ete VERIFIES a l'ecran
    # (`sol(haut)` = 479, trente-deux lignes au-dessus de la regle). A reprendre avec
    # une capture, pas avant : ce plan-la marche.
    "bg01": 479,
}


def sol(decor, moitie="bas"):
    """La ligne du sol dans la banque : derniere ligne non vide de la moitie basse.

    `elem.y` et `m.y` d'un morceau sont des **hauteurs au-dessus du sol**, et le `109`
    du code de dessin est la ligne du sol **a l'ecran**. Pour poser un sprite dans le
    plan il faut donc la ligne du sol **dans la banque**, et elle se mesure au lieu de
    se supposer.
    """
    src = os.path.join(RACINE, "pvc-2i", decor + ".pvc")
    if not os.path.exists(src):
        src = os.path.join(RACINE, "pvc-ng", decor + ".pvc")
    if not os.path.exists(src):
        return None
    pages, _u, _ = pvc.decode(open(src, "rb").read())
    arr = bande3sx.banque_rgba(pages, 0, carte_morton(SIDE))[0]
    d = 512 if moitie == "bas" else 0
    lignes = np.where((arr[d:d + 512, :, 3] > 0).any(1))[0]
    return int(lignes.max()) + d if len(lignes) else None


def sols():
    out = {}
    for _e, d, _b in ETAGES:
        g = sol(d, "bas")
        if g is None:
            continue
        loin = PLANS_LOINTAINS.get(d)
        if loin:
            gl = SOL_LOINTAIN.get(d, g - 512)
            out[d] = {None: g, **{p: gl for p in loin}}
        else:
            out[d] = {None: g}
    # bg08 et bg09 sont le meme etat releve : le casting ne garde que bg09.
    if "bg09" in out:
        out.setdefault("bg08", out["bg09"])
    return out


def plans_de_sprites(garder=None, g=None):
    """decor -> RGBA 1024x1024, tous les sprites d'un decor empiles.

    **Dans l'ordre de la liste d'affichage, pas par numero de plan.** La boucle de
    dessin `0x8C0F693C` parcourt les elements et dessine chacun aussitot : l'ordre de
    la liste EST l'ordre de dessin, et `plan` ne choisit que le defilement.

    Empiler par plan croissant -- ce que faisait cette fonction -- est faux partout :
    sur les vingt-six releves les deux ordres different a chaque fois. Pour `bg00`
    l'ordre de la liste est 0, 1, 7, 3, 2, 4, donc le petit obelisque du plan 7
    (element 2) se dessine AVANT le temple du plan 3 (element 4) et passe derriere.
    Le tri par plan le mettait devant.
    """
    ass = P.assets()
    out = {}
    global TROISIEME, QUATRIEME
    TROISIEME = {}
    QUATRIEME = {}
    for chemin in sorted(glob.glob(os.path.join(X.DOS, X.MOTIF))):
        couches = []
        decors, rapport, _fiches, plans = X.rend_etat(chemin, ass, g, couches)
        if not plans:
            continue
        img = np.zeros((1024, 1024, 4), np.uint8)
        # Le TROISIEME plan de 3SX : les plans de 2I qu'aucun objet de fond ne pilote,
        # donc statiques. Ils sortent de la cuisson -- ils ne sont plus peints dans le
        # fond, ils ont leur propre plan, avec `speed_x = 0`.
        tiers = np.zeros((1024, 1024, 4), np.uint8)
        quatre = np.zeros((1024, 1024, 4), np.uint8)
        loin3 = set()
        loin4 = set()
        for d in (decors or []):
            loin3 |= PLANS_TROISIEME.get(d, set())
            loin4 |= PLANS_QUATRIEME.get(d, set())
        for _i, p, couche in couches:
            if garder is not None and p not in garder:
                continue
            op = couche[:, :, 3] > 0
            if p in loin4:
                quatre[op] = couche[op]
            elif p in loin3:
                tiers[op] = couche[op]
            else:
                img[op] = couche[op]
        for d in (decors or []):
            if loin3:
                TROISIEME[d] = tiers
            if loin4:
                QUATRIEME[d] = quatre
            # Un etat peut porter deux decors -- `bg08-bg09` : les deux le recoivent.
            anc = out.get(d)
            if anc is None or (img[:, :, 3] > 0).sum() > (anc[:, :, 3] > 0).sum():
                out[d] = img
    return out


def main():
    args = sys.argv[1:]
    garder = None
    if "--plans" in args:
        i = args.index("--plans")
        garder = {int(v) for v in args[i + 1].split(",")}
        del args[i:i + 2]
    filtre = args[0] if args else None
    g = sols()
    print("ligne du sol, mesuree dans la banque : "
          + ", ".join(f"{d} {v[None]}"
                      + ("".join(f" (plan {p} -> {q})" for p, q in sorted((k, w) for k, w in v.items() if k is not None)))
                      for d, v in sorted(g.items())))
    surcouches = plans_de_sprites(garder, g)
    if garder is not None:
        print(f"seuls les plans {sorted(garder)} sont cuits")
    print(f"{len(surcouches)} decors ont des sprites : {', '.join(sorted(surcouches))}\n")
    os.makedirs(SORTIE, exist_ok=True)
    for etage, decor, bq_loin in ETAGES:
        if filtre and filtre != decor:
            continue
        sc = surcouches.get(decor)
        n = int((sc[:, :, 3] > 0).sum()) if sc is not None else 0
        print(f"etage {etage}  {decor}  "
              + (f"{n} pixels de sprites cuits" if n else "aucun sprite"))
        tiers = TROISIEME.get(decor)
        quatre = QUATRIEME.get(decor)
        # L'etage 22 emprunte desormais le bloc de l'etage 2 (Ryu), la seule archive a
        # TROIS plans avec celle de l'etage 14. Elle ne contient que 52 textures : on ne
        # peut donc pas masquer 32 pages par plan comme avec Yang, mais 16 par plan --
        # la bande vue -- soit 48, ce qui tient. Les autres etages gardent Yang et
        # leurs masques pleins.
        if tiers is not None:
            # Trois plans PLEINS : l'etage a sa propre archive de 96 pages
            # (`outils/archive.py`), il n'emprunte plus rien a personne.
            liste = [(LISTE_LOINTAIN, PLEIN, "haut", bq_loin),
                     (LISTE_PROCHE,   PLEIN, "bas",  0),
                     (LISTE_TIERS,    PLEIN, "bas",  0, tiers)]
            if quatre is not None:
                liste.append((LISTE_QUATRE, PLEIN, "bas", 0, quatre))
        else:
            liste = [(LISTE_LOINTAIN, PLEIN, "haut", bq_loin),
                     (LISTE_PROCHE,   PLEIN, "bas",  0)]
        bande3sx.decouper(
            decor, liste,
            os.path.join(SORTIE, f"stage{etage}"),
            surcouche=sc)
        if sc is not None:
            Image.fromarray(sc).save(
                os.path.join(RACINE, "rendus", "elements", f"cuit-{decor}.png"))
        print()


if __name__ == "__main__":
    main()
