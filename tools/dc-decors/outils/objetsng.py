# -*- coding: utf-8 -*-
"""LES OBJETS D'UNE BANDE DE NEW GENERATION, lus comme ceux de 2nd Impact -- 16/09/2026.

POURQUOI
--------
`animerng` posait, pour chaque DECOR, tous les enregistrements de `ng_blocs.json` sur sa
PREMIERE bande. Cinq defauts en sortaient, tous corriges en 2I :

  1. les bandes d'un decor etaient melangees : la rue et le temple de Hong Kong sur le
     meme etage, rien sur les autres. La routine choisit par l'AIRE (`cheminng.py`) ;
  2. les variantes `z` etaient toutes posees a la fois, les unes sur les autres ;
  3. les pieces du CHARGEUR B (`0x8C0A21A4`) etaient posees : ce sont des DEBRIS, crees
     quand l'objet parent est frappe (`0x8C0A12F0`, sous-etat 1 de la statue), et leur
     position est relative au parent -- d'ou les x negatifs ;
  4. les enregistrements a deux scripts (repos, action) etaient sautes faute de `script` ;
  5. les objets a VALEURS EN DUR (la menagerie d'Oro, la cage de Yun, les poissons de
     Yang) n'etaient pas lus du tout.

Les objets de NG portent les MEMES numeros que ceux de 2I (table `0x8C1ADA10` contre
`0x8C179FDC`), et leurs spawners sont souvent les memes octet pour octet : le chien d'Oro
choisit sa place selon les combattants, les poissons nagent avec les memes vitesses et
les memes bornes. Ce qui a ete lu et valide en 2I se transpose donc ici.

    python objetsng.py 16        ce que la bande 16 (Oro) pose
"""
import json
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import routineng as RN          # la bascule vers le binaire de NG, avant tout le reste
import cheminng as CN
import sh4ng as NG

SP, IM = RN.SP, RN.IM
ICI = os.path.dirname(os.path.abspath(__file__))

LECTEURS_ELEMENTS = {0x8C09C83C, 0x8C09CA14}
CHARGEUR_A = 0x8C0A1A40
CHARGEUR_DEBRIS = 0x8C0A21A4
# Les appels de service des routines d'etage : ni objets ni blocs.
SERVICE = {0x8C086CC0, 0x8C086854, 0x8C08635A, 0x8C087ED2, 0x8C087F6C, 0x8C095332,
           0x8C110A2A, 0x8C031632, 0x8C087A52, 0x8C087E24, 0x8C087A98, 0x8C0BEEE0,
           0x8C0B2454, 0x8C0ADD24,
           # LU LE 25/09/2026 (Alex) : `0x8C039BF0` ne cree rien. C'est un PREDICAT --
           # il rend 1 quand un combattant est actif et que `u16[0x8C7250E4]` ou
           # `u16[0x8C7250E8]` porte un des bits 0x07F0. La routine d'etage d'Alex s'en
           # sert pour doubler la vitesse de son plan supplementaire (`0x8C0896EE` :
           # `plan[+28] -= plan[+20] << 2` au lieu de `<< 1`).
           0x8C039BF0}

SANS_AMI, AVEC_AMI = 0x10, 0x20


_ID_CHARGEUR = {}


def id_du_chargeur(lecteur):
    """L'id que ce chargeur ecrit dans la fiche, ou None.

    Un bloc d'enregistrements ne porte pas l'id de l'acteur : c'est le CHARGEUR qui
    l'ecrit, en constante, juste apres avoir pris sa place dans le tas --
    `mov #id,r0 ; mov.w r0,@(8,rn)`. C'est le seul crible qui marche pour ces
    objets-la (23/09/2026).
    """
    if not _ID_CHARGEUR:
        import sh4ng as _N
        for a in range(0x8C010000, 0x8C0F0000, 2):
            w = _N.U16(a)
            if (w & 0xFF00) != 0xE000 or ((w >> 8) & 15) != 0:
                continue
            for k in range(1, 10):
                if (_N.U16(a + 2 * k) & 0xFF0F) == 0x8104:
                    _ID_CHARGEUR[a] = w & 0xFF
                    break
    try:
        cible = int(lecteur, 16) if isinstance(lecteur, str) else int(lecteur)
    except (TypeError, ValueError):
        return None
    for a, i in _ID_CHARGEUR.items():
        if cible <= a < cible + 0x120:
            return i
    return None

