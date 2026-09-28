# -*- coding: utf-8 -*-
"""Base de palette par decor et par groupe de drapeaux (2nd Impact).

Le champ palette d'un morceau vaut `drapeaux << 9 | offset`. La palette reelle dans
la banque de l'executable est **base(decor, drapeaux) + offset**.

Les bases ci-dessous sont deduites des palettes confirmees de PALETTES-CONFIRMEES.md :
chaque base explique plusieurs palettes a la fois, exactement, sans reste. Elles
coincident toutes avec la source d'un transfert de la table 0x1D4DBC de SF3_2ND.BIN
(enregistrements de 12 octets {u32 destination, u32 adresse de palette, u32 taille}).

  drapeau 1  = bit 9 seul   ;  5 = bits 9+11  ;  9 = bits 9+12  ;  13 = bits 9+11+12
"""

# LES BASES SONT LUES DANS LE BINAIRE, PLUS DEDUITES -- 30/08/2026.
#
#   principale (drapeau 1) : index = u16 [0x8C1D5D38 + bande*2], puis
#                            table de transferts 0x8C1E4B50 + index*12
#   secondaire (drapeau 9) : index passe en dur par le script d'etage
#
#   numero de palette = (source - 0x02798000) / 128    nb palettes = taille / 128
#
# Les dix bases qui avaient ete deduites s'y retrouvent toutes ; TROIS etaient fausses --
# bg02 (1625 au lieu de 989), bg03 (1631 au lieu de 1043), bg04 (1641 au lieu de 1117).
# Le nombre de palettes est donne aussi, et il borne l'offset employable.
# LA BASE SECONDAIRE EST CELLE DU **SECOND JEU DE TRANSFERTS** — 02/09/2026.
#
# 2nd Impact a deux tables d'index de palettes, comme New Generation :
#
#     0x8C1D5D38   premier jeu, destination 0x02000
#     0x8C1D5D16   SECOND jeu,  destination 0x12000     <- 34 octets avant, soit 17 x 2,
#                                                          le nombre de bandes
#
# Treize decors sur quatorze donnent bien `dst = 0x12000` sur le second : ce n'est pas une
# lecture decalee au hasard. Or les bases du groupe de drapeaux 9 avaient ete CALEES A
# L'OEIL, et elles ne correspondent pas au second jeu.
#
# L'EPREUVE QUI TRANCHE, et elle ne demande aucune capture : le vert pur 0x03E0 est la
# couleur de remplissage des cases de palette NON INITIALISEES (les palettes 1246 a 1253
# en sont entierement faites). Un pixel vert denonce donc une palette fausse. Compte des
# cases vertes atteintes par les morceaux a drapeaux 9 :
#
#     bg06 Hugo   base 1652 -> 850 vertes      base 1304 (jeu 2) ->   0
#     bg08        base 1663 ->  16             base 1397         ->   0
#     bg0b Yang   base 1638 -> 270             base 1498         ->   0
#     les autres  0 dans les deux cas -- aucune regression
#
# `bg0a` (Oro) garde 1674 : le detecteur ne le departage pas (0 vert des deux cotes) et
# cette valeur est VALIDEE A L'ECRAN -- « les chats, le perroquet et le chien sortent
# fauves, exactement comme sur la capture ». On ne defait pas ce qui est vu.
BASES_2I = {
    'bg00': {1: 827,  9: 958},    # 48 palettes ; jeu 2 : 958 (31)
    'bg01': {1: 927},             # 31
    'bg02': {1: 989,  9: 1064},   # 27 ; jeu 2 : 1064 (21)
    'bg03': {1: 1043, 9: 1143},   # 21 ; jeu 2 : 1143 (26)
    'bg04': {1: 1117, 9: 1194},   # 26 ; jeu 2 : 1194 (25)
    'bg05': {1: 1169, 9: 1254},   # 25 ; jeu 2 : 1254 (35)
    'bg06': {1: 1219, 9: 1304},   # 35 ; jeu 2 : 1304 (15)  -- 850 cases vertes en moins
    'bg08': {1: 1319, 9: 1397},   # 23 ; jeu 2 : 1397 (32)
    'bg0a': {1: 1429, 9: 1674},   # 24  -- VALIDEE A L'ECRAN, on n'y touche pas (jeu 2 : 1101)
    'bg0b': {1: 1085, 9: 1498},   # 16 ; jeu 2 : 1498 (21)  -- 270 cases vertes en moins
    'bg0c': {1: 1477, 9: 1552},   # 21 ; jeu 2 : 1552 (33)
    'bg0d': {1: 1519, 9: 1615},   # 33 ; jeu 2 : 1615 (8)
    'bg0e': {1: 1607, 9: 2159},   # 8  ; jeu 2 : 2159 (15)
    'bg0f': {1: 2144},            # 15  -- Akuma, relevee le 31/08/2026
    'bg10': {1: 1219, 9: 1304},   # 35, meme decor que bg06
}

