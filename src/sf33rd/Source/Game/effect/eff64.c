/**
 * @file eff64.c
 * TODO: identify what this effect does
 */

#include "sf33rd/Source/Game/effect/eff64.h"
#include "common.h"
#include "port/sound/bgm_remix.h"
#include "port/video/pal_remix.h"
#include "sf33rd/Source/Game/effect/eff61.h"
#include "sf33rd/Source/Game/effect/effect.h"
#include "sf33rd/Source/Game/engine/workuser.h"
#include "sf33rd/Source/Game/rendering/aboutspr.h"
#include "sf33rd/Source/Game/rendering/texcash.h"
#include "sf33rd/Source/Game/screen/sel_data.h"
#include "sf33rd/Source/Game/stage/bg.h"

void EFF64_WAIT(WORK_Other_CONN* ewk);
void EFF64_SLIDE_IN(WORK_Other_CONN* ewk);
void EFF64_CHAR_CHANGE(WORK_Other_CONN* /* unused */);
void EFF64_SUDDENLY(WORK_Other_CONN* ewk);
void Disp_64_Sub(WORK_Other_CONN* ewk);
void Setup_Letter_64(WORK_Other_CONN* ewk, s16 disp_index);
s16 disp_index_64(WORK_Other_CONN* ewk);
static s16 subject_64(WORK_Other_CONN* ewk);

const s8* Letter_Data_64[23][16] = {
    { "\"OFF\"", "\"/ON/\"", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL },
    { "#;;;;;;;",
      "##;;;;;;",
      "###;;;;;",
      "####;;;;",
      "#####;;;",
      "######;;",
      "#######;",
      "########",
      NULL,
      NULL,
      NULL,
      NULL,
      NULL,
      NULL,
      NULL,
      NULL },
    { "30", "60", "99", "{", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL },
    { "1", "3", "5", "7", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL },
    { "#;;;", "##;;", "###;", "####", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL },
    { "OLD", "NEW", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL },
    { "DISABLE", "ENABLE", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL },
    { "OFF", "ON", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL },
    { "HUMAN", "CPU", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL },
    { "EN", "JP", "FR", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL },
    { "SYSTEM  NORMAL",
      "SYSTEM  CUSTOM",
      NULL,
      NULL,
      NULL,
      NULL,
      NULL,
      NULL,
      NULL,
      NULL,
      NULL,
      NULL,
      NULL,
      NULL,
      NULL,
      NULL },
    { "Silence", "-14", "-13", "-12", "-11", "-10", "-9", "-8", "-7", "-6", "-5", "-4", "-3", "-2", "-1", "Standard" },
    { "Arrange", "Original", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL },
    { "-PLAY(A)", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL },
    { " STOP(B) BUTTON-", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL },
    // LETTER_TYPE_SOUNDTRACK: filled in at runtime from the installed soundtracks
    { NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL },
    // The Display page. Everything past the first entry of each row is greyed out, see
    // letter_data_64_selectable below.
    { "384x224", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL },
    { "SD", "HD", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL },
    // Per Round swaps set between rounds: round 1 Original, round 2 Arranged, round 3 Original
    { "Original", "re:THIRD", "Per Round", "Random", "Custom", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
      NULL, NULL },
    // Same, per stage on the Custom backgrounds screen, so without Custom itself
    { "Original", "re:THIRD", "Per Round", "Random", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
      NULL },
    // How the characters' palette set gets chosen, which is what this row settles now — see
    // CHAR_COLOR_MODE_* for why it stopped naming a set. The hyphen in the third rather than a
    // slash: Setup_Letter_64 reads a slash as a half space and never draws one.
    { "Disabled", "Custom", "Start Button", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
      NULL },
    // Same, per character on the Custom character colours screen, so without Custom itself
    { "New Generation", "2nd Impact", "3rd Strike", "Random", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL,
      NULL, NULL, NULL },
    // That screen's navigation row
    { "PREV", "EXIT", "NEXT", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL }
};

