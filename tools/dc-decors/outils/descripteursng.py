# -*- coding: utf-8 -*-
"""Les DESCRIPTEURS DE SCENE de New Generation : ce que le Dreamcast dessine, couche par couche.

LU DANS LE CODE -- 17/09/2026. Frederic, sur NG : « GIL decor casse », « ALEX arriere-plan a
revoir », « DUDLEY 1 a revoir completement », « IBUKI 1/2/3 completement casse », « ELENA 2
completement casse », « KEN ciel a droite manquant », « ORO le ciel ne couvre pas toute la
zone »...

NG emule la CPS3 comme 2I. Sa liste d'affichage (`0x8C613004`) porte, pour chaque couche,
des ordres « dessine la carte n » avec des bandes de lignes (la table `0x8C4DDBA4`, remplie
par `0x8C146714`). MAIS LE DREAMCAST NE LIT PAS CES BANDES : l'interprete (`0x8C110BD4`)
n'en tire que la profondeur de la carte (`0x8C10E3B0` l'ecrit dans `0x8C5BA154[n]`). Les
cartes elles-memes sont dessinees par `0x8C10FBCC`, qui parcourt des LISTES DE RECTANGLES,
exactement comme le moteur de 2I (`descripteurs2i.py`) :

    enregistrement de 20 octets
        +0  u16  couche (la carte 0..3) ; 0xFFFF termine la liste
        +2  u8   x / 16 dans la scene       +3  u8  largeur / 16
        +4  u8   y / 16                     +5  u8  hauteur / 16
        +6  u16  la texture : banque 0 ou 1 du .pvc (2 et 3 : textures calculees)
        +8  u16  u / 16                     +10 u16 v / 16   (le coin dans la banque)
        +12 i32  l'attribut CPS3 (couleur, fondu) ; -1 = celui par defaut
        +16 u8   la ligne defile (sol en perspective)   +17 u8 un drapeau de dessin

    ecran x = x - ((defilement x + 1) & 0x3FF), ecran y = y - ((defilement y + 20) & 0x3FF),
    chaque rectangle redessine a +1024 en x et en y : la scene boucle.

Les listes du decor courant sont choisies par `0x8C10FEDC`, une table de sauts indexee par
`u32[0x8C4DF128]` -- LA BANDE (0 = Gill : la couche 1 ne porte que le sol, la couche 0
alterne deux vues selon la carte que la routine id 12 y pose). Cinq bandes prennent la liste
par defaut `0x8C4DF2D8`, qui n'est PAS l'identite : la couche 2 y est faite du quart haut
gauche de la banque 1 (x 0..511) et de son quart BAS gauche (x 512..1023). C'est le ciel
« manquant a droite » de Ken et d'Oro.

LES ANIMATIONS DE PAGES choisissent une liste de plus (`u32[0x8C5BD3E4 + 4 * emplacement]`
= la page courante), comme chez 2I : la cascade de Ryu, celles d'Ibuki, d'Elena 2.

Coordonnees : celles de la page du port (la moitie basse, lignes 512..1023, est ce que
`scr_trans` pose) -- la meme convention que `descripteurs2i`.

    python descripteursng.py            # les listes de chaque bande
"""
import os
import struct
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
sys.path.insert(0, ICI)

import numpy as np

import sh4ng as N

# L'image initialisee du .bss : ses donnees sont dans le fichier 0x12420 plus bas.
DECALAGE_BSS = 0x12420
DEFAUT = 0x8C4DF2D8

# u32[0x8C5BD3E4 + 4k] : la page courante de l'emplacement d'animation k.


def _lit(a, fmt):
    a = a if a < 0x8C200000 else a - DECALAGE_BSS
    return struct.unpack_from(fmt, N.D, N.a2o(a))


