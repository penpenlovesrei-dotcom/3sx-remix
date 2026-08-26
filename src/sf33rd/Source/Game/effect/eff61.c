/**
 * @file eff61.c
 * Menu options
 */

#include "sf33rd/Source/Game/effect/eff61.h"
#include "common.h"
#include "sf33rd/Source/Game/effect/effect.h"
#include "sf33rd/Source/Game/engine/workuser.h"
#include "sf33rd/Source/Game/rendering/aboutspr.h"
#include "sf33rd/Source/Game/rendering/texcash.h"
#include "sf33rd/Source/Game/screen/sel_data.h"
#include "sf33rd/Source/Game/stage/bg.h"

void EFF61_WAIT(WORK_Other_CONN* ewk);
void EFF61_SLIDE_IN(WORK_Other_CONN* ewk);
void EFF61_SLIDE_OUT(WORK_Other_CONN* /* unused */);
void EFF61_SUDDENLY(WORK_Other_CONN* ewk);

const s8* Menu_Letter_Data[174] = { "ARCADE",
                                   "VERSUS",
                                   "TRAINING",
                                   "SYSTEM DIRECTION",
#if NETPLAY_ENABLED
                                   "NETWORK",
#else
                                   "REPLAY",
#endif
                                   "OPTION",
                                   "EXIT GAME",
                                   "GAME OPTION",
                                   "BUTTON CONFIG.",
                                   "DISPLAY",
                                   "SOUND",
                                   "SAVE#/#LOAD",
                                   "EXTRA OPTION",
                                   "EXIT",
                                   "X POSITION^^^",
                                   "Y POSITION^^^",
                                   "X RANGE^^^^^^",
                                   "Y RANGE^^^^^^",
                                   "LANGUAGE^^^^^",
                                   "DEFAULT SETTING",
                                   "EXIT",
                                   "SAVE  DATA",
                                   "LOAD  DATA",
                                   "EXIT",
                                   "",
                                   "DIFFICULTY^^^^^^ L         #H",
                                   "TIME LIMIT^^^^^^",
                                   "ROUNDS(1P)^^^^^^",
                                   "ROUNDS(VS)^^^^^^",
                                   "DAMAGE LEVEL^^^^ L     #H",
                                   "GUARD JUDGMENT^^",
                                   "ANALOG STICK^^^^",
                                   "HANDICAP(VS)^^^^",
                                   "PLAYER1(VS)^^^^^",
                                   "PLAYER2(VS)^^^^^",
                                   "DEFAULT SETTING",
                                   "EXIT",
                                   "CONTINUE",
                                   "REPLAY SAVE",
                                   "EXIT",
                                   "CONTINUE",
                                   "REPLAY SAVE",
                                   "EXIT",
                                   "DIRECTION",
                                   "SAVE",
                                   "LOAD",
                                   "EXIT",
                                   "GAME OPTION",
                                   "BUTTON CONFIG.",
                                   "DISPLAY",
                                   "SOUND",
                                   "SAVE#/#LOAD",
                                   "EXIT",
                                   "NORMAL TRAINING",
                                   "PARRYING TRAINING",
                                   "EXIT",
                                   "RESTART",
                                   "SAVE",
                                   "EXIT",
                                   "BGM LEVEL",
                                   "SE LEVEL",
                                   "BGM SELECT",
                                   "DEFAULT SETTING",
                                   "BGM TEST",
                                   "EXIT",
                                   "FIND MATCH",
                                   "EXIT",
                                   // The Custom tracklist, second half of each row: the theme in
                                   // brackets and its leader, in the menu's small charset,
                                   // following the character drawn in the condensed one.
                                   "(KILLING MOON).........",
                                   "(JAZZY NYC '99)...",
                                   "(CHINA VOX)..........",
                                   "(YOU BLOW MY MIND)....",
                                   "(BEATS IN MY HEAD).....",
                                   "(PSYCH OUT).............",
                                   "(THE CIRCUIT)...........",
                                   "(TWILIGHT).............",
                                   "(SPUNKY)..............",
                                   "(SNOWLAND)....",
                                   "(THE THEME OF Q)...........",
                                   "(THE BEEP)..............",
                                   "(KOBU)...................",
                                   "(THE LONGSHOREMAN)",
                                   "(CRAZY CHILI DOG)......",
                                   "(CROWDED STREET)..",
                                   // The Display page, on the sound menu's diagonal grown to eight
                                   // rows. HUD and ARTWORKS are still placeholders, greyed out by
                                   // letter_data_64_selectable; the rest are wired up.
                                   "SCREEN ADJUST",
                                   "RESOLUTION",
                                   // Abbreviated: a label sharing its row with a value column has
                                   // 176px, and "CHARACTER COLOR" needs 210 in this charset. Sits
                                   // this high up so its long value names clear the screen edge.
                                   "CHAR. COLOR",
                                   "BACKGROUNDS",
                                   "HUD",
                                   "ARTWORKS",
                                   // The page's eighth row. Its diagonal had the room — it steps
                                   // 18px and stopped at 73, so 55 was free and the six rows above
                                   // did not move. Everything after this entry did shift by one,
                                   // which is what BACKGROUND_STAGE_FIRST is counting.
                                   "COLOR EDIT",
                                   "EXIT",
                                   // The Custom backgrounds screen, second half of each row: the
                                   // stage in brackets, in the small charset, dotted out to where
                                   // the value column starts. Each row's dot count differs because
                                   // the character name before it does. The character is what tells
                                   // the four shared locations apart, since unlike the music, each
                                   // of those pairs is two distinct sets of assets.
                                   "(KOUSYU STREET).........",
                                   "(SUBWAY STATION).........",
                                   "(CHINESE RESTAURANT)..",
                                   "(MAIN STREET)..........",
                                   "(SAVANNA)...............",
                                   "(GILL STAGE).............",
                                   "(HOME SWEET HOME)........",
                                   "(A ROAD IN KYOTO).......",
                                   "(SUBWAY STATION)..........",
                                   "(DOJO OF RINDO-KAN)....",
                                   "(MOSQUE)................",
                                   "(SANTOS HARBOR)...........",
                                   "(SUBWAY STATION)............",
                                   "(CLUB METRO).............",
                                   "(SUZAKU CASTLE ROOFTOP)...",
                                   "(SANTOS HARBOR)..........",
                                   "(MOSQUE)...............",
                                   "(ORMECA RUINS)..........",
                                   "(SHOPPING DISTRICT)......",
                                   "(SHOPPING DISTRICT).......",
                                   // The colour editor's three channel captions. Appended past
                                   // everything rather than placed with the rest of that screen,
                                   // because an entry inserted anywhere shifts every index after
                                   // it — Slide_Pos_Data_61 is indexed by the same number.
                                   "R",
                                   "G",
                                   "B",
                                   // The cast, in engine order, for the colour editor's name line.
                                   // The message table has these too, but only in the charset
                                   // effect_18 draws and in alphabetical order; here they are in
                                   // the numbering the rest of that screen works in, and in
                                   // whichever charset the caller asks for.
                                   //
                                   // Chun-Li's hyphen was checked on screen and draws correctly,
                                   // so the charset covers it as it does the punctuation in the
                                   // labels above.
                                   "GILL",
                                   "ALEX",
                                   "RYU",
                                   "YUN",
                                   "DUDLEY",
                                   "NECRO",
                                   "HUGO",
                                   "IBUKI",
                                   "ELENA",
                                   "ORO",
                                   "YANG",
                                   "KEN",
                                   "SEAN",
                                   "URIEN",
                                   "AKUMA",
                                   "CHUN-LI",
                                   "MAKOTO",
                                   "Q",
                                   "TWELVE",
                                   "REMY",
                                   // The colour editor's two menu rows, under the name. Drawn by
                                   // effect_61 rather than effect_18, which every other menu row
                                   // uses: effect_18 draws in the wide charset, where "DEFAULT
                                   // COLOR" runs 182px from an x of 46 and off the right edge.
                                   // The narrow one takes 8px a letter and fits.
                                   "COLOR",
                                   "SAVE",
                                   // 137-140: which set the editor is working on, as the value of
                                   // the COLOR row. Abbreviated where the full name would not fit
                                   // beside its label: the column runs from x 94 to the right edge,
                                   // which is eighteen letters of this charset.
                                   "3RD STRIKE",
                                   "NEW GEN",
                                   "2ND IMPACT",
                                   "COLOR EDIT",
                                   // 141-172: the button that picks each of the sixteen palette
                                   // rows, named as Setup_PL_Color reads it at the character
                                   // select: the six attack buttons take rows 0-5, LP+HP+MK takes
                                   // the seventh, and Start held with each of the six takes 7-12.
                                   // The last three are named for nothing — no gesture reaches
                                   // them, and what a file holds there is whatever it was built
                                   // with.
                                   //
                                   // Twice over, 141-156 beside the character's name for the row
                                   // being edited and 157-172 beside SAVE for the row about to be
                                   // written: Slide_Pos_Data_61 is indexed by the string, so two
                                   // places on screen mean two copies of the list.
                                   "LP",
                                   "MP",
                                   "HP",
                                   "LK",
                                   "MK",
                                   "HK",
                                   "LP+HP+MK",
                                   "ST+LP",
                                   "ST+MP",
                                   "ST+HP",
                                   "ST+LK",
                                   "ST+MK",
                                   "ST+HK",
                                   "-",
                                   "-",
                                   "-",
                                   "LP",
                                   "MP",
                                   "HP",
                                   "LK",
                                   "MK",
                                   "HK",
                                   "LP+HP+MK",
                                   "ST+LP",
                                   "ST+MP",
                                   "ST+HP",
                                   "ST+LK",
                                   "ST+MK",
                                   "ST+HK",
                                   "-",
                                   "-",
                                   "-" };