/// The rows the Display page owns advertise more than the port can honour; every other row means
/// every entry it declares.
s16 letter_data_64_selectable(s16 letter_type, s16 disp_index, s16 subject) {
    switch (letter_type) {
    case LETTER_TYPE_RESOLUTION:
    case LETTER_TYPE_SD_HD:
        return disp_index == 0;

    // These two rows set every stage or every fighter at once. A set is offered when it holds
    // anything at all — which stages it actually covers is then the per-row screen's business, and
    // the loader falls the rest back to the game's own colours.
    case LETTER_TYPE_BACKGROUNDS:
        return (disp_index == BACKGROUNDS_VALUE_CUSTOM) || PalRemix_HasBackgroundSet(disp_index);

    // Start offers the two earlier games' colours by name, so with neither installed it would
    // promise something that cannot happen. Disabled and Custom always stand: the first is the
    // game as it shipped and the second is the screen that sets it per fighter, which is also this
    // row's default — a default the page would otherwise keep putting back and greying out in the
    // same breath.
    case LETTER_TYPE_CHARACTER_COLOR:
        return (disp_index == CHAR_COLOR_MODE_DISABLED) || (disp_index == CHAR_COLOR_MODE_CUSTOM)
               || PalRemix_HasCharacterSet(PAL_SET_NEW_GENERATION) || PalRemix_HasCharacterSet(PAL_SET_2ND_IMPACT);

    // A set is offered to a fighter only if it can dress that fighter: New Generation never had
    // Makoto, so her row must not offer it. Where the row stands for no one in particular, the
    // question falls back to whether the set exists at all.
    case LETTER_TYPE_CHARACTER_SET:
        return (subject >= 0) ? PalRemix_HasCharacter(subject, disp_index)
                              : PalRemix_HasCharacterSet(disp_index);

    case LETTER_TYPE_BACKGROUND_SET:
        return (subject >= 0) ? PalRemix_HasStage(subject, disp_index)
                              : PalRemix_HasBackgroundSet(disp_index);

    // Same idea on the Custom tracklist: a pack that has no track for this stage would fall back
    // to the arranged one, so offering it as a choice would promise something it cannot do.
    case LETTER_TYPE_SOUNDTRACK:
        return (subject >= 0) ? BgmRemix_SoundtrackCoversStage(disp_index, subject) : 1;

    default:
        return 1;
    }
}

void (*const EFF64_Jmp_Tbl[4])() = { EFF64_WAIT, EFF64_SLIDE_IN, EFF64_CHAR_CHANGE, EFF64_SUDDENLY };

/// Row of Letter_Data_64 holding the `BGM Type` values
#define LETTER_TYPE_BGM_TYPE 12

// Convert_Buff holds twelve values per row and is part of the netplay state, so the sixteen
// stages get their own buffer rather than being squeezed in.
s8 Custom_Buff[16];
s8 Custom_Page;

// Alphabetical by character, which is how the two other Custom screens list theirs
const s8 Custom_Row_To_Theme[16] = { 7, 0, 3, 10, 8, 15, 2, 5, 6, 1, 13, 12, 4, 9, 14, 11 };

// The characters and backgrounds screens list their rows alphabetically too — Akuma, Alex,
// Chun-Li, Dudley, Elena, Gill, Hugo, Ibuki, Ken, Makoto, Necro, Oro, Q, Remy, Ryu, Sean, Twelve,
// Urien, Yang, Yun — while the palettes behind them are keyed by the engine's own numbering from
// constants.h. This turns a row into that number. A stage carries its character's number, so the
// same table serves both screens.
const s8 Custom_Row_To_Char[20] = { 14, 1, 15, 4, 8, 0, 6, 7, 11, 16, 5, 9, 17, 19, 2, 12, 18, 13, 10, 3 };

