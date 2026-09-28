import io
import struct
import sys
import zlib

path = sys.argv[1]
out = sys.argv[2]
side = int(sys.argv[3]) if len(sys.argv) > 3 else 256
start = int(sys.argv[4], 0) if len(sys.argv) > 4 else 0x80

d = io.open(path, 'rb').read()
need = side * side
avail = (len(d) - start) // 2
if need > avail:
    raise SystemExit('%d pixels demandes, %d disponibles' % (need, avail))
pix = struct.unpack_from('<%dH' % need, d, start)


def morton(x, y, n):
    i = 0
    bit = 0
    while (1 << bit) < n:
        i |= ((y >> bit) & 1) << (2 * bit)
        i |= ((x >> bit) & 1) << (2 * bit + 1)
        bit += 1
    return i


def argb1555(v):
    r = (v >> 10) & 31
    g = (v >> 5) & 31
    b = v & 31
    return ((r << 3) | (r >> 2), (g << 3) | (g >> 2), (b << 3) | (b >> 2))


def rgb565(v):
    r = (v >> 11) & 31
    g = (v >> 5) & 63
    b = v & 31
    return ((r << 3) | (r >> 2), (g << 2) | (g >> 4), (b << 3) | (b >> 2))


def argb4444(v):
    r = (v >> 8) & 15
    g = (v >> 4) & 15
    b = v & 15
    return (r * 17, g * 17, b * 17)


FORMATS = [('ARGB1555', argb1555), ('RGB565', rgb565), ('ARGB4444', argb4444)]

# ordre entrelace calcule une fois
order = [morton(x, y, side) for y in range(side) for x in range(side)]

W = side * len(FORMATS) + 8 * (len(FORMATS) - 1)
H = side
rows = []
for y in range(H):
    row = bytearray()
    for k, (label, dec) in enumerate(FORMATS):
        if k:
            row += b'\x20\x20\x20' * 8
        base = y * side
        for x in range(side):
            r, g, b = dec(pix[order[base + x]])
            row += bytes((r, g, b))
    rows.append(row)

raw = b''.join(b'\x00' + bytes(r) for r in rows)


def chunk(tag, data):
    c = tag + data
    return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)


png = (b'\x89PNG\r\n\x1a\n'
       + chunk(b'IHDR', struct.pack('>IIBBBBB', W, H, 8, 2, 0, 0, 0))
       + chunk(b'IDAT', zlib.compress(raw, 6))
       + chunk(b'IEND', b''))
io.open(out, 'wb').write(png)
print('%s -> %s  (%dx%d, %s de gauche a droite)'
      % (path.rsplit('\\', 1)[-1], out, W, H, ', '.join(f[0] for f in FORMATS)))
