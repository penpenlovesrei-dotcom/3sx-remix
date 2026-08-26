/**
 * @file pl19tlk_fr.c
 * Remy Pre-Fight Dialogue (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl19tlk_fr.h"
#include "common.h"

static s8* msgTlkPL19_00P[1] = { "" };
static s8* msgTlkPL19_01P[2] = {
    "  R*eponds-moi...                               ",
    "  Pourquoi te bats-tu ?                         ",
};
static s8* msgTlkPL19_02P[2] = {
    "  Je ne sais pas... Je me battais bien          ",
    "  avant d'en conna^itre la raison.              ",
};
static s8* msgTlkPL19_03P[2] = {
    "  Cet *ego=isme fait des victimes, tue          ",
    "  l'amour et engendre la haine !                ",
};
static s8* msgTlkPL19_04P[2] = {
    "  Je ne leur pardonnerai jamais ! Ceux          ",
    "  qui se disent \"guerriers\"...                  ",
};
static s8* msgTlkPL19_05P[2] = {
    "  Comme mon p`ere, un homme qui a               ",
    "  d*esert*e et trahi sa famille !               ",
};
static s8* msgTlkPL19_06P[2] = {
    "  Et alors ? Si tu as besoin d'un               ",
    "  psy, va voir ailleurs !                       ",
};
static s8* msgTlkPL19_07P[2] = {
    "  Mais si c'est de la douleur que tu            ",
    "  veux, j'en ai en r*eserve !                   ",
};

static s8** msgTalkAdrPL19[8] = {
    msgTlkPL19_00P, msgTlkPL19_01P, msgTlkPL19_02P, msgTlkPL19_03P, msgTlkPL19_04P, msgTlkPL19_05P,
    msgTlkPL19_06P, msgTlkPL19_07P,
};

static s8 msgTalkCtrPL19[8] = { 1, 2, 2, 2, 2, 2, 2, 2 };

MessageTable pl19tlk_fr_tbl = { msgTalkAdrPL19, msgTalkCtrPL19 };
