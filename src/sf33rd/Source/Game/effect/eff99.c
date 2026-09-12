/**
 * @file eff99.c
 * TODO: identify what this effect does
 */

#include "sf33rd/Source/Game/effect/eff99.h"
#include "common.h"
#include "port/video/trace_fin.h"
#include "sf33rd/Source/Game/effect/effect.h"
#include "sf33rd/Source/Game/engine/workuser.h"
#include "sf33rd/Source/Game/rendering/aboutspr.h"
#include "sf33rd/Source/Game/rendering/texcash.h"
#include "sf33rd/Source/Game/stage/bg.h"

void Setup_Letter_99(WORK_Other_CONN* ewk, s16 letter_index, s16 disp_index);

const s16 Pos_Data_99[5][3] = { { -144, 128, 23 }, { 48, 128, 23 }, { 8, 54, 23 }, { 0, 42, 23 }, { 0, 30, 23 } };

const s8* Letter_Data_99[5][58] = {
    { ";;;;;;;#", ";;;;;;##", ";;;;;###", ";;;;####", ";;;#####", ";;######", ";#######", "########" },
    { "#;;;;;;;", "##;;;;;;", "###;;;;;", "####;;;;", "#####;;;", "######;;", "#######;", "########" },
    { "UNKNOWN", "AMERICA", "JAPAN",  "HONG KONG", "ENGLAND", "RUSSIA", "GERMANY",
      "JAPAN",   "KENYA",   "BRAZIL", "HONG KONG", "AMERICA", "BRAZIL", "MEXICO",
      "JAPAN",   "CHINA",   "JAPAN",  "",          "RUSSIA",  "FRANCE", "RANDOM",
      "",
      "2ND IMPACT",
      "2ND IMPACT",
      "2ND IMPACT",
      "2ND IMPACT",
      "2ND IMPACT",
      "2ND IMPACT",
      "2ND IMPACT",
      "2ND IMPACT",
      "2ND IMPACT",
      "2ND IMPACT",
      "2ND IMPACT",
      "2ND IMPACT",
      "2ND IMPACT",
      "2ND IMPACT",
      "2ND IMPACT",
      "HIGH SEAS",
      "AMERICA",
      "AMERICA",
      "JAPAN",
      "JAPAN",
      "HONG KONG",
      "HONG KONG",
      "ENGLAND",
      "ENGLAND",
      "RUSSIA",
      "GERMANY",
      "JAPAN",
      "JAPAN",
      "JAPAN",
      "KENYA",
      "KENYA",
      "BRAZIL",
      "HONG KONG",
      "HONG KONG",
      "2ND IMPACT",
      "2ND IMPACT" },
    { "GILL STAGE",
      "SUBWAY STATION",
      "SUZAKU CASTLE ROOFTOP",
      "SHOPPING DISTRICT",
      "MAIN STREET",
      "MOSQUE",
      "HOME SWEET HOME",
      "A ROAD IN KYOTO",
      "SAVANNA",
      "SANTOS HARBOR",
      "SHOPPING DISTRICT",
      "SUBWAY STATION",
      "SANTOS HARBOR",
      "ORMECA RUINS",
      "KOUSYU STREET",
      "CHINESE RESTAURANT",
      "THE DOJO OF RINDO-KAN",
      "",
      "MOSQUE",
      "CLUB METRO",
      "",
      "",
      "GILL STAGE",
      "ALEX STAGE",
      "RYU STAGE",
      "YUN STAGE",
      "DUDLEY STAGE",
      "NECRO STAGE",
      "HUGO STAGE",
      "IBUKI STAGE",
      "ELENA STAGE",
      "ORO STAGE",
      "YANG STAGE",
      "KEN STAGE",
      "SEAN STAGE",
      "URIEN STAGE",
      "GORGE STAGE",
      "NG GILL",
      "NG ALEX",
      "NG SEAN",
      "NG RYU",
      "NG KEN",
      "NG YUN 1",
      "NG YUN 2",
      "NG DUDLEY 1",
      "NG DUDLEY 2",
      "NG NECRO",
      "NG HUGO",
      "NG IBUKI 1",
      "NG IBUKI 2",
      "NG IBUKI 3",
      "NG ELENA 1",
      "NG ELENA 2",
      "NG ORO",
      "NG YANG 1",
      "NG YANG 2",
      "2ND IMPACT BG08",
      "2ND IMPACT BG10"  },
    { "",
      "ALEX STAGE",
      "RYU STAGE",
      "YUN STAGE",
      "DUDLEY STAGE",
      "NECRO STAGE",
      "HUGO STAGE",
      "IBUKI STAGE",
      "ELENA STAGE",
      "ORO STAGE",
      "YANG STAGE",
      "KEN STAGE",
      "SEAN STAGE",
      "URIEN STAGE",
      "AKUMA STAGE",
      "CHUN-LI STAGE",
      "MAKOTO STAGE",
      "",
      "TWELVE STAGE",
      "REMY STAGE",
      "",
      "",
      "2ND IMPACT BG00",
      "2ND IMPACT BG01",
      "2ND IMPACT BG02",
      "2ND IMPACT BG03",
      "2ND IMPACT BG04",
      "2ND IMPACT BG05",
      "2ND IMPACT BG06",
      "2ND IMPACT BG07",
      "2ND IMPACT BG09",
      "2ND IMPACT BG0A",
      "2ND IMPACT BG0B",
      "2ND IMPACT BG0C",
      "2ND IMPACT BG0D",
      "2ND IMPACT BG0E",
      "2ND IMPACT BG0F",
      "NG GILL",
      "NG ALEX",
      "NG SEAN",
      "NG RYU",
      "NG KEN",
      "NG YUN 1",
      "NG YUN 2",
      "NG DUDLEY 1",
      "NG DUDLEY 2",
      "NG NECRO",
      "NG HUGO",
      "NG IBUKI 1",
      "NG IBUKI 2",
      "NG IBUKI 3",
      "NG ELENA 1",
      "NG ELENA 2",
      "NG ORO",
      "NG YANG 1",
      "NG YANG 2",
      "2ND IMPACT BG08",
      "2ND IMPACT BG10"  }
};