# LES OBJETS A VALEURS EN DUR, transposes de 2I (meme spawner, meme id, memes scripts).
# `script` est dans la numerotation de la table que l'objet pose en `+0x16C`, rapportee a
# celle du decor par `table`.
EN_DUR = {
    # ORO -- le perroquet (id 55), le chien (id 71), la chatte (72) et ses chatons (73).
    # Pas de repartiteur `z` dans NG : tous sont crees a chaque entree.
    # LE PERROQUET S'ENVOLE -- 28/09/2026. Frederic : « le perroquet peut s'envoler dans la
    # version d'origine, ce qui n'est plus le cas ici ». Sa routine est `0x8C0A6B54` (table
    # des routines d'objet `0x8C1ADA10`, entree 55) et elle se lit en entier :
    #
    #     etat 0  0x8C0A6B96   perche
    #     etat 1  0x8C0A6BEA   le vol, six sous-etats (table 0x8C1B22F0)
    #     etat 2  0x8C0A6E42   il revient : [+36] = 0 et [+38] = 0
    #
    # LE DECLENCHEUR EST LE DRAPEAU DE FIN DE SCRIPT. L'etat 0 pose le script 20, rend
    # l'objet visible, puis avance le script et teste `objet[+468]` -- l'octet de drapeau du
    # pas courant. Il part des qu'il n'est pas nul, et le script 20 le porte a son
    # enregistrement 48 (image 21805, duree 5, drapeau 0x01), apres les trois tours de sa
    # boucle `0x0C`/`0x0D` : 4358 trames de perchoir, soit soixante-douze secondes.
    #
    # LE VOL. Le sous-etat 0 pose le script 21 (six images de quatre trames, les battements
    # d'ailes) et ecrit les quatre champs de mouvement, tous lus :
    #
    #     [+124] = 0x00018000   vitesse x      +1,5    pixel par trame
    #     [+132] = 10240        acceleration x +0,15625
    #     [+128] = 128          vitesse y      +0,00195
    #     [+136] = 512          acceleration y +0,0078
    #
    # (`0x8C0857B0` fait `[+124] += [+132]` puis `[+100] += [+124]`, `0x8C085850` la meme
    # chose sur `[+128]`/`[+136]`/`[+104]` : c'est la meme paire d'integrateurs que pour les
    # petales de Ryu.) Le sous-etat 1 s'arrete quand `[+102]` depasse **912** ; parti de 672,
    # cela fait 240 pixels, soit quarante-huit trames a cette acceleration.
    #
    # CE QUI EST APPROCHE, ET C'EST DIT. Un `trajet` va a vitesse constante par segment : on
    # decoupe donc le vol en SIX segments de huit trames, chacun a la vitesse moyenne de
    # l'intervalle -- 252 pixels au lieu de 240, douze de trop, hors champ de toute facon.
    # La branche tiree au sort du sous-etat 1 et le retour de l'etat 2 ne sont pas rendus :
    # le trajet boucle, et l'oiseau retrouve son perchoir d'un coup, hors de l'ecran.
    #
    # LE SIGNE DE `vy` : positif fait DESCENDRE, comme pour les petales de Ryu (la page
    # compte y vers le bas, le monde vers le haut). L'oiseau monte, donc vy est negatif ici.
    # Si les deux partent du mauvais cote, c'est un seul caractere a changer, aux deux
    # endroits.
    0x8C0A6E66: [dict(x=672, y=114, pal=86, plan=2, script=20, col=0x2058, id=55,
                      comportement=5, suites=[20, 21],
                      trajet=[(4358, 0, 0, 0, 0),       # le perchoir, script 20
                              (8, 544, -9, 1, 0),       # l'envol, script 21
                              (8, 864, -24, -1, 0),
                              (8, 1184, -40, -1, 0),
                              (8, 1504, -56, -1, 0),
                              (8, 1824, -72, -1, 0),
                              (8, 2144, -88, -1, 0)])],
    0x8C0A9F06: [dict(x=608, y=53, pal=74, plan=2, script=28, col=0x2058, id=71,
                      variante=0xF | AVEC_AMI, comportement=1,
                      suites=[[(28, 0), (28, 2), (28, 4)], (30, "une"), (29, "une")]),
                 dict(x=700, y=56, pal=74, plan=2, script=40, col=0x2058, id=71,
                      variante=0xF | SANS_AMI, comportement=2,
                      suites=[40, (41, "une")])],
    0x8C0AA100: [dict(x=411, y=80, pal=75, plan=2, script=13, col=0x2058, id=72),
                 dict(x=493, y=81, pal=75, plan=2, script=17, col=0x2058, id=73)],
    # HONG KONG, LA RUE -- la cage (id 23), ses trois oiseaux (id 21, table + 36, le
    # troisieme retourne), l'oiseau de l'id 22 (table + 42) et le fumeur (id 24).
    0x8C0A0C20: [dict(x=672, y=48, pal=90, plan=2, script=7, col=0x2040, id=23),
                 dict(x=696, y=64, pal=74, plan=2, script=36, col=0x2055, id=21, deroule=True),
                 dict(x=752, y=84, pal=74, plan=2, script=38, col=0x2055, id=21, deroule=True),
                 dict(x=752, y=63, pal=74, plan=2, script=40, col=0x2055, id=21, deroule=True,
                      miroir=True),
                 dict(x=712, y=56, pal=74, plan=2, script=42, col=0x2055, id=22),
                 dict(x=728, y=48, pal=91, plan=2, script=24, col=0x2055, id=24)],
    # HONG KONG, LE TEMPLE -- les deux poissons (id 29), tables + 82 et + 86 : la nage de
    # NG est celle de 2I (memes constantes, memes etats ; `0x8C0A2768`).
    #
    # LA PROFONDEUR EST CELLE DE 2I, PAS CELLE DU CODE DE NG -- 17/09/2026. Le spawner de NG
    # ecrit 87, et la vitre de l'aquarium (script 61) est a 86 : un z plus grand est plus
    # loin, les poissons passaient donc DERRIERE une vitre que notre moteur dessine opaque.
    # Frederic, sur Yang 2 : « poissons manquants ». On les pose a 85, devant la vitre,
    # comme en 2I ; `pal` ne sert ici qu'a la profondeur (les couleurs viennent de `col`).
    0x8C0A2982: [dict(x=240, y=136, pal=85, plan=2, script=82, col=0x50, id=29,
                      comportement=3,
                      suites=[(82, "boucle"), (83, "sans"), (84, "boucle"), (85, "sans")]),
                 dict(x=128, y=148, pal=85, plan=2, script=86, col=0x50, id=29,
                      comportement=4,
                      suites=[86, (87, "sans"), 88, (89, "sans"), (90, "boucle"),
                              (91, "sans"), 92])],
    # NECRO -- LE CONDUCTEUR (id 7, spawner `0x8C09CBF8`) ET SON VOISIN (id 8, cree par lui
    # en `0x8C09CD5C`) -- 18/09/2026. Frederic : « personnages du decor absents ». Les memes
    # qu'en 2I, octet pour octet : position en `+84`/`+86` (463,77 et 432,118), `+556` = 64,
    # `+554` = 89 et 0x2040, plan 2, tables `0x8C0D66B8` et `0x8C0D6678` = la table du decor
    # + 34 et + 18.
    0x8C09CBF8: [dict(x=463, y=77, pal=64, plan=2, script=34, col=89, id=7),
                 dict(x=432, y=118, pal=64, plan=2, script=18, col=0x2040, id=8)],
    # IBUKI 1 ET 2 -- LES PERSONNAGES (18/09/2026). Frederic : « personnages du decor
    # manquants ». L'id 82 (`0x8C0ABF72`, bandes 11 et 12) cree l'id 77 (`0x8C0AB0EE`), qui
    # cree les ids 78, 79 et 80. Chacun porte sa table en dur -- la table du decor + 194, 200,
    # 205 et 211 -- et sa routine pose le script 0 avec sa profondeur au premier etat :
    #
    #   id 77  320,52   prof 70  le maitre            aire 0 : 194 ; sinon 198 (la lance)
    #   id 78  512,51   prof 71  le colosse           aire 0 : 200 ; sinon 204 (le baton)
    #   id 79  480,51   prof 70  le garcon            aire 0 seulement (`0x8C0AB874`)
    #   id 80  496,322  prof 70  le ninja perche      aire 0 seulement (`0x8C0ABB74`)
    #
    # Les routines des ids 77 et 78 sautent ailleurs quand l'aire n'est pas 0 (`0x8C0AB090`,
    # `0x8C0AB400`) : le script 4 de leur table, une image. `aires` filtre par l'aire de la
    # bande. Ibuki 3 n'appelle pas l'id 82 : ses objets sont des nuages (id 83, plan 3) et
    # des petits sprites tires au hasard (id 20 -> id 67), qui se deplacent.
    0x8C0ABF72: [dict(x=320, y=52, pal=70, plan=2, script=194, col=0x2051, id=77, aires=[0]),
                 dict(x=512, y=51, pal=71, plan=2, script=200, col=0x2051, id=78, aires=[0]),
                 dict(x=480, y=51, pal=70, plan=2, script=205, col=0x51, id=79, aires=[0]),
                 dict(x=496, y=322, pal=70, plan=2, script=211, col=0x2051, id=80, aires=[0]),
                 dict(x=320, y=52, pal=70, plan=2, script=198, col=0x2051, id=77, aires=[1, 2]),
                 dict(x=512, y=51, pal=71, plan=2, script=204, col=0x2051, id=78, aires=[1, 2])],
    # ELENA 2 -- L'OBJET POSE SUR UN COMBATTANT (id 85, `0x8C0AC4AA`) -- 23/09/2026.
    # Le premier objet du port dont la position ne vient PAS des donnees : sa routine
    # `0x8C0AB52C` le place a `plw[cote].xyz[0].pos - 64`, soixante-quatre unites a
    # gauche d'un combattant (etat `0x8C0AB6A8`). Le spawner lui donne sa naissance en
    # 604,94, sa palette 79, son plan 2, sa table `0x8C0D9E88` ; c'est sa ROUTINE qui
    # pose le script 2 de cette table -- une seule image, celle qui se deplace.
    # `comportement=6` = SUR_COMBATTANT dans `decor_objets.c`.
    0x8C0AC4AA: [dict(x=604, y=94, pal=79, plan=2, script=2, col=0x60, id=85,
                      table_objet=0x8C0D9E88, comportement=6)],

    # DUDLEY 2 -- LE PUNK AU SKATE (id 68, `0x8C0A961C`) -- 18/09/2026. Frederic : « il manque
    # 2 punks animes supplementaires ». x 160 (+512 : le decor 4 compte du milieu, 672 comme
    # en 2I), y 47, profondeur 75, `+554` = 0x2058, script 17 (`+456`, dix-huit images) ; sa
    # routine passe au 18 quand un combattant approche. L'autre punk est l'id 66 (bloc).
    0x8C0A961C: [dict(x=160, y=47, pal=75, plan=2, script=17, col=0x2058, id=68)],

    # KEN (NG, le bain a ciel ouvert) -- SES DEUX OBJETS DU CENTRE -- 28/09/2026
    # --------------------------------------------------------------------------
    # Frederic : « variant bain a ciel ouvert : il manque les inscriptions sur les rochers ».
    # Sa routine d'etage fait deux appels que la chaine listait en NON LU, et les deux
    # engendreurs se lisent entierement :
    #
    #   `0x8C0B13C0` (id 115)   `[+102]` = 496, `[+86]` = 80 et `[+104]` = 0x00500000,
    #                           `[+88]` et `[+556]` = 10, `[+456]` = 6, `[+364]` = 0x8C0DE6D8
    #                           (la table de Ken, sans decalage), `[+558]` = 1, `[+554]` = 67
    #   `0x8C0B168C` (id 117)   x 512, `[+86]` = 104 et `[+104]` = 0x00680000, memes
    #                           profondeur, palette, plan et col, `[+456]` = 7
    #
    # ET LEURS SCRIPTS NE SONT JOUES PAR PERSONNE : le depouillement de la table de Ken
    # contre ses vingt-et-un objets laisse les scripts 6 et 7 de cote, et ils vivent sur un
    # bloc de sprites a eux (25641..25760) -- le reste de ses objets est dans 22832..23695 et
    # 4798..4830. Meme signature que les huit scripts du sakura de Ryu.
    #
    #     script 6   48 images  12240 trames   255 trames par image : tres lent
    #     script 7   12 images   3060 trames
    #
    # ILS NAISSENT INVISIBLES. Les deux ecrivent `mov.b r0,@(1,r4)` avec r0 nul --
    # `disp_flag` a zero, comme les objets reactifs lus le 23/09 : le Dreamcast ne les montre
    # que lorsqu'une condition tient. Le port garde le defaut deja choisi pour cette famille
    # (visibles ; `SF3_DECOR_REACTIF=1` donne l'autre lecture), et c'est Frederic qui tranche
    # sur l'image -- y compris sur la question de savoir si ce sont bien ses inscriptions.
    #
    # Leur table de 54 octets (`0x8C553E40`) est de la RAM, construite par la routine
    # d'etage elle-meme ; elle ne porte AUCUN des champs ci-dessus, qui sont tous en
    # immediats dans les engendreurs. On n'en a donc pas besoin.
    # ET ILS SONT RETIRES -- 29/09/2026. Frederic : « KEN NG, des planches qui volent ».
    #
    # C'etaient eux, et la lecture le disait : les deux ecrivent `disp_flag` a ZERO, ils
    # naissent INVISIBLES. J'ai quand meme choisi le defaut « visibles » de la famille
    # reactive, et on voit des planches de bain flotter au milieu de l'ecran. Ce ne sont pas
    # non plus les inscriptions sur les rochers.
    #
    # Le releve reste ici pour la suite -- il est juste, c'est la decision de les montrer
    # qui etait fausse :
    #
    #     0x8C0B13C0 (id 115)   x 496, y 80,  script 6, plan 1, profondeur et palette 10,
    #                           col 67, table 0x8C0DE6D8 (celle de Ken, sans decalage)
    #     0x8C0B168C (id 117)   x 512, y 104, script 7, tout le reste identique
    #
    # Pour les remettre il faudra d'abord lire CE QUI LES ALLUME : la condition est dans
    # leurs routines, `0x8C0B102C` et `0x8C0B1618` (table `0x8C1ADA10`).
    # 0x8C0B13C0: [dict(x=496, y=80, pal=10, plan=1, script=6, col=67, id=115)],
    # 0x8C0B168C: [dict(x=512, y=104, pal=10, plan=1, script=7, col=67, id=117)],

    # RYU (NG) -- LES PETALES DE SAKURA (id 34, `0x8C0A2C94`) -- 28/09/2026
    # ---------------------------------------------------------------------
    # Frederic : « RYU et Ken variant rue : il manque les feuilles de sakura qui tombent des
    # arbres ». Toute la chaine est lue, de la routine d'etage jusqu'aux vitesses de chute.
    #
    # CE QUI A MIS SUR LA PISTE. Le depouillement de la table de scripts de Ryu
    # (`0x8C0D1338`) contre les six objets que la chaine emettait laissait HUIT scripts que
    # personne ne joue -- les 2 a 9 -- quatre images chacun, sur un bloc de trente-deux
    # sprites contigus (30488..30519) qu'aucun autre script du decor n'emploie.
    #
    # LA CHAINE, LUE BOUT A BOUT :
    #
    #   `0x8C089970` -> `0x8C03121C`   monte les 32 sprites du sakura dans le pool de tuiles
    #                                  (`mov.w 0x8C031332,r9` = 30488, boucle de 0 a 32), et
    #                                  depose leurs emplacements dans `0x8C549870` et
    #                                  `0x8C5498D0`. Son jumeau `0x8C03135C` les redescend.
    #   `0x8C08999A` -> `0x8C0A2C94`   L'EMETTEUR (id 34). A chaque reveil il tire au sort
    #                                  une rangee de sept indices (tables `0x8C1B1754` pour
    #                                  les petales proches, valeurs 0..10, et `0x8C1B17C4`
    #                                  pour les lointaines, 11..21), en pose 1 a 7, puis
    #                                  attend un delai pris dans `0x8C1B1834` (10, 24, 28,
    #                                  34, 40, 48, 60, 78, 88, 94, 108, 114).
    #   `0x8C0A2FBC`                   LE POSEUR d'un petale. Il alloue un objet de genre 3,
    #                                  id 35, plan 2, `+554` = 0x204E, et deverse le
    #                                  vingt-deuxieme enregistrement de `0x8C1B1874`
    #                                  (douze octets, six mots) :
    #
    #       mot 0 -> `[+84]` et `[+102]`   x        mot 3 -> `[+456]`  le script, 0 a 3
    #       mot 1 -> `[+86]` et `[+106]`   y        mot 4 -> `[+156]`  un delai
    #       mot 2 -> `[+556]` et `[+88]`   la profondeur               mot 5 -> `[+160]`
    #
    #                                  puis `[+164]` = 0 pour les indices < 11, 1 au-dela,
    #                                  et surtout `[+364]` -- LA TABLE DE SCRIPTS DE L'OBJET
    #                                  -- qui prend `0x8C0D1340` pres et `0x8C0D1350` loin.
    #
    # ET C'EST LA QUE LES HUIT SCRIPTS SE REFERMENT : la table de Ryu est `0x8C0D1338`, donc
    # `0x8C0D1340` est son entree **2** et `0x8C0D1350` son entree **6**. Un script `n` de
    # 0 a 3 est donc le script **n + 2** pour un petale proche et **n + 6** pour un lointain :
    # les 2 a 5 et les 6 a 9, exactement les huit que personne ne jouait.
    #
    # LA CHUTE, LUE AUSSI. `0x8C0A32FC` tire au sort une paire dans `0x8C1B197C`, indexee par
    # `[+164]`, et la pose en `[+128]` (vitesse y) et `[+136]` (acceleration y) ; l'etat 1 du
    # petale (`0x8C0A318A`) integre par `0x8C085850` (`[+128] += [+136]` puis `[+104] +=
    # [+128]`) et s'arrete quand `[+106]` atteint `[+160]`, le mot 5 de l'enregistrement.
    #
    #     petales proches (`[+164]` = 0)   vitesse -0,078 a -0,305 px/trame
    #                                      acceleration -0,004 a -0,018
    #     petales lointaines (= 1)         vitesse -0,016 a -0,180
    #                                      acceleration -0,000 a -0,014
    #
    # y DECROIT quand le petale descend -- `sol` monte, c'est la regle de l'axe vertical.
    #
    # CE QUI EST APPROCHE, ET C'EST DIT. On pose les vingt-deux points, chacun avec son
    # script, sa profondeur et sa chute. Trois choses restent au hasard sur la console et
    # sont figees ici : le couple de vitesse (on prend le NEUVIEME des trente-deux, celui du
    # milieu : -0,227 / -0,009 pres, -0,102 / -0,005 loin), le nombre de petales servis a la
    # fois (1 a 7) et le delai entre deux lachers. La duree de chaque chute se calcule alors
    # de la hauteur lue et de ce couple, et `trajet` la joue a vitesse constante -- une chute
    # uniforme au lieu d'une chute qui s'accelere, sur 168 a 346 pixels.
    #
    # LE BUDGET TRANCHERA. Vingt-deux objets de quatre images sur un etage qui en porte six :
    # `animerng.budget` garde ce qui tient et DIT ce qu'il laisse, comme partout ailleurs.
    0x8C0A2C94: [
        dict(x=x, y=y, pal=z, plan=2, script=sc, col=0x204E, id=35, dx=512,
             trajet=[(t, 0, vy, -1, 0)])
        for x, y, z, sc, vy, t in (
            #  x    y   prof script  vy   duree      la chute, en pixels
            (-288, 288,  22,  5,  302, 212),   # 250
            (-208, 304,  73,  4,  296, 207),   # 239
            (-184, 264,  22,  2,  291, 202),   # 230
            (-120, 264,  22,  3,  290, 201),   # 228
            (-128, 408,  73,  5,  350, 253),   # 346
            (   0, 320,  22,  2,  319, 227),   # 283
            (  32, 312,  22,  4,  315, 224),   # 276
            (-256, 272,  22,  5,  294, 204),   # 234
            (-232, 274,  73,  4,  279, 192),   # 209
            (-169, 312,  22,  2,  316, 225),   # 278
            ( -92, 296,  22,  3,  308, 216),   # 260
            (-304, 384,  90,  6,  240, 333),   # 312
            (-264, 368,  90,  7,  234, 324),   # 296
            (-160, 240,  90,  8,  179, 240),   # 168
            ( -80, 304,  90,  9,  208, 285),   # 232
            (   0, 336,  90,  7,  222, 305),   # 264
            (  80, 344,  90,  6,  225, 310),   # 272
            ( -48, 400,  90,  8,  246, 342),   # 328
            (-288, 361,  90,  6,  231, 320),   # 289
            (-244, 377,  90,  7,  237, 329),   # 305
            ( -98, 276,  90,  9,  196, 266),   # 204
            (  36, 323,  90,  7,  216, 297),   # 251
        )],
    # ALEX (NG) -- LES DEUX PASSANTS DU FOND (id 64, `0x8C0A88D6`) -- 25/09/2026.
    # Frederic : « les passants en arriere plan sont manquants ». La chaine les VOYAIT et ne
    # les emettait pas : `objetsng` les listait en NON LU, deux appels de la routine d'etage
    # (`0x8C089500` r4=3 et `0x8C089506` r4=4), faute d'entree ici.
    #
    # LE SPAWNER `0x8C0A88D6(k)` ne pose presque rien : `[+8] = 64`, `[+552] = 0x4200`,
    # `[+4] = k`, `[+416] = 0x8C0DE32C`, et `[+38] = u16[0x8C1B255C + 44k]`. TOUT le reste
    # est dans un enregistrement de QUARANTE-QUATRE octets, `0x8C1B255C + 44k`, que
    # l'initialiseur `0x8C0A87A4` deverse champ par champ, dans cet ordre :
    #
    #     w0  -> [+32]   w1  -> [+38]   w2  -> [+558] plan   w3  -> [+554] col
    #     w4  -> [+102] x   w5  -> [+106] y   w6  -> [+88] palette ET [+556] profondeur
    #     w7  -> [+456] script   w8  -> [+68]   w9  -> [+118]   w10 -> [+52]
    #     w11 -> [+54] (saute quand on ré-initialise)   w12 -> [+56]   w13 -> [+10] miroir
    #     w14 -> [+126]   w15 -> [+124]   w16 -> [+134]   w17 -> [+132]   w18 -> [+130]
    #     w19 -> [+128]   w20 -> [+138]   w21 -> [+136]
    #
    # `[+124]` et `[+126]` sont les deux moities du 16.16 de la VITESSE : w14 en poids fort.
    #
    #     k = 3   x 320, y 87, palette et profondeur 85, script 34, plan 2, col 0x205C,
    #             miroir 0, [+52] = 400, [+54] = 32, vitesse +0x00010000 = +1 pixel/trame
    #     k = 4   x 912, y 87, palette et profondeur 86, script 34, plan 2, col 0x205C,
    #             miroir 1, [+52] = -192, [+54] = 32, vitesse 0xFFFF0000 = -1 pixel/trame
    #
    # LE CYCLE, lu dans `0x8C0A860A` (le comportement que `[+38]` = 4 ou 5 designe dans la
    # table de sauts `0x8C4DE964`) :
    #
    #     [+40] = 0   initialise, puis [+40] = 2
    #     [+40] = 2   `0x8C0A888A` : [+54] -= 1 ; sous zero -> [+40] = 3
    #     [+40] = 3   avance le script ([+68] != 0), deplace (`0x8C0857B0`), et teste
    #                 l'arrivee (`0x8C0A88A4`) : [+38] PAIR -> arrive quand x > [+52] ;
    #                 [+38] IMPAIR -> arrive quand x < [+52]. C'est le sens de la marche.
    #     a l'arrivee : [+40] = 1 -> re-initialise SANS toucher [+54], qui vient d'etre tire
    #
    # DONC : k=3 marche a DROITE, de 320 a 401 -- quatre-vingt-une trames ; k=4 marche a
    # GAUCHE, de 912 a -193 -- mille cent cinq trames. Puis chacun revient a sa naissance.
    #
    # L'ATTENTE ENTRE DEUX PASSAGES EST TIREE. `0x8C0191C0` rend
    # `u16[0x8C153C04 + 2 * ((compteur + 1) & 63)]`, un indice 0..15, et il sert dans
    # `u16[0x8C1B251C + 2 * indice]` -- seize durees lues :
    #
    #     1428 2120 1472 512 1860 392 1728 1280 576 640 2048 1840 960 1024 1216 1536
    #
    # LE TRAJET DU PORT N'A PAS DE TIRAGE, et il ne sait pas non plus ramener l'objet en
    # cours de liste : il ne boucle qu'a son premier segment.
    #
    # TROIS SEGMENTS, ET UNE MARCHE DE 1024 -- 27/09/2026. Deux verdicts a la suite :
    #
    #   26/09 « le passant blanc n'est pas corrige » : le PREMIER segment est aussi celui
    #         sur lequel la liste boucle. J'y avais mis l'attente ENTRE DEUX PASSAGES, 1280
    #         trames, donc VINGT ET UNE SECONDES avant son premier pas ; un round finit
    #         avant, et il ne marchait jamais.
    #   27/09 « il y en a plusieurs, qui viennent de droite et de gauche, dont UN SEUL
    #         disparait en pleine animation. Respecte le nombre et la frequence
    #         d'apparition de la version dreamcast. » Mettre 32 en tete les faisait
    #         traverser toutes les 15,5 secondes, deux fois trop souvent.
    #
    # LA DISPARITION EST UNE CONSEQUENCE DU MASQUE. La position de dessin est repliee sur la
    # bande (`*x = (anim->x + (px >> 16)) & 0x3FF`, decor_objets.c) : elle fait 1024 et ce
    # qui sort d'un bord revient par l'autre. Avec 895 trames, k=3 finissait a 1215, soit
    # **191 a l'ecran** -- encore en vue -- et le bouclage de la liste le RAMENAIT d'un coup
    # a 320 : un saut, vu comme une disparition en pleine animation. k=4 finissait a -193,
    # soit 831, et sautait de meme.
    #
    # D'OU LA MARCHE DE **1024 TRAMES** : une largeur de bande entiere a 1 px/trame ramene
    # l'objet exactement sur sa naissance (320 + 1024 = 1344, et 1344 & 0x3FF = 320 ;
    # 912 - 1024 = -112, et -112 & 0x3FF = 912). Le bouclage ne deplace plus rien, donc plus
    # aucun saut, et le passant traverse toute la bande une fois par tour.
    #
    # ET L'ATTENTE REVIENT EN QUEUE, ou elle ne se voit pas : l'objet y est deja sur sa
    # naissance, et la console fait exactement cela -- son etat 2 ne decremente que `[+54]`,
    # le passant TIENT son image, debout a sa place. Le premier segment garde la premiere
    # attente de la console, 32 trames, lue dans `[+54]`.
    #
    # LA FREQUENCE EST CELLE DE LA CONSOLE, et elle se calcule : la-bas un passage coute
    # l'attente tiree plus la marche, soit en moyenne 1289,5 + 81 = 1370 trames, donc UNE
    # APPARITION TOUTES LES 22,8 SECONDES par passant. Ici 32 + 1024 + 392 = 1448 trames
    # (24,1 s) pour k=3 et 32 + 1024 + 512 = 1568 (26,1 s) pour k=4.
    #
    # LES DEUX ATTENTES DE QUEUE SONT PRISES DANS LES SEIZE, et elles sont DIFFERENTES
    # expres : avec la meme, les deux passants marcheraient eternellement ensemble -- ce que
    # Frederic a vu -- alors que la console les tire separement. Deux longueurs de cycle qui
    # ne se divisent pas les font deriver l'une par rapport a l'autre. 392 et 512 sont deux
    # des seize durees lues ci-dessus ; **le choix parmi les seize est assume**, comme
    # l'etait celui de 1280.
    #
    # LE NOMBRE, LUI, EST CELUI DE LA CONSOLE : deux passants, k=3 et k=4, pas un de plus.
    # ET L'ATTENTE FIGE LE SCRIPT -- corrige le 25/09/2026. Frederic : « *une fois sur 2 le
    # pieton disparait trop tot* ».
    #
    # L'etat 2 (`0x8C0A888A`) ne fait QUE decrementer `[+54]` : il n'avance pas le script.
    # Le passant tient donc son image pendant toute l'attente, et ne s'anime qu'en etat 3.
    # Mes deux fiches n'avaient pas de suites : ils marchaient SUR PLACE pendant 1280
    # trames, puis sautaient de 81 pixels en arriere. Deux suites le reglent -- la premiere
    # est l'image du pas 0 du script 34, tenue ; la seconde est le script entier.
    #
    # CE QUI RESTE LA VALEUR DE LA CONSOLE, et qui n'est PAS touche : k=3 ne marche que
    # 81 pixels. `0x8C0A88A4` desassemble : `[+38]` PAIR -> arrive quand `s16[+102] > [+52]`,
    # IMPAIR -> quand `s16[+102] < [+52]`. k=3 a `[+38]` = 4 et `[+52]` = 400, part de 320 a
    # +1 px/trame ; k=4 a `[+38]` = 5 et `[+52]` = -192, part de 912 a -1 px/trame. Et le
    # script 34 ne porte AUCUNE commande `0x29` : rien d'autre ne les deplace. C'est donc
    # bien la console qui fait marcher l'un 81 pixels et l'autre 1105.
    # ET IL TRAVERSE -- 26/09/2026, ECART ASSUME ET DEMANDE. Frederic : « *le passant du
    # decor (celui habille en blanc) de Alex NG n'est pas corrige* ». La console le fait
    # marcher 81 pixels, c'est mesure et ca reste ecrit plus haut ; ce n'est donc PAS une
    # correction de lecture, c'est un ecart, et il est demande.
    #
    # LA LONGUEUR N'EST PAS INVENTEE, elle est prise SUR SON JUMEAU. k=4 part de 912 et
    # s'arrete a -192, soit 192 pixels AU-DELA du bord gauche de la bande (0..1023). Le
    # miroir de cette regle donne a k=3 une arrivee a 1023 + 192 = 1215, donc
    # 1215 - 320 = 895 trames a +1 px/trame. Les deux passants sortent alors de la bande du
    # meme cote qu'ils la quittent sur console, et par la meme marge.
    (0x8C0A88D6, 3): [dict(x=320, y=87, pal=85, plan=2, script=34, col=0x205C, id=64,
                           comportement=5, suites=[[(34, 0)], 34],
                           trajet=[(32, 0, 0, 0), (1024, 256, 0, 1), (392, 0, 0, 0)])],
    (0x8C0A88D6, 4): [dict(x=912, y=87, pal=86, plan=2, script=34, col=0x205C, id=64,
                           miroir=True, comportement=5, suites=[[(34, 0)], 34],
                           trajet=[(32, 0, 0, 0), (1024, -256, 0, 1), (512, 0, 0, 0)])],
    # ALEX -- L'ARRIERE DE LA VOITURE (id 69, `0x8C0A9806`). Frederic : « arriere de la voiture
    # absente dans le tunnel de gauche ». x 192, y 48, profondeur 80, `+554` = 0x2040, table du
    # decor ; sa routine pose le script 16 a sa naissance (`0x8C0A9706`), puis 19 quand la
    # voiture est frappee.
    # ET ELLE SE BRISE -- 23/09/2026. Frederic : « pour Alex, je ne sais pas quel objet du
    # decor est destructible ». C'est celui-ci, et la note ci-dessus le disait deja sans que
    # j'y prenne garde : « puis 19 quand la voiture est frappee ».
    #
    # Son etat appelle le test de contact `0x8C085A1E` (le jumeau NG de `0x8C0D7D74`) et,
    # tant que `u16[0x8C55262C]` depasse son `+38`, avance d'un cran (`0x8C0A97B6`). Les
    # crans sont des scripts consecutifs, et les trois premiers portent LA MEME image :
    #
    #     scripts 16, 17, 18 : 22077   la voiture intacte -- elle encaisse
    #     script  19         : 22078   l'arriere enfonce
    #
    # Le spawner ecrit `+4 = 6` (`0x8C0A987C`), d'ou la boite du type 6 -- et les tables de
    # boites de New Generation (`0x8C1890B0`, `0x8C189108`) sont IDENTIQUES a celles de 2I.
    0x8C0A9806: [dict(x=192, y=48, pal=80, plan=2, script=16, col=0x2040, id=69,
                      comportement=9, suites=[16, 17, 18, (19, "une")],
                      boite=(-53, 39, 20, 25))],
    # SEAN, VARIANTE 0 -- LES DEUX COSTAUDS (id 61 `0x8C0A7F48`, id 62 `0x8C0A817A`). Tout en
    # dur : 392,58 et 448,58 (bloc `0x8C1B2508`), profondeur 77, `+554` = 88, tables du decor
    # + 26 et + 25, script 0 -- donc les scripts 26 (85 images) et 25 (31 images).
    0x8C0A7F48: [dict(x=392, y=58, pal=77, plan=2, script=26, col=88, id=61),
                 dict(x=448, y=58, pal=77, plan=2, script=25, col=88, id=62)],
    # SEAN -- LES IMMEUBLES DE NEW YORK (id 44, `0x8C0A4C38`). Frederic : « arriere plan
    # incomplet », « reflet dans flaque d'eau manquant ». Quatorze enregistrements de 18 octets
    # en `0x8C1B1DA4` {+32, plan, +554, x, y, profondeur, script, +68, +118}, et une table a
    # eux, `0x8C0D1080`, dont les images sont dans F_ETC35. Le reflet est le script 1 (528,8,
    # profondeur 95 : juste derriere la rue, vu par le trou de la flaque). Les plans 3 et 5
    # n'ont pas de couche : leur coefficient est nul (plan 3) ou absent (plan 5) ; ils suivent
    # le plan lointain (`animerng.famille_du_plan`).
    0x8C0A4C38: "immeubles",
    # ORO -- les chauves-souris (id 74), bloc de six octets, scripts poses par type.
    0x8C0AA7B0: "chauves-souris",
    # ELENA 1 = LA VARIANTE DU PONT DE 2I -- 17/09/2026. Frederic : « ELENA 1 affichage
    # uniquement de l'arriere-plan ». La bande 14 n'a qu'une couche, le ciel lent ; tout le
    # premier plan est fait d'objets, et deux manquaient.
    #
    # LE PONT (id 123, routine `0x8C0B262C`), type 0 (r4 = 0, la bande 14) : script 0, plan 2,
    # profondeur 76. L'etat 0 le pose en x 512, y 384 ; l'etat 1 le fait descendre jusqu'a
    # y < 40, puis leve `u16[0x8C553E0C]`. On le pose ou il s'arrete, x 512, y 40 -- la valeur
    # que 2I avait calee sur une capture. Le type 1 (r4 = 1, Elena 2) ne sert qu'a la chute :
    # le pont de la bande 15 est dans sa page (liste « planches » de `descripteursng`).
    (0x8C0B27BA, 0): [dict(x=512, y=40, pal=76, plan=2, script=0, col=0x2040, id=123)],
    (0x8C0B27BA, 1): [],
    # LES HERBES ET LES CORDES A CRANE (id 122, spawner `0x8C0B253C`) : quatre enregistrements
    # de huit octets en `0x8C1B33B4`, {x, y, profondeur, script} -- ceux de 2I, scripts + 1.
    # La routine `0x8C0B248C` attend `u16[0x8C553E0C]` (le pont arrive), joue le script UNE
    # fois et s'arrete sur sa DERNIERE image jusqu'a la fin de la manche : c'est celle qu'on pose.
    #
    # ELLES RESTENT SUR LEUR PREMIERE IMAGE -- 18/09/2026. Frederic : « les cordes du pont sont
    # manquantes ». On posait la DERNIERE image de leur script : la corde a terre, molle, apres
    # la chute du pont. L'etat 1 de `0x8C0B248C` n'avance pas le script tant que le pont tient,
    # et c'est ce que 2I pose aussi (`animer2i`, `fige`) : la corde tendue, image 0.
    0x8C0B253C: [dict(x=784, y=32, pal=20, plan=2, script=9, col=0x2040, id=122, fige=True),
                 dict(x=720, y=64, pal=77, plan=2, script=10, col=0x2040, id=122, fige=True),
                 dict(x=240, y=32, pal=20, plan=2, script=11, col=0x2040, id=122, fige=True),
                 dict(x=304, y=64, pal=77, plan=2, script=12, col=0x2040, id=122, fige=True)],
    # ELENA 1 -- L'OISEAU POSE (id 53, `0x8C0A6864`). Frederic : « oiseaux volant manquants ».
    # Celui-la se tient en 656,48, profondeur 67, `+554` = 87, table du decor + 22 : sa routine
    # (`0x8C0A63F0`) pose le script 0 -- donc le 22 -- et attend 148 trames avant de s'envoler,
    # ce que notre moteur ne sait pas faire. On le pose a son perchoir. L'id 56, lui, entre par
    # la gauche (x -256) : hors champ tant qu'il ne vole pas, il reste de cote.
    # ET SA PROFONDEUR CHANGE EN COURS DE VOL -- 25/09/2026. Frederic : « *l oiseau en bas a
    # droite a une animation qui tourne en boucle, et sur certaines frames il doit etre
    # derriere le ponton* ». C est ecrit dans sa routine, `0x8C0A63F0`, une machine a DIX
    # etats sur `[+36]` :
    #
    #   etat 0  1 trame  : rend l objet visible, pose le script 0 (= le 22), `[+148]` = 120
    #   etat 1  120 tr.  : decompte `[+148]`. Il n avance PAS le script -- l oiseau reste
    #                      donc fige sur son image 0 pendant tout ce temps.
    #   etat 2           : avance le script chaque trame jusqu a ce que le DRAPEAU du pas
    #                      courant (`[+468]`) vaille 2, puis ecrit
    #                          0x8C0A64D4   [+556] = 79   ET   [+88] = 79
    #                      79 est DERRIERE le ponton, qui est a 78. C est exactement ce que
    #                      Frederic decrit.
    #   etat 3           : avance tant que le drapeau est 0 ; au premier drapeau non nul il
    #                      met `[+1]` a 0 -- l oiseau DISPARAIT -- et passe a l etat 4.
    #   etats 4 a 9      : le vol. Il se positionne sur `u16[0x8C552758 + 10]` et `+12`,
    #                      pose `[+124]`/`[+128]` = 512 et `[+132]`/`[+136]` = +/-320 --
    #                      une vitesse ET une acceleration -- et l etat 8 ecrit
    #                          0x8C0A66DA   [+556] = 10   ET   [+88] = 10
    #                      devant tout. **Ce vol n est PAS reproduit** : un trajet a vitesse
    #                      constante ne sait pas rendre une acceleration, et la position de
    #                      depart est lue a l execution. C est dit, pas comble.
    #
    # LE DECOUPAGE DU SCRIPT 22 (`0x8C0D9C00`, table d Elena `0x8C0D9618`), 38 pas :
    #
    #     pas  0..11  drapeau 0, 6 trames  images 20504..20515   le perchoir
    #     pas 12      drapeau 1, 6 trames
    #     pas 13      drapeau 0x2B, duree 0 : une COMMANDE, zero trame
    #     pas 14..15  drapeau 0, 6 et 8 trames
    #     pas 16      DRAPEAU 2, 1 trame   <- l etat 2 s arrete ici, cumul 92
    #     pas 17..35  drapeau 0, 9 trames  images 20518..20536   l envol
    #     pas 36      drapeau 1, 2 trames  <- l etat 3 s arrete ici, cumul 264
    #
    # D ou les trois segments, et leurs profondeurs :
    #
    #     121 trames  z 67  l image du pas 0, tenue   (1 de l etat 0 + 120 de l etat 1)
    #      92 trames  z 67  les pas 0 a 15
    #     172 trames  z 79  les pas 16 a 35           <- DERRIERE LE PONTON
    #
    # 92 = 12*6 + 6 + 6 + 8 ; 172 = 1 + 19*9. Les deux se recomptent sur le tableau.
    #
    # IL NE REBOUCLE PAS, IL S EFFACE -- 25/09/2026. Frederic : « *l oiseau du decor d
    # elena NG a toujours une animation qui tourne en boucle* ». Elle tournait parce que le
    # trajet, lui, boucle. La routine, non :
    #
    #     etat 3, 0x8C0A6526   objet[+1] = 0        disp_flag : il DISPARAIT
    #
    # et l etat 4 attend QUATRE conditions globales avant le vol (`0x8C085B08` :
    # `u8[0x8C545295]`, `u16[0x8C5452E6] == 1`, `s16[0x8C5493AC] >= 2`, `u8[0x8C5493B4]`).
    # Le vol fini, l etat 9 passe a l etat 10, qui DETRUIT l objet (`0x8C032578` puis
    # `0x8C09B12E`). Le perchoir ne revient jamais. `fin=True` eteint donc l objet apres
    # ses trois segments : 385 trames, puis plus rien -- ce que fait la console.
    0x8C0A6864: [dict(x=656, y=48, pal=67, plan=2, script=22, col=87, id=53,
                      comportement=5, fin=True,
                      suites=[[(22, 0)], (22, 0, 16), (22, 16, 36)],
                      trajet=[(121, 0, 0, 0, 67), (92, 0, 0, 1, 67), (172, 0, 0, 2, 79)])],
    # id 45 (spawner `0x8C0A4DD8`, routine `0x8C0A4D34`) : script 8, plan 1 (le ciel lent),
    # profondeur 100 -- derriere le ciel, vu a travers lui. La routine glisse de 0,5 pixel par
    # trame et, toutes les 33 trames, revient en x -4 et avance le script d'une image.
    # SON x SE COMPTE DU MILIEU DE LA BANDE (+512), comme les objets du plan 2 de Ryu : a -4
    # l'eau sortait sur les bords de la page ; a +512 elle bouche exactement le trou de la
    # riviere, peint transparent dans la banque (x 420..545, lignes 915..945).
    #
    # ELLE COULE -- 18/09/2026. Frederic : « animation du fleuve a revoir ». L'etat 1 de la
    # routine retire 0x8000 (un demi-pixel) a `+100` a chaque trame et, la 33e, remet `+100`
    # a -4 et avance le script d'une image (`0x8C033464`). L'eau glisse donc de seize pixels
    # vers la gauche, puis revient : c'est un TRAJET d'un seul segment.
    0x8C0A4DD8: [dict(x=-4, y=80, pal=100, plan=1, script=8, col=0x2040, id=45, duree=33,
                      dx=512, comportement=5, trajet=[(33, -128, 0, -1)])],
    # DUDLEY 1 -- LA CALECHE DU TUNNEL DE DROITE (id 65, `0x8C0A8BCC`, routine `0x8C0A8970`).
    # Frederic : « animation de la caleche qui passe dans le tunnel de droite est manquante ».
    # Elle nait en 416,64 (+512 : le decor 4 compte du milieu), profondeur 79, `+554` = 0x2059,
    # script 10 -- huit images de huit trames, dont les drapeaux 1 et 2 marquent les sabots.
    # Sa routine attend 600 trames, part a -1,125 pixel pendant 196 trames (`+124` =
    # 0xFFFEE000), puis a -1 pixel (`0xFFFF0000`) jusqu'a passer sous x 48, et tout recommence.
    # ET ELLE RETRECIT -- porte le 23/09/2026, apres que Frederic a rappele que je le lui
    # avais signale moi-meme le 22. La loi, relue au mot pres :
    #
    #     8C0A89CA  mov #55,r4                 L'ECHELLE DE DEPART
    #     8C0A89F8  objet[+570] = 55           les deux champs partent ensemble
    #     8C0A89FE  objet[+568] = 55
    #     8C0A8AFC  objet[+52] += 1            le compteur, DANS L'ETAT 2 SEULEMENT
    #     8C0A8B0A  and #7,r0                  ... module 8
    #     8C0A8B14  cmp/eq #7,r0               une fois toutes les HUIT trames
    #     8C0A8B22  objet[+570] -= 1           ... et on s'arrete a zero
    #     8C0A8B2A  objet[+568] -= 1
    #
    # (Le 22/09 j'avais ecrit « toutes les sept trames » : le compteur va de 0 a 7, il y a
    # donc HUIT trames par cran.)
    #
    # Le code de dessin du Dreamcast lit ces champs avec 63 pour neutre (`0x8C032F28`,
    # `add #-63,r2`), et `mlt_obj_matrix` du port fait `njScale((size + 1) / 64)` : MEME
    # CHAMP, MEME NEUTRE. La caleche nait donc a 56/64 -- 87,5 % -- et descend a 38/64
    # (59 %) en 148 trames de roulage, avant de repasser sous x 48 et de tout recommencer.
    #
    # `echelle_seg = 2` : elle ne retrecit que sur le dernier segment, celui ou elle roule.
    # Sous le tunnel et au demarrage, elle garde sa taille.
    # ELENA 1 -- LES OISEAUX QUI VOLENT AU LOIN (id 56, `0x8C0A707A`, routine `0x8C0A5A14`).
    # Frederic : « NG Elena 1, les oiseaux volant au loin (quelques pixels blancs) sont
    # manquants ». Le spawner etait VU par la chaine et jamais emis.
    #
    # CE QUI EST LU, ET IL Y EN A BEAUCOUP :
    #
    #     id 56, plan 1 (le plan lointain), profondeur 81, palette 81, `+554` = 87
    #     naissance en x -256, y 112 : il entre par la gauche, hors ecran
    #     `+364` = 0x8C0D9658, une table de HUIT scripts de battement d'ailes
    #
    # Les huit, lus enregistrement par enregistrement (images 20504 a 20582) :
    #
    #     0 : 20576..20582, 14 trames chacune     le vol lent, celui du lointain
    #     1 : les memes, 10 8 7 7 8 7 6
    #     2 : 20569..20575, 8 trames              5 : 20555..20561, douze pas
    #     3 : 20562..20568                        6 : 20504..20515, treize pas
    #     4 : 20555..20561                        7 : 20537..20543, 9 a 11
    #
    # On prend le **script 0**, le plus lent : c'est celui d'un oiseau loin, et c'est ce que
    # Frederic decrit -- quelques pixels blancs.
    #
    # LE VOL, LU AU MOT PRES -- 24/09/2026, seconde passe. La premiere avait cherche dans
    # `0x8C0A5A14` : **ce n'etait pas la bonne routine**. La table des acteurs de New
    # Generation est `0x8C1ADA10` (celle qu'`objetsng` emploie depuis toujours), et l'id 56
    # y pointe sur **`0x8C0A6F10`**. J'avais pris `0x8C1AD9F8`, six entrees plus bas, et je
    # lisais l'acteur 50. Tout ce qui en sortait -- « la vitesse n'est jamais ecrite », la
    # volee de six oiseaux, les constantes 0,5 et 20,0 -- appartenait a un autre decor.
    #
    # LA VRAIE ROUTINE, ET ELLE DIT TOUT :
    #
    #   `0x8C0A6F10` copie huit octets de `0x8C1B2308` sur la pile : DEUX etats.
    #
    #   etat 0 (`0x8C0A6F7C`)   `[+52] -= 1` ; des qu'il passe sous zero, etat 1.
    #                           Le spawner pose **`[+52] = 108`** : cent huit trames.
    #
    #   etat 1 (`0x8C0A6FA2`)   trois sous-etats sur `[+38]` :
    #
    #     0 (`0x8C0A6FBE`)  `[+562] = 1`, `[+568] = [+570] = 12`,
    #                       **`[+124] = 0x2500`** et **`[+132] = 0`**
    #                       -- vitesse 0x2500/65536 = 0,14453125 pixel par trame,
    #                          acceleration NULLE.
    #     1 (`0x8C0A6FE2`)  avance le script, puis si **`[+102] > 510`** passe au 2,
    #                       sinon saute a `0x8C0857B0`, qui fait
    #                       `[+124] += [+132]` puis `[+100] += [+124]` : c'est lui qui
    #                       deplace, une fois par trame.
    #     2 (`0x8C0A7040`)  **tout recommence** : `[+36] = 0`, `[+38] = 0`,
    #                       `[+102] = -256`, `[+106] = 112`, **`[+52] = 600`**,
    #                       et `0x8C03324C(objet, 0, 0)` repose le script 0.
    #
    # LE CYCLE, EN CHIFFRES LUS :
    #
    #     attente 108 trames (la premiere fois), puis 600 a chaque tour
    #     vol de x -256 a x 510, soit 766 pixels, a 0x2500 par trame
    #     766 x 256 / 37 = 5300 trames, environ 88 secondes
    #
    # `0x2500 >> 8` fait **37**, et le TRAJET du port compte justement en 1/256 de pixel
    # par trame (`nos[k].px += seg[1] << 8`) : 37 y redonne 0x2500 exactement, sans arrondi.
    #
    # LA SEULE DIFFERENCE ASSUMEE : le trajet du port boucle sur son premier segment, donc
    # il ne sait pas distinguer la premiere attente (108) des suivantes (600). On pose 600,
    # le regime permanent. L'ecart ne joue qu'une fois, au tout premier passage.
    #
    # Le x de la fiche est 728 : le moteur de NG dessine en `[+102] & 0x3FF`, et -256
    # replie sur 768 (moins l'ancre de 40). Le repli est pose aussi dans le trajet du port,
    # sans quoi l'oiseau sortirait de la page a 1494.
    0x8C0A707A: [dict(x=-256, y=112, pal=81, plan=1, col=87, id=56, script=0,
                      comportement=5,
                      images_brutes=[(20576 + i, 14) for i in range(7)],
                      trajet=[(600, 0, 0, -1), (5300, 37, 0, -1)])],
    0x8C0A8BCC: [dict(x=416, y=64, pal=79, plan=2, script=10, col=0x2059, id=65,
                      comportement=5,
                      images_brutes=[(21280 + i, 8) for i in range(8)],
                      trajet=[(600, 0, 0, -1), (196, -288, 0, -1), (148, -256, 0, -1)],
                      echelle=55, echelle_pas=8, echelle_seg=2)],
}

