# -*- coding: utf-8 -*-
"""Genere les tables C des quinze etages ajoutes, depuis les donnees de 2nd Impact.

Rien ici n'est saisi a la main : les coefficients de parallaxe viennent du binaire, et
l'affectation des plans de la liste d'affichage relevee dans `releves2/`.

LES COEFFICIENTS, DANS `SF3_2ND.BIN`
------------------------------------
* **Plans lointain et proche** : table `0x8C1D4F48`, pas `0x20`, indexee par le numero de
  decor. Premiere paire (u32 16.16) = `(coef_x, coef_y)` de l'objet 0, deuxieme = objet 1.
  Seize decors sur seize, et elle couvre `bg07`, `bg08` et `bg0f`, que les etats Flycast
  ne couvrent pas -- c'est ce qui rendra la meme lecture possible pour New Generation.
* **Plan supplementaire** : ecrit en dur par le script d'etage, motif
  `mov.l Rm,@(16,Rn)` / `mov.l Rm,@(20,Rn)`. Trois decors l'ecrasent.
* **Sinon** : le defaut `0,875 / 0,875`. `bg00` n'ecrit aucun `0xE000` dans son script,
  et les objets 4 et 6 portent la meme valeur dans les vingt et un etats -- ce sont des
  valeurs initialisees, pas des restes.

LES PLANS DE 3SX
----------------
    plan 0  bgw[0]  la moitie lointaine du .pvc      coefficient de l'objet 0
    plan 1  bgw[1]  la moitie proche + le plan 2      1,00, plan de base
    plan 2  bgw[2]  un plan de 2I sans place ailleurs son coefficient
    plan 3  bgw[3]  le second, s'il y en a un         son coefficient

Un plan de 2I dont le coefficient egale celui de l'objet 0 n'a pas besoin d'un plan a
lui : il va sur la moitie lointaine, contre le fond qui defile comme lui.

    python etages.py          ecrit l'include C et les archives
"""
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import archive
import sh4

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)

TABLE_COEF = 0x8C1D4F48   # objet 0 du decor 0
PAS_COEF = 0x20
# Les defauts, PAR OBJET : ils sont identiques dans les vingt et un etats releves, donc
# initialises et non residuels. L'objet 2 sert au premier plan supplementaire, l'objet 6
# au second (le plan 7 de 2I). Le 0,625 / 0,875 de l'objet 6 est celui qui a ete valide a
# l'ecran sur le petit obelisque de bg00.
DEFAUTS_OBJET = {
    2: (0xE000, 0xE000),   # 0,875  / 0,875
    4: (0xE000, 0x10000),  # 0,875  / 1
    6: (0xA000, 0xE000),   # 0,625  / 0,875
}

# etage 3SX -> decor de 2nd Impact, et son numero dans la table de coefficients
ETAGES = [
    (22, "bg00", 0x0), (23, "bg01", 0x1), (24, "bg02", 0x2), (25, "bg03", 0x3),
    (26, "bg04", 0x4), (27, "bg05", 0x5), (28, "bg06", 0x6), (29, "bg07", 0x7),
    (30, "bg09", 0x9), (31, "bg0a", 0xA), (32, "bg0b", 0xB), (33, "bg0c", 0xC),
    (34, "bg0d", 0xD), (35, "bg0e", 0xE), (36, "bg0f", 0xF),
]

# PAS DE PARALLAXE -- 26/09/2026, SUR OBSERVATION, CONTRE LA TABLE.
#
# Frederic : « *les decors DUDLEY 2I et NG n'ont pas de parallaxe dans le jeu original* ».
#
# CE QUE LE BINAIRE DIT, ET IL EST LU : `0x8C1D4F48 + 4*0x20` donne a `bg04` l'objet 0 a
# `0x0C000 / 0x0E000`, soit 0,75 / 0,875 -- exactement ce que le port applique. La table
# ne dit donc PAS zero parallaxe, et ce qui suit n'est pas une correction de lecture :
# c'est un ECART, pose sur son observation, et annonce comme tel.
#
# Ce qui rend l'ecart plausible sans le prouver : quatre decors -- bg04, bg06, bg0a et
# bg0f -- portent la MEME paire 0,75 / 0,875 a l'objet 0, la plus repandue de la table.
# Une valeur partagee par quatre decors ressemble a une valeur initialisee que leur script
# n'ecrase pas, comme les defauts deja constates aux objets 2, 4 et 6. Ce n'est pas
# prouve : le script d'etage de bg04 n'a pas ete desassemble.
# ET L'ECART EST RETIRE -- 28/09/2026. Frederic : « DUDLEY remettre le paralaxe ».
#
# C'etait un ecart pose sur son observation CONTRE trois lectures concordantes, et annonce
# comme tel. Il le reprend : la table reprend ses droits, `bg04` retrouve les 0,75 / 0,875
# lus en `0x8C1D4F48 + 4*0x20`. Le dictionnaire reste, vide -- c'est lui qui dit ou se
# poserait le prochain ecart, et le commentaire ci-dessus garde l'histoire.
SANS_PARALLAXE = {}

