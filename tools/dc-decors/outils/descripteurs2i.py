# -*- coding: utf-8 -*-
"""Les DESCRIPTEURS DE SCENE de 2I : ce que le Dreamcast dessine, couche par couche.

LU DANS LE CODE -- 16/09/2026. Frederic, sur Ibuki : « la cascade de gauche est animee mais
beaucoup trop basse, la cascade de droite est en trop, un temple a droite en arriere-plan
manquant ».

2I emule les couches de la CPS3 (registres en `0x8C7EFCEC`, seize octets par couche), mais
ne dessine PAS leurs cases. Le moteur de decor (`0x8C0F8D94`, entree 0 a 22 de la table
`0x8C60A0B0`) choisit, selon le decor, une LISTE DE RECTANGLES et la passe a `0x8C0F8AE0`,
qui dessine chacun sur l'ecran :

    enregistrement de 40 octets, dix entiers :
        +0  couche (le registre 0..3 ; -1 termine la liste)
        +4  x dans la scene      +8  largeur
        +12 y dans la scene      +16 hauteur
        +20 texture (la banque 0 ou 1 du .pvc)
        +24 u   +28 v            (le coin dans la banque)
        +32, +36 des drapeaux

    ecran x = x - ((defilement x + 1) & 0x3FF), ecran y = y - ((defilement y + 20) & 0x3FF),
    et chaque rectangle est redessine decale de 1024 en x et en y : la scene boucle.

La scene fait donc 1024 x 1024, et la BANQUE N'EST QU'UN ATLAS. Pour douze decors le
descripteur est l'identite -- `0x8C603888` (deux couches) ou `0x8C603900` (trois) :

    (couche 0, x 0, 1024, y 512, 512, banque 0, u 0, v 0)     la banque 0 haut
    (couche 1, x 0, 1024, y 512, 512, banque 0, u 0, v 512)   la banque 0 bas
    (couche 2, x 0, 1024, y 512, 512, banque 1, u 0, v 0)     la banque 1 haut

C'est exactement la convention du port (la moitie haute sur les lignes 512 a 1023 de la
page), ce qui explique qu'elle marche partout ou le descripteur est l'identite. Cinq decors
en ont un propre : Hugo (6), IBUKI (7), les deux Elena (8, 9) et Akuma (15).

Les ANIMATIONS DE PAGES ne changent, chez 2I, que le numero de page d'un emplacement
(`0x8C71866C` + 4k) ; le moteur de decor s'en sert pour choisir un descripteur de plus, dessine
par-dessus la base. Chez Ibuki : page 69, 73..77 -> une des six vues de la cascade ; page 64
ou 71 -> une des deux versions de la cabane (les lanternes).

    python descripteurs2i.py            # les listes d'Ibuki
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import sh4

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)

# La table de sauts du moteur de decor : 18 decalages de seize bits, comptes depuis
# 0x8C0F8DBC. Elle sert de controle : les adresses ci-dessous sont celles que ses cas chargent.
SAUTS, ORIGINE_SAUTS = 0x8C0F8DC8, 0x8C0F8DBC
IDENTITE_DEUX, IDENTITE_TROIS = 0x8C603888, 0x8C603900

# IBUKI (cas 7, `0x8C0F8DFC`) : la base, puis la vue de la cascade de la page courante
# (69, 73, 74, 75, 76, 77, dans cet ordre), puis la cabane (64 ou 71).
IBUKI = dict(
    base=0x8C60495C,
    cascade={69: 0x8C604B3C, 73: 0x8C604B8C, 74: 0x8C604BDC,
             75: 0x8C604C2C, 76: 0x8C604C7C, 77: 0x8C604CCC},
    cabane={64: 0x8C604D1C, 71: 0x8C604D6C},
)

# LES DEUX ELENA -- 28/09/2026. Ce fichier annonce depuis le 16/09 que les decors 8 et 9 ont
# un descripteur propre ; seul Ibuki avait ete fait. Leurs cas sont desassembles et lus.
#
# CAS 9 (`0x8C0F8EB8`), LA CHUTE -- la bande 9, notre etage 30 :
#
#     mov.l  0x8C0F8F84,r4 ; bsr 0x8C0F8AE0      la base
#     mov.l  @r14,r13 ; add #-80,r13             emplacement 0 : page - 80
#     cmp/pz ... cmp/ge #12 ... mov #0,r13       borne a 0..11, sinon 0
#     mov.l  0x8C0F8F88,r0 ; mov.l @(r0,r4),r4   TABLE de douze descripteurs
#     mov.l  @(4,r14),r14 ; ... cmp/ge #2 ...    emplacement 1 : borne a 0..1
#     mov.l  0x8C0F8F8C,r0 ; mov.l @(r0,r4),r4   TABLE de deux descripteurs
#
# et la base tient en quatre rectangles :
#
#     couche 0  scene  128,512   768x352  <- banque 0    0,0     le ciel, la falaise
#     couche 0  scene  128,864   256x160  <- banque 0    0,352   le bas a gauche du trou
#     couche 0  scene  704,864   192x160  <- banque 0  576,352   le bas a droite du trou
#     couche 1  scene  128,576   768x384  <- banque 0    0,576   le plan proche
#
# TROIS CHOSES QUE LA DEMI-BANQUE NUE NE POUVAIT PAS DONNER :
#
#   * LA SCENE FAIT 768 DE LARGE, POSEE EN 128. On montait la banque entiere puis on la
#     faisait tourner de 128 (`statiques2i.DECALAGE_ELENA`) : le decalage etait le bon, mais
#     la rotation ramenait les colonnes 896..1023 de la banque sur la scene 0..127 -- et ces
#     colonnes-la ne sont pas du decor, ce sont les TROIS TRAMES TOURNEES de la cascade
#     (`animer2i.PAGES_ANIMEES["bg08"]`, trames 9 a 11, x 864). D'ou le morceau de cascade
#     colle au bord gauche de la page, et les 96 colonnes vides laissees au milieu.
#   * LE PLAN PROCHE COMMENCE EN 576, PAS EN 512. Les lignes 512 a 575 de la banque sont la
#     reserve du bord de l'eau : montees en couche, elles posaient une bande de 768x64 d'eau
#     en haut du plan proche.
#   * LE BAS DU PLAN PROCHE EST UNE ANIMATION. La scene 128,960 (768x64) prend la banque en
#     v 512 ou v 960 selon l'emplacement 1 ; on y montait v 960 en dur, c'est-a-dire l'etat
#     que 2I ne montre qu'une fois sur deux.
#
# CAS 8 (`0x8C0F8E5A`), LE PONT -- la bande 8, notre etage 56. Meme forme, sans table :
# quatre pages testees une a une pour chaque emplacement (73/77/78/79 et 75/80/81/82).
# SES PAGES NE SONT PAS REFAITES : Frederic les a validees le 27/09 (« les cordes du ponton
# sont completes »), et le descripteur confirme ce que `statiques2i.variante_elena` fait
# deja -- base en 256,512 (512x416), la bande de 16 en 928 et celle de 64 en 944.
ELENA_CHUTE = dict(
    base=0x8C6050B4,
    table_cascade=0x8C60553C,      # douze descripteurs, pages 80..91
    table_eau=0x8C60560C,          # deux descripteurs, le bord de l'eau
)

ELENA_PONT = dict(
    base=0x8C604DBC,
    lac_haut={73: 0x8C604E34, 77: 0x8C604E84, 78: 0x8C604ED4, 79: 0x8C604F24},
    lac_bas={75: 0x8C604F74, 80: 0x8C604FC4, 81: 0x8C605014, 82: 0x8C605064},
)


def table(adresse, n):
    """Les `n` descripteurs d'une table de pointeurs (`mov.l @(r0,r4),r4`)."""
    return [struct.unpack_from("<I", sh4.D, sh4.a2o(adresse + k * 4))[0] for k in range(n)]