void (*const EFF61_Jmp_Tbl[4])() = { EFF61_WAIT, EFF61_SLIDE_IN, EFF61_SLIDE_OUT, EFF61_SUDDENLY };

void effect_61_move(WORK_Other_CONN* ewk) {
    if (Check_Die_61((WORK_Other*)ewk)) {
        push_effect_work(&ewk->wu);
        return;
    }

    EFF61_Jmp_Tbl[ewk->wu.routine_no[0]](ewk);

    if (ewk->wu.be_flag == 0) {
        return;
    }

    ewk->wu.position_x = ewk->wu.xyz[0].disp.pos & 0xFFFF;
    ewk->wu.position_y = ewk->wu.xyz[1].disp.pos & 0xFFFF;

    if (ewk->wu.char_index >= 37 && ewk->wu.char_index < 43) {
        if (Menu_Cursor_Y[ewk->master_id] == ewk->wu.type) {
            if (Menu_Cursor_X[ewk->master_id]) {
                ewk->wu.my_clear_level = 0;
            } else {
                ewk->wu.my_clear_level = 51;
            }
        } else {
            ewk->wu.my_clear_level = 179;
        }
    } else if (ewk->wu.char_index >= 56 && ewk->wu.char_index < 59) {
        if (Menu_Cursor_Y[ewk->master_id] == ewk->wu.type) {
            ewk->wu.my_bright_type = 0;
            ewk->wu.my_bright_level = 0;
            ewk->wu.my_clear_level = 0;
        } else {
            ewk->wu.my_bright_type = 1;
            ewk->wu.my_bright_level = 8;
            ewk->wu.my_clear_level = 51;
        }
    } else if (Menu_Cursor_Y[ewk->master_id] == ewk->wu.type) {
        ewk->wu.my_clear_level = 0;
    } else if (ewk->wu.char_index == 1 && Connect_Status == 0) {
        ewk->wu.my_clear_level = 179;
    } else {
        ewk->wu.my_clear_level = 128;
    }

    sort_push_request3(&ewk->wu);
}