# Les ecrasements du coefficient de l'objet 2, releves par balayage du binaire :
# `mov.l Rm,@(16,Rn)` suivi de `mov.l Rm,@(20,Rn)`, litteraux pris dans le pool.
ECRASEMENTS = {
    "bg01": (0xD000, 0xE000),   # 0,8125 / 0,875   -- 0x8C0DC0BA, 0x8C0DF650
    "bg09": (0xC000, 0xC000),   # 0,75   / 0,75    -- 0x8C0DDF90, 0x8C0DE3D0, ...
    "bg0e": (0xC000, 0xE000),   # 0,75   / 0,875   -- 0x8C0DEE30, 0x8C0E0C96
}

# Les decors dont la BANDE porte plus de couches que le casting a deux plans n'en prend.
#
# `bg0a` (Oro) a trois demi-banques non vides -- la grotte du fond (banque 0 haut, 79810
# px), la grotte proche (banque 0 bas) et le couchant (banque 1 haut) -- et trois objets
# de fond dans la table des coefficients : 0,75 / 1,0 / 0,5. Le plus LENT est le plus
# LOIN, donc le couchant est l'objet **2** et non l'objet 0. La liste 132 le faisait
# defiler a la vitesse de l'objet 0, celle de la grotte du fond, et la grotte du fond
# n'etait expediee nulle part -- elle disparaissait derriere le couchant.
#
#   decor -> (objet du plan lointain, [objet de chaque plan supplementaire])
# Les pages, elles, sont ecrites par `outils/couches2i.py`.
# LES SIX DECORS A TROIS COUCHES, pas un seul -- corrige le 30/08/2026.
#
# `couches2i.py` releve les demi-banques non vides des deux banques du `.pvc` : six decors
# en portent trois. Seul `bg0a` etait declare ici, donc les cinq autres perdaient leur
# couche du MILIEU -- c'est le « decor mal assemble » vu sur Akuma.
#
#   (objet du plan lointain, [objets des plans supplementaires])
# Le plus lent est le plus loin : l'objet 2 tient le fond, l'objet 0 le milieu, et
# l'objet 1 (toujours a 1,0) le plan proche.
# `bg0f` n'y est PAS : sa troisieme demi-banque est un magasin d'images d'animation,
# pas une couche. Voir `couches2i.py`.
#
# `bg09` (Elena) N'Y EST PLUS -- 16/09/2026. La table des couches de 2I (`TABLE_COUCHES`)
# ne lui donne que deux couches : sa banque 1 haut n'est dessinee par aucune. C'est la
# RESERVE des neuf trames de la cascade (3 x 3 de 320x160), que l'animation de pages 0
# recopie dans le trou de sa couche du fond. La poser comme plan lointain montrait la
# mosaique dans ce trou. `bg06` (Hugo) est dans le meme cas -- sa banque 1 haut est la
# reserve des bateaux --, mais son plafond la cache et Frederic l'a valide : on n'y touche
# pas.
COUCHES_EN_PLUS = {
    "bg05": (2, [0]),
    "bg06": (2, [0]),
    "bg07": (2, [0]),
    "bg0a": (2, [0]),
}

# Le z de chaque plan : un octet, et un z PLUS GRAND est plus LOIN.
#
# LU DANS SF3_2ND.BIN, PLUS CHOISI -- 16/09/2026. Voir DECORS.md, section 11.
#
# 2I dessine son decor comme UNE liste triee par profondeur : couches, elements et objets.
# Chaque couche y entre avec SA profondeur, ecrite en clair dans le binaire :
#
#     TABLE_COUCHES = 0x8C601EE8    4 pointeurs par decor, un par couche k
#     couche k      = [plan, PROFONDEUR, (3 mots par morceau)..., -1], lue par
#                     0x8C10B070 et inseree dans la liste triee par 0x8C10A2D2
#
# et la couche k dessine la demi-banque k du .pvc : k = banque*2 + (1 si "bas").
# Valeurs : 94 et 84 pour presque tous, 104 pour la banque 1 haut, Yun 104/94/114,
# Yang 114/104, la variante d'Elena 94/120. Les 27 releves de la liste d'affichage les
# confirment toutes (outil `ordre2i.py`) -- ils ne servent que de controle.
#
# Les objets gardent leur profondeur de 2I, sans decalage : le +16 de la veille et le recul
# des cascades sont retires, ils compensaient des couches mal placees.
TABLE_COUCHES = 0x8C601EE8
Z_LOIN_DEFAUT, Z_PROCHE_DEFAUT = 0x5E, 0x54

