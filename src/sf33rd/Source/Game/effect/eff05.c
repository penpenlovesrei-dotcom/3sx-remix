/**
 * @file eff05.c
 * Stage background objects
 */

#include "sf33rd/Source/Game/effect/eff05.h"
#include "bin2obj/char_table.h"
#include "common.h"
#include "sf33rd/Source/Game/effect/effect.h"
#include "sf33rd/Source/Game/engine/charset.h"
#include "sf33rd/Source/Game/rendering/aboutspr.h"
#include "sf33rd/Source/Game/rendering/texcash.h"
#include "sf33rd/Source/Game/stage/bg.h"
#include "sf33rd/Source/Game/stage/bg_sub.h"
#include "sf33rd/Source/Game/stage/ta_sub.h"
#include "sf33rd/Source/Game/rendering/chren3rd.h"
#include "sf33rd/Source/Game/rendering/texgroup.h"
#include "sf33rd/Source/Game/engine/slowf.h"
#include "sf33rd/Source/Game/engine/workuser.h"
#include "port/video/decor_objets.h"
#include "port/video/jalon.h"
#include "port/video/trace_fin.h"

const s16 scr_obj_num[58] = {
    0, 2, 0, 0, 0, 2, 1, 0, 3, 1, 0, 1, 1, 1, 1, 2, 2, 0, 2, 4, 1, 4,
    /* Les quinze etages ajoutes demandent UN objet de decor chacun. Ceux qui n'ont pas
       d'animation posable n'en auront pas pour autant : `effect_05_init` interroge
       `DecorObjets_Animation(bg_index)` et rend l'objet au tas quand elle rend NULL.
       C'est la table generee qui decide, pas celle-ci. */
    1 /* 22 GILL */,  1 /* 23 ALEX */,  1 /* 24 RYU */,   1 /* 25 YUN */,
    1 /* 26 DUDLEY */, 1 /* 27 NECRO */, 1 /* 28 HUGO */,  1 /* 29 IBUKI */,
    1 /* 30 ELENA */,  1 /* 31 ORO */,   1 /* 32 YANG */,  1 /* 33 KEN */,
    1 /* 34 SEAN */,   1 /* 35 URIEN */, 1 /* 36 GORGE */
};

const s16 stg_dum_data_tbl[1] = { 0 };

/* La fiche qui a servi a prouver la mecanique sur un etage ajoute. Gardee comme modele :
   { dead_f, plan, palette, x, y, z, index d'animation, sync }.
   Plan 1 et non 3 -- BG220 n'initialise que les plans 0 et 1. L'index 4 et la palette
   8492 sont ceux du premier objet de eff07, le seul effet de decor de l'etage 1 qui
   appelle char_move() ; eff05 et eff06 ne l'appellent pas, leurs objets sont FIXES par
   conception. z = 16 le met au premier plan.
   Pour animer un sprite de 2nd Impact il faudra la meme fiche, avec un index et une
   palette qui designent NOTRE art. */
/* z = 16 et non 98 : au PREMIER plan. A 98 l'objet peut passer derriere les deux plans
   de fond de l'etage et rester invisible meme s'il s'anime -- c'est l'hypothese que cet
   essai tranche. */
/* { dead_f, plan, palette, x, y, z, index d'animation, sync }
   x = 480, y = 48 : LA VRAIE POSITION, lue dans la liste d'affichage de l'etat Flycast --
   `bg01`, element 5. Elle y a toujours ete, et `releves2/` la porte pour chacun des
   elements de chaque decor. Le 512, 64 d'avant etait pose a la main, et c'est pour ca que
   la ventilation n'etait pas a sa place.

   Le plan, en revanche, reste 1 et non 2 : `BG220` n'initialise que les plans 0 et 1, et
   la liste d'affichage dit plan 2. C'est une approximation assumee tant que le script
   d'etage n'aura pas ses huit plans. */
