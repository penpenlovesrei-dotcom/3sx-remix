#!/usr/bin/env python3
"""Fabrique la modification de effb6.c qui rend les lettres accentuees atteignables.

Deux changements, indissociables :

1. `src_han_alpha2` est retokenise. Ses jetons d'origine employaient `%` `)` `(` `,`,
   qui apparaissent dans les textes anglais -- `(A` y figure quatre fois, dans `(ALEX)`
   et compagnie. Les nouvelles tetes n'apparaissent nulle part.

2. `msgConvertObjNum` essaie d'abord un jeton de deux octets sur les trois tables, puis
   retombe sur un octet seul. Avant, seul `^` ouvrait une paire, et la recherche
   s'arretait a `han_adrs[1]`.

Pris ensemble, les deux laissent le rendu anglais rigoureusement identique : aucune paire
formable par un texte anglais n'existe dans la nouvelle table. Pris separement, le second
casserait `(ALEX)`.

    python tools/msg_patch_effb6.py --source C:/3sx-up --sortie traduction/effb6-accents.patch
"""

import argparse
import difflib
import os
import re
import sys

import msg_catalogue as MC

REL = "src/sf33rd/Source/Game/effect/effb6.c"

ANCIEN_LECTEUR = """\
    if (moji[0] == 0x5E) {
        tmpstr[0] = moji[0];
        tmpstr[1] = moji[1];
        tmpstr[2] = 0;
        rnum = 2;
    } else {
        tmpstr[0] = moji[0];
        tmpstr[1] = 0;
        rnum = 1;
    }

    if (tmpstr[0] == ' ') {
        goto one;
    }

    for (i = 0; i < 2; i++) {
        for (j = 0; j < 128; j++) {
            if (strcmp(&tmpstr[0], han_adrs[i][j]) != 0) {
                continue;
            }

            *hz = 0;
            *spc = 0;
            *num = j + (i * 128) + 0x7F30;
            return rnum;
        }
    }
"""

NOUVEAU_LECTEUR = """\
    if (moji[0] == ' ') {
        goto one;
    }

    // Un jeton de deux octets d'abord, sur les trois tables : `^D` du jeu d'origine et les
    // lettres accentuees de src_han_alpha2. Une entree d'un seul caractere ne peut pas
    // egaler une chaine de deux, donc rien ne se confond. Si la paire n'existe dans aucune
    // table on relit l'octet seul, ce qui laisse les textes anglais inchanges : aucune de
    // leurs paires ne figure dans src_han_alpha2.
    if (moji[1] != 0) {
        tmpstr[0] = moji[0];
        tmpstr[1] = moji[1];
        tmpstr[2] = 0;

        for (i = 0; i < 3; i++) {
            for (j = 0; j < 128; j++) {
                if (strcmp(&tmpstr[0], han_adrs[i][j]) != 0) {
                    continue;
                }

                *hz = 0;
                *spc = 0;
                *num = j + (i * 128) + 0x7F30;
                return 2;
            }
        }
    }

    tmpstr[0] = moji[0];
    tmpstr[1] = 0;
    rnum = 1;

    for (i = 0; i < 2; i++) {
        for (j = 0; j < 128; j++) {
            if (strcmp(&tmpstr[0], han_adrs[i][j]) != 0) {
                continue;
            }

            *hz = 0;
            *spc = 0;
            *num = j + (i * 128) + 0x7F30;
            return rnum;
        }
    }
"""

# Anciennes tetes -> nouvelles, relevees sur les glyphes rendus par font_inventory.py
RETETE = {0x25: "trema", 0x29: "aigu", 0x28: "grave",
          0x5E: "circonflexe", 0x7E: "tilde", 0x2C: "cedille"}


def retokenise(src):
    """Reecrit les 48 jetons reels de src_han_alpha2 avec les nouvelles tetes."""
    debut = src.index("const s8* src_han_alpha2[128] = {")
    fin = src.index("};", debut) + 2
    bloc = src[debut:fin]

    n = [0]

    def remplace(m):
        octets = [int(b, 16) for b in re.findall(r"\\x([0-9A-Fa-f]{2})", m.group(0))]
        if len(octets) != 2 or octets == [0x5E, 0x5F]:
            return m.group(0)          # emplacement vide, on n'y touche pas
        accent = RETETE.get(octets[0])
        if accent is None:
            return m.group(0)
        n[0] += 1
        return '"\\x%02X\\x%02X"' % (ord(MC.TETES[accent]), octets[1])

    neuf = re.sub(r'"(?:\\x[0-9A-Fa-f]{2})+"', remplace, bloc)
    if n[0] != 48:
        raise SystemExit("src_han_alpha2 : %d jetons retokenises, 48 attendus" % n[0])

    commentaire = (
        "// Lettres latines accentuees. Les jetons sont du code, pas de la donnee : seul l'indice\n"
        "// compte, il designe l'objet j + 256 + 0x7F30. Les tetes d'origine etaient % ) ( , et\n"
        "// elles figurent dans les textes anglais : \"(ALEX)\" se serait mis a commencer par un A\n"
        "// accent grave. Elles ont donc ete remplacees par des octets qu'aucun texte n'emploie,\n"
        "// verifie sur les 58 fichiers de personnages plus msgsysdir, msgextra et msgmenu :\n"
        "//   ` grave   * aigu   ^ circonflexe   = trema   ~ tilde   ; cedille\n"
    )
    return src[:debut] + commentaire + neuf + src[fin:]


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", default="C:/3sx-up", help="racine du clone amont, lue seulement")
    ap.add_argument("--sortie", default="traduction/effb6-accents.patch")
    ap.add_argument("--ecrire-dans", help="au lieu d'un patch, reecrire effb6.c dans ce clone")
    args = ap.parse_args()

    chemin = os.path.join(args.source, REL)
    if not os.path.exists(chemin):
        raise SystemExit("introuvable : %s" % chemin)
    brut = open(chemin, encoding="latin-1", newline="").read()

    # Le depot a core.autocrlf = true alors que ses blobs sont en LF : la copie de travail
    # peut etre dans l'une ou l'autre convention. On travaille en LF et on restitue.
    crlf = "\r\n" in brut
    avant = brut.replace("\r\n", "\n")

    if ANCIEN_LECTEUR not in avant:
        raise SystemExit("msgConvertObjNum n'a pas la forme attendue : l'amont a bouge, "
                         "il faut relire effb6.c avant de regenerer ce patch.")

    apres = retokenise(avant).replace(ANCIEN_LECTEUR, NOUVEAU_LECTEUR)

    if args.ecrire_dans:
        cible = os.path.join(args.ecrire_dans, REL)
        if not os.path.exists(cible):
            raise SystemExit("introuvable : %s" % cible)
        texte = apres.replace("\n", "\r\n") if crlf else apres
        open(cible, "w", encoding="latin-1", newline="").write(texte)
        print("reecrit %s (%s)" % (cible, "CRLF" if crlf else "LF"))
        return 0

    diff = difflib.unified_diff(avant.splitlines(True), apres.splitlines(True),
                                "a/" + REL, "b/" + REL)
    os.makedirs(os.path.dirname(os.path.abspath(args.sortie)), exist_ok=True)
    open(args.sortie, "w", encoding="latin-1", newline="\n").writelines(diff)
    print("ecrit %s" % args.sortie)
    return 0


if __name__ == "__main__":
    sys.exit(main())
