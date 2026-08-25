/**
 * @file pl16tlk_fr.c
 * Makoto Pre-Fight Dialogue (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl16tlk_fr.h"
#include "common.h"

static s8* msgTlkPL16_00P[1] = { "" };
static s8* msgTlkPL16_01P[2] = {
    "  J'ai entendu parler de toi...                 ",
    "  Tu es Ryu, n'est-ce pas ?                     ",
};
static s8* msgTlkPL16_02P[2] = {
    "  Ce bandeau et ce karategi port*e en           ",
    "  toute saison ! Aucun doute !                  ",
};
static s8* msgTlkPL16_03P[1] = { "  Alors, accepte mon d*efi !                    " };
static s8* msgTlkPL16_04P[2] = {
    "  Hmm... Tu pratiques le karat*e...             ",
    "  Et tu sembles dou*ee...                       ",
};
static s8* msgTlkPL16_05P[2] = {
    "  Int*eressant !                                ",
    "  Montre-moi ce que tu vaux !!                  ",
};

static s8** msgTalkAdrPL16[6] = {
    msgTlkPL16_00P, msgTlkPL16_01P, msgTlkPL16_02P, msgTlkPL16_03P, msgTlkPL16_04P, msgTlkPL16_05P,
};

static s8 msgTalkCtrPL16[6] = { 1, 2, 2, 1, 2, 2 };

MessageTable pl16tlk_fr_tbl = { msgTalkAdrPL16, msgTalkCtrPL16 };
