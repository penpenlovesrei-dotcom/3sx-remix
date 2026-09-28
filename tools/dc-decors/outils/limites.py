# -*- coding: utf-8 -*-
"""Les BORNES DE CAMERA des etages ajoutes, LUES DANS LE BINAIRE DE 2nd IMPACT.

Frederic, 16/09/2026 : « le decor n'est pas aussi large que dans la version dreamcast, on
ne peut pas aller au bout des extremites droite et gauche. Corrige et verifie pour tous
les autres decors ». Les quinze etages portaient 0x140..0x2c0 pose a la main, soit 384 px
de course pour presque tous, et les dix-neuf de New Generation la meme valeur.

J'AI D'ABORD MESURE LES PAGES, ET RYU L'A DEMENTI. La regle « la camera va jusqu'au bord
du dessin » -- premiere colonne peinte + 192, derniere - 192 -- retombe pourtant sur Gill,
Dudley et Ken. Elle donnait 639 px a Ryu, qui peint sa bande entiere. Frederic : « je
viens de tester Ryu, ca ne va pas du tout ». La page dit jusqu'ou le decor EXISTE, pas
jusqu'ou le jeu laisse aller.

LA TABLE EST DANS LE BINAIRE, ET LE CHARGEUR LA LIT SOUS NOS YEUX. `0x8C0DA7A0` pose un
pointeur `[0x8C0DA864] = 0x8C1D557C`, ajoute `bande * 48 + plan * 12`, et ecrit six mots
d'affilee avec `mov.w @r4+,r1` dans les champs du plan :

    +104 l_limit    +100 r_limit    +106 l_limit2    +102 r_limit2    +108 y_limit
    +110 y_limit2

Ce sont EXACTEMENT les champs, et l'ordre, de `limit_tbl3` cote 3rd Strike. Puis, si
`u8[0x8C841F3C]` est NUL, `0x8C0DA7F8` recopie `l_limit`/`r_limit` par-dessus
`l_limit2`/`r_limit2` : la paire LARGE remplace la paire etroite. C'est bien NUL --
`0x8C0DA7F4` fait `tst r2,r2 ; bf 0x8C0DA814`, et `bf` SAUTE la recopie quand l'octet
n'est pas nul. New Generation a les memes instructions en `0x8C08833A`, sur
`u8[0x8C7252B8]`. La note d'avant disait l'inverse ; la conclusion, elle, ne change
pas : c'est la paire large qu'on garde.

C'est la paire large qui correspond a ce qui est valide a l'ecran depuis des semaines :

    Dudley  0x110..0x2f0  ->  au pixel pres        Alex  0x102..0x2fc  contre 0x100..0x300
    Gill    0x142..0x2bc  contre 0x140..0x2c0      Ken   0x0e4..0x31c  contre 0x0df..0x320

et elle rend a Necro ses 630 px de course, la ou la mesure n'en donnait que 459. La paire
etroite, elle, donne 270 px a Gill : personne n'a jamais joue comme ca.

RYU EST COMPTE DEPUIS LE MILIEU DE LA BANDE, comme ses objets (`animer2i.DECALAGE_X`) :
ses bornes sont negatives, -202..203, et il faut leur ajouter 512.

    python limites.py            la table, comparee a ce qui est pose
    python limites.py --ecrire   recrit les quinze lignes de bg_data.c
"""
import io
import os
import re
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import poser2i as P

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BG_DATA = os.path.normpath(r"C:\Temp3sx\src\sf33rd\Source\Game\stage\bg_data.c")
DEMI = 192          # bg_w.pos_offset : le milieu de la fenetre de 384
BASE = 196          # la liste du plan de base, celui qui suit la camera au 1/1
SOL_BANDE = 64      # les lignes du bas ou l'on cherche le sol

DOSSIERS = [(range(22, 37), "etages2i-sprites"), (range(56, 58), "etages2i-sprites"),
            (range(37, 56), "etagesng-sprites")]

