# -*- coding: utf-8 -*-
"""Cuit les elements de decor des quinze etages de 2nd Impact, sans aucun etat.

C'est `poser22.py` generalise par `annuaire2i`. Aucun `.state` nulle part, ni ici ni dans
ce qu'on importe -- ce fichier n'importe ni `elements`, ni `etat`, ni `flycast`.

    element du decor (annuaire2i)  ->  script du DECOR  ->  index global
        ->  anims de SON asset F_ETC  ->  sprite  ->  assemblage.poser_couleur
        ->  banque, a  (x + ancre + x0, sol - y + ancre_y + y0)
        ->  32 pages .tex par liste

LA CORRESPONDANCE DECOR -> BG N'EST PAS SUPPOSEE, ELLE EST DEDUITE
-----------------------------------------------------------------
On resout les scripts d'un decor et on regarde dans quel asset F_ETC ils tombent ; le nom
de l'asset porte l'etiquette du decor (`2i-b03-F_ETC26`). Les decors 0 a 13 se rangent
ainsi tout seuls, et le 16 tombe sur l'asset de `bg06` -- ce que `bases.py` disait deja de
`bg10`, « hugo bis, meme decor que bg06 ».

CE QUE CETTE CHAINE NE DONNE PAS ENCORE
---------------------------------------
Les **figures animees**, celles de la table de 8 octets. Elles ne sont dans aucune des dix
tables de la serie : le code de l'etage les porte en dur, une fonction par etage
(`0x8C04AE04` pour `bg00`, atteinte depuis `0x8C0DBA76`). Seul `bg00` en a donc, et c'est
`poser22.py` qui les pose. Les autres etages n'ont ici que leurs elements statiques.

    python poser2i.py              # mesure l'ecart, n'ecrit rien
    python poser2i.py --ecrire     # ecrit les pages
    python poser2i.py --ecrire bg03
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import annuaire2i as AN
import assemblage as A
import bande3sx
import bases
import fetc
import palettes
import pvc
from rendupvc import carte_morton, SIDE

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
BIN = os.path.join(RACINE, "SF3_2ND.BIN")
POFF = 0x1D9AEC

# Le meme casting que `cuire.py` : etage de 3SX, decor de 2I, banque du plan lointain.
ETAGES = [
    (22, "bg00", 0), (23, "bg01", 0), (24, "bg02", 0), (25, "bg03", 0),
    (26, "bg04", 0), (27, "bg05", 0), (28, "bg06", 0), (29, "bg07", 1),
    (30, "bg09", 1), (31, "bg0a", 1), (32, "bg0b", 0), (33, "bg0c", 0),
    (34, "bg0d", 0), (35, "bg0e", 0), (36, "bg0f", 1),
]

# Le plan `j` prend les emplacements `j*64 + 132`.
LISTE_LOINTAIN, LISTE_PROCHE, LISTE_TIERS, LISTE_QUATRE = 132, 196, 260, 324

# Quels plans de 2I partent sur le troisieme et le quatrieme plan de 3SX. Releve dans
# `cuire.py`, ou ces choix ont ete faits et vus a l'ecran.
PLANS_TROISIEME = {"bg00": {3}, "bg01": {3}, "bg09": {3}, "bg0e": {3}}
PLANS_QUATRIEME = {"bg00": {7}}

# Positions gelees sur l'ANCIENNE regle -- celle sans `y0`. Voir `poser22.py` : elles
# n'ont pas ete signalees, et `SANS-ETAT.md` interdit de deplacer ce qui ne l'a pas ete.
SANS_Y0 = {"bg00": {1}}

_banque = None
_assets = {}


def banque_des_palettes():
    global _banque
    if _banque is None:
        _banque = palettes.lire(BIN, POFF, 2715)
    return _banque


def asset(nom_fichier):
    if nom_fichier not in _assets:
        chemin = os.path.join(RACINE, "sprites", nom_fichier)
        _assets[nom_fichier] = (fetc.lire(open(chemin, "rb").read()),
                                A.charger(chemin)[1])
    return _assets[nom_fichier]


def decor_de_chaque_bloc():
    """bg -> numero de decor, DEDUIT : on suit les scripts jusqu'a l'asset."""
    spans = AN.spans_des_assets()
    out = {}
    for d in range(17):
        noms = set()
        for e in AN.elements(d):
            g = AN.index_global(d, e["script"])
            if g is None:
                noms.add(None)
                continue
            noms |= {n for n, (lo, hi) in spans.items() if lo <= g < hi}
        noms.discard(None)
        if not noms:
            continue
        # `2i-b03-F_ETC26` -> `bg03`. Un asset partage (b06 / b10) rend les deux ; on
        # garde celui qui n'est pas deja pris.
        for n in sorted(noms):
            bg = "bg" + n.split("-")[1][1:]
            if bg not in out:
                out[bg] = d
                break
    return out


# LE SOL EST UNE CONSTANTE DU REPERE, PAS LA DERNIERE LIGNE PEINTE — 01/09/2026.
#
# `sol` se mesurait « derniere ligne non vide de la moitie basse ». C'est une heuristique,
# et elle tombe juste seulement quand le decor descend jusqu'en bas de sa banque. Sur les
# quatorze decors elle rend **1023 pour douze d'entre eux** — dont `bg00`, dont les
# positions sont validees a l'ecran — et deux valeurs plus hautes :
#
#     bg0d  1007     bg05   972
#
# Or `element.y` est une HAUTEUR AU-DESSUS DU SOL, et le sol du repere ne depend pas de ce
# que le decor a peint : c'est la derniere ligne de la banque. La mesure ne disait donc pas
# le sol, elle disait « ou s'arrete le dessin » — encore une coherence prise pour un role.
#
# L'EFFET, ET IL EST VISIBLE : sur Sean, les 16 pixels d'ecart remontaient TOUT ce que nous
# posons — les elements cuits comme les objets animes, qui partagent cette fonction. C'est
# ce que Frederic a vu : « le singe anime est sur sa copie, les sprites sont trop haut ».
# Les deux chaines s'accordaient entre elles et se trompaient ensemble.
SOL_REPERE = 1023

# ===================================================================================
# LE SENS DE L'AXE EST ETABLI -- MESURE DU 01/09/2026, ET NON PLUS DEDUITE.
#
# L'acolyte de `bg00`, seul sprite dont la position soit validee a l'ecran (288, 81) et
# fige sur son image 0, a ete deplace de `y 81` a `y 113`. **Frederic : « monte ».** Donc,
# sans plus aucune ambiguite :
#
#     position_y ↑  ->  vers le HAUT
#     bank_y     ↑  ->  vers le BAS      (car y = 1024 - bank_y - (ligs-1)*16)
#     sol        ↑  ->  vers le BAS
#
# C'est l'inverse de ce que j'avais conclu en fin de session, et c'est pourquoi j'avais
# annule a tort : revenir a la mesure REMONTAIT Sean et Necro, dont les sprites etaient
# deja trop hauts.
#
# `sol` est donc la constante du repere. Les deux banques qui s'arretent avant 1023
# (`bg0d` a 1007, `bg05` a 972) ne posent pas leur sol ailleurs : elles ne PEIGNENT pas
# jusqu'en bas, ce qui est autre chose -- voir `decalage_sol`.
# ===================================================================================
SOL_MESURE = set()


# UN OBJET SUIT LA PAGE QU'ON A RECALEE -- 16/09/2026, et c'est la panne de Sean.
#
# `couches2i.demi_banque` descend la moitie basse de `bg0d` de SEIZE pixels pour que son
# dessin touche 1023 comme les douze autres (`decalage_sol`). Les objets, eux, restaient
# poses sur `SOL_REPERE` : la page descendait, eux non, et **tout ce que le code de 2I
# place chez Sean se retrouvait seize pixels trop haut**. Frederic : « une partie des
# sprites sont decales vers le haut ».
#
# LA PREUVE TIENT DANS LES TROUS DE LA PAGE. Les elements statiques de Sean ne sont pas
# peints dans sa banque : elle est **decoupee a leur silhouette**, et le jeu pose l'objet
# dans le trou. En cherchant, pour chacun, l'endroit ou sa silhouette couvre le trou et
# rien d'autre, on lit sa place VRAIE dans la banque brute :
#
#     script 3 (le conducteur)      formule 575,863  ->  trou 576,864
#     script 4 (le petit palmier)   formule 367,751  ->  trou 368,752
#     script 5 (le poteau)          formule 662,895  ->  trou 663,896
#     script 2 (l'homme a genou)    formule 655,911  ->  trou 656,912
#
# **Quatre sur cinq a un pixel pres**, dans la banque BRUTE. La formule etait donc juste
# et le repere aussi ; ce qui manquait, c'est que le recalage de la page s'applique aussi
# a ce qu'on pose dessus. `sol` le porte, et il ne change rien aux treize autres decors --
# leur `decalage_sol` vaut zero.
def sol(decor, banque=0):
    """La ligne du sol dans la PAGE CUITE : le repere, plus le recalage de cette banque."""
    if decor in SOL_MESURE:
        arr = banque_nue(decor)
        lignes = np.where((arr[512:, :, 3] > 0).any(1))[0]
        return int(lignes.max()) + 512 if len(lignes) else SOL_REPERE

    return SOL_REPERE + decalage_sol(decor, banque)


_nues = {}


# LE BAS DU DESSIN TOUCHE LA LIGNE 1023 -- SUR DOUZE DECORS SUR QUATORZE.
#
# Mesure du 01/09/2026, derniere ligne non vide de la moitie basse de la banque 0 :
#
#     bg00 bg01 bg02 bg03 bg04 bg06 bg08 bg0a bg0b bg0c bg0e bg10  ->  1023
#     bg0d Sean                                                    ->  1007
#     bg05 Necro                                                   ->   972
#
# Douze decors cales au pixel sur 1023, ce n'est pas un hasard : c'est la regle du format,
# et `bg00` -- dont les positions sont validees a l'ecran -- en fait partie. Les deux
# exceptions sont EXACTEMENT les deux decors que Frederic signale comme « trop hauts ».
#
# Leur dessin est donc pose trop haut dans la banque, et TOUT ce qui s'y rattache monte
# avec : la voiture, son conducteur et le personnage a genou -- qui sont PEINTS dans le
# decor, pas poses par nous -- autant que nos objets animes. C'est ce qui rendait le
# diagnostic trompeur : nos sprites n'etaient pas en cause, le plan l'etait.
#
# On rend donc a ces deux banques le calage des douze autres. Le decalage n'est pas choisi,
# il se mesure : `1023 - derniere ligne non vide`.
_decalages = {}


def decalage_sol(decor, banque=0):
    """De combien descendre la moitie basse pour que son dessin touche 1023.

    PLUS DE DECALAGE -- 16/09/2026. Le descripteur de scene de 2I (`descripteurs2i.py`)
    pose la moitie basse ligne pour ligne dans TOUS les decors, Sean compris : son dessin
    s'arrete en 1007 parce que 2I le montre ainsi, pas parce qu'il est mal cale. Frederic,
    avec les seize lignes : « tout le decor est affiche trop bas par rapport aux
    combattants ». La page et les objets remontent ensemble (`sol` suit). La mesure
    ci-dessous reste pour memoire ; elle ne s'applique plus.
    """
    return 0
    cle = (decor, banque)

    if cle not in _decalages:
        arr = _brute(decor, banque)
        par_ligne = (arr[512:, :, 3] > 0).sum(1)
        lignes = np.where(par_ligne > 0)[0]

        # LE DECALAGE NE VAUT QUE POUR UN SOL PLEIN, et c'est la correction du 01/09 (bis).
        #
        # Applique a `bg05` (Necro), il l'a DEGRADE : Frederic a vu ses personnages
        # d'arriere-plan partir trop haut. La mesure disait vrai et je l'ai mal lue --
        # les douze dernieres lignes de chaque banque :
        #
        #     bg00  768 768 768 768 768 768 768 768 768 768 768 768   sol PLEIN
        #     bg0d  768 768 768 768 768 768 768 768 768 768 768 768   sol PLEIN
        #     bg05  338 287 222  82  34  61  65  35  28  37  27   6   des BOUTS
        #
        # Le plan proche de Necro n'est pas un fond, c'est un PREMIER PLAN decoupe : sa
        # derniere ligne non vide n'est que le bout d'un sprite qui depasse, et la caler
        # sur 1023 deplace tout le reste. « Ou s'arrete le dessin » ne veut dire quelque
        # chose que quand le dessin est plein jusqu'au bord.
        seuil = arr.shape[1] // 3

        if not len(lignes) or par_ligne[lignes.max()] < seuil:
            _decalages[cle] = 0
        else:
            _decalages[cle] = 1023 - (int(lignes.max()) + 512)

    return _decalages[cle]


def _brute(decor, banque=0):
    """La banque telle qu'elle sort du disque, sans recalage."""
    cle = (decor, banque)
    if cle not in _nues:
        src = os.path.join(RACINE, "pvc-2i", decor + ".pvc")
        pages, _u, _ = pvc.decode(open(src, "rb").read())
        _nues[cle] = bande3sx.banque_rgba(pages, banque, carte_morton(SIDE))[0]
    return _nues[cle]


