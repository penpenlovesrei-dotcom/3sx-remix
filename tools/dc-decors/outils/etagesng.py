# -*- coding: utf-8 -*-
"""Les dix-neuf etages de New Generation, ajoutes a 3rd Strike apres ceux de 2nd Impact.

Meme modele que `etages.py`, avec ce qui change :

* les coefficients de parallaxe sont en **`0x8C189BA0`**, pas `0x20`, et la table est
  indexee par la **BANDE** -- en 2I c'est `0x8C1D4F48`, indexee par le decor ;
* il y a **19 bandes** (`bg_set00` .. `bg_set12`), et une vingtieme (`bg_set13`) qui n'a
  ni script ni element : on ne la monte pas ;
* les etages vont de **37 a 55**, les archives de **1550 a 1568**.

LE NOMBRE DE PLANS SE LIT DANS LE BINAIRE, PAS DANS LES IMAGES. Le compte de demi-banques
non vides ne le donne pas : la bande 15 en a quatre pour deux objets, la bande 14 une pour
deux. C'est le nombre d'objets de parallaxe non nuls qui fait foi -- la table est
confirmee par son appelant (`0x8C088260` la charge, `0x8C088282` l'indexe par la bande).

LA REGLE D'AFFECTATION, reprise de 2I et verifiee sur Oro :

    la demi-banque d'ordre k porte l'objet k   (b0 haut -> 0, b0 bas -> 1, b1 haut -> 2)
    le plan le plus LOINTAIN est celui de plus petit coefficient

Sur `bg0a` : objet 2 a 0,5 est le fond, objet 0 a 0,75 le plan intermediaire, objet 1 a
1,0 le proche -- exactement ce que `couches2i.COUCHES` porte a la main.
"""

import io
import os
import struct
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
sys.path.insert(0, ICI)

import archive

BIN = open(os.path.join(RACINE, "SF3_1ST.BIN"), "rb").read()
BASE = 0x8C010000
TABLE_COEF = 0x8C189BA0
PAS_COEF = 0x20

# LES BANDES SONT NOMMEES DANS LE BINAIRE, table `0x8C1B7E98`, entrees de 12 octets,
# indexee par la bande. Rien n'a ete cale dessus : elles ont ete trouvees APRES coup, et
# elles recoupent tout ce qui avait ete etabli autrement.
#
# En particulier elles expliquent pourquoi les decors 2 et 11 emettaient la meme sequence
# de blocs -- ce sont Ryu et Ken, qui partagent le stage du Japon avec les bandes
# inversees -- et pourquoi les decors 3 et 10 faisaient de meme : Yun et Yang, Hong Kong.
# La bande 19 s'appelle `SELECT` : c'est l'ecran de selection, d'ou le decor 13 vide.
NOMS = {
    0: "H.S.(GILL)", 1: "N.Y.(ALEX)", 2: "N.Y.(SEAN)", 3: "JAPAN(RYU)",
    4: "JAPAN(KEN)", 5: "H.K.(YUN1)", 6: "H.K.(YUN2)", 7: "LOND(DUD1)",
    8: "LOND(DUD2)", 9: "MOSC(NECR)", 10: "MUN (HUGO)", 11: "JAP(IBUK1)",
    12: "JAP(IBUK2)", 13: "JAP(IBUK3)", 14: "NAI(ELEN1)", 15: "NAI(ELEN2)",
    16: "AMAZO(ORO)", 17: "H.K (YAN1)", 18: "H.K (YAN2)", 19: "SELECT",
}

# Les ressources que le lanceur recopie. Le meme dossier que `couchesng.RESSOURCES`.
RESSOURCES = r"C:\Users\frede\OneDrive\Bureau\SEPTEMBRE\SF3\CrowdedStreet-3SX\resources"

PREMIER_ETAGE = 37
PREMIER_FICHIER = 1550
PAGES_PAR_PLAN = 32
NB_BANDES = 19

