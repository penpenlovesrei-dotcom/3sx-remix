# -*- coding: utf-8 -*-
"""Les pages des dix-neuf etages de New Generation, en `.tex` pour `tex_remix`.

Meme mecanique que `couches2i.py` : on ecrit AUX DEUX endroits, le dossier de travail et
les ressources du jeu -- ecrire seulement dans le premier ne change rien a l'ecran.

L'affectation des demi-banques aux listes vient de `etagesng.fiche()`, qui applique la
regle verifiee sur Oro : la demi-banque d'ordre k porte l'objet k, et le plan le plus
lointain est celui de plus petit coefficient.

LA PAGE D'UNE COUCHE EST CELLE QUE LE DREAMCAST DESSINE -- 17/09/2026. Elle n'est plus la
demi-banque nue : `descripteursng.page()` pose les rectangles que le moteur de decor de NG
choisit pour la couche k (l'objet k), dans l'etat de depart des routines qui l'animent. Les
cases qu'une animation de pages doit servir en entier (`pagesng.evidees`) sont retirees.

ET ON ECRIT DANS LES RESSOURCES DE SEPTEMBRE, PAS DANS `%APPDATA%` : un processus lance par
l'agent y ecrit dans le conteneur de l'application Claude, invisible au jeu (REPRISE,
regle 12). Le lanceur de Frederic recopie ensuite ces pages dans le vrai `%APPDATA%`.
"""

import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
sys.path.insert(0, ICI)

import numpy as np

import bande3sx
import couches2i
import descripteursng
import etagesng
import pagesng
import pvc
from rendupvc import SIDE, carte_morton

LISTE_LOINTAIN, LISTE_PROCHE, LISTE_TIERS = 132, 196, 260
RESSOURCES = r"C:\Users\frede\OneDrive\Bureau\SEPTEMBRE\SF3\CrowdedStreet-3SX\resources\tex_remix"


def demi_banque(bande, banque, moitie):
    """Les 512 lignes voulues, dans un 1024x1024 pret pour `ecrire_liste`."""
    src = os.path.join(RACINE, "pvc-ng", "bg_set%02x.pvc" % bande)
    pages, _u, _ = pvc.decode(open(src, "rb").read())
    arr = bande3sx.banque_rgba(pages, banque * 4096, carte_morton(SIDE))[0]
    demi = arr[:512] if moitie == "haut" else arr[512:]
    out = np.zeros((1024, 1024, 4), np.uint8)
    out[512:] = demi
    return out


def page_decrite(bande, objet, choix=None, decalage=None):
    """La page de la couche `objet`, telle que le moteur de NG la dessine.

    `choix` et `decalage` servent aux VUES d'un plan anime (`plansng.py`) : la meme page,
    dans un autre etat de ses routines."""
    plan = descripteursng.page(bande, objet, choix, decalage)
    for couche, cases in pagesng.evidees(bande):
        if couche == objet:
            for lig, col in cases:
                plan[512 + lig * 16:512 + lig * 16 + 16, col * 16:col * 16 + 16] = 0
    return plan


def ecrire_liste(sortie, plan, liste):
    for d in (sortie, os.path.join(RESSOURCES, os.path.basename(sortie))):
        os.makedirs(d, exist_ok=True)
        for i in range(32):
            px, py = (i & 7) * 128, 512 + (i >> 3) * 128
            bande3sx.ecrire_tex(os.path.join(d, "%d-%d.tex" % (liste, liste + i)),
                                plan[py:py + 128, px:px + 128])


