# -*- coding: utf-8 -*-
"""Assemble les elements de decor d'un etat Flycast, tuiles et couleurs comprises.

C'est `pools.py` mis en images : le champ `tuile` d'un morceau indexe le pool de
l'asset `F_ETCnn` designe par l'octet bas de la cle (`enr+12`), bloc = `tuile >> 4`,
rang = `tuile & 15`, la tuile faisant 256 octets de 16x16 en valeurs d'index.

Ce que ce programme ajoute a `assemblage.py` : il ne part plus du fichier range sur le
disque mais de **l'etat du jeu**, ou tout est deja resolu -- position absolue, taille en
pixels, palette, et la liste d'affichage qui dit quel element va sur quel plan.

La liste d'affichage, lue en `0x8C0F693C`, tient au debut du meme tableau :

    {u16 drapeaux, u16 index, s16 x, s16 y, u16 mot, ...}   16 octets
    nombre de morceaux = drapeaux & 0x1FF
    plan               = ((drapeaux >> 10) & 28) / 4
    morceaux           = enregistrements `index` a `index + nombre - 1`
    elle s'arrete au premier enregistrement dont le bit 15 est arme

La position d'un morceau, lue en `0x8C0F6A90` et `0x8C0F6AA6`. Le mot `+8` donne
`hauteur = ((mot >> 8) & 127) + 1` et `largeur = (mot & 127) + 1` -- l'inverse de ce
que nommait `etat2.py`, et c'est le calcul du dessin qui le dit : le bit 0x0100 retire
la moitie de ce champ a **y**, le bit 0x0200 l'autre a **x**. A l'ecran :

    x = defil_x[plan] + elem.x + m.x - (largeur / 2 si le bit 0x0200 est arme)
    y = 109 - defil_y[plan] - elem.y - m.y - hauteur + (hauteur / 2 si le bit 0x0100)

L'axe y est **inverse** : `elem.y` et `m.y` sont des **hauteurs au-dessus du sol**, et
`109` est la ligne du sol **a l'ecran**. Dans le plan, le defilement s'annule avec celui
du fond et il faut remplacer 109 par la ligne du sol **dans la banque**, `G` :

    x = elem.x + m.x - (largeur / 2)          y = G - elem.y - m.y - hauteur + (h / 2)

`G` se mesure : c'est la derniere ligne non vide de la moitie basse de la banque `.pvc`
(`cuire.py` la calcule). Avec 109 a la place, tout le groupe se retrouve centre sur
`y = 0`, a cheval sur le bouclage -- chez Alex deux batiments se posaient au sol du toit
et le chateau d'eau flottait dans le ciel, chez Ryu les baigneurs sortaient de la bande
visible et on ne voyait plus rien.

Les deux masquees a 0x3FF : le plan boucle sur 1024. **Verifie par superposition** : sur
`bg03`, les etals, la charrette et l'enseigne 九記 se posent sur la chaussee de
`2i-bg03-banque0.png`, a la bonne echelle et devant les bonnes boutiques. Les deux autres
conventions essayees (garder le defilement, ou inverser l'axe du fond) les envoient dans
le ciel.

La palette depend de deux bits de l'octet `+9` de l'element, lus en `0x8C0F6A44` et
`0x8C0F6A64`, l'adresse etant calculee en `0x8C0F6E3A` :

    bit 5 arme    : l'emplacement vient du mot `+8` de **l'element** -- un seul pour
                    tous ses morceaux ; bit 5 eteint : du champ `+2` du **morceau**
    (octet & 6)!=0: emplacement = source & 0x1FF, palette de 128 octets (64 couleurs)
    (octet & 6)==0: emplacement = (source & 0x1FF) | 0x200, palette de 512 octets
    adresse = 0x8C7AFCCC + emplacement * 128         si emplacement < 0x200
              0x8C7AFCCC + (emplacement - 512) * 512 sinon

C'est ce bit 5 qui manquait : pris sur le morceau pour tout le monde, les elements a
octet `0x62` tombaient sur les emplacements 1 a 15, c'est-a-dire le bloc des
combattants, identique dans les dix-sept etats.

L'index 0 est transparent : le convertisseur ecrit zero dans la premiere case avant de
deplier la tuile (`mov.w r2,@r4` en `0x8C0F6EAC`).

    python elements.py                 # tous les etats, planche par element
    python elements.py bg02            # un decor
    lanceur : elements.cmd
"""
import glob, os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image

