/**
 * @file bgm_remix.c
 * Loads optional user-supplied remix packs that override BGM tracks.
 *
 * Packs live in `<resources>/bgm_remix/`, one folder each, described by a `remix.txt` manifest:
 *
 *     !name New Generation
 *
 *     # bgm code | file name | sound test label
 *     1 | theme_alex.adx | 1. Alex Stage -NEW GENERATION-
 *
 * Every pack takes a slot on the `BGM Type` row of the sound options, after `Arrange` and
 * `Original`. Any code a pack doesn't list keeps playing the arranged track, so a pack may
 * override a single stage or the whole soundtrack.
 *
 * A stage code with no entry falls back to its stage's mix 1 entry. That lets a soundtrack
 * without per-round mixes ship one track per stage and have it cover all three rounds — and
 * because all three rounds then resolve to the same file, sound3rd.c can let it play through
 * the round transitions untouched.
 */

#include "port/sound/bgm_remix.h"
#include "port/resources.h"
#include "port/sound/adx_decoder.h"

#include <SDL3/SDL.h>

#include <stdarg.h>

#define PACKS_DIR "bgm_remix"
#define MANIFEST_NAME "remix.txt"
#define MENU_NAME "menu.txt"
#define CUSTOM_NAME "custom.txt"

/// The sixteen stage themes, by the mix 1 code the game asks for and the name custom.txt uses.
/// Stages shared by two characters carry both, since the game gives them one theme.
static const struct {
    int base_code;
    const char* name;
} stage_themes[] = {
    { 1, "alex-ken" },  { 4, "necro-twelve" }, { 7, "hugo" },   { 10, "chun-li" },
    { 13, "ryu" },      { 16, "ibuki" },       { 19, "makoto" }, { 22, "akuma" },
    { 25, "elena" },    { 28, "sean-oro" },    { 31, "dudley" }, { 34, "yun-yang" },
    { 37, "remy" },     { 40, "q" },           { 43, "urien" },  { 46, "gill" },
};

#define STAGE_THEME_COUNT ((int)SDL_arraysize(stage_themes))

// The sound test draws one sprite per character at a fixed 8px pitch, starting near the left
// edge of a 384px wide screen. Longer labels would run off screen.
#define LABEL_LENGTH_MAX 44

typedef struct RemixTrack {
    char* path;
    char* name;
} RemixTrack;

typedef struct RemixPack {
    char* dir;  ///< Folder name, which is how menu.txt refers to the pack
    char* name;
    bool arcade;  ///< Follows the arcade layout: two per-round mixes per stage instead of three
    int volume_trim; ///< Level correction in tenths of a dB, for a pack mastered off the game's reference
    RemixTrack tracks[BGM_REMIX_CODE_MAX + 1];
} RemixPack;

/// One value of the `BGM Type` row
typedef struct MenuSlot {
    int type;
    char* label; ///< Override from menu.txt, or NULL to use the pack name / the game's own text
} MenuSlot;

static RemixPack packs[BGM_REMIX_PACKS_MAX] = { 0 };
static int pack_count = 0;
static MenuSlot slots[BGM_REMIX_SLOTS_MAX] = { 0 };
static int slot_count = 0;
/// Per-stage soundtrack from custom.txt, indexed like stage_themes; -1 means unassigned
static int custom_types[STAGE_THEME_COUNT];
static int custom_count = 0;
static bool loaded = false;

static void _log(SDL_LogPriority priority, const char* fmt, ...) {
    char buffer[512];
    va_list args;
    va_start(args, fmt);

    int len = SDL_snprintf(buffer, sizeof(buffer), "[BGM remix] ");
    SDL_vsnprintf(buffer + len, sizeof(buffer) - len, fmt, args);
    SDL_LogMessage(SDL_LOG_CATEGORY_APPLICATION, priority, "%s", buffer);

    va_end(args);
}

