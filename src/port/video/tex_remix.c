/**
 * @file tex_remix.c
 * Loads optional user-supplied texture pages that stand in for the game's own.
 *
 * A replacement lives in `<resources>/tex_remix/<key>.tex`, where the key is a fingerprint of the
 * page it replaces. Identity is the awkward part of this: a page has no name anywhere in the game,
 * it is a nameless block inside a nameless archive entry, reached through a handle that means
 * nothing between two runs. So a page is recognised by its own contents -- the same trick emulator
 * texture packs use -- which costs one pass over the data at load time and asks nothing of the rest
 * of the code. Palettes are held elsewhere, so a sprite drawn in twenty colour schemes still
 * fingerprints as one page.
 *
 * The `.tex` container is deliberately blunt: `3STX`, a version, width, height, then rows of RGBA.
 * There is no image decoder in this build and a page has no business carrying compression the game
 * would have to undo at load time. `tools/make_tex.py` builds one from any image.
 *
 * Set `tex-remix-dump` to have every page written to `<resources>/tex_remix/dump/`, which is how you
 * find out what a screen is made of, and which keys to name your files after. The manifest also
 * notes the page number the game loaded each one under -- no use for finding a replacement, but it
 * is the number the drawing code works in, so it is what lets a dumped page be traced back to the
 * code that puts it on screen.
 *
 * What a replacement gives up: a page that arrives here with 4 or 8 bits per pixel is drawn through
 * a palette, and the game does animate some of those -- flashes, fades to white, the colour cycling
 * on a few HUD pieces. A replacement is plain colour and keeps none of that. Artwork and lettering
 * never move their palettes and lose nothing; think twice before replacing anything that flashes.
 */

#include "port/video/tex_remix.h"
#include "port/config/config.h"
#include "port/resources.h"

#include <SDL3/SDL.h>

#define REMIX_DIR "tex_remix"
#define TEX_MAGIC 0x58545333u // '3STX', little end first
#define TEX_VERSION 1
#define TEX_HEADER_SIZE 16
#define DUMPED_KEYS_MAX 512

/// Pages already recorded this run, so one reloaded on every screen is dumped once. Keyed on the
/// fingerprint *and* where it came from: the same pixels reached through two different page numbers
/// is exactly the kind of thing the manifest is there to show.
static struct {
    Uint64 key;
    s32 index;
    s32 first;
} dumped[DUMPED_KEYS_MAX];

static int dumped_count = 0;

/// The page last fingerprinted, waiting for the handle the caller is about to create for it.
static Uint64 pending_key = 0;

/// Handles are small numbers the pool hands out and takes back, so they mean nothing between runs
/// and can be reused within one. They are only ever read back inside the same frame that set them,
/// which is all the pairing needs.
#define HANDLES_MAX 4096

static Uint64 texture_of_handle[HANDLES_MAX];
static Uint64 palette_of_handle[HANDLES_MAX];

#define PAIRS_MAX 8192

typedef struct {
    Uint64 page;
    Uint64 palette;
    int u0;
    int v0;
    int u1;
    int v1;
} Patch;

static Patch pairs[PAIRS_MAX];
static int pairs_count = 0;

/// The page handed out by the last substitution. One is enough: the caller has copied it into the
/// texture pool before it asks for another.
static void* replacement = NULL;

static void _log(SDL_LogPriority priority, SDL_PRINTF_FORMAT_STRING const char* fmt, ...) SDL_PRINTF_VARARG_FUNC(2);

static void _log(SDL_LogPriority priority, const char* fmt, ...) {
    char message[512];
    va_list args;

    va_start(args, fmt);
    SDL_vsnprintf(message, sizeof(message), fmt, args);
    va_end(args);

    SDL_LogMessage(SDL_LOG_CATEGORY_APPLICATION, priority, "[texture] %s", message);
}

/// FNV-1a over the page, salted with its shape so two pages that differ only in size cannot collide.
static Uint64 fingerprint(const plContext* bits) {
    Uint64 hash = 0xCBF29CE484222325u;
    const Uint8* const bytes = bits->ptr;
    const Sint32 size = bits->pitch * bits->height;

    const Sint32 shape[] = { bits->width, bits->height, bits->bitdepth };

    for (int i = 0; i < SDL_arraysize(shape); i++) {
        for (int b = 0; b < 4; b++) {
            hash = (hash ^ ((shape[i] >> (b * 8)) & 0xFF)) * 0x100000001B3u;
        }
    }

    for (Sint32 i = 0; i < size; i++) {
        hash = (hash ^ bytes[i]) * 0x100000001B3u;
    }

    return hash;
}