import flycast as F
import etat as E
import fetc, degonfle
import pools as P

ICI    = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
SORTIE = os.path.join(RACINE, "rendus", "elements")
DOS    = os.path.join(os.path.expanduser("~"), "Documents", "Dreamcast", "data")
MOTIF  = "Street Fighter III - Double Impact*.state"

PALRAM   = 0x8C7AFCCC
PALHAUTE = 0x8C6DC8D0
DEFIL    = 0x8C7EFCCC
PTR      = 0x8C602348
ORIGINE_Y = 109


# --- les tuiles d'un asset, degonflees une fois pour toutes -------------------

_cache = {}


def tuiles(nom):
    """Les tuiles 16x16 en valeurs d'index de l'asset `sprites/<nom>.bin`."""
    if nom in _cache:
        return _cache[nom]
    d = open(os.path.join(RACINE, "sprites", nom + ".bin"), "rb").read()
    r = fetc.lire(d)
    n = len(r["blocs"])
    out = []
    for k, b in enumerate(r["blocs"]):
        octets, _ = degonfle.degonfler(b, souple=(k == n - 1))
        a = np.frombuffer(octets, dtype=np.uint8)
        for t in range(16):
            out.append(a[t * 256:(t + 1) * 256].reshape(16, 16))
    _cache[nom] = out
    return out


# --- couleurs ----------------------------------------------------------------

def couleurs(ram, emplacement, n):
    """`n` couleurs RGBA depuis la palette RAM. ARGB1555, index 0 transparent."""
    if emplacement < 0x200:
        a = PALRAM + emplacement * 128
    else:
        a = PALRAM + (emplacement - 0x200) * 512
    o = a - F.BASE_RAM
    v = np.frombuffer(ram[o:o + n * 2], dtype="<u2").astype(np.uint32)
    r = ((v >> 10) & 31) * 255 // 31
    g = ((v >> 5) & 31) * 255 // 31
    b = (v & 31) * 255 // 31
    out = np.stack([r, g, b, np.full(n, 255, np.uint32)], axis=1).astype(np.uint8)
    out[0, 3] = 0
    return out


# --- la liste d'affichage et ses morceaux ------------------------------------

def mot(ram, base, i, k):
    return F.u16(ram, base + i * 16 + k * 2)


def smot(ram, base, i, k):
    return F.s16(ram, base + i * 16 + k * 2)


def liste(ram):
    """Les elements de la liste d'affichage, dans l'ordre de dessin."""
    base = F.u32(ram, PTR)
    out = []
    for i in range(512):
        d = mot(ram, base, i, 0)
        if d & 0x8000:
            break
        out.append(dict(i=i, drapeaux=d, nb=d & 0x1FF,
                        plan=((d >> 10) & 28) // 4,
                        index=mot(ram, base, i, 1),
                        x=smot(ram, base, i, 2), y=smot(ram, base, i, 3),
                        mot=mot(ram, base, i, 4),
                        octet9=F.u8(ram, base + i * 16 + 9)))
    return base, out


def morceaux(ram, base, e):
    out = []
    for k in range(e["nb"]):
        i = e["index"] + k
        w = [mot(ram, base, i, j) for j in range(8)]
        h = ((w[4] >> 8) & 127) + 1
        l = (w[4] & 127) + 1
        # Les deux bits de centrage, corriges le 29/08/2026 contre le desassemblage :
        # 0x8C0F6A22 teste 0x0100 pour retirer la moitie de la LARGEUR a x, et
        # 0x8C0F6A36 teste 0x0200 pour la moitie de la HAUTEUR a y. Ils etaient nommes
        # a l'envers ici. Sans consequence sur les rendus deja faits : les deux bits
        # sont toujours egaux sur les 3458 morceaux dessines des dix-huit etats.
        out.append(dict(i=i, tuile=w[0], pal=w[1], x=w[2], y=w[3],
                        l=l, h=h, code=w[5] & 0xFF,
                        centre_x=bool(w[5] & 0x0100), centre_y=bool(w[5] & 0x0200),
                        cle=w[6]))
    return out