void effect_99_move(WORK_Other_CONN* ewk) {
    if (Menu_Suicide[ewk->master_player]) {
        push_effect_work(&ewk->wu);
        return;
    }

    switch (ewk->wu.type) {
    case 0:
        Setup_Letter_99(ewk, ewk->wu.dir_step, Vital_Handicap[Present_Mode][ewk->master_id]);
        break;

    case 1:
        Setup_Letter_99(ewk, ewk->wu.dir_step, VS_Stage);
        break;
    }

    sort_push_request3(&ewk->wu);
}

s32 effect_99_init(s16 id, s16 type, s16 char_offset, s16 letter_index, s16 pos_index, s16 master_player) {
    WORK_Other_CONN* ewk;
    s16 ix;

    if ((ix = pull_effect_work(4)) == -1) {
        return -1;
    }

    ewk = (WORK_Other_CONN*)frw[ix];
    ewk->wu.be_flag = 1;
    ewk->wu.disp_flag = 1;
    ewk->wu.id = 99;
    ewk->wu.work_id = 16;
    ewk->wu.my_col_code = 0x1AC;
    ewk->wu.my_family = 3;
    ewk->master_id = id;
    ewk->wu.type = type;
    ewk->wu.old_cgnum = char_offset;
    ewk->wu.dir_step = letter_index;
    ewk->master_priority = pos_index;
    ewk->master_player = master_player;
    ewk->wu.my_mts = 13;
    ewk->wu.my_trans_mode = get_my_trans_mode(ewk->wu.my_mts);
    ewk->wu.position_x = bg_w.bgw[ewk->wu.my_family - 1].wxy[0].disp.pos + Pos_Data_99[pos_index][0];
    ewk->wu.position_y = bg_w.bgw[ewk->wu.my_family - 1].wxy[1].disp.pos + Pos_Data_99[pos_index][1];
    ewk->wu.position_z = Pos_Data_99[pos_index][2];
    return 0;
}

void Setup_Letter_99(WORK_Other_CONN* ewk, s16 letter_index, s16 disp_index) {
    s16 x;
    s16 ix;
    s16 offset_x;
    u8* ptr;
    u8 space;

    if (ewk->wu.old_cgnum == 0x70A7) {
        offset_x = 8;
    } else {
        offset_x = 14;
    }

    /* LE GARDE-FOU DE L'ECRAN DE SELECTION, pose le 31/08/2026.

       `Setup_Letter_99` est appelee avec `VS_Stage` en `disp_index`, et le selecteur va
       desormais jusqu'a 57. La table s'arretait a 37 : pour les etages de New Generation
       le pointeur lu venait d'APRES le tableau, et le `while (*ptr)` juste en dessous
       partait dans la memoire au hasard. C'est le plantage vu en arrivant sur les decors
       de NG dans le selecteur.

       La table est etendue plus bas. Ce garde reste pour que tout autre debordement se
       SIGNALE dans `fin-de-round.log` au lieu de tuer le jeu -- une ligne manquante vaut
       mieux qu'un plantage, et on saura laquelle. */
    if (letter_index < 0 || letter_index >= 5 || disp_index < 0 || disp_index >= 58 ||
        Letter_Data_99[letter_index][disp_index] == NULL) {
        TraceFin("Setup_Letter_99 hors bornes : ligne %d, etage %d, %d lignes\n",
                 (s32)letter_index, (s32)disp_index, 5);
        return;
    }

    ptr = (u8*)Letter_Data_99[letter_index][disp_index];
    ix = 0;
    x = 0;
    space = 0;

    while (*ptr != '\0') {
        if (*ptr == ' ') {
            x += offset_x;
            ptr++;
            space++;
            continue;
        }

        ewk->conn[ix].nx = x;
        ewk->conn[ix].ny = 0;
        ewk->conn[ix].col = 0;
        ewk->conn[ix].chr = ewk->wu.old_cgnum + *ptr;
        x += offset_x;
        ptr++;
        ix++;
    }

    ewk->num_of_conn = ix;

    if (ewk->wu.type != 1) {
        return;
    }

    if (ewk->wu.old_cgnum == 0x7047) {
        x = 16;
    } else {
        x = 8;
    }

    x = x * (ix + space) / 2;

    ewk->wu.position_x = bg_w.bgw[ewk->wu.my_family - 1].wxy[0].disp.pos + Pos_Data_99[ewk->master_priority][0] - x;
}
