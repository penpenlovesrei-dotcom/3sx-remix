# -*- coding: utf-8 -*-
"""Banque de palettes des sprites (SF3 Dreamcast).

Trouvee via la chaine de mise a jour de la palette RAM du PowerVR :
  0x8C619CB0  routine Katana : ecrit `r5` entrees u16 a 0x005F9000 + index*4
  0x8C0F594A  vidange : 8 emplacements, **64 entrees par appel**
  0x8C0F59AA  adresse d'une palette : 0x8C1E9AEC + offset - 0x02798000

La banque est **dans l'executable**, en ARGB1555, 64 couleurs (128 octets) par palette.
64 couleurs colle exactement aux index sur 6 bits que rendent les blocs graphiques.

  SF3_2ND.BIN : offset 0x1D9AEC (adresse 0x8C1E9AEC), 2715 palettes
  SF3_1ST.BIN : offset 0x1A8188 (adresse 0x8C1B8188), 2661 palettes

Ce qui manque encore : **quelle palette va avec quel sprite**. Ce n'est ni dans le
conteneur F_ETCnn (les champs 0, 3 et 5 des enregistrements d'animation sont nuls sur
les 16320 enregistrements des deux jeux, et les morceaux ne portent que page et
position), ni dans un champ d'en-tete connu. L'index vient du code, par etage.
"""
import numpy as np

BANQUES = {
    '2i': ('SF3_2ND.BIN', 0x1D9AEC, 2715),
    'ng': ('SF3_1ST.BIN', 0x1A8188, 2661),
}

def lire(chemin, offset, n):
    """Rend un tableau (n, 64, 3) d'octets RGB."""
    d = open(chemin, 'rb').read()
    u = np.frombuffer(d[offset:offset + n*128], dtype='<u2').reshape(n, 64)
    return np.dstack([((u >> 10) & 31)*255//31,
                      ((u >> 5) & 31)*255//31,
                      (u & 31)*255//31]).astype(np.uint8)

def opaque(chemin, offset, n):
    """Le bit 15 de chaque entree : 1 = opaque en ARGB1555."""
    d = open(chemin, 'rb').read()
    u = np.frombuffer(d[offset:offset + n*128], dtype='<u2').reshape(n, 64)
    return (u >= 0x8000)


def lire_brut(chemin, offset, n):
    """Rend un tableau (n, 64) des valeurs ARGB1555 TELLES QUELLES.

    `lire` convertit en RGB8 par `v*255//31`, ce qui n'est pas inversible : la valeur 1
    devient 8, et 8 ne redonne pas 1. Pour FABRIQUER une palette -- et non seulement
    l'afficher -- il faut les valeurs d'origine.
    """
    import numpy as np
    d = open(chemin, 'rb').read()
    return np.frombuffer(d[offset:offset + n * 128], dtype='<u2').reshape(n, 64).copy()