def recoller(pages, f):
    """Deux couches qui se touchent sans se recouvrir laissent passer une ligne.

    MESURE DU 22/09/2026, sur la capture de Frederic. Le decor de GILL montrait une ligne
    de pixels en bas d'ecran (ligne 175 des 224, 290 colonnes sur 384). Sa couleur
    moyenne etait (213, 119, 76) -- de la lave --, celle des lignes juste au-dessus et
    juste en dessous (90, 38, 15) -- de la roche. La correlation entre la ligne et ses
    voisines est nulle (0,1 a 0,3) : ce n'est pas un melange, c'est UNE AUTRE COUCHE.

    Et elle se lit dans les pages : l'horizon de Gill peint jusqu'a la ligne de scene 959
    et plus rien apres ; le sol commence a 960 et rien avant. Il suffit alors d'un pixel
    de jeu dans l'arrondi du moteur pour ouvrir une fente, et par la fente on voit le
    plan de derriere.

    COLONNE PAR COLONNE DEPUIS LE 22/09 AU SOIR. La version d'avant ne regardait que les
    bornes GLOBALES d'une couche, donc le seul cas de Gill. Or les memes fentes existent
    sur une poignee de colonnes ailleurs : le petit rectangle noir d'ALEX pres de la rampe
    de l'escalier (ligne 110, colonnes 266 a 273 -- le « vers x 268 » du verdict du
    18/09), une ligne chez Dudley 1 et une chez Elena 1. On comble donc, par colonne, tout
    intervalle d'au plus quatre lignes entre le bas d'une couche et le haut d'une autre,
    en recopiant vers le haut le premier pixel peint de la couche LA PLUS PROCHE.

    Quatre lignes, pas plus : au-dela ce n'est plus une fente mais un vrai trou de decor.

    ON N'A PAS ENCORE DE REGLE POUR CES TROUS-LA. Prolonger le fond opaque vers le bas
    (l'essai du 22/09 au soir) donne un aplat de la couleur de sa derniere ligne : chez
    Sean le biseau noir est devenu BLEU, et Frederic a tranche -- « correction tres
    mauvaise ». Retire. Sa piste, a reprendre : les arriere-plans sont peut-etre tout
    simplement mal POSITIONNES en vertical -- voir descripteursng.DECALAGE_Y, les 80 lignes
    dont le ciel de Gill est descendu sans qu'on sache pourquoi)."""
    z = dict(zip((LISTE_LOINTAIN, LISTE_PROCHE, LISTE_TIERS), f["z"]))
    bornes = {}

    for liste, plan in pages.items():
        op = plan[:, :, 3] > 0
        haut = np.where(op.any(axis=0), op.argmax(axis=0), -1)
        bas = np.where(op.any(axis=0), 1023 - op[::-1].argmax(axis=0), -1)
        bornes[liste] = (haut, bas)

    for loin, (_h, bas) in bornes.items():
        for pres, (haut, _b) in bornes.items():
            # un z PLUS PETIT est plus proche : seule la couche proche peut recouvrir
            if pres == loin or z.get(pres, 0) >= z.get(loin, 0):
                continue

            n, colonnes = 0, 0

            for col in range(1024):
                b, h = int(bas[col]), int(haut[col])

                # `h == b + 1` : les deux couches se TOUCHENT sans se recouvrir -- on
                # donne quand meme une ligne de recouvrement (le cas de Gill). Au-dela,
                # c'est une fente, et on la comble jusqu'a quatre lignes.
                if b < 0 or h < 0 or h <= b or h > b + 5:
                    continue

                pages[pres][b:h, col] = pages[pres][h, col]
                n += h - b
                colonnes += 1

            if n:
                print("   JONCTION : la liste %d rejoint la liste %d sur %d colonnes"
                      " (%d pixels)" % (pres, loin, colonnes, n))


