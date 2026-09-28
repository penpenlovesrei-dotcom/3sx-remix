import io
import struct
import sys
import zlib

path = sys.argv[1]
out = sys.argv[2]
side = int(sys.argv[3]) if len(sys.argv) > 3 else 256
payload = int(sys.argv[4], 0) if len(sys.argv) > 4 else 0x80

d = io.open(path, 'rb').read()
cb = struct.unpack_from('<1024H', d, payload)      # 256 entrees de 4 pixels
idx_off = payload + 2048
half = side // 2


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
    return (((v >> 8) & 15) * 17, ((v >> 4) & 15) * 17, (v & 15) * 17)


FORMATS = [('ARGB1555', argb1555), ('RGB565', rgb565), ('ARGB4444', argb4444)]

# index desentrelace une fois pour toutes
grid = [[d[idx_off + morton(bx, by, half)] for bx in range(half)] for by in range(half)]

W = side * len(FORMATS) + 8 * (len(FORMATS) - 1)
rows = []
for y in range(side):
    by = y >> 1
    sub_y = y & 1
    row = bytearray()
    for k, (label, dec) in enumerate(FORMATS):
        if k:
            row += b'\x20\x20\x20' * 8
        line = grid[by]
        for x in range(side):
            ent = line[x >> 1] * 4
            # dans une entree 2x2 la Dreamcast range en colonnes
            v = cb[ent + (x & 1) * 2 + sub_y]
            r, g, b = dec(v)
            row += bytes((r, g, b))
    rows.append(row)

raw = b''.join(b'\x00' + bytes(r) for r in rows)


def chunk(tag, data):
    c = tag + data
    return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xFFFFFFFF)


png = (b'\x89PNG\r\n\x1a\n'
       + chunk(b'IHDR', struct.pack('>IIBBBBB', W, side, 8, 2, 0, 0, 0))
       + chunk(b'IDAT', zlib.compress(raw, 6))
       + chunk(b'IEND', b''))
io.open(out, 'wb').write(png)
print('%s -> %s  (%dx%d, VQ %dx%d)' % (path.rsplit('\\', 1)[-1], out, W, side, side, side))
