#ifndef VIDEO_TEX_REMIX_H
#define VIDEO_TEX_REMIX_H

#include "sf33rd/AcrSDK/common/plcommon.h"
#include "types.h"

#include <stdbool.h>

/// @brief Where a page was loaded from. Recorded in the dump's manifest, and nothing more.
///
/// A replacement is still chosen by content alone; this only puts a name next to a fingerprint so a
/// dump can be read. The numbering is the one the drawing code uses: `seqsStoreChip` reaches a page
/// as `ppgGetUsingTextureHandle(NULL, gix + (code >> 8))`, which is @ref index. @ref first tells two
/// texture lists apart, since each numbers its own pages from its own base and the ranges overlap.
typedef struct {
    s32 index; ///< `ixNum`, the number the drawing code names this page by
    s32 first; ///< `ixNum1st` of the list it belongs to
    s32 entry; ///< archive entry the page was decompressed from
} TexPageOrigin;

/// @brief Swap a texture page for a higher-resolution replacement, if one is installed.
///
/// Called with the page the game has just decompressed, still in its own format, right before it is
/// handed to the texture pool. A replacement is found by what the page *contains*, never by where it
/// came from, so nothing has to know which screen or which archive entry is being loaded.
///
/// On a hit, `bits` is rewritten to describe the replacement -- larger, and always 32-bit colour --
/// and points at memory this module owns until the next call. Sprite corners are cut from a page in
/// fractions of its width, so a page that holds four times the pixels is cut in exactly the same
/// places: no geometry, no layout and no drawing code needs to hear about any of this.
///
/// @param from where the page came from, for the dump only. Required; nothing else reads it.
/// @return `true` if `bits` now describes a replacement, `false` to use the game's own page.
/// @brief Tell the remix which stage is loading, so a stage can own its pages by number.
///
/// Stages past the original 22 have no pages of their own in the archive: they borrow another
/// stage's file, so their pages carry that stage's fingerprints. Keying their replacements by
/// number instead of by content is what keeps the borrowed stage untouched.
void TexRemix_SetStage(s32 stage);

bool TexRemix_Substitute(plContext* bits, const TexPageOrigin* from);

/// @brief Tie the texture handle just created to the page last passed to @ref TexRemix_Substitute.
///
/// The dump writes a page as its index values, which is a shape and not a picture: the colours live
/// in a palette held somewhere else entirely, which is exactly what lets one sprite in twenty colour
/// schemes fingerprint as a single page. Recovering the picture means knowing which palette the game
/// draws it through, and the only place the two ever meet is a drawn quad. So the handles are
/// followed: this one names a texture, @ref TexRemix_NotePalette names a palette, and
/// @ref TexRemix_NotePair catches them together. Does nothing unless `tex-remix-dump` is on.
void TexRemix_NoteTextureHandle(u32 handle);

/// @brief Record a palette and tie it to its handle, fingerprinting it by its colours.
///
/// @param colours the palette's entries, as the game holds them
/// @param count how many entries
/// @param bytes bytes per entry, 2 for the 16-bit palettes and 4 for the 32-bit ones
void TexRemix_NotePalette(u32 handle, const void* colours, s32 count, s32 bytes);

/// @brief Remember the texture and palette a following quad will be drawn with.
///
/// @param tex_code the drawing code: texture handle low, palette handle high.
void TexRemix_NotePair(u32 tex_code);

/// @brief Record the patch of a page a quad covers, with the palette it is read through.
///
/// A page is not one picture through one palette. It is a bin: lettering, digits, a logo and a row
/// of mugshots packed together to fill it, and each of them is drawn through a palette slot of its
/// own -- `my_col_code` being an offset into a run of slots rather than an index. Colouring a whole
/// page through any single palette is therefore right over one patch and wrong everywhere else,
/// which is what the first attempt produced. The corners say which patch, so the page can be put
/// back together a patch at a time.
///
/// Coordinates are the quad's texture coordinates, 0 to 1 across the page.
void TexRemix_NoteQuad(float u0, float v0, float u1, float v1);

/// @brief Forget what a texture handle held. Called when one is (re)created, so a recycled
/// handle never keeps the mark of the page that used it before.
void TexRemix_ForgetHandle(u32 handle);

/// @brief Was this texture handle filled by a replacement page?
///
/// A page is not drawn as one quad. Its header carries a list of rectangles -- an 8x8 grid of
/// 16x16 blocks over a 128x128 page -- and `ppgWriteQuadUseTrans` draws only those, skipping
/// whatever the page left empty. That list belongs to the page the archive holds, and a
/// replacement does not change it: wherever the original was blank, the replacement's pixels are
/// never put on screen, and the layer behind shows through in 16x16 squares.
///
/// A replacement carries its own alpha and covers the whole page, so it wants one quad and no
/// coverage list. This is how the drawing code tells the two apart.
bool TexRemix_HandleIsReplacement(u32 handle);

/// @brief How much room the installed replacements will want in the texture pool, in bytes.
///
/// A page that grows sixteenfold and turns 32-bit needs a hundred times the memory it did, which the
/// pool was never sized for -- it was measured for a console, and a single 1024x1024 replacement
/// exhausts it outright. Asked once at startup, before the pool is created, so the pool can be made
/// big enough for whatever is actually installed. Nothing installed means nothing added, and the
/// game keeps the footprint it always had.
s64 TexRemix_ReservedBytes(void);

/// Drop everything held, so the next lookup re-reads the folder.
void TexRemix_Destroy(void);

#endif