# UNE COUCHE NE DESSINE PAS FORCEMENT TOUTE LA LARGEUR -- 24/09/2026.
#
# Frederic, trois fois : « les poteaux et la corde ne sont toujours pas sur le bon plan ».
# Le morceau d'une couche porte trois mots, et le PREMIER est un x de fin, par tranches de
# 128 pixels. Le releve des dix-sept decors le prouve :
#
#     decor  9 couche 1 : 8 morceaux, x_fin 127..1023   -> 1024 px, toute la bande
#     decor  8 couche 0 : 6 morceaux, 127..511 puis 895, 1023 -> avec un TROU
#     la plupart        : 4 morceaux, 127..511          -> 512 px seulement
#
# **Hugo est de ces derniers.** Sa couche proche (plan 2, profondeur 84) ne dessine que
# x 0..511. Or ses poteaux, ses cordes, ses gros tonneaux et son plancher sont a x 600..900.
#
# Ce qui les dessine est ecrit en clair dans son chargeur d'elements statiques :
#
#     element 0 : plan 2, x 512, y 144, PROFONDEUR 82, script 17
#     element 1 : plan 2, x 464, y  78, profondeur 76, script 4
#
# **82**, et le premier commence exactement la ou la couche s'arrete. Nos jets sont a 83 :
# en 2nd Impact ils passent donc DERRIERE lui, ce que Frederic decrit mot pour mot.
#
# Notre chaine, elle, cuit ces elements DANS la page proche, qui porte 84 : les jets
# passaient devant. Un cran, et il est lu.
#
# On donne donc a la couche proche la profondeur de l'element qui la prolonge. Rien d'autre
# du decor n'est a 82 ni a 83 -- ses objets sont a 74, 75, 76 et 83, ses autres couches a 94
# et 104 -- donc ce cran ne deplace QUE les deux jets, et dans le bon sens.
Z_PROCHE_ELEMENT = {}

# Les plans supplementaires de bg00, bg01, bg09 et bg0e ne portent PAS de couche du .pvc :
# on y cuit des ELEMENTS STATIQUES des plans 3 et 7 de 2I. Leur profondeur est celle de ces
# elements, LUE DANS LE CHARGEUR -- 16/09/2026 :
#
#     0x8C0233B6   nombre   = u16 [0x8C17B918 + (decor*3 + aire)*2]
#                  pointeur = u32 [0x8C5F9C04 + (decor*3 + aire)*4]
#                  enregistrement de 16 octets, lu mot par mot :
#                      +0 -> +32   +2 -> +558 PLAN   +4 -> +554   +6 -> +102 x
#                      +8 -> +106 y   +10 -> +88 ET +556 PROFONDEUR   +12 -> +456 script
#
# `+556` est exactement ce que la requete de dessin `0x8C0B46DA` passe au tri. Les six
# elements des plans 3 et 7 de Gill, Alex, Elena et Urien valent tous 86 : entre la couche du
# fond (94) et la couche proche (84), ce que les releves de liste d'affichage montrent aussi.
#
# `Z_TIERS` et `Z_QUATRE` ne servent plus que si un plan supplementaire n'a aucun element.
Z_TIERS, Z_QUATRE = 0x5A, 0x5C
ELEMENTS_NOMBRES, ELEMENTS_POINTEURS = 0x8C17B918, 0x8C5F9C04
DECOR_VERS_BANDE = 0x8C1D591C


def decor_et_aire(bande):
    """(decor, aire) de la premiere aire qui tire sur cette bande (table 0x8C1D591C)."""
    for d in range(17):
        for aire in range(3):
            if sh4.u16(sh4.a2o(DECOR_VERS_BANDE + (d * 3 + aire) * 2)) == bande:
                return d, aire
    return None


