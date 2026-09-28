# -*- coding: utf-8 -*-
"""Passe les pages de nos decors de la couleur pleine aux huit bits indexes.

POURQUOI
--------
Le vidage de pages du jeu (`tex_remix/dump/manifest.txt`) porte la taille et la
profondeur de chaque page que 3SX decompresse. Depouillement des listes de fond --
132, 196, 228, 260, 292, 324 :

    liste 132   7180 entrees   128x128  8 bpp
    liste 196   4696 entrees   128x128  8 bpp
    liste 228    252 entrees   128x128  8 bpp
    liste 260   2776 entrees   128x128  8 bpp
    liste 292      2 entrees   128x128  8 bpp
    liste 324   1312 entrees   128x128  8 bpp

**Aucune exception sur plus de 16 000 relevees.** Toute page de fond du jeu est un
128 x 128 indexe a huit bits, seize kilo-octets. Les notres etaient les memes 128 x 128
mais en trente-deux bits, soixante-quatre kilo-octets : les seuls objets de cette
profondeur dans tout le jeu, exactement quatre fois le format de la maison.

SANS PERTE
----------
Compte sur les 2550 pages distinctes de New Generation et de 2nd Impact : **aucune ne
depasse 256 couleurs**, la pire en porte 206 (`stage24/196-226.tex`). Il n'y a donc
aucune quantification a faire -- un index par couleur, et c'est tout. L'echantillonnage
est deja en NEAREST, donc l'image sortie est identique au pixel pres. Chaque page est
d'ailleurs RELUE et comparee a l'originale avant d'etre remplacee.

Une page qui depasserait 256 couleurs garde la version 1, que `tex_remix` lit toujours.

    python pages_8bits.py                 # ce que ca donnerait, sans rien ecrire
    python pages_8bits.py --appliquer     # ecrit
"""
import glob
import os
import struct
import sys

import numpy as np

MAGIC, VERSION, VERSION_INDEXEE = 0x58545333, 1, 2
ENTETE = 16

RESSOURCES = os.path.join(
    os.environ.get("USERPROFILE", ""),
    "OneDrive", "Bureau", "SEPTEMBRE", "SF3", "CrowdedStreet-3SX", "resources")


def convertir(octets):
    """Rend les octets de la version 2, ou None si la page ne tient pas dans 256 couleurs."""
    magic, version, w, h = struct.unpack("<IIII", octets[:ENTETE])
    assert magic == MAGIC, "pas un .tex"
    if version != VERSION:
        return None                      # deja indexee, ou inconnue : on n'y touche pas

    px = np.frombuffer(octets, dtype=np.uint8, offset=ENTETE, count=w * h * 4).reshape(-1, 4).copy()

    # Un pixel transparent ne se voit pas -- le nuanceur le jette sur alpha nul. Les
    # ramener tous a la meme valeur ne change rien a l'image et n'occupe qu'un seul
    # emplacement de palette au lieu d'un par teinte invisible.
    px[px[:, 3] == 0] = 0

    mots = px.view(np.uint32).ravel()
    couleurs, indices = np.unique(mots, return_inverse=True)
    if len(couleurs) > 256:
        return None

    palette = np.zeros(256, dtype=np.uint32)
    palette[:len(couleurs)] = couleurs
    return (struct.pack("<IIII", MAGIC, VERSION_INDEXEE, w, h)
            + palette.tobytes() + indices.astype(np.uint8).tobytes())


def relire(octets):
    """Reconstitue les pixels d'une version 2, pour verifier qu'ils sont les bons."""
    magic, version, w, h = struct.unpack("<IIII", octets[:ENTETE])
    assert magic == MAGIC and version == VERSION_INDEXEE
    palette = np.frombuffer(octets, dtype=np.uint32, offset=ENTETE, count=256)
    indices = np.frombuffer(octets, dtype=np.uint8, offset=ENTETE + 1024, count=w * h)
    return palette[indices].view(np.uint8).reshape(-1, 4)


def attendu(octets):
    """Les pixels de la version 1, apres la seule normalisation qu'on s'autorise."""
    _, _, w, h = struct.unpack("<IIII", octets[:ENTETE])
    px = np.frombuffer(octets, dtype=np.uint8, offset=ENTETE, count=w * h * 4).reshape(-1, 4).copy()
    px[px[:, 3] == 0] = 0
    return px


def main():
    appliquer = "--appliquer" in sys.argv
    racine = os.path.join(RESSOURCES, "tex_remix")
    if not os.path.isdir(racine):
        print("introuvable :", racine)
        return 1

    faits = gardes = deja = 0
    avant = apres = 0
    refus = []

    for d in sorted(glob.glob(os.path.join(racine, "stage*"))):
        nom = os.path.basename(d)
        if "ancien" in nom or "avant" in nom:
            continue
        for chemin in sorted(glob.glob(os.path.join(d, "*.tex"))):
            octets = open(chemin, "rb").read()
            version = struct.unpack("<I", octets[4:8])[0]
            if version == VERSION_INDEXEE:
                deja += 1
                avant += len(octets)
                apres += len(octets)
                continue

            neuf = convertir(octets)
            avant += len(octets)
            if neuf is None:
                gardes += 1
                apres += len(octets)
                refus.append(os.path.join(nom, os.path.basename(chemin)))
                continue

            # ON NE REMPLACE RIEN SANS AVOIR RELU. La page reconstituee depuis les
            # indices doit etre celle d'avant, octet pour octet.
            if not np.array_equal(relire(neuf), attendu(octets)):
                print("ECART :", chemin)
                return 1

            apres += len(neuf)
            faits += 1
            if appliquer:
                with open(chemin, "wb") as f:
                    f.write(neuf)

    print("pages converties : %d" % faits)
    print("deja indexees    : %d" % deja)
    print("gardees en 32    : %d%s" % (gardes, (" -> " + ", ".join(refus[:5])) if refus else ""))
    print("poids : %.1f Mo -> %.1f Mo" % (avant / 1048576.0, apres / 1048576.0))
    if not appliquer:
        print("\n(rien n'a ete ecrit ; --appliquer pour ecrire)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
