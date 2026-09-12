/**
 * @file bg_220.c
 * Waterfall Gorge -- a 2nd Impact stage added to the roster.
 *
 * Two planes and nothing else. The stage owns its pages through `tex_remix/stage22/`, so the
 * script has no scenery objects to spawn: the artwork is entirely in the background planes.
 */

#include "sf33rd/Source/Game/stage/bg220.h"
#include "common.h"
#include "sf33rd/Source/Game/effect/eff05.h"
#include "sf33rd/Source/Game/engine/plcnt.h"
#include "sf33rd/Source/Game/stage/bg.h"
#include "sf33rd/Source/Game/stage/bg_data.h"
#include "port/video/etages2i_plans.inc"
#include "port/video/etagesng_plans.inc"
#include "port/video/etages2ibis_plans.inc"
#include "sf33rd/Source/Game/stage/bg_sub.h"
#include "sf33rd/Source/Game/stage/ta_sub.h"
#include "sf33rd/Source/Game/system/work_sys.h"

void BG220() {
    bgw_ptr = &bg_w.bgw[1];
    bg2202();
    bgw_ptr = &bg_w.bgw[0];
    bg2201();

    /* LE TROISIEME PLAN. Meme montage que `BG020`, qui pilote `bgw[2]` juste apres
       `bgw[0]`. La famille 3 = `bgw[2]` est le plan de dessin 2 : `scr_trans(bgnm)`
       prend `BgMATRIX[bgnm + 1]`, et `Bg_Family_Set` publie `Family_Set_W(i + 1, ...)`
       pour tout `i < bg_w.scno` -- d'ou le `use_scr[22] = 3`.

       Les decors de 2nd Impact demandent TROIS vitesses la ou `BG220` n'en offrait que
       deux : pour bg00, 0,25 pour le ciel, 1,00 pour le sol et les acolytes, et 0 pour
       le temple et les obelisques, dont le plan n'est pilote par aucun objet de fond et
       ne defile donc pas. Deux plans ne pouvaient pas porter ca. */
    if (bg_w.bg_index >= 22 && use_scr[bg_w.bg_index] >= 3) {
        bgw_ptr = &bg_w.bgw[2];
        bg2203();
    }

    /* LE QUATRIEME PLAN. Il n'existe que parce que l'etage a sa propre archive : le
       plan `j` prend les emplacements `j*64 + 132`, donc la liste 324, et il faut que
       l'archive porte 128 pages. Le bit 3 de `Screen_Switch` n'est mis que par
       `effd3.c`, l'effet d'aube, qu'aucun etage ajoute n'emploie : `scr_trans(3)` est
       donc libre pour nous, sous la garde posee dans `bg.c`. */
    if (bg_w.bg_index >= 22 && use_scr[bg_w.bg_index] >= 4) {
        bgw_ptr = &bg_w.bgw[3];
        bg2204();
    }

    zoom_ud_check();
    bg_pos_hosei2();
    Bg_Family_Set();
}

void bg2203() {
    void (*bg2203_jmp[2])() = { bg2203_init00, bg_move_common };
    bg2203_jmp[bgw_ptr->r_no_0]();
}

void bg2204() {
    void (*bg2204_jmp[2])() = { bg2204_init00, bg_move_common };
    bg2204_jmp[bgw_ptr->r_no_0]();
}

/* Le quatrieme plan porte le coefficient qui restait sans place. Pour `bg00` c'est
   l'objet 6, celui du plan 7 de 2nd Impact : le petit obelisque gris, 0,625 en x et
   0,875 en y. Avec trois plans il devait se contenter du 0,875 du temple. */
static const s32 bg220_speed_x_quatre[58] = { ETAGES2I_SPEED_X_QUATRE };

static const s32 bg220_speed_y_quatre[58] = { ETAGES2I_SPEED_Y_QUATRE };

