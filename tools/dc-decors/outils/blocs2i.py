# -*- coding: utf-8 -*-
"""LES OBJETS D'UN DECOR, LUS DEPUIS LE CODE DE SES CHARGEURS — sans table ecrite a la main.

CE QUE CET OUTIL REMPLACE
-------------------------
`animer2i.TABLES` s'est construit au fil des trouvailles : une adresse de bloc reperee ici,
un `pas` devine la, des offsets de champ poses par ressemblance avec le bloc voisin. Ca
marche jusqu'au jour ou un chargeur range ses champs autrement -- et alors on pose un objet
au mauvais endroit sans qu'aucun garde-fou ne le dise. Le panneau vertical de Yun a passe
des jours devant le fumeur pour cette raison : son bloc ecrit `+84/+86`, et on avait pris
ces deux mots pour la position par analogie avec les blocs voisins.

ICI, RIEN N'EST DEVINE. Pour chaque decor :

    routine d'etage  ->  `jsr` vers ses chargeurs (`chargeurs2i.appels`)
    chaque chargeur  ->  `spawners2i.analyser` DECODE son code et rend
                            * le pas de l'enregistrement,
                            * la carte  rang du champ -> offset dans l'objet,
                            * ses tables de nombres et de pointeurs
    `spawners2i.blocs(a, arg)`  ->  l'adresse et le compte pour CHAQUE z

Le rang d'un champ donne sa place dans l'enregistrement : les chargeurs lisent au `mov.w
@rM+`, donc le champ de rang k est a l'octet 2k. Le `pas` peut etre plus grand que la somme
des champs -- il reste alors des mots que le chargeur ne lit pas, et on ne les invente pas.

LA REGLE QUI EVITE LA FAUTE DU PANNEAU : **un chargeur qui n'ecrit pas `+102` ne dit pas ou
va son objet.** On le signale au lieu de prendre un autre champ pour la position.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import annuaire2i as AN
import chargeurs2i as CH
import spawners2i as SP

# Les offsets d'objet qui nous interessent, et ce qu'ils sont. Voir `structs.h` du port.
X, Y, PALETTE, PLAN, DRAPEAUX = 102, 106, 88, 558, 554
SCRIPT, SC_REPOS, SC_ACTION = 456, 150, 152

PROFONDEUR = 3


def arbre(depart, fin, vus=None, profondeur=0):
    """[(fonction, arg)] atteints depuis ce bloc de code, sans repetition."""
    vus = set() if vus is None else vus
    out = []

    for _site, cible, arg in CH.appels(depart, fin):
        if cible in vus or profondeur >= PROFONDEUR:
            continue

        vus.add(cible)
        out.append((cible, arg))
        f = CH.fin_de_fonction(cible)

        if f:
            out.extend(arbre(cible, f, vus, profondeur + 1))

    return out


def chargeurs_du_decor(decor):
    """[(fonction, arg)] que la routine d'etage de ce decor atteint."""
    b2d = CH.bande_vers_decor()
    out = []

    for deb, fin, bande in CH.scripts_detage():
        if b2d.get(bande) != decor:
            continue

        out.extend(arbre(deb, fin))

    return out


