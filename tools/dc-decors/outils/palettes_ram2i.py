# -*- coding: utf-8 -*-
"""L'EMPLACEMENT DE PALETTE RAM D'UN OBJET, et la palette du binaire qui le remplit.

`+554` d'un objet de 2I est son `my_col_code` (DECORS §5t). Ses neuf bits bas sont un
EMPLACEMENT de la palette RAM : 0x40 = 64 = 0x2000 / 128, la destination du premier jeu.
Le chargeur d'etage remplit la RAM par trois transferts (DECORS §3c-quater) :

    second jeu   0x8C1D5D14[bande*2]          -> dst 0x12000
    premier jeu  0x8C1D5D38[bande*2]          -> dst 0x2000
    secondaire   0x8C1D5D66[(bande-1)*2]      -> dst 0x2000 + nb1*128, en general

Un morceau d'offset `o` d'un objet d'emplacement `e` est donc peint avec l'emplacement
RAM `e + o`, et la palette du binaire est celle du transfert qui couvre cet emplacement.

    python palettes_ram2i.py 5      les transferts de la bande 5
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sh4

u16 = lambda a: sh4.u16(sh4.a2o(a))
u32 = lambda a: sh4.u32(sh4.a2o(a))
ENTREES = 0x8C1E4B50
RAM = 0x02798000


def entree(idx):
    src, dst, taille = u32(ENTREES + idx * 12), u32(ENTREES + idx * 12 + 4), u32(ENTREES + idx * 12 + 8)
    return dict(idx=idx, base=(src - RAM) // 128, dst=dst, nb=taille // 128)


def transferts(bande):
    out = [("second", entree(u16(0x8C1D5D14 + bande * 2))),
           ("premier", entree(u16(0x8C1D5D38 + bande * 2)))]
    if bande > 0:
        out.append(("secondaire", entree(u16(0x8C1D5D66 + (bande - 1) * 2))))
    return out


def palette(bande, emplacement, offset):
    """Le numero de palette du binaire pour l'emplacement RAM `emplacement + offset`."""
    slot = (emplacement & 0x1FF) + offset
    for _nom, e in transferts(bande):
        d = e["dst"] // 128
        if d <= slot < d + e["nb"]:
            return e["base"] + slot - d
    return None


if __name__ == "__main__":
    for b in sys.argv[1:]:
        b = int(b)
        for nom, e in transferts(b):
            print("bande %d  %-10s idx %3d  base %4d  nb %2d  emplacements %d..%d"
                  % (b, nom, e["idx"], e["base"], e["nb"], e["dst"] // 128, e["dst"] // 128 + e["nb"] - 1))
