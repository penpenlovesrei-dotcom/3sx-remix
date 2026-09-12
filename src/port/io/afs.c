#include "port/io/afs.h"
#include "common.h"
#include "port/resources.h"

#include "stb/stb_ds.h"
#include <SDL3/SDL.h>

#include <stdarg.h>
#include <stdio.h>

// Inspired by https://github.com/MaikelChan/AFSLib

#define AFS_MAGIC 0x41465300
#define AFS_ATTRIBUTE_HEADER_SIZE 8
#define AFS_ATTRIBUTE_ENTRY_SIZE 48
#define AFS_MAX_NAME_LENGTH 32

typedef struct AFSEntry {
    size_t offset;
    size_t size;
    char name[AFS_MAX_NAME_LENGTH];
    /// Flux propre a cette entree, ou NULL pour l'archive d'origine.
    ///
    /// C'est ce qui permet d'AJOUTER des fichiers sans toucher a `SF33RD.AFS`. Un etage
    /// ajoute cessait d'emprunter l'archive de pages d'un etage existant : il herite
    /// sinon du nombre de plans de cette archive, de ses masques troues et de ses
    /// pixels partout ou on ne remplace pas. Avec la sienne, on choisit le nombre de
    /// pages, donc le nombre de plans. Voir @ref ajouter_fichiers_du_disque.
    SDL_IOStream* io;
} AFSEntry;

typedef struct AFS {
    const char* file_path;
    size_t entry_count;
    AFSEntry* entries;
} AFS;

typedef struct ReadRequest {
    bool initialized;
    size_t file_num;
    size_t bytes_to_read;
    size_t bytes_read;
    Uint8* buf;
    AFSReadState state;
} ReadRequest;

static AFS afs = { 0 };
static ReadRequest* requests = NULL;
static SDL_IOStream* stream = NULL;
static size_t _read_chunk_size = 0;

static void _log(const char* fmt, ...) {
    char buffer[512];
    va_list args;
    va_start(args, fmt);

    int len = SDL_snprintf(buffer, sizeof(buffer), "[AFS] ");
    SDL_vsnprintf(buffer + len, sizeof(buffer) - len, fmt, args);
    SDL_LogMessage(SDL_LOG_CATEGORY_APPLICATION, SDL_LOG_PRIORITY_DEBUG, "%s", buffer);

    va_end(args);
}

static bool is_valid_attribute_data(Uint32 attributes_offset, Uint32 attributes_size, Sint64 file_size,
                                    Uint32 entries_end_offset, Uint32 entry_count) {
    if ((attributes_offset == 0) || (attributes_size == 0)) {
        return false;
    }

    if (attributes_size > (file_size - entries_end_offset)) {
        return false;
    }

    if (attributes_size < (entry_count * AFS_ATTRIBUTE_ENTRY_SIZE)) {
        return false;
    }

    if (attributes_offset < entries_end_offset) {
        return false;
    }

    if (attributes_offset > (file_size - attributes_size)) {
        return false;
    }

    return true;
}

static void read_string(SDL_IOStream* src, char* dst) {
    char c;

    do {
        SDL_ReadS8(src, &c);
        *dst++ = c;
    } while (c != '\0');
}

