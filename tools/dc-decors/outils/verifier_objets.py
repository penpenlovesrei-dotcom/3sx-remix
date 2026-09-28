# -*- coding: utf-8 -*-
"""RELIT `decor_objets_data.c` ET VERIFIE CE QU'IL ANNONCE, champ par champ.

POURQUOI CET OUTIL EXISTE
-------------------------
Trois bornes du moteur ne se voient nulle part dans le generateur, et chacune se paie par
un GEL SANS MESSAGE -- le defaut le plus cher de ce chantier :

1. **`nb_tuiles` est la borne de boucle de `DecorObjets_Tuile`.** Elle valait
   `nb_images * cols * ligs`, ce qui supposait la table PLEINE. Depuis que les cases
   entierement transparentes sont sautees, l'annoncer ainsi ferait lire AU-DELA du
   tableau -- des octets pris au hasard televerses comme une tuile.
2. **`OBJETS_MAX` vaut 32**, et c'est la cle de cache qui l'impose : `rang << 11 |
   image << 5 | case` ne laisse que cinq bits au rang. Au-dela, deux objets partagent
   leurs cles et se dessinent l'un a la place de l'autre. `DecorObjets_Combien` ECRETE en
   silence : rien ne le dirait a l'ecran, sinon des objets manquants.
3. **le tas ne tient que 1024 morceaux** (`x16_map[4][16]`). Ce qui compte n'est pas le
   total mais les morceaux VIVANTS : `mts_base[7].life16` vaut douze trames, donc seules
   les images vues dans les douze dernieres occupent un emplacement. C'est cette mesure-la
   qui separe Akuma (marche) d'Ibuki a deux cascades (`CG展開エラー 16x16`).

    python verifier_objets.py
"""
import io
import os
import re
import sys

DATA = r"C:\Temp3sx\src\port\video\decor_objets_data.c"
TEXCASH = r"C:\Temp3sx\src\sf33rd\Source\Game\rendering\texcash.c"
INC_NG = r"C:\Temp3sx\src\port\video\etagesng_plans.inc"
INC_BIS = r"C:\Temp3sx\src\port\video\etages2ibis_plans.inc"

OBJETS_MAX = 56       # decor_objets.c -- 56 depuis le 18/09, la cle n'est plus en bits
CASES_MAX_C = 64      # NotreTrans.cases[], decor_objets.c
CLE_CASES = 64        # CASES_MAX de decor_objets.c (la cle n'a plus de champ de case)
CLE_IMAGES = 256      # huit bits d'image dans l'identite de motif, depuis le 17/09
MOTIFS = 128          # PATTERN_COLLECTION_MAX (structs.h), 64 sur la console : `rang <<6 | image` vus par le cache
VIE = 12              # mts_base[7].life16, en trames
PAR_PAGE = 256        # `mltnum16 = page16 << 8`, texcash.c
SERRE = 0.75          # au-dela, on previent : Dudley a GELE a 0,85 -- voir `budgets`


# CE CONTROLE A MENTI, ET IL A COUTE UN GEL -- 27/09/2026.
#
# Il comparait les morceaux vivants a une constante : 1024 pour 2nd Impact, 2560 pour New
# Generation. Or le tas n'est pas le meme pour tous : `mts_OB_page` le donne PAR ETAGE, et
# Dudley (etage 26) n'avait qu'UNE page, 256 morceaux, avec le commentaire « 1 objet, 6
# cases -- le feu de circulation ». Depuis le 25/09 il en porte dix, 218 morceaux vivants :
# 85 % de sa page. Le jeu a gele en fin de combat sur
#
#     fatal.log : « ＣＧキャッシュが一杯になりました。×１６　ＥＸＴ２ »
#
# et ce programme disait 218 sur 1024, 21 %, tout va bien. On lit donc desormais le budget
# REEL, la ou le build le pose : le tableau de `texcash.c`, et les deux macros generees
# qu'il epelle pour New Generation et pour les etages 56 et 57.
#
# ET ON PREVIENT A 75 %, pas seulement au depassement : le modele ci-dessous SOUS-COMPTE.
# La cle du cache est `(code, palette)` -- le meme morceau sous deux palettes prend deux
# emplacements -- et au changement d'aire les morceaux de la manche precedente vivent
# encore douze trames a cote de ceux de la nouvelle. 85 % a suffi a geler.
def _paires(txt):
    return [(int(a), int(b)) for a, b in re.findall(r"\{\s*(\d+)\s*,\s*(\d+)\s*\}", txt)]


