/**
 * @file pl08tlk_fr.c
 * Elena Pre-Fight Dialogue (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl08tlk_fr.h"
#include "common.h"

static s8* msgTlkPL08_00P[1] = { "" };
static s8* msgTlkPL08_01P[2] = {
    "  Qu'est-ce qui te prend ?! Arr^ete de          ",
    "  sourire comme ;ca ! C'est glauque !           ",
};
static s8* msgTlkPL08_02P[2] = {
    "  Je viens pour un vrai combat ! Tu vas         ",
    "  le payer si tu te moques de moi !             ",
};
static s8* msgTlkPL08_03P[1] = { "  Je veux juste ^etre ton amie !                " };
static s8* msgTlkPL08_04P[2] = {
    "  C'est pour ;ca qu'on se bat !                 ",
    "  Alors profitons du combat !                   ",
};
static s8* msgTlkPL08_05P[2] = {
    "  Amie ?! Je crois que je ne te                 ",
    "  comprendrai jamais.                           ",
};

static s8** msgTalkAdrPL08[6] = {
    msgTlkPL08_00P, msgTlkPL08_01P, msgTlkPL08_02P, msgTlkPL08_03P, msgTlkPL08_04P, msgTlkPL08_05P,
};

static s8 msgTalkCtrPL08[6] = { 1, 2, 2, 1, 2, 2 };

MessageTable pl08tlk_fr_tbl = { msgTalkAdrPL08, msgTalkCtrPL08 };