static bool init_afs(const char* file_path) {
    afs.file_path = SDL_strdup(file_path);
    SDL_IOStream* io = SDL_IOFromFile(file_path, "rb");

    if (io == NULL) {
        return false;
    }

    // Check magic

    Uint32 magic = 0;
    SDL_ReadU32BE(io, &magic);

    if (magic != AFS_MAGIC) {
        SDL_CloseIO(io);
        return false;
    }

    // Read entries

    SDL_ReadU32LE(io, &afs.entry_count);
    afs.entries = SDL_calloc(afs.entry_count, sizeof(AFSEntry));

    Uint32 entries_start_offset = 0;
    Uint32 entries_end_offset = 0;

    for (int i = 0; i < afs.entry_count; i++) {
        AFSEntry* entry = &afs.entries[i];
        SDL_ReadU32LE(io, &entry->offset);
        SDL_ReadU32LE(io, &entry->size);

        if (entry->offset != 0) {
            if (entries_start_offset == 0) {
                entries_start_offset = entry->offset;
            }

            entries_end_offset = entry->offset + entry->size;
        }
    }

    // Locate attributes

    Uint32 attributes_offset;
    Uint32 attributes_size;
    bool has_attributes = false;

    SDL_ReadU32LE(io, &attributes_offset);
    SDL_ReadU32LE(io, &attributes_size);

    if (is_valid_attribute_data(
            attributes_offset, attributes_size, SDL_GetIOSize(io), entries_end_offset, afs.entry_count)) {
        has_attributes = true;
    } else {
        SDL_SeekIO(io, entries_start_offset - AFS_ATTRIBUTE_HEADER_SIZE, SDL_IO_SEEK_SET);

        SDL_ReadU32LE(io, &attributes_offset);
        SDL_ReadU32LE(io, &attributes_size);

        if (is_valid_attribute_data(
                attributes_offset, attributes_size, SDL_GetIOSize(io), entries_end_offset, afs.entry_count)) {
            has_attributes = true;
        }
    }

    for (int i = 0; i < afs.entry_count; i++) {
        AFSEntry* entry = &afs.entries[i];

        if ((entry->offset != 0) && has_attributes) {
            SDL_SeekIO(io, attributes_offset + i * AFS_ATTRIBUTE_ENTRY_SIZE, SDL_IO_SEEK_SET);
            read_string(io, entry->name);
        } else {
            SDL_zeroa(entry->name);
        }
    }

    stream = io;
    return true;
}

/// @brief Ajoute a l'archive les fichiers de `resources/stages/`, sans la modifier.
///
/// Le NOM du fichier est son numero : `resources/stages/1535.bin` devient le fichier
/// 1535. C'est volontairement explicite -- `color_file[].apfn` doit porter ce numero,
/// et un scan trie par ordre alphabetique rendrait la correspondance fragile.
///
/// Les trous entre la fin de l'archive d'origine et nos numeros sont remplis par des
/// entrees vides : `fsOpen` les refuse (`size == 0`), personne ne les demande.
static void ajouter_fichiers_du_disque(void) {
    char* dossier = Resources_GetPath("stages");
    if (dossier == NULL) {
        return;
    }

    int nb = 0;
    char** noms = SDL_GlobDirectory(dossier, "*.bin", SDL_GLOB_CASEINSENSITIVE, &nb);
    if (noms == NULL) {
        SDL_free(dossier);
        return;
    }

    for (int i = 0; i < nb; i++) {
        char* fin = NULL;
        const long num = SDL_strtol(noms[i], &fin, 10);
        if (fin == noms[i] || num < 0 || num > 65535) {
            _log("stages/%s : le nom n'est pas un numero de fichier, ignore", noms[i]);
            continue;
        }

        char chemin[1024];
        SDL_snprintf(chemin, sizeof(chemin), "%s/%s", dossier, noms[i]);

        SDL_IOStream* io = SDL_IOFromFile(chemin, "rb");
        if (io == NULL) {
            _log("stages/%s : ouverture impossible, ignore", noms[i]);
            continue;
        }

        const Sint64 taille = SDL_GetIOSize(io);
        if (taille <= 0) {
            SDL_CloseIO(io);
            continue;
        }

        // `afs.entries` vient d'un `SDL_calloc`, pas de stb_ds : on l'agrandit a la main
        // et on met les nouvelles entrees a zero -- une entree de taille nulle est
        // refusee par `fsOpen`, ce qui est le comportement voulu pour un trou.
        if ((size_t)num >= afs.entry_count) {
            const size_t neuf = (size_t)num + 1;
            AFSEntry* agrandi = SDL_realloc(afs.entries, neuf * sizeof(AFSEntry));
            if (agrandi == NULL) {
                SDL_CloseIO(io);
                continue;
            }
            SDL_memset(agrandi + afs.entry_count, 0, (neuf - afs.entry_count) * sizeof(AFSEntry));
            afs.entries = agrandi;
            afs.entry_count = neuf;
        }

        AFSEntry* e = &afs.entries[num];
        if (e->io != NULL) {
            SDL_CloseIO(e->io);
        }
        e->offset = 0;
        e->size = (size_t)taille;
        e->io = io;
        SDL_snprintf(e->name, sizeof(e->name), "%s", noms[i]);
        SDL_Log("[stages] %s -> fichier %ld, %lld octets", noms[i], num, (long long)taille);
    }

    SDL_free(noms);
    SDL_free(dossier);
}

