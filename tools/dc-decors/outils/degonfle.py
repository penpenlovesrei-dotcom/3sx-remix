# -*- coding: utf-8 -*-
"""Decompresseurs des blocs graphiques F_ETCnn (SF3 Dreamcast).

Traduits des routines SH-4 de SF3_2ND.BIN. Les deux rendent **4096 octets**, ecrits
**a rebours** depuis la fin du tampon (le code fait `mov.b rX,@-r5`).

Schema A -- 0x8C0F6548, octets de commande + table de valeurs recentes
  Une table circulaire de 16 valeurs, initialisee a 1..16 ; `dernier` retient la
  derniere valeur emise (initialise a 17).
    b & 0x80 : n = (b & 7) + 1 copies de table[(b >> 3) & 15] ; dernier = cette valeur
    b & 0x40 : n = (b & 31) + 1 copies de `dernier` si b & 0x20, sinon de 0
    sinon    : litteral b (0..0x3F), ecrit une fois, range dans la table, dernier = b

Schema B -- 0x8C0F663C, RLE a drapeaux
  512 tours de 8 sorties. Un octet de controle par tour ; le bit k dit s'il faut lire
  un nouvel octet avant la sortie k. Sinon on repete le precedent. 512 x 8 = 4096.

Aucun champ connu ne dit lequel s'applique : on essaie, et la double contrainte
(consommer tout le bloc ET remplir exactement 4096) tranche sans ambiguite.
"""
TAILLE = 4096

def schema_a(src, taille=TAILLE):
    out = bytearray(taille)
    table = bytearray(range(1, 17))
    pos = 0; dernier = 17
    p = taille; i = 0
    while p > 0 and i < len(src):
        b = src[i]; i += 1
        if b & 0x80:
            v = table[(b >> 3) & 15]; n = (b & 7) + 1; dernier = v
        elif b & 0x40:
            v = dernier if (b & 0x20) else 0; n = (b & 31) + 1
        else:
            table[pos] = b; pos = (pos + 1) & 15; dernier = b; v = b; n = 1
        for _ in range(n):
            p -= 1
            if p < 0: return bytes(out), i, p
            out[p] = v
    return bytes(out), i, p

def schema_b(src, taille=TAILLE):
    out = bytearray(taille)
    p = taille; i = 0; v = 0
    while p > 0 and i < len(src):
        ctrl = src[i]; i += 1
        if ctrl & 1:
            if i >= len(src): break
            v = src[i]; i += 1
        for k in range(8):
            p -= 1
            if p < 0: return bytes(out), i, p
            out[p] = v
            if k < 7 and ((ctrl >> (k+1)) & 1):
                if i >= len(src): break
                v = src[i]; i += 1
    return bytes(out), i, p

def degonfler(src, souple=False):
    """Essaie les deux schemas. Rend (octets, nom du schema) ou leve ValueError.
    `souple` accepte qu'il reste du bourrage apres le flux (dernier bloc d'un fichier)."""
    for nom, fn in (('A', schema_a), ('B', schema_b)):
        out, used, p = fn(src)
        if p == 0 and (used == len(src) or (souple and used <= len(src))):
            return out, nom
    raise ValueError('aucun schema ne rend un bloc exact')