NOMS = {22: "bg00 GILL", 23: "bg01 ALEX", 24: "bg02 RYU", 25: "bg03 YUN", 26: "bg04 DUDLEY",
        27: "bg05 NECRO", 28: "bg06 HUGO", 29: "bg07 IBUKI", 30: "bg09 ELENA", 31: "bg0a ORO",
        32: "bg0b YANG", 33: "bg0c KEN", 34: "bg0d SEAN", 35: "bg0e URIEN", 36: "bg0f GORGE",
        56: "bg08 ELENA 1", 57: "bg10 HUGO BIS"}


def dossier(etage):
    for plage, nom in DOSSIERS:
        if etage in plage:
            return os.path.join(RACINE, nom, "stage%d" % etage)
    return None


def etendue(etage, liste=BASE):
    """(x0, x1) des colonnes peintes de cette page, ou None si la page n'existe pas."""
    d = dossier(etage)
    if d is None or not os.path.isdir(d):
        return None
    if not any(f.startswith("%d-" % liste) for f in os.listdir(d)):
        return None
    a = P.lire_liste(d, liste)
    xs = np.where((a[:, :, 3] > 0).any(0))[0]
    return (int(xs.min()), int(xs.max())) if len(xs) else None


INC = [r"C:\Temp3sx\src\port\video\etages2i_plans.inc",
       r"C:\Temp3sx\src\port\video\etagesng_plans.inc",
       r"C:\Temp3sx\src\port\video\etages2ibis_plans.inc"]
_vitesses = None


def vitesses():
    """{etage: {plan: vitesse horizontale}} -- lues dans les includes que le jeu compile."""
    global _vitesses
    if _vitesses is not None:
        return _vitesses
    _vitesses = {}
    for chemin in INC:
        lignes = io.open(chemin, encoding="utf-8").read().splitlines()
        for i, l in enumerate(lignes):
            m = re.match(r"#define ETAGES\w+_SPEED_X_(LOIN|TIERS|QUATRE)", l)
            if not m:
                continue
            plan = {"LOIN": 0, "TIERS": 2, "QUATRE": 3}[m.group(1)]
            for p in lignes[i + 1].split(","):
                mm = re.match(r"\s*\[(\d+)\] = (0x[0-9A-Fa-f]+)", p)
                if mm:
                    _vitesses.setdefault(int(mm.group(1)), {})[plan] = \
                        int(mm.group(2), 16) / 65536.0
    return _vitesses


def contrainte(etage, plan, vitesse):
    """(P_min, P_max) que ce plan impose a la camera, ou None s'il n'impose rien.

    La position du plan vaut `vitesse * (P - 512) + 512`, et sa fenetre de 384 doit rester
    dans son dessin. Un plan dont la page est plus etroite que la fenetre n'est PAS un
    fond -- c'est un element statique pose en plan, comme le temple de Gill ou l'arbre
    d'Elena -- et il n'impose rien : le borner le figerait a l'ecran.
    """
    ext = etendue(etage, 132 + 64 * plan)
    if ext is None or ext[1] - ext[0] < 384 or vitesse <= 0:
        return None
    return (512 + (ext[0] + DEMI - 512) / vitesse, 512 + (ext[1] - DEMI - 512) / vitesse)