# Combien de palettes chaque decor charge : un offset au-dela est HORS de sa plage.
NB_PALETTES = {
    'bg00': 48, 'bg01': 31, 'bg02': 27, 'bg03': 21, 'bg04': 26, 'bg05': 25,
    'bg06': 35, 'bg08': 23, 'bg0a': 24, 'bg0b': 16, 'bg0c': 21, 'bg0d': 33,
    'bg0e': 8, 'bg0f': 15, 'bg10': 35,
}

# L'INDEX D'ETAGE EST L'INDEX DE BANDE -- etabli, plus suppose.
#
# Les neuf index de base secondaire que les scripts d'etage passent EN DUR tombent tous,
# sans exception, sur la palette de la bande de MEME numero : etage 2 -> bg02, 3 -> bg03,
# 4 -> bg04, 5 -> bg05, 6 -> bg06, 8 -> bg08, 10 -> bg0a, 11 -> bg0b. Huit sur huit.
# C'est ce qui autorise a lire la table des scripts `0x8C1D3FB4` comme une table de
# bandes, et donc a dire que l'etage 15 est bg0f, celui d'Akuma.

# COMMENT LE JEU CHOISIT SA PALETTE -- la chaine complete
# ---------------------------------------------------------
# `0x8C0DA45E` lit un identifiant dans le contexte, `0x8C0DA46C` le convertit en index de
# transfert, et `0x8C0EDFEA` execute le transfert :
#
#     bande     = u16 [contexte + 74]            0 pour bg00 ... 16 pour bg10
#     index     = u16 [0x8C1D5D38 + bande*2]
#     entree    = 0x8C1E4B50 + index*12          {source RAM, destination, taille}
#     palette   = (source - 0x02798000) / 128    nb = taille / 128
#
# La base SECONDAIRE (drapeau 9) suit le meme chemin mais son index est passe **en dur**
# par le script d'etage : etage 2 -> 103, 3 -> 106, 4 -> 101, 5 -> 97, 6 -> 96, 8 -> 98,
# 9 -> 99, 10 -> 108, 11 -> 107. C'est ce qui donne 1625 a Ryu -- une valeur juste, mais
# pour le mauvais groupe de drapeaux : voila d'ou venait la confusion.
#
# UN DECOR PEUT AVOIR DEUX BANQUES DE PALETTES, ET ORO EN A DEUX
# ------------------------------------------------------------------
# On a longtemps cherche LA base d'Oro, et les deux valeurs candidates se contredisaient
# a l'ecran : 1674 rendait la chute d'eau bleue, 1429 rendait le chien vert. Les deux sont
# justes, chacune pour sa moitie de l'asset, et c'est l'OFFSET du morceau qui les separe :
#
#     offsets 16..20   ->  1429   la grotte : la vasque, la vapeur, les chutes, l'edifice
#     offsets  0.. 3   ->  1674   les betes : les chats, le perroquet, le chien, les
#                                 chauves-souris
#
# Ce n'est pas un reglage : **aucun des 272 sprites de l'asset ne melange les deux
# groupes**, et la coupure tombe pile entre le sprite 135 et le sprite 136.
#
# Chaque banque tient par une mesure independante :
#
#   * 1429 -- le petit edifice de pierre (sprite 79) est PEINT dans la banque du disque,
#     dans la grotte du fond. Ses couleurs relues sur la page rendent la palette 1446 sur
#     17 index sur 18, et son morceau porte l'offset 17 : 1446 - 17 = 1429. Le meme 1429
#     explique la palette 1445 de la chute d'eau, celle que l'ancienne chaine avait
#     validee a l'ecran.
#   * 1674 -- les chats, le perroquet et le chien rendus avec cette base sortent fauves,
#     vert-bleu-orange et fauve, exactement comme sur la capture du jeu
#     (`reference-oro.png`). Avec 1429 les trois sortent vert fluo.
#
# **Ne pas mesurer sur les pages cuites.** Elles portent deja ce que nos outils y ont
# pose : les chats de `poser2i.py` y sont, avec la base du jour ou on les a cuits. C'est
# la banque du `.pvc` qui fait foi, et elle seule.
# `BANQUES_2I` A ETE VIDE LE 02/09, ET C'ETAIT L'ERREUR — REMIS LE 02/09 AU SOIR.
#
# Le motif du vidage : « une base par groupe de DRAPEAUX suffit ». Elle ne suffit pas,
# elle n'existe pas -- les drapeaux sont les bits de retournement (voir `numero`). Le
# partage par plage d'OFFSETS, lui, est reel et mesure : aucun des 272 sprites d'Oro ne
# melange les deux groupes, et la coupure tombe pile entre le sprite 135 et le 136.
#
#     offsets 16..20  ->  1429 + offset   la grotte : vasque, vapeur, chutes, edifice
#     offsets  0.. 3  ->  1674 + offset   les betes : chats, perroquet, chien, chauves-souris
#
# 1674 est **validee a l'ecran** (« les chats, le perroquet et le chien sortent fauves,
# exactement comme sur la capture ») et 1429 rendait le chien vert fluo. Videe, la table
# renvoyait les betes sur 1429 -- c'est-a-dire sur la configuration explicitement rejetee.
#
# Et 1674 n'est pas un reglage : c'est le transfert SECONDAIRE d'Oro, l'entree 108 de
# `0x8C1E4B50`, dont la destination `0x2C00` suit EXACTEMENT les 24 palettes du premier
# jeu (0x2000 + 24*128) et qui porte exactement QUATRE palettes -- de quoi couvrir les
# offsets 0 a 3, et pas un de plus. Huit des neuf transferts secondaires passes en dur
# par les scripts d'etage sont ainsi contigus au premier jeu de leur bande.
#
# LA REGLE, MESUREE SUR LES QUATORZE DECORS PAR `outils/banques2i.py`
# --------------------------------------------------------------------
# Les offsets d'un decor se rangent en groupes DISJOINTS separes par un large trou, et
# chaque groupe tire sur une banque :
#
#     le groupe BAS   -> le transfert SECONDAIRE (celui que le script d'etage passe en dur)
#     le groupe HAUT  -> le PREMIER JEU (l'index lu par la bande)  == `BASES_2I[..][1]`
#
# Trois choses concordent, et aucune n'a servi a caler les autres :
#
#   * le detecteur de vert, INDEX 0 EXCLU : `bg03` passe de 12518 pixels verts a ZERO,
#     `bg06` de 23092 a ZERO. A l'inverse le groupe HAUT est propre avec le premier jeu
#     et sale avec le secondaire (`bg0a` 16..20 : 0 contre 17826) ;
#   * le NOMBRE de palettes du transfert borne le groupe qu'il peut servir. C'est lui qui
#     ecarte le secondaire pour `bg05` (5 palettes pour 25 offsets) et `bg08` (4 pour 8) ;
#   * `bg0a` offsets 0..3 -> 1674 est **validee a l'ecran** (« les chats, le perroquet et
#     le chien sortent fauves, exactement comme sur la capture »), et le detecteur ne
#     departage pas ce cas-la. La regle le retrouve tout seul.
#
# BG02 EST APPLIQUE DEPUIS LE 03/09 : Frederic a signale « beaucoup d'anomalies » sur le
# decor de Ryu. Le detecteur de vert reste muet sur ce groupe (zero des deux cotes), mais
# les deux autres mesures le designent -- la destination contigue et le nombre de palettes
# -- et 1625 est la valeur que RELAIS et SANS-ETAT donnent deja pour ce groupe depuis le
# 30/08. Il recevait 989, le premier jeu.
#
# BG04 EST APPLIQUE DEPUIS LE 03/09 : Frederic a signale que « le monsieur avec sa canne
# et son chapeau n'a pas la bonne couleur ». Meme situation que Ryu -- detecteur muet,
# destination contigue et nombre de palettes d'accord, valeur deja notee le 30/08.
#
#     plage d'offsets (bornes comprises) -> base
BANQUES_2I = {
    'bg02': [(0, 5, 1625)],     # signale a l'ecran ; detecteur muet, regle et doc d'accord
    'bg04': [(0, 5, 1641)],     # signale a l'ecran : le monsieur a la canne
    'bg03': [(0, 6, 1631)],     # 12518 pixels verts -> 0
    'bg06': [(0, 11, 1652)],    # 23092 pixels verts -> 0
    'bg10': [(0, 11, 1652)],    # meme decor et meme asset que bg06
    # ORO. 1674 EST VALIDEE A L'ECRAN pour les betes, et on ne la redecide pas -- mais
    # elle ne couvre pas l'offset 3.
    #
    # La destination `0x2C00` (= 0x2000 + 24*128, la suite du premier jeu) porte TROIS
    # entrees de la table, pas une : idx108 base 1674 nb 4, idx105 base 2184 nb 8,
    # idx134 base 1760 nb 1. Ce sont les VARIANTES de l'etage -- le meme emplacement de
    # palette RAM, rempli differemment selon le tirage. Leurs couleurs n'ont rien de
    # commun : 63 des 64 cases different entre 1674 et 2184.
    #
    # L'objet 14 (script 20, x 672) sort **401 pixels verts** avec 1674+3 = 1677, et
    # ZERO avec 2184+3 = 2187. C'est le seul candidat propre a cette destination.
    # Les huit autres objets d'Oro sont propres des deux cotes : le detecteur ne les
    # departage pas, donc on ne les touche pas.
    #
    # Notre portage aplatit les variantes en un seul etage : chaque objet est donc peint
    # avec la palette de la variante a laquelle il appartient, et le melange est ici la
    # lecture juste, pas une incoherence.
    'bg0a': [(0, 2, 1674), (3, 3, 2184)],
    # BG08 EST LE SEUL DECOR DE 2I A PORTER DEUX BANDES, ET C'EST LA TABLE QUI LE DIT.
    #
    #     bande = u16[0x8C1D591C + decor*6 + aire*2]        -- trois aires par decor
    #
    # Les seize autres decors rendent trois fois la meme bande. Le decor 8 rend **[8, 9,
    # 9]** : son aire 0 tire sur la bande 8, ses aires 1 et 2 sur la bande 9. C'est la
    # meme structure qu'en New Generation, ou `d["bandes"]` porte deja plusieurs valeurs.
    #
    # L'objet `a30o0` (script 1, offset 7) sortait **3265 pixels verts** avec la bande 8
    # -- Frederic l'a vu, c'est la tache magenta et verte au centre de l'etage 30 -- et il
    # est PROPRE avec le premier jeu de la bande 9, base 1365. Le secondaire des deux
    # bandes ne porte que 4 et 7 palettes : il ne peut pas servir l'offset 7.
    #
    # Aucune autre fiche posee de bg08 n'est a l'offset 7 : les vingt-trois autres sont a
    # l'offset 1. La bascule ne touche donc que lui.
    'bg08': [(7, 7, 1365)],
}