def banque_nue(decor, banque=0):
    arr = _brute(decor, banque).copy()
    d = decalage_sol(decor, banque)

    if d:
        bas = arr[512:].copy()
        arr[512:] = 0
        arr[512 + d:] = bas[:512 - d]

    return arr


def placer(decor, d, e, sans_y0=False):
    """(image RGBA, bx, by, palettes) pour un element de decor, ou None."""
    g = AN.index_global(d, e["script"])
    if g is None:
        return None
    a, tuiles = asset(bases.ASSETS[decor])
    lo, hi = a["index_global"]
    if not lo <= g < hi:
        return None
    offs = sorted({r[4] for r in a["anims"]})
    rec = a["anims"][g - lo]
    sp = a["sprites"][offs.index(rec[4])]
    b = bases.BASES_2I[decor]
    # Un decor peut avoir deux banques de palettes -- Oro en a deux, separees par
    # l'offset du morceau. `bases.numero` les demele ; le dict ne le pourrait pas.
    resoudre = lambda dr, off: bases.numero(decor, dr, off)
    pose = A.poser_couleur(sp, tuiles, banque_des_palettes(), b[min(b)], resoudre)
    if pose is None:
        return None
    rgba, x0, y0 = pose
    if sans_y0:
        x0 = y0 = 0
    bx = (e["x"] + rec[1] + x0) & 0x3FF
    by = (sol(decor) - e["y"] + rec[2] + y0) & 0x3FF
    pals = {}
    for m in A.morceaux(sp):
        n = bases.numero(decor, m["drapeaux"], m["palette"])
        if n is not None:
            pals[n] = pals.get(n, 0) + 1
    return rgba, bx, by, pals


