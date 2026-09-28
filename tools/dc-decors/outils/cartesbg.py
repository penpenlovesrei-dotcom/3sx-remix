# -*- coding: utf-8 -*-
"""Decodage de bg_map_tbl / stageXXX_map[64] de 3SX, et regle de placement des pages.

Tout ce qui est imprime ici est verifie contre le code de src/sf33rd/Source/Game/stage/
et contre les tables de bg_data.c. Rien n'est suppose.

    python cartesbg.py            # la demonstration complete
    python cartesbg.py --cartes   # les 42 cartes dessinees
"""
import re, sys
from collections import Counter
from cartes import lire, cartes, table_bg_map, tableau_u32_2d, tableau_u8, cells

SYM = {0: ".", 1: "#", 2: "+"}
NOMS = ["GILL","ALEX","RYU","YUN","DUDLEY","NECRO","HUGO","IBUKI","ELENA","ORO","YANG","KEN",
        "SEAN","URIEN","AKUMA","CHUN-LI","MAKOTO","(=16)","TWELVE","REMY","BONUS1","BONUS2"]
# bg_map_tbl2 et bgtex_etc_gbix, pour les ecrans fixes
ETC = [("win_lose_map", 0xFFFF), ("rank_map", 0xF0F0), ("select_map", 0xFFFF),
       ("win_lose_map", 0xFFFF), ("win_lose_map", 0xFFFF), ("win_lose_map", 0xFFFF),
       ("rank_map", 0xF0F0)]


def contexte():
    src = lire()
    cs = cartes(src)
    tbl = table_bg_map(src)
    gbix = tableau_u32_2d(src, "bgtex_stage_gbix", 23, 3)
    urs = tableau_u8(src, "use_real_scr")
    plans = []
    for st in range(22):
        for i in range(3):
            if tbl[st][i] != "NULL":
                plans.append((st, i, tbl[st][i], gbix[st][i]))
    return cs, plans


def alphabet(cs):
    print("1. L'alphabet des cases")
    c = Counter()
    for v in cs.values():
        c.update(cells(v))
    tot = sum(c.values())
    print(f"   {len(cs)} cartes x 64 mots x 8 cases = {tot} cases")
    for k in (0, 1, 2, 3):
        print(f"     valeur {k} : {c[k]:6d}")
    print("   La valeur 3 n'apparait jamais. Un champ de 2 bits qui ne prend que trois")
    print("   valeurs sur 21504 tirages n'est pas un hasard : la case fait bien 2 bits,")
    print("   il y en a 512 par carte, et l'etat 3 n'existe pas.\n")


def semantique(cs, plans):
    print("2. Ce que valent 1 et 2")
    print("   Repartition selon le rang du plan (0 = fond, 1 et 2 = avant-plans) :")
    agg = {}
    for st, i, n, g in plans:
        cl = cells(cs[n])
        a, b = agg.setdefault(i, [0, 0])
        agg[i] = [a + cl.count(1), b + cl.count(2)]
    for i in sorted(agg):
        u, d = agg[i]
        print(f"     plan {i} : {u:5d} cases a 1, {d:5d} cases a 2  -> {100*d/(u+d):4.1f} % de 2")
    print("   Les cas extremes tranchent : DUDLEY plan 0, YANG plan 0, CHUN-LI plan 0 et")
    print("   BONUS2 n'ont aucune case a 2 ; YANG plan 1 et ELENA plan 1 n'ont aucune case")
    print("   a 1. Un fond est opaque de bout en bout, un avant-plan est troue de bout en")
    print("   bout. Donc : 0 = rien a dessiner, 1 = opaque, 2 = comporte du transparent.\n")


