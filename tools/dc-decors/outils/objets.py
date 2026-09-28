# -*- coding: utf-8 -*-
"""Exporte un sprite anime de 2nd Impact en tuiles pretes pour le moteur de 3SX.

POURQUOI CE FORMAT-LA, ET PAS UN AUTRE
--------------------------------------
Un objet de decor de 3SX est dessine morceau par morceau. Chaque morceau est un
**chip de 16x16 en index sur 8 bits, soit 256 octets** -- exactement le format de nos
tuiles. `mtrans.c` le decomprime dans `mt->mltbuf` puis le televerse :

    size = (wh * wh) << 6;                               256 pour un 16x16
    lz_ext_p6_fx(&((u8*)texptr)[1], mt->mltbuf, size);
    njReLoadTexturePartNumG(page, mltbuf, chip, size);

Il suffit donc de recopier NOS 256 octets dans `mltbuf` juste apres la decompression.
Rien d'autre a percer : ni format d'archive, ni nouveau groupe, et surtout pas
`tex_remix`, qui ne voit jamais ces pages -- elles ne passent pas par
`ppgSetupTexChunk_3rd`.

La grille, elle, reste celle du motif donneur : c'est lui qui dit ou tombe chaque
morceau. On repere donc nos tuiles **par leur position dans la grille**, et on rend un
morceau vide partout ailleurs pour que l'art du donneur ne transparaisse pas.

CE QUE CE PROGRAMME SORT
------------------------
Un fichier C compilable, `port/video/decor_objets_data.c`, avec :

  * `DECOR_NB_IMAGES` images,
  * pour chacune, une grille de tuiles reperees par (x, y) dans le repere du motif,
  * les 256 octets d'index de chaque tuile.

Les index sont ceux de nos tuiles, sur 6 bits. La palette employee a l'ecran sera celle
de l'objet (`my_col_code`) : les couleurs seront donc approximatives tant qu'on n'aura
pas installe la notre. La FORME et le MOUVEMENT, eux, seront justes -- c'est ce qu'on
cherche d'abord.

    python objets.py                 la ventilation d'Alex, trois images
    lanceur : objets.cmd
"""
import os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import assemblage

ICI    = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
SORTIE = r"C:\Temp3sx\src\port\video\decor_objets_data.c"

# L'asset, les sprites qui forment l'animation, et ou poser la tuile (0,0) dans la
# grille du motif donneur.
#
# LA GRILLE EST LA NOTRE MAINTENANT. On n'emprunte plus la liste de morceaux du donneur :
# `DecorObjets_Motif` la recrit, neuf morceaux de 16x16 en 3x3, aux positions
#
#     x = 0, 16, 32        y = 0, 16, 32
#
# L'origine est donc (0, 0), et elle ne peut plus se desaccorder de la grille : les deux
# viennent du meme endroit. C'est ce qui a manque a la version d'avant -- on cherchait a
# faire coincider nos tuiles avec une grille qu'on ne maitrisait pas, et un signe inverse
# dans mon decodage hors ligne suffisait a ce qu'aucune ne tombe jamais juste.
ASSET   = "2i-b01-F_ETC34"
IMAGES  = [2, 3, 4]          # la boule metallique dans ses trois positions
ORIGINE = (0, 0)             # coin haut-gauche de notre sprite dans le repere du motif


def table_entrelacement():
    """La table que `ppgMakeConvTableTexDC` construit dans 3SX, reproduite a l'identique.

    Le televersement d'un chip ne prend pas les octets tels quels : il lit la source a
    travers cette table (`PPGFile.c`, `ppgRenewDotDataSeqs`, cas 0x100) --

        for (i = 0; i < 16; i++)
            for (j = 0; j < 16; j++)
                *dst++ = src[dctex_linear[j + (i << 5)]];

    -- donc `dest(i, j) = src[T[j + i * 32]]`. Le moteur attend ses 256 octets **en ordre
    entrelacé**, pas lineaire. Nos tuiles etant lineaires, elles sortaient en bruit : c'est
    ce qui faisait un pave de rayures a la place de la ventilation.

    Rend la liste des 256 indices, qui est une permutation exacte de 0..255 -- verifie.
    """
    seed = [0x0000, 0x0002, 0x0008, 0x000A, 0x0020, 0x0022, 0x0028, 0x002A,
            0x0080, 0x0082, 0x0088, 0x008A, 0x00A0, 0x00A2, 0x00A8, 0x00AA,
            0x0200, 0x0202, 0x0208, 0x020A, 0x0220, 0x0222, 0x0228, 0x022A,
            0x0280, 0x0282, 0x0288, 0x028A, 0x02A0, 0x02A2, 0x02A8, 0x02AA]
    ajout = [0x0000, 0x0004, 0x0010, 0x0014, 0x0040, 0x0044, 0x0050, 0x0054,
             0x0100, 0x0104, 0x0110, 0x0114, 0x0140, 0x0144, 0x0150, 0x0154]
    t = [0] * 1024
    for i in range(16):
        for j in range(32):
            t[j + i * 64] = seed[j] + ajout[i]
        for j in range(32):
            t[j + i * 64 + 32] = t[j + i * 64] + 1
    return [t[j + i * 32] for i in range(16) for j in range(16)]