# LE DRAPEAU `+17` -- LU LE 22/09/2026, jusqu'au materiel.
#
#   0x8C10FD1C   l'octet +17 est empile en 3e argument de pile du constructeur de
#                quadrilateres 0x8C10F8A2
#   0x8C10FAD2   celui-ci le relit en @(156,r15), `tst ; movt` : il passe
#                `drapeau == 0` en r7 a 0x8C4F0F34
#   0x8C4F0F34   deux branches : le meme reglage 0x8C4FE0A0 avec 0x0210000A (drapeau 0)
#                ou 0x0008000A (drapeau 1), puis deux fermetures de liste, 0x8C4FD730
#                (+20 du contexte 0x8C4FD820) ou 0x8C4FD684 (+16)
#   0x8C4EF412   les bits du mot : masque 0x020000FF dans le mot +144, masque 0x00180000
#                dans le mot +152. Les deux mots ne different que par le bit 25 et par
#                le bit 20 contre le bit 19.
#
# Bit 20 = Use Alpha, bit 19 = Ignore Texture Alpha dans le mot TSP du PowerVR2, et les
# deux fermetures sont deux listes d'affichage. Donc :
#
#   drapeau 1 -> rectangle OPAQUE, alpha de texture ignore, liste opaque
#   drapeau 0 -> rectangle dessine avec l'alpha, liste translucide
#
# Sur les 146 rectangles des dix-neuf etages, les 33 qui le portent sont TOUJOURS ceux de
# la couche la plus lointaine -- le fond. `composer()` ne s'en sert pas : ces couches
# n'ont rien derriere elles, un trou y montre deja du noir.

def lire(adresse):
    """Les rectangles d'un descripteur, dans l'ordre ou le moteur les dessine."""
    out = []
    while _lit(adresse, "<H")[0] != 0xFFFF:
        c, x, w, y, h, tex, u, v, attr, ligne, drap = _lit(adresse, "<HBBBBHHHiBB")
        out.append(dict(couche=c, x=x * 16, larg=w * 16, y=y * 16, haut=h * 16,
                        texture=tex, u=u * 16, v=v * 16, attr=attr, ligne=ligne, drapeau=drap))
        adresse += 20
    return out


def table(adresse, n):
    return [_lit(adresse + 4 * i, "<I")[0] for i in range(n)]


