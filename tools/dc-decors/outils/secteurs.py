# -*- coding: utf-8 -*-
"""Empreinte par secteur de 2048 : entropie et nombre d'octets distincts.
Sert a reperer les frontieres entre parties d'un .pk."""
import sys, math, collections
def ent(b):
    c = collections.Counter(b); n=len(b)
    return -sum(v/n*math.log2(v/n) for v in c.values())
for path in sys.argv[1:]:
    d = open(path,'rb').read()
    ns = len(d)//2048
    print(f"== {path}  {len(d)} octets = {ns} secteurs")
    prev=None; line=[]
    for s in range(ns):
        b = d[s*2048:(s+1)*2048]
        e = ent(b); u = len(set(b))
        line.append((s,e,u))
    # resume compacte : marquer les sauts d'entropie
    print("   secteur:entropie/distincts (saut marque *)")
    out=[]
    for i,(s,e,u) in enumerate(line):
        mark = ''
        if i>0 and abs(e-line[i-1][1])>1.5: mark='*'
        out.append(f"{mark}{s}:{e:.1f}/{u}")
    print("   " + " ".join(out))