def _define(chemin, nom):
    src = io.open(chemin, encoding="utf-8", errors="surrogateescape").read()
    m = re.search(r"#define\s+" + nom + r"\s*\\\s*\n(.*?)\n\s*\n", src, re.S)
    return _paires(m.group(1)) if m else []


def budgets():
    """Les morceaux 16x16 que le build accorde a CHAQUE etage. Lu, pas suppose."""
    src = io.open(TEXCASH, encoding="utf-8", errors="surrogateescape").read()
    m = re.search(r"mts_OB_page\[58\]\[2\]\s*=\s*\{(.*?)\n\};", src, re.S)

    if not m:
        return {}

    corps = re.sub(r"/\*.*?\*/", " ", m.group(1), flags=re.S)
    pages = []

    for t in re.finditer(r"\{\s*(\d+)\s*,\s*(\d+)\s*\}|(ETAGES\w*_OB_PAGE)", corps):
        if t.group(3):
            pages.extend(_define(INC_NG if "NG" in t.group(3) else INC_BIS, t.group(3)))
        else:
            pages.append((int(t.group(1)), int(t.group(2))))

    return {i: p[0] * PAR_PAGE for i, p in enumerate(pages)}


def lire():
    src = io.open(DATA, encoding="utf-8", errors="surrogateescape").read()

    # les tables de tuiles : combien d'entrees chacune porte REELLEMENT
    tuiles = {}
    for m in re.finditer(r"static const DecorTuile (\w+)_tuiles\[\] = \{(.*?)\n\};",
                         src, re.S):
        entrees = re.findall(r"\{\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),", m.group(2))
        tuiles[m.group(1)] = [tuple(int(v) for v in e) for e in entrees]

    durees = {}
    for m in re.finditer(r"static const unsigned char (\w+)_durees\[(\d+)\] = \{(.*?)\};",
                         src, re.S):
        durees[m.group(1)] = [int(v) for v in m.group(3).split(",") if v.strip()]

    palettes = {}
    for m in re.finditer(r"static const unsigned short (\w+)_palette\[64\] = \{(.*?)\};",
                         src, re.S):
        palettes[m.group(1)] = [int(v, 16) for v in
                                re.findall(r"0x([0-9A-Fa-f]{4})", m.group(2))]

    fiches = []
    bloc = re.search(r"const DecorAnimation decor_animations\[\] = \{(.*?)\n\};", src, re.S)
    for l in bloc.group(1).splitlines():
        m = re.match(r'\s*\{ "(\w+)", (\d+), (\d+), (\d+), (\d+), (\d+), (\w+)_tuiles'
                     r'.*?,\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),'
                     r'\s*(0x[0-9A-Fa-f]+)(?:,\s*-?\w+)*\s*\},',
                     l)
        if m:
            # LE DERNIER CHAMP EST `boucle`, ET IL CHANGE TOUT POUR LE CACHE.
            # Un objet qui ne boucle pas reste sur son image 0 (`image_de` le rend sans
            # condition) : il n'occupe donc qu'UNE identite de motif et les cases d'UNE
            # image, quel qu'en soit le nombre. Les acolytes de Gill sont dans ce cas.
            fiches.append(dict(decor=m.group(1), etage=int(m.group(2)),
                               nb_images=int(m.group(3)), nb_tuiles=int(m.group(4)),
                               cols=int(m.group(5)), ligs=int(m.group(6)),
                               prefixe=m.group(7), boucle=int(m.group(12)),
                               variante=int(m.group(13), 16)))

    par_etage = {}
    m = re.search(r"decor_nb_par_etage\[58\] = \{(.*?)\};", src, re.S)
    for i, v in enumerate(m.group(1).split(",")):
        par_etage[i] = int(v)

    m = re.search(r"decor_anim_par_etage\[58\] = \{(.*?)\};", src, re.S)
    premier = [int(v) for v in m.group(1).split(",")]

    return fiches, tuiles, durees, palettes, par_etage, premier


