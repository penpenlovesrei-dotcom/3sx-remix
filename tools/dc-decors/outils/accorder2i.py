# -*- coding: utf-8 -*-
"""Quelle TABLE DE SCRIPTS va avec quel bloc — mesure, au lieu de supposer l'index.

`chargeurs2i.py` dit quel script d'etage appelle quel bloc. Mais l'index du script d'etage
n'est PAS celui de la table de scripts d'animation : le bloc d'Oro est appele par l'etage
d'index 10 et ne se resout que par la table d'index 9. Le decalage n'est pas explique, et
il n'est pas constant -- `bg00` n'en a pas.

On le mesure donc, par le seul critere qui separe nettement le bon du mauvais :

  * tous les enregistrements doivent se resoudre dans l'asset du decor ;
  * et le TOTAL D'IMAGES doit etre eleve. C'est ce qui a trahi l'erreur sur Oro : avec la
    bonne table ses huit objets rendaient 14, 16, 12, 9, 9, 9, 11 et 2 images ; avec la
    mauvaise, **une seule image chacun**. Un objet anime a plusieurs images ; une table
    qui n'en rend qu'une par objet n'est pas la sienne.

    python accorder2i.py bg01 0x8C17E7A8 6
    python accorder2i.py bg01               tous les blocs connus
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import annuaire2i as AN
import assemblage as A
import bases
import poser2i as P
import sh4

_D, _B = sh4.D, sh4.BASE
u8 = lambda a: _D[a - _B]
u16 = lambda a: struct.unpack_from('<H', _D, a - _B)[0]
s16 = lambda a: struct.unpack_from('<h', _D, a - _B)[0]
u32 = lambda a: struct.unpack_from('<I', _D, a - _B)[0]

# Ce que `chargeurs2i.py` a releve : (bloc, nombre, index du script d'etage appelant).
BLOCS = [
    (0x8C17C210, 2, 2), (0x8C17E7A8, 6, 2),
    (0x8C17C230, 2, 3), (0x8C17E808, 2, 3),
    (0x8C17E828, 1, 4),
    (0x8C17C260, 5, 5), (0x8C17E838, 10, 5),
    (0x8C17C2B0, 2, 6), (0x8C17E8D8, 3, 6),
    (0x8C17C310, 1, 9),
    (0x8C17C320, 1, 10), (0x8C17E918, 8, 10),
    (0x8C17C250, 1, 11), (0x8C17E998, 1, 11),
    (0x8C17E9A8, 2, 13),
    (0x8C17C2F0, 2, 16), (0x8C17E908, 1, 16),
]


def images_du_script(decor, sc):
    """[index global] du script, ou None si le script n'existe pas dans cette table."""
    t, n = AN.table_scripts(decor)

    if not 0 <= sc < n:
        return None

    p = u32(t + sc * 4)
    out = []

    for k in range(96):
        cmd, duree, idx = u8(p + k * 8), u8(p + k * 8 + 1), u16(p + k * 8 + 6)

        if cmd == 0x01:
            break

        if cmd == 0x00 and duree:
            out.append(idx)

    return out


def essayer(bg, bloc, nb, table):
    """(resolus, total d'images, positions) du bloc lu avec la table de scripts `table`."""
    a, _t = P.asset(bases.ASSETS[bg])
    lo = a["index_global"][0]
    n = len(a["anims"])
    resolus = 0
    total = 0
    xs = []

    for k in range(nb):
        ad = bloc + k * 16
        sc = u16(ad + 10)
        ims = images_du_script(table, sc)

        if not ims or not all(lo <= i < lo + n for i in ims):
            continue

        resolus += 1
        total += len(ims)
        xs.append(s16(ad + 4))

    etendue = (max(xs) - min(xs)) if len(xs) > 1 else 0
    return resolus, total, etendue


def main():
    bg = sys.argv[1]

    if len(sys.argv) >= 4:
        cands = [(int(sys.argv[2], 0), int(sys.argv[3]), None)]
    else:
        cands = BLOCS

    print("asset %s (%s)\n" % (bg, bases.ASSETS[bg]))
    print("%-10s %-4s %-6s %s" % ("bloc", "nb", "etage", "meilleures tables de scripts"))

    for bloc, nb, etage in cands:
        notes = []

        for table in range(17):
            r, tot, et = essayer(bg, bloc, nb, table)

            if r == nb and tot > nb:          # tout resolu, et pas une image par objet
                notes.append((tot, table, et))

        notes.sort(reverse=True)

        if not notes:
            continue

        print("%08X   %-4d %-6s %s" % (bloc, nb, etage,
              "  ".join("table %d : %d images, x sur %d" % (t, tot, et)
                        for tot, t, et in notes[:3])))


if __name__ == "__main__":
    main()
