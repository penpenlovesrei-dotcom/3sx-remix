/**
 * @file art_remix.c
 * Full-resolution stand-ins for the character select portraits.
 *
 * The sister of `tex_remix`, for the assets that one cannot reach. A texture page is loaded whole
 * and can be swapped on its way to the pool; a portrait never is. Effect 38 draws it through
 * multitexture slot 13, whose pages are created empty and filled 16x16 chip by chip out of sprite
 * data, refreshed by a raw copy every few frames. There is no page to substitute, and anything
 * written into one would be overwritten on the next refresh.
 *
 * So a portrait replacement is not a substitution at all: it is a picture drawn over the box the
 * chips would have covered, which `mlt_obj_bounds` computes by replaying their placement. The work
 * keeps its own behaviour -- sliding in, shifting, fading, sorting -- and only the filling changes.
 *
 * Files are named after the select screen's face number rather than a content fingerprint. A
 * fingerprint would have nothing to bite on here: the picture being replaced is never in memory in
 * one piece.
 */

#include "port/video/art_remix.h"
#include "port/resources.h"
#include "sf33rd/AcrSDK/ps2/flps2vram.h"

#include <SDL3/SDL.h>

#define ART_DIR "art_remix"
#define TEX_MAGIC 0x58545333u // '3STX', little end first
#define TEX_VERSION 1
#define TEX_HEADER_SIZE 16

/// Two portraits are on screen at once and the cursor walks between them, so a little more than two
/// keeps the neighbours warm without holding twenty megabytes of faces nobody is looking at.
#define LOADED_MAX 4

typedef struct {
    s32 face;
    u32 handle;
    u32 age;
    s32 width;
    s32 height;
} Portrait;

static Portrait loaded[LOADED_MAX];
static u32 clock_tick = 0;

static void _log(SDL_LogPriority priority, SDL_PRINTF_FORMAT_STRING const char* fmt, ...) SDL_PRINTF_VARARG_FUNC(2);

static void _log(SDL_LogPriority priority, const char* fmt, ...) {
    char message[512];
    va_list args;

    va_start(args, fmt);
    SDL_vsnprintf(message, sizeof(message), fmt, args);
    va_end(args);

    SDL_LogMessage(SDL_LOG_CATEGORY_APPLICATION, priority, "[portrait] %s", message);
}

static char* art_path(const char* leaf) {
    char* relative;
    SDL_asprintf(&relative, "%s/%s", ART_DIR, leaf);

    if (relative == NULL) {
        return NULL;
    }

    char* path = Resources_GetPath(relative);
    SDL_free(relative);
    return path;
}

/// The file for a face, or the shared `any.tex` when that face has none of its own.
static char* path_for(s32 face) {
    char leaf[32];
    SDL_snprintf(leaf, sizeof(leaf), "face-%02d.tex", face);
    char* path = art_path(leaf);

    if (path != NULL && SDL_GetPathInfo(path, NULL)) {
        return path;
    }

    SDL_free(path);
    path = art_path("any.tex");

    if (path != NULL && SDL_GetPathInfo(path, NULL)) {
        return path;
    }

    SDL_free(path);
    return NULL;
}