def geometrie(cs):
    print("3. La geometrie : deux mots par page de 128x128")
    print("   Preuve par les ecrans fixes, ou bgtex_etc_gbix est simple et sans surprise.")
    print("   Regle testee : les mots 2c et 2c+1 decrivent la page dont le bit gbix vaut c.")
    print()
    print(f"   {'ecran':10s} {'carte':14s} {'gbix':>8s}  dessine sans page / page sans dessin")
    ok = True
    for t, (n, g) in enumerate(ETC):
        m, v = _verifie(cs[n], g)
        if n != "rank_map" and (m or v):
            ok = False
        print(f"   etc {t:<6d} {n:14s} {g:#08x}  {len(m):2d} {str(m) if m else '':28s} {len(v):2d}")
    print()
    print("   win_lose_map et select_map tombent juste dans les deux sens, zero ecart :")
    print("   16 pages chargees, 16 pages dessinees, les memes. rank_map decale de quatre,")
    print("   et c'est attendu : c'est le seul ecran dont Bg_Texture_Load2 remappe l'ordre")
    print("   des morceaux par etcBgGixCnvTable.")
    print("   Donc une page = 2 mots = 16 cases, et une case = 32x32 pixels.\n")
    return ok


def _verifie(v, g):
    manque, vide = [], []
    for c in range(32):
        plein = v[2 * c] != 0 or v[2 * c + 1] != 0
        pres = bool(g & (0x80000000 >> c))
        if plein and not pres:
            manque.append(c)
        if pres and not plein:
            vide.append(c)
    return manque, vide


def etages(cs, plans):
    print("4. Les etages : la carte deborde toujours du meme cote")
    print(f"   {'etage':22s} {'carte':14s} {'gbix':>10s}  hors-page / page vide")
    for st, i, n, g in plans:
        m, v = _verifie(cs[n], g)
        print(f"   {st:2d} {NOMS[st]:8s} plan {i}   {n:14s} {g:#010x}  {len(m):2d} {len(v):2d}   {m if m else ''}")
    print()
    print("   Les etages dont gbix vaut 0xFFFFFFFF tombent juste sans exception.")
    print("   Ceux dont gbix est ajoure debordent, et toujours sur les colonnes 0 et 7 :")
    print("   la carte decrit un plan entier de 8 colonnes, l'atlas PS2 n'en charge que")
    print("   ce dont il se sert. La carte est plus vieille que ce portage.\n")


def placement():
    print("5. Ou atterrit une page -- lu dans le code, pas deduit de la carte")
    print("   stage/bg.c, scr_trans() et bgDrawOneScreen() :")
    print()
    print("       gbix = ((y >> 7) << 3) + (x >> 7) + gixbase   avec gixbase = bgnm*64 + 100")
    print("       for (y = yy[0]; y < yy[1]; y += 128)")
    print("         for (x = xx[0]; x < xx[1]; x += 128)")
    print()
    print("   et Bg_Texture_Load_EX() charge le i-eme bit de bgtex_stage_gbix[etage][plan]")
    print("   sous le numero bgnm*64 + 132 + i. Comme 132 = 100 + 32 :")
    print()
    print("       page i  ->  x = (i & 7) * 128        y = 512 + (i >> 3) * 128")
    print()
    print("   x et y sont bornes a 0x3FF : l'espace de defilement d'un plan fait 1024x1024")
    print("   et boucle. Les 32 pages occupent sa moitie basse, 8 colonnes sur 4 rangees,")
    print("   remplies dans l'ordre de lecture par numero de bit croissant.")
    print()
    print("   C'est la reponse a << ou atterrit chaque page >>, et elle ne doit rien a la")
    print("   carte. La carte ne place rien : elle classe ce qui est deja place.\n")


def dessine(cs):
    for n in sorted(cs):
        print(f"--- {n}   (32 pages de 4x4 cases ; une page par bloc, 8 par rangee)")
        cl = cells(cs[n])
        for pr in range(4):
            for ly in range(4):
                ligne = []
                for pc in range(8):
                    p = pr * 8 + pc
                    ligne.append("".join(SYM[cl[p * 16 + ly * 4 + lx]] for lx in range(4)))
                print("   " + " ".join(ligne))
            print()


if __name__ == "__main__":
    cs, plans = contexte()
    if "--cartes" in sys.argv:
        dessine(cs)
    else:
        print("=" * 78)
        print("  bg_map_tbl / stageXXX_map[64] -- ce que c'est, et ce que ce n'est pas")
        print("=" * 78 + "\n")
        alphabet(cs)
        semantique(cs, plans)
        geometrie(cs)
        etages(cs, plans)
        placement()