# CE QUE CHAQUE CAS CHARGE, lu dans `0x8C10FEDC` (cas = bande). `base` est toujours dessine ;
# chaque entree de `variantes` est un choix parmi plusieurs listes, fait par le moteur selon
# une condition (la carte posee sur une couche, ou la page courante d'un emplacement). Le
# premier element de chaque choix est celui du repos -- la branche que le code prend quand
# aucune condition ne tient, ou l'etat de depart.
CAS = {
    # Gill : le sol ; la couche 0 alterne deux vues (la carte de la routine id 12).
    0: dict(base=[0x8C4DF134],
            variantes=[("couche 0 : carte A / B", [0x8C4DF15C, 0x8C4DF1C0])]),
    1: dict(base=[0x8C4DF224]),                                  # Alex
    2: dict(base=[0x8C4DF33C]),                                  # Sean
    # Ryu : la cascade (emplacement 0 : 89 ou autre, 96, 97) et un morceau du fond
    # (emplacement 2 : 65 ou autre, 94, 95).
    3: dict(base=[0x8C4DF378],
            variantes=[("emplacement 0 : 89, 96, 97", [0x8C4DF3DC, 0x8C4DF404, 0x8C4DF42C]),
                       ("emplacement 2 : 65, 94, 95", [0x8C4DF454, 0x8C4DF47C, 0x8C4DF4A4])]),
    4: dict(base=[DEFAUT]),                                      # Ken
    5: dict(base=[DEFAUT]),                                      # Yun 1
    6: dict(base=[0x8C4DF33C]),                                  # Yun 2
    # Dudley 1 : la couche 0 prend une vue parmi quatre, selon sa carte.
    7: dict(base=[0x8C4DF4CC],
            variantes=[("couche 0 : quatre cartes",
                        [0x8C4DF530, 0x8C4DF6C0, 0x8C4DF850, 0x8C4DF9E0])]),
    8: dict(base=[0x8C4DFB70]),                                  # Dudley 2
    9: dict(base=[DEFAUT]),                                      # Necro
    10: dict(base=[DEFAUT]),                                     # Hugo
    14: dict(base=[0x8C4E01B0]),                                 # Elena 1
    # Elena 2 : la cascade (emplacement 0, pages 84..95 -> douze vues), et le bas de la
    # couche 1 selon sa carte.
    15: dict(base=[0x8C4E0200],
             variantes=[("emplacement 0 : pages 84..95", table(0x8C4E0458, 12)),
                        ("couche 1 : cartes A / B", [0x8C4E0488, 0x8C4E04C4])]),
    16: dict(base=[DEFAUT]),                                     # Oro
    17: dict(base=[DEFAUT]),                                     # Yang 1
    18: dict(base=[0x8C4DF33C]),                                 # Yang 2
}
# Ibuki 1, 2, 3 : un seul cas (`0x8C110140`).
IBUKI_CASCADE_BASSE = [0x8C4DFC74, 0x8C4DFCB0, 0x8C4DFCEC, 0x8C4DFD28, 0x8C4DFD64, 0x8C4DFDA0]
IBUKI_CASCADE_HAUTE = [0x8C4DFDDC, 0x8C4DFE18, 0x8C4DFE54, 0x8C4DFE90, 0x8C4DFECC, 0x8C4DFF08]
for _b in (11, 12, 13):
    CAS[_b] = dict(
        base=[0x8C4E00D4],
        variantes=[
            ("couche 0 : cartes A / B", [0x8C4DFBAC, 0x8C4DFC10]),
            # la page de l'emplacement 0 (69, 73..77) ; DEUX SERIES selon le defilement
            # vertical de la carte 0 (`u16[0x8C6D3026]` > 0x200 : la haute). Elles suivent
            # la copie de la scene que la carte montre : la routine id 48 decale la carte 0
            # de 512 lignes un pas sur deux (voir `ETATS`).
            ("emplacement 0, serie basse : 69, 73..77", IBUKI_CASCADE_BASSE),
            ("emplacement 0, serie haute : 69, 73..77", IBUKI_CASCADE_HAUTE),
            ("couche 1 : quatre cartes", [0x8C4DFF44, 0x8C4DFF80, 0x8C4DFFBC, 0x8C4DFFF8]),
            ("emplacement 6 : 67 / 78", [0x8C4E0034, 0x8C4E005C]),
            ("emplacement 7 : 64 / 79", [0x8C4E0084, 0x8C4E00AC]),
        ])

_BANQUES = {}


def banque(bande, n):
    """La banque `n` du .pvc de la bande, en 1024 x 1024 RGBA."""
    if (bande, n) not in _BANQUES:
        import bande3sx
        import pvc
        from rendupvc import carte_morton, SIDE
        src = os.path.join(RACINE, "pvc-ng", "bg_set%02x.pvc" % bande)
        pages, _u, _s = pvc.decode(open(src, "rb").read())
        _BANQUES[bande, n] = bande3sx.banque_rgba(pages, n * 4096, carte_morton(SIDE))[0]
    return _BANQUES[bande, n]


def poser(toile, rgba, x, y):
    """Pose `rgba` en (x, y), par-dessus, en bouclant sur 1024 comme le moteur."""
    h, w = rgba.shape[:2]
    op = rgba[:, :, 3] > 0
    ys = (np.arange(h) + y) % 1024
    xs = (np.arange(w) + x) % 1024
    zone = toile[np.ix_(ys, xs)]
    zone[op] = rgba[op]
    toile[np.ix_(ys, xs)] = zone


def rectangles(bande, choix=None):
    """Les rectangles dessines pour la bande, `choix[i]` etant l'indice pris dans la
    variante i (0 par defaut)."""
    cas = CAS[bande]
    out = []
    for a in cas["base"]:
        out += lire(a)
    for i, (_nom, listes) in enumerate(cas.get("variantes", [])):
        k = (choix or {}).get(i, 0)
        if k is not None:
            out += lire(listes[k])
    return out


def composer(bande, rects, couche, toile=None):
    """La page 1024 x 1024 d'une couche : ses rectangles poses dans la scene, dans l'ordre."""
    if toile is None:
        toile = np.zeros((1024, 1024, 4), np.uint8)
    for r in rects:
        if r["couche"] != couche:
            continue
        if r["texture"] not in (0, 1):
            continue
        b = banque(bande, r["texture"])
        poser(toile, b[r["v"]:r["v"] + r["haut"], r["u"]:r["u"] + r["larg"]], r["x"], r["y"])
    return toile


