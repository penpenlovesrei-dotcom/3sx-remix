/**
 * @file pl15end_fr.c
 * Chun-Li Ending Text (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl15end_fr.h"
#include "common.h"

static s8* msgEndPL15_00[1] = { "" };
static s8* msgEndPL15_01[1] = { "   \"Mademoiselle !\"                             " };
static s8* msgEndPL15_02[1] = { "   \"Tout va bien maintenant...\"                 " };
static s8* msgEndPL15_03[1] = { "   ...Six mois ont pass*e depuis...             " };
static s8* msgEndPL15_04[2] = {
    "   ...Quand j'ai serr*e dans mes bras           ",
    "   la petite que j'avais sauv*ee...             ",
};
static s8* msgEndPL15_05[2] = {
    "   j'ai enfin compris quel devait ^etre         ",
    "   mon v*eritable \"combat\"...                   ",
};
static s8* msgEndPL15_06[2] = {
    "   Pour notre pays, celui que mon               ",
    "   p`ere a tent*e de prot*eger...               ",
};
static s8* msgEndPL15_07[2] = {
    "   Ya !                                         ",
    "   Haah !                                       ",
};
static s8* msgEndPL15_08[2] = {
    "   Pour tous les gens au grand coeur            ",
    "   que j'ai crois*es de par le monde...         ",
};
static s8* msgEndPL15_09[2] = {
    "   Ha !                                         ",
    "   Taaah !                                      ",
};
static s8* msgEndPL15_10[2] = {
    "   Pour enseigner `a ces enfants la vraie       ",
    "   force et la vraie beaut*e...                 ",
};
static s8* msgEndPL15_11[2] = {
    "   Voil`a le but de ma vie,                     ",
    "   et mon avenir.                               ",
};
static s8* msgEndPL15_12[2] = {
    "   Je b^atirai notre demain                     ",
    "   de mes propres poings !                      ",
};
static s8* msgEndPL15_13[1] = { "   Iyaaaaahh !!                                 " };

static s8** msgEndAdrPL15[14] = {
    msgEndPL15_00, msgEndPL15_01, msgEndPL15_02, msgEndPL15_03, msgEndPL15_04, msgEndPL15_05,
    msgEndPL15_06, msgEndPL15_07, msgEndPL15_08, msgEndPL15_09, msgEndPL15_10, msgEndPL15_11,
    msgEndPL15_12, msgEndPL15_13,
};

static s8 msgEndCtrPL15[14] = { 1, 1, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1 };

MessageTable pl15end_fr_tbl = { msgEndAdrPL15, msgEndCtrPL15 };
