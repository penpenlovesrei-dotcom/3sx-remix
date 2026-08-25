/**
 * @file col_edit.c
 * The fighter preview behind COLOR EDIT MODE.
 *
 * See col_edit.h for why the screen carries a real fighter rather than a grid of swatches.
 */

#include "sf33rd/Source/Game/menu/col_edit.h"
#include "common.h"
#include "sf33rd/Source/Game/effect/effect.h"
#include "sf33rd/Source/Game/engine/workuser.h"
#include "sf33rd/Source/Game/io/gd3rd.h"
#include "sf33rd/Source/Game/rendering/aboutspr.h"
#include "sf33rd/Source/Game/rendering/chren3rd.h"
#include "sf33rd/Source/Game/rendering/color3rd.h"
#include "sf33rd/Source/Game/rendering/dc_ghost.h"
#include "sf33rd/Source/Game/rendering/mtrans.h"
#include "sf33rd/Source/Game/rendering/texcash.h"
#include "sf33rd/Source/Game/rendering/texgroup.h"
#include "sf33rd/Source/Game/stage/bg.h"
#include "sf33rd/Source/Game/stage/bg_data.h"
#include "sf33rd/Source/Game/system/ramcnt.h"
#include "sf33rd/Source/Game/system/work_sys.h"
#include "structs.h"

#include <SDL3/SDL.h>

/// Texture group of a character, the table listing them one past a leading empty entry
#define CHARACTER_GROUP(character) ((s16)((character) + 1))
#define CHARACTER_TOTAL 20
/// Player one's slot, whose multitexture is 3 and whose palette lands in ColorRAM[0]
#define PREVIEW_PLAYER 0
#define PREVIEW_MTS 3
/// Where the character's colours land in ColorRAM, which is player one's own slot
#define PREVIEW_COLOR_RAM 0
/// Ghost palette slot the sprite actually reads. Players take 0 and 8, and none are live in a
/// menu, so the preview reuses player one's. Must stay under 16: colPalBuffDC holds no more, and
/// the streaming path masks the colour code with 0xF before using it as a slot.
#define PREVIEW_GHOST_SLOT 0
/// @name The reference fighter
///
/// The same character, the same pose, drawn a second time from the palette he arrived in. Player
/// two's slots hold it: a menu has no second fighter loaded, the next fight overwrites them
/// anyway, and using them keeps the reference on exactly the same footing as the fighter being
/// edited rather than on a special case.
///
/// Only the first bank is filled. The mirrored one exists for fighters the sprite path flips, and
/// it reaches it by ORing 8 into a colour code whose work_id says it belongs to a player — which
/// this one's does not, deliberately, for the reason given where it is set.
/// @{
#define REFERENCE_COLOR_RAM 16
#define REFERENCE_GHOST_SLOT 8
/// @}
/// The BG the menus hang their effects on, as a family — effect_66 reaches it as target_bg 2
#define PREVIEW_FAMILY 3

/// @name Layout
///
/// Offsets from the menu BG's own origin, not screen coordinates: the sprite path multiplies by
/// that BG's matrix and the menus sit at world x 512, so a raw screen value would put the fighter
/// some six hundred units off the left edge. The usable band runs y 28 at the bottom to y 178 at
/// the top, y growing upward, and x roughly -192 to 192.
///
/// The fighter stands centred at the top on a black panel, with the bars down the left, the chip
/// of the colour being worked on to the right, and the sixty-four swatches in a strip along the
/// bottom. Nothing here is load-bearing — nudge freely.
/// @{
#define PREVIEW_X (-55)
#define PREVIEW_Y 90
#define PREVIEW_Z 3
/// Behind the fighter, which needs a larger z: PrioBase climbs with its index and the hit-judge
/// boxes sit at 1 precisely so that they cover the fighters at 3.
#define BACKDROP_Z 16
/// Two panels side by side, as the reference screen has: the fighter stands on the left one and
/// the right one waits for the untouched copy to compare him against. Tall enough for Hugo, who
/// is the one the height has to clear.
#define BACKDROP_X (-120)
#define BACKDROP_Y 84
#define BACKDROP_W 130
#define BACKDROP_H 136
#define BACKDROP_GAP 8
#define BACKDROP2_X (BACKDROP_X + BACKDROP_W + BACKDROP_GAP)
#define BACKDROP_COLOR 0xFF000000
/// The reference fighter stands on the right panel where the edited one stands on the left, so his
/// x is the same offset from his own panel: PREVIEW_X measured from BACKDROP_X.
#define REFERENCE_X (BACKDROP2_X + (PREVIEW_X - BACKDROP_X))
#define REFERENCE_Y PREVIEW_Y
/// @}

