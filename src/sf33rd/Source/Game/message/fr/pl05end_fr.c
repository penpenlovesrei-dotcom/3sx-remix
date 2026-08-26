/**
 * @file pl05end_fr.c
 * Necro Ending Text (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl05end_fr.h"
#include "common.h"

static s8* msgEndPL05_00[1] = { "" };
static s8* msgEndPL05_01[2] = {
    "   Aaah !                                       ",
    "   On est coinc*es !!                           ",
};
static s8* msgEndPL05_02[2] = {
    "   Ne dis pas ;ca ! On ne s'arr^ete pas !!      ",
    "   N'abandonne jamais ! Cours !!                ",
};
static s8* msgEndPL05_03[2] = {
    "   On arrive aux bois de la fronti`ere !        ",
    "   On y est presque !                           ",
};
static s8* msgEndPL05_04[1] = { "   Ils sont sur le toit !                       " };
static s8* msgEndPL05_05[2] = {
    "   Toi ! Va au premier wagon, on les            ",
    "   prendra des deux c^ot*es !                   ",
};
static s8* msgEndPL05_06[2] = {
    "   Ils ne doivent jamais tomber                 ",
    "   aux mains de l'ennemi !                      ",
};
static s8* msgEndPL05_07[2] = {
    "   Leurs cellules m^emes sont                   ",
    "   une menace pour nous !                       ",
};
static s8* msgEndPL05_08[1] = { "   C'est donc la fin... ?                       " };
static s8* msgEndPL05_09[2] = {
    "   Non... Pas encore !                          ",
    "   Viens avec moi, Effie !                      ",
};
static s8* msgEndPL05_10[1] = { "   ...Iyaaaaaaaah !                             " };
static s8* msgEndPL05_11[2] = {
    "   Aaaaah !!                                    ",
    "   Illiaaaaaaaaa !!                             ",
};
static s8* msgEndPL05_12[1] = { "   Effieeeeee !!                                " };
static s8* msgEndPL05_13[1] = { "   C'est un miracle...                          " };
static s8* msgEndPL05_14[2] = {
    "   Pour la premi`ere fois... je suis            ",
    "   reconnaissant envers ce corps !              ",
};

static s8** msgEndAdrPL05[15] = {
    msgEndPL05_00, msgEndPL05_01, msgEndPL05_02, msgEndPL05_03, msgEndPL05_04, msgEndPL05_05,
    msgEndPL05_06, msgEndPL05_07, msgEndPL05_08, msgEndPL05_09, msgEndPL05_10, msgEndPL05_11,
    msgEndPL05_12, msgEndPL05_13, msgEndPL05_14,
};

static s8 msgEndCtrPL05[15] = { 1, 2, 2, 2, 1, 2, 2, 2, 1, 2, 1, 2, 1, 1, 2 };

MessageTable pl05end_fr_tbl = { msgEndAdrPL05, msgEndCtrPL05 };
