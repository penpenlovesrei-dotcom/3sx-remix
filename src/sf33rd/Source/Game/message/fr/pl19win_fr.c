/**
 * @file pl19win_fr.c
 * Remy Win Quotes (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl19win_fr.h"
#include "common.h"

static s8* msgWinPL19_00P[1] = { "" };
static s8* msgWinPL19_01P[1] = { "" };
static s8* msgWinPL19_02P[1] = { "" };
static s8* msgWinPL19_03P[1] = { "" };
static s8* msgWinPL19_04P[1] = { "" };
static s8* msgWinPL19_05P[1] = { "" };
static s8* msgWinPL19_06P[1] = { "" };
static s8* msgWinPL19_07P[1] = { "" };
static s8* msgWinPL19_08P[1] = { "" };
static s8* msgWinPL19_09P[1] = { "" };
static s8* msgWinPL19_10P[1] = { "" };
static s8* msgWinPL19_11P[1] = { "" };
static s8* msgWinPL19_12P[1] = { "" };
static s8* msgWinPL19_13P[1] = { "" };
static s8* msgWinPL19_14P[1] = { "" };
static s8* msgWinPL19_15P[1] = { "" };
static s8* msgWinPL19_16P[1] = { "" };
static s8* msgWinPL19_17P[1] = { "" };
static s8* msgWinPL19_18P[1] = { "" };
static s8* msgWinPL19_19P[1] = { "" };
static s8* msgWinPL19_20P[2] = {
    "   La victoire, la gloire, l'honneur...         ",
    "   Rien de tout cela ne m'*emeut.               ",
};
static s8* msgWinPL19_21P[2] = {
    "   Dans la mort, tu trouveras peut-^etre        ",
    "   les r*eponses que tu cherches.               ",
};
static s8* msgWinPL19_22P[2] = {
    "   Je n'ai pas l'intention de te                ",
    "   tabasser encore. Va-t'en...                  ",
};
static s8* msgWinPL19_23P[1] = { "   Qu'est-ce que je fais ici, au fond ?         " };
static s8* msgWinPL19_24P[2] = {
    "   La douleur est un pi`etre substitut          ",
    "   `a une jauge de vie !                        ",
};
static s8* msgWinPL19_25P[2] = {
    "   Tu ne vois pas que le chemin que tu          ",
    "   prends ne m`ene nulle part ?!                ",
};
static s8* msgWinPL19_26P[2] = {
    "   Reste `a terre. Ou tu veux que               ",
    "   je te fasse encore mal ?                     ",
};
static s8* msgWinPL19_27P[2] = {
    "   Ta cause m'int*eresse, mais je ne            ",
    "   pourrai jamais y adh*erer.                   ",
};

static s8** msgWinAdrPL19[28] = {
    msgWinPL19_00P, msgWinPL19_01P, msgWinPL19_02P, msgWinPL19_03P, msgWinPL19_04P, msgWinPL19_05P,
    msgWinPL19_06P, msgWinPL19_07P, msgWinPL19_08P, msgWinPL19_09P, msgWinPL19_10P, msgWinPL19_11P,
    msgWinPL19_12P, msgWinPL19_13P, msgWinPL19_14P, msgWinPL19_15P, msgWinPL19_16P, msgWinPL19_17P,
    msgWinPL19_18P, msgWinPL19_19P, msgWinPL19_20P, msgWinPL19_21P, msgWinPL19_22P, msgWinPL19_23P,
    msgWinPL19_24P, msgWinPL19_25P, msgWinPL19_26P, msgWinPL19_27P,
};

static s8 msgWinCtrPL19[28] = { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 1, 2, 2, 2, 2 };

MessageTable pl19win_fr_tbl = { msgWinAdrPL19, msgWinCtrPL19 };
