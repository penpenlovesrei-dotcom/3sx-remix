# -*- coding: utf-8 -*-
"""Decoupe un decor de Double Impact en pages de texture pour un plan de 3SX.

La regle, mesuree des deux cotes :

* cote Dreamcast, une banque `.pvc` est un plan de 1024x1024 qui boucle, et le contenu
  s'y range en deux bandes separees a **y = 512**, sans une exception sur les 21 decors
  de 2nd Impact : la bande du haut est le plan lointain, celle du bas le plan proche
  (`bandes.py` les mesure).
* cote 3SX, `scr_trans()` pose la page `i` d'un plan en
  `x = (i & 7) * 128`, `y = 512 + (i >> 3) * 128` (`CARTES-BG.md`).

Donc chaque demi-banque de 1024x512 se pose **a l'identique** sur les 32 pages d'un plan :
la moitie basse telle quelle, la moitie haute remontee de 512. Aucun recadrage a la main.

    python bande3sx.py bg02 132:0xFFFFFFFF:haut 196:0xFFFFFFFF:bas ../etages2i/stage24
    python bande3sx.py bg09 132:0xFFFFFFFF:haut:1 196:0xFFFFFFFF:bas ../etages2i/stage30

Chaque argument de plan est `<base de liste>:<gbix>:<moitie>`. Les `.tex` sortent nommes
`<base>-<base+i>.tex`, ce que `tex_remix` attend pour un etage au-dela des 22 d'origine.
"""
import os, struct, sys
import numpy as np
import pvc
from rendupvc import carte_morton, SIDE

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAGIC, VERSION, VERSION_INDEXEE = 0x58545333, 1, 2


