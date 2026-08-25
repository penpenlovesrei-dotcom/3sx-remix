/**
 * @file pl07end_fr.c
 * Ibuki Ending Text (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl07end_fr.h"
#include "common.h"

static s8* msgEndPL07_00[1] = { "" };
static s8* msgEndPL07_01[2] = {
    "   \"Universit*e Sarusuberi\"...                  ",
    "   J'y suis arriv*ee !                          ",
};
static s8* msgEndPL07_02[2] = {
    "   Apr`es une vie d'entra^inement, je vais      ",
    "   enfin vivre comme une fille normale !        ",
};
static s8* msgEndPL07_03[2] = {
    "   D*ecouvrir le campus... Me faire des         ",
    "   amis... Je suis tout excit*ee !              ",
};
static s8* msgEndPL07_04[1] = { "   Salut, jolie demoiselle !                    " };
static s8* msgEndPL07_05[2] = {
    "   Tu ne veux pas rejoindre mon club ?          ",
    "   C'est si sympa qu'on n'en part plus !        ",
};
static s8* msgEndPL07_06[2] = {
    "   (Et donc je me suis consacr*ee aux           ",
    "   joyeuses activit*es du club...               ",
};
static s8* msgEndPL07_07[2] = {
    "   Un entra^inement d'endurance atroce          ",
    "   sous la houlette des anciens...              ",
};
static s8* msgEndPL07_08[2] = {
    "   Je m'entra^ine `a la surface                 ",
    "   de l'eau...                                  ",
};
static s8* msgEndPL07_09[2] = {
    "   Et je chevauche un cerf-volant en            ",
    "   pleine temp^ete...) H*e ! Une minute !       ",
};
static s8* msgEndPL07_10[2] = {
    "   Ha ha ha ! Ibuki ! Tu as encore              ",
    "   un angle mort !                              ",
};
static s8* msgEndPL07_11[2] = {
    "   Si tu restes aussi n*egligente, je te        ",
    "   tranche la carotide, la prochaine fois !     ",
};
static s8* msgEndPL07_12[2] = {
    "   Ha ha ha ! Je vois que tu adores             ",
    "   les frissons du ninjutsu !                   ",
};
static s8* msgEndPL07_13[1] = { "   ...Quoi ?                                    " };
static s8* msgEndPL07_14[1] = { "   ...Ce n'est pas ce que j'esp*erais !         " };

static s8** msgEndAdrPL07[15] = {
    msgEndPL07_00, msgEndPL07_01, msgEndPL07_02, msgEndPL07_03, msgEndPL07_04, msgEndPL07_05,
    msgEndPL07_06, msgEndPL07_07, msgEndPL07_08, msgEndPL07_09, msgEndPL07_10, msgEndPL07_11,
    msgEndPL07_12, msgEndPL07_13, msgEndPL07_14,
};

static s8 msgEndCtrPL07[15] = { 1, 2, 2, 2, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1 };

MessageTable pl07end_fr_tbl = { msgEndAdrPL07, msgEndCtrPL07 };
