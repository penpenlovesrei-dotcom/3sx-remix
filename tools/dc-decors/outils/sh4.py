# -*- coding: utf-8 -*-
"""Outils SH-4 pour SF3_2ND.BIN : base 0x8C010000."""
import struct, sys
from capstone import Cs, CS_ARCH_SH, CS_MODE_SH4, CS_MODE_LITTLE_ENDIAN

BASE = 0x8C010000
PATH = r"C:\Users\frede\Downloads\3sx-outils\dc-decors\SF3_2ND.BIN"
D = open(PATH,'rb').read()

def a2o(a): return a - BASE
def o2a(o): return o + BASE
def u32(o): return struct.unpack_from('<I', D, o)[0]
def u16(o): return struct.unpack_from('<H', D, o)[0]

_md = Cs(CS_ARCH_SH, CS_MODE_SH4 | CS_MODE_LITTLE_ENDIAN)
_md.detail = False

def disasm(addr, count=40):
    o = a2o(addr)
    out=[]
    for i in _md.disasm(D[o:o+count*2], addr):
        out.append((i.address, i.mnemonic, i.op_str))
        if len(out)>=count: break
    return out

def show(addr, count=40, marks=None):
    marks = marks or {}
    for a,m,ops in disasm(addr,count):
        tag = marks.get(a,'')
        print(f"  {a:08X} {D[a2o(a)]:02x}{D[a2o(a)+1]:02x}  {m:<10s} {ops:<28s} {tag}")

def find_u32(val):
    """offsets fichier ou apparait la valeur (alignee 4)."""
    res=[]; b = struct.pack('<I', val); i = D.find(b)
    while i != -1:
        if i % 4 == 0: res.append(i)
        i = D.find(b, i+1)
    return res

# --- resolution des literal pools : mov.l @(disp,PC),Rn ---
def pool_refs(target_off):
    """Instructions mov.l @(disp,PC),Rn dont le pool vaut l'adresse cible."""
    hits=[]
    for pool_off in find_u32(o2a(target_off) if target_off < BASE else target_off):
        pool_addr = o2a(pool_off)
        # mov.l @(disp,PC),Rn : opcode 1101nnnndddddddd ; cible = (PC&~3)+4+disp*4
        for ins_off in range(max(0,pool_off-1100), pool_off, 2):
            w = u16(ins_off)
            if (w >> 12) != 0xD: continue
            pc = o2a(ins_off)
            tgt = ((pc + 4) & ~3) + (w & 0xFF)*4
            if tgt == pool_addr:
                hits.append((pc, (w>>8)&0xF, pool_addr))
    return hits

def show2(addr, count=60, pas=None):
    """Desassemble mot par mot : un opcode invalide n'interrompt pas le flux."""
    for i in range(count):
        a = addr + i*2
        o = a2o(a)
        ins = list(_md.disasm(D[o:o+2], a))
        w = u16(o)
        if ins:
            print(f"  {a:08X} {w:04x}  {ins[0].mnemonic:<10s} {ins[0].op_str}")
        else:
            print(f"  {a:08X} {w:04x}  ???")