/// @name The swatch grid
/// Sixteen to a row across the bottom, which is as close to the reference screen's single strip as
/// sixty-four colours allow while keeping each one wide enough to judge.
///
/// All sixty-four are shown, padding included. A palette does not fill its bank: Hugo's holds 46
/// distinct colours, with 0xFDE0 — a flat blue — repeated across entries 48 to 63 and again at 32
/// to 34. That matches what this project measured of palettes generally, 34 to 64 distinct out of
/// 64. Where the padding starts is per character, so hiding it would mean deciding a boundary from
/// the data rather than showing what is actually there.
/// @{
#define SWATCH_COLS 16
#define SWATCH_ROWS 4
#define SWATCH_TOTAL (SWATCH_COLS * SWATCH_ROWS)
#define SWATCH_SIZE 13
#define SWATCH_STEP (SWATCH_SIZE + 1)
#define SWATCH_ORIGIN_X (-190)
#define SWATCH_ORIGIN_Y 68
/// Blend attribute the hit-judge boxes use, and the only one proven to draw a flat quad here
#define SWATCH_ATTR 0x60
/// Flat panels all sit at the same depth, in front of the fighter and his backdrop
#define PANEL_Z 1
#define SWATCH_CURSOR_COLOR 0xFFFFFFFF
#define SWATCH_CURSOR_THICKNESS 2
/// @}

/// @name The channel bars
/// Three of them, left of the grid, plus a large chip showing the colour being worked on. Lengths
/// stand in for numbers — see the header.
/// @{
#define BAR_WIDTH 12
#define BAR_STEP 18
#define BAR_HEIGHT 72
#define BAR_ORIGIN_X (-180)
#define BAR_ORIGIN_Y 142
#define BAR_TRACK_COLOR 0xC0202020
#define BAR_IDLE_COLOR 0xFF808080
#define BAR_MAX 31
/// The value above each bar, and the R, G or B caption below it. The captions are drawn by the
/// menu's own charset from Menu_Letter_Data; the values cannot be, so they are quads — see
/// digit_font.
#define VALUE_Y (BAR_ORIGIN_Y + BAR_HEIGHT + 6)
/// A block font pixel. Three by five of them make a digit, so a digit is 6 by 10 and a pair of
/// them 14 wide, which centres over a 12-wide bar at one pixel to its left.
#define DIGIT_PIXEL 2
#define DIGIT_W (3 * DIGIT_PIXEL)
#define DIGIT_GAP 2
#define VALUE_X_OFFSET (-1)
#define VALUE_COLOR 0xFFFFFFFF
/// @brief The chip of the colour being worked on, below the bars and their captions.
///
/// Wider than it is tall on purpose, so that it comes out square on screen. The window is asked
/// for 640x480 in the config while the image is 384x224, and nothing letterboxes the difference:
/// the vertical is stretched by about 1.29, which a chip large enough to notice shows plainly. The
/// swatches carry the same stretch and read as squares only because they are small.
///
/// Set from the window this was judged in, so it follows that window. Making it exact everywhere
/// would mean asking the renderer for the ratio at runtime; making it moot would mean a window
/// that keeps the image's own 12:7.
#define CHIP_W 34
#define CHIP_H 26
#define CHIP_X (BAR_ORIGIN_X + 7)
#define CHIP_Y 96
/// @}

/// Slot this module occupies in the effect move table, which held a dummy before it
#define COL_EDIT_EFFECT_ID 28
/// Effect list to hang it on. The menus use list 4, and Basic_Sub runs it.
#define COL_EDIT_EFFECT_LIST 4

/// Index into frw of the live preview work, or -1 when there is none
static s16 preview_ix = -1;
/// The same, for the untouched fighter on the right-hand panel
static s16 reference_ix = -1;
/// The sixty-four colours the character arrived in, taken before anything could change them
static u16 original_pal[64];
static bool original_saved;
static s16 loaded_character = -1;
static s16 pending_character = -1;
static s16 pose;
/// Which of the sixty-four colours the cursor sits on
static s16 cursor;
/// Which channel the lever is on, and whether it is driving them at all
static s16 channel;
static bool editing;
/// Whether this module was the one to bring the multitexture up, and so should take it back down
static bool made_texcash;
/// One-shot guard on the draw diagnostic, so it costs one line and not one per frame
static bool logged_draw;

static void _log(SDL_PRINTF_FORMAT_STRING const char* fmt, ...) SDL_PRINTF_VARARG_FUNC(1);

static void _log(const char* fmt, ...) {
    char message[256];
    va_list args;

    va_start(args, fmt);
    SDL_vsnprintf(message, sizeof(message), fmt, args);
    va_end(args);

    SDL_LogInfo(SDL_LOG_CATEGORY_APPLICATION, "[col_edit] %s", message);
}

