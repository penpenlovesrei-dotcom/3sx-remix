# -*- coding: utf-8 -*-
"""Fabrique une archive de pages d'etage -- la NOTRE, sans emprunter celle d'un etage.

C'est ce qui leve la contrainte du donneur. Jusqu'ici un etage ajoute empruntait le bloc
de chargement d'un etage reel, et heritait de tout ce qui allait avec : le nombre de
plans de son archive, ses masques troues, et ses pixels partout ou on ne remplacait pas.
Avec une archive a nous, on choisit le nombre de pages, donc le nombre de plans.

LE FORMAT, lu dans `ppgSetupTexChunk_1st` et verifie sur l'archive de l'etage 2
(fichier 0x571 de SF33RD.AFS, 110932 octets, 52 chunks -- exactement ce que le jeu
compte a l'execution) :

    chunk pTEX, entete de 16 octets, gros-boutiste pour les deux u32 :
        u32 magic     'pTEX'
        u32 fileSize  entete comprise
        u8  width     en puissance de deux : 8 -> 256
        u8  height
        u8  compress  2 = zlib
        u8  pixel     129
        u16 formARGB
        u16 transNums
    charge utile zlib, le tout aligne sur 4 octets
    ...
    'pEND'  -- QUATRE octets, rien de plus : la boucle de lecture teste le magic
              avant de lire `fileSize`, et s'arrete la.

Le contenu des pages n'a aucune importance : `TexRemix_Substitute` les repeint une a une
apres decodage. On empile donc N fois un chunk modele pris dans une vraie archive, ce qui
garantit un chunk valide sans avoir a en synthetiser un.

    python archive.py 96 sortie.bin
"""
import os
import struct
import sys
import zlib

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
AFS = os.path.join(os.environ.get("APPDATA", ""), "CrowdedStreet", "3SX",
                   "resources", "SF33RD.AFS")

MAGIC_TEX = b"pTEX"
MAGIC_END = b"pEND"
ENTETE = 16


def entrees_afs(chemin=AFS):
    """(offset, taille) de chaque fichier de l'AFS."""
    with open(chemin, "rb") as f:
        assert f.read(4) == b"AFS\x00", "ce n'est pas une AFS"
        n = struct.unpack("<I", f.read(4))[0]
        return [struct.unpack("<II", f.read(8)) for _ in range(n)]


def lire_fichier(num, chemin=AFS):
    ent = entrees_afs(chemin)
    off, taille = ent[num]
    with open(chemin, "rb") as f:
        f.seek(off)
        return f.read(taille)


def decouper(données):
    """Les chunks pTEX d'une archive, en (offset, taille, largeur, hauteur)."""
    out = []
    o = 0
    while o + 8 <= len(données):
        if données[o:o + 4] != MAGIC_TEX:
            break
        fs = struct.unpack(">I", données[o + 4:o + 8])[0]
        out.append((o, fs, 1 << données[o + 8], 1 << données[o + 9]))
        o += (fs + 3) & ~3
    return out, o


def modele(num=1393):
    """Le plus petit chunk d'une vraie archive, aligne, pret a etre empile.

    Le plus petit parce que son contenu ne sert a rien -- il sera repeint -- et qu'une
    archive de 96 pages doit rester legere.
    """
    d = lire_fichier(num)
    chunks, _fin = decouper(d)
    assert chunks, "aucun chunk pTEX dans le fichier %d" % num
    o, fs, _l, _h = min(chunks, key=lambda c: c[1])
    return d[o:o + ((fs + 3) & ~3)]


def ecrire(nb_pages, sortie, num_modele=1393):
    m = modele(num_modele)
    with open(sortie, "wb") as f:
        for _ in range(nb_pages):
            f.write(m)
        f.write(MAGIC_END)
    return os.path.getsize(sortie)


def verifier(chemin):
    """Relit ce qu'on vient d'ecrire avec la meme boucle que le jeu."""
    d = open(chemin, "rb").read()
    chunks, fin = decouper(d)
    ok = d[fin:fin + 4] == MAGIC_END
    return len(chunks), ok, len(d)


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        return 1
    nb = int(sys.argv[1])
    sortie = sys.argv[2]
    taille = ecrire(nb, sortie)
    n, ok, total = verifier(sortie)
    print("%s : %d pages, %d octets" % (os.path.basename(sortie), n, total))
    print("relecture : %d chunks pTEX, pEND %s" % (n, "present" if ok else "ABSENT"))
    if n != nb or not ok:
        print("ECHEC : attendu %d pages et un pEND" % nb)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
