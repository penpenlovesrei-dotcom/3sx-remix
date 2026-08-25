/**
 * @file pl15win_fr.c
 * Chun-Li Win Quotes (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl15win_fr.h"
#include "common.h"

static s8* msgWinPL15_00P[1] = { "" };
static s8* msgWinPL15_01P[1] = { "" };
static s8* msgWinPL15_02P[1] = { "" };
static s8* msgWinPL15_03P[1] = { "" };
static s8* msgWinPL15_04P[1] = { "" };
static s8* msgWinPL15_05P[1] = { "" };
static s8* msgWinPL15_06P[1] = { "" };
static s8* msgWinPL15_07P[1] = { "" };
static s8* msgWinPL15_08P[1] = { "" };
static s8* msgWinPL15_09P[1] = { "" };
static s8* msgWinPL15_10P[1] = { "" };
static s8* msgWinPL15_11P[1] = { "" };
static s8* msgWinPL15_12P[1] = { "" };
static s8* msgWinPL15_13P[1] = { "" };
static s8* msgWinPL15_14P[1] = { "" };
static s8* msgWinPL15_15P[1] = { "" };
static s8* msgWinPL15_16P[1] = { "" };
static s8* msgWinPL15_17P[1] = { "" };
static s8* msgWinPL15_18P[1] = { "" };
static s8* msgWinPL15_19P[1] = { "" };
static s8* msgWinPL15_20P[2] = {
    "   Il y a bien longtemps que je n'avais         ",
    "   pas eu de combat loyal !                     ",
};
static s8* msgWinPL15_21P[2] = {
    "   Laissez-moi tranquille !                     ",
    "   Je me bats, je ne suis pas reporter !        ",
};
static s8* msgWinPL15_22P[2] = {
    "   Non, je n'ai jamais jet*e un seul de         ",
    "   mes bracelets. Pourquoi ?                    ",
};
static s8* msgWinPL15_23P[2] = {
    "   La puissance ne sert `a rien sans            ",
    "   technique ni vitesse !                       ",
};
static s8* msgWinPL15_24P[2] = {
    "   R*efl*echis avant d'agir et tu               ",
    "   n'auras plus rien `a regretter.              ",
};
static s8* msgWinPL15_25P[2] = {
    "   Tu n'as pas vu mon meilleur !                ",
    "   Laisse-moi te le montrer !                   ",
};
static s8* msgWinPL15_26P[2] = {
    "   Tu serais redoutable avec une                ",
    "   meilleure raison de te battre !              ",
};
static s8* msgWinPL15_27P[2] = {
    "   Suis-je toujours la femme la plus            ",
    "   forte du monde ? Dis-le-moi !                ",
};

static s8** msgWinAdrPL15[28] = {
    msgWinPL15_00P, msgWinPL15_01P, msgWinPL15_02P, msgWinPL15_03P, msgWinPL15_04P, msgWinPL15_05P,
    msgWinPL15_06P, msgWinPL15_07P, msgWinPL15_08P, msgWinPL15_09P, msgWinPL15_10P, msgWinPL15_11P,
    msgWinPL15_12P, msgWinPL15_13P, msgWinPL15_14P, msgWinPL15_15P, msgWinPL15_16P, msgWinPL15_17P,
    msgWinPL15_18P, msgWinPL15_19P, msgWinPL15_20P, msgWinPL15_21P, msgWinPL15_22P, msgWinPL15_23P,
    msgWinPL15_24P, msgWinPL15_25P, msgWinPL15_26P, msgWinPL15_27P,
};

static s8 msgWinCtrPL15[28] = { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2 };

MessageTable pl15win_fr_tbl = { msgWinAdrPL15, msgWinCtrPL15 };
