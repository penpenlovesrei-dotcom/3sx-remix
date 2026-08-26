/**
 * @file pl09end_fr.c
 * Oro Ending Text (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl09end_fr.h"
#include "common.h"

static s8* msgEndPL09_00[1] = { "" };
static s8* msgEndPL09_01[2] = {
    "   Hi hi hi... Cela faisait 50 ans que          ",
    "   je ne m'*etais pas entra^in*e ainsi !        ",
};
static s8* msgEndPL09_02[2] = {
    "   Chaque fois que je vois ce gamin,            ",
    "   mon sang se remet `a bouillir...             ",
};
static s8* msgEndPL09_03[2] = {
    "   Il est unique en son genre... Je ne          ",
    "   vais pas m'ennuyer de sit^ot !               ",
};
static s8* msgEndPL09_04[1] = { "   Hmm ??                                       " };
static s8* msgEndPL09_05[2] = {
    "   J'ai cru entendre la voix de                 ",
    "   ce dr^ole de vieillard... ?                  ",
};
static s8* msgEndPL09_06[2] = {
    "   C'*etait sans doute                          ",
    "   mon imagination...                           ",
};
static s8* msgEndPL09_07[2] = {
    "   Il doit s'entra^iner d'arrache-pied          ",
    "   en ce moment m^eme !                         ",
};
static s8* msgEndPL09_08[2] = {
    "   J'esp`ere qu'il deviendra assez fort         ",
    "   pour me faire user de mes deux bras !        ",
};
static s8* msgEndPL09_09[2] = {
    "   Mais... il faudra au moins 15 ans            ",
    "   avant que cela n'arrive...                   ",
};
static s8* msgEndPL09_10[1] = { "   Je devrais peut-^etre me reposer...          " };
static s8* msgEndPL09_11[1] = { "   Ouf !                                        " };

static s8** msgEndAdrPL09[12] = {
    msgEndPL09_00, msgEndPL09_01, msgEndPL09_02, msgEndPL09_03, msgEndPL09_04, msgEndPL09_05,
    msgEndPL09_06, msgEndPL09_07, msgEndPL09_08, msgEndPL09_09, msgEndPL09_10, msgEndPL09_11,
};

static s8 msgEndCtrPL09[12] = { 1, 2, 2, 2, 1, 2, 2, 2, 2, 2, 1, 1 };

MessageTable pl09end_fr_tbl = { msgEndAdrPL09, msgEndCtrPL09 };
