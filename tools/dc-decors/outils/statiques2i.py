# -*- coding: utf-8 -*-
"""Les plans supplementaires de 2nd Impact : ELEMENTS STATIQUES, lus dans leur chargeur.

Un plan supplementaire de Gill, Alex, Elena ou Urien ne porte pas de couche du `.pvc` : il
porte les elements statiques d'un plan de 2I (3 ou 7). Tout ce qu'il faut en savoir est
dans l'enregistrement que lit `0x8C0233B6` -- voir `etages.elements_statiques` :

    plan, x, y, PROFONDEUR (+556, celle que la requete de dessin passe au tri), script

et rien n'est suppose pour le peindre :

    asset     celui dont `index_global` contient l'index du script -- pas `bases.ASSETS`,
              qui ne connait qu'un asset par decor (Elena en a deux, F_ETC30 et F_ETC31)
    palette   le premier transfert de SA bande : u16[0x8C1D5D38 + bande*2] -> 0x8C1E4B50
    position  la regle de `poser2i.placer`, validee a l'ecran sur Gill

ELENA (bande 9, etage 30), CE QUE CET OUTIL REFAIT -- 16/09/2026
----------------------------------------------------------------
La table des couches de 2I ne donne a la bande 9 que deux couches, la banque 0 haut (94)
et la banque 0 bas (84). Sa banque 1 haut est la RESERVE de l'animation de pages 0 :
neuf trames de 320x160, que le jeu recopie dans le trou de sa couche du fond (320x160 en
256,352 -- la taille exacte d'une trame, et la seule fenetre transparente de la couche).
3SX posait cette reserve en plan lointain : la mosaique se voyait dans le trou.

    liste 132  plan lointain   banque 0 haut + la trame 0 dans son trou   (94, vitesse 0,5)
    liste 196  plan proche     banque 0 bas nue (le feu est un objet)     (84)
    liste 260  plan statique   l'element du plan 3, x 384 y 96            (86, vitesse 0,75)

Les listes 132 et 196 sont decalees de 128 : voir `DECALAGE_ELENA`. La cascade est animee
par les fiches de pages d'`animer2i` ; la trame 0 peinte dans le trou reste dessous.

    python statiques2i.py            # controle sur Gill, Alex, Urien ; n'ecrit rien
    python statiques2i.py --ecrire   # ecrit les listes 132, 196 et 260 de l'etage 30
"""
import glob
import os
import shutil
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import annuaire2i as AN
import assemblage as A
import bande3sx
import couches2i
import etages as E
import poser2i as P

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
DEPLOIEMENT = r"C:\Users\frede\OneDrive\Bureau\SEPTEMBRE\SF3\CrowdedStreet-3SX\resources\tex_remix"

# (etage, bg, bande, {plan de 2I -> liste de 3SX})
PLANS = [
    (22, "bg00", 0, {3: 260, 7: 324}),
    (23, "bg01", 1, {3: 260}),
    (30, "bg09", 9, {3: 260}),
    (35, "bg0e", 14, {3: 260}),
]


def base_de_palette(bande):
    idx = AN.u16(0x8C1D5D38 + bande * 2)
    return (AN.u32(0x8C1E4B50 + idx * 12) - 0x02798000) // 128


_assets = None


def asset_du_script(g):
    global _assets
    if _assets is None:
        _assets = AN.spans_des_assets()
    for nom, (lo, hi) in sorted(_assets.items()):
        if lo <= g < hi:
            return nom + ".bin"
    return None


def peindre_element(bande, e):
    """(rgba, bx, by) d'un element statique, sans rien supposer du decor."""
    d, aire = E.decor_et_aire(bande)
    t = AN.u32(AN.SCRIPTS + (d * 3 + aire) * 4)
    g = AN.u16(AN.u32(t + e["script"] * 4) + 6)
    nom = asset_du_script(g)
    if nom is None:
        return None
    a, tuiles = P.asset(nom)
    lo, _hi = a["index_global"]
    offs = sorted({r[4] for r in a["anims"]})
    rec = a["anims"][g - lo]
    sp = a["sprites"][offs.index(rec[4])]
    base = base_de_palette(bande)
    rgba, x0, y0 = A.poser_couleur(sp, tuiles, P.banque_des_palettes(), base,
                                   lambda _dr, off: base + off)
    bx = (e["x"] + rec[1] + x0) & 0x3FF
    by = (P.SOL_REPERE - e["y"] + rec[2] + y0) & 0x3FF
    return rgba, bx, by, nom, base