CHAUVES_SOURIS = [35, 34, 34, 34]

# UNE CASE DE TEMPS OU L'OBJET N'EST PAS AFFICHE (`disp_flag` a 0) : `animerng` en fait une
# image vide, et la cadence des autres images reste la bonne.
VIDE = -1


def _script_images(table, sc):
    """[(image, duree)] d'un script, lu comme `animerng.script_images`."""
    p = SP.u32(table + sc * 4)
    out = []
    for k in range(96):
        cmd, duree, idx = SP.D[p + k * 8 - 0x8C010000], SP.D[p + k * 8 + 1 - 0x8C010000], \
            SP.u16(p + k * 8 + 6)
        if cmd == 0x01:
            break
        if cmd == 0x00 and duree:
            out.append((idx, duree))
    return out


# GILL -- LES VAGUES DE LAVE (id 47) ET LEURS GERBES (id 19) -- 19/09/2026.
#
# Frederic, deux fois : « il manque plusieurs grosses vagues de lave ». Elles ne sont ni dans
# la page ni dans les scripts du decor : la routine de Gill appelle `0x8C0A5198`, qui cree
# CINQ objets id 47 depuis le bloc `0x8C1B1EB0` (huit octets : `+554`, x, y, profondeur), et
# `0x8C032D38`, qui prepare leurs quarante-cinq images : l'image globale 25488 +
# `u16[0x8C18AC70 + 2k]`, dans le second conteneur de l'asset (F_ETC39, 25488..25616).
#
# La routine de l'id 47 (`0x8C0A5084`) ne joue pas de script : chaque trame, elle dessine
# en direct (`0x8C032E54`) l'image `[type][pas]` -- le type est le rang de la vague (0..4),
# le pas avance toutes les `u8[0x8C1B1ED8 + pas]` = 8 trames, de 0 a 8, et reboucle. Un
# cycle de 72 trames, le meme pour les cinq. Le dessin direct prend la couleur de l'objet
# prepare par `0x8C032D38` (`+554` = 64), pas celle du bloc.
#
# Le meme spawner cree ensuite sept objets id 19 (`0x8C0A02F2`, table `0x8C1B0F38`
# {x, y, profondeur}, scripts 11 + rang de la table du decor, `+554` = 0x2040) dont le
# PARENT est une vague. Leur routine (`0x8C0A01BC`) les tient caches, et les montre selon
# le pas de la vague -- rang 1 a 3 au pas 0, rang 4 au pas 6, rangs 5 et 6 au pas 8 ; le
# rang 0 jamais. Montres, ils jouent leur script UNE fois, puis se cachent et le remettent
# au debut (`0x8C0A02C0`). Sur le cycle de 72 trames, c'est une suite fixe : on la deroule,
# les trames cachees etant des images vides.
CYCLE_GILL = 72
DEPART_GERBES = {1: 0, 2: 0, 3: 0, 4: 48, 5: 64, 6: 64}


