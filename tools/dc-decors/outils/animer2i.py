# -*- coding: utf-8 -*-
"""Genere les objets ANIMES d'un decor, depuis le binaire seul, et les pose dans le C.

C'est la suite de `poser22.py` pour ce qui bouge. `animations.py` n'exportait qu'UNE
animation par etage, choisie a la plus grande qui tienne dans la grille du motif
emprunte ; le binaire, lui, en donne quatre rien que pour Gill.

    table des objets animes   0x8C183DC8 pour bg00, quatre enregistrements de 8 octets
        {u16 x, u16 y, u16 palette, u16 script}
              |
    table de scripts du decor   0x8C5F9B38 + aire*4
        enregistrements de 8 octets {u8 commande, u8 duree, u16 ?, u16 index global}
        commande 1 = fin ; duree 0 = a sauter
              |
    asset F_ETCnn : anims[index global - span]  ->  ancre et numero de sprite
              |
    assemblage.poser  ->  l'image d'index, et (x0, y0), le coin dans le repere du sprite

LA POSITION, la meme regle que partout :

    bank_x = element.x + ancre_x + x0        bank_y = sol - element.y + ancre_y + y0
    x = bank_x                               y = 1024 - bank_y - (ligs - 1) * 16

LES TUILES sont **entrelacees** : le televersement lit sa source a travers `dctex_linear`,
et une tuile lineaire sortirait en rayures.

    python animer2i.py             # dit ce qu'il ferait
    python animer2i.py --ecrire    # recrit decor_objets_data.c
"""
import io
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import animations as AN0          # pour `entrelacer` seulement -- aucun etat n'est lu
import annuaire2i as AN
import assemblage as A
import bases
import fetc
import immediats2i as IM
import palettes
import palettes_ram2i as PR
import poser2i as P
import sh4

DATA = r"C:\Temp3sx\src\port\video\decor_objets_data.c"
SOL = 1023

# LA PALETTE D'UN OBJET EST CELLE DE SON EMPLACEMENT RAM -- 16/09/2026.
#
# `+554` (`my_col_code`) : ses neuf bits bas designent l'emplacement de la palette RAM, et
# le morceau d'offset `o` y lit `emplacement + o`. Les trois transferts du chargeur d'etage
# disent quelle palette du binaire occupe chaque emplacement (`palettes_ram2i.py`). La
# regle retrouve seule les valeurs deja validees -- Yun 1631 et 1063, Oro 1674, Hugo 1652,
# Dudley 1642 -- et donne a la dame de Necro, a ses bocaux (0x2059 = 64 + 25) et a l'objet
# de Yang en 0x2050 le transfert SECONDAIRE que la chaine ne leur donnait pas : « mauvaise
# couleur ».
#
# Appliquee aux decors qu'on reprend. Ailleurs elle rend les memes palettes, a trois
# exceptions non tranchees (Ryu script 7, Hugo id 63, le perroquet d'Oro qui prend une
# variante de palette) : on ne touche pas a ce qui est vu.
#
# LE PERROQUET D'ORO EST TRANCHE -- 16/09/2026. Frederic : « la couleur du perroquet est
# mauvaise ». Son spawner (`0x8C030546`) ecrit `+554` = 0x2058, comme le chien, le chat et
# les chatons : l'emplacement 88, que le transfert secondaire (idx 108) remplit avec 1674..
# 1677. La chaine lui donnait 2187, une palette du transfert idx 105. Rendu avec la regle :
# tete verte, face orange, aile bleue -- la reference `reference-oro-perroquet.png`. Pour
# Oro, c'est la seule palette que la regle change.
# BG06 TRANCHE -- 24/09/2026. Frederic : « la couleur du tonneau n'est pas bonne, il est
# bleu au lieu de beige ». C'etait la troisieme exception laissee ouverte ci-dessus, et
# elle se lit sans rien deviner :
#
#     le spawner du tonneau (0x8C031B56) ecrit `+554` = 0x2040, soit l'emplacement 64,
#     que le chargeur de la bande 6 remplit avec 1219.. ; son premier morceau est a
#     l'offset 11, donc la palette 1230.
#
# `BANQUES_2I["bg06"]` envoyait tout offset 0..11 sur 1652+offset, donc 1663. Les deux
# banques sont mesurables et sans appel :
#
#     1663 : treize couleurs sur seize plus bleues que rouges, le maximum de rouge a 19/31
#     1230 : une rampe chaude complete, de R04 G02 B01 a R31 G31 B19 -- le beige du chene
#
# ET LE MEME TONNEAU EST DEJA JUSTE DANS BG10, qui est dans cette liste depuis le debut :
# sa fiche porte 1230. Le meme objet, le meme asset, deux couleurs -- c'etait la preuve
# sous nos yeux.
#
# LES AUTRES OBJETS DE BG06 NE BOUGENT PAS : leur `+554` vaut 0x2064, l'emplacement 100,
# que le meme chargeur remplit avec 1652.. Les deux regles ne se contredisent donc nulle
# part ; l'ancienne rangeait simplement par OFFSET ce qui se range par EMPLACEMENT.
PALETTES_RAM = {"bg03", "bg05", "bg06", "bg0a", "bg0b", "bg0d", "bg10"}
DECOR_VERS_BANDE = 0x8C1D591C

# LES COMBATTANTS DANS LE MASQUE DE VARIANTE -- 16/09/2026. Les quatre bits bas sont le
# tirage `z` ; ces deux-la disent si l'objet existe quand un des combattants est un AMI du
# decor (`decor_objets.c`, `humeur_du_decor`), ou quand aucun ne l'est. Ni l'un ni l'autre :
# dans les deux cas. Le chien d'Oro est le premier objet qui en depend.
SANS_AMI, AVEC_AMI = 0x10, 0x20

# LES COMPORTEMENTS -- un objet dont la ROUTINE choisit l'image, au lieu de derouler un
# script. Ses images sont des SUITES bout a bout ; la fiche porte le numero et les debuts
# des suites 1 et 2 (la suite 0 commence a 0). Le moteur les lit dans
# `decor_objets.c`, `conduire`.
# L'ACOLYTE DE GILL QUI REGARDE : UN SEUL DES QUATRE (corrige le 23/09/2026 au soir).
#
# Frederic : « dans Gill 2I, l'acolyte central suit bien des yeux les combattants mais les
# autres personnages n'ont plus aucune animation ». Il a raison, et la faute etait ici :
# j'avais marque REGARD les QUATRE enregistrements du bloc `0x8C183DC8`. Le binaire dit
# autre chose.
#
# Le chargeur du bloc (`0x8C04AE04`) ecrit en `objet[+52]` l'INDICE DE LA BOUCLE :
#
#     8C04AE82  add #52,r3            r3 = objet + 52
#     8C04AE9A  mov.w r11,@r3         objet[+52] = r11, l'indice 0,1,2,3
#     8C04AEB6  add #1,r11
#
# et l'id 184 (`0x8C04AA54`) repartit la-dessus AVANT toute autre chose :
#
#     indice 0 -> 8C04AA92   pose le script 11 et l'anime : UNE ANIMATION ORDINAIRE
#     indice 1 -> 8C04AB88   LE REGARD
#     indice 2,3 -> 8C04AD0C pose `objet[+456]`, le script de son enregistrement (5, 6)
#
# Seul l'indice 1 -- l'enregistrement `0x8C183DD0`, x=576, script 12 -- passe par
# `0x8C04ACB2`, qui lit le X du combattant et pose le script 12 a l'etape choisie :
#
#     8C04ACDC  mov.w r0,@(4,r5)      objet[+56] = l'orientation, 0..5
#     8C04ACE4  cmp/eq r0,r3          la meme que la precedente (+58) ? alors rien
#     8C04ACF0  mov #12,r6            LE SCRIPT 12
#     8C04ACF4  mov.w @(r0,r14),r7    r7 = orientation
#     8C04ACF6  add #1,r7
#     8C04ACF8  jsr 0x8C0B4B90        poser(objet, table 0, script 12, etape r7-1)
#
# `0x8C0B4B90` n'est pas le poseur ordinaire `0x8C0B4AD4` : il prend une ETAPE de depart
# (`add #-1,r7` puis autant d'avances). L'orientation est donc un NUMERO D'ETAPE dans le
# script 12 -- ce que le port rend exactement en prenant l'image de ce rang.
#
# C'est donc un enregistrement, pas un bloc.
REGARD_ELEMENTS = {0x8C183DD0}

COMPORTEMENTS = {
    1: "CHIEN DEBOUT : regard, queue, aboiement",
    2: "CHIEN COUCHE : repos en boucle, reveil",
    3: "POISSON ROUGE : va-et-vient de 160 a 240",
    4: "POISSON NOIR : le tour de l'aquarium",
    7: "REGARD : l'image choisie par le X d'un combattant",
    9: "RUPTURE : il se brise sous la chute d'un combattant",
}

_D, _B = sh4.D, sh4.BASE
u8 = lambda a: _D[a - _B]
u16 = lambda a: struct.unpack_from('<H', _D, a - _B)[0]
u32 = lambda a: struct.unpack_from('<I', _D, a - _B)[0]

