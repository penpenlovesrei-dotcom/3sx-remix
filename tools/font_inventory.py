#!/usr/bin/env python3
"""Inventaire des glyphes des polices de 3SX, lu dans SF33RD.AFS.

Repond a une seule question : qu'est-ce que le jeu sait dessiner comme lettres, et donc
quelles langues une traduction peut viser sans toucher aux assets.

Deux polices repondent differemment, et c'est tout l'interet de l'inventaire :

  * la police des messages (groupe 38, fichier AFS 1458) -- dialogues, fins, citations de
    victoire, tables systeme/extra/menu. Adressee par des jetons de texte que effb6.c
    convertit en numeros d'objet. Elle contient 48 lettres latines accentuees.

  * les deux jeux de lettres des menus (groupe 23, fichier AFS 1454) -- eff61.c, eff64.c,
    eff51.c, eff63.c ecrivent `chr = base + octet`, donc l'octet ASCII brut sert d'index.
    96 glyphes chacun, ASCII 0x20 a 0x7F, et le groupe s'arrete la : aucun accent, et pas
    un numero d'objet de libre pour en ajouter.

Sortie : un compte rendu sur la console, et si Pillow est installe, des planches PNG.

    python tools/font_inventory.py                 -> compte rendu seul
    python tools/font_inventory.py --png <dossier> -> compte rendu + planches
"""

import argparse
import os
import re
import struct
import sys

AFS_DEFAULT = os.path.join(
    os.environ.get("APPDATA", ""), "CrowdedStreet", "3SX", "resources", "SF33RD.AFS"
)
EFFB6 = "src/sf33rd/Source/Game/effect/effb6.c"

# texgrpdat[] (texgroup.c) : num_of_1st, apfn, to_tex
GRP_MESSAGE = dict(first=0x7F30, apfn=1458, to_tex=25088)
GRP_MENU = dict(first=0x69E0, apfn=1454, to_tex=134308)

# Les bases que les effets de menu ajoutent a l'octet ASCII
MENU_BASES = [(0x7047, "grande"), (0x70A7, "etroite")]

# Le jeton que effb6.c met partout ou la table ne definit rien
PLACEHOLDER = bytes([0x5E, 0x5F])

# Ce que chaque octet de tete signifie, releve sur les glyphes rendus
ACCENTS = {
    0x25: ("%", "trema"),
    0x29: (")", "aigu"),
    0x28: ("(", "grave"),
    0x5E: ("^", "circonflexe"),
    0x7E: ("~", "tilde"),
    0x2C: (",", "cedille"),
}

# ppgMakeConvTableTexDC (PPGFile.c) : l'ordre entrelace Dreamcast des pixels d'une tuile
_SEED = [0x0000, 0x0002, 0x0008, 0x000A, 0x0020, 0x0022, 0x0028, 0x002A,
         0x0080, 0x0082, 0x0088, 0x008A, 0x00A0, 0x00A2, 0x00A8, 0x00AA,
         0x0200, 0x0202, 0x0208, 0x020A, 0x0220, 0x0222, 0x0228, 0x022A,
         0x0280, 0x0282, 0x0288, 0x028A, 0x02A0, 0x02A2, 0x02A8, 0x02AA]
_SEED_ADD = [0x0000, 0x0004, 0x0010, 0x0014, 0x0040, 0x0044, 0x0050, 0x0054,
             0x0100, 0x0104, 0x0110, 0x0114, 0x0140, 0x0144, 0x0150, 0x0154]

DCTEX = [0] * 0x400
for _i in range(16):
    for _j in range(32):
        DCTEX[_j + _i * 64] = _SEED[_j] + _SEED_ADD[_i]
    for _j in range(32):
        DCTEX[_j + _i * 64 + 32] = DCTEX[_j + _i * 64] + 1


def afs_entry(path, index):
    with open(path, "rb") as f:
        if f.read(4) != b"AFS\x00":
            raise SystemExit("%s n'est pas une archive AFS" % path)
        count = struct.unpack("<I", f.read(4))[0]
        if index >= count:
            raise SystemExit("l'archive n'a que %d entrees" % count)
        f.seek(8 + 8 * index)
        off, size = struct.unpack("<II", f.read(8))
        f.seek(off)
        return f.read(size)


def lz_ext_p6_fx(src, start, length):
    """Transcription directe de lz_ext_p6_fx (mtrans.c)."""
    dst = bytearray()
    p = start
    while len(dst) < length:
        tmp = src[p]
        p += 1
        top = tmp & 0xC0
        if top == 0x00:
            dst.append(tmp)
        elif top == 0x40:
            tmp &= 0x3F
            q = len(dst) - (tmp >> 2) - 1
            for _ in range((tmp & 3) + 2):
                dst.append(dst[q])
                q += 1
        elif top == 0x80:
            tmp = ((tmp & 0x3F) << 8) | src[p]
            p += 1
            q = len(dst) - (tmp >> 6) - 1
            for _ in range((tmp & 0x3F) + 2):
                dst.append(dst[q])
                q += 1
        else:
            flg = tmp & 0x30
            for _ in range((tmp & 0xF) + 2):
                b = src[p]
                p += 1
                dst.append(flg | (b >> 4))
                dst.append(flg | (b & 0xF))
    return bytes(dst[:length])


