# -*- coding: utf-8 -*-
"""L'ETAGE RENDU DEPUIS `decor_objets_data.c` LUI-MEME — les tuiles, pas les sprites.

POURQUOI CET OUTIL EXISTE
-------------------------
`apercu_etage.py` relit les POSITIONS dans le C, mais redessine les images depuis les
sprites du disque. Il reste donc une hypothese entre lui et le jeu : que les tuiles emises
soient bien celles qu'il croit. Cet outil-la n'en fait aucune -- il decode les 256 octets
de chaque `DecorTuile`, les depose a la case que le moteur en deduit, et colore avec la
palette de la fiche. **C'est exactement ce que le jeu televerse.**

Il repond donc a la seule question qui compte quand Frederic voit un objet en double ou a
cote : est-ce la DONNEE qui est fausse, ou le moteur qui la place mal ?

    python rendu_fiches.py 25 bg03        l'etage de Yun
    python rendu_fiches.py 25 bg03 --nu   les objets seuls, sans le decor
"""
import io
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw

import animations as AN0
import poser2i as P

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE = os.path.join(RACINE, "rendus")
DATA = r"C:\Temp3sx\src\port\video\decor_objets_data.c"

# L'inverse de `animations.entrelacer`. Celle-ci ecrit `out[TABLE[k]] = plat[k]` ; on relit
# donc `plat[k] = out[TABLE[k]]`, c'est-a-dire une simple indexation PAR `TABLE`. La
# permutation inverse -- `DETABLE[TABLE[k]] = k` -- rend des rayures : c'est l'autre sens.
DETABLE = np.array(AN0.TABLE, np.int32)

FICHE = re.compile(r'\{\s*"(\w+)",([^}]*)\}\s*,\s*/\*([^*]*)\*/')
TABLEAU = re.compile(r"static const unsigned char (\w+)\[256\] = \{([^}]*)\};")
PALETTE = re.compile(r"static const unsigned short (\w+)\[64\] = \{([^}]*)\};")
TUILES = re.compile(r"static const DecorTuile (\w+)\[\] = \{(.*?)\};", re.S)
ENTREE = re.compile(r"\{\s*(\d+),\s*(\d+),\s*(\d+),\s*(\w+)\s*\}")


def charger():
    """Le C entier, decode : les tuiles, les tables de cases et les palettes."""
    src = io.open(DATA, encoding="utf-8", errors="surrogateescape").read()
    octets = {n: np.array([int(v) for v in c.split(",") if v.strip()], np.uint8)
              for n, c in TABLEAU.findall(src)}
    palettes = {n: [int(v, 0) for v in c.split(",") if v.strip()]
                for n, c in PALETTE.findall(src)}
    cases = {n: [(int(a), int(b), int(d), e) for a, b, d, e in ENTREE.findall(c)]
             for n, c in TUILES.findall(src)}
    return src, octets, palettes, cases


def rgba_de(idx16, palette):
    """Une tuile 16x16 d'index, coloree par la palette 64 entrees en ARGB1555."""
    pal = np.array(palette, np.uint16)
    v = pal[np.clip(idx16, 0, len(pal) - 1)].astype(np.uint32)
    out = np.zeros(idx16.shape + (4,), np.uint8)
    out[..., 0] = ((v >> 10) & 31) * 255 // 31
    out[..., 1] = ((v >> 5) & 31) * 255 // 31
    out[..., 2] = (v & 31) * 255 // 31
    # L'index 0 est transparent -- c'est la regle de la ColorRAM, pas le bit de la couleur.
    out[..., 3] = np.where(idx16 != 0, 255, 0)
    return out


def main():
    etage = int(sys.argv[1]) if len(sys.argv) > 1 else 25
    bg = sys.argv[2] if len(sys.argv) > 2 else "bg03"
    nu = "--nu" in sys.argv
    image_voulue = 0
    variante = -1

    for a in sys.argv:
        if a.startswith("--image="):
            image_voulue = int(a.split("=")[1])
        if a.startswith("--variante="):
            variante = int(a.split("=")[1])

    src, octets, palettes, cases = charger()
    fond = Image.new("RGBA", (1024, 1024), (0, 0, 0, 255))

    # LE DOSSIER DES PAGES N'EST LU QUE SI ON LE DESSINE. Il etait lu dans tous les cas, et
    # `--nu` echouait donc sur les etages de New Generation, qui n'en ont pas -- alors que
    # c'est justement le mode qui n'en a pas besoin.
    if not nu:
        dossier = os.path.join(RACINE, "etages2i-sprites", "stage%d" % etage)
        listes = sorted({int(f.split("-")[0]) for f in os.listdir(dossier)})

        for l in listes:
            page = P.lire_liste(dossier, l)

            if page is not None:
                fond.alpha_composite(Image.fromarray(page, "RGBA"))

    d = ImageDraw.Draw(fond)
    n = 0

    for m in FICHE.finditer(src):
        ch = [c.strip() for c in m.group(2).split(",")]

        if len(ch) < 15 or m.group(1) != bg or int(ch[0]) != etage:
            continue

        masque = int(ch[14], 0)

        if variante >= 0 and masque and not masque & (1 << variante):
            continue

        cols, ligs = int(ch[3]), int(ch[4])
        nom_t, nom_p = ch[5], ch[7]
        x, y = int(ch[9]), int(ch[10])
        bank_y = 1024 - y - (ligs - 1) * 16
        pal = palettes.get(nom_p)

        if pal is None or nom_t not in cases:
            continue

        for image, tx, ty, nom_px in cases[nom_t]:
            if image != image_voulue or nom_px not in octets:
                continue

            # LE `y` D'UNE TUILE EST EN REPERE IMAGE, pas en repere moteur : le generateur
            # ecrit `lig * 16`, et c'est le moteur qui le retourne au moment de chercher
            # (`t->y == y_moteur(a, y)`, une involution). Le renverser ici sortait les
            # objets en morceaux empiles a l'envers.
            plat = octets[nom_px][DETABLE].reshape(16, 16)
            fond.alpha_composite(Image.fromarray(rgba_de(plat, pal), "RGBA"),
                                 (x + tx, bank_y + ty))

        note = m.group(3).strip()
        sc = re.search(r"script (\d+)", note)
        d.rectangle([x, bank_y, x + cols * 16 - 1, bank_y + ligs * 16 - 1],
                    outline=(255, 0, 255, 255))
        d.text((x + 1, bank_y - 10), "%s s%s" % (ch[5].replace("_tuiles", ""),
                                                 sc.group(1) if sc else "?"),
               fill=(255, 255, 0, 255))
        print("%-14s script %-3s  x %-4d bank_y %-4d  %dx%d cases  palette %s"
              % (ch[5].replace("_tuiles", ""), sc.group(1) if sc else "?", x, bank_y,
                 cols, ligs, ch[8]))
        n += 1

    os.makedirs(SORTIE, exist_ok=True)
    chemin = os.path.join(SORTIE, "fiches-%d%s.png" % (etage, "-nu" if nu else ""))
    fond.save(chemin)
    print("\n%d fiches  ->  %s" % (n, chemin))


if __name__ == "__main__":
    main()
