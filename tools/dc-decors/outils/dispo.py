# -*- coding: utf-8 -*-
"""Cherche la disposition des tuiles : mesure la coherence entre lignes voisines.
Plus le chiffre est bas, plus l'image est coherente."""
import sys
import os; sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import pvc

def rgb(c):
    r=((c>>10)&31)*255//31; g=((c>>5)&31)*255//31; b=(c&31)*255//31
    return r,g,b

def demorton(i, bits, y_low):
    x=y=0
    for k in range(bits):
        if y_low: y |= ((i>>(2*k))&1)<<k;  x |= ((i>>(2*k+1))&1)<<k
        else:     x |= ((i>>(2*k))&1)<<k;  y |= ((i>>(2*k+1))&1)<<k
    return x,y

def build(pages, first, tiles_w, tiles_h, tile_morton, page_morton, y_low):
    W=tiles_w*16; H=tiles_h*16
    img=[[0]*W for _ in range(H)]
    for p in range(tiles_w*tiles_h):
        px = pages[first+p]
        if px is None: continue
        if page_morton: tx,ty = demorton(p, 6, y_low)
        else:           tx,ty = p%tiles_w, p//tiles_w
        if tx>=tiles_w or ty>=tiles_h: continue
        for i in range(256):
            if tile_morton: ix,iy = demorton(i, 4, y_low)
            else:           ix,iy = i%16, i//16
            img[ty*16+iy][tx*16+ix] = px[i]
    return img

def coherence(img):
    H=len(img); W=len(img[0]); tot=0; n=0
    for y in range(0,H-1,2):
        for x in range(0,W,3):
            a=rgb(img[y][x]); b=rgb(img[y+1][x])
            tot += abs(a[0]-b[0])+abs(a[1]-b[1])+abs(a[2]-b[2]); n+=1
    return tot/n/3

if __name__ == '__main__':
    path, sz = sys.argv[1], int(sys.argv[2])
    buf = open(path,'rb').read()[:sz]
    pages,_,_ = pvc.decode(buf)
    print(f"== {path} : coherence verticale (bas = mieux)")
    for tm in (False,True):
        for pm in (False,True):
            for yl in (True,False):
                if not tm and not pm and not yl: continue
                img = build(pages, 0, 64, 64, tm, pm, yl)
                c = coherence(img)
                print(f"   tuile{'Morton' if tm else 'lineaire':>9s} page{'Morton' if pm else 'lineaire':>9s} {'Yfaible' if yl else 'Xfaible'} -> {c:6.2f}")
