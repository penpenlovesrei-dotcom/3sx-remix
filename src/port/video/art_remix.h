#ifndef VIDEO_ART_REMIX_H
#define VIDEO_ART_REMIX_H

#include "types.h"

#include <stdbool.h>

/// @brief The texture code for a character select portrait's replacement, or 0 if there is none.
///
/// Unlike a texture page, a portrait cannot be swapped for its pixels: it is assembled at draw time
/// from 16x16 chips melted into a streaming cache, so there is no loaded page to stand in for. A
/// replacement is therefore a picture of its own, drawn over the box the chips would have covered,
/// and this hands out the texture to draw with.
///
/// Files live in `<resources>/art_remix/`, named `face-NN.tex` after the select screen's own face
/// number, with `any.tex` standing in for every face that has no file of its own. The container is
/// the one `tools/make_tex.py` already writes.
///
/// @param face the portrait's face number, as the select screen numbers them
/// @param width receives the picture's width, needed to keep its proportions on the box
/// @param height receives the picture's height
/// @return a code for `FLRENDER_TEXSTAGE0`, or 0 when nothing is installed for this face
u32 ArtRemix_TexCode(s32 face, s32* width, s32* height);

/// @brief How much room the installed portraits want in the texture pool, in bytes.
///
/// Asked once at startup, before the pool is created. An Online Edition portrait is a few megabytes
/// on its own and the pool was measured for a console, so without this the first one to load empties
/// it. Nothing installed adds nothing.
s64 ArtRemix_ReservedBytes(void);

/// Drop every loaded portrait and its texture handle.
void ArtRemix_Destroy(void);

#endif
