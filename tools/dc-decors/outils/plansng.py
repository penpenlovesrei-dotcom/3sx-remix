# -*- coding: utf-8 -*-
"""LES PLANS ANIMES DE NEW GENERATION -- la pluie de Londres et l'horizon de Gill.

POURQUOI PAS DES OBJETS
-----------------------
Une animation de page qui ne touche que quelques cases se sert en objets (`pagesng.py`).
Mais deux d'entre elles changent leur couche ENTIERE, sur les 1024 colonnes :

  * la pluie de Dudley 1 (id 11, `0x8C09DFBC`) : quatre cartes -- quatre textures de pluie
    prises en u 0, 256, 512 et 768 de la banque -- et, un pas sur deux, le decalage de 512
    lignes qui montre l'autre copie de la scene. HUIT vues, et les 32 puces changent a
    chaque pas. En objets il faudrait plus de deux mille morceaux : impossible.
  * l'horizon de Gill (id 12, `0x8C09E298`) : deux cartes et le meme decalage, quatre vues.
    En objets, seules les cases qui tiennent dans le budget etaient posees -- Frederic :
    « il manque plusieurs grosses vagues de lave ».

LE MECANISME DU JEU, ET IL EXISTE DEJA
--------------------------------------
3rd Strike sait remplacer une puce de 128x128 par une autre au fil des trames : c'est
`bgrw` (`rewrite_scr`, `bgrw_on`, `bgRWWorkUpdate`), avec une liste de pages en plus dans
l'archive de l'etage, chargee en `(plans * 64) + 0x64`. On s'en sert autrement : au lieu
d'une entree par puce, le plan ENTIER bascule sur la vue courante -- `bgDrawOneScreen`
decale l'index de puce vers la liste de reecriture. Une vue = 32 pages.

CE QUE CET OUTIL FAIT
---------------------
  * il ecrit les pages des vues 1..n-1 (la vue 0 est la page posee par `couchesng`) ;
  * il emet `etagesng_pages.inc` : les suites (duree, vue), la table des plans animes et
    le nombre de pages de reecriture par etage.

    python plansng.py            ce qu'il ferait
    python plansng.py --ecrire   les pages et l'include
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import bande3sx
import couchesng as C
import descripteursng as D
import etagesng as E

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
RESSOURCES = r"C:\Users\frede\OneDrive\Bureau\SEPTEMBRE\SF3\CrowdedStreet-3SX\resources\tex_remix"
INCLUDE = r"C:\Temp3sx\src\port\video\etagesng_pages.inc"
INCLUDE_REECRITURE = r"C:\Temp3sx\src\port\video\etagesng_reecriture.inc"
PAGES_PAR_VUE = 32


def _vues_pluie():
    return [({0: t}, y) for t in range(4) for y in (512, 0)]


def _suite_pluie():
    """Les pas de l'id 11 : quatorze motifs, chacun repete son tableau de quatre pas."""
    vues = _vues_pluie()
    rang = {(c[0], y): i for i, (c, y) in enumerate(vues)}
    out = []
    for p in range(14):
        rep, t = D._lit(0x8C1AFCE4 + p * 4, "<HH")
        pas = D.table_pas(0x8C1AFC24 + t * 24, 4)
        for _ in range(rep):
            for carte, y, duree in pas:
                out.append((duree, rang[(carte, y)]))
    return out


def _vues_gill():
    return [({0: t}, y) for t, y, _d in D.table_pas(0x8C1AFE1C, 4)]


def _suite_gill():
    return [(d, i) for i, (_t, _y, d) in enumerate(D.table_pas(0x8C1AFE1C, 4))]


# LES PLANS ANIMES, bande par bande. `couche` est la demi-banque dessinee, donc la liste
# du port ; `vues[0]` doit etre l'etat que `descripteursng.ETATS` pose dans la page.
PLANS = {
    0: [dict(couche=0, vues=_vues_gill(), suite=_suite_gill(),
             quoi="l'horizon de Gill (id 12) : deux cartes, deux copies")],
    7: [dict(couche=0, vues=_vues_pluie(), suite=_suite_pluie(),
             quoi="la pluie de Londres (id 11) : quatre cartes, deux copies")],
}


def liste_de_couche(bande, couche):
    """(liste du port, rang du plan) de la couche d'une bande."""
    f = E.fiche(bande)
    for liste in sorted(f["couches"]):
        if f["couches"][liste][2] == couche:
            return liste, sorted(f["couches"]).index(liste)
    return None, None


def premier_gix(bande):
    """Le premier index de la liste de reecriture : `(plans * 64) + 0x64`."""
    return len(E.fiche(bande)["couches"]) * 64 + 100


