import sys, os
# Autocorrelation par difference absolue moyenne, pour trouver la periode
# de ligne / de tuile dans un fichier binaire.
def probe(path, start=0x80, maxlen=1<<19):
    d = open(path,'rb').read()[start:start+maxlen]
    n = len(d)
    base = sum(abs(d[i]-d[i+1]) for i in range(0, n-1, 7)) / (n//7)
    out=[]
    for s in list(range(1,65))+[72,80,96,112,128,144,160,176,192,224,256,288,320,384,448,512,640,768,896,1024,1280,1536,2048]:
        if s>=n: break
        tot=0; cnt=0
        for i in range(0, n-s, 7):
            tot += abs(d[i]-d[i+s]); cnt+=1
        out.append((tot/cnt, s))
    out.sort()
    return base, out

for path in sys.argv[1:]:
    base, out = probe(path)
    print(f"== {os.path.basename(os.path.dirname(path))}/{os.path.basename(path)}  ref(stride1)={base:.2f}")
    print("   meilleurs strides:", ", ".join(f"{s}:{v:.2f}" for v,s in out[:12]))
