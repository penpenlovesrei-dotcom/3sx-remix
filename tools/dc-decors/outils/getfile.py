import io
import os
import struct
import sys

PATH = r'C:\Users\frede\Documents\Dreamcast\Games\Street Fighter III - Double Impact.cdi'
OUT = r'C:\Users\frede\Downloads\3sx-outils\dc-decors'
SECTOR = 2336
SKIP = 8
BASE = 166 - 16

f = io.open(PATH, 'rb')


def read_lba(lba, count=1):
    out = []
    for i in range(count):
        f.seek((BASE + lba + i) * SECTOR + SKIP)
        out.append(f.read(2048))
    return b''.join(out)


def entries(lba, length):
    data = read_lba(lba, (length + 2047) // 2048)
    i = 0
    out = []
    while i < length:
        n = data[i]
        if n == 0:
            i = (i // 2048 + 1) * 2048
            continue
        rec = data[i:i + n]
        name = rec[33:33 + rec[32]].decode('latin-1').split(';')[0]
        if name not in (chr(0), chr(1)):
            out.append((name, struct.unpack('<I', rec[2:6])[0],
                        struct.unpack('<I', rec[10:14])[0], rec[25]))
        i += n
    return out


pvd = read_lba(16)
lba = struct.unpack('<I', pvd[158:162])[0]
length = struct.unpack('<I', pvd[166:170])[0]

parts = [p for p in sys.argv[1].split('/') if p]
for k, part in enumerate(parts):
    hit = None
    for name, l, sz, fl in entries(lba, length):
        if name.upper() == part.upper():
            hit = (l, sz, fl)
            break
    if hit is None:
        raise SystemExit('introuvable : ' + part)
    lba, length, fl = hit

os.makedirs(OUT, exist_ok=True)
dst = os.path.join(OUT, parts[-1])
data = read_lba(lba, (length + 2047) // 2048)[:length]
io.open(dst, 'wb').write(data)
print('%s -> %s (%d octets)' % (sys.argv[1], dst, length))
