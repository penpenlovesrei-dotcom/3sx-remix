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
            out.append((name,
                        struct.unpack('<I', rec[2:6])[0],
                        struct.unpack('<I', rec[10:14])[0],
                        rec[25]))
        i += n
    return out


pvd = read_lba(16)
root_lba = struct.unpack('<I', pvd[158:162])[0]
root_len = struct.unpack('<I', pvd[166:170])[0]

folders = {}
for name, lba, sz, fl in entries(root_lba, root_len):
    if fl & 2:
        folders[name.upper()] = (lba, sz)

os.makedirs(OUT, exist_ok=True)

for game in ('SFNG', 'SFNG2'):
    if game not in folders:
        print('%s : absent' % game)
        continue
    dst = os.path.join(OUT, game)
    os.makedirs(dst, exist_ok=True)
    rows = [r for r in entries(*folders[game]) if r[0].upper().startswith('B')
            and r[0].upper().endswith('.PK')]
    rows.sort()
    print('%s : %d decors' % (game, len(rows)))
    total = 0
    for name, lba, sz, fl in rows:
        data = read_lba(lba, (sz + 2047) // 2048)[:sz]
        with io.open(os.path.join(dst, name), 'wb') as o:
            o.write(data)
        total += sz
        print('   %-10s %9d octets' % (name, sz))
    print('   -> %s  (%.1f Mo)' % (dst, total / 1048576.0))