static void log_state(const char* what) {
    _log("%s: character %d, pose %d", what, loaded_character, pose);
}

/// Which pattern of a character's group to stand them in, as an offset from its first. Engine
/// numbering, as `constants.h` orders them.
///
/// Filled by looking, never by deduction — see the header. All twenty were checked on screen, so a
/// wrong pose here is a regression rather than an unknown. The second pattern is the neutral
/// stance for eighteen of them; the two exceptions are not a numbering quirk but a difference in
/// how their groups are laid out, Oro's opening on a block of text tiles before any animation.
static const s8 pose_offset[CHARACTER_TOTAL] = {
    [0] = 1,    // Gill
    [1] = 1,    // Alex
    [2] = 1,    // Ryu
    [3] = 1,    // Yun
    [4] = 1,    // Dudley
    [5] = 1,    // Necro
    [6] = 1,    // Hugo
    [7] = 1,    // Ibuki
    [8] = 1,    // Elena
    [9] = 13,   // Oro — his group opens on a block of text tiles rather than on animation
    [10] = 1,   // Yang
    [11] = 1,   // Ken
    [12] = 1,   // Sean
    [13] = 1,   // Urien
    [14] = 1,   // Akuma
    [15] = 5,   // Chun-Li
    [16] = 1,   // Makoto
    [17] = 1,   // Q
    [18] = 1,   // Twelve
    [19] = 1,   // Remy
};

s16 ColEdit_Pose(void) {
    return pose;
}

/// First pattern of the loaded character's group, and how many it holds. Groups 1 to 20 are the
/// characters in engine order and their first patterns ascend, so the next group's first is one
/// past this group's last — entry 21 exists and carries the run on, which is what keeps the last
/// character from needing a special case.
static s16 pose_first(void) {
    return (s16)texgrpdat[CHARACTER_GROUP(loaded_character)].num_of_1st;
}

static s16 pose_count(void) {
    const s16 group = CHARACTER_GROUP(loaded_character);

    return (s16)(texgrpdat[group + 1].num_of_1st - texgrpdat[group].num_of_1st);
}

void ColEdit_StepPose(s16 delta) {
    const s16 count = pose_count();

    if (loaded_character < 0 || count <= 0) {
        return;
    }

    pose = (s16)(pose_first() + (((pose - pose_first() + delta) % count + count) % count));

    // The group is logged too: a pattern whose group is not this character's is skipped rather
    // than drawn, and telling that apart from a pattern that draws the wrong thing is the whole
    // difference between "the sprite is missing" and "the sprite is not a fighter".
    _log("pose %d, offset %d of %d for character %d, group %d wanted %d", pose, pose - pose_first(), count,
         loaded_character, obj_group_table[pose], CHARACTER_GROUP(loaded_character));
}

/// @brief Dress one pulled effect work as a fighter reading from a given ghost palette slot.
///
/// The two fighters differ in nothing but that slot and where they stand, so they are built the
/// same way and the caller places them.
static void setup_fighter_work(s16 ix, s16 ghost_slot) {
    WORK* wk = (WORK*)frw[ix];

    // Deliberately not cleared here. push_effect_work zeroes a work as it releases it and
    // pull_effect_work then rebuilds myself, listix, timing and the before/behind links, so
    // wiping it at this point takes the work back out of its own list and the effect walker
    // follows the wreckage. Set what is needed and leave the bookkeeping alone.
    wk->be_flag = 1;
    wk->disp_flag = 1;
    wk->id = COL_EDIT_EFFECT_ID;
    // Not 1, which would mean "this is a player". exchange_current_colcd answers that by
    // deriving a ghost palette slot from the work's id — and this work's id has to be its slot
    // in the effect table, 28, which would send the copy to ghost slot 224 and write sixty-four
    // colours far past the end of colPalBuffDC. 0 matches no case there and leaves the colour
    // code alone; the copy the players get for free is made by hand in ColEdit_Move instead.
    wk->work_id = 0;
    wk->my_family = PREVIEW_FAMILY;
    wk->my_col_code = ghost_slot;
    wk->my_mts = PREVIEW_MTS;
    wk->my_trans_mode = get_my_trans_mode(PREVIEW_MTS);
    // Zero, not 128. This is a transparency level, not a brightness: effect_61 draws its
    // selected row at 0 and dims the others to 128. At 128 the menu background showed
    // straight through the fighter and tinted him green.
    wk->my_clear_level = 0;
    wk->position_z = PREVIEW_Z;
}