def peindre(plan, rgba, bx, by, libre=None):
    """Pose un element. `libre` : masque des pixels ou l'on a le droit d'ecrire.

    **On n'ecrit que la ou il n'y avait pas deja un sprite.** Les positions du binaire
    retrouvent celles des relevés au pixel -- verifie sur onze elements de quatre decors,
    recouvrement maximal a (0,0) pour tous. Ce qui differe encore, ce sont des COULEURS :
    `bases.py` ne connait la base de palette d'un decor que pour les offsets que
    `PALETTES-CONFIRMEES.md` a etablis, et les autres sont extrapoles. Le relevé, lui,
    lisait la palette dans la RAM du jeu. Repeindre par-dessus, ce serait remplacer une
    couleur mesuree par une couleur supposee.
    """
    h, w = rgba.shape[:2]
    sub = plan[by:by + h, bx:bx + w]
    src = rgba[:sub.shape[0], :sub.shape[1]]
    op = src[:, :, 3] > 0
    if libre is not None:
        op = op & libre[by:by + sub.shape[0], bx:bx + sub.shape[1]]
    sub[op] = src[op]
    return int(op.sum())


def effacer(plan, rgba, bx, by, nue):
    """Rend a la banque nue les pixels de cette empreinte, et EUX SEULS.

    C'est l'inverse exact de `peindre` : on ne touche qu'aux pixels que l'element aurait
    couverts, et on y remet ce que le disque porte. Le reste de la page -- y compris ce
    qu'une cuisson anterieure y a laisse et qu'aucun objet ne remplace -- ne bouge pas.
    """
    h, w = rgba.shape[:2]
    sub = plan[by:by + h, bx:bx + w]
    src = rgba[:sub.shape[0], :sub.shape[1]]
    fond = nue[by:by + sub.shape[0], bx:bx + sub.shape[1]]
    op = src[:, :, 3] > 0
    # Seulement la ou la page differe deja du disque : ailleurs il n'y a rien a defaire.
    change = op & (np.abs(sub[:, :, :3].astype(int) - fond[:, :, :3].astype(int)).sum(2) > 0)
    sub[change] = fond[change]
    return int(change.sum())


