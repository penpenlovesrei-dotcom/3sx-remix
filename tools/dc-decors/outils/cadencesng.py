# -*- coding: utf-8 -*-
"""Les cadences des sprites de decor de NEW GENERATION -- 23/09/2026.

Le pendant exact de `cadences.py`. Meme format d'enregistrement (huit octets
`{cmd, duree, 0, 0, index global}`), meme resolution de l'index par le span des `F_ETCnn`.
Seule la table maitresse change :

    2I : 0x8C5F9B38 + aire*4                 (64 aires posees bout a bout)
    NG : 0x8C4CC1F0 + (decor*3 + aire)*4     (dix-neuf decors, trois aires chacun)

    python cadencesng.py            toutes les cadences, decor par decor
    python cadencesng.py ng-b00     seulement les tables qui citent cet asset
"""
import glob
import os
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
RACINE = os.path.dirname(ICI)

import sh4ng as sh4

MAITRESSE = 0x8C4CC1F0
NB_DECORS = 19
FIN = 0x01


def dans_le_binaire(v):
    return sh4.BASE <= v < sh4.BASE + len(sh4.D)


def assets():
    import fetc
    out = {}
    for p in sorted(glob.glob(os.path.join(RACINE, "sprites", "ng-b*.bin"))):
        nom = os.path.basename(p)[:-4]
        r = fetc.lire(open(p, "rb").read())
        o = 0x20 + len(r["anims"]) * 12
        par_offset = {}
        for i, sp in enumerate(r["sprites"]):
            par_offset[o] = i
            o += 8 + len(sp["morceaux"]) * 8
        out[nom] = dict(span=r["index_global"],
                        enr=[(a[1], a[2], par_offset.get(a[4])) for a in r["anims"]])
    return out


def resout(ass, idx):
    for nom, d in ass.items():
        a, b = d["span"]
        if a <= idx < b:
            k = idx - a
            if k < len(d["enr"]):
                x, y, sp = d["enr"][k]
                return nom, k, x, y, sp
            return nom, k, None, None, None
    return None, None, None, None, None


def script(adresse, ass, maxi=64):
    out = []
    for k in range(maxi):
        o = sh4.a2o(adresse + k * 8)
        if o + 8 > len(sh4.D):
            break
        cmd, duree = sh4.D[o], sh4.D[o + 1]
        idx = sh4.u16(o + 6)
        if cmd == FIN:
            break
        if cmd == 0x00 and duree:
            out.append(dict(cmd=cmd, duree=duree, index=idx, resolu=resout(ass, idx)))
        else:
            out.append(dict(cmd=cmd, duree=duree, index=idx, resolu=(None,) * 5))
    return out


def table_du_decor(decor, aire=0):
    return sh4.u32(sh4.a2o(MAITRESSE + (decor * 3 + aire) * 4))


def tables(ass):
    """Les tables distinctes, avec les decors qui les citent."""
    vues = {}
    for d in range(NB_DECORS):
        for aire in range(3):
            t = table_du_decor(d, aire)
            if not dans_le_binaire(t):
                continue
            vues.setdefault(t, []).append((d, aire))

    out = []
    for t, ou in sorted(vues.items()):
        scripts = []
        for k in range(64):
            p = sh4.u32(sh4.a2o(t + k * 4))
            if not dans_le_binaire(p):
                break
            scripts.append((p, script(p, ass)))
        noms = set()
        for _p, s in scripts:
            for e in s:
                if e["resolu"][0]:
                    noms.add(e["resolu"][0])
        if scripts:
            out.append(dict(adresse=t, ou=ou, scripts=scripts, assets=sorted(noms)))
    return out


def main():
    filtre = sys.argv[1] if len(sys.argv) > 1 else None
    ass = assets()
    print("Les cadences des sprites de decor de New Generation")
    print("table maitresse 0x%08X + (decor*3 + aire)*4\n" % MAITRESSE)
    ntab = nscr = nimg = 0
    for t in tables(ass):
        if filtre and not any(filtre in a for a in t["assets"]):
            continue
        ntab += 1
        print("=" * 78)
        print("table 0x%08X  decors %s  assets cites : %s"
              % (t["adresse"],
                 ",".join("%d(aire %d)" % o for o in t["ou"]),
                 ", ".join(t["assets"]) or "aucun"))
        for p, s in t["scripts"]:
            nscr += 1
            images = [e for e in s if e["cmd"] == 0x00]
            connues = [e for e in images if e["resolu"][0]]
            nimg += len(images)
            if not images:
                print("   0x%08X : aucune image (commandes seules)" % p)
                continue
            total = sum(e["duree"] for e in images)
            ancres = {(e["resolu"][2], e["resolu"][3]) for e in connues}
            boucle = " ; boucle x%d" % next(
                (e["index"] for e in s if e["cmd"] == 0x0C), 0) if any(
                e["cmd"] == 0x0C for e in s) else ""
            print("   0x%08X : %d image(s), %d trames en tout%s%s"
                  % (p, len(images), total, boucle,
                     ("  ancre%s %s" % ("" if len(ancres) == 1 else "s",
                                        " ".join("(%s,%s)" % a for a in sorted(ancres))))
                     if ancres else "  (asset hors de sprites/)"))
            for e in images:
                nom, k, x, y, sp = e["resolu"]
                if nom:
                    print("        sprite %-4s (enr %4d de %-22s) pendant %3d trames"
                          % (sp, k, nom, e["duree"]))
                else:
                    print("        index global %-6d (asset non extrait)      pendant %3d trames"
                          % (e["index"], e["duree"]))
        print()
    print("=" * 78)
    print("%d tables, %d scripts, %d images" % (ntab, nscr, nimg))


if __name__ == "__main__":
    main()