def plan_anime(bande):
    """[(plan, vues, premiere, suite, quoi, pages)] pour une bande."""
    out, premiere = [], 0
    for a in PLANS.get(bande, []):
        liste, plan = liste_de_couche(bande, a["couche"])
        if liste is None:
            print("   bande %d : la couche %d n'a pas de liste" % (bande, a["couche"]))
            continue
        pages = (len(a["vues"]) - 1) * PAGES_PAR_VUE
        out.append(dict(a, plan=plan, liste=liste, premiere=premiere, pages=pages))
        premiere += pages
    return out


def ecrire_pages(bande, a, ecrire):
    """Les pages des vues 1..n-1, dans le dossier de travail et dans celui du jeu."""
    etage = E.PREMIER_ETAGE + bande
    gix = premier_gix(bande)
    dossiers = [os.path.join(RACINE, "etagesng-sprites", "stage%d" % etage),
                os.path.join(RESSOURCES, "stage%d" % etage)]
    for v, (choix, decalage) in enumerate(a["vues"]):
        if v == 0:
            continue
        # LES MEMES EVIDEMENTS QUE LA PAGE DE L'ETAGE : une case servie par un objet anime
        # est retiree de toutes les vues, sinon elle reapparaitrait sous lui.
        plan = C.page_decrite(bande, a["couche"], choix, decalage)
        for i in range(PAGES_PAR_VUE):
            px, py = (i & 7) * 128, 512 + (i >> 3) * 128
            n = gix + a["premiere"] + (v - 1) * PAGES_PAR_VUE + i
            if not ecrire:
                continue
            for d in dossiers:
                os.makedirs(d, exist_ok=True)
                bande3sx.ecrire_tex(os.path.join(d, "%d-%d.tex" % (gix, n)),
                                    plan[py:py + 128, px:px + 128])


NL = chr(10)


def include():
    lignes = ["/* Genere par dc-decors/outils/plansng.py -- ne pas modifier a la main.",
              " *",
              " * LES PLANS ANIMES DE NEW GENERATION. Une couche entiere change d'image au fil",
              " * des trames : le plan bascule sur une VUE, et chaque vue est un jeu de 32 pages",
              " * dans la liste de reecriture de l'etage (`rewrite_scr`, chargee en (plans*64)+0x64).",
              " * La suite donne (duree, vue) et boucle. Lu dans les routines des objets id 11 et",
              " * id 12, et dans les descripteurs de scene. */",
              ""]
    table, reecriture = [], []
    for bande in sorted(PLANS):
        etage = E.PREMIER_ETAGE + bande
        entrees, total = [], 0
        for a in plan_anime(bande):
            nom = "ng_plan_anime_%d_%d" % (etage, a["plan"])
            pas = "".join(" %d, %d," % (d, v) for d, v in a["suite"])
            lignes.append("/* %s */" % a["quoi"])
            lignes.append("static const s16 %s[] = {%s -1 };" % (nom, pas))
            lignes.append("")
            entrees.append("{ %d, %d, %d, %s }" % (a["plan"], len(a["vues"]),
                                                   a["premiere"], nom))
            total += a["pages"]
        table.append("    [%d] = { %s }" % (etage, ", ".join(entrees)))
        reecriture.append("    [%d] = %d" % (etage, total))
    lignes.append("#define ETAGESNG_PLANS_ANIMES \\")
    lignes.append((", \\" + NL).join(table))
    lignes.append("")
    r = ["/* Genere par dc-decors/outils/plansng.py -- ne pas modifier a la main.",
         " *",
         " * Combien de pages de REECRITURE chaque etage de New Generation demande : une vue",
         " * d'un plan anime en prend 32, et la vue 0 est la page de l'etage. Voir `bg.c`. */",
         "",
         "#define ETAGESNG_REWRITE \\",
         (", \\" + NL).join(reecriture) + ",",
         ""]
    return NL.join(lignes), NL.join(r)


def main():
    ecrire = "--ecrire" in sys.argv
    for bande in sorted(PLANS):
        for a in plan_anime(bande):
            print("bande %2d  etage %d  plan %d (liste %d)  %d vues  %d pages  %d pas  %s"
                  % (bande, E.PREMIER_ETAGE + bande, a["plan"], a["liste"], len(a["vues"]),
                     a["pages"], len(a["suite"]), a["quoi"]))
            ecrire_pages(bande, a, ecrire)
    if ecrire:
        inc, reec = include()
        open(INCLUDE, "w", encoding="utf-8").write(inc)
        open(INCLUDE_REECRITURE, "w", encoding="utf-8").write(reec)
        print("ecrit %s et %s" % (INCLUDE, INCLUDE_REECRITURE))
    else:
        print()
        print(include()[0])
        print(include()[1])
        print("Rien n'a ete ecrit. `--ecrire` pour poser les pages et l'include.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
