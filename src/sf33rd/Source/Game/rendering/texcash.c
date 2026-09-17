/**
 * @file texcash.c
 * Texture Cache Manager
 */

#include "sf33rd/Source/Game/rendering/texcash.h"
#include "port/video/etagesng_plans.inc"
#include "port/video/etages2ibis_plans.inc"
#include "common.h"
#include "port/utils.h"
#include "sf33rd/Source/Common/PPGFile.h"
#include "sf33rd/Source/Game/effect/effect.h"
#include "sf33rd/Source/Game/rendering/aboutspr.h"
#include "sf33rd/Source/Game/rendering/mtrans.h"
#include "sf33rd/Source/Game/stage/bg.h"
#include "sf33rd/Source/Game/system/ramcnt.h"
#include "sf33rd/Source/Game/system/sys_sub.h"
#include "structs.h"

#include <SDL3/SDL.h>

typedef struct {
    s32 p16;
    s32 p32;
    s32 gix;
    s16 life16;
    s16 life32;
    s16 type;
    u16 mode;
    u32 attribute;
} MTSBase;

s8* texcash_name[29] = { "    16x16 (tm)  32x32 (tm) GIX      (mn.nw)",
                         "QA",
                         "HT",
                         "1P",
                         "2P",
                         "CA",
                         "SW",
                         "OB",
                         "ED",
                         "DM",
                         "OT",
                         "MJ",
                         "MS",
                         "SL",
                         "EU",
                         "RR",
                         "GI",
                         "xx",
                         "xx",
                         "xx",
                         "xx",
                         "xx",
                         "xx",
                         "xx",
                         "   /   (  )    /   (  )     +    (  .  )",
                         "--- --- --  --- --- --  ---   --  -- --",
                         "--- --- --",
                         "--",
                         "--.--" };

u8* texcash_melt_buffer;
TexturePoolUsed* tpu_free;
s16 mts_ob_curr_stage;

// forward decls
extern const s16 mts_OB_page[58][2];
extern const MTSBase mts_base[24];
void clear_texcash_work(s16 ix);

void search_texcash_free_area(s16 ix) {
    PatternState* mc;
    s16 i;
    s16 num = 0;

    for (mc = mts[ix].mltcsh16, i = 0; i < mts[ix].mltnum16; i++) {
        if (mc[i].cs.code == -1) {
            num++;
        }
    }

    if (num < mts_ok[ix].min16) {
        mts_ok[ix].min16 = num;
    }

    num = 0;
    for (mc = mts[ix].mltcsh32, i = 0; i < mts[ix].mltnum32; i++) {
        if (mc[i].cs.code == -1) {
            num++;
        }
    }

    if (num < mts_ok[ix].min32) {
        mts_ok[ix].min32 = num;
    }

    if ((mts[ix].ext) && (mts[ix].cpat->kazu > mts_ok[ix].mincg)) {
        mts_ok[ix].mincg = mts[ix].cpat->kazu;
    }
}

void init_texcash_1st() {
    s16 i;

    for (i = 0; i < MULTITEXTURE_MAX; i++) {
        mts_ok[i].be = 0;
        mts_ok[i].mincg = 0;
        mts_ok[i].min16 = 0x7FFF;
        mts_ok[i].min32 = 0x7FFF;
        mts_ok[i].key0 = 0;
        mts_ok[i].key1 = 0;
        mts[i].mode = -1;
    }
}

void init_texcash_before_process() {
    s16 i;

    for (i = 1; i < 24; i++) {
        if ((mts_ok[i].be) && (mts[i].ext)) {
            init_texcash_2nd(i);
        }
    }
}

void init_texcash_2nd(s16 ix) {
    PatternState* mc;
    PatternCollection* cp;
    TexturePoolFree* tf;
    TexturePoolUsed* tu;
    s16 i;

    tf = mts[ix].tpf;
    tu = mts[ix].tpu;
    cp = mts[ix].cpat;
    tf->x32 = 0;
    tf->x16 = 0;
    tu->x32 = 0;
    tu->x16 = 0;
    mc = mts[ix].mltcsh16;

    for (i = mts[ix].mltnum16 - 1; i >= 0; i--) {
        if (mc[i].cs.code == -1) {
            tf->x16_free[tf->x16] = i;
            tf->x16 += 1;
        } else {
            tu->x16_used[tu->x16] = i;
            tu->x16 += 1;
        }
    }

    mc = mts[ix].mltcsh32;

    for (i = mts[ix].mltnum32 - 1; i >= 0; i--) {
        if (mc[i].cs.code == -1) {
            tf->x32_free[tf->x32] = i;
            tf->x32 += 1;
        } else {
            tu->x32_used[tu->x32] = i;
            tu->x32 += 1;
        }
    }

    cp->kazu = 0;

    for (i = 0; i < PATTERN_COLLECTION_MAX; i++) {
        if (cp->patt[i].time) {
            cp->adr[cp->kazu] = &cp->patt[i];
            cp->kazu += 1;
        }
    }
}

