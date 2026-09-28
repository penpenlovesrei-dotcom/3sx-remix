# -*- coding: utf-8 -*-
"""Decodeur .pvc (Street Fighter III Double Impact, Dreamcast).

Format retrouve dans SF3_2ND.BIN a 0x8C0F81B4 :
  pour chaque page (tuile 16x16, 512 octets en sortie, 8192 pages max) :
    u16 H
      H == 0        : page vide, rien de plus
      H & 0x8000    : page recopiee depuis la page (H & 0x7FFF)
      sinon n = H   : palette de n couleurs u16, puis 256 pixels
                      n <= 16 -> 4 bits/pixel (quartet fort d'abord), 128 octets
                      n >  16 -> 8 bits/pixel (octet fort d'abord),  256 octets
"""
import struct

PAGE_PX = 256
MAX_PAGES = 8192

def decode(buf, max_pages=MAX_PAGES):
    """Rend (pages, consomme, stats). pages[i] = liste de 256 couleurs u16, ou None si vide."""
    pages = [None]*max_pages
    o = 0; n_buf = len(buf)
    stats = {'vides':0, 'copies':0, '4bits':0, '8bits':0, 'pages':0}
    p = 0
    while p < max_pages and o + 2 <= n_buf:
        H = struct.unpack_from('<H', buf, o)[0]; o += 2
        if H == 0:
            stats['vides'] += 1
        elif H & 0x8000:
            src = H & 0x7FFF
            pages[p] = pages[src] if src < max_pages else None
            stats['copies'] += 1
        else:
            npal = H
            pal = struct.unpack_from(f'<{npal}H', buf, o); o += npal*2
            px = []
            if npal <= 16:
                stats['4bits'] += 1
                for _ in range(PAGE_PX//4):
                    w = struct.unpack_from('<H', buf, o)[0]; o += 2
                    px.append(pal[(w >> 12) & 15]); px.append(pal[(w >> 8) & 15])
                    px.append(pal[(w >>  4) & 15]); px.append(pal[w & 15])
            else:
                stats['8bits'] += 1
                for _ in range(PAGE_PX//2):
                    w = struct.unpack_from('<H', buf, o)[0]; o += 2
                    px.append(pal[(w >> 8) & 0xFF]); px.append(pal[w & 0xFF])
            pages[p] = px
        p += 1
    stats['pages'] = p
    return pages, o, stats
