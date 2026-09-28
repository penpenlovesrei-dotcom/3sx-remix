# -*- coding: utf-8 -*-
"""Choisit UNE animation de decor par etage et l'exporte pour 3SX.

CE QUE CE PROGRAMME FAIT
------------------------
1. Il relit les scripts d'animation du binaire (voir `cadences.py` et DONNEES.md) :
   une table maitresse a `0x8C5F9B38`, des tables de scripts, des enregistrements de
   huit octets `{cmd, duree, 0, 0, index global}`.
2. Il relit la liste d'affichage de chaque etat Flycast pour savoir **ou** chaque objet
   est pose, sur quel plan, et avec quelle palette.
3. Il apparie les deux : un element montre un sprite ; le script qui cite ce sprite est
   son animation.
4. Il exporte le tout dans `decor_objets_data.c`.

LES DEUX BORNES, ET POURQUOI
----------------------------
* **La grille.** `DecorObjets_Motif` recrit la liste de morceaux du motif emprunte. Elle
  ne peut pas etre plus longue que celle du donneur, sous peine de deborder sur l'entree
  suivante de la table de trans. Le motif d'essai en porte ~27 : on se limite donc a
  `MAX_TUILES` cases.
* **La tenue.** Une image tenue plus de `MAX_TENUE` trames ne se lit pas comme une
  animation dans un essai court. On ecarte, sans juger de l'oeuvre.

CE QUI EST ECARTE, ET CE N'EST PAS DU DECOR
-------------------------------------------
Les elements du **plan 3 a palette 128** apparaissent a l'identique dans les dix-huit
etats, aux memes coordonnees, quel que soit le decor : c'est l'affichage, pas le fond.
Les palettes 0, 8, 16 et 79 sont celles des combattants. On ne garde que les
emplacements < 128 en 64 couleurs, sur les plans 1 et 2.

    python animations.py            choisit, exporte et se relit
    python animations.py --liste    montre les candidats sans rien ecrire
    lanceur : animations.cmd
"""
import collections, glob, os, sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
RACINE = os.path.dirname(ICI)

import numpy as np
import sh4, fetc, assemblage, donnees as D
import flycast as F, etat as E

SORTIE = r"C:\Temp3sx\src\port\video\decor_objets_data.c"
MAITRESSE = 0x8C5F9B38
MAX_TUILES = 25
MAX_TENUE = 20
PALRAM = 0x8C7AFCCC

# L'asset propre a chaque decor : la table de cles de RELAIS.md, verifiee par pools.py.
ASSET = {'bg00': '2i-b00-F_ETC41', 'bg01': '2i-b01-F_ETC34', 'bg02': '2i-b02-F_ETC25',
         'bg03': '2i-b03-F_ETC26', 'bg04': '2i-b04-F_ETC32', 'bg05': '2i-b05-F_ETC28',
         'bg06': '2i-b06-F_ETC29', 'bg08': '2i-b08-F_ETC30', 'bg09': '2i-b08-F_ETC31',
         'bg0a': '2i-b0a-F_ETC33', 'bg0b': '2i-b0b-F_ETC27', 'bg0c': '2i-b0c-F_ETC24',
         'bg0d': '2i-b0d-F_ETC35', 'bg0e': '2i-b0e-F_ETC94'}
ETAGE = {'bg00': 22, 'bg01': 23, 'bg02': 24, 'bg03': 25, 'bg04': 26, 'bg05': 27,
         'bg06': 28, 'bg07': 29, 'bg08': 30, 'bg09': 30, 'bg0a': 31, 'bg0b': 32,
         'bg0c': 33, 'bg0d': 34, 'bg0e': 35, 'bg0f': 36}


def dans_le_binaire(v):
    return sh4.BASE <= v < sh4.BASE + len(sh4.D)


def charger_assets():
    out = {}
    for p in sorted(glob.glob(os.path.join(RACINE, "sprites", "2i-b*.bin"))):
        nom = os.path.basename(p)[:-4]
        r = fetc.lire(open(p, "rb").read())
        o = 0x20 + len(r["anims"]) * 12
        par_off = {}
        for i, sp in enumerate(r["sprites"]):
            par_off[o] = i
            o += 8 + len(sp["morceaux"]) * 8
        out[nom] = dict(chemin=p, span=r["index_global"], sprites=r["sprites"],
                        rec=[par_off.get(a[4]) for a in r["anims"]])
    return out