# LES ANIMATIONS DE PAGES DE NG : `0x8C1B09C0 + k * 20` = {plan, emplacement, suite, debut,
# fin}, le format de 2I (`animer2i.entree_de_pages`). La suite est une file de paires
# [duree, page] qui boucle ; `u32[0x8C5BD3E4 + 4 * emplacement]` en garde la page courante,
# et c'est elle que le constructeur de listes consulte. Onze entrees : 0 Elena 2, 1 a 3 Ryu,
# 4 a 10 Ibuki (id 14, `0x8C09F258(k)`).
ENTREES_PAGES = 0x8C1B09C0


def entree_de_pages(k):
    plan, slot, suite, _debut, _fin = _lit(ENTREES_PAGES + k * 20, "<iiIII")
    seq = []
    while True:
        d, pg = _lit(suite, "<hh")
        if d == -1:
            return dict(plan=plan, emplacement=slot, suite=seq)
        seq.append((d, pg))
        suite += 4


def table_pas(adresse, n):
    """Les pas des routines qui changent la carte d'une couche (id 11, 12, 48) :
    (carte, decalage vertical, duree), six octets chacun."""
    return [_lit(adresse + 6 * i, "<hhBB")[:3] for i in range(n)]


# L'ETAT DE DEPART DES COUCHES QU'UNE ROUTINE ANIME. Trois routines changent la CARTE d'une
# couche et, un pas sur deux, la DECALENT DE 512 LIGNES : la scene porte deux copies de la
# couche (lignes 0..511 et 512..1023), et le decalage montre l'une ou l'autre.
#
#     id 12, Gill      `0x8C1AFE1C` : (carte 0, +512), (0, 0), (1, +512), (1, 0), 12 trames
#     id 11, Dudley 1  `0x8C1AFC24` : la pluie, cartes 0..3, 3 a 7 trames
#     id 48, Ibuki     `0x8C1B21A4` (couche 0), `0x8C1B221C` (couche 1, cartes 2..5)
#
# La page du port montre les lignes 512..1023 : un decalage de 512 y fait passer la copie du
# haut. `choix` donne l'indice pris dans chaque variante (None : rien), `decalage` le
# decalage du pas 0.
#
# ELENA 2 : sa couche 1 garde SA carte (`u32[plan 1 + 40]`), qui designe la seconde liste --
# les planches du pont, en y 960. La premiere n'est prise que si la couche passe sur la carte 0.
ETATS = {
    0: {0: dict(choix={0: 0}, decalage=512)},
    7: {0: dict(choix={0: 0}, decalage=512)},
    15: {1: dict(choix={1: 1})},
}
for _b in (11, 12, 13):
    ETATS[_b] = {0: dict(choix={0: 0, 1: 0, 2: None}, decalage=512),
                 1: dict(choix={1: None, 2: None, 3: 0, 4: 0, 5: 0})}