static char* remix_path(const char* leaf) {
    char* relative;
    SDL_asprintf(&relative, "%s/%s", REMIX_DIR, leaf);

    if (relative == NULL) {
        return NULL;
    }

    char* path = Resources_GetPath(relative);
    SDL_free(relative);
    return path;
}

/// @brief Write a page out as a greyscale image, which is enough to recognise what it holds.
///
/// Indexed pages are dumped as their index values rather than their colours -- the palette that
/// would turn those into a picture is not here, and does not belong to the page anyway. Shapes,
/// lettering and artwork all read perfectly well that way, which is all this is for. 16- and 32-bit
/// pages are named in the manifest but not written: nothing has ever needed one yet.
static void dump_page(Uint64 key, const plContext* bits, const TexPageOrigin* from) {
    bool same_pixels = false;

    for (int i = 0; i < dumped_count; i++) {
        if (dumped[i].key != key) {
            continue;
        }

        same_pixels = true;

        if (dumped[i].index == from->index && dumped[i].first == from->first) {
            return;
        }
    }

    if (dumped_count < DUMPED_KEYS_MAX) {
        dumped[dumped_count].key = key;
        dumped[dumped_count].index = from->index;
        dumped[dumped_count].first = from->first;
        dumped_count++;
    }

    char* dir = remix_path("dump");

    if (dir == NULL) {
        return;
    }

    SDL_CreateDirectory(dir);

    char* manifest_path = NULL;
    SDL_asprintf(&manifest_path, "%s/manifest.txt", dir);

    if (manifest_path != NULL) {
        SDL_IOStream* manifest = SDL_IOFromFile(manifest_path, "a");

        if (manifest != NULL) {
            char line[128];
            const int length = SDL_snprintf(
                line, sizeof(line), "%016" SDL_PRIx64 "  %4dx%-4d  %d bpp  page %d  list %d  entry %d\n", key,
                bits->width, bits->height, (bits->bitdepth == 0) ? 4 : bits->bitdepth * 8, from->index, from->first,
                from->entry
            );
            SDL_WriteIO(manifest, line, length);
            SDL_CloseIO(manifest);
        }

        SDL_free(manifest_path);
    }

    // Named in the manifest under its new page number, but the picture is already on disk.
    if (same_pixels || bits->bitdepth > 1) {
        SDL_free(dir);
        return;
    }

    char* path = NULL;
    SDL_asprintf(&path, "%s/%016" SDL_PRIx64 ".pgm", dir, key);
    SDL_IOStream* io = (path != NULL) ? SDL_IOFromFile(path, "wb") : NULL;

    if (io != NULL) {
        char header[64];
        const int length = SDL_snprintf(header, sizeof(header), "P5\n%d %d\n255\n", bits->width, bits->height);
        SDL_WriteIO(io, header, length);

        const Uint8* const source = bits->ptr;
        Uint8* row = SDL_malloc(bits->width);

        for (Sint32 y = 0; y < bits->height && row != NULL; y++) {
            for (Sint32 x = 0; x < bits->width; x++) {
                if (bits->bitdepth == 0) {
                    const Uint8 packed = source[(y * bits->pitch) + (x / 2)];
                    // Four bits of index spread over the whole range, or every page reads as black
                    row[x] = (((x & 1) == 0) ? (packed & 0xF) : (packed >> 4)) * 17;
                } else {
                    row[x] = source[(y * bits->pitch) + x];
                }
            }

            SDL_WriteIO(io, row, bits->width);
        }

        SDL_free(row);
        SDL_CloseIO(io);
    }

    SDL_free(path);
    SDL_free(dir);
}

static Uint64 fingerprint_bytes(const Uint8* bytes, size_t size) {
    Uint64 hash = 0xCBF29CE484222325u;

    for (size_t i = 0; i < size; i++) {
        hash = (hash ^ bytes[i]) * 0x100000001B3u;
    }

    return hash;
}

