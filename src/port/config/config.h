#ifndef PORT_CONFIG_H
#define PORT_CONFIG_H

#include <stdbool.h>

#define CFG_KEY_FULLSCREEN "fullscreen"
#define CFG_KEY_WINDOW_WIDTH "window-width"
#define CFG_KEY_WINDOW_HEIGHT "window-height"
#define CFG_KEY_SCALEMODE "scale-mode"
#define CFG_KEY_SCANLINES "scanlines"
/// How many pixels per side the 384x224 screen is rendered into, so 4 draws a 1536x896 frame. The
/// game's own art gains nothing from it -- it is what gives HD replacements somewhere to be seen.
/// Read once at startup.
#define CFG_KEY_RENDER_SCALE "render-scale"
/// Write every texture page the game loads to `<resources>/tex_remix/dump/`, which is how you find
/// the key to name a replacement after. Costs a file write per new page, nothing per frame.
#define CFG_TEX_REMIX_DUMP "tex-remix-dump"
/// Outline the box the character select portraits' chips cover, the portraits still drawing inside
/// it. Says whether a replacement drawn on that box would land in the right place -- a question no
/// numeric check can answer, and one a frame around the art answers at a glance.
#define CFG_ART_REMIX_BOXES "art-remix-boxes"
/// Starting BGM and SE levels, on the sound menu's own scale: 0 silences, 15 is Standard, and the
/// values between are the decibel trims that menu names, so 11 is its -4. The game only ever
/// applied a saved sound setting when the Sound menu was opened, which left every session starting
/// at Standard whatever had been chosen; these say what to start at instead.
#define CFG_KEY_BGM_LEVEL "bgm-level"
#define CFG_KEY_SE_LEVEL "se-level"
#define CFG_DRAW_PLAYERS_ABOVE_HUD "draw-players-above-hud"
#define CFG_ARCADE_BALANCE "arcade-balance"

/// Initialize config system
void Config_Init();

/// Destroy resources used by config system
void Config_Destroy();

/// Get the value associated with the given key as a `bool`
/// @return The value associated with `key` if `key` is among entries and the value's type is `bool`, `false` otherwise
bool Config_GetBool(const char* key);

/// Get the value associated with the given key as an `int`
/// @return The value associated with `key` if `key` is among entries and the value's type is `int`, `0` otherwise
int Config_GetInt(const char* key);

/// Get the value associated with the given key as a `string`
/// @return The value associated with `key` if `key` is among entries and the value's type is `string`, `NULL` otherwise
const char* Config_GetString(const char* key);

#endif