void texture_cash_update() {
    s16 i;
    s16 num;

    for (num = 0; num < 24; num++) {
        if (mts_ok[num].be != 0) {
            if (mts[num].ext) {
                for (i = 0; i < mts[num].cpat->kazu; i++) {
                    if ((--mts[num].cpat->adr[i]->time) == 0) {
                        makeup_tpu_free(mts[num].mltnum16 / 256, mts[num].mltnum32 / 64, &mts[num].cpat->adr[i]->map);

                        if ((tpu_free->x16 != mts[num].cpat->adr[i]->x16) ||
                            (tpu_free->x32 != mts[num].cpat->adr[i]->x32)) {
                            SDL_assert(false);
                        }

                        update_with_tpu_free(mts[num].mltcsh16, mts[num].mltcsh32);
                    }
                }
            } else {
                if ((mts[num].mltcshtime16 + mts[num].mltcshtime32) != 0) {
                    mlt_obj_trans_update(&mts[num]);
                }
            }

            search_texcash_free_area(num);
        }
    }
}

void update_with_tpu_free(PatternState* mc16, PatternState* mc32) {
    s16 i;

    for (i = 0; i < tpu_free->x16; i++) {
        mc16[tpu_free->x16_used[i]].time -= 1;

        if (mc16[tpu_free->x16_used[i]].time < 0) {
            SDL_assert(false);
        }

        if (mc16[tpu_free->x16_used[i]].time <= 0) {
            mc16[tpu_free->x16_used[i]].cs.code = -1;
        }
    }

    for (i = 0; i < tpu_free->x32; i++) {
        mc32[tpu_free->x32_used[i]].time -= 1;

        if (mc32[tpu_free->x32_used[i]].time < 0) {
            SDL_assert(false);
        }

        if (mc32[tpu_free->x32_used[i]].time <= 0) {
            mc32[tpu_free->x32_used[i]].cs.code = -1;
        }
    }
}

s16 get_my_trans_mode(s16 curr) {
    if (mts_ok[curr].be == 0) {
        return -1;
    }

    return mts[curr].mode;
}

