# -*- coding: utf-8 -*-
"""LES BANQUES DE PALETTES D'UNE BANDE DE NEW GENERATION — l'equivalent de `banques2i.py`.

POURQUOI CET OUTIL EXISTE
-------------------------
Frederic a signale des couleurs fausses sur `ng05` : **515 pixels verts**, dont 474 sur un
seul objet -- un vetement entier. Le vert pur `0x03E0` est une case de palette JAMAIS
ecrite : un pixel qui tombe dessus denonce une palette fausse, sans capture.

La cause n'etait aucune de celles qu'on avait ecartees une a une -- ni la base (lue dans la
table de transferts, exacte), ni le second jeu (rendu identique), ni les morceaux a
palettes multiples (aucune des fiches vertes n'en a). Elle est structurelle :

    `animerng` prend le numero de palette DANS LE SPRITE, le champ du premier morceau.
    `animer2i` le prend dans l'ENREGISTREMENT, resolu par `bases.numero(decor, drapeaux,
    offset)` -- parce qu'un decor charge DEUX banques et que l'offset du morceau choisit
    laquelle.

Et la correlation se voit : sur les 8 enregistrements de `ng05` au drapeau `0x2055`, CINQ
sont verts ; sur les 50 au drapeau `0x2040`, quatre. `0x2055` contre `0x2040`, c'est
exactement la distinction que 2I traite comme un changement de banque.

CE QUE CET OUTIL MESURE
-----------------------
Pour chaque bande, il range les offsets de morceau en groupes disjoints -- separes par un
large trou -- et, pour chaque groupe, compte les pixels qui tomberaient sur une case non
initialisee avec chaque banque candidate :

    le PREMIER JEU   entree 52 + bande de `0x8C1AAB7C`, destination 0x2000
    le SECOND JEU    entree 69 + bande, destination 0x12000

**L'INDEX 0 EST EXCLU** : il est transparent et n'est jamais peint. C'est en le comptant
que la session du 02/09 avait cru voir « 850 cases vertes » en 2I et rejete la bonne base.

LE DETECTEUR ELIMINE, IL NE CHOISIT PAS. Un groupe propre des deux cotes ne tranche rien,
et c'est dit tel quel dans le tableau.

    python banquesng.py            toutes les bandes
    python banquesng.py 5          une seule
"""
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import animerng as AN
import annuaireng as ANG
import assemblage as A
import fetc

VERT = 0x03E0
TABLE = 0x8C1AAB7C       # la table de transferts de New Generation
JEU1, JEU2 = 52, 69      # PERIMES : voir `index_jeu1` / `index_jeu2` plus bas

# LES TROIS TABLES D'INDEX, LUES DANS LE CHARGEUR D'ETAGE (0x8C03ABC6 et suivants).
#
# Le chargeur lit la bande en `@(74,r13)`, puis indexe TROIS tables d'affilee et appelle
# le meme transfert pour chacune :
#
#     0x8C18ABE4   bande*2       le SECOND jeu, destination 0x12000
#     0x8C18AC10   bande*2       le PREMIER jeu, destination 0x2000
#     0x8C18AC46   (bande-1)*2   le SECONDAIRE
#
# La troisieme est indexee par `bande - 1` -- `add #-1,r4` avant le `shll` -- et la bande
# 0 la saute. C'est elle qui donne le TROISIEME TRANSFERT de la bande 5, l'index 106,
# base 1397 : la valeur que les trois criteres de 2I avaient deja designee, retrouvee
# cette fois par le code seul.
IDX_JEU2, IDX_JEU1, IDX_SEC = 0x8C18ABE4, 0x8C18AC10, 0x8C18AC46
_banque = None


def _u16(a):
    return int.from_bytes(AN.BIN[a - AN.BASE:a - AN.BASE + 2], "little")


# `JEU1 + bande` ETAIT UNE SUPPOSITION, ET ELLE CASSE A LA BANDE 17 — 05/09/2026.
#
# On ecrivait `transfert(52 + bande)`, en lisant dans le tableau des entrees que les
# dix-sept premieres se suivaient. Elles se suivent bien pour les bandes 0 a 16, mais NG
# en a **dix-neuf** : `52 + 17` tombe sur l'entree 69, qui est le SECOND jeu de la bande
# 0. La bande 17 sortait donc avec la base 25 au lieu de 338, et le balayage lui comptait
# **64 476 pixels verts** qui n'existaient pas.
#
# La table le dit sans supposition : bande 17 -> index 57, la meme entree que la bande 5.
def index_jeu1(bande):
    return _u16(IDX_JEU1 + bande * 2)


def index_jeu2(bande):
    return _u16(IDX_JEU2 + bande * 2)


def secondaire(bande):
    """L'index de transfert secondaire de cette bande, LU dans la table. None pour 0."""
    return None if bande < 1 else _u16(IDX_SEC + (bande - 1) * 2)


def u32(a):
    return int.from_bytes(AN.BIN[a - AN.BASE:a - AN.BASE + 4], "little")