def objets_du_decor(decor, sur_erreur=None):
    """Tous les objets que le CODE pose pour ce decor.

    Rend [{...}] avec `script`, `x`, `y`, `palette`, `plan`, `drapeaux`, `variante`
    (masque des z), `chargeur`, `bloc`, `rang`. Les champs absents valent None -- ils ne
    sont jamais remplaces par un autre champ.
    """
    trouves = {}

    for f, arg in chargeurs_du_decor(decor):
        try:
            a = SP.analyser(f)
        except Exception as e:
            if sur_erreur:
                sur_erreur("%08X illisible : %s" % (f, e))
            continue

        if a is None:
            continue

        ou = {off: rang for rang, off in a["champs"]}

        if X not in ou:
            # Le chargeur n'ecrit pas la position : son bloc ne dit pas ou va l'objet.
            if sur_erreur:
                sur_erreur("%08X sans +102 : %d champs, ignore" % (f, len(a["champs"])))
            continue

        try:
            lots = SP.blocs(a, arg if arg is not None else 0)
        except Exception:
            lots = []

        for z, nb, p in lots:
            for i in range(nb or 0):
                base = p + i * a["pas"]
                lire = lambda off: (SP.u16(base + ou[off] * 2) if off in ou else None)
                sc = lire(SCRIPT)

                if sc is None:
                    # La paire repos/action : on prend l'ACTION, plus riche que le repos.
                    sc = lire(SC_ACTION) if SC_ACTION in ou else lire(SC_REPOS)

                if sc is None:
                    continue

                # UN SCRIPT QUI N'EXISTE PAS DANS LA TABLE DU DECOR N'EST PAS A LUI.
                #
                # Deux bandes peuvent atteindre le MEME chargeur avec le MEME argument --
                # les bandes 12 et 13 appellent toutes deux `8C028792` arg 7 -- et le bloc
                # se retrouve attribue aux deux decors. Un seul peut l'avoir, et c'est la
                # donnee qui tranche : le script 9 a huit images chez le decor 12 et
                # n'existe pas chez le 11, qui n'en compte que six.
                if not 0 <= sc < AN.table_scripts(decor)[1]:
                    if sur_erreur:
                        sur_erreur("%08X rang %d : script %d hors de la table du decor %d"
                                   % (p, i, sc, decor))
                    continue

                cle = (p, i)
                o = trouves.get(cle)

                if o is None:
                    o = dict(script=sc, x=lire(X), y=lire(Y), palette=lire(PALETTE),
                             plan=lire(PLAN), drapeaux=lire(DRAPEAUX),
                             chargeur=f, bloc=p, rang=i, variante=0,
                             repos=lire(SC_REPOS), action=lire(SC_ACTION))
                    trouves[cle] = o

                o["variante"] |= 1 << z

    # L'ORDRE EST CELUI DE LA CREATION, ET IL COMPTE. La profondeur, elle, est en `+556`
    # (`my_priority`, qui vaut le numero de palette) -- j'avais ecrit ici le contraire en
    # la cherchant a `+76`, offset calcule dans une structure du port sans rapport avec
    # l'objet de 2I. A PRIORITE EGALE, c'est l'ordre de creation qui decide qui passe
    # devant : l'ordre des `jsr` dans la routine d'etage, puis celui des enregistrements.
    # Trier par adresse de bloc le detruirait.
    return list(trouves.values())


def main():
    decor = int(sys.argv[1], 0) if len(sys.argv) > 1 else 3
    soucis = []
    objs = objets_du_decor(decor, soucis.append)

    print("DECOR %d : ce que le CODE de ses chargeurs pose" % decor)
    print()
    print("%-9s %-9s %-4s %-6s %-5s %-5s %-6s %-6s %-5s %s"
          % ("chargeur", "bloc", "n", "script", "x", "y", "palette", "plan", "drap", "z"))
    print("-" * 88)

    for o in objs:
        z = "".join(str(k) for k in range(4) if o["variante"] & (1 << k))
        paire = ("  (repos %s / action %s)" % (o["repos"], o["action"])
                 if o["repos"] is not None and o["repos"] != o["action"] else "")
        print("%08X  %08X  %-4d %-6s %-5s %-5s %-6s %-6s %-5s %s%s"
              % (o["chargeur"], o["bloc"], o["rang"], o["script"], o["x"], o["y"],
                 o["palette"], o["plan"], o["drapeaux"], z, paire))

    print()
    print("%d objets." % len(objs))

    if soucis:
        print()
        print("CHARGEURS ECARTES, et pourquoi :")
        for s in soucis:
            print("   " + s)


if __name__ == "__main__":
    main()
