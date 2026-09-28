import io
import sys

path = sys.argv[1]
d = io.open(path, 'rb').read()
n = len(d)
print('=== %s : %d octets ===' % (path.rsplit('\\', 1)[-1], n))


def morton(x, y, n):
    i = 0
    bit = 0
    while (1 << bit) < n:
        i |= ((y >> bit) & 1) << (2 * bit)
        i |= ((x >> bit) & 1) << (2 * bit + 1)
        bit += 1
    return i


def rowdiff(data, off, side, twid):
    """sur une grille d index d un octet, cote 'side'"""
    need = side * side
    if off + need > len(data):
        return None
    diff = 0
    cnt = 0
    step = max(1, side // 48)
    for y in range(0, side - 1, step):
        for x in range(0, side, step):
            if twid:
                a = data[off + morton(x, y, side)]
                b = data[off + morton(x, y + 1, side)]
            else:
                a = data[off + y * side + x]
                b = data[off + (y + 1) * side + x]
            diff += 1 if a != b else 0
            cnt += 1
    return diff * 100.0 / cnt


print()
print('Hypothese VQ : codebook de 2048 octets a partir de PAYLOAD,')
print('puis un index d un octet par bloc de 2x2 pixels.')
print()
print('%-10s %-8s %10s %10s' % ('payload', 'grille', 'lineaire', 'entrelace'))
for payload in (0x80, 0x00):
    idx = payload + 2048
    for side in (64, 128, 256, 512):
        lin = rowdiff(d, idx, side, False)
        tw = rowdiff(d, idx, side, True)
        if lin is None:
            continue
        mark = ''
        if tw < 45:
            mark = '  <-- image plausible'
        elif tw < lin - 15:
            mark = '  <-- entrelace meilleur'
        print('0x%04X     %4dx%-4d %9.1f%% %9.1f%%%s' % (payload, side, side, lin, tw, mark))

print()
print('--- le codebook aurait-il l allure de couleurs ? ---')
import struct
cb = struct.unpack_from('<1024H', d, 0x80)
print('  1024 mots a 0x80 : %d valeurs distinctes' % len(set(cb)))
print('  %d%% ont le bit 15 arme' % (sum(1 for v in cb if v & 0x8000) * 100 // 1024))
print('  premiers : %s' % ' '.join('%04X' % v for v in cb[:12]))
print('  vers la fin : %s' % ' '.join('%04X' % v for v in cb[-12:]))
