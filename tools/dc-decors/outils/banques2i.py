# -*- coding: utf-8 -*-
"""LES BANQUES DE PALETTES D'UN DECOR : combien, et laquelle pour quels offsets.

CE QUE CET OUTIL REPOND
-----------------------
Un decor ne charge pas UNE banque de palettes mais DEUX, et les documents le savaient
pour Oro et Ryu sans en faire une regle :

    le PREMIER JEU   index = u16[0x8C1D5D38 + bande*2], entree de 0x8C1E4B50
                     destination 0x2000, `nb` palettes -- emplacements 64 et suivants
    le SECONDAIRE    index passe EN DUR par le script d'etage, destination CONTIGUE
                     au premier jeu dans la palette RAM

La contiguite n'est pas supposee : sur les neuf secondaires connus, **huit** ont pour
destination exactement `0x2000 + nb1 * 128`, la suite immediate du premier jeu. Une
adresse au hasard ne fait pas ca. (Le neuvieme, `bg06`, tombe un emplacement plus loin.)

Et c'est l'OFFSET DU MORCEAU qui choisit la banque, pas ses drapeaux -- les drapeaux sont
les bits de retournement, voir `bases.numero`. Les offsets d'un decor se rangent en
groupes disjoints separes par un large trou, et chaque groupe tire sur une banque.

LE DETECTEUR, ET SA SEULE CONDITION
-----------------------------------
Le vert pur `0x03E0` remplit les cases de palette JAMAIS ecrites. Un pixel qui tombe
dessus denonce une palette fausse, sans capture. Il ELIMINE, il ne choisit pas : sur les
2715 palettes de la banque, environ 2000 passent le test.

**L'INDEX 0 EST EXCLU.** Il est transparent et n'est jamais peint. C'est en le comptant
que la session du 02/09 a cru voir « 850 cases vertes » chez Hugo et a rejete la bonne
base. Index 0 exclu, la mesure change de camp.

    python banques2i.py           tous les decors
    python banques2i.py bg06      un seul, en detail
"""
import os
import sys
from collections import defaultdict

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import assemblage as A
import bases
import inventaire as I
import palettes
import poser2i as P

VERT = 0x03E0
IDX_JEU1 = 0x8C1D5D38

# Le decor -> sa bande (la table 0x8C1D591C dit `decor*3 + aire -> bande` ; ici on va
# droit a la bande, qui est ce qui indexe la table des palettes).
BANDES = {"bg00": 0, "bg01": 1, "bg02": 2, "bg03": 3, "bg04": 4, "bg05": 5,
          "bg06": 6, "bg08": 8, "bg0a": 10, "bg0b": 11, "bg0c": 12, "bg0d": 13,
          "bg0e": 14, "bg0f": 15, "bg10": 16}

# LES INDEX DE TRANSFERT SECONDAIRE NE SONT PAS "EN DUR" : ILS SONT DANS UNE TABLE.
#
# On les avait releves un a un dans les scripts d'etage, et ecrits a la main :
#
#     EN_DUR = {2: 103, 3: 106, 4: 101, 5: 97, 6: 96, 8: 98, 9: 99, 10: 108, 11: 107}
#
# Neuf bandes sur dix-sept, et les huit autres reputees sans secondaire. C'etait une
# collecte, pas une lecture. **La table existe** : trois tables paralleles se suivent dans
# le binaire, et le chargeur d'etage les lit l'une apres l'autre --
#
#     0x8C1D5D14   bande*2       le SECOND jeu, destination 0x12000
#     0x8C1D5D38   bande*2       le PREMIER jeu, destination 0x2000
#     0x8C1D5D66   (bande-1)*2   le SECONDAIRE
#
# La troisieme est indexee par `bande - 1` : la bande 0 n'en a pas, et le code saute la
# lecture pour elle. Elle rend **les neuf valeurs relevees a la main, les neuf exactes**,
# et sept de plus -- bandes 1, 7, 12, 13, 14, 15 et 16. Le meme motif existe en New
# Generation, table `0x8C18AC46`, ou il a donne le troisieme transfert de la bande 5.
#
# Le controle independant : la bande 16 rend l'index 96, base 1652 -- exactement ce que
# `BANQUES_2I['bg10']` portait deja, etabli par le detecteur de vert seul.
SECONDAIRES = 0x8C1D5D66


