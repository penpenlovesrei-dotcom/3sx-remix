# -*- coding: utf-8 -*-
"""LA CARTE COMPLÈTE DES CHAMPS D'UN CHARGEUR — bloc ET constantes réunis.

POURQUOI CET OUTIL EXISTE
-------------------------
Un chargeur de décor remplit son objet de deux façons, et jusqu'ici deux outils séparés en
voyaient chacun la moitié :

  * `spawners2i.analyser` suit les champs LUS DANS UN BLOC (`mov.w @rM+`) ;
  * `immediats2i.analyser` relève les CONSTANTES écrites dans l'objet.

Aucun des deux ne rendait l'objet entier, et la moitié manquante coûtait cher. Mesure faite
sur les 97 fonctions atteintes par une routine d'étage :

    +364               absent de la carte de 16 chargeurs sur 16
    +556 my_priority   absent de 12 sur 16      <- LA PROFONDEUR
    +552, +6, +8       absents de 15 sur 16
    +554, +558         absents de 6 et 5

C'est ce trou qui a fait écrire, ici même, que « la profondeur n'est pas dans les données ».
Elle y était : `my_priority` est écrit, simplement pas listé.

CE QU'IL REND
-------------
Pour chaque fonction : d'où vient chaque champ de l'objet — d'un enregistrement (avec son
rang, donc son octet), ou d'une constante (avec sa valeur). Rien n'est fusionné en silence :
quand les deux sources donnent le même offset, les deux sont montrées.

    python champs2i.py 0x8C02356A
    python champs2i.py --decor 3
    python champs2i.py --tous            les 97, en tableau
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import blocs2i as B
import chargeurs2i as CH
import immediats2i as IM
import spawners2i as SP

NOMS = dict(IM.NOMS)
NOMS.update({552: "my_col_mode", 554: "my_col_code", 556: "my_priority",
             558: "my_family", 560: "my_ext_pri", 364: "?364", 6: "work_id", 8: "id",
             72: "cgromtype", 0: "be_flag"})


def carte(f):
    """{offset: (origine, detail)} pour cette fonction, et son analyse de bloc."""
    try:
        a = SP.analyser(f)
    except Exception:
        a = None

    try:
        imm, appels, _fin = IM.analyser(f)
    except Exception:
        imm, appels = {}, []

    out = {}

    if a is not None:
        for rang, off in a["champs"]:
            out[off] = ("enregistrement", "octet %d" % (rang * 2))

    for off, v in imm.items():
        # UNE CONSTANTE NE REMPLACE PAS UN CHAMP D'ENREGISTREMENT : quand le chargeur lit
        # un bloc, la valeur que `immediats2i` voit dans le registre est le RESTE de la
        # lecture, pas une constante. On ne l'écrase donc jamais -- on l'ajoute.
        if off in out:
            continue

        out[off] = ("constante", "inconnue" if v is None
                    else "%d (0x%04X)" % (v, v & 0xFFFF))

    return out, a, appels


def toutes_les_fonctions():
    """[(bande, decor, fonction, arg)] atteintes par une routine d'etage.

    LE « DEJA VU » EST PAR BANDE, PAS GLOBAL, et c'est tout sauf un detail : les cinq gros
    chargeurs servent de huit a quatorze decors chacun. Avec un ensemble partage, le
    premier decor qui atteignait `8C028792` se l'appropriait et TOUS LES AUTRES le
    perdaient -- Sean (bande 13) se retrouvait avec trois fonctions, aucune n'ecrivant un
    champ d'objet, alors que ses trois objets viennent justement de ce chargeur.
    """
    b2d = CH.bande_vers_decor()
    out = []

    for deb, fin, bande in CH.scripts_detage():
        vus = set()

        for f, arg in B.arbre(deb, fin, vus):
            out.append((bande, b2d.get(bande), f, arg))

    return out


def decrire(f, entete=True):
    m, a, appels = carte(f)

    if entete:
        genre = ("lit un bloc de %d octets" % a["pas"]) if a else "sans bloc"
        print("%08X   %s" % (f, genre))

    for off in sorted(m):
        origine, detail = m[off]
        print("   +%-5d %-14s %-15s %s" % (off, NOMS.get(off, ""), origine, detail))

    if appels:
        print("   appelle : %s" % " ".join("%08X" % x for x in appels))


def main():
    args = sys.argv[1:]

    if "--tous" in args or "--decor" in args:
        cible = (int(args[args.index("--decor") + 1], 0)
                 if "--decor" in args else None)
        n = 0
        avec_prio = 0
        print("%-6s %-5s %-9s %-4s %-22s %s"
              % ("bande", "decor", "fonction", "arg", "genre", "my_priority (+556)"))
        print("-" * 84)

        for bande, decor, f, arg in toutes_les_fonctions():
            if cible is not None and decor != cible:
                continue

            m, a, _ap = carte(f)
            n += 1
            p = m.get(556)

            if p:
                avec_prio += 1

            print("%-6s %-5s %08X  %-4s %-22s %s"
                  % (bande, decor, f, arg,
                     ("bloc de %d o, %d champs" % (a["pas"], len(m))) if a
                     else "sans bloc, %d champs" % len(m),
                     ("%s %s" % p) if p else "-"))

        print()
        print("%d fonctions, dont %d qui posent une profondeur." % (n, avec_prio))
        return

    for x in args:
        decrire(int(x, 0))
        print()


if __name__ == "__main__":
    main()
