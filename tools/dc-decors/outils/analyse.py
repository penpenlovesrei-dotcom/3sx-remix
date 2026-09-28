import io
import struct
import sys
from collections import Counter

path = sys.argv[1]
d = io.open(path, 'rb').read()
n = len(d)
print('=== %s : %d octets ===' % (path.rsplit('\\', 1)[-1], n))

print()
print('--- 128 premiers octets ---')
for off in range(0, 128, 16):
    row = d[off:off + 16]
    print('%04X  %-48s %s' % (off, row.hex(' '),
                              ''.join(chr(c) if 32 <= c < 127 else '.' for c in row)))

print()
print('--- lus comme des u32 ---')
vals = struct.unpack_from('<16I', d, 0)
print('  ' + '  '.join('%d' % v for v in vals[:8]))
print('  ' + '  '.join('0x%X' % v for v in vals[:8]))

print()
print('--- une table d offsets ? ---')
plausible = []
for i in range(0, min(256, n // 4)):
    v = struct.unpack_from('<I', d, i * 4)[0]
    if 0 < v < n:
        plausible.append((i * 4, v))
    else:
        if i > 2:
            break
print('  %d valeurs de suite tiennent dans le fichier' % len(plausible))
for off, v in plausible[:10]:
    print('    a 0x%03X : 0x%X (%d)  -> octets la-bas : %s' % (off, v, v, d[v:v + 8].hex()))

print()
print('--- entropie par tranche de 64 Ko ---')
for start in range(0, n, 65536):
    chunk = d[start:start + 65536]
    c = Counter(chunk)
    distinct = len(c)
    zeros = c.get(0, 0) * 100.0 // len(chunk)
    top = c.most_common(1)[0]
    print('  0x%06X  %3d valeurs distinctes, %2d%% de zeros, plus frequent 0x%02X (%d%%)'
          % (start, distinct, zeros, top[0], top[1] * 100 // len(chunk)))

print()
print('--- repetitions longues (indice de donnees non compressees) ---')
runs = 0
i = 1
best = 0
cur = 1
while i < n:
    if d[i] == d[i - 1]:
        cur += 1
    else:
        if cur >= 16:
            runs += 1
        best = max(best, cur)
        cur = 1
    i += 1
print('  %d suites de 16 octets identiques ou plus, la plus longue : %d' % (runs, best))
