#!/usr/bin/env python3
"""Genere message/<lang>/ a partir d'un catalogue traduit, et verifie les contraintes.

    python tools/msg_build.py --catalogue traduction/fr.txt --lang fr \
                              --source <depot>/src/sf33rd/Source/Game/message/en \
                              --sortie <depot>/src/sf33rd/Source/Game/message/fr

Le catalogue est en francais accentue ordinaire ; l'encodage en jetons de deux octets se
fait ici. Trois controles, du plus grave au moins grave :

  ERREUR   un caractere que le jeu ne sait pas dessiner
  ERREUR   un message de plus de 108 glyphes -- au-dela, le jeu se fige
  ERREUR   un aller-retour encode/decode qui ne retombe pas sur le texte d'origine
  ALERTE   une ligne qui depasse la colonne 43, la plus a droite que l'anglais atteint
  ALERTE   un bloc laisse vide, qui restera en anglais

Rien n'est ecrit tant qu'il reste une ERREUR, sauf avec --quand-meme.

Le CMakeLists de l'amont fait `file(GLOB_RECURSE GAME_SRC ... src/*.c)` : les fichiers
generes sont pris par la compilation sans rien declarer.
"""

import argparse
import datetime
import glob
import os
import re
import sys

import msg_catalogue as MC


def lit_catalogue(path):
    blocs = {}
    cle = None
    for no, ligne in enumerate(open(path, encoding="utf-8"), 1):
        ligne = ligne.rstrip("\n")
        if ligne.startswith("["):
            if "]" not in ligne:
                raise SystemExit("%s:%d : crochet non ferme" % (path, no))
            cle = ligne[1:ligne.index("]")]
            blocs[cle] = {"en": [], "fr": [], "ligne": no}
        elif ligne.startswith("=") and cle:
            blocs[cle]["en"].append(ligne[1:].lstrip(" "))
        elif ligne.startswith(">") and cle:
            blocs[cle]["fr"].append(ligne[1:].lstrip(" ").rstrip())
    return blocs


def verifie(cle, bloc, indent, erreurs, alertes):
    """-> [lignes encodees] ou None si le bloc est a laisser en anglais.

    `indent` est le retrait du message d'origine, 3 pour les citations et les fins, 2 pour
    les dialogues. Il compte dans la position a l'ecran : une ligne de 41 signes retraitee
    de 3 finit colonne 44, pas 41.
    """
    fr = bloc["fr"]
    if not any(l.strip() for l in fr):
        alertes.append("%s : pas traduit, reste en anglais" % cle)
        return None
    if len(fr) != len(bloc["en"]):
        erreurs.append("%s : %d lignes traduites pour %d lignes d'origine"
                       % (cle, len(fr), len(bloc["en"])))
        return None

    encodees = []
    total = 0
    for i, texte in enumerate(fr):
        norm, corrections = MC.normalise(texte)
        if corrections:
            vus = sorted(set("%s -> %s" % c for c in corrections))
            alertes.append("%s ligne %d : typographie corrigee (%s)" % (cle, i + 1, ", ".join(vus)))
        enc, refuses = MC.encode(norm)
        if refuses:
            erreurs.append("%s ligne %d : caracteres que le jeu ne sait pas dessiner : %s"
                           % (cle, i + 1, " ".join(sorted(set(refuses)))))
            continue
        if MC.decode(enc) != norm:
            erreurs.append("%s ligne %d : l'encodage ne se relit pas a l'identique. "
                           "Un caractere sert de tete d'accent (%s) juste avant une lettre."
                           % (cle, i + 1, " ".join(sorted(MC.LEADS))))
            continue
        col = indent + MC.derniere_colonne(enc)
        if col > MC.COLONNE_MAX:
            alertes.append("%s ligne %d : va jusqu'a la colonne %d (retrait %d compris), "
                           "l'anglais s'arrete a %d"
                           % (cle, i + 1, col, indent, MC.COLONNE_MAX))
        if col > MC.LARGEUR_BOITE:
            erreurs.append("%s ligne %d : colonne %d, hors de la boite de %d"
                           % (cle, i + 1, col, MC.LARGEUR_BOITE))
        total += MC.compte_glyphes(enc)
        encodees.append(enc)

    if total > MC.CAP_GLYPHES:
        erreurs.append("%s : %d glyphes pour un plafond de %d -- au-dela, le jeu se fige"
                       % (cle, total, MC.CAP_GLYPHES))
    return encodees if len(encodees) == len(fr) else None


