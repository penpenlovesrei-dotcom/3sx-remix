/**
 * @file eff18.c
 * TODO: identify what this effect does
 */

#include "sf33rd/Source/Game/effect/eff18.h"
#include "common.h"
#include "sf33rd/Source/Game/effect/effb6.h"
#include "sf33rd/Source/Game/effect/effect.h"
#include "sf33rd/Source/Game/engine/workuser.h"
#include "sf33rd/Source/Game/rendering/aboutspr.h"
#include "sf33rd/Source/Game/stage/bg.h"

void Setup_Pos_18(WORK_Other_CONN* ewk);
void Check_TenTen(WORK_Other_CONN* ewk);

void effect_18_move(WORK_Other_CONN* ewk) {
    if (Menu_Suicide[ewk->master_player]) {
        push_effect_work(&ewk->wu);
        return;
    }

    if (Menu_Cursor_Y[0] == ewk->wu.type) {
        ewk->wu.my_clear_level = 0;
    } else {
        ewk->wu.my_clear_level = 128;
    }

    sort_push_request3(&ewk->wu);
}

/// @param y_base Row zero's height. The System Direction menu's own 199 leaves no room above it,
/// which the Custom character colours screen needs for its page indicator.
/// @param x_base Left margin. The Custom tracklist starts further left than the others, its value
/// column having to hold soundtrack names of any length.
s32 effect_18_init(s16 disp_index, s16 cursor_id, s16 sync_bg, s16 master_player, s16 y_base, s16 x_base) {
    WORK_Other_CONN* ewk;
    s16 ix;

    if ((ix = pull_effect_work(4)) == -1) {
        return -1;
    }

    ewk = (WORK_Other_CONN*)frw[ix];
    ewk->wu.routine_no[0] = 0;
    ewk->wu.be_flag = 1;
    ewk->wu.disp_flag = 1;
    ewk->wu.id = 18;
    ewk->wu.work_id = 16;
    ewk->wu.rl_flag = 0;
    ewk->wu.my_col_code = 428;
    ewk->wu.my_family = sync_bg + 1;
    ewk->wu.type = cursor_id;
    ewk->wu.dir_step = y_base;
    ewk->wu.dir_old = x_base;
    ewk->master_player = master_player;
    get_message_conn_data(ewk, 3, 0, disp_index);
    ewk->wu.my_mts = 12;
    Setup_Pos_18(ewk);
    return 0;
}

void Setup_Pos_18(WORK_Other_CONN* ewk) {
    ewk->wu.position_x = bg_w.bgw[ewk->wu.my_family - 1].wxy[0].disp.pos + ewk->wu.dir_old;
    ewk->wu.position_y = bg_w.bgw[ewk->wu.my_family - 1].wxy[1].disp.pos + ewk->wu.dir_step - ewk->wu.type * 18;
    ewk->wu.position_z = 68;
    Check_TenTen(ewk);
}

void Check_TenTen(WORK_Other_CONN* ewk) {
    s16 ix;

    for (ix = 0; ix < ewk->num_of_conn; ix++) {
        if (ewk->conn[ix].chr == 0x855B) {
            ewk->conn[ix].chr = 0x80EA;
        }

        if (ewk->conn[ix].chr == 0x862C) {
            ewk->conn[ix].chr = 0x80EB;
        }
    }
}
