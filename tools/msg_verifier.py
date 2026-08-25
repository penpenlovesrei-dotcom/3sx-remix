#!/usr/bin/env python3
"""Rejoue msgConvertObjNum sur les textes, avant et apres le changement de effb6.c.

Deux questions, une reponse chacune :

  1. Le changement laisse-t-il l'anglais intact ? On fait lire les 61 fichiers anglais par
     l'ancien lecteur puis par le nouveau, et on compare les suites de numeros d'objet.
     La moindre difference est un texte qui ne s'afficherait plus pareil.

  2. Le francais genere se relit-il ? On fait lire les fichiers de message/<lang>/ par le
     nouveau lecteur, et on remonte des numeros d'objet vers les caracteres.

    python tools/msg_verifier.py --amont C:/3sx-up --genere traduction/message_fr
"""

import argparse
import glob
import os
import re
import sys

import msg_catalogue as MC

REL_EFFB6 = "src/sf33rd/Source/Game/effect/effb6.c"
BASE_HAN = 0x7F30
VIDE = bytes([0x5E, 0x5F])


def lit_tables(chemin):
    """Les trois tables de han_adrs, telles qu'elles sont dans le fichier."""
    src = open(chemin, encoding="latin-1").read().replace("\r\n", "\n")
    tables = []
    for nom in ("src_han_kata", "src_han_alpha", "src_han_alpha2"):
        i = src.index("const s8* %s[128] = {" % nom)
        j = src.index("};", i)
        items = re.findall(r'"((?:\\x[0-9A-Fa-f]{2})+)"', src[i:j])
        toks = [bytes(int(b, 16) for b in re.findall(r'\\x([0-9A-Fa-f]{2})', it)) for it in items]
        if len(toks) != 128:
            raise SystemExit("%s : %d entrees, 128 attendues" % (nom, len(toks)))
        tables.append([t.rstrip(b"\x00").decode("latin-1") for t in toks])
    return tables


def lecteur_ancien(texte, tables):
    """msgConvertObjNum d'origine, chemin anglais : `^` seul ouvre une paire, i < 2."""
    out = []
    i = 0
    while i < len(texte):
        if texte[i] == "^" and i + 1 < len(texte):
            jeton, avance = texte[i:i + 2], 2
        else:
            jeton, avance = texte[i], 1
        if jeton == " ":
            out.append(None)
        else:
            trouve = None
            for t in range(2):
                for j in range(128):
                    if tables[t][j] == jeton:
                        trouve = j + t * 128 + BASE_HAN
                        break
                if trouve is not None:
                    break
            out.append(trouve)   # None = introuvable, donc une espace a l'ecran
        i += avance
    return out


def lecteur_nouveau(texte, tables):
    """La version corrigee : paire d'abord sur i < 3, sinon octet seul sur i < 2."""
    out = []
    i = 0
    while i < len(texte):
        if texte[i] == " ":
            out.append(None)
            i += 1
            continue
        trouve = None
        avance = 1
        if i + 1 < len(texte):
            paire = texte[i:i + 2]
            for t in range(3):
                for j in range(128):
                    if tables[t][j] == paire and tables[t][j] != VIDE.decode("latin-1"):
                        trouve = j + t * 128 + BASE_HAN
                        break
                if trouve is not None:
                    break
            if trouve is not None:
                avance = 2
        if trouve is None:
            for t in range(2):
                for j in range(128):
                    if tables[t][j] == texte[i]:
                        trouve = j + t * 128 + BASE_HAN
                        break
                if trouve is not None:
                    break
        out.append(trouve)
        i += avance
    return out


def objets_vers_texte(objets, tables):
    """Remonte des numeros d'objet vers les caracteres, pour relire ce que le jeu affichera."""
    out = []
    for n in objets:
        if n is None:
            out.append(" ")
            continue
        idx = n - BASE_HAN
        jeton = tables[idx // 128][idx % 128]
        out.append(MC.DE_ACCENTS.get(jeton, jeton))
    return "".join(out)


_ARR = re.compile(r'static s8\* (\w+)\[(\d+)\] = \{(.*?)\};', re.S)
_STR = re.compile(r'"((?:[^"\\]|\\.)*)"')
_ESC = re.compile(r'\\x([0-9A-Fa-f]{2})')


def chaines(dossier, motif):
    """Toutes les lignes de message d'un dossier, quelle que soit la forme du reste du fichier.

    msgtable_*.c n'a pas de tableaux de messages : il n'en sort simplement rien.
    """
    for p in sorted(glob.glob(os.path.join(dossier, motif))):
        src = open(p, encoding="latin-1").read()
        for m in _ARR.finditer(src):
            for k, s in enumerate(_STR.finditer(m.group(3))):
                t = _ESC.sub(lambda mm: chr(int(mm.group(1), 16)), s.group(1))
                t = t.replace('\\"', '"').replace("\\\\", "\\")
                if t.strip():
                    yield os.path.basename(p), m.group(1), k, t


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--amont", default="C:/3sx-up")
    ap.add_argument("--effb6-corrige", help="effb6.c deja corrige ; sinon on corrige en memoire")
    ap.add_argument("--genere", default="traduction/message_fr")
    args = ap.parse_args()

    avant = lit_tables(os.path.join(args.amont, REL_EFFB6))
    if args.effb6_corrige:
        apres = lit_tables(args.effb6_corrige)
    else:
        import msg_patch_effb6 as P
        src = open(os.path.join(args.amont, REL_EFFB6), encoding="latin-1").read().replace("\r\n", "\n")
        tmp = os.path.join(os.path.dirname(os.path.abspath(args.genere)), "_effb6_corrige.c")
        open(tmp, "w", encoding="latin-1", newline="\n").write(P.retokenise(src))
        apres = lit_tables(tmp)
        os.remove(tmp)

    print("1. L'anglais est-il intact ?")
    en = os.path.join(args.amont, "src/sf33rd/Source/Game/message/en")
    n = differences = 0
    for f, nom, k, ligne in chaines(en, "*.c"):
        n += 1
        if lecteur_ancien(ligne, avant) != lecteur_nouveau(ligne, apres):
            differences += 1
            if differences <= 5:
                print("   DIFFERENT %s %s ligne %d : %r" % (f, nom, k + 1, ligne.strip()))
    print("   %d lignes anglaises relues, %d rendues differemment" % (n, differences))

    if not os.path.isdir(args.genere):
        print("\n2. Pas de dossier genere (%s), controle saute." % args.genere)
        return 1 if differences else 0

    print("\n2. Le francais genere se relit-il ?")
    n = fautes = 0
    exemples = []
    for f, nom, k, ligne in chaines(args.genere, "pl??*_*.c"):
        n += 1
        relu = objets_vers_texte(lecteur_nouveau(ligne, apres), apres).rstrip()
        attendu = MC.decode(ligne).rstrip()
        if relu != attendu:
            fautes += 1
            if fautes <= 5:
                print("   DIFFERENT %s %s ligne %d\n      attendu %r\n      relu    %r"
                      % (f, nom, k + 1, attendu, relu))
        elif len(exemples) < 4 and any(c in MC.ACCENTS for c in attendu):
            exemples.append((f, attendu.strip()))
    print("   %d lignes relues, %d fautes" % (n, fautes))
    for f, t in exemples:
        print("   exemple  %-16s %s" % (f, t))

    return 1 if (differences or fautes) else 0


if __name__ == "__main__":
    sys.exit(main())