/* LA PROFONDEUR EST 80, ET C'EST LU, PAS CHOISI.
   Le sixieme champ est `position_z`, qui indexe `PrioBase[]` -- et dans ce moteur un z
   PLUS GRAND est plus LOIN. Ca se lit dans `stage_priority[22..36] = 0x5E540000` : le
   plan lointain de nos etages est a 0x5E = 94, le plan proche a 0x54 = 84.
   Les objets de decor des etages d'origine poses sur la famille 2 emploient 68, 77 et 80
   -- devant leur plan (84), derriere les combattants. `stg1600_data_tbl` porte
   `{ 0, 2, 300, 511, 0, 80, 4, 0 }`, exactement notre cas.
   Ce champ valait **16**, une valeur d'essai laissee par une session precedente pour
   rendre l'objet visible pendant un debogage -- le commentaire disait « au PREMIER
   plan ». C'est elle qui mettait l'acolyte de Gill devant les combattants. */
const s16 stg2200_data_tbl[8] = { 0, 2, 8492, 480, 48, 80, 4, 0 };

const s16 stg0100_data_tbl[16] = { 0, 1, 300, 568, 48, 86, 0, 0, 0, 2, 8492, 528, 47, 68, 19, 0 };

const s16 stg0A00_data_tbl[8] = { 0, 3, 300, 512, 16, 88, 10, 0 };

const s16 stg0500_data_tbl[32] = { 0, 3, 300, 512, 0, 88, 9, 0, 0, 3, 8492, 560, 0, 88, 10, 0,
                                   0, 2, 300, 512, 0, 84, 3, 0, 0, 2, 300,  512, 0, 84, 4,  0 };

const s16 stg1300_data_tbl[32] = { 0, 3, 300, 512, 0, 88, 21, 0, 0, 3, 8492, 560, 0, 88, 22, 0,
                                   0, 2, 300, 512, 0, 84, 15, 0, 0, 2, 300,  512, 0, 84, 16, 0 };

const s16 stg0600_data_tbl[8] = { 0, 1, 8492, 511, 96, 88, 11, 0 };

const s16 stg0700_data_tbl[32] = { 0, 3, 8492, 504, 48,  94, 4, 0, 0, 3, 8492, 504, 112, 94, 8, 0,
                                   0, 2, 8492, 464, 256, 84, 7, 0, 0, 2, 8492, 512, 352, 84, 8, 0 };

const s16 stg0800_data_tbl[48] = { 0, 2, 8492, 496, 48, 85, 1,  0, 0, 7, 8492, 512, 43,  88, 12, 0,
                                   0, 7, 8492, 512, 43, 88, 13, 0, 0, 2, 8492, 624, 120, 86, 7,  0,
                                   0, 3, 8492, 512, 72, 90, 1,  0, 0, 3, 8492, 512, 72,  90, 2,  0 };

const s16 stg0900_data_tbl[8] = { 0, 6, 8492, 352, 16, 10, 5, 0 };

const s16 stg0c00_data_tbl[8] = { 0, 6, 8492, 352, 16, 10, 5, 0 };

const s16 stg0d00_data_tbl[8] = { 0, 3, 300, 512, 32, 88, 0, 0 };

const s16 stg0e00_data_tbl[24] = { 0,  3,  300, 512, 88, 98, 7,   0,   0,   2,  300, 576,
                                   64, 84, 5,   0,   0,  2,  300, 560, 208, 84, 6,   0 };

const s16 stg1000_data_tbl[16] = { 0, 3, 8492, 512, 80, 86, 0, 0, 0, 2, 8492, 480, 16, 12, 2, 0 };

const s16 stg1100_data_tbl[16] = { 0, 1, 8492, 512, 176, 90, 2, 0, 0, 1, 8492, 512, 240, 90, 3, 0 };