static char* trim(char* string) {
    while (*string == ' ' || *string == '\t') {
        string += 1;
    }

    char* end = string + SDL_strlen(string);

    while ((end > string) && ((end[-1] == ' ') || (end[-1] == '\t') || (end[-1] == '\r'))) {
        end -= 1;
    }

    *end = '\0';
    return string;
}

/// The menu font maps a byte straight onto a sprite index, so anything outside printable ASCII
/// would pull in garbage tiles. Replace those with spaces and cut the text to size.
static char* sanitize(const char* text, int max_length) {
    char* result = SDL_malloc(max_length + 1);
    int i = 0;

    for (; (i < max_length) && (text[i] != '\0'); i++) {
        const unsigned char c = (unsigned char)text[i];
        result[i] = ((c >= 0x20) && (c <= 0x7E)) ? (char)c : ' ';
    }

    result[i] = '\0';
    return result;
}

/// @brief Mix 1 code of the stage a code belongs to, or 0 when it isn't a stage theme.
///
/// Stage themes run from code 1 to 48 in groups of three: 1/2/3 are stage 1 mixes 1/2/3, 4/5/6
/// are stage 2, and so on.
static int base_mix_code(int bgm_code) {
    if ((bgm_code < 1) || (bgm_code > BGM_REMIX_STAGE_CODE_MAX)) {
        return 0;
    }

    return ((bgm_code - 1) / 3) * 3 + 1;
}

/// @brief Entry a code resolves to, following the mix 1 fallback.
static const RemixTrack* resolve(int pack, int bgm_code) {
    if ((pack < 0) || (pack >= pack_count) || (bgm_code < 1) || (bgm_code > BGM_REMIX_CODE_MAX)) {
        return NULL;
    }

    const RemixTrack* track = &packs[pack].tracks[bgm_code];

    if (track->path != NULL) {
        return track;
    }

    const int base = base_mix_code(bgm_code);

    if ((base != 0) && (base != bgm_code) && (packs[pack].tracks[base].path != NULL)) {
        return &packs[pack].tracks[base];
    }

    return NULL;
}

/// Reject unplayable files up front: `track_init` treats a decoder failure as fatal, so a typo
/// in a manifest would otherwise take the game down mid-match.
static bool validate_adx(const char* path) {
    SDL_IOStream* io = SDL_IOFromFile(path, "rb");

    if (io == NULL) {
        _log(SDL_LOG_PRIORITY_WARN, "%s: cannot be opened", path);
        return false;
    }

    ADXDecoder decoder;
    const bool valid = ADXDecoder_Init(&decoder, io);

    if (!valid) {
        _log(SDL_LOG_PRIORITY_WARN, "%s: not a supported ADX file (need standard encoding, 4-bit, 1-2 channels)", path);
    } else if (!decoder.header.loop_enabled) {
        _log(SDL_LOG_PRIORITY_INFO, "%s: no loop points, the track will play once and stop", path);
    }

    SDL_CloseIO(io);
    return valid;
}

static void parse_track_line(RemixPack* pack, const char* pack_dir, char* line) {
    char* code_field = line;
    char* file_field = SDL_strchr(line, '|');

    if (file_field == NULL) {
        _log(SDL_LOG_PRIORITY_WARN, "%s: skipping malformed line: %s", pack->name, line);
        return;
    }

    *file_field++ = '\0';
    char* name_field = SDL_strchr(file_field, '|');

    if (name_field != NULL) {
        *name_field++ = '\0';
        name_field = trim(name_field);
    }

    code_field = trim(code_field);
    file_field = trim(file_field);

    const int code = SDL_atoi(code_field);

    if ((code < 1) || (code > BGM_REMIX_CODE_MAX)) {
        _log(SDL_LOG_PRIORITY_WARN, "%s: skipping out of range BGM code %s (expected 1-%d)", pack->name, code_field,
             BGM_REMIX_CODE_MAX);
        return;
    }

    if (pack->tracks[code].path != NULL) {
        _log(SDL_LOG_PRIORITY_WARN, "%s: BGM code %d listed twice, keeping the first entry", pack->name, code);
        return;
    }

    if (*file_field == '\0') {
        _log(SDL_LOG_PRIORITY_WARN, "%s: skipping BGM code %d: no file name", pack->name, code);
        return;
    }

    char* relative_path;
    SDL_asprintf(&relative_path, "%s/%s/%s", PACKS_DIR, pack_dir, file_field);
    char* path = Resources_GetPath(relative_path);
    SDL_free(relative_path);

    if (!validate_adx(path)) {
        SDL_free(path);
        return;
    }

    pack->tracks[code].path = path;

    if ((name_field != NULL) && (*name_field != '\0')) {
        pack->tracks[code].name = sanitize(name_field, LABEL_LENGTH_MAX);
    }
}