# LA COUCHE LA PLUS LOINTAINE N'A RIEN DERRIERE ELLE -- 28/09/2026
# -----------------------------------------------------------------
# Frederic, le 28/09 : « ALEX une ligne noire en arriere plan notifiee plein de fois mais
# jamais traitee ». Mesure, sur les pages que le jeu charge :
#
#     banque 0 de bg_set01, le quart que la couche 2 dessine (u 512..1023, v 0..255) :
#     43 520 px peints, tous dans u 560..831, v 0..159. Le reste du rectangle est VIDE.
#
# Le plan le plus lointain d'Alex est donc un timbre de 272 x 160 dans une page de
# 1024 x 512. Partout ou les deux plans plus proches ne couvrent pas, l'ecran montre le
# noir -- et l'endroit le plus visible est la ruelle entre les deux immeubles du fond
# (scene x 779..807), un trait de deux a trois colonnes sur 240 lignes : LA ligne noire.
#
# Ce fichier le disait deja, sans en tirer la consequence (note du drapeau +17) :
# « ces couches n'ont rien derriere elles, un trou y montre deja du noir ».
#
# La meme famille de defaut revient sur la liste du 28/09 : « KEN variant bain a ciel
# ouvert : les extremites gauche et droite ne sont pas affichees (decor pas assez large) »,
# et le docstring de `descripteursng` garde « KEN ciel a droite manquant », « ORO le ciel ne
# couvre pas toute la zone ». C'est chaque fois le plan du fond qui s'arrete avant le bord.
#
# ON N'INVENTE AUCUNE COULEUR : chaque pixel comble prend celui du pixel PEINT LE PLUS
# PROCHE de la meme page (transformee de distance euclidienne). Un ciel en degrade se
# prolonge donc en degrade, et un fond qui couvre deja tout n'est pas touche.
#
# ET SEULEMENT LA COUCHE LA PLUS LOINTAINE : les plans du milieu et de devant doivent
# garder leurs trous, c'est par eux qu'on voit ce qu'il y a derriere.
#
# QUATRE ETAGES SONT LAISSES DE COTE -- et c'est mesure, pas prudent.
#
# Un objet de decor dont le PLAN est celui du fond se dessine A TRAVERS les trous de la page
# du fond. Rendre cette page opaque le ferait disparaitre. Depouillement des 531 fiches de
# NG, celles dont la famille est 1 (la liste 132) :
#
#     etage 38  ALEX      2 fiches STATIQUES, priorite 104  le gratte-ciel de New York
#                                                           (script 2, plan 3, 2 x 64x240)
#     etage 40  RYU       1 fiche animee,     priorite 103  le fond anime (entree 3)
#     etage 44  DUDLEY 1  2 fiches STATIQUES, priorite  90  la tour de Londres (script 8)
#     etage 45  DUDLEY 2  2 fiches STATIQUES, priorite  90  la meme
#
# et la profondeur de leur liste 132 vaut 104 dans les quatre cas. Les deux Dudley sont a 90,
# donc DEVANT leur fond : eux ne risquent rien. Alex est a 104, EGAL -- et `animer2i` a
# mesure le 15/09 qu'a profondeur egale c'est LE PLAN QUI GAGNE. Boucher le fond d'Alex
# effacerait donc son gratte-ciel, qui est precisement ce qui remplit la ruelle.
#
# La suite pour ces quatre-la : cuire les fiches statiques DANS la page du fond (elles ne
# bougent pas, meme plan, meme famille, meme profondeur : c'est exactement equivalent) puis
# boucher. Ca demande le repere des fiches, qui n'est pas encore etabli -- a faire.
# ET LES QUATRE SONT RENTRES -- 28/09/2026, le meme jour.
#
# La cause n'etait pas le bouchage mais l'ORDRE DE DESSIN : un objet dont la profondeur est
# EGALE a celle de sa page passe apres elle sur la console, avant elle ici. On rend l'ordre
# de la console dans `animerng.famille_et_z` (z - 1 d'un cran, deux fiches concernees, le
# gratte-ciel d'Alex), et plus rien ne s'oppose au bouchage. La liste reste, vide, parce que
# c'est elle qui dit ou regarder si un objet du fond disparait.
#
#
# LE BOUCHAGE EST RETIRE -- 29/09/2026. LA REGLE ETAIT FAUSSE.
# ---------------------------------------------------------------
# Frederic, sur RYU NG : « un gros carre violet ». C'etait celui-ci.
#
# La regle disait : « le plan le plus lointain n'a rien derriere lui, donc un trou y montre
# du noir, donc on le bouche ». La premisse est juste ; la conclusion ne l'est pas, parce
# qu'un plan lointain n'est pas toujours un CIEL. Le descripteur de scene le dit, et il
# suffisait de le lire avant :
#
#     bande 1  ALEX   couche 2  scene  512,512  512x256    un ciel, un seul rectangle
#     bande 4  KEN    couche 2  scene    0,512  512x512    un ciel, deux rectangles jointifs
#                               scene  512,512  512x512
#     bande 3  RYU    couche 2  scene  192,672  320x256    DEUX MORCEAUX LOCAUX, poses
#                               scene  512,672  256x256    au milieu de la scene
#
# Chez Ryu la couche 2 n'est pas un fond : ce sont les deux vues de son fond anime (l'entree
# 3), 320x256 et 256x256 posees en 192,672 et 512,672. Les etaler sur 1024x512 par le pixel
# peint le plus proche donne un aplat de la couleur de leur bord -- le carre violet.
#
# CE QU'IL AURAIT FALLU FAIRE, et qui reste a faire : ne boucher que la surface que le
# DESCRIPTEUR declare pour cette couche, et seulement quand ses rectangles couvrent la
# largeur de la scene. La mesure est deja ecrite ci-dessus, elle attend d'etre branchee.
#
# En attendant, on ne touche a rien : dix-sept etages sur dix-neuf n'avaient rien demande.
# Le trait noir d'Alex et les extremites de Ken sont a reprendre autrement.
SANS_BOUCHAGE = set(range(37, 56))