/// @brief Take the palette the character arrived in, and give the reference fighter his own copy.
///
/// The copy goes to ColorRAM rather than only to the array because a sprite cannot be drawn from
/// an array: the reference fighter reads a ghost slot, and a ghost slot is filled from ColorRAM.
static void save_original(void) {
    s16 i;

    for (i = 0; i < 64; i++) {
        original_pal[i] = ColorRAM[PREVIEW_COLOR_RAM][i];
        ColorRAM[REFERENCE_COLOR_RAM][i] = original_pal[i];
    }

    original_saved = true;

    // Four entries, not sixty-four: enough to tell a real palette from a bank of zeroes, which is
    // what a snapshot taken a frame early would look like, without a line per colour.
    _log("original palette for character %d: %04X %04X %04X %04X", loaded_character, original_pal[0], original_pal[1],
         original_pal[2], original_pal[3]);
}

void ColEdit_Load(s16 character) {
    if (character == loaded_character && pending_character < 0) {
        return;
    }

    ColEdit_Unload();

    // The palette request reads My_char to know whose colours to convert, and Character_Buff to
    // know which set they should come from, so the character has to be in place before the ask.
    My_char[PREVIEW_PLAYER] = (u8)character;
    pending_character = character;
    Push_LDREQ_Queue_Player(PREVIEW_PLAYER, character);
}

bool ColEdit_Ready(void) {
    if (loaded_character >= 0) {
        return true;
    }

    if (pending_character < 0 || Check_LDREQ_Queue_Player(PREVIEW_PLAYER) == 0) {
        return false;
    }

    loaded_character = pending_character;
    pending_character = -1;

    // The fighter draws through player one's multitexture, which a menu has no reason to have
    // brought up. make_texcash_work returns early if it is already there, so this only ever adds
    // what is missing — and only what this module added is taken back down again.
    if (get_my_trans_mode(PREVIEW_MTS) < 0) {
        make_texcash_work(PREVIEW_MTS);
        made_texcash = true;
    }

    pose = (s16)(pose_first() + pose_offset[loaded_character]);

    preview_ix = pull_effect_work(COL_EDIT_EFFECT_LIST);

    if (preview_ix == -1) {
        _log("no free effect work for the preview");
        return false;
    }

    setup_fighter_work(preview_ix, PREVIEW_GHOST_SLOT);

    // Taken here rather than on entering the screen: this is the first frame at which the load has
    // landed and ColorRAM holds the character's own colours. A frame earlier it still holds the
    // one before him, and the reference panel would stand the wrong fighter's palette next to him.
    save_original();

    // Optional. Without a free work the reference panel simply stays black, which is where it
    // started; the fighter being edited is not worth losing over it.
    reference_ix = pull_effect_work(COL_EDIT_EFFECT_LIST);

    if (reference_ix == -1) {
        _log("no free effect work for the reference fighter");
    } else {
        setup_fighter_work(reference_ix, REFERENCE_GHOST_SLOT);
    }

    log_state("loaded");
    return true;
}

/// The palette every menu element shares, and the slot the recoloured copy of it goes to.
///
/// The copy lands in a player's slot, which is free for as long as a menu is up: no fighter is
/// loaded there, and the next fight overwrites it anyway. It must not be one of 7, 15, 23 or 31 —
/// those are the hit marks.
#define MENU_COL_CODE 0x1AC
#define MENU_COL_VARIANT 1
/// How many consecutive slots to carry over. The code is an offset added to each tile's own
/// palette number, so a sprite reads a run starting there rather than the one slot it names.
#define MENU_COL_SPAN 8
/// The one slot of that run the page indicator draws from, found by flooding each with a colour
/// nothing else could be mistaken for and seeing which one it took
#define MENU_PAGE_SLOT (MENU_COL_CODE + 6)
/// How much redder than blue an entry has to be before it counts as tuned for an orange background
#define MENU_PAGE_WARMTH 3
/// Where each hue's ten-step ramp starts in that palette, and how long it runs
#define MENU_RAMP_WHITE 1
#define MENU_RAMP_BLUE 17
#define MENU_RAMP_GREEN 33
#define MENU_RAMP_ORANGE 49
#define MENU_RAMP_LENGTH 10

