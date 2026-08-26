/**
 * @file pl10end_fr.c
 * Yang Ending Text (fr)
 *
 * Genere par tools/msg_build.py -- ne pas editer a la main.
 * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).
 */

#include "sf33rd/Source/Game/message/fr/pl10end_fr.h"
#include "common.h"

static s8* msgEndPL10_00[1] = { "" };
static s8* msgEndPL10_01[2] = {
    "   Arr^etez ! Vous allez cesser de              ",
    "   vous chamailler, tous les deux !!            ",
};
static s8* msgEndPL10_02[2] = {
    "   C'est toujours pareil ! Occupez-vous         ",
    "   donc un peu de notre ville !                 ",
};
static s8* msgEndPL10_03[2] = {
    "   Vous ^etes partis des semaines               ",
    "   et je me suis fait un sang d'encre !         ",
};
static s8* msgEndPL10_04[2] = {
    "   Vous feriez mieux d'aller crever             ",
    "   au milieu de nulle part !                    ",
};
static s8* msgEndPL10_05[2] = {
    "   Surveille ton langage ! Tu n'as              ",
    "   aucune id*ee de ce qu'on a v*ecu !           ",
};
static s8* msgEndPL10_06[2] = {
    "   Cette ville aurait eu de gros ennuis         ",
    "   si on ne s'*etait pas battus !               ",
};
static s8* msgEndPL10_07[2] = {
    "   Et alors plus personne n'aurait rien         ",
    "   `a faire de ton riz saut*e infect !          ",
};
static s8* msgEndPL10_08[2] = {
    "   Infect, tu as dit ?!                         ",
    "   R*ep`ete un peu !                            ",
};
static s8* msgEndPL10_09[2] = {
    "   Oh non... Comme je le pensais, Hoimei        ",
    "   doit ^etre amoureuse de mon fr`ere...        ",
};
static s8* msgEndPL10_10[1] = { "   Je ne gagnerai jamais...                     " };
static s8* msgEndPL10_11[1] = { "   Ma soeur est vraiment maladroite...          " };
static s8* msgEndPL10_12[2] = {
    "   Elle s'inqui*etait. Elle a du mal `a         ",
    "   exprimer son soulagement.                    ",
};
static s8* msgEndPL10_13[2] = {
    "   Tu sais, elle n'a rien aval*e                ",
    "   pendant votre absence...                     ",
};
static s8* msgEndPL10_14[1] = { "   Shaomei...                                   " };
static s8* msgEndPL10_15[2] = {
    "   Je tiens `a la ville, mais je tiens          ",
    "   bien plus `a vous deux...                    ",
};
static s8* msgEndPL10_16[2] = {
    "   Alors s'il vous pla^it...                    ",
    "   Ne soyez pas si imprudents, d'accord ?       ",
};
static s8* msgEndPL10_17[2] = {
    "   Oui... Je comprends. D*esol*e de             ",
    "   t'avoir inqui*et*ee.                         ",
};
static s8* msgEndPL10_18[2] = {
    "   (Il n'y a pas que ma soeur... Moi            ",
    "   aussi je dois ^etre honn^ete...)             ",
};
static s8* msgEndPL10_19[1] = { "   (Il faut que je sois courageux !)            " };

static s8** msgEndAdrPL10[20] = {
    msgEndPL10_00, msgEndPL10_01, msgEndPL10_02, msgEndPL10_03, msgEndPL10_04, msgEndPL10_05,
    msgEndPL10_06, msgEndPL10_07, msgEndPL10_08, msgEndPL10_09, msgEndPL10_10, msgEndPL10_11,
    msgEndPL10_12, msgEndPL10_13, msgEndPL10_14, msgEndPL10_15, msgEndPL10_16, msgEndPL10_17,
    msgEndPL10_18, msgEndPL10_19,
};

static s8 msgEndCtrPL10[20] = { 1, 2, 2, 2, 2, 2, 2, 2, 2, 2, 1, 1, 2, 2, 1, 2, 2, 2, 2, 1 };

MessageTable pl10end_fr_tbl = { msgEndAdrPL10, msgEndCtrPL10 };