def plan_statique(bande, plan):
    toile = np.zeros((1024, 1024, 4), np.uint8)
    for e in E.elements_statiques(bande):
        if e["plan"] != plan:
            continue
        r = peindre_element(bande, e)
        if r is None:
            print("      element %d,%d : script %d irresolu" % (e["x"], e["y"], e["script"]))
            continue
        rgba, bx, by, nom, base = r
        P.peindre(toile, rgba, bx, by)
        print("      element plan %d  %d,%d  profondeur %d  -> banque %d,%d  %s  base %d"
              % (plan, e["x"], e["y"], e["profondeur"], bx, by, nom, base))
    return toile


# LES COUCHES D'ELENA 1 SONT POSEES 128 PLUS A DROITE QUE LA BANQUE -- 15/09/2026, nuit.
#
# Frederic : « decor casse ». L'elephant de pierre sortait A GAUCHE du feu, et la cascade
# se voyait la ou 2I montre l'elephant. Deux lectures independantes donnent le meme ecart :
#
#   * le binaire : l'animation de pages 0 ecrit sa trame en x 384 (`0x8C17D3DC`), et le trou
#     de la couche du fond est en 256 dans la banque ;
#   * la capture Flycast `cap-elena2.png`, ramenee a 384x224 et comparee aux pages : la
#     couche proche s'y cale au pixel en x 26 de la banque, alors que le feu -- un OBJET, en
#     coordonnees du monde (511 - 240 = 271) -- dit 154. Avec les pages decalees de 128,
#     les trois plans tombent ensemble sur les vitesses de 3SX a la camera de la capture :
#     proche 154, lointain 237 (0,5 : 320 + (154-320)/2 = 237, mesure 237), element du
#     plan 3 194 (0,75 : 195,5, mesure 194). Ecarts moyens 10 a 16 sur 255.
#
# Les elements statiques et les objets sont en coordonnees du monde : on ne les decale pas.
# La variante du pont (bande 8) n'a pas cet ecart : ses trames du lac tombent a leur x.
#
# LE DECALAGE ETAIT BON, LA ROTATION NE L'ETAIT PAS -- 28/09/2026.
# -----------------------------------------------------------------
# Frederic, apres une semaine d'essais : « le decor du 2eme round est glitche », puis
# « arrete de chercher, reconstruit correctement le decor, tu as une capture d'ecran, la
# version dreamcast, l'exemple de la version NG ».
#
# La version NG etait la bonne piste, et elle se mesure. Les deux Elena sont la meme scene :
#
#     Elena NG (etage 52)  liste 132  393216 px  colonnes 128..895  lignes 512..1023
#                          liste 196             colonnes 128..895  lignes 585..1023
#
# 768 de large, posee en 128. La notre montait la banque ENTIERE (1024) et la faisait
# tourner de 128 : les colonnes 896..1023 de la banque revenaient sur la scene 0..127, et il
# restait 96 colonnes vides au milieu -- le rectangle que Frederic voyait. Or ces colonnes
# ne sont pas du decor : `animer2i.PAGES_ANIMEES["bg08"]` les designe depuis le 15/09 comme
# les TROIS TRAMES TOURNEES de la cascade (x 864). On collait donc un bout de cascade au
# bord de la page, et on laissait un trou a cote.
#
# ON NE FAIT PLUS TOURNER RIEN : on pose les rectangles du DESCRIPTEUR DE SCENE du decor 9
# (`descripteurs2i.ELENA_CHUTE`, cas 9 du moteur de decor, desassemble), comme on le fait
# pour Ibuki depuis le 16/09. Mesure de la page ainsi composee :
#
#     liste 132  393216 px  colonnes 128..895  (0 creuse)  lignes 512..1023
#     liste 196  166120 px  colonnes 128..895              lignes 585..1023
#
# soit, au pixel pres pour la 132 et a la ligne pres pour la 196, la geometrie de NG.
DECALAGE_ELENA = 128