# OU SONT LES OBJETS DE DECOR, ET A QUI ILS APPARTIENNENT
# -------------------------------------------------------
# `bg00` : son spawner `0x8C04AE04` porte son bloc EN DUR (`mov.l <0x8C183DC8>,r14`),
# quatre enregistrements de 8 octets `{x, y, palette, script}`.
#
# Les autres passent par un chargeur a table, atteint depuis le script d'etage :
#
#     0x8C1D3FB4[etage]  ->  jsr <chargeur>  avec  mov #arg,r4
#     0x8C02E1FE : nb = u16[0x8C17E794 + arg*2]   bloc = u32[0x8C5F9F64 + arg*4]
#     0x8C025A9A : nb = u16[0x8C17C1F8 + arg*2]   bloc = u32[0x8C5F9DF8 + arg*4]
#
# Le premier enregistrement est a **pointeur + 2**, comme dans l'annuaire des elements,
# au format 16 octets `{plan, drapeaux, x, y, palette, script, ...}`.
# `outils/chargeurs2i.py` sort l'attribution des dix-sept decors d'un trait.
#
# UN DECALAGE RESTE INEXPLIQUE, ET IL FAUT LE SAVOIR
# --------------------------------------------------
# Le bloc `0x8C17E918` est appele par le script d'etage d'index **10**, alors que la table
# de scripts qui le resout correctement est celle d'index **9**. Les deux tables ne sont
# donc pas indexees pareil. J'en avais conclu que ce bloc etait celui de Yang et je l'ai
# retire d'Oro : c'etait faux. Frederic est formel, et l'ecran le montre -- la vasque, la
# vapeur, les trois chutes d'eau et l'edifice de pierre sont a ORO.
#
# **Ce qui fait foi est la combinaison validee a l'ecran** : bloc `0x8C17E918`, asset
# `bg0a`, table de scripts du decor 9. Tant que le decalage n'est pas explique, on ne
# touche pas a ce qui est vu.
#
# DEUX BLOCS ONT ETE ESSAYES ET REJETES A L'ECRAN, a ne pas reprendre
# -------------------------------------------------------------------
# * `0x8C17E838`, dix enregistrements : ses quatre betes sortent EMPILEES en x 336, 339,
#   323 et 321, et il apporte un objet inconnu au ras du sol (script 11, banque_y 975) ;
# * `0x8C17BDB2` / `0x8C17BD50` / `0x8C17BD40`, choisis sur la seule dispersion de leurs
#   x : « le perroquet et le chat ne sont pas a leur place, le chien au premier plan non
#   plus ».
# LE FORMAT EST LE MEME PARTOUT, une fois le debut du bloc bien pose : depuis le pointeur
# de la table, `x` est a +6, `y` a +8 et le script a +12. Les chargeurs a table pointent
# deux octets avant leur premier enregistrement -- d'ou `adresse = pointeur + 2` et les
# champs a +4, +6, +10, qui est la meme lecture. Le spawner d'Alex, lui, pointe droit sur
# l'enregistrement : il porte donc ses champs explicitement.
# LES SPAWNERS DEDIES, LUS PAR `outils/spawners2i.py` — 02/09/2026
# ------------------------------------------------------------------
# L'outil desassemble chaque spawner et en sort trois choses qui n'etaient pas connues :
# le nombre de champs et leur offset d'objet (donc la TAILLE de l'enregistrement), la
# facon dont le bloc est atteint (en dur, indexe par l'argument, ou par deux tables), et
# le nombre de tours de sa boucle. Rien n'est suppose.
#
# CE QU'IL A CORRIGE, ET C'ETAIT UNE FAUSSE ATTRIBUTION
# ------------------------------------------------------
# `0x8C17F54C` n'est pas un bloc : c'est la table des NOMBRES du spawner `0x8C036480`,
# qui s'indexe `nombre = u16[0x8C17F54C + arg*8 + z*2]` et
# `pointeur = u32[0x8C5FA00C + arg*16 + z*4]` -- le meme moule que les lecteurs de New
# Generation, `z` compris. La chaine lisait cette table comme des enregistrements, a
# `0x8C17F54C + 38`, et en tirait QUATRE objets pour Hugo.
#
# Le spawner n'est appele que DEUX fois dans tout le binaire : bande 3 (Yun) avec
# l'argument 2, bande 6 (Hugo) avec l'argument 3. Chacun a **un** enregistrement --
# Yun a `0x8C17F572`, Hugo a `0x8C17F584`. Les deux suivants, `0x8C17F596` et
# `0x8C17F5A8`, sont l'argument 4, que **personne n'appelle** : ils etaient poses chez
# Hugo sans appartenir a aucun decor, et le premier des quatre etait celui de YUN.
#
# ET `z` EXISTE AUSSI EN 2nd IMPACT. C'est un TIRAGE uniforme sur 0..3 refait a chaque
# entree d'etage (le generateur et sa table de 64 entrees sont identiques octet pour
# octet dans les deux jeux).
#
# ON CUIT `z = 0`, ET C'EST MESURE, PAS ARBITRAIRE. Sur les dix couples
# (lecteur, argument) qu'un script d'etage atteint, **deux seulement** portent des blocs
# reellement differents selon `z` :
#
#     Yun  (0x8C028792 arg 2)  z0/z2 -> script 19 posable ; z1/z3 -> RIEN de posable
#     Hugo (0x8C028792 arg 3)  z0 -> 7, 9, 11 ; z1/z3 -> 7, 5, 11 ; z2 -> 7, 11, 13
#
# `z = 0` est donc le plus riche chez Yun et a egalite chez Hugo, ou les quatre variantes
# donnent trois objets et ne different que par UN sprite (9, 5 ou 13). Poser leur union
# montrerait trois figures la ou le jeu n'en montre qu'une : on reste sur une variante.
# LES DEUX LECTEURS SANS CHAMP `+456` — RESOLUS LE 02/09/2026
# ------------------------------------------------------------
# `0x8C0323F0` (id 66, Alex et Dudley) et `0x8C028792` (id 18, sept bandes) n'ecrivent
# aucun numero de script dans l'objet. J'en avais conclu que leurs objets n'etaient pas
# des animes de notre espece. **C'est faux, et le chemin est plus long d'un cran.**
#
# L'objet est un WORK, et sa disposition est celle que le port porte en C (`structs.h`) :
#
#     +0 be_flag   +1 disp_flag   +4 type   +6 work_id   +8 id
#     +36 routine_no[]   +52 old_rno[]
#
# `+8` est l'**id**, et c'est lui qui choisit la routine dans la table d'effets de 2nd
# Impact, **`0x8C179FDC`, 196 entrees**, lue par le repartiteur `0x8C0215E0` :
#
#     mov.w @(8,r14),r0 ; shll2 r0 ; mov.l @(r0,r10),r3 ; jsr @r3 ; mov r14,r4
#
# (`r10` = 0x8C179FDC, `r11` = 0x8C6466EC, le tas d'objets de 2048 octets -- le meme
# litteral que les spawners emploient.) Chaque spawner est ecrit JUSTE APRES sa routine :
# id 18 -> 0x8C028510 puis le spawner 0x8C028792 ; id 66 -> 0x8C03215C puis 0x8C0323F0 ;
# id 87 -> 0x8C0363A4 puis 0x8C036480. Trois sur trois : la table se valide elle-meme.
#
# ET LA ROUTINE EN APPELLE UNE AUTRE, choisie par un CHAMP DU BLOC :
#
#     mov #38,r0 ; mov.w @(r0,r14),r3 ; mov.l @(r0,<table>),r2 ; jsr @r2
#
#     id 66 -> table 0x8C5F9FB4 (4 entrees, dont deux `rts` nus)
#     id 18 -> table 0x8C5F9EA4 (2 entrees)
#
# C'est CETTE routine-la qui pose le script, et le scan ne la suivait pas : elle n'est
# atteinte que par une table, jamais par un litteral de code. Elle appelle
# **`0x8C0B4AD4`**, qui fait `objet+454 = r5` puis `objet+456 = r6` -- r6 etant le numero
# de script, lu dans l'objet a un offset que la routine connait :
#
#     id 66 -> objet+52  (old_rno[0])     id 18 -> objet+150
#
# **Et les deux tombent sur le meme endroit du bloc : l'OCTET 12 de l'enregistrement.**
# Les deux lecteurs ont des enregistrements de 24 octets (douze champs ; mon premier
# decodage en annoncait 20 et 22 parce qu'il ratait le champ ecrit par `mov.w r3,@r1`,
# ou r1 = objet+52, et le dernier, lu sans post-increment).
#
# L'EPREUVE : les scripts ainsi lus se resolvent dans l'asset de leur propre decor --
# Alex 2 et 3, Dudley 4 et 5, et neuf des onze enregistrements de l'id 18. Les deux qui
# ne se resolvent pas rendent ZERO image, donc rien a poser de toute facon.
#
# Au passage : l'entree `bg01` lisait deja son script a l'octet 12. Elle etait juste, et
# c'est maintenant etabli au lieu d'etre un heureux hasard.
TABLES = {
    "bg00": [dict(decor=0, adresse=0x8C183DC8, nb=4, pas=8),
             # LE SECOND SPAWNER DE GILL, `0x8C0258DA`, appele une seule fois dans tout
             # le binaire, depuis sa routine d'etage (site 0x8C0DBC4E) et sans argument.
             # Bloc EN DUR, enregistrements de DIX octets {x, y, +556, script, +148} :
             # ni plan ni palette, d'ou les deux `None`. Sa boucle compare a `mov #4,r3`
             # -- quatre enregistrements, et ce sont exactement les quatre qui se
             # resolvent (scripts 0, 1, 2, 2 ; les suivants sont du bruit).
             dict(decor=0, adresse=0x8C17C190, nb=4, pas=10,
                  x=0, y=2, sc=6, plan=None, pal=None),
             # LES DEUX SPAWNERS INDEXES SUR LE DECOR COURANT -- 25/09/2026.
             #
             # `0x8C0233B6` et `0x8C02356A` suivent le moule de `0x8C02E1FE` (pas 16,
             # champs +32, +558, +554, +102, +106, +88, +456, +118) mais lisent leurs
             # tables avec `u8[0x8C6AF308]`, LE DECOR COURANT, et non l'argument du
             # chargeur -- ce qui les rendait invisibles au balayage par argument :
             #
             #     0x8C0233B6   nb = u16[0x8C17B918 + decor*6 + aire*2]
             #                  bloc = u32[0x8C5F9C04 + decor*12 + aire*4]
             #     0x8C02356A   nb = u16[0x8C17BBC4 + decor*6 + aire*2]
             #                  bloc = u32[0x8C5F9CD0 + decor*12 + aire*4]
             #
             # Les `+2` calent les offsets par defaut (x a 4, y a 6, pal a 8, sc a 10,
             # plan a 0, col_code a 2) sur un bloc dont le premier champ est a l'offset 0.
             # Douze de leurs enregistrements ne sont PAS ici : ceux des AIRES 1 et 2 de
             # Hugo et de bg10, que le port ne sait pas distinguer sur un etage a bande
             # unique. Ils sont nommes dans DECORS.md.
             # Gill : scripts 7, 8 et 9 -- plans 3, 3 et 7
             dict(decor=0, adresse=0x8C17B980, nb=3, pas=16)
            ],
    # ALEX -- spawner dedie 0x8C0323F0, appele avec l'argument 2 depuis son script
    # d'etage (site 0x8C0DBF72). Enregistrements de 24 octets a `0x8C17F2D8 + arg*24`,
    # et le meme spawner sert a Dudley avec l'argument 0.
    "bg01": [dict(decor=1, adresse=0x8C17F308, nb=1, pas=24, x=6, y=8, sc=12),
             # Alex : scripts 1 et 0, plan 3
             dict(decor=1, adresse=0x8C17B9B0, nb=2, pas=16)
            ],
    # RYU -- deux blocs, tous deux appeles par son script d'etage d'index 2, et tous deux
    # resolus par la table de scripts 2 : 106 images pour le premier, 18 pour le second,
    # avec des x etales sur 641 et 304. Aucun decalage d'index pour lui.
    "bg02": [dict(decor=2, adresse=0x8C17E7A8, nb=6, pas=16),
             dict(decor=2, adresse=0x8C17C210, nb=2, pas=16),
             # LE SPAWNER DEDIE DE RYU, `0x8C036688`, argument 0, appele une seule fois
             # (site 0x8C0DC2E0). Meme moule que celui de Hugo : deux tables,
             # `nombre = u16[0x8C17F5B8 + arg*8 + z*2]` et
             # `pointeur = u32[0x8C5FA05C + arg*16 + z*4]`. Trois enregistrements de 18
             # octets, les quatre `z` donnant le meme bloc.
             dict(decor=2, adresse=0x8C17F65A, nb=3, pas=18),
             # ID 18, arg 1 : scripts 20 (19 images) et 8 (14 images). Le second porte
             # x = -112, et Ryu est le seul decor a x negatifs.
             dict(decor=2, adresse=0x8C17DB92, nb=2, pas=24, sc2=12),
             # CINQ OBJETS QUI MANQUAIENT -- 25/09/2026. Frederic : « *decor ryu 2I, il y a
             # toujours des anomalies aux extremites du decor et des sprites en trop ou mal
             # places* ». Ils etaient CUITS DANS LE FOND par `cuire.py`, qui pose a
             # `x & 0x3FF` sans le decalage de Ryu : 512 pixels a cote, donc aux extremites.
             #
             # Leurs deux spawners suivent le meme moule que `0x8C02E1FE` (pas 16, champs
             # {+32, +558, +554, +102, +106, +88, +456, +118}) mais s'indexent sur le DECOR
             # COURANT, `u8[0x8C6AF308]`, et non sur l'argument -- ce qui les rendait
             # invisibles au balayage :
             #
             #     0x8C0233B6   nb = u16[0x8C17B918 + decor*6 + z*2]
             #                  bloc = u32[0x8C5F9C04 + decor*12 + z*4]
             #     0x8C02356A   nb = u16[0x8C17BBC4 + ...]   bloc = u32[0x8C5F9CD0 + ...]
             #
             # Pour le decor 2 : 2 objets en 0x8C17B9CE (scripts 17 et 23, x -17 et -89) et
             # 3 en 0x8C17BC2E (scripts 15, 16 et 22, x -217, -265 et 264). Les `+2` sont
             # le calage des offsets par defaut, comme pour les deux blocs ci-dessus.
             #
             # LES AUTRES DECORS EN ONT AUSSI, et ils ne sont PAS portes : 30 objets pour le
             # premier spawner (decors 0,1,3,4,5,6,10,11,12,13,16) et 36 pour le second
             # (3,4,5,6,8,9,10,12,16). C'est ecrit ici pour ne pas l'oublier.
             dict(decor=2, adresse=0x8C17B9D0, nb=2, pas=16),
             dict(decor=2, adresse=0x8C17BC30, nb=3, pas=16)],
    # YUN -- deux blocs, appeles par son script d'etage d'index 3 et resolus par la
    # table de scripts 3 : pas de decalage, comme Ryu.
    # YUN -- LA CAGE D'OISEAUX QUI SE BRISE (id 23, `0x8C02936E`) -- 23/09/2026.
    # Frederic : « pour les decors de Yun et Yang, ce sont les cages d'oiseaux et la statue
    # qui se brisent ». La routine d'etage la cree en 672,48, palette 90, profondeur 90 --
    # et `DECORS.md` notait deja « cages 90 ».
    #
    # Son etat 1 (`0x8C029280`) appelle le test de contact `0x8C0D7D74` et, s'il rend autre
    # chose que zero, pose le script 12 (`0x8C029290`). Son etat 0 lit un compteur qui
    # survit a la manche : non nul, il pose directement le script 34, la cage deja brisee.
    #
    #     script  7 :  1 image  32117         INTACTE
    #     script 12 : 14 images 32273..32285  LA RUPTURE, qui tient sa derniere image
    #     script 34 :  1 image  32105         BRISEE, a la manche suivante
    #
    # Son type est ecrit en dur par le spawner (`0x8C0293DE`, `mov #8,r0`), d'ou la boite
    # du type 8 : `0x8C1D3ED4 + 8*8`.
    "bg03": [dict(decor=3, immediats=[dict(script=7, x=672, y=48, pal=90, plan=2,
                                           spawner=0x8C02936E, comportement=9,
                                           suites=[7, (12, "une")],
                                           boite=(12, 61, 16, 28))]),
             dict(decor=3, adresse=0x8C17C230, nb=2, pas=16),
             dict(decor=3, adresse=0x8C17E808, nb=2, pas=16),
             # YUN APPELLE LE SPAWNER DE HUGO, avec l'argument 2 (site 0x8C0DC680). UN
             # enregistrement, `0x8C17F570 + 2`. C'est celui que la chaine posait chez
             # Hugo -- script 28, huit images -- et il est a Yun.
             dict(decor=3, adresse=0x8C17F572, nb=1, pas=18),
             # ID 18, arg 2, z 0. Le second enregistrement (script 21) rend ZERO image :
             # il n'y a rien a poser, et la chaine le saute d'elle-meme.
             # LES DEUX VARIANTES `z` DE YUN, ET C'EST LA QU'ETAIENT SES DEUX
             # PERSONNAGES. Frederic les a montres en capture -- un vieil homme au
             # panier rond et une femme en rose au chapeau -- et ils sont les scripts 33
             # et 31, qui ne vivent que dans la variante z 1/3. On cuisait z 0.
             dict(decor=3, adresse=0x8C17DBC2, nb=2, pas=24, sc2=12, variante=0x5),
             dict(decor=3, adresse=0x8C17DBF2, nb=2, pas=24, sc2=12, variante=0xA),
             # L'ARBRE DES SPAWNERS DE YUN — 03/09/2026.
             #
             # Frederic, a l'ecran : « pour le decor de Yun, manquent les animations des 2
             # personnages devant le tram et celles du personnage a droite qui fume et des
             # oiseaux dans les cages a droite ». Ils sont tous derriere UN spawner que la
             # chaine ignorait, et qui en appelle TROIS AUTRES -- le meme motif que la
             # chatte d'Oro qui fait ses chatons.
             #
             #     routine d'etage de la bande 3, site 0x8C0DC68E
             #        -> 0x8C02936E   id 23   x 672, y 48,  palette 90
             #             -> 0x8C028E62   id 21   TROIS objets, bloc 0x8C17DD58
             #             -> 0x8C02912C   id 22   x 712, y 56,  palette 74
             #             -> 0x8C02962E   id 24   x 728, y 48,  palette 91
             #
             # Les six sont a DROITE de la bande (672 a 752), ce qui recoupe ce que
             # Frederic decrit. Les trois spawners portent la table de scripts du decor 3
             # (`0x8C123DA0`) en dur -- l'appelant et le litteral disent la meme chose.
             #
             # LE BLOC DE L'ID 21 : dix octets, {script, x, y, +556}, et son `x`/`y` part
             # en `objet+84`/`+86` et non en `+102`/`+106`. **Que ce soit bien la position
             # se mesure** : les spawners voisins, ids 22 et 24, ecrivent LA MEME valeur
             # aux deux endroits -- 712/56 en +84/+86 et en +102/+106. Ce n'est donc pas
             # une ressemblance de valeurs, c'est un doublon ecrit par le code.
             # LA CHARRETTE ETAIT POSEE DEUX FOIS — 03/09/2026, signale a l'ecran :
             # « le personnage a droite est anime mais un sprite est devant lui ».
             #
             # Le script 2 est une charrette de marchand, 160 x 112. Deux objets la
             # rendent : le DEUXIEME enregistrement de ce bloc (x 752, pose en bx 576) et
             # l'id 22 (x 712, pose en bx 536). Le fumeur anime est en bx 728 : la
             # premiere s'etale de 576 a 736 et **le recouvre**, la seconde de 536 a 696
             # et s'arrete juste avant lui.
             #
             # ON GARDE CELLE DE L'ID 22 ET ON ECARTE L'AUTRE -- et c'est un ARBITRAGE,
             # pas une lecture : les deux enregistrements existent bel et bien dans le
             # binaire, et je n'ai pas su etablir lequel des deux le jeu emploie. Ce qui
             # est mesure, c'est que l'une des deux recouvre le fumeur et l'autre non.
             # `adresses` liste donc les deux enregistrements gardes, sans le deuxieme.
             # LE CHARGEUR 0x8C02356A — trouve le 04/09/2026 en exploitant l'inventaire.
             #
             # C'est LUI qui porte le panneau vertical, et sa position n'est pas celle
             # qu'on lui pretait. Le chargeur ecrit `+102`/`+106`, donc il dit vraiment ou
             # va l'objet -- contrairement au bloc 0x8C17DD58 retire ci-dessous.
             #
             # COMMENT ON A RETROUVE SES TABLES. `spawners2i` rendait « nombres u16 [?] » :
             # l'interpreteur perd la base. Les sept litteraux de la fonction la donnent --
             # une adresse en 0x8C17xxxx pour les nombres, une en 0x8C5F9xxx pour les
             # pointeurs, exactement la forme de 0x8C028792 dont les tables etaient
             # resolues. Ici 0x8C17BBC4 et 0x8C5F9CD0, indexes `arg*8 + z*2` et
             # `arg*16 + z*4`, avec **arg = decor - 1**.
             #
             # DEUX RECOUPEMENTS INDEPENDANTS, parce qu'une forme d'indexation qui
             # « marche » ne prouve rien toute seule :
             #
             #   * le chargeur voisin 0x8C0233B6, meme forme, arg 2, rend EXACTEMENT les
             #     quatre elements statiques de Yun -- 383,32 / 413,69 / 479,64 / 576,64,
             #     que `poser2i` cuit deja ;
             #   * le meme 0x8C02356A, arg 3, rend le punk au blouson Union Jack de Dudley
             #     en x 736, la position mesuree au balayage a 99 %.
             #
             # ET IL CORRIGE UNE ERREUR : il met les paniers (script 4) en 640, la ou le
             # balayage les trouvait peints, et non en 752 comme le bloc invente.
             dict(decor=3, adresse=0x8C17BC5E, nb=5, pas=16,
                  sc=12, x=6, y=8, pal=10, plan=2),
             # RETIRE LE 04/09/2026 — `+84/+86` N'EST PAS UNE POSITION.
             #
             # Le bloc est REEL : `spawners2i.py 0x8C028E62` le lit, dix octets, trois
             # tours, champs `+456` (script), `+84`, `+86`, `+556`. Ce qui ne l'est pas,
             # c'est que `+84/+86` porte la position : **la position d'un WORK est en
             # `+102/+106`, et ce spawner ne l'ecrit JAMAIS**. On l'avait deduit par
             # analogie avec les spawners voisins (ids 22 et 24), qui ecrivent la meme
             # valeur aux deux endroits. Une analogie n'est pas une lecture.
             #
             # ET L'ECRAN LA CONTREDIT TROIS FOIS. Frederic a signale trois fois « le
             # sprite devant l'homme qui fume » : c'est le PANNEAU VERTICAL, pose en 696,
             # qui recouvre le fumeur en 728. Sa capture Dreamcast le montre a l'autre
             # bout, contre les portes rouges -- dans la zone 896-1024 que notre page
             # n'extrait meme pas.
             #
             # On retire donc les deux objets qui en venaient : le panneau (script 0) et
             # les paniers (script 4, peints de toute facon). Ils reviendront quand on
             # saura lire leur vraie position, pas avant.
             #
             # dict(decor=3, adresses=[0x8C17DD58, 0x8C17DD6C], pas=10,
             #      x=2, y=4, sc=0, pal=None, plan=None, plan_fixe=2),
             # ET LES TROIS OBJETS A IMMEDIATS. Leur script n'est ni dans un bloc ni une
             # constante du spawner : la routine le pose depuis un ETAT. On prend le
             # premier etat qui porte des images -- la meme regle que pour la menagerie
             # d'Oro, et le meme controle : elle rend la valeur deja etablie a la main la
             # ou on la connaissait.
             #
             # Ce que la regle laisse de cote, et qu'il faut savoir : l'id 23 a un etat
             # bien plus riche (script 12, TREIZE images) que celui qu'on pose (script 7,
             # une image), et l'id 22 n'a que des poses d'une image (scripts 0, 1, 2).
             # Si une figure sort figee la ou une animation est attendue, c'est ici.
             #
             # `doublons` : l'id 22 joue le script 2, que le bloc de l'id 21 joue deja --
             # mais ce sont DEUX figures, en 712,56 et en 752,84. La garde anti-doublon
             # en mangeait une.
             #
             # L'ID 22 N'EST PAS UNE CHARRETTE -- 16/09/2026. Son spawner pose en `+0x16C` la
             # table `0x8C123E48`, qui est la table du decor 3 DECALEE DE 42 entrees
             # (`routine2i.py` le releve ; l'id 21 est a +36). Son « script 2 » est donc le 44
             # du decor, et le script de repos que sa routine pose a l'etat 0 (`mov #0,r6`,
             # 0x8C029006) est le **42** : un oiseau de 16x16, quatre images. Le 44 n'est pose
             # que si le compteur de coups `u16[0x8C6AF288 + 16]` n'est pas nul. On lisait le
             # script 2 dans la table du decor : la charrette de marchand, posee sur la foule.
             # Frederic : « enlever la charrette ». La charrette du jeu 1 d'elements
             # (`0x8C0233B6`, 479/64) est un autre objet, reel, et reste.
             #
             # LES TROIS OISEAUX DE LA CAGE -- 16/09/2026, nuit. Frederic : « il y a peut-etre
             # plusieurs oiseaux dans la cage ». Il y en a quatre. La cage (id 23) cree, en
             # plus de l'oiseau de l'id 22, trois objets de l'id 21 par `0x8C028E62` : un bloc
             # de dix octets `{script, x, y, priorite, retournement}` en `0x8C17DD58`, sur la
             # table du decor + 36, et leurs vitesses en `0x8C17DD78`.
             #
             # LE RETRAIT DU 04/09 ETAIT UNE ERREUR DE LECTURE : ce spawner ECRIT bien la
             # position, en `+102` et `+106` (sites 0x8C028F14 et 0x8C028F24), a cote de
             # `+84/+86`. Les « panneau » et « paniers » n'existaient pas : le script 0 de
             # la table + 36 est le 36 du decor, un oiseau.
             #
             #   36 en 696,64    38 en 752,84    40 en 752,63, RETOURNE (`+10` = 1)
             #
             # Leur routine (`0x8C028CE8`) les laisse PERCHES tant que la cage n'est pas
             # frappee (`u16[0x8C6AF288 + 16]`) ; frappee, ils s'envolent (37, 39, 41) et
             # sortent de l'ecran. Le port ne brise pas la cage : ils restent perches, et
             # leur script boucle, boucles internes comprises (`deroule`).
             dict(decor=3, doublons=True, immediats=[
                 dict(x=696, y=64, pal=74, plan=2, script=36, col=0x2055, deroule=True,
                      spawner=0x8C028E62),   # id 21
                 dict(x=752, y=84, pal=74, plan=2, script=38, col=0x2055, deroule=True,
                      spawner=0x8C028E62),   # id 21
                 dict(x=752, y=63, pal=74, plan=2, script=40, col=0x2055, deroule=True,
                      miroir=True, spawner=0x8C028E62),   # id 21, retourne
                 dict(x=672, y=48, pal=90, plan=2, script=7,
                      spawner=0x8C02936E),   # id 23
                 dict(x=712, y=56, pal=74, plan=2, script=42,
                      spawner=0x8C02912C),   # id 22, table +42
                 dict(x=728, y=48, pal=91, plan=2, script=24,
                      spawner=0x8C02962E),   # id 24
             ]),
             # Yun : scripts 14, 1, 2 et 3
             dict(decor=3, adresse=0x8C17B9F0, nb=4, pas=16)
            ],
    # NECRO -- blocs appeles par son script d'etage d'index 5, resolus par la table 5.
    # Son premier bloc rend 129 images a lui seul.
    "bg05": [dict(decor=5, adresse=0x8C17C260, nb=5, pas=16),
             dict(decor=5, adresse=0x8C17E838, nb=10, pas=16),
             # ID 18, arg 5 : script 24, neuf images.
             dict(decor=5, adresse=0x8C17DD12, nb=1, pas=24, sc2=12),
             # LE SECOND JEU D'ELEMENTS DE NECRO, DEVANT LES COMBATTANTS -- 16/09/2026.
             # `0x8C02356A` (appele au site 0x8C0DCF9E) rend deux enregistrements, tous deux a
             # la priorite **2** : les chaines qui pendent a gauche (script 0, 160x463, en
             # 168/16) et les tuyaux de droite (script 17, en 880/16). A 2 ils passent devant
             # tout, combattants compris -- la capture de 2I le montre pour les chaines. Une
             # vieille cuisson les avait peintes dans la page proche, a 84 : derriere.
             # `col` est leur `+554` (octets 4 de l'enregistrement : 0x40 et 0x2040).
             dict(decor=5, immediats=[
                 dict(x=168, y=16, pal=2, plan=2, script=0, col=0x40),
                 dict(x=880, y=16, pal=2, plan=2, script=17, col=0x2040),
             ]),
             # LE PREMIER JEU D'ELEMENTS DE NECRO -- 16/09/2026, site 0x8C0DCF98, index 15.
             # Trois pieces de la grande machine du fond : un tuyau vertical (script 3), la
             # tete rouge du broyeur (script 4) et la bouche du four (script 5). Aucune n'etait
             # posee ; elles laissaient un trou au milieu du decor.
             dict(decor=5, immediats=[
                 dict(x=504, y=192, pal=75, plan=2, script=3, col=0x2040),
                 dict(x=552, y=152, pal=75, plan=2, script=4, col=0x2040),
                 dict(x=499, y=168, pal=76, plan=2, script=5, col=0x40),
             ]),
             # LE CONDUCTEUR ET SA GRILLE -- 16/09/2026. Frederic : « absence du conducteur du
             # train ». Deux spawners a immediats que rien n'atteignait :
             #
             #   8C0DCFB0  0x8C023756  id 7  -> table du decor +34, script 0 = le script 34
             #   8C02380A  0x8C0238DC  id 8  -> table du decor +18, script 0 = le script 18
             #
             # Ils n'ecrivent NI `+102` NI `+106` : leur position est en `+84`/`+86`, masquee
             # par 0x3FF. Lues dans le code : (463, 77) et (432, 118). Le reste est en dur --
             # `+552` = 0x4200 (col_mode), `+554` = **89** et 0x2040 (col_code), `+558` = 2
             # (plan), `+556` = 64 (profondeur). Avec le col_code 89 l'homme sort en blouse
             # grise, penche sur le pupitre de la machine : c'est le conducteur.
             dict(decor=5, immediats=[
                 dict(x=463, y=77, pal=64, plan=2, script=34, col=89),
                 dict(x=432, y=118, pal=64, plan=2, script=18, col=0x2040),
             ])],
    # HUGO -- blocs appeles par son script d'etage d'index 6, resolus par la table 6
    # (pas de decalage). ATTENTION : c'est un decor A VARIANTES, ses trois aires
    # different (2/3/3 elements) -- on ne lit ici que l'AIRE 0. Voir PROMPT-SUITE,
    # chantier 1 bis.
    # L'OBJET A IMMEDIATS DE HUGO — trouve le 04/09/2026 en chainant les trois outils.
    #
    # `8C031B56` alloue, pose l'id 63 en `+8`, et ecrit tout le reste en constantes :
    # x 816, y 52, palette 74, `my_priority` 74, `my_family` 2. Son script n'est nulle part
    # dans le spawner -- c'est sa ROUTINE (`8C031918`) qui le pose, et `etats2i` en releve
    # trois : 30 (une image), 32 (trois) et **34 (VINGT ET UNE)**. On prend le plus riche,
    # comme pour la paire repos/action.
    #
    # Il etait invisible aux deux inventaires : `blocs2i` ne lit que les chargeurs a bloc,
    # et la recherche « script en constante » ne le voyait pas non plus.
    # DEUX DECORS QUI N'AVAIENT AUCUNE ENTREE — trouves le 04/09/2026.
    #
    # `bg0c` (etage 33) et `bg0e` (etage 35) n'etaient dans TABLES ni l'un ni l'autre : la
    # chaine ne leur posait AUCUN objet anime. Leurs objets viennent des chargeurs partages
    # `8C0233B6` et `8C02356A`, dont l'argument n'est pas capture au site d'appel -- il
    # vaut **decor - 1**, la convention etablie au §5s -- et dont les tables sont
    # `8C17B918`/`8C5F9C04` et `8C17BBC4`/`8C5F9CD0`.
    #
    # `bg0e` en a onze, repartis sur TROIS variantes de z, et deux sont richement animes :
    # le script 15 (seize images) et le 26 (neuf).
    "bg0c": [dict(decor=11, adresse=0x8C17C330, nb=1, pas=16,
                  sc=12, x=6, y=8, pal=10, plan=2),
             # Ken : scripts 0, 4, 3 et 1 -- le rang 2 (script 2) est deja porte
             dict(decor=11, adresses=[0x8C17BB44, 0x8C17BB54, 0x8C17BB74, 0x8C17BB84], pas=16)
            ],
    # BG0E : ENTREES RETIREES, FAUTE DE SPRITES — 04/09/2026.
    #
    # Le code lui donne onze objets sur trois variantes de z, par les chargeurs partages
    # `8C0233B6` et `8C02356A` a l'argument 12. Mais leurs images portent des index
    # **43594 a 43823**, et le `.pk` de bg0e ne charge que `F_ETC94`, dont l'intervalle est
    # 45400..45448. Aucun conteneur qu'il charge ne les contient : ces blocs ne sont donc
    # pas les siens, et la convention « arg = decor - 1 » ne vaut pas ici.
    #
    # RIEN A EXTRAIRE DU DISQUE : `decoupe.py` lit les tables de l'executable, et les seize
    # `F_ETC` de 2nd Impact sont tous deja sortis. `b07`, `b0f`, `b11`, `b13`, `b14` et
    # `b16` n'ont QU'UNE partie -- leur `.pvc` -- et pas de `F_ETC` du tout : ces decors
    # n'ont aucun sprite anime, c'est la donnee du jeu, pas une lacune de notre chaine.
    # LE TONNEAU QUI SE BRISE -- 23/09/2026. Frederic : « dans le decor d'Hugo, le tonneau
    # a l'extremite droite du decor se brise », et « la destruction ne se joue pas en
    # boucle, mais une seule fois, avec la derniere image de l'animation persistante ».
    #
    # On posait le script 34, qui est la SECONDE destruction (vingt-trois images) : le
    # tonneau jouait donc sa ruine en boucle, sans arret. L'etat 0 de l'id 63 choisit en
    # realite son script sur un compteur qui survit a la manche -- 31 intact, 33 fele,
    # 30 detruit -- et c'est 31 qu'il faut poser.
    #
    # Suite 0 : le script 31, intact, en boucle. Suite 1 : le script 32, la rupture, JOUEE
    # UNE FOIS. `boite` est celle du type 7 (`0x8C1D3ED4 + 7*8`), dans le repere du DC.
    # LES DEUX JEUX D'ELEMENTS STATIQUES DE HUGO -- 24/09/2026.
    #
    # Frederic, quatre fois : « les 2 poteaux et la corde doivent etre au premier plan ».
    # Il avait raison chaque fois, et la preuve etait chez son jumeau.
    #
    # **HUGO BIS LES POSE DEJA**, et sa fiche `a57o4` porte **z 19** -- devant les
    # combattants, qui sont a 28..56. Hugo, lui, ne posait que son tonneau : ses elements
    # restaient cuits dans la page proche, a 84, derriere tout le monde.
    #
    # Les deux jeux se lisent dans les memes tables que ceux de Hugo bis :
    #
    #     premier jeu (0x8C17B918 / 0x8C5F9C04) : 512,144 z 82 sc 17 ; 464,78 z 76 sc 4
    #     second  jeu (0x8C17BBC4 / 0x8C5F9CD0) : 224,12  z 20 sc 19 ; 666,62 z 74 sc 26
    #                                             686,25  z 19 sc 27 ; 624,145 z 82 sc 24
    #
    # **19 et 20 sont devant les combattants.** Le `686,25 script 27` couvre x 686 a 926 :
    # c'est la paire de poteaux et sa corde. Le `224,12 script 19` est celle de gauche.
    #
    # LE SECOND JEU N'ETAIT LU POUR PERSONNE d'autre que la variante d'Elena. C'est la
    # lacune : `etages.elements_statiques` ne lit que le premier, et rien n'allait chercher
    # le second pour les quinze autres decors.
    #
    # La copie peinte dans la page reste : elle est exactement sous le sprite, a 84, donc
    # invisible des que celui-ci passe -- c'est ce que fait le Dreamcast lui-meme, dont la
    # banque porte les poteaux ET l'element.
    "bg06": [dict(decor=6, immediats=[dict(script=31, x=816, y=52, pal=74, plan=2,
                                           spawner=0x8C031B56, comportement=9,
                                           suites=[31, (32, "une")],
                                           boite=(6, 64, 33, 69)),
                                      # LES AIRES DE HUGO -- 25/09/2026. Frederic :
                                      # « *porte aussi les douze de hugo, ajoute une
                                      # variante par aire* ». Ses deux spawners lisent
                                      # `bloc = table[decor*12 + aire*4]`, et les trois
                                      # aires donnent trois blocs :
                                      #
                                      #   aire 0  8C17BA9E : sc 17, 4
                                      #           8C17BD1E : sc 19, 26, 27, 24
                                      #   aire 1  8C17BABE : sc 20, 22, 4
                                      #           8C17BD5E : sc 15, 26, 27, 24
                                      #   aire 2  8C17BAEE : sc 20, 21, 22
                                      #           8C17BD5E : les memes
                                      #
                                      # D'ou un masque par objet -- bit 0 = manche 1.
                                      dict(x=512, y=144, pal=82, plan=2, script=17, col=0x2040, aires=0x1),
                                      dict(x=464, y=78, pal=76, plan=2, script=4, col=0x2064, aires=0x3),
                                      dict(x=336, y=81, pal=80, plan=2, script=20, col=0x2040, aires=0x6),
                                      dict(x=512, y=70, pal=83, plan=2, script=22, col=0x2040, aires=0x6),
                                      dict(x=448, y=56, pal=73, plan=2, script=21, col=0x2040, aires=0x4),
                                      dict(x=224, y=12, pal=20, plan=2, script=19, col=0x2040, aires=0x1),
                                      dict(x=688, y=56, pal=73, plan=2, script=15, col=0x0064, aires=0x6),
                                      dict(x=666, y=62, pal=74, plan=2, script=26, col=0x2040),
                                      dict(x=686, y=25, pal=19, plan=2, script=27, col=0x2040),
                                      dict(x=624, y=145, pal=82, plan=2, script=24, col=0x40)]),
             dict(decor=6, adresse=0x8C17C2B0, nb=2, pas=16),
             dict(decor=6, adresse=0x8C17E8D8, nb=3, pas=16),
             # LE BLOC DU SPAWNER DEDIE, enfin lisible -- 02/09/2026.
             #
             # `chargeurs2i` nommait `0x8C036480 porte 0x8C17F54C` depuis le debut, sans
             # que la chaine l'exploite : on ne savait pas son format. Le desassemblage le
             # donne -- neuf `mov.w @r14+` de deux octets, donc 18 par enregistrement, et
             # chaque champ va a un offset d'objet ecrit en clair dans le code :
             #
             #     champ 1 -> objet+558 PLAN     champ 5 -> objet+88  PALETTE
             #     champ 2 -> objet+554 DRAPEAUX champ 6 -> objet+456 SCRIPT
             #     champ 3 -> objet+102 X        champ 4 -> objet+106 Y
             #
             # 558 et 556 ne sont pas devines : un `mov.w @(disp,PC)` les charge, et
             # 554 = 558-4, 456 = 556-100.
             #
             # Les deux premiers enregistrements ont des x,y a 0 et 1 -- un en-tete, pas
             # des objets -- d'ou le saut de 2*18. Le `+2` final aligne `plan` sur l'offset
             # 0 que `objets()` attend, si bien que les offsets par defaut (x+4, y+6,
             # script+10) retombent juste.
             # CORRIGE LE 02/09 : c'est `0x8C17F584`, UN enregistrement, pas quatre a
             # `0x8C17F54C + 38`. Voir le commentaire en tete de `TABLES` -- l'ancienne
             # adresse lisait la table des NOMBRES du spawner comme un bloc, et les trois
             # objets de trop appartenaient a Yun et a un argument que personne n'appelle.
             dict(decor=6, adresse=0x8C17F584, nb=1, pas=18),
             # ID 18, arg 3, z 0 : scripts 7, 9 et 11 -- 10, 12 et 24 images. Le script 7
             # est celui que la chaine posait par erreur depuis le bloc mal lu ci-dessus.
             # Il est bien a Hugo ; il y revient simplement par le bon chemin.
             dict(decor=6, adresse=0x8C17DC22, nb=3, pas=24, sc2=12)],
    # DUDLEY -- chargeur 0x8C02E1FE arg 2, appele depuis la BANDE 4 (= decor 4).
    "bg04": [dict(decor=4, adresse=0x8C17E828, nb=1, pas=16),
             # LE SPAWNER DEDIE DE DUDLEY, `0x8C0323F0` (id 66), argument 0 -- le meme
             # spawner qu'Alex, qui passe 2. Enregistrement de 24 octets pointe droit sur
             # son champ 0, d'ou `x=6, y=8, sc=12`. Script 4, treize images.
             dict(decor=4, adresse=0x8C17F2D8, nb=1, pas=24, x=6, y=8, sc=12),
             # ID 18, arg 6 : script 2, une image.
             dict(decor=4, adresse=0x8C17DD2A, nb=1, pas=24, sc2=12),
             # UN PUNK AU SKATEBOARD — 03/09/2026, signale a l'ecran : « des animations
             # sont manquantes : 3 jeunes punks ».
             #
             # Sa routine d'etage appelle `0x8C032B32` (site 0x8C0DCD62, argument 0), un
             # spawner a IMMEDIATS que la chaine ignorait : id 68, x 672, y 47,
             # palette 75, plan 2, script 6 -- huit images. Sa routine confirme le meme
             # script dans son etat 0.
             #
             # LES DEUX AUTRES PUNKS NE SONT PAS TROUVES. Les scripts 5 (dix images), 7
             # (treize) et 10 les montrent, et rien dans son arbre de spawners ne les
             # cree. C'est ce qui reste a chercher chez lui.
             dict(decor=4, immediats=[
                 dict(x=672, y=47, pal=75, plan=2, script=6, spawner=0x8C032B32),
             ]),
             # Dudley, premier spawner : scripts 9 et 8
             dict(decor=4, adresse=0x8C17BA50, nb=2, pas=16),
             # Dudley, second spawner : scripts 1 et 10
             dict(decor=4, adresse=0x8C17BCE0, nb=2, pas=16)
            ],
    # ELENA -- chargeur 0x8C025A9A arg 6, appele depuis la BANDE 9. Et la bande 9 est le
    # decor 8 : `0x8C1D591C` donne decor 8 -> bandes 8, 9, 9. C'est la lecture par la
    # bande qui le dit ; lu comme « decor 9 » ce bloc allait a Oro.
    #
    # SA TABLE DE SCRIPTS EST CELLE DE L'AIRE 1 -- 15/09/2026, nuit. Le bloc etait lu avec la table
    # du decor (aire 0, `0x8C129180`, celle du pont) et l'asset du decor (F_ETC30) : son
    # script 1 y est une FALAISE du pont, une image. Dans la table de la bande 9
    # (`0x8C1299DC`, index (8*3+1)) le script 1 est LE FEU d'Elena 1 : dix images de huit
    # trames, dans F_ETC31, palettes a partir de 1365 (le premier transfert de la bande 9,
    # comme ses elements statiques). C'etait le feu fige peint dans la page, et une falaise
    # etrangere posee sous le pont de l'etage 30.
    "bg08": [dict(decor=8, adresse=0x8C17C310, nb=1, pas=16, etage=30,
                  aire=1, asset="2i-b08-F_ETC31.bin", base_palette=1365),
             # LE SPAWNER DEDIE D'ELENA, `0x8C03CBCC`, appele une seule fois dans tout le
             # binaire depuis sa routine d'etage (site 0x8C0DDB60), bloc EN DUR et sans
             # argument. Enregistrements de HUIT octets {x, y, palette, script}, le meme
             # format que celui de Gill. Sa boucle compare a `mov #4,r8` : quatre
             # enregistrements, et les quatre se resolvent -- scripts 8, 9, 10 et 11,
             # douze images chacun, en 784/32, 720/64, 240/32 et 304/64. Le cinquieme et
             # les suivants sont du bruit, ce qui recoupe la borne lue dans le code.
             #
             # MAIS IL APPARTIENT A LA BANDE 8 -- 16/09/2026. Son site 0x8C0DDB60 est dans
             # la routine de la bande 8 (0x8C0DDA1C..0x8C0DE0A3), pas dans celle de la
             # bande 9 (0x8C0DE0A4..) qui appelle le chargeur ci-dessus. Ses herbes et sa
             # corde a crane sont celles du PONT, la variante montee a l'etage 56.
             #
             # ET ILS NE S'ANIMENT PAS PENDANT LE COMBAT -- 15/09/2026, nuit. Les quatre sont l'id
             # 122, routine `0x8C03CAD8` :
             #     etat 0  pose le script (0x8C0B4AD4), passe a 1
             #     etat 1  N'AVANCE PAS le script ; attend u16[0x8C6B0AA4] != 0
             #     etat 2  avance (0x8C0B51F2) jusqu'a la fin du script, UNE fois
             #     etat 3  attend u16[0x8C6AF3E8 + 6] >= 2, puis l'objet s'efface
             # `0x8C6B0AA4` appartient au pont (id 123, routine `0x8C03CC98`) : zero a sa
             # naissance, UN quand, en chute (`0x8C0D7B5A`), son `y` passe sous 40
             # (0x8C03CD2C). C'est la chute du pont qui les fait jouer ; tant qu'il tient,
             # herbes et cordes restent sur l'image 0.
             # Frederic voyait les cordes tourner en boucle.
             dict(decor=8, adresse=0x8C17FD04, nb=4, pas=8, etage=56, fige=True),
             # Elena, AIRES 1 et 2 (bande bg09) : script 2
             dict(decor=8, adresse=0x8C17BB22, nb=1, pas=16, etage=30),
             # Elena, aires 1 et 2, second spawner : le meme script 2
             dict(decor=8, adresse=0x8C17BE32, nb=1, pas=16, etage=30),
             # Elena, AIRE 0 (bande bg08) : neuf objets, scripts 2 a 14
             dict(decor=8, adresse=0x8C17BDA2, nb=9, pas=16, etage=56)
            ],
    "bg0a": [dict(decor=9, adresse=0x8C17E918, nb=8, pas=16),
             # LES CHAUVES-SOURIS D'ORO — 02/09/2026, id 74, spawner `0x8C033FC2`.
             #
             # C'est le premier morceau de sa menagerie qu'on retrouve, et il a fallu
             # REMONTER le graphe d'appels : aucune enumeration descendante n'atteignait
             # ce spawner. `remonter2i.py` part de la fonction et cherche qui charge son
             # adresse -- par litteral ou dans une table de pointeurs -- jusqu'a tomber
             # dans une routine d'etage. Celle-ci est atteinte depuis la BANDE 10, qui est
             # le decor 9, Oro.
             #
             # DEUX CHEMINS INDEPENDANTS DISENT LE MEME DECOR, et c'est ce qui l'etablit :
             # l'appelant (bande 10 -> decor 9) et la table de scripts que le spawner
             # porte EN DUR, `0x8C12AB8C`, qui est celle du decor 9.
             #
             # Enregistrements de six octets {x, y, palette} et rien d'autre : ni plan
             # (le spawner ecrit 2 en dur) ni script. Le script vient de la ROUTINE, qui
             # recopie une table de quatre pointeurs sur la pile et l'indexe par le `type`
             # de l'objet -- lequel est le rang de l'enregistrement (`mov.b r11,@(4,r4)`,
             # r11 etant le compteur de boucle). Les quatre routines posent les scripts
             # **35, 34, 34, 34**.
             #
             # Et le catalogue de la menagerie, etabli par les sprites eux-memes, donne
             # les scripts 32 a 39 aux CHAUVES-SOURIS. Quatre d'entre elles, en 567/288,
             # 396/320, 502/337 et 535/313 -- haut dans la grotte, ou des chauves-souris
             # ont leur place.
             #
             # La routine ecrit `+102`/`+106` en plus de `+84`/`+86` : elles se DEPLACENT.
             # On les pose a leur position de depart, celle du bloc, comme partout
             # ailleurs.
             dict(decor=9, adresse=0x8C17F38C, nb=4, pas=6,
                  x=0, y=2, pal=4, plan=None, plan_fixe=2,
                  scripts=[35, 34, 34, 34], doublons=True),
             # LE RESTE DE LA MENAGERIE D'ORO — 02/09/2026, ET IL N'A AUCUN BLOC.
             #
             # C'est la plus vieille enigme du chantier, et la reponse est qu'on cherchait
             # une chose qui n'existe pas. Le chat, le chien et le perroquet n'ont pas
             # d'enregistrement : leur spawner ecrit x, y, palette, plan et la table de
             # scripts en IMMEDIATS, et le numero de script est pose par la ROUTINE de
             # l'objet. Trois enregistrements avaient ete essayes au juge et rejetes a
             # l'ecran ; il n'y en avait pas a trouver.
             #
             # LA ROUTINE D'ETAGE D'ORO, `0x8C0DE548` (bande 10), les appelle en clair :
             #
             #     8C0DE5C2  jsr 8C033FC2   id 74  les chauves-souris (bloc, ci-dessus)
             #     8C0DE5CE  jsr 8C030546   id 55  LE PERROQUET
             #     8C0DE5FA  jsr 8C0338E8   id 72  LE GROS CHAT
             #     8C0DE61A  jsr 8C03369E   id 71  LE CHIEN
             #
             # SA MENAGERIE A QUATRE VARIANTES, ET C'EST LE TIRAGE `z` QUI CHOISIT.
             #
             # Frederic l'a vu sur des videos avant qu'on le lise : « j'ai 2 versions du
             # decor, avec les sprites qui changent ». Le repartiteur est en clair juste
             # apres le perroquet, en `0x8C0DE5D2`, et il lit `u8[0x8C6AF30A]` --
             # c'est-a-dire **contexte+6, le tirage** :
             #
             #     z 0 -> 8C0DE61A   LE CHIEN seul
             #     z 1 -> 8C0DE5EC   le chat + les chatons, PUIS le chien
             #     z 2 -> 8C0DE602   le chat + les chatons, SANS le chien (jmp, pas jsr)
             #     z 3 -> 8C0DE61A   LE CHIEN seul
             #
             # Le perroquet et les chauves-souris sont appeles AVANT le repartiteur :
             # eux sont de toutes les variantes.
             #
             # **ON CUIT LES QUATRE**, et c'est le MOTEUR qui tire, comme le jeu le fait.
             # Chaque fiche porte un masque `variante` -- un bit par valeur de `z` -- et
             # `DecorObjets_Combien` ne compte que ceux du tirage courant. `0xF` = de
             # toutes les variantes, ce qui est le cas de tout le reste du port.
             #
             #     le chat, les chatons -> z 1 et 2    -> 0b0110 = 0x6
             #     le chien             -> z 0, 1 et 3 -> 0b1011 = 0xB
             #     le perroquet, les chauves-souris    -> 0xF, avant le repartiteur
             #
             # `SF3_DECOR_VARIANTE=0..3` force le tirage : c'est ce qui permet de voir les
             # quatre a la demande au lieu d'attendre le hasard.
             #
             # Chaque spawner porte EN DUR la table de scripts `0x8C12AB8C`, celle du
             # decor 9 : l'appelant et le litteral disent la meme chose, et aucun n'a
             # servi a caler l'autre.
             #
             # LE SCRIPT est celui que la routine pose dans son PREMIER etat -- le premier
             # appel a `0x8C0B4AD4` dans l'ordre des adresses. Le controle est les
             # chauves-souris : la meme lecture y rend le script 35, celui qu'on avait
             # etabli a la main.
             #
             # Et les scripts tombent sur le catalogue de la menagerie, etabli il y a des
             # jours par les sprites eux-memes et sans rapport avec ce chemin :
             #
             #     id 72 -> 13 et 51   le gros chat couche, puis qui se redresse
             #     id 71 -> 29, 30, 40, 41   le chien
             #     id 55 -> 20, 21, 26       le perroquet
             #
             # LES CHATONS : C'EST LA MERE QUI LES CREE — 02/09/2026.
             #
             # Aucun appelant ne menait a l'id 73, et pour cause : il n'est pas appele
             # depuis la routine d'etage. **Le spawner du CHAT le cree**, en dernier
             # geste, au site `0x8C033966` -- `jsr 0x8C033ACC`. La chatte fait ses
             # chatons.
             #
             # Le spawner des chatons, `0x8C033ACC`, ecrit lui aussi tout en immediats et
             # porte la meme table de scripts `0x8C12AB8C` : id 73, x 493, y 81,
             # palette 75, plan 2. Ils sont a COTE de leur mere, qui est en 411, 80 --
             # un recoupement qui ne coute rien et qui dit beaucoup.
             #
             # Script 17, douze images, par la meme regle du premier etat.
             #
             # LE CHIEN A DEUX VIES, ET CE SONT LES COMBATTANTS QUI CHOISISSENT -- 16/09/2026.
             # Frederic : « le chien est revenu mais il n'est peut-etre pas a la bonne
             # place ». Il ne l'etait pas. Son spawner (`0x8C03369E`) n'ecrit PAS sa
             # position en dur : il lit le personnage des deux joueurs (`plw + 0x358`) et
             #
             #   * si l'un d'eux est Ibuki, Elena ou Oro -> type 0, x 0x260 = 608, y 53 :
             #     le chien DEBOUT (routine `0x8C03331C`) ;
             #   * sinon                               -> type 1, x 0x2BC = 700, y 56 :
             #     le chien COUCHE (routine `0x8C03360C`).
             #
             # Le port posait le script 29 -- un chien debout qui aboie -- a la place du
             # chien couche. Le « premier etat » ne suffisait pas : il y a deux routines.
             #
             # DEBOUT, il suit du regard le combattant qu'il prefere (`0x8C17F364` : Ibuki
             # et Elena 1, Oro 2 ; a egalite, la camera). Script 28 tenu, entre a
             # l'enregistrement 0, 2 ou 4 : gauche, face, droite. Il remue la queue
             # (script 30) quand un ami est devant lui, et aboie (script 29) quand un
             # combattant lance un coup special (`0x8C0D7EFC`).
             # COUCHE, il joue le script 40 en boucle et se redresse (script 41) sur le
             # meme coup special.
             dict(decor=9, immediats=[
                 dict(x=411, y=80, pal=75, plan=2, script=13, variante=0x6,
                      spawner=0x8C0338E8),   # le gros chat couche      z 1, 2
                 dict(x=608, y=53, pal=74, plan=2, script=28, variante=0xB | AVEC_AMI,
                      comportement=1, suites=[[(28, 0), (28, 2), (28, 4)], (30, "une"), (29, "une")],
                      spawner=0x8C03369E),   # le chien debout          z 0, 1, 3
                 dict(x=700, y=56, pal=74, plan=2, script=40, variante=0xB | SANS_AMI,
                      comportement=2, suites=[40, (41, "une")],
                      spawner=0x8C03369E),   # le chien couche          z 0, 1, 3
                 dict(x=672, y=114, pal=86, plan=2, script=20,
                      spawner=0x8C030546),   # le perroquet             toutes
                 dict(x=493, y=81, pal=75, plan=2, script=17, variante=0x6,
                      spawner=0x8C033ACC),   # les chatons, par la mere z 1, 2
             ]),
             # ID 18, arg 4 : script 15, ZERO image -- rien a poser, garde pour memoire.
             # `sc2` MANQUAIT, et l'objet disparaissait en silence. Ce bloc porte la paire
             # repos/action comme ses voisins : repos 15, qui a ZERO image, et action 16,
             # qui en a deux. Sans `sc2=12` on lisait le repos, donc rien -- Oro perdait un
             # objet que le code pose. Trouve par le balayage « ce que le code donne et que
             # la chaine ignore », le 04/09/2026.
             #
             # ET IL N'EST QUE DES VARIANTES DU CHAT -- 16/09/2026. La routine d'etage
             # (`0x8C0DE5D2`) n'appelle `0x8C028792` arg 4 que dans les branches z 1 et z 2,
             # juste avant le chat ; il etait pose dans les quatre.
             dict(decor=9, adresse=0x8C17DCFA, nb=1, pas=24, sc2=12, variante=0x6),
             # `0x8C025A9A` arg 7, dans les memes deux branches : UN enregistrement,
             # script 19 (seize images de 32x16), en 472/88, palette 76. Il manquait.
             dict(decor=9, adresse=0x8C17C320, nb=1, pas=16, variante=0x6),
             # Oro : script 7, x 656
             dict(decor=9, adresse=0x8C17BE42, nb=1, pas=16)
            ],
    # YANG -- appele depuis la BANDE 11, et la bande 11 est le decor 10. Le « decalage
    # d'un cran » que ce commentaire disait inexplique n'existe pas : l'index de
    # `0x8C1D3FB4` est la BANDE, pas le decor. Voir SANS-ETAT.md, 01/09/2026.
    # YANG -- appele depuis la BANDE 11, et la bande 11 est le decor 10.
    #
    # LE LECTEUR DE L'ID 25, TROUVE EN DEPOUILLANT LA TABLE D'EFFETS -- 02/09/2026.
    # `effets2i.py` balaie les 196 entrees de `0x8C179FDC` et ne retient que les spawners
    # qui LISENT UN BLOC. Celui-ci, `0x8C029B00`, etait le seul atteint depuis un script
    # d'etage que la chaine ignorait encore. Il prend son bloc dans
    # `u32[0x8C5F9EAC + arg*4]`, un enregistrement par appel, et **Yang l'appelle TROIS
    # fois** -- sites 0x8C0DCAB6, 0x8C0DCABA et 0x8C0DCABE, args 0, 1 et 2, tous les trois
    # dans sa propre routine.
    #
    # Enregistrement de 30 octets, le script au champ 6 (octet 12) : les offsets par
    # defaut retombent juste depuis `pointeur + 2`. Scripts 65, 63 et 3, une image
    # chacun -- ce sont des poses fixes, pas des animations.
    "bg0b": [dict(decor=10, adresse=0x8C17C250, nb=1, pas=16),
             dict(decor=10, adresse=0x8C17E998, nb=1, pas=16),
             # LES TROIS STATUES QUI SE BRISENT (id 25, `0x8C029B00`) -- 23/09/2026.
             # Frederic : « pour les decors de Yun et Yang, ce sont les cages d'oiseaux et
             # la statue qui se brisent ».
             #
             # `DECORS.md` le savait depuis le 16/09 sans en tirer la consequence : « leurs
             # enregistrements portent trois scripts de plus -- (70, 72, 66), (69, 73, 64),
             # (22, 74, 0) -- qui sont le rocher sculpte, le guerrier vert et le personnage
             # de droite BRISES au fil du combat. Seul le premier etat est pose. »
             #
             # L'id 25 a QUATRE sites d'appel au test de contact `0x8C0D7D74` ; chacun
             # avance d'un cran et pose le script suivant (`objet[+54]`). Le TYPE, qui
             # choisit la boite, est l'ARGUMENT de l'appel -- `0x8C029B0C` range `r4` et
             # `0x8C029B64` le recopie en `+4` -- donc 0, 1 et 2, dans l'ordre des appels.
             #
             #   statue     intact    ruptures        boite (type)
             #   rocher     65 33027  70 33029, 72 33026   0 : -159, 48, 65, 93
             #   guerrier   63 33025  69 33030, 73 33028   1 :   90, 63, 98, 45
             #   personnage  3 32710  22 (13 images), 74   2 :    5, 61, 41, 40
             #
             # Le troisieme script des deux premieres (66, 64) porte LA MEME image que le
             # deuxieme : c'est l'etat de repos, pas un cran de plus. Et le `0` de la
             # troisieme n'est pas le script 0 -- la lanterne -- mais un « aucun ».
             dict(decor=10, immediats=[
                 dict(x=512, y=32, pal=81, plan=2, script=65, spawner=0x8C029B00,
                      comportement=9, suites=[65, (70, "une"), (72, "une")],
                      boite=(-159, 48, 65, 93)),
                 dict(x=527, y=49, pal=84, plan=2, script=63, spawner=0x8C029B00,
                      comportement=9, suites=[63, (69, "une"), (73, "une")],
                      boite=(90, 63, 98, 45)),
                 dict(x=751, y=48, pal=90, plan=2, script=3, spawner=0x8C029B00,
                      comportement=9, suites=[3, (22, "une"), (74, "une")],
                      boite=(5, 61, 41, 40))]),
             # LES CINQ ELEMENTS DE YANG -- 16/09/2026. Sa routine d'etage appelle les deux
             # chargeurs d'elements (index 30). AUCUN n'est dans la banque d'origine : ils
             # etaient cuits dans la page par une ancienne passe, a la profondeur de la page.
             # Or deux d'entre eux passent DEVANT les combattants dans 2I -- Frederic : « un
             # objet cote gauche doit etre devant les combattants, la plante a droite aussi » :
             #
             #   jeu 1  512/176  script 0   la lanterne      84
             #          352/21   script 1   la grue          20   <- devant
             #   jeu 2  288/32   script 2   le cabinet       88
             #          512/128  script 9   le petit bambou  103
             #          736/24   script 62  le grand bambou  23   <- devant
             #
             # La grue etait meme invisible : cuite a la profondeur de la page, elle passait
             # derriere le rocher sculpte (script 65, a 81).
             dict(decor=10, immediats=[
                 dict(x=512, y=176, pal=84, plan=2, script=0, col=0x2040),
                 dict(x=352, y=21, pal=20, plan=2, script=1, col=0x2040),
                 dict(x=288, y=32, pal=88, plan=2, script=2, col=0x2040),
                 dict(x=512, y=128, pal=103, plan=2, script=9, col=0x2040),
                 dict(x=736, y=24, pal=23, plan=2, script=62, col=0x2040)]),
             # LE MONSIEUR EN VERT -- id 28, cree par `0x8C02AE4E` (appele par pointeur depuis
             # `0x8C02A434`, donc hors de la liste de `routine2i`). Tout est en dur : x 496,
             # y 64, `+556` = 83, `+554` = 0x50, et `+0x16C` = la table du decor + 76 -- ses
             # scripts sont les 76 a 81, six animations (19, 8, 20, 7, 41 et 24 images). La
             # page en portait une cuisson BROUILLEE, deux tetes et des blocs decales :
             # « monsieur en vert mal affiche ». On pose son attente, le 76.
             #
             # LES POISSONS -- id 29, `0x8C02B356` arg 2. Deux enregistrements de six octets
             # {x, y, profondeur} ; le premier prend la table + 82, le second la table + 86
             # (`tst r13` en 0x8C02B3D2). `+554` = 0x50. Frederic : « poissons manquants
             # dans l'aquarium » -- l'aquarium est l'objet du script 61, en 128..272.
             #
             # ILS NAGENT -- 16/09/2026, nuit. Frederic : « verifie le 2eme poisson noir ».
             # La routine de l'id 29 (`0x8C02AEEC`) choisit par le `type` :
             #
             #   ROUGE (`0x8C02AF90`)  va-et-vient : nage a gauche (82) a -0,375 px par
             #     trame jusqu'a x 160, demi-tour (83), nage a droite (84) jusqu'a 240,
             #     demi-tour (85).
             #   NOIR  (`0x8C02B0C8`)  le tour de l'aquarium : 86 en haut, a droite jusqu'a
             #     256, a gauche jusqu'a 128, a droite jusqu'a 256 ; tourne (87) ; plonge en
             #     diagonale (88) jusqu'a y 112 ; se retourne (89) ; file a gauche au fond
             #     (90) jusqu'a 160 ; tourne (91) ; remonte (92) jusqu'a y 151.
             #
             # Le port les posait IMMOBILES, chacun sur son premier script. Les demi-tours
             # changent d'etat dans la trame : leur image marquee ne se voit pas ("sans").
             dict(decor=10, doublons=True, immediats=[
                 dict(x=496, y=64, pal=83, plan=2, script=76, col=0x50,
                      spawner=0x8C02AE4E),
                 dict(x=240, y=136, pal=86, plan=2, script=82, col=0x50,
                      comportement=3,
                      suites=[(82, "boucle"), (83, "sans"), (84, "boucle"), (85, "sans")],
                      spawner=0x8C02B356),
                 dict(x=128, y=148, pal=86, plan=2, script=86, col=0x50,
                      comportement=4,
                      suites=[86, (87, "sans"), 88, (89, "sans"), (90, "boucle"),
                              (91, "sans"), 92],
                      spawner=0x8C02B356)])],
    # SEAN -- chargeur 0x8C02E1FE arg 8, appele depuis la BANDE 13 (= decor 12), au site
    # 0x8C0DEB7A. Deux enregistrements : le script 6 (30 images) et le script 7, qui est
    # LE SINGE -- le seul objet du port dont la provenance manquait, et qui se trouvait
    # ici. Recoupements : sprite 18 egal a 2560 pixels sur 2560, durees identiques au C,
    # et `x 736 y 208 script 7` unique dans tout le binaire.
    "bg0d": [dict(decor=12, adresse=0x8C17E9A8, nb=2, pas=16),
             # ID 18, arg 7 : script 8, trois images.
             dict(decor=12, adresse=0x8C17DD42, nb=1, pas=24, sc2=12),
             # LES CINQ ELEMENTS STATIQUES DE SEAN -- 16/09/2026. Sa routine d'etage
             # `0x8C0DEAD8` appelle les deux chargeurs d'elements (`routine2i.py 13`) :
             #
             #   8C0DEB64  0x8C0233B6  jeu 1  index 36 : 575/128 script 3, 431/176 script 4
             #   8C0DEB6A  0x8C02356A  jeu 2  index 36 : 273/176 script 0, 671/96 script 5,
             #                                           655/48 script 2
             #
             # Aucun n'etait pose, et ils ne sont PAS peints dans sa banque : elle est
             # **decoupee a leur silhouette**. Quatre des cinq trous tombent sur la
             # position calculee a un pixel pres -- voir `poser2i.sol`. Sans eux, Sean
             # montre des trous a la place du conducteur de la voiture, de l'homme a
             # genou, du poteau et d'un palmier.
             #
             # Leur `+556` vaut 72, devant la couche proche (84) et derriere les
             # combattants ; leur `+554` vaut 0x2040, le premier jeu de palettes.
             dict(decor=12, immediats=[
                 dict(x=575, y=128, pal=72, plan=2, script=3, col=0x2040),
                 dict(x=431, y=176, pal=72, plan=2, script=4, col=0x2040),
                 dict(x=273, y=176, pal=72, plan=2, script=0, col=0x2040),
                 dict(x=671, y=96, pal=72, plan=2, script=5, col=0x2040),
                 dict(x=655, y=48, pal=72, plan=2, script=2, col=0x2040)])],
    # HUGO BIS (decor 16, bande 16, etage 57) -- 16/09/2026. Frederic : « aucun sprite ». Il
    # n'avait pas d'entree. Tout est lu dans sa routine d'etage `0x8C0DF0C8` (`routine2i.py 16`) ;
    # sa table de scripts est celle de Hugo (`0x8C1281F8`, partagee par les decors 6 et 16) et
    # ses images sont dans F_ETC29, l'asset de Hugo.
    #
    #   8C0DF186  0x8C0233B6   jeu 1 : script 17 en 512/144 (82), script 4 en 464/78 (76)
    #   8C0DF18C  0x8C02356A   jeu 2 : 19 en 224/12 (20), 26 en 666/62 (74), 27 en 686/25 (19),
    #                                  24 en 624/145 (82)
    #   8C0DF192  0x8C031B56   id 63, 816/52 (74) -- le meme spawner que Hugo
    #   8C0DF198  0x8C025A9A   arg 5 : script 29 en 512/224, script 28 en 606/105
    #   8C0DF19E  0x8C02E1FE   arg 5 : script 18 en 688/73
    #   8C0DF1A6  0x8C02C68A   arg 0 : NON LU -- sa table de nombres n'est pas resolue
    #
    # Les deux jeux d'elements ne sont pas cuits dans ses pages (elles sont les demi-banques
    # nues) : ils sont poses en objets, a leur profondeur -- deux passent devant les
    # combattants (20 et 19). `col` est leur `+554`.
    # URIEN -- son seul objet vient du spawner `0x8C0233B6`, indexe sur le decor courant
    # (voir le commentaire dans `bg00`) : script 32, x 600, y 48, plan 3.
    "bg0e": [dict(decor=13, adresse=0x8C17BBB4, nb=1, pas=16)],
    "bg10": [dict(decor=16, etage=57, asset="2i-b06-F_ETC29.bin", immediats=[
                 # LES MEMES AIRES QUE HUGO -- il partage ses blocs. Mais son second
                 # spawner n'a que DEUX objets aux aires 1 et 2 (8C17BEC0 : sc 15 et 24) :
                 # ses 26 et 27 sont de la premiere manche seule.
                 dict(x=512, y=144, pal=82, plan=2, script=17, col=0x2040, aires=0x1),
                 dict(x=464, y=78, pal=76, plan=2, script=4, col=0x2064, aires=0x3),
                 dict(x=336, y=81, pal=80, plan=2, script=20, col=0x2040, aires=0x6),
                 dict(x=512, y=70, pal=83, plan=2, script=22, col=0x2040, aires=0x6),
                 dict(x=448, y=56, pal=73, plan=2, script=21, col=0x2040, aires=0x4),
                 dict(x=224, y=12, pal=20, plan=2, script=19, col=0x2040, aires=0x1),
                 dict(x=688, y=56, pal=73, plan=2, script=15, col=0x0064, aires=0x6),
                 dict(x=666, y=62, pal=74, plan=2, script=26, col=0x2040, aires=0x1),
                 dict(x=686, y=25, pal=19, plan=2, script=27, col=0x2040, aires=0x1),
                 dict(x=624, y=145, pal=82, plan=2, script=24, col=0x40),
                 dict(x=816, y=52, pal=74, plan=2, script=31, spawner=0x8C031B56,
                      comportement=9, suites=[31, (32, "une")],
                      boite=(6, 64, 33, 69))]),
             dict(decor=16, etage=57, asset="2i-b06-F_ETC29.bin",
                  adresse=0x8C17C2F0, nb=2, pas=16),
             dict(decor=16, etage=57, asset="2i-b06-F_ETC29.bin",
                  adresse=0x8C17E908, nb=1, pas=16)],
}