def _cycle(images, depart, total=CYCLE_GILL):
    """Le script joue une fois a partir de `depart`, cache le reste du cycle."""
    trames = [idx for idx, d in images for _ in range(d)]
    par_trame = [trames[(f - depart) % total] if (f - depart) % total < len(trames) else VIDE
                 for f in range(total)]
    out = []
    for idx in par_trame:
        if out and out[-1][0] == idx:
            out[-1] = (idx, out[-1][1] + 1)
        else:
            out.append((idx, 1))
    return out


def _vagues_gill():
    table = 0x8C0CE4BC
    T = [NG.U16(0x8C18AC70 + 2 * k) for k in range(45)]
    out = []
    for t in range(5):
        a = 0x8C1B1EB0 + 8 * t
        _col, x, y, pal = [NG.U16(a + 2 * i) for i in range(4)]
        out.append(dict(x=x & 0x3FF, y=y & 0x3FF, pal=pal, plan=2, script=0, col=64, id=47,
                        boucle=True, table_objet=table,
                        images_brutes=[(25488 + T[9 * t + k], NG.U8(0x8C1B1ED8 + k))
                                       for k in range(9)]))
    for rang, depart in sorted(DEPART_GERBES.items()):
        a = 0x8C1B0F38 + 6 * rang
        x, y, pal = [NG.S16(a + 2 * i) for i in range(3)]
        out.append(dict(x=x, y=y, pal=pal, plan=2, script=11 + rang, col=0x2040, id=19,
                        boucle=True, table_objet=table,
                        images_brutes=_cycle(_script_images(table, 11 + rang), depart)))
    return out