static void parse_directive(RemixPack* pack, char* line) {
    char* directive = line + 1;
    char* value = directive;

    while ((*value != '\0') && (*value != ' ') && (*value != '\t')) {
        value += 1;
    }

    if (*value != '\0') {
        *value++ = '\0';
        value = trim(value);
    }

    if (SDL_strcmp(directive, "name") == 0) {
        if (*value == '\0') {
            _log(SDL_LOG_PRIORITY_WARN, "!name with no value, keeping %s", pack->name);
            return;
        }

        SDL_free(pack->name);
        pack->name = sanitize(value, BGM_REMIX_NAME_MAX);
    } else if (SDL_strcmp(directive, "volume") == 0) {
        // Decibels, so "-6.4" is a little over half the way to half-loudness. Accept a comma as
        // the decimal mark too, since that is what a French keyboard and locale will produce.
        char* comma = SDL_strchr(value, ',');

        if (comma != NULL) {
            *comma = '.';
        }

        const double db = SDL_atof(value);

        if ((db < -40.0) || (db > 12.0)) {
            _log(SDL_LOG_PRIORITY_WARN, "%s: !volume %s is outside -40..+12 dB, ignoring", pack->name, value);
            return;
        }

        pack->volume_trim = (int)SDL_round(db * 10.0);
    } else if (SDL_strcmp(directive, "structure") == 0) {
        if (SDL_strcasecmp(value, "arcade") == 0) {
            pack->arcade = true;
        } else if (SDL_strcasecmp(value, "console") == 0) {
            pack->arcade = false;
        } else {
            _log(SDL_LOG_PRIORITY_WARN, "%s: !structure takes arcade or console, not \"%s\"", pack->name, value);
        }
    } else {
        _log(SDL_LOG_PRIORITY_WARN, "%s: unknown directive !%s", pack->name, directive);
    }
}

/// @brief Read one pack. `pack_dir` is a folder name under `bgm_remix/`, or "." for a manifest
///        sitting directly in `bgm_remix/` (the single-pack layout).
/// @return `true` if the pack holds at least one usable track.
static bool load_pack(RemixPack* pack, const char* pack_dir, const char* default_name) {
    char* relative_path;
    SDL_asprintf(&relative_path, "%s/%s/%s", PACKS_DIR, pack_dir, MANIFEST_NAME);
    char* manifest_path = Resources_GetPath(relative_path);
    SDL_free(relative_path);

    char* contents = SDL_LoadFile(manifest_path, NULL);

    if (contents == NULL) {
        SDL_free(manifest_path);
        return false;
    }

    pack->dir = SDL_strdup(pack_dir);
    pack->name = sanitize(default_name, BGM_REMIX_NAME_MAX);

    char* cursor = contents;
    int declared = 0;

    while (*cursor != '\0') {
        char* line = cursor;
        char* newline = SDL_strchr(cursor, '\n');

        if (newline != NULL) {
            *newline = '\0';
            cursor = newline + 1;
        } else {
            cursor += SDL_strlen(cursor);
        }

        line = trim(line);

        if ((*line == '\0') || (*line == '#')) {
            continue;
        }

        if (*line == '!') {
            parse_directive(pack, line);
        } else {
            declared += 1;
            parse_track_line(pack, pack_dir, line);
        }
    }

    SDL_free(contents);

    int count = 0;

    for (int i = 1; i <= BGM_REMIX_CODE_MAX; i++) {
        if (pack->tracks[i].path != NULL) {
            count += 1;
        }
    }

    if (count == 0) {
        // A manifest holding nothing but comments is a pack waiting to be filled, not a mistake
        _log(declared == 0 ? SDL_LOG_PRIORITY_INFO : SDL_LOG_PRIORITY_WARN,
             declared == 0 ? "%s declares no track yet, hiding the pack"
                           : "%s has no usable entries, hiding the pack",
             manifest_path);
        SDL_free(pack->dir);
        SDL_free(pack->name);
        SDL_zerop(pack);
        SDL_free(manifest_path);
        return false;
    }

    _log(SDL_LOG_PRIORITY_INFO, "Pack \"%s\": %d track(s) from %s", pack->name, count, manifest_path);
    SDL_free(manifest_path);
    return true;
}