# LA CLE DE CACHE BORNE LA GRILLE A 32 CASES.
#
# `decor_objets.c` forme `cle = rang << 11 | image << 5 | case` : cinq bits pour la case,
# six pour l'image, cinq pour le rang. Un objet dont la grille depasse 32 cases ecraserait
# les cles de son voisin. C'est ce qui ecarte l'enregistrement 0x8C17E858 d'Oro, dont le
# sprite 81 fait 7 x 6 = 42 cases.
# LES OBJETS QUI VIENNENT DES PAGES, ET NON DE L'ASSET
# ------------------------------------------------------
# Certains decors n'animent pas des sprites mais des PAGES. `bg_data.c` porte le mecanisme
# d'origine : `bgrw_on[stage]` designe des entrees de `bgrw_data_tbl` {plan, page source,
# suite}, et la suite est une liste de paires `[duree, page cible]` terminee par -1, qui
# boucle. Nos quinze etages ont `bgrw_on = {-1, ...}` : aucune animation de page. C'est
# pour ca que la cascade d'Akuma ne coule pas et que son entree de grotte manque.
#
# La deuxieme banque du `.pvc` sert de MAGASIN : ses pages ne sont pas une couche, ce sont
# les images. Chez Akuma, la page 22 porte **deux images de 80x64 empilees** -- 1068 pixels
# different de l'une a l'autre, c'est bien une animation -- et le premier plan a **un seul
# trou interieur, en 688,320, de 80x64 exactement**. La correspondance est sans ambiguite.
#
# On ne porte pas le mecanisme du jeu : on fabrique un objet anime de NOTRE systeme, qui
# sait deja poser des tuiles a une cadence. Les images viennent des pages au lieu de
# l'asset, et la palette se deduit de leurs couleurs.
#
# TOUT CE QUI SUIT EST LU DANS LE BINAIRE, PLUS DEDUIT -- 31/08/2026.
#
# Le mecanisme d'origine de 2nd Impact est le meme qu'en 3rd Strike, et il est complet :
#
#   `0x8C0277C4(k)` cree l'objet d'animation de pages ; k va en +4 de l'objet.
#   `0x8C17D8DC + k*20` = { s32 plan, s32 slot, s16* suite, u8* debut, u8* fin }
#   la suite est une file de paires [duree, page], terminee par -1, et elle BOUCLE.
#   `0x8C17D3DC + k*2` = le decalage de DESTINATION, et il vaut
#
#       decalage = 4 * (index du bloc 16x16 dans un plan large de 1024)
#
#   d'ou  x = (index % 64) * 16   et   y = (index / 64) * 16.
#
# Les appelants donnent l'appartenance, et eux seuls : etage 7 -> entrees 4, 5, 11 ;
# etage 8 -> 6, 7 ; etage 9 -> 0 ; etage 15 (Akuma) -> 8, 9, 10.
#
# Les trois destinations d'Akuma tombent EXACTEMENT sur les trois seules fenetres
# entierement transparentes de ses plans, celles que la recherche de trous avait elues
# separement. Deux mesures independantes, trois concordances : il n'y a rien a arbitrer.
#
#   banque, moitie : ou lire, dans le `.pvc`
#   sx, sy         : le coin de la GRILLE de trames dans cette moitie
#   larg, haut     : la taille d'une trame ; nc, nl : la grille, lue en ligne d'abord
#   bx, by         : ou la poser, dans le repere de la banque du plan
#   duree          : en trames, celle de la suite du binaire
#   fam            : la matrice de defilement. LA PROFONDEUR N'EST PLUS ECRITE ICI :
#                    une animation de page est un morceau de son plan, donc elle en prend
#                    la priorite -- 94 pour le plan lointain, 84 pour le proche, 90 pour le
#                    troisieme. Elles portaient toutes `z = 92`, la priorite du QUATRIEME
#                    plan, ce qui mettait celle de `bg0f` devant son plan et celle de
#                    `bg07` derriere le sien. Le PLAN, lui, vient du code : les notes le
#                    disent (« entree 8, plan 0 », « entree 10, plan 1 »).
PAGES_ANIMEES = {
    "bg0f": [
        dict(banque=4096, moitie="haut", sx=0, sy=0, larg=304, haut=144, nc=2, nl=3,
             bx=144, by=320, duree=4, fam=1,
             quoi="la grande cascade (entree 8, plan 0, bloc 1289)"),
        dict(banque=4096, moitie="haut", sx=768, sy=0, larg=48, haut=128, nc=4, nl=1,
             bx=400, by=272, duree=4, fam=1,
             quoi="la chute fine du fond (entree 9, plan 0, bloc 1113)"),
        dict(banque=4096, moitie="haut", sx=768, sy=256, larg=80, haut=64, nc=1, nl=2,
             bx=688, by=320, duree=4, fam=2,
             quoi="l'entree de la grotte (entree 10, plan 1, bloc 1323)"),
    ],

    # IBUKI : voir la fin du dictionnaire. (Le 02/09, monter DEUX cascades avait fige le jeu
    # -- « CG展開エラー 16x16 », trop de morceaux vivants ; 2I n'en dessine d'ailleurs qu'une.)
    # LES DEUX ELENA (le decor 8) -- 16/09/2026. Voir `entree_de_pages` plus bas.
    # `trames` : (banque, x, y, tournee) dans la banque entiere de 1024x1024, dans l'ordre
    # des pages triees. `pvc` et `etage` disent quelle bande et quel etage.
    "bg08": [
        # ELENA 1 (bande 9, etage 30) : la cascade entre les falaises. La destination lue
        # dit x 384 quand le trou est en 256 dans la banque : l'ecart de 128 est celui de
        # TOUT le decor de la bande 9 -- ses couches sont posees 128 plus a droite que la
        # banque (mesure sur la capture `cap-elena2.png`, voir `statiques2i.DECALAGE_ELENA`).
        # Les pages de l'etage 30 sont decalees d'autant, et la destination tombe juste.
        #
        # LES TROIS TRAMES TOURNEES COMMENCENT EN 80, 400 ET 720 -- 15/09/2026, nuit.
        # Frederic : « une frame est decalee ». Elles etaient notees 64, 384, 704, le debut
        # des cases de 320 de la colonne ; mais la trame fait 304 de large (lu dans l'entree),
        # et c'est la FIN de la case qu'elle occupe. Rognees en 304 depuis 64, elles sortaient
        # 16 pixels a cote. Remesure : en 80/400/720, chaque trame a pour plus proches voisines
        # sa precedente et sa suivante, a 1,12-1,14 ; en 64/384/704, l'ecart a la trame 0
        # montait a 34.
        dict(entree=0, pvc="bg09", etage=30, fam=1, quoi="la cascade d'Elena 1 (entree 0)",
             trames=[(1, 0, 0, False), (1, 0, 160, False), (1, 0, 320, False),
                     (1, 320, 0, False), (1, 320, 160, False), (1, 320, 320, False),
                     (1, 640, 0, False), (1, 640, 160, False), (1, 640, 320, False),
                     (0, 864, 720, True), (0, 864, 400, True), (0, 864, 80, True)]),
        # LA VARIANTE DU PONT (bande 8, etage 56) : le lac sous la montagne.
        dict(entree=6, pvc="bg08", etage=56, fam=1, quoi="les reflets du lac, bande haute (entree 6)",
             trames=[(0, 416, 512, False), (0, 416, 528, False), (0, 416, 544, False),
                     (0, 416, 560, False)]),
        dict(entree=7, pvc="bg08", etage=56, fam=1, quoi="les reflets du lac (entree 7)",
             trames=[(0, 352, 576, False), (0, 352, 640, False), (0, 352, 704, False),
                     (0, 352, 768, False)]),
    ],

    # IBUKI : LU DANS LE DESCRIPTEUR DE SCENE -- 16/09/2026 (`descripteurs2i.py`).
    #
    # 2I ne recopie aucun bloc. Pour les pages 69, 73..77, son moteur de decor redessine UNE
    # des six vues (272x256) en 224,688 de la scene, par-dessus la base, dans l'ordre des
    # pages : colonne par colonne, (0,0) (0,256) (272,0) (272,256) (544,0) (544,256). La
    # scene commence a la ligne 512 de la page, d'ou 224,176 dans le plan. On l'animait
    # 80 lignes trop bas, a cote d'une seconde cascade qui n'existe pas.
    #
    # Pour 64 et 71 (l'entree 11), c'est la cabane : 71 redessine celle de la banque 0 bas,
    # 64 laisse voir la seconde (banque 0 haut, 832..1023). Elles ne different que par les
    # lanternes, dont tous les pixels tombent dans le masque de l'entree (80x64, en 112,352).
    "bg07": [
        dict(pvc="bg07", etage=29, fam=3, larg=272, haut=256, masque=[[1] * 17] * 16,
             trames=[(0, 0, 0, False), (0, 0, 256, False), (0, 272, 0, False),
                     (0, 272, 256, False), (0, 544, 0, False), (0, 544, 256, False)],
             suite_trames=[0, 1, 2, 3, 4, 5], durees=[4] * 6,
             bx=224, by=176, sx=0, sy=0, banque=0,
             quoi="la cascade (pages 69, 73..77 : une vue en 224,688)"),
        dict(entree=11, pvc="bg07", etage=29, fam=2,
             quoi="les lanternes de la cabane (entree 11, pages 64 et 71)",
             trames=[(0, 880, 352, False), (0, 112, 864, False)]),
    ],
}


