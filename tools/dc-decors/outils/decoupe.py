# -*- coding: utf-8 -*-
"""Decoupe les conteneurs .pk des deux jeux d'apres les tables de l'executable.

Base de chargement des deux binaires : 0x8C010000.
Liste primaire  : {char* nom, u32 taille, u32 somme}  -> les .pvc
Liste secondaire: {u32 id, char* nom, u32 taille}     -> les assets F_ (sprites animes)
Chaque partie est alignee sur un secteur de 2048.
"""
import struct, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pvc as PVC

BASE = 0x8C010000
RAC = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

JEUX = {
    'ng': dict(exe='SF3_1ST.BIN', dossier='SFNG', bn=0x4c4b0c, pl=0x4c4bf4, sl=0x4c4ca0, nsec=20, n=43),
    '2i': dict(exe='SF3_2ND.BIN', dossier='SFNG2', bn=0x600bcc, pl=0x600cc0, sl=0x600d64, nsec=18, n=24),
}

def somme32(b, taille):
    s = 0
    for i in range((taille + 3) // 4):
        s = (s + struct.unpack_from('<I', b, i*4)[0]) & 0xFFFFFFFF
    return s

def decouper(court):
    j = JEUX[court]
    d = open(os.path.join(RAC, j['exe']), 'rb').read()
    def cstr(a):
        o = a - BASE; e = d.find(b'\x00', o); return d[o:e].decode('ascii','replace').rstrip('.')
    def u32(o): return struct.unpack_from('<I', d, o)[0]
    sect = lambda n: (n + 2047) // 2048
    vu = {}
    for i in range(j['n']):
        bn = u32(j['bn'] + i*4)
        if not (BASE <= bn < 0x8D000000): continue
        nom = cstr(bn)
        if nom in vu: continue
        parts = []
        lp = u32(j['pl'] + i*4)
        if BASE <= lp < 0x8D000000:
            o = lp - BASE
            while True:
                p, sz, som = struct.unpack_from('<III', d, o)
                if not (BASE <= p < 0x8D000000): break
                parts.append((cstr(p), sz, som)); o += 12
        if i < j['nsec']:
            sp = u32(j['sl'] + i*4)
            if BASE <= sp < 0x8D000000:
                o = sp - BASE
                while True:
                    ident, p, sz = struct.unpack_from('<III', d, o)
                    if not (BASE <= p < 0x8D000000): break
                    parts.append((cstr(p), sz, None)); o += 12
        if parts: vu[nom] = parts
    return vu, sect
