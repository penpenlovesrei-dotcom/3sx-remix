# -*- coding: utf-8 -*-
"""TOUS LES CHARGEURS ET SPAWNERS DE TOUS LES DECORS — et lesquels la chaine ignore.

POURQUOI CET OUTIL EXISTE
-------------------------
Le 04/09/2026, Frederic a arrete le chantier apres trois corrections ratees d'affilee. La
cause de fond n'etait pas l'une ou l'autre de ces corrections : c'est que `animer2i.TABLES`
s'est construit **au fil des trouvailles**, bloc par bloc, et que personne ne savait ce
qu'il restait dehors. On corrigeait donc des objets au jugé sans savoir si le bon
enregistrement avait seulement ete lu.

Cet outil repond a la seule question qui compte avant toute correction :

    pour chaque decor, QUELS chargeurs sa routine d'etage atteint, QUEL bloc chacun porte,
    QUEL format il lit -- et LESQUELS la chaine n'exploite pas.

Il ne devine rien : la marche des appels vient de `chargeurs2i` (qui suit `jsr`/`jmp` et la
constante du delay slot), et la carte des champs de `spawners2i.analyser`, qui interprete
le code du chargeur.

LA COLONNE QUI COMPTE EST LA DERNIERE. `+102/+106` est la position d'un WORK ; un chargeur
qui ne les ecrit PAS ne dit rien de l'endroit ou va son objet, meme s'il porte des champs
qui y ressemblent. C'est exactement ce qui a fait poser le panneau vertical de Yun au
mauvais endroit pendant des jours : son bloc ecrit `+84/+86`, et on l'avait pris pour la
position par analogie avec ses voisins.

    python inventaire_spawners.py            le tableau complet
    python inventaire_spawners.py --manque   seulement ce que la chaine ignore
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import animer2i as AM
import chargeurs2i as CH
import spawners2i as SP

# Les deux offsets qui font qu'un bloc sait ou va son objet.
POSITION = (102, 106)
PROFONDEUR = 3          # combien de niveaux d'appels on suit


def arbre(depart, fin, vus, profondeur=0):
    """[(fonction, arg, profondeur)] atteints depuis ce bloc de code, sans repetition."""
    out = []

    for _site, cible, arg in CH.appels(depart, fin):
        if cible in vus or profondeur >= PROFONDEUR:
            continue

        vus.add(cible)
        out.append((cible, arg, profondeur))
        f = CH.fin_de_fonction(cible)

        if f:
            out.extend(arbre(cible, f, vus, profondeur + 1))

    return out


def exploites():
    """{(decor, adresse de bloc)} et {(decor, adresse de spawner)} que la chaine emploie."""
    blocs, spawns = set(), set()

    for bg, entrees in AM.TABLES.items():
        for e in entrees:
            d = e.get("decor")

            if "adresse" in e:
                blocs.add((d, e["adresse"]))

            for a in e.get("adresses", []):
                blocs.add((d, a))

            for im in e.get("immediats", []):
                if "spawner" in im:
                    spawns.add((d, im["spawner"]))

    return blocs, spawns


def main():
    seulement_manque = "--manque" in sys.argv
    b2d = CH.bande_vers_decor()
    blocs_pris, spawns_pris = exploites()
    total = manques = 0

    print("TOUS LES CHARGEURS ATTEINTS PAR UNE ROUTINE D'ETAGE")
    print()
    print("%-6s %-9s %-4s %-6s %-7s %-16s %-7s %s"
          % ("bande", "chargeur", "arg", "pas", "champs", "bloc", "tours", "position ?"))
    print("-" * 100)

    for deb, fin, bande in CH.scripts_detage():
        decor = b2d.get(bande)

        if decor is None:
            continue

        lignes = []

        for f, arg, prof in arbre(deb, fin, set()):
            try:
                a = SP.analyser(f)
            except Exception:
                a = None

            if a is None:
                continue

            offs = {o for _r, o in a["champs"]}
            pos = "OUI" if POSITION[0] in offs else "non  <-- ne dit PAS ou va l'objet"

            # ON RESOUT LE BLOC PAR SON ARGUMENT. La plupart des chargeurs ne portent pas
            # leur bloc en dur : ils l'indexent dans deux tables (nombres, pointeurs).
            # Comparer l'expression symbolique aux adresses de `TABLES` ne pouvait rien
            # apparier -- tout serait sorti « ignore », ce qui aurait ete faux.
            try:
                trouves = SP.blocs(a, arg if arg is not None else 0)
            except Exception:
                trouves = []

            adr = [p for _z, _n, p in trouves]
            connu = ((decor, f) in spawns_pris) or any((decor, p) in blocs_pris
                                                       for p in adr)
            bloc = ("%08X" % adr[0]) if adr else "?"

            if len(adr) > 1:
                bloc += "+%d" % (len(adr) - 1)

            if seulement_manque and connu:
                continue

            total += 1

            if not connu:
                manques += 1

            lignes.append("%-6s %-9s %-4s %-6s %-7s %-13s %-7s %-32s %s"
                          % (bande, "%08X" % f, arg, a["pas"], len(a["champs"]), bloc,
                             (trouves[0][1] if trouves else "?"), pos,
                             "" if connu else "  *** IGNORE ***"))

        for l in lignes:
            print(l)

    print()
    print("%d chargeurs lisibles, dont %d que la chaine n'exploite pas." % (total, manques))
    print()
    print("« position ? non » veut dire que le chargeur n'ecrit jamais +102/+106 :")
    print("son bloc ne dit pas ou va l'objet, quels que soient les champs qu'il porte.")


if __name__ == "__main__":
    main()