def banque_rgba(pages, first, carte):
    """1024x1024 RGBA. Page absente ou pixel a bit 15 nul -> transparent."""
    plat = np.zeros(SIDE * SIDE, dtype=np.uint16)
    pleine = np.zeros(SIDE * SIDE, dtype=bool)
    for p in range(SIDE * SIDE // 256):
        px = pages[first + p]
        if px is not None:
            plat[p*256:(p+1)*256] = np.asarray(px, dtype=np.uint16)
            pleine[p*256:(p+1)*256] = True
    img, occupe = plat[carte], pleine[carte]
    r = (((img >> 10) & 31).astype(np.uint16) * 255 // 31).astype(np.uint8)
    g = (((img >> 5) & 31).astype(np.uint16) * 255 // 31).astype(np.uint8)
    b = ((img & 31).astype(np.uint16) * 255 // 31).astype(np.uint8)
    # Transparent si et seulement si le pixel vaut 0x0000. Mesure sur les atlas : le bit 15
    # est arme exactement la ou le pixel n'est pas nul -- 40,9 % + 59,1 % = 100,0 % sur bg02.
    # Le repli d'avant ("si le bit 15 n'est jamais arme, la banque est opaque") rendait une
    # banque entierement vide en noir opaque : c'est ce qui faisait croire que la banque 1
    # de bg0b portait un plan.
    a = np.where(img != 0, 255, 0).astype(np.uint8)
    return np.dstack([r, g, b, a]), bool(((img >> 15) & 1).any())


def ecrire_tex(chemin, page):
    """Ecrit une page de decor. HUIT BITS des que la page tient dans 256 couleurs.

    Le jeu n'a jamais charge que du 128x128 a huit bits indexes -- 16 Ko la page, mesure
    sur les 26 000 pages du vidage, sans une exception. Nos decors etaient les seuls
    objets trente-deux bits de tout 3SX, quatre fois plus lourds que ceux d'a cote.

    Ils tiennent tous : sur les 2550 pages distinctes de New Generation et de 2nd Impact,
    la pire en porte 206 (`stage24/196-226.tex`). La conversion est donc SANS PERTE --
    aucune quantification, juste un index par couleur -- et l'echantillonnage etant deja
    en NEAREST, l'image sortie est identique.

    Au-dela de 256 couleurs on retombe sur la version 1, que `tex_remix` lit toujours.
    """
    h, w = page.shape[:2]
    p = page.copy()
    p[:, :, [0, 2]] = p[:, :, [2, 0]]           # rouge et bleu echanges : mesure a l'ecran

    # Un pixel transparent ne se voit pas : le nuanceur le jette sur alpha nul. Ramener
    # tous ces pixels a la meme valeur ne change rien a l'image et n'occupe qu'un seul
    # emplacement de palette au lieu d'un par teinte invisible.
    p[p[:, :, 3] == 0] = 0

    mots = p.reshape(-1, 4).view(np.uint32).ravel()
    couleurs, indices = np.unique(mots, return_inverse=True)

    with open(chemin, "wb") as f:
        if len(couleurs) <= 256:
            palette = np.zeros(256, dtype=np.uint32)
            palette[:len(couleurs)] = couleurs
            f.write(struct.pack("<IIII", MAGIC, VERSION_INDEXEE, w, h))
            f.write(palette.tobytes())
            f.write(indices.astype(np.uint8).tobytes())
        else:
            f.write(struct.pack("<IIII", MAGIC, VERSION, w, h))
            f.write(p.tobytes())


def decouper(decor, plans, sortie, surcouche=None):
    """`plans` = [(base de liste, gbix, moitie, banque)]. La banque est presque toujours 0 :
    le decor tient dans la premiere, coupe a y = 512. Quatre decors font exception -- leur
    banque 0 est une seule bande continue et c'est la **banque 1** qui porte le plan
    lointain. Ca se mesure, decor par decor : on garde celle qui laisse le moins de noir
    dans la zone jouee, et on regarde l'image avant de trancher."""
    src = os.path.join(RACINE, "pvc-2i", decor + ".pvc")
    if not os.path.exists(src):
        src = os.path.join(RACINE, "pvc-ng", decor + ".pvc")
    buf = open(src, "rb").read()
    pages, used, _ = pvc.decode(buf)
    assert used == len(buf), f"{decor} : consomme {used} sur {len(buf)}"
    carte = carte_morton(SIDE)
    banques = {}
    os.makedirs(sortie, exist_ok=True)
    for entree in plans:
        # Un cinquieme element, optionnel, remplace la banque par une image fournie :
        # c'est ce qui permet d'ecrire le TROISIEME plan de 3SX, qui ne porte pas de
        # fond mais seulement les sprites des plans de 2I qu'aucun objet ne pilote.
        base, gbix, moitie, bq = entree[:4]
        propre = entree[4] if len(entree) > 4 else None
        if propre is not None:
            arr = propre
            dy = 0 if moitie == "haut" else 512
            for i in range(32):
                if not (gbix & (0x80000000 >> i)):
                    continue
                x, y = (i & 7) * 128, dy + (i >> 3) * 128
                ecrire_tex(os.path.join(sortie, f"{base}-{base + i}.tex"), arr[y:y+128, x:x+128])
            print(f"   liste {base} : plan propre, {bin(gbix).count('1')} pages")
            continue
        if bq not in banques:
            b = banque_rgba(pages, bq * 4096, carte)[0]
            # `surcouche` est un RGBA de 1024x1024 dans le MEME repere que la banque :
            # les sprites de decor deja poses a leur place (`elements.py`). On les cuit
            # ici, avant la coupe, donc la moitie ou tombe un sprite se decide toute
            # seule par son y -- rien a arbitrer.
            if surcouche is not None and bq == 0:
                op = surcouche[:, :, 3] > 0
                b[op] = surcouche[op]
            banques[bq] = b
        arr = banques[bq]
        dy = 0 if moitie == "haut" else 512
        n = 0
        for i in range(32):
            if not (gbix & (0x80000000 >> i)):
                continue
            x, y = (i & 7) * 128, dy + (i >> 3) * 128
            ecrire_tex(os.path.join(sortie, f"{base}-{base + i}.tex"), arr[y:y+128, x:x+128])
            n += 1
        if moitie == "bas" and bq == 0:
            # De quoi resserrer limit_tbl3 : la camera est centree sur 0x200 et la fenetre
            # fait 384 px, donc elle montre le plan de (l - 192) a (r + 192). Une seule
            # colonne vide au bord de cette fenetre, et le plan lointain se voit sur toute
            # la hauteur : c'est la bande verticale.
            #
            # On prend donc la plus grande plage CONTINUE autour du centre ou le plan
            # proche n'a pas une colonne vide. Sans arrondir aux pages : l'arrondi elargit
            # la plage au-dela de l'art, et c'est lui qui remettait les bandes sur alex
            # (art 64..960 arrondi a 0..1024) et sur dudley.
            plein = (arr[768:1024, :, 3] > 0).mean(0) > 0.0
            x0 = x1 = 512
            while x0 > 0 and plein[x0 - 1]:
                x0 -= 1
            while x1 < 1024 and plein[x1]:
                x1 += 1
            # Un art qui touche le bord du plan (0 ou 1024) n'y est pas par hasard : c'est
            # du remplissage que le jeu d'origine ne montre pas -- les voiles du navire chez
            # hugo, par exemple. Les treize autres decors s'arretent d'eux-memes a 128..896,
            # et la planche de reference de 2nd Impact donne 124..896 sur bg02 : on rabat
            # donc sur cette largeur-la quand l'art deborde jusqu'au bord.
            if x0 == 0:
                x0 = 128
            if x1 == 1024:
                x1 = 896
            l, r = min(x0 + 192, 512), max(x1 - 192, 512)
            print(f"   art continu : x {x0}..{x1}"
                  f"   ->  limit_tbl3 = {{ {l:#06x}, {r:#06x}, 0xF0, 0xF0 }}   {r-l} px jouables")
        vide = sum(1 for i in range(32) if gbix & (0x80000000 >> i)
                   and not arr[(0 if moitie == "haut" else 512) + (i >> 3)*128:
                               (0 if moitie == "haut" else 512) + (i >> 3)*128 + 128,
                               (i & 7)*128:(i & 7)*128 + 128, 3].any())
        print(f"   liste {base} banque {bq} moitie {moitie} : {n} pages ecrites, dont {vide} vides")


def main():
    if len(sys.argv) < 4:
        print(__doc__); return
    decor = sys.argv[1]
    sortie = sys.argv[-1]
    plans = []
    for a in sys.argv[2:-1]:
        champs = a.split(":")
        base, gbix, moitie = champs[0], champs[1], champs[2]
        bq = int(champs[3]) if len(champs) > 3 else 0
        plans.append((int(base, 0), int(gbix, 0), moitie, bq))
    decouper(decor, plans, sortie)


if __name__ == "__main__":
    main()
