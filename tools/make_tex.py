#!/usr/bin/env python3
"""Build a `.tex` replacement page for tex_remix, from any image Pillow can read.

A page is recognised by a fingerprint of its contents, printed by the game into
`<resources>/tex_remix/dump/manifest.txt` when `tex-remix-dump` is on. Name the output after the
page you mean to replace and drop it in `<resources>/tex_remix/`:

    python tools/make_tex.py ryu_hd.png --key 3f2a91c40b7e5d18 --scale 4 --page 256x256
    -> 3f2a91c40b7e5d18.tex, 1024x1024

The size must be a whole multiple of the page it replaces, so each original pixel keeps the same
number of new ones; give either --scale with --page, or --size outright. The image is fitted to that
size, and anything it does not cover is left transparent.
"""

import argparse
import struct
import sys
from pathlib import Path

from PIL import Image

MAGIC = b"3STX"
VERSION = 1


def parse_size(text):
    w, _, h = text.lower().partition("x")
    return int(w), int(h)


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("image", type=Path, help="source image, any format Pillow reads (PNG, DDS, ...)")
    p.add_argument("--key", required=True, help="16 hex digits, from the dump manifest")
    p.add_argument("--page", type=parse_size, help="size of the page being replaced, e.g. 256x256")
    p.add_argument("--scale", type=int, default=4, help="multiple of the page size (default 4)")
    p.add_argument("--size", type=parse_size, help="output size outright, instead of --page/--scale")
    p.add_argument("--out-dir", type=Path, default=Path("."), help="where to write the .tex")
    p.add_argument("--fit", choices=("stretch", "contain"), default="contain",
                   help="contain keeps the aspect ratio and centres (default), stretch fills")
    args = p.parse_args()

    if args.size:
        width, height = args.size
    elif args.page:
        width, height = args.page[0] * args.scale, args.page[1] * args.scale
    else:
        p.error("give --page (with --scale) or --size")

    key = args.key.lower().removesuffix(".tex")
    if len(key) != 16 or any(c not in "0123456789abcdef" for c in key):
        p.error(f"--key must be 16 hex digits, got {args.key!r}")

    source = Image.open(args.image).convert("RGBA")
    canvas = Image.new("RGBA", (width, height), (0, 0, 0, 0))

    if args.fit == "stretch":
        canvas = source.resize((width, height), Image.LANCZOS)
    else:
        scaled = source.copy()
        scaled.thumbnail((width, height), Image.LANCZOS)
        canvas.paste(scaled, ((width - scaled.width) // 2, (height - scaled.height) // 2))

    out = args.out_dir / f"{key}.tex"
    with open(out, "wb") as f:
        f.write(MAGIC)
        f.write(struct.pack("<III", VERSION, width, height))
        f.write(canvas.tobytes())

    print(f"{out}: {width}x{height}, {out.stat().st_size} bytes")
    return 0


if __name__ == "__main__":
    sys.exit(main())
