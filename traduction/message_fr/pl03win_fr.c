/**
 * @file pl03win_fr.c
 * Yun Win Quotes (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl03win_fr.h"
#include "common.h"

static s8* msgWinPL03_00P[1] = { "" };
static s8* msgWinPL03_01P[1] = { "" };
static s8* msgWinPL03_02P[1] = { "" };
static s8* msgWinPL03_03P[1] = { "" };
static s8* msgWinPL03_04P[1] = { "" };
static s8* msgWinPL03_05P[1] = { "" };
static s8* msgWinPL03_06P[1] = { "" };
static s8* msgWinPL03_07P[1] = { "" };
static s8* msgWinPL03_08P[1] = { "" };
static s8* msgWinPL03_09P[1] = { "" };
static s8* msgWinPL03_10P[1] = { "" };
static s8* msgWinPL03_11P[1] = { "" };
static s8* msgWinPL03_12P[1] = { "" };
static s8* msgWinPL03_13P[1] = { "" };
static s8* msgWinPL03_14P[1] = { "" };
static s8* msgWinPL03_15P[1] = { "" };
static s8* msgWinPL03_16P[1] = { "" };
static s8* msgWinPL03_17P[1] = { "" };
static s8* msgWinPL03_18P[1] = { "" };
static s8* msgWinPL03_19P[1] = { "" };
static s8* msgWinPL03_20P[2] = {
    "   Je vois pourquoi tu as perdu... Tu ne        ",
    "   t'es pas amus*e une seule seconde !          ",
};
static s8* msgWinPL03_21P[2] = {
    "   Mon style change, le r*esultat non.          ",
    "   Je gagne. Tu perds !                         ",
};
static s8* msgWinPL03_22P[2] = {
    "   Tu as peur de ce qui tombe du ciel,          ",
    "   maintenant ? D*esol*e !                      ",
};
static s8* msgWinPL03_23P[2] = {
    "   Je pr*ef`ere faire la f^ete que              ",
    "   faire des b^etises ! Salut !                 ",
};
static s8* msgWinPL03_24P[2] = {
    "   Tu pr*ef`eres peut-^etre m'affronter         ",
    "   `a un jeu de skate ?                         ",
};
static s8* msgWinPL03_25P[1] = { "   Radin ? Cette casquette m'a co^ut*e cher !   " };
static s8* msgWinPL03_26P[2] = {
    "   Mon skate n'est pas un brancard,             ",
    "   mais il te m`enera `a l'h^opital !           ",
};
static s8* msgWinPL03_27P[2] = {
    "   Tu ne sais pas qu'il est malpoli de          ",
    "   demander `a gagner un round ?!               ",
};

static s8** msgWinAdrPL03[28] = {
    msgWinPL03_00P, msgWinPL03_01P, msgWinPL03_02P, msgWinPL03_03P, msgWinPL03_04P, msgWinPL03_05P,
    msgWinPL03_06P, msgWinPL03_07P, msgWinPL03_08P, msgWinPL03_09P, msgWinPL03_10P, msgWinPL03_11P,
    msgWinPL03_12P, msgWinPL03_13P, msgWinPL03_14P, msgWinPL03_15P, msgWinPL03_16P, msgWinPL03_17P,
    msgWinPL03_18P, msgWinPL03_19P, msgWinPL03_20P, msgWinPL03_21P, msgWinPL03_22P, msgWinPL03_23P,
    msgWinPL03_24P, msgWinPL03_25P, msgWinPL03_26P, msgWinPL03_27P,
};

static s8 msgWinCtrPL03[28] = { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 1, 2, 2 };

MessageTable pl03win_fr_tbl = { msgWinAdrPL03, msgWinCtrPL03 };
