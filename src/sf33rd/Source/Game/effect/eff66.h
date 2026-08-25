#ifndef EFF66_H
#define EFF66_H

#include "structs.h"
#include "types.h"

/// @brief Index in `frw` of the work effect_66_init made last, or -1 if it could not make one.
///
/// A caller that wants to change something about the sprite it just asked for — its palette, say —
/// has no other way to reach it: the init returns only success, and the colour code it sets is the
/// one every menu element shares. Fifty-one call sites made adding a parameter the worse trade.
extern s16 effect_66_last_work;

void effect_66_move(WORK_Other* ewk);
s32 effect_66_init(s16 order_index, s16 id, s16 master_player, s16 target_bg, s16 char_ix, s16 char_ix2, s16 option);

#endif
