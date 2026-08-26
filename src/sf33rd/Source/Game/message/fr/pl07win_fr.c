/**
 * @file pl07win_fr.c
 * Ibuki Win Quotes (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl07win_fr.h"
#include "common.h"

static s8* msgWinPL07_00P[1] = { "" };
static s8* msgWinPL07_01P[1] = { "" };
static s8* msgWinPL07_02P[1] = { "" };
static s8* msgWinPL07_03P[1] = { "" };
static s8* msgWinPL07_04P[1] = { "" };
static s8* msgWinPL07_05P[1] = { "" };
static s8* msgWinPL07_06P[1] = { "" };
static s8* msgWinPL07_07P[1] = { "" };
static s8* msgWinPL07_08P[1] = { "" };
static s8* msgWinPL07_09P[1] = { "" };
static s8* msgWinPL07_10P[1] = { "" };
static s8* msgWinPL07_11P[1] = { "" };
static s8* msgWinPL07_12P[1] = { "" };
static s8* msgWinPL07_13P[1] = { "" };
static s8* msgWinPL07_14P[1] = { "" };
static s8* msgWinPL07_15P[1] = { "" };
static s8* msgWinPL07_16P[1] = { "" };
static s8* msgWinPL07_17P[1] = { "" };
static s8* msgWinPL07_18P[1] = { "" };
static s8* msgWinPL07_19P[1] = { "" };
static s8* msgWinPL07_20P[2] = {
    "   Personne ne doit savoir que j'ai             ",
    "   perdu mon temps sur un cas pareil !          ",
};
static s8* msgWinPL07_21P[2] = {
    "   D*esol*ee que ;ca ait *et*e si court !       ",
    "   Une fille doit s'amuser, non ?               ",
};
static s8* msgWinPL07_22P[2] = {
    "   Quel examen de fin d'*etudes !               ",
    "   Ce n'est pas facile, d'^etre shinobi !       ",
};
static s8* msgWinPL07_23P[2] = {
    "   J'ai des tenues bien plus `a la mode         ",
    "   que celle-ci ! Crois-moi !                   ",
};
static s8* msgWinPL07_24P[2] = {
    "   Ne regarde pas. Je dois me changer           ",
    "   et je n'ai plus de bombes...                 ",
};
static s8* msgWinPL07_25P[2] = {
    "   Je dirai `a tout le monde que tu             ",
    "   t'es bien battu, d'accord ?                  ",
};
static s8* msgWinPL07_26P[2] = {
    "   Ce n'*etait pas la fa;con la plus            ",
    "   efficace de t'assommer, mais bon !           ",
};
static s8* msgWinPL07_27P[2] = {
    "   Je ne crois pas que tu tiendrais             ",
    "   bien longtemps dans mon village...           ",
};

static s8** msgWinAdrPL07[28] = {
    msgWinPL07_00P, msgWinPL07_01P, msgWinPL07_02P, msgWinPL07_03P, msgWinPL07_04P, msgWinPL07_05P,
    msgWinPL07_06P, msgWinPL07_07P, msgWinPL07_08P, msgWinPL07_09P, msgWinPL07_10P, msgWinPL07_11P,
    msgWinPL07_12P, msgWinPL07_13P, msgWinPL07_14P, msgWinPL07_15P, msgWinPL07_16P, msgWinPL07_17P,
    msgWinPL07_18P, msgWinPL07_19P, msgWinPL07_20P, msgWinPL07_21P, msgWinPL07_22P, msgWinPL07_23P,
    msgWinPL07_24P, msgWinPL07_25P, msgWinPL07_26P, msgWinPL07_27P,
};

static s8 msgWinCtrPL07[28] = { 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2 };

MessageTable pl07win_fr_tbl = { msgWinAdrPL07, msgWinCtrPL07 };
