#!/usr/bin/env python3
"""Build a `.tex` character select portrait for art_remix, from any image Pillow can read.

Unlike a texture page, a portrait is not matched by a fingerprint: it is never in memory as one
picture, so there is nothing to fingerprint. It is named after the select screen's face number
instead, and drawn over the box the original's chips covered.

    python tools/make_art.py "Assets HD/204_Chun-Li.dds" --face 7
    -> face-07.tex, 1040x692

    python tools/make_art.py "Assets HD/204_Chun-Li.dds" --any
    -> any.tex, standing in for every face that has no file of its own

Any size is allowed: the picture is stretched onto the box, not cut into it. Drop the result in
`<resources>/art_remix/`.
"""

import argparse
import struct
import sys
from pathlib import Path

from PIL import Image, ImageEnhance

MAGIC = b"3STX"
VERSION = 1


def main():
    p = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    p.add_argument("image", type=Path, help="source image, any format Pillow reads (DDS, PNG, ...)")
    group = p.add_mutually_exclusive_group(required=True)
    group.add_argument("--face", type=int, help="face number on the select screen")
    group.add_argument("--any", action="store_true", help="write any.tex, the stand-in for every face")
    p.add_argument("--out-dir", type=Path, default=Path("."), help="where to write the .tex")
    p.add_argument("--saturation", type=float, default=1.0,
                   help="colour boost, 1.0 leaves it alone. The Online Edition redraws are softer than "
                        "the pixel art they replace, which the renderer cannot fix -- it draws the file "
                        "exactly -- so it is corrected here or not at all")
    p.add_argument("--contrast", type=float, default=1.0, help="contrast boost, 1.0 leaves it alone")
    p.add_argument("--max-width", type=int, default=0, help="shrink if wider than this, keeping the aspect")
    p.add_argument("--squash", action="store_true",
                   help="squash to 7/9 height. The Online Edition portraits are already in the game's "
                        "squashed space -- they are exact 10/3 upscales of its own sprites -- so this is "
                        "only for artwork drawn somewhere else, at true proportions")
    args = p.parse_args()

    image = Image.open(args.image).convert("RGBA")

    if args.max_width and image.width > args.max_width:
        height = round(image.height * args.max_width / image.width)
        image = image.resize((args.max_width, height), Image.LANCZOS)

    # The game draws a 384x224 buffer onto a 4:3 screen, so everything it holds is squashed to 7/9
    # of its true height and stretched back on the way out. Its own art is drawn that way, and so
    # are the Online Edition portraits, which measure exactly 10/3 of the sprites they redraw on
    # both axes. Artwork from anywhere else has to be squashed to match.
    if args.squash:
        image = image.resize((image.width, round(image.height * 7 / 9)), Image.LANCZOS)

    # Applied to the colours only; the alpha is put back untouched, or a boost would eat the cut-out.
    if args.saturation != 1.0 or args.contrast != 1.0:
        alpha = image.getchannel("A")
        rgb = image.convert("RGB")
        rgb = ImageEnhance.Color(rgb).enhance(args.saturation)
        rgb = ImageEnhance.Contrast(rgb).enhance(args.contrast)
        image = rgb.convert("RGBA")
        image.putalpha(alpha)

    name = "any.tex" if args.any else f"face-{args.face:02d}.tex"
    args.out_dir.mkdir(parents=True, exist_ok=True)
    out = args.out_dir / name

    with open(out, "wb") as f:
        f.write(MAGIC)
        f.write(struct.pack("<III", VERSION, image.width, image.height))
        f.write(image.tobytes())

    print(f"{out}, {image.width}x{image.height}, {out.stat().st_size // 1024} KB")


if __name__ == "__main__":
    sys.exit(main())