static void load_custom();

static int SDLCALL compare_names(const void* a, const void* b) {
    return SDL_strcmp(*(const char* const*)a, *(const char* const*)b);
}

/// @brief BGM type a `menu.txt` entry names: a reserved word for the stock soundtracks, or a
///        pack folder name.
/// @return -1 when nothing matches.
static int type_from_menu_name(const char* name) {
    if (SDL_strcasecmp(name, "arrange") == 0) {
        return BGM_REMIX_TYPE_ARRANGED;
    }

    if (SDL_strcasecmp(name, "original") == 0) {
        return BGM_REMIX_TYPE_ORIGINAL;
    }

    if (SDL_strcasecmp(name, "random") == 0) {
        return BGM_REMIX_TYPE_RANDOM;
    }

    if (SDL_strcasecmp(name, "custom") == 0) {
        return BGM_REMIX_TYPE_CUSTOM;
    }

    for (int p = 0; p < pack_count; p++) {
        if (SDL_strcasecmp(name, packs[p].dir) == 0) {
            return BGM_REMIX_TYPE_FIRST_PACK + p;
        }
    }

    return -1;
}

/// @brief Whether a name belongs to a pack folder that exists but holds no track yet.
///
/// Listing a pack in `menu.txt` before filling it is a normal way to work, so it shouldn't read
/// like a typo in the log.
static bool pack_folder_exists(const char* name) {
    char* relative_path;
    SDL_asprintf(&relative_path, "%s/%s/%s", PACKS_DIR, name, MANIFEST_NAME);
    char* path = Resources_GetPath(relative_path);
    SDL_free(relative_path);

    SDL_PathInfo info;
    const bool exists = SDL_GetPathInfo(path, &info) && (info.type == SDL_PATHTYPE_FILE);
    SDL_free(path);
    return exists;
}

/// Default row: the two stock soundtracks, the packs in the order they were found, then Random.
static void build_default_slots() {
    SDL_zeroa(slots);
    slot_count = 0;
    slots[slot_count++].type = BGM_REMIX_TYPE_ARRANGED;
    slots[slot_count++].type = BGM_REMIX_TYPE_ORIGINAL;

    for (int p = 0; p < pack_count; p++) {
        slots[slot_count++].type = BGM_REMIX_TYPE_FIRST_PACK + p;
    }

    // Random draws among the entries above, so it only earns a place once there are several
    slots[slot_count++].type = BGM_REMIX_TYPE_RANDOM;
    slots[slot_count++].type = BGM_REMIX_TYPE_CUSTOM;
}

