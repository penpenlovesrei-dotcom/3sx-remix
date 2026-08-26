/**
 * @file pl12end_fr.c
 * Sean Ending Text (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl12end_fr.h"
#include "common.h"

static s8* msgEndPL12_00[1] = { "" };
static s8* msgEndPL12_01[1] = { "   Victoire !!                                  " };
static s8* msgEndPL12_02[2] = {
    "   Sean remporte le premier tournoi             ",
    "   de sa carri`ere !                            ",
};
static s8* msgEndPL12_03[1] = { "   J'ai r*eussi ! Enfin !                       " };
static s8* msgEndPL12_04[1] = { "   Me voil`a champion des *Etats-Unis !         " };
static s8* msgEndPL12_05[2] = {
    "   Je suis au niveau de mon ma^itre !           ",
    "   Un r^eve qui se r*ealise !                   ",
};
static s8* msgEndPL12_06[2] = {
    "   ...lut ...Oh*e ? Sean !                      ",
    "   (...Quo ...Quoi ?)                           ",
};
static s8* msgEndPL12_07[1] = { "   ;Ca va ?!                                    " };
static s8* msgEndPL12_08[2] = {
    "   Bien ! Tu reprends tes esprits...            ",
    "   Enfin, je crois...                           ",
};
static s8* msgEndPL12_09[2] = {
    "   C'*etait juste... Tu as failli passer        ",
    "   les qualifications !                         ",
};
static s8* msgEndPL12_10[2] = {
    "   Tu ne t'es pas entra^in*e comme il           ",
    "   faut. Fais mieux la prochaine fois !         ",
};
static s8* msgEndPL12_11[2] = {
    "   D'accord, comptez sur moi ! Je               ",
    "   prendrai ma revanche au prochain !           ",
};
static s8* msgEndPL12_12[2] = {
    "   Hein ? C'*etait un r^eve ?!                  ",
    "   Mais un jour... un jour je gagnerai !        ",
};

static s8** msgEndAdrPL12[13] = {
    msgEndPL12_00, msgEndPL12_01, msgEndPL12_02, msgEndPL12_03, msgEndPL12_04, msgEndPL12_05,
    msgEndPL12_06, msgEndPL12_07, msgEndPL12_08, msgEndPL12_09, msgEndPL12_10, msgEndPL12_11,
    msgEndPL12_12,
};

static s8 msgEndCtrPL12[13] = { 1, 1, 2, 1, 1, 2, 2, 1, 2, 2, 2, 2, 2 };

MessageTable pl12end_fr_tbl = { msgEndAdrPL12, msgEndCtrPL12 };
