#!/usr/bin/env python3
"""Branche une troisieme langue dans les menus et dans le choix des tables de messages.

Complement de msg_patch_effb6.py, qui lui rend les accents affichables. Ici on ajoute la
langue elle-meme :

  structs.h   LANG_FRENCH dans l'enumeration, et Language_Toggle devient un cycle
  eff64.c     la ligne d'option affiche "FR" en plus de "EN" et "JP"
  effb6.c     mess_tables choisit les tables francaises selon mpp_w.language
  main.c      Get_Default_Language reconnait la locale "fr"

Les libelles de menu sont dessines par un jeu de 96 glyphes ASCII : "FR" passe, un nom
accentue ne passerait pas.

    python tools/msg_patch_langue.py --ecrire-dans C:/3sx-fr
    python tools/msg_patch_langue.py --source C:/3sx-up --sortie traduction/langue-fr.patch
"""

import argparse
import difflib
import os
import sys

MODIFS = [
    # fichier, avant, apres
    ("src/structs.h",
     """typedef enum Language : u8 {
    LANG_ENGLISH,
    LANG_JAPANESE,
} Language;

#define Language_Toggle(lang) ((lang) == LANG_ENGLISH ? LANG_JAPANESE : LANG_ENGLISH)""",
     """typedef enum Language : u8 {
    LANG_ENGLISH,
    LANG_JAPANESE,
    LANG_FRENCH,
    LANG_COUNT,
} Language;

/// Cycle plutot que bascule : les deux sens du menu appellent la meme macro, comme avant.
#define Language_Toggle(lang) ((Language)(((lang) + 1) % LANG_COUNT))"""),

    ("src/sf33rd/Source/Game/effect/eff64.c",
     """    { "EN", "JP", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL },""",
     """    { "EN", "JP", "FR", NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL, NULL },"""),

    ("src/sf33rd/Source/Game/effect/effb6.c",
     """MessageTable** mess_tables[6] = { pl_mes_tbl, pl_tlk_tbl, pl_end_tbl, msgSysDirTbl, msgExtraTbl, msgMenuTbl };""",
     """MessageTable** mess_tables[6] = { pl_mes_tbl, pl_tlk_tbl, pl_end_tbl, msgSysDirTbl, msgExtraTbl, msgMenuTbl };

/// Seuls les trois premiers jeux sont traduits : citations, dialogues d'avant-combat et
/// fins. Les tables systeme, extra et menu restent celles de l'anglais.
MessageTable** mess_tables_fr[6] = { pl_mes_tbl_fr, pl_tlk_tbl_fr,  pl_end_tbl_fr,
                                     msgSysDirTbl,  msgExtraTbl,    msgMenuTbl };"""),

    ("src/sf33rd/Source/Game/effect/effb6.c",
     """    msghead = (u8**)mess_tables[kind][pl]->msgAdr[msg];
    msgline = mess_tables[kind][pl]->msgNum[msg];""",
     """    MessageTable*** tables = (mpp_w.language == LANG_FRENCH) ? mess_tables_fr : mess_tables;

    msghead = (u8**)tables[kind][pl]->msgAdr[msg];
    msgline = tables[kind][pl]->msgNum[msg];"""),

    ("src/sf33rd/Source/Game/effect/effb6.c",
     """#include "sf33rd/Source/Game/message/en/msgtable_en.h\"""",
     """#include "main.h"
#include "sf33rd/Source/Game/message/en/msgtable_en.h"
#include "sf33rd/Source/Game/message/fr/msgtable_fr.h\""""),

    ("src/main.c",
     """        } else if (SDL_strcmp(locales[i]->language, "en") == 0) {""",
     """        } else if (SDL_strcmp(locales[i]->language, "fr") == 0) {
            language = LANG_FRENCH;
            break;
        } else if (SDL_strcmp(locales[i]->language, "en") == 0) {"""),
]


def applique(racine, ecrire):
    diffs = []
    par_fichier = {}
    for rel, avant, apres in MODIFS:
        par_fichier.setdefault(rel, []).append((avant, apres))

    for rel, paires in par_fichier.items():
        chemin = os.path.join(racine, rel)
        if not os.path.exists(chemin):
            raise SystemExit("introuvable : %s" % chemin)
        brut = open(chemin, encoding="latin-1", newline="").read()
        crlf = "\r\n" in brut
        texte = brut.replace("\r\n", "\n")
        origine = texte
        for avant, apres in paires:
            if avant not in texte:
                if apres.split("\n")[0].strip() in texte:
                    print("  deja applique : %s" % rel)
                    continue
                raise SystemExit("%s : le passage attendu est absent. L'amont a bouge :\n%s"
                                 % (rel, avant.split("\n")[0]))
            texte = texte.replace(avant, apres, 1)
        if texte == origine:
            continue
        if ecrire:
            open(chemin, "w", encoding="latin-1", newline="").write(
                texte.replace("\n", "\r\n") if crlf else texte)
            print("  reecrit %s" % rel)
        diffs.extend(difflib.unified_diff(origine.splitlines(True), texte.splitlines(True),
                                          "a/" + rel, "b/" + rel))
    return diffs


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", default="C:/3sx-up", help="clone lu, pour produire un patch")
    ap.add_argument("--sortie", default="traduction/langue-fr.patch")
    ap.add_argument("--ecrire-dans", help="au lieu d'un patch, modifier ce clone")
    args = ap.parse_args()

    if args.ecrire_dans:
        applique(args.ecrire_dans, True)
        print("La langue est branchee. Le CMakeLists prend message/fr tout seul.")
        return 0

    diffs = applique(args.source, False)
    os.makedirs(os.path.dirname(os.path.abspath(args.sortie)), exist_ok=True)
    open(args.sortie, "w", encoding="latin-1", newline="\n").writelines(diffs)
    print("ecrit %s" % args.sortie)
    return 0


if __name__ == "__main__":
    sys.exit(main())