void EFF61_WAIT(WORK_Other_CONN* ewk) {
    if ((ewk->wu.routine_no[0] = Order[ewk->wu.dir_old])) {
        ewk->wu.routine_no[1] = 0;
    }
}

void EFF61_SLIDE_IN(WORK_Other_CONN* ewk) {
    if (Order[ewk->wu.dir_old] != 1) {
        ewk->wu.routine_no[0] = Order[ewk->wu.dir_old];
        ewk->wu.routine_no[1] = 0;
        return;
    }

    switch (ewk->wu.routine_no[1]) {
    case 0:
        if (--Order_Timer[ewk->wu.dir_old]) {
            break;
        }

        ewk->wu.routine_no[1]++;
        ewk->wu.disp_flag = 1;
        ewk->wu.xyz[0].disp.pos =
            bg_w.bgw[ewk->wu.my_family - 1].wxy[0].disp.pos + Slide_Pos_Data_61[ewk->wu.char_index][0] + 384;
        ewk->wu.xyz[1].disp.pos =
            bg_w.bgw[ewk->wu.my_family - 1].wxy[1].disp.pos + Slide_Pos_Data_61[ewk->wu.char_index][1];
        ewk->wu.position_z = 68;
        ewk->wu.hit_quake = bg_w.bgw[ewk->wu.my_family - 1].wxy[0].disp.pos + Slide_Pos_Data_61[ewk->wu.char_index][0];
        ewk->wu.mvxy.a[0].sp = -0x400000;
        ewk->wu.mvxy.d[0].sp = 0x50000;
        break;

    default:
        ewk->wu.xyz[0].cal += ewk->wu.mvxy.a[0].sp;
        ewk->wu.mvxy.a[0].sp += ewk->wu.mvxy.d[0].sp;

        if (ewk->wu.hit_quake < ewk->wu.xyz[0].disp.pos) {
            break;
        }

        if (Order[ewk->wu.dir_old] == ewk->wu.routine_no[0]) {
            Order[ewk->wu.dir_old] = 0;
        }

        ewk->wu.routine_no[0] = 0;
        ewk->wu.xyz[0].disp.pos = ewk->wu.hit_quake;
        Menu_Cursor_Move--;
        break;
    }
}

