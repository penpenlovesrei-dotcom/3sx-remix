# -*- coding: utf-8 -*-
"""Ecrit `outils/ng_blocs.json` : l'attribution complete des blocs de decor de NG.

C'est le fichier machine que consomme la generation du C. Tout ce qu'il contient vient de
`blocsng.py` et de `decorsng.py` ; rien n'est saisi a la main sauf les cartes de champs
corrigees ci-dessous, qui sont relevees dans le desassemblage.

CE QU'IL FAUT SAVOIR AVANT DE LIRE LE JSON
------------------------------------------
* **Le pointeur d'un bloc pointe sur le CHAMP 0, pas sur le champ `plan`.** Le champ 0 va
  en `objet+32` ; le `plan` est le champ 1. Pour l'annuaire des elements, l'usage etabli
  sur 2nd Impact est de compter a partir de `pointeur+2` -- c'est le meme octet, appele
  autrement. `ng_blocs.json` donne les deux : `bloc` (le pointeur) et, pour chaque
  enregistrement, son adresse reelle.
* **Les offsets d'objet sont la vraie signature d'un champ**, pas son rang : les lecteurs
  n'ont ni le meme nombre de champs ni le meme ordre, mais un champ qui part en
  `objet+102` est un x chez tous.

      +558 plan     +554 drapeaux     +102 x     +106 y     +88 palette     +456 script

  (`+456 = script` est confirme par 2nd Impact : dans son annuaire des elements, le champ
  qui part en `+456` est le sixieme mot du record, celui que `SANS-ETAT.md` nomme
  `script`.)
* **x et y du chargeur B sont RELATIFS a son parent** -- et lui seul fait ca. Voir la clef
  `relatif_au_parent` de chaque bloc.

    python exportng.py
"""
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blocsng as X
import decorsng as N
import sh4ng as sh4

D, B = sh4.D, sh4.BASE
u16 = lambda a: struct.unpack_from('<H', D, a - B)[0]
s16 = lambda a: struct.unpack_from('<h', D, a - B)[0]
u32 = lambda a: struct.unpack_from('<I', D, a - B)[0]

ICI = os.path.dirname(os.path.abspath(__file__))
SORTIE = os.path.join(ICI, "ng_blocs.json")

NOMS = {558: "plan", 554: "drapeaux", 102: "x", 106: "y", 88: "palette", 456: "script"}

# Le binaire NOMME ses dix-neuf bandes : table de chaines de 12 octets en 0x8C1B7E98,
# indexee par le numero de bande. C'est ce qui donne enfin les personnages -- et chaque
# nom recoupe une conclusion tiree autrement (voir NEW-GENERATION.md, section 1 bis).
NOMS_BANDES = 0x8C1B7E98
# La premiere des dix tables de la serie : les scripts d'animation, par (decor, aire).
TABLE_SCRIPTS_ANIM = 0x8C4CC1F0


def nom_bande(b):
    a = NOMS_BANDES + b * 12
    return D[a - B:a - B + 10].decode("latin1").strip()

# Les bornes de chaque lecteur, prises entre deux debuts de fonction : sans elles
# `champs()` deborde sur la fonction suivante et compte des champs qui n'existent pas.
BORNES = {
    0x8C09C83C: 0x8C09C960, 0x8C09CA14: 0x8C09CB20, 0x8C0A0070: 0x8C0A0190,
    0x8C0A1318: 0x8C0A1410, 0x8C0A1A40: 0x8C0A1CA0, 0x8C0A21A4: 0x8C0A2404,
    0x8C0A7B9A: 0x8C0A7C70, 0x8C0A8EE4: 0x8C0A8FA8, 0x8C0AC75C: 0x8C0AC880,
    0x8C0AC934: 0x8C0ACA44,
}

# Corrections a la carte automatique : `champs()` ne modelise pas un store via un registre
# prepare a l'avance (`mov r14,r1 ; add #52,r1 ; ... ; mov.w r2,@r1`). Releve a la main.
CORRECTIONS = {
    0x8C0A1318: {9: 52},        # 0x8C0A13B8 : mov.w r2,@r1 avec r1 = objet + 52
}

# Le champ qui porte l'index du bloc SUIVANT, et le lecteur vise.
ENCHAINE = {
    0x8C0A1318: [(9, 0x8C0A21A4, "objet+52"), (15, 0x8C0A1A40, "flux, si >= 0")],
    0x8C0A1A40: [(16, 0x8C0A21A4, "objet+62")],
}

# Les lecteurs dont x et y s'ajoutent a ceux du parent (`objet[+102] += parent[+102]`).
RELATIFS = {0x8C0A21A4: (0x8C0A2262, 0x8C0A2270)}


def carte(f):
    """[(rang, offset objet)] d'un lecteur, corrections comprises."""
    ch = dict(X.champs(f, BORNES[f]))
    ch.update(CORRECTIONS.get(f, {}))
    return [(k, ch.get(k)) for k in sorted(ch)]


