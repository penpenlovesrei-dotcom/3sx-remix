/**
 * @file pl15tlk_fr.c
 * Chun-Li Pre-Fight Dialogue (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl15tlk_fr.h"
#include "common.h"

static s8* msgTlkPL15_00P[1] = { "" };
static s8* msgTlkPL15_01P[2] = {
    "  J'ignore quel est                             ",
    "  ton stratag`eme...                            ",
};
static s8* msgTlkPL15_02P[2] = {
    "  Mais je ne te laisserai pas                   ",
    "  t'en prendre `a des enfants !                 ",
};
static s8* msgTlkPL15_03P[1] = { "  O`u est cette petite ?                        " };
static s8* msgTlkPL15_04P[2] = {
    "  Tu me d*eranges pour si peu ?                 ",
    "  Il faut ^etre bien sotte !                    ",
};
static s8* msgTlkPL15_05P[2] = {
    "  Je te rendrai la petite, mais tu              ",
    "  devras me divertir en retour.                 ",
};
static s8* msgTlkPL15_06P[2] = {
    "  On dit que tes jambes l*egendaires            ",
    "  ont d*etruit \"cette organisation\".            ",
};
static s8* msgTlkPL15_07P[2] = {
    "  Je vais v*erifier moi-m^eme si les            ",
    "  rumeurs `a ton sujet sont vraies...           ",
};

static s8** msgTalkAdrPL15[8] = {
    msgTlkPL15_00P, msgTlkPL15_01P, msgTlkPL15_02P, msgTlkPL15_03P, msgTlkPL15_04P, msgTlkPL15_05P,
    msgTlkPL15_06P, msgTlkPL15_07P,
};

static s8 msgTalkCtrPL15[8] = { 1, 2, 2, 1, 2, 2, 2, 2 };

MessageTable pl15tlk_fr_tbl = { msgTalkAdrPL15, msgTalkCtrPL15 };