def images_vives(f, durees):
    """Combien d'IMAGES de cet objet sont vivantes au pire moment de la fenetre.

    LA BORNE QUI A GELE IBUKI, ET ELLE N'EST PAS CELLE DU TAS. `DecorObjets_Identite`
    forme `0x00D3 <<16 | rang <<6 | image` : c'est l'identite de MOTIF que le cache de
    `mlt_obj_trans_cp3_ext` indexe, et `PatternCollection` n'en tient que **64**. La trace
    du gel le disait en toutes lettres -- « 43 emplacements seulement dans la collection ».
    Chaque couple (objet, image) encore vivant en occupe un.
    """
    d = durees.get(f["prefixe"], [])
    if not d:
        return 0

    if not f.get("boucle", 1):
        return 1

    n = len(d)
    pire = 0

    for depart in range(n):
        reste = VIE
        k = depart
        vus = 0
        while reste > 0 and vus < n:
            vus += 1
            reste -= d[k % n]
            k += 1
        pire = max(pire, vus)

    return pire


def vivants(f, tuiles, durees):
    """Les morceaux VIVANTS au pire moment : la fenetre de douze trames la plus chargee.

    Le cache garde un motif douze trames ; les images vues dans cette fenetre occupent
    donc chacune ses cases. On fait glisser la fenetre sur le cycle et on prend le pire.
    """
    d = durees.get(f["prefixe"], [])
    t = tuiles.get(f["prefixe"], [])

    if not d or not t:
        return 0

    # cases occupees par image
    cases = {}
    for img, _x, _y in t:
        cases[img] = cases.get(img, 0) + 1

    if not f.get("boucle", 1):
        return sum(1 for img, _x, _y in t if img == 0)

    n = len(d)
    total = sum(d) or 1
    pire = 0

    # la fenetre part au debut de chaque image ; le cycle boucle
    for depart in range(n):
        reste = VIE
        k = depart
        vus = set()
        while reste > 0 and len(vus) < n:
            vus.add(k % n)
            reste -= d[k % n]
            k += 1
        pire = max(pire, sum(cases.get(i, 0) for i in vus))

    return pire


