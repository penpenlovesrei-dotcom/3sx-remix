/**
 * @file pl03tlk_fr.c
 * Yun Pre-Fight Dialogue (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl03tlk_fr.h"
#include "common.h"

static s8* msgTlkPL03_00P[1] = { "" };
static s8* msgTlkPL03_01P[1] = { "  Alors c'est toi, Gill...                      " };
static s8* msgTlkPL03_02P[2] = {
    "  C'est quoi ce plan de conqu^ete du            ",
    "  monde ?! R*eveille-toi un peu !               ",
};
static s8* msgTlkPL03_03P[2] = {
    "  La jeunesse est imprudente, mais              ",
    "  je ne t'en tiens pas rigueur.                 ",
};
static s8* msgTlkPL03_04P[2] = {
    "  R*efl*echis... Quelle serait la               ",
    "  vie id*eale, pour toi ?                       ",
};
static s8* msgTlkPL03_05P[2] = {
    "  Un gar;con comme toi devrait le voir.         ",
    "  Remets-t'en simplement `a moi !               ",
};
static s8* msgTlkPL03_06P[2] = {
    "  Arrrgh ! Arr^ete de me sermonner !            ",
    "  Que nos poings parlent !                      ",
};

static s8** msgTalkAdrPL03[7] = {
    msgTlkPL03_00P, msgTlkPL03_01P, msgTlkPL03_02P, msgTlkPL03_03P, msgTlkPL03_04P, msgTlkPL03_05P,
    msgTlkPL03_06P,
};

static s8 msgTalkCtrPL03[7] = { 1, 1, 2, 2, 2, 2, 2 };

MessageTable pl03tlk_fr_tbl = { msgTalkAdrPL03, msgTalkCtrPL03 };
