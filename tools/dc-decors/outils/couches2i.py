# -*- coding: utf-8 -*-
"""Ecrit les COUCHES DE FOND d'un etage -- les demi-banques du `.pvc`, pas les sprites.

`poser2i.py` pose les elements ; celui-ci pose le fond. Il existe parce qu'un decor peut
porter plus de deux couches, et que le casting a deux plans en laissait tomber.

    bg0a (Oro, etage 31) : TROIS demi-banques non vides
        banque 0 haut   79 810 px   la grotte du fond      <- n'etait nulle part
        banque 0 bas   364 508 px   la grotte proche       liste 196
        banque 1 haut   76 032 px   le couchant            liste 132

    et TROIS objets de fond dans la table 0x8C1D4F48 :
        objet 0   x 0,75   y 0,875
        objet 1   x 1,00   y 1,00
        objet 2   x 0,50   y 0,9375

**Le plus lent est le plus loin.** Le couchant est donc l'objet 2 et non l'objet 0 : la
liste 132 le faisait defiler a 0,75, la vitesse de la grotte du fond, et la grotte du
fond, elle, n'etait expediee nulle part. C'est ce que Frederic a vu -- « les nuages roses
recouvrent un plan qui est cense etre devant ».

    liste 132  z 0x5E  le plus loin   le couchant       objet 2  0,5   / 0,9375
    liste 260  z 0x5A  au milieu      la grotte du fond objet 0  0,75  / 0,875
    liste 196  z 0x54  le plus pres   la grotte proche  objet 1  1,0   / 1,0

Les deux moities d'une meme banque s'alignent d'elles-memes : `scr_trans` pose la page i
de tous les plans au meme y, et `decouper` envoie la rangee r de la moitie haute et la
rangee r+512 de la moitie basse sur la meme page.

    python couches2i.py            # dit ce qu'il ferait
    python couches2i.py --ecrire
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import bande3sx
import etages as E
import pvc
from rendupvc import carte_morton, SIDE

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)

LISTE_LOINTAIN, LISTE_PROCHE, LISTE_TIERS = 132, 196, 260

# Les etages dont la bande porte plus de deux couches.
#
# `loin`, `tiers` et `proche` : (banque, moitie, objet de la table 0x8C1D4F48). L'objet
# fixe la vitesse ; c'est `etages.py` qui la sort dans l'include C.
# SIX DECORS ONT TROIS COUCHES, PAS UN SEUL -- corrige le 30/08/2026.
#
# Le releve est mecanique : on compte les demi-banques non vides des deux banques du
# `.pvc`. Six decors en ont trois, et `couches2i.py` n'en traitait qu'UN. Les cinq autres
# perdaient leur couche du milieu depuis le debut -- c'est le « decor mal assemble » que
# Frederic a vu sur Akuma.
#
#     bg05 Necro   b0 haut 483696  b0 bas 113470  b1 haut 114688
#     bg06 Hugo    b0 haut 454516  b0 bas 320502  b1 haut 327865
#     bg07         b0 haut 296774  b0 bas 205600  b1 haut 277156
#     bg09 Ibuki   b0 haut 413696  b0 bas 291964  b1 haut 460800
#     bg0a Oro     b0 haut  79810  b0 bas 364508  b1 haut  76032
#     bg0f Akuma   b0 haut 196101  b0 bas 232770  b1 haut 274432
#
# L'ORDRE VIENT DES COEFFICIENTS, pas de l'oeil : le plus lent est le plus loin.
# La table 0x8C1D4F48 donne trois objets par decor, et les six suivent le meme schema --
# objet 1 a 1,0 (le plan proche), objet 0 autour de 0,75 (le milieu), objet 2 le plus lent
# (le fond). D'ou la meme repartition pour tous :
#
#     liste 132  le plus loin   banque 1 haut   objet 2
#     liste 260  au milieu      banque 0 haut   objet 0
#     liste 196  le plus pres   banque 0 bas    objet 1
# ATTENTION : UNE DEMI-BANQUE NON VIDE N'EST PAS FORCEMENT UNE COUCHE.
#
# La banque 1 haut d'Akuma porte **six variantes de la meme cascade** et un petit rectangle
# aux braises orange : ce n'est pas un plan de fond, c'est un MAGASIN D'IMAGES D'ANIMATION.
# Le decor a des trous -- a gauche pour la cascade, au centre pour l'entree de la grotte --
# et ces pages viennent les remplir tour a tour. La poser comme couche donne la mosaique de
# cascades et les rectangles noirs que Frederic a vus.
#
# Le tri se fait a l'oeil sur le contenu, pas sur le compte de pixels : une couche est une
# image continue, un magasin est fait de vignettes repetees.
#
# `bg09` (Elena) N'Y EST PLUS -- 16/09/2026. La table des couches de 2I (`etages.TABLE_COUCHES`)
# ne dessine pas sa banque 1 haut : c'est la reserve de la cascade (animation de pages 0).
# Ses listes 132 et 260 sont ecrites par `statiques2i.py`.
#
TROIS = ("bg05", "bg06", "bg07", "bg0a")

# `bg07` (Ibuki) GARDE SES COUCHES -- la liste k est bien la couche k de 2I, et `etages.py`
# en tire les profondeurs --, MAIS SES PAGES NE S'ECRIVENT PLUS ICI -- 16/09/2026. Sa banque
# est un atlas que le moteur de decor pose rectangle par rectangle : ses trois listes
# viennent de `statiques2i.py --ibuki`, qui suit le descripteur (`descripteurs2i.py`).
COMPOSES = ("bg07",)

COUCHES = {
    bg: {
        LISTE_LOINTAIN: (1, "haut", 2),
        LISTE_TIERS:    (0, "haut", 0),
        LISTE_PROCHE:   (0, "bas",  1),
    }
    for bg in TROIS
}

# AKUMA : deux couches seulement, et sa banque 1 est un magasin d'images.
# Son fond est la canopee (banque 0 haut), son premier plan le rocher et la barque.
COUCHES["bg0f"] = {
    LISTE_LOINTAIN: (0, "haut", 2),
    LISTE_PROCHE:   (0, "bas",  1),
}

ETAGE = {decor: etage for etage, decor, _n in E.ETAGES}
DECOR_N = {decor: n for _e, decor, n in E.ETAGES}


# IBUKI N'EST PLUS FABRIQUE ICI -- 16/09/2026.
#
# On y avait lu un plan qui garde sa reserve hors champ (31/08), puis un ciel decale de 128
# trouve en bouchant des vides (16/09). Les deux etaient faux : le descripteur de 2I pose le
# ciel en x 192 et UNE seule vue de la cascade, et le temple est dans la couche du milieu
# (`descripteurs2i.py`). Le vide que le decalage bouchait venait de la mosaique elle-meme.
FABRIQUER = {}

#   (decor, banque, moitie) -> colonnes
DECALAGE = {}


def tranches(decor, banque, moitie):
    """Ce que la couche dessine VRAIMENT -- et pourquoi on ne le coupe pas.

    UNE COUCHE NE DESSINE PAS TOUTE LA DEMI-BANQUE -- 24/09/2026, demande par Frederic :
    « corrige couches2i.py qui ecrit la demi-banque entiere comme couche partout, ce qui est
    une regle fausse ». Elle est fausse, en effet. Mais la corriger en coupant la page le
    serait davantage, et la mesure le dit.

    LE FORMAT, LU. Le morceau d'une couche (`0x8C601EE8`, trois mots, poses par
    `0x8C10B070` en +6, +8 et +10 d'un enregistrement de 16 octets) est un morceau de sprite
    deja resolu, dont `etat2.py` donne les champs contre le desassemblage :

        +6 = y      +8 = (hauteur-1) << 8 | (largeur-1)      +10 = code

    La tranche est donc `[y - hauteur + 1, y]`, et le controle est immediat :

        decor 9 couche 1 : y 127, 255 … 1023, hauteur 128  ->  0..1023, sans trou
        decor 8 couche 0 : y 127…511 puis 895, 1023        ->  un TROU de 512 a 767
        decor 6 couche 0 : y 255 (h 112), 383, 511         ->  144..511

    Si `y` etait un HAUT de tranche, le premier cas deborderait de 127 lignes. Il ne
    deborde pas : c'est un BAS.

    POURQUOI ON NE COUPE PAS. Croisees avec les lignes REELLEMENT peintes de chaque
    demi-banque, les tranches ne sont pas des lignes de banque :

        | couche          | lignes peintes | tranches        | pixels dans les tranches |
        |-----------------|----------------|-----------------|--------------------------|
        | bg0a k0 (Oro)   | 0..431         | 64..207         | **0 %**                  |
        | bg0a k2 (Oro)   | 304..411       | 64..207         | **0 %**                  |
        | bg05 k2 (Necro) | 288..399       | 128..255        | **0 %**                  |
        | bg08 k1 (Elena) | 0..511         | 382..383        | **0 %**                  |
        | bg06 k0 (Hugo)  | 0..511         | 144..511        | 71 %                     |
        | la plupart      | —              | 0..511          | 100 %                    |

    **Zero pour cent.** Couper aurait efface tout le fond d'Oro -- le couchant et la grotte
    --, que Frederic a valide en septembre. Une couche ne peut pas dessiner 0 % de sa
    demi-banque : la tranche n'est donc pas un intervalle de lignes de la BANQUE.

    Ce qu'elle est, la mesure le suggere : une BANDE D'ECRAN. `bg05 k2` a une tranche de
    128 lignes pour un contenu de 112, `bg0a k0` une de 144 pour 432 : la tranche donne ou
    le plan peint, et le defilement y fait passer la banque. Modeliser ca -- un plan qui ne
    peint qu'une bande de l'ecran -- est un autre chantier, et il faudra une observation
    pour le lancer.

    En attendant, cette fonction MESURE et se tait sur le reste : elle rend les tranches, et
    signale les couches dont la tranche ne couvre pas 0..511. La regle fausse est desormais
    bornee et ecrite, ce qui vaut mieux qu'une coupe qui casserait cinq decors.
    """
    import etages as E

    k = banque * 2 + (1 if moitie == "bas" else 0)
    t = E.morceaux_couche(int(decor[2:], 16), k)

    if not t:
        return None

    bandes = [(y - h + 1, y) for y, h in t]
    couvre = set()

    for a, b in bandes:
        couvre.update(range(max(a, 0), min(b, 511) + 1))

    if len(couvre) < 512:
        print("   %s couche %d : la couche ne peint que %s -- NON coupee, voir `tranches`"
              % (decor, k, bandes))

    return bandes


def demi_banque(decor, banque, moitie):
    """Les 512 lignes voulues, dans un 1024x1024 pret pour `ecrire_liste`."""
    src = os.path.join(RACINE, "pvc-2i", decor + ".pvc")
    pages, _u, _ = pvc.decode(open(src, "rb").read())
    arr = bande3sx.banque_rgba(pages, banque * 4096, carte_morton(SIDE))[0]
    demi = arr[:512] if moitie == "haut" else arr[512:]

    # LE MEME RECALAGE QUE `poser2i.banque_nue` -- voir le commentaire la-bas.
    #
    # Douze decors sur quatorze posent le bas de leur dessin sur la ligne 1023 ; `bg0d` le
    # laisse a 1007 et `bg05` a 972, et leur decor entier apparait d'autant trop haut. Sans
    # cette ligne, les pages cuites ICI garderaient l'ancien calage pendant que les objets
    # animes, eux, seraient poses sur 1023 : les deux se separeraient.
    if moitie == "bas":
        import poser2i as P

        d = P.decalage_sol(decor, banque * 4096)

        if d:
            neuf = np.zeros_like(demi)
            neuf[d:] = demi[:512 - d]
            demi = neuf

    f = FABRIQUER.get((decor, banque, moitie))

    if f is not None:
        demi = demi.copy()
        # on releve les trames AVANT d'effacer, sinon on poserait du vide
        trames = [(demi[sy:sy + h, sx:sx + w].copy(), dx, dy)
                  for sx, sy, w, h, dx, dy in f["poser"]]

        for x, y, w, h in f["effacer"]:
            demi[y:y + h, x:x + w] = 0

        for t, dx, dy in trames:
            h = min(t.shape[0], 512 - dy)
            w = min(t.shape[1], 1024 - dx)
            coin = demi[dy:dy + h, dx:dx + w]
            op = t[:h, :w, 3] > 0
            coin[op] = t[:h, :w][op]

    d = DECALAGE.get((decor, banque, moitie))

    if d:
        demi = np.roll(demi, d, axis=1)

    tranches(decor, banque, moitie)

    out = np.zeros((1024, 1024, 4), np.uint8)
    out[512:] = demi
    return out


# LE JEU NE LIT PAS `etages2i-sprites/`, IL LIT SES RESSOURCES.
#
# `tex_remix.c` cherche ses pages dans `<resources>/tex_remix/stage<N>/<liste>-<n>.tex`.
# Ecrire dans le dossier de travail sans recopier la-bas ne change rien a l'ecran : c'est
# ce qui a fait croire que la troisieme couche d'Akuma etait posee alors qu'elle ne l'etait
# pas. On ecrit donc AUX DEUX endroits.
RESSOURCES = os.path.join(os.environ.get("APPDATA", ""), "CrowdedStreet", "3SX",
                          "resources", "tex_remix")


def ecrire_liste(sortie, plan, liste):
    dossiers = [sortie]
    etage = os.path.basename(sortie)

    if os.path.isdir(RESSOURCES):
        dossiers.append(os.path.join(RESSOURCES, etage))

    for d in dossiers:
        os.makedirs(d, exist_ok=True)

        for i in range(32):
            px, py = (i & 7) * 128, 512 + (i >> 3) * 128
            bande3sx.ecrire_tex(os.path.join(d, "%d-%d.tex" % (liste, liste + i)),
                                plan[py:py + 128, px:px + 128])


def main():
    ecrire = "--ecrire" in sys.argv
    for decor, couches in sorted(COUCHES.items()):
        etage = ETAGE[decor]
        sortie = os.path.join(RACINE, "etages2i-sprites", "stage%d" % etage)
        print("etage %d  %s" % (etage, decor))
        for liste, (bq, moitie, objet) in sorted(couches.items()):
            plan = demi_banque(decor, bq, moitie)
            n = int((plan[:, :, 3] > 0).sum())
            cx, cy = E.coefs_objet(DECOR_N[decor], objet)
            print("   liste %3d  <-  banque %d %-4s  %6d px  objet %d  %.4g / %.4g"
                  % (liste, bq, moitie, n, objet, cx / 65536, cy / 65536))
            if ecrire and liste != LISTE_PROCHE and decor not in COMPOSES:
                # La 196 porte les elements poses par `poser2i.py` : on n'y touche pas.
                ecrire_liste(sortie, plan, liste)
                print("      ecrit")
    if not ecrire:
        print("\nRien n'a ete ecrit. `--ecrire` pour poser les pages.")


if __name__ == "__main__":
    main()