def sol(etage):
    """(x0, x1) du SOL : l'etendue peinte dans les 64 dernieres lignes, tous plans reunis.

    LE PLAN DE BASE N'EST PAS TOUJOURS LE SOL, et c'est ce qui manquait le 16/09 au soir.
    Mesurer la liste 196 rendait les bonnes bornes pour Gill, Dudley et Ken, et une bande
    trop etroite pour Necro : sa liste 196 n'est pas un sol, c'est un PREMIER PLAN decoupe
    (297..839 au ras du sol), et le vrai sol est sa liste 260, qui va de 0 a 1023.
    Frederic : « il n'a toujours pas la bonne largeur, ni les chaines » -- ses chaines
    pendent en 8..168, hors de la liste 196, et la camera ne pouvait pas les atteindre.

    On prend donc la reunion de ce que TOUS les plans peignent au ras du sol : c'est la ou
    les combattants marchent, et c'est ce qui laisserait un vide si la camera allait plus
    loin. La regle rend toujours les quatre etages valides -- Gill 128..895, Dudley 80..943,
    Ken 31..991 -- et elle ouvre Necro, Alex et Ibuki, dont un plan peint la bande entiere.
    """
    x0, x1 = 1024, -1
    for plan in range(4):
        d = dossier(etage)
        liste = 132 + 64 * plan
        if d is None or not os.path.isdir(d):
            continue
        if not any(f.startswith("%d-" % liste) for f in os.listdir(d)):
            continue
        a = P.lire_liste(d, liste)
        xs = np.where((a[1024 - SOL_BANDE:, :, 3] > 0).any(0))[0]
        if len(xs):
            x0, x1 = min(x0, int(xs.min())), max(x1, int(xs.max()))
    return (x0, x1) if x1 >= 0 else None


TABLE_2I = 0x8C1D557C     # SF3_2ND.BIN,  bande * 48 + plan * 12, six mots par plan
TABLE_NG = 0x8C18A3F8     # le binaire de New Generation, meme chargeur, meme disposition
PAS_BANDE, PAS_PLAN = 48, 12
BANDE = {22: 0, 23: 1, 24: 2, 25: 3, 26: 4, 27: 5, 28: 6, 29: 7, 30: 9, 31: 10,
         32: 11, 33: 12, 34: 13, 35: 14, 36: 15, 56: 8, 57: 16}


def table_jeu(etage, plan):
    """(l_limit2, r_limit2) du plan, lus dans le binaire d'origine.

    On prend la paire LARGE (`l_limit`, `r_limit`, les deux premiers mots) : c'est celle
    que `0x8C0DA7F8` installe quand `u8[0x8C841F3C]` est NUL, et la seule qui
    corresponde a ce qui est valide a l'ecran.

    DES BORNES NEGATIVES SONT COMPTEES DEPUIS LE MILIEU DE LA BANDE. Ryu est dans ce cas
    dans 2nd Impact (-202..203), comme ses objets le sont deja (`animer2i.DECALAGE_X`), et
    six bandes de New Generation aussi. Une position de camera ne peut pas etre negative :
    le signe est donc la marque de l'origine, et on ajoute 512.
    """
    if etage in BANDE:
        import sh4 as B
        base, bande = TABLE_2I, BANDE[etage]
    elif 37 <= etage <= 55:
        import sh4ng as B
        base, bande = TABLE_NG, etage - 37
    else:
        return None

    l, r = struct.unpack_from("<2h", B.D,
                              B.a2o(base + bande * PAS_BANDE + min(plan, 3) * PAS_PLAN))
    if l < 0:
        l, r = l + 512, r + 512
    return l, r


table_2i = table_jeu       # l'ancien nom, garde pour les appelants


def bornes(etage):
    """(l_limit2, r_limit2) de l'etage, mesures sur son SOL (voir `sol`).

    UNE SEULE PAIRE POUR LES TROIS PLANS, et c'est delibere. `limit_tbl3` en porte une par
    plan, et les etages d'origine s'en servent ; la mesure, elle, ne vaut que pour le plan
    de base. Sur les plans de fond la page n'est pas toujours un fond : celle du plan 3 de
    Gill ne porte qu'un element statique de 345 px de large, et la borner sur son dessin
    FIGERAIT ce plan -- l'element resterait colle a l'ecran au lieu de defiler. On garde
    donc la meme paire partout, comme les quinze etages le font depuis le debut.
    """
    e = sol(etage) or etendue(etage) or (128, 895)
    l, r = e[0] + DEMI, e[1] - DEMI

    # LES PLANS DE FOND NE BORNENT PAS, ET J'AI ESSAYE. Oro peint sa bande entiere au plan
    # proche mais son couchant s'arrete a 831 : on pourrait croire qu'il faut s'y tenir.
    # Applique, ce raisonnement RAMENAIT ALEX de 512 px de course a 125 -- et Alex est
    # valide a l'ecran depuis des semaines. Un plan de fond qui ne couvre pas toute la
    # fenetre n'ouvre donc pas forcement un vide : un plan plus proche le recouvre, ou le
    # bord tombe hors du champ utile. La contrainte reste calculee (`contrainte`) et
    # SIGNALEE, elle n'est plus appliquee.
    if r < l:
        l = r = (e[0] + e[1]) // 2
    return l, r


