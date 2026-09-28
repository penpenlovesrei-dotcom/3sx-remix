#include "port/utils.h"

#if _WIN32
#define WIN32_LEAN_AND_MEAN
#include <windows.h>

#include <dbghelp.h>
#define SYMBOL_NAME_MAX 256
#elif __APPLE__ || linux
#include <execinfo.h>
#include <signal.h>
#include <unistd.h>
#endif

#include <stdarg.h>
#include <stdio.h>
#include <stdlib.h>

#define BACKTRACE_MAX 100

void fatal_error(const char* fmt, ...) {
    va_list args;
    va_start(args, fmt);

    fprintf(stderr, "Fatal error: ");
    vfprintf(stderr, fmt, args);
    fprintf(stderr, "\n");

    va_end(args);

#if __APPLE__ || linux
    void* buffer[BACKTRACE_MAX];

    int nptrs = backtrace(buffer, BACKTRACE_MAX);
    fprintf(stderr, "Stack trace:\n");
    backtrace_symbols_fd(buffer, nptrs, fileno(stderr));
#elif _WIN32
    void* buffer[BACKTRACE_MAX];

    fprintf(stderr, "Stack trace:\n");
    HANDLE process = GetCurrentProcess();
    SymInitialize(process, NULL, TRUE);
    int nptrs = CaptureStackBackTrace(0, BACKTRACE_MAX, buffer, NULL);
    SYMBOL_INFO* symbol = (SYMBOL_INFO*)calloc(1, sizeof(SYMBOL_INFO) + SYMBOL_NAME_MAX);

    if (!symbol) {
        fprintf(stderr, "Calloc failed when allocating SYMBOL_INFO, bailing!\n\n");
        SymCleanup(process);
        abort();
    }

    symbol->MaxNameLen = SYMBOL_NAME_MAX;
    symbol->SizeOfStruct = sizeof(SYMBOL_INFO);

    for (int i = 0; i < nptrs; i++) {
        SymFromAddr(process, (DWORD64)buffer[i], 0, symbol);
        fprintf(stderr, "%i: %s - 0x%0llX\n", nptrs - i - 1, symbol->Name, symbol->Address);
    }

    free(symbol);
    SymCleanup(process);
#endif

    abort();
}

/* UN PLANTAGE DUR MOURAIT MUET -- 24/09/2026.

   `fatal_error` ne sert que sur les chemins que le jeu connait (`flLogOut`, les gels).
   Une VRAIE faute de memoire, elle, n'avait aucun gestionnaire : le processus disparaissait
   sans une ligne, et le journal s'arretait sur la derniere chose qu'il avait eu le temps
   d'ecrire. C'est ce qui s'est passe a l'entree de l'etage 39, et ca n'a rien appris.

   Windows laisse poser un dernier recours. Il reutilise le meme dumpeur de symboles que
   `fatal_error`, donc la trace aura la meme forme -- et le lanceur la trouvera dans
   `fatal.log` comme les autres. */
#if _WIN32
static LONG WINAPI dernier_recours(EXCEPTION_POINTERS* info) {
    {
        /* L'ADRESSE SEULE NE DIT RIEN : Windows deplace l'image a chaque lancement.
           On donne l'ECART au debut du module, et l'adresse que les symboles de
           l'executable portent (base preferee 0x140000000) -- `nm` la resout. */
        char* base = (char*)GetModuleHandleA(NULL);
        char* ou = (char*)info->ExceptionRecord->ExceptionAddress;

        fatal_error("plantage dur : code 0x%08lX, ecart 0x%llX, symbole 0x%llX",
                    (unsigned long)info->ExceptionRecord->ExceptionCode,
                    (unsigned long long)(ou - base),
                    (unsigned long long)(0x140000000ULL + (ou - base)));
    }
    return EXCEPTION_EXECUTE_HANDLER;
}
#endif

void install_crash_handler(void) {
#if _WIN32
    SetUnhandledExceptionFilter(dernier_recours);
#endif
}

void not_implemented(const char* func) {
    fatal_error("Function not implemented: %s\n", func);
}

void debug_print(const char* fmt, ...) {
#if DEBUG
    va_list args;
    va_start(args, fmt);
    vfprintf(stdout, fmt, args);
    fprintf(stdout, "\n");
    va_end(args);
#endif
}
