/**
 * @file pl04tlk_fr.c
 * Dudley Pre-Fight Dialogue (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl04tlk_fr.h"
#include "common.h"

static s8* msgTlkPL04_00P[1] = { "" };
static s8* msgTlkPL04_01P[2] = {
    "  Vous ^etes donc ce fameux                     ",
    "  combattant samoura=i ?                        ",
};
static s8* msgTlkPL04_02P[2] = {
    "  Quelle co=incidence ! Moi aussi,              ",
    "  je vous cherchais !                           ",
};
static s8* msgTlkPL04_03P[2] = {
    "  J'aimerais affronter le boxeur                ",
    "  num*ero 1 d'Angleterre !                      ",
};
static s8* msgTlkPL04_04P[2] = {
    "  Bien parl*e ! Vous avez les mani`eres         ",
    "  d'un gentleman et une force rare !            ",
};
static s8* msgTlkPL04_05P[2] = {
    "  Ce sera fort plaisant !                       ",
    "  N'^etes-vous pas d'accord ?                   ",
};

static s8** msgTalkAdrPL04[6] = {
    msgTlkPL04_00P, msgTlkPL04_01P, msgTlkPL04_02P, msgTlkPL04_03P, msgTlkPL04_04P, msgTlkPL04_05P,
};

static s8 msgTalkCtrPL04[6] = { 1, 2, 2, 2, 2, 2 };

MessageTable pl04tlk_fr_tbl = { msgTalkAdrPL04, msgTalkCtrPL04 };