/// @return the handle, or 0 if the file is missing or malformed. Fills @p out_w and @p out_h on
/// success.
static u32 create_handle(s32 face, s32* out_w, s32* out_h) {
    char* path = path_for(face);

    if (path == NULL) {
        return 0;
    }

    size_t size = 0;
    void* file = SDL_LoadFile(path, &size);

    if (file == NULL || size < TEX_HEADER_SIZE) {
        _log(SDL_LOG_PRIORITY_WARN, "%s could not be read", path);
        SDL_free(file);
        SDL_free(path);
        return 0;
    }

    const u32* const header = file;
    const u32 width = header[2];
    const u32 height = header[3];
    const size_t expected = (size_t)width * height * 4;
    u32 handle = 0;

    if (header[0] != TEX_MAGIC || header[1] != TEX_VERSION) {
        _log(SDL_LOG_PRIORITY_WARN, "%s is not a version %d .tex file", path, TEX_VERSION);
    } else if (size - TEX_HEADER_SIZE < expected) {
        _log(SDL_LOG_PRIORITY_WARN, "%s claims %ux%u but holds %zu bytes of pixels", path, width, height,
             size - TEX_HEADER_SIZE);
    } else {
        // A `.tex` holds plain RGBA, which is what an image file gives and what the tools write.
        // What comes out of the pool is red and blue traded -- a face turns lavender and a hand
        // turns blue, which is the one mistake a colour cannot hide. So the swap is done here,
        // once per load, rather than asking every pack to be authored the wrong way round.
        u8* const pixels = SDL_malloc(expected);

        if (pixels == NULL) {
            SDL_free(file);
            SDL_free(path);
            return 0;
        }

        const u8* const source = (const u8*)file + TEX_HEADER_SIZE;

        for (size_t i = 0; i < expected; i += 4) {
            pixels[i + 0] = source[i + 2];
            pixels[i + 1] = source[i + 1];
            pixels[i + 2] = source[i + 0];
            pixels[i + 3] = source[i + 3];
        }

        plContext bits = { 0 };
        bits.desc = 0;
        bits.width = width;
        bits.height = height;
        bits.bitdepth = 4;
        bits.pitch = width * 4;
        bits.ptr = pixels;
        bits.pixelformat = (PixelFormat) {
            .rl = 8, .rs = 0,  .rm = 0xFF,
            .gl = 8, .gs = 8,  .gm = 0xFF,
            .bl = 8, .bs = 16, .bm = 0xFF,
            .al = 8, .as = 24, .am = 0xFF,
        };

        // The pool takes its own copy, as PPGFile.c shows by freeing the page right after.
        handle = flCreateTextureHandle(&bits, 1);
        SDL_free(pixels);

        if (handle == 0) {
            _log(SDL_LOG_PRIORITY_WARN, "the texture pool refused %ux%u for face %d", width, height, face);
        } else {
            *out_w = (s32)width;
            *out_h = (s32)height;
            _log(SDL_LOG_PRIORITY_INFO, "face %d <- %s, %ux%u", face, path, width, height);
        }
    }

    SDL_free(file);
    SDL_free(path);
    return handle;
}

u32 ArtRemix_TexCode(s32 face, s32* width, s32* height) {
    s32 oldest = 0;

    clock_tick++;

    for (s32 i = 0; i < LOADED_MAX; i++) {
        if (loaded[i].handle != 0 && loaded[i].face == face) {
            loaded[i].age = clock_tick;
            *width = loaded[i].width;
            *height = loaded[i].height;
            return loaded[i].handle;
        }

        if (loaded[i].handle == 0 || loaded[i].age < loaded[oldest].age) {
            oldest = i;
        }
    }

    s32 w = 0;
    s32 h = 0;
    const u32 handle = create_handle(face, &w, &h);

    if (handle == 0) {
        return 0;
    }

    if (loaded[oldest].handle != 0) {
        flReleaseTextureHandle(loaded[oldest].handle);
    }

    loaded[oldest].face = face;
    loaded[oldest].handle = handle;
    loaded[oldest].age = clock_tick;
    loaded[oldest].width = w;
    loaded[oldest].height = h;
    *width = w;
    *height = h;
    return handle;
}

static SDL_EnumerationResult keep_largest(void* userdata, const char* dirname, const char* fname) {
    if (!SDL_strstr(fname, ".tex")) {
        return SDL_ENUM_CONTINUE;
    }

    char* path = NULL;
    SDL_asprintf(&path, "%s%s", dirname, fname);

    SDL_PathInfo info;

    if (path != NULL && SDL_GetPathInfo(path, &info) && info.size > *(s64*)userdata) {
        *(s64*)userdata = info.size;
    }

    SDL_free(path);
    return SDL_ENUM_CONTINUE;
}

s64 ArtRemix_ReservedBytes(void) {
    char* dir = Resources_GetPath(ART_DIR);

    if (dir == NULL) {
        return 0;
    }

    s64 largest = 0;
    SDL_EnumerateDirectory(dir, keep_largest, &largest);
    SDL_free(dir);

    if (largest == 0) {
        return 0;
    }

    // What can be resident, not what is installed: portraits come and go with the cursor, so only
    // the cache is ever held, and twenty faces at four megabytes would reserve a heap nobody needs.
    // The cache is also keyed by face, so one file standing in for several faces is held once per
    // face -- which is why this counts slots and not files.
    s64 total = largest * LOADED_MAX;
    total += total / 8;
    _log(SDL_LOG_PRIORITY_INFO, "reserving %" SDL_PRIs64 " KB of texture pool for portraits", total / 1024);
    return total;
}

void ArtRemix_Destroy(void) {
    for (s32 i = 0; i < LOADED_MAX; i++) {
        if (loaded[i].handle != 0) {
            flReleaseTextureHandle(loaded[i].handle);
        }

        loaded[i].handle = 0;
        loaded[i].face = 0;
        loaded[i].age = 0;
    }

    clock_tick = 0;
}