# Le z de chaque plan : un octet, et un z PLUS GRAND est plus LOIN.
#
# LU DANS SF3_1ST.BIN, PLUS CHOISI -- 16/09/2026. La meme mecanique qu'en 2nd Impact
# (`etages.TABLE_COUCHES`), retrouvee par les octets de ses routines :
#
#     constructeur de couches   2I 0x8C10B070   NG 0x8C146714   (memes octets)
#     insertion triee           2I 0x8C10A2D2   NG 0x8C145976   (memes octets)
#     table des couches         2I 0x8C601EE8   NG 0x8C4DDBA4, en .bss : son image est
#                                               decalee de 0x12420 -> 0x8C4CB784
#
# lue par l'initialisation des plans `0x8C088200` : `table[bande*16 + k*4]`, bande en +74.
# Chaque couche est `[plan, PROFONDEUR, (3 mots par bande)..., -1]`, et la couche k dessine
# la demi-banque k. Les valeurs different de celles de 2I sur plusieurs bandes : Sean
# 114/94, Yun 1 et Yang 1 104/94/114, Yun 2 et Yang 2 114/104, Dudley 2 104/84 -- et
# **la couche 0 de Dudley 1, la pluie de Londres, est a 20 : DEVANT les combattants**.
#
# Les 94/84/90 d'avant etaient ceux de 2I recopies, et le 90 du troisieme plan une valeur
# a l'oeil.
Z_LOIN, Z_TIERS, Z_QUATRE, Z_PROCHE = 0x5E, 0x5A, 0x5C, 0x54
TABLE_COUCHES = 0x8C4DDBA4
DECALAGE_BSS = 0x12420


# LES TROIS AIRES D'UN DECOR, LUES DANS LE BINAIRE -- 26/09/2026.
#
# `0x8C088046` : `bande = u16[0x8C18A804 + decor * 6 + aire * 2]`. Six octets par decor,
# trois aires de deux. Treize decors, et sept d'entre eux changent de bande entre les
# manches :
#
#     decor  aire 0   aire 1   aire 2
#       2    e40 RYU  e41 KEN  e41 KEN      le stage du Japon bascule sur l'autre
#       3    e42      e43      e43          Yun
#       4    e44      e45      e45          DUDLEY
#       7    e48      e49      e50          IBUKI, la seule a trois bandes distinctes
#       8    e51      e52      e52          ELENA
#      10    e55      e54      e54          Yang -- il COMMENCE par Yang 2
#      11    e41 KEN  e40 RYU  e40 RYU      l'autre sens du stage du Japon
#
# Les six autres (Gill, Alex, Necro, Hugo, Oro, Sean) gardent leur bande aux trois aires.
#
# ON N'EN OUVRE QUE TROIS. Frederic a demande Ibuki, puis Dudley, puis Elena. Ryu/Ken, Yun
# et Yang sont lus et ecrits ici, mais laisses fermes tant qu'il ne les a pas demandes --
# la bascule Ryu/Ken change le decor de fond en fond, et Yang ferait commencer le match sur
# sa seconde bande.
TABLE_AIRES = 0x8C18A804
DECORS_OUVERTS = {2, 3, 4, 7, 8, 10, 11}   # les SEPT : Ryu, Yun, Dudley, Ibuki,
#                                           Elena, Yang, Ken. Frederic, le 26/09 :
#                                           « oui on traite aussi Ryu/Ken, Yun et Yang ».


def bandes_du_decor(decor):
    """Les trois bandes d'un decor, aire par aire."""
    return tuple(struct.unpack_from("<H", BIN, TABLE_AIRES + decor * 6 + a * 2 - BASE)[0]
                 for a in range(3))


def aires_de_letage(etage):
    """Les trois etages qu'un etage d'ENTREE enchaine, ou None s'il n'en a qu'un.

    Un etage d'entree est celui de l'aire 0 d'un decor ouvert. Les autres -- l'etage 45
    de Dudley, le 52 d'Elena -- gardent leur propre aire, fixe : on peut donc encore les
    choisir tels quels sans que rien ne bouge."""
    for decor in sorted(DECORS_OUVERTS):
        b = bandes_du_decor(decor)

        if max(b) >= NB_BANDES:
            continue

        etages = tuple(PREMIER_ETAGE + x for x in b)

        if etages[0] == etage and len(set(etages)) > 1:
            return etages

    return None


