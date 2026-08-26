/**
 * @file pl19end_fr.c
 * Remy Ending Text (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl19end_fr.h"
#include "common.h"

static s8* msgEndPL19_00[1] = { "" };
static s8* msgEndPL19_01[2] = {
    "   Chaque fois que je plonge dans cette         ",
    "   mer de Bisque, j'ai si froid.                ",
};
static s8* msgEndPL19_02[2] = {
    "   Aussi froide que mon coeur,                  ",
    "   que rien ne peut gu*erir.                    ",
};
static s8* msgEndPL19_03[2] = {
    "   (Les mar*ees gagnent en vitesse              ",
    "   et en fr*equence...)                         ",
};
static s8* msgEndPL19_04[2] = {
    "   (Ce sera la derni`ere fois que               ",
    "   je viens ici...)                             ",
};
static s8* msgEndPL19_05[2] = {
    "   Je me d*ebats dans les t*en`ebres            ",
    "   depuis bien longtemps...                     ",
};
static s8* msgEndPL19_06[2] = {
    "   J'ai essay*e de peindre l'obscurit*e         ",
    "   avec une autre ombre...                      ",
};
static s8* msgEndPL19_07[2] = {
    "   Au fond... c'*etait les t*en`ebres           ",
    "   du \"guerrier\"...                             ",
};
static s8* msgEndPL19_08[2] = {
    "   Elles ont fait dispara^itre notre p`ere      ",
    "   et nous ont laiss*es seuls...                ",
};
static s8* msgEndPL19_09[1] = { "   ...Je ne peux pas encore lui pardonner.      " };
static s8* msgEndPL19_10[2] = {
    "   Mais... rien ne changerait                   ",
    "   si je continuais ainsi.                      ",
};
static s8* msgEndPL19_11[1] = { "   Alors... je vais tout oublier.               " };
static s8* msgEndPL19_12[2] = {
    "   Je crois que c'est ainsi qu'on               ",
    "   pourra ^etre heureux.                        ",
};
static s8* msgEndPL19_13[1] = { "   Adieu... ma soeur !                          " };
static s8* msgEndPL19_14[2] = {
    "   Apr`es ces adieux, Remy aper;coit            ",
    "   une lumi`ere sur le chemin du retour.        ",
};
static s8* msgEndPL19_15[2] = {
    "   Jamais il n'aurait cru pouvoir               ",
    "   voir une telle lumi`ere...                   ",
};
static s8* msgEndPL19_16[2] = {
    "   Pour en d*ecouvrir le sens, Remy             ",
    "   se met en marche...                          ",
};

static s8** msgEndAdrPL19[17] = {
    msgEndPL19_00, msgEndPL19_01, msgEndPL19_02, msgEndPL19_03, msgEndPL19_04, msgEndPL19_05,
    msgEndPL19_06, msgEndPL19_07, msgEndPL19_08, msgEndPL19_09, msgEndPL19_10, msgEndPL19_11,
    msgEndPL19_12, msgEndPL19_13, msgEndPL19_14, msgEndPL19_15, msgEndPL19_16,
};

static s8 msgEndCtrPL19[17] = { 1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2, 1, 2, 1, 2, 2, 2 };

MessageTable pl19end_fr_tbl = { msgEndAdrPL19, msgEndCtrPL19 };
