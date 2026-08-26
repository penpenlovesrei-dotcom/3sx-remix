/**
 * @file pl05tlk_fr.c
 * Necro Pre-Fight Dialogue (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl05tlk_fr.h"
#include "common.h"

static s8* msgTlkPL05_00P[1] = { "" };
static s8* msgTlkPL05_01P[2] = {
    "  ;Ca suffit ! Il est temps de                  ",
    "  montrer ton vrai visage !                     ",
};
static s8* msgTlkPL05_02P[2] = {
    "  C'est clair ! C'est Gill qui                  ",
    "  t'envoie, pas vrai ?!                         ",
};
static s8* msgTlkPL05_03P[1] = { "" };
static s8* msgTlkPL05_04P[2] = {
    "  Je ne perdrai pas contre un mod`ele           ",
    "  de s*erie, m^eme \"parfait\" !                  ",
};
static s8* msgTlkPL05_05P[2] = {
    "  Je mettrai ce qui reste de toi dans           ",
    "  un carton que j'enverrai `a Gill !            ",
};

static s8** msgTalkAdrPL05[6] = {
    msgTlkPL05_00P, msgTlkPL05_01P, msgTlkPL05_02P, msgTlkPL05_03P, msgTlkPL05_04P, msgTlkPL05_05P,
};

static s8 msgTalkCtrPL05[6] = { 1, 2, 2, 1, 2, 2 };

MessageTable pl05tlk_fr_tbl = { msgTalkAdrPL05, msgTalkCtrPL05 };
