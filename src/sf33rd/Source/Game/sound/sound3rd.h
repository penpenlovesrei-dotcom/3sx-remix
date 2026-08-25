#ifndef SOUND3RD_H
#define SOUND3RD_H

#include "structs.h"
#include "types.h"

extern s16 bgm_level;
extern s16 se_level;
extern s8* sdbd[3];
extern SoundEvent* cseTSBDataTable[];
extern s8* csePHDDataTable[];

void Init_sound_system();
/// @brief Settle which soundtrack plays the fight ahead, when the choice isn't one already.
/// @param base_code The stage theme's mix 1 code, which Custom keys on. 0 outside a fight.
void Resolve_bgm_type(u16 base_code);
/// Put the player's BGM Type choice into effect, drawing one if that choice is Random
void Apply_bgm_choice();
s32 sndCheckVTransStatus(s32 type);
void sndInitialLoad();
void checkAdxFileLoaded();
void Exit_sound_system();
void Init_bgm_work();
void sound_all_off();
void setSeVolume();
void setupSoundMode();
void BGM_Server();
void setupAlwaysSeamlessFlag(s16 flag);
s32 adx_now_playend();
s32 bgm_play_status();
s32 bgmSkipCheck(s32 code);
void SsAllNoteOff();
void SsRequest(u16 ReqNumber);
void SsRequest_CC(u16 num);
void Standby_BGM(u16 num);
void Go_BGM();
void SsBgmFadeOut(u16 time);
void SsBgmHalfVolume(s16 flag);
void SE_cursor_move();
void SE_selected();
void SE_dir_cursor_move();
void SE_dir_selected();
void SsBgmControl(s8 /* unused */, s8 VOLUME);
void SsRequestPan(u16 reqNum, s16 start, s16 /* unused */, s32 /* unused */, s32 /* unused */);
void SsBgmOff();
void SsBgmFadeIn(u16 ReqNumber, u16 FadeSpeed);
void spu_all_off();

#endif