/// @brief Apply the optional `bgm_remix/menu.txt`, which lists the row's entries in order and may
///        relabel them.
///
/// Entries the file leaves out keep their default order after the listed ones, so a file naming
/// only the packs still leaves `Arrange` and `Original` reachable.
static void apply_menu_order() {
    char* path = Resources_GetPath(PACKS_DIR "/" MENU_NAME);
    char* contents = SDL_LoadFile(path, NULL);

    if (contents == NULL) {
        SDL_free(path);
        return;
    }

    MenuSlot ordered[BGM_REMIX_SLOTS_MAX] = { 0 };
    bool placed[BGM_REMIX_SLOTS_MAX] = { false };
    int ordered_count = 0;

    char* cursor = contents;

    while (*cursor != '\0') {
        char* line = cursor;
        char* newline = SDL_strchr(cursor, '\n');

        if (newline != NULL) {
            *newline = '\0';
            cursor = newline + 1;
        } else {
            cursor += SDL_strlen(cursor);
        }

        line = trim(line);

        if ((*line == '\0') || (*line == '#')) {
            continue;
        }

        // "<name>" or "<name> = <label>"
        char* label = SDL_strchr(line, '=');

        if (label != NULL) {
            *label++ = '\0';
            label = trim(label);
        }

        const char* name = trim(line);
        const int type = type_from_menu_name(name);

        if (type < 0) {
            if (pack_folder_exists(name)) {
                _log(SDL_LOG_PRIORITY_INFO, "%s: \"%s\" has no track yet, leaving it out of the row", MENU_NAME, name);
            } else {
                _log(SDL_LOG_PRIORITY_WARN, "%s: no soundtrack called \"%s\"", MENU_NAME, name);
            }

            continue;
        }

        int slot = -1;

        for (int i = 0; i < slot_count; i++) {
            if (slots[i].type == type) {
                slot = i;
                break;
            }
        }

        if ((slot < 0) || placed[slot]) {
            _log(SDL_LOG_PRIORITY_WARN, "%s: \"%s\" listed twice, keeping the first position", MENU_NAME, name);
            continue;
        }

        placed[slot] = true;
        ordered[ordered_count].type = type;

        if ((label != NULL) && (*label != '\0')) {
            ordered[ordered_count].label = sanitize(label, BGM_REMIX_NAME_MAX);
        }

        ordered_count += 1;
    }

    SDL_free(contents);

    for (int i = 0; i < slot_count; i++) {
        if (!placed[i]) {
            ordered[ordered_count++] = slots[i];
        }
    }

    SDL_memcpy(slots, ordered, sizeof(slots));
    _log(SDL_LOG_PRIORITY_INFO, "Applied the row order from %s", path);
    SDL_free(path);
}

static void load() {
    loaded = true;

    // Single-pack layout: a manifest sitting directly in bgm_remix/
    if (load_pack(&packs[pack_count], ".", "Remix")) {
        pack_count += 1;
    }

    char* packs_root = Resources_GetPath(PACKS_DIR);
    int entry_count = 0;
    char** entries = SDL_GlobDirectory(packs_root, NULL, 0, &entry_count);
    SDL_free(packs_root);

    if (entries == NULL) {
        build_default_slots();
        apply_menu_order();
        load_custom();
        return;
    }

    // Folder order is not guaranteed, so sort to keep the menu stable between runs
    SDL_qsort(entries, entry_count, sizeof(*entries), compare_names);

    for (int i = 0; i < entry_count; i++) {
        if (pack_count >= BGM_REMIX_PACKS_MAX) {
            _log(SDL_LOG_PRIORITY_WARN, "Reached the %d pack limit, ignoring the rest", BGM_REMIX_PACKS_MAX);
            break;
        }

        // load_pack fails harmlessly on entries that aren't pack folders
        if (load_pack(&packs[pack_count], entries[i], entries[i])) {
            pack_count += 1;
        }
    }

    SDL_free(entries);
    build_default_slots();
    apply_menu_order();
    load_custom();
}