void EFF61_SLIDE_OUT(WORK_Other_CONN* /* unused */) {}

void EFF61_SUDDENLY(WORK_Other_CONN* ewk) {
    switch (ewk->wu.routine_no[1]) {
    case 0:
        if (--Order_Timer[ewk->wu.dir_old]) {
            break;
        }

        ewk->wu.routine_no[1]++;
        ewk->wu.disp_flag = 1;
        ewk->wu.xyz[0].disp.pos =
            bg_w.bgw[ewk->wu.my_family - 1].wxy[0].disp.pos + Slide_Pos_Data_61[ewk->wu.char_index][0];
        ewk->wu.xyz[1].disp.pos =
            bg_w.bgw[ewk->wu.my_family - 1].wxy[1].disp.pos + Slide_Pos_Data_61[ewk->wu.char_index][1];
        ewk->wu.position_z = 68;

        if (ewk->wu.char_index >= 56 && ewk->wu.char_index < 59) {
            ewk->wu.position_z = 20;
        }

        break;

    default:
        ewk->wu.routine_no[0] = 0;
        Order[ewk->wu.dir_old] = 0;
        break;
    }
}

s32 Check_Die_61(WORK_Other* ewk) {
    return Menu_Suicide[ewk->master_player];
}

// Where the last line built by effect_61_init went, on the model of effect_66's own. A caller that
// has to take a line back down again — a value that changes, so its sprite must be rebuilt — has no
// other way to name it: Menu_Suicide kills every line sharing a master_player, which is all of them.
s16 effect_61_last_work = -1;

s32 effect_61_init(s16 master, u8 dir_old, s16 sync_bg, s16 master_player, s16 char_ix, s16 cursor_index,
                   u16 letter_type) {
    WORK_Other_CONN* ewk;
    s16 ix;
    u16 x;
    s16 offset_x;
    const u8* ptr;

    if ((ix = pull_effect_work(4)) == -1) {
        effect_61_last_work = -1;
        return -1;
    }

    effect_61_last_work = ix;
    ewk = (WORK_Other_CONN*)frw[ix];
    ewk->wu.be_flag = 1;
    ewk->wu.id = 61;
    ewk->wu.work_id = 16;
    ewk->master_id = master;
    ewk->wu.my_family = sync_bg + 1;
    ewk->wu.my_col_code = 0x1AC;
    ewk->wu.type = cursor_index;
    ewk->wu.char_index = char_ix;
    ewk->wu.old_cgnum = letter_type;
    ewk->wu.dir_old = dir_old;
    ewk->master_player = master_player;

    if (ewk->wu.old_cgnum == 0x70A7) {
        offset_x = 8;
    } else {
        offset_x = 14;
    }

    ptr = (u8*)Menu_Letter_Data[char_ix];
    ix = 0;
    x = 0;

    while (*ptr != '\0') {
        if (*ptr == ' ') {
            x += offset_x;
            ptr++;
            continue;
        }

        if (*ptr == '#') {
            x += offset_x / 2;
            ptr++;
            continue;
        }

        ewk->conn[ix].nx = x;
        ewk->conn[ix].ny = 0;
        ewk->conn[ix].col = 0;
        ewk->conn[ix].chr = ewk->wu.old_cgnum + *ptr;

        if (offset_x == 14 && *ptr == '/') {
            ewk->conn[ix].nx -= 8;
            ewk->conn[ix].ny += 17;
        }

        x += offset_x;
        ptr++;
        ix++;
    }

    ewk->num_of_conn = ix;
    ewk->wu.my_mts = 13;
    ewk->wu.my_trans_mode = get_my_trans_mode(ewk->wu.my_mts);
    return 0;
}