def _elena_chute(couche, etat):
    """Les rectangles du descripteur de la bande 9 pour une couche, plus son etat anime.

    `etat` : le descripteur de l'emplacement 0 (la cascade, douze trames) pour la couche 0,
    celui de l'emplacement 1 (le bord de l'eau, deux etats) pour la couche 1. On cuit l'etat
    0 : les suivants sont servis par les fiches de pages d'`animer2i`."""
    import descripteurs2i as D

    toile = D.composer("bg09", D.lire(D.ELENA_CHUTE["base"]), couche)
    D.composer("bg09", D.lire(etat), couche, toile)
    return toile


def elena_lointain():
    """Couche 0 de la bande 9 : le ciel, la falaise, et la trame 0 de la cascade dans le trou.

    Le trou de 320x160 en scene 384,864 est laisse par la base elle-meme -- elle peint
    128..383 et 704..895 sur ces lignes, pas le milieu."""
    import descripteurs2i as D

    return _elena_chute(0, D.table(D.ELENA_CHUTE["table_cascade"], 12)[0])


def elena_proche():
    """Couche 1 de la bande 9 : le plan proche (banque v 576), et l'etat 0 du bord de l'eau.

    Le feu n'y est pas cuit : c'est l'objet du chargeur `0x8C025A9A` (script 1 de l'aire 1,
    dix images). Les trous de la banque autour de lui sont exactement sous le sprite."""
    import descripteurs2i as D

    return _elena_chute(1, D.table(D.ELENA_CHUTE["table_eau"], 2)[0])


# ELENA, LA VARIANTE (bande 8, etage 56) -- LE PONT DE CORDE AU-DESSUS DU LAC, 16/09/2026
# ------------------------------------------------------------------------------------------
# Tout est lu dans le code de la routine d'etage de la bande 8 (0x8C0DDA1C..0x8C0DE0A3),
# et recoupe par les captures Flycast `apercu-3elena.png` :
#
#   * la table des couches ne lui donne qu'UNE couche utile, la banque 0 haut (94) : le ciel
#     et la montagne. Sa couche 1 (120) n'est qu'une bande de 2 lignes vides ; le reste de
#     sa banque 0 bas est la RESERVE du lac ;
#   * les animations de pages 6 et 7 (`0x8C0277C4`, args 6 et 7) recopient le lac dans la
#     bande vide de 80 lignes sous la montagne : 144x16 en (416,416), 320x64 en (352,432).
#     Les blocs qui changent d'une trame a l'autre tombent EXACTEMENT sur ces destinations :
#     les trames sont rangees a leur place horizontale, 96 et 144 lignes plus bas ;
#   * le second jeu d'elements statiques (`0x8C02356A`) : NEUF elements -- les deux
#     falaises (78), le rocher violet du plan 3 (79), les deux arbres morts a cranes (20,
#     DEVANT les combattants) ;
#   * le PONT est l'objet 123 de `0x8C03CE46` : script 0, plan 2, profondeur 76, le sprite 0
#     de 768x48. Le spawner n'ecrit pas sa position -- centre, x 512 -- et sa hauteur est
#     calee sur la capture : son plancher est au meme endroit de l'ecran que celui d'Elena 1,
#     peint en ligne 452 de sa banque 0 bas, d'ou y 40. Il est cuit : dans 2I il tombe a la
#     fin de la manche, ce que 3SX ne joue pas.
#
#     liste 132  ciel + trames 0 du lac        94   0,0625 / 0,5  (objet 0)
#     liste 196  falaises + pont               78   1 / 1         (plan de base)
#     liste 260  rocher du plan 3              79   0,75 / 0,75   (objet 2, ecrit en dur)
#     liste 324  arbres a cranes               20   1 / 1         (devant les combattants)
VARIANTE_BANDE, VARIANTE_ETAGE = 8, 56
PONT = dict(asset="2i-b08-F_ETC30.bin", sprite=0, x=512, y=40)


