/**
 * @file pl01win_fr.c
 * Alex Win Quotes (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl01win_fr.h"
#include "common.h"

static s8* msgWinPL01_00P[1] = { "" };
static s8* msgWinPL01_01P[1] = { "" };
static s8* msgWinPL01_02P[1] = { "" };
static s8* msgWinPL01_03P[1] = { "" };
static s8* msgWinPL01_04P[1] = { "" };
static s8* msgWinPL01_05P[1] = { "" };
static s8* msgWinPL01_06P[1] = { "" };
static s8* msgWinPL01_07P[1] = { "" };
static s8* msgWinPL01_08P[1] = { "" };
static s8* msgWinPL01_09P[1] = { "" };
static s8* msgWinPL01_10P[1] = { "" };
static s8* msgWinPL01_11P[1] = { "" };
static s8* msgWinPL01_12P[1] = { "" };
static s8* msgWinPL01_13P[1] = { "" };
static s8* msgWinPL01_14P[1] = { "" };
static s8* msgWinPL01_15P[1] = { "" };
static s8* msgWinPL01_16P[1] = { "" };
static s8* msgWinPL01_17P[1] = { "" };
static s8* msgWinPL01_18P[1] = { "" };
static s8* msgWinPL01_19P[1] = { "" };
static s8* msgWinPL01_20P[2] = {
    "   La d*efaite t'aidera `a r*egler              ",
    "   ton petit probl`eme d'ego.                   ",
};
static s8* msgWinPL01_21P[2] = {
    "   Ma^itrise ton esprit avant de                ",
    "   pr*etendre ma^itriser ton corps !            ",
};
static s8* msgWinPL01_22P[2] = {
    "   Ne me fais pas perdre mon temps.             ",
    "   Tu n'as rien `a m'apprendre.                 ",
};
static s8* msgWinPL01_23P[2] = {
    "   *Etudie tes adversaires et exploite          ",
    "   leurs faiblesses. Voil`a la cl*e...          ",
};
static s8* msgWinPL01_24P[2] = {
    "   Sers-toi de ta t^ete, ou je le ferai !       ",
    "   Il me faut une boule de bowling...           ",
};
static s8* msgWinPL01_25P[2] = {
    "   Pas besoin d'^etre costaud                   ",
    "   pour avoir l'air d'un gros nul.              ",
};
static s8* msgWinPL01_26P[2] = {
    "   Tu ne peux pas fuir ! Un vrai                ",
    "   combattant conna^it sa vocation !            ",
};
static s8* msgWinPL01_27P[2] = {
    "   Le manque de coeur m`ene                     ",
    "   toujours `a la d*efaite !                    ",
};

static s8** msgWinAdrPL01[28] = {
    msgWinPL01_00P, msgWinPL01_01P, msgWinPL01_02P, msgWinPL01_03P, msgWinPL01_04P, msgWinPL01_05P,
    msgWinPL01_06P, msgWinPL01_07P, msgWinPL01_08P, msgWinPL01_09P, msgWinPL01_10P, msgWinPL01_11P,
    msgWinPL01_12P, msgWinPL01_13P, msgWinPL01_14P, msgWinPL01_15P, msgWinPL01_16P, msgWinPL01_17P,
    msgWinPL01_18P, msgWinPL01_19P, msgWinPL01_20P, msgWinPL01_21P, msgWinPL01_22P, msgWinPL01_23P,
    msgWinPL01_24P, msgWinPL01_25P, msgWinPL01_26P, msgWinPL01_27P,
};

static s8 msgWinCtrPL01[28] = { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2 };

MessageTable pl01win_fr_tbl = { msgWinAdrPL01, msgWinCtrPL01 };
