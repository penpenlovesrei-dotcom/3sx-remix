#ifndef SOUND_BGM_REMIX_H
#define SOUND_BGM_REMIX_H

#include <stdbool.h>

/// Highest BGM code that can be overridden. Matches the size of `bgm_table` entries in sound3rd.c.
#define BGM_REMIX_CODE_MAX 67

/// Last BGM code belonging to a stage theme. Codes 1..48 are 16 stages of 3 per-round mixes;
/// everything above is a jingle or a menu track with no round variation.
#define BGM_REMIX_STAGE_CODE_MAX 48

/// How many packs can be installed at once. Each takes a slot in `BgmType`, so raising this
/// widens every table indexed by the BGM type.
#define BGM_REMIX_PACKS_MAX 8

/// @name BGM type values
/// Mirrored by the `BgmType` enum, which this module can't include: `structs.h` includes this
/// header, not the other way around.
/// @{
#define BGM_REMIX_TYPE_ARRANGED 0
#define BGM_REMIX_TYPE_ORIGINAL 1
#define BGM_REMIX_TYPE_FIRST_PACK 2
/// Draws one of the real soundtracks per fight rather than being one itself
#define BGM_REMIX_TYPE_RANDOM (BGM_REMIX_TYPE_FIRST_PACK + BGM_REMIX_PACKS_MAX)
/// Reads a soundtrack per stage from custom.txt rather than being one itself
#define BGM_REMIX_TYPE_CUSTOM (BGM_REMIX_TYPE_RANDOM + 1)
/// @}

/// Menu positions: the two stock soundtracks, one per pack, then Random and Custom
#define BGM_REMIX_SLOTS_MAX (BGM_REMIX_TYPE_CUSTOM + 1)

/// @name Pack name widths
///
/// The `BGM Type` row draws one sprite per character starting at x=64, and the screen's right
/// edge sits at x=192 in the menu's centred coordinates — 128px of room. The menu's own charset
/// has a 14px pitch, which fits 9 characters; the sound test's smaller charset has an 8px pitch
/// and fits 16. A name keeps the stock charset while it fits the wide budget and switches to the
/// narrow one otherwise, and a `~` in the name flips between the two mid-text — hence the couple
/// of extra characters of room here, which markers don't spend on width.
/// @{
#define BGM_REMIX_NAME_MAX 18
#define BGM_REMIX_NAME_WIDE_MAX 9
/// @}


/// @brief Path of the .adx overriding a BGM code.
///
/// A stage code with no entry of its own resolves to its stage's mix 1 entry, so a pack holding
/// a single track per stage covers all three rounds.
///
/// @param pack 0-based pack index.
/// @param bgm_code Index into `bgm_table` (1..BGM_REMIX_CODE_MAX).
/// @return Path owned by this module, or `NULL` when the pack doesn't override this code.
const char* BgmRemix_GetTrackPath(int pack, int bgm_code);

/// @brief Sound test label overriding a BGM code, resolved like `BgmRemix_GetTrackPath`.
/// @return Label owned by this module, or `NULL` to fall back to the arranged label.
const char* BgmRemix_GetTrackName(int pack, int bgm_code);

/// @brief Whether a pack follows the arcade soundtrack's layout — two per-round mixes per stage
///        instead of three — and so should read the game's arcade tables.
///
/// The sound test then skips the third-mix codes the arcade never had, instead of listing them as
/// duplicates of the first, and codes the pack leaves out fall back to arcade tracks rather than
/// arranged ones. Declared by a pack with `!structure arcade`.
bool BgmRemix_UsesArcadeTables(int pack);

/// @brief Level trim a pack asks for, in tenths of a decibel, or 0 when it asks for none.
///
/// The game sets each track's volume from its own tables, which are calibrated for how loudly
/// Capcom mastered that soundtrack. A pack mastered to a different reference plays louder or
/// quieter than the rest of the game for that reason alone, so it can correct itself with
/// `!volume <dB>`.
int BgmRemix_GetVolumeTrim(int pack);

