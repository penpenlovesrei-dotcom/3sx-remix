/**
 * @file pl18end_fr.c
 * Twelve Ending Text (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl18end_fr.h"
#include "common.h"

static s8* msgEndPL18_00[1] = { "" };
static s8* msgEndPL18_01[2] = {
    "   La pression interne du berceau               ",
    "   est stable. Situation normale.               ",
};
static s8* msgEndPL18_02[1] = { "   Chef, le docteur est de retour...            " };
static s8* msgEndPL18_03[1] = { "   Bon retour, docteur Kure.                    " };
static s8* msgEndPL18_04[2] = {
    "   Nous avons retir*e le 12 et le 14.           ",
    "   Le processus est termin*e.                   ",
};
static s8* msgEndPL18_05[1] = { "   ...Comment va-t-il ?                         " };
static s8* msgEndPL18_06[1] = { "   Il est absolument parfait.                   " };
static s8* msgEndPL18_07[2] = {
    "   Chacune de ses cellules a retrouv*e          ",
    "   son *etat d'avant le combat.                 ",
};
static s8* msgEndPL18_08[2] = {
    "   La th*eorie de reconstruction du corps       ",
    "   de sire Urien est g*eniale !                 ",
};
static s8* msgEndPL18_09[2] = {
    "   Avec cette technologie... l'homme ne         ",
    "   vieillirait ni ne mourrait plus.             ",
};
static s8* msgEndPL18_10[2] = {
    "   Il ne reste qu'`a maintenir la perte         ",
    "   de m*emoire sous les 0.0001%.                ",
};
static s8* msgEndPL18_11[2] = {
    "   Ainsi... le \"guerrier immortel\"              ",
    "   est n*e...                                   ",
};
static s8* msgEndPL18_12[2] = {
    "   Toute douleur, tout plaisir s'efface.        ",
    "   Tu vas na^itre de nouveau...                 ",
};
static s8* msgEndPL18_13[2] = {
    "   Dans ton sommeil profond... quel             ",
    "   genre de r^eve fais-tu ?                     ",
};
static s8* msgEndPL18_14[2] = {
    "   Non... Il n'en a pas                         ",
    "   la facult*e.                                 ",
};
static s8* msgEndPL18_15[2] = {
    "   Sa m*emoire *etant sans cesse en             ",
    "   activit*e, il ne peut pas r^ever.            ",
};
static s8* msgEndPL18_16[2] = {
    "   Ce n'est donc pas si formidable de           ",
    "   vivre *eternellement ! Ha ha ha !!           ",
};

static s8** msgEndAdrPL18[17] = {
    msgEndPL18_00, msgEndPL18_01, msgEndPL18_02, msgEndPL18_03, msgEndPL18_04, msgEndPL18_05,
    msgEndPL18_06, msgEndPL18_07, msgEndPL18_08, msgEndPL18_09, msgEndPL18_10, msgEndPL18_11,
    msgEndPL18_12, msgEndPL18_13, msgEndPL18_14, msgEndPL18_15, msgEndPL18_16,
};

static s8 msgEndCtrPL18[17] = { 1, 2, 1, 1, 2, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2 };

MessageTable pl18end_fr_tbl = { msgEndAdrPL18, msgEndCtrPL18 };
