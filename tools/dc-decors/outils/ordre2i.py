# -*- coding: utf-8 -*-
"""L ORDRE DE DESSIN DE 2ND IMPACT, decor par decor -- une seule liste triee.

Croise la liste d affichage de chaque releve (releves2/*.json) avec les profondeurs
lues (+556) des fiches de decor_objets_data.c. Rend, pour chaque decor, la suite
[couche plan k] / profondeur d objet dans l ordre ou 2I les dessine, puis encadre la
profondeur de chaque couche par les objets dessines avant et apres elle.

    python ordre2i.py            les encadrements par plan
    python ordre2i.py --detail   la suite de chaque releve

ATTENTION : les releves viennent d etats Flycast (regle 3). Cet outil sert a VERIFIER
une lecture du binaire, et n est la source de rien tant que Frederic n en a pas decide.
"""
import json, re, glob, os, collections, sys
C = open(r"C:\Temp3sx\src\port\video\decor_objets_data.c", encoding="utf-8", errors="replace").read()
FICHE = re.compile(r'\{ "(bg[0-9a-f]{2})", (\d+), \d+, \d+, \d+, \d+, \w+_tuiles, \w+, \w+, \d+, (-?\d+), (-?\d+), (\d+), (\d+), (\d+), 0x[0-9A-Fa-f]+ \},\s*/\*(.*?)\*/')
fiches = collections.defaultdict(dict)
for m in FICHE.finditer(C):
    bg, fam, z, com = m.group(1), int(m.group(5)), int(m.group(6)), m.group(8)
    e = re.search(r"element (-?\d+),(-?\d+)", com)
    if e and "priorite lue" in com:
        fiches[bg][(int(e.group(1)), int(e.group(2)))] = z
detail = "--detail" in sys.argv
inter = collections.defaultdict(list)
for f in sorted(glob.glob(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "releves2", "*.json"))):
    r = json.load(open(f, encoding="utf-8"))
    prio = {}
    for bg in r["decors"]: prio.update(fiches.get(bg, {}))
    seq = []
    for e in r["elements"]:
        d = e["drapeaux"]; nb = d & 0x0FFF; plan = (d >> 12) & 7
        if nb == 0: continue
        if e["x"] == 0 and e["y"] == 0: seq.append(("C", plan, None, e["i"]))
        elif (e["x"], e["y"]) in prio: seq.append(("O", plan, prio[(e["x"], e["y"])], e["i"]))
    if detail:
        print(os.path.basename(f), " ".join(f"[C{p}]" if t == "C" else f"{z}" for t, p, z, _ in seq))
    for k, (t, plan, _, _) in enumerate(seq):
        if t != "C": continue
        avant = [p for tt, _, p, _ in seq[:k] if tt == "O"]
        apres = [p for tt, _, p, _ in seq[k+1:] if tt == "O"]
        inter[plan].append((os.path.basename(f), max(apres) if apres else None, min(avant) if avant else None))
for plan in sorted(inter):
    L = inter[plan]
    los = [lo for _, lo, _ in L if lo is not None]; his = [hi for _, _, hi in L if hi is not None]
    print(f"couche plan {plan} ({len(L)} fois) : > {max(los) if los else '-'}  et  < {min(his) if his else '-'}")
    contradictions = [(n, lo, hi) for n, lo, hi in L if lo is not None and hi is not None and lo >= hi]
    if contradictions: print("   contradictions internes :", contradictions)