void bg2204_init00() {
    bgw_ptr->r_no_0++;
    bgw_ptr->old_pos_x = bgw_ptr->xy[0].disp.pos = bgw_ptr->pos_x_work = 0x200;
    bgw_ptr->hos_xy[0].cal = bgw_ptr->wxy[0].cal = bgw_ptr->xy[0].cal;
    bgw_ptr->zuubun = 0;
    bgw_ptr->y_limit = bgw_ptr->y_limit2 = 0xF0;
    bgw_ptr->pos_y_work = 0;
    bgw_ptr->xy[1].disp.pos = 0;

    /* CELLE-CI RESTE, et c'est voulu : `bg220_speed_x_quatre` ne porte que
       `ETAGES2I_SPEED_X_QUATRE`. Aucun etage de New Generation n'a de QUATRIEME plan --
       seul `bg00` en a un en 2nd Impact -- donc il n'y a rien a lire au-dela de 36, et
       lever la garde ici irait chercher des zeros. */
    if (bg_w.bg_index >= 22 && bg_w.bg_index < 37) {
        bgw_ptr->speed_x = bg220_speed_x_quatre[bg_w.bg_index];
        bgw_ptr->speed_y = bg220_speed_y_quatre[bg_w.bg_index];
    }
}

/* LE TROISIEME PLAN SUIT L'OBJET 2, ET IL BOUGE.
 *
 * Je l'avais fait statique en croyant qu'aucun objet ne pilotait le plan 3 : `nb_objets`
 * vaut 2 dans l'etat de Gill. C'est faux, et Frederic l'a vu a l'ecran -- ces elements
 * bougent dans 2nd Impact. Le coefficient de l'objet 2 **varie decor par decor** (0,875
 * pour bg00, 0,8125 pour bg01, 0 pour bg03), alors que ceux des objets 4 et 6 sont
 * identiques dans les vingt et un etats : ces deux-la sont des restes, l'objet 2 non.
 * `0x8C6AF314` n'est donc pas le nombre d'objets.
 *
 * `y_limit` / `y_limit2` restent poses, comme dans `bg020_sync_init` : `bg_y_move_check`
 * ecrete sur `y_limit2`, et le laisser a zero rabattrait le plan des qu'il bougerait. */
static const s32 bg220_speed_x_tiers[58] = { ETAGES2I_SPEED_X_TIERS, ETAGESNG_SPEED_X_TIERS };

/* LA VERTICALE AUSSI, et elle se lit au meme endroit : `+20` de la fiche d'objet.
 * Laissee a zero, le plan ne suivait pas du tout la camera en hauteur et se decalait
 * vers le haut des qu'un personnage sautait haut -- vu a l'ecran. L'objet 2 de bg00
 * porte `coef_y = 0xE000`, la meme valeur que son `coef_x`.
 *
 * C'est ce plan-ci qui peut la prendre, et pas `bgw[0]` : `bg_y_move_check` ecrete sur
 * `y_limit2`, et seul `bg2203_init00` le pose. */
static const s32 bg220_speed_y_tiers[58] = { ETAGES2I_SPEED_Y_TIERS, ETAGESNG_SPEED_Y_TIERS };

void bg2203_init00() {
    bgw_ptr->r_no_0++;
    bgw_ptr->old_pos_x = bgw_ptr->xy[0].disp.pos = bgw_ptr->pos_x_work = 0x200;
    bgw_ptr->hos_xy[0].cal = bgw_ptr->wxy[0].cal = bgw_ptr->xy[0].cal;
    bgw_ptr->zuubun = 0;
    bgw_ptr->y_limit = bgw_ptr->y_limit2 = 0xF0;
    bgw_ptr->pos_y_work = 0;
    bgw_ptr->xy[1].disp.pos = 0;

    /* LA GARDE S'ARRETAIT A 37 ET PRIVAIT NEW GENERATION DE SON DEFILEMENT.
       `bg220_speed_x_tiers` porte pourtant `ETAGESNG_SPEED_X_TIERS` : les donnees etaient
       generees, lues par personne. Les dix-neuf decors de NG avaient donc un troisieme
       plan immobile, quoi que fasse la camera. */
    if (bg_w.bg_index >= 22) {
        bgw_ptr->speed_x = bg220_speed_x_tiers[bg_w.bg_index];
        bgw_ptr->speed_y = bg220_speed_y_tiers[bg_w.bg_index];
    }
}

void bg2201() {
    void (*bg2201_jmp[2])() = { bg2201_init00, bg_move_common };
    bg2201_jmp[bgw_ptr->r_no_0]();
}

