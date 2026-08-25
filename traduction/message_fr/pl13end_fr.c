/**
 * @file pl13end_fr.c
 * Urien Ending Text (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl13end_fr.h"
#include "common.h"

static s8* msgEndPL13_00[1] = { "" };
static s8* msgEndPL13_01[2] = {
    "   Voil`a donc les \"cerveaux\" amass*es          ",
    "   pendant 2000 ans...                          ",
};
static s8* msgEndPL13_02[2] = {
    "   J'ignore ce qu'ils valent, mais              ",
    "   ils sont laids et stupides.                  ",
};
static s8* msgEndPL13_03[2] = {
    "   ...Un tas de rebut incapable de              ",
    "   la moindre action utile !                    ",
};
static s8* msgEndPL13_04[2] = {
    "   Mon fr`ere ! Que regardes-tu donc ?          ",
    "   Vois-tu le monde ?                           ",
};
static s8* msgEndPL13_05[2] = {
    "   Regardes-tu comment se b^atit                ",
    "   ton monde id*eal ?                           ",
};
static s8* msgEndPL13_06[2] = {
    "   Ha... ha ha ha ha ha !                       ",
    "   Ha ha ha ha ha ha ha ha !!                   ",
};
static s8* msgEndPL13_07[2] = {
    "   Identit*e v*erifi*ee... Reconnu comme        ",
    "   successeur l*egitime...                      ",
};
static s8* msgEndPL13_08[2] = {
    "   Code d'autodestruction :                     ",
    "   A22ST8996HYXW...                             ",
};
static s8* msgEndPL13_09[2] = {
    "   Il ne reste ni mission ni h*eritage          ",
    "   dont je doive h*eriter !                     ",
};
static s8* msgEndPL13_10[2] = {
    "   D*esormais, ma propre histoire               ",
    "   commence `a cet instant !                    ",
};
static s8* msgEndPL13_11[2] = {
    "   Je d*ecr`ete cette ann*ee la premi`ere       ",
    "   de l'`ere \"A.U.\" (Apr`es Urien) !!           ",
};

static s8** msgEndAdrPL13[12] = {
    msgEndPL13_00, msgEndPL13_01, msgEndPL13_02, msgEndPL13_03, msgEndPL13_04, msgEndPL13_05,
    msgEndPL13_06, msgEndPL13_07, msgEndPL13_08, msgEndPL13_09, msgEndPL13_10, msgEndPL13_11,
};

static s8 msgEndCtrPL13[12] = { 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2 };

MessageTable pl13end_fr_tbl = { msgEndAdrPL13, msgEndCtrPL13 };