def elements_second_jeu(bande):
    d, aire = E.decor_et_aire(bande)
    i = d * 3 + aire
    n = AN.u16(0x8C17BBC4 + i * 2)
    p = AN.u32(0x8C5F9CD0 + i * 4)
    out = []
    for k in range(n):
        w = struct.unpack_from("<8H", AN._D, p + k * 16 - AN._B)
        s = lambda v: struct.unpack("<h", struct.pack("<H", v))[0]
        out.append(dict(rang=k, plan=w[1], x=s(w[3]), y=s(w[4]), profondeur=w[5], script=w[6]))
    return out


def poser_sans_repli(toile, rgba, x, y):
    """Pose en coordonnees de banque SANS le `& 0x3FF` : ce qui passe sous la ligne 1023
    (le bas des falaises) est coupe, pas replie en haut de la page."""
    h, w = rgba.shape[:2]
    y0, y1 = max(0, y), min(1024, y + h)
    x0, x1 = max(0, x), min(1024, x + w)
    if y0 >= y1 or x0 >= x1:
        return 0
    src = rgba[y0 - y:y1 - y, x0 - x:x1 - x]
    dst = toile[y0:y1, x0:x1]
    op = src[:, :, 3] > 0
    dst[op] = src[op]
    return int(op.sum())


def element_sans_repli(bande, e):
    d, aire = E.decor_et_aire(bande)
    t = AN.u32(AN.SCRIPTS + (d * 3 + aire) * 4)
    g = AN.u16(AN.u32(t + e["script"] * 4) + 6)
    nom = asset_du_script(g)
    a, tuiles = P.asset(nom)
    offs = sorted({r[4] for r in a["anims"]})
    rec = a["anims"][g - a["index_global"][0]]
    sp = a["sprites"][offs.index(rec[4])]
    base = base_de_palette(bande)
    rgba, x0, y0 = A.poser_couleur(sp, tuiles, P.banque_des_palettes(), base,
                                   lambda _dr, off: base + off)
    return rgba, e["x"] + rec[1] + x0, P.SOL_REPERE - e["y"] + rec[2] + y0


def variante_elena():
    """{liste: toile} des quatre plans de l'etage 56."""
    listes = {}
    fond = couches2i.demi_banque("bg08", 0, "haut")
    brute = couches2i.demi_banque("bg08", 0, "bas")          # la reserve, lignes 0..511
    # entree 6 : 16 lignes en 416 <- reserve 512 ; entree 7 : 64 lignes en 432 <- 576
    fond[512 + 416:512 + 432, 256:768] = brute[512 + 0:512 + 16, 256:768]
    fond[512 + 432:512 + 496, 256:768] = brute[512 + 64:512 + 128, 256:768]
    listes[132] = fond

    proche = np.zeros((1024, 1024, 4), np.uint8)
    tiers = np.zeros((1024, 1024, 4), np.uint8)
    devant = np.zeros((1024, 1024, 4), np.uint8)
    els = elements_second_jeu(VARIANTE_BANDE)
    # du plus loin au plus pres ; a egalite, le dernier enregistrement d'abord (2I insere
    # en tete de seau, donc le dernier demande est dessine le premier)
    for e in sorted(els, key=lambda e: (-e["profondeur"], -e["rang"])):
        rgba, x, y = element_sans_repli(VARIANTE_BANDE, e)
        cible = tiers if e["plan"] == 3 else (devant if e["profondeur"] < 28 else proche)
        n = poser_sans_repli(cible, rgba, x, y)
        print("      plan %d  %4d,%-4d profondeur %3d script %2d -> %d,%d  %d px visibles"
              % (e["plan"], e["x"], e["y"], e["profondeur"], e["script"], x, y, n))
    # le pont (76) passe devant les falaises (78)
    a, tuiles = P.asset(PONT["asset"])
    base = base_de_palette(VARIANTE_BANDE)
    offs = sorted({r[4] for r in a["anims"]})
    rec = next(r for r in a["anims"] if offs.index(r[4]) == PONT["sprite"])
    rgba, x0, y0 = A.poser_couleur(a["sprites"][PONT["sprite"]], tuiles,
                                   P.banque_des_palettes(), base, lambda _d, off: base + off)
    bx, by = PONT["x"] + rec[1] + x0, P.SOL_REPERE - PONT["y"] + rec[2] + y0
    n = poser_sans_repli(proche, rgba, bx, by)
    print("      pont  768x48 -> %d,%d  %d px" % (bx, by, n))
    listes[196], listes[260], listes[324] = proche, tiers, devant
    return listes


