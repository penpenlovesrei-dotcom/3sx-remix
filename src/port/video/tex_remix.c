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
 * The `.tex` container is deliberately blunt: `3STX`, a version, width, height, then rows of RGBA --
 * or, in version 2, a palette of 256 entries and then one index byte per pixel, which is the format
 * the game's own background pages have always used and a quarter of the weight.
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
#include "port/video/trace_fin.h"
#include "port/config/config.h"
#include "port/resources.h"

#include <SDL3/SDL.h>

#define REMIX_DIR "tex_remix"
#define STAGE_COUNT_ORIGINAL 22
/// Une de plus que le dernier etage ajoute (57), pour les boucles qui les parcourent.
#define STAGE_COUNT_ADDED 58
#define TEX_MAGIC 0x58545333u // '3STX', little end first
#define TEX_VERSION 1
/* LA VERSION 2 : LA MEME PAGE, MAIS EN INDICES -- 25/09/2026.
 *
 * Une page de decor porte 128 x 128 pixels. En couleur pleine c'est 64 Ko ; le jeu, lui,
 * n'a jamais charge que du 128 x 128 a huit bits indexes, soit 16 Ko -- mesure sur les
 * 26 000 pages du vidage, sans une exception, listes 132, 196, 228, 260, 292 et 324. Nos
 * decors etaient les seuls objets trente-deux bits de tout 3SX.
 *
 * Ils tiennent tous dans 256 couleurs : compte sur les 2550 pages distinctes de New
 * Generation et de 2nd Impact, la pire en porte 206 (`stage24/196-226.tex`). La
 * conversion est donc SANS PERTE, d'autant que l'echantillonnage est deja en NEAREST.
 *
 *     0  '3STX'
 *     4  2
 *     8  largeur
 *    12  hauteur
 *    16  256 entrees de quatre octets, dans l'ordre meme des pixels de la version 1
 *  1040  largeur * hauteur indices
 *
 * La palette garde les octets tels que la version 1 les posait : elle traverse le meme
 * `.bgra` du nuanceur, donc l'image sortie est la meme, octet pour octet. Rien a
 * raisonner sur l'ordre des composantes.
 *
 * La version 1 reste lue : une page qui depasserait 256 couleurs la garde, et les
 * illustrations de `art_remix` ne sont pas concernees du tout.
 */
#define TEX_VERSION_INDEXED 2
#define TEX_PALETTE_ENTRIES 256
#define TEX_PALETTE_SIZE (TEX_PALETTE_ENTRIES * 4)
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

/// Which handles hold a replacement, so the drawing code can give them one whole quad instead of
/// the original page's coverage list. Kept whether or not the dump is on -- this one is not
/// bookkeeping, the picture depends on it.
static bool replacement_handle[HANDLES_MAX];

/// Whether the page last passed to @ref TexRemix_Substitute was replaced.
static bool pending_replaced = false;
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

/* LA PALETTE DE LA PAGE QU'ON VIENT DE POSER, ET POURQUOI UNE SEULE CASE SUFFIT.
 *
 * `TexRemix_Substitute` est appelee dans `ppgSetupTexChunk_3rd` juste avant
 * `flCreateTextureHandle`, qui appelle lui-meme `Renderer_CreateTexture`. Entre les deux
 * il ne se cree aucune autre texture : le rendu peut donc reprendre ici la palette de la
 * page qu'il est en train de creer. Elle se reprend UNE FOIS --
 * `TexRemix_TakeReplacementPalette` la rend et la retire -- pour qu'une texture creee
 * plus tard ne puisse pas heriter de celle d'une page precedente. */
static u32 palette_en_attente[TEX_PALETTE_ENTRIES];
static bool palette_en_attente_prete = false;

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

/// Stage currently loading its pages, or -1. Only stages past the original 22 use it.
static s32 current_stage = -1;