class Group:
    """Un groupe de textures : sa table de trans en tete, sa table de textures a `to_tex`."""

    def __init__(self, blob, first, to_tex):
        self.d = blob
        self.first = first
        self.to_tex = to_tex
        self.nobj = struct.unpack_from("<I", blob, 0)[0] // 4
        self.offs = list(struct.unpack_from("<%dI" % self.nobj, blob, 0))

    def tiles(self, cg):
        n = cg - self.first
        if n < 0 or n >= self.nobj:
            return None
        o = self.offs[n]
        cnt = struct.unpack_from("<H", self.d, o)[0]
        return [struct.unpack_from("<hhHH", self.d, o + 2 + 8 * k) for k in range(cnt)]

    def tile(self, code):
        p = self.to_tex + struct.unpack_from("<I", self.d, self.to_tex + 4 * code)[0]
        wh = self.d[p]
        side = ((wh & 3) + 1) * 8
        dw = (wh & 0xE0) >> 2
        dh = (wh & 0x1C) * 2
        raw = lz_ext_p6_fx(self.d, p + 1, side * side)
        px = [[raw[DCTEX[j + (i << 5)]] for j in range(side)] for i in range(side)]
        return wh, side, min(dw, side), min(dh, side), px

    def ink(self, cg):
        """Encre totale de l'objet ; None s'il est hors du groupe."""
        ts = self.tiles(cg)
        if ts is None:
            return None
        return sum(sum(1 for r in self.tile(t[3])[4] for v in r if v) for t in ts)


def read_han_tables(root):
    """Les trois jeux de jetons que effb6.c consulte, dans l'ordre de han_adrs[]."""
    src = open(os.path.join(root, EFFB6), encoding="latin-1").read()
    out = []
    for name in ("src_han_kata", "src_han_alpha", "src_han_alpha2"):
        i = src.index("const s8* %s[128] = {" % name)
        j = src.index("};", i)
        items = re.findall(r'"((?:\\x[0-9A-Fa-f]{2})+)"', src[i:j])
        toks = [bytes(int(b, 16) for b in re.findall(r'\\x([0-9A-Fa-f]{2})', it)) for it in items]
        if len(toks) != 128:
            raise SystemExit("%s : %d entrees lues, 128 attendues" % (name, len(toks)))
        out.append((name, toks))
    return out


def token_text(tok):
    s = tok.rstrip(b"\x00")
    return "".join(chr(c) if 32 <= c < 127 else "<%02X>" % c for c in s)


def report(root, afs):
    print("Police des messages -- groupe 38, fichier AFS %d" % GRP_MESSAGE["apfn"])
    grp = Group(afs_entry(afs, GRP_MESSAGE["apfn"]), GRP_MESSAGE["first"], GRP_MESSAGE["to_tex"])
    print("  %d objets, cg 0x%04X a 0x%04X" % (grp.nobj, grp.first, grp.first + grp.nobj - 1))

    tables = read_han_tables(root)
    blank = grp.ink(grp.first + 0)  # han_kata[0] est un emplacement vide : sert de temoin
    for k, (name, toks) in enumerate(tables):
        base = grp.first + k * 128
        reels = [i for i, t in enumerate(toks) if t != PLACEHOLDER]
        vides = [i for i in reels if not grp.ink(base + i)]
        print("  %-15s cg 0x%04X-0x%04X : %3d jetons definis, %d sans dessin"
              % (name, base, base + 127, len(reels), len(vides)))
        if name == "src_han_alpha2":
            par_accent = {}
            for i in reels:
                t = toks[i]
                par_accent.setdefault(t[0], []).append(chr(t[1]))
            print("      atteignable seulement par han_adrs[2], que le chemin anglais n'explore pas")
            for lead, lettres in sorted(par_accent.items()):
                sym, nom = ACCENTS.get(lead, ("?", "?"))
                print("      %s %-12s %2d lettres : %s" % (sym, nom, len(lettres), " ".join(lettres)))

    print()
    print("Lettres des menus -- groupe 23, fichier AFS %d" % GRP_MENU["apfn"])
    grp2 = Group(afs_entry(afs, GRP_MENU["apfn"]), GRP_MENU["first"], GRP_MENU["to_tex"])
    print("  %d objets, cg 0x%04X a 0x%04X" % (grp2.nobj, grp2.first, grp2.first + grp2.nobj - 1))
    for base, nom in MENU_BASES:
        dessines, sans, hors = [], [], []
        for b in range(0x20, 0x100):
            v = grp2.ink(base + b)
            (hors if v is None else sans if v == 0 else dessines).append(b)
        print("  base 0x%04X (%-8s) : %3d octets dessines (0x%02X-0x%02X), %d vides, "
              "%d hors du groupe des 0x%02X"
              % (base, nom, len(dessines), dessines[0], dessines[-1], len(sans),
                 len(hors), hors[0] if hors else 0))
    print("  les deux jeux se suivent : 0x70A7 = 0x7047 + 0x60, et le groupe finit a 0x%04X."
          % (grp2.first + grp2.nobj - 1))
    print("  Il n'y a donc pas un numero d'objet libre apres le 96e glyphe de chaque jeu.")
    return grp, grp2, tables


