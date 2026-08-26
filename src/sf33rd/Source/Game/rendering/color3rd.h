#ifndef COLOR3RD_H
#define COLOR3RD_H

#include "sf33rd/Source/Game/io/gd3rd.h"
#include "structs.h"
#include "types.h"

extern u16 ColorRAM[512][64];
extern Col3rd_W col3rd_w;

void q_ldreq_color_data(LoadRequest* curr);
void load_any_color(u16 ix, u8 kokey);
void set_hitmark_color();
void init_trans_color_ram(s16 id, s16 key, u8 type, u16 data);
void init_color_trans_req();
void push_color_trans_req(s16 from_col, s16 to_col);
void palCopyGhostDC(s32 ofs, s32 cnt, void* data);
u16 palConvSrcToRam(u16 col);
/// The way back, for anything writing a palette out in the layout the archive uses.
u16 palConvRamToSrc(u16 col);
/// @brief The game's own palette entry for the character a player was loaded with, or NULL before
/// one has been.
///
/// The archive's, not the installed set's: a set is a file that can be read again at will, while
/// this is only in memory for the length of the call that reads it. ColorRAM keeps one row of the
/// twenty-eight, which is not enough to write an entry back out or to show another coloris.
/// @param size Filled in with its length in bytes.
const void* palGetPlayerSource(s16 id, s32* size);
void palCreateGhost();
Palette* palGetChunkGhostDC();
Palette* palGetChunkGhostCP3();
void palUpdateGhostDC();
void palUpdateGhostCP3(s32 pal, s32 nums);

#endif
