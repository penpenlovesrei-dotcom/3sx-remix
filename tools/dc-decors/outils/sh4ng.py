# -*- coding: utf-8 -*-
"""Outils SH-4 pour SF3_1ST.BIN (New Generation) : meme base 0x8C010000 que 2nd Impact.

Copie de `sh4.py` avec un autre binaire. La base est verifiee par `verifier_base()` :
les pointeurs internes du binaire doivent tomber dans [BASE, BASE+len).
"""
import struct
from capstone import Cs, CS_ARCH_SH, CS_MODE_SH4, CS_MODE_LITTLE_ENDIAN

BASE = 0x8C010000
PATH = r"C:\Users\frede\Downloads\3sx-outils\dc-decors\SF3_1ST.BIN"
D = open(PATH, 'rb').read()
FIN = BASE + len(D)


def a2o(a):
    return a - BASE


def o2a(o):
    return o + BASE


def u32(o):
    return struct.unpack_from('<I', D, o)[0]


def u16(o):
    return struct.unpack_from('<H', D, o)[0]


def U32(a):
    return struct.unpack_from('<I', D, a - BASE)[0]


def U16(a):
    return struct.unpack_from('<H', D, a - BASE)[0]


def S16(a):
    return struct.unpack_from('<h', D, a - BASE)[0]


def U8(a):
    return D[a - BASE]


_md = Cs(CS_ARCH_SH, CS_MODE_SH4 | CS_MODE_LITTLE_ENDIAN)
_md.detail = False


def disasm(addr, count=40):
    o = a2o(addr)
    out = []
    for i in _md.disasm(D[o:o + count * 2], addr):
        out.append((i.address, i.mnemonic, i.op_str))
        if len(out) >= count:
            break
    return out


def show(addr, count=40, marks=None):
    marks = marks or {}
    for a, m, ops in disasm(addr, count):
        tag = marks.get(a, '')
        print(f"  {a:08X} {D[a2o(a)]:02x}{D[a2o(a)+1]:02x}  {m:<10s} {ops:<28s} {tag}")


def show2(addr, count=60):
    """Desassemble mot par mot : un opcode invalide n'interrompt pas le flux."""
    for i in range(count):
        a = addr + i * 2
        o = a2o(a)
        ins = list(_md.disasm(D[o:o + 2], a))
        w = u16(o)
        if ins:
            print(f"  {a:08X} {w:04x}  {ins[0].mnemonic:<10s} {ins[0].op_str}")
        else:
            print(f"  {a:08X} {w:04x}  ???")


def find_u32(val):
    """offsets fichier alignes 4 ou apparait la valeur."""
    res = []
    b = struct.pack('<I', val)
    i = D.find(b)
    while i != -1:
        if i % 4 == 0:
            res.append(i)
        i = D.find(b, i + 1)
    return res


def verifier_base():
    """Combien de u32 alignes tombent dans le binaire -- une base fausse casse ce compte."""
    n = 0
    tot = 0
    for o in range(0, len(D) - 4, 4):
        v = struct.unpack_from('<I', D, o)[0]
        if 0x8C000000 <= v < 0x8D000000:
            tot += 1
            if BASE <= v < FIN:
                n += 1
    return n, tot


if __name__ == "__main__":
    print("SF3_1ST.BIN  %d octets   %08X .. %08X" % (len(D), BASE, FIN))
    n, tot = verifier_base()
    print("pointeurs 0x8Cxxxxxx alignes : %d, dont %d dans le binaire (%.1f %%)"
          % (tot, n, 100.0 * n / max(tot, 1)))