const s16 stg1400_data_tbl[32] = { 0, 2, 8492, 504, 11,  10, 0, 0, 0, 1, 8492, 496, 64,  86, 1, 0,
                                   0, 3, 300,  496, 144, 88, 3, 0, 0, 3, 300,  512, 320, 83, 5, 0 };

const s16 stg1500_data_tbl[8] = { 0, 2, 300, 445, 48, 10, 0, 0 };

const s16 stg1600_data_tbl[32] = { 0, 2, 300, 624, 0, 10, 2, 0, 0, 2, 8492, 511, 0,  12, 3,  0,
                                   0, 2, 300, 511, 0, 80, 4, 0, 0, 2, 300,  608, 48, 77, 11, 0 };

u32* char_add[58] = { _fnl_char_table, _usa_char_table, _j10_char_table, _hkg_char_table, _eng_char_table,
                      _rca_char_table, _grm_char_table, _j11_char_table, _afc_char_table, _brz_char_table,
                      _hkg_char_table, _usa_char_table, _brz_char_table, _orm_char_table, _jp2_char_table,
                      _chn_char_table, _jp3_char_table, _usa_char_table, _rca_char_table, _frc_char_table,
                      _bns_char_table, _bns_char_table,
    /* Les quinze etages ajoutes empruntent la table d'animation de l'etage 1 avec
       l'index 4 : c'est le seul couple dont on ait verifie qu'il produit un objet qui
       naît et avance ses images. Il ne sert qu'a faire tourner la mecanique -- la GRILLE
       et les PIXELS sont les notres, et la CADENCE aussi. */
    _usa_char_table, _usa_char_table, _usa_char_table, _usa_char_table, _usa_char_table,
    _usa_char_table, _usa_char_table, _usa_char_table, _usa_char_table, _usa_char_table,
    _usa_char_table, _usa_char_table, _usa_char_table, _usa_char_table, _usa_char_table,
    /* LE TABLEAU S'ARRETAIT ICI, A 37 -- ET C'ETAIT LE GEL DE NEW GENERATION.
       `effect_05_init` fait `char_table[0] = char_add[bg_w.bg_index]`, et `bg_index` vaut
       37 a 57 pour les vingt et un etages ajoutes ensuite. On lisait donc ce qui SUIT le
       tableau, et `set_char_move_init` -- appele des la premiere trame de dessin, dans le
       `case 0` de `effect_05_move` -- dereferencait un pointeur pris au hasard.

       D'ou un defaut qui ne ressemblait a rien : tantot un gel muet, tantot un crash sec,
       selon ce qui trainait en memoire a cet endroit. Ni `fatal.log`, ni trace de pile, et
       le decor entierement charge juste avant.

       C'est le meme piege que le commentaire de `scr_obj_data` decrit quinze lignes plus
       bas -- « la laisser a NULL n'aurait rien casse tant qu'ils n'avaient pas d'objets
       animes » -- et qui n'avait ete corrige que pour lui. Les deux tableaux sont indexes
       par le meme `bg_index` et doivent avoir la meme taille. */
    _usa_char_table, _usa_char_table, _usa_char_table, _usa_char_table, _usa_char_table,
    _usa_char_table, _usa_char_table, _usa_char_table, _usa_char_table, _usa_char_table,
    _usa_char_table, _usa_char_table, _usa_char_table, _usa_char_table, _usa_char_table,
    _usa_char_table, _usa_char_table, _usa_char_table, _usa_char_table, _usa_char_table,
    _usa_char_table
};