def lire_scripts():
    def un(a0):
        out = []
        for k in range(64):
            o = sh4.a2o(a0 + k * 8)
            cmd, duree, idx = sh4.D[o], sh4.D[o + 1], sh4.u16(o + 6)
            if cmd == 0x01:
                break
            if cmd == 0x00 and duree:
                out.append((idx, duree))
        return out
    out = {}
    for n in range(64):
        t = sh4.u32(sh4.a2o(MAITRESSE + n * 4))
        if not dans_le_binaire(t):
            continue
        for k in range(64):
            p = sh4.u32(sh4.a2o(t + k * 4))
            if not dans_le_binaire(p):
                break
            s = un(p)
            if len(s) >= 2:
                out[p] = s
    return out


def grille_du_sprite(ass, nom, sp, cache={}):
    """(colonnes, lignes) en tuiles de 16.

    On demande la taille a `assemblage.poser` plutot que de la recalculer : c'est lui qui
    pose les morceaux, et sa geometrie a ete corrigee le 29/08/2026 contre la liste
    d'affichage en RAM (le sprite est stocke TRANSPOSE dans le fichier). Recalculer ici
    avec l'ancienne convention donnait des grilles fausses, donc des sprites tronques.
    """
    chemin = ass[nom]["chemin"]
    if chemin not in cache:
        cache[chemin] = assemblage.charger(chemin)
    r, ts = cache[chemin]
    pose = assemblage.poser(r["sprites"][sp], ts)
    if pose is None:
        return 0, 0
    img = pose[0]
    return (img.shape[1] + 15) // 16, (img.shape[0] + 15) // 16


