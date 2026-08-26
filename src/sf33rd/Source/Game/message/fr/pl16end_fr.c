/**
 * @file pl16end_fr.c
 * Makoto Ending Text (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl16end_fr.h"
#include "common.h"

static s8* msgEndPL16_00[1] = { "" };
static s8* msgEndPL16_01[2] = {
    "   J'ai gagn*e... ?!                            ",
    "   J'ai enfin gagn*e !!                         ",
};
static s8* msgEndPL16_02[2] = {
    "   Plus personne ne r*esistera                  ",
    "   `a mes techniques !                          ",
};
static s8* msgEndPL16_03[2] = {
    "   Le nom du dojo Rindoukan r*esonnera          ",
    "   dans tout le pays !                          ",
};
static s8* msgEndPL16_04[2] = {
    "   La nouvelle de la plus jeune ma^itresse      ",
    "   du dojo se r*epand vite...                   ",
};
static s8* msgEndPL16_05[2] = {
    "   Et voil`a que des combattants s^urs          ",
    "   d'eux affluent au dojo Rindoukan.            ",
};
static s8* msgEndPL16_06[1] = { "   Chestoooo !!                                 " };
static s8* msgEndPL16_07[1] = { "   Doshaaaaaah !!                               " };
static s8* msgEndPL16_08[2] = {
    "   Attention ! La file s'arr^ete ici.           ",
    "   Merci de patienter !                         ",
};
static s8* msgEndPL16_09[2] = {
    "   Seuls 30 challengers seront re;cus           ",
    "   aujourd'hui. Vous ^etes bien ici ?!          ",
};
static s8* msgEndPL16_10[2] = {
    "   Masaru... Le dojo est pris d'assaut          ",
    "   depuis le retour de Makoto !                 ",
};
static s8* msgEndPL16_11[2] = {
    "   Jamais autant de gens n'ont voulu            ",
    "   apprendre notre style !                      ",
};
static s8* msgEndPL16_12[2] = {
    "   Oui, tout cela gr^ace `a elle.               ",
    "   Je suis tr`es fier d'elle.                   ",
};
static s8* msgEndPL16_13[2] = {
    "   Je suis son a^in*e, mais je n'ai aucun       ",
    "   talent `a c^ot*e du sien.                    ",
};
static s8* msgEndPL16_14[2] = {
    "   Je peux lui confier l'avenir du dojo         ",
    "   sans la moindre inqui*etude.                 ",
};
static s8* msgEndPL16_15[2] = {
    "   Grand-p`ere, je pars en voyage. Prends       ",
    "   bien soin d'elle en mon absence !            ",
};
static s8* msgEndPL16_16[1] = { "   Seyaaaaaah !!                                " };
static s8* msgEndPL16_17[2] = {
    "   Je n'en ai pas encore assez !                ",
    "   Je ne fais que commencer !!                  ",
};

static s8** msgEndAdrPL16[18] = {
    msgEndPL16_00, msgEndPL16_01, msgEndPL16_02, msgEndPL16_03, msgEndPL16_04, msgEndPL16_05,
    msgEndPL16_06, msgEndPL16_07, msgEndPL16_08, msgEndPL16_09, msgEndPL16_10, msgEndPL16_11,
    msgEndPL16_12, msgEndPL16_13, msgEndPL16_14, msgEndPL16_15, msgEndPL16_16, msgEndPL16_17,
};

static s8 msgEndCtrPL16[18] = { 1, 2, 2, 2, 2, 2, 1, 1, 2, 2, 2, 2, 2, 2, 2, 2, 1, 2 };

MessageTable pl16end_fr_tbl = { msgEndAdrPL16, msgEndCtrPL16 };
