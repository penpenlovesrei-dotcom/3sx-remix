/**
 * @file pl18win_fr.c
 * Twelve Win Quotes (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl18win_fr.h"
#include "common.h"

static s8* msgWinPL18_00P[1] = { "" };
static s8* msgWinPL18_01P[1] = { "" };
static s8* msgWinPL18_02P[1] = { "" };
static s8* msgWinPL18_03P[1] = { "" };
static s8* msgWinPL18_04P[1] = { "" };
static s8* msgWinPL18_05P[1] = { "" };
static s8* msgWinPL18_06P[1] = { "" };
static s8* msgWinPL18_07P[1] = { "" };
static s8* msgWinPL18_08P[1] = { "" };
static s8* msgWinPL18_09P[1] = { "" };
static s8* msgWinPL18_10P[1] = { "" };
static s8* msgWinPL18_11P[1] = { "" };
static s8* msgWinPL18_12P[1] = { "" };
static s8* msgWinPL18_13P[1] = { "" };
static s8* msgWinPL18_14P[1] = { "" };
static s8* msgWinPL18_15P[1] = { "" };
static s8* msgWinPL18_16P[1] = { "" };
static s8* msgWinPL18_17P[1] = { "" };
static s8* msgWinPL18_18P[1] = { "" };
static s8* msgWinPL18_19P[1] = { "" };
static s8* msgWinPL18_20P[1] = { "   01101.01111.10010.10100                      " };
static s8* msgWinPL18_21P[1] = { "   10100.10101.00101.10010                      " };
static s8* msgWinPL18_22P[1] = { "   01101.00001.01100                            " };
static s8* msgWinPL18_23P[1] = { "   00110.01001.01110.01001.10010                " };
static s8* msgWinPL18_24P[1] = { "   01011.01111                                  " };
static s8* msgWinPL18_25P[1] = { "   01100.00001.00110.01001.01110                " };
static s8* msgWinPL18_26P[1] = { "   10100.10111.00101.01100.10110.00101          " };
static s8* msgWinPL18_27P[1] = { "   00110.00001.00011.01001.01100.00101          " };

static s8** msgWinAdrPL18[28] = {
    msgWinPL18_00P, msgWinPL18_01P, msgWinPL18_02P, msgWinPL18_03P, msgWinPL18_04P, msgWinPL18_05P,
    msgWinPL18_06P, msgWinPL18_07P, msgWinPL18_08P, msgWinPL18_09P, msgWinPL18_10P, msgWinPL18_11P,
    msgWinPL18_12P, msgWinPL18_13P, msgWinPL18_14P, msgWinPL18_15P, msgWinPL18_16P, msgWinPL18_17P,
    msgWinPL18_18P, msgWinPL18_19P, msgWinPL18_20P, msgWinPL18_21P, msgWinPL18_22P, msgWinPL18_23P,
    msgWinPL18_24P, msgWinPL18_25P, msgWinPL18_26P, msgWinPL18_27P,
};

static s8 msgWinCtrPL18[28] = { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1 };

MessageTable pl18win_fr_tbl = { msgWinAdrPL18, msgWinCtrPL18 };