void make_texcash_work(s16 ix) {
    size_t memreq;
    u8* adrs;
    u32 page16;
    u32 page32;

    if (mts_ok[ix].be) {
        if ((Test_ramcnt_key(mts_ok[ix].key0) != 0) && (Test_ramcnt_key(mts_ok[ix].key1) != 0)) {
            return;
        }

        fatal_error("make_texcash_work: TEXCASH KEY ERROR");
    } else {
        if (ix == 7) {
            page16 = mts_OB_page[bg_w.stage][0];
            page32 = mts_OB_page[bg_w.stage][1];
            mts_ob_curr_stage = bg_w.stage;
        } else {
            page16 = mts_base[ix].p16;
            page32 = mts_base[ix].p32;
        }

        mts[ix].mltnum16 = (u32)page16 << 8;
        mts[ix].mltnum32 = page32 << 6;
        mts[ix].mltnum = (u32)page16 + page32;
        mts[ix].mltgidx16 = mts_base[ix].gix;
        mts[ix].mltgidx32 = (u32)page16 + mts_base[ix].gix;
        mts[ix].mltcshtime16 = mts_base[ix].life16;
        mts[ix].mltcshtime32 = mts_base[ix].life32;

        if ((mts[ix].ext = ((mts_base[ix].mode & 0x2000) != 0))) {
            memreq = (mts[ix].mltnum16 * 8) + (mts[ix].mltnum32 * 8) + sizeof(PatternCollection) +
                     sizeof(TexturePoolFree) + sizeof(TexturePoolUsed);
            mts_ok[ix].key0 = Pull_ramcnt_key(memreq, mts_base[ix].type, 0, 0);
            adrs = Get_ramcnt_pointer(mts_ok[ix].key0);
            mts[ix].mltcsh16 = (PatternState*)adrs;
            adrs += mts[ix].mltnum16 * 8;
            mts[ix].mltcsh32 = (PatternState*)adrs;
            adrs += mts[ix].mltnum32 * 8;
            mts[ix].cpat = (PatternCollection*)adrs;
            adrs += sizeof(PatternCollection);
            mts[ix].tpf = (TexturePoolFree*)adrs;
            adrs += sizeof(TexturePoolFree);
            mts[ix].tpu = (TexturePoolUsed*)adrs;
            SDL_zerop(mts[ix].cpat);
            SDL_zerop(mts[ix].tpf);
            SDL_zerop(mts[ix].tpu);
            init_texcash_2nd(ix);
        } else {
            memreq = mts[ix].mltnum16 * 8 + mts[ix].mltnum32 * 8;
            mts_ok[ix].key0 = Pull_ramcnt_key(memreq, mts_base[ix].type, 0, 0);
            adrs = Get_ramcnt_pointer(mts_ok[ix].key0);
            mts[ix].mltcsh16 = (PatternState*)adrs;
            adrs += mts[ix].mltnum16 * 8;
            mts[ix].mltcsh32 = (PatternState*)adrs;
        }

        mts[ix].mltbuf = texcash_melt_buffer;
        memreq = ((mts_base[ix].mode & 4) != 0) + 1;
        memreq *= (mts[ix].mltnum << 0x10);
        mts_ok[ix].key1 = Pull_ramcnt_key(memreq, mts_base[ix].type, 0, 0);
        mts[ix].attribute = mts_base[ix].attribute;
        mlt_obj_trans_init(&mts[ix], mts_base[ix].mode, Get_ramcnt_pointer(mts_ok[ix].key1));

        if (mts[ix].ext) {
            init_texcash_2nd(ix);
        }

        mts[ix].id = ix;
        mts[ix].mode = mts_base[ix].mode & 0xFF;
        mts_ok[ix].be = 1;
        mts_ok[ix].mincg = 0;
        mts_ok[ix].min16 = 0x7FFF;
        mts_ok[ix].min32 = 0x7FFF;
    }
}

void Clear_texcash_work() {
    s16 i;

    for (i = 1; i < 24; i++) {
        clear_texcash_work(i);
    }
}

void clear_texcash_work(s16 ix) {
    s16 i;

    if (((mts_ok[ix].be) != 0) && ((mts_base[ix].mode & 0x20) == 0)) {
        for (i = 0; i < mts[ix].mltnum16; i++) {
            mts[ix].mltcsh16[i].time = 0;
            mts[ix].mltcsh16[i].cs.code = -1;
        }

        for (i = 0; i < mts[ix].mltnum32; i++) {
            mts[ix].mltcsh32[i].time = 0;
            mts[ix].mltcsh32[i].cs.code = -1;
        }

        if (mts[ix].ext) {
            SDL_zerop(mts[ix].cpat);
            SDL_zerop(mts[ix].tpf);
            SDL_zerop(mts[ix].tpu);
            init_texcash_2nd(ix);
        }

        mts_ok[ix].mincg = 0;
        mts_ok[ix].min16 = 0x7FFF;
        mts_ok[ix].min32 = 0x7FFF;
    }
}

void purge_texcash_work(s16 ix) {
    if (mts_ok[ix].be == 0) {
        return;
    }

    if ((Test_ramcnt_key(mts_ok[ix].key0) != 0) && (Test_ramcnt_key(mts_ok[ix].key1) != 0)) {
        Push_ramcnt_key_original(mts_ok[ix].key0);
        Push_ramcnt_key_original(mts_ok[ix].key1);
    } else {
        fatal_error("purge_texcash_work: TEXCASH KEY ERROR");
    }

    ppgReleaseTextureHandle(&mts[ix].tex, -1);
    mts_ok[ix].be = 0;
    mts_ok[ix].key0 = 0;
    mts_ok[ix].key1 = 0;
}

