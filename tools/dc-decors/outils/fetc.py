# -*- coding: utf-8 -*-
"""Lecteur de conteneur F_ETCnn (sprites animes de decor, SF3 Dreamcast).

Disposition retrouvee dans SF3_2ND.BIN : la fonction d'installation est a 0x8C0F6814.
Elle range chaque asset dans une entree de 24 octets et pose
  entree+4  = les donnees
  entree+12 = donnees + hdr[0x14]        -> la section graphique
  entree+16 = donnees + 32 - N*12        -> les animations, indexees globalement

En-tete de 32 octets :
  0x00 u32  premier index global d'animation (== la table du jeu, indexee par id)
  0x04 u32  dernier + 1
  0x08 u32  0
  0x0C u32  0
  0x10 u32  role non etabli
  0x14 u32  offset de la section graphique
  0x18 u32  0
  0x1C u32  0

Trois sections :
  1. a 0x20 : (hdr[4]-hdr[0]) enregistrements de 12 octets, une image d'animation chacun
     {u16 ?, s16 x, s16 y, u16 ?, u16 sprite, u16 ?}   -- repetes = temps de maintien
  2. jusqu'a hdr[0x14] : entrees de taille variable, un sprite chacune
     en-tete 8 octets {u16 largeur, u16 hauteur, u16 ?, u16 nb de morceaux}
     puis nb morceaux de 8 octets {u16 ?, u16 page, u16 ?, u16 ?}
  3. a hdr[0x14] : {u32 nombre, u32 offsets[nombre]} puis les blocs graphiques.
     Les offsets sont relatifs au debut de la section.
     Le codage des blocs n'est PAS celui des pages .pvc (mesure) et reste a percer.

Le parcours des sections 1 et 2 tombe pile sur la section 3 pour les 37 assets
des deux jeux.
"""
import struct

def lire(buf):
    h = struct.unpack_from('<8I', buf, 0)
    nanim = h[1] - h[0]
    o = 0x20
    anims = [struct.unpack_from('<HhhHHH', buf, o + i*12) for i in range(nanim)]
    o += nanim * 12
    s3 = h[5]
    sprites = []
    while o < s3:
        w, ht, c, np = struct.unpack_from('<4H', buf, o)
        parts = [struct.unpack_from('<4H', buf, o + 8 + k*8) for k in range(np)]
        sprites.append(dict(largeur=w, hauteur=ht, inconnu=c, morceaux=parts))
        o += 8 + np*8
    assert o == s3, f"parcours a {o}, section graphique a {s3}"
    n, = struct.unpack_from('<I', buf, s3)
    offs = list(struct.unpack_from(f'<{n}I', buf, s3+4)) + [len(buf) - s3]
    blocs = [buf[s3+offs[i]:s3+offs[i+1]] for i in range(n)]
    return dict(index_global=(h[0], h[1]), inconnu=h[4], anims=anims, sprites=sprites, blocs=blocs)