def couches_ng(bande):
    """[(plan de NG, profondeur) ou None] pour les couches k = 0..3 d'une bande."""
    out = []
    for k in range(4):
        ptr = u32(TABLE_COUCHES - DECALAGE_BSS + bande * 16 + k * 4)
        if not (BASE <= ptr < BASE + len(BIN)):
            out.append(None)
            continue
        plan, prio = struct.unpack_from("<hh", BIN, ptr - BASE)
        out.append(None if plan == -1 else (plan & 7, prio))
    return out


def profondeur_liste(bande, banque, moitie, defaut):
    """La profondeur de la couche qui dessine (banque, moitie), ou `defaut` s'il n'y en a
    pas -- une demi-banque sans couche est une reserve, et on le signale."""
    k = banque * 2 + (1 if moitie == "bas" else 0)
    c = couches_ng(bande)[k]
    if c is None:
        print("   bande %d : la demi-banque %d n'a pas de couche (reserve ?)" % (bande, k))
        return defaut
    return c[1]

# Les demi-banques, dans l'ordre du fichier : c'est l'ordre des objets.
DEMIS = [(0, "haut"), (0, "bas"), (1, "haut"), (1, "bas")]


def u32(a):
    return struct.unpack_from("<I", BIN, a - BASE)[0]


def coefs(bande, k):
    """(coef_x, coef_y) de l'objet `k` de la bande, en 16.16."""
    a = TABLE_COEF + bande * PAS_COEF + k * 8
    return u32(a), u32(a + 4)


_pleines = {}


def demis_pleines(bande):
    """Quelles demi-banques de la bande portent quelque chose. Mesure, mise en cache."""
    if bande in _pleines:
        return _pleines[bande]

    import bande3sx
    import pvc
    from rendupvc import SIDE, carte_morton

    src = os.path.join(RACINE, "pvc-ng", "bg_set%02x.pvc" % bande)
    pages, _u, _ = pvc.decode(open(src, "rb").read())
    m = carte_morton(SIDE)
    ok = set()

    for k, (banque, moitie) in enumerate(DEMIS):
        arr = bande3sx.banque_rgba(pages, banque * 4096, m)[0]
        demi = arr[:512] if moitie == "haut" else arr[512:]
        if (demi[:, :, 3] > 0).mean() > 0.005:
            ok.add(k)

    _pleines[bande] = ok
    return ok


def objets(bande):
    """Les objets non nuls de la bande QUI ONT DES PIXELS, dans l'ordre.

    Le compte d'objets de parallaxe ne suffit pas : `bg_set01` en declare trois alors que
    sa troisieme demi-banque est vide, et on lui posait une couche de zero pixel. On ne
    garde donc que les objets dont la demi-banque porte quelque chose -- mais jamais moins
    de deux, le moteur en attendant au moins deux plans.
    """
    out = []
    for k in range(3):
        cx, cy = coefs(bande, k)
        if (cx, cy) != (0, 0):
            out.append((k, cx, cy))

    # LA COUCHE QUE LES LISTES DESSINENT COMPTE AUSSI -- 17/09/2026. Le troisieme objet
    # d'Alex (0,625, profondeur 104) n'a pas de demi-banque a lui : `descripteursng` montre
    # que le Dreamcast le peint avec le quart haut droit de la banque 0 -- le ciel du fond,
    # que Frederic voyait manquer (« ALEX arriere plan a revoir »).
    import descripteursng
    decrites = {k for k in descripteursng.couches_decrites(bande)
                if k < 4 and couches_ng(bande)[k] is not None}
    pleines = demis_pleines(bande)
    garde = [o for o in out if o[0] in pleines or o[0] in decrites]
    return garde if len(garde) >= 2 else out[:2]


