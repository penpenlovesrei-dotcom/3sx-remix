#ifndef NEXT_CPU_H
#define NEXT_CPU_H

#include "types.h"

s8 Check_Bonus_Stage();
s16 Next_CPU();
s32 After_Bonus();
s16 Next_Q();
s16 Select_CPU_First();
void Setup_PL_Color(s16 PL_id, u16 sw);
/// @brief Make the next fight the basketball bonus stage, loading what it needs.
///
/// Declared because the training menu's PARRY THE BALL row reaches it too, where before only the
/// arcade run did. It answers 0 when there is no bonus to run.
s8 Check_Bonus_Stage();
s32 Auto_Cut_Sub();

#endif