def effacer_les_animes(decor, etage, plan, nue):
    """Rend la banque nue sous l'empreinte de chaque objet anime de cet etage.

    L'empreinte est lue dans `decor_objets_data.c`, donc dans ce qui est COMPILE : c'est
    exactement la surface que le moteur va recouvrir. Rend (pixels rendus, nb d'objets).
    """
    try:
        import rendu_fiches
        src, octets, _pal, cases = rendu_fiches.charger()
    except Exception as e:
        print("   (fiches compilees illisibles : %s -- on n'efface rien)" % e)
        return 0, 0

    total = objets = 0

    for m in rendu_fiches.FICHE.finditer(src):
        ch = [c.strip() for c in m.group(2).split(",")]

        # ON APPARIE PAR ETAGE, PAS PAR NOM DE BG. Les deux chaines ne nomment pas toujours
        # le meme decor pareil -- l'etage 30 est `bg09` ici et `bg08` dans les fiches -- et
        # l'etage, lui, est sans ambiguite. Le nom servait de filtre et laissait bg08 sans
        # aucun nettoyage, alors que ses objets sont bel et bien poses.
        if len(ch) < 15 or int(ch[0]) != etage:
            continue

        cols, ligs = int(ch[3]), int(ch[4])
        x, y = int(ch[9]), int(ch[10])
        by = 1024 - y - (ligs - 1) * 16
        h, w = ligs * 16, cols * 16
        sub = plan[by:by + h, x:x + w]
        fond = nue[by:by + sub.shape[0], x:x + sub.shape[1]]

        if sub.shape[:2] != fond.shape[:2] or sub.size == 0:
            continue

        # LA BOITE N'EST PAS L'EMPREINTE, et les confondre a vide le decor.
        #
        # Un sprite ne remplit pas sa grille : effacer toute la boite rendait la banque
        # AUSSI la ou l'objet ne peint jamais rien, et emportait tout ce qu'une cuisson
        # ancienne y avait pose sans qu'aucun objet le remplace. Frederic : « il manque
        # tous les sprites ». L'empreinte, c'est l'UNION des pixels opaques sur toutes les
        # images -- en dehors, la cuisson reste.
        couvre = np.zeros((h, w), bool)

        for image, tx, ty, nom_px in cases.get(ch[5], ()):
            if nom_px not in octets:
                continue

            # Une tuile en bord de page est tronquee : on rogne le motif d'autant.
            plat = octets[nom_px][rendu_fiches.DETABLE].reshape(16, 16)
            zone = couvre[ty:ty + 16, tx:tx + 16]
            zone |= (plat != 0)[:zone.shape[0], :zone.shape[1]]

        couvre = couvre[:sub.shape[0], :sub.shape[1]]
        d = (np.abs(sub[:, :, :3].astype(int) - fond[:, :, :3].astype(int)).sum(2) > 0) & couvre
        sub[d] = fond[d]
        total += int(d.sum())
        objets += 1

    return total, objets