/* LES PAGES EN DOUBLE, ET L'INDEX QUI LES RETROUVE -- 23/09/2026.
 *
 * Une page d'etage ajoute pese 64 Ko, et Dudley 1 en porte 320 : deux listes de base, une
 * troisieme, et surtout la pluie de Londres, un plan anime a HUIT vues de 32 pages
 * (`etagesng_pages.inc`, `[44] = { plan 2, 8 vues }`). C'est le plus lourd des quarante
 * etages -- 20 Mo, le double du second -- et Frederic le trouve « tres long a charger ».
 *
 * Or la pluie ne couvre qu'une partie de chaque page : tout ce qu'elle ne touche pas se
 * repete d'une vue a l'autre. Mesure : 177 contenus distincts pour 320 fichiers, 143
 * doublons OCTET POUR OCTET, dont un groupe de vingt-quatre. Et ce n'est pas propre a
 * Dudley -- sur les quarante etages, 1467 pages sur 3360, soit 210 Mo qui tiennent en 118.
 *
 * `outils/pages_doublons.py --appliquer` ne garde donc qu'un fichier par contenu et ecrit
 * a cote un `doublons.txt` qui dit, pour chaque page effacee, laquelle porte son contenu :
 *
 *     de_liste de_page vers_liste vers_page
 *
 * On le lit UNE FOIS par etage, et seulement quand le chemin direct manque : un etage qui
 * n'a pas ete dedupliqué ne paie rien, et une installation qui garde ses doublons se
 * comporte exactement comme avant. Rien n'est perdu : le contenu efface etait identique.
 */
/* `remix_path` est defini plus bas ; l'index en a besoin des maintenant. */
static char* remix_path(const char* leaf);

#define DOUBLONS_MAX 2048

typedef struct {
    s32 de_liste;
    s32 de_page;
    s32 vers_liste;
    s32 vers_page;
} PageDoublon;

static PageDoublon doublons[DOUBLONS_MAX];
static s32 doublons_nb;
static s32 doublons_stage = -1;

/// Lit `stage<N>/doublons.txt`. Absent ou illisible : zero ligne, et on n'y revient pas.
static void charger_doublons(s32 stage) {
    doublons_stage = stage;
    doublons_nb = 0;

    char leaf[64];
    SDL_snprintf(leaf, sizeof(leaf), "stage%d/doublons.txt", (int)stage);
    char* path = remix_path(leaf);

    if (path == NULL) {
        return;
    }

    size_t taille = 0;
    char* texte = SDL_LoadFile(path, &taille);

    SDL_free(path);

    if (texte == NULL) {
        return;
    }

    const char* p = texte;
    const char* fin = texte + taille;

    while (p < fin && doublons_nb < DOUBLONS_MAX) {
        /* une ligne : quatre entiers, ou un commentaire qui commence par '#' */
        while (p < fin && (*p == '\r' || *p == '\n')) {
            p++;
        }

        if (p >= fin) {
            break;
        }

        if (*p == '#') {
            while (p < fin && *p != '\n') {
                p++;
            }
            continue;
        }

        s32 n[4];
        s32 lu = 0;

        while (lu < 4 && p < fin) {
            while (p < fin && (*p == ' ' || *p == '\t')) {
                p++;
            }

            if (p >= fin || *p < '0' || *p > '9') {
                break;
            }

            s32 v = 0;

            while (p < fin && *p >= '0' && *p <= '9') {
                v = v * 10 + (*p - '0');
                p++;
            }

            n[lu++] = v;
        }

        while (p < fin && *p != '\n') {
            p++;
        }

        if (lu == 4) {
            doublons[doublons_nb++] = (PageDoublon) { n[0], n[1], n[2], n[3] };
        }
    }

    SDL_free(texte);
    _log(SDL_LOG_PRIORITY_INFO, "stage %d: %d duplicate pages share %s", (int)stage, (int)doublons_nb,
         doublons_nb == 1 ? "another page" : "other pages");
}

/// La page qui porte le contenu de `(liste, page)`, quand celle-ci a ete effacee.
static bool page_canonique(s32 stage, s32 liste, s32 page, s32* o_liste, s32* o_page) {
    if (stage != doublons_stage) {
        charger_doublons(stage);
    }

    for (s32 i = 0; i < doublons_nb; i++) {
        if (doublons[i].de_liste == liste && doublons[i].de_page == page) {
            *o_liste = doublons[i].vers_liste;
            *o_page = doublons[i].vers_page;
            return true;
        }
    }

    return false;
}