# --- dessin ------------------------------------------------------------------

def dessine(ram, ts, m, img, x0, y0):
    """Pose un morceau. Les tuiles se suivent en colonnes, hauteur d'abord."""
    # D'ou vient l'emplacement de palette : `0x8C0F6A44` teste le **bit 5** de l'octet
    # `+9` de l'element. Bit arme, le mot `+8` de l'element fait foi pour tous ses
    # morceaux ; bit eteint, c'est le champ `+2` du morceau. Les deux sont ensuite
    # masques a 0x1FF.
    emplacement = (m["source_pal"]) & 0x1FF
    n = 64
    if not m["flags6"]:
        emplacement |= 0x200
        n = 256
    pal = couleurs(ram, emplacement, n)
    nc, nr = m["l"] // 16, m["h"] // 16
    t = m["tuile"]
    for cx in range(nc):
        for cy in range(nr):
            k = t + cx * nr + cy
            if k >= len(ts):
                return False
            bloc = ts[k]
            px, py = x0 + cx * 16, y0 + cy * 16
            if not (0 <= px <= img.shape[1] - 16 and 0 <= py <= img.shape[0] - 16):
                continue
            v = np.minimum(bloc, n - 1)
            rgba = pal[v]
            zone = img[py:py + 16, px:px + 16]
            opaque = rgba[:, :, 3] > 0
            zone[opaque] = rgba[opaque]
    return True