def combler_le_fond(plan):
    """Remplit les pixels vides du plan le plus lointain par le pixel peint le plus proche."""
    from scipy import ndimage

    zone = plan[512:]
    vide = zone[:, :, 3] == 0

    if not vide.any() or vide.all():
        return 0

    _d, (li, co) = ndimage.distance_transform_edt(vide, return_indices=True)
    zone[vide] = zone[li[vide], co[vide]]
    return int(vide.sum())


def main():
    ecrire = "--ecrire" in sys.argv

    # UNE SEULE BANDE, quand on n'en corrige qu'une : `python couchesng.py 1 --ecrire`.
    # Regenerer les dix-neuf pour une seule reecrirait des pages que Frederic a deja
    # validees, et ce dossier dit de ne pas defaire ce qui marche.
    choisies = [int(a) for a in sys.argv[1:] if a.isdigit()]

    for bande in (choisies or range(etagesng.NB_BANDES)):
        f = etagesng.fiche(bande)
        etage = f["etage"]
        sortie = os.path.join(RACINE, "etagesng-sprites", "stage%d" % etage)
        print("etage %d  bg_set%02x  (%d plans)" % (etage, bande, f["n"]))

        pages = {}

        for liste in (LISTE_LOINTAIN, LISTE_PROCHE, LISTE_TIERS):
            if liste not in f["couches"]:
                continue

            banque, moitie, objet = f["couches"][liste]
            plan = page_decrite(bande, objet)
            pages[liste] = plan
            px = int((plan[:, :, 3] > 0).sum())
            cx, cy = etagesng.coefs(bande, objet)
            print("   liste %3d  <-  couche %d  %7d px  %.4g / %.4g"
                  % (liste, objet, px, cx / 65536, cy / 65536))

        recoller(pages, f)

        # le plan le plus lointain est celui de plus petit coefficient : `f["couches"]`
        # range deja la 132 en lointain (voir `etagesng.fiche`)
        if LISTE_LOINTAIN in pages and etage not in SANS_BOUCHAGE:
            n = combler_le_fond(pages[LISTE_LOINTAIN])

            if n:
                print("   LE FOND : %d px vides combles par le pixel peint le plus proche"
                      % n)
        elif etage in SANS_BOUCHAGE:
            print("   LE FOND : laisse tel quel, un objet de decor se dessine a travers"
                  " (voir SANS_BOUCHAGE)")

        for liste, plan in sorted(pages.items()):
            if ecrire:
                ecrire_liste(sortie, plan, liste)

        if ecrire:
            print("      ecrit")

    if not ecrire:
        print("\nRien n'a ete ecrit. `--ecrire` pour poser les pages.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