void TexRemix_SetStage(s32 stage) {
    /* On note l'ouverture et la fermeture de la substitution : le journal du 31/08
       s'arretait sur soixante-quatre televersements de 128x128 tous identiques, sans
       qu'on puisse dire de quel etage ils venaient. Deux lignes suffisent a le dire. */
    if (stage != current_stage) {
        TraceFin("TexRemix_SetStage %d (etait %d)\n", (s32)stage, (s32)current_stage, 0);
    }

    current_stage = stage;
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

void TexRemix_ForgetHandle(u32 handle) {
    if (handle != 0 && handle < HANDLES_MAX) {
        replacement_handle[handle] = false;
    }
}

bool TexRemix_HandleIsReplacement(u32 handle) {
    return handle != 0 && handle < HANDLES_MAX && replacement_handle[handle];
}

void TexRemix_NoteTextureHandle(u32 handle) {
    if (handle == 0 || handle >= HANDLES_MAX) {
        return;
    }

    replacement_handle[handle] = pending_replaced;

    if (!Config_GetBool(CFG_TEX_REMIX_DUMP)) {
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

    // Pages owned by an added stage live one level down, and the pool has to make room for them too.
    //
    // LE PLUS GROS ETAGE, ET TOUS LES ETAGES AJOUTES -- 18/09/2026. La boucle s'arretait a
    // l'etage 37 : les pages de New Generation ne comptaient pas, et Dudley 1 en porte
    // maintenant 320 a lui seul (sa pluie a huit vues de 32 pages de reecriture). Les
    // additionner toutes demanderait un demi-gigaoctet ; or `Bg_Close` rend les poignees
    // d'un etage avant d'en charger un autre -- un seul jeu de pages vit a la fois. On
    // reserve donc la racine, plus le plus gros dossier d'etage.
    s64 pire = 0;

    for (s32 stage = STAGE_COUNT_ORIGINAL; stage < STAGE_COUNT_ADDED; stage++) {
        char leaf[32];
        SDL_snprintf(leaf, sizeof(leaf), "%s/stage%d", REMIX_DIR, (int)stage);
        char* sub = Resources_GetPath(leaf);

        if (sub != NULL) {
            s64 taille = 0;

            SDL_EnumerateDirectory(sub, add_file_size, &taille);
            SDL_free(sub);

            if (taille > pire) {
                pire = taille;
            }
        }
    }

    /* DEUX FOIS le plus gros : de quoi tenir si les pages d'un etage n'etaient pas encore
       rendues quand celles du suivant arrivent. */
    total += 2 * pire;

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

    /* L'EMPREINTE N'EST CALCULEE QUE SI ELLE SERT -- 22/09/2026. Elle parcourt la page
       octet par octet ; un etage ajoute, lui, retrouve ses pages PAR NUMERO et n'en a
       aucun besoin. Dudley 1 charge 320 pages (son archive porte sept vues de pluie) :
       c'etaient 320 empreintes pour rien a chaque entree dans le decor, et Frederic le
       trouve « tres long a charger ». On ne la prend plus que pour le vidage, ou quand
       la recherche par numero n'a rien donne et qu'il faut la cle. */
    pending_key = 0;
    pending_replaced = false;
    palette_en_attente_prete = false;

    const bool dump = Config_GetBool(CFG_TEX_REMIX_DUMP);

    if (dump) {
        pending_key = fingerprint(bits);
        dump_page(pending_key, bits, from);
    }

    char* path = NULL;

    // A stage added past the original 22 owns its pages by number, under stage<N>/<list>-<page>.tex.
    // It borrows another stage's archive file, so its pages carry that stage's fingerprints; keying
    // by number is what stops a replacement here from reaching the stage it borrowed from.
    if (current_stage >= STAGE_COUNT_ORIGINAL && from != NULL) {
        char leaf[64];
        SDL_snprintf(
            leaf, sizeof(leaf), "stage%d/%d-%d.tex", (int)current_stage, (int)from->first, (int)from->index
        );
        path = remix_path(leaf);

        if (path != NULL && !SDL_GetPathInfo(path, NULL)) {
            SDL_free(path);
            path = NULL;

            /* ELLE A PEUT-ETRE ETE DEDUPLIQUEE : une autre page porte le meme contenu,
               octet pour octet, et `doublons.txt` dit laquelle -- voir `charger_doublons`. */
            s32 liste = 0;
            s32 page = 0;

            if (page_canonique(current_stage, from->first, from->index, &liste, &page)) {
                SDL_snprintf(leaf, sizeof(leaf), "stage%d/%d-%d.tex", (int)current_stage, (int)liste, (int)page);
                path = remix_path(leaf);

                if (path != NULL && !SDL_GetPathInfo(path, NULL)) {
                    SDL_free(path);
                    path = NULL;
                }
            }
        }
    }

    if (path == NULL) {
        if (!dump) {
            pending_key = fingerprint(bits);
        }

        char* leaf = NULL;
        SDL_asprintf(&leaf, "%016" SDL_PRIx64 ".tex", pending_key);
        path = (leaf != NULL) ? remix_path(leaf) : NULL;
        SDL_free(leaf);
    }

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
    const Uint32 version = header[1];
    const Uint32 width = header[2];
    const Uint32 height = header[3];

    /* La version 2 porte sa palette entre l'entete et les indices, et un octet par pixel
       au lieu de quatre. Tout le reste du controle est le meme. */
    const bool indexee = (version == TEX_VERSION_INDEXED);
    const size_t avant = indexee ? (size_t)TEX_PALETTE_SIZE : 0u;
    const size_t expected = (size_t)width * height * (indexee ? 1u : 4u);

    if (header[0] != TEX_MAGIC || (version != TEX_VERSION && !indexee)) {
        _log(SDL_LOG_PRIORITY_WARN, "%s is not a version %d or %d .tex file", path, TEX_VERSION,
             TEX_VERSION_INDEXED);
    } else if (loaded - TEX_HEADER_SIZE < expected + avant) {
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
            SDL_memcpy(replacement, (const Uint8*)file + TEX_HEADER_SIZE + avant, expected);

            if (indexee) {
                SDL_memcpy(palette_en_attente, (const Uint8*)file + TEX_HEADER_SIZE, TEX_PALETTE_SIZE);
                palette_en_attente_prete = true;
            }

            bits->desc = 0;
            bits->width = width;
            bits->height = height;
            /* 1 = PSMT8, un octet d'indice par pixel ; 4 = PSMCT32, la couleur pleine.
               `flPS2ConvertTextureFromContext` recopie le PSMT8 tel quel, sans entrelacer :
               ce qu'on ecrit ici est exactement ce que le nuanceur lira. */
            bits->bitdepth = indexee ? 1 : 4;
            bits->pitch = width * bits->bitdepth;
            bits->ptr = replacement;
            bits->pixelformat = (PixelFormat) {
                .rl = 8, .rs = 0,  .rm = 0xFF,
                .gl = 8, .gs = 8,  .gm = 0xFF,
                .bl = 8, .bs = 16, .bm = 0xFF,
                .al = 8, .as = 24, .am = 0xFF,
            };

            /* UNE LIGNE PAR PAGE REMPLACEE, ET IL Y EN A 320 CHEZ DUDLEY 1 : en DEBUG,
               pas en INFO. La cle n'est plus calculee pour un etage ajoute ; le chemin
               dit de toute facon laquelle c'est. */
            _log(SDL_LOG_PRIORITY_DEBUG, "%s -> %ux%u", path, width, height);
            pending_replaced = true;
            SDL_free(file);
            SDL_free(path);
            return true;
        }
    }

    SDL_free(file);
    SDL_free(path);
    return false;
}

const u32* TexRemix_TakeReplacementPalette(void) {
    if (!palette_en_attente_prete) {
        return NULL;
    }

    palette_en_attente_prete = false;
    return palette_en_attente;
}

void TexRemix_Destroy(void) {
    SDL_free(replacement);
    replacement = NULL;
    palette_en_attente_prete = false;
    dumped_count = 0;
    SDL_zero(replacement_handle);
}