def fiche(bande):
    """Tout ce qu'il faut savoir d'un etage de NG."""
    obj = objets(bande)
    n = len(obj)

    # Du plus lointain au plus proche : le plus petit coefficient d'abord, le rang de
    # l'objet pour departager. On prend le PREMIER et le DERNIER, et ce qui reste au
    # milieu -- ainsi il y a toujours exactement n-2 plans supplementaires, meme quand
    # les trois coefficients sont egaux (la bande 9 les a tous a 1/1, et chercher « celui
    # qui vaut 1/1 » y retombait sur le lointain, d'ou deux plans du milieu).
    #
    # A COEFFICIENT EGAL, LA PROFONDEUR DEPARTAGE -- 17/09/2026. Necro (bande 9) : sa routine
    # du plan 2 (`0x8C08A970`, table `0x8C18AE70`) recule de 5 pixels par trame, comme
    # `0x8C0DD0E8` en 2I -- ce sont les montagnes, couche 2, profondeur 104. Le rang les
    # mettait sur le plan de BASE, qui suit la camera et ne peut pas defiler seul : Frederic,
    # « NECRO pas de scrolling ». Parmi les plus rapides, le plan de BASE est celui dont la
    # profondeur est la plus proche de 84 (Z_PROCHE) -- pas la pluie de Dudley 1 (20), qui a
    # le meme coefficient que la rue ; parmi les plus lents, le LOINTAIN est le plus profond.
    cn = couches_ng(bande)
    prof = lambda k: cn[k][1] if k < 4 and cn[k] else Z_PROCHE
    ordre = sorted(obj, key=lambda o: (o[1], o[2], o[0]))
    vite = [o for o in obj if o[1:] == ordre[-1][1:]]
    proche = min(vite, key=lambda o: (abs(prof(o[0]) - Z_PROCHE), o[0]))
    lents = [o for o in obj if o[1:] == ordre[0][1:] and o is not proche]
    loin = max(lents, key=lambda o: (prof(o[0]), -o[0])) if lents else ordre[0]
    milieu = [o for o in ordre if o is not loin and o is not proche]

    # UNE BANDE QUI N'A QU'UNE DEMI-BANQUE REMPLIE la met sur le PLAN DE BASE.
    # `bg_set0e` est dans ce cas : une seule demi-banque pour deux objets. La poser sur le
    # fond laissait le plan proche vide -- or c'est lui que le moteur dessine toujours et
    # sur lequel reposent le sol et les combattants. On echange donc les deux demi-banques
    # sans toucher aux coefficients. C'est le seul endroit ou la regle « demi-banque k =
    # objet k » est mise de cote, et c'est pour un cas degenere.
    #
    # RETIRE LE 17/09/2026 : LE CODE DIT LE CONTRAIRE. `descripteursng` montre que le
    # Dreamcast ne dessine que la couche 0 de la bande 14, avec le coefficient de l'objet 0
    # (0,0625) : c'est un CIEL LENT, comme dans la variante du pont de 2I dont Elena 1 est la
    # copie. Le sol et les combattants reposent sur des OBJETS du plan 2 (le pont, les
    # falaises, les arbres) ; l'echange les faisait defiler a 0,0625 et le ciel a 1,00.
    # Frederic : « ELENA 1 affichage uniquement de l'arriere-plan ».
    pleines = demis_pleines(bande)
    ECHANGE = False
    if ECHANGE and loin[0] in pleines and proche[0] not in pleines:
        loin, proche = (proche[0], loin[1], loin[2]), (loin[0], proche[1], proche[2])

    couches = {132: DEMIS[loin[0]] + (loin[0],),
               196: DEMIS[proche[0]] + (proche[0],),
               **({260: DEMIS[milieu[0][0]] + (milieu[0][0],)} if milieu else {})}

    # Chaque plan prend la profondeur de la couche de NG qui dessine SA demi-banque.
    z = [profondeur_liste(bande, *couches[132][:2], defaut=Z_LOIN),
         profondeur_liste(bande, *couches[196][:2], defaut=Z_PROCHE)]
    if 260 in couches:
        z.append(profondeur_liste(bande, *couches[260][:2], defaut=Z_TIERS))

    return dict(
        bande=bande,
        etage=PREMIER_ETAGE + bande,
        fichier=PREMIER_FICHIER + bande,
        n=n,
        coef0=(loin[1], loin[2]),
        vitesses=[(o[1], o[2]) for o in milieu],
        z=z,
        # liste -> (banque, moitie, objet) comme `couches2i.COUCHES`
        couches=couches,
    )


