#ifndef EFF05_H
#define EFF05_H

#include "structs.h"
#include "types.h"

extern const s16 stg_dum_data_tbl[1];

/* La taille est ECRITE, et ce n'est pas cosmetique : declare `[]`, ce tableau est reste a
   37 entrees pendant que `scr_obj_num` et `scr_obj_data` passaient a 58, et rien -- ni le
   compilateur, ni l'audit des tableaux indexes par l'etage -- ne l'a signale. Les trois
   sont indexes par le meme `bg_index` et doivent garder la meme taille. */
extern u32* char_add[58];

void effect_05_move(WORK_Other* ewk);
s32 effect_05_init();

#endif
