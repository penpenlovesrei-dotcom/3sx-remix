# Config

3SX supports a config file which allows you to change several useful options.

Config location:
- **Windows**: `C:\Users\<username>\AppData\Roaming\CrowdedStreet\3SX\config`
- **Linux**: `~/.local/share/CrowdedStreet/3SX/config`
- **macOS**: `~/Library/Application Support/CrowdedStreet/3SX/config`

## Options

### `fullscreen`

Whether the game should start in fullscreen mode.

### `window-width` / `window-height`

Window dimensions to use when `fullscreen` is set to `false`.

### `scale-mode`

The way the internal 384x224 buffer is scaled.

#### `nearest` (default)

Produces sharp pixels at the cost of sizing consistency.

#### `integer`

Produces a pixel-perfect image, but requires a 4K display.

> [!WARNING] 
> The image is gonna be cropped if your display resolution is smaller than 2688x2016.

#### `square-pixels`

The internal buffer is scaled up by an integer (whole number) factor. Use this if you play on a CRT

### `render-scale`

How many pixels per side the internal 384x224 buffer is rendered into, from `1` (default) to `8`. At
`4` the frame is drawn at 1536x896 before being scaled to the window.

The game's own artwork gains nothing from this: it is drawn from textures that hold no more detail
at `4` than at `1`, and the picture only stops being scaled up somewhere else. What the setting does
is give HD replacement assets somewhere to be seen, since nothing can show more than 384x224 worth
of detail until the frame itself is bigger.

Positions, layouts and the scanline filter keep counting in 384x224 whatever this is set to, so
nothing moves. Read once at startup.

### `tex-remix-dump`

Write every texture page the game loads to `<resources>/tex_remix/dump/`, which is how you find out
what a screen is made of and what to name a replacement after. See
[texture replacement](tex_remix.md). Costs a file write per new page, nothing per frame.

### `scanlines`

Defines the strength of the scanline filter (from `0` to `100`). `0` means the filter is disabled.

### `draw-players-above-hud`

Allow characters to render in front of the top HUD similar to Street Fighter IV.

> [!NOTE]
> With this setting on these stage decorations will be disabled to prevent overlapping with HUD:
> - Chun-Li's stage: Bamboo stick on the right
> - Makoto's stage: Tree on the right
> - Yang's stage: Rain overlay

### `arcade-balance`

Enables arcade balance instead of PS2 balance. 

> [!IMPORTANT]
> Requires `sfiii3nr1.zip` to be present in [`resources`](resources.md) directory.

> [!WARNING]
> Arcade balance is a work-in-progress. Expect bugs, crashes and instability when enabling this feature.