EN_DUR[0x8C0A5198] = _vagues_gill()


# SEAN (NG, BANDE 2) : LES DEUX VOITURES ET L'HOMME A LA MALLETTE -- 26/09/2026.
#
# Frederic : « *dans une de ses variantes cherche la voiture traversant le decor au loin* ».
# Elle est dans la MEME table que les passants d'Alex : l'acteur id 64, enregistrements de
# 44 octets en `0x8C1B255C + 44k`, spawner `0x8C0A88D6`. La routine d'etage de Sean l'appelle
# avec k = 0, 1 et 2 -- trois appels que la chaine listait en NON LU.
#
# CE QUE CHAQUE VARIANTE CREE (`0x8C08C1BA`) : trois branches sur quatre retombent sur un
# TRONC COMMUN, et c'est le tronc qui porte les voitures --
#
#     z == 0  ->  0x8C0A7F48()      puis `bra` au tronc
#     z == 1  ->  0x8C0A88D6(0)     L'HOMME A LA MALLETTE, puis `bra` au tronc
#     z == 2  ->  idem
#     z == 3  ->  0x8C0A1318(3)     puis TOMBE sur le tronc
#     tronc (0x8C08C1E8), TOUJOURS : 0x8C0A88D6(1), 0x8C0A88D6(2), 0x8C0A1318(4)
#
# `cheminng` le retrouve seul : il donne z [1, 2] au premier appel et z [0,1,2,3] aux deux
# autres. On ne force donc aucun masque de variante ici.
#
# LES TROIS ENREGISTREMENTS, lus par le meme deversement que ceux d'Alex (`0x8C0A87A4`) :
#
#   k=0  [+38]=8  plan 2  col 0x2058  x 704  y 76   pal/prof 85   script 11  but -440
#   k=1  [+38]=5  plan 2  col 0x0040  x 656  y 114  pal/prof 102  script 2   but  -64  vit -1
#   k=2  [+38]=4  plan 2  col 0x0040  x 448  y 115  pal/prof 102  script 3   but  144  vit +1
#
# LES PALETTES, par la regle RAM (`+554`, `palettes_ramng`) et non par l'offset du morceau :
# les voitures sortent en **191** -- et les deux regles s'y accordent, elle est certaine ;
# l'homme en **1420** contre 172 pour la regle naive. C'est le piege du tonneau de Hugo.
#
# ---------------------------------------------------------------- k = 2 : ELLE EST GAREE
#
# Son `[+38]` est PAIR, donc `0x8C0A88A4` dit « arrive quand x DEPASSE `[+52]` » -- or elle
# nait en 448 et son but vaut 144 : **elle est deja arrivee**. Ce n'etait pas une
# contradiction, c'est une VOITURE A L'ARRET, et le cycle de `0x8C0A860A` le dit :
#
#     [+40]=1 -> re-initialise (x remis a 448)     [+40]=2 -> attend [+54]
#     [+40]=3 -> UNE trame : avance le script, avance d'un pixel, teste -> arrive
#     -> [+40]=1, [+54] = un tirage de 0x8C1B251C (392 a 2120 trames)
#
# L'objet n'est jamais detruit et son `[+1]` reste a 1 : il est DESSINE en permanence,
# immobile, et son script n'avance que d'un pas toutes les vingt secondes -- il faut deux
# pas pour changer d'image. On le pose donc **fige sur sa premiere image** (23935), comme le
# clochard d'Alex. C'est ce que le Dreamcast montre.
#
# ------------------------------------------- k = 0 : SON SCRIPT LE DEPLACE, PAS SA VITESSE
#
# Son `[+38]` vaut 8, et `0x8C4DE964[8] = 0x8C0A86E4` -- un comportement que rien n'avait
# encore lu. Il ne ressemble a aucun autre :
#
#     etat 0/1  il ATTEND que `s16[0x8C552758 + 26]` passe sous -64.
#               `0x8C552758` est `contexte + 228`, c'est-a-dire **l'enregistrement du plan
#               n. 1** (84 + 144), et `+26` en est l'abscisse entiere. C'est donc la CAMERA
#               qui le declenche : il part quand le plan proche a derive de 64 pixels.
#     etat 2    `0x8C0A888A` : `[+54]` decroit ; sous zero -> etat 3
#     etat 3    avance le script, teste l'arrivee (x < [+52]), et **N'APPELLE PAS
#               `0x8C0857B0`** -- rien ne le deplace par la vitesse.
#     arrivee   [+40] = 1 et `[+54] = u16[0x8C1B253C + 2*tirage]` -- la LONGUE table
#               (2708 a 8584 trames), celle des `[+38] > 5`.
#
# **C'EST SON SCRIPT QUI LE DEPLACE.** Le script 11 alterne une commande `0x29` et une
# image, douze fois. Le gestionnaire du `0x29` (`0x8C03402C`) fait, quand `u16[enreg+2]`
# est nul et que le miroir est nul :
#
#     u32[objet + 100] -= u16[enreg + 4] << 8        (miroir non nul : il AJOUTE)
#
# soit un deplacement de `u16[enreg+4] / 256` pixels vers la GAUCHE. Les douze pas du
# script 11 valent 0x0700 dix fois et 0x0B00 deux fois, c'est-a-dire **sept pixels, et onze
# deux fois** : 92 pixels par cycle de 78 trames.
#
# ET LE PORT COMPTE DANS LA MEME UNITE : son trajet fait `px += vx << 8`, exactement la
# meme operation. **`vx` est donc le mot du script, au signe pres** -- aucun arrondi, aucune
# conversion. On emet un segment d'UNE trame a `-mot` suivi d'un segment de `duree - 1`
# trames a zero : le pas saccade du Dreamcast, a la trame pres.
#
# DEUX SUITES : la 0 est sa POSE D'ATTENTE (le premier enregistrement d'image du script 11,
# l'image 24408) et la 1 sa marche entiere. Le premier segment du trajet appelle la 0, le
# premier segment de marche la 1 : pendant l'attente il ne marche donc pas sur place, comme
# sur la console ou son script n'avance qu'a l'etat 3.
#
# LA TABLE DES SCRIPTS DE SEAN est `0x8C0CF7D8` -- `u32[0x8C4DE610 + 12 * decor + 4 * aire]`
# pour sa paire (decor, aire), la meme formule que la fin de `0x8C0A87A4`.
TABLE_SEAN = 0x8C0CF7D8
ATTENTE_LONGUE = 0x8C1B253C      # les seize durees des `[+38] > 5`
ATTENTE_COURTE = 0x8C1B251C      # celles des `[+38] <= 5`


