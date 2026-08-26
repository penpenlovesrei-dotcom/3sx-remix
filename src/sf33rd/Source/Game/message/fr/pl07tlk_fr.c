/**
 * @file pl07tlk_fr.c
 * Ibuki Pre-Fight Dialogue (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl07tlk_fr.h"
#include "common.h"

static s8* msgTlkPL07_00P[1] = { "" };
static s8* msgTlkPL07_01P[1] = { "  Excusez-moi, vous ^etes un sennin ?           " };
static s8* msgTlkPL07_02P[2] = {
    "  C'est exact. Je suis le grand sennin !        ",
    "  Que veux-tu, petite ?                         ",
};
static s8* msgTlkPL07_03P[2] = {
    "  (Il est vieux comme le monde, mais            ",
    "  ;ca doit ^etre un ma^itre, j'imagine...)      ",
};
static s8* msgTlkPL07_04P[2] = {
    "  C'est un peu bizarre, mais je suis            ",
    "  en plein examen de fin d'*etudes.             ",
};
static s8* msgTlkPL07_05P[2] = {
    "  Je ne serai re;cue que si je vous             ",
    "  bats en 5 minutes... Alors...                 ",
};
static s8* msgTlkPL07_06P[1] = { "  Battez-vous avec moi !                        " };
static s8* msgTlkPL07_07P[2] = {
    "  Quoi ?! Je croyais que tu voulais             ",
    "  un rendez-vous ! Quelle d*eception !          ",
};

static s8** msgTalkAdrPL07[8] = {
    msgTlkPL07_00P, msgTlkPL07_01P, msgTlkPL07_02P, msgTlkPL07_03P, msgTlkPL07_04P, msgTlkPL07_05P,
    msgTlkPL07_06P, msgTlkPL07_07P,
};

static s8 msgTalkCtrPL07[8] = { 1, 1, 2, 2, 2, 2, 1, 2 };

MessageTable pl07tlk_fr_tbl = { msgTalkAdrPL07, msgTalkCtrPL07 };
