/**
 * @file pl04end_fr.c
 * Dudley Ending Text (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl04end_fr.h"
#include "common.h"

static s8* msgEndPL04_00[1] = { "" };
static s8* msgEndPL04_01[2] = {
    "   La beaut*e subtile de St. Swithun...         ",
    "   Le parfum d'Abraham Darby...                 ",
};
static s8* msgEndPL04_02[2] = {
    "   La l*eg`eret*e de Dainty Bess...             ",
    "   L'allure d'Uncle Walter...                   ",
};
static s8* msgEndPL04_03[2] = {
    "   P`ere... Vous m'avez laiss*e cette           ",
    "   majestueuse roseraie...                      ",
};
static s8* msgEndPL04_04[2] = {
    "   La beaut*e sans cesse changeante des         ",
    "   roses apaise encore mon coeur.               ",
};
static s8* msgEndPL04_05[1] = { "   Sir Dudley... Il serait temps...             " };
static s8* msgEndPL04_06[2] = {
    "   Ah oui, c'est vrai. C'est aujourd'hui        ",
    "   ce grand match royal...                      ",
};
static s8* msgEndPL04_07[1] = { "   `A quelle heure commence-t-il ?              " };
static s8* msgEndPL04_08[1] = { "   `A 20h00 pr*ecises, monsieur.                " };
static s8* msgEndPL04_09[2] = {
    "   Comment... ?!                                ",
    "   Il ne reste que cinq heures ?!               ",
};
static s8* msgEndPL04_10[2] = {
    "   Il faut rentrer au manoir                    ",
    "   imm*ediatement ! Courons !!                  ",
};

static s8** msgEndAdrPL04[11] = {
    msgEndPL04_00, msgEndPL04_01, msgEndPL04_02, msgEndPL04_03, msgEndPL04_04, msgEndPL04_05,
    msgEndPL04_06, msgEndPL04_07, msgEndPL04_08, msgEndPL04_09, msgEndPL04_10,
};

static s8 msgEndCtrPL04[11] = { 1, 2, 2, 2, 2, 1, 2, 1, 1, 2, 2 };

MessageTable pl04end_fr_tbl = { msgEndAdrPL04, msgEndCtrPL04 };
