/**
 * @brief Render dispatch through the appropriate host render backend.
 */

#include "core/renderer.h"

#if CRS_VIDEO_DRIVER_SDL_GENERIC
#include "args.h"
#include "port/video/tex_remix.h"

#include "platform/video/sdl_generic/sdl_generic_renderer.h"
#elif CRS_VIDEO_DRIVER_PSP
#include "platform/video/psp/psp_renderer.h"
#endif

#if CRS_VIDEO_DRIVER_SDL_GENERIC
static bool skip_rendering() {
#if STATCHECK
    return get_args()->statcheck.headless;
#elif NETPLAY_ENABLED
    return get_args()->netplay.stress;
#else
    return false;
#endif
}
#endif

void Renderer_CreateTexture(unsigned int th) {
#if CRS_VIDEO_DRIVER_SDL_GENERIC
    if (skip_rendering()) {
        return;
    }

    SDLGenericRenderer_CreateTexture(th);
#elif CRS_VIDEO_DRIVER_PSP
    PSPRenderer_CreateTexture(th);
#endif
}

void Renderer_DestroyTexture(unsigned int texture_handle) {
#if CRS_VIDEO_DRIVER_SDL_GENERIC
    if (skip_rendering()) {
        return;
    }

    SDLGenericRenderer_DestroyTexture(texture_handle);
#elif CRS_VIDEO_DRIVER_PSP
    PSPRenderer_DestroyTexture(texture_handle);
#endif
}

void Renderer_UnlockTexture(unsigned int th) {
#if CRS_VIDEO_DRIVER_SDL_GENERIC
    if (skip_rendering()) {
        return;
    }

    SDLGenericRenderer_UnlockTexture(th);
#elif CRS_VIDEO_DRIVER_PSP
    PSPRenderer_UnlockTexture(th);
#endif
}

void Renderer_CreatePalette(unsigned int ph) {
#if CRS_VIDEO_DRIVER_SDL_GENERIC
    if (skip_rendering()) {
        return;
    }

    SDLGenericRenderer_CreatePalette(ph);
#elif CRS_VIDEO_DRIVER_PSP
    PSPRenderer_CreatePalette(ph);
#endif
}

void Renderer_DestroyPalette(unsigned int palette_handle) {
#if CRS_VIDEO_DRIVER_SDL_GENERIC
    if (skip_rendering()) {
        return;
    }

    SDLGenericRenderer_DestroyPalette(palette_handle);
#elif CRS_VIDEO_DRIVER_PSP
    PSPRenderer_DestroyPalette(palette_handle);
#endif
}

void Renderer_UnlockPalette(unsigned int th) {
#if CRS_VIDEO_DRIVER_SDL_GENERIC
    if (skip_rendering()) {
        return;
    }

    SDLGenericRenderer_UnlockPalette(th);
#elif CRS_VIDEO_DRIVER_PSP
    PSPRenderer_UnlockPalette(th);
#endif
}

void Renderer_SetTexture(unsigned int th) {
#if CRS_VIDEO_DRIVER_SDL_GENERIC
    if (skip_rendering()) {
        return;
    }

    SDLGenericRenderer_SetTexture(th);
#elif CRS_VIDEO_DRIVER_PSP
    PSPRenderer_SetTexture(th);
#endif
}

void Renderer_DrawTexturedQuad(const Sprite* sprite, unsigned int color) {
#if CRS_VIDEO_DRIVER_SDL_GENERIC
    if (skip_rendering()) {
        return;
    }

    // Corners 0 and 3 are the diagonal pair everywhere in this renderer.
    TexRemix_NoteQuad(sprite->t[0].s, sprite->t[0].t, sprite->t[3].s, sprite->t[3].t);
    SDLGenericRenderer_DrawTexturedQuad(sprite, color);
#elif CRS_VIDEO_DRIVER_PSP
    PSPRenderer_DrawTexturedQuad(sprite, color);
#endif
}

void Renderer_DrawSprite(const Sprite* sprite, unsigned int color) {
#if CRS_VIDEO_DRIVER_SDL_GENERIC
    if (skip_rendering()) {
        return;
    }

    TexRemix_NoteQuad(sprite->t[0].s, sprite->t[0].t, sprite->t[3].s, sprite->t[3].t);
    SDLGenericRenderer_DrawSprite(sprite, color);
#elif CRS_VIDEO_DRIVER_PSP
    PSPRenderer_DrawSprite(sprite, color);
#endif
}

void Renderer_DrawSprite2(const Sprite2* sprite2) {
#if CRS_VIDEO_DRIVER_SDL_GENERIC
    if (skip_rendering()) {
        return;
    }

    TexRemix_NoteQuad(sprite2->t[0].s, sprite2->t[0].t, sprite2->t[1].s, sprite2->t[1].t);
    SDLGenericRenderer_DrawSprite2(sprite2);
#elif CRS_VIDEO_DRIVER_PSP
    PSPRenderer_DrawSprite2(sprite2);
#endif
}

void Renderer_DrawSolidQuad(const Quad* quad, unsigned int color) {
#if CRS_VIDEO_DRIVER_SDL_GENERIC
    if (skip_rendering()) {
        return;
    }

    SDLGenericRenderer_DrawSolidQuad(quad, color);
#elif CRS_VIDEO_DRIVER_PSP
    PSPRenderer_DrawSolidQuad(quad, color);
#endif
}