const s16* scr_obj_data[58] = {
    stg_dum_data_tbl, stg0100_data_tbl, stg_dum_data_tbl, stg_dum_data_tbl,
    stg_dum_data_tbl, stg0500_data_tbl, stg0600_data_tbl, stg0700_data_tbl,
    stg0800_data_tbl, stg0900_data_tbl, stg0A00_data_tbl, stg0100_data_tbl,
    stg0c00_data_tbl, stg0d00_data_tbl, stg0e00_data_tbl, stg1000_data_tbl,
    stg1100_data_tbl, stg_dum_data_tbl, stg1300_data_tbl, stg1400_data_tbl,
    stg1500_data_tbl, stg1600_data_tbl,
    /* Les quinze etages ajoutes partagent la meme fiche modele. Elle ne porte que ce qui
       est commun -- la palette, la profondeur, l'index d'animation du donneur ; la
       position et le plan sont ecrases dans `effect_05_init` par ceux de l'animation.
       ATTENTION : `stg_dum_data_tbl` ne compte qu'UNE entree, et `effect_05_init` en lit
       HUIT. Le laisser ici avec `scr_obj_num` a 1 lirait hors du tableau. */
    stg2200_data_tbl, stg2200_data_tbl, stg2200_data_tbl, stg2200_data_tbl,
    stg2200_data_tbl, stg2200_data_tbl, stg2200_data_tbl, stg2200_data_tbl,
    stg2200_data_tbl, stg2200_data_tbl, stg2200_data_tbl, stg2200_data_tbl,
    stg2200_data_tbl, stg2200_data_tbl, stg2200_data_tbl,
    /* LES VINGT ET UN ETAGES SUIVANTS -- dix-neuf de New Generation, puis les deux bandes
       de 2nd Impact restees de cote -- prennent la MEME fiche modele. La laisser a NULL
       n'aurait rien casse tant qu'ils n'avaient pas d'objets animes ; depuis qu'ils en
       ont, `lp_cnt` est non nul et `data_ptr` est dereférencé juste apres. */
    stg2200_data_tbl, stg2200_data_tbl, stg2200_data_tbl, stg2200_data_tbl,
    stg2200_data_tbl, stg2200_data_tbl, stg2200_data_tbl, stg2200_data_tbl,
    stg2200_data_tbl, stg2200_data_tbl, stg2200_data_tbl, stg2200_data_tbl,
    stg2200_data_tbl, stg2200_data_tbl, stg2200_data_tbl, stg2200_data_tbl,
    stg2200_data_tbl, stg2200_data_tbl, stg2200_data_tbl, stg2200_data_tbl,
    stg2200_data_tbl
};

void effect_05_move(WORK_Other* ewk) {
    if (obr_no_disp_check() == 0) {
        switch (ewk->wu.routine_no[0]) {
        case 0:
            ewk->wu.routine_no[0]++;
            ewk->wu.disp_flag = 1;
            set_char_move_init(&ewk->wu, 0, ewk->wu.char_index);
            break;

        case 1:
            if (compel_dead_check(ewk) != 0) {
                ewk->wu.routine_no[0]++;
                break;
            }
            /* Ce que les etages AJOUTES ont besoin qu'on fasse pour eux, et que le jeu
               d'origine n'a jamais eu a faire. Mesure en jeu le 28/08/2026 : sans ces
               deux lignes rien ne bouge ou tout gele ; avec, un objet de decor naît,
               avance ses images une par trame et se dessine (verdict 2).

               1. LE PAS D'ANIMATION. eff05 n'appelle jamais char_move() : ses objets
                  sont FIXES par conception, comme ceux de eff06. C'est eff07 qui anime.

               2. LE GROUPE DE GRAPHIQUES, ET AVANT LE DESSIN. Il est normalement charge
                  par la liste de chargement de l'etage ; un etage ajoute emprunte celle
                  d'un autre et ne l'a donc pas. mtrans.c ne s'en remet pas : il
                  journalise "les donnees de trans ne sont pas valides" et **boucle a
                  l'infini** -- c'est ca, le "plantage au chargement". Mettre ce
                  chargement APRES le dessin reproduit le gel a la premiere trame.
                  load_any_texture_patnum ne coute rien si le groupe est deja la. */
            if (bg_w.bg_index >= 22) {
                /* Nos couleurs, a chaque image. Le chargement de l'etage peut reecrire
                   l'emplacement apres coup, et une palette est vivante : soixante-quatre
                   u16 par image ne coutent rien. */
                Jalon("       eff05 objet", ewk->wu.type);
                DecorObjets_InstallerPalette(&ewk->wu);
                Jalon("       eff05 palette posee", ewk->wu.type);
                DecorObjets_Avancer(&ewk->wu);
                Jalon("       eff05 avance", ewk->wu.type);
                char_move(&ewk->wu);
                Jalon("       eff05 char_move cg", ewk->wu.cg_number);
                if (ewk->wu.cg_number < 37664) {
                    load_any_texture_patnum(ewk->wu.cg_number, 2, 0);
                    Jalon("       eff05 texture chargee", ewk->wu.type);
                }

                /* UN OBJET QUI NAGE -- les poissons de Yang. `disp_pos_trans_entry_s` relit
                   `xyz` juste apres : il suffit d'y poser la position de la trame. */
                {
                    s32 x;
                    s32 y;

                    if (DecorObjets_Position(&ewk->wu, &x, &y)) {
                        ewk->wu.xyz[0].disp.pos = (s16)x;
                        ewk->wu.xyz[1].disp.pos = (s16)y;
                    }
                }
            }
            Jalon("       eff05 disp_pos_trans_entry_s", ewk->wu.type);
            disp_pos_trans_entry_s(ewk);
            Jalon("       eff05 objet rendu", ewk->wu.type);
            break;

        default:

            all_cgps_put_back(&ewk->wu);
            push_effect_work(&ewk->wu);
            break;
        }
    }
}