def secondaire(bande):
    """L'index de transfert secondaire de cette bande, LU dans la table. None pour 0."""
    return None if bande < 1 else I.u16(SECONDAIRES + (bande - 1) * 2)

_banque = None


def banque():
    global _banque
    if _banque is None:
        _banque = palettes.lire_brut(P.BIN, P.POFF, 2715)
    return _banque


def cases_vertes():
    """Pour chaque palette, quelles de ses 64 cases sont NON INITIALISEES.

    LE VERT N'EST PAS UNE SEULE VALEUR. `0x03E0` (g = 248) etait la seule connue, et
    chercher cette valeur exacte a fait annoncer « zero vert » alors qu'il en restait
    3207 sur les fiches compilees -- l'objet `n05o19` de New Generation emploie `0x0280`
    (g = 160). Ce qui caracterise une case jamais ecrite, ce sont les CANAUX : rouge et
    bleu nuls, vert non nul. La premisse etroite a masque le defaut des deux cotes.
    """
    b = banque()
    return ((b & 0x7C1F) == 0) & ((b & 0x03E0) != 0)


def usage(decor):
    """offset -> histogramme des 64 index employes par les morceaux de cet offset.

    Tout l'asset, sprites poses ou non. L'index 0 est mis a zero : il est transparent.
    """
    a, tuiles = P.asset(bases.ASSETS[decor])
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


def transferts(bande):
    """(premier jeu, secondaire) de cette bande, les deux LUS dans leurs tables."""
    j1 = I.transfert(I.u16(IDX_JEU1 + bande * 2))
    d = secondaire(bande)
    return j1, (I.transfert(d) if d is not None else None)


def examiner(decor, bavard=False):
    bande = BANDES[decor]
    j1, sec = transferts(bande)
    h = usage(decor)
    offs = sorted(h)
    gs = groupes(offs)
    lignes = []

    for g in gs:
        px = sum(int(h[o].sum()) for o in g)
        cand = [("jeu 1", j1["base"], j1["nb"])]

        if sec is not None:
            cand.append(("secondaire", sec["base"], sec["nb"]))

        mes = []
        for nom, b, nb in cand:
            v = verts(h, g, b)
            hors = [o for o in g if o >= nb]
            mes.append((nom, b, v, hors))

        lignes.append((g, px, mes))

    if bavard:
        print("%s : bande %d" % (decor, bande))
        print("   jeu 1       base %-5d %2d palettes  (dst 0x2000, fin 0x%04X)"
              % (j1["base"], j1["nb"], 0x2000 + j1["nb"] * 128))
        if sec is not None:
            print("   secondaire  base %-5d %2d palettes  (dst 0x%04X)%s"
                  % (sec["base"], sec["nb"], sec["destination"],
                     "  CONTIGU" if sec["destination"] == 0x2000 + j1["nb"] * 128
                     else "  (pas contigu)"))
        else:
            print("   secondaire  -- aucun index en dur releve --")
        print()

    return j1, sec, lignes


def main():
    cibles = sys.argv[1:] or sorted(d for d in bases.ASSETS if d in BANDES)
    seul = len(cibles) == 1

    print("%-6s %-16s %-9s %-24s %s"
          % ("decor", "groupe d'offsets", "pixels", "jeu 1", "secondaire"))
    print("-" * 88)

    for decor in cibles:
        if decor not in BANDES or decor not in bases.ASSETS:
            continue

        if seul:
            print()

        j1, sec, lignes = examiner(decor, bavard=seul)

        for g, px, mes in lignes:
            cols = []
            for nom, b, v, hors in mes:
                t = "%d : %d verts" % (b, v)
                if hors:
                    t += " (%d hors plage)" % len(hors)
                cols.append(t)

            etiquette = ("%d..%d" % (g[0], g[-1])) if len(g) > 1 else str(g[0])
            # celle qui gagne : zero vert, aucun offset hors plage
            gagne = [nom for nom, b, v, hors in mes if v == 0 and not hors]
            note = ""
            if len(gagne) == 1:
                note = "   -> %s" % gagne[0]
            elif not gagne:
                note = "   -> AUCUNE ne convient"

            print("%-6s %-16s %-9d %-24s %-24s%s"
                  % (decor, etiquette, px, cols[0],
                     cols[1] if len(cols) > 1 else "-", note))

        print()


if __name__ == "__main__":
    main()
