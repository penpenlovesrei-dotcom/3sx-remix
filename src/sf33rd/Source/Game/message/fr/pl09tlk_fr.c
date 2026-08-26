/**
 * @file pl09tlk_fr.c
 * Oro Pre-Fight Dialogue (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl09tlk_fr.h"
#include "common.h"

static s8* msgTlkPL09_00P[1] = { "" };
static s8* msgTlkPL09_01P[2] = {
    "  Oh ! Tu poss`edes un niveau de                ",
    "  chi absolument incroyable !                   ",
};
static s8* msgTlkPL09_02P[2] = {
    "  C'est ce qu'on appelle... le mal ?            ",
    "  Impressionnant, pour un jeune homme !         ",
};
static s8* msgTlkPL09_03P[1] = { "  J'ai entendu parler de toi, sennin.           " };
static s8* msgTlkPL09_04P[2] = {
    "  Surveille tes mots, ou ils                    ",
    "  annonceront ta destruction.                   ",
};
static s8* msgTlkPL09_05P[2] = {
    "  Tu te pr*etends ma^itre du poing...           ",
    "  Cela me trouble...                            ",
};
static s8* msgTlkPL09_06P[2] = {
    "  La voie de la vraie ma^itrise est bien        ",
    "  plus rude. Empruntons-la...                   ",
};

static s8** msgTalkAdrPL09[7] = {
    msgTlkPL09_00P, msgTlkPL09_01P, msgTlkPL09_02P, msgTlkPL09_03P, msgTlkPL09_04P, msgTlkPL09_05P,
    msgTlkPL09_06P,
};

static s8 msgTalkCtrPL09[7] = { 1, 2, 2, 1, 2, 2, 2 };

MessageTable pl09tlk_fr_tbl = { msgTalkAdrPL09, msgTalkCtrPL09 };