def elements_statiques(bande):
    """Les elements statiques d'une bande, dans l'ordre de leurs enregistrements."""
    da = decor_et_aire(bande)
    if da is None:
        return []
    i = da[0] * 3 + da[1]
    n = sh4.u16(sh4.a2o(ELEMENTS_NOMBRES + i * 2))
    p = sh4.u32(sh4.a2o(ELEMENTS_POINTEURS + i * 4))
    out = []
    for k in range(n):
        w = struct.unpack_from("<8H", sh4.D, sh4.a2o(p + k * 16))
        out.append(dict(rang=k, plan=w[1], x=struct.unpack("<h", struct.pack("<H", w[3]))[0],
                        y=w[4], profondeur=w[5], script=w[6]))
    return out


def profondeur_elements(bande, plan):
    """(profondeur, dernier rang) des elements statiques de ce plan de 2I, ou None.

    Plusieurs profondeurs dans un meme plan ne tiennent pas dans un plan de 3SX : on le
    dit, et on prend celle du plus grand nombre."""
    els = [e for e in elements_statiques(bande) if e["plan"] == plan]
    if not els:
        return None
    vals = sorted({e["profondeur"] for e in els})
    if len(vals) > 1:
        print("   ATTENTION bande %d plan %d : profondeurs %s dans un seul plan"
              % (bande, plan, vals))
    z = max(vals, key=lambda v: sum(e["profondeur"] == v for e in els))
    return z, max(e["rang"] for e in els)


def couches_2i(n_decor):
    """[(plan de 2I, profondeur) ou None] pour les couches k = 0..3 d'un decor, lues dans
    la table `0x8C601EE8` de SF3_2ND.BIN."""
    out = []
    for k in range(4):
        ptr = sh4.u32(sh4.a2o(TABLE_COUCHES + n_decor * 16 + k * 4))
        if not (sh4.BASE <= ptr < sh4.BASE + len(sh4.D)):
            out.append(None)
            continue
        o = sh4.a2o(ptr)
        plan = struct.unpack_from("<h", sh4.D, o)[0]
        if plan == -1:
            out.append(None)
            continue
        out.append((plan & 7, struct.unpack_from("<h", sh4.D, o + 2)[0]))
    return out


# Quand un decor n'a pas d'entree pour une couche que 3SX dessine quand meme (Hugo et Elena
# posent la banque 1 haut au loin, sans ligne dans leur table) : la valeur que TOUS les
# decors qui l'ont donnent a cet indice. Sans elle, Hugo retombait a 94, a egalite avec son
# plan du milieu, et l'ordre des deux devenait indetermine.
DEFAUT_PAR_COUCHE = {0: 94, 1: 84, 2: 104, 3: 114}


def morceaux_couche(n_decor, k):
    """[(y, hauteur)] des tranches de la couche k, ou [] si elle n'existe pas.

    Le morceau porte trois mots ; `0x8C10B070` les pose en +6, +8 et +10 d'un
    enregistrement de 16 octets, qui est un morceau de sprite resolu :

        +6 = y      +8 = (hauteur-1) << 8 | (largeur-1)      +10 = code

    Voir `couches2i.tranches` pour la demonstration et pour ce qu'on en fait.
    """
    ptr = sh4.u32(sh4.a2o(TABLE_COUCHES + n_decor * 16 + k * 4))

    if not (sh4.BASE <= ptr < sh4.BASE + len(sh4.D)):
        return []

    o = sh4.a2o(ptr)
    plan = struct.unpack_from("<h", sh4.D, o)[0]

    if plan == -1:
        return []

    out = []
    i = 4

    while True:
        w = struct.unpack_from("<3h", sh4.D, o + i)

        if w[0] == -1:
            break

        out.append((w[0], ((w[1] >> 8) & 127) + 1))
        i += 6

    return out


def profondeur_couche(n_decor, banque, moitie, defaut):
    """La profondeur de 2I de la couche qui dessine (banque, moitie). Sans entree dans la
    table : la valeur commune de cet indice (`DEFAUT_PAR_COUCHE`), sinon `defaut`."""
    c = couches_2i(n_decor)
    k = banque * 2 + (1 if moitie == "bas" else 0)
    if k < len(c) and c[k] is not None:
        return c[k][1]
    return DEFAUT_PAR_COUCHE.get(k, defaut)

PREMIER_FICHIER = 1535    # numero AFS de l'archive du premier etage ajoute
PAGES_PAR_PLAN = 32