def _attente_moyenne(table):
    """L'entree de la table de tirage la plus proche de la moyenne des seize.

    LE TRAJET DU PORT N'A PAS DE TIRAGE. On en choisit donc UNE, et c'est un choix, pas une
    invention : la valeur est lue, seul le choix parmi les seize est assume. Le meme que
    pour les passants d'Alex."""
    v = [NG.U16(table + 2 * i) for i in range(16)]
    moy = sum(v) / 16.0
    return min(v, key=lambda x: abs(x - moy))


def _marche_du_script(table, script, distance):
    """Les segments de trajet d'un objet que son SCRIPT deplace (commande `0x29`).

    Rend `[(duree, vx, vy, suite)]` : pour chaque pas du script, une trame au deplacement
    lu puis le reste de la duree a l'arret. On repete le script jusqu'a couvrir `distance`
    pixels -- c'est ce que fait la console, qui reboucle sur `0x01` jusqu'a ce que le test
    d'arrivee morde."""
    p = NG.U32(table + script * 4)
    lus, mot, k = [], 0, 0

    while k < 256:
        drap, duree = NG.U8(p + k * 8), NG.U8(p + k * 8 + 1)
        if duree:
            lus.append((mot, duree))
            mot = 0
        elif drap == 0x29:
            mot = NG.U16(p + k * 8 + 4)
        elif drap == 0x01:
            break
        k += 1

    out, parcouru, i = [], 0, 0
    while parcouru < distance and len(out) < 1024:
        m, duree = lus[i % len(lus)]
        out.append((1, -m, 0, 1 if not out else -1))
        if duree > 1:
            out.append((duree - 1, 0, 0, -1))
        parcouru += m >> 8
        i += 1
    return out