# LA SEULE ECHARDE, ET IL FAUT LA CONNAITRE : le transfert secondaire de `bg06` porte
# ONZE palettes (offsets 0 a 10) alors que ses morceaux emploient l'offset 11. C'est
# aussi le seul des neuf secondaires dont la destination ne suit pas exactement le
# premier jeu -- 0x3200 quand la suite immediate serait 0x3180, un emplacement plus loin,
# ou une autre entree (base 2181, trois palettes) se pose. Les deux anomalies vont
# ensemble et ne sont pas expliquees. 1652 + 11 = 1663 n'a aucune case verte aux index
# employes, donc rien ne s'y oppose ; ce n'est simplement pas etabli.


# « DRAPEAU 9 » N'EST PAS UNE BANQUE : C'EST LE BIT DE MIROIR — 02/09/2026
# =========================================================================
# `drapeaux = champ >> 9` ne prend que QUATRE valeurs sur les quatorze assets, et leurs
# bits disent exactement ce que `assemblage.morceaux` lit sur les MEMES bits :
#
#     drapeaux  morceaux  bit 11  bit 12   soit
#     1         12499                      aucun retournement
#     5             3     oui              miroir vertical
#     9           512             oui      miroir horizontal
#     13            4     oui     oui      les deux
#
# Il n'y a pas de cinquieme valeur. Un morceau « drapeau 9 » est donc un morceau
# RETOURNE HORIZONTALEMENT, et rien d'autre -- sa palette est `base + offset` comme
# celle de n'importe quel autre.
#
# L'EPREUVE QUI TRANCHE, et elle ne doit rien a ce raisonnement : les quatre figures
# animees de `bg00` ont les palettes 871, 872, 873 et 874 -- etabli par deux chemins
# independants, et 871 est validee a l'ecran. Leurs morceaux portent TOUS `drapeaux 1`,
# offsets 44 a 47, et `827 + offset` les rend exactement. La chaine confirmee n'emploie
# donc jamais la seconde base.
#
# CE QUE LA SECONDE BASE FAISAIT : elle envoyait les 512 morceaux retournes chercher
# leurs couleurs dans une palette lointaine -- 1304 au lieu de 1219 chez Hugo, 1498 au
# lieu de 1085 chez Yang. Un vetement dont la moitie est un morceau miroir sortait donc
# d'une couleur sans rapport avec l'autre moitie.
#
# ET LA MESURE QUI AVAIT SERVI A LES CHOISIR NE MESURAIT RIEN. Les « 850 cases vertes »
# de `bg06` et les « 270 » de `bg0b` comptaient l'INDEX 0, qui est transparent et n'est
# jamais peint. Index 0 exclu, les trois candidates possibles rendent **zero** vert sur
# les quatorze decors : le detecteur ne departageait rien. Et un balayage des 2715
# palettes laisse 1932 bases sans un seul pixel vert -- il elimine, il ne choisit pas.
#
# Les valeurs sont gardees ci-dessus pour memoire, et pour qu'on ne les recherche pas
# une troisieme fois. Elles ne colorent plus rien.
def numero(decor, drapeaux, offset):
    """Le numero de palette dans la banque du binaire, ou None si on ne sait pas.

    `drapeaux` ne sert plus qu'a reconnaitre un champ valide : ce sont les bits de
    retournement, pas un choix de banque. Voir le commentaire ci-dessus.

    `BANQUES_2I` reste consulte -- une base par plage d'OFFSETS, ce qui est un partage
    reel, celui d'Oro : sa grotte et ses betes ne tirent pas sur la meme banque et c'est
    l'offset du morceau qui les separe.
    """
    for lo, hi, b in BANQUES_2I.get(decor, ()):
        if lo <= offset <= hi:
            return b + offset

    b = BASES_2I.get(decor, {})
    return b[1] + offset if 1 in b else None


# Les .pk et leur asset principal, pour les planches
ASSETS = {
    'bg00': '2i-b00-F_ETC41.bin', 'bg01': '2i-b01-F_ETC34.bin',
    'bg02': '2i-b02-F_ETC25.bin', 'bg03': '2i-b03-F_ETC26.bin',
    'bg04': '2i-b04-F_ETC32.bin', 'bg05': '2i-b05-F_ETC28.bin',
    'bg06': '2i-b06-F_ETC29.bin', 'bg08': '2i-b08-F_ETC30.bin',
    'bg0a': '2i-b0a-F_ETC33.bin', 'bg0b': '2i-b0b-F_ETC27.bin',
    'bg0c': '2i-b0c-F_ETC24.bin', 'bg0d': '2i-b0d-F_ETC35.bin',
    'bg0e': '2i-b0e-F_ETC94.bin', 'bg10': '2i-b10-F_ETC29.bin',
}