TABLE = table_entrelacement()
assert sorted(TABLE) == list(range(256)), "la table doit etre une permutation de 0..255"


def entrelacer(tuile):
    """Range une tuile 16x16 lineaire dans l'ordre que le televersement attend."""
    out = bytearray(256)
    for i in range(16):
        for j in range(16):
            out[TABLE[j + i * 16]] = tuile[i][j]
    return bytes(out)


def tuiles_du_sprite(chemin, index):
    """Rend {(col, lig): 256 octets} pour un sprite, decoupe en tuiles de 16x16."""
    r, ts = assemblage.charger(chemin)
    pose = assemblage.poser(r["sprites"][index], ts)
    if pose is None:
        return None, 0, 0
    img, msk, _x0, _y0 = pose
    h, w = img.shape
    # Un morceau vide est un index 0 : le moteur le traite comme transparent.
    img = np.where(msk, img, 0).astype(np.uint8)
    out = {}
    for lig in range((h + 15) // 16):
        for col in range((w + 15) // 16):
            t = np.zeros((16, 16), np.uint8)
            a = img[lig * 16:lig * 16 + 16, col * 16:col * 16 + 16]
            t[:a.shape[0], :a.shape[1]] = a
            out[(col, lig)] = entrelacer(t)
    return out, w, h


def palette_du_jeu():
    """Les 64 entrees de la palette que le jeu emploie pour cet element, telles quelles.

    On sort l'ARGB1555 de la palette RAM de la Dreamcast **sans le toucher**, et c'est le
    port qui convertit : `DecorObjets_InstallerPalette` echange rouge et bleu en ecrivant
    dans `ColorRAM`. Ne pas convertir ici, sous peine de le faire deux fois.

    ATTENTION -- ce qui etait ecrit ici etait faux : `ColorRAM` n'est PAS en ARGB1555, elle
    est en **ABGR1555**. `palCreateGhost` le construit ainsi (`palFormRam.rs = 0`,
    `palFormRam.bs = 10`, contre `rs = 10` et `bs = 0` pour `palFormSrc`) et `col_edit.c`
    le nomme au-dessus de `swatch_color` : "red sits in the low bits and blue in the high
    ones, the reverse of the archive's ARGB1555. Getting this backwards is the same mistake
    that once turned every fighter's skin blue, and it passes every numeric check."
    La ligne de `col_edit.c` qui servait de preuve, `(grey << 10) | (grey << 5) | grey`,
    ecrit un GRIS : il est invariant par l'echange et ne temoigne de rien.

    L'emplacement vient de l'etat Flycast : pour l'element 5 de `bg01`, l'octet +9 a son
    bit 5 arme, donc la palette est le mot +8 de l'element, masque a 0x1FF.
    """
    import glob
    import numpy as np
    import flycast as F, etat as E, elements as X

    etats = sorted(glob.glob(os.path.join(X.DOS, X.MOTIF)))
    ch = [c for c in etats
          if os.path.splitext(os.path.basename(c))[0].endswith("Impact_17")]
    if not ch:
        return None
    ram, _ = F.lire_ram(ch[0], E.EXE)
    base, el = X.liste(ram)
    e = [x for x in el if x["i"] == 5]
    if not e:
        return None
    empl = (e[0]["mot"] if e[0]["octet9"] & 0x20 else 0) & 0x1FF
    o = X.PALRAM - F.BASE_RAM + empl * 128
    return empl, np.frombuffer(ram[o:o + 128], dtype="<u2").tolist()


def mire():
    """Neuf tuiles d'aplat, et une palette de neuf couleurs franches.

    C'est un test qui separe la PLOMBERIE du CONTENU en une seule partie. Si l'ecran
    montre une grille 3x3 d'aplats nets dans le bon ordre, alors la geometrie,
    l'entrelacement, la palette et le cache sont tous justes, et ce qui cloche est dans
    nos pixels. Sinon, chaque ecart designe un maillon :

        rien du tout        l'objet n'est pas dessine
        aplats brouilles    l'entrelacement ou le televersement
        mauvaises couleurs  la palette
        cases manquantes    la geometrie

    Les couleurs sont volontairement criardes : on doit pouvoir les nommer sans hesiter.
    """
    couleurs = [0x0000,          # 0 transparent
                0xFC00, 0x83E0, 0x801F, 0xFFE0, 0xFC1F, 0x83FF, 0xFFFF, 0x8C63, 0xFD40]
    couleurs += [0x8000] * (64 - len(couleurs))
    images = []
    for n in range(3):
        tuiles = {}
        for lig in range(3):
            for col in range(3):
                # Chaque case son aplat ; l'image decale les indices pour qu'un
                # changement d'image se voie comme un changement de couleur.
                v = 1 + ((lig * 3 + col + n * 3) % 9)
                t = np.full((16, 16), v, np.uint8)
                t[0, :] = 7   # un liseré blanc en haut : dit le sens de la tuile
                tuiles[(col, lig)] = entrelacer(t)
        images.append((n, tuiles, 48, 48))
    return images, couleurs


def main():
    mode_mire = "--mire" in sys.argv
    chemin = os.path.join(RACINE, "sprites", ASSET + ".bin")
    images = []

    if mode_mire:
        images, couleurs_mire = mire()
        print("MIRE : 9 aplats, 3 images, couleurs franches")
        _ecrire(images, couleurs_mire)
        return

    for i in IMAGES:
        tuiles, w, h = tuiles_du_sprite(chemin, i)
        if tuiles is None:
            print(f"sprite {i} : vide, ignore")
            continue
        images.append((i, tuiles, w, h))
        print(f"sprite {i} : {w}x{h}, {len(tuiles)} tuiles")

    if not images:
        print("rien a exporter")
        return

    pal = palette_du_jeu()
    _ecrire(images, list(pal[1]) if pal else None)


def _ecrire(images, couleurs):
    ox, oy = ORIGINE
    lignes = []
    lignes.append("/* Genere par dc-decors/outils/objets.py -- ne pas modifier a la main. */")
    lignes.append('#include "port/video/decor_objets.h"')
    lignes.append("")
    lignes.append(f"/* {ASSET}, sprites {IMAGES} : {images[0][2]}x{images[0][3]}. */")
    lignes.append("")

    total = 0
    for n, (i, tuiles, w, h) in enumerate(images):
        for (col, lig), octets in sorted(tuiles.items()):
            nom = f"tuile_{n}_{col}_{lig}"
            corps = ", ".join(str(b) for b in octets)
            lignes.append(f"static const unsigned char {nom}[256] = {{ {corps} }};")
            total += 1
        lignes.append("")

    lignes.append("static const DecorTuile tuiles[] = {")
    for n, (i, tuiles, w, h) in enumerate(images):
        for (col, lig) in sorted(tuiles.keys()):
            lignes.append(f"    {{ {n}, {ox + col * 16}, {oy + lig * 16}, tuile_{n}_{col}_{lig} }},")
    lignes.append("};")
    lignes.append("")
    if couleurs:
        lignes.append("/* 64 entrees ARGB1555, telles que la Dreamcast les tient. ColorRAM est en ABGR :")
        lignes.append("   c'est DecorObjets_InstallerPalette qui echange rouge et bleu, pas ce fichier. */")
        lignes.append("const unsigned short decor_palette_ventilation[64] = {")
        for k in range(0, 64, 8):
            lignes.append("    " + ", ".join("0x%04X" % c for c in couleurs[k:k + 8]) + ",")
        lignes.append("};")
        lignes.append("")
        print(f"palette : {len(couleurs)} couleurs")
    else:
        lignes.append("const unsigned short decor_palette_ventilation[64] = { 0 };")
        lignes.append("")
        print("palette : aucune")

    lignes.append("const DecorAnimation decor_objet_ventilation = {")
    lignes.append(f"    {len(images)},")
    lignes.append(f"    {sum(len(t) for _i, t, _w, _h in images)},")
    lignes.append("    tuiles")
    lignes.append("};")
    lignes.append("")

    os.makedirs(os.path.dirname(SORTIE), exist_ok=True)
    open(SORTIE, "w", encoding="utf-8").write("\n".join(lignes))
    print(f"{total} tuiles ecrites dans {SORTIE}")


if __name__ == "__main__":
    main()
