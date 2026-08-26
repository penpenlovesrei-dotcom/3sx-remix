/**
 * @file pl09win_fr.c
 * Oro Win Quotes (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl09win_fr.h"
#include "common.h"

static s8* msgWinPL09_00P[1] = { "" };
static s8* msgWinPL09_01P[1] = { "" };
static s8* msgWinPL09_02P[1] = { "" };
static s8* msgWinPL09_03P[1] = { "" };
static s8* msgWinPL09_04P[1] = { "" };
static s8* msgWinPL09_05P[1] = { "" };
static s8* msgWinPL09_06P[1] = { "" };
static s8* msgWinPL09_07P[1] = { "" };
static s8* msgWinPL09_08P[1] = { "" };
static s8* msgWinPL09_09P[1] = { "" };
static s8* msgWinPL09_10P[1] = { "" };
static s8* msgWinPL09_11P[1] = { "" };
static s8* msgWinPL09_12P[1] = { "" };
static s8* msgWinPL09_13P[1] = { "" };
static s8* msgWinPL09_14P[1] = { "" };
static s8* msgWinPL09_15P[1] = { "" };
static s8* msgWinPL09_16P[1] = { "" };
static s8* msgWinPL09_17P[1] = { "" };
static s8* msgWinPL09_18P[1] = { "" };
static s8* msgWinPL09_19P[1] = { "" };
static s8* msgWinPL09_20P[2] = {
    "   Tes coups sont mortels... Ils                ",
    "   pourraient me tuer d'ennui !                 ",
};
static s8* msgWinPL09_21P[2] = {
    "   Tu n'as aucun sens de la d*efense ?          ",
    "   Ou tu aimes juste avoir mal ?                ",
};
static s8* msgWinPL09_22P[2] = {
    "   Si on rentrait tout de suite, qui            ",
    "   s'en soucierait ? Personne.                  ",
};
static s8* msgWinPL09_23P[2] = {
    "   Continue comme ;ca et tu conna^itras         ",
    "   l'horreur de la douleur !                    ",
};
static s8* msgWinPL09_24P[2] = {
    "   Tu veux rencontrer mes animaux ?             ",
    "   Ou tu es trop amoch*e ?                      ",
};
static s8* msgWinPL09_25P[2] = {
    "   Si la col`ere t'aveugle, comment             ",
    "   esp`eres-tu frapper juste ?                  ",
};
static s8* msgWinPL09_26P[2] = {
    "   Si je continuais `a t'affronter,             ",
    "   je finirais par r*egresser !                 ",
};
static s8* msgWinPL09_27P[2] = {
    "   Je m'ennuie ! Je me sens `a l'*etroit !      ",
    "   Hein ? Toi aussi ?                           ",
};

static s8** msgWinAdrPL09[28] = {
    msgWinPL09_00P, msgWinPL09_01P, msgWinPL09_02P, msgWinPL09_03P, msgWinPL09_04P, msgWinPL09_05P,
    msgWinPL09_06P, msgWinPL09_07P, msgWinPL09_08P, msgWinPL09_09P, msgWinPL09_10P, msgWinPL09_11P,
    msgWinPL09_12P, msgWinPL09_13P, msgWinPL09_14P, msgWinPL09_15P, msgWinPL09_16P, msgWinPL09_17P,
    msgWinPL09_18P, msgWinPL09_19P, msgWinPL09_20P, msgWinPL09_21P, msgWinPL09_22P, msgWinPL09_23P,
    msgWinPL09_24P, msgWinPL09_25P, msgWinPL09_26P, msgWinPL09_27P,
};

static s8 msgWinCtrPL09[28] = { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2 };

MessageTable pl09win_fr_tbl = { msgWinAdrPL09, msgWinCtrPL09 };