def enregistrements(f, p, n, T, decale=0):
    """Les enregistrements d'un bloc, champs nommes par leur offset d'objet."""
    c = carte(f)
    out = []
    for k in range(n):
        a = p + decale + k * T
        r = {"adresse": "0x%08X" % a, "champs": []}
        for rang, off in c:
            v = s16(a + rang * 2)
            r["champs"].append({"rang": rang, "octet": rang * 2, "objet": off, "valeur": v})
            if off in NOMS:
                r[NOMS[off]] = v
        out.append(r)
    return out


def bloc_json(f, arg, z, parent=None):
    n, p = X.bloc(f, arg, z)
    T = X.INDEXES[f]['T']
    if n is None:
        n = 1
    d = {"lecteur": "0x%08X" % f, "arg": arg, "z": z, "bloc": "0x%08X" % p,
         "taille_enregistrement": T, "nb": n,
         "relatif_au_parent": f in RELATIFS}
    if parent:
        d["parent"] = parent
    d["enregistrements"] = enregistrements(f, p, n, T)
    return d


def main():
    doc = {
        "binaire": "SF3_1ST.BIN",
        "base": "0x8C010000",
        "genere_par": "dc-decors/outils/exportng.py",
        "notes": {
            "pointeur": ("le pointeur d'un bloc vise le CHAMP 0 (qui part en objet+32) ; "
                         "le champ `plan` est le champ 1, deux octets plus loin"),
            "offsets_objet": {str(k): v for k, v in sorted(NOMS.items())},
            "x_y_relatifs": ("seuls les blocs du chargeur 0x8C0A21A4 sont relatifs : "
                             "0x8C0A2262 fait objet[+102] += parent[+102] et 0x8C0A2270 "
                             "objet[+106] += parent[+106]. Le parent est le premier "
                             "argument de l'appel, c'est-a-dire l'objet cree par "
                             "0x8C0A1318 (index dans son champ 9, range en objet+52) ou "
                             "par le chargeur A 0x8C0A1A40 (champ 16, range en objet+62). "
                             "Tous les autres lecteurs ecrivent x et y bruts."),
            "scripts_animation": ("script_ptr = u32[ table0[(decor*3+aire)] + script*4 ], "
                                  "avec table0 = 0x8C4CC1F0 (image .data de 0x8C4DE610). "
                                  "Le champ `script` d'un enregistrement est celui qui "
                                  "part en objet+456."),
            "z": ("z = u8[contexte+6] = (0x8C0191C0() & 3). 0x8C0191C0 est un generateur "
                  "pseudo-aleatoire a table : compteur u16 en 0x8C549504 incremente et "
                  "masque a 63, puis lecture de u16[0x8C153C04 + compteur*2]. Les 64 "
                  "valeurs de la table donnent exactement 16 fois chacun des restes 0..3. "
                  "z est donc un TIRAGE UNIFORME refait a chaque entree d'etage, PAS un "
                  "numero de round. Les quatre blocs d'un couple (lecteur, arg) sont "
                  "quatre variantes equiprobables."),
            "attribution": ("l'appelant fait foi : les appels sont pris dans le corps meme "
                            "de la routine de decor, bornee par la suivante"),
        },
        "bandes": [{"bande": b, "nom": nom_bande(b),
                    "script_etage": "0x%08X" % u32(N.TABLE_ETAGES + b * 4)
                                    if b < N.NB_ETAGES else None,
                    "pvc": "bg_set%02x.pvc" % b}
                   for b in range(20)],
        "lecteurs": {},
        "decors": [],
    }

    for f, d in sorted(X.INDEXES.items()):
        doc["lecteurs"]["0x%08X" % f] = {
            "taille_enregistrement": d['T'],
            "table_nombres": "0x%08X" % d['nb'] if d['nb'] else None,
            "table_pointeurs": "0x%08X" % (d.get('ptr') or d['dur']),
            "indexation": "(arg, z)" if d['z'] else "(arg)",
            "un_seul_enregistrement": bool(d.get('un')),
            "relatif_au_parent": f in RELATIFS,
            "champs": [{"rang": k, "objet": o, "nom": NOMS.get(o)} for k, o in carte(f)],
            "enchaine": [{"champ": c, "vers": "0x%08X" % g, "par": v}
                         for c, g, v in ENCHAINE.get(f, [])],
        }
    for f in (0x8C09C83C, 0x8C09CA14):
        doc["lecteurs"]["0x%08X" % f] = {
            "taille_enregistrement": N.TAILLE_ELEMENT,
            "table_nombres": "0x%08X" % (N.NB_ELEMENTS if f == 0x8C09C83C
                                         else N.NB_ELEMENTS2),
            "table_pointeurs": "0x%08X" % (N.PTR_ELEMENTS if f == 0x8C09C83C
                                           else N.PTR_ELEMENTS2),
            "indexation": "(decor*3 + aire), pris dans le contexte 0x8C552674",
            "un_seul_enregistrement": False,
            "relatif_au_parent": False,
            "champs": [{"rang": k, "objet": o, "nom": NOMS.get(o)} for k, o in carte(f)],
            "enchaine": [],
        }

    par_routine = {}
    for r, a, b in X.routines():
        par_routine[r] = sorted({(c, v, s) for s, c, (k, v) in X.appels(a, b)
                                 if c in X.INDEXES and k == 'const'})
    # Le seul bloc atteint plus loin qu'un appel direct, verifie a part (cf. NEW-GENERATION)
    par_routine[0x8C08BFE0].append((0x8C0A21A4, 6, 0x8C0A8398))

    for d in range(N.NB_DECORS):
        bandes = [N.bande(d, a) for a in range(3)]
        fiche = {"decor": d, "bandes": bandes,
                 "noms_bandes": [nom_bande(x) for x in bandes],
                 "scripts_animation": ["0x%08X" % u32(TABLE_SCRIPTS_ANIM + (d * 3 + a) * 4)
                                       for a in range(3)],
                 "routines": sorted({"0x%08X" % N.routine(x) for x in bandes
                                     if N.routine(x)}),
                 "elements": {"jeu1": [], "jeu2": []}, "blocs": []}
        for jeu, (tnb, tptr, lec) in enumerate((
                (N.NB_ELEMENTS, N.PTR_ELEMENTS, 0x8C09C83C),
                (N.NB_ELEMENTS2, N.PTR_ELEMENTS2, 0x8C09CA14))):
            vus = set()
            for a in range(3):
                n = u16(tnb + (d * 3 + a) * 2)
                p = u32(tptr + (d * 3 + a) * 4)
                if (n, p) in vus or not n:
                    continue
                vus.add((n, p))
                fiche["elements"]["jeu%d" % (jeu + 1)].append({
                    "aires": [k for k in range(3)
                              if u32(tptr + (d * 3 + k) * 4) == p],
                    "lecteur": "0x%08X" % lec, "bloc": "0x%08X" % p, "nb": n,
                    "taille_enregistrement": N.TAILLE_ELEMENT,
                    "enregistrements": enregistrements(lec, p, n, N.TAILLE_ELEMENT)})

        for r, a, b in X.routines():
            if r not in [N.routine(x) for x in bandes if N.routine(x)]:
                continue
            for c, v, site in par_routine[r]:
                for z in (range(4) if X.INDEXES[c]['z'] else [0]):
                    n, p = X.bloc(c, v, z)
                    if not X.DONNEES(p) or (n is not None and (n == 0 or n > 300)):
                        continue
                    e = bloc_json(c, v, z)
                    e["routine"] = "0x%08X" % r
                    e["appel"] = "0x%08X" % site
                    e["bandes"] = [x for x in bandes if N.routine(x) == r]
                    fiche["blocs"].append(e)
                    # l'arbre
                    for champ, vers, comment in ENCHAINE.get(c, []):
                        idx = s16(p + champ * 2)
                        if idx < 0 or idx > 8:
                            continue
                        n2, p2 = X.bloc(vers, idx, 0)
                        if not X.DONNEES(p2) or not n2:
                            continue
                        f2 = bloc_json(vers, idx, 0,
                                       parent={"bloc": "0x%08X" % p, "lecteur":
                                               "0x%08X" % c, "par": comment})
                        f2["routine"] = "0x%08X" % r
                        f2["bandes"] = e["bandes"]
                        fiche["blocs"].append(f2)
                        for champ3, vers3, com3 in ENCHAINE.get(vers, []):
                            i3 = s16(p2 + champ3 * 2)
                            if i3 < 0 or i3 > 8:
                                continue
                            n3, p3 = X.bloc(vers3, i3, 0)
                            if not X.DONNEES(p3) or not n3:
                                continue
                            f3 = bloc_json(vers3, i3, 0,
                                           parent={"bloc": "0x%08X" % p2,
                                                   "lecteur": "0x%08X" % vers,
                                                   "par": com3})
                            f3["routine"] = "0x%08X" % r
                            f3["bandes"] = e["bandes"]
                            fiche["blocs"].append(f3)
        doc["decors"].append(fiche)

    with open(SORTIE, "w", encoding="utf-8") as f:
        json.dump(doc, f, ensure_ascii=False, indent=1)

    nb = sum(len(x["enregistrements"]) for d in doc["decors"] for x in d["blocs"])
    nel = sum(len(x["enregistrements"]) for d in doc["decors"]
              for j in d["elements"].values() for x in j)
    print("%s ecrit" % SORTIE)
    print("  %d decors, %d blocs a chargeur (%d enregistrements), %d elements"
          % (len(doc["decors"]), sum(len(d["blocs"]) for d in doc["decors"]), nb, nel))


if __name__ == "__main__":
    main()
