# -*- coding: utf-8 -*-
"""Recalcule la position des objets animes de `decor_objets_data.c`, depuis l'asset.

POURQUOI IL LE FAUT
-------------------
`animations.py` ecrivait `x = element.x + dx` mais `y = element.y` **brut**. Or
`element.y` est une HAUTEUR au-dessus du sol de 2nd Impact, pas une ordonnee du moteur de
3SX : les deux ne sont ni dans le meme sens ni dans le meme repere. D'ou des objets qui
s'animent correctement -- le journal le montre -- et qu'on ne voit jamais, ou qu'on voit
en haut de l'ecran.

LA CHAINE, ET ELLE EST EXACTE
-----------------------------
1. **On identifie le sprite dans l'asset du decor**, en comparant l'image 0 de
   l'animation -- desentrelacee depuis le C -- aux sprites assembles. La correspondance
   est totale : 2048 pixels sur 2048 pour Oro, 6144 sur 6144 pour Gill. Ce n'est pas une
   correlation, c'est une egalite.
2. Le sprite donne son enregistrement d'animation, donc **l'ancre** ; `assemblage.poser`
   donne **`(x0, y0)`**, le coin de la boite dans le repere du sprite.
3. Le reste est la chaine deja etablie :

       bank_y = sol - element.y + ancre_y + y0          sol mesure dans la banque
       y      = 1024 - bank_y - (ligs - 1) * 16
       x      = la valeur de la fiche, deja une abscisse de banque

**L'ancre n'a pas la meme forme pour tous.** L'acolyte de Gill a `ancre_y + y0 = -96`,
soit la hauteur de sa grille : son origine est au BAS de son image, il se tient debout.
Le filet d'eau d'Oro a `ancre_y + y0 = 0` : son origine est en HAUT, il pend. Une regle
d'ecart constant -- « +17 » -- marche pour le premier et se trompe de 64 pixels sur le
second. Il faut le calcul.

EPREUVE : sur `bg00`, la chaine rend `288, 81`, exactement la valeur verifiee a l'ecran.

    python situer_objets.py            # dit ce qu'il ferait
    python situer_objets.py --ecrire
"""
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import animations as AN
import assemblage as A
import bases
import fetc
import poser2i as P

DATA = r"C:\Temp3sx\src\port\video\decor_objets_data.c"


def fiches(texte):
    """Les entrees de `decor_animations`."""
    bloc = re.search(r"const DecorAnimation decor_animations\[\]\s*=\s*\{(.*?)\n\};",
                     texte, re.S).group(1)
    out = []
    for ligne in bloc.splitlines():
        # LE DERNIER CHAMP EST FACULTATIF, ET L'OUBLIER REND L'OUTIL MUET.
        # Ce motif s'arretait a `z` : ecrit avant que `boucle` n'existe, il ne reconnaissait
        # plus AUCUNE fiche des 188 une fois le champ ajoute -- et `main()` annoncait alors
        # « rien a corriger », ce qui se lit comme un succes alors que rien n'a ete examine.
        # Le groupe est non capturant pour ne pas decaler les numeros utilises plus bas.
        m = re.match(r'\s*\{\s*"(\w+)",\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),\s*(\d+),'
                     r'\s*(\w+),\s*\w+,\s*\w+,\s*(-?\d+),\s*(-?\d+),\s*(-?\d+),\s*(\d+),'
                     r'\s*-?\d+(?:,\s*-?\d+)?\s*\},?'
                     r'(?:\s*/\* element\.y (-?\d+) \*/)?', ligne)
        if m:
            # `element.y` brut, garde en commentaire pour que l'outil soit rejouable :
            # sans lui, une deuxieme passe reconvertirait une valeur deja convertie.
            brut = int(m.group(12)) if m.group(12) else int(m.group(10))
            out.append(dict(ligne=ligne, decor=m.group(1), etage=int(m.group(2)),
                            cols=int(m.group(5)), ligs=int(m.group(6)),
                            prefixe=m.group(7).split("_")[0],
                            x=int(m.group(9)), y=int(m.group(10)), brut=brut,
                            famille=int(m.group(11))))
    return out


def image_zero(texte, prefixe, cols, ligs):
    """L'image 0 de l'animation, desentrelacee et posee sur sa grille."""
    out = np.zeros((ligs * 16, cols * 16), np.uint8)
    for lig in range(ligs):
        for col in range(cols):
            m = re.search(r"\b%s_i0_%d_%d\[\d*\]\s*=\s*\{(.*?)\};" % (prefixe, col, lig),
                          texte, re.S)
            if m is None:
                continue
            oct = bytes(int(v, 0) for v in m.group(1).replace("\n", "").split(",")
                        if v.strip())
            out[lig * 16:lig * 16 + 16, col * 16:col * 16 + 16] = AN.desentrelacer(oct)
    return out