/// @brief Read the optional `bgm_remix/custom.txt`, which names a soundtrack per stage theme.
///
/// One `stage = soundtrack` per line. A stage left out plays the arranged track, so a file may
/// assign a single stage or all sixteen.
static void load_custom() {
    for (int i = 0; i < STAGE_THEME_COUNT; i++) {
        custom_types[i] = -1;
    }

    custom_count = 0;

    char* path = Resources_GetPath(PACKS_DIR "/" CUSTOM_NAME);
    char* contents = SDL_LoadFile(path, NULL);

    if (contents == NULL) {
        SDL_free(path);
        return;
    }

    char* cursor = contents;

    while (*cursor != '\0') {
        char* line = cursor;
        char* newline = SDL_strchr(cursor, '\n');

        if (newline != NULL) {
            *newline = '\0';
            cursor = newline + 1;
        } else {
            cursor += SDL_strlen(cursor);
        }

        line = trim(line);

        if ((*line == '\0') || (*line == '#')) {
            continue;
        }

        char* value = SDL_strchr(line, '=');

        if (value == NULL) {
            _log(SDL_LOG_PRIORITY_WARN, "%s: skipping malformed line: %s", CUSTOM_NAME, line);
            continue;
        }

        *value++ = '\0';
        const char* stage = trim(line);
        const char* soundtrack = trim(value);

        int index = -1;

        for (int i = 0; i < STAGE_THEME_COUNT; i++) {
            if (SDL_strcasecmp(stage, stage_themes[i].name) == 0) {
                index = i;
                break;
            }
        }

        if (index < 0) {
            _log(SDL_LOG_PRIORITY_WARN, "%s: no stage called \"%s\"", CUSTOM_NAME, stage);
            continue;
        }

        const int type = type_from_menu_name(soundtrack);

        if ((type < 0) || (type >= BGM_REMIX_TYPE_RANDOM)) {
            _log(SDL_LOG_PRIORITY_WARN, "%s: %s cannot use \"%s\"", CUSTOM_NAME, stage, soundtrack);
            continue;
        }

        custom_types[index] = type;
        custom_count += 1;
    }

    SDL_free(contents);
    _log(SDL_LOG_PRIORITY_INFO, "Custom: %d stage(s) assigned from %s", custom_count, path);
    SDL_free(path);
}

static void ensure_loaded() {
    if (!loaded) {
        load();
    }
}


const char* BgmRemix_GetTrackPath(int pack, int bgm_code) {
    ensure_loaded();
    const RemixTrack* track = resolve(pack, bgm_code);
    return (track != NULL) ? track->path : NULL;
}

const char* BgmRemix_GetTrackName(int pack, int bgm_code) {
    ensure_loaded();
    const RemixTrack* track = resolve(pack, bgm_code);
    return (track != NULL) ? track->name : NULL;
}

bool BgmRemix_UsesArcadeTables(int pack) {
    ensure_loaded();

    if ((pack < 0) || (pack >= pack_count)) {
        return false;
    }

    return packs[pack].arcade;
}

int BgmRemix_GetVolumeTrim(int pack) {
    ensure_loaded();

    if ((pack < 0) || (pack >= pack_count)) {
        return 0;
    }

    return packs[pack].volume_trim;
}

int BgmRemix_GetSlotCount() {
    ensure_loaded();
    return slot_count;
}

int BgmRemix_GetSlotType(int slot) {
    ensure_loaded();

    if ((slot < 0) || (slot >= slot_count)) {
        return BGM_REMIX_TYPE_ARRANGED;
    }

    return slots[slot].type;
}

int BgmRemix_GetSlotForType(int type) {
    ensure_loaded();

    for (int i = 0; i < slot_count; i++) {
        if (slots[i].type == type) {
            return i;
        }
    }

    return 0;
}

