# -*- coding: utf-8 -*-
"""L'annuaire des objets ANIMES : la SIXIEME table de la serie `0x8C5F9B38`.

Le meme verrou que les elements statiques, et la meme cle. `annuaire2i.py` a montre que
`0x8C5F9B38` est la premiere d'une serie de dix tables de 51 entrees (17 decors x 3 aires)
posees bout a bout, et que la DEUXIEME porte les elements de decor. La **sixieme** --
`0x8C5F9B38 + 5*204 = 0x8C5F9F34` -- porte les objets ANIMES : ses pointeurs valent, eux
aussi, **deux octets avant** le premier enregistrement, et le bloc va jusqu'au pointeur
distinct suivant.

    8C17E7A6  ->  8C17E7A8    8C17E836  ->  8C17E838    8C17E916  ->  8C17E918
    8C17E806  ->  8C17E808    8C17E8D6  ->  8C17E8D8    8C17E996  ->  8C17E998

Le bloc d'Oro trouve a la main -- `0x8C17E928`, sept enregistrements -- est **la queue**
de l'un d'eux : le bloc `0x8C17E918` en compte huit.

CE QUI DECIDE DU DECOR N'EST PAS L'INDEX DE LA TABLE
----------------------------------------------------
Lue comme les autres, la sixieme table rangerait ces blocs sous les decors 3 a 6. C'est
faux, et l'epreuve de `SANS-ETAT.md` le dit : le numero de script d'un enregistrement doit
s'entendre dans la table de scripts **de son decor**, et l'index global obtenu doit tomber
dans l'asset F_ETC **du meme decor**. On ne suppose donc rien : on essaie les dix-sept
decors sur chaque bloc, et on garde celui qui les resout TOUS.

    python annuaire_animes.py            les blocs de la region, et leur decor
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

SERIE = 0x8C5F9B38
NB_AIRES = 51
ANIMES = SERIE + 5 * NB_AIRES * 4          # 0x8C5F9F34

# `bases.ASSETS` est indexe par nom de bande ; il faut le numero de decor.
BG_DE_DECOR = {0: "bg00", 1: "bg01", 2: "bg02", 3: "bg03", 4: "bg04", 5: "bg05",
               6: "bg06", 8: "bg08", 9: "bg0a", 10: "bg0b", 11: "bg0c", 12: "bg0d",
               13: "bg0e", 16: "bg10"}


def script_images(decor, sc):
    """[(index global, duree)] d'un script, ou None si le script n'existe pas."""
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
            out.append((idx, duree))

    return out


def lire(adresse):
    """L'enregistrement de 16 octets, au format de l'annuaire."""
    return dict(adresse=adresse, plan=u16(adresse), drapeaux=u16(adresse + 2),
                x=s16(adresse + 4), y=u16(adresse + 6),
                palette=u16(adresse + 8), script=u16(adresse + 10))


def resout(decor, e):
    """(index global, numero de sprite) si l'enregistrement tient dans CE decor."""
    if decor not in BG_DE_DECOR:
        return None

    ims = script_images(decor, e["script"])

    if not ims:
        return None

    a, _tuiles = P.asset(bases.ASSETS[BG_DE_DECOR[decor]])
    lo = a["index_global"][0]
    n = len(a["anims"])

    if not all(lo <= i < lo + n for i, _d in ims):
        return None

    offs = sorted({r[4] for r in a["anims"]})
    return ims[0][0], offs.index(a["anims"][ims[0][0] - lo][4])


def blocs():
    """[(debut, nombre)] des blocs de la sixieme table, dans l'ordre des adresses."""
    p = sorted({u32(ANIMES + k * 4) for k in range(NB_AIRES)})
    out = []

    for i, a in enumerate(p[:-1]):
        out.append((a + 2, (p[i + 1] - a) // 16))

    return out


def decor_du_bloc(deb, nb):
    """(decor, resolus, total) : le decor qui resout le plus d'enregistrements."""
    best = (None, -1)

    for d in BG_DE_DECOR:
        c = sum(1 for k in range(nb) if resout(d, lire(deb + k * 16)))

        if c > best[1]:
            best = (d, c)

    return best[0], best[1], nb


def main():
    for deb, nb in blocs():
        if not 0x8C17E000 <= deb < 0x8C180000 or not 1 <= nb <= 64:
            continue

        d, bons, tot = decor_du_bloc(deb, nb)
        print("bloc %08X  %2d enregistrement(s)  ->  decor %s (%s)  %d/%d resolus"
              % (deb, tot, d, BG_DE_DECOR.get(d), bons, tot))

        for k in range(nb):
            e = lire(deb + k * 16)
            r = resout(d, e)
            print("      %08X  plan %d  x %5d  y %3d  pal %3d  script %2d  %s"
                  % (e["adresse"], e["plan"], e["x"], e["y"], e["palette"],
                     e["script"],
                     "index %5d  sprite %3d" % r if r else "NE RESOUT PAS"))


if __name__ == "__main__":
    main()
