# -*- coding: utf-8 -*-
"""Ce que le jeu a vraiment chargé pour l'étage 22, et ce que notre jeu de pages couvre.

Le dump de `tex_remix` note, pour chaque page écrite, son numéro et la liste sous
laquelle le jeu l'a chargée. On compare aux `.tex` posés : une page chargée que nous
ne fournissons pas, c'est du décor emprunté qui reste à l'écran.

    python pages22.py [dossier des .tex]
"""
import collections, glob, os, sys

DUMP = os.path.join(os.environ.get("APPDATA", ""), "CrowdedStreet", "3SX",
                    "resources", "tex_remix", "dump")
POSE = os.path.join(os.environ.get("APPDATA", ""), "CrowdedStreet", "3SX",
                    "resources", "tex_remix", "stage22")


def poses(rep):
    d = collections.defaultdict(set)
    for f in glob.glob(os.path.join(rep, "*.tex")):
        a, p = os.path.basename(f)[:-4].split("-")
        d[int(a)].add(int(p))
    return d


def main():
    rep = sys.argv[1] if len(sys.argv) > 1 else POSE
    nos = poses(rep)
    print(f"pages posees dans {rep} :")
    for li in sorted(nos):
        v = sorted(nos[li])
        print(f"   liste {li:<4d} : {len(v):3d} pages  {v[0]}..{v[-1]}")
    m = os.path.join(DUMP, "manifest.txt")
    if not os.path.exists(m):
        print("\naucun manifeste : le jeu n'a rien ecrit.")
        return
    g = collections.defaultdict(set)
    for l in open(m, encoding="utf-8", errors="replace"):
        c = l.split()
        if len(c) > 7:
            g[int(c[7])].add(int(c[5]))
    print("\npages chargees par le jeu :")
    for li in sorted(g):
        v = sorted(g[li])
        marque = ""
        if li in nos:
            manque = sorted(set(v) - nos[li])
            marque = ("  -> TOUTES couvertes" if not manque
                      else f"  -> NON COUVERTES : {manque}")
        elif li not in (0, 590, 600, 601):
            marque = "  -> liste que nous ne remplacons pas du tout"
        print(f"   liste {li:<4d} : {len(v):3d} pages  {v[0]}..{v[-1]}{marque}")
    print("\nboot et menus = listes 0, 590, 600, 601. Le reste est du decor.")


if __name__ == "__main__":
    main()