s16 ColEdit_MenuPaletteVariant(void) {
    static u16 original[64];
    static bool saved;
    s16 i;

    // The page indicator turned out to have a palette to itself. The colour code is an offset, not
    // an index — the sprite path computes `(tile attribute & 0x1FF) + colcd` — so the menus' shared
    // 0x1AC is the base of a run, and this sprite alone draws from the seventh slot of it. Flooding
    // each slot of the run with its own unmistakable colour is what showed that: everything else on
    // screen took a different one.
    //
    // So no copy and no second sprite are needed after all. The entries are changed where they are,
    // and put back on the way out, because the run as a whole is shared even though this slot is not.
    if (!saved) {
        saved = true;

        for (i = 0; i < 64; i++) {
            original[i] = ColorRAM[MENU_PAGE_SLOT][i];
        }

        {
            char line[8 * 5 + 1];

            for (i = 0; i < 64; i++) {
                SDL_snprintf(&line[(i % 8) * 5], 6, "%04X ", original[i]);

                if ((i % 8) == 7) {
                    _log("page palette %2d-%2d: %s", i - 7, i, line);
                }
            }
        }
    }

    // Warm entries are the ones drawn to sit on an orange background; against green they read as a
    // muddy halo. Each is taken to the grey of the same brightness, which keeps the sprite's own
    // shading and picks no new hue — the neutral is the one thing that suits either background.
    for (i = 0; i < 64; i++) {
        const u16 v = original[i];
        const s16 r = (v >> 10) & 31;
        const s16 g = (v >> 5) & 31;
        const s16 b = v & 31;

        if (r > b + MENU_PAGE_WARMTH) {
            const s16 grey = (s16)((r * 2 + g * 3 + b) / 6);

            ColorRAM[MENU_PAGE_SLOT][i] = (u16)((v & 0x8000) | (grey << 10) | (grey << 5) | grey);
        } else {
            ColorRAM[MENU_PAGE_SLOT][i] = v;
        }
    }

    palUpdateGhostCP3(MENU_PAGE_SLOT, 1);
    return MENU_COL_CODE;
}

s16 ColEdit_Cursor(void) {
    return cursor;
}

u16 ColEdit_Color(void) {
    return ColorRAM[PREVIEW_COLOR_RAM][cursor];
}

void ColEdit_MoveCursor(s16 dx, s16 dy) {
    const s16 col = (s16)(((cursor % SWATCH_COLS) + dx + SWATCH_COLS) % SWATCH_COLS);
    const s16 row = (s16)(((cursor / SWATCH_COLS) + dy + SWATCH_ROWS) % SWATCH_ROWS);

    cursor = (s16)(row * SWATCH_COLS + col);
}

/// Five bits a channel widened to eight, the low bits repeated so that full scale stays full.
#define EXPAND5(v) (((v) << 3) | ((v) >> 2))

/// How far each channel is shifted in a ColorRAM entry. Red low, blue high — the order
/// palConvSrcToRam leaves behind, which is not the archive's.
static const u8 channel_shift[COL_EDIT_CHANNELS] = { 0, 5, 10 };
/// What each bar is drawn in when it is the one being changed
static const u32 channel_color[COL_EDIT_CHANNELS] = { 0xFFFF4040, 0xFF40FF40, 0xFF4040FF };

bool ColEdit_Editing(void) {
    return editing;
}

void ColEdit_BeginEdit(void) {
    editing = true;
    channel = 0;
}

void ColEdit_EndEdit(void) {
    editing = false;
}

void ColEdit_SelectChannel(s16 delta) {
    channel = (s16)(((channel + delta) % COL_EDIT_CHANNELS + COL_EDIT_CHANNELS) % COL_EDIT_CHANNELS);
}

static s16 channel_value(u16 ram, s16 which) {
    return (s16)((ram >> channel_shift[which]) & 31);
}

void ColEdit_Adjust(s16 delta) {
    u16 ram = ColorRAM[PREVIEW_COLOR_RAM][cursor];
    s16 value = (s16)(channel_value(ram, channel) + delta);

    if (value < 0) {
        value = 0;
    } else if (value > BAR_MAX) {
        value = BAR_MAX;
    }

    ram = (u16)((ram & ~(31u << channel_shift[channel])) | ((u32)value << channel_shift[channel]));

    // Both banks. A character's colours are written twice at load, into this slot and the one
    // eight above it, which is the mirrored copy the sprite path reaches for when the fighter
    // faces the other way. Editing one and not the other would show the change on one side only.
    ColorRAM[PREVIEW_COLOR_RAM][cursor] = ram;
    ColorRAM[PREVIEW_COLOR_RAM + 8][cursor] = ram;
}

u16 ColEdit_OriginalColor(void) {
    return original_pal[cursor];
}

bool ColEdit_Modified(void) {
    s16 i;

    // Before the load lands there is nothing to compare against, and answering "yes" then would
    // offer a SAVE of whatever the previous character left in ColorRAM.
    if (!original_saved) {
        return false;
    }

    for (i = 0; i < 64; i++) {
        if (ColorRAM[PREVIEW_COLOR_RAM][i] != original_pal[i]) {
            return true;
        }
    }

    return false;
}

