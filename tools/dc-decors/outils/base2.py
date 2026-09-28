import struct, collections
d = open(r"C:\Users\frede\Downloads\3sx-outils\dc-decors\SF3_2ND.BIN",'rb').read()
n = len(d)
# offsets connus (debut d'une table ou d'une chaine notable)
known = [0x230B7C, 0x230D2C, 0x230DCC, 0x230D20, 0x230B48, 0x230B70]
votes = collections.Counter()
for off in range(0, n-4, 2):          # les pools litteraux sont alignes 4 mais on ratisse large
    v = struct.unpack_from('<I', d, off)[0]
    if not (0x8C000000 <= v < 0x8D000000): continue
    for k in known:
        b = v - k
        if b & 0xFFF: continue        # base supposee alignee 4 Ko
        votes[b] += 1
for b, c in votes.most_common(8):
    hits = [hex(k) for k in known if any(struct.unpack_from('<I', d, o)[0]==b+k for o in range(0,n-4,2))]
    print(f"base {b:#x}  votes={c}  offsets touches={hits}")
