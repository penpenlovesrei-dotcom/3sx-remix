#include "port/video/trace_fin.h"

#include <stdio.h>

/* Vidage a chaque ligne : un gel ne doit pas emporter la derniere information ecrite.
   C'est justement le cas qu'on instrumente -- `get_mltbuf16_ext` ne rend jamais la main. */
void TraceFin(const char* fmt, s32 a, s32 b, s32 c) {
    static FILE* jrn = NULL;
    static s32 lignes = 0;

    if (jrn == NULL) {
        jrn = fopen("fin-de-round.log", "w");

        if (jrn == NULL) {
            return;
        }
    }

    /* Borne : `Bg_On_R` peut etre appele a chaque trame. On veut la fin de round, pas un
       fichier de cent mega-octets. */
    if (lignes >= 4000) {
        return;
    }

    lignes++;
    fprintf(jrn, fmt, (int)a, (int)b, (int)c);
    fflush(jrn);
}
