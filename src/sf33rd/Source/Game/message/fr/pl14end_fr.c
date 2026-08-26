/**
 * @file pl14end_fr.c
 * Akuma Ending Text (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl14end_fr.h"
#include "common.h"

static s8* msgEndPL14_00[1] = { "" };
static s8* msgEndPL14_01[2] = {
    "   Ici Deep Sea 3000.                           ",
    "   150 m avant l'objectif... Termin*e.          ",
};
static s8* msgEndPL14_02[2] = {
    "   Point d'observation atteint dans             ",
    "   environ 40 secondes.                         ",
};
static s8* msgEndPL14_03[2] = {
    "   Contact visuel avec l'*epave *etabli.        ",
    "   Passage en phase trois... Termin*e.          ",
};
static s8* msgEndPL14_04[1] = { "   ...Quoi ?!                                   " };
static s8* msgEndPL14_05[2] = {
    "   C'est... un homme ?!                         ",
    "   Non... impossible !                          ",
};
static s8* msgEndPL14_06[1] = { "   Ce n'est pas possible...                     " };
static s8* msgEndPL14_07[2] = {
    "   Quoi ? Qu'avez-vous vu ?!                    ",
    "   R*epondez !! Termin*e !                      ",
};
static s8* msgEndPL14_08[2] = {
    "   Il y a un probl`eme !                        ",
    "   La radio est coup*ee... Aaaah !!             ",
};
static s8* msgEndPL14_09[1] = { "   Muuuuuuunn !!                                " };
static s8* msgEndPL14_10[1] = { "   Tenshou Kaireki Jin !!                       " };

static s8** msgEndAdrPL14[11] = {
    msgEndPL14_00, msgEndPL14_01, msgEndPL14_02, msgEndPL14_03, msgEndPL14_04, msgEndPL14_05,
    msgEndPL14_06, msgEndPL14_07, msgEndPL14_08, msgEndPL14_09, msgEndPL14_10,
};

static s8 msgEndCtrPL14[11] = { 1, 2, 2, 2, 1, 2, 1, 2, 2, 1, 1 };

MessageTable pl14end_fr_tbl = { msgEndAdrPL14, msgEndCtrPL14 };
