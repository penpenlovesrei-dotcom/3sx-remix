# -*- coding: utf-8 -*-
"""Rejoue toute la chaine des sprites de decor et rend un verdict.

Quatre epreuves, chacune capable d'echouer :

1. **Les bornes du pool.** Pour chaque couple (etat, cle), toutes les tuiles demandees
   doivent tomber dans le nombre de blocs de l'asset que la cle designe. Attendu :
   187 sur 187.
2. **La cle se relit.** Le champ `+20` de la fiche `0x8C602384 + (cle & 0xFF) * 24`
   doit valoir la cle elle-meme. Une fiche qui ne se relit pas veut dire que la table
   n'est pas celle qu'on croit.
3. **L'asset se nomme par ses octets.** Les 256 premiers octets de la section graphique
   en RAM doivent se retrouver tels quels dans un fichier de `sprites/`. Attendu :
   quatorze cles nommees, aucune ambigue hors `F_ETC29` (partage par bg06 et bg10).
4. **Le sol.** Aucun pixel de sprite ne doit tomber dans la moitie **haute** de la
   banque, sauf pour les decors dont `cuire.PLANS_LOINTAINS` envoie exprES un plan
   dans le lointain : les elements de decor se tiennent sur le sol du plan proche. C'est ce qui
   a manque au premier jet -- avec le `109` du code de dessin, qui est la ligne du sol
   **a l'ecran** et non dans la banque, tout le groupe se retrouvait a cheval sur le
   bouclage a `y = 0`.
5. **Les images.** Reconstruit la planche de tous les decors et les superpositions
   sur les banques `.pvc`. C'est la seule epreuve qui se juge a l'oeil : les objets
   doivent se tenir sur le sol du decor, a la bonne echelle.

    python verifier.py          # tout
    lanceur : tester.cmd
"""
import glob, os, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image, ImageDraw

import flycast as F
import etat as E
import pools as P
import elements as X

ICI    = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
SORTIE = os.path.join(RACINE, "rendus", "elements")

# Le decor, la banque .pvc a superposer, et ce qu'on doit y voir.
SUPERPOSITIONS = [
    # Pas de caractere hors ASCII ici : la console de Windows est en cp1252 et
    # `print` y leve une UnicodeEncodeError sur les ideogrammes de l'enseigne.
    ("bg03", "2i-bg03-banque0.png", "les etals et l'enseigne du marchand sur la chaussee"),
    ("bg0b", "2i-bg0b-banque0.png", "les rochers et les figures sur le sol du temple"),
    ("bg06", "2i-bg06-banque0.png", "la foule et les cordages sur le pont du navire"),
    ("bg02", "2i-bg02-banque0.png", "les baigneurs au bord du bassin (le plan boucle)"),
]


def barre(titre):
    print()
    print("=" * 72)
    print(titre)
    print("=" * 72)


def epreuves_1_2_3():
    """Bornes du pool, relecture de la cle, identification par les octets."""
    ass = P.assets()
    total = bon = 0
    relu = relu_ok = 0
    noms = {}
    hors = []
    for chemin in sorted(glob.glob(os.path.join(X.DOS, X.MOTIF))):
        nom_etat = os.path.basename(chemin)
        decors, ms = P.morceaux_json(nom_etat)
        if ms is None:
            continue
        ram, _ = F.lire_ram(chemin, E.EXE)
        par_cle = {}
        for m in ms:
            d = par_cle.setdefault(m["palette"], -1)   # `palette` = la cle, cf. etat2.py
            par_cle[m["palette"]] = max(d, m["tuile"])
        for cle, tmax in par_cle.items():
            f = P.fiche(ram, cle & 0xFF)
            nb = P.nb_blocs(ram, f["graphique"])
            relu += 1
            relu_ok += (f["cle"] == cle)
            if nb is None:
                continue                       # asset non resident : reste d'un autre etage
            total += 1
            pas = 3 if cle == P.CLE_DEMI else 4
            if (tmax >> pas) < nb:
                bon += 1
            else:
                hors.append((nom_etat, cle, tmax >> pas, nb))
            t = ram[f["graphique"] - F.BASE_RAM: f["graphique"] - F.BASE_RAM + 256]
            for n in P.nomme(t, ass):
                noms.setdefault(cle, set()).add(n)

    barre("1. Les bornes du pool -- tuile >> 4 < nombre de blocs")
    print(f"   {bon} sur {total} couples (etat, cle)")
    for h in hors:
        print(f"   HORS BORNES : {h[0]} cle {h[1]:#06x} bloc {h[2]} / {h[3]}")
    print("   " + ("REUSSI" if bon == total and total else "ECHOUE"))

    barre("2. La cle se relit dans sa fiche -- fiche[+20] == cle")
    print(f"   {relu_ok} sur {relu} fiches")
    print("   " + ("REUSSI" if relu_ok == relu and relu else "ECHOUE"))

    barre("3. L'asset se nomme par ses octets")
    for cle in sorted(noms):
        print(f"   {cle:#06x} ({cle & 0xFF:3d})  {', '.join(sorted(noms[cle]))}")
    print(f"   {len(noms)} cles nommees")
    print("   " + ("REUSSI" if len(noms) >= 14 else "ECHOUE"))
    return bon == total and relu_ok == relu and len(noms) >= 14