# LES PAGES PROCHES D'ORO ET DE NECRO, REFAITES DEPUIS LA BANQUE -- 16/09/2026.
#
# Elles portaient des cuissons d'anciennes passes que plus rien ne reproduit, et `poser2i`
# ne les efface pas : il repart de la page en place. Frederic les voyait en double :
#
#   Oro    un chien couche, l'edifice de pierre et les chatons, peints dans la page -- «
#          2 chiens » ; aucun n'est un element du code (jeu 1 vide, jeu 2 = une touffe).
#   Necro  la dame en blouse, le calmar et la pieuvre SUR leurs bocaux, les chaines de
#          gauche : « superposition de la copie de la dame ». La dame et les bocaux sont des
#          objets ; les chaines sont un element de priorite 2, devant les combattants,
#          desormais pose en objet par `animer2i`.
#
# La page repart donc de `poser2i.banque_nue` (la demi-banque basse, sol cale), et ne recoit
# que les elements que le code pose et qui restent au plan proche (priorite >= 28, derriere
# les combattants) : pour Necro les trois du jeu 1 (75, 75, 76), pour Oro la touffe du jeu 2.
# SEAN ET NECRO : PLUS RIEN N'EST PEINT, TOUT EST POSE -- 16/09/2026.
#
# Frederic : « le conducteur et le personnage a genou sont doubles ». Leurs pages portaient
# DEJA ces figures, cuites par une ancienne passe de `poser2i`, et `animer2i` les pose
# maintenant en objets : on les voyait deux fois, a seize pixels l'une de l'autre -- la
# cuisson au calage d'avant, l'objet au calage recale (`poser2i.sol`).
#
# Un element du code se POSE, il ne se peint pas. C'est ce que fait 2I, c'est ce qui lui
# rend sa profondeur (75, devant la couche a 84), et c'est ce qui evite qu'une passe laisse
# derriere elle un dessin que la suivante ne sait plus effacer. Les deux etages repartent
# donc de la banque nue, sans rien y ajouter.
REFAITES = [
    # (etage, bg, bande, elements a peindre : "jeu1" / "jeu2")
    (31, "bg0a", 10, ("jeu2",)),
    (27, "bg05", 5, ()),
    (34, "bg0d", 13, ()),
    # YANG -- 16/09/2026 : ses cinq elements et le monsieur en vert etaient cuits dans la
    # page, le monsieur en vert brouille. Tout est pose en objet par `animer2i`.
    (32, "bg0b", 11, ()),
]


def page_refaite(bg, bande, jeux):
    toile = P.banque_nue(bg).copy()
    els = []
    if "jeu1" in jeux:
        els += [("jeu1", e) for e in E.elements_statiques(bande)]
    if "jeu2" in jeux:
        els += [("jeu2", e) for e in elements_second_jeu(bande)]
    for jeu, e in sorted(els, key=lambda t: (-t[1]["profondeur"], -t[1]["rang"])):
        if e["profondeur"] < 28 or e["plan"] != 2:
            print("      %s %d,%d profondeur %d : pas au plan proche, laisse aux objets"
                  % (jeu, e["x"], e["y"], e["profondeur"]))
            continue
        rgba, x, y = element_sans_repli(bande, e)
        n = poser_sans_repli(toile, rgba, x, y)
        print("      %s script %d  %d,%d (profondeur %d) -> banque %d,%d  %d px"
              % (jeu, e["script"], e["x"], e["y"], e["profondeur"], x, y, n))
    return toile


# IBUKI : SES TROIS PAGES SONT COMPOSEES PAR LE DESCRIPTEUR DE 2I -- 16/09/2026.
#
# Sa banque n'est pas sa scene : c'est un atlas, que le moteur de decor pose rectangle par
# rectangle (`descripteurs2i.py`). Montee telle quelle, elle donnait deux cascades cote a
# cote, la cascade 80 lignes trop bas, et le temple dans le ciel au lieu du plan du milieu.
#
#   liste 132 (le fond, couche 2)   le ciel, banque 1 (384..1023), en x 192
#   liste 260 (le milieu, couche 0) la montagne et le temple (banque 1, 0..367) en x 496,
#                                   puis les six vues de la cascade empilees en 224,688
#   liste 196 (le proche, couche 1) la banque 0 bas a l'identite, et la seconde cabane
#                                   (banque 0 haut, 832..1023) par-dessus, en x 64
IBUKI_LISTES = {132: 2, 260: 0, 196: 1}