const char* BgmRemix_GetSlotLabel(int slot) {
    ensure_loaded();

    if ((slot < 0) || (slot >= slot_count)) {
        return NULL;
    }

    if (slots[slot].label != NULL) {
        return slots[slot].label;
    }

    const int type = slots[slot].type;

    if (type == BGM_REMIX_TYPE_RANDOM) {
        return "Random";
    }

    if (type == BGM_REMIX_TYPE_CUSTOM) {
        return "Custom";
    }

    if (type >= BGM_REMIX_TYPE_FIRST_PACK) {
        return packs[type - BGM_REMIX_TYPE_FIRST_PACK].name;
    }

    return NULL; // Stock entry the user left alone
}

int BgmRemix_GetCustomType(int base_code) {
    ensure_loaded();

    for (int i = 0; i < STAGE_THEME_COUNT; i++) {
        if (stage_themes[i].base_code == base_code) {
            return custom_types[i];
        }
    }

    return -1;
}

bool BgmRemix_HasCustom() {
    ensure_loaded();
    return custom_count > 0;
}

int BgmRemix_GetStageCount() {
    return STAGE_THEME_COUNT;
}

int BgmRemix_GetStageCode(int index) {
    if ((index < 0) || (index >= STAGE_THEME_COUNT)) {
        return 0;
    }

    return stage_themes[index].base_code;
}

/// @brief The soundtrack at a position in the screen's list, skipping Random and Custom.
/// @return -1 past the end.
static int soundtrack_type_at(int index) {
    int seen = 0;

    for (int i = 0; i < slot_count; i++) {
        const int type = slots[i].type;

        if ((type == BGM_REMIX_TYPE_RANDOM) || (type == BGM_REMIX_TYPE_CUSTOM)) {
            continue;
        }

        if (seen == index) {
            return type;
        }

        seen += 1;
    }

    return -1;
}

int BgmRemix_GetSoundtrackCount() {
    ensure_loaded();
    int count = 0;

    for (int i = 0; i < slot_count; i++) {
        const int type = slots[i].type;

        if ((type != BGM_REMIX_TYPE_RANDOM) && (type != BGM_REMIX_TYPE_CUSTOM)) {
            count += 1;
        }
    }

    return count;
}

bool BgmRemix_SoundtrackCoversStage(int index, int stage_index) {
    ensure_loaded();
    const int type = soundtrack_type_at(index);

    if (type < BGM_REMIX_TYPE_FIRST_PACK) {
        return true;   // Arrange and Original are the game's own, and cover every stage
    }

    if ((stage_index < 0) || (stage_index >= STAGE_THEME_COUNT)) {
        return false;
    }

    // resolve() already falls a stage's other mixes back to its mix 1, so asking about that one
    // code answers for the whole stage
    return BgmRemix_GetTrackPath(type - BGM_REMIX_TYPE_FIRST_PACK,
                                 stage_themes[stage_index].base_code) != NULL;
}

const char* BgmRemix_GetSoundtrackLabel(int index) {
    ensure_loaded();
    const int type = soundtrack_type_at(index);

    // This screen draws in the smaller charset with a wider column than the BGM Type row, so a
    // pack shows the full name from its manifest rather than whatever abbreviation menu.txt had
    // to settle for.
    if (type >= BGM_REMIX_TYPE_FIRST_PACK) {
        return packs[type - BGM_REMIX_TYPE_FIRST_PACK].name;
    }

    for (int i = 0; i < slot_count; i++) {
        if (slots[i].type == type) {
            const char* label = BgmRemix_GetSlotLabel(i);
            return (label != NULL) ? label : ((type == BGM_REMIX_TYPE_ORIGINAL) ? "Original" : "Arrange");
        }
    }

    return "Arrange";
}

int BgmRemix_GetStageChoice(int stage_index) {
    ensure_loaded();

    if ((stage_index < 0) || (stage_index >= STAGE_THEME_COUNT)) {
        return 0;
    }

    // An unassigned stage reads as the arranged soundtrack, which is what it plays
    const int type = (custom_types[stage_index] >= 0) ? custom_types[stage_index] : BGM_REMIX_TYPE_ARRANGED;
    const int count = BgmRemix_GetSoundtrackCount();

    for (int i = 0; i < count; i++) {
        if (soundtrack_type_at(i) == type) {
            return i;
        }
    }

    return 0;
}