def ecrire_liste(sortie, plan, liste):
    os.makedirs(sortie, exist_ok=True)
    for i in range(32):
        px, py = (i & 7) * 128, 512 + (i >> 3) * 128
        bande3sx.ecrire_tex(os.path.join(sortie, "%d-%d.tex" % (liste, liste + i)),
                            plan[py:py + 128, px:px + 128])


def lire_liste(sortie, liste):
    """Les 32 pages d'une liste, recomposees en 1024x1024, ou None si elles manquent.

    **On repart des pages en place, pas de la banque nue.** Ajouter, pas repeindre : la
    chaine ne sait pas encore produire les figures animees des autres etages (leurs
    tables de 8 octets sont portees en dur par le code de chaque etage), et recuire
    depuis la banque les effacerait. Un element deja pose au bon endroit se retrouve
    repeint a l'identique -- ce qui est aussi un controle : le nombre de pixels CHANGES
    dit ce que le binaire apporte vraiment.
    """
    out = np.zeros((1024, 1024, 4), np.uint8)
    vues = 0
    for i in range(32):
        f = os.path.join(sortie, "%d-%d.tex" % (liste, liste + i))
        if not os.path.exists(f):
            continue
        vues += 1
        d = open(f, "rb").read()
        a = np.frombuffer(d[16:], dtype=np.uint8).reshape(128, 128, 4).copy()
        a[:, :, [0, 2]] = a[:, :, [2, 0]]
        px, py = (i & 7) * 128, 512 + (i >> 3) * 128
        out[py:py + 128, px:px + 128] = a
    return out if vues else None


