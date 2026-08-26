/**
 * @file pal_remix.c
 * Loads optional user-supplied colour palettes that override the game's own.
 *
 * A set lives in `<resources>/pal_remix/<set>/` and holds one file per character or per stage:
 *
 *     pal_remix/new-generation/char-02.pal     Ryu, engine numbering
 *     pal_remix/arranged/stage-11.pal          Ken's stage
 *
 * A file is a verbatim stand-in for the entry the game would have read out of `SF33RD.AFS`, so
 * nothing has to know a new format: `init_trans_color_ram` reads it with the layout it already
 * uses. Colours are ARGB1555, sixty-four to a palette, exactly as they sit in the archive.
 *
 * The sets named on the two Custom screens map to folders, except the game's own data — `3rd
 * Strike` for characters and `Original` for backgrounds — which needs no files and is what a
 * missing override falls back to. A set whose folder holds nothing is not offered at all.
 */

#include "port/video/pal_remix.h"
#include "port/resources.h"

#include <SDL3/SDL.h>

#define SETS_DIR "pal_remix"
#define CHARACTER_TOTAL 20
#define STAGE_TOTAL 20

/// Folder behind each position of the two value rows. The game's own data has none.
static const char* const character_dirs[] = {
    [PAL_SET_NEW_GENERATION] = "new-generation",
    [PAL_SET_2ND_IMPACT] = "2nd-impact",
    [PAL_SET_3RD_STRIKE] = NULL,
    [PAL_SET_CHARACTER_RANDOM] = NULL,
    [PAL_SET_COLOR_EDIT] = "color-edit",
};

static const char* const background_dirs[] = {
    [PAL_SET_ORIGINAL] = NULL,
    [PAL_SET_RETHIRD] = "rethird",
    [PAL_SET_PER_ROUND] = "per-round",
    [PAL_SET_BACKGROUND_RANDOM] = NULL,
};

#define CHARACTER_SET_COUNT ((s16)SDL_arraysize(character_dirs))
#define BACKGROUND_SET_COUNT ((s16)SDL_arraysize(background_dirs))

typedef struct {
    void* data;   ///< Payload, owned here, loaded the first time it is asked for
    s32 size;
    bool tried;   ///< Whether the file has been looked for, so a miss is not retried every fight
} PalFile;

typedef struct {
    PalFile characters[CHARACTER_TOTAL];
    PalFile stages[STAGE_TOTAL];
    bool present;   ///< Whether the folder holds anything at all
    bool scanned;
} PalSet;

static PalSet character_sets[CHARACTER_SET_COUNT];
static PalSet background_sets[BACKGROUND_SET_COUNT];

static void _log(SDL_LogPriority priority, SDL_PRINTF_FORMAT_STRING const char* fmt, ...) SDL_PRINTF_VARARG_FUNC(2);

static void _log(SDL_LogPriority priority, const char* fmt, ...) {
    char message[512];
    va_list args;

    va_start(args, fmt);
    SDL_vsnprintf(message, sizeof(message), fmt, args);
    va_end(args);

    SDL_LogMessage(SDL_LOG_CATEGORY_APPLICATION, priority, "[palette] %s", message);
}

/// Path of one file of a set, or NULL when the set has no folder of its own.
static char* set_file_path(const char* dir, const char* kind, s16 index) {
    if (dir == NULL) {
        return NULL;
    }

    char* relative;
    SDL_asprintf(&relative, "%s/%s/%s-%02d.pal", SETS_DIR, dir, kind, index);

    if (relative == NULL) {
        return NULL;
    }

    char* path = Resources_GetPath(relative);
    SDL_free(relative);
    return path;
}

/// Does the set hold at least one file? Answered once, then remembered.
static void scan_set(PalSet* set, const char* dir) {
    if (set->scanned) {
        return;
    }

    set->scanned = true;
    set->present = false;

    if (dir == NULL) {
        return;
    }

    for (s16 kind = 0; kind < 2; kind++) {
        const char* name = (kind == 0) ? "char" : "stage";
        const s16 total = (kind == 0) ? CHARACTER_TOTAL : STAGE_TOTAL;

        for (s16 i = 0; i < total; i++) {
            char* path = set_file_path(dir, name, i);

            if (path == NULL) {
                continue;
            }

            const bool exists = SDL_GetPathInfo(path, NULL);
            SDL_free(path);

            if (exists) {
                set->present = true;
                _log(SDL_LOG_PRIORITY_INFO, "set \"%s\" is installed", dir);
                return;
            }
        }
    }
}

/// The payload of one file, loaded on first use. A miss is remembered so it costs one try.
static const void* set_file(PalSet* set, const char* dir, const char* kind, s16 index, PalFile* slot, s32* size) {
    if (!slot->tried) {
        slot->tried = true;
        char* path = set_file_path(dir, kind, index);

        if (path != NULL) {
            size_t loaded = 0;
            slot->data = SDL_LoadFile(path, &loaded);
            slot->size = (s32)loaded;

            if (slot->data != NULL) {
                // A palette is sixty-four ARGB1555 colours; anything else would be read as a
                // ragged block and upload garbage over the last entries.
                if ((slot->size == 0) || ((slot->size % 128) != 0)) {
                    _log(SDL_LOG_PRIORITY_WARN, "%s: %d bytes is not a whole number of 64-colour palettes",
                         path, slot->size);
                    SDL_free(slot->data);
                    slot->data = NULL;
                    slot->size = 0;
                } else {
                    _log(SDL_LOG_PRIORITY_INFO, "%s: %d palette(s)", path, slot->size / 128);
                }
            }

            SDL_free(path);
        }
    }

    if ((slot->data != NULL) && (size != NULL)) {
        *size = slot->size;
    }

    (void)set;
    return slot->data;
}