void TexRemix_NoteTextureHandle(u32 handle) {
    if (!Config_GetBool(CFG_TEX_REMIX_DUMP) || handle == 0 || handle >= HANDLES_MAX) {
        return;
    }

    texture_of_handle[handle] = pending_key;
}

void TexRemix_NotePalette(u32 handle, const void* colours, s32 count, s32 bytes) {
    if (!Config_GetBool(CFG_TEX_REMIX_DUMP) || handle == 0 || handle >= HANDLES_MAX) {
        return;
    }

    if (colours == NULL || count <= 0 || bytes <= 0) {
        return;
    }

    const size_t size = (size_t)count * (size_t)bytes;
    const Uint64 key = fingerprint_bytes(colours, size);
    palette_of_handle[handle] = key;

    char* dir = remix_path("dump/palettes");

    if (dir == NULL) {
        return;
    }

    SDL_CreateDirectory(dir);

    char* path = NULL;
    SDL_asprintf(&path, "%s/%016" SDL_PRIx64 "_%d_%d.pal", dir, key, count, bytes);

    // Content addressed, so a palette already written is the same palette; skip it in silence.
    if (path != NULL && !SDL_GetPathInfo(path, NULL)) {
        SDL_IOStream* io = SDL_IOFromFile(path, "wb");

        if (io != NULL) {
            SDL_WriteIO(io, colours, size);
            SDL_CloseIO(io);
        }
    }

    SDL_free(path);
    SDL_free(dir);
}

/// The pair the next quad will be drawn with, set when the renderer is told which texture to use.
static Uint64 current_page = 0;
static Uint64 current_palette = 0;

void TexRemix_NotePair(u32 tex_code) {
    if (!Config_GetBool(CFG_TEX_REMIX_DUMP)) {
        return;
    }

    const u32 tex_handle = tex_code & 0xFFFF;
    const u32 pal_handle = (tex_code >> 16) & 0xFFFF;

    current_page = (tex_handle < HANDLES_MAX) ? texture_of_handle[tex_handle] : 0;
    current_palette = (pal_handle < HANDLES_MAX) ? palette_of_handle[pal_handle] : 0;
}

void TexRemix_NoteQuad(float u0, float v0, float u1, float v1) {
    if (!Config_GetBool(CFG_TEX_REMIX_DUMP) || current_page == 0 || current_palette == 0) {
        return;
    }

    // Rounded to the page's own grid before comparing, or the same glyph drawn at two sub-pixel
    // offsets counts twice and the list fills with duplicates of one letter.
    const int a = (int)(SDL_min(u0, u1) * 1024.0f + 0.5f);
    const int b = (int)(SDL_min(v0, v1) * 1024.0f + 0.5f);
    const int c = (int)(SDL_max(u0, u1) * 1024.0f + 0.5f);
    const int d = (int)(SDL_max(v0, v1) * 1024.0f + 0.5f);

    if (c <= a || d <= b) {
        return;
    }

    for (int i = 0; i < pairs_count; i++) {
        if (pairs[i].page == current_page && pairs[i].palette == current_palette && pairs[i].u0 == a &&
            pairs[i].v0 == b && pairs[i].u1 == c && pairs[i].v1 == d) {
            return;
        }
    }

    if (pairs_count >= PAIRS_MAX) {
        return;
    }

    pairs[pairs_count] = (Patch) { current_page, current_palette, a, b, c, d };
    pairs_count++;

    char* dir = remix_path("dump");

    if (dir == NULL) {
        return;
    }

    SDL_CreateDirectory(dir);

    char* path = NULL;
    SDL_asprintf(&path, "%s/quads.txt", dir);

    if (path != NULL) {
        SDL_IOStream* io = SDL_IOFromFile(path, "a");

        if (io != NULL) {
            char line[128];
            const int length = SDL_snprintf(line, sizeof(line), "%016" SDL_PRIx64 " %016" SDL_PRIx64 " %d %d %d %d\n",
                                            current_page, current_palette, a, b, c, d);
            SDL_WriteIO(io, line, length);
            SDL_CloseIO(io);
        }

        SDL_free(path);
    }

    SDL_free(dir);
}

