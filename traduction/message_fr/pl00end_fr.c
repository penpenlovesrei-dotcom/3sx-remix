/**
 * @file pl00end_fr.c
 * Gill Ending Text (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl00end_fr.h"
#include "common.h"

static s8* msgEndPL00_00[1] = { "" };
static s8* msgEndPL00_01[1] = { "   Tu avais tort...                             " };
static s8* msgEndPL00_02[2] = {
    "   Nul ne ma^itrise la haine ou l'amour         ",
    "   qui l'habitent...                            ",
};
static s8* msgEndPL00_03[2] = {
    "   Chaque ^ame se nourrit et survit             ",
    "   de ses *emotions...                          ",
};
static s8* msgEndPL00_04[2] = {
    "   Ignorer certaines *emotions peut             ",
    "   briser ou d*etruire les ^etres !             ",
};
static s8* msgEndPL00_05[2] = {
    "   Ouvre ton esprit : chaque sentiment          ",
    "   a besoin de son contraire...                 ",
};
static s8* msgEndPL00_06[1] = { "   Laisse-moi te guider...                      " };
static s8* msgEndPL00_07[1] = { "   \"...Hein ? Que se passe-t-il... ?\"           " };
static s8* msgEndPL00_08[2] = {
    "   \"On m'a retir*e quelque chose... Et          ",
    "   pourtant, quelque chose s'ajoute...\"         ",
};
static s8* msgEndPL00_09[2] = {
    "   Le paradis... Tous en r^event et le          ",
    "   cherchent leur vie enti`ere...               ",
};
static s8* msgEndPL00_10[1] = { "   Mais le paradis n'existe pas.                " };
static s8* msgEndPL00_11[1] = { "   Les hommes sont aveugles `a la v*erit*e.     " };
static s8* msgEndPL00_12[1] = { "   2000 ans, c'*etait trop long.                " };
static s8* msgEndPL00_13[2] = {
    "   Je vais achever la mission que mon           ",
    "   pr*ed*ecesseur avait entreprise.             ",
};
static s8* msgEndPL00_14[1] = { "   L'avenir sombre est r*evolu...               " };
static s8* msgEndPL00_15[1] = { "   Voil`a... La voie est trac*ee.               " };
static s8* msgEndPL00_16[2] = {
    "   Elle m`enera les pauvres hommes de ce        ",
    "   monde vers leur *evolution...                ",
};
static s8* msgEndPL00_17[1] = { "   Oui... Voici le chemin du paradis !          " };

static s8** msgEndAdrPL00[18] = {
    msgEndPL00_00, msgEndPL00_01, msgEndPL00_02, msgEndPL00_03, msgEndPL00_04, msgEndPL00_05,
    msgEndPL00_06, msgEndPL00_07, msgEndPL00_08, msgEndPL00_09, msgEndPL00_10, msgEndPL00_11,
    msgEndPL00_12, msgEndPL00_13, msgEndPL00_14, msgEndPL00_15, msgEndPL00_16, msgEndPL00_17,
};

static s8 msgEndCtrPL00[18] = { 1, 1, 2, 2, 2, 2, 1, 1, 2, 2, 1, 1, 1, 2, 1, 1, 2, 1 };

MessageTable pl00end_fr_tbl = { msgEndAdrPL00, msgEndCtrPL00 };