bool AFS_Init(const char* file_path, size_t read_chunk_size) {
    SDL_assert(read_chunk_size > 0);
    _read_chunk_size = read_chunk_size;

    if (!init_afs(file_path)) {
        return false;
    }

    ajouter_fichiers_du_disque();
    return true;
}

void AFS_Finish() {
    for (size_t i = 0; i < afs.entry_count; i++) {
        if (afs.entries[i].io != NULL) {
            SDL_CloseIO(afs.entries[i].io);
            afs.entries[i].io = NULL;
        }
    }

    SDL_CloseIO(stream);
    stream = NULL;
    SDL_free(afs.file_path);
    SDL_free(afs.entries);
    SDL_zero(afs);
    arrfree(requests);
}

size_t AFS_GetFileCount() {
    return afs.entry_count;
}

size_t AFS_GetSize(size_t file_num) {
    if (file_num >= afs.entry_count) {
        return 0;
    }

    return afs.entries[file_num].size;
}

// AFS reading

static int find_free_request_slot() {
    for (int i = 0; i < arrlen(requests); i++) {
        if (!requests[i].initialized) {
            return i;
        }
    }

    return arraddnindex(requests, 1);
}

static void read_into_request(ReadRequest* request, size_t max_read) {
    const AFSEntry* entry = &afs.entries[request->file_num];
    // Une entree ajoutee depuis `resources/stages/` a son propre flux et commence a 0.
    SDL_IOStream* io = (entry->io != NULL) ? entry->io : stream;
    const Sint64 offset = entry->offset + request->bytes_read;
    SDL_SeekIO(io, offset, SDL_IO_SEEK_SET);

    const size_t bytes_to_read = SDL_min(request->bytes_to_read, max_read);
    const size_t bytes_read = SDL_ReadIO(io, request->buf + request->bytes_read, bytes_to_read);

    request->bytes_read += bytes_read;
    request->bytes_to_read -= bytes_read;

    if (request->bytes_to_read == 0) {
        request->state = AFS_READ_STATE_FINISHED;
    }
}

void AFS_RunServer() {
    int running_requests = 0;

    for (int i = 0; i < arrlen(requests); i++) {
        if (requests[i].state == AFS_READ_STATE_READING) {
            running_requests += 1;
        }
    }

    if (running_requests <= 0) {
        return;
    }

    const size_t max_read_per_request = _read_chunk_size / running_requests;

    for (int i = 0; i < arrlen(requests); i++) {
        ReadRequest* request = &requests[i];

        if (request->state != AFS_READ_STATE_READING) {
            continue;
        }

        read_into_request(request, max_read_per_request);
    }
}

AFSHandle AFS_Open(size_t file_num) {
    if (file_num >= afs.entry_count) {
        return AFS_NONE;
    }

    const int index = find_free_request_slot();
    ReadRequest* request = &requests[index];

    request->file_num = file_num;
    request->bytes_to_read = afs.entries[file_num].size;
    request->bytes_read = 0;
    request->buf = NULL;
    request->state = AFS_READ_STATE_IDLE;
    request->initialized = true;

    _log("Open %s (file_num = %d)", afs.entries[file_num].name, file_num);
    return index;
}

void AFS_Read(AFSHandle handle, void* buf) {
    ReadRequest* request = &requests[handle];
    _log("Read %s (bytes = 0x%X)", afs.entries[request->file_num].name, request->bytes_to_read);
    SDL_assert(request->buf == NULL);
    SDL_assert(request->state == AFS_READ_STATE_IDLE);
    request->buf = buf;
    request->state = AFS_READ_STATE_READING;
}

void AFS_ReadSync(AFSHandle handle, void* buf) {
    ReadRequest* request = &requests[handle];
    _log("Read (sync) %s", afs.entries[request->file_num].name);
    AFS_Read(handle, buf);
    read_into_request(request, request->bytes_to_read);
    SDL_assert(request->state == AFS_READ_STATE_FINISHED);
}

void AFS_Stop(AFSHandle handle) {
    ReadRequest* request = &requests[handle];
    _log("Stop %s", afs.entries[request->file_num].name);
    request->state = AFS_READ_STATE_IDLE;
}

void AFS_Close(AFSHandle handle) {
    ReadRequest* request = &requests[handle];
    _log("Close %s", afs.entries[request->file_num].name);
    SDL_zerop(request);
}

AFSReadState AFS_GetState(AFSHandle handle) {
    return requests[handle].state;
}
