/**
 * @file pl11tlk_fr.c
 * Ken Pre-Fight Dialogue (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl11tlk_fr.h"
#include "common.h"

static s8* msgTlkPL11_00P[1] = { "" };
static s8* msgTlkPL11_01P[1] = { "  Tu n'es pas ce que j'imaginais...             " };
static s8* msgTlkPL11_02P[2] = {
    "  Mais tu as bien la t^ete                      ",
    "  d'un combattant !                             ",
};
static s8* msgTlkPL11_03P[2] = {
    "  Tiens-toi bien... Mon destin est de           ",
    "  r*egner sur le si`ecle nouveau.               ",
};
static s8* msgTlkPL11_04P[2] = {
    "  Remercie-moi de te prendre                    ",
    "  pour distraction !                            ",
};
static s8* msgTlkPL11_05P[2] = {
    "  Continue comme ;ca et je ferai bien           ",
    "  plus que te distraire !                       ",
};

static s8** msgTalkAdrPL11[6] = {
    msgTlkPL11_00P, msgTlkPL11_01P, msgTlkPL11_02P, msgTlkPL11_03P, msgTlkPL11_04P, msgTlkPL11_05P,
};

static s8 msgTalkCtrPL11[6] = { 1, 1, 2, 2, 2, 2 };

MessageTable pl11tlk_fr_tbl = { msgTalkAdrPL11, msgTalkCtrPL11 };
