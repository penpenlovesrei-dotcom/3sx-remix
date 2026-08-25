/**
 * @file pl06end_fr.c
 * Hugo Ending Text (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl06end_fr.h"
#include "common.h"

static s8* msgEndPL06_00[1] = { "" };
static s8* msgEndPL06_01[2] = {
    "   La salle explose de ferveur                  ",
    "   ce soir !                                    ",
};
static s8* msgEndPL06_02[2] = {
    "   Le champion du monde par *equipes            ",
    "   vient d'^etre d*esign*e !                    ",
};
static s8* msgEndPL06_03[1] = { "" };
static s8* msgEndPL06_04[1] = { "   Euh... Un tremblement de terre !!            " };
static s8* msgEndPL06_05[2] = {
    "   D*esol*e de couper, mais nous avons          ",
    "   une annonce importante...                    ",
};
static s8* msgEndPL06_06[2] = {
    "   Nous venons de la H.W.A. !                   ",
    "   ...La Huge Wrestling Army !                  ",
};
static s8* msgEndPL06_07[2] = {
    "   `A compter de maintenant,                    ",
    "   vous nous appartenez !                       ",
};
static s8* msgEndPL06_08[2] = {
    "   Si vous avez une objection, il               ",
    "   faudra d'abord battre notre Hugo !           ",
};
static s8* msgEndPL06_09[2] = {
    "   Plus de 50 ont d*ej`a essay*e et sont        ",
    "   tous devenus nos soldats !                   ",
};
static s8* msgEndPL06_10[2] = {
    "   Oh non... Qu'est-ce que je fais l`a ?        ",
    "   H*e... Ryu ?!                                ",
};
static s8* msgEndPL06_11[2] = {
    "   Hmm. Cela pourrait ^etre exaltant.           ",
    "   Voil`a une bonne *epreuve !                  ",
};
static s8* msgEndPL06_12[2] = {
    "   (Ryu ! Je ne peux pas croire que tu          ",
    "   t'amuses dans un moment pareil !)            ",
};
static s8* msgEndPL06_13[2] = {
    "   Alors ? Vous avez peur de nos                ",
    "   membres, ou quoi ?!                          ",
};
static s8* msgEndPL06_14[2] = {
    "   Pas d'objection ? Parfait ! Ce ring          ",
    "   devient notre base d'op*erations !           ",
};

static s8** msgEndAdrPL06[15] = {
    msgEndPL06_00, msgEndPL06_01, msgEndPL06_02, msgEndPL06_03, msgEndPL06_04, msgEndPL06_05,
    msgEndPL06_06, msgEndPL06_07, msgEndPL06_08, msgEndPL06_09, msgEndPL06_10, msgEndPL06_11,
    msgEndPL06_12, msgEndPL06_13, msgEndPL06_14,
};

static s8 msgEndCtrPL06[15] = { 1, 2, 2, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2 };

MessageTable pl06end_fr_tbl = { msgEndAdrPL06, msgEndCtrPL06 };
