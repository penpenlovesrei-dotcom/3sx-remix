/**
 * @file pl06tlk_fr.c
 * Hugo Pre-Fight Dialogue (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl06tlk_fr.h"
#include "common.h"

static s8* msgTlkPL06_00P[1] = { "" };
static s8* msgTlkPL06_01P[2] = {
    "  Tu dois ^etre celui dont                      ",
    "  Poison m'a parl*e.                            ",
};
static s8* msgTlkPL06_02P[2] = {
    "  On recrute ceux qui peuvent devenir           ",
    "  de grands catcheurs.                          ",
};
static s8* msgTlkPL06_03P[2] = {
    "  Passons un march*e. Promets-moi de            ",
    "  nous rejoindre si tu perds !                  ",
};
static s8* msgTlkPL06_04P[2] = {
    "  D'accord... Le catch a peut-^etre             ",
    "  quelque chose `a m'apprendre.                 ",
};
static s8* msgTlkPL06_05P[2] = {
    "  Mais je ne perdrai pas ! Je vais te           ",
    "  montrer ce qu'est la vraie force !            ",
};

static s8** msgTalkAdrPL06[6] = {
    msgTlkPL06_00P, msgTlkPL06_01P, msgTlkPL06_02P, msgTlkPL06_03P, msgTlkPL06_04P, msgTlkPL06_05P,
};

static s8 msgTalkCtrPL06[6] = { 1, 2, 2, 2, 2, 2 };

MessageTable pl06tlk_fr_tbl = { msgTalkAdrPL06, msgTalkCtrPL06 };