// The Display page's values are cosmetic for now and never survive the page, so they stay out of
// the netplay state too. Same for the one set per stage behind its Custom backgrounds screen.
/// Starts on each row's own default rather than on zero, and outlives the page: what a row shows
/// is a live setting, so reopening Display has to find the setting still there. The character
/// colour row is the one where zero is wrong — zero is Disabled, and the per-fighter screen is
/// the way this shipped, with every fighter on the game's own colours until someone says
/// otherwise. So the default names that screen and changes nothing on its own.
s8 Display_Buff[8] = { 0, 0, CHAR_COLOR_MODE_CUSTOM, 0, 0, 0, 0, 0 };
s8 Background_Buff[58]; /* indexe par bg_w.stage : il en faut un par etage,
                           et il n'en avait que 20 -- l'etage 22 debordait deja */
s8 Background_Page;
/// Every fighter starts on the game's own palettes, which is not what zero means here: zero is New
/// Generation. Left to the loader's zero-fill, a fresh boot dressed the whole cast in that set
/// without anyone having asked — in fights as much as on the screens that show it — and only
/// touching the CHAR. COLOR row or opening the Custom screen ever put it right.
s8 Character_Buff[20] = {
    PAL_SET_3RD_STRIKE, PAL_SET_3RD_STRIKE, PAL_SET_3RD_STRIKE, PAL_SET_3RD_STRIKE, PAL_SET_3RD_STRIKE,
    PAL_SET_3RD_STRIKE, PAL_SET_3RD_STRIKE, PAL_SET_3RD_STRIKE, PAL_SET_3RD_STRIKE, PAL_SET_3RD_STRIKE,
    PAL_SET_3RD_STRIKE, PAL_SET_3RD_STRIKE, PAL_SET_3RD_STRIKE, PAL_SET_3RD_STRIKE, PAL_SET_3RD_STRIKE,
    PAL_SET_3RD_STRIKE, PAL_SET_3RD_STRIKE, PAL_SET_3RD_STRIKE, PAL_SET_3RD_STRIKE, PAL_SET_3RD_STRIKE,
};

// Both sides start on the game's own colours, which is where the Start button's cycle begins.
s8 Player_Pal_Set[2] = { PAL_SET_3RD_STRIKE, PAL_SET_3RD_STRIKE };

/// The order Start walks. 3rd Strike first because it is what the fighter wears if nobody touches
/// anything, so the first press has to be a visible departure rather than a return to where you
/// already were.
#define PALETTE_CYCLE_STOPS 5

static const s8 palette_cycle[PALETTE_CYCLE_STOPS] = { PAL_SET_3RD_STRIKE, PAL_SET_NEW_GENERATION, PAL_SET_2ND_IMPACT,
                                                       PAL_SET_PER_CHARACTER, PAL_SET_COLOR_EDIT };

/// Printed by the select screen in the charset SSPutStr draws, which is the capitals-only one the
/// PRESS START lines use. Same order as palette_cycle.
static const s8* const palette_cycle_name[PALETTE_CYCLE_STOPS] = { "3RD STRIKE", "NEW GENERATION", "2ND IMPACT",
                                                                   "CUSTOM", "COLOR EDIT" };

/// Where a set sits in that cycle, or 0 for one that is not in it.
static s16 palette_cycle_index(s8 set) {
    s16 i;

    for (i = 0; i < PALETTE_CYCLE_STOPS; i++) {
        if (palette_cycle[i] == set) {
            return i;
        }
    }

    return 0;
}

s16 Character_Palette_Set(s16 player, s16 character) {
    s16 set;

    switch (Display_Buff[DISPLAY_ROW_CHARACTER_COLOR]) {
    case CHAR_COLOR_MODE_DISABLED:
        return PAL_SET_3RD_STRIKE;

    case CHAR_COLOR_MODE_CUSTOM:
        set = Character_Buff[character];
        break;

    // Start mode, where the select screen has already left its answer here.
    default:
        set = Player_Pal_Set[player];

        if (set == PAL_SET_PER_CHARACTER) {
            set = Character_Buff[character];
        }

        break;
    }

    // A set with nothing for this fighter would otherwise reach the loader, which answers it by
    // falling back anyway — but silently, and one level further down, where the reason is lost.
    return PalRemix_HasCharacter(character, set) ? set : PAL_SET_3RD_STRIKE;
}