void BgmRemix_SetStageChoice(int stage_index, int soundtrack_index) {
    ensure_loaded();

    if ((stage_index < 0) || (stage_index >= STAGE_THEME_COUNT)) {
        return;
    }

    const int type = soundtrack_type_at(soundtrack_index);

    if (type < 0) {
        return;
    }

    if (custom_types[stage_index] < 0) {
        custom_count += 1;
    }

    custom_types[stage_index] = type;
}

void BgmRemix_SaveCustom() {
    ensure_loaded();

    char* path = Resources_GetPath(PACKS_DIR "/" CUSTOM_NAME);
    SDL_IOStream* io = SDL_IOFromFile(path, "w");

    if (io == NULL) {
        _log(SDL_LOG_PRIORITY_WARN, "Cannot write %s", path);
        SDL_free(path);
        return;
    }

    const char* header = "# One soundtrack per stage, for the Custom BGM type.\n"
                         "# Written by the game; edit freely, it is read back at startup.\n\n";
    SDL_WriteIO(io, header, SDL_strlen(header));

    for (int i = 0; i < STAGE_THEME_COUNT; i++) {
        if (custom_types[i] < 0) {
            continue;
        }

        const char* soundtrack = "arrange";

        if (custom_types[i] == BGM_REMIX_TYPE_ORIGINAL) {
            soundtrack = "original";
        } else if (custom_types[i] >= BGM_REMIX_TYPE_FIRST_PACK) {
            soundtrack = packs[custom_types[i] - BGM_REMIX_TYPE_FIRST_PACK].dir;
        }

        char line[128];
        const int length = SDL_snprintf(line, sizeof(line), "%-13s = %s\n", stage_themes[i].name, soundtrack);
        SDL_WriteIO(io, line, length);
    }

    SDL_CloseIO(io);
    _log(SDL_LOG_PRIORITY_INFO, "Custom: saved %d stage(s) to %s", custom_count, path);
    SDL_free(path);
}

bool BgmRemix_CanRandomise() {
    ensure_loaded();
    int count = 0;

    for (int i = 0; i < slot_count; i++) {
        if (slots[i].type != BGM_REMIX_TYPE_RANDOM) {
            count += 1;
        }
    }

    return count > 1;
}

int BgmRemix_PickRandomType(int previous) {
    ensure_loaded();

    int choices[BGM_REMIX_SLOTS_MAX];
    int count = 0;

    for (int i = 0; i < slot_count; i++) {
        if (slots[i].type != BGM_REMIX_TYPE_RANDOM) {
            choices[count++] = slots[i].type;
        }
    }

    if (count == 0) {
        return BGM_REMIX_TYPE_ARRANGED;
    }

    if (count == 1) {
        return choices[0];
    }

    // Draw again rather than repeat: hearing the same soundtrack twice running would read as the
    // setting having no effect. SDL's generator is used so the game's own stays untouched — it
    // drives gameplay and the rollback netcode replays it.
    for (int attempt = 0; attempt < 8; attempt++) {
        const int pick = choices[SDL_rand(count)];

        if (pick != previous) {
            return pick;
        }
    }

    return choices[0];
}

void BgmRemix_Destroy() {
    for (int i = 0; i < slot_count; i++) {
        SDL_free(slots[i].label);
    }

    SDL_zeroa(slots);
    slot_count = 0;

    for (int p = 0; p < pack_count; p++) {
        SDL_free(packs[p].dir);
        SDL_free(packs[p].name);

        for (int i = 0; i <= BGM_REMIX_CODE_MAX; i++) {
            SDL_free(packs[p].tracks[i].path);
            SDL_free(packs[p].tracks[i].name);
        }
    }

    SDL_zeroa(packs);
    pack_count = 0;
    loaded = false;
}
