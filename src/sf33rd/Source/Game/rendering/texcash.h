#ifndef TEXCASH_H
#define TEXCASH_H

#include "structs.h"
#include "types.h"

/// L'etage pour lequel `mts[7]`, le cache des objets de decor, a ete taille.
///
/// `make_texcash_work` l'ecrit depuis toujours et PERSONNE ne le lisait. Son premier
/// lecteur est le journal du gel « x16 EXT2 » de `mtrans.c` : quand la reserve deborde, ce
/// qu'on veut savoir n'est pas l'etage courant mais celui dont la reserve a ete taillee --
/// les deux ne sont pas le meme quand un decor change de bande d'une manche a l'autre, ce que fait
/// Elena 2I (etage 56 a la manche 1, etage 30 ensuite).
extern s16 mts_ob_curr_stage;

extern TexturePoolUsed* tpu_free;
extern u8* texcash_melt_buffer;

void init_texcash_1st();
void init_texcash_2nd(s16 ix);
void init_texcash_before_process();
void search_texcash_free_area(s16 ix);
void update_with_tpu_free(PatternState* mc16, PatternState* mc32);
void texture_cash_update();
void make_texcash_work(s16 ix);
void purge_texcash_work(s16 ix);
void Clear_texcash_work();
s16 get_my_trans_mode(s16 curr);

#endif
