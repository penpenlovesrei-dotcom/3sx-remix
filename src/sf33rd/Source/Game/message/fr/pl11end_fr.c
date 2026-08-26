/**
 * @file pl11end_fr.c
 * Ken Ending Text (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl11end_fr.h"
#include "common.h"

static s8* msgEndPL11_00[1] = { "" };
static s8* msgEndPL11_01[2] = {
    "   C'est parti !                                ",
    "   Sho... Ryuuuu... Kennnn !                    ",
};
static s8* msgEndPL11_02[2] = {
    "   Oh non ! Il n'a pas l'air                    ",
    "   de vouloir se relever !                      ",
};
static s8* msgEndPL11_03[1] = { "   Le combat est termin*e !!                    " };
static s8* msgEndPL11_04[2] = {
    "   Avec la puissance qu'on lui conna^it,        ",
    "   le vainqueur est Ken !                       ",
};
static s8* msgEndPL11_05[2] = {
    "   Trois titres am*ericains d'affil*ee !        ",
    "   Une page d'histoire s'*ecrit !               ",
};
static s8* msgEndPL11_06[2] = {
    "   Quel moment pour Ken, sa famille             ",
    "   et ses amis !                                ",
};
static s8* msgEndPL11_07[2] = {
    "   Tu vois ? Je l'ai mis KO en                  ",
    "   30 secondes, comme promis !                  ",
};
static s8* msgEndPL11_08[2] = {
    "   Ah oui ! Tiens, Sean...                      ",
    "   C'est pour toi !                             ",
};
static s8* msgEndPL11_09[2] = {
    "   Le troph*ee du championnat...                ",
    "   Tu le voulais, non ?                         ",
};
static s8* msgEndPL11_10[2] = {
    "   M... Ma^itre !                               ",
    "   Ce n'est pas ce que je voulais dire !        ",
};
static s8* msgEndPL11_11[2] = {
    "   ;Ca n'a aucune valeur si je ne l'ai          ",
    "   pas gagn*e par mes propres moyens !          ",
};
static s8* msgEndPL11_12[2] = {
    "   Ah bon ? Ne te tracasse pas                  ",
    "   trop avec ;ca.                               ",
};
static s8* msgEndPL11_13[2] = {
    "   Au minimum, il faudra passer les             ",
    "   qualifications la prochaine fois !           ",
};
static s8* msgEndPL11_14[2] = {
    "   Mais tu ne gagneras pas, puisque tu          ",
    "   ne peux pas me battre ! Ha ha ha !           ",
};

static s8** msgEndAdrPL11[15] = {
    msgEndPL11_00, msgEndPL11_01, msgEndPL11_02, msgEndPL11_03, msgEndPL11_04, msgEndPL11_05,
    msgEndPL11_06, msgEndPL11_07, msgEndPL11_08, msgEndPL11_09, msgEndPL11_10, msgEndPL11_11,
    msgEndPL11_12, msgEndPL11_13, msgEndPL11_14,
};

static s8 msgEndCtrPL11[15] = { 1, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2 };

MessageTable pl11end_fr_tbl = { msgEndAdrPL11, msgEndCtrPL11 };
