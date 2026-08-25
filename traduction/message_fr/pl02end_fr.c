/**
 * @file pl02end_fr.c
 * Ryu Ending Text (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl02end_fr.h"
#include "common.h"

static s8* msgEndPL02_00[1] = { "" };
static s8* msgEndPL02_01[1] = { "   \"Qu'est-ce qu'un vrai guerrier ?\"            " };
static s8* msgEndPL02_02[2] = {
    "   \"Pourquoi devrais-je ^etre fort ?            ",
    "   Qu'y a-t-il au-del`a de la victoire ?\"       ",
};
static s8* msgEndPL02_03[2] = {
    "   Depuis ma jeunesse, ces pens*ees             ",
    "   ne m'ont jamais quitt*e.                     ",
};
static s8* msgEndPL02_04[2] = {
    "   Il fallait choisir... Cesser de me           ",
    "   poser ces questions...                       ",
};
static s8* msgEndPL02_05[2] = {
    "   ...ou lutter pour en                         ",
    "   trouver les r*eponses...                     ",
};
static s8* msgEndPL02_06[1] = { "" };
static s8* msgEndPL02_07[2] = {
    "   Hmm. J'en suis loin. Je ne sais m^eme        ",
    "   pas o`u les feuilles vont tomber...          ",
};
static s8* msgEndPL02_08[2] = {
    "   Tant que les adversaires forts et            ",
    "   les combats rudes m'exaltent...              ",
};
static s8* msgEndPL02_09[2] = {
    "   Tant qu'il me restera la force de            ",
    "   bouger ne serait-ce qu'un doigt...           ",
};
static s8* msgEndPL02_10[1] = { "   ...je continuerai `a me battre !             " };

static s8** msgEndAdrPL02[11] = {
    msgEndPL02_00, msgEndPL02_01, msgEndPL02_02, msgEndPL02_03, msgEndPL02_04, msgEndPL02_05,
    msgEndPL02_06, msgEndPL02_07, msgEndPL02_08, msgEndPL02_09, msgEndPL02_10,
};

static s8 msgEndCtrPL02[11] = { 1, 1, 2, 2, 2, 2, 1, 2, 2, 2, 1 };

MessageTable pl02end_fr_tbl = { msgEndAdrPL02, msgEndCtrPL02 };
