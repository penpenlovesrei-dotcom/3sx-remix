# -*- coding: utf-8 -*-
"""Ajoute N etages a 3SX en etendant toutes les tables indexees par l'etage.

Le piege de ce projet, ce sont les **tables paralleles** : le jeu en a vingt-six indexees
par `bg_w.stage` ou `bg_w.bg_index`, dans neuf fichiers, et en oublier une suffit a faire
lire n'importe quoi. Elles ont ete relevees par leurs **consommateurs**, pas par leur
taille -- il y a 23 personnages ET 23 etages, et confondre les deux est facile.

Chaque etage ajoute est une copie de l'etage 22, qui marche : meme script `BG220`, meme
nombre de plans, meme masque plein. Ne changent que le nom affiche, les limites de terrain
(calculees sur l'etendue de l'art par `bande3sx.py`) et l'index de fond.

    python ajouter_etages.py --voir      ce qui serait fait, sans rien ecrire
    python ajouter_etages.py             ecrit
"""
import os
import re
import sys

SRC = r"C:\Temp3sx\src"

# nom, fichier. Relevees par grep sur `[bg_w.stage]` et `[bg_w.bg_index]`, pas par la taille.
TABLES = [
    ("use_scr", "sf33rd/Source/Game/stage/bg_data.c"),
    ("use_real_scr", "sf33rd/Source/Game/stage/bg_data.c"),
    ("use_family", "sf33rd/Source/Game/stage/bg_data.c"),
    ("rewrite_scr", "sf33rd/Source/Game/stage/bg_data.c"),
    ("stage_bgw_number", "sf33rd/Source/Game/stage/bg_data.c"),
    ("msp", "sf33rd/Source/Game/stage/bg_data.c"),
    ("bgtex_stage_gbix", "sf33rd/Source/Game/stage/bg_data.c"),
    ("stage_priority", "sf33rd/Source/Game/stage/bg_data.c"),
    ("stage_opaque", "sf33rd/Source/Game/stage/bg_data.c"),
    ("bgrw_on", "sf33rd/Source/Game/stage/bg_data.c"),
    ("ake_bg_off", "sf33rd/Source/Game/stage/bg_data.c"),
    ("limit_tbl3", "sf33rd/Source/Game/stage/bg_data.c"),
    ("bg_index_tbl", "sf33rd/Source/Game/stage/bg_data.c"),
    ("bg_map_tbl", "sf33rd/Source/Game/stage/bg_data.c"),
    ("ta_move_tbl", "sf33rd/Source/Game/stage/tate00.c"),
    ("mts_OB_page", "sf33rd/Source/Game/rendering/texcash.c"),
    ("scr_obj_num", "sf33rd/Source/Game/effect/eff05.c"),
    ("scr_obj_data", "sf33rd/Source/Game/effect/eff05.c"),
    ("char_add", "sf33rd/Source/Game/effect/eff05.c"),
    ("scr_obj_num6", "sf33rd/Source/Game/effect/eff06.c"),
    ("scr_obj_data6", "sf33rd/Source/Game/effect/eff06.c"),
    ("ag_sel_table", "sf33rd/Source/Game/effect/effc9.c"),
    ("smoke_check", "sf33rd/Source/Game/animation/appear.c"),
    ("win_2000_tbl", "sf33rd/Source/Game/animation/win_pl.c"),
    ("BGM_Stage_Data", "sf33rd/Source/Game/sound/se.c"),
]

# declarations sans initialiseur : en-tetes, `extern`, tampons
DECLS = [
    ("smoke_check", "sf33rd/Source/Game/animation/appear.h"),
    ("ag_sel_table", "sf33rd/Source/Game/effect/effc9.c"),
    ("mts_OB_page", "sf33rd/Source/Game/rendering/texcash.c"),
    ("use_scr", "sf33rd/Source/Game/stage/bg_data.h"),
    ("use_real_scr", "sf33rd/Source/Game/stage/bg_data.h"),
    ("use_family", "sf33rd/Source/Game/stage/bg_data.h"),
    ("rewrite_scr", "sf33rd/Source/Game/stage/bg_data.h"),
    ("stage_bgw_number", "sf33rd/Source/Game/stage/bg_data.h"),
    ("msp", "sf33rd/Source/Game/stage/bg_data.h"),
    ("bgtex_stage_gbix", "sf33rd/Source/Game/stage/bg_data.h"),
    ("stage_priority", "sf33rd/Source/Game/stage/bg_data.h"),
    ("stage_opaque", "sf33rd/Source/Game/stage/bg_data.h"),
    ("bgrw_on", "sf33rd/Source/Game/stage/bg_data.h"),
    ("ake_bg_off", "sf33rd/Source/Game/stage/bg_data.h"),
    ("limit_tbl3", "sf33rd/Source/Game/stage/bg_data.h"),
    ("bg_index_tbl", "sf33rd/Source/Game/stage/bg_data.h"),
    ("bg_map_tbl", "sf33rd/Source/Game/stage/bg_data.h"),
    ("ta_move_tbl", "sf33rd/Source/Game/stage/tate00.h"),
    ("scr_obj_num", "sf33rd/Source/Game/effect/eff05.h"),
    ("scr_obj_data", "sf33rd/Source/Game/effect/eff05.h"),
    ("char_add", "sf33rd/Source/Game/effect/eff05.h"),
    ("scr_obj_num6", "sf33rd/Source/Game/effect/eff06.h"),
    ("scr_obj_data6", "sf33rd/Source/Game/effect/eff06.h"),
    ("win_2000_tbl", "sf33rd/Source/Game/animation/win_pl.h"),
    ("BGM_Stage_Data", "sf33rd/Source/Game/sound/se.h"),
]

