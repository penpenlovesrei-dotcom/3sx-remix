/**
 * @file canvas.c
 * Size of the off-screen surface a frame is rendered into, before it is scaled to the window.
 *
 * The game draws for a 384x224 screen and always will: that is the space its layouts, its clipping
 * tests and its collision-free menu columns are written in. What the backends are free to choose is
 * how many real pixels one of those 384x224 pixels lands on, because every vertex reaches them
 * already divided by that screen -- `convert_to_screen_x` and its kin hand the GPU clip space, not
 * pixels. Enlarging the canvas therefore rasterises the very same geometry more finely, without a
 * single drawing call knowing about it.
 *
 * On its own that buys nothing to look at. Detail comes from the textures, which are still the
 * game's own and still sampled point-blank, so a larger canvas only stops being an expensive way to
 * draw the same picture once HD replacements are fed to it. This is the half that has to exist
 * first: assets have nowhere to show their detail until the frame is bigger than 384x224.
 */

#include "port/video/canvas.h"
#include "port/config/config.h"

#include <SDL3/SDL.h>

static int scale = 0;

int Canvas_Scale(void) {
    if (scale == 0) {
        const int configured = Config_GetInt(CFG_KEY_RENDER_SCALE);
        scale = SDL_clamp(configured, 1, CANVAS_SCALE_MAX);

        if (scale != configured) {
            SDL_Log("Ignoring render-scale %d, using %d", configured, scale);
        }

        if (scale > 1) {
            SDL_Log("Rendering to a %dx%d canvas (render-scale %d)", Canvas_Width(), Canvas_Height(), scale);
        }
    }

    return scale;
}

int Canvas_Width(void) {
    return CANVAS_BASE_WIDTH * Canvas_Scale();
}

int Canvas_Height(void) {
    return CANVAS_BASE_HEIGHT * Canvas_Scale();
}