static SDL_EnumerationResult add_file_size(void* userdata, const char* dirname, const char* fname) {
    if (!SDL_strstr(fname, ".tex")) {
        return SDL_ENUM_CONTINUE;
    }

    char* path = NULL;
    SDL_asprintf(&path, "%s%s", dirname, fname);

    SDL_PathInfo info;

    if (path != NULL && SDL_GetPathInfo(path, &info)) {
        *(s64*)userdata += info.size;
    }

    SDL_free(path);
    return SDL_ENUM_CONTINUE;
}

s64 TexRemix_ReservedBytes(void) {
    char* dir = Resources_GetPath(REMIX_DIR);

    if (dir == NULL) {
        return 0;
    }

    s64 total = 0;
    SDL_EnumerateDirectory(dir, add_file_size, &total);
    SDL_free(dir);

    if (total == 0) {
        return 0;
    }

    // Room for every replacement at once, which is more than any one screen will hold, plus a
    // margin for the pool's own bookkeeping and alignment.
    total += total / 8;
    _log(SDL_LOG_PRIORITY_INFO, "reserving %" SDL_PRIs64 " KB of texture pool for replacements", total / 1024);
    return total;
}

bool TexRemix_Substitute(plContext* bits, const TexPageOrigin* from) {
    if (bits == NULL || bits->ptr == NULL) {
        return false;
    }

    const Uint64 key = fingerprint(bits);
    pending_key = key;

    if (Config_GetBool(CFG_TEX_REMIX_DUMP)) {
        dump_page(key, bits, from);
    }

    char* leaf = NULL;
    SDL_asprintf(&leaf, "%016" SDL_PRIx64 ".tex", key);
    char* path = (leaf != NULL) ? remix_path(leaf) : NULL;
    SDL_free(leaf);

    if (path == NULL) {
        return false;
    }

    if (!SDL_GetPathInfo(path, NULL)) {
        SDL_free(path);
        return false;
    }

    size_t loaded = 0;
    void* file = SDL_LoadFile(path, &loaded);

    if (file == NULL || loaded < TEX_HEADER_SIZE) {
        _log(SDL_LOG_PRIORITY_WARN, "%s could not be read", path);
        SDL_free(file);
        SDL_free(path);
        return false;
    }

    const Uint32* const header = file;
    const Uint32 width = header[2];
    const Uint32 height = header[3];
    const size_t expected = (size_t)width * height * 4;

    if (header[0] != TEX_MAGIC || header[1] != TEX_VERSION) {
        _log(SDL_LOG_PRIORITY_WARN, "%s is not a version %d .tex file", path, TEX_VERSION);
    } else if (loaded - TEX_HEADER_SIZE < expected) {
        _log(
            SDL_LOG_PRIORITY_WARN, "%s claims %ux%u but holds %zu bytes of pixels", path, width, height,
            loaded - TEX_HEADER_SIZE
        );
    } else if ((width % bits->width) != 0 || (height % bits->height) != 0) {
        // Any size would land in the right places, the corners being fractions of the page. A whole
        // multiple is still worth insisting on: it is the only way each original pixel keeps the
        // same number of new ones, which is what stops lettering from wobbling along a row.
        _log(
            SDL_LOG_PRIORITY_WARN, "%s is %ux%u, not a whole multiple of the %dx%d page it replaces", path, width,
            height, bits->width, bits->height
        );
    } else {
        SDL_free(replacement);
        replacement = SDL_malloc(expected);

        if (replacement != NULL) {
            SDL_memcpy(replacement, (const Uint8*)file + TEX_HEADER_SIZE, expected);

            bits->desc = 0;
            bits->width = width;
            bits->height = height;
            bits->bitdepth = 4;
            bits->pitch = width * 4;
            bits->ptr = replacement;
            bits->pixelformat = (PixelFormat) {
                .rl = 8, .rs = 0,  .rm = 0xFF,
                .gl = 8, .gs = 8,  .gm = 0xFF,
                .bl = 8, .bs = 16, .bm = 0xFF,
                .al = 8, .as = 24, .am = 0xFF,
            };

            _log(SDL_LOG_PRIORITY_INFO, "%016" SDL_PRIx64 " -> %ux%u", key, width, height);
            SDL_free(file);
            SDL_free(path);
            return true;
        }
    }

    SDL_free(file);
    SDL_free(path);
    return false;
}

void TexRemix_Destroy(void) {
    SDL_free(replacement);
    replacement = NULL;
    dumped_count = 0;
}
