/**
 * @file pl13win_fr.c
 * Urien Win Quotes (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl13win_fr.h"
#include "common.h"

static s8* msgWinPL13_00P[1] = { "" };
static s8* msgWinPL13_01P[1] = { "" };
static s8* msgWinPL13_02P[1] = { "" };
static s8* msgWinPL13_03P[1] = { "" };
static s8* msgWinPL13_04P[1] = { "" };
static s8* msgWinPL13_05P[1] = { "" };
static s8* msgWinPL13_06P[1] = { "" };
static s8* msgWinPL13_07P[1] = { "" };
static s8* msgWinPL13_08P[1] = { "" };
static s8* msgWinPL13_09P[1] = { "" };
static s8* msgWinPL13_10P[1] = { "" };
static s8* msgWinPL13_11P[1] = { "" };
static s8* msgWinPL13_12P[1] = { "" };
static s8* msgWinPL13_13P[1] = { "" };
static s8* msgWinPL13_14P[1] = { "" };
static s8* msgWinPL13_15P[1] = { "" };
static s8* msgWinPL13_16P[1] = { "" };
static s8* msgWinPL13_17P[1] = { "" };
static s8* msgWinPL13_18P[1] = { "" };
static s8* msgWinPL13_19P[1] = { "" };
static s8* msgWinPL13_20P[2] = {
    "   `A quel point es-tu mauvais ? Laisse-moi     ",
    "   compter tes plaies ! 1, 2, 3...              ",
};
static s8* msgWinPL13_21P[2] = {
    "   Regarde ! Tes cellules t'ont                 ",
    "   trahi pour me servir !                       ",
};
static s8* msgWinPL13_22P[2] = {
    "   C'est cela... Agenouille-toi !               ",
    "   La vue te pla^it, d'en bas ?!                ",
};
static s8* msgWinPL13_23P[2] = {
    "   Reste couch*e autant que tu veux.            ",
    "   Je me suis assez amus*e.                     ",
};
static s8* msgWinPL13_24P[2] = {
    "   Tu n'es m^eme pas digne de servir            ",
    "   mes desseins ! Disparais !                   ",
};
static s8* msgWinPL13_25P[2] = {
    "   Te marteler est satisfaisant,                ",
    "   mais il me faut davantage...                 ",
};
static s8* msgWinPL13_26P[2] = {
    "   Tes fluides inf*erieurs souillent            ",
    "   le sol ! Nettoie-moi ;ca !                   ",
};
static s8* msgWinPL13_27P[2] = {
    "   Comment oses-tu refuser de t'incliner        ",
    "   devant un ^etre sup*erieur ?                 ",
};

static s8** msgWinAdrPL13[28] = {
    msgWinPL13_00P, msgWinPL13_01P, msgWinPL13_02P, msgWinPL13_03P, msgWinPL13_04P, msgWinPL13_05P,
    msgWinPL13_06P, msgWinPL13_07P, msgWinPL13_08P, msgWinPL13_09P, msgWinPL13_10P, msgWinPL13_11P,
    msgWinPL13_12P, msgWinPL13_13P, msgWinPL13_14P, msgWinPL13_15P, msgWinPL13_16P, msgWinPL13_17P,
    msgWinPL13_18P, msgWinPL13_19P, msgWinPL13_20P, msgWinPL13_21P, msgWinPL13_22P, msgWinPL13_23P,
    msgWinPL13_24P, msgWinPL13_25P, msgWinPL13_26P, msgWinPL13_27P,
};

static s8 msgWinCtrPL13[28] = { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2 };

MessageTable pl13win_fr_tbl = { msgWinAdrPL13, msgWinCtrPL13 };