# LES DEUX ELENA -- 16/09/2026. Cette fois tout vient de l'entree du binaire : taille et
# masque (`fin` pointe sur {largeur, hauteur} en blocs, `debut` sur le masque), suite exacte
# des pages avec SES durees, destination. Seules les TRAMES sont mesurees -- la table qui
# donne la page d'une trame n'est pas dans le fichier -- et dans le meme ordre que les pages
# triees, ce que la continuite confirme :
#
#   * le lac : 4 trames de 320x64 et 4 bandes de 144x16, rangees a leur place horizontale ;
#     les blocs qui changent d'une trame a l'autre tombent exactement sur les destinations,
#     et les ecarts vont croissant dans l'ordre de la reserve (0,08 0,09 0,08) ;
#   * la cascade d'Elena 1 : DOUZE trames pour douze pages. Neuf en banque 1 (3 x 3 de
#     320x160), et trois TOURNEES d'un quart de tour dans la colonne x 864 de la banque 0
#     (lignes 64 a 1023) -- l'ecart a une trame droite tombe a 1,08 une fois retournee. Le
#     cycle le plus continu les enchaine a pas constant (1,12 a 1,14) : les neuf par
#     colonnes, puis les trois tournees de bas en haut.
#
# Chaque trame n'est servie que sur les blocs du masque : les autres ne changent pas, et la
# page du plan porte deja la premiere trame (`statiques2i.py`).
ENTREES_PAGES, DESTINATIONS_PAGES = 0x8C17D8DC, 0x8C17D3DC


