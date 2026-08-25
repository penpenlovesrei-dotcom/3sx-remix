/**
 * @file pl13tlk_fr.c
 * Urien Pre-Fight Dialogue (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl13tlk_fr.h"
#include "common.h"

static s8* msgTlkPL13_00P[1] = { "" };
static s8* msgTlkPL13_01P[2] = {
    "  Je comprends ta jalousie. Un gouffre          ",
    "  s*epare les hommes d'un dieu.                 ",
};
static s8* msgTlkPL13_02P[2] = {
    "  Tu ne peux pas me pardonner                   ",
    "  parce que tu ne peux pas me nier.             ",
};
static s8* msgTlkPL13_03P[2] = {
    "  Laisse-moi t'offrir la mort, en               ",
    "  guise de piti*e fraternelle !                 ",
};
static s8* msgTlkPL13_04P[2] = {
    "  Quand je regarde le pass*e,                   ",
    "  je vois le d*eshonneur et la haine.           ",
};
static s8* msgTlkPL13_05P[2] = {
    "  Quand je regarde l'avenir,                    ",
    "  je suis libre de toute souillure.             ",
};
static s8* msgTlkPL13_06P[2] = {
    "  Quelle splendeur...                           ",
    "  Un monde sans toi !                           ",
};

static s8** msgTalkAdrPL13[7] = {
    msgTlkPL13_00P, msgTlkPL13_01P, msgTlkPL13_02P, msgTlkPL13_03P, msgTlkPL13_04P, msgTlkPL13_05P,
    msgTlkPL13_06P,
};

static s8 msgTalkCtrPL13[7] = { 1, 2, 2, 2, 2, 2, 2 };

MessageTable pl13tlk_fr_tbl = { msgTalkAdrPL13, msgTalkCtrPL13 };
