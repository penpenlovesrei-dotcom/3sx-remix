/**
 * @file pl12tlk_fr.c
 * Sean Pre-Fight Dialogue (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl12tlk_fr.h"
#include "common.h"

static s8* msgTlkPL12_00P[1] = { "" };
static s8* msgTlkPL12_01P[2] = {
    "  Comme convenu...                              ",
    "  C'est aujourd'hui.                            ",
};
static s8* msgTlkPL12_02P[2] = {
    "  Tes coups sp*eciaux... tes propres            ",
    "  tactiques... Tout est permis !                ",
};
static s8* msgTlkPL12_03P[2] = {
    "  Essaie de m'impressionner ! Et si tu          ",
    "  vois une ouverture, prends un round !         ",
};
static s8* msgTlkPL12_04P[1] = { "  Enfin... si tu en es capable !                " };
static s8* msgTlkPL12_05P[2] = {
    "  Ma^itre... Je ne suis plus celui              ",
    "  que j'*etais il y a un an !                   ",
};
static s8* msgTlkPL12_06P[1] = { "  Je vais vous le prouver !!                    " };

static s8** msgTalkAdrPL12[7] = {
    msgTlkPL12_00P, msgTlkPL12_01P, msgTlkPL12_02P, msgTlkPL12_03P, msgTlkPL12_04P, msgTlkPL12_05P,
    msgTlkPL12_06P,
};

static s8 msgTalkCtrPL12[7] = { 1, 2, 2, 2, 1, 2, 1 };

MessageTable pl12tlk_fr_tbl = { msgTalkAdrPL12, msgTalkCtrPL12 };
