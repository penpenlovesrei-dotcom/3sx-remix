/**
 * @file pl01tlk_fr.c
 * Alex Pre-Fight Dialogue (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl01tlk_fr.h"
#include "common.h"

static s8* msgTlkPL01_00P[1] = { "" };
static s8* msgTlkPL01_01P[2] = {
    "  Un karategi et un bandeau...                  ",
    "  Tu dois ^etre Ryu.                            ",
};
static s8* msgTlkPL01_02P[2] = {
    "  On m'a beaucoup parl*e de toi !               ",
    "  Je vais v*erifier ces rumeurs.                ",
};
static s8* msgTlkPL01_03P[2] = {
    "  Hmm... Je vois la puissance                   ",
    "  dans ton regard...                            ",
};
static s8* msgTlkPL01_04P[2] = {
    "  Ne te retiens pas !                           ",
    "  Montre-moi tout ce que tu as !                ",
};

static s8** msgTalkAdrPL01[5] = {
    msgTlkPL01_00P, msgTlkPL01_01P, msgTlkPL01_02P, msgTlkPL01_03P, msgTlkPL01_04P,
};

static s8 msgTalkCtrPL01[5] = { 1, 2, 2, 2, 2 };

MessageTable pl01tlk_fr_tbl = { msgTalkAdrPL01, msgTalkCtrPL01 };
