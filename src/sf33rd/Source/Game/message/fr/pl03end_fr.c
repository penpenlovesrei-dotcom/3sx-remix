/**
 * @file pl03end_fr.c
 * Yun Ending Text (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl03end_fr.h"
#include "common.h"

static s8* msgEndPL03_00[1] = { "" };
static s8* msgEndPL03_01[1] = { "   Quelle magnifique prestation !               " };
static s8* msgEndPL03_02[2] = {
    "   En signe de respect, je te confie            ",
    "   cette ville.                                 ",
};
static s8* msgEndPL03_03[2] = {
    "   Tu recevras aussi les plus hauts             ",
    "   privil`eges dans mon dessein.                ",
};
static s8* msgEndPL03_04[2] = {
    "   H*e, cr*etin ! Laisse tomber !               ",
    "   Ton plan ne vaut absolument rien !           ",
};
static s8* msgEndPL03_05[1] = { "   Une soci*et*e id*eale ? R*eveille-toi !      " };
static s8* msgEndPL03_06[2] = {
    "   Je propose le plan le plus rationnel         ",
    "   et le plus juste pour tous.                  ",
};
static s8* msgEndPL03_07[2] = {
    "   Je ne te forcerai pas `a me                  ",
    "   suivre... C'est ton choix.                   ",
};
static s8* msgEndPL03_08[1] = { "   Mais... je n'ai pas de temps `a perdre.      " };
static s8* msgEndPL03_09[2] = {
    "   Deux forces contraires nous                  ",
    "   accompagnent depuis l'origine...             ",
};
static s8* msgEndPL03_10[2] = {
    "   La naissance et la mort, la cr*eation        ",
    "   et la destruction, l'amour, la haine.        ",
};
static s8* msgEndPL03_11[2] = {
    "   Leur *equilibre va s'effondrer               ",
    "   dans un avenir proche !                      ",
};
static s8* msgEndPL03_12[2] = {
    "   Pour assurer notre survie, je propose        ",
    "   la symbiose de ces deux forces.              ",
};
static s8* msgEndPL03_13[1] = { "   Ha ha ha ha ! Je me demande...               " };
static s8* msgEndPL03_14[2] = {
    "   Comment ces combattants vont-ils             ",
    "   survivre `a la destruction... ?              ",
};
static s8* msgEndPL03_15[2] = {
    "   Ce sera un petit plaisir                     ",
    "   que de le d*ecouvrir.                        ",
};
static s8* msgEndPL03_16[2] = {
    "   Grand fr`ere... J'ai un mauvais              ",
    "   pressentiment.                               ",
};
static s8* msgEndPL03_17[1] = { "   Ses mots... Ils me troublent.                " };
static s8* msgEndPL03_18[2] = {
    "   H*e... Ressaisis-toi, Yang !                 ",
    "   On est les chefs de cette ville !            ",
};
static s8* msgEndPL03_19[2] = {
    "   On ne va pas laisser cet apprenti            ",
    "   dieu faire ce qu'il veut, si ?               ",
};
static s8* msgEndPL03_20[2] = {
    "   Rentrons en ville !                          ",
    "   On r*ealisera nos propres r^eves !           ",
};

static s8** msgEndAdrPL03[21] = {
    msgEndPL03_00, msgEndPL03_01, msgEndPL03_02, msgEndPL03_03, msgEndPL03_04, msgEndPL03_05,
    msgEndPL03_06, msgEndPL03_07, msgEndPL03_08, msgEndPL03_09, msgEndPL03_10, msgEndPL03_11,
    msgEndPL03_12, msgEndPL03_13, msgEndPL03_14, msgEndPL03_15, msgEndPL03_16, msgEndPL03_17,
    msgEndPL03_18, msgEndPL03_19, msgEndPL03_20,
};

static s8 msgEndCtrPL03[21] = { 1, 1, 2, 2, 2, 1, 2, 2, 1, 2, 2, 2, 2, 1, 2, 2, 2, 1, 2, 2, 2 };

MessageTable pl03end_fr_tbl = { msgEndAdrPL03, msgEndCtrPL03 };
