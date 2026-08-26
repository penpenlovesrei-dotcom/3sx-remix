#ifndef BBBSCOM_H
#define BBBSCOM_H

#include "structs.h"
#include "types.h"

extern const BBBSTable* bbbs_table[][5];

/// @name PARRY THE BALL, the training menu's way into this stage
///
/// The arcade reaches the basketball bonus after the third and sixth fights of a run, at a level
/// drawn from the player's grade. The training row asks for it directly, and names the level
/// itself — which the stage already allows, `makeup_bonus_game_level` reading a held button
/// combination for exactly that. This is the same door with a menu in front of it.
/// @{
/// The basketball's stage number, which is also the Bonus_Type that selects it
#define PARRY_THE_BALL_STAGE 21

/// @param on Whether the next fight should be the bonus stage instead.
/// @param level 0 to 9, as set_bonus_game_nando numbers them: 0-4 are one set of throw patterns
///        and 5-9 the other.
void Request_Parry_The_Ball(s16 on, s16 level);
/// Whether the menu asked. Read where a fight would otherwise start.
s32 Parry_The_Ball_Requested(void);
/// Forget the request, so leaving the stage does not walk straight back into it.
void Parry_The_Ball_Clear(void);
/// Whether this stage was entered from the training row at all, which stays true for the whole of
/// it -- the request itself is spent as soon as the level is settled.
s32 Parry_The_Ball_Was_Requested(void);
/// Clear that, on the way out.
void Parry_The_Ball_Forget(void);
/// Arm the level again for another run of the stage, the end menu's RETRY.
void Parry_The_Ball_Again(void);
/// The level the end menu shows and changes, 0 to 9.
s32 Parry_The_Ball_Level(void);
void Parry_The_Ball_Step_Level(s16 delta);
/// @}

void bbbs_com_execute(PLW* wk);
void bbbs_com_initialize();
void makeup_bonus_game_level(s16 ix);
s32 set_bonus_game_difficulty(s16 emid);
s32 set_bonus_game_nando(u16 swdat);
s32 katteni_bonus_nando(u16 swdat);

#endif