# ON NE CUIT PAS CE QUE LE CODE ANIME — 04/09/2026
# ================================================
# Frederic a signale cinq fois des « copies » fixes sous les sprites animes de Yun. La
# cause n'etait ni une carte de tuiles, ni une position, ni un filtre : **c'etait ce
# fichier**. On cuisait comme element statique un personnage que le code cree comme objet
# anime, puis `animer2i` posait l'objet par-dessus. Deux figures des que l'animation
# s'ecarte de la pose peinte.
#
# LA MESURE : la demi-banque BRUTE du disque montre la scene SANS le vieil homme ni la dame
# en rose ; notre page cuite les contient. 40 660 pixels de difference, colonnes 128-463,
# **480-575** -- leurs positions exactes -- et 624-783.
#
# L'import est TARDIF, et il le faut : `animer2i` importe ce module.
def scripts_animes(decor):
    """Les scripts que `animer2i` pose en objets animes pour ce decor."""
    try:
        import animer2i
    except Exception as e:
        print("   (animer2i indisponible : %s -- on cuit tout)" % e)
        return set()

    if decor not in animer2i.TABLES:
        return set()

    try:
        return {o["script"] for o in animer2i.objets(decor)}
    except Exception as e:
        print("   (liste des objets animes indisponible : %s -- on cuit tout)" % e)
        return set()


# Repartir de la banque BRUTE au lieu de la page deja cuite. Sans ca, retirer un element de
# la cuisson ne l'efface pas : il reste dans la page ecrite au tour precedent.
REFAIRE = "--refaire" in sys.argv


