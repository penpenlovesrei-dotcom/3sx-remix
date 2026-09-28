# -*- coding: utf-8 -*-
"""Desassemble SF3_1ST.BIN mot par mot, avec le flottant et les litteraux PC-relatifs.

    py -3 dng.py 8C10FBCC 200
"""
import os
import sys
import struct

sys.path.insert(0, r"C:\Users\frede\Downloads\3sx-outils\dc-decors\outils")
import sh4ng as S

BIN_ = {0x0: "fadd", 0x1: "fsub", 0x2: "fmul", 0x3: "fdiv", 0x4: "fcmp/eq",
        0x5: "fcmp/gt", 0xC: "fmov"}
UN = {0x2: "float fpul,fr%d", 0x3: "ftrc fr%d,fpul", 0x4: "fneg fr%d", 0x5: "fabs fr%d",
      0x6: "fsqrt fr%d", 0x8: "fldi0 fr%d", 0x9: "fldi1 fr%d", 0xA: "fcnvsd",
      0xB: "fcnvds", 0xE: "fipr", 0xD: "fsca/ftrv"}


def fpu(w):
    if w >> 12 != 0xF:
        return None
    n, m, x = (w >> 8) & 15, (w >> 4) & 15, w & 15
    if x in BIN_:
        return "%s fr%d,fr%d" % (BIN_[x], m, n)
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
        return UN[m] % n if "%d" in UN[m] else UN[m]
    if x == 0xE:
        return "fmac fr0,fr%d,fr%d" % (m, n)
    return "f??? %04x" % w


def autres(w):
    n, x = (w >> 8) & 15, w & 0xFF
    if w >> 12 == 0x4 and x == 0x5A:
        return "lds r%d,fpul" % n
    if w >> 12 == 0x0 and x == 0x5A:
        return "sts fpul,r%d" % n
    if w >> 12 == 0x4 and x == 0x6A:
        return "lds r%d,fpscr" % n
    if w >> 12 == 0x4 and x == 0x2A:
        return "lds r%d,pr" % n
    return None


def litteral(a, w):
    """Resout `mov.l @(d,pc),rn` / `mov.w @(d,pc),rn` / `mova`."""
    top = w >> 12
    n = (w >> 8) & 15
    d = w & 0xFF
    if top == 0xD:                       # mov.l
        cible = ((a + 4) & ~3) + d * 4
        try:
            v = S.U32(cible)
        except Exception:
            return None
        s = "  ; r%d = %08X" % (n, v)
        if S.BASE <= v < S.FIN:
            s += "  (dans le binaire)"
        else:
            sv = v - 0x100000000 if v & 0x80000000 else v
            if abs(sv) < 0x10000:
                s += "  = %d" % sv
        return s
    if top == 0x9:                       # mov.w
        cible = a + 4 + d * 2
        try:
            v = S.U16(cible)
        except Exception:
            return None
        sv = v - 0x10000 if v & 0x8000 else v
        return "  ; r%d = %04X = %d" % (n, v, sv)
    if top == 0xC and ((w >> 8) & 15) == 7:   # mova
        cible = ((a + 4) & ~3) + d * 4
        return "  ; r0 = %08X" % cible
    return None


def montrer(adresse, nombre):
    from capstone import Cs, CS_ARCH_SH, CS_MODE_SH4, CS_MODE_LITTLE_ENDIAN
    md = Cs(CS_ARCH_SH, CS_MODE_SH4 | CS_MODE_LITTLE_ENDIAN)
    for k in range(nombre):
        a = adresse + k * 2
        o = S.a2o(a)
        w = struct.unpack_from("<H", S.D, o)[0]
        t = fpu(w) or autres(w)
        if t is None:
            ins = list(md.disasm(S.D[o:o + 2], a))
            t = "%s %s" % (ins[0].mnemonic, ins[0].op_str) if ins else "??? %04x" % w
        note = litteral(a, w) or ""
        print("  %08X  %04x  %-30s%s" % (a, w, t.strip(), note))


if __name__ == "__main__":
    montrer(int(sys.argv[1], 16), int(sys.argv[2]) if len(sys.argv) > 2 else 60)
