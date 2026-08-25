#!/usr/bin/env python3
"""Lecture, ecriture et encodage des tables de messages de 3SX.

Partage entre msg_extract.py et msg_build.py. Rien ici ne connait de langue en
particulier : c'est la forme des fichiers et l'encodage des accents, pas leur contenu.

L'encodage des accents
----------------------
Les glyphes accentues sont dans la ROM, adresses par `src_han_alpha2` (effb6.c), une table
de jetons de deux octets : tete = accent, second octet = lettre. Cette table est du code
source, pas de la donnee : les jetons sont a nous. Ceux d'origine employaient
`%` `)` `(` `^` `~` `,`, dont quatre apparaissent deja dans les textes anglais -- `(A` y
figure quatre fois, dans `(ALEX)` et compagnie -- ce qui en fait des pieges.

Les tetes retenues ici n'apparaissent dans AUCUN texte passant par msgConvertObjNum,
verifie sur les 58 fichiers de personnages plus msgsysdir, msgextra et msgmenu :

    `   grave        `e     *   aigu    *e     ^   circonflexe  ^e
    =   trema        =e     ~   tilde   ~n     ;   cedille      ;c

`^` sert deja de tete a deux octets dans le code (`if (moji[0] == 0x5E)`) et n'apparait
dans les textes que sous la forme `^D`, jamais suivi d'une voyelle : le reutiliser pour le
circonflexe ne casse rien.

Le traducteur n'ecrit jamais ces jetons. Il ecrit du francais accentue ; c'est
msg_build.py qui encode, et qui verifie l'encodage par aller-retour.
"""

import re
import unicodedata

# ------------------------------------------------------------------ l'alphabet du jeu

TETES = {"trema": "=", "aigu": "*", "grave": "`", "circonflexe": "^", "tilde": "~", "cedille": ";"}
LEADS = set(TETES.values())

# Ordre des emplacements dans src_han_alpha2, releve sur les glyphes rendus par
# font_inventory.py. Les 80 autres emplacements de la table sont vides.
DISPOSITION_ALPHA2 = [
    (20, "trema", "A"), (21, "aigu", "A"), (22, "grave", "A"), (23, "circonflexe", "A"),
    (25, "tilde", "A"), (27, "cedille", "C"),
    (28, "trema", "E"), (29, "aigu", "E"), (30, "grave", "E"), (31, "circonflexe", "E"),
    (32, "trema", "I"), (33, "aigu", "I"), (34, "grave", "I"), (35, "circonflexe", "I"),
    (37, "tilde", "N"),
    (38, "trema", "O"), (39, "aigu", "O"), (40, "grave", "O"), (41, "circonflexe", "O"),
    (42, "tilde", "O"),
    (44, "trema", "U"), (45, "aigu", "U"), (46, "grave", "U"), (47, "circonflexe", "U"),
    (49, "trema", "a"), (50, "aigu", "a"), (51, "grave", "a"), (52, "circonflexe", "a"),
    (54, "tilde", "a"), (56, "cedille", "c"),
    (57, "trema", "e"), (58, "aigu", "e"), (59, "grave", "e"), (60, "circonflexe", "e"),
    (61, "trema", "i"), (62, "aigu", "i"), (63, "grave", "i"), (64, "circonflexe", "i"),
    (66, "tilde", "n"),
    (68, "trema", "o"), (69, "aigu", "o"), (70, "grave", "o"), (71, "circonflexe", "o"),
    (72, "tilde", "o"),
    (74, "trema", "u"), (75, "aigu", "u"), (76, "grave", "u"), (77, "circonflexe", "u"),
]

_COMBINANT = {"grave": "̀", "aigu": "́", "circonflexe": "̂",
              "tilde": "̃", "trema": "̈", "cedille": "̧"}

ACCENTS = {}      # caractere compose -> jeton de deux octets
DE_ACCENTS = {}   # jeton -> caractere compose
for _i, _acc, _base in DISPOSITION_ALPHA2:
    _c = unicodedata.normalize("NFC", _base + _COMBINANT[_acc])
    ACCENTS[_c] = TETES[_acc] + _base
    DE_ACCENTS[TETES[_acc] + _base] = _c

# Ce que src_han_alpha et src_han_kata savent dessiner en un octet, releve dans effb6.c.
ASCII_DISPO = set(
    "abcdefghijklmnopqrstuvwxyz"
    "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    "0123456789"
    " !?.,\"'$%&()#:;/+-"
)

# Ce que le jeu ne sait pas dessiner : corrige d'office, avec un avertissement.
REMPLACEMENTS = {
    "’": "'", "‘": "'",                 # apostrophes typographiques
    "“": '"', "”": '"',                 # guillemets courbes
    "«": '"', "»": '"',                 # guillemets francais
    "…": "...",                              # points de suspension
    "–": "-", "—": "-",                 # tirets demi et cadratin
    " ": " ", " ": " ",                 # espaces insecables
    "œ": "oe", "Œ": "OE",               # oe colle
    "æ": "ae", "Æ": "AE",
    "ÿ": "y", "Ÿ": "Y",
    "ß": "ss",
    "¿": "?", "¡": "!",
}