/// @name BGM Type row layout
///
/// The row's order is a user's choice, so the menu works in slots and translates to a BGM type
/// only when handing the value to the sound engine. Saves keep storing the type, which means
/// reordering the row later never repoints a saved setting at a different soundtrack.
/// @{

/// @brief Number of values the `BGM Type` row offers.
int BgmRemix_GetSlotCount();

/// @brief BGM type shown at a menu position.
/// @return A `BgmType` value, or `BGM_REMIX_TYPE_ARRANGED` when `slot` is out of range.
int BgmRemix_GetSlotType(int slot);

/// @brief Menu position showing a BGM type. The inverse of `BgmRemix_GetSlotType`.
/// @return 0 when the type has no slot, so a stale saved value lands on the first entry.
int BgmRemix_GetSlotForType(int type);

/// @brief Draw a soundtrack for `BGM_RANDOM`, avoiding an immediate repeat of `previous`.
/// @return A real BGM type, never `BGM_REMIX_TYPE_RANDOM`.
int BgmRemix_PickRandomType(int previous);

/// @brief Whether the row holds more than one real soundtrack, so drawing between them means
///        something. When it doesn't, the Random entry is left off the row.
bool BgmRemix_CanRandomise();

/// @brief Soundtrack the player assigned to a stage theme in `custom.txt`.
/// @param base_code The stage's mix 1 BGM code — 1, 4, 7 … 46.
/// @return A real BGM type, or -1 when that stage has no assignment.
int BgmRemix_GetCustomType(int base_code);

/// @brief Whether `custom.txt` assigns at least one stage, so the Custom entry is worth showing.
bool BgmRemix_HasCustom();

/// @name The Custom tracklist screen
///
/// The screen offers each stage theme a soundtrack, so it works in two flat lists: the sixteen
/// stages in code order, and the real soundtracks — Random and Custom excluded, since neither is
/// one and letting a stage pick Custom would be circular.
/// @{

/// Number of stage themes the screen lists
int BgmRemix_GetStageCount();

/// @brief The mix 1 BGM code of the stage at `index`, which is what custom.txt keys on.
int BgmRemix_GetStageCode(int index);

/// Number of soundtracks a stage can be assigned
int BgmRemix_GetSoundtrackCount();

/// @brief Name of the soundtrack at `index`, as the row should show it.
const char* BgmRemix_GetSoundtrackLabel(int index);

/// @brief Whether a soundtrack has a track for one stage theme.
///
/// A pack need not cover every stage — New Generation has no music for fighters that game never
/// had — and an uncovered stage falls back to the arranged track. Answering this per row lets the
/// Custom screen grey out a soundtrack on the stages it cannot fill, rather than offering a choice
/// that silently does nothing. The two stock soundtracks cover everything.
///
/// @param index Position in the soundtrack list, as `BgmRemix_GetSoundtrackLabel` numbers them.
/// @param stage_index Position in the stage theme list, which is what `custom.txt` keys on.
bool BgmRemix_SoundtrackCoversStage(int index, int stage_index);

/// @brief Soundtrack currently assigned to the stage at `index`, as a position in that list.
int BgmRemix_GetStageChoice(int index);

/// @brief Assign the soundtrack at `soundtrack_index` to the stage at `stage_index`.
void BgmRemix_SetStageChoice(int stage_index, int soundtrack_index);

/// Write the assignments back to custom.txt, so they outlive the session
void BgmRemix_SaveCustom();
/// @}

/// @brief Text a menu position shows.
/// @return The pack name, a `menu.txt` override, or `NULL` for a stock entry the user left
///         alone — the caller then uses the game's own text.
const char* BgmRemix_GetSlotLabel(int slot);
/// @}

/// Release the loaded packs
void BgmRemix_Destroy();

#endif
