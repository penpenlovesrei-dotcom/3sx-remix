#ifndef FOUNDAPS2_H
#define FOUNDAPS2_H

#include "port/utils.h"
#include "sf33rd/AcrSDK/common/plcommon.h"
#include "structs.h"
#include "types.h"

#define VRAM_CONTROL_SIZE 1344
#define VRAM_BLOCK_HEADER_SIZE 3
#define FL_PALETTE_MAX 1088
/* 512 DEPUIS LE 18/09/2026 (256 sur la console). Les plans animes de New Generation
   chargent des pages en plus -- 224 pour la pluie de Londres, 96 pour l'horizon de Gill --
   et l'etage seul depassait alors les 256 poignees. Les tableaux sont statiques et la
   poignee tient sur seize bits : il n'y a que la memoire de ces tableaux a payer. */
#define FL_TEXTURE_MAX 512

extern s32 flVramStaticNum;
extern FL_FMS flFMS;
extern u32 flSystemRenderOperation;
extern s32 flHeight;
extern s32 flWidth;
extern FLTexture flPalette[FL_PALETTE_MAX];
extern FLTexture flTexture[FL_TEXTURE_MAX];
extern FLPS2State flPs2State;

s32 flInitialize();
s32 flFlip(u32 flag);
__dead2 s32 flLogOut(const char* format, ...);

#endif
