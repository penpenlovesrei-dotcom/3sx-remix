/**
 * @file pl10tlk_fr.c
 * Yang Pre-Fight Dialogue (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl10tlk_fr.h"
#include "common.h"

static s8* msgTlkPL10_00P[1] = { "" };
static s8* msgTlkPL10_01P[2] = {
    "  ...Pourquoi est-ce que ;ca compte             ",
    "  autant pour toi ?                             ",
};
static s8* msgTlkPL10_02P[2] = {
    "  C'est une perte de temps de                   ",
    "  savoir qui est le plus fort.                  ",
};
static s8* msgTlkPL10_03P[1] = { "  Je sais. C'est juste que...                   " };
static s8* msgTlkPL10_04P[2] = {
    "  J'aimerais que tu voies les progr`es          ",
    "  que j'ai faits ces derni`eres semaines.       ",
};
static s8* msgTlkPL10_05P[2] = {
    "  Tr`es bien.                                   ",
    "  Je n'ai pas le choix, j'accepte...            ",
};
static s8* msgTlkPL10_06P[2] = {
    "  Je vais te montrer quels murs                 ",
    "  barreront toujours ta route !                 ",
};

static s8** msgTalkAdrPL10[7] = {
    msgTlkPL10_00P, msgTlkPL10_01P, msgTlkPL10_02P, msgTlkPL10_03P, msgTlkPL10_04P, msgTlkPL10_05P,
    msgTlkPL10_06P,
};

static s8 msgTalkCtrPL10[7] = { 1, 2, 2, 1, 2, 2, 2 };

MessageTable pl10tlk_fr_tbl = { msgTalkAdrPL10, msgTalkCtrPL10 };