void Character_Palette_Cycle(s16 player) {
    const s16 next = (s16)((palette_cycle_index(Player_Pal_Set[player]) + 1) % PALETTE_CYCLE_STOPS);

    Player_Pal_Set[player] = palette_cycle[next];
}

bool Character_Palette_Selectable(s16 player) {
    // The editor's set is the one stop that can be empty: it exists only once something has been
    // saved into it. So the answer is the folder's, not a constant — the line stops being dim the
    // moment there is a palette behind it.
    if (Player_Pal_Set[player] == PAL_SET_COLOR_EDIT) {
        return PalRemix_HasCharacterSet(PAL_SET_COLOR_EDIT);
    }

    return true;
}

const s8* Character_Palette_Name(s16 player) {
    return palette_cycle_name[palette_cycle_index(Player_Pal_Set[player])];
}

void Character_Palette_Reset(void) {
    Player_Pal_Set[0] = PAL_SET_3RD_STRIKE;
    Player_Pal_Set[1] = PAL_SET_3RD_STRIKE;
}
s8 Character_Page;
s8 Page_Nav_Value;

/// @brief Text shown for one value of a menu option.
///
/// On the `BGM Type` row the value is a menu position, not a BGM type: packs add entries and the
/// user can reorder and relabel the row, so it can't be a fixed table.
static const s8* letter_data_64_at(s16 letter_type, s16 disp_index) {
    if (letter_type == LETTER_TYPE_SOUNDTRACK) {
        const char* label = BgmRemix_GetSoundtrackLabel(disp_index);
        return (label != NULL) ? (const s8*)label : (const s8*)"Arrange";
    }

    if (letter_type == LETTER_TYPE_BGM_TYPE) {
        const char* label = BgmRemix_GetSlotLabel(disp_index);

        if (label != NULL) {
            return (const s8*)label;
        }

        return Letter_Data_64[letter_type][BgmRemix_GetSlotType(disp_index)];
    }

    return Letter_Data_64[letter_type][disp_index];
}

void effect_64_move(WORK_Other_CONN* ewk) {
    if (Check_Die_61((WORK_Other*)ewk)) {
        push_effect_work(&ewk->wu);
        return;
    }

    EFF64_Jmp_Tbl[ewk->wu.routine_no[0]](ewk);

    if (ewk->wu.be_flag == 0) {
        return;
    }

    ewk->wu.position_x = ewk->wu.xyz[0].disp.pos & 0xFFFF;
    ewk->wu.position_y = ewk->wu.xyz[1].disp.pos & 0xFFFF;

    if (!letter_data_64_selectable(ewk->wu.char_index, disp_index_64(ewk), subject_64(ewk))) {
        // Advertised but not available: stays faint even under the cursor
        ewk->wu.my_clear_level = 179;
    } else if (Menu_Cursor_Y[0] == ewk->wu.type) {
        ewk->wu.my_clear_level = 0;
    } else {
        ewk->wu.my_clear_level = 128;
    }

    sort_push_request3(&ewk->wu);
}

void EFF64_WAIT(WORK_Other_CONN* ewk) {
    if ((ewk->wu.routine_no[0] = Order[ewk->wu.dir_old])) {
        ewk->wu.routine_no[1] = 0;
    }

    Disp_64_Sub(ewk);
}

void EFF64_SLIDE_IN(WORK_Other_CONN* ewk) {
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
            bg_w.bgw[ewk->wu.my_family - 1].wxy[0].disp.pos + Slide_Pos_Data_64[ewk->wu.dir_step][0] + 384;
        ewk->wu.xyz[1].disp.pos =
            bg_w.bgw[ewk->wu.my_family - 1].wxy[1].disp.pos + Slide_Pos_Data_64[ewk->wu.dir_step][1];
        ewk->wu.position_z = 70;
        ewk->wu.hit_quake = bg_w.bgw[ewk->wu.my_family - 1].wxy[0].disp.pos + Slide_Pos_Data_64[ewk->wu.dir_step][0];
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
        break;
    }
}