def candidats(ass, scripts):
    """Pour chaque decor : les animations posables, la meilleure en tete."""
    par_sprite = collections.defaultdict(list)
    for p, s in scripts.items():
        for idx, _d in s:
            for nom, a in ass.items():
                lo, hi = a["span"]
                if lo <= idx < hi:
                    k = idx - lo
                    if k < len(a["rec"]) and a["rec"][k] is not None:
                        par_sprite[(nom, a["rec"][k])].append(p)

    def sprite_de(nom, idx):
        lo, _hi = ass[nom]["span"]
        return ass[nom]["rec"][idx - lo]

    out = {}
    t = D.temoins()
    for ch in sorted(glob.glob(os.path.join(D.DOS, D.MOTIF))):
        r = D.releve(ch, t)
        if not r["decors"]:
            continue
        dec = r["decors"][0]
        att = ASSET.get(dec)
        if att is None or dec in out:
            continue
        ram, base = r["ram"], r["base"]
        cands = []
        for el in r["elements"]:
            if not el["nb"] or el["plan"] not in (1, 2):
                continue
            m0 = D.morceau(ram, base, el["debut"])
            emp, nc = D.emplacement_palette(el, m0)
            if emp >= 128 or nc != 64:
                continue                      # affichage et combattants, pas du decor
            ts = [D.morceau(ram, base, el["debut"] + k)["tuile"] for k in range(el["nb"])]
            for i, sp in enumerate(ass[att]["sprites"]):
                if [m[0] for m in sp["morceaux"]] != ts:
                    continue
                for p in set(par_sprite.get((att, i), [])):
                    s = scripts[p]
                    sps = [sprite_de(att, idx) for idx, _d in s]
                    if any(x is None for x in sps):
                        continue
                    gs = [grille_du_sprite(ass, att, x) for x in sps]
                    cols = max(g[0] for g in gs)
                    ligs = max(g[1] for g in gs)
                    tenue = max(d for _idx, d in s)
                    if not (0 < cols * ligs <= MAX_TUILES) or tenue > MAX_TENUE:
                        continue
                    # L'ANCRE. La grille du motif part du COIN de la boite du
                    # sprite, pas de la position de l'element : il faut donc ajouter
                    # l'ecart entre les deux. Sans lui l'objet est pose trop a droite.
                    #
                    # Verification croisee : pour la ventilation d'Alex (bg01,
                    # element 5) cet ecart vaut (-48, -48) -- exactement l'ancre que
                    # `cadences.py` lit dans le script d'animation du binaire
                    # (0x8C122704). Deux chemins independants, la meme valeur.
                    ms_el = [D.morceau(ram, base, el["debut"] + k)
                             for k in range(el["nb"])]
                    dx = min((m["x"] - (m["largeur"] // 2 if m["centre_x"] else 0))
                             for m in ms_el if m["dessine"]) if ms_el else 0
                    if dx > 512:
                        dx -= 1024          # le champ boucle sur 0x3FF
                    cands.append(dict(decor=dec, etage=ETAGE[dec], asset=att, script=p,
                                      element=el["i"], plan=el["plan"],
                                      x=(el["x"] + dx) & 0x3FF, y=el["y"], emplacement=emp,
                                      sprites=sps, durees=[d for _idx, d in s],
                                      cols=cols, ligs=ligs, ram=ram))
        if cands:
            # LA PLUS GRANDE d'abord : c'est ce qui se voit dans un essai. Puis le plus
            # d'images. Et on ecarte la rangee repliee (y > 512), qui sort de la bande jouee.
            cands.sort(key=lambda c: (c["y"] < 512, c["cols"] * c["ligs"], len(c["sprites"])),
                       reverse=True)
            out[dec] = cands
    return out


def palette(ram, emplacement):
    o = PALRAM - F.BASE_RAM + emplacement * 128
    return np.frombuffer(ram[o:o + 128], dtype="<u2").tolist()


def table_entrelacement():
    """La table de `ppgMakeConvTableTexDC`, reproduite -- voir objets.py."""
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


def entrelacer(t16):
    out = bytearray(256)
    for i in range(16):
        for j in range(16):
            out[TABLE[j + i * 16]] = t16[i][j]
    return bytes(out)


def tuiles(chemin, index, cols, ligs):
    """{(col, lig): 256 octets entrelaces} pour un sprite, sur une grille cols x ligs."""
    r, ts = assemblage.charger(chemin)
    pose = assemblage.poser(r["sprites"][index], ts)
    if pose is None:
        return None
    img, msk, _x0, _y0 = pose
    img = np.where(msk, img, 0).astype(np.uint8)
    h, w = img.shape
    out = {}
    for lig in range(ligs):
        for col in range(cols):
            t16 = np.zeros((16, 16), np.uint8)
            a = img[lig * 16:lig * 16 + 16, col * 16:col * 16 + 16]
            if a.size:
                t16[:a.shape[0], :a.shape[1]] = a
            out[(col, lig)] = entrelacer(t16)
    return out


def ecrire(choisis):
    L = []
    a = L.append
    a("/* Genere par dc-decors/outils/animations.py -- ne pas modifier a la main. */")
    a("#include \"port/video/decor_objets.h\"")
    a("")
    a("/* UNE animation de decor par etage, choisie comme la plus riche qui tienne dans la")
    a("   grille du motif emprunte (%d cases au plus) et qui bouge assez pour se voir" % MAX_TUILES)
    a("   (%d trames par image au plus). Position, plan et palette sont lus dans la liste" % MAX_TENUE)
    a("   d'affichage de l'etat Flycast ; les images et leurs durees dans les scripts du")
    a("   binaire. Voir DONNEES.md. */")
    a("")
    noms = []
    for c in choisis:
        pref = "a%d" % c["etage"]
        for k, sp in enumerate(c["sprites"]):
            for (col, lig), octets in sorted(c["tuiles"][k].items()):
                n = "%s_i%d_%d_%d" % (pref, k, col, lig)
                a("static const unsigned char %s[256] = { %s };"
                  % (n, ", ".join(str(x) for x in octets)))
        a("")
        a("static const DecorTuile %s_tuiles[] = {" % pref)
        for k, sp in enumerate(c["sprites"]):
            for (col, lig) in sorted(c["tuiles"][k]):
                a("    { %d, %d, %d, %s_i%d_%d_%d }," % (k, col * 16, lig * 16, pref, k, col, lig))
        a("};")
        a("static const unsigned char %s_durees[%d] = { %s };"
          % (pref, len(c["durees"]), ", ".join(str(d) for d in c["durees"])))
        a("static const unsigned short %s_palette[64] = { %s };"
          % (pref, ", ".join("0x%04X" % v for v in c["palette"])))
        a("")
        noms.append((pref, c))
    a("const DecorAnimation decor_animations[] = {")
    for pref, c in noms:
        a("    { \"%s\", %d, %d, %d, %d, %d, %s_tuiles, %s_durees, %s_palette, %d, %d, %d, %d },"
          % (c["decor"], c["etage"], len(c["sprites"]),
             len(c["sprites"]) * c["cols"] * c["ligs"], c["cols"], c["ligs"],
             pref, pref, pref, c["emplacement"], c["x"], c["y"],
             2 if c["plan"] == 2 else 1))
    a("};")
    a("")
    a("const int decor_nb_animations = %d;" % len(noms))
    a("")
    a("/* Index dans `decor_animations` pour chaque etage, -1 s'il n'en a pas. */")
    par_etage = [-1] * 37
    for i, (pref, c) in enumerate(noms):
        par_etage[c["etage"]] = i
    a("const signed char decor_anim_par_etage[37] = { %s };"
      % ", ".join(str(v) for v in par_etage))
    open(SORTIE, "w", encoding="utf-8", newline="\n").write("\n".join(L) + "\n")
    return len("\n".join(L))


def main():
    if "--mire" in sys.argv:
        mire()
        return
    ass = charger_assets()
    scripts = lire_scripts()
    cands = candidats(ass, scripts)
    print("Une animation de decor par etage\n")
    choisis = []
    for dec in sorted(cands, key=lambda d: ETAGE[d]):
        c = cands[dec][0]
        c["tuiles"] = []
        ok = True
        for sp in c["sprites"]:
            t = tuiles(ass[c["asset"]]["chemin"], sp, c["cols"], c["ligs"])
            if t is None:
                ok = False
                break
            c["tuiles"].append(t)
        if not ok:
            print("  %-5s etage %2d : un sprite ne se pose pas, ecarte" % (dec, ETAGE[dec]))
            continue
        c["palette"] = palette(c["ram"], c["emplacement"])
        choisis.append(c)
        print("  %-5s etage %2d : element %2d plan %d (%4d,%4d)  %2d images, tenue %d..%d tr,"
              "  grille %dx%d = %2d tuiles  palette %d"
              % (dec, c["etage"], c["element"], c["plan"], c["x"], c["y"],
                 len(c["sprites"]), min(c["durees"]), max(c["durees"]),
                 c["cols"], c["ligs"], c["cols"] * c["ligs"], c["emplacement"]))
    manquants = [d for d in ETAGE if d not in cands and d not in ("bg08",)]
    print()
    print("  sans animation posable : %s" % ", ".join(sorted(set(manquants))))
    if "--liste" in sys.argv:
        return
    n = ecrire(choisis)
    print()
    print("  ecrit %s (%d octets, %d animations)" % (SORTIE, n, len(choisis)))




def desentrelacer(octets):
    """L'aller-retour de `entrelacer` : rend la tuile 16x16 lineaire."""
    t = [[0] * 16 for _ in range(16)]
    for i in range(16):
        for j in range(16):
            t[i][j] = octets[TABLE[j + i * 16]]
    return t


def rendre(choisis):
    """Une planche par animation, RECONSTRUITE DEPUIS LES TUILES EXPORTEES.

    C'est le point : la planche ne re-assemble pas le sprite depuis l'asset, elle rejoue
    ce que le jeu va faire -- desentrelacer chaque tuile et la poser sur la grille aux
    memes coordonnees que `DecorObjets_Motif`. Une planche qui montre le bon objet dit
    donc que l'export est juste ; si l'ecran ne lui ressemble pas, le defaut est dans le
    portage. La version d'avant re-assemblait depuis la source : elle ne pouvait rien
    reveler.

    A cote de chaque image reconstruite, la meme sortie de `assemblage.poser` : la
    reference. Les deux doivent etre identiques.
    """
    from PIL import Image
    rep = os.path.join(RACINE, "rendus", "animations")
    os.makedirs(rep, exist_ok=True)
    ass = charger_assets()
    sorties = []
    for c in choisis:
        pal = []
        for k, v in enumerate(c["palette"]):
            r = ((v >> 10) & 31) * 255 // 31
            g = ((v >> 5) & 31) * 255 // 31
            b = (v & 31) * 255 // 31
            pal.append((r, g, b, 0 if k == 0 else 255))
        w, h = c["cols"] * 16, c["ligs"] * 16
        n = len(c["sprites"])
        marge = 6
        planche = Image.new("RGBA", (n * (w + marge), h * 2 + marge), (28, 28, 36, 255))

        # rangee du haut : reconstruit depuis les tuiles exportees
        for k in range(n):
            im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            px = im.load()
            for (col, lig), octets in c["tuiles"][k].items():
                t = desentrelacer(octets)
                for yy in range(16):
                    for xx in range(16):
                        v = t[yy][xx]
                        if v:
                            px[col * 16 + xx, lig * 16 + yy] = pal[v] if v < len(pal) else (255, 0, 255, 255)
            planche.paste(im, (k * (w + marge), 0), im)

        # rangee du bas : la reference, assemblee depuis l'asset
        r, ts = assemblage.charger(ass[c["asset"]]["chemin"])
        for k, sp in enumerate(c["sprites"]):
            pose = assemblage.poser(r["sprites"][sp], ts)
            if pose is None:
                continue
            img, msk, _x0, _y0 = pose
            im = Image.new("RGBA", (w, h), (0, 0, 0, 0))
            px = im.load()
            for yy in range(min(h, img.shape[0])):
                for xx in range(min(w, img.shape[1])):
                    if msk[yy][xx]:
                        v = int(img[yy][xx])
                        px[xx, yy] = pal[v] if v < len(pal) else (255, 0, 255, 255)
            planche.paste(im, (k * (w + marge), h + marge), im)

        f = os.path.join(rep, "%s-etage%d.png" % (c["decor"], c["etage"]))
        ech = 4 if w <= 48 else 3
        planche.resize((planche.width * ech, planche.height * ech), Image.NEAREST).save(f)
        sorties.append(f)
    return sorties


# ---------------------------------------------------------------- LA MIRE
# Neuf aplats de couleurs franches en 3x3, un liseré blanc en HAUT de chaque case.
# Elle répond en une partie à la seule question que le code ne tranche pas : dans quel
# sens le moteur pose les rangées d'une grille. La matrice de fond contient un
# `njScale(0, 1.0, -1.0, 1.0)` -- un retournement de y -- mais le calcul des sommets de
# `seqsStoreChip` (v[0].y = y, v[1].y = y - h) implique le contraire. Les deux lectures
# se contredisent ; la mire ne se contredit pas.
#
# Ce qu'on lit à l'écran :
#   rouge en haut à gauche, ordre de lecture   -> la grille est juste
#   rouge en bas à gauche                      -> les RANGEES sont inversées
#   rouge en haut à droite                     -> les COLONNES sont inversées
#   liseré blanc en bas de chaque case         -> les pixels de la tuile sont inversés
#   brouillé                                   -> l'entrelacement ou le téléversement
MIRE_COULEURS = [
    (31, 0, 0), (0, 31, 0), (0, 0, 31),      # rouge   vert    bleu
    (31, 31, 0), (31, 0, 31), (0, 31, 31),   # jaune   magenta cyan
    (31, 31, 31), (15, 15, 15), (31, 16, 0), # blanc   gris    orange
]
MIRE_NOMS = ["rouge", "vert", "bleu", "jaune", "magenta", "cyan", "blanc", "gris", "orange"]


def mire():
    """Remplace l'animation de l'étage 23 par une mire de neuf aplats."""
    import numpy as np
    lignes = []
    a = lignes.append
    a("/* Genere par dc-decors/outils/animations.py --mire -- ne pas modifier a la main. */")
    a("#include \"port/video/decor_objets.h\"")
    a("")
    a("/* LA MIRE : neuf aplats en 3x3, un lisere blanc en HAUT de chaque case.")
    a("   Ordre de lecture, de gauche a droite puis de haut en bas :")
    a("     %s */" % ", ".join(MIRE_NOMS))
    a("")
    for k, nom in enumerate(MIRE_NOMS):
        t = np.full((16, 16), k + 1, np.uint8)
        t[0:2, :] = 10                       # le lisere blanc, en HAUT
        a("static const unsigned char mire_%d[256] = { %s };"
          % (k, ", ".join(str(x) for x in entrelacer(t))))
    a("")
    a("static const DecorTuile mire_tuiles[] = {")
    for k in range(9):
        a("    { 0, %d, %d, mire_%d }," % ((k % 3) * 16, (k // 3) * 16, k))
    a("};")
    a("static const unsigned char mire_durees[1] = { 60 };")
    pal = [0]
    for (r, g, b) in MIRE_COULEURS:
        pal.append(0x8000 | (r << 10) | (g << 5) | b)
    pal.append(0x8000 | (31 << 10) | (31 << 5) | 31)     # 10 : blanc du lisere
    pal += [0] * (64 - len(pal))
    a("static const unsigned short mire_palette[64] = { %s };"
      % ", ".join("0x%04X" % v for v in pal))
    a("")
    a("const DecorAnimation decor_animations[] = {")
    a("    { \"mire\", 23, 1, 9, 3, 3, mire_tuiles, mire_durees, mire_palette, 93, 480, 48, 2 },")
    a("};")
    a("")
    a("const int decor_nb_animations = 1;")
    a("const signed char decor_anim_par_etage[37] = { %s };"
      % ", ".join("0" if i == 23 else "-1" for i in range(37)))
    open(SORTIE, "w", encoding="utf-8", newline="\n").write("\n".join(lignes) + "\n")
    print("MIRE ecrite dans %s" % SORTIE)
    print("  neuf aplats 3x3 sur l'etage 23 (ALEX), un lisere blanc en HAUT de chaque case")
    print("  ordre attendu : %s" % ", ".join(MIRE_NOMS))


if __name__ == "__main__":
    main()