def lire(adresse):
    """Les rectangles d'un descripteur, dans l'ordre ou le moteur les dessine."""
    out = []
    while True:
        r = struct.unpack_from("<10i", sh4.D, sh4.a2o(adresse))
        if r[0] < 0:
            return out
        out.append(dict(couche=r[0], x=r[1], larg=r[2], y=r[3], haut=r[4],
                        texture=r[5], u=r[6], v=r[7], drapeaux=(r[8], r[9])))
        adresse += 40


_BANQUES = {}


def banque(decor, n):
    """La banque `n` du .pvc, en 1024 x 1024 RGBA."""
    if (decor, n) not in _BANQUES:
        import bande3sx
        import pvc
        from rendupvc import carte_morton, SIDE
        src = os.path.join(RACINE, "pvc-2i", decor + ".pvc")
        pages, _u, _s = pvc.decode(open(src, "rb").read())
        _BANQUES[decor, n] = bande3sx.banque_rgba(pages, n * 4096, carte_morton(SIDE))[0]
    return _BANQUES[decor, n]


def poser(toile, rgba, x, y):
    """Pose `rgba` en (x, y), par-dessus, en bouclant sur 1024 comme le moteur."""
    h, w = rgba.shape[:2]
    op = rgba[:, :, 3] > 0
    ys = (np.arange(h) + y) % 1024
    xs = (np.arange(w) + x) % 1024
    zone = toile[np.ix_(ys, xs)]
    zone[op] = rgba[op]
    toile[np.ix_(ys, xs)] = zone


def composer(decor, rectangles, couche, toile=None):
    """La page 1024 x 1024 d'une couche : ses rectangles poses dans la scene, dans l'ordre."""
    if toile is None:
        toile = np.zeros((1024, 1024, 4), np.uint8)
    for r in rectangles:
        if r["couche"] != couche:
            continue
        b = banque(decor, r["texture"])
        poser(toile, b[r["v"]:r["v"] + r["haut"], r["u"]:r["u"] + r["larg"]], r["x"], r["y"])
    return toile


def controle():
    """Les cas du moteur de decor, et le descripteur d'identite qu'ils chargent."""
    decalages = struct.unpack_from("<18H", sh4.D, sh4.a2o(SAUTS))
    return {n: ORIGINE_SAUTS + d for n, d in enumerate(decalages)}


def main():
    cas = controle()
    print("cas 7 (Ibuki) -> %08X" % cas[7])
    base = lire(IBUKI["base"])
    for r in base:
        print("   couche %d  scene %4d,%4d  %4dx%-4d <- banque %d  %4d,%4d"
              % (r["couche"], r["x"], r["y"], r["larg"], r["haut"], r["texture"], r["u"], r["v"]))
    for page, a in sorted(IBUKI["cascade"].items()):
        r = lire(a)[0]
        print("   page %d : la vue %d,%d en %d,%d" % (page, r["u"], r["v"], r["x"], r["y"]))
    for page, a in sorted(IBUKI["cabane"].items()):
        r = lire(a)[0]
        print("   page %d : banque %d %d,%d en %d,%d" % (page, r["texture"], r["u"], r["v"], r["x"], r["y"]))


if __name__ == "__main__":
    main()
