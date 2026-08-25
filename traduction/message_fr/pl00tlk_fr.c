/**
 * @file pl00tlk_fr.c
 * Gill Pre-Fight Dialogue (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl00tlk_fr.h"
#include "common.h"

static s8* msgTlkPL00_00P[1] = { "" };
static s8* msgTlkPL00_01P[1] = { "  Je t'attendais, Alex.                         " };
static s8* msgTlkPL00_02P[2] = {
    "  D`es notre premi`ere rencontre, j'ai su       ",
    "  que nos destins *etaient li*es...             ",
};
static s8* msgTlkPL00_03P[2] = {
    "  Je savais que tu viendrais me                 ",
    "  chercher pour conna^itre la v*erit*e...       ",
};
static s8* msgTlkPL00_04P[2] = {
    "  Comment ;ca, tu savais que je                 ",
    "  viendrais ici... ?                            ",
};
static s8* msgTlkPL00_05P[2] = {
    "  Tes visions ne m'impressionnent pas.          ",
    "  Je veux juste te d*emolir !!                  ",
};
static s8* msgTlkPL00_06P[2] = {
    "  Je sais que je trouverai ce que je            ",
    "  cherche une fois que je t'aurai vaincu.       ",
};
static s8* msgTlkPL00_07P[2] = {
    "  Je savais que tu dirais ;ca...                ",
    "  Ha ha ha !                                    ",
};
static s8* msgTlkPL00_08P[1] = { "  Embrassons notre destin !!                    " };

static s8** msgTalkAdrPL00[9] = {
    msgTlkPL00_00P, msgTlkPL00_01P, msgTlkPL00_02P, msgTlkPL00_03P, msgTlkPL00_04P, msgTlkPL00_05P,
    msgTlkPL00_06P, msgTlkPL00_07P, msgTlkPL00_08P,
};

static s8 msgTalkCtrPL00[9] = { 1, 1, 2, 2, 2, 2, 2, 2, 1 };

MessageTable pl00tlk_fr_tbl = { msgTalkAdrPL00, msgTalkCtrPL00 };