const MTSBase mts_base[24] = {
    { .p16 = 0, .p32 = 0, .gix = 0, .life16 = 0, .life32 = 0, .type = 0, .mode = 0, .attribute = 0 },
    { .p16 = 1, .p32 = 1, .gix = 20, .life16 = 0, .life32 = 0, .type = 8, .mode = 4114, .attribute = 1 },
    { .p16 = 2, .p32 = 4, .gix = 30, .life16 = 8, .life32 = 8, .type = 8, .mode = 4113, .attribute = 1 },
    { .p16 = 3, .p32 = 6, .gix = 40, .life16 = 20, .life32 = 20, .type = 9, .mode = 8209, .attribute = 1 },
    { .p16 = 3, .p32 = 6, .gix = 50, .life16 = 20, .life32 = 20, .type = 9, .mode = 8209, .attribute = 1 },
    { .p16 = 1, .p32 = 4, .gix = 60, .life16 = 2, .life32 = 2, .type = 9, .mode = 8210, .attribute = 1 },
    { .p16 = 1, .p32 = 5, .gix = 70, .life16 = 0, .life32 = 0, .type = 8, .mode = 4113, .attribute = 1 },
    /* mts[7] est celui des objets de decor, et ces deux valeurs-la NE SERVENT PAS :
       `make_texcash_work` lit `mts_OB_page[bg_w.stage]` quand `ix == 7`. C'est plus bas
       qu'il faut regarder. */
    { .p16 = 1, .p32 = 1, .gix = 80, .life16 = 12, .life32 = 12, .type = 9, .mode = 8210, .attribute = 1 },
    { .p16 = 2, .p32 = 8, .gix = 1200, .life16 = 16, .life32 = 16, .type = 9, .mode = 4114, .attribute = 1 },
    { .p16 = 4, .p32 = 34, .gix = 500, .life16 = 20, .life32 = 20, .type = 9, .mode = 4129, .attribute = 1 },
    { .p16 = 4, .p32 = 8, .gix = 80, .life16 = 4, .life32 = 4, .type = 9, .mode = 4113, .attribute = 1 },
    { .p16 = 1, .p32 = 2, .gix = 1000, .life16 = 0, .life32 = 0, .type = 8, .mode = 4113, .attribute = 1 },
    { .p16 = 1, .p32 = 0, .gix = 1020, .life16 = 10, .life32 = 10, .type = 9, .mode = 4114, .attribute = 1 },
    { .p16 = 1, .p32 = 6, .gix = 1030, .life16 = 2, .life32 = 2, .type = 8, .mode = 8210, .attribute = 1 },
    { .p16 = 2, .p32 = 6, .gix = 1100, .life16 = 4, .life32 = 4, .type = 8, .mode = 8210, .attribute = 1 },
    { .p16 = 1, .p32 = 2, .gix = 1120, .life16 = 2, .life32 = 2, .type = 8, .mode = 4113, .attribute = 1 },
    { .p16 = 1, .p32 = 2, .gix = 960, .life16 = 2, .life32 = 2, .type = 8, .mode = 4113, .attribute = 1 },
    { .p16 = 1, .p32 = 1, .gix = 1140, .life16 = 2, .life32 = 2, .type = 8, .mode = 4114, .attribute = 1 },
    { .p16 = 1, .p32 = 1, .gix = 1100, .life16 = 0, .life32 = 0, .type = 8, .mode = 4116, .attribute = 1 },
    { .p16 = 1, .p32 = 1, .gix = 1100, .life16 = 0, .life32 = 0, .type = 8, .mode = 4116, .attribute = 1 },
    { .p16 = 1, .p32 = 1, .gix = 1100, .life16 = 0, .life32 = 0, .type = 8, .mode = 4116, .attribute = 1 },
    { .p16 = 1, .p32 = 1, .gix = 1100, .life16 = 0, .life32 = 0, .type = 8, .mode = 4116, .attribute = 1 },
    { .p16 = 1, .p32 = 1, .gix = 1100, .life16 = 0, .life32 = 0, .type = 8, .mode = 4116, .attribute = 1 },
    { .p16 = 1, .p32 = 1, .gix = 1100, .life16 = 0, .life32 = 0, .type = 8, .mode = 4116, .attribute = 1 }
};

/* Combien de pages de morceaux le cache d'objets de decor recoit, PAR ETAGE.
 *
 * C'est cette table que `make_texcash_work` lit pour `mts[7]`, pas `mts_base[7]`. Une
 * page vaut 256 morceaux de 16x16 (`mltnum16 = page16 << 8`) et 64 de 32x32.
 *
 * Nos quinze etages heritaient d'une copie de l'etage 5 -- une seule page. Ca tenait
 * tant qu'ils n'avaient qu'UN objet anime ; depuis qu'ils portent ce que le binaire de
 * 2nd Impact leur donne -- quatre pour Gill, NEUF pour Oro -- 256 morceaux ne suffisent
 * plus, et `get_mltbuf16_ext_2` part en `while (1) {}` :
 *
 *     fatal.log : « CGキャッシュが一杯になりました。×１６　ＥＸＴ２ »
 *
 * La demande se calcule : somme des cases de chaque grille, multipliee par le nombre
 * d'images que `life16` (12 trames) laisse vivantes a la fois, soit trois ou quatre.
 * Gill demande 65 cases, Oro 82. Le total de pages reste dans ce que le jeu s'accorde
 * lui-meme ailleurs -- l'etage 19 en prend cinq. */