EN_DUR[(0x8C0A88D6, 0)] = [
    dict(x=704, y=76, pal=85, plan=2, script=11, col=0x2058, id=64,
         comportement=5, suites=[[(11, 1)], 11],
         trajet=([(_attente_moyenne(ATTENTE_LONGUE), 0, 0, 0)]
                 + _marche_du_script(TABLE_SEAN, 11, 704 + 440)))]

EN_DUR[(0x8C0A88D6, 1)] = [
    dict(x=656, y=114, pal=102, plan=2, script=2, col=0x0040, id=64,
         comportement=5,
         trajet=[(_attente_moyenne(ATTENTE_COURTE), 0, 0, -1), (720, -256, 0, -1)])]

EN_DUR[(0x8C0A88D6, 2)] = [
    dict(x=448, y=115, pal=102, plan=2, script=3, col=0x0040, id=64, fige=True)]

_JSON = None


def blocs_json():
    global _JSON
    if _JSON is None:
        _JSON = json.load(open(os.path.join(ICI, "ng_blocs.json")))
    return _JSON


def decor(d):
    return [x for x in blocs_json()["decors"] if x["decor"] == d][0]


# `0x8C0A8EE4` (l'id 66, le punk de Dudley 2) ecrit ses deux scripts en `+52` (octet 12) et
# `+54` (octet 20) : `ng_blocs.json` range le premier sous `+68`, a tort -- le lecteur fait
# `mov r4,r1 ; add #52,r1 ; mov.w r3,@r1`. Sa routine (`0x8C0A8D0E`) joue `+52` au repos et
# `+54` quand un combattant passe a moins de 32 pixels.
REPOS_PAR_OCTET = {"0x8C0A8EE4": (12, 20)}


def repos_action(e, lecteur=None):
    """L'enregistrement, avec `repos` et `action` quand il les porte -- 18/09/2026.

    Le lecteur `0x8C0A0070` (l'id 18, jumeau de `0x8C028792` en 2I) ne pose pas de `+456` :
    il ecrit DEUX scripts, `+150` (repos) et `+152` (action), que sa routine joue selon
    l'etat. Faute de `script`, ses 36 blocs etaient sautes : les passants de Hong Kong, la
    foule de Hugo, le personnage de Necro, ceux de Ryu, Ken et Oro. `animerng` joue le plus
    riche des deux, comme `sc2` en 2I."""
    if e.get("script") is not None or e.get("repos") is not None:
        return e
    if lecteur in REPOS_PAR_OCTET:
        o_r, o_a = REPOS_PAR_OCTET[lecteur]
        par_octet = {c.get("octet"): c.get("valeur") for c in e.get("champs", ())}
        return dict(e, repos=par_octet.get(o_r), action=par_octet.get(o_a))
    ch = {c.get("objet"): c.get("valeur") for c in e.get("champs", ())}
    if 150 in ch:
        e = dict(e, repos=ch[150], action=ch.get(152))
    return e


# LES PLANS D'UNE BANDE, LUS DANS LE BINAIRE -- 22/09/2026.
#
# La table de parallaxe `0x8C189BA0` a un PAS DE 32 OCTETS par bande, soit QUATRE
# entrees de huit : une bande de New Generation n'a jamais plus de quatre plans, et le
# plan p lit l'entree p-1 (`0x8C0862CC` : `contexte[+128 + (plan-1)*144]`). Par-dessus,
# `0x8C088042` pose `contexte[+16] = u16[0x8C18965C + bande*2]` -- 2 ou 3 selon la bande,
# exactement le nombre d'entrees non nulles -- et les deux boucles d'initialisation des
# plans (`0x8C0881A8`, `0x8C088242`) s'y arretent.
#
# ON N'ECARTE QUE LES PLANS > 4, ceux qui sortent de la table. Un plan 3 ou 4 sur une
# bande qui n'en declare que deux reste pose : son entree existe (coefficient nul, un
# plan fixe), et comme ces elements ont `+118 = 0`, `0x8C086316` ne va jamais chercher
# leur table de defilement -- leur position est leur position de fiche. C'est le cas de
# la riviere d'Elena 1 et de l'objet d'Elena 2, que Frederic a valides le 18/09.
#
# LE REVERBERE D'IBUKI (`0x8C1AEEA0`, plan 5, profondeur 73) sort, lui, de la table :
# aucun coefficient, aucune couche, aucun plan. New Generation ne le pose nulle part ;
# le port le dessinait devant les bambous -- verdict de Frederic du 18/09.
PLANS_MAX = 4