def ibuki():
    import descripteurs2i as D
    base = D.lire(D.IBUKI["base"])
    return {liste: D.composer("bg07", base, couche) for liste, couche in IBUKI_LISTES.items()}


def main():
    ecrire = "--ecrire" in sys.argv
    if "--ibuki" in sys.argv:
        sortie = os.path.join(RACINE, "etages2i-sprites", "stage29")
        print("etage 29  bg07 : les pages du descripteur")
        for liste, toile in sorted(ibuki().items()):
            en_place = P.lire_liste(sortie, liste)
            d = np.any(toile[512:] != en_place[512:], axis=2).sum() if en_place is not None else -1
            print("   liste %d : %d px, %d changent" % (liste, int((toile[:, :, 3] > 0).sum()), d))
            if ecrire:
                couches2i_ecrire(sortie, toile, liste)
        return
    if "--refaire" in sys.argv:
        for etage, bg, bande, jeux in REFAITES:
            sortie = os.path.join(RACINE, "etages2i-sprites", "stage%d" % etage)
            print("etage %d  %s  bande %d : page proche refaite" % (etage, bg, bande))
            toile = page_refaite(bg, bande, jeux)
            en_place = P.lire_liste(sortie, 196)
            d = np.any(toile[512:] != en_place[512:], axis=2).sum()
            print("      %d px changent par rapport a la page en place" % d)
            if ecrire:
                couches2i_ecrire(sortie, toile, 196)
        return
    if "--variante" in sys.argv:
        sortie = os.path.join(RACINE, "etages2i-sprites", "stage%d" % VARIANTE_ETAGE)
        print("etage %d  bg08  bande %d" % (VARIANTE_ETAGE, VARIANTE_BANDE))
        for liste, toile in sorted(variante_elena().items()):
            print("   liste %d : %d px" % (liste, int((toile[:, :, 3] > 0).sum())))
            if ecrire:
                couches2i_ecrire(sortie, toile, liste)
        return
    for etage, bg, bande, listes in PLANS:
        sortie = os.path.join(RACINE, "etages2i-sprites", "stage%d" % etage)
        print("etage %d  %s  bande %d" % (etage, bg, bande))
        for plan, liste in sorted(listes.items()):
            toile = plan_statique(bande, plan)
            en_place = P.lire_liste(sortie, liste)
            mien = toile[:, :, 3] > 0
            if etage != 30 and en_place is not None:
                # controle : ce que la page en place porte deja, la ou on peindrait
                eg = (np.abs(toile[:, :, :3].astype(int) - en_place[:, :, :3].astype(int)).sum(2) == 0)
                print("      liste %d : %d px peints, dont %d identiques a la page en place"
                      % (liste, mien.sum(), (eg & mien & (en_place[:, :, 3] > 0)).sum()))
            if etage == 30 and ecrire:
                couches2i_ecrire(sortie, toile, liste)
        if etage == 30 and ecrire:
            couches2i_ecrire(sortie, elena_lointain(), 132)
            couches2i_ecrire(sortie, elena_proche(), 196)
    if not ecrire:
        print("\nRien n'a ete ecrit. `--ecrire` pour les listes 132, 196 et 260 de l'etage 30.")


def couches2i_ecrire(sortie, plan, liste):
    """Les 32 pages, au dossier de travail ET a la source que le lanceur deploie."""
    dossiers = [sortie, os.path.join(DEPLOIEMENT, os.path.basename(sortie))]
    for d in dossiers:
        os.makedirs(d, exist_ok=True)
        for i in range(32):
            px, py = (i & 7) * 128, 512 + (i >> 3) * 128
            bande3sx.ecrire_tex(os.path.join(d, "%d-%d.tex" % (liste, liste + i)),
                                plan[py:py + 128, px:px + 128])
    print("      liste %d ecrite (%s)" % (liste, ", ".join(dossiers)))


if __name__ == "__main__":
    main()
