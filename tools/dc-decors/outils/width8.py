import io
import sys

path = sys.argv[1]
start = int(sys.argv[2], 0) if len(sys.argv) > 2 else 0x80
d = io.open(path, 'rb').read()
pix = d[start:]
count = len(pix)
print('=== %s : %d octets a partir de 0x%X, lus comme 8 bits ===' % (path.rsplit('\\', 1)[-1], count, start))
print('valeurs distinctes : %d' % len(set(pix)))
print()


def score(w, data):
    rows = len(data) // w
    if rows < 16:
        return None
    diff = 0
    n = 0
    step = max(1, rows // 128)
    for r in range(0, rows - 1, step):
        a = r * w
        b = a + w
        k = 0
        while k < w:
            diff += 1 if data[a + k] != data[b + k] else 0
            n += 1
            k += max(1, w // 32)
    return diff * 100.0 / n if n else None


WIDTHS = (8, 16, 24, 32, 48, 64, 96, 128, 160, 192, 224, 256, 288, 320, 336, 352, 384, 400, 416,
          448, 480, 512, 576, 640, 704, 768, 800, 896, 1024, 1280, 2048)

print('--- 8 bits par pixel ---')
c = sorted((s, w) for s, w in ((score(w, pix), w) for w in WIDTHS) if s is not None)
for s, w in c[:8]:
    print('  largeur %4d : %5.1f%%   (%d lignes, reste %d)' % (w, s, count // w, count % w))

print()
print('--- 4 bits par pixel (deux pixels par octet) ---')
nib = bytearray(count * 2)
for i, b in enumerate(pix):
    nib[i * 2] = b & 15
    nib[i * 2 + 1] = b >> 4
c = sorted((s, w) for s, w in ((score(w, nib), w) for w in WIDTHS) if s is not None)
for s, w in c[:8]:
    print('  largeur %4d : %5.1f%%   (%d lignes)' % (w, s, len(nib) // w))
