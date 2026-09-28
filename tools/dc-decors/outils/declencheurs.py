# -*- coding: utf-8 -*-
"""CE QUI DECLENCHE UNE ANIMATION DE DECOR -- 23/09/2026.

La cadence d'une animation est dans son script (`cadences.py`, `cadencesng.py`) : quelle
image, tenue combien de trames, et combien de tours de boucle. Mais ce qui FAIT CHANGER de
script -- le badaud qui suit les combattants des yeux, celui qui sursaute quand on tombe --
n'est pas dans le script. C'est dans la ROUTINE de l'objet.

Le pivot est le poseur de script :

    2I 0x8C0B4AD4   poser_script(objet r4, table r5, script r6)
       objet[+454] = table, objet[+456] = script,
       objet[+448] = u32[ u32[objet + 364 + table*4] + script*4 ]

Toute animation qui change vient d'un appel a ce poseur. On enumere donc ses appelants --
`jsr` par litteral ET `bsr` relatif, le troisieme chemin que `remonter2i` manquait -- puis,
pour chaque site, on lit ce que la routine consulte juste avant : les adresses de RAM
qu'elle charge, et les comparaisons qui gardent le saut.

    python declencheurs.py          2I puis NG
    python declencheurs.py ng       New Generation seulement
"""
import os
import struct
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)

POSEUR_2I = 0x8C0B4AD4


def jumeau(mod2i, modng, adresse, n=22, saut=6):
    """L'adresse jumelle dans l'autre binaire, retrouvee par les octets de la routine."""
    p = mod2i.D[mod2i.a2o(adresse + saut):mod2i.a2o(adresse + saut) + n]
    i = modng.D.find(p)
    return None if i == -1 else modng.o2a(i) - saut


def appelants(mod, cible, debut, fin):
    """Tous les sites qui appellent `cible` : `bsr` relatif, `jsr`/`jmp` par litteral."""
    out = []
    for a in range(debut, fin, 2):
        w = mod.u16(mod.a2o(a))
        if w >> 12 == 0xB:                      # bsr
            d = w & 0xFFF
            if d & 0x800:
                d -= 0x1000
            if a + 4 + d * 2 == cible:
                out.append((a, "bsr"))
    for o in mod.find_u32(cible):
        lit = mod.o2a(o)
        for b in range(max(debut, lit - 0x400), lit, 2):
            w = mod.u16(mod.a2o(b))
            if w >> 12 == 0xD and ((b + 4) & ~3) + (w & 0xFF) * 4 == lit:
                n = (w >> 8) & 15
                for c in range(b, min(b + 0x40, fin), 2):
                    x = mod.u16(mod.a2o(c))
                    if x in (0x400B | (n << 8), 0x402B | (n << 8)):
                        out.append((c, "jsr" if (x & 0xFF) == 0x0B else "jmp"))
                        break
    return sorted(set(out))


def debut_de_routine(mod, a, recul=0x600):
    """Le premier mot apres le `rts` qui precede : approximation de l'entree."""
    for b in range(a - 2, a - recul, -2):
        if mod.u16(mod.a2o(b)) == 0x000B:
            return b + 4
    return a - recul


def litteraux(mod, debut, fin, lo, hi):
    """Les u32 charges en PC-relatif dans [debut, fin] qui tombent dans [lo, hi[."""
    out = {}
    for a in range(debut, fin, 2):
        w = mod.u16(mod.a2o(a))
        if w >> 12 != 0xD:
            continue
        c = ((a + 4) & ~3) + (w & 0xFF) * 4
        try:
            v = mod.u32(mod.a2o(c))
        except Exception:
            continue
        if lo <= v < hi:
            out.setdefault(v, []).append(a)
    return out


def immediats_compares(mod, debut, fin):
    """Les `cmp/eq #n` de la fenetre : les valeurs testees."""
    out = []
    for a in range(debut, fin, 2):
        w = mod.u16(mod.a2o(a))
        if (w & 0xFF00) == 0x8800:
            n = w & 0xFF
            out.append(n if n < 0x80 else n - 0x100)
    return out


def analyser(mod, nom, poseur, code, ram):
    sites = appelants(mod, poseur, *code)
    print("=" * 78)
    print("%s : poseur de script 0x%08X, %d sites d'appel" % (nom, poseur, len(sites)))
    print("=" * 78)

    compte = {}
    fiches = []
    for a, genre in sites:
        d = debut_de_routine(mod, a)
        f = min(a + 0x120, code[1])
        lits = litteraux(mod, d, f, *ram)
        cmps = immediats_compares(mod, d, f)
        for v in lits:
            compte[v] = compte.get(v, 0) + 1
        fiches.append((a, genre, d, lits, cmps))

    print("\nLES ETATS CONSULTES, par nombre de routines qui les lisent :")
    for v, n in sorted(compte.items(), key=lambda kv: -kv[1])[:30]:
        print("   %08X  lu par %2d routine(s)%s" % (v, n, "   <-- partage" if n > 4 else ""))

    print("\nSITE PAR SITE :")
    for a, genre, d, lits, cmps in fiches:
        part = [v for v in lits if compte[v] > 4]
        propre = [v for v in lits if compte[v] <= 4]
        print("   %08X %-3s  routine ~%08X" % (a, genre, d))
        if propre:
            print("      etats PROPRES  : %s" % " ".join("%08X" % v for v in propre))
        if part:
            print("      etats partages : %s" % " ".join("%08X" % v for v in part))
        if cmps:
            print("      cmp/eq         : %s" % " ".join(str(c) for c in cmps[:14]))
    return fiches


def main():
    quoi = (sys.argv[1] if len(sys.argv) > 1 else "tout").lower()
    import sh4
    import sh4ng

    if quoi in ("tout", "2i"):
        analyser(sh4, "2nd Impact", POSEUR_2I,
                 (0x8C010000, 0x8C120000), (0x8C500000, 0x8C900000))
    if quoi in ("tout", "ng"):
        p = jumeau(sh4, sh4ng, POSEUR_2I)
        if p is None:
            print("New Generation : poseur de script introuvable par les octets")
            return
        analyser(sh4ng, "New Generation", p,
                 (0x8C010000, 0x8C0F0000), (0x8C400000, 0x8C800000))


if __name__ == "__main__":
    main()