# ------------------------------------------------------------------ contraintes

CAP_GLYPHES = 108   # CONN conn[108], puis while (1) {} dans get_message_conn_data
LARGEUR_BOITE = 48  # toutes les chaines anglaises sont completees a 48
COLONNE_MAX = 43    # la colonne la plus a droite que l'anglais atteint


def normalise(texte):
    """Ramene la typographie a ce que le jeu sait ecrire. -> (texte, [(avant, apres), ...])"""
    corrections = []
    out = []
    for c in unicodedata.normalize("NFC", texte):
        if c in REMPLACEMENTS:
            corrections.append((c, REMPLACEMENTS[c]))
            out.append(REMPLACEMENTS[c])
        else:
            out.append(c)
    return "".join(out), corrections


def encode(texte):
    """Francais accentue -> octets que msgConvertObjNum sait lire.

    -> (chaine encodee, [caracteres refuses])
    """
    out, refuses = [], []
    for c in texte:
        if c in ACCENTS:
            out.append(ACCENTS[c])
        elif c in ASCII_DISPO:
            out.append(c)
        else:
            refuses.append(c)
    return "".join(out), refuses


def decode(encode_str):
    """Relit comme le fera msgConvertObjNum : une tete suivie d'une lettre connue fait un jeton."""
    out = []
    i = 0
    while i < len(encode_str):
        pair = encode_str[i:i + 2]
        if len(pair) == 2 and pair in DE_ACCENTS:
            out.append(DE_ACCENTS[pair])
            i += 2
        else:
            out.append(encode_str[i])
            i += 1
    return "".join(out)


def jetons(encode_str):
    """Decoupe en jetons, comme le lecteur. -> [(jeton, est_espace)]"""
    out = []
    i = 0
    while i < len(encode_str):
        pair = encode_str[i:i + 2]
        if len(pair) == 2 and pair in DE_ACCENTS:
            out.append((pair, False))
            i += 2
        else:
            c = encode_str[i]
            out.append((c, c == " "))
            i += 1
    return out


def compte_glyphes(encode_str):
    """Nombre de CONN consommes : l'espace n'en consomme pas."""
    return sum(1 for _, espace in jetons(encode_str) if not espace)


def derniere_colonne(encode_str):
    """Colonne (1 = la premiere) du dernier glyphe non-espace. 0 si la ligne est vide."""
    col = 0
    derniere = 0
    for _, espace in jetons(encode_str):
        col += 1
        if not espace:
            derniere = col
    return derniere


# ------------------------------------------------------------------ lecture des .c

_ARR = re.compile(r'static s8\* (\w+)\[(\d+)\] = \{(.*?)\};', re.S)
_ADR = re.compile(r'static s8\*\* (\w+)\[(\d+)\] = \{(.*?)\};', re.S)
_CTR = re.compile(r'static s8 (\w+)\[(\d+)\] = \{(.*?)\};', re.S)
_TBL = re.compile(r'MessageTable (\w+) = \{ (\w+), (\w+) \};')
_STR = re.compile(r'"((?:[^"\\]|\\.)*)"')
_ESC = re.compile(r'\\x([0-9A-Fa-f]{2})')

KINDS = [("win", "citations de victoire"),
         ("tlk", "dialogues d'avant-combat"),
         ("end", "fins")]

NOMS = ["Gill", "Alex", "Ryu", "Yun", "Dudley", "Necro", "Hugo", "Ibuki", "Elena", "Oro",
        "Yang", "Ken", "Sean", "Urien", "Akuma", "Chun-Li", "Makoto", "Q", "Twelve", "Remy"]


def _decode_c(s):
    t = _ESC.sub(lambda m: chr(int(m.group(1), 16)), s)
    return t.replace('\\"', '"').replace("\\\\", "\\")


def echappe_c(s):
    return s.replace("\\", "\\\\").replace('"', '\\"')


def lit_fichier(path):
    """La structure d'un pl<NN><kind>_<lang>.c, telle qu'elle est."""
    src = open(path, encoding="latin-1").read()
    messages = {}
    for m in _ARR.finditer(src):
        messages[m.group(1)] = [_decode_c(s.group(1)) for s in _STR.finditer(m.group(3))]
    adr, ctr, tbl = _ADR.search(src), _CTR.search(src), _TBL.search(src)
    if not (adr and ctr and tbl):
        raise SystemExit("%s : structure inattendue" % path)
    return {
        "table": tbl.group(1),
        "adr": adr.group(1),
        "ctr": ctr.group(1),
        "ordre": re.findall(r'\b(msg\w+)\b', adr.group(3)),
        "messages": messages,
    }


def indent_de(lignes, defaut=3):
    """L'indentation d'un message : celle de sa premiere ligne non vide."""
    for l in lignes:
        if l.strip():
            return len(l) - len(l.lstrip(" "))
    return defaut
