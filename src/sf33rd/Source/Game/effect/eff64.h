#ifndef EFF64_H
#define EFF64_H

#include "structs.h"
#include "types.h"

#include <stdbool.h>

/// Row of Letter_Data_64 whose values are the installed soundtracks
#define LETTER_TYPE_SOUNDTRACK 16
/// @name Rows of Letter_Data_64 belonging to the Display page
/// @{
#define LETTER_TYPE_RESOLUTION 17
#define LETTER_TYPE_SD_HD 18
#define LETTER_TYPE_BACKGROUNDS 19
/// Same values per stage, on the Custom backgrounds screen
#define LETTER_TYPE_BACKGROUND_SET 20
/// How a character's palette set gets chosen
#define LETTER_TYPE_CHARACTER_COLOR 21
/// Same per character, on the Custom character colours screen, and that screen's navigation row
#define LETTER_TYPE_CHARACTER_SET 22
#define LETTER_TYPE_PAGE_NAV 23
/// @}
/// @name How a character's palette set gets chosen
///
/// The CHAR. COLOR row no longer names a set. Naming one there meant every fighter wore the same
/// game's colours and neither player could say otherwise, which is the wrong shape for a setting
/// two people share a screen over. The row now names the **way** a set is picked, and the picking
/// itself happens where the fighters are chosen.
///
/// @{
/// The game's own colours throughout, as if none of this existed.
#define CHAR_COLOR_MODE_DISABLED 0
/// One set per fighter, from the Custom character colours screen.
#define CHAR_COLOR_MODE_CUSTOM 1
/// Stepped with Start on the character select screen, which shows what each side is on.
#define CHAR_COLOR_MODE_START 2
#define CHAR_COLOR_MODES 3
/// @}

/// @brief A Player_Pal_Set value meaning "whatever the Custom screen holds for this fighter".
///
/// Not a set of its own — it is the fourth stop of the Start button's cycle, and it defers rather
/// than deciding, so that the per-fighter screen keeps working underneath the per-player choice.
/// Sits past the four real sets so it can never collide with one.
#define PAL_SET_PER_CHARACTER 4

/// @brief The colour editor's own palette, as a stop on the Start button's cycle.
///
/// Nothing behind it yet: the editor can change a palette but cannot save one, so there is no set
/// on disk for this to name. It cycles into view greyed rather than being hidden, which is how
/// every other unfinished value in these menus behaves — the row shows where it is going.
#define PAL_SET_COLOR_EDIT 5

/// Row of the Display page holding that mode. Named here, beside the buffer it indexes, because
/// the setting is read from the select screen and from the palette loader — both a long way from
/// the page that writes it.
#define DISPLAY_ROW_CHARACTER_COLOR 2
/// LETTER_TYPE_PAGE_NAV values
#define PAGE_NAV_PREV 0
#define PAGE_NAV_EXIT 1
#define PAGE_NAV_NEXT 2
/// The LETTER_TYPE_BACKGROUNDS value that opens the per-stage screen rather than setting anything
#define BACKGROUNDS_VALUE_CUSTOM 4
/// Convert_Buff row reserved for the Custom tracklist, which has its own buffer
#define CONVERT_ID_CUSTOM 4
/// Likewise for the Display page and its Custom backgrounds screen. Convert_Buff only has four
/// rows, so all three are sentinels
#define CONVERT_ID_DISPLAY 5
#define CONVERT_ID_BACKGROUND 6
#define CONVERT_ID_CHARACTER 7
#define CONVERT_ID_PAGE_NAV 8
/// Rows per page of the two long Custom screens
#define CHARACTER_PAGE_ROWS 8
#define BACKGROUND_PAGE_ROWS 8

/// One soundtrack choice per stage theme, as a position in the soundtrack list. Indexed by theme,
/// which is the order the save file uses — not the order the screen lists them in.
extern s8 Custom_Buff[16];
extern s8 Custom_Page;

/// Which theme each row of the Custom tracklist stands for, the screen being sorted by character
extern const s8 Custom_Row_To_Theme[16];

/// Which character a row of the characters or backgrounds screen stands for, both being sorted
/// alphabetically while the palettes behind them use the engine's numbering. Stages carry their
/// character's number, so one table covers both.
extern const s8 Custom_Row_To_Char[20];
/// Themes listed per page of it
#define CUSTOM_PAGE_ROWS 8

/// The value shown on each row of the Display page, as a position in its Letter_Data_64 row
extern s8 Display_Buff[8];

/// One background set per stage, as a position in LETTER_TYPE_BACKGROUND_SET. As with the
/// characters, the page decides which eight of them the screen is showing.
extern s8 Background_Buff[20];
extern s8 Background_Page;

/// One palette set per character, alphabetically, as a position in LETTER_TYPE_CHARACTER_SET. The
/// page decides which five of them the screen is showing, so the value works index through it.
extern s8 Character_Buff[20];
extern s8 Character_Page;
extern s8 Page_Nav_Value;

/// @name The set each side is wearing, chosen on the character select screen
///
/// Per player rather than per fighter, which the buffer above cannot be: two people can pick the
/// same fighter, and the screen shows them each a line of their own.
/// @{
extern s8 Player_Pal_Set[2];

/// @brief Which set a player's fighter should actually be dressed in.
///
/// The one place that answers the question, so that the loader, the select screen and anything
/// else all agree. Falls back to the game's own colours whenever the chosen set has nothing for
/// this fighter — New Generation never had Makoto, and a set that cannot dress her must not be
/// allowed to leave her half-painted.
///
/// @param player 0 or 1.
/// @param character Engine character number, as `constants.h` numbers them.
s16 Character_Palette_Set(s16 player, s16 character);

/// Step one player to the next set, in the order the Start button walks: the game's own colours
/// first, then the two earlier games, then whatever the Custom screen says.
void Character_Palette_Cycle(s16 player);

/// What to print for a player's current set, in the select screen's own charset. Never NULL.
const s8* Character_Palette_Name(s16 player);

/// Whether the set a player is on can actually dress anyone, or is only showing where the cycle
/// goes. A false here is what the select screen dims its line for.
bool Character_Palette_Selectable(s16 player);

/// Put both sides back on the game's own colours, for a fresh visit to the select screen.
void Character_Palette_Reset(void);
/// @}

/// @brief Whether one entry of a value row can actually be chosen.
///
/// The Display page advertises settings the port cannot honour yet. They cycle into view greyed
/// out so the row shows where it is going, and the page puts the value back before leaving.
/// Custom on the backgrounds row is the exception: picking it applies nothing, but it opens the
/// per-stage screen, so it reads as live.
/// @param subject The character or stage the row stands for, or -1 where the row is a global
///        setting rather than one per fighter. Availability of a palette set is per subject.
s16 letter_data_64_selectable(s16 letter_type, s16 disp_index, s16 subject);

void effect_64_move(WORK_Other_CONN* ewk);
s32 effect_64_init(u8 dir_old, s16 sync_bg, s16 master_player, s16 letter_type, s16 cursor_index, u16 char_offset,
                   s16 pos_index, s16 convert_id, s16 convert_id2);

#endif