def elargies(etage, actuelles):
    """La mesure, mais on ne RETRECIT jamais ce qui est pose : Ibuki est plus large que sa
    page ne le permet, et son decor est deja a reprendre -- ce n'est pas le moment de lui
    retirer de la course.

    ET UNE PAGE PLUS ETROITE QUE LA FENETRE NE DIT RIEN. L'etage 46 de New Generation ne
    peint que 512 colonnes sur 1024 : la formule lui rendrait 127 px de course, ce qui
    n'est pas une limite de camera mais un plan de base a moitie vide. On le laisse tel
    qu'il est, et c'est un decor a regarder de plus pres."""
    l, r = bornes(etage)
    if r - l < 384:
        return tuple(actuelles)
    return min(l, actuelles[0]), max(r, actuelles[1])


def sans_bande(etage, l, r):
    """Les bornes du binaire, resserrees la ou la VUE sortirait du plan de base -- NG.

    19/09/2026, Frederic, captures a l'appui : « RYU 2 bandes verticales etroites aux
    extremites », « KEN 2 bandes verticales aux extremites ». `ecran_ng.py` les reproduit
    aux butees de la paire large :

      * Ken (182..861) voit la scene de -10 a 1053 : son plan de base peint les 1024
        colonnes et BOUCLE, la vue franchit la couture et montre l'autre bout du decor --
        10 px du mur rose a gauche, 30 px des rochers a droite ;
      * Ryu (314..708) voit de 122 a 900, et son plan de base ne porte ses batiments que de
        128 a 895 : 6 px a gauche et 4 a droite ou rien n'est peint au-dessus du sol.

    On ne resserre QUE si les deux conditions tiennent : la vue sort de l'etendue peinte
    du plan de base (au-dessus du sol), ET l'ecran compose avec toutes les pages montre un
    vide ou franchit la couture. Necro et Hugo sortent aussi de leur plan de base, mais un
    autre plan les couvre (le sol de Necro est la liste 260) : ils ne bougent pas. Les
    objets ne comptent pas dans la mesure -- ils bouchent des trous ailleurs (Elena 1 n'est
    faite que d'objets), jamais aux bords de ces deux decors.
    """
    import ecran_ng
    page = ecran_ng.lire_liste(etage, BASE, dossier(etage))
    if page is None:
        return l, r
    haut = np.where((page[:512 - 80, :, 3] > 0).any(0))[0]
    if not len(haut) or (l - DEMI >= haut[0] and r + DEMI <= haut[-1] + 1
                         and l - DEMI >= 0 and r + DEMI <= 1024):
        return l, r
    pages = {p: ecran_ng.lire_liste(etage, 132 + 64 * p, dossier(etage))
             for p in ecran_ng.plans(etage)[0]}

    def propre(cam):
        ec = ecran_ng.composer(etage, cam, pages=pages, sans_objets=True)[0]
        # les lignes au-dessus du sol : les combattants marchent en 224 - 40
        return bool((ec[:184, :, 3] > 0).all()) and 0 <= cam - DEMI and cam + DEMI <= 1024

    l2, r2 = l, r
    while l2 < r2 and not propre(l2):
        l2 += 1
    while r2 > l2 and not propre(r2):
        r2 -= 1
    return l2, r2