s32 effect_05_init() {
    WORK_Other* ewk;
    s16 ix;
    s16 lp_cnt;
    s16 i;
    const s16* data_ptr;
    const DecorAnimation* notre_anim = NULL;

    /* GARDE-FOU DE BORNES. Trois tableaux sont indexes ici par `bg_index` -- `scr_obj_num`,
       `scr_obj_data` et `char_add` -- et il a suffi que l'un des trois ne soit pas etendu
       pour donner un defaut illisible : tantot gel muet, tantot crash sec, sans message ni
       trace, le decor entierement charge juste avant. On le dit maintenant, au lieu de
       lire n'importe ou. */
    if (bg_w.bg_index < 0 || bg_w.bg_index >= 58) {
        TraceFin("eff05 : bg_index %d HORS BORNES (0..57)\n", (s32)bg_w.bg_index, 0, 0);
        return 0;
    }

    lp_cnt = scr_obj_num[bg_w.bg_index];

    /* UN ETAGE AJOUTE EN DEMANDE AUTANT QUE SES DONNEES EN PORTENT. C'est la table
       generee qui decide, pas `scr_obj_num` -- Gill a QUATRE figures animees dans le
       binaire de 2nd Impact, et une seule etait posee. On le decide AVANT de tirer un
       WORK du tas : en tirer un pour le rendre aussitot laisse la fiche a moitie
       remplie. */
    if (bg_w.bg_index >= 22) {
        lp_cnt = (s16)DecorObjets_Combien(bg_w.bg_index);
    }

    if (lp_cnt == 0) {
        return 0;
    }

    data_ptr = scr_obj_data[bg_w.bg_index];

    for (i = 0; i < lp_cnt; i++) {
        /* La fiche modele de nos etages ne compte qu'UNE entree de huit champs : on la
           relit pour chaque objet au lieu d'avancer dans un tableau qui n'existe pas.
           Tout ce qui compte -- position, plan, profondeur, palette -- est ensuite
           ecrase par l'animation. */
        if (bg_w.bg_index >= 22) {
            data_ptr = scr_obj_data[bg_w.bg_index];
        }

        if ((ix = pull_effect_work(4)) == -1) {
            return -1;
        }

        ewk = (WORK_Other*)frw[ix];
        ewk->wu.be_flag = 1;
        ewk->wu.id = 5;
        ewk->wu.work_id = 0x10;
        ewk->wu.cgromtype = 1;
        ewk->wu.rl_flag = 0;
        ewk->wu.my_col_mode = 0x4200;
        ewk->wu.char_table[0] = char_add[bg_w.bg_index];
        ewk->wu.type = i;
        ewk->wu.dead_f = *data_ptr++;
        ewk->wu.my_family = *data_ptr++;
        ewk->wu.my_col_code = *data_ptr++;
        ewk->wu.xyz[0].disp.pos = *data_ptr++;
        ewk->wu.xyz[1].disp.pos = *data_ptr++;
        ewk->wu.my_priority = ewk->wu.position_z = *data_ptr++;
        ewk->wu.char_index = *data_ptr++;
        ewk->wu.sync_suzi = *data_ptr++;

        suzi_offset_set(ewk);

        ewk->wu.my_mts = 7;
        ewk->wu.my_trans_mode = get_my_trans_mode(ewk->wu.my_mts);

        /* C'est CET objet-la, et lui seul, dont mtrans.c remplacera les morceaux. La
           garde ne peut pas porter sur l'etage : la fonction de dessin est partagee avec
           les combattants.

           LA FICHE VIENT DES DONNEES, pas du tableau ci-dessus. `stg2200_data_tbl` ne
           sert plus que de modele : la position, le plan et le nombre d'images sont ceux
           de l'animation choisie pour cet etage par `dc-decors/outils/animations.py`,
           lus dans la liste d'affichage de 2nd Impact. Un etage ajoute sans animation
           n'a pas d'objet du tout -- sans ce test il en naitrait un qui dessinerait
           l'art du donneur. */
        if (bg_w.bg_index >= 22) {
            notre_anim = DecorObjets_Animation(bg_w.bg_index, i);

            if (notre_anim == NULL) {
                push_effect_work(&ewk->wu);
                continue;
            }

            ewk->wu.my_family = notre_anim->famille;
            ewk->wu.xyz[0].disp.pos = notre_anim->x;
            ewk->wu.xyz[1].disp.pos = notre_anim->y;

            /* CHAQUE OBJET SA PALETTE. `wk->colcd` sort de `my_col_code & 0x1FF`, soit
               300 pour la fiche modele ; le rang s'y ajoute, et `DecorObjets_InstallerPalette`
               pose les couleurs en 300 + rang. Sans ca les quatre figures de Gill se
               partageraient un seul emplacement et prendraient la couleur de la derniere. */
            ewk->wu.my_col_code = (s16)(ewk->wu.my_col_code + i);

            /* LA PROFONDEUR EST INDEPENDANTE DU PLAN. `mlt_obj_matrix` prend la matrice
               de `my_family` -- donc le defilement -- mais la profondeur de
               `position_z`. Les 80 du modele mettent l'objet devant TOUS les plans de
               fond (94, 90, 84), ce qui est juste pour l'acolyte de Gill mais faux pour
               la chute d'eau d'Oro : elle defile avec la grotte du fond et doit se
               dessiner juste devant le couchant. Zero garde la valeur du modele. */
            if (notre_anim->z) {
                ewk->wu.my_priority = ewk->wu.position_z = notre_anim->z;
            }

            /* PAS DE DECALAGE : la profondeur lue dans 2I est la bonne, a condition que les
               plans aient les leurs -- lues dans SF3_2ND.BIN depuis le 16/09 (table
               0x8C601EE8, voir DECORS.md section 11). Le recul de 16 des cascades est
               retire : il compensait des plans mal places. */

            /* DIAGNOSTIC `SF3_DECOR_Z` -- voir `DecorObjets_ProfondeurForcee`. */
            if (DecorObjets_ProfondeurForcee()) {
                ewk->wu.my_priority = ewk->wu.position_z = (s16)DecorObjets_ProfondeurForcee();
            }

            DecorObjets_Marquer(&ewk->wu, bg_w.bg_index, i);
        }
    }

    return 0;
}
