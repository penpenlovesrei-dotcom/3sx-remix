/**
 * @file pl02tlk_fr.c
 * Ryu Pre-Fight Dialogue (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl02tlk_fr.h"
#include "common.h"

static s8* msgTlkPL02_00P[1] = { "" };
static s8* msgTlkPL02_01P[1] = { "  Tu ne t'en lasses jamais, hein ?              " };
static s8* msgTlkPL02_02P[1] = { "  Je pourrais te dire la m^eme chose...         " };
static s8* msgTlkPL02_03P[2] = {
    "  Tr`es bien, je vais faire vite et             ",
    "  simple. Pr*epare-toi `a perdre !              ",
};
static s8* msgTlkPL02_04P[2] = {
    "  Peut-^etre, mais j'ai encore le               ",
    "  meilleur palmar`es ! Tiens bon !              ",
};

static s8** msgTalkAdrPL02[5] = {
    msgTlkPL02_00P, msgTlkPL02_01P, msgTlkPL02_02P, msgTlkPL02_03P, msgTlkPL02_04P,
};

static s8 msgTalkCtrPL02[5] = { 1, 1, 1, 2, 2 };

MessageTable pl02tlk_fr_tbl = { msgTalkAdrPL02, msgTalkCtrPL02 };