def main():
    fiches, tuiles, durees, palettes, par_etage, premier = lire()
    fautes = []
    BUD = budgets()

    if not BUD:
        fautes.append("mts_OB_page est introuvable dans texcash.c : aucun budget verifie")

    print("%d fiches" % len(fiches))
    print()

    for f in fiches:
        p = f["prefixe"]
        t = tuiles.get(p)
        d = durees.get(p)

        if t is None:
            fautes.append("%s : aucune table de tuiles" % p)
            continue

        # 1. LA BORNE DE BOUCLE
        if f["nb_tuiles"] != len(t):
            fautes.append("%s : la fiche annonce %d tuiles, la table en porte %d"
                          % (p, f["nb_tuiles"], len(t)))

        if d is None or len(d) != f["nb_images"]:
            fautes.append("%s : %d images annoncees, %d durees"
                          % (p, f["nb_images"], len(d) if d else 0))

        # 2. LES CASES SONT-ELLES DANS LA GRILLE, ET LES IMAGES DANS LE COMPTE
        for img, x, y in t:
            if not 0 <= img < f["nb_images"]:
                fautes.append("%s : tuile d'image %d hors des %d"
                              % (p, img, f["nb_images"]))
                break
            if not (0 <= x < f["cols"] * 16 and 0 <= y < f["ligs"] * 16):
                fautes.append("%s : tuile en %d,%d hors de la grille %dx%d"
                              % (p, x, y, f["cols"], f["ligs"]))
                break

        # 3. LES BORNES DE LA CLE DE CACHE
        if f["cols"] * f["ligs"] > CLE_CASES:
            fautes.append("%s : %d cases, la cle n'en code que %d"
                          % (p, f["cols"] * f["ligs"], CLE_CASES))

        if f["cols"] * f["ligs"] > CASES_MAX_C:
            fautes.append("%s : %d cases, `NotreTrans.cases` n'en tient que %d"
                          % (p, f["cols"] * f["ligs"], CASES_MAX_C))

        if f["nb_images"] > CLE_IMAGES:
            fautes.append("%s : %d images, la cle n'en code que %d"
                          % (p, f["nb_images"], CLE_IMAGES))

        # 4. LA PALETTE : l'index 0 doit rester transparent
        pal = palettes.get(p)
        if pal and pal[0] != 0:
            fautes.append("%s : l'index 0 de la palette vaut %04X, pas 0" % (p, pal[0]))

    # 5. LE COMPTE PAR ETAGE, ET LES MORCEAUX VIVANTS
    print("%-7s %-7s %-8s %-12s %-9s %-8s %-5s %-8s %s"
          % ("etage", "fiches", "tuiles", "cases/trame", "morceaux", "son tas", "%",
             "motifs", ""))
    print("-" * 86)

    for e in sorted(set(f["etage"] for f in fiches)):
        mes = [f for f in fiches if f["etage"] == e]
        nt = sum(f["nb_tuiles"] for f in mes)
        nc = sum(f["cols"] * f["ligs"] for f in mes)

        # LES BORNES SE COMPTENT PAR VARIANTE, pas sur l'etage entier. Le tableau porte
        # les quatre variantes d'Oro, mais le moteur n'en montre qu'une : additionner
        # tout surestimerait la charge et ecarterait des objets sans raison. On prend la
        # variante la PLUS CHARGEE.
        nv = nm = 0
        pire = mes
        # ET LES COMBATTANTS -- 16/09/2026 : les bits 0x10 (aucun ami du decor) et 0x20
        # (un ami) separent encore le chien couche du chien debout d'Oro.
        for zz, ami in [(zz, ami) for zz in range(4) for ami in (0x10, 0x20)]:
            vus = [f for f in mes if f.get("variante", 0xF) & (1 << zz)
                   and (not f.get("variante", 0xF) & 0x30 or f["variante"] & ami)]
            v = sum(vivants(f, tuiles, durees) for f in vus)
            m2 = sum(images_vives(f, durees) for f in vus)
            if m2 > nm or (m2 == nm and v > nv):
                nv, nm, pire = v, m2, vus

        note = ""

        if len(pire) > OBJETS_MAX:
            note = "  <<< %d fiches, ECRETE a %d" % (len(pire), OBJETS_MAX)
            fautes.append("etage %d : %d fiches pour %d places"
                          % (e, len(pire), OBJETS_MAX))

        if nm > MOTIFS:
            note += "  <<< %d motifs vivants, la collection en tient %d" % (nm, MOTIFS)
            fautes.append("etage %d : %d motifs vivants, la collection en tient %d"
                          % (e, nm, MOTIFS))

        tas = BUD.get(e, 0)
        pct = (100 * nv // tas) if tas else 0

        if not tas:
            fautes.append("etage %d : budget de morceaux illisible dans texcash.c" % e)
        elif nv > tas:
            note += "  <<< %d morceaux vivants pour %d, %d %%" % (nv, tas, pct)
            fautes.append("etage %d : %d morceaux vivants, son tas en tient %d (%d %%)"
                          % (e, nv, tas, pct))
        elif nv > SERRE * tas:
            note += "  <<< SERRE : %d %% de son tas" % pct
            fautes.append("etage %d : SERRE, %d morceaux sur %d (%d %%) -- Dudley a gele a"
                          " 85 %%, et le modele sous-compte" % (e, nv, tas, pct))

        if par_etage.get(e) != len(mes):
            fautes.append("etage %d : `decor_nb_par_etage` dit %d, il y a %d fiches"
                          % (e, par_etage.get(e), len(mes)))

        print("%-7d %-7d %-8d %-12d %-9d %-8d %-5d %-8d %s"
              % (e, len(mes), nt, nc, nv, tas, pct, nm, note))

    # 6. L'INDEX : la premiere fiche de chaque etage doit tomber sur une fiche a lui
    for e, p0 in enumerate(premier):
        if p0 < 0:
            continue
        n = par_etage.get(e, 0)
        for k in range(n):
            if p0 + k >= len(fiches) or fiches[p0 + k]["etage"] != e:
                fautes.append("etage %d : l'index %d ne tombe pas sur une de ses fiches"
                              % (e, p0 + k))
                break

    print()

    if fautes:
        print("%d FAUTES" % len(fautes))
        for f in fautes:
            print("  " + f)
        return 1

    print("Rien a signaler : bornes, index et tables se recoupent.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