const s16 mts_OB_page[58][2] = { { 1, 1 }, { 1, 3 }, { 1, 2 }, { 1, 1 }, { 1, 2 }, { 1, 1 }, { 1, 2 }, { 1, 2 },
                                 { 1, 2 }, { 1, 1 }, { 1, 1 }, { 1, 2 }, { 1, 1 }, { 1, 1 }, { 1, 1 }, { 1, 2 },
                                 { 1, 2 }, { 1, 4 }, { 1, 2 }, { 1, 4 }, { 1, 1 }, { 1, 2 },
    { 3, 1 } /* etage 22 gill  : 4 objets, 65 cases */,
    { 1, 1 } /* etage 23 alex  : 1 objet, 27 cases au pire */,
    { 2, 1 } /* etage 24 ryu   : 9 objets, 104 cases par trame -- deux de plus depuis que
                le grand sprite est servi en morceaux */,
    { 3, 1 } /* etage 25 yun   : 8 objets, 130 cases par trame. Il en avait 3 et UNE page :
                son sprite de 9x11 = 99 cases etait ECARTE faute de tenir dans les 32 cases
                de la cle de cache, il est maintenant servi en CINQ morceaux voisins */,
    { 1, 1 } /* etage 26 dudley : 1 objet, 6 cases -- le feu de circulation */,
    { 4, 1 } /* etage 27 necro : 34 objets depuis le 16/09 -- son conducteur, sa rambarde,
                les trois pieces de la machine. 398 morceaux vivants au pire : 77 % de deux
                pages, sans marge (Hugo figeait a 108 %). Quatre pages : 38 %. */,
    { 4, 1 } /* etage 28 hugo  : 16 objets aujourd'hui, plus 5. Au pire 556 morceaux
                vivants a la fois, pour 512 avec deux pages : 108 %, et le jeu figeait
                sur « ×１６　ＥＸＴ２ » (15/09). Quatre pages : 54 %, comme Ibuki, Oro
                et Akuma. Mesure : dc-decors, demande par etage. */,
    { 4, 1 } /* etage 29 ibuki : 9 objets, 272 cases par trame -- une cascade en six
                images de 272x245. Les DEUX cascades (18 objets, 544 cases, 3456 morceaux
                distincts) figeaient le jeu sur « CG展開エラー 16x16 » : le chemin de
                recherche ne retrouvait plus ce que le televersement n'avait pas pose. */,
    { 4, 1 } /* etage 30 elena : 8 objets, 160 cases par trame. Il n'en avait AUCUN : son
                unique sprite fait 8x20 = 160 cases, cinq fois la limite de la cle, et il
                etait ecarte en entier. Servi en huit morceaux voisins.
                QUATRE PAGES DEPUIS LE 16/09/2026 : la cascade animee (entree 0) ajoute
                sept morceaux de 174 cases par image ; au pire moment quatre images vivent,
                soit ~700 morceaux plus les 160 du sprite -- plus que les 768 de trois
                pages, moins que les 1024 de quatre. */,
    { 4, 1 } /* etage 31 oro   : 9 objets, 82 cases */,
    { 4, 1 } /* etage 32 yang  : 34 objets depuis le 17/09 -- ses cinq elements, le
                monsieur en vert (19 images de 30 cases) et les deux poissons. 574 morceaux
                vivants au pire : 112 % de deux pages, le jeu aurait fige. Quatre : 56 %. */,
    { 1, 1 } /* etage 33 */,
    { 2, 1 } /* etage 34 sean  : 9 objets depuis le 16/09 -- les singes, les deux porteurs
                et les cinq elements. 201 morceaux au pire : 78 % d'une page. Deux : 39 %. */,
    { 1, 1 } /* etage 35 */,
    { 4, 1 } /* etage 36 akuma : 9 objets, 215 cases par trame -- les deux cascades et
                l'entree de la grotte. A quatre trames par image et douze de duree de vie,
                trois images restent au chaud : 645 cases au pire, il en faut 1024. */,
    /* Les dix-neuf etages de New Generation -- genere, voir etagesng_plans.inc */
    ETAGESNG_OB_PAGE,
    ETAGES2IBIS_OB_PAGE
};
