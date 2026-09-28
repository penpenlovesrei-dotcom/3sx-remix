# -*- coding: ascii -*-
import io, re, struct, collections
B = open(r"C:\Users\frede\Downloads\3sx-outils\dc-decors\SF3_1ST.BIN","rb").read(); BASE=0x8C010000
def U8(a): return B[a-BASE]
def U16(a): return struct.unpack_from("<H", B, a-BASE)[0]
def U32(a): return struct.unpack_from("<I", B, a-BASE)[0]
ed = {}
for d in range(13):
    for a in range(3):
        ed.setdefault(37 + U16(0x8C18A804 + d*6 + a*2), (d, a))
src = io.open(r"C:\Temp3sx\src\port\video\decor_objets_data.c", encoding="utf-8", errors="replace", newline="").read()
dur = {}
for m in re.finditer(r"static const unsigned char (\w+)_durees\[(\d+)\] = \{([^}]*)\};", src):
    dur[m.group(1)] = [int(x) for x in re.findall(r"\d+", m.group(3))]
ecarts = []
vus = 0
for l in src.split("\n"):
    t = l.strip()
    if not t.startswith('{ "ng') or "_durees" not in t or "/*" not in t: continue
    pre = re.search(r"(\w+)_durees", t).group(1)
    etage = int(re.findall(r'", (\d+),', t)[0])
    sc = re.search(r"script (\d+)", t)
    if not sc or etage not in ed: continue
    d, a = ed[etage]
    table = U32(0x8C4CC1F0 + d*12 + a*4)
    if not (BASE <= table < BASE+len(B)): continue
    p = U32(table + int(sc.group(1))*4)
    if not (BASE <= p < BASE+len(B)): continue
    lues = []
    for k in range(256):
        drap, duree = U8(p+k*8), U8(p+k*8+1)
        if drap in (0x01, 0x02) and duree == 0: break
        if duree: lues.append(duree)
    em = dur.get(pre)
    if em is None or not lues: continue
    vus += 1
    if sum(lues) != sum(em):
        ecarts.append((etage, int(sc.group(1)), pre, lues, em))
print("fiches NG verifiees : %d, ecarts de somme : %d" % (vus, len(ecarts)))
classe = collections.Counter(); restes = []
for x in ecarts:
    etage, sc, pre, lues, em = x
    if len(em) == 1:
        classe["objet reduit a UNE image (fige / pose balayee)"] += 1
    elif sum(em) == 72:
        classe["cycle aligne sur 72 trames"] += 1
    elif len(em) < len(lues) and em == lues[:len(em)]:
        classe["tronque : moins d'images emises, debut identique"] += 1
    elif len(em) > len(lues):
        classe["plus d'images emises que le script n'en tient"] += 1
    else:
        classe["A REGARDER"] += 1; restes.append(x)
print("")
for k, n in classe.most_common():
    print("   %-52s %3d" % (k, n))
print("")
print("les %d cas a regarder :" % len(restes))
for x in restes[:12]:
    print("   etage %2d script %2d %-9s binaire %4d %s" % (x[0], x[1], x[2], sum(x[3]), x[3][:8]))
    print("                                emis    %4d %s" % (sum(x[4]), x[4][:8]))