TITRES = {"win": "Win Quotes", "tlk": "Pre-Fight Dialogue", "end": "Ending Text"}


def ecrit_fichier(chemin_c, chemin_h, base, lang, data, traduits):
    """Reecrit un pl<NN><kind> avec les lignes traduites, en gardant tout le reste."""
    num = base[2:4]
    kind = base[4:7]
    suffixe = "_" + lang
    tbl_src = data["table"]                        # pl02win_usa_tbl
    tbl_dst = tbl_src.replace("_usa_", "_%s_" % lang)
    garde = (base + suffixe).upper().replace("-", "_") + "_H"

    lignes_c = []
    lignes_c.append("/**")
    lignes_c.append(" * @file %s%s.c" % (base, suffixe))
    lignes_c.append(" * %s %s (%s)" % (MC.NOMS[int(num)], TITRES[kind], lang))
    lignes_c.append(" *")
    lignes_c.append(" * Genere par tools/msg_build.py -- ne pas editer a la main.")
    lignes_c.append(" * Les paires comme `e ou *e sont des jetons de src_han_alpha2 (effb6.c).")
    lignes_c.append(" */")
    lignes_c.append("")
    lignes_c.append('#include "sf33rd/Source/Game/message/%s/%s%s.h"' % (lang, base, suffixe))
    lignes_c.append('#include "common.h"')
    lignes_c.append("")

    compte = []
    for nom in data["ordre"]:
        origine = data["messages"][nom]
        cle = "%s/%s" % (base, nom)
        lignes = traduits.get(cle)
        if lignes is None:
            lignes = [l for l in origine]           # non traduit : on garde l'anglais tel quel
        else:
            ind = MC.indent_de(origine)
            lignes = [(" " * ind + l).ljust(MC.LARGEUR_BOITE)[:MC.LARGEUR_BOITE] for l in lignes]
        compte.append(len(lignes))
        if len(lignes) == 1:
            lignes_c.append('static s8* %s[1] = { "%s" };' % (nom, MC.echappe_c(lignes[0])))
        else:
            lignes_c.append("static s8* %s[%d] = {" % (nom, len(lignes)))
            for l in lignes:
                lignes_c.append('    "%s",' % MC.echappe_c(l))
            lignes_c.append("};")
    lignes_c.append("")

    lignes_c.append("static s8** %s[%d] = {" % (data["adr"], len(data["ordre"])))
    for i in range(0, len(data["ordre"]), 6):
        lignes_c.append("    " + " ".join("%s," % n for n in data["ordre"][i:i + 6]))
    lignes_c.append("};")
    lignes_c.append("")
    lignes_c.append("static s8 %s[%d] = { %s };" % (data["ctr"], len(compte),
                                                    ", ".join(str(c) for c in compte)))
    lignes_c.append("")
    lignes_c.append("MessageTable %s = { %s, %s };" % (tbl_dst, data["adr"], data["ctr"]))
    lignes_c.append("")

    open(chemin_c, "w", encoding="latin-1", newline="\n").write("\n".join(lignes_c))

    lignes_h = ["#ifndef %s" % garde, "#define %s" % garde, "",
                '#include "structs.h"', '#include "types.h"', "",
                "extern MessageTable %s;" % tbl_dst, "", "#endif", ""]
    open(chemin_h, "w", encoding="latin-1", newline="\n").write("\n".join(lignes_h))
    return tbl_dst