/* LA PARALLAXE DU PLAN LOINTAIN, en 16.16, un coefficient par etage ajoute.
 *
 * `bgw[0]` -- le plan que `bg2201` pilote -- etait FIGE, et ca se lit dans
 * `bg_x_move_check` : `xy[0].cal = speed_x * bg_w.bg2_sp_x2`. Avec le `speed_x` a zero
 * laisse par `bg_initialize`, `cal` vaut zero et le plan ne quitte jamais son origine
 * 0x200, pendant que `bgw[1]`, le plan de base, suit la camera a 1,00.
 *
 * Les coefficients sont ceux des objets de fond de 2nd Impact, lus en RAM dans la fiche
 * d'objet (`+16` / `+20`, deja en 16.16) -- voir DONNEES.md. Notre moitie lointaine
 * porte le fond de l'objet 0, donc c'est SON coefficient.
 *
 * `0x10000` = 1,00. Les etages d'origine emploient la meme echelle sur leur troisieme
 * plan (`bg020_sync_init` pose 0xE000).
 *
 * LA VERTICALE N'EST PAS POSEE, ET C'EST DELIBERE. `bg_y_move_check` ecrete sur
 * `y_limit2`, que cet init ne pose pas : il vaudrait zero, et le plan serait rabattu a
 * zero des qu'il bougerait. Poser `speed_y` demande donc aussi `y_limit` / `y_limit2`,
 * une seconde inconnue. Une variable a la fois.
 */
static const s32 bg220_speed_x[58] = { ETAGES2I_SPEED_X_LOIN, ETAGESNG_SPEED_X_LOIN, ETAGES2IBIS_SPEED_X_LOIN };

void bg2201_init00() {
    bgw_ptr->r_no_0++;
    bgw_ptr->old_pos_x = bgw_ptr->xy[0].disp.pos = bgw_ptr->pos_x_work = 0x200;
    bgw_ptr->hos_xy[0].cal = bgw_ptr->wxy[0].cal = bgw_ptr->xy[0].cal;
    bgw_ptr->zuubun = 0;

    /* LA VERTICALE DU PLAN LOINTAIN EST RETIREE, ET C'EST DELIBERE.
       Je l'avais ajoutee au passage du cablage : `speed_y`, plus `y_limit`,
       `pos_y_work` et `xy[1].disp.pos` pour lever l'ecretage. Frederic a vu les
       arriere-plans perdre leur defilement vertical au super saut -- c'est cette
       modification, pas les donnees.
       Les etages d'ORIGINE ne posent rien de tout ca sur leur plan lointain
       (`bg0201_init00`, `bg0501_init00`) et defilent pourtant : la verticale de fond
       vient d'ailleurs, du plan de base et de `bg_prm[].bg_v_shift`. On ne touche donc
       qu'a l'horizontale, qui est validee. */
    /* Meme garde levee : `bg220_speed_x` porte `ETAGESNG_SPEED_X_LOIN` et
       `ETAGES2IBIS_SPEED_X_LOIN`, donc les 58 entrees sont remplies. Le plan LOINTAIN de
       New Generation ne defilait pas non plus. */
    if (bg_w.bg_index >= 22) {
        bgw_ptr->speed_x = bg220_speed_x[bg_w.bg_index];
    }
}

void bg2202() {
    void (*bg2202_jmp[2])() = { bg2202_init00, bg_base_move_common };
    bg2202_jmp[bgw_ptr->r_no_0]();
}

void bg2202_init00() {
    bgw_ptr->r_no_0++;
    bgw_ptr->old_pos_x = bgw_ptr->xy[0].disp.pos = bgw_ptr->pos_x_work = 0x200;
    bgw_ptr->hos_xy[0].cal = bgw_ptr->wxy[0].cal = bgw_ptr->xy[0].cal;
    bgw_ptr->zuubun = 0;
    /* Fait naitre les objets de decor de scr_obj_num[bg_index]. Sans cet appel un etage
       ajoute ne peut avoir AUCUN objet : tous les etages d'origine qui ont du decor le
       font depuis leur init, et bg220.c ne le faisait pas. Ne coute rien tant que
       scr_obj_num vaut zero. */
    effect_05_init();
}
