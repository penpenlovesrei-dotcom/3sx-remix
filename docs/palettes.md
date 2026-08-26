# Palette sets

3SX can dress the cast and the stages in colours of your own. A set is a folder of files, each one
standing in for a palette the game would have read out of `SF33RD.AFS`, so nothing has to know a
new format.

Two sets ship with the mod — New Generation and 2nd Impact, captured from the arcade ROMs — and a
third, `color-edit`, is written by the [in-game editor](color_edit.md).

## Installing a set

One folder per set under `pal_remix`, in your [resources](resources.md) folder:

```
resources/
├── SF33RD.AFS
└── pal_remix/
    ├── new-generation/
    │   ├── char-02.pal          Ryu
    │   └── char-11.pal          Ken
    ├── 2nd-impact/
    │   └── ...
    ├── color-edit/              written by COLOR EDIT MODE
    │   └── ...
    └── rethird/
        └── stage-11.pal         Ken's stage
```

Files are numbered in the **engine's** order, which `constants.h` lists — not the alphabetical
order the menus show. A set needs no file for every character: one is enough, and anyone it does
not cover keeps the game's own colours.

Folders are read the first time a palette is asked for, so a set added while the game is running
is picked up without a restart.

## The file

A `.pal` is the archive entry, byte for byte. `init_trans_color_ram` reads it with the layout it
already uses:

| | |
|---|---|
| Layout | `u16 col[28][64]` — 28 palettes of 64 colours |
| Rows 0-15 | the coloris, one per colour button; see below |
| Rows 16-21 | the six palettes that character's own effects draw from |
| Rows 22-25 | the portrait, read as one run of 256 |
| Colours | ARGB1555, alpha in the top bit |
| Size | 3584 bytes, or **7168 for Gill** |

Gill is the only character carrying two banks — his mirrored side is a different palette rather
than a copy — so his file is twice the size. A file shorter than its character needs is refused
with a warning rather than read past its end.

A stage's block has no fixed length: stages run from 6 palettes to 128, and the replacement
carries its own, however many it holds.

### Which row is which colour

Set by the button that picks it at the character select, as `Setup_PL_Color` reads it:

| Row | Button | Row | Button |
|---|---|---|---|
| 0-5 | LP, MP, HP, LK, MK, HK | 7-12 | Start held with each of the six |
| 6 | LP+HP+MK | 13-15 | nothing reaches these |

New Generation filled six of them, 2nd Impact seven — the seventh on **HP+LK** on that game's own
board, which is row 6 here.

## Choosing a set in game

**Options → Display → CHAR. COLOR** settles how a set gets picked, not which one:

| | |
|---|---|
| `Disabled` | the game's own colours throughout |
| `Custom` | one set per fighter, from the per-character screen that row opens |
| `Start Button` | each side picks its own at the character select |

In `Start Button`, the set each player is on is named in the corner of the character select — the
blue line the PRESS START messages use — and Start steps it: 3rd Strike, New Generation, 2nd
Impact, Custom, Color Edit. Alone, that line sits bottom left; with two players it moves to top
left and player two takes bottom right. A stop with nothing installed behind it is drawn at half
brightness.

**Options → Display → BACKGROUNDS** does the same for stages, with a per-stage screen of its own.

A set that has no file for a fighter is not offered to that fighter: New Generation never had
Makoto, and her row must not promise a set that cannot dress her.

## Making a set

The colours are ARGB1555 as the console stores them. Three conversions turn up in practice and are
easy to confuse — getting one wrong passes every numeric check and turns skin blue:

| Source | Form |
|---|---|
| Console archive | ARGB1555 little-endian, **red in the high bits** |
| CPS3 arcade RAM | xBGR555 big-endian, **blue in the high bits** — swap R and B *and* the byte order |
| `.act` swatch files | RGB 8 bits, narrowed by `round(v * 31 / 255)` |

`ColorRAM` holds a fourth arrangement — `palConvSrcToRam` puts red in the low bits — so anything
reading colours back out of memory converts again on the way. `palConvRamToSrc` is the way back.

Indexed GIFs from colour-reference sites are an exact source rather than a likeness: their colour
table **is** the game's palette, in the game's order, widened to 8 bits. Watch for images that
have been re-optimised, which rebuilds the table: the colours survive, the order does not, and the
signature is index-by-index agreement collapsing while overall agreement stays high.

## Known limits

**Ibuki's stage sky** does not follow a replacement. The loader works — a magenta file turns the
whole stage magenta *except* the sky — so that sky is painted from outside the `ColorRAM[300]`
block. Ruled out so far: the backdrop layers, the texture group palettes, the colour transition
system, and the ROM, the last by 62 identical palette captures between stock and patched ROMs.
