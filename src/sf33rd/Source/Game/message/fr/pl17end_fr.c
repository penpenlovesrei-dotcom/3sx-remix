/**
 * @file pl17end_fr.c
 * Q Ending Text (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl17end_fr.h"
#include "common.h"

static s8* msgEndPL17_00[1] = { "" };
static s8* msgEndPL17_01[2] = {
    "   13 affaires *etranges en 10 jours,           ",
    "   un peu partout dans le monde...              ",
};
static s8* msgEndPL17_02[2] = {
    "   En voyant ces photos prises sur              ",
    "   place, vous ne remarquez rien ?              ",
};
static s8* msgEndPL17_03[2] = {
    "   Alors, Juliana ? Pas besoin de               ",
    "   tourner autour du pot avec moi !             ",
};
static s8* msgEndPL17_04[2] = {
    "   Vous alliez dire qu'un type louche           ",
    "   appara^it sur chaque sc`ene ?                ",
};
static s8* msgEndPL17_05[2] = {
    "   David... Vous avez peut-^etre un don         ",
    "   de t*el*epathie, finalement.                 ",
};
static s8* msgEndPL17_06[2] = {
    "   Regardez... Sur chaque photo, on             ",
    "   voit un homme en trench-coat.                ",
};
static s8* msgEndPL17_07[2] = {
    "   Impossible ! Ces affaires ont eu             ",
    "   lieu aux quatre coins du monde !             ",
};
static s8* msgEndPL17_08[1] = { "   Ce ne peut pas ^etre le m^eme homme !        " };
static s8* msgEndPL17_09[2] = {
    "   Ils ont au moins les m^emes go^uts           ",
    "   vestimentaires...                            ",
};
static s8* msgEndPL17_10[2] = {
    "   Quoi qu'il en soit, cet \"inconnu\"            ",
    "   relie toutes ces affaires.                   ",
};
static s8* msgEndPL17_11[2] = {
    "   Alors, avez-vous                             ",
    "   identifi*e cet homme ?                       ",
};
static s8* msgEndPL17_12[1] = { "   Malheureusement, pas encore...               " };
static s8* msgEndPL17_13[2] = {
    "   Mais l'analyse des photos nous a             ",
    "   permis de reconstituer son visage.           ",
};
static s8* msgEndPL17_14[2] = {
    "   Enfin, pas exactement son visage...          ",
    "   Mais... regardez plut^ot.                    ",
};
static s8* msgEndPL17_15[2] = {
    "   Qu'est-ce que c'est ?!                       ",
    "   Un masque... Un masque de fer ?              ",
};
static s8* msgEndPL17_16[2] = {
    "   Bien ! Diffusez cette photo `a toutes        ",
    "   nos antennes, niveau de s*ecurit*e 4 !       ",
};
static s8* msgEndPL17_17[2] = {
    "   Ouvrez imm*ediatement une enqu^ete           ",
    "   sur cet homme. Rompez !                      ",
};

static s8** msgEndAdrPL17[18] = {
    msgEndPL17_00, msgEndPL17_01, msgEndPL17_02, msgEndPL17_03, msgEndPL17_04, msgEndPL17_05,
    msgEndPL17_06, msgEndPL17_07, msgEndPL17_08, msgEndPL17_09, msgEndPL17_10, msgEndPL17_11,
    msgEndPL17_12, msgEndPL17_13, msgEndPL17_14, msgEndPL17_15, msgEndPL17_16, msgEndPL17_17,
};

static s8 msgEndCtrPL17[18] = { 1, 2, 2, 2, 2, 2, 2, 2, 1, 2, 2, 2, 1, 2, 2, 2, 2, 2 };

MessageTable pl17end_fr_tbl = { msgEndAdrPL17, msgEndCtrPL17 };
