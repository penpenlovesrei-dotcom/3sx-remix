# -*- coding: utf-8 -*-
"""L'EMPLACEMENT DE PALETTE RAM D'UN OBJET DE NEW GENERATION -- le pendant de `palettes_ram2i`.

La regle de 2I (`+554` = `my_col_code`, ses neuf bits bas sont l'emplacement RAM) vaut
ici, avec les tables de NG :

    second jeu   0x8C18ABE4[bande*2]          -> dst 0x12000
    premier jeu  0x8C18AC10[bande*2]          -> dst 0x2000
    secondaire   0x8C18AC46[(bande-1)*2]      -> dst 0x2000 + nb1*128, en general
    entrees      0x8C1AAB7C, 12 octets        {src, dst, taille}, RAM 0x027B0000

CONTROLE -- 16/09/2026 : la seule correction de couleur NG validee, `BANQUES_NG[5]`
(offsets 0..8 -> base 1397, trouvee au detecteur de vert), tombe d'elle-meme : le
secondaire de la bande 5 est l'entree 106, destination 0x2A80 = emplacement 85, et
`+554` = 0x2055 y designe l'emplacement 85.

    python palettes_ramng.py 5      les transferts de la bande 5
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sh4ng as sh4

u16 = lambda a: sh4.U16(a)
u32 = lambda a: sh4.U32(a)
ENTREES = 0x8C1AAB7C
RAM = 0x027B0000
SECOND, PREMIER, SECONDAIRE = 0x8C18ABE4, 0x8C18AC10, 0x8C18AC46


def entree(idx):
    src, dst, taille = u32(ENTREES + idx * 12), u32(ENTREES + idx * 12 + 4), u32(ENTREES + idx * 12 + 8)
    return dict(idx=idx, base=(src - RAM) // 128, dst=dst, nb=taille // 128)


def transferts(bande):
    out = [("second", entree(u16(SECOND + bande * 2))),
           ("premier", entree(u16(PREMIER + bande * 2)))]
    if bande > 0:
        out.append(("secondaire", entree(u16(SECONDAIRE + (bande - 1) * 2))))
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
            print("bande %2d  %-10s idx %3d  base %4d  nb %2d  emplacements %d..%d"
                  % (b, nom, e["idx"], e["base"], e["nb"], e["dst"] // 128, e["dst"] // 128 + e["nb"] - 1))