def trio(etage, actuelles=(0x140, 0x2c0), y=0xF0):
    """Les trois plans d'un etage, au format de `limit_tbl3`.

    CHAQUE PLAN A LES SIENNES dans le binaire, et on les rend telles quelles. Faute de
    table -- New Generation -- les trois plans partagent la mesure du sol, comme avant.

    Seul le plan de base (1) borne la camera (`bg_base_x_move_check`) ; pour New
    Generation il passe par `sans_bande`.
    """
    out = []
    for plan in range(3):
        v = table_2i(etage, plan)
        l, r = v if v is not None else elargies(etage, actuelles)
        if plan == 1 and 37 <= etage <= 55:
            l, r = sans_bande(etage, l, r)
        out.append("{ 0x%04X, 0x%04X, 0x%02X, 0x%02X }" % (l & 0xFFFF, r & 0xFFFF, y, y))
    return ", ".join(out)


def ligne_c(etage, actuelles, y=0xF0):
    v = table_2i(etage, 1) or elargies(etage, actuelles)
    return ("    { %s },  /* etage %d : %s, %d px jouables */"
            % (trio(etage, actuelles, y), etage, NOMS.get(etage, "etage %d" % etage),
               v[1] - v[0]))


def main():
    ecrire = "--ecrire" in sys.argv
    lignes = io.open(BG_DATA, encoding="utf-8",
                     errors="surrogateescape").read().splitlines(True)
    n = 0
    print("%-22s %-21s %-21s %s" % ("etage", "pose", "mesure", "retenu"))

    for i, l in enumerate(lignes):
        m = re.search(r"etage (\d+) :", l)
        if not (m and l.lstrip().startswith("{ {") and 22 <= int(m.group(1)) <= 36):
            continue
        etage = int(m.group(1))
        v = [int(x, 16) for x in re.findall(r"0x([0-9A-Fa-f]{3,4})", l)[:2]]
        y = int(re.search(r"0x([0-9A-Fa-f]{2}) \}", l).group(1), 16)
        mes = table_2i(etage, 1) or bornes(etage)
        ret = mes
        print("%-22s 0x%03X..0x%03X (%3d)    0x%03X..0x%03X (%3d)    0x%03X..0x%03X (%3d)%s"
              % ("%d %s" % (etage, NOMS.get(etage, "")), v[0], v[1], v[1] - v[0],
                 mes[0], mes[1], mes[1] - mes[0], ret[0], ret[1], ret[1] - ret[0],
                 "   <= CHANGE" if tuple(ret) != tuple(v) else ""))
        lignes[i] = ligne_c(etage, v, y) + "\n"
        n += 1

    for etage in list(range(37, 56)) + [56, 57]:
        mes = table_2i(etage, 1) or bornes(etage)
        ret = mes if table_2i(etage, 1) else elargies(etage, (0x140, 0x2c0))
        print("%-22s 0x%03X..0x%03X (%3d)    0x%03X..0x%03X (%3d)    0x%03X..0x%03X (%3d)%s"
              % ("%d %s" % (etage, NOMS.get(etage, "New Generation")), 0x140, 0x2c0, 384,
                 mes[0], mes[1], mes[1] - mes[0], ret[0], ret[1], ret[1] - ret[0],
                 "   <= CHANGE" if tuple(ret) != (0x140, 0x2c0) else ""))

    if not ecrire:
        print("\nRien n'a ete ecrit. `--ecrire` pour poser les quinze lignes de bg_data.c.")
        print("Les etages 37 a 57 passent par `etagesng.py` et `etages2ibis.py`.")
        return 0

    io.open(BG_DATA, "w", encoding="utf-8",
            errors="surrogateescape").write("".join(lignes))
    print("\n%d lignes recrites dans %s" % (n, BG_DATA))
    return 0


if __name__ == "__main__":
    sys.exit(main())