# decor, nom affiche, l_limit2, r_limit2 -- les limites viennent de bande3sx.py, qui les
# calcule sur l'etendue reelle de l'art dans la zone jouee.
DECORS = [
    ("bg00", "GILL", 0x0140, 0x02C0),
    ("bg01", "ALEX", 0x00C0, 0x0340),
    ("bg02", "RYU", 0x0140, 0x02C0),
    ("bg03", "YUN", 0x0140, 0x02C0),
    ("bg04", "DUDLEY", 0x00C0, 0x0340),
    ("bg05", "NECRO", 0x00C0, 0x02C0),
    ("bg06", "HUGO", 0x00C0, 0x0340),
    ("bg07", "IBUKI", 0x00C0, 0x0340),
    ("bg09", "ELENA", 0x00C0, 0x0340),
    ("bg0a", "ORO", 0x0140, 0x02C0),
    ("bg0b", "YANG", 0x0140, 0x02C0),
    ("bg0c", "KEN", 0x00C0, 0x0340),
    ("bg0d", "SEAN", 0x0140, 0x02C0),
    ("bg0e", "URIEN", 0x0140, 0x02C0),
    ("bg0f", "GORGE", 0x0240, 0x02C0),
]

BASE = 22            # l'etage 22 existe deja et sert de modele a tous les autres
N = len(DECORS)      # etages 22 .. 22+N-1
FIN = BASE + N


def elements(txt):
    """Decoupe un initialiseur en elements de premier niveau.

    Les commentaires sont sautes : `/* etage 22, copie de 5 */` porte une virgule, et la
    compter en ferait un element de plus -- c'est ce qui a fait echouer le premier essai.
    """
    out, prof, deb, i, n = [], 0, 0, 0, len(txt)
    while i < n:
        c = txt[i]
        if c == "/" and i + 1 < n and txt[i + 1] == "*":
            j = txt.find("*/", i + 2)
            i = n if j == -1 else j + 2
            continue
        if c == "/" and i + 1 < n and txt[i + 1] == "/":
            j = txt.find(chr(10), i)
            i = n if j == -1 else j + 1
            continue
        if c in "{[(":
            prof += 1
        elif c in "}])":
            prof -= 1
        elif c == "," and prof == 0:
            out.append(txt[deb:i])
            deb = i + 1
        i += 1
    if txt[deb:].strip():
        out.append(txt[deb:])
    return out


def corps(s, i):
    """Le contenu de l'accolade ouverte en i, et l'index de sa fermante."""
    prof, j = 0, i
    while j < len(s):
        if s[j] == "{":
            prof += 1
        elif s[j] == "}":
            prof -= 1
            if prof == 0:
                return s[i + 1:j], j
        j += 1
    raise ValueError("accolade non fermee")


def etendre(s, nom):
    """Passe `nom[23]` a `nom[FIN]` et duplique l'element 22 autant de fois qu'il faut."""
    # on veut la DEFINITION -- celle suivie d'un `=` -- et pas un `extern` ni un prototype
    m = None
    for c in re.finditer(r"\b" + re.escape(nom) + r"\s*\[\s*(\d*)\s*\]", s):
        eq, pv = s.find("=", c.end()), s.find(";", c.end())
        if eq != -1 and (pv == -1 or eq < pv):
            m = c
            break
    if m is None:
        return s, "definition introuvable"
    s = s[:m.start(1)] + str(FIN) + s[m.end(1):]
    eq = s.find("=", m.start() + len(nom))
    d = s.find("{", eq)
    txt, fin = corps(s, d)
    els = elements(txt)
    if len(els) != 23:
        return s, f"{len(els)} elements au lieu de 23 -- NON TOUCHE"
    ajout = "".join(",\n    " + els[BASE].strip() for _ in range(N - 1))
    return s[:fin] + ajout + "\n" + s[fin:], f"[23] -> [{FIN}], element 22 duplique {N-1} fois"


def main():
    voir = "--voir" in sys.argv
    rapport = []

    par_fichier = {}
    for nom, fic in TABLES:
        par_fichier.setdefault(fic, []).append(nom)

    for fic, noms in par_fichier.items():
        p = os.path.join(SRC, fic)
        s = open(p, encoding="utf-8").read()
        for nom in noms:
            s, msg = etendre(s, nom)
            rapport.append(f"  {os.path.basename(fic):16s} {nom:20s} {msg}")
        if not voir:
            open(p, "w", encoding="utf-8").write(s)

    for nom, fic in DECLS:
        p = os.path.join(SRC, fic)
        if not os.path.exists(p):
            rapport.append(f"  {os.path.basename(fic):16s} {nom:20s} fichier absent")
            continue
        s = open(p, encoding="utf-8").read()
        n = len(re.findall(r"\b" + re.escape(nom) + r"\s*\[\s*23\s*\]", s))
        if n:
            s = re.sub(r"\b(" + re.escape(nom) + r")\s*\[\s*23\s*\]", r"\1[" + str(FIN) + "]", s)
            rapport.append(f"  {os.path.basename(fic):16s} {nom:20s} {n} declaration(s) -> [{FIN}]")
            if not voir:
                open(p, "w", encoding="utf-8").write(s)

    print(("CE QUI SERAIT FAIT" if voir else "FAIT") + f" : {N} etages, {BASE} a {FIN - 1}")
    print("\n".join(rapport))


if __name__ == "__main__":
    main()