def mot_priorite(f):
    """`stage_priority` : un octet par plan, du plan 0 (poids fort) au plan 3."""
    o = list(f["z"]) + [0] * (4 - len(f["z"]))
    return (o[0] << 24) | (o[1] << 16) | (o[2] << 8) | o[3]


def ecrire_include(fiches, sortie):
    L = []
    L.append("/* Genere par dc-decors/outils/etagesng.py -- ne pas modifier a la main.")
    L.append(" *")
    L.append(" * Les dix-neuf etages de New Generation, ajoutes apres les quinze de 2nd")
    L.append(" * Impact. Etages 37 a 55, archives 1550 a 1568.")
    L.append(" *")
    L.append(" * Les coefficients viennent du binaire de New Generation : table 0x8C189BA0,")
    L.append(" * pas 0x20, indexee par la BANDE (et non par le decor comme en 2I).")
    L.append(" *")
    L.append(" * Le nombre de plans est le nombre d'objets de parallaxe non nuls, pas le")
    L.append(" * compte de demi-banques non vides -- la bande 15 en a quatre pour deux")
    L.append(" * objets, la bande 14 une pour deux. */")
    L.append("")
    L.append("#define ETAGESNG_USE_SCR \\")
    L.append("    " + ", ".join(str(f["n"]) for f in fiches))
    L.append("")
    L.append("#define ETAGESNG_BGW_NUMBER \\")
    L.append("    " + ", ".join("{ %s }" % ", ".join(str(k + 1) for k in range(f["n"]))
                                for f in fiches))
    L.append("")
    L.append("#define ETAGESNG_PRIORITY \\")
    L.append("    " + ", ".join("0x%08X" % mot_priorite(f) for f in fiches))
    L.append("")
    L.append("#define ETAGESNG_GBIX \\")
    L.append("    " + ", ".join("{ %s }" % ", ".join(["0xFFFFFFFF"] * f["n"]) for f in fiches))
    L.append("")
    for quoi, idx in (("X", 0), ("Y", 1)):
        L.append("#define ETAGESNG_SPEED_%s_LOIN \\" % quoi)
        L.append("    " + ", ".join("[%d] = 0x%X" % (f["etage"], f["coef0"][idx])
                                    for f in fiches))
        L.append("")
    for quoi, idx in (("X", 0), ("Y", 1)):
        ent = ["[%d] = 0x%X" % (f["etage"], f["vitesses"][0][idx])
               for f in fiches if f["vitesses"]]
        L.append("#define ETAGESNG_SPEED_%s_TIERS \\" % quoi)
        L.append("    " + (", ".join(ent) if ent else "[37] = 0"))
        L.append("")

    # LES TABLES OU LE ZERO N'EST PAS UN DEFAUT SUR. Le C complete a zero ce qu'on
    # n'initialise pas, ce qui convient a la plupart des tables d'etage -- mais pas a
    # celles-ci : un `bgrw_on` a zero designerait l'entree 0 de `bgrw_data_tbl` au lieu de
    # dire « aucune animation de page », un `limit_tbl3` a zero collerait la camera a
    # l'origine, un `mts_OB_page` a zero donnerait un cache de taille nulle, et un
    # `bg_index_tbl` a zero renverrait tous les etages sur le fond de Gill.
    # LES AIRES D'UN MEME DECOR -- 26/09/2026.
    #
    # Ibuki n'a pas trois decors : elle a UN decor et TROIS AIRES, et le Dreamcast les fait
    # avancer entre les manches. C'est `0x8C03AE20`, l'etat 4 de la machine de deroulement
    # du match (table `0x8C15BE18`) :
    #
    #     u8[contexte + 5] += 1      plafonne a 2
    #     puis 0x8C085F28, dont l'etat 0 remonte l'etage
    #
    # et son chargeur `0x8C1172B8` recharge la bande, parce qu'il n'en garde qu'UNE a la
    # fois (`0x8C612E70`) : il court-circuite quand c'est deja la bonne, sinon il charge.
    #
    # Le port en avait fait trois etages separes, chacun avec `{ n, n, n }` -- l'aire ne
    # servait a rien. On rend donc au premier ses trois aires. Les etages 49 et 50 restent
    # choisissables tels quels, une aire fixe chacun : rien de ce qui marche ne change.
    AIRES = {f["etage"]: t for f in fiches
             for t in [aires_de_letage(f["etage"])] if t}

    L.append("#define ETAGESNG_INDEX_TBL \\")
    L.append("    " + ", ".join("{ %d, %d, %d }" % AIRES.get(f["etage"],
                                                             (f["etage"],) * 3)
                                for f in fiches))
    L.append("")
    # LES BORNES SE MESURENT SUR LA PAGE -- 16/09/2026. Elles valaient 0x140..0x2c0 pour
    # les dix-neuf, soit 384 px de course, alors que quinze de ces etages peignent leur
    # bande entiere et en permettent 639. Frederic : « on ne peut pas aller au bout des
    # extremites droite et gauche du decor ». Voir `limites.py` : la regle se verifie sur
    # les quatre etages de 2nd Impact deja valides a l'ecran.
    import limites
    L.append("#define ETAGESNG_LIMIT \\")
    L.append("    " + ", ".join("{ %s }" % limites.trio(f["etage"]) for f in fiches))
    L.append("")
    L.append("#define ETAGESNG_MSP \\")
    L.append("    " + ", ".join(
        "{ { 0x%X, 0x%X }, { 0x10000, 0x10000 }, { 0x%X, 0x%X } }"
        % (f["coef0"][0], f["coef0"][1],
           f["vitesses"][0][0] if f["vitesses"] else 0,
           f["vitesses"][0][1] if f["vitesses"] else 0) for f in fiches))
    L.append("")
    L.append("#define ETAGESNG_OPAQUE \\")
    L.append("    " + ", ".join("0x80" for _f in fiches))
    L.append("")
    L.append("#define ETAGESNG_BGRW_ON \\")
    L.append("    " + ", ".join("{ -1, -1, -1, -1, -1, -1, -1, -1 }" for _f in fiches))
    L.append("")
    L.append("#define ETAGESNG_OB_PAGE \\")
    # HUIT PAGES DEPUIS LE 17/09/2026 -- `PatternMap.x16_map` (structs.h) en tient huit.
    # A quatre (1024 morceaux, l'ancien plafond dur) le budget d'`animerng` ecartait les
    # grands elements fixes : l'auvent de l'etal de Hong Kong (176 morceaux), les
    # personnages de Necro (988), des pieces d'Ibuki, d'Elena, de Dudley et de Gill.
    # Frederic les a vus manquer. Une page coute 65 Ko du tas ; les index de texture 80 a
    # 88 sont libres (les pages de decor commencent a 100).
    # DIX PAGES LE SOIR DU 17/09 : le pont et les cordes d'Elena 1 ecartaient une falaise.
    # Seize-pages en 80..89, la page de 32 en 90 -- toujours sous les pages de decor (100).
    L.append("    " + ", ".join("{ 10, 1 }" for _f in fiches))
    L.append("")
    L.append("#define ETAGESNG_AKE_BG_OFF \\")
    L.append("    " + ", ".join(str((1 << f["n"]) - 1) for f in fiches))
    L.append("")
    io.open(sortie, "w", encoding="utf-8").write("\n".join(L) + "\n")


