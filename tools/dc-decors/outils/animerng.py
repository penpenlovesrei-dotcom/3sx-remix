# -*- coding: utf-8 -*-
"""Les objets animes des decors de New Generation, cuits comme ceux de 2nd Impact.

La chaine est la MEME qu'en 2I -- le format `F_ETC` est partage, `fetc.py` le dit
lui-meme : son parcours tombe juste sur les trente-sept assets des deux jeux. Ce qui
change tient en quatre points :

    binaire            SF3_1ST.BIN
    table de scripts   u32 [0x8C4CC1F0 + (decor*3 + aire)*4]   (dans ng_blocs.json)
    banque de couleurs 0x8C1B8188, base RAM 0x027B0000          (2I : 0x8C1E9AEC)
    bases de palette   par BANDE, table 0x8C18AC10 -> 0x8C1AAB7C

L'APPARIEMENT DECOR -> ASSET NE SE DEVINE PAS, IL SE MESURE. Les seize `.pk` de New
Generation ne sont pas numerotes comme les bandes. `annuaireng.py` resout tous les scripts
d'un decor et regarde dans quelle plage d'index global ils tombent : sept decors sur
quatorze designent un asset unique avec 100 % de leurs scripts, et les paires Ryu/Ken et
Yun/Yang y ressortent une troisieme fois -- apres les noms de bandes et apres les
sequences de blocs.

    python animerng.py             # dit ce qu'il ferait
    python animerng.py --ecrire    # ajoute les fiches a decor_objets_data.c
"""

import io
import json
import os
import re
import struct
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
sys.path.insert(0, ICI)

import numpy as np

import animations as AN0
import annuaireng as ANG
import assemblage as A
import fetc
import pagesng as PG

BIN = open(os.path.join(RACINE, "SF3_1ST.BIN"), "rb").read()
BASE = 0x8C010000
POFF = 0x1A8188          # la banque de couleurs de NG, en offset fichier
SOL = 1023
PREMIER_ETAGE = 37

# Les bases de palette par bande, lues dans la table de transferts 0x8C1AAB7C
# (entrees 52 a 68, le meme intervalle qu'en 2nd Impact). Le second jeu, destination
# 0x12000, suit immediatement le premier : base2 = base1 + nb1.
BASES = {
    0: (0, 25), 1: (112, 28), 2: (168, 24), 3: (216, 35), 4: (286, 26),
    5: (338, 21), 6: (380, 16), 7: (412, 25), 8: (462, 24), 9: (510, 25),
    10: (572, 36), 11: (712, 17), 12: (644, 17), 13: (678, 17), 14: (746, 23),
    15: (792, 32), 16: (856, 24),
}
# Les bandes 17 et 18 partagent l'index de palette des bandes 5 et 6.
BASES[17] = BASES[5]
BASES[18] = BASES[6]

# QUELLE BANQUE POUR QUELS OFFSETS — l'equivalent NG de `BANQUES_2I` — 05/09/2026
# ==============================================================================
# Une bande charge DEUX jeux de palettes : le premier en destination 0x2000 (entrees
# 52..68 de la table `0x8C1AAB7C`) et le second en 0x12000 (entrees 69..85), dont la base
# suit exactement le premier -- base2 = base1 + nb1, verifie sur les dix-sept bandes.
#
# `BASES` ci-dessus donne le PREMIER jeu, et c'est ce qu'on employait partout. Frederic a
# signale des couleurs fausses sur `ng05` : **515 pixels verts**, dont 474 sur un seul
# objet. Le detecteur de `banquesng.py` -- vert pur `0x03E0`, INDEX 0 EXCLU -- tranche :
#
# DEUX PREMISSES FAUSSES ONT ETE CORRIGEES POUR ARRIVER ICI, ET LES DEUX MERITENT
# D'ETRE ECRITES parce que chacune avait produit une conclusion nette et fausse.
#
# 1. LE DETECTEUR CHERCHAIT UNE VALEUR, PAS UN CANAL. Il testait `== 0x03E0`, alors que
#    l'objet `n05o19` tombe sur `0x0280` -- vert lui aussi (g = 160 au lieu de 248), mais
#    d'une autre valeur. Il annoncait donc « zero vert » avec 474 pixels verts a l'ecran.
#    Une case jamais ecrite se reconnait a ses CANAUX : rouge et bleu nuls, vert non nul.
#    Corrige, il rendait 16 272 verts des DEUX cotes -- ni le premier jeu ni le second.
#
# 2. LE BALAYAGE DE LA TABLE S'ARRETAIT A LA PREMIERE ENTREE INVALIDE. La table en compte
#    147 valides jusqu'a l'index 148, avec des trous ; en s'arretant au premier trou je
#    n'en voyais que 86, et j'ai conclu qu'AUCUN transfert n'avait la destination
#    contigue de la bande 5. Il y en a un, et un seul.
#
# CE QUI EST ETABLI, PAR LES TROIS CRITERES DE 2I, TOUS CONCORDANTS :
#
#     la DESTINATION    0x2A80 = 0x2000 + 21*128, la suite immediate du premier jeu.
#                       UNE SEULE entree de la table y ecrit : l'index 106, base 1397.
#     le DETECTEUR      offsets 0..8 : 14 713 pixels verts avec le premier jeu (et
#                       autant avec le second), **ZERO** avec la base 1397. Sur les
#                       sept offsets peints du groupe, aucun n'y resiste.
#     le NOMBRE         nb = 9 borne exactement le groupe qu'il sert, 0..8.
#
# La bande 5 est la SEULE des dix-neuf dans ce cas : partout ailleurs le premier jeu est
# deja propre, ou l'entree qui tombe sur la destination contigue est sale -- elle sert une
# autre bande, la coincidence de destination ne suffit pas. **Le detecteur elimine, il ne
# choisit pas** : rien n'est touche la ou il est muet des deux cotes.
#
# RESTE, ET C'EST DIT : les offsets 9..15 de la bande 5 gardent 1 559 pixels verts, et la
# bande 17 en a 64 476 sur son groupe haut (aucun de ses objets n'est pose aujourd'hui).
#
#     bande : [(offset min, offset max, base)]
BANQUES_NG = {5: [(0, 8, 1397)]}


def u8(a):
    return BIN[a - BASE]


def u16(a):
    return struct.unpack_from("<H", BIN, a - BASE)[0]


def u32(a):
    return struct.unpack_from("<I", BIN, a - BASE)[0]


def script_images(table, sc):
    """[(index global, duree)] d'un script, dans l'ordre. Meme format qu'en 2I.

    LA REGLE EST LA DUREE, PAS LE PREMIER OCTET -- CORRIGE LE 23/09/2026.

    L'interprete (2I `0x8C0B50DC`) compare le PREMIER MOT de l'enregistrement a 256.
    Ce mot vaut `premier octet | duree << 8` : des que la duree n'est pas nulle il
    depasse 256, et l'enregistrement est une IMAGE quel que soit son premier octet --
    celui-ci n'est qu'un drapeau, recopie dans la fiche en `+468` pour la routine.
    Ne garder que `cmd == 0` perdait **88 images en 2nd Impact et 67 en New
    Generation** : tous les drapeaux 2, 3 a 9 et 0xFF.
    """
    if not ANG.dedans(table):
        return []

    p = u32(table + sc * 4)

    if not ANG.dedans(p):
        return []

    out = []

    for k in range(96):
        if not ANG.dedans(p + k * 8 + 7):
            break

        cmd, duree, idx = u8(p + k * 8), u8(p + k * 8 + 1), u16(p + k * 8 + 6)

        if duree:
            out.append((idx, duree))
            continue

        if cmd == 0x01:
            break

    return out


# LA COMMANDE 0x29 EST UN DEPLACEMENT -- LUE LE 28/09/2026
# ---------------------------------------------------------
# Frederic : « DUDLEY, dans le variant de jour, le punk de gauche marche vers l'arriere puis
# fait un saut vers l'avant ». Son script (le 17 de la bande 8, le punk au skate, id 68)
# porte DOUZE enregistrements de duree nulle que `script_images` traverse sans rien en
# faire, et qui ne sont pas des images :
#
#     8C0D62D0  29 00 00 00 00 04 00 00      8C0D6368  29 00 00 00 00 F4 00 00
#
# Son gestionnaire est l'entree 0x29 de la table des commandes (`0x8C1C5BC8` en 2I),
# `0x8C0B5A64`, et il se lit entierement :
#
#     mov.w @(2,r5),r0     le mot +2 choisit l'AXE : 0 -> x, 2 -> y
#     mov.b @(10,r4),r0    l'octet +10 de l'objet est son MIROIR
#     mov.w @(4,r5),r0     le mot +4, SIGNE, est le pas
#     shll8 r0 ; add/sub   u32[objet + 100] += pas << 8   (soustrait si l'objet est mirroite)
#
# `u32[+100]` est le x en 16.16 (son entier est `[+102]`, ce que `objetsng` a lu sur Alex),
# donc `pas << 8` vaut `pas / 256` PIXELS. Les trois valeurs du punk se lisent alors :
# 0x0400 = +4 px, 0x0800 = +8 px, 0xF400 = **-12 px**.
#
# Somme sur son script : +48 sur les huit premieres commandes, -48 sur les quatre dernieres.
# Le punk roule en avant puis revient, et il retombe EXACTEMENT sur sa place. On ne jouait
# ni l'un ni l'autre : restaient les images, dont les quatre dernieres (21340..21343) sont
# dessinees pour un corps qui a recule de 48 pixels. D'ou le saut.
#
# ON NE LE POSE QUE SI LA SOMME EST NULLE. Le contrat de `trajet` (voir `decor_objets.c`)
# est que « la liste boucle sur son premier segment, ou l'objet retrouve sa position de
# naissance ». Un script dont la somme n'est pas nulle derive a chaque tour : sa routine
# d'origine doit le replacer, et on ne sait pas encore ou. C'est le cas du script 11 de
# SEAN (bande 2, x 704), +92 pixels par tour -- laisse tel quel, a reprendre.
def deplacements_du_script(table, sc):
    """[(duree, dx, dy)] : chaque image du script, et le deplacement qui la precede.

    `dx` et `dy` sont en 1/256 de pixel, l'unite meme du champ du script et celle de
    `trajet` dans `decor_objets.c`."""
    if not ANG.dedans(table):
        return []

    p = u32(table + sc * 4)

    if not ANG.dedans(p):
        return []

    segs, dx, dy = [], 0, 0

    for k in range(96):
        a = p + k * 8

        if not ANG.dedans(a + 7):
            break

        cmd, duree = u8(a), u8(a + 1)

        if duree:
            segs.append((duree, dx, dy))
            dx = dy = 0
            continue

        if cmd == 0x01:
            break

        if cmd == 0x29:
            axe = u16(a + 2)
            pas = u16(a + 4)
            pas = pas - 0x10000 if pas & 0x8000 else pas

            if axe == 0:
                dx += pas
            elif axe == 2:
                dy += pas

    return segs