def rend_etat(chemin, ass_par_cle, sols=None, couches=None):
    """`sols` : decor -> ligne du sol dans la banque. A defaut, `ORIGINE_Y`.

    `couches` : liste a remplir, si on la fournit. Elle recoit `(i, plan, image)` pour
    chaque element dessine, **dans l'ordre de la liste d'affichage** -- qui est l'ordre
    de dessin : la boucle `0x8C0F693C` parcourt les elements et dessine chacun aussitot.
    `plan` ne choisit que le defilement, il n'ordonne PAS la profondeur. Empiler par
    numero de plan croissant est faux, et ca se mesure : sur les vingt-six releves, les
    deux ordres different a chaque fois, et les plages d'indices des plans se
    chevauchent partout. Pour `bg00` l'ordre de la liste est 0, 1, 7, 3, 2, 4 -- le
    plan 7 arrive AVANT le plan 3, donc son petit obelisque passe DERRIERE le temple.
    """
    nom_etat = os.path.basename(chemin)
    decors, _ = P.morceaux_json(nom_etat)
    ram, _ = F.lire_ram(chemin, E.EXE)
    base, elems = liste(ram)
    defil = [(F.u16(ram, DEFIL + k * 4), F.u16(ram, DEFIL + k * 4 + 2))
             for k in range(8)]
    plans = {}
    fiches = {}
    rapport = []
    for e in elems:
        ms = morceaux(ram, base, e)
        if not ms:
            continue
        cles = {m["cle"] for m in ms}
        noms = set()
        for c in cles:
            f = P.fiche(ram, c & 0xFF)
            nb = P.nb_blocs(ram, f["graphique"])
            if nb is None:
                continue
            t = ram[f["graphique"] - F.BASE_RAM: f["graphique"] - F.BASE_RAM + 256]
            noms.update(P.nomme(t, ass_par_cle))
        # Tout element dont les tuiles viennent d'un asset F_ETC identifie. Les
        # combattants et le HUD n'en sont pas : leurs pools ne sont pas dans `sprites/`,
        # donc ils tombent d'eux-memes. `bg02` cote releve, `2i-b02-F_ETC25` cote asset.
        if not noms:
            continue
        etiquettes = {"-" + d.replace("bg", "b") + "-" for d in (decors or [])}
        propres = {n for n in noms if any(t in n for t in etiquettes)}
        nom_asset = sorted(propres or noms)[0]
        ts = tuiles(nom_asset)
        dx, dy = defil[e["plan"]]
        for m in ms:
            m["flags6"] = bool(e["octet9"] & 6)
            m["source_pal"] = e["mot"] if (e["octet9"] & 0x20) else m["pal"]
        # planche isolee de l'element, dans ses propres coordonnees
        xs = [(m["x"] - (m["l"] // 2 if m["centre_x"] else 0)) for m in ms]
        ys = [(-m["y"] - m["h"] + (m["h"] // 2 if m["centre_y"] else 0)) for m in ms]
        # `e["y"]` se retranche aussi : voir la formule en tete de fichier.
        x1 = min(xs); y1 = min(ys)
        larg = max(x + m["l"] for x, m in zip(xs, ms)) - x1
        haut = max(y + m["h"] for y, m in zip(ys, ms)) - y1
        if larg <= 0 or haut <= 0 or larg > 2048 or haut > 2048:
            continue
        vig = np.zeros((haut, larg, 4), np.uint8)
        for m, x, y in zip(ms, xs, ys):
            dessine(ram, ts, m, vig, x - x1, y - y1)
        # Dans le plan, pas a l'ecran : le defilement `dx`, `dy` s'annule avec celui du
        # fond. Il ne sert plus qu'a se rappeler d'ou vient la mesure.
        sol = ORIGINE_Y
        for d in (decors or []):
            if sols and d in sols:
                v = sols[d]
                # int : une seule ligne de sol. dict : une par plan, cle `None` par
                # defaut -- c'est ce qui permet d'envoyer un plan dans la moitie
                # lointaine, avec la ligne de sol de CETTE bande-la.
                sol = v.get(e["plan"], v[None]) if isinstance(v, dict) else v
        img = plans.setdefault(e["plan"], np.zeros((1024, 1024, 4), np.uint8))
        for m, x, y in zip(ms, xs, ys):
            dessine(ram, ts, m, img,
                    (e["x"] + x) & 0x3FF,
                    (sol - e["y"] + y) & 0x3FF)
        if couches is not None:
            seul = np.zeros((1024, 1024, 4), np.uint8)
            for m, x, y in zip(ms, xs, ys):
                dessine(ram, ts, m, seul,
                        (e["x"] + x) & 0x3FF,
                        (sol - e["y"] + y) & 0x3FF)
            couches.append((e["i"], e["plan"], seul))
        fiches[e["i"]] = (nom_asset, vig)
        rapport.append((e, nom_asset, len(ms), larg, haut))
    return decors, rapport, fiches, plans


def main():
    os.makedirs(SORTIE, exist_ok=True)
    ass = P.assets()
    filtre = sys.argv[1] if len(sys.argv) > 1 else None
    for chemin in sorted(glob.glob(os.path.join(DOS, MOTIF))):
        decors, rapport, fiches, plans = rend_etat(chemin, ass)
        nom = "-".join(decors or ["inconnu"])
        if filtre and filtre not in nom:
            continue
        print(f"=== {os.path.basename(chemin)}  {nom} ===")
        if not rapport:
            print("   aucun element de decor propre a ce decor")
            continue
        for e, a, n, l, h in rapport:
            print(f"   element {e['i']:3d}  plan {e['plan']}  {n:3d} morceaux  "
                  f"{l:4d}x{h:<4d}  x={e['x']:5d} y={e['y']:5d}  "
                  f"octet9 {e['octet9']:#04x}  {a}")
        for i, (a, vig) in fiches.items():
            Image.fromarray(vig).save(os.path.join(SORTIE, f"{nom}-e{i:03d}.png"))
        for p, img in plans.items():
            Image.fromarray(img).save(os.path.join(SORTIE, f"{nom}-plan{p}.png"))
        print(f"   -> rendus/elements/{nom}-*.png")
        print()


if __name__ == "__main__":
    main()
