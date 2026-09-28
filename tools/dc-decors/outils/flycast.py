# -*- coding: utf-8 -*-
"""Lecture d'un etat sauvegarde Flycast : rend la RAM principale de la Dreamcast.

Le fichier commence par un en-tete `FLYSAVE1`, une vignette PNG, puis la charge utile
au format **#RZIPv** : des tranches zlib de 1 Mo, chacune precedee de sa longueur
compressee sur 4 octets.

La RAM (16 Mo, adresse 0x8C000000) est reperee **par signature**, pas par offset :
l'executable du jeu est charge a 0x8C010000, donc les premiers octets de `SF3_2ND.BIN`
apparaissent tels quels dans le flux. On cherche ou, et on en deduit la base.
"""
import struct, zlib, os

BASE_RAM = 0x8C000000
TAILLE_RAM = 16 * 1024 * 1024

def charge_utile(chemin):
    """Rend la charge utile decompressee de l'etat."""
    d = open(chemin, 'rb').read()
    if d[:8] != b'FLYSAVE1':
        raise ValueError('ce n\'est pas un etat Flycast (FLYSAVE1 attendu)')
    taille_png, = struct.unpack_from('<I', d, 20)
    o = 24 + taille_png
    if d[o:o+6] != b'#RZIPv':
        raise ValueError('charge utile inattendue : %r' % d[o:o+8])
    tranche, = struct.unpack_from('<I', d, o + 8)
    total, = struct.unpack_from('<Q', d, o + 12)
    p = o + 20
    morceaux = []
    while sum(len(m) for m in morceaux) < total and p + 4 <= len(d):
        n, = struct.unpack_from('<I', d, p); p += 4
        if n == 0 or p + n > len(d):
            break
        morceaux.append(zlib.decompress(d[p:p+n])); p += n
    return b''.join(morceaux), tranche, total

def base_ram(flux, exe):
    """Offset de la RAM dans le flux, trouve par la signature de l'executable."""
    temoin = open(exe, 'rb').read(256)
    i = flux.find(temoin)
    while i != -1:
        if i >= 0x10000 and i - 0x10000 + TAILLE_RAM <= len(flux):
            return i - 0x10000
        i = flux.find(temoin, i + 1)
    return None

def lire_ram(chemin, exe):
    """Rend (ram, offset_dans_le_flux). `ram` s'indexe par adresse - 0x8C000000."""
    flux, _, _ = charge_utile(chemin)
    b = base_ram(flux, exe)
    if b is None:
        raise ValueError('RAM introuvable : la signature de %s n\'apparait pas' % os.path.basename(exe))
    return flux[b:b+TAILLE_RAM], b

def u8(ram, a):  return ram[a - BASE_RAM]
def u16(ram, a): return struct.unpack_from('<H', ram, a - BASE_RAM)[0]
def s16(ram, a): return struct.unpack_from('<h', ram, a - BASE_RAM)[0]
def u32(ram, a): return struct.unpack_from('<I', ram, a - BASE_RAM)[0]
def s32(ram, a): return struct.unpack_from('<i', ram, a - BASE_RAM)[0]
