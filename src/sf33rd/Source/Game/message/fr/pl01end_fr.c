/**
 * @file pl01end_fr.c
 * Alex Ending Text (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl01end_fr.h"
#include "common.h"

static s8* msgEndPL01_00[1] = { "" };
static s8* msgEndPL01_01[2] = {
    "   Argh ! Je n'ai pas pu contrer                ",
    "   un seul de ses coups !                       ",
};
static s8* msgEndPL01_02[2] = {
    "   (Sa r*eputation ne lui rend pas              ",
    "   justice ! Il est bien plus fort !)           ",
};
static s8* msgEndPL01_03[2] = {
    "   \"D*esol*e, je ne peux pas venir camper.      ",
    "   Pr*esente mes excuses `a Pat.\"               ",
};
static s8* msgEndPL01_04[2] = {
    "   \"...Je sais que ;ca para^it fou, mais        ",
    "   je n'arrive pas `a me retenir.\"              ",
};
static s8* msgEndPL01_05[2] = {
    "   \"Le revoir et me battre ! Je ne              ",
    "   pense plus qu'`a ;ca !\"                      ",
};
static s8* msgEndPL01_06[2] = {
    "   \"Je serai sur les routes un moment...        ",
    "   Tom, on se revoit plus tard !\"               ",
};
static s8* msgEndPL01_07[1] = { "   (Son heure est venue...)                     " };
static s8* msgEndPL01_08[2] = {
    "   (Il doit se dire que je ne fais              ",
    "   plus le poids face `a lui...)                ",
};
static s8* msgEndPL01_09[2] = {
    "   (Alex, `a ton retour, je jugerai par         ",
    "   moi-m^eme de ta nouvelle force !)            ",
};
static s8* msgEndPL01_10[1] = { "   Papa ! Au fait, o`u est Alex ?               " };
static s8* msgEndPL01_11[2] = {
    "   On a besoin de lui pour monter               ",
    "   la tente au bord du lac.                     ",
};
static s8* msgEndPL01_12[1] = { "   Papa, tu m'*ecoutes ?!                       " };
static s8* msgEndPL01_13[2] = {
    "   Qu'est-ce qui t'arrive ?!                    ",
    "   C'est tout ce que tu as ?                    ",
};
static s8* msgEndPL01_14[2] = {
    "   Ha ha... Pas du tout !                       ",
    "   Le spectacle ne fait que commencer !         ",
};
static s8* msgEndPL01_15[1] = { "   Pr*epare-toi !                               " };

static s8** msgEndAdrPL01[16] = {
    msgEndPL01_00, msgEndPL01_01, msgEndPL01_02, msgEndPL01_03, msgEndPL01_04, msgEndPL01_05,
    msgEndPL01_06, msgEndPL01_07, msgEndPL01_08, msgEndPL01_09, msgEndPL01_10, msgEndPL01_11,
    msgEndPL01_12, msgEndPL01_13, msgEndPL01_14, msgEndPL01_15,
};

static s8 msgEndCtrPL01[16] = { 1, 2, 2, 2, 2, 2, 2, 1, 2, 2, 1, 2, 1, 2, 2, 1 };

MessageTable pl01end_fr_tbl = { msgEndAdrPL01, msgEndCtrPL01 };
