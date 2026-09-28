# -*- coding: utf-8 -*-
"""Pose les elements de decor de `bg00` dans les pages de l'etage 22, sans aucun etat.

Tout vient de `SF3_2ND.BIN` et de l'asset `2i-b00-F_ETC41.bin`. Aucun `.state` n'est
ouvert, ni ici ni dans ce qu'on importe.

LA REGLE, ET LE MAILLON QUI LUI MANQUAIT
----------------------------------------
La chaine de `SANS-ETAT.md` s'arretait a l'ancre du script :

    bx = element.x + ancre_x                 by = 1023 - element.y + ancre_y

Elle oublie que `assemblage.poser` ne rend pas une image dont le coin serait l'origine
du sprite : il rend `(image, masque, x0, y0)`, ou `(x0, y0)` EST le coin de la boite
**dans le repere du sprite**. C'est ecrit dans la fonction : `x0 = min(px)` sur les
morceaux, avec `px, py = m['y'] - 8*largeur, m['x'] - 8*hauteur`. L'ancre mene a
l'origine du sprite, `(x0, y0)` mene de cette origine au coin de l'image. Les deux
s'ajoutent :

    bx = (element.x + ancre_x + x0) & 0x3FF
    by = (1023 - element.y + ancre_y + y0) & 0x3FF

`x0` vaut zero pour les sept elements de `bg00` -- d'ou un x juste malgre l'oubli. `y0`
non : -32 pour le temple, -16 pour les obelisques et pour l'acolyte, 0 pour les autres.
C'est exactement de ces valeurs-la que ces trois-la etaient trop bas.

CONTROLE, PAR UN CHEMIN INDEPENDANT
-----------------------------------
Les pages cuites avant que les etats disparaissent posaient le temple en 384,863,
les obelisques en 608,743 et l'acolyte en 288,863. La regle corrigee rend ces trois
positions **au pixel** ; l'ancienne rendait 895, 759 et 879, soit +32, +16 et +16.

    python poser22.py            # recuit les listes 196, 260 et 324
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import annuaire2i as AN
import assemblage as A
import bande3sx
import bases
import fetc
import palettes
import pvc
import sh4
from rendupvc import carte_morton, SIDE

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
BIN = os.path.join(RACINE, "SF3_2ND.BIN")
POFF = 0x1D9AEC                     # la banque de 2715 palettes de 64 couleurs
ASSET = os.path.join(RACINE, "sprites", "2i-b00-F_ETC41.bin")
SORTIE = os.path.join(RACINE, "etages2i-sprites", "stage22")

DECOR = 0                           # bg00 -- son bloc vient de `annuaire2i`
ELEMENTS_8 = 0x8C183DC8             # bg00 : {x, y, palette, script} -- les quatre figures
MAITRESSE = 0x8C5F9B38              # un pointeur de table de scripts par aire d'etage
SOL = 1023                          # la ligne du sol dans la banque, treize decors sur seize

# Le plan `j` prend les emplacements `j*64 + 132`.
LISTE_PROCHE, LISTE_TIERS, LISTE_QUATRE = 196, 260, 324

# Les elements du bloc qui gardent l'ANCIENNE regle -- celle sans `y0`.
#
# Il n'en reste qu'un : les obelisques, indice 1. Ils ne sont pas dans ce que Frederic a
# signale, et `SANS-ETAT.md` interdit de deplacer ce qui ne l'a pas ete. La correction les
# remonterait de 16, exactement sur la position validee du 12:12. A lever quand il le dira.
SANS_Y0 = {1}


def charger():
    a = fetc.lire(open(ASSET, "rb").read())
    _r, tuiles = A.charger(ASSET)
    return a, tuiles, sorted({r[4] for r in a["anims"]})


def sprite_du_script(a, offs, sc):
    """(sprite, enregistrement d'animation, numero de sprite) pour un script d'etage.

    `MAITRESSE + aire*4` donne la table des scripts, un script donne des
    enregistrements de 8 octets dont l'u16 a +6 est l'index GLOBAL d'animation, et
    l'asset indexe ses `anims` par cet index moins son propre `index_global[0]`.
    """
    lo, _hi = a["index_global"]
    tbl = sh4.u32(sh4.a2o(MAITRESSE))
    q = sh4.u32(sh4.a2o(tbl + sc * 4))
    g = sh4.u16(sh4.a2o(q) + 6)
    rec = a["anims"][g - lo]
    n = offs.index(rec[4])
    return a["sprites"][n], rec, n


_banque = None


def banque_des_palettes():
    """Les 2715 palettes de 64 couleurs du binaire, indexees par leur NUMERO."""
    global _banque
    if _banque is None:
        _banque = palettes.lire(BIN, POFF, 2715)
    return _banque


def palettes_du_sprite(sp):
    """Les numeros de palette employes, morceau par morceau : base(drapeaux) + offset."""
    b = bases.BASES_2I["bg00"]
    out = {}
    for m in A.morceaux(sp):
        n = b.get(m["drapeaux"])
        if n is not None:
            out[n + m["palette"]] = out.get(n + m["palette"], 0) + 1
    return out


def placer(a, tuiles, offs, x_el, y_el, sc, sans_y0=False):
    """(image RGBA, bx, by, palettes employees) pour un element.

    **Chaque morceau porte SA palette**, et il faut la lui laisser : le champ n'est pas
    constant sur un sprite. Le temple d'horizon a deux palettes -- 842 sur deux de ses
    dix-sept morceaux, 867 sur les quinze autres -- et les obelisques aussi, 848 et 850.
    Imposer celle du premier morceau a tout le sprite sort du magenta `0xFC1F` : les
    emplacements que la palette imposee n'emploie pas. Vingt-neuf pixels sur le temple,
    cent vingt-trois sur les obelisques. C'est `assemblage.poser_couleur` qui fait ca.
    """
    sp, rec, _n = sprite_du_script(a, offs, sc)
    b = bases.BASES_2I["bg00"]
    rgba, x0, y0 = A.poser_couleur(sp, tuiles, banque_des_palettes(), b[1], b)
    if sans_y0:
        x0 = y0 = 0
    bx = (x_el + rec[1] + x0) & 0x3FF
    by = (SOL - y_el + rec[2] + y0) & 0x3FF
    return rgba, bx, by, palettes_du_sprite(sp)


def peindre(plan, rgba, bx, by):
    h, w = rgba.shape[:2]
    sub = plan[by:by + h, bx:bx + w]
    src = rgba[:sub.shape[0], :sub.shape[1]]
    op = src[:, :, 3] > 0
    sub[op] = src[op]
    return int(op.sum())


def elements_16():
    """Les elements statiques de `bg00`, d'apres l'annuaire : (k, plan, x, y, script).

    **Trois, pas cinq.** Le bloc de `bg00` fait 48 octets. Les deux etoiles filantes qui
    le suivaient en 0x8C17B9B0 et 0x8C17B9C0 sont le bloc du DECOR 1, et elles
    appartiennent a la petite scene d'introduction d'avant-combat de 2nd Impact -- une
    scene que 3rd Strike n'a plus. Elles n'ont donc rien a faire dans l'etage.
    """
    return [(k, e["plan"], e["x"], e["y"], e["script"])
            for k, e in enumerate(AN.elements(DECOR))]


def elements_8():
    """Les quatre figures animees : (k, x, y, emplacement de palette, script)."""
    out = []
    for k in range(4):
        ad = ELEMENTS_8 + k * 8
        w = [sh4.u16(sh4.a2o(ad + j * 2)) for j in range(4)]
        out.append((k, w[0], w[1], w[2], w[3]))
    return out


def ecrire_liste(plan, liste):
    """Les 32 pages d'une liste, moitie basse de la banque."""
    os.makedirs(SORTIE, exist_ok=True)
    for i in range(32):
        px, py = (i & 7) * 128, 512 + (i >> 3) * 128
        bande3sx.ecrire_tex(os.path.join(SORTIE, "%d-%d.tex" % (liste, liste + i)),
                            plan[py:py + 128, px:px + 128])


def dit(pals):
    return ", ".join("%d x%d" % (n, c) for n, c in sorted(pals.items()))


def main():
    a, tuiles, offs = charger()

    # --- liste 196 : la banque nue, plus les quatre figures animees ------------
    pages, _u, _ = pvc.decode(open(os.path.join(RACINE, "pvc-2i", "bg00.pvc"), "rb").read())
    proche = bande3sx.banque_rgba(pages, 0, carte_morton(SIDE))[0]
    # LES FIGURES ANIMEES NE SONT PLUS CUITES DANS LA PAGE.
    #
    # Elles y etaient tant qu'une seule d'entre elles bougeait : la copie servait de
    # pose fixe aux trois autres, et l'objet anime se calait dessus. Depuis que les
    # quatre sont animees (`outils/animer2i.py`), cette copie reste FIGEE sous l'objet
    # et se voit des que l'animation avance -- « je vois sous un sprite anime sa copie ».
    # La liste 196 ne porte donc plus que la banque nue.
    print("liste %d -- la banque nue ; les figures sont animees, pas cuites"
          % LISTE_PROCHE)
    for k, x_el, y_el, _emp, sc in elements_8():
        rgba, bx, by, pals = placer(a, tuiles, offs, x_el, y_el, sc)
        print("   figure %d  element %3d,%-3d  ->  banque %3d,%-3d  %dx%d  "
              "palettes %s   (animee, non cuite)"
              % (k, x_el, y_el, bx, by, rgba.shape[1], rgba.shape[0], dit(pals)))
    ecrire_liste(proche, LISTE_PROCHE)

    # --- listes 260 et 324 : les plans 3 et 7, sprites seuls ------------------
    tiers = np.zeros((1024, 1024, 4), np.uint8)
    quatre = np.zeros((1024, 1024, 4), np.uint8)
    print("\nlistes %d (plan 3) et %d (plan 7)" % (LISTE_TIERS, LISTE_QUATRE))
    for k, plan_2i, x_el, y_el, sc in elements_16():
        gele = k in SANS_Y0
        rgba, bx, by, pals = placer(a, tuiles, offs, x_el, y_el, sc, sans_y0=gele)
        cible = quatre if plan_2i == 7 else tiers
        n = peindre(cible, rgba, bx, by)
        print("   element %d  plan %d  %3d,%-3d  ->  banque %3d,%-3d  "
              "%dx%d  %5d px  palettes %s%s"
              % (k, plan_2i, x_el, y_el, bx, by, rgba.shape[1], rgba.shape[0], n,
                 dit(pals), "   (y sur l'ancienne regle, non signale)" if gele else ""))
    ecrire_liste(tiers, LISTE_TIERS)
    ecrire_liste(quatre, LISTE_QUATRE)

    # --- ce que l'objet anime doit porter -------------------------------------
    #
    # Le moteur compte y vers le haut (`njScale(0,1,-1,1)` avant le `njGetMatrix` de
    # `bg.c`), et une page posee en `bank_y` occupe `1024 - bank_y`. La grille du motif,
    # elle, met la rangee d'image `lig` en `(ligs-1-lig)*16` -- c'est `y_moteur` dans
    # `decor_objets.c` -- et un morceau pose en `cy` couvre `cy-16 .. cy`. La rangee 0 de
    # notre image est donc en `position_y + (ligs-1)*16`, a egaler a `1024 - bank_y` :
    #
    #     position_x = bank_x            position_y = 1024 - bank_y - (ligs - 1) * 16
    LIGS = 6
    k, x_el, y_el, _emp, sc = elements_8()[0]
    _rgba, bx, by, _p = placer(a, tuiles, offs, x_el, y_el, sc)
    print("\nobjet anime de l'etage 22 (grille %d rangees) :  "
          "position_x = %d   position_y = %d"
          % (LIGS, bx, 1024 - by - (LIGS - 1) * 16))


if __name__ == "__main__":
    main()
