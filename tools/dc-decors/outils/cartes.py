# -*- coding: utf-8 -*-
"""Extraction et analyse des cartes stageXXX_map[64] de 3SX (bg_data.c)."""
import re, sys, os

BG_DATA = r"C:\Temp3sx\src\sf33rd\Source\Game\stage\bg_data.c"

def lire(path=BG_DATA):
    return open(path, "r", encoding="utf-8", errors="replace").read()

def tableau_u16(src, nom):
    m = re.search(r"const\s+u16\s+" + nom + r"\s*\[\s*64\s*\]\s*=\s*\{(.*?)\}\s*;", src, re.S)
    if not m: return None
    vals = [int(v, 0) for v in re.findall(r"0[xX][0-9A-Fa-f]+|\b\d+\b", m.group(1))]
    assert len(vals) == 64, (nom, len(vals))
    return vals

def tableau_u32_2d(src, nom, n, m_):
    mm = re.search(r"const\s+u32\s+" + nom + r"\s*\[\s*\d*\s*\]\s*\[\s*\d+\s*\]\s*=\s*\{(.*?)\n\};", src, re.S)
    txt = mm.group(1)
    vals = [int(v, 0) for v in re.findall(r"0[xX][0-9A-Fa-f]+|\b\d+\b", txt)]
    return [vals[i*m_:(i+1)*m_] for i in range(n)]

def tableau_u8(src, nom):
    mm = re.search(r"const\s+u8\s+" + nom + r"\s*\[\s*\d+\s*\]\s*=\s*\{(.*?)\}\s*;", src, re.S)
    vals = [int(v, 0) for v in re.findall(r"0[xX][0-9A-Fa-f]+|\b\d+\b", mm.group(1))]
    return vals

def cartes(src):
    """{nom: [64 u16]}"""
    d = {}
    for nom in re.findall(r"const u16 (\w+_map)\[64\]", src):
        d[nom] = tableau_u16(src, nom)
    return d

def table_bg_map(src):
    mm = re.search(r"const u16\* bg_map_tbl\[23\]\[3\]\s*=\s*\{(.*?)\n\};", src, re.S)
    txt = mm.group(1)
    noms = re.findall(r"(\w+_map|NULL)", txt)
    return [noms[i*3:(i+1)*3] for i in range(23)]

def cells(mot_liste, lsb=True):
    """512 valeurs 2 bits, dans l'ordre des mots puis des paires."""
    out = []
    for w in mot_liste:
        for k in range(8):
            if lsb:
                out.append((w >> (2*k)) & 3)
            else:
                out.append((w >> (14 - 2*k)) & 3)
    return out

def pages_gbix(g):
    """indices de page 0..31 presents (bit MSB = page 0)."""
    return set(i for i in range(32) if g & (0x80000000 >> i))

if __name__ == "__main__":
    src = lire()
    cs = cartes(src)
    tbl = table_bg_map(src)
    gbix = tableau_u32_2d(src, "bgtex_stage_gbix", 23, 3)
    urs = tableau_u8(src, "use_real_scr")
    print("cartes:", len(cs))
    # inventaire des valeurs 2 bits
    from collections import Counter
    tot = Counter()
    for n, v in cs.items():
        tot.update(cells(v))
    print("valeurs 2 bits (LSB):", dict(tot))
    tot = Counter()
    for n, v in cs.items():
        tot.update(cells(v, lsb=False))
    print("valeurs 2 bits (MSB):", dict(tot))