void EFF64_CHAR_CHANGE(WORK_Other_CONN* /* unused */) {}

/// Places a value without the slide-in, for screens whose labels appear at once — the value would
/// otherwise cross the screen on its own while the row it belongs to already sits still.
void EFF64_SUDDENLY(WORK_Other_CONN* ewk) {
    switch (ewk->wu.routine_no[1]) {
    case 0:
        if (--Order_Timer[ewk->wu.dir_old]) {
            break;
        }

        ewk->wu.routine_no[1]++;
        ewk->wu.disp_flag = 1;
        ewk->wu.xyz[0].disp.pos =
            bg_w.bgw[ewk->wu.my_family - 1].wxy[0].disp.pos + Slide_Pos_Data_64[ewk->wu.dir_step][0];
        ewk->wu.xyz[1].disp.pos =
            bg_w.bgw[ewk->wu.my_family - 1].wxy[1].disp.pos + Slide_Pos_Data_64[ewk->wu.dir_step][1];
        ewk->wu.position_z = 70;
        break;

    default:
        ewk->wu.routine_no[0] = 0;
        Order[ewk->wu.dir_old] = 0;
        break;
    }
}

s32 effect_64_init(u8 dir_old, s16 sync_bg, s16 master_player, s16 letter_type, s16 cursor_index, u16 char_offset,
                   s16 pos_index, s16 convert_id, s16 convert_id2) {
    WORK_Other_CONN* ewk;
    s16 ix;

    if ((ix = pull_effect_work(4)) == -1) {
        return -1;
    }

    ewk = (WORK_Other_CONN*)frw[ix];
    ewk->wu.be_flag = 1;
    ewk->wu.id = 64;
    ewk->wu.work_id = 16;
    ewk->wu.my_family = sync_bg + 1;
    ewk->wu.my_col_code = 0x1AC;
    ewk->wu.dir_step = pos_index;
    ewk->wu.type = cursor_index;
    ewk->wu.char_index = letter_type;
    ewk->wu.dir_old = dir_old;
    ewk->master_player = master_player;
    ewk->wu.old_cgnum = char_offset;
    ewk->master_priority = convert_id;
    ewk->wu.cg_type = convert_id2;
    ewk->wu.my_mts = 13;
    ewk->wu.my_trans_mode = get_my_trans_mode(ewk->wu.my_mts);
    Disp_64_Sub(ewk);
    return 0;
}

/// @brief Which character or stage a value row stands for, or -1 when it stands for none.
///
/// The two Custom screens list their rows alphabetically and page through them, so the row on
/// screen has to be translated before it means anything to the palettes behind it.
static s16 subject_64(WORK_Other_CONN* ewk) {
    if (ewk->master_priority == CONVERT_ID_CUSTOM) {
        return Custom_Row_To_Theme[Custom_Page * CUSTOM_PAGE_ROWS + ewk->wu.type];
    }

    if (ewk->master_priority == CONVERT_ID_CHARACTER) {
        return Custom_Row_To_Char[Character_Page * CHARACTER_PAGE_ROWS + ewk->wu.type];
    }

    if (ewk->master_priority == CONVERT_ID_BACKGROUND) {
        return Custom_Row_To_Char[Background_Page * BACKGROUND_PAGE_ROWS + ewk->wu.type];
    }

    return -1;
}