def coefs_objet(n_decor, k):
    """(coef_x, coef_y) de l'objet `k` du decor `n_decor`, lus dans le binaire."""
    a = TABLE_COEF + n_decor * PAS_COEF + k * 8
    return sh4.u32(sh4.a2o(a)), sh4.u32(sh4.a2o(a + 4))


def affectation(chemin=os.path.join(ICI, "plans_auto.json")):
    """decor -> (plans au loin, [(plan, coef_x, coef_y) par plan supplementaire]).

    Vient de la liste d'affichage : quels plans de 2I portent vraiment des sprites, et
    quel coefficient chacun suit. Le plan 2 va toujours au plan proche ; un plan dont le
    coefficient egale celui de l'objet 0 va au plan lointain ; les autres ont le leur.
    """
    brut = json.load(open(chemin, encoding="utf-8"))
    out = {}
    for d, (_etage, loin, extras, _c0, _c0y, _n) in brut.items():
        out[d] = (set(loin), [(p, c, y) for p, c, y in extras])
    return out


def plan_du_decor(decor, n_decor, aff):
    """Tout ce qu'il faut savoir d'un etage : nombre de plans, z, vitesses."""
    if decor in COUCHES_EN_PLUS:
        # La bande porte plus de couches que le casting a deux plans : les objets sont
        # nommes en clair, et les pages viennent de `couches2i.py`.
        obj_loin, objs = COUCHES_EN_PLUS[decor]
        import couches2i as CC
        cc = CC.COUCHES[decor]
        z = [profondeur_couche(n_decor, *cc[CC.LISTE_LOINTAIN][:2], Z_LOIN_DEFAUT),
             profondeur_couche(n_decor, *cc[CC.LISTE_PROCHE][:2], Z_PROCHE_DEFAUT)]
        if len(objs) >= 1:
            z.append(profondeur_couche(n_decor, *cc[CC.LISTE_TIERS][:2], Z_TIERS))
        return dict(decor=decor, n=2 + len(objs), loin=[], extras=[],
                    coef0=coefs_objet(n_decor, obj_loin),
                    vitesses=[coefs_objet(n_decor, o) for o in objs],
                    z=z)
    cx0, cy0 = coefs_objet(n_decor, 0)
    loin, extras = aff.get(decor, (set(), []))
    vitesses = []
    for i, (p, _c, _y) in enumerate(extras[:2]):
        if decor in ECRASEMENTS and i == 0:
            vitesses.append(ECRASEMENTS[decor])
        else:
            # `plan k` suit `objet k-1` : le defaut se prend sur cet objet-la.
            vitesses.append(DEFAUTS_OBJET.get(p - 1, (0xE000, 0xE000)))
    n = 2 + len(vitesses)
    # Plan lointain = banque 0 haut, plan proche = banque 0 bas (bande3sx.py). Les plans
    # supplementaires portent les elements statiques de leur plan de 2I : leur profondeur.
    z = [profondeur_couche(n_decor, 0, "haut", Z_LOIN_DEFAUT),
         profondeur_couche(n_decor, 0, "bas", Z_PROCHE_DEFAUT)]
    rangs = []
    for i, (p, _c, _y) in enumerate(extras[:2]):
        lu = profondeur_elements(n_decor, p)
        z.append(lu[0] if lu else (Z_TIERS, Z_QUATRE)[i])
        rangs.append(lu[1] if lu else -1)
    # A PROFONDEUR EGALE, les deux moteurs ne departagent pas pareil. 2I range sa liste par
    # seaux, en inserant EN TETE (`0x8C10A2D2`) : l'element demande le DERNIER est dessine le
    # PREMIER, donc derriere -- le releve de Gill le montre, plan 7 avant les deux plans 3.
    # 3SX dessine ses plans dans l'ordre 0..3 avec un test de profondeur `<=` : a egalite,
    # le plan 3 passe DEVANT le plan 2. Quand 2I le veut derriere, on le recule d'un cran.
    if len(rangs) == 2 and z[2] == z[3] and rangs[1] > rangs[0]:
        z[3] += 1
    return dict(decor=decor, n=n, loin=sorted(loin),
                extras=[p for p, _c, _y in extras[:2]],
                coef0=(cx0, cy0), vitesses=vitesses, z=z)


def mot_priorite(f):
    """`stage_priority` : un octet par plan, du plan 0 (poids fort) au plan 3."""
    o = list(f["z"]) + [0] * (4 - len(f["z"]))
    return (o[0] << 24) | (o[1] << 16) | (o[2] << 8) | o[3]


