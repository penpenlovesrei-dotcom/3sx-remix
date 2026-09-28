import io
import struct
import sys

PATH = r'C:\Users\frede\Documents\Dreamcast\Games\Street Fighter III - Double Impact.cdi'
SECTOR = 2336
SKIP = 8
BASE = 166 - 16   # secteur fichier du LBA 0 du volume

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
        elba = struct.unpack('<I', rec[2:6])[0]
        esize = struct.unpack('<I', rec[10:14])[0]
        flags = rec[25]
        nlen = rec[32]
        name = rec[33:33 + nlen].decode('latin-1')
        if name not in (chr(0), chr(1)):
            out.append((name, elba, esize, flags))
        i += n
    return out


pvd = read_lba(16)
root = pvd[156:190]
root_lba = struct.unpack('<I', root[2:6])[0]
root_len = struct.unpack('<I', root[10:14])[0]


def walk(path):
    lba, length = root_lba, root_len
    for part in [p for p in path.split('/') if p]:
        hit = None
        for name, l, sz, fl in entries(lba, length):
            if name.upper().rstrip(';1') == part.upper() and (fl & 2):
                hit = (l, sz)
                break
        if hit is None:
            raise SystemExit('introuvable : ' + part)
        lba, length = hit
    return lba, length


target = sys.argv[1] if len(sys.argv) > 1 else ''
lba, length = walk(target)
rows = entries(lba, length)
print('--- /%s --- %d entrees' % (target, len(rows)))
print('%-22s %10s %12s  %s' % ('nom', 'lba', 'octets', 'type'))
total = 0
for name, l, sz, fl in sorted(rows, key=lambda r: -r[2]):
    print('%-22s %10d %12d  %s' % (name, l, sz, 'dossier' if fl & 2 else 'fichier'))
    total += sz
print('total %d octets' % total)
