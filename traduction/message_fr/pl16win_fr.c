/**
 * @file pl16win_fr.c
 * Makoto Win Quotes (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl16win_fr.h"
#include "common.h"

static s8* msgWinPL16_00P[1] = { "" };
static s8* msgWinPL16_01P[1] = { "" };
static s8* msgWinPL16_02P[1] = { "" };
static s8* msgWinPL16_03P[1] = { "" };
static s8* msgWinPL16_04P[1] = { "" };
static s8* msgWinPL16_05P[1] = { "" };
static s8* msgWinPL16_06P[1] = { "" };
static s8* msgWinPL16_07P[1] = { "" };
static s8* msgWinPL16_08P[1] = { "" };
static s8* msgWinPL16_09P[1] = { "" };
static s8* msgWinPL16_10P[1] = { "" };
static s8* msgWinPL16_11P[1] = { "" };
static s8* msgWinPL16_12P[1] = { "" };
static s8* msgWinPL16_13P[1] = { "" };
static s8* msgWinPL16_14P[1] = { "" };
static s8* msgWinPL16_15P[1] = { "" };
static s8* msgWinPL16_16P[1] = { "" };
static s8* msgWinPL16_17P[1] = { "" };
static s8* msgWinPL16_18P[1] = { "" };
static s8* msgWinPL16_19P[1] = { "" };
static s8* msgWinPL16_20P[2] = {
    "   Tu t'en sortirais mieux si tu                ",
    "   te d*eridais un peu !                        ",
};
static s8* msgWinPL16_21P[2] = {
    "   C'*etait bien plus facile que                ",
    "   ce que je croyais !                          ",
};
static s8* msgWinPL16_22P[2] = {
    "   Tu ne t'es pas donn*e `a fond !              ",
    "   Arr^ete de te retenir !                      ",
};
static s8* msgWinPL16_23P[2] = {
    "   Il en faudra bien plus pour me               ",
    "   mettre KO ! On remet ;ca !                   ",
};
static s8* msgWinPL16_24P[2] = {
    "   ;Ca fait deux fois plus mal quand            ",
    "   on sait que c'est sa faute !                 ",
};
static s8* msgWinPL16_25P[2] = {
    "   `A quoi penses-tu quand on se bat ?          ",
    "   Je veux savoir !                             ",
};
static s8* msgWinPL16_26P[2] = {
    "   Battons-nous jusqu'`a ce qu'on soit          ",
    "   pleinement satisfaits tous les deux !        ",
};
static s8* msgWinPL16_27P[2] = {
    "   Papa, tu as cru en moi !                     ",
    "   Cette victoire est pour le dojo !            ",
};

static s8** msgWinAdrPL16[28] = {
    msgWinPL16_00P, msgWinPL16_01P, msgWinPL16_02P, msgWinPL16_03P, msgWinPL16_04P, msgWinPL16_05P,
    msgWinPL16_06P, msgWinPL16_07P, msgWinPL16_08P, msgWinPL16_09P, msgWinPL16_10P, msgWinPL16_11P,
    msgWinPL16_12P, msgWinPL16_13P, msgWinPL16_14P, msgWinPL16_15P, msgWinPL16_16P, msgWinPL16_17P,
    msgWinPL16_18P, msgWinPL16_19P, msgWinPL16_20P, msgWinPL16_21P, msgWinPL16_22P, msgWinPL16_23P,
    msgWinPL16_24P, msgWinPL16_25P, msgWinPL16_26P, msgWinPL16_27P,
};

static s8 msgWinCtrPL16[28] = { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2 };

MessageTable pl16win_fr_tbl = { msgWinAdrPL16, msgWinCtrPL16 };