# PAS DE PARALLAXE -- 26/09/2026, SUR OBSERVATION, CONTRE LA TABLE.
#
# Frederic : « *les decors DUDLEY 2I et NG n'ont pas de parallaxe dans le jeu original* ».
# Le pendant de `etages.SANS_PARALLAXE`, et le meme statut : un ECART, pas une lecture.
#
# CE QUE LA TABLE `0x8C189BA0` DIT, et il est lu :
#
#     bande  7 (etage 44)  obj0 1/1      obj1 1/1   obj2 0,75/1
#     bande  8 (etage 45)  obj0 0,75/1   obj1 1/1   obj2 absent
#
# La bande 7 met donc DEJA son objet 0 a 1/1 ; c'est son objet 2, a 0,75, que la regle
# « le plus lointain est le plus petit coefficient » envoie au plan lointain. La bande 8,
# elle, porte bien 0,75 a l'objet 0. Les deux aires de Dudley ne disent pas la meme chose,
# et aucune des deux ne dit zero. On pose zero sur son observation, pour les deux.
# ET L'ECART EST RETIRE -- 28/09/2026. Frederic : « DUDLEY remettre le paralaxe ».
# Meme decision que dans `etages.SANS_PARALLAXE` : les deux bandes reprennent les
# coefficients de `0x8C189BA0`. L'ensemble reste, vide, avec son histoire au-dessus.
SANS_PARALLAXE = set()


