#ifndef SOUND_ADX_H
#define SOUND_ADX_H

#include <stdbool.h>
#include <stddef.h>

typedef enum ADXState {
    ADX_STATE_STOP,
    ADX_STATE_PLAYING,
    ADX_STATE_PLAYEND,
} ADXState;

void ADX_ProcessTracks();

void ADX_Init();
void ADX_Exit();
void ADX_Stop();
int ADX_IsPaused();
void ADX_Pause(int pause);
void ADX_StartSeamless();
void ADX_StartMem(void* buf, size_t size);
int ADX_GetNumFiles();
void ADX_EntryAfs(int file_id);
void ADX_StartAfs(int file_id);
/// @brief Play a looping .adx read from disk instead of from the AFS archive.
/// @param path Absolute path to the file. Playback is skipped if it can't be read.
void ADX_StartFile(const char* path);
/// @brief Path passed to the last ADX_StartFile, as long as it is still the loaded track.
/// @return `NULL` once playback stopped or moved to an AFS track.
const char* ADX_GetCurrentFilePath();
void ADX_ResetEntry();
void ADX_SetOutVol(int volume);
ADXState ADX_GetState();

#endif