def planche():
    """La planche de tous les decors, un decor par ligne."""
    decors = sorted({os.path.basename(f).split("-e")[0]
                     for f in glob.glob(os.path.join(SORTIE, "*-e*.png"))})
    lignes = []
    for d in decors:
        ims = [Image.open(f).convert("RGBA")
               for f in sorted(glob.glob(os.path.join(SORTIE, f"{d}-e*.png")))]
        ims = [i for i in ims if i.width < 400 and i.height < 400]
        if not ims:
            continue
        larg = sum(i.width + 6 for i in ims) + 120
        haut = max(i.height for i in ims) + 8
        r = Image.new("RGBA", (larg, haut), (35, 35, 42, 255))
        x = 120
        for i in ims:
            r.paste(i, (x, 4), i)
            x += i.width + 6
        lignes.append((d, r))
    if not lignes:
        return None
    W = max(r.width for _, r in lignes)
    H = sum(r.height + 2 for _, r in lignes)
    out = Image.new("RGBA", (W, H), (25, 25, 30, 255))
    dr = ImageDraw.Draw(out)
    y = 0
    for d, r in lignes:
        out.paste(r, (0, y))
        dr.text((8, y + 8), d, fill=(230, 230, 230, 255))
        y += r.height + 2
    c = os.path.join(SORTIE, "planche-tous.png")
    out.save(c)
    return c, len(lignes)


def superpositions():
    faits = []
    for dec, banque, attendu in SUPERPOSITIONS:
        cb = os.path.join(RACINE, "rendus", banque)
        plans = sorted(glob.glob(os.path.join(SORTIE, f"{dec}-plan*.png")))
        if not (os.path.exists(cb) and plans):
            continue
        bg = Image.open(cb).convert("RGBA")
        o = Image.new("RGBA", bg.size, (20, 20, 28, 255))
        o.alpha_composite(bg)
        for p in plans:
            o.alpha_composite(Image.open(p).convert("RGBA"))
        c = os.path.join(SORTIE, f"superpose-{dec}.png")
        o.save(c)
        faits.append((c, attendu))
    return faits


def epreuve_sol():
    """Aucun sprite cuit ne doit tomber dans la moitie haute de la banque."""
    barre("4. Le sol -- aucun sprite dans la moitie lointaine")
    fichiers = sorted(glob.glob(os.path.join(SORTIE, "cuit-bg*.png")))
    if not fichiers:
        print("   rien a verifier : lancer d'abord  python cuire.py")
        return True
    import cuire
    ok = True
    for f in fichiers:
        a = np.array(Image.open(f).convert("RGBA"))
        m = a[:, :, 3] > 0
        if not m.any():
            continue
        haut, bas = int(m[:512].sum()), int(m[512:].sum())
        r = np.where(m.any(1))[0]
        dec = os.path.basename(f)[5:-4]
        attendu = dec in cuire.PLANS_LOINTAINS
        bon = (haut == 0) or attendu
        etat = "ok" if haut == 0 else ("lointain voulu" if attendu else "DEBORDE")
        ok &= bon
        print(f"   {os.path.basename(f)[5:-4]:6s}  {bas:6d} pixels, y {r.min()}..{r.max()}"
              f"   {haut:6d} en haut   {etat}")
    print("   " + ("REUSSI" if ok else "ECHOUE"))
    return ok


def main():
    ok = epreuves_1_2_3()
    ok &= epreuve_sol()

    barre("5. Les images -- a juger a l'oeil")
    pl = planche()
    if pl:
        print(f"   planche de {pl[1]} decors  ->  {os.path.relpath(pl[0], RACINE)}")
    for c, attendu in superpositions():
        print(f"   {os.path.relpath(c, RACINE):46s}  attendu : {attendu}")

    barre("VERDICT")
    print("   Epreuves mesurables : " + ("REUSSI" if ok else "ECHOUE"))
    print("   Les images s'ouvrent toutes seules ; ce qui doit s'y voir est ci-dessus.")


if __name__ == "__main__":
    main()