/// One colour or all of them, put back into both banks the way ColEdit_Adjust writes them.
static void restore(s16 i) {
    ColorRAM[PREVIEW_COLOR_RAM][i] = original_pal[i];
    ColorRAM[PREVIEW_COLOR_RAM + 8][i] = original_pal[i];
}

void ColEdit_RevertColor(void) {
    if (original_saved) {
        restore(cursor);
    }
}

void ColEdit_RevertAll(void) {
    s16 i;

    if (!original_saved) {
        return;
    }

    for (i = 0; i < 64; i++) {
        restore(i);
    }

    _log("reverted character %d to its loaded palette", loaded_character);
}

/// One ColorRAM entry as an opaque ARGB8888 fill.
///
/// ColorRAM holds what palConvSrcToRam produced, which is not the layout the file had: red sits in
/// the low bits and blue in the high ones, the reverse of the archive's ARGB1555. Getting this
/// backwards is the same mistake that once turned every fighter's skin blue, and it passes every
/// numeric check, so it is worth naming. The top bit is the archive's alpha and means nothing to a
/// swatch — a colour that is transparent in play is still a colour being edited — so the fill is
/// forced opaque.
static u32 swatch_color(u16 ram) {
    const u32 r = EXPAND5((u32)(ram & 31));
    const u32 g = EXPAND5((u32)((ram >> 5) & 31));
    const u32 b = EXPAND5((u32)((ram >> 10) & 31));

    return 0xFF000000u | (r << 16) | (g << 8) | b;
}

/// Where a cell's bottom-left corner sits, relative to the grid's origin. The row runs downward
/// while y runs upward, hence the negation.
static void swatch_corner(s16 index, f32* x, f32* y) {
    *x = (f32)((index % SWATCH_COLS) * SWATCH_STEP);
    *y = (f32)(-(index / SWATCH_COLS) * SWATCH_STEP);
}

/// Anchor the flat quads that follow at an offset from the menu BG's origin.
///
/// Each panel sets this for itself. The sprite path leaves the current matrix wherever the fighter
/// is, and njTranslate accumulates, so a panel that inherited another's matrix would be placed
/// twice over.
static void panel_matrix(s16 x, s16 y, s16 z) {
    njSetMatrix(NULL, &BgMATRIX[PREVIEW_FAMILY]);
    njTranslate(NULL,
                bg_w.bgw[PREVIEW_FAMILY - 1].wxy[0].disp.pos + x,
                bg_w.bgw[PREVIEW_FAMILY - 1].wxy[1].disp.pos + y + base_y_pos,
                PrioBase[z]);
}

/// @brief A flat quad of one colour, at a depth of its own.
///
/// draw_hit_judge_line would do all of this except the depth, which it fixes at PrioBase[1] — the
/// layer the hit boxes use to sit over the fighters. A panel meant to go behind one cannot be
/// drawn with it, so the priority is a parameter here.
static void draw_quad(f32 px, f32 py, f32 sx, f32 sy, u32 col, s16 z) {
    Vec3 point[2];
    PAL_CURSOR quad;
    PAL_CURSOR_P xy[4];
    PAL_CURSOR_COL cc[4];

    point[0].x = px;
    point[0].y = py;
    point[0].z = 0.0f;
    point[1].x = px + sx;
    point[1].y = py + sy;
    point[1].z = 0.0f;
    njCalcPoints(NULL, point, point, 2);

    quad.p = xy;
    quad.col = cc;
    quad.tex = NULL;
    quad.num = 4;
    quad.p[0].x = quad.p[2].x = point[0].x;
    quad.p[1].x = quad.p[3].x = point[1].x;
    quad.p[0].y = quad.p[1].y = point[0].y;
    quad.p[2].y = quad.p[3].y = point[1].y;
    quad.col[0].color = quad.col[1].color = quad.col[2].color = quad.col[3].color = col;

    // The matrix carries position only: njCalcPoints hands back x and y, and the depth a quad ends
    // up at is this argument alone. Passing it is the whole reason this function exists.
    njDrawPolygon2D(&quad, 4, PrioBase[z], SWATCH_ATTR);
}

/// The two panels, behind the fighters rather than over them. The left one carries the fighter
/// being edited and the right one the same fighter in the palette he was loaded in, so that a
/// change is judged against what it replaced rather than against memory.
static void draw_backdrop(void) {
    panel_matrix(BACKDROP_X, BACKDROP_Y, BACKDROP_Z);
    draw_quad(0.0f, 0.0f, BACKDROP_W, BACKDROP_H, BACKDROP_COLOR, BACKDROP_Z);

    panel_matrix(BACKDROP2_X, BACKDROP_Y, BACKDROP_Z);
    draw_quad(0.0f, 0.0f, BACKDROP_W, BACKDROP_H, BACKDROP_COLOR, BACKDROP_Z);
}