_cache = {}


def asset(decor):
    """L'asset du decor, ou None s'il n'en a pas.

    TOUS LES OBJETS ANIMES NE VIENNENT PAS D'UN ASSET. Ceux d'Akuma (`bg0f`) et d'Ibuki
    sont des ANIMATIONS DE PAGES : leurs tuiles sortent du magasin d'un `.pvc`, pas d'un
    `F_ETC`, et ces decors n'ont donc aucune entree dans `bases.ASSETS`. L'outil levait
    ici un `KeyError` et s'arretait NET sur `bg0f` -- il n'examinait donc jamais les
    fiches situees plus loin dans le fichier, dont celle du singe de Sean.
    """
    if decor not in bases.ASSETS:
        return None

    if decor not in _cache:
        chemin = os.path.join(P.RACINE, "sprites", bases.ASSETS[decor])
        _cache[decor] = (fetc.lire(open(chemin, "rb").read()), A.charger(chemin)[1])
    return _cache[decor]


def identifier(decor, cible):
    """(numero de sprite, ancre, x0, y0) : le sprite dont l'image EGALE la cible."""
    paire = asset(decor)

    if paire is None:
        return "sans asset"

    a, tuiles = paire
    lo, _hi = a["index_global"]
    offs = sorted({r[4] for r in a["anims"]})
    meilleur = None
    for i, sp in enumerate(a["sprites"]):
        p = A.poser(sp, tuiles)
        if p is None:
            continue
        im = p[0]
        h, w = min(im.shape[0], cible.shape[0]), min(im.shape[1], cible.shape[1])
        n = h * w
        eg = int((im[:h, :w] == cible[:h, :w]).sum())
        if meilleur is None or eg > meilleur[0]:
            meilleur = (eg, n, i, p[2], p[3])
    eg, n, i, x0, y0 = meilleur
    if i >= len(offs):
        return None
    rec = next((r for r in a["anims"] if r[4] == offs[i]), None)
    if rec is None:
        return None
    return dict(sprite=i, egal=eg, total=n, ancre=(rec[1], rec[2]), x0=x0, y0=y0)


def main():
    ecrire = "--ecrire" in sys.argv
    texte = open(DATA, encoding="utf-8", errors="replace").read()
    print("%-6s %-6s %-4s %-11s %-9s %-12s %s"
          % ("decor", "etage", "spr", "identite", "ancre+y0", "fiche", "le calcul"))
    remplacements = []
    for f in fiches(texte):
        cible = image_zero(texte, f["prefixe"], f["cols"], f["ligs"])
        if not (cible > 0).any():
            print("%-6s %-6d  image 0 introuvable" % (f["decor"], f["etage"]))
            continue
        r = identifier(f["decor"], cible)
        if r == "sans asset":
            print("%-6s %-6d  animation de pages, pas d'asset -- ignore"
                  % (f["decor"], f["etage"]))
            continue
        if r is None or r["egal"] < r["total"]:
            print("%-6s %-6d  sprite non identifie (%s)"
                  % (f["decor"], f["etage"],
                     "aucun" if r is None else "%d/%d" % (r["egal"], r["total"])))
            continue
        sol = P.sol(f["decor"])
        dy = r["ancre"][1] + r["y0"]
        bank_y = (sol - f["brut"] + dy) & 0x3FF
        ny = 1024 - bank_y - (f["ligs"] - 1) * 16
        print("%-6s %-6d %-4d %4d/%-6d %-9d %-12s element.y %3d -> y %d"
              % (f["decor"], f["etage"], r["sprite"], r["egal"], r["total"], dy,
                 "%d,%d" % (f["x"], f["y"]), f["brut"], ny))
        neuf = re.sub(r"(,\s*-?\d+,\s*)-?\d+(,\s*\d+,\s*-?\d+\s*\},?).*$",
                      lambda m: "%s%d%s  /* element.y %d */"
                                % (m.group(1), ny, m.group(2), f["brut"]), f["ligne"])
        if neuf != f["ligne"]:
            remplacements.append((f["ligne"], neuf))

    if not remplacements:
        print("\nrien a corriger")
        return
    if not ecrire:
        print("\n%d fiches a corriger. `--ecrire` pour le faire." % len(remplacements))
        return
    for vieux, neuf in remplacements:
        assert vieux in texte
        texte = texte.replace(vieux, neuf, 1)
    open(DATA, "w", encoding="utf-8", newline="").write(texte)
    print("\n%d fiches corrigees dans decor_objets_data.c" % len(remplacements))


if __name__ == "__main__":
    main()