s16 disp_index_64(WORK_Other_CONN* ewk) {
    // The row is a slot on the current page; the buffer behind it is keyed by theme
    if (ewk->master_priority == CONVERT_ID_CUSTOM) {
        return Custom_Buff[Custom_Row_To_Theme[Custom_Page * CUSTOM_PAGE_ROWS + ewk->wu.type]];
    }

    if (ewk->master_priority == CONVERT_ID_DISPLAY) {
        return Display_Buff[ewk->wu.type];
    }

    // The row is a slot on the current page; the buffer behind it is keyed by stage
    if (ewk->master_priority == CONVERT_ID_BACKGROUND) {
        return Background_Buff[Custom_Row_To_Char[Background_Page * BACKGROUND_PAGE_ROWS + ewk->wu.type]];
    }

    // The row is a slot on the current page; the buffer behind it is keyed by character
    if (ewk->master_priority == CONVERT_ID_CHARACTER) {
        return Character_Buff[Custom_Row_To_Char[Character_Page * CHARACTER_PAGE_ROWS + ewk->wu.type]];
    }

    if (ewk->master_priority == CONVERT_ID_PAGE_NAV) {
        return Page_Nav_Value;
    }

    return Convert_Buff[ewk->master_priority][ewk->wu.cg_type][ewk->wu.type];
}

void Disp_64_Sub(WORK_Other_CONN* ewk) {
    Setup_Letter_64(ewk, disp_index_64(ewk));
}

/// Switches a `BGM Type` value between the menu's lettering and the smaller one, mid-text.
#define LETTER_FONT_TOGGLE '~'

/// Charset the `BGM Type` row borrows when a value needs more room than its own allows
#define LETTER_CGNUM_NARROW 0x70A7

/// Rendered length, so the toggles an author wrote don't count towards the width budget
static s16 letter_length_64(const u8* text) {
    s16 length = 0;

    for (s16 i = 0; text[i] != '\0'; i++) {
        if (text[i] != LETTER_FONT_TOGGLE) {
            length++;
        }
    }

    return length;
}

void Setup_Letter_64(WORK_Other_CONN* ewk, s16 disp_index) {
    s16 x;
    s16 ix;
    s16 offset_x;
    const u8* ptr;
    bool is_bgm_type;
    bool narrow;
    bool substituted;

    ptr = (u8*)letter_data_64_at(ewk->wu.char_index, disp_index);
    is_bgm_type = ewk->wu.char_index == LETTER_TYPE_BGM_TYPE;
    narrow = ewk->wu.old_cgnum == LETTER_CGNUM_NARROW;

    // A remix pack name can be wider than this row's charset allows, so it starts on the narrower
    // one. Arrange and Original are short enough to keep their usual size.
    if (is_bgm_type && (letter_length_64(ptr) > BGM_REMIX_NAME_WIDE_MAX)) {
        narrow = true;
    }

    ix = 0;
    x = 0;

    while (*ptr != '\0') {
        // Authors can flip charset mid-name, to keep part of it at full size. The marker is always
        // consumed rather than drawn, so a name carrying one reads correctly on rows that don't
        // honour it — the Custom tracklist, which is already in the narrower charset.
        if (*ptr == LETTER_FONT_TOGGLE) {
            narrow = is_bgm_type ? !narrow : narrow;
            ptr++;
            continue;
        }

        offset_x = narrow ? 8 : 14;

        if (*ptr == ' ') {
            x += offset_x;
            ptr++;
            continue;
        }

        if (*ptr == '/') {
            x += offset_x / 2;
            ptr++;
            continue;
        }

        // The borrowed glyphs sit lower and further right than the menu's own, so nudge them back
        // onto the row. Screen y grows upwards here, as the menu's row positions show. Rows drawn
        // with that charset to begin with are already aligned and want no nudge.
        substituted = narrow && (ewk->wu.old_cgnum != LETTER_CGNUM_NARROW);

        ewk->conn[ix].nx = substituted ? x - 2 : x;
        ewk->conn[ix].ny = substituted ? 2 : 0;
        ewk->conn[ix].col = 0;
        ewk->conn[ix].chr = (narrow ? LETTER_CGNUM_NARROW : ewk->wu.old_cgnum) + *ptr;
        x += offset_x;
        ptr++;
        ix++;
    }

    ewk->num_of_conn = ix;
}
