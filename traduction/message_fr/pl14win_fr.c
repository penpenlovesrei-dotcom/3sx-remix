/**
 * @file pl14win_fr.c
 * Akuma Win Quotes (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl14win_fr.h"
#include "common.h"

static s8* msgWinPL14_00P[1] = { "" };
static s8* msgWinPL14_01P[1] = { "" };
static s8* msgWinPL14_02P[1] = { "" };
static s8* msgWinPL14_03P[1] = { "" };
static s8* msgWinPL14_04P[1] = { "" };
static s8* msgWinPL14_05P[1] = { "" };
static s8* msgWinPL14_06P[1] = { "" };
static s8* msgWinPL14_07P[1] = { "" };
static s8* msgWinPL14_08P[1] = { "" };
static s8* msgWinPL14_09P[1] = { "" };
static s8* msgWinPL14_10P[1] = { "" };
static s8* msgWinPL14_11P[1] = { "" };
static s8* msgWinPL14_12P[1] = { "" };
static s8* msgWinPL14_13P[1] = { "" };
static s8* msgWinPL14_14P[1] = { "" };
static s8* msgWinPL14_15P[1] = { "" };
static s8* msgWinPL14_16P[1] = { "" };
static s8* msgWinPL14_17P[1] = { "" };
static s8* msgWinPL14_18P[1] = { "" };
static s8* msgWinPL14_19P[1] = { "" };
static s8* msgWinPL14_20P[1] = { "   Mon poing n'a pas d'*egal !                  " };
static s8* msgWinPL14_21P[1] = { "   La perfection, c'est l'an*eantissement !     " };
static s8* msgWinPL14_22P[2] = {
    "   Ton corps a pris sa vraie forme              ",
    "   quand mes poings l'ont d*echir*e !           ",
};
static s8* msgWinPL14_23P[2] = {
    "   La faiblesse est une maladie...              ",
    "   Je suis le rem`ede !                         ",
};
static s8* msgWinPL14_24P[2] = {
    "   Ceux qui n'en sont pas dignes                ",
    "   doivent ^etre ray*es du monde.               ",
};
static s8* msgWinPL14_25P[2] = {
    "   Tu as rempli ton r^ole en me                 ",
    "   laissant y mettre fin !                      ",
};
static s8* msgWinPL14_26P[2] = {
    "   Coquille faible, ^ame faible. Les            ",
    "   s*eparer fut un jeu d'enfant...              ",
};
static s8* msgWinPL14_27P[2] = {
    "   Faire preuve de piti*e, c'est                ",
    "   prouver son imperfection !                   ",
};

static s8** msgWinAdrPL14[28] = {
    msgWinPL14_00P, msgWinPL14_01P, msgWinPL14_02P, msgWinPL14_03P, msgWinPL14_04P, msgWinPL14_05P,
    msgWinPL14_06P, msgWinPL14_07P, msgWinPL14_08P, msgWinPL14_09P, msgWinPL14_10P, msgWinPL14_11P,
    msgWinPL14_12P, msgWinPL14_13P, msgWinPL14_14P, msgWinPL14_15P, msgWinPL14_16P, msgWinPL14_17P,
    msgWinPL14_18P, msgWinPL14_19P, msgWinPL14_20P, msgWinPL14_21P, msgWinPL14_22P, msgWinPL14_23P,
    msgWinPL14_24P, msgWinPL14_25P, msgWinPL14_26P, msgWinPL14_27P,
};

static s8 msgWinCtrPL14[28] = { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2 };

MessageTable pl14win_fr_tbl = { msgWinAdrPL14, msgWinCtrPL14 };
