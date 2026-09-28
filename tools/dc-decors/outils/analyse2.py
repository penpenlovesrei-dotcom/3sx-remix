import io
import struct
import sys

path = sys.argv[1]
d = io.open(path, 'rb').read()
n = len(d)
name = path.rsplit('\\', 1)[-1]
print('=== %s : %d octets ===' % (name, n))

# ou finit la zone de zeros de tete
i = 0
while i < n and d[i] == 0:
    i += 1
first = i
# le tout premier mot n est pas nul, on repart apres lui
i = 4
while i < n and d[i] == 0:
    i += 1
print('zone nulle de 4 a 0x%X (%d octets)' % (i, i - 4))
start = i

print()
print('--- autour du premier octet non nul ---')
base = (start // 16) * 16 - 32
for off in range(max(0, base), max(0, base) + 96, 16):
    row = d[off:off + 16]
    print('%06X  %-48s %s' % (off, row.hex(' '),
                              ''.join(chr(c) if 32 <= c < 127 else '.' for c in row)))

print()
print('--- ces octets vus comme des couleurs 16 bits ---')
print('  ARGB1555 / RGB565, seize premieres valeurs a 0x%X :' % start)
vals = struct.unpack_from('<16H', d, start)
for v in vals:
    a = (v >> 15) & 1
    r5 = (v >> 10) & 31
    g5 = (v >> 5) & 31
    b5 = v & 31
    r6 = (v >> 11) & 31
    g6 = (v >> 5) & 63
    b6 = v & 31
    print('   0x%04X   1555 a=%d r=%2d g=%2d b=%2d    565 r=%2d g=%2d b=%2d'
          % (v, a, r5, g5, b5, r6, g6, b6))

print()
print('--- taille utile et decoupages plausibles ---')
usable = n - start
print('  %d octets a partir de 0x%X' % (usable, start))
for bpp, label in ((1, '8 bits par pixel'), (2, '16 bits par pixel')):
    px = usable // bpp
    print('  %s -> %d pixels' % (label, px))
    for w in (256, 320, 384, 512, 640, 1024):
        if px % w == 0:
            print('       %d x %d' % (w, px // w))
    for tile in (8, 16, 32):
        per = tile * tile
        if px % per == 0:
            print('       %d tuiles de %dx%d' % (px // per, tile, tile))