def enregistrements(bande, bavard=False):
    """[(e, source)] : les objets que la bande pose, prets pour `animerng`.

    `e` porte x, y, plan, script (ou repos/action), palette, adresse, et au besoin
    variante, col, comportement, suites, deroule, miroir, table (la table de scripts)."""
    paires = CN.aires_de_bande(bande)
    if not paires:
        return [], []
    dnum, aire = paires[0]
    d = decor(dnum)
    table = int(d["scripts_animation"][aire], 16)
    out, inconnus = [], []

    # 1. LES ELEMENTS de l'aire -- et d'elle seule.
    for jeu in ("jeu1", "jeu2"):
        for b in d.get("elements", {}).get(jeu, []):
            if aire in b.get("aires", [0]):
                for e in b["enregistrements"]:
                    if e.get("plan") and e["plan"] > PLANS_MAX:
                        if bavard:
                            print("   element %s : plan %d, hors de la table de"
                                  " parallaxe -- New Generation ne le place pas"
                                  % (e.get("adresse"), e["plan"]))
                        continue
                    # UN ELEMENT DONT `+68` EST NUL N'ANIME PAS -- 25/09/2026.
                    # Frederic, sur Alex : « verifie les timings et declencheurs du
                    # clochard ». Il n'a pas de declencheur : il ne bouge JAMAIS.
                    #
                    # Un element devient un objet d'id 6 (`0x8C09CA14` ecrit `[+8] = 6`),
                    # et la routine de l'id 6 est `0x8C09C988`. Son etat 1 dit :
                    #
                    #     si `[+68]` est NUL, on n'appelle pas `0x8C0337C2`
                    #     -- le poseur de pas de script.
                    #
                    # `+68` est le huitieme mot de l'enregistrement, celui qu'`objetsng`
                    # nomme deja `objet 68`. Le port, lui, faisait tourner le script de
                    # TOUS les elements.
                    #
                    # LA PORTEE EST DE DEUX OBJETS dans toute New Generation -- mesure sur
                    # les dix-neuf bandes, elements a script de plus d'une image :
                    #
                    #     bande 1 (Alex)  script 8, 36 images, x 752 y 86, plan 1, pal 90
                    #                     -- LE CLOCHARD : il dort, se leve, leve les bras
                    #                        (22069..22076), se recouche. 808 trames en
                    #                        tout, et le Dreamcast n'en montre JAMAIS que
                    #                        la premiere image, 22065.
                    #     bande 4 (Ken)   script 16, 11 images, x -265 y 59
                    #
                    # Tous les autres elements a `+68` nul n'ont qu'une image : les figer
                    # ne change rien pour eux.
                    fixe = {c["objet"]: c["valeur"] for c in e.get("champs", [])}
                    fig = dict(e, table=table)
                    if fixe.get(68) == 0:
                        fig["fige"] = True
                    out.append((fig, "elements %s %s" % (jeu, b["bloc"])))

    # 2. LES APPELS que la routine fait pour cette aire, tirage par tirage.
    par_z = {z: CN.explorer_bande(bande, dnum, aire, z) for z in range(4)}
    sites = sorted(set().union(*par_z.values()))
    blocs = d.get("blocs", [])
    parents_poses = {}

    for site, cible, arg in sites:
        zs = [z for z in range(4) if (site, cible, arg) in par_z[z]]
        masque_site = sum(1 << z for z in zs)
        if cible in LECTEURS_ELEMENTS or cible in SERVICE:
            continue

        lies = [b for b in blocs if int(b.get("appel", "0"), 16) == site
                and (arg is None or b.get("arg") in (arg, None))]
        if lies:
            # un meme enregistrement peut servir plusieurs tirages : on reunit les masques
            vus = {}
            for b in lies:
                if b.get("z", 0) not in zs and len(lies) > 1:
                    continue
                bit = (1 << b["z"]) if len(lies) > 1 else masque_site
                parents_poses[b["bloc"]] = parents_poses.get(b["bloc"], 0) | bit
                for e in b["enregistrements"]:
                    cle = e["adresse"]
                    if cle in vus:
                        vus[cle][0]["variante"] |= bit
                    else:
                        d = dict(repos_action(e, b["lecteur"]), table=table,
                                 variante=bit)
                        # L'ID DE L'ACTEUR SE LIT DANS SON CHARGEUR -- 23/09/2026. Un bloc
                        # ne porte pas d'id ; celui qui le remplit l'ecrit en constante
                        # (`mov #id,r0 ; mov.w r0,@(8,rn)`). L'id 87 est le sprite qui
                        # attend que le combattant agisse : REACTIF, comportement 8.
                        if id_du_chargeur(b["lecteur"]) == 87:
                            d["comportement"] = 8
                        vus[cle] = (d, "bloc %s %s" % (b["lecteur"], b["bloc"]))
            out.extend(vus.values())
            continue

        conn = EN_DUR.get((cible, arg), EN_DUR.get(cible))
        if conn == []:
            continue
        if conn == "immeubles":
            for i in range(14):
                a = 0x8C1B1DA4 + i * 18
                r = [SP.u16(a + 2 * k) for k in range(9)]
                r = [v - 65536 if v > 32767 else v for v in r]
                out.append((dict(x=r[3], y=r[4], plan=r[1], palette=r[5], pal=r[5],
                                 col=r[2], script=r[6], adresse="0x%08X" % a,
                                 table=0x8C0D1080, variante=masque_site, doublon=True),
                            "immeubles %08X" % cible))
            continue
        if conn == "chauves-souris":
            a = SP.analyser(cible)
            for zz, nb, p in SP.blocs(a, 0):
                for i in range(nb or 0):
                    b = p + i * a["pas"]
                    ou = {off: rang for rang, off in a["champs"]}
                    x = SP.u16(b + ou[102] * 2)
                    y = SP.u16(b + ou[106] * 2)
                    pal = SP.u16(b + ou[88] * 2)
                    out.append((dict(x=x, y=y, plan=2, palette=pal, pal=pal, col=0x2058,
                                     script=CHAUVES_SOURIS[i], adresse="0x%08X" % b,
                                     table=table, doublon=True),
                                "chauves-souris %08X" % cible))
                break
            continue
        if conn:
            for k, c in enumerate(conn):
                if "aires" in c and aire not in c["aires"]:
                    continue
                e = dict(c)
                e.setdefault("palette", e["pal"])
                e.setdefault("variante", masque_site)
                e["variante"] |= 0           # les bits de combattants restent
                if not e["variante"] & 0xF:
                    e["variante"] |= masque_site
                e["adresse"] = "0x%08X" % cible
                e["table"] = e.pop("table_objet", table)
                e["doublon"] = True
                out.append((e, "en dur %08X id %s" % (cible, c.get("id"))))
            continue

        imm, _sous = RN.immediats(cible)
        inconnus.append((site, cible, arg, zs, imm))

    # 3. LES ENFANTS DU CHARGEUR A dont le parent est pose (la statue et son vase).
    #    Ceux du chargeur B sont des debris : jamais poses.
    #
    #    18/09/2026 : UN ENFANT N'EXISTE QUE LA OU SON PARENT EXISTE. Le chargeur A est appele
    #    par le spawner du parent (`0x8C0A13E4`, index = le 16e mot de son enregistrement) ; il
    #    prend donc le masque de variantes du parent. L'enfant de Sean (le motard, script 18)
    #    etait pose dans les quatre variantes, et en x -304 : Frederic, « personnage de droite
    #    a revoir, n'existe pas normalement ». Son `+118` vaut 1 -- le drapeau des objets dont
    #    le x se compte du milieu de la bande (tous ceux de Ryu, Londres et la fete de Hugo
    #    le portent) : il est en 208, a cote de sa moto (224), et seulement dans la variante 3.
    #
    #    ET L'INDEX 0 CREE D'ABORD LE MONSIEUR EN VERT (`0x8C0A1A6C` : `jsr 0x8C0A251C` quand
    #    r5 = 0). C'est le vase de Yun 2 et Yang 2 (`0x8C1B1058`) qui le porte : id 28 en
    #    496,64, profondeur 83, `+554` = 0x50, table du decor + 76 -- le meme qu'en 2I.
    for b in blocs:
        par = b.get("parent") or {}
        if (b["lecteur"] == "0x%08X" % CHARGEUR_A and par.get("bloc") in parents_poses
                and not b.get("relatif_au_parent")):
            masque = parents_poses[par["bloc"]]
            if b.get("arg") == 0:
                out.append((dict(x=496, y=64, pal=83, palette=83, plan=2, script=76, col=0x50,
                                 id=28, table=table, variante=masque, doublon=True,
                                 adresse="0x8C0A251C"),
                            "monsieur en vert, enfant 0 de %s" % par.get("bloc")))
            for e in b["enregistrements"]:
                ch = {}
                for c in e.get("champs", ()):
                    ch.setdefault(c.get("objet"), c.get("valeur"))
                enf = dict(e, table=table, variante=masque)
                if ch.get(118) == 1 and dnum not in (2, 4, 6, 11):
                    enf["dx"] = 512
                out.append((enf, "enfant %s de %s" % (b["bloc"], par.get("bloc"))))

    if bavard:
        print("BANDE %d  decor %d aire %d  table %08X" % (bande, dnum, aire, table))
        for e, src in out:
            sc = e.get("script", (e.get("repos"), e.get("action")))
            print("   %-38s x %4s y %4s script %-10s var 0x%X" % (src, e.get("x"), e.get("y"), sc,
                                                                  e.get("variante", 0xF)))
        for site, cible, arg, zs, imm in inconnus:
            print("   NON LU  %08X -> %08X r4=%s z %s %s" % (site, cible, arg, zs, imm))
    return out, inconnus


def main():
    for b in [int(a) for a in sys.argv[1:]] or range(19):
        enregistrements(b, bavard=True)
        print()


if __name__ == "__main__":
    main()