def main():
    fiches = [fiche(b) for b in range(NB_BANDES)]
    for f in fiches:
        if f["etage"] in SANS_PARALLAXE:
            f["coef0"] = (0x10000, 0x10000)
            f["vitesses"] = [(0x10000, 0x10000) for _ in f["vitesses"]]

    print("%-8s %-14s %-6s %-6s %-8s %-16s %s"
          % ("bande", "nom", "etage", "plans", "fichier", "loin", "plan supplementaire"))
    for f in fiches:
        v = "  ".join("%.4g / %.4g" % (x / 65536, y / 65536) for x, y in f["vitesses"])
        print("bg_set%02x %-14s %-6d %-6d %-8d %-16s %s"
              % (f["bande"], NOMS.get(f["bande"], "?"), f["etage"], f["n"], f["fichier"],
                 "%.4g / %.4g" % (f["coef0"][0] / 65536, f["coef0"][1] / 65536), v or "-"))

    if "--ecrire" not in sys.argv:
        print("\nRien n'a ete ecrit. `--ecrire` pour poser l'include et les archives.")
        return 0

    inc = "C:/Temp3sx/src/port/video/etagesng_plans.inc"
    ecrire_include(fiches, inc)
    print("\ninclude C ecrit : %s" % inc)

    # ON N'ECRIT PLUS DANS %APPDATA% -- 26/09/2026.
    #
    # C'est la regle de Frederic, et cet outil l'enfreignait depuis le debut : il posait
    # ses dix-neuf archives directement dans le dossier du jeu. Deux raisons de ne plus le
    # faire, et la seconde suffit :
    #
    #  1. un processus lance par l'agent ecrit dans le conteneur de l'application Claude,
    #     pas dans le vrai dossier : les fichiers n'arrivent jamais au jeu ;
    #  2. c'est au LANCEUR de recopier, parce que c'est lui que Frederic lance, et lui
    #     seul sait quand le jeu est ferme.
    #
    # Elles vont donc dans les ressources de SEPTEMBRE, comme les pages de `couchesng`,
    # et le lanceur les recopie deja (son robocopy sur le dossier `stages`).
    dossier = os.path.join(RESSOURCES, "stages")
    os.makedirs(dossier, exist_ok=True)
    for f in fiches:
        archive.ecrire(f["n"] * PAGES_PAR_PLAN,
                       os.path.join(dossier, "%d.bin" % f["fichier"]))
    print("%d archives ecrites dans %s" % (len(fiches), dossier))
    return 0


if __name__ == "__main__":
    sys.exit(main())