# LE CIEL DE GILL EST DESCENDU DE 80 LIGNES -- 17/09/2026. MESURE, PAS LU. Sa couche 0 s'arrete
# a la ligne 879 de la scene et le sol (couche 1) commence en 960 : 80 lignes que rien ne
# couvre, et les elements de lave (plan 2, lignes 943..959) posent sur le vide. Les bandes de
# lignes de la table `0x8C4DDBA4` disent la meme chose (couche 0 a partir de la ligne 144,
# couche 1 jusqu'a 64) : le jeu ecarte donc les deux cartes de 80 lignes, par un decalage
# vertical que je n'ai pas retrouve. On le porte dans la page.
#
# OU IL VIT, LU LE 23/09. Le rasteriseur `0x8C10FBCC` donne
#     ecran y = (champ +4) * 16 - ((defilement y + 20) & 0x3FF),
# et le defilement vient du registre CPS3 emule `0x8C724758 + 16 n + 14`, UN PAR
# COUCHE (`0x8C13B2E8` le recopie en `0x8C6D3024 + 16 n`). Aucun terme de la
# correction -- ni le +1, ni le +20, ni les globaux `0x8C7246C4/CE/D0`, ni le -260 --
# n'est indexe par la couche. Les couches sont donc des REPERES INDEPENDANTS : la
# couche 0 de Gill en scene 0..879 et sa couche 1 en 960..1023 ne laissent pas un trou
# de 80 lignes, elles ne se comparent pas. Ces 80 sont l'ecart entre les deux
# registres, et c'est l'interprete de plans `0x8C110BD4` (celui qui remplit deja la
# profondeur en `0x8C5BA154` via `0x8C10E3B0`) qui les ecrit. Verifie aussi : la table
# de pas de Gill `0x8C1AFE1C` ne contient que (0,512) (0,0) (1,512) (1,0), pas de 80.
# CHAQUE COUCHE A SON PROPRE ORIGINE VERTICALE, ET ELLE SE LIT -- 25/09/2026.
#
# Frederic, sur ALEX : « une ligne de pixels noirs en arriere plan (verifie les positions
# des arriere plan et leurs scrollings) ». Elle se lit, et voici ou.
#
# L'ETAT DE DEPART D'UN PLAN. Chaque plan de NG est un enregistrement de 144 octets en
# `contexte + 84 + k * 144` (le contexte est `0x8C552674`). Son initialisation generique
# `0x8C088260` y recopie les deux coefficients de parallaxe :
#
#     u32[plan + 16] = u32[0x8C189BA0 + bande * 32 + k * 8]        le coefficient X
#     u32[plan + 20] = u32[0x8C189BA0 + bande * 32 + k * 8 + 4]    le coefficient Y
#
# et l'etat 0 de chaque plan (Alex : `0x8C0893CE`, `0x8C0894A0`, `0x8C089578`) pose sa
# position verticale de depart :
#
#     u32[plan + 28] = u32[plan + 20] * 266        (`mov.w #0x010A,r3 ; mul.l r3,r1`)
#
# 266 est la hauteur de camera au repos ; `plan[+30]`, la moitie haute de ce 16.16, est
# l'entier qui part au materiel. UN COEFFICIENT PLUS PETIT DONNE DONC UNE ORIGINE PLUS
# PETITE, et la couche est POSEE PLUS HAUT : le registre est NIE avant d'etre employe --
#
#     `0x8C13B366`   `neg r0,r0` sur `u16[0x8C724758 + 16n + 14]`, puis
#                    `ecran y = (champ + 4) * 16 - ((defilement y + 20) & 0x3FF)`
#
# donc `ecran y = scene y + plan[+30] - K`, et K ne depend pas de la couche.
#
# ALEX, BANDE 1, en chiffres lus :
#
#     couche 0 (le plan du milieu)  coef Y 0,875  ->  0xE000 * 266 >> 16 = 232
#     couche 1 (la rue, au premier) coef Y 1,000  ->                       266
#     couche 2 (le ciel)            coef Y 1,000  ->                       266
#
# La couche 0 est donc **34 lignes plus haut** que les deux autres, et le port les posait
# toutes trois a la meme origine. MESURE, d'accord avec la lecture : le trou entre les
# trois couches tombe de 5806 a 4520 pixels, et le minimum de la mesure est a -34..-38.
#
# Ce qui RESTE ouvert (4520 pixels, colonnes 746..804) est la fente entre les deux
# immeubles du fond : aucune texture derriere elle -- la banque 0 de `bg_set01` est
# entierement employee, la banque 1 est vide -- c'est l'element `script 2` (le gratte-ciel,
# 240 x 128, plan 3, profondeur 104) qui la couvre.
#
# LES ORIGINES HORIZONTALES, elles, sont TOUTES EGALES : l'etat 0 de chaque plan pose
# `u16[plan+26] = u16[plan+48] = u16[plan+72] = 512`, et `0x8C0912BC` calcule
# `x = (plan[+26] & 0x3FF) - contexte[+40]`. Rien a corriger de ce cote.
#
# LES 80 LIGNES DE GILL restent une MESURE, pas une lecture : son coefficient Y de couche 0
# vaut 1,0 comme celui de sa couche 1, et la regle ci-dessus lui donnerait 0. Sa routine
# d'etage monte un plan de PLUS (`0x8C089160` : `plan[+2] = 4`, coefficients 0xC000/0xF000,
# et `u32[plan+28] = u32[plan+20] << 8` -- un autre multiplicateur). On n'y touche pas.
#
# ET LE DECALAGE D'ALEX EST RETIRE -- 25/09/2026.
#
# Frederic : « *avant l'ajout du pieton, le decor etait convenablement affiche. Trouve
# comment l'afficher correctement a nouveau* », apres « *il manque le plan derriere le
# clochard* ». Les deux changements etaient dans la MEME livraison ; ce n'est pas le
# pieton, c'est ce decalage-ci.
#
# LA MESURE, sur les pages deployees de l'etage 38 :
#
#     liste 260, contenu aux lignes de scene 562..941
#                (donc 596..975 avant le -34)
#
# `np.roll` ENROULE : les 34 lignes du haut de la bande -- vides chez Alex -- repassent en
# bas. Le contenu de la liste 260 s'arrete donc 34 lignes trop haut, et il n'y a plus rien
# en dessous. Or **le clochard est sur cette liste** (plan DC 1 -> famille 3 -> liste 260,
# confirme par les coefficients : 0,875) et il est a hauteur de sol. Les 34 lignes
# manquantes sont exactement derriere lui.
#
# LA DERIVATION RESTE JUSTE -- couche 0 a `0xE000 * 266 >> 16` = 232 contre 266, soit 34
# lignes plus haut -- mais elle se pose sur l'ORIGINE DU PLAN, pas sur la texture. La
# console ecrit `u32[plan+28]`, un registre de position ; rouler les pixels dans la page
# n'est pas la meme chose des que la bande n'est pas pleine sur ses 1024 lignes. La
# ligne noire que ce decalage corrigeait peut donc revenir : c'est a reprendre par
# l'origine, pas ici.
DECALAGE_Y = {(0, 0): 80}


