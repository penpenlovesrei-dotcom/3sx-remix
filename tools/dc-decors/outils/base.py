import struct, collections, sys
d = open(r"C:\Users\frede\Downloads\3sx-outils\dc-decors\SF3_2ND.BIN",'rb').read()
n = len(d)
vals = []
for off in range(0, n-4, 4):
    v = struct.unpack_from('<I', d, off)[0]
    if 0x8C000000 <= v < 0x8D000000:
        vals.append((off, v))
print("pointeurs 0x8Cxxxxxx alignes :", len(vals))
# base candidate: value - knownOffset pour des offsets connus
known = {0x230B7C:"bg00.pvc", 0x230DCC:"b00.pk", 0x230D2C:"c00.pk"}
cnt = collections.Counter()
for off,v in vals:
    for k in known:
        cnt[v-k] += 1
print("bases candidates (via tables de noms) :", cnt.most_common(6))
# consistance : combien de pointeurs tombent dans [base, base+n)
for base in [0x8C010000, 0x8C000000, 0x8C008000, 0x8C020000]:
    ok = sum(1 for _,v in vals if base <= v < base+n)
    print(f"base {base:#x} : {ok}/{len(vals)} pointeurs dans le fichier ({100*ok/len(vals):.1f}%)")