def trajet_du_script(table, sc):
    """Le `trajet` que les commandes 0x29 d'un script decrivent, ou None.

    Un segment par image : `{ duree, vx, vy, -1, 0 }`, vx et vy en 1/256 de pixel PAR
    TRAME. Le reste de la division est reporte sur le segment suivant, pour que la somme
    des segments soit exactement celle du script."""
    segs = deplacements_du_script(table, sc)

    if not segs:
        return None

    if sum(s[1] for s in segs) or sum(s[2] for s in segs):
        return None                      # le trajet ne revient pas : voir le commentaire

    if not any(s[1] or s[2] for s in segs):
        return None                      # aucun deplacement : rien a poser

    out, rx, ry = [], 0, 0

    for duree, dx, dy in segs:
        rx += dx
        ry += dy
        vx, vy = int(rx / duree), int(ry / duree)
        rx -= vx * duree
        ry -= vy * duree
        out.append((duree, vx, vy, -1, 0))

    return out


# UN SCRIPT NE REBOUCLE PAS TOUJOURS A SON DEBUT -- 28/09/2026
# --------------------------------------------------------------
# Frederic, sur Oro : « l'animation d'un chaton tourne en boucle alors que ses premieres
# phases d'animation ne doivent etre realisees qu'une seule fois ».
#
# Un script se termine par une commande, et il y en a deux :
#
#     0x01   reprend a l'enregistrement 0         tout le script reboucle
#     0x02   reprend a l'enregistrement mot3 - 2  ce qui precede ne passe qu'UNE fois
#
# Le `0x02` etait deja lu le 23/09 pour la statue de Yang (`animer2i.script_deroule` :
# « index = pas x (mot3 - 2) », gestionnaire `0x8C0B530C`), mais traite comme un `0x01` --
# « il boucle : on le traite comme un 0x01 ». Il boucle, oui, mais PAS AU MEME ENDROIT.
#
# Le chaton d'Oro (script 17, vingt-cinq images) finit sur `0x02` avec mot3 = 0x000E : le
# Dreamcast rejoue a partir de l'enregistrement 12, donc ses douze premieres images -- la
# pose de 103 trames, les baillements -- ne passent qu'une fois. Trois objets de NG sont
# dans ce cas : lui, et un objet de Yun 1 et de Yang 1 (script 24, 2 images sur 7).
def depart_de_boucle(table, sc):
    """L'IMAGE ou la boucle du script reprend. Zero quand tout le script reboucle."""
    if not ANG.dedans(table):
        return 0

    p = u32(table + sc * 4)

    if not ANG.dedans(p):
        return 0

    for k in range(96):
        a = p + k * 8

        if not ANG.dedans(a + 7):
            return 0

        cmd, duree = u8(a), u8(a + 1)

        if duree:
            continue

        if cmd == 0x01:
            return 0

        if cmd == 0x02:
            cible = u16(a + 6) - 2
            return sum(1 for j in range(max(0, cible)) if u8(p + j * 8 + 1))

    return 0


def script_deroule(table, sc, fin="une"):
    """[(index global, duree)] d'un script TEL QU'IL SE JOUE -- `animer2i.script_deroule`.

    Une duree non nulle est une image (bit 0 du premier octet : la FIN) ; une duree nulle
    une commande : `0x01` relance, `0x0C`/`0x0D` bouclent. `fin` dit ce que devient l'image
    marquee : `"une"` (une trame), `"sans"` (jamais vue), `"boucle"` (son temps, puis on
    relance)."""
    p = u32(table + sc * 4)
    out, k, boucle, boucle2 = [], 0, None, None
    for _garde in range(1024):
        drap, duree, idx = u8(p + k * 8), u8(p + k * 8 + 1), u16(p + k * 8 + 6)
        if duree:
            if drap & 1 and fin != "boucle":
                if fin == "une":
                    out.append((idx, 1))
                return out
            out.append((idx, duree))
            k += 1
        elif drap == 0x01:
            return out
        elif drap == 0x0C:
            boucle = [k + 1, idx]
            k += 1
        elif drap == 0x0D:
            boucle[1] -= 1
            k = boucle[0] if boucle[1] > 0 else k + 1
        elif drap in (0x0E, 0x0F):
            # LA SECONDE BOUCLE (`0x8C0B5576` / `0x8C0B55E8`), compteur `+194` : la meme
            # paire que 0x0C/0x0D, imbriquee. Lue le 23/09/2026.
            if drap == 0x0E:
                boucle2 = [k + 1, idx]
                k += 1
            else:
                boucle2[1] -= 1
                k = boucle2[0] if boucle2[1] > 0 else k + 1
        elif drap == 0x32:
            # UN SAUT RELATIF EN ARRIERE (`0x8C0B5C62`) : `index -= pas * (mot3 + 1)`,
            # le pas valant deux mots. On recule donc de `idx + 1` enregistrements.
            k -= idx + 1
            if k < 0:
                raise ValueError("script %d : saut 0x32 avant le debut" % sc)
        elif drap in (0x28, 0x29, 0x2A, 0x2B):
            # DEPLACER EN X ET/OU EN Y (0x28, 0x29, 0x2A) et APPELER UN EFFET (0x2B).
            # Ils ne changent pas l'image : on les passe. Le deplacement, lui, se porte
            # par `trajet` -- voir TRAJET dans `decor_objets.c`.
            k += 1
        else:
            raise ValueError("script %d : commande 0x%02X non lue" % (sc, drap))
    raise ValueError("script %d : ne finit pas" % sc)


def plage_du_script(table, sc, debut, fin):
    """Les pas `debut..fin-1` d'un script, AVEC leurs durees.

    Ajoute le 25/09/2026 pour l'oiseau d'Elena 1. Sa routine (`0x8C0A63F0`) decoupe son
    script en phases sur le DRAPEAU du pas courant, qu'elle lit en `[+468]` :

        etat 2  avance jusqu'a voir le drapeau 2 (le pas 16), puis pose [+556] = 79
        etat 3  avance tant que le drapeau est 0, jusqu'au pas 36 (drapeau 1)

    Une suite doit donc pouvoir tenir une PLAGE de pas sans perdre les durees. La forme
    liste (`[(script, pas), ...]`) donne une trame par pas, ce qui n'irait pas : le
    perchoir tient six trames par image et l'envol neuf.

    Les pas de duree nulle sont des COMMANDES (`0x2B` au pas 13 chez l'oiseau) : ils ne
    prennent pas de trame et sont sautes.
    """
    p = u32(table + sc * 4)
    out = []
    for k in range(debut, fin):
        duree, idx = u8(p + k * 8 + 1), u16(p + k * 8 + 6)
        if duree:
            out.append((idx, duree))
    return out


def suites_d_images(table, suites):
    """Les pas d'un objet a comportement -- `animer2i.suites_d_images`."""
    out = []
    for s in suites:
        if isinstance(s, int):
            out.append(script_deroule(table, s))
        elif isinstance(s, tuple) and len(s) == 3:
            out.append(plage_du_script(table, s[0], s[1], s[2]))
        elif isinstance(s, tuple):
            out.append(script_deroule(table, s[0], s[1]))
        else:
            out.append([(u16(u32(table + sc * 4) + r * 8 + 6), 1) for sc, r in s])
    return out


