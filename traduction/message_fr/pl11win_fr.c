/**
 * @file pl11win_fr.c
 * Ken Win Quotes (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl11win_fr.h"
#include "common.h"

static s8* msgWinPL11_00P[1] = { "" };
static s8* msgWinPL11_01P[1] = { "" };
static s8* msgWinPL11_02P[1] = { "" };
static s8* msgWinPL11_03P[1] = { "" };
static s8* msgWinPL11_04P[1] = { "" };
static s8* msgWinPL11_05P[1] = { "" };
static s8* msgWinPL11_06P[1] = { "" };
static s8* msgWinPL11_07P[1] = { "" };
static s8* msgWinPL11_08P[1] = { "" };
static s8* msgWinPL11_09P[1] = { "" };
static s8* msgWinPL11_10P[1] = { "" };
static s8* msgWinPL11_11P[1] = { "" };
static s8* msgWinPL11_12P[1] = { "" };
static s8* msgWinPL11_13P[1] = { "" };
static s8* msgWinPL11_14P[1] = { "" };
static s8* msgWinPL11_15P[1] = { "" };
static s8* msgWinPL11_16P[1] = { "" };
static s8* msgWinPL11_17P[1] = { "" };
static s8* msgWinPL11_18P[1] = { "" };
static s8* msgWinPL11_19P[1] = { "" };
static s8* msgWinPL11_20P[2] = {
    "   T*em*eraire ou courageux, adopte le          ",
    "   style qui te convient le mieux !             ",
};
static s8* msgWinPL11_21P[2] = {
    "   Attends le combat avec impatience !          ",
    "   Vis pour le frisson de la bagarre !          ",
};
static s8* msgWinPL11_22P[1] = { "   Je te souhaite bonne chance !                " };
static s8* msgWinPL11_23P[2] = {
    "   C'est ;ca l'esprit ! Bats-toi avec           ",
    "   rage `a chaque instant !                     ",
};
static s8* msgWinPL11_24P[2] = {
    "   Je me battrai avec style et finesse,         ",
    "   quel que soit le r*esultat !                 ",
};
static s8* msgWinPL11_25P[2] = {
    "   Mon gamin devrait peut-^etre                 ",
    "   s'entra^iner contre toi !                    ",
};
static s8* msgWinPL11_26P[2] = {
    "   Merci de m'avoir aid*e `a montrer `a Mel     ",
    "   qui a les poings les plus forts !            ",
};
static s8* msgWinPL11_27P[2] = {
    "   Ils feront peut-^etre une figurine           ",
    "   `a ton effigie, un jour !                    ",
};

static s8** msgWinAdrPL11[28] = {
    msgWinPL11_00P, msgWinPL11_01P, msgWinPL11_02P, msgWinPL11_03P, msgWinPL11_04P, msgWinPL11_05P,
    msgWinPL11_06P, msgWinPL11_07P, msgWinPL11_08P, msgWinPL11_09P, msgWinPL11_10P, msgWinPL11_11P,
    msgWinPL11_12P, msgWinPL11_13P, msgWinPL11_14P, msgWinPL11_15P, msgWinPL11_16P, msgWinPL11_17P,
    msgWinPL11_18P, msgWinPL11_19P, msgWinPL11_20P, msgWinPL11_21P, msgWinPL11_22P, msgWinPL11_23P,
    msgWinPL11_24P, msgWinPL11_25P, msgWinPL11_26P, msgWinPL11_27P,
};

static s8 msgWinCtrPL11[28] = { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 1, 2, 2, 2, 2, 2 };

MessageTable pl11win_fr_tbl = { msgWinAdrPL11, msgWinCtrPL11 };
