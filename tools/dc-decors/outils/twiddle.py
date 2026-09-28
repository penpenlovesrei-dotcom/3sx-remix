import io
import struct
import sys

path = sys.argv[1]
start = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x80
d = io.open(path, 'rb').read()
avail = (len(d) - start) // 2
print('=== %s : %d pixels de 16 bits a partir de 0x%X ===' % (path.rsplit('\\', 1)[-1], avail, start))


def untwiddle_index(x, y, n):
    """position d un pixel (x,y) dans une texture entrelacee de cote n"""
    i = 0
    bit = 0
    while (1 << bit) < n:
        i |= ((y >> bit) & 1) << (2 * bit)
        i |= ((x >> bit) & 1) << (2 * bit + 1)
        bit += 1
    return i


def rowdiff(get, w, h):
    """proportion de pixels qui different de celui juste au-dessus"""
    diff = 0
    n = 0
    ystep = max(1, h // 64)
    xstep = max(1, w // 64)
    for y in range(0, h - 1, ystep):
        for x in range(0, w, xstep):
            diff += 1 if get(x, y) != get(x, y + 1) else 0
            n += 1
    return diff * 100.0 / n


print()
print('%-14s %10s %10s' % ('taille', 'lineaire', 'entrelace'))
for side in (64, 128, 256, 512):
    need = side * side
    if need > avail:
        continue
    pix = struct.unpack_from('<%dH' % need, d, start)

    lin = rowdiff(lambda x, y: pix[y * side + x], side, side)
    tw = rowdiff(lambda x, y: pix[untwiddle_index(x, y, side)], side, side)
    print('%-14s %9.1f%% %9.1f%%  %s' % ('%dx%d' % (side, side), lin, tw,
                                         '<-- entrelace bien meilleur' if tw < lin - 15 else ''))
