# Texture replacement

Any texture page the game loads can be swapped for a larger one. Drop `.tex` files in
`<resources>/tex_remix/` and they are picked up at load time.

This is what [`render-scale`](config.md#render-scale) exists for: a replacement has nowhere to show
its detail until the frame is bigger than 384x224. Set both, or you gain nothing.

## Finding what to replace

A page has no name. It is a nameless block inside an archive entry, so a replacement is matched by a
fingerprint of the page's own contents. Turn `tex-remix-dump` on in the config and play through the
screens you care about:

```
tex-remix-dump = true
```

Every page is written once to `<resources>/tex_remix/dump/`:

- `manifest.txt` — one line per page: fingerprint, size, bits per pixel, and where it was loaded
  from — `page` is the number the game asked for, `list` the base its texture list numbers from, and
  `entry` the archive entry it was decompressed out of.
- `<fingerprint>.pgm` — the page as a greyscale image.

The greyscale is the page's *index values*, not its colours: the palette that would turn those into a
picture lives elsewhere and does not belong to the page. Shapes, lettering and artwork are perfectly
recognisable that way, which is all the dump is for.

Only the fingerprint names a replacement. The page number is there to be read the other way: it is
the number the drawing code works in — `seqsStoreChip` reaches a page as `gix + (code >> 8)` — so a
page you can see in the dump can be traced back to the code that draws it. `list` matters because
each texture list numbers its own pages from its own base and those ranges overlap; two lines with
the same `page` but a different `list` are different pages.

The same fingerprint can appear on more than one line, under different page numbers. That is the
game loading identical pixels through two routes, and only the first line writes a `.pgm`.

To find which page draws which part of a screen without reading any code, write a flat colour into
each one, run the game and look: whatever changes colour is that page. Screens are built from a
handful of pages, so this answers the question in one pass.

## Building a replacement

```
python tools/make_tex.py artwork.png --key 3f2a91c40b7e5d18 --page 256x256 --scale 4
```

The size must be a whole multiple of the page it replaces. Any size would land in the right places —
sprites are cut out of a page in fractions of its width, so the cuts follow whatever size the page
is — but a whole multiple is the only way each original pixel keeps the same number of new ones,
which is what stops lettering from wobbling along a row.

The container is `3STX`, a version, width, height, then rows of RGBA. No compression: there is no
image decoder in this build, and a page has no business carrying one the game would have to undo at
load time.

## What a replacement gives up

A page arriving with 4 or 8 bits per pixel is drawn through a palette, and the game animates some of
those — flashes, fades to white, the colour cycling on a few HUD pieces. A replacement is plain
colour and keeps none of that. Artwork and lettering never move their palettes and lose nothing;
think twice before replacing anything that flashes.

## Memory

The texture pool is the console's, 10 MB, and a 1024x1024 replacement is 4 MB of it — one page is
enough to exhaust it. The pool is grown at startup by the size of whatever is installed, so a machine
with no replacements keeps exactly the footprint it always had, and a large pack costs its own size
in ordinary memory. Nothing else is needed.
