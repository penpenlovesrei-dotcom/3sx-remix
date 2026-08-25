/**
 * @file pl18tlk_fr.c
 * Twelve Pre-Fight Dialogue (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl18tlk_fr.h"
#include "common.h"

static s8* msgTlkPL18_00P[1] = { "" };
static s8* msgTlkPL18_01P[2] = {
    "  Pourquoi ?! Pourquoi ne pouvez-vous           ",
    "  pas me laisser tranquille ?!                  ",
};
static s8* msgTlkPL18_02P[2] = {
    "  Je ne suis qu'un rat*e, non ?!                ",
    "  Je n'ai rien que vous vouliez !               ",
};
static s8* msgTlkPL18_03P[2] = {
    "  Ton corps regorge d'informations              ",
    "  confidentielles et dangereuses.               ",
};
static s8* msgTlkPL18_04P[2] = {
    "  Le monde ne doit jamais apprendre             ",
    "  que tu existes.                               ",
};
static s8* msgTlkPL18_05P[2] = {
    "  C'est `a chacun de d*ecider s'il              ",
    "  doit exister ou non !                         ",
};

static s8** msgTalkAdrPL18[6] = {
    msgTlkPL18_00P, msgTlkPL18_01P, msgTlkPL18_02P, msgTlkPL18_03P, msgTlkPL18_04P, msgTlkPL18_05P,
};

static s8 msgTalkCtrPL18[6] = { 1, 2, 2, 2, 2, 2 };

MessageTable pl18tlk_fr_tbl = { msgTalkAdrPL18, msgTalkCtrPL18 };