const void* PalRemix_Character(s16 character, s16 set, s32* size) {
    if ((character < 0) || (character >= CHARACTER_TOTAL)) {
        return NULL;
    }

    if ((set < 0) || (set >= CHARACTER_SET_COUNT) || (character_dirs[set] == NULL)) {
        return NULL;
    }

    return set_file(&character_sets[set], character_dirs[set], "char", character,
                    &character_sets[set].characters[character], size);
}

bool PalRemix_SaveCharacter(s16 character, const void* data, s32 size) {
    if ((character < 0) || (character >= CHARACTER_TOTAL) || (data == NULL) || (size <= 0)) {
        return false;
    }

    char* path = set_file_path(character_dirs[PAL_SET_COLOR_EDIT], "char", character);

    if (path == NULL) {
        return false;
    }

    // The set's folder is made on the way rather than at startup: an installation that never
    // saves anything has no reason to carry an empty one, and the loader offers a set only when
    // it holds a file.
    {
        char* dir;
        SDL_asprintf(&dir, "%s/%s", SETS_DIR, character_dirs[PAL_SET_COLOR_EDIT]);

        if (dir != NULL) {
            char* full = Resources_GetPath(dir);

            if (full != NULL) {
                SDL_CreateDirectory(full);
                SDL_free(full);
            }

            SDL_free(dir);
        }
    }

    const bool written = SDL_SaveFile(path, data, (size_t)size);

    if (written) {
        _log(SDL_LOG_PRIORITY_INFO, "%s: wrote %d palette(s)", path, size / 128);
    } else {
        _log(SDL_LOG_PRIORITY_ERROR, "%s: %s", path, SDL_GetError());
    }

    SDL_free(path);

    // The slot may hold a miss remembered from before this file existed, and scan_set may have
    // decided the whole set was empty. Both answers are now wrong.
    if (written) {
        PalFile* slot = &character_sets[PAL_SET_COLOR_EDIT].characters[character];

        SDL_free(slot->data);
        slot->data = NULL;
        slot->size = 0;
        slot->tried = false;
        character_sets[PAL_SET_COLOR_EDIT].scanned = false;
    }

    return written;
}

const void* PalRemix_Stage(s16 stage, s16 set, s32* size) {
    if ((stage < 0) || (stage >= STAGE_TOTAL)) {
        return NULL;
    }

    if ((set < 0) || (set >= BACKGROUND_SET_COUNT) || (background_dirs[set] == NULL)) {
        return NULL;
    }

    return set_file(&background_sets[set], background_dirs[set], "stage", stage,
                    &background_sets[set].stages[stage], size);
}

/// Does a set hold this one file? Answered from the cached slot when it has already been loaded,
/// and from the filesystem otherwise, so a menu can ask about every row every frame.
static bool has_file(PalSet* set, const char* dir, const char* kind, s16 index, PalFile* slot) {
    if (slot->tried) {
        return slot->data != NULL;
    }

    char* path = set_file_path(dir, kind, index);

    if (path == NULL) {
        return false;
    }

    const bool exists = SDL_GetPathInfo(path, NULL);
    SDL_free(path);
    (void)set;
    return exists;
}

bool PalRemix_HasCharacter(s16 character, s16 set) {
    if ((character < 0) || (character >= CHARACTER_TOTAL) || (set < 0) || (set >= CHARACTER_SET_COUNT)) {
        return false;
    }

    if (character_dirs[set] == NULL) {
        return set == PAL_SET_3RD_STRIKE;   // the game's own data dresses everyone
    }

    return has_file(&character_sets[set], character_dirs[set], "char", character,
                    &character_sets[set].characters[character]);
}

bool PalRemix_HasStage(s16 stage, s16 set) {
    if ((stage < 0) || (stage >= STAGE_TOTAL) || (set < 0) || (set >= BACKGROUND_SET_COUNT)) {
        return false;
    }

    if (background_dirs[set] == NULL) {
        return set == PAL_SET_ORIGINAL;
    }

    return has_file(&background_sets[set], background_dirs[set], "stage", stage,
                    &background_sets[set].stages[stage]);
}

bool PalRemix_HasCharacterSet(s16 set) {
    if ((set < 0) || (set >= CHARACTER_SET_COUNT)) {
        return false;
    }

    if (character_dirs[set] == NULL) {
        return set == PAL_SET_3RD_STRIKE;   // the game's own data is always there
    }

    scan_set(&character_sets[set], character_dirs[set]);
    return character_sets[set].present;
}

bool PalRemix_HasBackgroundSet(s16 set) {
    if ((set < 0) || (set >= BACKGROUND_SET_COUNT)) {
        return false;
    }

    if (background_dirs[set] == NULL) {
        return set == PAL_SET_ORIGINAL;
    }

    scan_set(&background_sets[set], background_dirs[set]);
    return background_sets[set].present;
}

static void free_set(PalSet* set) {
    for (s16 i = 0; i < CHARACTER_TOTAL; i++) {
        SDL_free(set->characters[i].data);
    }

    for (s16 i = 0; i < STAGE_TOTAL; i++) {
        SDL_free(set->stages[i].data);
    }

    SDL_zerop(set);
}

void PalRemix_Destroy(void) {
    for (s16 i = 0; i < CHARACTER_SET_COUNT; i++) {
        free_set(&character_sets[i]);
    }

    for (s16 i = 0; i < BACKGROUND_SET_COUNT; i++) {
        free_set(&background_sets[i]);
    }
}