def est_une_boucle(images):
    """Une vraie boucle, ou une POSE BALAYEE (un regard) ? -- `animer2i.est_une_boucle`."""
    ims = [np.where(im["msk"], im["img"], 0) for im in images]
    n = len(ims)
    if n < 4:
        return True
    h = max(i.shape[0] for i in ims)
    w = max(i.shape[1] for i in ims)

    def cadre(a):
        b = np.zeros((h, w), np.uint8)
        b[:a.shape[0], :a.shape[1]] = a
        return b

    ims = [cadre(a) for a in ims]
    ec = [int((ims[k] != ims[0]).sum()) for k in range(n)]
    miroir = all(abs(ec[k] - ec[n - k]) <= max(2, ec[k] * 0.06) for k in range(1, n))
    haut = ec.index(max(ec))
    milieu = abs(haut - n // 2) <= 1
    tranche = max(ec) > 2 * (sorted(ec)[n // 2] or 1)
    return not (miroir and milieu and tranche)


def asset_du_decor(d, sp):
    """L'asset qui contient le plus de scripts du decor, et combien il en couvre."""
    tables = [int(t, 16) for t in d["scripts_animation"]]
    compte = {}

    for aire, sc in ANG.scripts_du_decor(d):
        g = ANG.index_global(tables[aire], sc)

        if g is None:
            continue

        for nom, (a, b) in sp.items():
            if a <= g < b:
                compte[nom] = compte.get(nom, 0) + 1

    if not compte:
        return None, 0

    nom = max(compte, key=lambda n: (compte[n], n))
    return nom, compte[nom]


def palette(bande, champ):
    """Les 64 couleurs ARGB1555 d'un sprite, et le numero employe."""
    base, nb = BASES.get(bande, (None, 0))

    if base is None:
        return None, None

    offset = champ & 0x1FF

    # C'EST L'OFFSET DU MORCEAU QUI CHOISIT LA BANQUE. Voir `BANQUES_NG`.
    for lo, hi, autre in BANQUES_NG.get(bande, ()):
        if lo <= offset <= hi:
            base = autre
            break

    num = base + offset
    pal = np.frombuffer(BIN[POFF + num * 128:POFF + num * 128 + 128], dtype="<u2").copy()
    # L'index 0 est transparent par construction : la banque y met une vraie couleur, et
    # le convertisseur du jeu ecrit zero dedans avant de deplier la tuile. Sans ca chaque
    # sprite sort entoure d'un carre noir opaque.
    pal[0] = 0
    return num, pal


def grille(images):
    """(cols, ligs, ox, oy, ecarts) -- la grille qui contient TOUTES les images.

    Chaque image se pose a l'ecart que son ancre lui donne, l'origine commune etant celle
    de l'image 0 : les caler toutes sur le coin ferait sauter le sprite d'une image a
    l'autre. La lecon est de 2nd Impact, elle vaut ici.
    """
    ref = images[0]
    rx, ry = ref["ancre"][0] + ref["x0"], ref["ancre"][1] + ref["y0"]
    ec = [(im["ancre"][0] + im["x0"] - rx, im["ancre"][1] + im["y0"] - ry)
          for im in images]
    x0, y0 = min(d[0] for d in ec), min(d[1] for d in ec)
    x1 = max(d[0] + im["img"].shape[1] for d, im in zip(ec, images))
    y1 = max(d[1] + im["img"].shape[0] for d, im in zip(ec, images))
    return (x1 - x0 + 15) // 16, (y1 - y0 + 15) // 16, -x0, -y0, ec


_CONTENEURS = None


def conteneurs_du_pk(nom_asset):
    """TOUS les `F_ETC` que le `.pk` de cet asset charge, pas seulement le principal.

    UN ETAGE CHARGE PLUSIEURS CONTENEURS, et l'ignorer coutait **102 enregistrements** sur
    les 445 de New Generation -- mesure du 05/09/2026. `asset_du_decor` rend celui qui
    couvre le PLUS de scripts ; les autres scripts du meme decor tombaient alors « hors de
    son asset » et leur objet etait perdu.

    Ou tombaient-ils vraiment ? Chaque fois dans un autre conteneur du MEME `.pk` :

        decor 2 et 11 (Ryu, Ken)  b03 : F_ETC25 rendu, images dans F_ETC24
        decor 8 (Elena)           b09 : F_ETC31 rendu, images dans F_ETC30
        decor 3 et 10 (Yun, Yang) b04/b0b : F_ETC26 et F_ETC27 se partagent le decor

    La liste vient des tables de l'executable, par `decoupe.py` -- pas d'une supposition.
    Et les vingt et un conteneurs de NG sont tous extraits : il n'y avait rien a sortir du
    disque.
    """
    global _CONTENEURS

    if _CONTENEURS is None:
        import decoupe
        _CONTENEURS = {}

        for pk, parts in decoupe.decouper("ng")[0].items():
            bg = pk.split(".")[0]
            _CONTENEURS[bg] = ["ng-%s-%s" % (bg, p) for p, _s, _c in parts
                               if p.upper().startswith("F_")]

    bg = nom_asset.split("-")[1]
    return [n for n in _CONTENEURS.get(bg, []) if n != nom_asset]


def charger_asset(nom_asset):
    chemin = os.path.join(RACINE, "sprites", nom_asset + ".bin")
    a = fetc.lire(open(chemin, "rb").read())
    conteneurs = [(a, A.charger(chemin)[1], a["index_global"][0],
                   sorted({r[4] for r in a["anims"]}))]
    for nom2 in conteneurs_du_pk(nom_asset):
        c2 = os.path.join(RACINE, "sprites", nom2 + ".bin")
        if os.path.exists(c2):
            a2 = fetc.lire(open(c2, "rb").read())
            conteneurs.append((a2, A.charger(c2)[1], a2["index_global"][0],
                               sorted({r[4] for r in a2["anims"]})))
    return conteneurs


def poser_image(conteneurs, idx):
    """(image posee, enregistrement, sprite) pour un index global, ou None.

    UN ETAGE CHARGE PLUSIEURS CONTENEURS -- voir `conteneurs_du_pk` : l'image est cherchee
    dans chacun, le principal d'abord."""
    for aa, tt, ll, oo in conteneurs:
        if ll <= idx < ll + len(aa["anims"]):
            rec = aa["anims"][idx - ll]
            n = oo.index(rec[4])
            pose = A.poser(aa["sprites"][n], tt)
            if pose is None:
                return None
            poser_image.tuiles = tt
            return pose, rec, aa["sprites"][n], n
    return None


def objets(bande, sp):
    """Les objets animes d'une BANDE de NG -- 16/09/2026.

    La liste vient de `objetsng.enregistrements` : les elements de l'aire, les appels que
    la routine fait VRAIMENT pour elle (`cheminng`), les variantes `z`, les objets a
    valeurs en dur transposes de 2I ; ni debris ni enregistrement d'une autre aire."""
    import objetsng as ON

    enregs, inconnus = ON.enregistrements(bande)
    if not enregs:
        return [], None, inconnus
    dnum, aire = ON.CN.aires_de_bande(bande)[0]
    d = ON.decor(dnum)
    nom_asset, _n = asset_du_decor(d, sp)
    if nom_asset is None:
        return [], None, inconnus
    conteneurs = charger_asset(nom_asset)
    out, vus, rang = [], set(), 0

    for e, source in enregs:
        table = e["table"]
        sc = e.get("script")

        # UN ENREGISTREMENT PORTE DEUX SCRIPTS, REPOS ET ACTION (`0x8C0A0070`, comme
        # `0x8C028792` en 2I) : on joue le plus riche. Ils etaient SAUTES faute de `script`.
        if sc is None and e.get("repos") is not None:
            r, a_ = e.get("repos"), e.get("action")
            sc = r
            if a_ is not None and len(script_images(table, a_)) > len(script_images(table, r)):
                sc = a_
        if sc is None:
            continue

        cle = (sc, e.get("x"), e.get("y"))
        if cle in vus and not e.get("doublon"):
            continue

        suites = pas = bornes = None
        depart = 0
        if e.get("comportement") and e.get("suites"):
            suites = suites_d_images(table, e["suites"])
            trames = [t for s_ in suites for t in s_]
            distinctes = []
            for idx, duree in trames:
                if idx not in [i for i, _ in distinctes]:
                    distinctes.append((idx, duree))
            pas = [([i for i, _ in distinctes].index(idx), duree) for idx, duree in trames]
            bornes = [sum(len(t) for t in suites[:j]) for j in range(len(suites) + 1)]
            trames = distinctes
        elif e.get("deroule"):
            trames = script_deroule(table, sc, "boucle")
        elif e.get("images_brutes"):
            # UN SCRIPT QUE `script_images` NE LIT PAS. Celui de la caleche de Dudley 1
            # (le 10) porte des drapeaux 1 et 2 sur chaque image -- des repères de son,
            # pas la fin -- et la lecture s'arretait a la premiere. On donne ses images.
            trames = list(e["images_brutes"])
        else:
            trames = script_images(table, sc)
            # L'INTRODUCTION NE PASSE QU'UNE FOIS quand le script finit sur un `0x02` --
            # voir `depart_de_boucle`. Seulement sur cette branche : les autres ne rendent
            # pas les images du script dans son ordre.
            depart = depart_de_boucle(table, sc)

        # LA DERNIERE IMAGE, OU UNE CADENCE IMPOSEE PAR LA ROUTINE -- 17/09/2026 (Elena 1) :
        # les cordes jouent leur script une fois et s'y arretent ; l'id 45 n'avance son script
        # que toutes les 33 trames.
        if e.get("image_finale") and trames:
            trames = trames[-1:]
        if e.get("fige") and trames:
            trames = trames[:1]
        if e.get("duree"):
            trames = [(idx, e["duree"]) for idx, _d in trames]

        images = []
        vides = []
        huit_bits = False
        for idx, duree in trames:
            # UNE TRAME CACHEE (`objetsng.VIDE`) -- 19/09/2026, les gerbes de lave de Gill :
            # l'objet existe mais ne s'affiche pas. On la garde a sa place dans la suite et
            # on la remplit apres, sur la geometrie d'une vraie image.
            if idx == -1:
                vides.append(len(images))
                images.append(dict(duree=duree))
                continue
            r = poser_image(conteneurs, idx)
            if r is None:
                if suites:
                    images = []
                    print("   ecarte : script %d, image %d introuvable" % (sc, idx))
                    break
                continue
            pose, rec, sprite, n = r
            im = dict(sprite=n, duree=duree, ancre=(rec[1], rec[2]),
                      img=pose[0], msk=pose[1], x0=pose[2], y0=pose[3],
                      morceaux=sprite["morceaux"])
            # PLUSIEURS OFFSETS DE PALETTE DANS LE MEME SPRITE -- 17/09/2026. `bloc_c`
            # colorait tout avec la palette du PREMIER morceau : 57 objets de NG sur 260
            # en melangent plusieurs (le haut du pilier de Gill, un sprite de Ken...). On
            # compose l'image en ARGB1555 vrai, chaque morceau avec SA palette, comme
            # `animer2i`, et on garde la provenance de chaque pixel.
            # LES SPRITES A HUIT BITS -- 22/09/2026, les quatorze immeubles de Sean
            # (id 44). Leurs index montent a 255 : leur palette tient quatre
            # emplacements, et `bloc_c` les coloriait avec un seul -- les index > 63
            # allaient lire les emplacements voisins, d'ou les aplats jaunes et
            # mauves que Frederic a vus le 18/09. Aucun autre objet de NG n'a
            # d'index > 63.
            if pose[0].max() > 63:
                pc = A.poser_1555(sprite, poser_image.tuiles, banque_brute(), 0,
                                  lambda dr, off, bb=bande: num_de_morceau_8bits(bb, off),
                                  avec_source=True, huit_bits=True)
                if pc is not None:
                    im["c1555"], im["src1555"] = pc[0], pc[1]
                    huit_bits = True
            elif len({m[1] & 0x1FF for m in sprite["morceaux"]}) > 1:
                pc = A.poser_1555(sprite, poser_image.tuiles, banque_brute(), 0,
                                  lambda dr, off, e=e: num_de_morceau(bande, e, off),
                                  avec_source=True)
                if pc is not None:
                    im["c1555"], im["src1555"] = pc[0], pc[1]
            # LE RETOURNEMENT (`+10`) : pixel d'ecart `dx` pose en `-dx - 1`.
            if e.get("miroir"):
                gauche = rec[1] + pose[2]
                im.update(img=pose[0][:, ::-1].copy(), msk=pose[1][:, ::-1].copy(),
                          ancre=(-(gauche + pose[0].shape[1]) - pose[2], rec[2]))
                for cle in ("c1555", "src1555"):
                    if cle in im:
                        im[cle] = im[cle][:, ::-1].copy()
            images.append(im)

        if vides:
            vraies = [im for im in images if "img" in im]
            if not vraies:
                continue
            ref = vraies[0]
            for n in vides:
                im = dict(ref, duree=images[n]["duree"], img=np.zeros((16, 16), ref["img"].dtype),
                          msk=np.zeros((16, 16), bool), x0=ref["x0"], y0=ref["y0"])
                for cle in ("c1555", "src1555"):
                    if cle in ref:
                        im[cle] = np.zeros((16, 16), ref[cle].dtype)
                images[n] = im

        if not images:
            continue

        cols, ligs, _ox, _oy, _e = grille(images)
        # 256 IMAGES DEPUIS LE 17/09/2026 : l'identite de motif du moteur a huit bits
        # d'image (`DecorObjets_Identite`), et `pas` en garde l'index sur un octet.
        if len(images) > 256:
            print("   ecarte : script %d, %d images (max 256)" % (sc, len(images)))
            continue
        if ligs > CASES_PAR_RANG:
            print("   ecarte : script %d, %d lignes, indecoupable en colonnes" % (sc, ligs))
            continue

        vus.add(cle)
        col = e.get("col", e.get("drapeaux"))
        # LA PROFONDEUR : `+88` quand le lecteur l'ecrit, sinon `+556` (la statue ecrit
        # `+556` puis le recopie en `+88`).
        prof = e.get("pal", e.get("palette"))
        if prof is None:
            for c in e.get("champs", ()):
                if c.get("objet") == 556:
                    prof = c["valeur"]
        out.append(dict(huit_bits=huit_bits,
                        x=e.get("x", 0), y=e.get("y", 0), plan=e.get("plan", 2),
                        script=sc, images=images, rang=rang, bande=bande,
                        bande_pal=bande, aire=aire, bandes=[bande],
                        adresse=e["adresse"], pal=prof, decor=dnum,
                        prio=e.get("prio"), col=col, source=source,
                        variante=e.get("variante", 0xF), dx=e.get("dx"),
                        comportement=e.get("comportement", 0), pas=pas, bornes=bornes,
                        trajet=e.get("trajet") or trajet_du_script(table, sc),
                        force_boucle=e.get("boucle", False),
                        fin=e.get("fin", False),
                        echelle=e.get("echelle"), echelle_pas=e.get("echelle_pas"),
                        echelle_seg=e.get("echelle_seg", -1),
                        boite=e.get("boite"), depart_boucle=depart))
        rang += 1

    return out, nom_asset, inconnus


# LE BUDGET D'UN ETAGE, ET IL EST DUR
# -----------------------------------
# Servir les objets larges en morceaux les fait tous rentrer -- 353 au lieu de 125 -- mais
# un etage ne peut pas les porter tous :
#
#   * la cle de cache `rang<<11 | image<<5 | case` n'a que CINQ bits de rang : 32 objets ;
#   * le tas de morceaux tient QUATRE pages, 1024 emplacements, et `life16` laisse trois a
#     quatre images vivantes a la fois -- d'ou 256 cases par trame au plus.
#
# Sans ce garde, la bande 0 de NG demandait 58 objets et 1517 cases : trois fois ce qui
# figeait deja Ibuki (544). On choisit donc, et on DIT ce qu'on laisse.
#
# L'ORDRE DE CHOIX : les objets qui tiennent d'une piece d'abord -- ils ne coutent qu'un
# rang -- puis les decoupes, du moins large au plus large. C'est ce qui montre le plus
# d'objets DISTINCTS, plutot qu'un seul grand sprite qui mangerait tout le budget.
RANGS_MAX = 56          # OBJETS_MAX de decor_objets.c depuis le 18/09
CASES_PAR_TRAME_MAX = 256

# LA TROISIEME LIMITE, ET C'EST ELLE QUI GELE LE JEU — ajoutee le 05/09/2026.
#
# `PatternCollection` ne tient que 64 motifs, et `verifier_objets.py` le controle depuis
# longtemps cote 2nd Impact. Le budget de NG, lui, ne comptait que les rangs et les cases :
# en recuperant 34 objets des conteneurs voisins, l'etage 55 est monte a **76 motifs
# vivants pour 64**. Le moteur ne rend pas d'erreur dans ce cas -- il part en `while (1)`.
MOTIFS_MAX = 128        # PATTERN_COLLECTION_MAX -- 64 sur la console, 128 ici


def motifs_vivants(o, boucle=1):
    """Combien d'images de cet objet vivent en meme temps (`mts_base[7].life16 = 12`).

    LE COMPTE DE 2I, BRANCHE ICI LE 16/09/2026 avec la revue de NG : une image reste vivante
    douze trames APRES son dernier dessin, et la pire trame est une transition -- l'image
    qui apparait, plus celles qui ont fini dans les douze trames d'avant. Un objet qui ne
    boucle pas n'en a qu'une.
    """
    if not boucle:
        return 1
    d = [im["duree"] for im in o["images"]]
    n = len(d)
    pire = 1
    for depart in range(n):
        vus, ecart, k = 1, 1, depart - 1
        while vus < n and ecart <= 12:
            vus += 1
            ecart += d[k % n]
            k -= 1
        pire = max(pire, vus)
    return pire


# LA DEMANDE AU CACHE DE MORCEAUX, AU LIEU DES « 256 CASES PAR TRAME » -- 16/09/2026.
#
# L'ancienne borne comptait les cases de chaque objet comme si toutes ses images vivaient :
# les elements FIXES de New Generation, qui n'ont qu'une image mais jusqu'a 290 cases,
# l'epuisaient a eux seuls, et la revue en ecartait des dizaines -- des trous dans le decor.
# Le cache des etages de NG tient quatre pages (`ETAGESNG_OB_PAGE`), 1024 morceaux ; la
# demande d'un objet est ses cases fois ses images vivantes au pire, et on garde 15 % de
# marge (Hugo figeait a 108 %).
# HUIT PAGES DEPUIS LE 17/09/2026 (`ETAGESNG_OB_PAGE`, `PatternMap.x16_map[8]`) : 2048
# morceaux, et toujours 15 % de marge.
# 2240 DEPUIS LE 22/09/2026, soit 12,5 % de marge au lieu de 15 %. Les cinq vagues de
# lave et les six gerbes de Gill portent sa demande a 2221 : la marge de 15 % l'ecartait
# de 46 morceaux, et le budget rendait alors son plus gros element (script 3, quatre
# fiches, 161 morceaux) -- un objet qui marche aujourd'hui. 2221 sur 2560, c'est 87 % du
# cache : loin des 108 % qui faisaient figer Hugo. `verifier_objets` mesure la demande
# reelle apres coup ; c'est elle qui tranche, pas cette borne.
MORCEAUX_MAX = 2240      # dix pages (2560 morceaux) depuis le soir du 17/09


def cases_pleines(o):
    """Les cases NON VIDES de l'image la plus chargee -- celles que `bloc_c` emet.

    LA DEMANDE COMPTAIT LA GRILLE ENTIERE -- corrige le 17/09/2026. Or `bloc_c` saute les
    cases entierement transparentes, et le cache ne recoit que les autres : sur Gill le
    budget estimait 1545 morceaux vivants, `verifier_objets` en mesure 903. Ce facteur
    ecartait l'auvent de Hong Kong, les grands arbres d'Elena 1, un element de Hugo."""
    cols, ligs, ox, oy, ec = grille(o["images"])
    pire = 0
    for n, im in enumerate(o["images"]):
        g = np.zeros((ligs * 16, cols * 16), bool)
        a, b = oy + ec[n][1], ox + ec[n][0]
        g[a:a + im["msk"].shape[0], b:b + im["msk"].shape[1]] = im["msk"] & (im["img"] != 0)
        pire = max(pire, int(g.reshape(ligs, 16, cols, 16).any(axis=(1, 3)).sum()))
    return pire


def budget(obj, depart=(0, 0, 0)):
    """(gardes, refuses, (rangs, morceaux, motifs)) : ce qui tient dans un etage, ce qu'on
    laisse, et ce qui est pris -- `depart` etant ce que les animations de pages ont deja pris."""
    cotes = []

    for o in obj:
        tr = morceaux_objet(o)
        boucle = 1 if (o.get("comportement") or o.get("force_boucle")
                      or est_une_boucle(o["images"])) else 0
        vivantes = motifs_vivants(o, boucle)
        cotes.append((len(tr), cases_pleines(o) * vivantes, o, tr, vivantes))

    cotes.sort(key=lambda t: (t[0], t[1]))
    gardes, refuses = [], []
    rangs, morceaux, motifs = depart

    for nrangs, demande, o, tr, vivantes in cotes:
        nm = len(tr) * vivantes

        if (rangs + nrangs > RANGS_MAX or morceaux + demande > MORCEAUX_MAX
                or motifs + nm > MOTIFS_MAX):
            refuses.append((o, nrangs, demande))
            continue

        rangs += nrangs
        morceaux += demande
        motifs += nm
        gardes.append((o, tr))

    return gardes, refuses, (rangs, morceaux, motifs)


# UNE ANIMATION DE PAGES QUI NE TIENT PAS ENTIERE TIENT EN PARTIE -- 28/09/2026
# ------------------------------------------------------------------------------
# Frederic : « IBUKI les bambous de gauche qui ne bougent pas sous l'effet du vent, il faut
# ajouter cette animation ». Elle existe, elle est lue, et elle etait JETEE EN ENTIER par le
# budget. Les chiffres, pour ses trois bandes :
#
#     etage  pris par le reste          le vent sur la couche 1        total
#       48   20 rangs, 1893 morceaux    7 rangs, 984 morceaux, 21 mot.  2877 / 2240
#       49   17 rangs, 1542 morceaux    idem                            2526 / 2240
#       50   14 rangs, 1464 morceaux    idem                            2448 / 2240
#
# Les rangs (27 sur 56) et les motifs (103 sur 128) passaient largement : c'est le seul
# compte de MORCEAUX qui bloquait, et de peu.
#
# Or une animation de pages est deja DECOUPEE EN TRANCHES DE COLONNES (`pagesng.morceler`),
# et chaque tranche est un objet a part entiere : rien n'oblige a les prendre toutes. On en
# garde donc autant qu'il en tient, DE LA GAUCHE VERS LA DROITE -- ce sont les bambous de
# gauche que Frederic ne voit pas bouger.
#
# Le cout d'une tranche se recalcule exactement comme `pagesng.preparer` le fait pour la
# somme : `cases * vivantes` pour le cout, une par tranche pour le rang, `vivantes` par
# tranche pour les motifs.
def _part_de(p, gardees):
    """L'animation `p` reduite a ces tranches-la, cout, rangs et motifs recalcules."""
    viv = p["motifs"] // max(1, p["rangs"])
    cases = sum(int(p["masque"][r0:r1, c0:c1].sum()) for r0, r1, c0, c1 in gardees)
    return dict(p, morceaux=gardees, cout=cases * viv, rangs=len(gardees),
                motifs=len(gardees) * viv, partielle=len(gardees) != len(p["morceaux"]))


def budget_pages(pages, pris):
    """Les animations de pages qui tiennent encore, dans leur ordre.

    Celle qui ne tient pas entiere est servie en partie : ses tranches de colonnes sont
    prises de la gauche vers la droite tant qu'elles tiennent."""
    rangs, morceaux, motifs = pris
    gardes, refuses = [], []

    for p in pages:
        if (rangs + p["rangs"] <= RANGS_MAX and morceaux + p["cout"] <= MORCEAUX_MAX
                and motifs + p["motifs"] <= MOTIFS_MAX):
            rangs += p["rangs"]
            morceaux += p["cout"]
            motifs += p["motifs"]
            gardes.append(p)
            continue

        # de la gauche vers la droite : `morceler` rend (r0, r1, c0, c1)
        tenues = []

        for tr in sorted(p["morceaux"], key=lambda t: (t[2], t[0])):
            essai = _part_de(p, tenues + [tr])

            if (rangs + essai["rangs"] > RANGS_MAX
                    or morceaux + essai["cout"] > MORCEAUX_MAX
                    or motifs + essai["motifs"] > MOTIFS_MAX):
                break

            tenues.append(tr)

        if not tenues:
            refuses.append(p)
            continue

        part = _part_de(p, tenues)
        rangs += part["rangs"]
        morceaux += part["cout"]
        motifs += part["motifs"]
        gardes.append(part)

    return gardes, refuses, (rangs, morceaux, motifs)


# LES CASES D'UN RANG : 64 DEPUIS LE 17/09/2026. Les 32 venaient de la cle de cache
# `rang << 11 | image << 5 | case` ; elle n'existe plus (la cle est un rang de morceau dans
# l'etage), et la borne restante est `CASES_MAX` de `decor_objets.c`, 64. Deux fois moins de
# tranches par grand objet, donc deux fois moins de rangs : Hugo, Gill et Elena 1 perdaient
# leurs grands elements sur la limite des 48 objets. `animer2i` garde 32 : 2I est valide.
CASES_PAR_RANG = 64


def morceaux_objet(o):
    """Le decoupage en tranches de colonnes qui tiennent sous `CASES_PAR_RANG` cases.

    Meme regle que dans `animer2i` : un objet trop large n'est pas a retailler, il est a
    SERVIR en plusieurs objets voisins qui se rejoignent au pixel pres.
    """
    cols, ligs, _ox, _oy, _e = grille(o["images"])

    if cols * ligs <= CASES_PAR_RANG:
        return [(0, cols)]

    large = max(1, CASES_PAR_RANG // ligs)
    return [(c, min(large, cols - c)) for c in range(0, cols, large)]


_VERTES = None


def cases_vertes():
    """Les cases NON INITIALISEES de la banque : rouge et bleu nuls, vert non nul."""
    global _VERTES

    if _VERTES is None:
        n = (len(BIN) - POFF) // 128
        b = np.frombuffer(BIN[POFF:POFF + n * 128], dtype="<u2").reshape(n, 64)
        _VERTES = ((b & 0x7C1F) == 0) & ((b & 0x03E0) != 0)

    return _VERTES


def bande_de_palette(o):
    """Parmi LES BANDES DU DECOR, celle dont la palette ne tombe sur aucune case vide.

    POURQUOI CE CHOIX N'EST PAS UN REGLAGE — 05/09/2026
    ---------------------------------------------------
    Un decor a variantes porte plusieurs bandes, `d["bandes"]`, et chacune charge son
    propre jeu de palettes. On prenait `bandes[0]` pour tous ses objets. Frederic a
    signale `n05o9` : il sort 236 pixels verts ainsi, et **propre** avec la deuxieme
    bande du decor.

    L'AIRE NE DONNE PAS LA REPONSE, ET C'EST MESURE. Prendre `bandes[aire]` corrige le
    decor 3 (`[5, 6, 6]`) et casse le decor 10 (`[18, 17, 17]`) -- deux objets propres y
    repassent a 70 et 116 verts. Or les bandes 5 et 17 chargent la MEME base (338), 6 et
    18 aussi (380) : dans les deux decors, les objets concernes veulent 380. La liste des
    bandes n'est donc pas dans l'ordre des aires, et on ne peut pas s'en servir comme
    index.

    Ce qui reste licite, c'est ce que le detecteur sait faire : **eliminer**. On garde
    `bandes[0]` par defaut -- il ne se discute que s'il est pris en faute -- et on ne
    passe a une autre bande DU MEME DECOR que si elle est propre la ou lui ne l'est pas.
    Aucun candidat n'est invente : ils viennent tous de l'annuaire du decor.
    """
    champ = o["images"][0]["morceaux"][0][1]
    defaut = o["bande"]
    cands = [defaut] + [b for b in o.get("bandes", ()) if b != defaut]

    h = np.zeros(64, np.int64)
    for im in o["images"]:
        h += np.bincount(np.where(im["msk"], im["img"], 0).astype(np.uint8).ravel(),
                         minlength=64)[:64]
    h[0] = 0
    employes = np.nonzero(h)[0]

    if not len(employes):
        return defaut

    v = cases_vertes()

    for b in cands:
        num, _p = palette(b, champ)

        if num is None or num >= len(v):
            continue

        if not v[num][employes].any():
            return b

    return defaut


_BRUTE = None


def banque_brute():
    """La banque de couleurs de NG en ARGB1555 brut, une palette de 64 par ligne."""
    global _BRUTE
    if _BRUTE is None:
        n = (len(BIN) - POFF) // 128
        _BRUTE = np.frombuffer(BIN[POFF:POFF + n * 128], dtype="<u2").reshape(n, 64)
    return _BRUTE


def num_de_morceau(bande, e, offset):
    """Le numero de palette d'un morceau d'offset `offset` -- la regle de `bloc_c`, morceau
    par morceau : la base de la bande, puis la regle RAM quand l'emplacement est connu."""
    num, _p = palette(bande, offset)
    col = e.get("col", e.get("drapeaux"))
    if col is not None:
        import palettes_ramng as PRN
        n_ram = PRN.palette(bande, col, offset)
        if n_ram is not None:
            num = n_ram
    return num


# LA PALETTE D'UN SPRITE A HUIT BITS -- 22/09/2026, corrige le soir meme.
#
# Elle tient QUATRE emplacements consecutifs (256 couleurs), et l'offset du morceau les
# compte par banque de 256 : emplacement = base du transfert + offset*4, couleur =
# index % 64, emplacement + index // 64.
#
# LA BASE EST CELLE DU PREMIER TRANSFERT (`0x8C18AC10`), et c'est LE DECOR LUI-MEME QUI
# LE DIT. Chaque rectangle de scene porte en `+12` un code couleur lu par `0x8C10FB64` :
# ses neuf bits bas sont l'emplacement de palette RAM, exactement comme le `+554` d'un
# objet. Les deux couches de Sean portent `0x240` : emplacement 64 -- la destination du
# PREMIER transfert de la bande 2 (0x2000), base 168 dans le binaire. Les immeubles sont
# les immeubles de ce decor : ils tirent sur la meme banque que ses couches.
#
# CONTROLE PAR LA MESURE : coloriee depuis 168, la moyenne des immeubles est
# (95, 64, 91) contre (137, 93, 169) pour la page lointaine -- qui porte la meme ville ;
# depuis 192, elle tombe a (61, 40, 58), bien plus loin. Ecart total aux trois canaux :
# 148 contre 240.
#
# CE QUE LA PREMIERE MESURE DISAIT, ET POURQUOI ON NE LA SUIT PAS. Noter chaque base par
# l'ecart de couleur moyen entre pixels VOISINS donnait 2,63 a la base 192 et 3,97 a la
# base 168. Mais ce critere ne dit que la REGULARITE d'une palette, pas sa justesse : il
# prefere la plus plate. Le code couleur des couches, lui, se lit. Et Frederic, le 22/09,
# sur la capture : « les 2 moities horizontales du decor n'ont pas la meme palette » --
# le haut de l'ecran de Sean est fait d'OBJETS (jusqu'a 384 colonnes sur 384 des lignes 0
# a 110), le bas de ses PAGES (250 a 350 colonnes des lignes 112 a 223). C'est exactement
# les immeubles contre les couches.
def num_de_morceau_8bits(bande, offset):
    """Le premier des quatre emplacements d'un morceau de sprite a huit bits."""
    import palettes_ramng as PRN
    e = PRN.entree(PRN.u16(PRN.PREMIER + bande * 2))
    return e["base"] + offset * 4


def multipalette(o):
    return all(im.get("c1555") is not None for im in o["images"])


def composer_1555(o):
    """(images ARGB1555, provenances) posees sur la grille entiere de l'objet."""
    cols, ligs, ox, oy, ec = grille(o["images"])
    ims, srcs = [], []
    for n, im in enumerate(o["images"]):
        u = np.zeros((ligs * 16, cols * 16), np.uint16)
        s_ = np.zeros((ligs * 16, cols * 16), np.uint16)
        a, b = oy + ec[n][1], ox + ec[n][0]
        c = im["c1555"]
        u[a:a + c.shape[0], b:b + c.shape[1]] = c
        s_[a:a + c.shape[0], b:b + c.shape[1]] = im["src1555"]
        ims.append(u)
        srcs.append(s_)
    return ims, srcs


def groupes_palette(o, col0, ncols):
    """`[None]` si la tranche tient dans 63 couleurs, sinon des groupes de palettes source
    a poser en objets SUPERPOSES -- la regle de `animer2i.groupes_palette`."""
    if not multipalette(o):
        return [None]
    # UN SPRITE A HUIT BITS NE SE DECOUPE PAS PAR PALETTE : ses quatre quarts se
    # partagent les memes pixels, et le decoupage donnait 71 fiches a Sean pour les 56
    # places d'`OBJETS_MAX` (mesure de `verifier_objets`). On le sert en UNE fiche,
    # avec la palette effective reduite -- voir `bloc_c_1555`.
    if o.get("huit_bits"):
        return [None]
    ims, srcs = composer_1555(o)
    x0, x1 = col0 * 16, (col0 + ncols) * 16
    par_source, toutes = {}, set()
    for u, s_ in zip(ims, srcs):
        z, zs = u[:, x0:x1], s_[:, x0:x1]
        peints = z != 0
        toutes.update(int(v) for v in np.unique(z[peints]))
        for num in np.unique(zs[peints]):
            par_source.setdefault(int(num), set()).update(
                int(v) for v in np.unique(z[peints & (zs == num)]))
    if len(toutes) <= 63:
        return [None]
    groupes, courant, couleurs = [], set(), set()
    for num in sorted(par_source):
        if courant and len(couleurs | par_source[num]) > 63:
            groupes.append(frozenset(courant))
            courant, couleurs = set(), set()
        courant.add(num)
        couleurs |= par_source[num]
    if courant:
        groupes.append(frozenset(courant))
    return groupes


def bloc_c_1555(o, prefixe, col0, ncols, garder):
    """Le C d'un objet a plusieurs palettes : palette FABRIQUEE avec les couleurs employees."""
    cols_tot, ligs, _ox, _oy, _ec = grille(o["images"])
    cols = ncols
    ims, srcs = composer_1555(o)
    x0, x1 = col0 * 16, (col0 + cols) * 16
    rang, couleurs = {}, []
    for n in range(len(ims)):
        if garder is not None:
            ims[n] = np.where(np.isin(srcs[n], sorted(garder)), ims[n], 0)
        for v in np.unique(ims[n][:, x0:x1]):
            if v and int(v) not in rang:
                rang[int(v)] = len(couleurs) + 1
                couleurs.append(int(v))
    # PLUS DE 63 COULEURS : ON REDUIT AU LIEU D'ECARTER -- 22/09/2026.
    #
    # Les immeubles de Sean sont des sprites a HUIT bits : jusqu'a 177 couleurs dans un
    # objet. Le moteur du port n'a que 63 emplacements par fiche. Les decouper par quart
    # de palette donnait 71 fiches pour les 56 places de l'etage ; les ecarter laissait
    # des trous dans New York. On garde donc les 63 couleurs LES PLUS PEINTES et on
    # envoie chaque autre sur la plus proche (distance sur les trois canaux de 5 bits).
    # L'ecart moyen est dit a l'ecran : c'est une mesure, pas un choix a l'oeil.
    table = np.zeros(65536, np.uint8)
    if len(couleurs) > 63:
        poids = {}
        for n in range(len(ims)):
            z = ims[n][:, x0:x1]
            vs, cs = np.unique(z[z != 0], return_counts=True)
            for v, c in zip(vs, cs):
                poids[int(v)] = poids.get(int(v), 0) + int(c)
        gardees = sorted(sorted(poids, key=lambda v: -poids[v])[:63])
        def _rgb(v):
            return np.array([(v >> 10) & 31, (v >> 5) & 31, v & 31], np.int32)
        pg = np.array([_rgb(v) for v in gardees], np.int32)
        rang = {v: k + 1 for k, v in enumerate(gardees)}
        couleurs = list(gardees)
        ecart, total = 0, 0
        for v in poids:
            d = np.abs(pg - _rgb(v)).sum(1)
            k = int(d.argmin())
            table[v] = k + 1
            ecart += int(d[k]) * poids[v]
            total += poids[v]
        print("   %s : %d couleurs ramenees a 63, ecart moyen %.2f / 93"
              % (prefixe, len(poids), ecart / float(total)))
    else:
        for v, k in rang.items():
            table[v] = k
    L, cases = [], []
    for n in range(len(ims)):
        g = table[ims[n]]
        for lig in range(ligs):
            for col in range(cols):
                sc = (col0 + col) * 16
                bloc = g[lig * 16:lig * 16 + 16, sc:sc + 16]
                if not bloc.any():
                    continue
                nom = "%s_i%d_%d_%d" % (prefixe, n, col, lig)
                L.append("static const unsigned char %s[256] = { %s };"
                         % (nom, ", ".join(str(v) for v in AN0.entrelacer(bloc))))
                cases.append("    { %d, %d, %d, %s }," % (n, col * 16, lig * 16, nom))
    pal = [0] * 64
    for v, k in rang.items():
        pal[k] = v
    if garder:
        num = min(garder)
    else:
        num = min(int(sv[sv > 0].min()) for sv in srcs if (sv > 0).any())
    L.append("")
    L.append("static const DecorTuile %s_tuiles[] = {" % prefixe)
    L.extend(cases)
    L.append("};")
    L.append("static const unsigned char %s_durees[%d] = { %s };"
             % (prefixe, len(o["images"]), ", ".join(str(im["duree"]) for im in o["images"])))
    L.append("static const unsigned short %s_palette[64] = { %s };"
             % (prefixe, ", ".join("0x%04X" % v for v in pal)))
    if o.get("comportement") and o.get("pas"):
        L.append("static const unsigned char %s_pas[%d] = { %s };"
                 % (prefixe, 2 * len(o["pas"]), ", ".join("%d, %d" % ip for ip in o["pas"])))
        L.append("static const unsigned short %s_suites[%d] = { %s };"
                 % (prefixe, len(o["bornes"]), ", ".join(str(b) for b in o["bornes"])))
    if o.get("trajet"):
        # UN SEGMENT PORTE CINQ CHAMPS DEPUIS LE 25/09/2026 : duree, vx, vy, suite, et
        # la PROFONDEUR. Zero garde celle de la fiche -- les trajets ecrits a quatre
        # champs sont completes ici, et rien ne change pour eux.
        L.append("static const short %s_trajet[%d] = { %s };"
                 % (prefixe, 5 * len(o["trajet"]),
                    ", ".join("%d, %d, %d, %d, %d" % (tuple(t) + (0,) * 5)[:5]
                              for t in o["trajet"])))
    L.append("")
    return NL.join(L), cols, ligs, len(o["images"]), len(cases), num


NL = chr(10)


def bloc_c(o, prefixe, col0=0, ncols=None, garder=None):
    if multipalette(o):
        cols_tot = grille(o["images"])[0]
        return bloc_c_1555(o, prefixe, col0, cols_tot if ncols is None else ncols, garder)
    cols_tot, ligs, ox, oy, ec = grille(o["images"])
    cols = cols_tot if ncols is None else ncols
    L, cases = [], []

    for n, im in enumerate(o["images"]):
        g = np.zeros((ligs * 16, cols_tot * 16), np.uint8)
        src = np.where(im["msk"], im["img"], 0).astype(np.uint8)
        a, b = oy + ec[n][1], ox + ec[n][0]
        g[a:a + src.shape[0], b:b + src.shape[1]] = src

        for lig in range(ligs):
            for col in range(cols):
                sc = (col0 + col) * 16
                bloc = g[lig * 16:lig * 16 + 16, sc:sc + 16]

                if not bloc.any():
                    continue

                nom = "%s_i%d_%d_%d" % (prefixe, n, col, lig)
                L.append("static const unsigned char %s[256] = { %s };"
                         % (nom, ", ".join(str(v) for v in AN0.entrelacer(bloc))))
                cases.append("    { %d, %d, %d, %s }," % (n, col * 16, lig * 16, nom))

    # LA BANDE DE LA PALETTE N'EST PAS FORCEMENT CELLE DE L'ETAGE : voir
    # `bande_de_palette`. Elle reste `bandes[0]` sauf si le detecteur l'y prend en faute.
    champ = o["images"][0]["morceaux"][0][1]
    num, pal = palette(bande_de_palette(o), champ)

    # LA REGLE RAM DE 2I, PORTEE A NG -- 16/09/2026 (`palettes_ramng.py`). `+554` est
    # l'emplacement ; le morceau d'offset `o` lit l'emplacement `+554 + o`. Elle retrouve
    # seule la correction de la bande 5 (1397), trouvee au detecteur de vert.
    if o.get("col") is not None:
        import palettes_ramng as PRN
        n_ram = PRN.palette(o["bande"], o["col"], champ & 0x1FF)
        if n_ram is not None and n_ram != num:
            base = n_ram - (champ & 0x1FF)
            num = n_ram
            pal = np.frombuffer(BIN[POFF + num * 128:POFF + num * 128 + 128], dtype="<u2").copy()
            pal[0] = 0

    if pal is None:
        return None

    L.append("")
    L.append("static const DecorTuile %s_tuiles[] = {" % prefixe)
    L.extend(cases)
    L.append("};")
    L.append("static const unsigned char %s_durees[%d] = { %s };"
             % (prefixe, len(o["images"]),
                ", ".join(str(im["duree"]) for im in o["images"])))
    L.append("static const unsigned short %s_palette[64] = { %s };"
             % (prefixe, ", ".join("0x%04X" % v for v in pal)))
    if o.get("comportement") and o.get("pas"):
        L.append("static const unsigned char %s_pas[%d] = { %s };"
                 % (prefixe, 2 * len(o["pas"]), ", ".join("%d, %d" % ip for ip in o["pas"])))
        L.append("static const unsigned short %s_suites[%d] = { %s };"
                 % (prefixe, len(o["bornes"]), ", ".join(str(b) for b in o["bornes"])))
    if o.get("trajet"):
        # UN SEGMENT PORTE CINQ CHAMPS DEPUIS LE 25/09/2026 : duree, vx, vy, suite, et
        # la PROFONDEUR. Zero garde celle de la fiche -- les trajets ecrits a quatre
        # champs sont completes ici, et rien ne change pour eux.
        L.append("static const short %s_trajet[%d] = { %s };"
                 % (prefixe, 5 * len(o["trajet"]),
                    ", ".join("%d, %d, %d, %d, %d" % (tuple(t) + (0,) * 5)[:5]
                              for t in o["trajet"])))
    L.append("")
    return "\n".join(L), cols, ligs, len(o["images"]), len(cases), num


# COMBIEN DE PLANS CHAQUE BANDE DE NG PORTE -- `ETAGESNG_USE_SCR`, genere.
# Une bande a 2 plans n'a PAS de troisieme famille : y envoyer un objet le ferait
# disparaitre.
USE_SCR = [2, 2, 2, 3, 3, 3, 2, 3, 2, 3, 2, 3, 3, 3, 2, 2, 3, 3, 2]


# LA FAMILLE D'UN OBJET EST CELLE DE LA LISTE QUI PORTE SON PLAN -- 17/09/2026.
#
# `mlt_obj_matrix` prend `BgMATRIX[my_family]`, et `BgMATRIX[n + 1]` est la matrice de
# `bgw[n]` : famille 1 = liste 132, 2 = liste 196, 3 = liste 260 (`couchesng.py`). Or
# `etagesng.fiche()` ne range pas les plans de NG dans le meme ordre d'une bande a l'autre :
# la bande 7 met son plan 3 (le lointain, priorite 104) en liste 132, la bande 14 met son
# plan 2 en liste 132. L'ancienne regle -- « plan 1 et trois plans : famille 3, sinon 2 » --
# ne valait que pour les bandes rangees comme Oro, et c'est la que Frederic l'a validee.
#
# La regle generale : l'objet de plan `p` defile avec la couche `k` de meme plan
# (`couches_ng`), donc avec la famille de la liste qui porte `k`. Elle rend la meme chose
# qu'avant pour Oro et Ibuki ; elle remet sur leur plan la tour du fond de Londres (bandes 7
# et 8, x 479), le gratte-ciel lointain de New York (bande 1) et les objets de la bande 14.
# Un plan qui n'a pas de liste (demi-banque vide) prend la famille dont le coefficient de
# defilement est le plus proche du sien ; un plan introuvable ou ambigu garde la famille 2.
FAMILLE_DE_LISTE = {132: 1, 196: 2, 260: 3}


# Les bandes dont un objet sans couche SUIT LA RUE -- voir `famille_du_plan`. Mesure, pas
# reglage : Sean, le 24/09/2026, sur le dessin de ses deux couches et de ses fiches.
SANS_COUCHE_SUIT_LA_RUE = {2}


def famille_du_plan(bande, plan):
    import etagesng as E
    couches = E.couches_ng(bande)
    ks = [k for k in range(4) if couches[k] is not None and couches[k][0] == plan]
    # UN PLAN SANS COUCHE, AUTRE QUE LE 2 -- 18/09/2026 : les immeubles de Sean (plans 3 et 5).
    # L'initialisation des plans (`0x8C088242`) leur donne un coefficient nul, ou aucun (le
    # plan 5 est hors de la table) : ils ne suivent pas la rue. On les met sur le plan le plus
    # lent de la bande, le seul qui reste presque fixe.
    #
    # ET C'ETAIT FAUX POUR SEAN -- 24/09/2026. Frederic : « pour le decor NG de Sean, il y a
    # toujours la parallaxe qui ne devrait pas exister, qui montre le triangle noir qu'on ne
    # devrait pas voir ».
    #
    # Le dessin le montre sans ambiguite (`sean-complet.png`, les fiches posees sur ses deux
    # couches) : ses QUATORZE objets de plans 3 et 5 sont **les gratte-ciel du fond de la
    # rue**. Ils se rangent entre l'immeuble peint de gauche et celui de droite, leurs pieds
    # touchent le trottoir de la couche proche, et l'un d'eux vient combler l'arc creuse dans
    # la facade de droite. C'est UNE SEULE SCENE continue avec la rue.
    #
    # A 0,625 ils glissaient donc sur elle a chaque mouvement de camera, et le trou noir que
    # Frederic voit est cet arc qui se decouvre. Le defaut documente deux lignes plus bas --
    # « un plan introuvable ou ambigu garde la famille 2 » -- etait le bon pour lui.
    #
    # On ne le remet que pour Sean, la ou c'est mesure. Quatre autres etages passent par la
    # meme branche et ne sont PAS touches, faute d'observation : 38 (plan 3, 2 fiches),
    # 44 (plan 3, 2), 51 (plan 3, 3) et 52 (plans 3 et sans plan, 6). Meme construction,
    # meme soupcon -- a juger sur l'image, un par un.
    if not ks and plan != 2 and bande in SANS_COUCHE_SUIT_LA_RUE:
        return 2

    if not ks and plan != 2:
        f = E.fiche(bande)
        print("   plan %d sans couche (bande %d) : famille du plan le plus lent" % (plan, bande))
        liste = min(f["couches"], key=lambda l: E.coefs(bande, f["couches"][l][2])[0])
        return FAMILLE_DE_LISTE[liste]
    if len(ks) != 1:
        return 2
    k = ks[0]
    f = E.fiche(bande)
    for liste, (_bq, _m, objet) in f["couches"].items():
        if objet == k:
            return FAMILLE_DE_LISTE[liste]
    cx = E.coefs(bande, k)[0]
    if not cx:
        return 2
    liste = min(f["couches"],
                key=lambda l: (abs(E.coefs(bande, f["couches"][l][2])[0] - cx), l != 196))
    return FAMILLE_DE_LISTE[liste]


# LE `x` DE CERTAINS DECORS EST COMPTE DEPUIS LE MILIEU DE LA BANDE -- 17/09/2026.
#
# C'est la regle de Ryu en 2I (`animer2i.DECALAGE_X`, mesuree sur deux captures de
# l'original). Le decor 2 de NG EST ce decor : memes enregistrements, memes x (-233 les
# singes, -145 la femme au panneau, -112 la femme en rose, 273 le gros baigneur). Deux autres
# decors ont la meme signature -- tous leurs x sous 512, beaucoup de negatifs : le 4
# (Londres, bandes 7 et 8, x de -352 a 479) et le 6 (la fete sous la tente, bande 10, x de
# -367 a 201). Le 11 est une copie du 2.
#
# LA MESURE (`mesure_origine_ng.py`, pages brutes du disque) : a x + 512, cinq objets de
# Ryu NG retrouvent leur copie peinte dans la banque (39 a 51 % des pixels, contre 0 a 10 %
# a x). Recomposes, Londres et la tente ne se lisent qu'a x + 512 : le grand immeuble
# prolonge la facade du pub, la maison a colombages se pose sur le mur du pont, la chope
# pend au navire, la banderole tombe sur l'escalier. Enroules, ils flottaient.
#
# SEUL LE PLAN 2 EST DECALE. La tour du fond de Londres (plan lointain, x 479) est a sa
# place SANS decalage : au point de fuite, entre les deux rues. A x + 512 elle sortait de la
# couche. Les decors a x positifs (New York, Hong Kong, Elena...) ne bougent pas : New York
# decale perd son drapeau et ses escaliers.
DECALAGE_X = {2: 512, 4: 512, 6: 512, 11: 512}


def decalage_x(o):
    if o.get("dx") is not None:
        return o["dx"]
    return DECALAGE_X.get(o.get("decor"), 0) if o.get("plan", 2) == 2 else 0


def famille_et_z(o):
    """(famille, z) : la famille par le plan (`famille_du_plan`), le z par l'objet.

    `famille` choisit la MATRICE, donc le defilement ; `z` l'ORDRE DE DESSIN, et un z plus
    grand est plus loin. Les trois objets de plan 1 d'Oro NG -- ses cascades -- vont en
    famille 3 : c'est ce que Frederic a valide (« les cascades ne sont pas dans le bon
    plan », corrige le 04/09).
    """
    fam = famille_du_plan(o["bande"], o["plan"])

    # LA PROFONDEUR EST LUE, ELLE AUSSI — 04/09/2026, comme en 2nd Impact.
    #
    # L'enregistrement porte sa palette a l'octet 8, et **le chargeur ecrit cette meme
    # valeur en `+556` (`my_priority`)** -- verifie dans SF3_1ST.BIN sur `8C0A0070`,
    # `8C0AC75C` et `8C0AC934` : `+88` puis `+556`, tous deux depuis r3, en ecritures
    # consecutives. Exactement le motif de 2I.
    #
    # `8C0A1A40` est le seul lecteur qui n'ecrive PAS `+556` -- six champs au lieu de neuf.
    # Ses objets gardent donc la profondeur du modele, et c'est dit ici plutot que comble.
    z = o["pal"] if o.get("pal") is not None else 0

    # A PROFONDEUR EGALE, C'EST LE PLAN QUI GAGNE -- et le Dreamcast, lui, dessine l'objet
    # APRES -- 28/09/2026.
    #
    # Frederic : « ALEX une ligne noire en arriere plan notifiee plein de fois mais jamais
    # traitee ». Elle est dans la ruelle entre les deux immeubles du fond (scene x 779..807,
    # lignes 672..910), et c'est le GRATTE-CIEL qui la couvre : `0x8C1AF038`, script 2,
    # plan 3, profondeur 104, deux fiches de 64x240 en x 674 et 738 -- son emprise recouvre
    # la fente au pixel. `descripteursng` l'avait deja ecrit le 25/09.
    #
    # Mais son plan, la liste 132 d'Alex, porte la couche 2, elle aussi PLAN 3, PROFONDEUR
    # 104. Sur la console les deux sont dans deux listes d'affichage successives et l'objet
    # passe apres ; ici, `animer2i` a mesure le 15/09 qu'a profondeur egale le plan gagne.
    # Tant que la page du fond etait pleine de trous, ca ne se voyait pas : on voyait le
    # gratte-ciel A TRAVERS. Des qu'on bouche le fond (`couchesng.combler_le_fond`), le plan
    # le recouvre et le gratte-ciel disparait.
    #
    # ON REND L'ORDRE DE LA CONSOLE, d'un seul cran : un objet dont le plan est celui de la
    # couche la plus lointaine et dont la profondeur lui est EGALE passe a z - 1. Il reste
    # derriere tout le reste -- le plan du milieu d'Alex est a 94 --, il ne fait que passer
    # devant SA page. Deux fiches sont concernees dans les dix-neuf etages : celles du
    # gratte-ciel d'Alex.
    import etagesng as E

    f = E.fiche(o["bande"])

    if fam == 1 and 132 in f["couches"]:
        cn = E.couches_ng(o["bande"])
        k = f["couches"][132][2]

        if k < 4 and cn[k] and cn[k][0] == o["plan"] and cn[k][1] == z:
            return fam, z - 1

    return fam, z


def fiche(o, prefixe, cols, ligs, nb_images, nb_tuiles, num, col0=0):
    im = o["images"][0]
    _c, _l, ox, oy, _e = grille(o["images"])
    # LE REPLI SUR 1024 SE FAIT PAR OBJET, PAS PAR TRANCHE -- 19/09/2026. C'etait
    # `& 0x3FF` sur chaque tranche : la statue de Gill, qui deborde a gauche (x -10), voyait
    # sa premiere tranche partir en 1014 -- hors champ, a l'autre bout -- et la suivante
    # rester en 86. Frederic : « GIL sprite absent a l'extremite gauche », la statue coupee
    # net sur sa capture. Les objets ne bouclent pas avec le plan : on garde donc l'objet
    # entier, au representant de x modulo 1024 le plus proche du milieu de la bande.
    gauche = o["x"] + decalage_x(o) + im["ancre"][0] + im["x0"] - ox
    gauche -= 1024 * int(round((gauche + _c * 8 - 512) / 1024.0))
    bx = gauche + col0 * 16
    by = (SOL - o["y"] + im["ancre"][1] + im["y0"] - oy) & 0x3FF
    y = 1024 - by - (ligs - 1) * 16
    etage = PREMIER_ETAGE + o["bande"]
    fam, z = famille_et_z(o)
    # LA BOUCLE SE MESURE, comme en 2I : une pose balayee (un regard) reste sur son image 0.
    boucle = 1 if (o.get("comportement") or o.get("force_boucle")
                      or est_une_boucle(o["images"])) else 0
    # LES CHAMPS DE COMPORTEMENT : les suites d'abord, le trajet ensuite. Un objet a
    # TRAJET qui n'a pas de suites garde ses durees de script (`NULL, NULL, 0`).
    suite = ""
    if o.get("comportement"):
        if o.get("pas"):
            suite = ", %d, %s_pas, %s_suites, %d" % (o["comportement"], prefixe, prefixe,
                                                     len(o["bornes"]) - 1)
        else:
            suite = ", %d, NULL, NULL, 0" % o["comportement"]
    if o.get("trajet"):
        # UNE INITIALISATION POSITIONNELLE EXIGE TOUT CE QUI PRECEDE -- 28/09/2026.
        # Jusqu'ici tous les objets a trajet avaient aussi un comportement, et le defaut ne
        # se voyait pas. Le punk au skate de Dudley 2, dont le trajet vient de son SCRIPT
        # (`trajet_du_script`), n'en a pas : son pointeur de trajet partait dans le champ
        # `comportement`. Meme regle que pour `echelle` et `boite`, trois lignes plus bas.
        if not o.get("comportement"):
            suite += ", 0, NULL, NULL, 0"
        # LE TRAJET NE BOUCLE PAS TOUJOURS : `fin` eteint l'objet apres son dernier
        # segment, comme l'etat 3 de l'oiseau d'Elena 1 (`objet[+1] = 0`).
        suite += ", %s_trajet, %d, %d" % (prefixe, len(o["trajet"]),
                                          1 if o.get("fin") else 0)
    # L'ECHELLE VIENT EN DERNIER, et une initialisation POSITIONNELLE exige que tout ce qui
    # la precede soit ecrit : un objet qui retrecit sans comportement ni trajet doit donc
    # recevoir leurs valeurs neutres. La caleche a les deux, mais la regle doit tenir seule.
    if o.get("echelle"):
        if not o.get("comportement"):
            suite += ", 0, NULL, NULL, 0"
        if not o.get("trajet"):
            suite += ", NULL, 0, 0"
        suite += ", %d, %d, %d, %d" % (o["echelle"], o.get("echelle_pas", 0),
                                       o.get("echelle_seg", -1), col0 * 16)
    # LA BOITE DE RUPTURE, mise dans le repere de la fiche -- voir `animer2i.fiche`, meme
    # calcul. Elle vient en dernier, donc tout ce qui la precede doit etre ecrit.
    if o.get("boite"):
        bo = o["boite"]
        bo_x = gauche - (im["ancre"][0] + im["x0"] - ox) + bo[0]
        bo_y = 1024 - ((SOL - o["y"] - bo[2]) & 0x3FF)
        if not o.get("comportement"):
            suite += ", 0, NULL, NULL, 0"
        if not o.get("trajet"):
            suite += ", NULL, 0, 0"
        if not o.get("echelle"):
            suite += ", 0, 0, 0, 0"
        suite += ", { %d, %d, %d, %d }" % (bo_x, bo[1], bo_y, bo[3])
    # LE DEPART DE BOUCLE VIENT APRES TOUT LE RESTE -- meme regle positionnelle. Il n'est
    # ecrit que par les trois objets dont le script finit sur un `0x02`.
    if o.get("depart_boucle"):
        if not o.get("comportement"):
            suite += ", 0, NULL, NULL, 0"
        if not o.get("trajet"):
            suite += ", NULL, 0, 0"
        if not o.get("echelle"):
            suite += ", 0, 0, 0, 0"
        if not o.get("boite"):
            suite += ", { 0, 0, 0, 0 }"
        suite += ", %d" % o["depart_boucle"]
    return ('    { "ng%02x", %d, %d, %d, %d, %d, %s_tuiles, %s_durees, %s_palette, '
            '%d, %d, %d, %d, %d, %d, 0x%X, 0x%X%s },  /* %s, element %d,%d, script %d, plan %s, %s%s */'
            % (o["bande"], etage, nb_images, nb_tuiles, cols, ligs,
               prefixe, prefixe, prefixe, num, bx, y, fam, z, boucle, o.get("variante", 0xF),
               o.get("aires", 0), suite, o["adresse"], o["x"], o["y"], o["script"], o["plan"], o.get("source", ""),
               "" if boucle else ", POSE BALAYEE, figee"))


DATA = r"C:\Temp3sx\src\port\video\decor_objets_data.c"


def ecrire(blocs, fiches, par_bande):
    """Ajoute les objets de NG au C que `animer2i.py` vient d'ecrire.

    L'ORDRE DES DEUX OUTILS COMPTE : `animer2i.py --ecrire` d'abord, qui refait le fichier
    en entier, puis `animerng.py --ecrire`, qui y ajoute New Generation. Relancer `animer2i`
    seul efface donc les objets de NG -- c'est voulu et c'est le prix d'un seul tableau
    pour les deux jeux, plutot qu'un second tableau et une recherche a deux entrees dans
    `decor_objets.c`.
    """
    s = io.open(DATA, encoding="utf-8", errors="surrogateescape").read()

    # ON RETIRE D'ABORD CE QU'ON A DEJA POSE. `animer2i.py --ecrire` refait le tableau des
    # fiches mais CONSERVE les blocs de tuiles qu'il ne connait pas : les notres survivaient
    # a chaque passage, et on en empilait une copie de plus a chaque fois -- clang refusait
    # sur `redefinition of n00o0_i0_0_0` apres trois tours. On nettoie donc au prefixe.
    lignes = s.splitlines(True)
    garde = []
    dans_table = False

    for l in lignes:
        if dans_table:
            if l.startswith("};"):
                dans_table = False
            continue

        # LE `m\d+` DES MORCEAUX MANQUAIT, ET LE NETTOYAGE LES LAISSAIT PASSER.
        # Le motif s'arretait a `n\d+o\d+_`, donc `n00o6m1_i0_5_4` n'etait pas reconnu :
        # relancer `animerng --ecrire` sans repasser par `animer2i` en empilait une
        # seconde copie, et clang tombait sur « redefinition of n00o6m1_tuiles ».
        # Vu le 05/09/2026, apres que le build a echoue pour cette raison exacte.
        if re.match(r"static const \w[\w ]* n\d+(o\d+(m\d+)?(p\d+)?|q\d*(m\d+)?)_", l):
            # les tables `_tuiles` s'etendent sur plusieurs lignes, les autres non
            dans_table = l.rstrip().endswith("{")
            continue

        if "NEW GENERATION -- genere" in l or re.match(r'\s*\{ "ng[0-9a-f]{2}",', l):
            continue

        garde.append(l)

    s = "".join(garde)

    tete = s.index("const DecorAnimation decor_animations[]")
    fin_tab = s.index("\n};", tete)
    n2i = s[tete:fin_tab].count('{ "')

    # LA VIRGULE SE MET APRES L'ACCOLADE, PAS APRES LE COMMENTAIRE. La derniere fiche de
    # 2nd Impact se termine par `},  /* element.y 208 */` : ajouter une virgule a la fin
    # de la ligne donnait `*/,`, soit un element vide de plus dans le tableau, et clang
    # refusait. On la glisse donc juste apres la derniere accolade fermante.
    corps = s[tete:fin_tab].rstrip()

    # `animer2i` termine la derniere fiche conservee par `},  /* element.y 208 */,`. La
    # virgule finale est inoffensive quand c'est le dernier element du tableau -- C tolere
    # la virgule pendante -- mais des qu'une fiche suit, elle declare un ELEMENT VIDE entre
    # les deux virgules, et clang s'arrete sur « expected expression ». On la retire :
    # l'element est deja termine par la virgule qui suit son accolade.
    corps = re.sub(r"(\*/)\s*,\s*$", r"\1", corps)

    k = corps.rfind("}")

    if k >= 0 and "," not in corps[k + 1:]:
        corps = corps[:k + 1] + "," + corps[k + 1:]

    nouveau = (s[:tete] + "\n".join(blocs) + "\n\n" + corps + "\n"
               + "    /* NEW GENERATION -- genere par outils/animerng.py */\n"
               + "\n".join(fiches) + s[fin_tab:])

    # LES DEUX INDEX SE LISENT DANS LES FICHES, ILS NE SE DEDUISENT PAS DE L'ORDRE
    # DE GENERATION — 01/09/2026.
    #
    # Ils se calculaient `for bande in sorted(par_bande)`, c'est-a-dire dans l'ordre
    # croissant des BANDES, alors que les fiches sont posees dans l'ordre des DECORS. Or
    # les deux ne coincident pas : le decor 11 porte la bande 4, le decor 12 la bande 2, et
    # ils sont generes en dernier. `decor_anim_par_etage` designait donc les fiches d'un
    # AUTRE etage a partir du 39 — onze etages sur treize.
    #
    # C'est ce que Frederic a vu : « decor d'Oro NG avec les sprites du decor de Ryu ». Le
    # jeu affichait exactement ce qu'on lui demandait.
    #
    # On lit maintenant l'etage DANS chaque fiche : une seule source, qui ne peut plus se
    # desynchroniser de l'ordre d'ecriture.
    m = re.search(r'const DecorAnimation decor_animations\[\]\s*=\s*\{(.*?)\n\};',
                  nouveau, re.S)
    etages_des_fiches = [int(x.group(1)) for x in
                         re.finditer(r'^\s*\{ "[a-z0-9]+", (\d+),', m.group(1), re.M)]

    prem = [-1] * 58
    nb = [0] * 58

    for i, e in enumerate(etages_des_fiches):
        if prem[e] == -1:
            prem[e] = i
        nb[e] += 1

    # Un etage dont les fiches ne se suivent pas casserait l'index, qui n'est qu'un debut
    # et un compte. On le DIT au lieu de produire un C faux en silence.
    for e in range(58):
        if nb[e] and etages_des_fiches[prem[e]:prem[e] + nb[e]] != [e] * nb[e]:
            raise SystemExit("etage %d : ses %d fiches ne sont pas contigues" % (e, nb[e]))

    r = len(etages_des_fiches)

    nouveau = re.sub(r'(const short decor_anim_par_etage\[58\] = \{)[^}]*\}',
                     lambda m: m.group(1) + " " + ", ".join(str(v) for v in prem) + " }",
                     nouveau)
    nouveau = re.sub(r'(const short decor_nb_par_etage\[58\] = \{)[^}]*\}',
                     lambda m: m.group(1) + " " + ", ".join(str(v) for v in nb) + " }",
                     nouveau)
    nouveau = re.sub(r'const int decor_nb_animations = \d+;',
                     'const int decor_nb_animations = %d;' % r, nouveau)
    io.open(DATA, "w", encoding="utf-8", errors="surrogateescape").write(nouveau)
    return n2i, r


def travail_bande(bande, sp):
    """TOUT ce qu'une bande produit : ses blocs, ses fiches, ses pages gardees.

    SORTI DE `main` LE 25/09/2026 POUR ETRE MIS EN CACHE (`cache_decors.py`). Rien ici ne
    depend d'une autre bande : le budget de motifs repart de zero a chaque bande
    (`budget_pages(..., (0, 0, 0))`) et les prefixes des blocs portent deja son numero.

    Les lignes que `bloc_c` et `groupes_palette` impriment en passant -- « 69 couleurs
    ramenees a 63 » -- ne sont pas rejouees quand la bande vient du cache. Ce qui DECIDE
    quelque chose, lui, est rendu dans `refus` et reimprime a chaque passage.
    """
    obj, nom, _inconnus = objets(bande, sp)
    pages = PG.pour_bande(bande)

    if not obj and not pages:
        return dict(nom=nom, blocs=[], fiches=[], n=0, cases=0, refus=[], gardees=[])

    blocs, fiches, refus = [], [], []
    cases, n = 0, 0

    # LES ANIMATIONS DE PAGES D'ABORD (rang 0), puis les objets, puis ce qui reste
    # pour les animations de rang 1 (le vent d'Ibuki, l'horizon de Gill).
    p0, refus0, pris = budget_pages([p for p in pages if p["rang"] == 0], (0, 0, 0))
    gardes, refuses, pris = budget(obj, pris)
    p1, refus1, pris = budget_pages([p for p in pages if p["rang"] > 0], pris)

    for p in refus0 + refus1:
        refus.append("   BUDGET : page animee laissee de cote : %s (%d rangs, %d morceaux)"
                     % (p["quoi"], p["rangs"], p["cout"]))

    for o, refus_rangs, refus_cases in refuses:
        refus.append("   BUDGET : script %d laisse de cote (%d rangs, %d morceaux)"
                     % (o["script"], refus_rangs, refus_cases))

    for k, (o, tranches) in enumerate(gardes):
        for m, (col0, ncols) in enumerate(tranches):
            groupes = groupes_palette(o, col0, ncols)
            for g, garder in enumerate(groupes):
                prefixe = ("n%02do%d" % (bande, k)
                           + ("m%d" % m if m or col0 else "")
                           + ("p%d" % g if len(groupes) > 1 else ""))
                r = bloc_c(o, prefixe, col0, ncols, garder)

                if r is None:
                    continue

                c, cols, ligs, ni, nt, num = r
                blocs.append(c)
                fiches.append(fiche(o, prefixe, cols, ligs, ni, nt, num, col0))
                cases += cols * ligs
                n += 1

    tuiles = PG.Tuiles("n%02dq" % bande)
    for q, p in enumerate(p0 + p1):
        for m, morceau in enumerate(p["morceaux"]):
            c, f = PG.bloc_c(p, "n%02dq%dm%d" % (bande, q, m), tuiles, morceau)
            blocs.append(c)
            fiches.append(f)
            n += 1
    if tuiles.lignes:
        blocs.insert(len(blocs) - sum(len(p["morceaux"]) for p in p0 + p1),
                     "\n".join(tuiles.lignes) + "\n")

    return dict(nom=nom, blocs=blocs, fiches=fiches, n=n, cases=cases,
                refus=refus, gardees=PG.reduire_gardees(p0 + p1))


def main():
    import cache_decors as CA
    import objetsng as ON

    sp = ANG.spans()
    blocs, fiches, par_bande = [], [], {}
    non_lus = []
    gardees = []
    venus_du_cache = 0

    print("bande  nom             asset                  objets  cases  d'ou")
    for bande in range(19):
        # LA CLE D'UNE BANDE : l'empreinte des outils, plus CE QU'ELLE CONSOMME.
        # `enregistrements` coute une demi-seconde ; c'est le prix d'une cle honnete,
        # et c'est lui qui permet de corriger `objetsng.py` sans refaire les dix-huit
        # autres bandes. Les `inconnus` en sortent aussi, on n'a donc pas a les ranger.
        enregs, inconnus = ON.enregistrements(bande)
        non_lus.extend((bande,) + tuple(i) for i in inconnus)

        c = CA.cle("ng", bande, CA.signature_enregistrements(enregs))
        v = CA.lire(c)
        dou = "cache"

        if v is None:
            v = travail_bande(bande, sp)
            CA.ecrire(c, v)
            dou = "calcule"
        else:
            venus_du_cache += 1

        for l in v["refus"]:
            print(l)

        blocs.extend(v["blocs"])
        fiches.extend(v["fiches"])
        gardees.extend(v["gardees"])

        if v["n"]:
            par_bande[bande] = v["n"]

        if not v["n"] and not v["blocs"]:
            print("  %2d   %-22s %s" % (bande, v["nom"] or "-", "aucun"))
            continue

        print("  %2d   %-22s %4d   %4d   %s"
              % (bande, v["nom"], v["n"], v["cases"], dou))

    print()
    print("%d objets animes sur %d bandes (%d bandes venues du cache sur 19)"
          % (sum(par_bande.values()), len(par_bande), venus_du_cache))
    print("\nOBJETS A VALEURS EN DUR NON ENCORE LUS (a faire, decor par decor) :")
    for b, site, cible, arg, zs, imm in non_lus:
        print("   bande %2d  %08X -> %08X r4=%s z %s %s" % (b, site, cible, arg, zs, imm))

    if "--ecrire" not in sys.argv:
        print("Rien n'a ete ecrit. `--ecrire` pour les ajouter au C.")
        return 0

    PG.ecrire_gardees_reduites(gardees)
    n2i, tot = ecrire(blocs, fiches, par_bande)
    print("ajoutes a decor_objets_data.c : %d fiches de 2I + %d de NG = %d"
          % (n2i, tot - n2i, tot))
    return 0


if __name__ == "__main__":
    sys.exit(main())