def main():
    args = sys.argv[1:]
    ecrire = "--ecrire" in args
    if ecrire:
        args.remove("--ecrire")
    filtre = args[0] if args else None

    par_bg = decor_de_chaque_bloc()
    print("correspondance deduite  bg -> decor : "
          + ", ".join("%s=%d" % (k, v) for k, v in sorted(par_bg.items())))
    print()
    print("%-6s %-6s %-6s %s" % ("etage", "decor", "bloc", "ce que le binaire pose"))

    for etage, decor, _bq in ETAGES:
        if filtre and filtre != decor:
            continue
        sortie = os.path.join(RACINE, "etages2i-sprites", "stage%d" % etage)
        d = par_bg.get(decor)
        if d is None or decor not in bases.ASSETS or decor not in bases.BASES_2I:
            # PAS D'ELEMENT NE VEUT PAS DIRE RIEN A NETTOYER. Quatre decors -- bg07, bg09,
            # bg0a (Oro) et bg0f -- n'ont aucun element dans l'annuaire et sortaient donc
            # ici sans que la page soit touchee. Or leurs objets animes sont poses, et ce
            # que d'anciennes passes ont cuit sous eux y restait. Le nettoyage ne demande
            # que les fiches compilees : il n'a pas besoin de l'annuaire.
            n = ou = 0
            try:
                proche = lire_liste(sortie, LISTE_PROCHE)
                if proche is not None:
                    n, ou = effacer_les_animes(decor, etage, proche, banque_nue(decor))
                    if n and ecrire:
                        ecrire_liste(sortie, proche, LISTE_PROCHE)
            except Exception as e:
                print("%-6d %-6s %-6s  nettoyage impossible : %s" % (etage, decor, "-", e))
                continue

            print("%-6d %-6s %-6s  aucun element dans l'annuaire ; %d objet(s) anime(s), "
                  "%d px de cuisson rendus a la banque" % (etage, decor, "-", ou, n))
            continue
        els = AN.elements(d)
        animes = scripts_animes(decor)
        tiers_plans = PLANS_TROISIEME.get(decor, set())
        quatre_plans = PLANS_QUATRIEME.get(decor, set())
        proche = lire_liste(sortie, LISTE_PROCHE)
        if proche is None:
            proche = banque_nue(decor)
        tiers = lire_liste(sortie, LISTE_TIERS)
        if tiers is None:
            tiers = np.zeros((1024, 1024, 4), np.uint8)
        quatre = lire_liste(sortie, LISTE_QUATRE)
        if quatre is None:
            quatre = np.zeros((1024, 1024, 4), np.uint8)
        temoins = {LISTE_PROCHE: proche.copy(), LISTE_TIERS: tiers.copy(),
                   LISTE_QUATRE: quatre.copy()}
        nue = banque_nue(decor)

        # L'ORDRE : ON CUIT, PUIS ON NETTOIE. Et il a fallu deux essais pour y arriver.
        #
        # Nettoyer APRES avec une empreinte grossiere -- la BOITE de l'objet -- emportait
        # 4 265 pixels d'elements qu'aucun objet ne remplace. En nettoyant AVANT, les
        # elements se reposaient ensuite SOUS les sprites et la copie revenait.
        # Maintenant que l'empreinte est l'union des pixels opaques du sprite, nettoyer
        # apres ne retire QUE ce que l'objet recouvre vraiment.
        rendus = nb_animes = 0

        # Les pixels ou l'on a le droit d'ecrire : ceux qui ne portent pas deja un sprite.
        # Le masque se calcule APRES le nettoyage, sinon il interdirait d'ecrire la ou on
        # vient justement de rendre la banque.
        libres = {
            LISTE_PROCHE: ~((np.abs(proche[:, :, :3].astype(int) - nue[:, :, :3].astype(int)).sum(2) > 12)
                            & (proche[:, :, 3] > 0)),
            LISTE_TIERS: tiers[:, :, 3] == 0,
            LISTE_QUATRE: quatre[:, :, 3] == 0,
        }
        poses = []
        for k, e in enumerate(els):
            r = placer(decor, d, e, sans_y0=(k in SANS_Y0.get(decor, set())))

            # ON NE CUIT PAS CE QUE LE CODE ANIME, ET ON EFFACE CE QU'ON A CUIT AVANT.
            #
            # Effacer veut dire : rendre a la BANQUE NUE les pixels de l'empreinte, et eux
            # seuls. La premiere version repartait de la banque pour toute la page -- elle
            # emportait alors ce qu'une cuisson anterieure avait pose et qu'aucun objet ne
            # remplace. Frederic : « il est evident que si un element cuit et qu'aucun
            # objet ne le pose, il faut le garder ».
            if e["script"] in animes:
                if r is None:
                    poses.append("   element %d : script %d ANIME (empreinte inconnue)"
                                 % (k, e["script"]))
                    continue

                # ON NE CUIT PLUS, MAIS ON N'EFFACE PAS SON EMPREINTE D'ELEMENT.
                #
                # L'element et l'objet ne sont pas au meme endroit : la charrette de Yun est
                # element en banque 303 -- la ou le balayage la retrouve peinte -- et objet
                # en 536. Effacer l'empreinte de l'element retirait donc une charrette
                # qu'aucun objet ne remplace : 4 235 pixels, et « il manque tous les
                # sprites ». On n'efface que sous les SPRITES des objets, plus bas.
                _rgba, bx, by, _pals = r
                poses.append("   element %d  script %d ANIME : on ne le cuit plus "
                             "(il aurait ete en %d,%d)" % (k, e["script"], bx, by))
                continue
            if r is None:
                poses.append("   element %d : script %d irresolu" % (k, e["script"]))
                continue
            rgba, bx, by, pals = r
            if e["plan"] in quatre_plans:
                cible, ou = quatre, LISTE_QUATRE
            elif e["plan"] in tiers_plans:
                cible, ou = tiers, LISTE_TIERS
            else:
                cible, ou = proche, LISTE_PROCHE
            total = int((rgba[:, :, 3] > 0).sum())
            n = peindre(cible, rgba, bx, by, libres[ou])
            poses.append("   element %d  plan %d  %4d,%-3d -> banque %3d,%-3d  liste %d  "
                         "%dx%d  %5d px dont %5d ajoutes  palettes %s"
                         % (k, e["plan"], e["x"], e["y"], bx, by, ou,
                            rgba.shape[1], rgba.shape[0], total, n,
                            ", ".join(str(v) for v in sorted(pals))))
        rendus, nb_animes = effacer_les_animes(decor, etage, proche, nue)

        if rendus:
            poses.append("   %d objet(s) anime(s) : %d px de cuisson rendus a la banque "
                         "APRES la cuisson" % (nb_animes, rendus))

        changes = {}
        for liste, apres in ((LISTE_PROCHE, proche), (LISTE_TIERS, tiers),
                             (LISTE_QUATRE, quatre)):
            av = temoins[liste]
            changes[liste] = int((np.abs(apres.astype(int) - av.astype(int)).sum(2) > 0).sum())
        print("%-6d %-6s %-6d  %d element(s) ; pixels CHANGES : 196 %d, 260 %d, 324 %d"
              % (etage, decor, d, len(els),
                 changes[LISTE_PROCHE], changes[LISTE_TIERS], changes[LISTE_QUATRE]))
        for l in poses:
            print(l)
        if ecrire:
            if changes[LISTE_PROCHE]:
                ecrire_liste(sortie, proche, LISTE_PROCHE)
            if tiers_plans and changes[LISTE_TIERS]:
                ecrire_liste(sortie, tiers, LISTE_TIERS)
            if quatre_plans and changes[LISTE_QUATRE]:
                ecrire_liste(sortie, quatre, LISTE_QUATRE)
            print("   ecrit dans %s" % os.path.basename(sortie))

    if not ecrire:
        print("\nRien n'a ete ecrit. `--ecrire` pour poser les pages.")


if __name__ == "__main__":
    main()
