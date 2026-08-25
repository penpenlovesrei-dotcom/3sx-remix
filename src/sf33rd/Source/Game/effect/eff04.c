/**
 * @file eff04.c
 * TODO: identify what this effect does
 */

#include "sf33rd/Source/Game/effect/eff04.h"
#include "bin2obj/char_table.h"
#include "common.h"
#include "sf33rd/Source/Game/effect/effect.h"
#include "sf33rd/Source/Game/engine/charset.h"
#include "sf33rd/Source/Game/engine/workuser.h"
#include "sf33rd/Source/Game/rendering/aboutspr.h"
#include "sf33rd/Source/Game/rendering/texcash.h"
#include "sf33rd/Source/Game/stage/bg.h"

/// Cursor positions per menu layout. The stock menus run diagonally over seven rows; layout 8 is
/// the Custom tracklist, which needs sixteen straight ones, layout 9 the Custom backgrounds, which
/// needs twenty, layout 10 one page of the Custom character colours, and layout 11 the Display
/// page. Rows a layout doesn't use stay zeroed.
const s16 EFF04_Cursor_Data[12][20][2] = {
    { { 16, 156 }, { 32, 135 }, { 48, 114 }, { 64, 93 }, { 80, 72 }, { 96, 51 }, { 112, 30 } },
    { { 16, 164 }, { 32, 142 }, { 48, 120 }, { 64, 98 }, { 80, 76 }, { 96, 54 }, { 112, 32 } },
    { { 32, 140 }, { 48, 108 }, { 64, 76 }, { 112, 44 }, { 0, 0 }, { 0, 0 }, { 0, 0 } },
    { { 48, 156 }, { 64, 124 }, { 80, 92 }, { 96, 60 }, { 112, 28 }, { 0, 0 }, { 0, 0 } },
    { { 32, 156 }, { 48, 132 }, { 64, 108 }, { 80, 84 }, { 96, 60 }, { 112, 36 }, { 0, 0 } },
    { { 24, 132 }, { 48, 92 }, { 112, 52 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } },
    { { -16, 163 }, { 0, 145 }, { 16, 127 }, { 32, 109 }, { 48, 91 }, { 68, 68 }, { 120, 28 } },
    { { 24, 132 }, { 48, 92 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 }, { 0, 0 } },
    // Custom tracklist: one row per stage, sitting four of the small charset's 8px characters left
    // of the soundtrack column and a pixel below its baseline.
    { { -12, 177 }, { -12, 167 }, { -12, 157 }, { -12, 147 }, { -12, 137 }, { -12, 127 }, { -12, 117 },
      { -12, 107 }, { -12, 97 },  { -12, 87 },  { -12, 77 },  { -12, 67 },  { -12, 57 },  { -12, 47 },
      { -12, 37 },  { -12, 27 } },
    // Custom backgrounds: one row per stage, so twenty rather than sixteen. They only fit at 8px
    // apart, which puts the last one at 26 rather than the 28 the stock menus stop at.
    { { -12, 177 }, { -12, 169 }, { -12, 161 }, { -12, 153 }, { -12, 145 }, { -12, 137 }, { -12, 129 },
      { -12, 121 }, { -12, 113 }, { -12, 105 }, { -12, 97 },  { -12, 89 },  { -12, 81 },  { -12, 73 },
      { -12, 65 },  { -12, 57 },  { -12, 49 },  { -12, 41 },  { -12, 33 },  { -12, 25 } },
    // One page of the Custom character colours: five names plus the navigation row, at the option
    // menu's 22px, which is what the large charset wants.
    { { -12, 177 }, { -12, 155 }, { -12, 133 }, { -12, 111 }, { -12, 89 }, { -12, 67 } },
    // The Display page: the sound menu's diagonal of layout 6, but with its sixth row brought back
    // onto the regular 18px step and a seventh added below it, where that menu stops. Cursor x
    // trails the label by 144, as it does there.
    { { -16, 163 }, { 0, 145 }, { 16, 127 }, { 32, 109 }, { 48, 91 }, { 64, 73 }, { 80, 55 }, { 120, 28 } },
};

void effect_04_move(WORK_Other* ewk) {
    if (Menu_Suicide[ewk->master_player]) {
        push_effect_work(&ewk->wu);
        return;
    }

    switch (ewk->wu.routine_no[0]) {
    case 0:
        if (--ewk->wu.dir_timer) {
            break;
        }

        ewk->wu.routine_no[0]++;
        /* fallthrough */

    case 1:
        ewk->wu.position_x = EFF04_Cursor_Data[ewk->wu.type][Menu_Cursor_Y[0]][0] + ewk->wu.dmcal_m;
        ewk->wu.position_y = EFF04_Cursor_Data[ewk->wu.type][Menu_Cursor_Y[0]][1] + 0;
        char_move(&ewk->wu);
        sort_push_request4(&ewk->wu);
        break;
    }
}

s32 effect_04_init(s16 Death_Type, s16 cg_type, s16 sync_bg, s16 priority) {
    WORK_Other* ewk;
    s16 ix;

    if ((ix = pull_effect_work(4)) == -1) {
        return -1;
    }

    ewk = (WORK_Other*)frw[ix];
    ewk->wu.be_flag = 1;
    ewk->wu.disp_flag = 1;
    ewk->wu.id = 4;
    ewk->wu.work_id = 16;
    ewk->wu.my_family = sync_bg + 1;
    ewk->wu.my_col_code = 0x1AC;
    ewk->wu.dir_timer = 20;
    ewk->wu.type = cg_type;
    ewk->master_player = Death_Type;
    ewk->wu.my_priority = ewk->wu.position_z = priority;
    ewk->wu.my_mts = 13;
    ewk->wu.my_trans_mode = get_my_trans_mode(ewk->wu.my_mts);
    ewk->wu.char_table[0] = _sel_pl_char_table;
    ewk->wu.dmcal_m = bg_w.bgw[ewk->wu.my_family - 1].wxy[0].disp.pos;
    set_char_move_init(&ewk->wu, 0, 62);
    return 0;
}