# ---------------------------------------------------------------- planches PNG

BG = (24, 24, 28)


def shade(v):
    """Les bits 0x30 choisissent la banque de palette, pas l'intensite."""
    if v == 0:
        return BG
    v &= 0x0F
    if v == 0x0F:
        return (0, 0, 0)
    g = 255 - (v - 1) * 18
    return (g, g, g)


def draw_sheet(cells, title, out, scale, cols):
    from PIL import Image, ImageDraw

    cw = max(im.width for _, im in cells) * scale
    ch = max(im.height for _, im in cells) * scale
    pad, lblh = 10, 12
    rows = (len(cells) + cols - 1) // cols
    canvas = Image.new("RGB", (cols * (cw + pad) + pad, rows * (ch + pad + lblh) + pad + 20), BG)
    dr = ImageDraw.Draw(canvas)
    dr.text((pad, 5), title, fill=(255, 255, 255))
    for n, (label, im) in enumerate(cells):
        x = pad + (n % cols) * (cw + pad)
        y = 20 + pad + lblh + (n // cols) * (ch + pad + lblh)
        canvas.paste(im.resize((im.width * scale, im.height * scale), Image.NEAREST), (x, y))
        dr.text((x, y - 10), label, fill=(150, 200, 255))
    canvas.save(out)
    print("  ecrit %s (%dx%d)" % (out, canvas.width, canvas.height))


def cell_image(grp, cg):
    from PIL import Image

    ts = grp.tiles(cg)
    subs, w, h = [], 1, 1
    for _, _, _, code in ts:
        _, side, dw, dh, px = grp.tile(code)
        subs.append((dw, dh, px))
        w, h = max(w, dw), max(h, dh)
    im = Image.new("RGB", (w, h), BG)
    for dw, dh, px in subs:
        sub = Image.new("RGB", (dw, dh))
        sub.putdata([shade(px[y][x]) for y in range(dh) for x in range(dw)])
        im.paste(sub, (0, 0))
    return im


def png(grp, grp2, tables, outdir):
    try:
        import PIL  # noqa: F401
    except ImportError:
        print("  Pillow absent : pas de planches. pip install pillow")
        return
    os.makedirs(outdir, exist_ok=True)
    print("Planches :")

    for k, (name, toks) in enumerate(tables):
        if name == "src_han_kata":
            continue
        base = grp.first + k * 128
        cells = [(token_text(toks[i]), cell_image(grp, base + i))
                 for i in range(128) if toks[i] != PLACEHOLDER]
        titre = {"src_han_alpha": "Police des messages, jeu latin de base -- ce que l'anglais atteint deja",
                 "src_han_alpha2": "Police des messages, lettres accentuees -- dessinees, "
                                   "mais hors d'atteinte du chemin anglais"}[name]
        draw_sheet(cells, "%s (%d glyphes)" % (titre, len(cells)),
                   os.path.join(outdir, name + ".png"), scale=8, cols=12)

    for base, nom in MENU_BASES:
        cells = [(chr(b) if 33 <= b < 127 else "%02X" % b, cell_image(grp2, base + b))
                 for b in range(0x20, 0x80)]
        draw_sheet(cells, "Lettres des menus, %s (base 0x%04X) -- ASCII 0x20-0x7F, aucun accent"
                   % (nom, base), os.path.join(outdir, "menu_%s.png" % nom), scale=4, cols=16)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--afs", default=AFS_DEFAULT, help="chemin de SF33RD.AFS")
    ap.add_argument("--root", default=os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                    help="racine du depot, pour lire effb6.c")
    ap.add_argument("--png", metavar="DOSSIER", help="ecrire aussi les planches de glyphes")
    args = ap.parse_args()

    if not os.path.exists(args.afs):
        raise SystemExit("SF33RD.AFS introuvable : %s" % args.afs)

    grp, grp2, tables = report(args.root, args.afs)
    if args.png:
        print()
        png(grp, grp2, tables, args.png)
    return 0


if __name__ == "__main__":
    sys.exit(main())
