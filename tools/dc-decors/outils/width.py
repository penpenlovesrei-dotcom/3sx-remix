import io
import struct
import sys

path = sys.argv[1]
start = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x80
d = io.open(path, 'rb').read()
px = memoryview(d)[start:]
count = len(px) // 2
pix = struct.unpack_from('<%dH' % count, d, start)
print('=== %s : %d pixels de 16 bits a partir de 0x%X ===' % (path.rsplit('\\', 1)[-1], count, start))

# combien de couleurs distinctes, et le bit de poids fort
distinct = len(set(pix))
top = sum(1 for v in pix if v & 0x8000)
print('couleurs distinctes : %d   |   bit 15 arme : %d%% des pixels' % (distinct, top * 100 // count))

print()
print('--- ressemblance entre lignes voisines, par largeur ---')
print('(plus le score est bas, mieux la largeur explique l image)')


def score(w):
    rows = count // w
    if rows < 8:
        return None
    total = 0
    n = 0
    step = max(1, rows // 64)
    for r in range(0, rows - 1, step):
        a = r * w
        b = a + w
        s = 0
        for k in range(0, w, max(1, w // 64)):
            s += 1 if pix[a + k] != pix[b + k] else 0
        total += s
        n += max(1, w // 64) and len(range(0, w, max(1, w // 64)))
    return total * 100.0 / n if n else None


cands = []
for w in (4, 8, 12, 16, 24, 32, 48, 64, 96, 128, 160, 192, 224, 256, 288, 320, 336, 352, 384, 400, 416, 448, 480, 512, 576,
          640, 704, 768, 800, 896, 1024):
    sc = score(w)
    if sc is not None:
        cands.append((sc, w))
cands.sort()
for sc, w in cands[:10]:
    rows = count // w
    rest = count % w
    print('  largeur %4d : %5.1f%% de differences, %d lignes, reste %d' % (w, sc, rows, rest))