def ecrire_include(fiches, sortie):
    L = []
    L.append("/* Genere par dc-decors/outils/etages.py -- ne pas modifier a la main.")
    L.append(" *")
    L.append(" * Les quinze etages de 2nd Impact ajoutes a 3rd Strike. Chacun a SA PROPRE")
    L.append(" * archive de pages (`resources/stages/<n>.bin`), donc son nombre de plans ne")
    L.append(" * depend d'aucun etage existant.")
    L.append(" *")
    L.append(" * Les coefficients viennent du binaire de 2nd Impact : table 0x8C1D4F48 pour")
    L.append(" * les plans lointain et proche, litteraux du script d'etage pour le plan")
    L.append(" * supplementaire, defaut 0,875 sinon. */")
    L.append("")
    for nom, cle in (("ETAGES2I_USE_SCR", "n"),):
        L.append("#define %s \\" % nom)
        L.append("    " + ", ".join(str(f[cle]) for f in fiches))
        L.append("")
    L.append("#define ETAGES2I_BGW_NUMBER \\")
    L.append("    " + ", ".join("{ %s }" % ", ".join(str(k + 1) for k in range(f["n"]))
                                for f in fiches))
    L.append("")
    L.append("#define ETAGES2I_PRIORITY \\")
    L.append("    " + ", ".join("0x%08X" % mot_priorite(f) for f in fiches))
    L.append("")
    L.append("#define ETAGES2I_GBIX \\")
    L.append("    " + ", ".join("{ %s }" % ", ".join(["0xFFFFFFFF"] * f["n"]) for f in fiches))
    L.append("")
    for quoi, idx in (("X", 0), ("Y", 1)):
        L.append("#define ETAGES2I_SPEED_%s_LOIN \\" % quoi)
        L.append("    " + ", ".join("[%d] = 0x%X" % (f["etage"], f["coef0"][idx]) for f in fiches))
        L.append("")
    for rang, nom in ((0, "TIERS"), (1, "QUATRE")):
        for quoi, idx in (("X", 0), ("Y", 1)):
            ent = ["[%d] = 0x%X" % (f["etage"], f["vitesses"][rang][idx])
                   for f in fiches if len(f["vitesses"]) > rang]
            L.append("#define ETAGES2I_SPEED_%s_%s \\" % (quoi, nom))
            L.append("    " + (", ".join(ent) if ent else "[22] = 0"))
            L.append("")
    open(sortie, "w", encoding="utf-8").write("\n".join(L) + "\n")


def main():
    aff = affectation()
    fiches = []
    for etage, decor, n_decor in ETAGES:
        f = plan_du_decor(decor, n_decor, aff)
        # L'ECART SE POSE ICI, PAS DANS `plan_du_decor` : `coef0` sert aussi a
        # decider quel plan de 2I rejoint la moitie lointaine. Le changer plus haut
        # deplacerait des plans ; le changer ici ne change QUE la vitesse ecrite.
        if decor in SANS_PARALLAXE:
            f["coef0"] = SANS_PARALLAXE[decor]
        f["etage"] = etage
        f["fichier"] = PREMIER_FICHIER + (etage - 22)
        fiches.append(f)

    print("%-6s %-5s %-6s %-9s %-22s %s" % ("decor", "etage", "plans", "fichier",
                                            "loin (obj 0)", "plans supplementaires"))
    for f in fiches:
        v = "  ".join("%.4g / %.4g" % (x / 65536, y / 65536) for x, y in f["vitesses"])
        print("%-6s %-5d %-6d %-9d %-22s %s" % (
            f["decor"], f["etage"], f["n"], f["fichier"],
            "%.4g / %.4g" % (f["coef0"][0] / 65536, f["coef0"][1] / 65536), v or "-"))

    inc = "C:/Temp3sx/src/port/video/etages2i_plans.inc"
    ecrire_include(fiches, inc)
    print("\ninclude C ecrit : %s" % inc)

    dossier = os.path.join(os.environ.get("APPDATA", ""), "CrowdedStreet", "3SX",
                           "resources", "stages")
    os.makedirs(dossier, exist_ok=True)
    for f in fiches:
        chemin = os.path.join(dossier, "%d.bin" % f["fichier"])
        archive.ecrire(f["n"] * PAGES_PAR_PLAN, chemin)
    print("%d archives ecrites dans %s" % (len(fiches), dossier))
    return 0


if __name__ == "__main__":
    sys.exit(main())