def ecrit_msgtable(sortie, lang, source, tables):
    """msgtable_<lang>.c : les trois tableaux, avec le meme aiguillage que l'amont."""
    src = open(os.path.join(source, "msgtable_en.c"), encoding="latin-1").read()
    lignes_c = ["/**",
                " * @file msgtable_%s.c" % lang,
                " * Main Message Table Jumptables (%s)" % lang,
                " *",
                " * Genere par tools/msg_build.py -- ne pas editer a la main.",
                " */",
                "",
                '#include "sf33rd/Source/Game/message/%s/msgtable_%s.h"' % (lang, lang),
                '#include "common.h"']
    entetes = sorted(set(t[0] for t in tables))
    for base in entetes:
        lignes_c.append('#include "sf33rd/Source/Game/message/%s/%s_%s.h"' % (lang, base, lang))
    lignes_c.append("")

    noms = {"win": "pl_mes_tbl", "tlk": "pl_tlk_tbl", "end": "pl_end_tbl"}
    for kind, nom in noms.items():
        m = re.search(r'MessageTable\* %s\[20\] = \{(.*?)\};' % nom, src, re.S)
        if not m:
            raise SystemExit("msgtable_en.c : %s introuvable" % nom)
        refs = re.findall(r'&(\w+)', m.group(1))
        # L'amont fait pointer Akuma et Q sur le tlk d'un voisin, faute de fichier propre.
        refs = [r.replace("_usa_", "_%s_" % lang) for r in refs]
        lignes_c.append("MessageTable* %s_%s[20] = {" % (nom, lang))
        for i in range(0, 20, 4):
            lignes_c.append("    " + " ".join("&%s," % r for r in refs[i:i + 4]))
        lignes_c.append("};")
        lignes_c.append("")

    open(os.path.join(sortie, "msgtable_%s.c" % lang), "w",
         encoding="latin-1", newline="\n").write("\n".join(lignes_c))

    garde = "MSGTABLE_%s_H" % lang.upper()
    lignes_h = ["#ifndef %s" % garde, "#define %s" % garde, "",
                '#include "structs.h"', ""]
    for nom in noms.values():
        lignes_h.append("extern MessageTable* %s_%s[20];" % (nom, lang))
    lignes_h += ["", "#endif", ""]
    open(os.path.join(sortie, "msgtable_%s.h" % lang), "w",
         encoding="latin-1", newline="\n").write("\n".join(lignes_h))


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--catalogue", default="traduction/fr.txt")
    ap.add_argument("--lang", default="fr")
    ap.add_argument("--source", default="C:/3sx-up/src/sf33rd/Source/Game/message/en")
    ap.add_argument("--sortie", default=None, help="defaut : message/<lang> a cote de --source")
    ap.add_argument("--quand-meme", action="store_true", help="ecrire malgre les erreurs")
    args = ap.parse_args()

    sortie = args.sortie or os.path.join(os.path.dirname(args.source.rstrip("/\\")), args.lang)
    blocs = lit_catalogue(args.catalogue)
    print("catalogue : %d blocs" % len(blocs))

    # Le retrait de chaque message, relu dans l'original : il compte dans la largeur.
    sources = {}
    indents = {}
    for suf, _ in MC.KINDS:
        for path in sorted(glob.glob(os.path.join(args.source, "pl??%s_en.c" % suf))):
            base = os.path.basename(path)[:-5]
            data = MC.lit_fichier(path)
            sources[base] = data
            for nom, lignes in data["messages"].items():
                indents["%s/%s" % (base, nom)] = MC.indent_de(lignes)

    erreurs, alertes = [], []
    traduits = {}
    for cle, bloc in blocs.items():
        if cle not in indents:
            erreurs.append("%s : cle inconnue dans message/en/" % cle)
            continue
        enc = verifie(cle, bloc, indents[cle], erreurs, alertes)
        if enc is not None:
            traduits[cle] = enc

    for a in alertes:
        if "pas traduit" not in a:
            print("  ALERTE %s" % a)
    non_traduits = sum(1 for a in alertes if "pas traduit" in a)
    if non_traduits:
        print("  ALERTE %d blocs non traduits, laisses en anglais" % non_traduits)
    for e in erreurs:
        print("  ERREUR %s" % e)

    print("%d blocs traduits, %d erreurs, %d alertes"
          % (len(traduits), len(erreurs), len(alertes)))

    if erreurs and not args.quand_meme:
        print("rien n'a ete ecrit. Corrigez le catalogue, ou passez --quand-meme.")
        return 1

    os.makedirs(sortie, exist_ok=True)
    tables = []
    for base in sorted(sources):
        tbl = ecrit_fichier(os.path.join(sortie, "%s_%s.c" % (base, args.lang)),
                            os.path.join(sortie, "%s_%s.h" % (base, args.lang)),
                            base, args.lang, sources[base], traduits)
        tables.append((base, tbl))
    ecrit_msgtable(sortie, args.lang, args.source, tables)

    print("ecrit %d fichiers dans %s" % (len(tables) * 2 + 2, sortie))
    print("Le CMakeLists de l'amont les prend tout seul (GLOB_RECURSE sur src/*.c).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
