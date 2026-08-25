#ifndef VIDEO_PAL_REMIX_H
#define VIDEO_PAL_REMIX_H

#include "types.h"

#include <stdbool.h>

/// @name Palette sets a character row can be set to
/// Positions in `LETTER_TYPE_CHARACTER_SET`. `3rd Strike` is the game's own data and needs no
/// files; `Random` picks one of the sets that has them.
/// @{
#define PAL_SET_NEW_GENERATION 0
#define PAL_SET_2ND_IMPACT 1
#define PAL_SET_3RD_STRIKE 2
#define PAL_SET_CHARACTER_RANDOM 3
/// @}

/// @name Palette sets a background row can be set to
/// Positions in `LETTER_TYPE_BACKGROUND_SET`. `Original` is the game's own data.
/// @{
#define PAL_SET_ORIGINAL 0
#define PAL_SET_RETHIRD 1
#define PAL_SET_PER_ROUND 2
#define PAL_SET_BACKGROUND_RANDOM 3
/// @}

/// @brief Palette data replacing a character's file, or `NULL` to use the game's own.
///
/// The payload is a verbatim stand-in for the entry the game would have read out of the archive,
/// so `init_trans_color_ram` reads it with the layout it already knows: `u16 col[28][64]`, or
/// twice that for Gill, who is the only one carrying both banks.
///
/// @param character Engine character number, as `constants.h` numbers them.
/// @param set One of the `PAL_SET_*` character values, which is what the Custom screen stores.
/// @param size Filled in with the payload's length in bytes when one is returned.
const void* PalRemix_Character(s16 character, s16 set, s32* size);

/// @brief Palette data replacing a stage's file, or `NULL` to use the game's own.
///
/// A stage's palette block has no fixed length — the stages range from 6 palettes to 128 — so the
/// replacement carries its own, and `init_trans_color_ram` uploads however many it holds.
///
/// @param stage Stage number, which is its character's number.
/// @param set One of the `PAL_SET_*` background values.
/// @param size Filled in with the payload's length in bytes when one is returned.
const void* PalRemix_Stage(s16 stage, s16 set, s32* size);

/// @brief Whether any set at all is installed, so the menus can grey out what cannot be chosen.
/// @param set One of the `PAL_SET_*` values for that kind of row.
bool PalRemix_HasCharacterSet(s16 set);
bool PalRemix_HasBackgroundSet(s16 set);

/// @brief Whether one character or stage has a palette in a set.
///
/// Availability is per subject, not per set: New Generation has no Makoto and 2nd Impact no Q, so
/// their rows must not offer a set that cannot dress them. Answering this per row is what keeps
/// the screen honest about which fighters those games ever had.
bool PalRemix_HasCharacter(s16 character, s16 set);
bool PalRemix_HasStage(s16 stage, s16 set);

/// Drop everything held, so the next lookup re-reads the folders.
void PalRemix_Destroy(void);

#endif
