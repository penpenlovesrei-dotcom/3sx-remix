# -*- coding: utf-8 -*-
"""La chaine script -> image de New Generation, et l'appariement decor -> asset.

Meme forme qu'en 2nd Impact (`annuaire2i.index_global`) :

    table   = u32 [0x8C4CC1F0 + (decor*3 + aire)*4]     (dans `ng_blocs.json`)
    ptr     = u32 [table + script*4]
    global  = u16 [ptr + 6]

et l'asset qui contient cet index global est celui dont la plage `[premier, dernier+1[`,
lue dans l'en-tete `F_ETC`, l'englobe. Les assets de NG sont deja extraits sous
`sprites/ng-bXX-F_ETCnn.bin` -- `fetc.py` les lit, son parcours ayant ete valide sur les
trente-sept assets DES DEUX JEUX.

C'EST L'APPARIEMENT QUI EST L'ENJEU. Les seize `.pk` de NG ne sont pas numerotes comme les
bandes, et rien ne dit a priori quel fichier sert quel decor. On ne le devine pas : on
resout les scripts et on regarde dans quelle plage ils tombent. Un decor dont tous les
scripts tombent dans une seule plage designe son asset sans ambiguite ; un decor qui
s'eparpille signale une erreur de lecture.
"""

import glob
import json
import os
import struct
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
sys.path.insert(0, ICI)

import fetc

BIN = open(os.path.join(RACINE, "SF3_1ST.BIN"), "rb").read()
BASE = 0x8C010000
FIN = BASE + len(BIN)


def u16(a):
    return struct.unpack_from("<H", BIN, a - BASE)[0]


def u32(a):
    return struct.unpack_from("<I", BIN, a - BASE)[0]


def dedans(a):
    return BASE <= a < FIN


def blocs():
    return json.load(open(os.path.join(ICI, "ng_blocs.json"), encoding="utf-8"))


def index_global(table, script):
    """L'index global d'animation de la premiere image d'un script, ou None."""
    if not dedans(table):
        return None

    p = u32(table + script * 4)

    if not dedans(p) or not dedans(p + 6):
        return None

    return u16(p + 6)


def spans():
    """nom d'asset -> (premier index global, dernier + 1)."""
    out = {}
    for c in sorted(glob.glob(os.path.join(RACINE, "sprites", "ng-*.bin"))):
        out[os.path.basename(c)[:-4]] = fetc.lire(open(c, "rb").read())["index_global"]
    return out


def scripts_du_decor(d):
    """Tous les couples (aire, script) d'un decor : elements ET blocs a chargeur."""
    out = set()

    # TOUS LES ENREGISTREMENTS N'ONT PAS DE SCRIPT. Les lecteurs de New Generation ne
    # portent pas les memes champs -- le rang n'a de sens que par lecteur, seul l'offset
    # d'objet en a un partout. On ne prend donc que ceux qui ont bien un `script`.
    for jeu in ("jeu1", "jeu2"):
        for b in d.get("elements", {}).get(jeu, []):
            for aire in b.get("aires", [0]):
                for e in b["enregistrements"]:
                    if "script" in e:
                        out.add((aire, e["script"]))

    for b in d.get("blocs", []):
        for e in b["enregistrements"]:
            if "script" not in e:
                continue
            for aire in (0, 1, 2):
                out.add((aire, e["script"]))

    return sorted(out)


def main():
    j = blocs()
    sp = spans()
    print("%d assets de New Generation, plages d'index global :" % len(sp))
    for nom, (a, b) in sorted(sp.items(), key=lambda x: x[1]):
        print("   %-22s %5d .. %5d" % (nom, a, b - 1))
    print()

    print("decor  nom de bande     scripts  resolus  assets touches")
    for d in j["decors"]:
        tables = [int(t, 16) for t in d["scripts_animation"]]
        sc = scripts_du_decor(d)
        touche = {}
        resolus = 0

        for aire, script in sc:
            g = index_global(tables[aire], script)
            if g is None:
                continue
            resolus += 1
            for nom, (a, b) in sp.items():
                if a <= g < b:
                    touche[nom] = touche.get(nom, 0) + 1

        ordre = sorted(touche.items(), key=lambda x: -x[1])
        print("  %2d   %-16s %4d     %4d     %s"
              % (d["decor"], d["noms_bandes"][0], len(sc), resolus,
                 ", ".join("%s x%d" % (n, c) for n, c in ordre[:3]) or "-"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
