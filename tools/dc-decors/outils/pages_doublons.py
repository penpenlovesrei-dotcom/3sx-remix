# -*- coding: utf-8 -*-
"""LES PAGES EN DOUBLE DES ETAGES AJOUTES -- 23/09/2026.

Une page d'etage ajoute vit dans `resources/tex_remix/stage<N>/<liste>-<page>.tex`, 64 Ko.
Dudley 1 (etage 44) en porte **320** : deux listes de base, une troisieme, et surtout la
pluie de Londres, un plan anime a huit vues de 32 pages
(`etagesng_pages.inc`, `[44] = { plan 2, 8 vues }`). C'est le plus lourd des quarante
etages, 20 Mo, le double du second.

Or **la pluie ne couvre qu'une partie de chaque page** : tout ce qu'elle ne touche pas se
repete d'une vue a l'autre. Mesure du 23/09 : 177 contenus distincts pour 320 fichiers,
**143 doublons octet pour octet**, dont un groupe de vingt-quatre. Et ce n'est pas propre a
Dudley -- 64 % a l'etage 37, 61 % a l'etage 22, 38 % a l'etage 45.

CE QUE FAIT CE PROGRAMME. Il garde **un fichier par contenu distinct**, efface les copies,
et ecrit a cote un `doublons.txt` qui dit, pour chaque page effacee, quelle page porte son
contenu :

    de_liste de_page vers_liste vers_page

`tex_remix.c` lit ce fichier une fois par etage et s'en sert quand le chemin direct manque.

C'EST REVERSIBLE, ET SANS PERTE : `--annuler` recopie les canoniques sous les noms effaces
et retire l'index. Rien n'est perdu puisque le contenu efface etait, par construction,
identique octet pour octet a celui qu'on garde.

    py -3 pages_doublons.py --releve      ce qu'il y a a gagner, sans rien toucher
    py -3 pages_doublons.py --appliquer   deduplique
    py -3 pages_doublons.py --annuler     remet tout comme avant
    ... --etage 44                        un seul etage
"""
import hashlib
import os
import shutil
import sys

RACINE = (r"C:\Users\frede\OneDrive\Bureau\SEPTEMBRE\SF3\CrowdedStreet-3SX"
          r"\resources\tex_remix")
INDEX = "doublons.txt"


def dossiers(etage=None):
    """Les dossiers `stage<N>`, tries par numero. `dump` n'en est pas un."""
    out = []
    for d in os.listdir(RACINE):
        if not d.startswith("stage"):
            continue
        p = os.path.join(RACINE, d)
        if not os.path.isdir(p):
            continue
        try:
            n = int(d[5:])
        except ValueError:
            continue
        if etage is None or n == etage:
            out.append((n, p))
    return sorted(out)


def nom(f):
    """`132-148.tex` -> (132, 148), pour trier et pour l'index."""
    base = f[:-4] if f.endswith(".tex") else f
    a, _, b = base.partition("-")
    return int(a), int(b)


def groupes(p):
    """Les pages du dossier, rassemblees par contenu : empreinte -> [noms tries]."""
    par = {}
    for f in os.listdir(p):
        if not f.endswith(".tex") or f == INDEX:
            continue
        with open(os.path.join(p, f), "rb") as h:
            e = hashlib.md5(h.read()).hexdigest()
        par.setdefault(e, []).append(f)
    for e in par:
        par[e].sort(key=nom)
    return par


def releve(etage=None):
    tot_f = tot_d = tot_o = tot_go = 0
    print("%-10s %6s %6s %6s %9s %9s" % ("etage", "pages", "uniq", "doubl", "Mo", "Mo apres"))
    for n, p in dossiers(etage):
        par = groupes(p)
        f = sum(len(v) for v in par.values())
        d = f - len(par)
        o = sum(os.path.getsize(os.path.join(p, x)) for v in par.values() for x in v)
        go = sum(os.path.getsize(os.path.join(p, v[0])) for v in par.values())
        if d:
            print("stage%-5d %6d %6d %6d %9.1f %9.1f" % (n, f, len(par), d, o / 1048576.0, go / 1048576.0))
        tot_f += f
        tot_d += d
        tot_o += o
        tot_go += go
    print("-" * 52)
    print("%-10s %6d %6s %6d %9.1f %9.1f   (%.0f %% de moins)"
          % ("TOTAL", tot_f, "", tot_d, tot_o / 1048576.0, tot_go / 1048576.0,
             100.0 * (tot_o - tot_go) / max(tot_o, 1)))


def appliquer(etage=None):
    for n, p in dossiers(etage):
        par = groupes(p)
        lignes = []
        for _e, v in par.items():
            garde = v[0]
            for autre in v[1:]:
                a, b = nom(autre)
                c, d = nom(garde)
                lignes.append("%d %d %d %d" % (a, b, c, d))
        if not lignes:
            continue
        lignes.sort(key=lambda l: [int(x) for x in l.split()])
        # L'INDEX D'ABORD : rien n'est efface tant qu'il n'est pas sur le disque.
        with open(os.path.join(p, INDEX), "w", newline="\n") as h:
            h.write("# page en double -> page qui porte le contenu (identique octet pour octet)\n")
            h.write("\n".join(lignes) + "\n")
        efface = 0
        for _e, v in par.items():
            for autre in v[1:]:
                os.remove(os.path.join(p, autre))
                efface += 1
        print("stage%-5d %4d pages effacees, index de %d lignes" % (n, efface, len(lignes)))


def annuler(etage=None):
    for n, p in dossiers(etage):
        i = os.path.join(p, INDEX)
        if not os.path.exists(i):
            continue
        remis = 0
        with open(i) as h:
            for l in h:
                l = l.strip()
                if not l or l.startswith("#"):
                    continue
                a, b, c, d = (int(x) for x in l.split())
                src = os.path.join(p, "%d-%d.tex" % (c, d))
                dst = os.path.join(p, "%d-%d.tex" % (a, b))
                if not os.path.exists(dst):
                    shutil.copyfile(src, dst)
                    remis += 1
        os.remove(i)
        print("stage%-5d %4d pages remises, index retire" % (n, remis))


def main():
    etage = None
    if "--etage" in sys.argv:
        etage = int(sys.argv[sys.argv.index("--etage") + 1])
    if "--appliquer" in sys.argv:
        appliquer(etage)
    elif "--annuler" in sys.argv:
        annuler(etage)
    else:
        releve(etage)


if __name__ == "__main__":
    main()