def vue(bande, choix=None):
    """Les rectangles de la bande avec `choix` en surcharge des variantes."""
    return rectangles(bande, choix)


def page(bande, couche, choix=None, decalage=None):
    """La page du port pour une couche : son etat de depart, decalages compris."""
    e = ETATS.get(bande, {}).get(couche, {})
    c = dict(e.get("choix", {}))
    c.update(choix or {})
    d = e.get("decalage", 0) if decalage is None else decalage
    toile = composer(bande, vue(bande, c), couche)
    if d:
        toile = np.roll(toile, d, axis=0)
    dy = DECALAGE_Y.get((bande, couche), 0)
    if dy:
        toile = np.roll(toile, dy, axis=0)
    return toile


def couches_decrites(bande):
    """Les couches que les listes de la bande dessinent vraiment."""
    return {r["couche"] for r in vue(bande) if r["texture"] in (0, 1)}


def _suite(k, valeurs):
    """Les pas d'une entree de pages : (choix, duree), la page traduite par `valeurs`."""
    e = entree_de_pages(k)
    return [(valeurs(pg), d) for d, pg in e["suite"]]


# LES ANIMATIONS A SERVIR EN OBJETS. Chaque pas est (choix, decalage, duree) ; l'image d'un
# pas est la couche entiere telle que le Dreamcast la dessine, et l'objet ne couvre que les
# cases qui changent d'un pas a l'autre (la page porte le pas 0). `rang` : l'ordre de
# priorite quand la memoire manque -- les onze animations de pages d'abord.
def _animations():
    out = []
    # RYU : la cascade (entree 1 : 89, 96, 97) et le morceau du fond (entree 3 : 65, 94, 95).
    out.append(dict(bande=3, couche=0, rang=0, quoi="la cascade de Ryu (entree 1)",
                    pas=[({0: {89: 0, 96: 1, 97: 2}[pg]}, 0, d)
                         for d, pg in entree_de_pages(1)["suite"]]))
    out.append(dict(bande=3, couche=2, rang=0, quoi="le fond anime de Ryu (entree 3)",
                    pas=[({1: {65: 0, 94: 1, 95: 2}[pg]}, 0, d)
                         for d, pg in entree_de_pages(3)["suite"]]))
    # ELENA 2 : la cascade (entree 0, pages 84..95).
    out.append(dict(bande=15, couche=0, rang=0, quoi="la cascade d'Elena 2 (entree 0)",
                    pas=[({0: pg - 84, 1: 1}, 0, d) for d, pg in entree_de_pages(0)["suite"]]))
    for b in (11, 12, 13):
        # IBUKI : la cascade (entree 4, 69, 73..77), vue par la copie du haut (pas 0 de id 48).
        pages = {69: 0, 73: 1, 74: 2, 75: 3, 76: 4, 77: 5}
        out.append(dict(bande=b, couche=0, rang=0, quoi="la cascade d'Ibuki (entree 4)",
                        pas=[({0: 0, 1: pages[pg], 2: None}, 512, d)
                             for d, pg in entree_de_pages(4)["suite"]]))
        # les deux clignotements de la couche 1 (entrees 9 et 10)
        out.append(dict(bande=b, couche=1, rang=0, quoi="Ibuki, emplacement 6 (entree 9)",
                        pas=[({1: None, 2: None, 3: 0, 4: {67: 0, 78: 1}[pg], 5: 0}, 0, d)
                             for d, pg in entree_de_pages(9)["suite"]]))
        out.append(dict(bande=b, couche=1, rang=0, quoi="Ibuki, emplacement 7 (entree 10)",
                        pas=[({1: None, 2: None, 3: 0, 4: 0, 5: {64: 0, 79: 1}[pg]}, 0, d)
                             for d, pg in entree_de_pages(10)["suite"]]))
        # le vent (id 48) : moins prioritaire, il pese lourd
        out.append(dict(bande=b, couche=0, rang=1, quoi="Ibuki, le vent sur la couche 0 (id 48)",
                        pas=[({0: t, 1: 0 if y else None, 2: None if y else 0}, y, d)
                             for t, y, d in table_pas(0x8C1B21A4, 20)]))
        out.append(dict(bande=b, couche=1, rang=1, quoi="Ibuki, le vent sur la couche 1 (id 48)",
                        pas=[({1: None, 2: None, 3: t - 2, 4: 0, 5: 0}, y, d)
                             for t, y, d in table_pas(0x8C1B221C, 20)]))
    # GILL : l'horizon (id 12) N'EST PLUS UN OBJET -- 18/09/2026. Ses quatre vues changent
    # la couche entiere : elles sont servies par une ANIMATION DE PLAN (`plansng.py`, pages
    # de reecriture), qui les pose en entier. En objet, seules les cases qui tenaient dans le
    # budget etaient posees -- Frederic : « il manque plusieurs grosses vagues de lave ».
    return out


ANIMATIONS = _animations()


def images_animation(a):
    """(images RGBA 1024 x 1024, durees) d'une animation, une image par pas."""
    ims, durees = [], []
    for choix, dec, d in a["pas"]:
        ims.append(page(a["bande"], a["couche"], choix, dec))
        durees.append(d)
    return ims, durees


def decrire(r):
    return ("couche %d  scene %4d,%4d  %4dx%-4d <- banque %d  %4d,%4d%s%s"
            % (r["couche"], r["x"], r["y"], r["larg"], r["haut"], r["texture"], r["u"], r["v"],
               "  ligne" if r["ligne"] else "", "  drapeau %d" % r["drapeau"] if r["drapeau"] else ""))


def main():
    for bande in sorted(CAS):
        cas = CAS[bande]
        print("bande %d" % bande)
        for a in cas["base"]:
            for r in lire(a):
                print("   " + decrire(r))
        for nom, listes in cas.get("variantes", []):
            print("   variante %s" % nom)
            for a in listes:
                rs = lire(a)
                print("      %08X : %s" % (a, " | ".join(decrire(r) for r in rs[:2])
                                          + (" ... (%d)" % len(rs) if len(rs) > 2 else "")))


if __name__ == "__main__":
    main()