def entree_de_pages(k):
    """Plan, taille, masque, suite et destination de l'animation de pages `k` de 2I."""
    plan, _slot, suite, debut, fin = struct.unpack_from("<iiIII", _D, ENTREES_PAGES + k * 20 - _B)
    w, h = _D[fin - _B], _D[fin + 1 - _B]
    masque = [[_D[debut - _B + r * w + c] for c in range(w)] for r in range(h)]
    seq = []
    p = suite
    while True:
        dur, page = struct.unpack_from("<hh", _D, p - _B)
        if dur == -1:
            break
        seq.append((dur, page))
        p += 4
    bloc = u16(DESTINATIONS_PAGES + k * 2) // 4
    return dict(plan=plan, larg=w * 16, haut=h * 16, masque=masque, suite=seq,
                dest=((bloc % 64) * 16, (bloc // 64) * 16))


def completer_page_2i(o):
    """Remplit une animation decrite par son `entree` : la taille, les durees, la place."""
    if "entree" not in o or "durees" in o:
        return o
    e = entree_de_pages(o["entree"])
    o.update(larg=e["larg"], haut=e["haut"], masque=e["masque"])
    pages = sorted({pg for _d, pg in e["suite"]})
    assert len(pages) == len(o["trames"]), "%d pages pour %d trames" % (len(pages), len(o["trames"]))
    o["suite_trames"] = [pages.index(pg) for _d, pg in e["suite"]]
    o["durees"] = [d for d, _pg in e["suite"]]
    o.setdefault("bx", e["dest"][0])
    o.setdefault("by", e["dest"][1])
    o["sx"], o["sy"], o["banque"] = o["trames"][0][1], o["trames"][0][2], o["trames"][0][0] * 4096
    return o


# LES CASES D'UN RANG : 64 DEPUIS LE 27/09/2026 -- 2I rattrape New Generation.
#
# Les 32 venaient de la cle de cache `rang << 11 | image << 5 | case`, qui n'existe plus
# depuis le 16/09 : la cle est un RANG DE MORCEAU dans l'etage (`base + image * cases +
# case`), et la seule borne restante est `CASES_MAX` de `decor_objets.c`, qui vaut **64**
# (`MorceauTrans cases[CASES_MAX]`). `animerng` l'a releve le 17/09 en notant « animer2i
# garde 32 : 2I est valide » -- on ne voulait pas deranger ce qui l'etait.
#
# CE DECALAGE COUTAIT LES CORDES D'ELENA. Frederic, le 27/09 : « il manque des cordes du
# ponton », puis « pourquoi ne pas faire comme pour les autres decors ? ». L'etage 56 ne
# porte que QUINZE objets (`a56o1` a `a56o14`, plus deux plans) mais QUATRE-VINGT-ONZE
# fiches : 76 d'entre elles sont des morceaux de deux colonnes. `OBJETS_MAX` n'en montre
# que 56, donc trente-cinq tombaient -- dont les vingt herbes et cordes du pont (id 122) et
# les neuf « arbres a cordes ». New Generation sert les MEMES quatre elements
# (720,64 / 304,64 / 784,32 / 240,32) en QUATRE fiches entieres.
#
# A 64, chaque tranche est deux fois plus large, donc deux fois moins de rangs.
#
# MAIS LA LARGEUR NE SE CHANGE PAS POUR TOUT LE MONDE -- 27/09/2026, corrige le jour meme.
# Je l'avais passee a 64 GLOBALEMENT : les quinze decors de 2I ont ete redecoupes d'un coup,
# donc leurs rangs et leurs emplacements de palette (`+ k` a partir du premier) ont bouge --
# y compris ceux que Frederic avait valides. Il l'a vu tout de suite : « pourquoi tu as
# modifie des decors qui fonctionnaient ? ». C'etait defaire ce qui marche pour un defaut
# qui ne touchait qu'UN etage.
#
# `CASES_MAX` reste donc a 32, et seuls les etages de `CASES_LARGES` prennent 64. Les autres
# regenerent a l'octet pres. On elargit un etage le jour ou il le demande -- c'est-a-dire
# quand `verifier_objets` montre qu'`OBJETS_MAX` l'ecrete -- et on le regarde seul.
CASES_MAX = 32

# LES ETAGES QUI ONT DROIT A 64 CASES PAR MORCEAU, ET POURQUOI CHACUN.
#
#   56  Elena 2I, la gorge et son pont. Quinze objets decoupes en 76 morceaux de deux
#       colonnes : 91 fiches pour 56 places, donc 35 objets ecartes en silence -- dont les
#       vingt herbes et cordes du pont (id 122) et les neuf « arbres a cordes ». Frederic,
#       le 27/09 : « il manque des cordes du ponton ». A 64 : 46 fiches, plus rien d'ecrete.
CASES_LARGES = {56}


def cases_max_de(etage):
    """La largeur d'un morceau pour cet etage : 64 s'il en a besoin, 32 sinon."""
    return 64 if etage in CASES_LARGES else CASES_MAX
IMAGES_MAX = 64

# LA COLLECTION DE MOTIFS, ET C'EST ELLE QUI A GELE IBUKI — 02/09/2026
# ---------------------------------------------------------------------
# `DecorObjets_Identite` forme `0x00D3 <<16 | rang <<6 | image` : c'est l'identite que le
# cache de `mlt_obj_trans_cp3_ext` indexe, et `PatternCollection` n'en tient que
# SOIXANTE-QUATRE. Chaque couple (fiche, image encore vivante) en occupe une. Au-dela, le
# premier chemin televerse sous une identite que le second ne retrouve plus, et
# `get_mltbuf16_ext` part en `while (1) {}` -- `ＣＧ展開エラー　１６×１６`, sans autre message.
#
# La borne explique l'historique : Akuma 26 motifs et Ibuki a une cascade 27 marchent ;
# Ibuki a deux cascades en demandait plus de cent.
#
# Une image n'est vivante que douze trames (`mts_base[7].life16`), et un objet qui ne
# BOUCLE pas reste sur son image 0 : il n'occupe qu'une identite, quel que soit le nombre
# d'images qu'il porte.
MOTIFS_MAX = 128   # PATTERN_COLLECTION_MAX de structs.h -- 64 sur la console, 128 ici
VIE_MOTIF = 12


def motifs_vivants(o, boucle):
    """Combien d'identites de motif une fiche de cet objet occupe au pire moment.

    LE PIRE MOMENT EST LA TRANSITION, et l'ancien compte s'arretait une image trop tot --
    16/09/2026. Une identite reste vivante `VIE_MOTIF` trames APRES son dernier dessin :
    quand l'image j apparait, la precedente vient de finir (1 trame), celle d'avant a fini
    il y a 1 + sa duree, etc. A quatre trames par image : 1 + 3 anciennes = QUATRE, pas
    trois. La variante d'Elena avait ete admise a 60 sur 64 ; elle en demandait 80 et le jeu
    figeait sur « CGキャッシュバッファが一杯 ».
    """
    if not boucle:
        return 1

    d = [im["duree"] for im in o["images"]] if "images" in o else list(o["durees"])
    n = len(d)
    pire = 0

    for depart in range(n):
        vus = 1
        ecart = 1
        k = depart - 1

        while vus < n and ecart <= VIE_MOTIF:
            vus += 1
            ecart += d[k % n]
            k -= 1

        pire = max(pire, vus)

    return pire

# CE QUI EST MESURE PASSE DEVANT CE QUI EST CALCULE.
#
# L'edifice de pierre est PEINT dans la banque du disque d'Oro, dans la grotte du fond, et
# la mesure l'y place en 704,896 (`peints.py`, 706 pixels identiques sur 721). La formule
# le posait en 720,927 sur la grotte proche -- sur le dos du chien, ce que Frederic a vu.
# Son champ `plan` vaut pourtant 2 comme les autres : rien dans l'enregistrement ne le
# disait.
#
#     script -> (banque_x, banque_y, famille, z)
# UNE MESURE PAR ANCRE N'EST PAS UNE MESURE — 04/09/2026, et ca m'a coute une regression.
#
# `situer_animes.chercher` trouve sa pose par un PIXEL D'ANCRE : le plus rare de l'image.
# C'est rapide, mais ca n'a de sens que si l'objet est peint A L'IDENTIQUE. Des que la
# figure peinte differe un peu de la notre -- autre trame, autre palette -- l'ancre tombe
# sur un pixel isole et rend une position qui n'est pas la bonne.
#
# La femme en rose de Yun (script 31) : l'ancre disait 512, et j'ai deplace l'objet. Un
# BALAYAGE COMPLET, qui compte les pixels identiques a chaque decalage, dit 496 -- sa
# position calculee -- avec 69 % contre 84 % au vieil homme. Frederic a vu la regression
# tout de suite : « Yun, c'est pire ».
#
# LA REGLE : on ne deplace un objet que sur un accord FRANC, mesure par balayage. En
# dessous de ~90 %, l'objet peint n'est pas le notre et ne dit rien de sa place.
# `rendu_fiches.py` sert a ca -- il rend l'objet depuis les TUILES COMPILEES.
#
#     script -> (banque_x, banque_y, famille, z)
#
# L'EDIFICE D'ORO N'Y EST PLUS -- 16/09/2026. La mesure etait juste (l'edifice est peint dans la
# banque du fond, 713 pixels sur 721), mais ce qu'elle deplacait n'etait pas lui : l'objet du
# code (enregistrement 7 de `0x8C02E1FE` arg 6, plan 2, 720/96, priorite 90) est dans le plan
# PROCHE, a 90 -- donc DERRIERE lui (84) -- et le sol de ce plan en couvre 687 pixels sur 721,
# le chien (74) le reste. Dans 2I on ne le voit pas ; pose dans la grotte du fond, il sortait a
# cote du chien. Frederic : « a supprimer ». Voir `EXCLUS`.
#
# IL Y REVIENT -- 16/09/2026. Frederic : « l'animation du bloc de pierre incruste dans le mur
# de la grotte est manquante ». Le « petit bloc a supprimer » du 16/09 etait la copie PERIMEE
# cuite dans la page proche (`statiques2i.REFAITES` l'a effacee le meme jour), pas l'objet
# pose sur l'edifice peint. L'objet reprend sa place mesuree, dans la grotte du fond.
MESURE = {
    "bg0a": {9: (704, 896, 3, 92)},
}

# « CE QUE LE DECOR PEINT DEJA, ON NE LE POSE PAS » ETAIT UNE MAUVAISE REGLE — 04/09/2026
# =======================================================================================
# Je l'avais tiree du fait que les figures peintes et les objets se redoublaient. Frederic
# a montre en une phrase qu'elle prend le probleme a l'envers :
#
#     « les cages sont DERRIERE le personnage qui fume au lieu d'etre DEVANT »
#
# La figure peinte est dans le DECOR, donc derriere tout. L'objet, lui, se dessine PAR
# DESSUS. Quand l'original montre l'element devant un personnage, c'est precisement
# l'objet qui le met la -- le retirer laisse la version peinte, c'est-a-dire derriere.
#
# Et pour le vieil homme et la femme en rose, retirer l'objet retirait l'ANIMATION, qui
# etait tout ce qu'on cherchait a leur rendre.
#
# La table reste, vide, parce que le cas existera : un objet qui n'anime rien ET qui
# recouvre exactement sa copie peinte ne sert a rien. Mais il se demontre, il ne se
# suppose pas.
#
# LE CAS EXISTE : l'edifice anime d'Oro (script 9), cache dans 2I derriere le sol du plan proche
# et derriere le chien -- voir `MESURE`. 34 pixels sur 721 depasseraient du sol.
# (L'edifice d'Oro en est ressorti le 16/09 : voir `MESURE`.)
EXCLUS = {}

# LE `x` DE RYU EST COMPTE DEPUIS LE MILIEU DE LA BANDE — 03/09/2026
# ==================================================================
# Ryu est le seul decor dont des enregistrements portent un `x` NEGATIF : sept sur treize,
# de -368 a -96. L'enroulement `& 0x3FF` les renvoyait a droite (641 a 897), et Frederic
# voyait « les sprites pas a leur place ».
#
# DEUX HYPOTHESES FERMEES AVANT CELLE-CI, pour ne pas les rouvrir :
#
#   * **le chargeur ne decale pas.** `SANS-ETAT.md` soupconnait un `objet[+102] +=
#     parent[+102]`. Verifie sur ses QUATRE chargeurs : aucun n'ajoute quoi que ce soit a
#     `+102`, et le detecteur trouve bien l'addition dans `0x8C02AA7C`, le chargeur temoin
#     qui, lui, decale ;
#   * **aucun de ses objets n'est peint dans la banque du disque.** La mesure qui avait
#     redresse l'edifice d'Oro n'existe pas chez lui : zero correspondance sur treize.
#
# LA MESURE QUI TRANCHE. Frederic a fourni deux captures de l'original a deux positions de
# camera. Le DECOR y sert de reglet -- le panneau 湯, le parasol, la lanterne de pierre
# donnent la position de la camera -- et cinq objets identifies s'y relevent :
#
#     les singes            x -233   ->  bande  230    ecart 463
#     la femme au panneau   x -145   ->  bande  325    ecart 470
#     la femme en rose      x -112   ->  bande  371    ecart 483
#     le gros baigneur      x  273   ->  bande  810    ecart 537
#     le singe de droite    x  336   ->  bande  857    ecart 521
#
# **Un ecart CONSTANT d'environ 512**, et il vaut pour les positifs comme pour les
# negatifs -- ce n'est donc pas une correction de l'enroulement, c'est une ORIGINE. 512
# est le milieu de la bande, et c'est le litteral que les dix-sept plans portent en `+26`.
#
# La dispersion (463 a 537) est celle de mes releves au pixel sur une capture, pas celle
# de la donnee : chaque sprite a en plus son ancre.
#
# C'EST LA PREMIERE FOIS QU'UNE REFERENCE EXTERIEURE CALE LA CHAINE, et `BILAN.md`
# reclamait exactement ca depuis le 01/09 : « rendre le decor complet et le comparer a une
# capture une fois pour toutes ». Elle ne vaut que pour Ryu tant qu'un autre decor ne l'a
# pas demandee.
DECALAGE_X = {
    "bg02": 512,
}

# UN PIXEL, MESURE SUR LES TROUS DE SEAN -- 16/09/2026.
#
# Sa banque n'est pas peinte sous ses elements statiques : elle est DECOUPEE a leur
# silhouette, et le jeu pose l'objet dans le trou. Le trou est donc un etalon. En cherchant,
# pour chacun, l'ecart ou la silhouette couvre le trou et rien d'autre :
#
#     le conducteur     +1,+1        le poteau          +1,+1
#     le petit palmier  +1,+1        l'homme a genou    +1,+1
#
# **Les quatre disent le meme pixel**, et Frederic le voit : « une partie des sprites sont
# decales vers le haut de 1 ou 2 pixels ». Je ne sais pas D'OU il vient -- la formule est
# celle des treize autres decors, dont les positions sont validees a l'ecran --, donc il
# reste ce qu'il est : une mesure, pour le seul decor ou on a de quoi la faire.
#
# LE PIXEL EN x, LE MOTEUR LE MET DEJA -- 16/09/2026. Avec +1,+1, Frederic voit « une
# colonne de pixels noirs au niveau de la voiture jaune, des pixels blancs au niveau de la
# table ». Recompose au pixel : decale d'UN pixel vers la droite, le conducteur decouvre le
# bord gauche de son trou (x 608, 21 lignes -- la colonne noire), et la table le pave clair
# peint sous son bord gauche. Aucun autre decalage ne donne une colonne seule. Le moteur place
# donc deja nos objets un pixel a droite des plans, comme 2I (`x - (defilement + 1)`), et
# l'ajustement le comptait deux fois. La verticale reste : sans elle, Frederic les voyait trop
# hauts.
AJUSTEMENT = {
    "bg0d": (0, 1),
}

ETAGE = {"bg00": 22, "bg01": 23, "bg02": 24, "bg03": 25, "bg04": 26, "bg05": 27,
         "bg06": 28, "bg07": 29, "bg08": 30, "bg0a": 31, "bg0b": 32, "bg0c": 33,
         "bg0d": 34, "bg0e": 35, "bg0f": 36, "bg10": 57}


def etage_de(decor, o):
    """L'etage d'un objet : celui de son decor, sauf si son bloc en nomme un autre (le
    decor 8 porte deux bandes, montees a deux etages)."""
    return o.get("etage") or ETAGE[decor]

# `famille` choisit la MATRICE, donc le defilement ; `z` l'ORDRE DE DESSIN.
# Sur l'etage 31 le plan 1 de 2nd Impact est la grotte du FOND, notre troisieme plan --
# famille 3 -- et il se dessine juste devant le couchant, d'ou z 92. Le plan 2 est le
# plan proche, famille 2, et garde le z du modele.
# Le levier a la main, quand l'oeil voit ce que la mesure ne dit pas.
#
# `est_une_boucle` ne decide plus rien depuis le 23/09 au soir : l'id 184 montre que les
# quatre acolytes de Gill posent bel et bien un script, et que seul l'indice 1 regarde.
# BOUCLE reste la main sur le levier : si un objet fait encore un mouvement absurde, on le
# nomme ici et il garde son image 0.
#
#     "bg00": {0: 0, 2: 0}     l'objet 0 et l'objet 2 restent sur leur image 0
BOUCLE = {}

FAMILLE = {"bg0c": {None: 2}, "bg0e": {None: 2}, "bg00": {None: 2}, "bg01": {None: 2}, "bg02": {None: 2},
           "bg03": {None: 2}, "bg04": {None: 2}, "bg05": {None: 2},
           "bg06": {None: 2}, "bg08": {None: 2}, "bg0a": {1: 3, None: 2},
           "bg0b": {None: 2}, "bg0d": {None: 2}, "bg0f": {None: 2}, "bg10": {None: 2}}
Z = {"bg0c": {None: 0}, "bg0e": {None: 0}, "bg00": {None: 0}, "bg01": {None: 0}, "bg02": {None: 0},
     "bg03": {None: 0}, "bg04": {None: 0}, "bg05": {None: 0},
     "bg06": {None: 0}, "bg08": {None: 0}, "bg0a": {1: 92, None: 0},
     "bg0b": {None: 0}, "bg0d": {None: 0}, "bg0f": {None: 0}, "bg10": {None: 0}}

# LA PROFONDEUR D'UN OBJET EN PARTICULIER, quand deux objets d'un meme plan se recouvrent.
#
# `Z` ci-dessus donne la profondeur d'un PLAN ; elle ne peut pas departager deux objets
# qui partagent le meme. Ils recoivent alors tous deux le 0 qui veut dire « garde celle
# du modele » -- 80 -- et l'ordre de rendu ne tient plus qu'a leur rang dans la fiche.
#
# UN Z PLUS PETIT EST PLUS PRES. Voir `DecorAnimation.z` dans `decor_objets.h`.
#
#     bg04, script 6 : les deux punks de Dudley se chevauchent sur 48 pixels -- celui de
#     gauche s'etale de 672 a 768, celui de droite de 720 a 784. Frederic a releve sur
#     l'original que CELUI DE GAUCHE passe devant. C'est donc une observation de sa part,
#     pas une lecture du binaire, et c'est dit tel quel.
# LA PROFONDEUR EST DANS LES DONNEES : C'EST `+556` — 04/09/2026
# =============================================================
# J'avais ecrit ici que « aucun chargeur n'ecrit la profondeur ». C'ETAIT FAUX, et deux
# fois : j'avais cherche `position_z` a `+76`, offset calcule dans une structure du port
# qui fait 140 octets et n'a rien a voir avec l'objet de 2I.
#
# L'ANCRE QUI NOMME TOUT. Les trois spawners a immediats de Yun ecrivent `0x4200` en
# `+552` -- exactement la constante que `eff05.c` pose dans `my_col_mode`. En alignant
# les deux, les champs suivants se nomment seuls :
#
#     +552  my_col_mode  (0x4200)      +556  my_priority   <- LA PROFONDEUR
#     +554  my_col_code                +558  my_family     <- notre « plan »
#
# ET LES VALEURS LUES REPONDENT A CE QUE FREDERIC VOIT :
#
#     les cages    +556 = 90     devant
#     le fumeur    +556 = 91     derriere
#     la charrette +556 = 74     devant les deux
#
# Un `z` plus GRAND est plus LOIN (voir `DecorAnimation.z`). Les cages passent donc devant
# le fumeur, ce qu'il signalait ; et la charrette devant l'etal.
#
# CE QUI RESTE UN REGLAGE : `bg04`, le punk de Dudley. Son bloc de 24 octets ne porte pas
# `+556`, et le 78 vient d'une observation, pas d'une lecture. C'est dit ici et dans la
# fiche.
#
# ET L'ECHELLE DE 2I N'EST PAS CELLE DE 3SX — 04/09/2026, regression signalee a l'ecran.
#
# J'ai reporte tels quels les `my_priority` lus chez Yun : cages 90, charrette 74, fumeur
# 91. Or dans NOTRE moteur les plans de fond sont a **84, 90 et 94**, et un `z` plus grand
# est plus loin : un objet a 90 ou 91 passe DERRIERE le plan proche, donc il disparait.
# Frederic : « il manque tous les sprites ».
#
# La valeur est juste, c'est le repere qui differe. Tant que la correspondance entre les
# deux echelles n'est pas ETABLIE -- et elle ne l'est pas -- on garde 0, qui veut dire
# « la profondeur du modele », et les objets restent devant les plans.
# VIDEE LE 04/09/2026 : LE CODE DONNAIT DEJA LA REPONSE.
#
# Elle ne contenait qu'une entree, le punk de Dudley, reglee a 78 sur une observation de
# Frederic. Or son `+556` vaut **75**, et l'autre punk (script 4) vaut 76 : le code le met
# donc DEJA devant, et plus franchement que mon reglage. Un `z` a l'oeil qui contredit une
# valeur lue n'a aucune raison de rester.
#
# La table reste, vide, pour le cas ou deux objets partageraient exactement la meme
# priorite ET se recouvriraient. Ca ne s'est pas encore produit.
Z_OBJET = {}


def script_images(decor, sc, aire=0):
    """[(index global, duree)] d'un script, dans l'ordre.

    `aire` choisit la table : (decor*3 + aire). Le decor 8 porte deux bandes, et la bande 9
    (Elena 1) lit ses scripts dans la table de l'aire 1 -- voir le bloc `bg08`.

    LA REGLE EST LA DUREE, PAS LE PREMIER OCTET -- CORRIGE LE 23/09/2026.

    L'interprete (2I `0x8C0B50DC`) compare le PREMIER MOT de l'enregistrement a 256.
    Ce mot vaut `premier octet | duree << 8` : des que la duree n'est pas nulle il
    depasse 256, et l'enregistrement est une IMAGE quel que soit son premier octet --
    celui-ci n'est qu'un drapeau, recopie dans la fiche en `+468` pour la routine.
    Ne garder que `cmd == 0` perdait **88 images en 2nd Impact et 67 en New
    Generation** : tous les drapeaux 2, 3 a 9 et 0xFF.
    """
    if aire:
        t = u32(AN.SCRIPTS + (decor * 3 + aire) * 4)
        n = 0
        while n < 128 and 0x8C010000 <= u32(t + n * 4) < 0x8C645580:
            n += 1
    else:
        t, n = AN.table_scripts(decor)

    if not 0 <= sc < n:
        return []

    p = u32(t + sc * 4)
    out = []

    for k in range(96):
        cmd = u8(p + k * 8)
        duree = u8(p + k * 8 + 1)
        idx = u16(p + k * 8 + 6)

        if duree:
            out.append((idx, duree))
            continue

        if cmd == 0x01:
            break

    return out


def script_deroule(decor, sc, aire=0, fin="une"):
    """[(index global, duree)] d'un script TEL QU'IL SE JOUE : boucles deroulees.

    `script_images` saute les commandes, et joue donc une boucle une seule fois. Un
    enregistrement de 2I fait huit octets `{drapeaux, duree, .., .., image}` et c'est la
    DUREE qui decide (`0x8C0B5218`) :

      * duree non nulle : une IMAGE. Son premier octet est recopie en `+0x1D4`, et c'est
        ce que les routines d'objet attendent pour changer d'etat -- le bit 0 marque la FIN.
        La routine le lit juste apres l'avance et repart aussitot : l'image marquee ne se
        voit qu'UNE trame.
      * duree nulle : une COMMANDE (`0x8C1C5BC8`). `0x01` reprend le script au debut --
        il tourne alors de lui-meme ; `0x0C` ouvre une boucle, son compte dans le mot 6 ;
        `0x0D` la ferme et repart tant que le compte, decremente, reste positif.

    Rend aussi `True` si le script finit sur une image marquee, `False` s'il boucle.
    Lu pour le chien d'Oro, 16/09/2026.

    **CE QUE DEVIENT L'IMAGE MARQUEE DEPEND DE LA ROUTINE** (`fin`) -- les poissons de Yang :

      * `"une"`    la routine voit la marque et change d'etat A LA TRAME SUIVANTE : l'image
                   se voit une trame (le chien d'Oro) ;
      * `"sans"`   elle change d'etat DANS la trame, apres l'avance : l'image ne se voit
                   jamais (les demi-tours des poissons) ;
      * `"boucle"` elle ne regarde pas la marque : l'image dure son temps et le `0x01` qui
                   suit relance le script (un poisson qui nage).
    """
    t, n = AN.table_scripts(decor) if not aire else (None, 0)

    if aire or not 0 <= sc < n:
        raise ValueError("script %d du decor %d hors table" % (sc, decor))

    p = u32(t + sc * 4)
    out = []
    k = 0
    boucle = None

    for _garde in range(1024):
        drap, duree, idx = u8(p + k * 8), u8(p + k * 8 + 1), u16(p + k * 8 + 6)

        if duree:
            if drap & 1 and fin != "boucle":
                if fin == "une":
                    out.append((idx, 1))
                return out, True
            out.append((idx, duree))
            k += 1
        elif drap == 0x01:
            return out, False
        elif drap == 0x0C:
            boucle = [k + 1, idx]
            k += 1
        elif drap == 0x0D:
            boucle[1] -= 1
            k = boucle[0] if boucle[1] > 0 else k + 1
        elif drap == 0x02:
            # LE SAUT ABSOLU, lu le 23/09/2026. Son gestionnaire est `0x8C0B530C` (table
            # des commandes `0x8C1C5BC8`, entree 2) : `index = pas x (mot3 - 2)`, donc il
            # reprend le script a l'enregistrement `mot3 - 2`. C'est le frere du `0x32`,
            # qui saute en arriere d'un nombre RELATIF d'enregistrements.
            #
            # Il boucle : on le traite comme un `0x01`, qui relance le script. La statue de
            # Yang (script 72) est le premier objet porte qui l'emploie.
            return out, False
        else:
            raise ValueError("script %d : commande 0x%02X non lue" % (sc, drap))

    raise ValueError("script %d : ne finit pas" % sc)


def enregistrement(decor, sc, r):
    """(index global, duree) du `r`-ieme enregistrement d'un script -- le chien d'Oro
    ENTRE dans son script 28 a l'enregistrement 0, 2 ou 4 selon son regard."""
    t, _n = AN.table_scripts(decor)
    p = u32(t + sc * 4) + r * 8
    return u16(p + 6), u8(p + 1)


def suites_d_images(decor, suites):
    """Les pas d'un objet a COMPORTEMENT, suite par suite (voir `COMPORTEMENTS`).

    Une suite est un numero de script, deroule ; un couple `(script, fin)` qui dit ce que
    devient son image marquee (`script_deroule`) ; ou une liste `(script, enregistrement)`
    d'images TENUES -- le regard du chien."""
    out = []

    for s in suites:
        if isinstance(s, int):
            out.append(script_deroule(decor, s)[0])
        elif isinstance(s, tuple):
            out.append(script_deroule(decor, s[0], fin=s[1])[0])
        else:
            out.append([(enregistrement(decor, sc, r)[0], 1) for sc, r in s])

    return out


def objets(decor):
    """Les objets animes d'un decor : x, y, palette, script, et ses images.

    Les blocs se suivent dans l'ordre de `TABLES`, et le rang -- qui est la place dans
    les cles de cache et dans les emplacements de palette -- court d'un bloc a l'autre.

    Deux ecarts sont refuses et DITS :

      * un script deja vu dans un bloc precedent. Les deux blocs d'Oro partagent trois
        scripts (6, 8, 9) ; on garde la version du premier, celle qui est a l'ecran.
      * une grille de plus de 32 cases, que la cle de cache ne sait pas coder.
    """
    out = []
    vus = {}

    for bloc in TABLES[decor]:
        d = bloc["decor"]
        aire = bloc.get("aire", 0)
        # UN BLOC PEUT NOMMER SON ASSET ET SA BASE DE PALETTES -- 15/09/2026, nuit. `bases.ASSETS`
        # ne connait qu'un asset par decor ; Elena en a deux (F_ETC30 pour le pont, F_ETC31
        # pour Elena 1), comme ses elements statiques (`statiques2i.asset_du_script`).
        a, tuiles = P.asset(bloc.get("asset", bases.ASSETS[decor]))
        lo, _hi = a["index_global"]
        offs = sorted({r[4] for r in a["anims"]})
        base_bloc = bloc.get("base_palette")

        if base_bloc is None:
            base_pal = bases.BASES_2I[decor][min(bases.BASES_2I[decor])]
            resoudre = lambda dr, off: bases.numero(decor, dr, off)
        else:
            base_pal = base_bloc
            resoudre = lambda _dr, off, b=base_bloc: b + off

        # UN OBJET PEUT N'AVOIR AUCUN BLOC — 02/09/2026.
        #
        # Les betes d'Oro sont dans ce cas, et c'est l'explication de la plus vieille
        # enigme du chantier : on a cherche leur bloc pendant des semaines, il n'y en a
        # pas. Leur spawner ecrit x, y, palette, plan et la table de scripts en
        # IMMEDIATS, et le numero de script est pose par la routine de l'objet.
        # `immediats` porte donc les valeurs telles qu'elles sont lues dans le code.
        if "immediats" in bloc:
            champs = [(o.get("spawner", 0), o.get("plan"), o["x"], o["y"],
                       o.get("pal", 0), o["script"]) for o in bloc["immediats"]]
            masques = [o.get("variante", 0xF) for o in bloc["immediats"]]
            aires_enr = [o.get("aires", bloc.get("aires", 0)) for o in bloc["immediats"]]
            pas = 0
        else:
            pas = bloc["pas"]
            # Un bloc est soit une suite -- `adresse` et `nb` --, soit une liste
            # d'enregistrements NOMMES, quand on n'en retient qu'une partie.
            suite = bloc.get("adresses")

            if suite is None:
                suite = [bloc["adresse"] + k * pas for k in range(bloc["nb"])]

            champs = [(a0, None, 0, 0, 0, 0) for a0 in suite]
            masques = [bloc.get("variante", 0xF)] * len(champs)
            aires_enr = [bloc.get("aires", 0)] * len(champs)

        for rang_enr, (a0, plan, x_el, y_el, pal_el, sc) in enumerate(champs):

            if pas == 0:
                pass
            elif pas == 8:
                plan = None
                x_el, y_el, pal_el, sc = [u16(a0 + j * 2) for j in range(4)]
            else:
                # `x`, `y`, `sc` : les offsets des champs dans l'enregistrement. Par
                # defaut ceux de l'annuaire ; un bloc qui pointe droit sur son premier
                # enregistrement les decale de deux.
                #
                # `plan` et `pal` valent None quand le spawner N'ECRIT PAS ce champ --
                # et ca se lit dans son code (`spawners2i.py`), ca ne se suppose pas.
                # Le spawner `0x8C0258DA` de Gill n'ecrit ni l'un ni l'autre : ses
                # enregistrements de dix octets sont {x, y, +556, script, +148}. Lire un
                # `plan` a l'offset 0 y rendrait son `x`.
                ox, oy = bloc.get("x", 4), bloc.get("y", 6)
                osc = bloc.get("sc", 10)
                opl = bloc.get("plan", 0)
                opal = bloc.get("pal", oy + 2)
                # `plan_fixe` : le spawner ecrit un plan CONSTANT au lieu de le lire dans
                # l'enregistrement. Celui d'Oro pose `mov #2,r9` puis `r9 -> objet+558`.
                plan = (u16(a0 + opl) if opl is not None
                        else bloc.get("plan_fixe"))
                x_el, y_el = u16(a0 + ox), u16(a0 + oy)
                # La palette de l'enregistrement n'est plus qu'une etiquette : la palette
                # EFFECTIVE se fabrique depuis les morceaux (`bloc_c`). Zero convient.
                pal_el = u16(a0 + opal) if opal is not None else 0
                # `scripts` : le numero de script n'est PAS dans l'enregistrement, c'est
                # la routine de l'objet qui le pose -- un par `type`, et le `type` est le
                # rang de l'enregistrement. On le donne explicitement, lu dans le code.
                scs = bloc.get("scripts")
                sc = scs[rang_enr] if scs else u16(a0 + osc)

                # UN ENREGISTREMENT PORTE DEUX SCRIPTS, ET LE SECOND EST L'ACTION.
                #
                # Les blocs du chargeur `0x8C028792` (id 18) ont un champ de plus, deux
                # octets apres le script : il part en `objet+152` quand le premier part en
                # `+150`, et il vaut TOUJOURS le premier plus un. C'est une paire
                # (repos, action) que la routine alterne :
                #
                #     Yun    +150 = 32 (ZERO image)   +152 = 33 (douze images)
                #     Hugo   +150 =  7 (dix images)   +152 =  8 (dix-neuf images)
                #     Dudley +150 =  2 (une image)    +152 =  3 (neuf images)
                #
                # Notre moteur ne joue qu'un script : on prend LE PLUS RICHE des deux.
                # C'est ce qui manquait pour que ces figures bougent -- Frederic voyait
                # « les 2 personnages devant le tram et les oiseaux dans la cage » figes,
                # et c'etait le script de repos qui etait pose.
                osc2 = bloc.get("sc2")

                if osc2 is not None and not scs:
                    sc2 = u16(a0 + osc2)
                    if len(script_images(d, sc2, aire)) > len(script_images(d, sc, aire)):
                        sc = sc2

            # LA PALETTE SE LIT DANS `my_col_code` (+554) -- 16/09/2026. Voir
            # `palettes_ram2i.py` et `PALETTES_RAM`. L'enregistrement le porte juste avant
            # son `x` (champs de rang 2 et 3 dans les quatre formes de 14 a 30 octets) ;
            # un spawner a immediats l'ecrit en constante.
            col = None
            res_obj, base_obj, bande_obj = resoudre, base_pal, None

            if decor in PALETTES_RAM and base_bloc is None:
                if pas == 0:
                    imm = bloc["immediats"][rang_enr]
                    col = imm.get("col")
                    if col is None and imm.get("spawner"):
                        col = IM.analyser(imm["spawner"])[0].get(554)
                elif pas >= 14:
                    col = bloc.get("col_code", u16(a0 + bloc.get("x", 4) - 2))
                else:
                    col = bloc.get("col_code")

                if col is not None:
                    bande_obj = u16(DECOR_VERS_BANDE + (d * 3 + aire) * 2)
                    if PR.palette(bande_obj, col, 0) is not None:
                        base_obj = PR.palette(bande_obj, col, 0)
                        res_obj = (lambda dr, off, b=bande_obj, c=col:
                                   PR.palette(b, c, off) if PR.palette(b, c, off) is not None
                                   else bases.numero(decor, dr, off))
                    else:
                        col = None

            images = []
            # UN OBJET A COMPORTEMENT porte ses suites bout a bout, et le moteur en choisit
            # une selon l'etat -- voir `COMPORTEMENTS`. Une image perdue decalerait toutes
            # les bornes : on refuse plutot que de sauter.
            imm = bloc["immediats"][rang_enr] if pas == 0 else {}
            suites = suites_d_images(d, imm["suites"]) if imm.get("comportement") else None
            trames = ([t for s in suites for t in s] if suites else
                      script_deroule(d, sc, fin="boucle")[0] if imm.get("deroule") else
                      script_images(d, sc, aire))

            # LES PAS D'UN OBJET A COMPORTEMENT RENVOIENT A DES IMAGES DISTINCTES -- le
            # poisson noir de Yang enchaine 66 images, et l'identite de motif n'en code que
            # 64. Ses suites repassent par les memes : on ne les emet qu'une fois.
            if suites:
                distinctes = []
                for idx, duree in trames:
                    if idx not in [i for i, _ in distinctes]:
                        distinctes.append((idx, duree))
                pas_obj = [([i for i, _ in distinctes].index(idx), duree)
                           for idx, duree in trames]
                trames = distinctes

            for idx, duree in trames:
                if not lo <= idx < lo + len(a["anims"]):
                    if suites:
                        raise ValueError("image %d hors de l'asset" % idx)
                    continue

                rec = a["anims"][idx - lo]
                n = offs.index(rec[4])
                pose = A.poser(a["sprites"][n], tuiles)

                if pose is None:
                    if suites:
                        raise ValueError("image %d sans pose" % idx)
                    continue

                # La MEME image, composee en ARGB1555 vrai : chaque morceau avec sa
                # propre palette. C'est elle qui sert a fabriquer la palette de l'objet.
                #
                # ET SA PROVENANCE -- `src1555` porte, pixel par pixel, le NUMERO de la
                # palette qui l'a peint. C'est ce qui permet de servir un objet en
                # PLUSIEURS palettes quand ses couleurs depassent les 63 d'une seule :
                # voir `groupes_palette`.
                c1555 = None
                src1555 = None
                pc = A.poser_1555(a["sprites"][n], tuiles, banque_brute(),
                                  base_obj, res_obj, avec_source=True)

                if pc is not None:
                    c1555, src1555 = pc[0], pc[1]

                im = dict(sprite=n, duree=duree, ancre=(rec[1], rec[2]),
                          img=pose[0], msk=pose[1], x0=pose[2], y0=pose[3],
                          c1555=c1555, src1555=src1555,
                          morceaux=a["sprites"][n]["morceaux"])

                # UN OBJET RETOURNE (`+10`, `rl_flag`) -- le troisieme oiseau de Yun. Le
                # moteur de 2I pose le pixel d'ecart `dx` en `-dx - 1` : l'image se retourne
                # et son bord gauche passe en `-(gauche + largeur)`.
                if imm.get("miroir"):
                    gauche = rec[1] + pose[2]
                    larg = pose[0].shape[1]
                    im.update(img=pose[0][:, ::-1].copy(), msk=pose[1][:, ::-1].copy(),
                              ancre=(-(gauche + larg) - pose[2], rec[2]))
                    if c1555 is not None:
                        im["c1555"] = c1555[:, ::-1].copy()
                    if src1555 is not None:
                        im["src1555"] = src1555[:, ::-1].copy()

                images.append(im)

            if not images:
                continue

            o = dict(rang=len(out), x=x_el, y=y_el, pal=pal_el, script=sc, plan=plan,
                     images=images, adresse=a0, variante=masques[rang_enr],
                     aires=aires_enr[rang_enr],
                     etage=bloc.get("etage"), fige=bloc.get("fige", False),
                     base_palette=base_bloc, col=col, bande=bande_obj,
                     # LE REGARD : un enregistrement du bloc des acolytes de Gill n'a pas
                     # d'animation, son image est choisie par le X d'un combattant.
                     comportement=(7 if a0 in REGARD_ELEMENTS
                                   else imm.get("comportement", 0)),
                     pas=pas_obj if suites else None,
                     # LA BOITE DE RUPTURE vient du dictionnaire, comme le comportement :
                     # sans cette ligne elle ne traverse pas, et la fiche sort sans boite.
                     boite=imm.get("boite"),
                     bornes=([sum(len(t) for t in suites[:j]) for j in range(len(suites) + 1)]
                             if suites else None))

            # UN SCRIPT DEJA VU EST ECARTE -- sauf quand le bloc dit le contraire.
            #
            # La regle protege d'un vrai doublon : les deux blocs d'Oro partagent les
            # scripts 6, 8 et 9, et on garde la version du premier, celle qui est a
            # l'ecran. Mais elle est trop large pour un bloc ou plusieurs objets
            # DISTINCTS jouent la meme animation a des places differentes -- les quatre
            # chauves-souris d'Oro, dont trois portent le script 34. Sans `doublons`,
            # trois d'entre elles disparaissaient en silence.
            # LA CLE PORTE L'ETAGE -- 25/09/2026. Elle ne portait que le script, et le
            # decor 8 en souffrait : ses deux bandes sont DEUX ETAGES (56 pour l'aire 0,
            # 30 pour les aires 1 et 2) et leurs objets se ressemblent. Le script 2 de
            # l'etage 56, en x 720, etait ecarte parce que l'etage 30 en avait deja un,
            # en x 384. Deux objets distincts, deux etages : ce n'etait pas un doublon.
            # Les decors a un seul etage ne changent pas d'un pixel.
            cle_vue = (bloc.get("etage") or ETAGE[decor], sc)

            if cle_vue in vus and not bloc.get("doublons"):
                print("   %08X script %d ecarte : deja pose depuis %08X (etage %d)"
                      % (a0, sc, vus[cle_vue], cle_vue[0]))
                continue

            cols, ligs, _ox, _oy, _e = grille(o)

            # LA LARGEUR N'ECARTE PLUS : on SERT en morceaux voisins (`morceaux_objet`).
            # Seul le nombre d'images reste redhibitoire -- la cle n'a que six bits pour
            # l'image, et il n'y a pas de « morceau » qui puisse la contourner.
            if len(images) > IMAGES_MAX:
                print("   %08X script %d ecarte : %d images (max %d)"
                      % (a0, sc, len(images), IMAGES_MAX))
                continue

            if ligs > CASES_MAX:
                print("   %08X script %d ecarte : %d lignes, indecoupable en colonnes"
                      % (a0, sc, ligs))
                continue

            vus[cle_vue] = a0
            out.append(o)

    return ordonner_comme_le_code(decor, out)


def ordonner_comme_le_code(decor, objs):
    """Remet les objets dans l'ordre ou le CODE les cree.

    AUCUN des 97 chargeurs lisibles du binaire n'ecrit `+76` -- `position_z` dans le WORK.
    La profondeur n'est donc pas dans les blocs : tous les objets d'un decor la prennent du
    modele, et **a profondeur egale c'est l'ordre de creation qui decide qui passe devant**.

    Cet ordre est dans le code : l'ordre des `jsr` de la routine d'etage, puis l'ordre des
    enregistrements de chaque bloc -- c'est celui que `blocs2i` conserve. Le notre suivait
    l'ordre de `TABLES`, ecrit a la main au fil des trouvailles, et c'est ce qui mettait
    les cages de Yun DERRIERE le fumeur au lieu de devant.

    Un objet dont le bloc n'apparait pas dans la marche du code garde sa place relative, a
    la fin : on ne lui invente pas un rang.
    """
    # L'ORDRE VIENT DE `my_priority`, ET ON LE LIT DEJA : c'est `+556`, et il vaut le
    # NUMERO DE PALETTE (§5t). Un `z` plus GRAND est plus LOIN, donc le plus lointain se
    # dessine EN PREMIER et le plus proche EN DERNIER : on trie par priorite DECROISSANTE.
    #
    # C'est ce qui met les cages de Yun (90) devant les paniers (93), que Frederic
    # signalait. Et ca n'importe PAS l'echelle absolue de 2I -- reporter 90 ou 91 dans le
    # `z` d'une fiche place l'objet derriere nos plans (84, 90, 94) et le fait disparaitre.
    # L'ordre relatif, lui, ne peut rien cacher.
    # A PRIORITE EGALE, c'est l'ordre de CREATION qui departage : l'ordre des `jsr` de la
    # routine d'etage, puis celui des enregistrements. On l'apparie par numero de script,
    # la seule cle que les deux cotes portent a coup sur.
    numero = next((e["decor"] for e in TABLES[decor] if "decor" in e), None)
    rang = {}

    if numero is not None:
        try:
            import blocs2i

            for k, o in enumerate(blocs2i.objets_du_decor(numero)):
                rang.setdefault(o["script"], k)
        except Exception as e:
            print("   ordre du code indisponible (%s) : on s'en tient a la priorite" % e)

    # Ce que le code ne place pas garde sa place relative, a la fin : on ne lui invente pas
    # un rang. Et un objet sans palette lue garde la sienne aussi -- on ne lui suppose pas
    # une profondeur.
    tard = len(rang) + len(objs)
    ordre = {id(o): k for k, o in enumerate(objs)}

    def cle(o):
        p = o.get("pal")
        return (-p if p is not None else 1,
                rang.get(o["script"], tard),
                ordre[id(o)])

    return sorted(objs, key=cle)


def palette_de(decor, sp_morceaux):
    """Les 64 couleurs ARGB1555 du sprite.

    Le numero passe par `bases.numero` : un decor peut avoir DEUX banques, separees par
    l'offset du morceau et non par ses drapeaux. Oro est dans ce cas -- 1429 pour la
    grotte, 1674 pour les betes -- et aucun de ses sprites ne melange les deux, donc une
    palette par sprite suffit toujours.
    """
    champ = sp_morceaux[0][1]
    num = bases.numero(decor, champ >> 9, champ & 0x1FF)

    if num is None:
        raise SystemExit("palette inconnue : decor %s, drapeaux %d, offset %d"
                         % (decor, champ >> 9, champ & 0x1FF))

    d = open(P.BIN, "rb").read()
    pal = np.frombuffer(d[P.POFF + num * 128:P.POFF + num * 128 + 128],
                        dtype="<u2").copy()

    # L'INDEX 0 EST TRANSPARENT PAR CONSTRUCTION, et la banque du binaire ne le sait
    # pas : elle y met une vraie couleur. Le convertisseur du jeu ecrit zero dans la
    # premiere case avant de deplier la tuile (`mov.w r2,@r4` en 0x8C0F6EAC), et nos
    # cases VIDES sont justement des zeros. Sans ca, chaque sprite sort entoure d'un
    # carre noir opaque -- vu a l'ecran le 30/08 sur les figures de Gill.
    pal[0] = 0
    return num, pal


_brute = None


def banque_brute():
    """La banque de couleurs en ARGB1555 BRUT -- `palettes.lire` convertit en RGB8, ce qui
    n'est pas inversible et ne permet donc pas de FABRIQUER une palette."""
    global _brute

    if _brute is None:
        _brute = palettes.lire_brut(P.BIN, P.POFF, 2715)

    return _brute


def grille(o):
    """(cols, ligs, ox, oy, [(dx, dy) par image]) -- la grille qui contient TOUT.

    **Les images d'une animation n'ont ni la meme taille ni la meme ancre.** Les caler
    toutes sur le coin de la grille, ce que faisait la premiere version, fait sauter le
    sprite d'une image a l'autre -- vu a l'ecran le 30/08 sur Gill. Chaque image se pose
    donc a l'ecart que son ancre lui donne, l'origine commune etant celle de l'image 0.
    """
    ref = o["images"][0]
    rx = ref["ancre"][0] + ref["x0"]
    ry = ref["ancre"][1] + ref["y0"]
    ecarts = [(im["ancre"][0] + im["x0"] - rx, im["ancre"][1] + im["y0"] - ry)
              for im in o["images"]]
    x0 = min(d[0] for d in ecarts)
    y0 = min(d[1] for d in ecarts)
    x1 = max(d[0] + im["img"].shape[1] for d, im in zip(ecarts, o["images"]))
    y1 = max(d[1] + im["img"].shape[0] for d, im in zip(ecarts, o["images"]))
    ox, oy = -x0, -y0
    cols = (x1 - x0 + 15) // 16
    ligs = (y1 - y0 + 15) // 16
    return cols, ligs, ox, oy, ecarts


def est_une_boucle(o):
    """Toujours oui -- LA MESURE A ETE REMPLACEE PAR LA LECTURE (23/09/2026 au soir).

    Cette fonction cherchait un PALINDROME dans les ecarts d'image a image pour decider
    qu'une suite n'etait pas une animation mais une pose balayee, et elle ne servait qu'a
    un seul objet de tout 2nd Impact : l'acolyte 0 de Gill (`bg00`), dont le profil est

        0 86 89 147 189 259 351 382 351 259 189 147 89 86

    Le binaire tranche autrement, et il a le dernier mot. Le chargeur `0x8C04AE04` ecrit
    en `objet[+52]` l'indice de la boucle, et l'id 184 (`0x8C04AA54`) repartit dessus :

        indice 0 -> 8C04AA92   `mov #11,r6` puis le poseur ORDINAIRE `0x8C0B4AD4`
        indice 1 -> 8C04AB88   le regard, seul a passer par `0x8C04ACB2`
        indice 2,3 -> 8C04AD0C `objet[+456]`, le script de l'enregistrement, meme poseur

    L'acolyte 0 pose donc son script 11 et le laisse se derouler : c'est une ANIMATION,
    et un palindrome y est normal -- une tete qui part et revient. Le figer etait une
    erreur, et c'est celle que Frederic a vue : « l'acolyte central suit bien des yeux
    les combattants mais les autres personnages n'ont plus aucune animation ».

    On garde la fonction parce que la fiche l'appelle, mais elle ne decide plus rien.
    """
    return True


class TropDeCouleurs(Exception):
    """L'objet demande plus de 63 couleurs -- une palette de 64 n'y suffit pas."""


def morceaux_objet(o, etage=None):
    """Le decoupage d'un objet d'ASSET en tranches de colonnes qui tiennent dans le cache.

    Un objet trop large n'est pas a retailler, il est a SERVIR en plusieurs objets voisins
    qui se rejoignent au pixel. C'est ce qui manquait pour les gros sprites de decor :
    etaient ecartes faute de ce decoupage Elena (8x20 = 160 cases), Yun (99), Ryu (36), et
    une bonne moitie des objets de New Generation, jusqu'a 240 cases.

    `etage` absent = la largeur par defaut, 32 cases. Voir `cases_max_de` : seuls les etages
    qu'`OBJETS_MAX` ecrete prennent 64, et on les elargit UN PAR UN.
    """
    cases_max = cases_max_de(etage)
    cols, ligs, _ox, _oy, _e = grille(o)

    if cols * ligs <= cases_max:
        return [(0, cols)]

    large = max(1, cases_max // ligs)
    return [(c, min(large, cols - c)) for c in range(0, cols, large)]


def composer(o):
    """Les images de l'objet posees sur la grille ENTIERE, en couleur et en provenance.

    Rend `(cols_tot, ligs, [image ARGB1555], [provenance])`. La provenance porte, pixel
    par pixel, le NUMERO de la palette source qui l'a peint -- c'est `poser_1555` qui la
    releve pendant la composition, la ou le recouvrement des morceaux se decide.

    Les images sont posees sur la grille entiere et tranchees APRES : un morceau qui se
    composerait sur sa seule tranche perdrait les pixels que l'ecart d'ancre d'une image
    amene depuis la colonne voisine.
    """
    cols_tot, ligs, ox, oy, ecarts = grille(o)
    images = []
    sources = []

    for n, im in enumerate(o["images"]):
        u = np.zeros((ligs * 16, cols_tot * 16), np.uint16)
        s = np.zeros((ligs * 16, cols_tot * 16), np.uint16)
        src = im.get("c1555")
        prov = im.get("src1555")

        if src is None:
            # pas de composition en couleur : on retombe sur les index bruts
            src = np.where(im["msk"], im["img"], 0).astype(np.uint16)
            prov = None

        a, b = oy + ecarts[n][1], ox + ecarts[n][0]
        u[a:a + src.shape[0], b:b + src.shape[1]] = src

        if prov is not None:
            s[a:a + prov.shape[0], b:b + prov.shape[1]] = prov

        images.append(u)
        sources.append(s)

    return cols_tot, ligs, images, sources


def groupes_palette(o, col0=0, ncols=None):
    """Comment servir cette tranche : la liste des groupes de PALETTES SOURCE a poser.

    C'EST LE JUMEAU DE `morceaux_objet`, ET LA MEME IDEE — 02/09/2026.
    -----------------------------------------------------------------
    Un objet trop LARGE n'est pas a retailler, il est a servir en plusieurs objets voisins
    (`morceaux_objet`). Un objet trop COLORE n'est pas a reduire non plus : il est a servir
    en plusieurs objets SUPERPOSES, chacun avec sa palette, chacun ne dessinant que les
    pixels qui lui reviennent. Deux objets de Hugo le demandaient -- 78 et 93 couleurs
    quand une palette n'en tient que 63 -- et c'est ce qui bloquait sa foule.

    LE PARTAGE SE FAIT PAR PROVENANCE, PAS PAR COULEUR, et c'est ce qui le rend sur :

    * **une palette source ne porte que 63 couleurs utiles** (l'index 0 est transparent et
      n'est jamais ecrit). Une couche batie sur UNE palette source tient donc TOUJOURS,
      sans avoir a l'esperer. Mesure sur les huit objets de Hugo : 53 au plus ;
    * **chaque pixel n'a qu'une provenance**, celle relevee pendant la composition. Les
      couches forment donc une partition -- verifie : leur somme redonne l'image au pixel
      pres, sur tous les objets du port. Partager par COULEUR aurait le meme effet ici,
      mais un pixel recouvert par un morceau d'une autre palette serait sorti dans les
      deux couches, et l'ordre de dessin de deux objets de meme `z` ne les departage pas.

    Les groupes sont fusionnes tant que leur union tient sous 63 : un objet qui melange
    trois palettes source n'en demande pas trois si deux suffisent.

    Rend `[None]` quand une seule palette suffit -- le cas de tous les objets sauf deux --
    pour que ni le prefixe ni la sortie ne changent pour eux.
    """
    cols_tot, ligs, images, sources = composer(o)
    cols = cols_tot if ncols is None else ncols
    x0, x1 = col0 * 16, (col0 + cols) * 16

    # les couleurs de la tranche, palette source par palette source
    par_source = {}
    toutes = set()

    for u, s in zip(images, sources):
        z, zs = u[:, x0:x1], s[:, x0:x1]
        peints = z != 0
        toutes.update(int(v) for v in np.unique(z[peints]))

        for num in np.unique(zs[peints]):
            m = peints & (zs == num)
            par_source.setdefault(int(num), set()).update(
                int(v) for v in np.unique(z[m]))

    if len(toutes) <= 63:
        return [None]

    groupes = []
    courant = set()
    couleurs = set()

    for num in sorted(par_source):
        if courant and len(couleurs | par_source[num]) > 63:
            groupes.append(frozenset(courant))
            courant, couleurs = set(), set()

        courant.add(num)
        couleurs |= par_source[num]

    if courant:
        groupes.append(frozenset(courant))

    return groupes


def bloc_c(decor, o, prefixe, col0=0, ncols=None, garder=None):
    """Le C d'un objet : ses tuiles, sa table de cases, ses durees, sa palette.

    `col0` / `ncols` decoupent la grille en tranches de colonnes -- voir `morceaux_objet`.
    `garder`, quand il est donne, est l'ensemble des PALETTES SOURCE que cette couche
    dessine ; les pixels des autres lui sont transparents -- voir `groupes_palette`.
    """
    cols_tot, ligs, images_1555, sources = composer(o)
    cols = cols_tot if ncols is None else ncols
    L = []
    cases = []

    # LA PALETTE EST FABRIQUEE, PAS EMPRUNTEE A UN MORCEAU — 02/09/2026.
    #
    # `palette_de` ne prenait que la palette du PREMIER morceau. Or un sprite peut en
    # melanger plusieurs : vingt et un chez Hugo, onze chez Yang, et leurs morceaux tirent
    # sur deux banques eloignees (1221 et 1654). Tous les morceaux qui n'etaient pas du
    # premier groupe sortaient donc avec de fausses couleurs -- c'est ce que Frederic
    # voyait sur Hugo (tous), Ryu, Yun et Yang.
    #
    # On compose chaque image en ARGB1555 vrai (`poser_1555`, chaque morceau avec SA
    # palette), on releve les couleurs reellement employees, et on les reindexe dans une
    # palette a nous.
    #
    # LE RECENSEMENT PORTE SUR LA TRANCHE, PAS SUR LA GRILLE ENTIERE — 02/09/2026.
    #
    # Il comptait les couleurs de tout l'objet, si bien que decouper en colonnes ne
    # reduisait RIEN : les trois morceaux d'`a28o5` annoncaient tous les 78 couleurs de
    # l'objet entier, alors qu'ils en emploient 65, 75 et 15. Les couleurs hors tranche ne
    # sont de toute facon jamais emises -- elles tombent hors des cases qu'on ecrit.
    couleurs = []
    rang_de_couleur = {}
    x0, x1 = col0 * 16, (col0 + cols) * 16

    for n in range(len(images_1555)):
        if garder is not None:
            # LA COUCHE : les pixels des autres palettes source lui sont transparents.
            images_1555[n] = np.where(np.isin(sources[n], sorted(garder)),
                                      images_1555[n], 0)

        z = images_1555[n][:, x0:x1]

        for v in np.unique(z):
            if v and v not in rang_de_couleur:
                rang_de_couleur[int(v)] = len(couleurs) + 1
                couleurs.append(int(v))

    if len(couleurs) > 63:
        # UN OBJET NE PORTE QU'UNE PALETTE DE 64. `groupes_palette` doit l'avoir partage
        # avant d'arriver ici ; s'il ne l'a pas fait, on le DIT et on l'ecarte plutot que
        # d'arreter toute la generation.
        raise TropDeCouleurs("%s : %d couleurs, la palette n'en tient que 63"
                             % (prefixe, len(couleurs)))

    table = np.zeros(65536, np.uint8)
    for v, r in rang_de_couleur.items():
        table[v] = r

    for n, im in enumerate(o["images"]):
        g = table[images_1555[n]]

        for lig in range(ligs):
            for col in range(cols):
                sc = (col0 + col) * 16
                bloc = g[lig * 16:lig * 16 + 16, sc:sc + 16]

                # UNE CASE ENTIEREMENT TRANSPARENTE NE VAUT PAS UN MORCEAU DE CACHE.
                #
                # Le moteur sait deja quoi faire d'une case que la table ne couvre pas :
                # `DecorObjets_Tuile` rend `tuile_vide` sous `CLE_VIDE`, une seule entree
                # partagee pour toutes. L'emettre quand meme, c'etait payer un morceau
                # plein pour du vide -- et le tas n'en tient QUE 1024 (`x16_map[4][16]`).
                # `bloc_c_page` sautait deja ces cases ; ici elles etaient toutes emises,
                # ce qui ne se voyait pas tant qu'un objet couvrait sa grille. Une COUCHE
                # de palette, elle, en laisse vides la plupart.
                if not bloc.any():
                    continue

                nom = "%s_i%d_%d_%d" % (prefixe, n, col, lig)
                oct = AN0.entrelacer(bloc)
                L.append("static const unsigned char %s[256] = { %s };"
                         % (nom, ", ".join(str(v) for v in oct)))
                cases.append("    { %d, %d, %d, %s }," % (n, col * 16, lig * 16, nom))

    L.append("")
    L.append("static const DecorTuile %s_tuiles[] = {" % prefixe)
    L.extend(cases)
    L.append("};")
    L.append("static const unsigned char %s_durees[%d] = { %s };"
             % (prefixe, len(o["images"]),
                ", ".join(str(im["duree"]) for im in o["images"])))
    # La palette EFFECTIVE : l'index 0 reste transparent, les couleurs relevees suivent.
    pal = [0] * 64
    for v, r in rang_de_couleur.items():
        pal[r] = v

    # Le numero d'origine n'est plus qu'une etiquette, gardee pour le journal et pour
    # retrouver d'ou vient l'objet ; ce n'est plus lui qui colore. Pour une couche, c'est
    # la palette source de la couche qui est parlante.
    if garder:
        num = min(garder)
    elif o.get("base_palette") is not None:
        # la base du bloc, comme pour la composition ; `bases.numero` ne connait que celles
        # du decor
        num = o["base_palette"] + (o["images"][0]["morceaux"][0][1] & 0x1FF)
    elif o.get("col") is not None:
        num = PR.palette(o["bande"], o["col"], o["images"][0]["morceaux"][0][1] & 0x1FF)
    else:
        num, _ = palette_de(decor, o["images"][0]["morceaux"])
    L.append("static const unsigned short %s_palette[64] = { %s };"
             % (prefixe, ", ".join("0x%04X" % v for v in pal)))
    L.append("")
    return "\n".join(L), cols, ligs, len(o["images"]), num, len(cases)


def boucle_de(decor, o):
    """Le champ `boucle` d'une fiche. Un objet a comportement tourne : c'est le moteur qui
    choisit son image parmi toutes."""
    if o.get("comportement"):
        return 1
    if o.get("fige"):
        return 0
    return BOUCLE.get(decor, {}).get(o["rang"], 1 if est_une_boucle(o) else 0)


def fiche(decor, o, prefixe, cols, ligs, nb_images, num_pal, col0=0, nb_tuiles=None,
          garder=None, variante=0xF):
    """La ligne de `decor_animations` : position calculee, comme partout.

    `col0` decale l'abscisse d'un morceau : les tranches d'un objet decoupe se rejoignent
    au pixel pres, chacune posee 16 px plus a droite que la precedente par colonne.

    `nb_tuiles` est le nombre de tuiles REELLEMENT emises, et il ne vaut plus
    `nb_images * cols * ligs` : les cases entierement transparentes sont sautees. C'est
    la borne de la boucle de `DecorObjets_Tuile` -- l'annoncer trop grand lui ferait lire
    au-dela du tableau.

    Une COUCHE de palette (`garder`) se pose exactement au meme endroit que ses soeurs :
    elles se superposent, elles ne se cotoient pas.
    """
    im = o["images"][0]
    sol = P.sol(decor)
    _c, _l, ox, oy, _e = grille(o)
    # LE `x` EST SIGNE, et un decor peut le compter depuis le milieu de la bande.
    # Sans `DECALAGE_X`, `x_signe` vaut `o["x"]` pour les treize autres decors -- leurs
    # `x` sont tous positifs -- et rien ne change pour eux.
    x_signe = o["x"] - 65536 if o["x"] > 32767 else o["x"]
    ajx, ajy = AJUSTEMENT.get(decor, (0, 0))
    bx = (x_signe + DECALAGE_X.get(decor, 0) + ajx
          + im["ancre"][0] + im["x0"] - ox + col0 * 16) & 0x3FF
    by = (sol - o["y"] + ajy + im["ancre"][1] + im["y0"] - oy) & 0x3FF
    fam = FAMILLE[decor].get(o["plan"], FAMILLE[decor][None])
    z = Z[decor].get(o["plan"], Z[decor][None])
    dou = "formule"


    # La mesure passe devant : quand une copie de l'objet est peinte dans la banque du
    # disque, c'est elle qui dit ou il va, et sur quel plan.
    if o["script"] in MESURE.get(decor, {}):
        # LA MESURE DIT LA PLACE ET LE PLAN, PAS LA PROFONDEUR. Le `z` du quadruplet est
        # ignore : `+556` le donne, et pour l'edifice d'Oro il vaut **90** quand la table
        # en portait 92. Retrouver un objet peint dans une page etablit ou il est et sur
        # quel plan ; ca ne dit rien de son ordre de dessin, que le code, lui, ecrit.
        bx, by, fam, _z_ignore = MESURE[decor][o["script"]]
        # La mesure porte sur l'OBJET ENTIER ; chaque morceau garde son decalage de
        # colonnes, sans quoi les tranches se superposeraient toutes au meme endroit.
        bx = (bx + col0 * 16) & 0x3FF
        dou = "MESURE dans la banque"

    # Elle passe apres la mesure : la mesure dit ou l'objet est, cette table dit seulement
    # lequel de deux objets superposes est devant l'autre.
    if o["script"] in Z_OBJET.get(decor, {}):
        z = Z_OBJET[decor][o["script"]]
        dou += " + z force"

    # LA PROFONDEUR EST LUE, ET LES DEUX ECHELLES SONT LA MEME — mesure du 04/09/2026.
    #
    # `+556 my_priority` vaut le numero de palette (§5t). Restait a savoir si l'echelle de
    # 2I est celle de 3SX. **Elle l'est, et ca se lit dans les deux binaires** : la fiche
    # d'un combattant est `{ my_col_mode 0x4200, my_col_code 0x2000, my_pr, my_family 2 }`,
    # et SF3_2ND.BIN en porte DIX-SEPT, avec des `my_pr` de **28 a 56** -- exactement les
    # valeurs de `char_init_data2` cote 3S. Memes constantes, meme intervalle.
    #
    # J'avais d'abord borne le report a « en dessous de 80 », par crainte qu'un objet a 90
    # ne passe derriere nos plans (84, 90, 94) et disparaisse. Cette crainte venait d'une
    # regression -- « il manque tous les sprites » -- dont la cause etait AILLEURS : la
    # page effacee sur la BOITE des objets au lieu de l'empreinte de leurs sprites. La
    # borne n'avait donc aucun fondement, et un objet a 90 n'est pas cache : il passe
    # derriere les parties opaques du plan proche, ce que 2I fait aussi.
    if o.get("pal") is not None:
        z = o["pal"]
        dou = "priorite lue (+556)"

    y = 1024 - by - (ligs - 1) * 16
    b = boucle_de(decor, o)
    nt = nb_images * cols * ligs if nb_tuiles is None else nb_tuiles
    couche = "" if not garder else ", couche des palettes %s" % sorted(garder)
    # LE MASQUE DE VARIANTES : un bit par valeur de `z`. 0xF = de toutes les variantes,
    # ce qui est le cas de tout le port sauf la menagerie d'Oro.
    varie = "" if variante & 0xF == 0xF else (", variantes z %s"
                                              % [k for k in range(4) if variante & (1 << k)])
    varie += {SANS_AMI: ", sans ami du decor", AVEC_AMI: ", avec un ami du decor"}.get(
        variante & (SANS_AMI | AVEC_AMI), "")
    # LE COMPORTEMENT ET SES DEUX BORNES ne s'ecrivent que s'il y en a un : les autres
    # fiches s'arretent a `variante`, et le C complete a zero.
    # Un comportement SANS suites -- le REGARD des acolytes de Gill -- ecrit `NULL, NULL,
    # 0` comme un TRAJET de NG : son image ne vient pas d'une suite.
    if not o.get("comportement"):
        suite = ""
    elif o.get("bornes"):
        suite = ", %d, %s_pas, %s_suites, %d" % (o["comportement"], prefixe, prefixe,
                                                len(o["bornes"]) - 1)
    else:
        suite = ", %d, NULL, NULL, 0" % o["comportement"]
    # LA BOITE VIENT EN DERNIER, et une initialisation POSITIONNELLE exige tout ce qui la
    # precede : le trajet et les quatre champs d'echelle, a leurs valeurs neutres.
    #
    # ELLE EST MISE DANS LE REPERE DE LA FICHE. Le Dreamcast la range relative a
    # `objet[+102]`/`+106` ; ici `x` et `y` sont ceux de la fiche, et le `y` du port croit
    # dans le MEME SENS que celui de la scene (`1024 - (sol - y)`). Le tonneau de Hugo,
    # boite (6, 64, 33, 69) posee en 816,52, tombe donc en x 822..886 et y 86..155 --
    # dans sa fiche, qui va de 797 a 893 en x et de 65 a 209 en y.
    if o.get("boite"):
        bo = o["boite"]
        bo_x = (x_signe + DECALAGE_X.get(decor, 0) + ajx + bo[0]) & 0x3FF
        bo_y = 1024 - ((sol - o["y"] - bo[2] + ajy) & 0x3FF)
        if not o.get("comportement"):
            suite += ", 0, NULL, NULL, 0"
        # trajet, nb_trajet, TRAJET_FIN, puis les quatre champs d'echelle, puis la boite.
        suite += ", NULL, 0, 0, 0, 0, 0, 0, { %d, %d, %d, %d }" % (bo_x, bo[1], bo_y, bo[3])
    quoi = (COMPORTEMENTS[o["comportement"]] if o.get("comportement") else
            "boucle" if b else ("figee sur l'image 0 par sa routine" if o.get("fige")
                                else "POSE BALAYEE, figee sur l'image 0"))
    # LES AIRES : un masque de manches, 0 quand l'objet ne depend pas de la manche.
    # Voir `DecorAnimation::aires` -- Hugo change d'objets d'une manche a l'autre sans
    # changer de bande.
    return ('    { "%s", %d, %d, %d, %d, %d, %s_tuiles, %s_durees, %s_palette, %d, %d, %d, %d, %d, %d, 0x%X, 0x%X%s },'
            '  /* %08X, element %d,%d, objet %d, script %d, plan %s, %s, %s%s%s */'
            % (decor, etage_de(decor, o), nb_images, nt, cols, ligs,
               prefixe, prefixe, prefixe, num_pal, bx, y, fam, z, b, variante,
               o.get("aires", 0), suite,
               o.get("adresse", 0), o["x"], o["y"], o["rang"], o["script"], o["plan"],
               dou, quoi, couche, varie))


def images_de_page(decor, o):
    """Les trames de la grille du magasin, et leur palette commune.

    La grille se lit EN LIGNE D'ABORD : c'est l'ordre ou les pages se suivent dans la
    VRAM, donc celui ou la suite du binaire les enumere.
    """
    import pvc
    import bande3sx
    from rendupvc import carte_morton, SIDE

    src = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "pvc-2i", o.get("pvc", decor) + ".pvc")
    pages, _u, _s = pvc.decode(open(src, "rb").read())

    if "trames" in o:
        # Une image par pas de la SUITE du binaire : l'aller-retour du lac rejoue ses
        # trames, et chaque pas garde sa duree. Hors du masque, rien : ces blocs ne
        # changent pas et la page du plan les porte deja.
        banques = {}
        w, h = o["larg"], o["haut"]
        trames = []
        for bq, x, y, tournee in o["trames"]:
            if bq not in banques:
                banques[bq] = bande3sx.banque_rgba(pages, bq * 4096, carte_morton(SIDE))[0]
            if tournee:
                im = np.rot90(banques[bq][y:y + w, x:x + h], 3)[:h, :w].copy()
            else:
                im = banques[bq][y:y + h, x:x + w].copy()
            for r, ligne in enumerate(o["masque"]):
                for c, garde in enumerate(ligne):
                    if not garde:
                        im[r * 16:(r + 1) * 16, c * 16:(c + 1) * 16] = 0
            trames.append(im)
        return [trames[t] for t in o["suite_trames"]]

    arr = bande3sx.banque_rgba(pages, o["banque"], carte_morton(SIDE))[0]
    demi = arr[:512] if o["moitie"] == "haut" else arr[512:]

    w, h = o["larg"], o["haut"]
    # LE PAS N'EST PAS LA TAILLE. Chez Ibuki les trames font 272x245 mais se suivent tous
    # les 256 en hauteur : lire au pas de la hauteur decalerait chaque rangee de onze
    # pixels. On les separe.
    px, py = o.get("pas_x", w), o.get("pas_y", h)
    brutes = [demi[o["sy"] + l * py:o["sy"] + l * py + h,
                   o["sx"] + c * px:o["sx"] + c * px + w]
              for l in range(o["nl"]) for c in range(o["nc"])]

    return brutes


def indexer(brutes, decor, o, col0, cols):
    """Indexe les trames sur UNE palette, batie sur le seul morceau demande.

    La grande cascade porte 81 couleurs sur toute sa largeur -- plus que les 63 d'une
    palette. Chaque morceau n'en voit qu'une tranche, et sa propre palette suffit : c'est
    le decoupage qui rend la chose possible, pas une reduction des couleurs.
    """
    x0, x1 = col0 * 16, (col0 + cols) * 16
    tranches = [im[:, x0:x1] for im in brutes]

    # LA PALETTE : l'index 0 est transparent par construction, comme partout ailleurs.
    vus = [im[:, :, :3][im[:, :, 3] > 0] for im in tranches]
    vus = [v for v in vus if len(v)]
    couleurs = np.unique(np.concatenate(vus), axis=0) if vus else np.zeros((0, 3), np.uint8)

    if len(couleurs) > 63:
        raise SystemExit("%s en %d,%d, morceau %d : %d couleurs, une palette n'en tient que 63"
                         % (decor, o["sx"], o["sy"], col0, len(couleurs)))

    cle = {tuple(int(v) for v in c): i + 1 for i, c in enumerate(couleurs)}
    pal = np.zeros(64, np.uint16)

    for c, i in cle.items():
        # ARGB1555, comme la banque du binaire ; le bit 15 marque l'opacite.
        pal[i] = 0x8000 | ((c[0] >> 3) << 10) | ((c[1] >> 3) << 5) | (c[2] >> 3)

    images = []

    for im in tranches:
        idx = np.zeros(im.shape[:2], np.uint8)
        op = im[:, :, 3] > 0

        for y, x in zip(*np.nonzero(op)):
            idx[y, x] = cle[tuple(int(v) for v in im[y, x, :3])]

        images.append(idx)

    return images, pal


def couleurs_de_tranche(brutes, col0, cols):
    """Combien de couleurs opaques DISTINCTES une tranche emploie, toutes images confondues."""
    x0, x1 = col0 * 16, (col0 + cols) * 16
    vus = []

    for im in brutes:
        z = im[:, x0:x1]
        v = z[:, :, :3][z[:, :, 3] > 0]

        if len(v):
            vus.append(v)

    if not vus:
        return 0

    return len(np.unique(np.concatenate(vus), axis=0))


def morceaux_de_page(o, decor=None, etage=None):
    """Le decoupage en objets qui tiennent dans le cache, par tranches de colonnes.

    Un objet trop large n'est pas a retailler : il est a SERVIR en plusieurs objets voisins
    qui se rejoignent au pixel pres. La grande cascade fait 19 x 9 = 171 cases.

    DEUX BORNES, ET LA SECONDE SE MESURE -- 27/09/2026.

    La premiere est le cache : `cases_max_de(etage)`, 32 par defaut et 64 pour les etages
    de `CASES_LARGES`. Le plafond du moteur est 64 (`MorceauTrans cases[CASES_MAX]` de
    `decor_objets.c`) ; on ne s'en approche QUE pour l'etage qui le demande, parce que
    changer la largeur change les rangs, donc les palettes, donc tout le decor.

    La seconde est LA PALETTE : un morceau n'en porte qu'une, de 64 entrees dont la
    premiere est transparente, donc SOIXANTE-TROIS couleurs. Elle ne se calcule pas, elle
    se compte -- et c'est elle qui a tue la generation quand 2I est passe a 64 : un plan
    d'Akuma (`bg0f`) rassemblait alors 67 couleurs dans une seule tranche, et `indexer`
    s'arretait.

    On part donc de la tranche la plus large que le cache autorise et on la RETRECIT de
    moitie tant qu'une tranche depasse 63 couleurs. A 32 cases rien ne change : c'est la
    largeur qui a toujours ete servie, et les tranches y tenaient deja.
    """
    cases_max = cases_max_de(etage)
    cols = -(-o["larg"] // 16)
    ligs = -(-o["haut"] // 16)
    large = cols if cols * ligs <= cases_max else max(1, cases_max // ligs)

    if decor is not None:
        brutes = None

        while large > 1:
            if brutes is None:
                brutes = images_de_page(decor, o)

            if all(couleurs_de_tranche(brutes, c, min(large, cols - c)) <= 63
                   for c in range(0, cols, large)):
                break

            large //= 2

    return [(c, min(large, cols - c)) for c in range(0, cols, large)]


def bloc_c_page(decor, o, prefixe, col0=0, ncols=None):
    """Le C d'un objet tire des pages : ses tuiles, ses cases, ses durees, sa palette."""
    brutes = images_de_page(decor, o)
    ligs = -(-o["haut"] // 16)
    cols = ncols if ncols is not None else -(-o["larg"] // 16)
    # on complete la trame jusqu'au bord des cases AVANT de trancher, sinon la derniere
    # colonne d'un morceau deborderait de l'image.
    pleines = []
    for im in brutes:
        p = np.zeros((ligs * 16, -(-o["larg"] // 16) * 16, 4), im.dtype)
        p[:im.shape[0], :im.shape[1]] = im
        pleines.append(p)
    images, pal = indexer(pleines, decor, o, col0, cols)
    L = []
    cases = []

    vides = 0

    for n, g in enumerate(images):
        for lig in range(ligs):
            for col in range(cols):
                bloc = g[lig * 16:lig * 16 + 16, col * 16:col * 16 + 16]

                # UNE CASE ENTIEREMENT TRANSPARENTE NE VAUT PAS UN MORCEAU DE CACHE.
                #
                # Le moteur sait deja quoi faire quand aucune tuile ne couvre une case :
                # `DecorObjets_Tuile` rend `tuile_vide` sous `CLE_VIDE`, une seule entree
                # partagee. L'emettre quand meme, c'etait payer un morceau plein pour du
                # vide -- et le tas n'en tient QUE 1024 (`x16_map[4][16]`, quatre pages).
                # La cascade d'Ibuki a 272 cases dont 192 occupees : a quatre images
                # vivantes, 1088 morceaux au lieu de 768, et le jeu figeait.
                if not bloc.any():
                    vides += 1
                    continue

                nom = "%s_i%d_%d_%d" % (prefixe, n, col, lig)
                oct = AN0.entrelacer(bloc)
                L.append("static const unsigned char %s[256] = { %s };"
                         % (nom, ", ".join(str(v) for v in oct)))
                cases.append("    { %d, %d, %d, %s }," % (n, col * 16, lig * 16, nom))

    L.append("")
    L.append("static const DecorTuile %s_tuiles[] = {" % prefixe)
    L.extend(cases)
    L.append("};")
    durees = o["durees"] if "durees" in o else [o["duree"]] * len(images)
    L.append("static const unsigned char %s_durees[%d] = { %s };"
             % (prefixe, len(images), ", ".join(str(v) for v in durees)))
    L.append("static const unsigned short %s_palette[64] = { %s };"
             % (prefixe, ", ".join("0x%04X" % v for v in pal)))
    L.append("")
    return "\n".join(L), cols, ligs, len(images), len(cases), vides


def fiche_page(decor, o, prefixe, cols, ligs, nb_images, nb_tuiles, col0=0):
    """La ligne de `decor_animations` pour un objet tire des pages.

    La palette est POSEE avec l'objet, pas prise dans la banque : son numero ne sert donc
    a rien ici, et on met 0.
    """
    # `by` est le y DANS SON PROPRE PLAN, celui que donne l'index de bloc de destination.
    # L'entree de la grotte portait 832, mesure dans la banque entiere ; c'est la meme
    # chose pour la moitie basse (1024-832 = 512-320) mais faux pour la moitie haute, ou
    # le plan lointain serait sorti a 576 -- bien au-dela de l'ecran.
    y = 512 - o["by"] - (ligs - 1) * 16
    fam = o.get("fam", FAMILLE.get(decor, {}).get(None, 2))

    # UNE ANIMATION DE PAGE EST UN MORCEAU DE SON PLAN, donc elle en prend la PROFONDEUR.
    #
    # Ces objets-la -- les cascades de `bg07` et `bg0f`, l'entree de la grotte -- ne sont
    # PAS des objets de 2I : ces deux decors sont justement les seuls, avec `bg11`, dont le
    # `.pk` n'a pas de `F_ETC`. Ce sont des regions animees du fond, que nous decoupons
    # nous-memes. Aucun `+556` n'existe pour elles.
    #
    # Elles portaient toutes `z = 92`, qui est `Z_QUATRE` -- la priorite du QUATRIEME plan
    # de `etages.py`. La valeur n'etait pas arbitraire, mais elle etait la MEME pour
    # toutes : la cascade de `bg0f` (plan lointain, 94) passait donc devant son plan, et
    # celle de `bg07` (troisieme plan, 90) DERRIERE le sien. On prend maintenant la
    # profondeur du plan auquel chacune appartient, et l'ordre de dessin -- les objets
    # apres les plans -- la met juste devant les tuiles qu'elle remplace.
    #
    #     Z_LOIN 0x5E = 94   Z_PROCHE 0x54 = 84   Z_TIERS 0x5A = 90
    PLAN_DE_FAMILLE = {1: 94, 2: 84, 3: 90}
    z = o.get("z", PLAN_DE_FAMILLE.get(fam, Z.get(decor, {}).get(None, 0)))

    # A PROFONDEUR EGALE, LE PLAN GAGNE -- 15/09/2026, nuit. La cascade d'Elena 1 et le lac du
    # pont s'animaient dans le journal et restaient figes a l'ecran. Le plan est dessine a
    # `PrioBase[z]` ; chaque morceau d'objet ajoute 1/65536 a la matrice
    # (`appRenewTempPriority_1_Chip`, dans `seqsStoreChip`) et `PrioBase[z]` en garde la
    # trace : les morceaux d'un objet de meme `z` sont donc un peu PLUS LOIN que le plan, et le
    # test `LESS_OR_EQUAL` les refuse partout ou le plan est opaque. Akuma passe parce que son
    # plan est transparent sous ses cascades (10 % opaque) ; sous ces trames-ci, la trame 0 est
    # peinte dans la page (100 %). Un cran devant leur plan, et rien d'autre ne s'intercale.
    if "trames" in o and "z" not in o:
        z -= 1

    # Le dernier champ est le masque de VARIANTES : une animation de pages est de toutes
    # les variantes, aucun repartiteur `z` n'en depend.
    return ('    { "%s", %d, %d, %d, %d, %d, %s_tuiles, %s_durees, %s_palette, 0, %d, %d, %d, %d, 1, 0xF },'
            '  /* magasin %d,%d de la banque %d, %s%s */'
            % (decor, o.get("etage") or ETAGE[decor], nb_images, nb_tuiles, cols, ligs,
               prefixe, prefixe, prefixe, o["bx"] + col0 * 16, y, fam, z,
               o["sx"], o["sy"], o["banque"], o["quoi"],
               "" if col0 == 0 and cols * ligs <= cases_max_de(o.get("etage") or ETAGE[decor])
               else ", morceau a partir de la case %d" % col0))


def travail_decor(decor):
    """TOUT ce qu'un decor de 2nd Impact produit : ses blocs, ses fiches, son budget.

    SORTI DE `main` LE 25/09/2026 POUR ETRE MIS EN CACHE (`cache_decors.py`). Le budget
    de motifs y est LOCAL et part de zero : c'est ce qui rend le decor independant des
    autres, et `main` verifie au versement qu'aucun etage n'est servi deux fois.
    """
    blocs, fiches, lignes = [], [], []
    budget = {}

    for o in objets(decor):
        if o["script"] in EXCLUS.get(decor, set()):
            lignes.append("   %08X script %d ECARTE : voir EXCLUS"
                          % (o.get("adresse", 0), o["script"]))
            continue

        tranches = morceaux_objet(o, etage_de(decor, o))
        b = boucle_de(decor, o)
        nb_fiches = sum(len(groupes_palette(o, c, n)) for c, n in tranches)
        cout = nb_fiches * motifs_vivants(o, b)
        pris = budget.get(etage_de(decor, o), 0)

        if pris + cout > MOTIFS_MAX:
            lignes.append("   %08X script %d ecarte : %d motifs, il n'en reste que %d sur %d"
                          % (o.get("adresse", 0), o["script"], cout,
                             MOTIFS_MAX - pris, MOTIFS_MAX))
            continue

        budget[etage_de(decor, o)] = pris + cout

        for m, (col0, ncols) in enumerate(tranches):
            # DEUX DECOUPAGES, ET ILS SE COMPOSENT. Le premier est SPATIAL -- des
            # objets voisins, quand la grille passe 32 cases ; le second est
            # CHROMATIQUE -- des objets superposes, quand la tranche passe 63
            # couleurs. Les deux servent le meme objet en plusieurs, ils ne le
            # retaillent ni ne le reduisent.
            groupes = groupes_palette(o, col0, ncols)

            for g, garder in enumerate(groupes):
                prefixe = ("a%do%d" % (etage_de(decor, o), o["rang"])
                           + ("m%d" % m if m or col0 else "")
                           + ("p%d" % g if len(groupes) > 1 else ""))

                try:
                    c, cols, ligs, ni, num, nt = bloc_c(decor, o, prefixe, col0,
                                                        ncols, garder)
                except TropDeCouleurs as exc:
                    lignes.append("   ECARTE : %s" % exc)
                    continue

                f = fiche(decor, o, prefixe, cols, ligs, ni, num, col0, nt, garder,
                          o.get("variante", 0xF))
                blocs.append(c)
                # LES PAS ET LES SUITES d'un objet a comportement : (image, duree) pas par
                # pas, puis le premier pas de chaque suite et la fin.
                if o.get("comportement") and o.get("pas"):
                    blocs.append("static const unsigned char %s_pas[%d] = { %s };\n"
                                 "static const unsigned short %s_suites[%d] = { %s };\n"
                                 % (prefixe, 2 * len(o["pas"]),
                                    ", ".join("%d, %d" % ip for ip in o["pas"]),
                                    prefixe, len(o["bornes"]),
                                    ", ".join(str(b) for b in o["bornes"])))
                fiches.append(f)
                suite = ("" if len(tranches) == 1
                         else "   [morceau %d/%d, colonne %d]"
                         % (m + 1, len(tranches), col0))
                suite += ("" if len(groupes) == 1
                          else "   [couche %d/%d, palettes %s]"
                          % (g + 1, len(groupes), sorted(garder)))
                lignes.append("%-10s %-6d %-8d %-7d %s%s"
                              % (prefixe, cols, ligs, ni, f.strip()[:80], suite))

    return dict(blocs=blocs, fiches=fiches, lignes=lignes, budget=budget)


def main():
    ecrire = "--ecrire" in sys.argv
    src = io.open(DATA, encoding="utf-8", errors="surrogateescape").read()
    lignes = src.splitlines(True)

    # les blocs existants, un par prefixe, dans l'ordre du fichier
    debuts = {}
    for i, l in enumerate(lignes):
        # LES PREFIXES A CONSERVER SE DEDUISENT DE `ETAGE`, ILS NE S'ECRIVENT PAS EN DUR.
        #
        # Cette liste etait figee a `("a22", "a31")` du temps ou seuls Gill et Oro etaient
        # generes. En ajoutant Alex, Ryu, Yun, Necro et Hugo, leurs ANCIENNES fiches --
        # `a23`, `a24`, `a25`, `a27`, `a28` -- ont ete conservees EN PLUS des nouvelles,
        # et `decor_anim_par_etage` pointait sur l'ancienne : le jeu jouait encore l'objet
        # d'avant. C'est ce que Frederic a vu, « la ventilation n'est pas animee ».
        for p in ("a22", "a23", "a24", "a25", "a27", "a28", "a31", "a34"):
            if int(p[1:3]) in ETAGE.values():
                continue
            if l.startswith("static const unsigned char %s_i" % p) or \
               l.startswith("static const DecorTuile %s_tuiles" % p):
                debuts.setdefault(p, i)
    ordre = sorted(debuts, key=lambda p: debuts[p])
    fins = {}
    for k, p in enumerate(ordre):
        fins[p] = debuts[ordre[k + 1]] if k + 1 < len(ordre) else None

    for k, p in enumerate(ordre):
        if fins[p] is None:
            j = debuts[p]
            while j < len(lignes) and not lignes[j].startswith("const DecorAnimation"):
                j += 1
            fins[p] = j

    # les fiches existantes, telles quelles
    i0 = next(i for i, l in enumerate(lignes) if l.startswith("const DecorAnimation"))
    i1 = next(i for i in range(i0, len(lignes)) if lignes[i].startswith("};"))
    anciennes = {}
    for l in lignes[i0 + 1:i1]:
        m = l.strip()
        if m.startswith('{ "'):
            anciennes[m.split('"')[1]] = l.rstrip("\n")

    print("%-8s %-6s %-8s %-7s %s" % ("objet", "cols", "ligs", "images", "fiche"))
    blocs = []
    fiches = []
    # LE BUDGET DE MOTIFS, PAR ETAGE. Un objet se pose ENTIER ou pas du tout : le servir
    # a moitie laisserait un sprite tronque a l'ecran. On le dit quand on l'ecarte, au
    # lieu de laisser le moteur geler.
    budget = {}

    # LE CACHE PAR DECOR -- 25/09/2026, voir `cache_decors.py`. Le travail d'un decor
    # ne depend d'aucun autre : son budget de motifs est indexe par ETAGE, et deux decors
    # ne partagent pas d'etage (verifie a l'execution, juste en dessous). On le calcule
    # donc dans un budget LOCAL, parti de zero, et on verse le resultat dans le global.
    #
    # La cle ne porte que l'empreinte des outils : contrairement a New Generation, 2nd
    # Impact n'a pas de module d'enregistrements separe -- ses tables sont DANS
    # `animer2i.py`, qui est dans l'empreinte. Corriger un outil de NG ne touche donc pas
    # a ce cache, et c'est tout le gain : les deux minutes de 2I ne se repaient plus.
    import cache_decors as CA
    venus_du_cache = 0

    for decor in TABLES:
        c = CA.cle("2i", decor)
        v = CA.lire(c)

        if v is None:
            v = travail_decor(decor)
            CA.ecrire(c, v)
        else:
            venus_du_cache += 1

        for l in v["lignes"]:
            print(l)

        for e, cout in v["budget"].items():
            if budget.get(e):
                # Deux decors sur le meme etage : le budget du second ne partirait plus
                # de zero et le cache mentirait. On le DIT au lieu de produire un C faux.
                print("   ATTENTION : l'etage %d recoit deux decors -- le cache par decor"
                      " ne vaut plus, relance avec --froid" % e)
            budget[e] = budget.get(e, 0) + cout

        blocs.extend(v["blocs"])
        fiches.extend(v["fiches"])

    print("   (%d decors de 2I venus du cache sur %d)" % (venus_du_cache, len(TABLES)))

    for decor, liste in PAGES_ANIMEES.items():
        for k, o in enumerate(liste):
            o = completer_page_2i(o)
            etage = o.get("etage") or ETAGE[decor]
            tranches = morceaux_de_page(o, decor, etage)
            # LE BUDGET DE MOTIFS VAUT AUSSI POUR LES PAGES -- 16/09/2026 : il n'etait compte
            # que pour les objets de l'asset, et c'est l'etage entier qui le paie.
            if "durees" in o:
                cout = len(tranches) * motifs_vivants(o, True)
                pris = budget.get(etage, 0)
                if pris + cout > MOTIFS_MAX:
                    print("   PAGES %s ecartees : %d motifs, il n'en reste que %d sur %d"
                          % (o.get("quoi", k), cout, MOTIFS_MAX - pris, MOTIFS_MAX))
                    continue
                budget[etage] = pris + cout
            for m, (col0, ncols) in enumerate(tranches):
                prefixe = "a%dp%d" % (etage, k) + ("m%d" % m if m or col0 else "")
                c, cols, ligs, ni, nt, vides = bloc_c_page(decor, o, prefixe, col0, ncols)
                f = fiche_page(decor, o, prefixe, cols, ligs, ni, nt, col0)
                blocs.append(c)
                fiches.append(f)
                print("%-10s %2dx%-2d %d images  %4d tuiles (%3d cases vides sautees)"
                      % (prefixe, cols, ligs, ni, nt, vides))

    print("\nbudget de motifs par etage (sur %d) : %s"
          % (MOTIFS_MAX, ", ".join("%d:%d" % kv for kv in sorted(budget.items()))))

    # LES FICHES D'UN MEME ETAGE DOIVENT SE SUIVRE : les animations de pages viennent apres
    # tous les objets, et l'etage 30 ou 56 en a des deux sortes. On les range par etage, sans
    # changer leur ordre a l'interieur d'un etage -- c'est lui qui donne le rang.
    # Groupees dans l'ordre ou chaque etage apparait pour la premiere fois : les autres
    # etages ne bougent pas.
    premier = {}
    for i, f in enumerate(fiches):
        premier.setdefault(int(f.split(",")[1]), i)
    fiches = sorted(fiches, key=lambda f: premier[int(f.split(",")[1])])

    if not ecrire:
        print("\nRien n'a ete ecrit. `--ecrire` pour poser le C.")
        return

    # on remonte le fichier : l'en-tete, nos blocs, puis ceux des autres etages.
    #
    # LA COUPE SE FAIT A LA PREMIERE DECLARATION DE TUILES, quel que soit son prefixe --
    # sinon les blocs qu'on regenere restent EN PLUS des anciens, et le C ne compile plus
    # (redefinition). `debuts` ne contient que les prefixes conserves.
    tete = next(i for i, l in enumerate(lignes)
                if l.startswith("static const unsigned char a"))
    out = list(lignes[:tete])
    out.append("\n".join(blocs) + "\n")
    for p in ordre:
        out.extend(lignes[debuts[p]:fins[p]])

    rangs = {}
    n = 0
    lignes_fiches = []
    for f in fiches:
        lignes_fiches.append(f)
    n = 0
    # L'index par etage doit couvrir LES DEUX sources, et dans l'ordre ou les fiches ont
    # ete posees : d'abord les objets tires de l'asset, puis ceux tires des pages. Un
    # decor absent de cette boucle garde `-1` et n'affiche rien, quoi qu'on ait genere.
    #
    # ON COMPTE PAR ETAGE LU DANS LA FICHE, PAS PAR DECOR -- 16/09/2026 : le decor 8 pose ses
    # objets a deux etages (30 et 56). Les fiches d'un meme etage doivent se suivre.
    for f in fiches:
        etage = int(f.split(",")[1])
        if etage in rangs and rangs[etage][0] + rangs[etage][1] != n:
            print("   ATTENTION : les fiches de l'etage %d ne se suivent pas" % etage)
        p0, c = rangs.get(etage, (n, 0))
        rangs[etage] = (p0, c + 1)
        n += 1
    for p in ordre:
        etage = int(p[1:3])
        decor = [d for d in anciennes if anciennes[d].split(",")[1].strip() == str(etage)]
        if not decor:
            continue
        lignes_fiches.append(anciennes[decor[0]])
        rangs[etage] = (n, 1)
        n += 1

    out.append("const DecorAnimation decor_animations[] = {\n")
    out.append("\n".join(lignes_fiches) + "\n")
    out.append("};\n\n")
    out.append("const int decor_nb_animations = %d;\n\n" % n)
    prem = [-1] * 58
    nb = [0] * 58
    for etage, (p0, c) in rangs.items():
        prem[etage] = p0
        nb[etage] = c
    out.append("/* Index de la PREMIERE animation de chaque etage, -1 s'il n'en a pas. */\n")
    out.append("const short decor_anim_par_etage[58] = { %s };\n\n"
               % ", ".join(str(v) for v in prem))
    out.append("/* Combien d'animations chaque etage porte. Gill en a quatre. */\n")
    out.append("const short decor_nb_par_etage[58] = { %s };\n"
               % ", ".join(str(v) for v in nb))

    io.open(DATA, "w", encoding="utf-8", errors="surrogateescape",
            newline="").write("".join(out))
    print("\n%d fiches ecrites dans decor_objets_data.c" % n)
    # CE FICHIER EST ECRIT A NEUF, ET NEW GENERATION N'EST PAS DEDANS -- 24/09/2026.
    #
    # `animerng.py --ecrire` AJOUTE ses 525 fiches a celles-ci ; ecrire ici sans le
    # relancer laisse le port sans AUCUN objet anime sur les DIX-NEUF etages de New
    # Generation. Rien ne le signale : la compilation passe, le jeu se lance, et les
    # decors sont simplement vides. Frederic l'a vu chez Sean -- « a priori, il n'y a
    # pas de parallaxe » --, et deux lanceurs etaient partis avec l'amputation.
    print("   ATTENTION : New Generation N'EST PAS dans ce fichier.")
    print("   Relance MAINTENANT :  py -3 animerng.py --ecrire")


if __name__ == "__main__":
    main()
