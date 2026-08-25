#!/usr/bin/env python3
"""Extrait les citations, dialogues et fins de message/en/ vers un catalogue a traduire.

    python tools/msg_extract.py --source <depot>/src/sf33rd/Source/Game/message/en \
                                --sortie traduction/fr.txt

Le catalogue est en UTF-8. On y ecrit du francais accentue, normalement ; c'est
msg_build.py qui encode et qui verifie. Relancer l'extraction sur un catalogue
existant conserve les traductions deja ecrites.
"""

import argparse
import datetime
import glob
import os
import sys

import msg_catalogue as MC

# Budget de frappe : la boite s'arrete colonne 43 a l'ecran, et le jeu ajoute un retrait de
# 3 (citations, fins) ou de 2 (dialogues). On tient une seule regle, la plus stricte.
BUDGET = 40
REGLE = "....|....1....|....2....|....3....|....4"

ENTETE = """\
# ============================================================================
# Catalogue de traduction de 3SX -- citations de victoire, dialogues, fins
# Genere le %(date)s depuis %(source)s
#
# COMMENT REMPLIR
#   Chaque bloc [..] est un message. Les lignes "=" sont l'anglais, en lecture
#   seule. Ecrivez la traduction sur les lignes ">", une par ligne d'origine.
#   Ecrivez les accents normalement -- e accent aigu, c cedille, et le reste.
#   Un bloc dont aucune ligne ">" n'est remplie reste en anglais.
#
# LA BOITE
#   %(budget)d signes par ligne au maximum. La regle ci-dessous s'aligne sur le
#   premier caractere qui suit "> " :
#   %(regle)s
#   Une lettre accentuee occupe une colonne, comme les autres. Le jeu ajoute
#   ensuite son propre retrait, ce qui amene la ligne a la colonne %(colonne)d.
#
# CE QU'IL NE FAUT PAS CHANGER
#   Les lignes [..], et le nombre de lignes ">" d'un bloc : il fixe le nombre
#   de lignes affichees. Deux au maximum, comme en anglais.
#
# Les messages vides du jeu -- les pauses dans les fins -- ne sont pas listes.
# ----------------------------------------------------------------------------
# 3SX translation catalogue -- win quotes, pre-fight dialogue, endings
# Generated on %(date)s from %(source)s
#
# HOW TO FILL IT IN
#   Each [..] block is one message. The "=" lines are the English source and are
#   read-only. Write the translation on the ">" lines, one per source line.
#   Type accents normally -- e acute, c cedilla, and the rest. The generator
#   encodes them. A block with no ">" line filled in stays in English.
#
# THE BOX
#   %(budget)d characters per line, at most. The ruler below lines up with the
#   first character after "> ":
#   %(regle)s
#   An accented letter takes one column, like any other. The game then adds its
#   own indent, which brings the line out to column %(colonne)d.
#
# WHAT NOT TO CHANGE
#   The [..] lines, and how many ">" lines a block has: that count sets how many
#   lines are drawn on screen. Two at most, as in English.
#
# The game's empty messages -- the beats between lines of an ending -- are not
# listed here.
# ============================================================================

"""


def lit_catalogue(path):
    """Les traductions deja ecrites, pour ne pas les perdre en reextrayant."""
    if not os.path.exists(path):
        return {}
    acquis = {}
    cle = None
    for ligne in open(path, encoding="utf-8"):
        ligne = ligne.rstrip("\n")
        if ligne.startswith("["):
            cle = ligne[1:ligne.index("]")]
            acquis[cle] = []
        elif ligne.startswith(">") and cle:
            acquis[cle].append(ligne[1:].lstrip(" "))
    return {k: v for k, v in acquis.items() if any(l.strip() for l in v)}


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", default="C:/3sx-up/src/sf33rd/Source/Game/message/en",
                    help="le dossier message/en du depot amont")
    ap.add_argument("--sortie", default="traduction/fr.txt", help="le catalogue a ecrire")
    args = ap.parse_args()

    if not os.path.isdir(args.source):
        raise SystemExit("dossier introuvable : %s" % args.source)

    acquis = lit_catalogue(args.sortie)
    if acquis:
        print("catalogue existant : %d blocs deja traduits, conserves" % len(acquis))

    os.makedirs(os.path.dirname(os.path.abspath(args.sortie)), exist_ok=True)
    out = open(args.sortie, "w", encoding="utf-8", newline="\n")
    out.write(ENTETE % {"date": datetime.date.today().isoformat(),
                        "source": args.source,
                        "colonne": MC.COLONNE_MAX,
                        "budget": BUDGET,
                        "regle": REGLE})

    nblocs = nlignes = 0
    for suf, libelle in MC.KINDS:
        for path in sorted(glob.glob(os.path.join(args.source, "pl??%s_en.c" % suf))):
            base = os.path.basename(path)
            num = int(base[2:4])
            data = MC.lit_fichier(path)
            pleins = [(nom, data["messages"][nom]) for nom in data["ordre"]
                      if any(l.strip() for l in data["messages"].get(nom, []))]
            if not pleins:
                continue
            out.write("\n## %s -- %s, %s (%d messages)\n\n"
                      % (base[:-5], MC.NOMS[num], libelle, len(pleins)))
            for nom, lignes in pleins:
                cle = "%s/%s" % (base[:-5], nom)
                out.write("[%s]\n" % cle)
                for l in lignes:
                    out.write("= %s\n" % l.strip())
                deja = acquis.get(cle)
                for i in range(len(lignes)):
                    out.write("> %s\n" % (deja[i] if deja and i < len(deja) else ""))
                out.write("\n")
                nblocs += 1
                nlignes += len(lignes)
    out.close()

    print("ecrit %s" % args.sortie)
    print("  %d blocs, %d lignes a traduire" % (nblocs, nlignes))
    reste = nblocs - len(acquis)
    print("  %d blocs deja remplis, %d restants" % (len(acquis), reste))
    return 0


if __name__ == "__main__":
    sys.exit(main())
