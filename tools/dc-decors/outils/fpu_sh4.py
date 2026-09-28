# -*- coding: utf-8 -*-
"""Les instructions FLOTTANTES du SH-4, que `sh4.disasm` rend en `???`.

Ecrit pour lire le constructeur de quadrilateres de 2nd Impact (`0x8C0F6A90`), ou la
taille et les coordonnees de texture d'une bande de decor se calculent en virgule
flottante. Seules les formes `1111 nnnn mmmm xxxx` sont traitees ; le reste est laisse
a `sh4`.

    python fpu_sh4.py 8C0F6A90 120
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sh4

BIN = {0x0: "fadd", 0x1: "fsub", 0x2: "fmul", 0x3: "fdiv", 0x4: "fcmp/eq", 0x5: "fcmp/gt",
       0xC: "fmov"}
UN = {0x2: "float fpul,fr%d", 0x3: "ftrc fr%d,fpul", 0x4: "fneg fr%d", 0x5: "fabs fr%d",
      0x6: "fsqrt fr%d", 0x8: "fldi0 fr%d", 0x9: "fldi1 fr%d"}


def fpu(w):
    """Le texte d'une instruction flottante, ou None si `w` n'en est pas une."""
    if w >> 12 != 0xF:
        return None
    n, m, x = (w >> 8) & 15, (w >> 4) & 15, w & 15
    if x in BIN:
        return "%s fr%d,fr%d" % (BIN[x], m, n)
    if x == 0x6:
        return "fmov.s @(r0,r%d),fr%d" % (m, n)
    if x == 0x7:
        return "fmov.s fr%d,@(r0,r%d)" % (m, n)
    if x == 0x8:
        return "fmov.s @r%d,fr%d" % (m, n)
    if x == 0x9:
        return "fmov.s @r%d+,fr%d" % (m, n)
    if x == 0xA:
        return "fmov.s fr%d,@r%d" % (m, n)
    if x == 0xB:
        return "fmov.s fr%d,@-r%d" % (m, n)
    if x == 0xD and m in UN:
        return UN[m] % n
    return None


def autres(w):
    """Les transferts entre registres entiers et FPUL."""
    n, x = (w >> 8) & 15, w & 0xFF
    if w >> 12 == 0x4 and x == 0x5A:
        return "lds r%d,fpul" % n
    if w >> 12 == 0x0 and x == 0x5A:
        return "sts fpul,r%d" % n
    return None


def montrer(adresse, nombre):
    o = sh4.a2o(adresse)
    for k in range(nombre):
        a = adresse + 2 * k
        w = struct.unpack_from("<H", sh4.D, o + 2 * k)[0]
        texte = fpu(w) or autres(w)
        if texte is None:
            # un mot a la fois : `sh4.disasm` s'arrete au premier mot qu'il ne connait pas
            r = sh4.disasm(a, 1)
            texte = "%-10s %s" % (r[0][1], r[0][2]) if r else "?"
        print("  %08X %04x  %s" % (a, w, texte))


if __name__ == "__main__":
    montrer(int(sys.argv[1], 16), int(sys.argv[2]))
