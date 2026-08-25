/**
 * @file pl08end_fr.c
 * Elena Ending Text (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl08end_fr.h"
#include "common.h"

static s8* msgEndPL08_00[1] = { "" };
static s8* msgEndPL08_01[1] = { "   Ma ch`ere Naru-chan,                         " };
static s8* msgEndPL08_02[2] = {
    "   Comment vas-tu ?                             ",
    "   Moi je vais bien, comme toujours.            ",
};
static s8* msgEndPL08_03[2] = {
    "   Je me sens seule, maintenant que la          ",
    "   f^ete des moissons est termin*ee.            ",
};
static s8* msgEndPL08_04[2] = {
    "   En buvant mon th*e, je repense `a nos        ",
    "   beaux *et*es au Japon.                       ",
};
static s8* msgEndPL08_05[2] = {
    "   ...Quand on allait `a la f^ete bien          ",
    "   habill*ees, voir les feux d'artifice...      ",
};
static s8* msgEndPL08_06[2] = {
    "   Tout *etait si amusant ! Et les              ",
    "   combats *etaient palpitants !                ",
};
static s8* msgEndPL08_07[2] = {
    "   J'aimerais inviter ta famille `a voir        ",
    "   la grande plaine de mon pays.                ",
};
static s8* msgEndPL08_08[2] = {
    "   Je suis s^ure que ma famille                 ",
    "   t'adorera !                                  ",
};
static s8* msgEndPL08_09[2] = {
    "   Aux vacances d'hiver, peut-^etre...          ",
    "   Je sais que tu r*evises beaucoup.            ",
};
static s8* msgEndPL08_10[2] = {
    "   Prends bien soin de ta sant*e !              ",
    "   `A tr`es bient^ot !                          ",
};
static s8* msgEndPL08_11[2] = {
    "   Il me reste beaucoup `a faire !              ",
    "   Moi aussi je vais travailler !               ",
};

static s8** msgEndAdrPL08[12] = {
    msgEndPL08_00, msgEndPL08_01, msgEndPL08_02, msgEndPL08_03, msgEndPL08_04, msgEndPL08_05,
    msgEndPL08_06, msgEndPL08_07, msgEndPL08_08, msgEndPL08_09, msgEndPL08_10, msgEndPL08_11,
};

static s8 msgEndCtrPL08[12] = { 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2 };

MessageTable pl08end_fr_tbl = { msgEndAdrPL08, msgEndCtrPL08 };
