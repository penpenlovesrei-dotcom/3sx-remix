import io
import struct
import sys

PATH = r'C:\Users\frede\Documents\Dreamcast\Games\Street Fighter III - Double Impact.cdi'
SECTOR = 2336
SKIP = 8
BASE = 166 - 16

f = io.open(PATH, 'rb')


def read_lba(lba, count=1):
    out = b''
    for i in range(count):
        f.seek((BASE + lba + i) * SECTOR + SKIP)
        out += f.read(2048)
    return out


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
        out.append((rec[33:33 + rec[32]].decode('latin-1'),
                    struct.unpack('<I', rec[2:6])[0],
                    struct.unpack('<I', rec[10:14])[0],
                    rec[25]))
        i += n
    return out


pvd = read_lba(16)
root_lba = struct.unpack('<I', pvd[158:162])[0]
root_len = struct.unpack('<I', pvd[166:170])[0]


def find(path):
    lba, length = root_lba, root_len
    parts = [p for p in path.split('/') if p]
    for k, part in enumerate(parts):
        hit = None
        for name, l, sz, fl in entries(lba, length):
            base = name.split(';')[0].upper()
            if base == part.upper():
                hit = (l, sz, fl)
                break
        if hit is None:
            raise SystemExit('introuvable : ' + part)
        lba, length, fl = hit
    return lba, length


for arg in sys.argv[1:]:
    lba, size = find(arg)
    head = read_lba(lba, 1)
    print('%-18s lba %6d  %9d octets' % (arg, lba, size))
    print('   ascii : %s' % ''.join(chr(c) if 32 <= c < 127 else '.' for c in head[:64]))
    print('   hex   : %s' % head[:32].hex())
    print()