def transfert(k):
    """(base, nb palettes) de l'entree `k`, ou None si elle ne pointe pas la banque."""
    s, d, t = u32(TABLE + k * 12), u32(TABLE + k * 12 + 4), u32(TABLE + k * 12 + 8)

    if not (0x02700000 <= s < 0x02800000) or not t:
        return None

    # La banque de couleurs de NG est en RAM a 0x027B0000 ; 128 octets par palette.
    return dict(base=(s - 0x027B0000) // 128, nb=t // 128, dest=d)


def banque():
    global _banque

    if _banque is None:
        n = (len(AN.BIN) - AN.POFF) // 128
        _banque = np.frombuffer(AN.BIN[AN.POFF:AN.POFF + n * 128],
                                dtype="<u2").reshape(n, 64)

    return _banque


def cases_vertes():
    """Les cases NON INITIALISEES : rouge et bleu a zero, vert non nul.

    LE VERT N'EST PAS UNE SEULE VALEUR. `0x03E0` etait la seule connue ; l'objet `n05o19`
    de `ng05` en emploie une autre, **`0x0280`** (g = 160 au lieu de 248). Chercher la
    valeur exacte laissait donc passer 474 pixels verts en annoncant zero. Ce qui
    caracterise une case jamais ecrite, c'est le canal : rouge et bleu nuls.
    """
    b = banque()
    return ((b & 0x7C1F) == 0) & ((b & 0x03E0) != 0)


def usage(nom_asset):
    """offset de morceau -> histogramme des 64 index employes. L'index 0 est mis a zero."""
    chemin = os.path.join(AN.RACINE, "sprites", nom_asset + ".bin")
    a = fetc.lire(open(chemin, "rb").read())
    tuiles = A.charger(chemin)[1]
    h = defaultdict(lambda: np.zeros(64, np.int64))

    for sp in a["sprites"]:
        for m in A.morceaux(sp):
            k = m["tuile"]

            for i in range(m["largeur"] * m["hauteur"]):
                if k + i < len(tuiles):
                    h[m["palette"]] += np.bincount(tuiles[k + i].ravel(),
                                                   minlength=64)[:64]

    for o in h:
        h[o][0] = 0

    return h


def groupes(offs, trou=4):
    """Les offsets ranges en groupes contigus, coupes par un trou d'au moins `trou`."""
    out = []

    for o in sorted(offs):
        if out and o - out[-1][-1] <= trou:
            out[-1].append(o)
        else:
            out.append([o])

    return out


def verts(h, offs, base):
    """Les pixels qui tomberaient sur une case non initialisee avec cette base."""
    v = cases_vertes()
    n = len(banque())
    return sum(int(h[o][v[base + o]].sum()) for o in offs if 0 <= base + o < n)


def examiner(bande, tous=False):
    d = next((x for x in ANG.blocs()["decors"] if bande in x["bandes"]), None)

    if d is None:
        return None

    nom, _n = AN.asset_du_decor(d, ANG.spans())

    if nom is None:
        return None

    t1, t2 = transfert(index_jeu1(bande)), transfert(index_jeu2(bande))
    h = usage(nom)
    lignes = []

    for g in groupes(h):
        # Un transfert ne peut servir qu'un groupe qui tient dans son nombre de palettes.
        cand = []

        for nomt, t in (("jeu 1", t1), ("jeu 2", t2)):
            if t is None:
                continue

            tient = max(g) < t["nb"]
            cand.append((nomt, t["base"], verts(h, g, t["base"]), tient))

        px = sum(int(h[o].sum()) for o in g)
        lignes.append((g, px, cand))

    return nom, t1, t2, lignes


def main():
    args = [int(a, 0) for a in sys.argv[1:] if not a.startswith("-")]
    bandes = args or sorted({b for x in ANG.blocs()["decors"] for b in x["bandes"]})

    print("LES BANQUES DE PALETTES DE NEW GENERATION")
    print("le vert `0x03E0` ELIMINE une banque ; il n'en choisit pas. Index 0 exclu.")
    print()

    for bande in bandes:
        r = examiner(bande)

        if r is None:
            print("bande %-3d : pas de decor" % bande)
            continue

        nom, t1, t2, lignes = r
        print("bande %-3d %-24s jeu1 base %-5s nb %-4s | jeu2 base %-5s nb %s"
              % (bande, nom,
                 t1["base"] if t1 else "-", t1["nb"] if t1 else "-",
                 t2["base"] if t2 else "-", t2["nb"] if t2 else "-"))

        for g, px, cand in lignes:
            det = "  ".join("%s %d verts%s" % (n, v, "" if tient else " (HORS BORNE)")
                            for n, _b, v, tient in cand)
            propres = [n for n, _b, v, tient in cand if v == 0 and tient]
            verdict = ("-> %s" % propres[0] if len(propres) == 1
                       else "-> AMBIGU (%s)" % ", ".join(propres) if propres
                       else "-> AUCUNE banque propre")
            print("   offsets %-14s %7d px   %-46s %s"
                  % ("%d..%d" % (g[0], g[-1]), px, det, verdict))

        print()


if __name__ == "__main__":
    main()