/// @brief A three-by-five block font, one row of three bits per line, top row first.
///
/// The menus can draw text, but only text fixed when its effect is created: effect_61 walks the
/// string once and bakes a sprite per character. A value that follows the lever has to be redrawn
/// every frame, so it is built from the same flat quads as the bars themselves.
static const u8 digit_font[10][5] = {
    { 7, 5, 5, 5, 7 },   // 0
    { 2, 6, 2, 2, 7 },   // 1
    { 7, 1, 7, 4, 7 },   // 2
    { 7, 1, 7, 1, 7 },   // 3
    { 5, 5, 7, 1, 1 },   // 4
    { 7, 4, 7, 1, 7 },   // 5
    { 7, 4, 7, 5, 7 },   // 6
    { 7, 1, 1, 1, 1 },   // 7
    { 7, 5, 7, 5, 7 },   // 8
    { 7, 5, 7, 1, 7 },   // 9
};

/// One digit, its lower-left corner at x,y. Rows are listed top first while y climbs, hence the
/// flip on the row index.
static void draw_digit(f32 x, f32 y, s16 value, u32 col) {
    s16 row;
    s16 bit;

    for (row = 0; row < 5; row++) {
        for (bit = 0; bit < 3; bit++) {
            if (digit_font[value][row] & (4 >> bit)) {
                draw_quad(x + (f32)(bit * DIGIT_PIXEL), y + (f32)((4 - row) * DIGIT_PIXEL), DIGIT_PIXEL, DIGIT_PIXEL,
                          col, PANEL_Z);
            }
        }
    }
}

/// A channel's value, always two digits so the three columns stay aligned as values cross ten.
static void draw_value(f32 x, f32 y, s16 value) {
    draw_digit(x, y, (s16)(value / 10), VALUE_COLOR);
    draw_digit(x + DIGIT_W + DIGIT_GAP, y, (s16)(value % 10), VALUE_COLOR);
}

/// The three channel bars, their values above them, and the resulting colour below.
static void draw_bars(void) {
    const u16 ram = ColorRAM[PREVIEW_COLOR_RAM][cursor];
    s16 i;

    panel_matrix(BAR_ORIGIN_X, BAR_ORIGIN_Y, PANEL_Z);

    for (i = 0; i < COL_EDIT_CHANNELS; i++) {
        const f32 x = (f32)(i * BAR_STEP);
        const s16 filled = (s16)((channel_value(ram, i) * BAR_HEIGHT) / BAR_MAX);
        // Grey until the lever is on it, so which channel is live reads at a glance
        const u32 fill = (editing && i == channel) ? channel_color[i] : BAR_IDLE_COLOR;

        draw_quad(x, 0.0f, BAR_WIDTH, BAR_HEIGHT, BAR_TRACK_COLOR, PANEL_Z);

        if (filled > 0) {
            draw_quad(x, 0.0f, BAR_WIDTH, filled, fill, PANEL_Z);
        }

        draw_value(x + VALUE_X_OFFSET, (f32)(VALUE_Y - BAR_ORIGIN_Y), channel_value(ram, i));
    }

    panel_matrix(CHIP_X, CHIP_Y, PANEL_Z);
    draw_quad(0.0f, 0.0f, CHIP_W, CHIP_H, swatch_color(ram), PANEL_Z);
}

static void draw_swatches(void) {
    f32 x;
    f32 y;
    s16 i;

    panel_matrix(SWATCH_ORIGIN_X, SWATCH_ORIGIN_Y, PANEL_Z);

    for (i = 0; i < SWATCH_TOTAL; i++) {
        swatch_corner(i, &x, &y);
        draw_quad(x, y, SWATCH_SIZE, SWATCH_SIZE, swatch_color(ColorRAM[PREVIEW_COLOR_RAM][i]), PANEL_Z);
    }

    // The cursor as four edges rather than a filled box, so the colour it is over stays readable
    swatch_corner(cursor, &x, &y);
    draw_quad(x, y, SWATCH_SIZE, SWATCH_CURSOR_THICKNESS, SWATCH_CURSOR_COLOR, PANEL_Z);
    draw_quad(x, y + SWATCH_SIZE - SWATCH_CURSOR_THICKNESS, SWATCH_SIZE, SWATCH_CURSOR_THICKNESS,
              SWATCH_CURSOR_COLOR, PANEL_Z);
    draw_quad(x, y, SWATCH_CURSOR_THICKNESS, SWATCH_SIZE, SWATCH_CURSOR_COLOR, PANEL_Z);
    draw_quad(x + SWATCH_SIZE - SWATCH_CURSOR_THICKNESS, y, SWATCH_CURSOR_THICKNESS, SWATCH_SIZE,
              SWATCH_CURSOR_COLOR, PANEL_Z);
}

void ColEdit_Move(WORK* wk) {
    // Both fighters run through here, sharing the one effect table entry. Which is which is
    // settled by pointer: every WORK field that could have carried a flag is read by the sprite
    // path for something else, and the two are otherwise identical.
    const bool is_reference = (reference_ix != -1) && (wk == (WORK*)frw[reference_ix]);

    if (loaded_character < 0) {
        return;
    }

    // A character's colours are uploaded to the CP3 ghost, but this multitexture reads the DC one
    // — mts_base[3].mode has 1 in its low three bits, which picks palGetChunkGhostDC. Without this
    // copy the sprite asks for a palette handle that was never registered, and the renderer stops
    // the game outright rather than drawing it wrong. Done every frame so that editing a colour
    // shows up on the next one.
    //
    // The reference's copy is pushed every frame too, though its source never changes: the DC
    // ghost is a buffer the whole game shares, and leaving a slot filled once and trusting it to
    // stay is how a palette goes stale the first time anything else writes there.
    push_color_trans_req(is_reference ? REFERENCE_COLOR_RAM : PREVIEW_COLOR_RAM,
                         is_reference ? REFERENCE_GHOST_SLOT : PREVIEW_GHOST_SLOT);

    wk->cg_number = (u16)pose;

    // Re-anchored every frame rather than once at setup: the menu BG slides as pages come and go,
    // and a position taken down when the screen opened would drift with it. These are offsets from
    // that BG's origin, not screen coordinates — see PREVIEW_X.
    wk->position_x =
        (s16)(bg_w.bgw[PREVIEW_FAMILY - 1].wxy[0].disp.pos + (is_reference ? REFERENCE_X : PREVIEW_X));
    wk->position_y =
        (s16)(bg_w.bgw[PREVIEW_FAMILY - 1].wxy[1].disp.pos + (is_reference ? REFERENCE_Y : PREVIEW_Y));

    // The panels belong to the screen, not to either fighter, so they are drawn once — by the
    // edited one, who is the one guaranteed to exist.
    if (!is_reference) {
        draw_backdrop();
    }

    // A pattern outside the character's own group would send the sprite path looking for a texture
    // group nobody loaded, which it answers with an infinite loop rather than a return. Stepping
    // the pose can only stay inside the range, but the check costs nothing and the failure is not
    // one worth risking. Only the fighter is skipped: the swatches do not depend on him.
    if (obj_group_table[pose] == CHARACTER_GROUP(loaded_character)) {
        sort_push_request(wk);
    }

    if (is_reference) {
        return;
    }

    draw_swatches();
    draw_bars();

    if (!logged_draw) {
        logged_draw = true;
        _log("drawing at %d,%d, reference at %d", wk->position_x, wk->position_y,
             bg_w.bgw[PREVIEW_FAMILY - 1].wxy[0].disp.pos + REFERENCE_X);
    }
}

void ColEdit_Draw(void) {
    // Nothing to push here: the drawing belongs to ColEdit_Move, which the effect lists run from
    // inside the texture cache's window. This only nudges the load along.
    (void)ColEdit_Ready();
}

void ColEdit_Unload(void) {
    if (preview_ix != -1) {
        push_effect_work((WORK*)frw[preview_ix]);
        preview_ix = -1;
    }

    if (reference_ix != -1) {
        push_effect_work((WORK*)frw[reference_ix]);
        reference_ix = -1;
    }

    if (loaded_character >= 0) {
        // By key type, not by group. A player request brings in more than the character's own
        // textures — there is a shared group behind it too — and releasing a key clears whatever
        // group it held, so sweeping player one's keys takes down all of them. Freeing only the
        // character's group left that shared one marked resident, and the next request answered a
        // group it thought was already there with a duplicate transfer, which is fatal rather than
        // merely wrong.
        purge_player_texture(PREVIEW_PLAYER);
        Purge_memory_of_kind_of_key(lpc_seldat[PREVIEW_PLAYER]);
    }

    if (made_texcash) {
        purge_texcash_work(PREVIEW_MTS);
        made_texcash = false;
    }

    loaded_character = -1;
    pending_character = -1;
    pose = 0;
    logged_draw = false;
    // Dropped with the character it belongs to: a stale one would answer ColEdit_Modified for the
    // next fighter, and SAVE reads that answer.
    original_saved = false;
}
