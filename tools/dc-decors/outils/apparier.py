# -*- coding: utf-8 -*-
"""LES FONCTIONS DE 2nd IMPACT RETROUVEES DANS NEW GENERATION -- 16/09/2026.

POURQUOI
--------
2nd Impact est une suite de New Generation : son code de decor en descend, souvent octet
pour octet a d'autres adresses (`NEW-GENERATION.md`, la table des couches). Tout ce qui a
ete LU dans 2I -- le poseur de script, les chargeurs, le chien d'Oro, les poissons de Yang,
les oiseaux de Yun -- se transpose donc a NG si l'on sait quelle fonction de NG est
laquelle de 2I.

COMMENT
-------
Une fonction est reconnue a sa SIGNATURE : ses mots d'instruction, dont on efface ce qui
depend de la disposition du binaire --

  * le deplacement des `mov.l @(d,pc)` et des `mova` (le litteral est ailleurs) ;
  * le deplacement des `bsr`/`bra` (la cible aussi) ;

-- et dont on garde tout le reste, y compris la VALEUR des `mov.w @(d,pc)` (ce sont des
offsets d'objet, 0x0228, 0x016C : ils identifient). Les litteraux 32 bits ne comptent que
par leur NATURE (code, donnees) ; une seconde passe les compare quand ils designent des
fonctions deja appariees.

Un debut de fonction est une cible de `jsr`/`jmp` par litteral, de `bsr`, ou une entree
d'une table de pointeurs vers le code. La signature couvre la fonction jusqu'a son premier
`rts` suivi de son creneau (au plus 400 mots).

    python apparier.py                     le bilan
    python apparier.py 8C0B4AD4 8C03369E   ce que deviennent ces fonctions de 2I dans NG
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

RACINE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE = 0x8C010000
BINS = {"2i": os.path.join(RACINE, "SF3_2ND.BIN"), "ng": os.path.join(RACINE, "SF3_1ST.BIN")}
CODE_FIN = {"2i": 0x8C120000, "ng": 0x8C160000}


class Binaire:
    def __init__(self, jeu):
        self.jeu = jeu
        self.D = open(BINS[jeu], "rb").read()
        self.fin = BASE + len(self.D)
        self.code_fin = CODE_FIN[jeu]
        self._debuts = None

    def lisible(self, a, n=4):
        return BASE <= a and a + n <= self.fin

    def u16(self, a):
        return struct.unpack_from("<H", self.D, a - BASE)[0]

    def u32(self, a):
        return struct.unpack_from("<I", self.D, a - BASE)[0]

    def est_code(self, v):
        return BASE <= v < self.code_fin and not v & 1

    def litteral(self, pc):
        w = self.u16(pc)
        pool = (pc & ~3) + 4 + (w & 0xFF) * 4
        return self.u32(pool) if self.lisible(pool) else None

    def debuts(self):
        """Les debuts de fonction : cibles de jsr/jmp par litteral, de bsr, et de tables."""
        if self._debuts is not None:
            return self._debuts
        deb = set()
        charge = {}
        for c in range(BASE, self.code_fin - 2, 2):
            w = self.u16(c)
            if (w >> 12) == 0xD:
                v = self.litteral(c)
                if v is not None:
                    charge[(w >> 8) & 0xF] = v
            elif (w & 0xF0FF) in (0x400B, 0x402B):
                v = charge.get((w >> 8) & 0xF)
                if v is not None and self.est_code(v):
                    deb.add(v)
            elif (w >> 12) == 0xB:
                d = w & 0xFFF
                if d & 0x800:
                    d -= 0x1000
                t = c + 4 + d * 2
                if self.est_code(t):
                    deb.add(t)
        self._debuts = sorted(deb)
        return self._debuts

    def fin_de(self, f):
        """Le mot apres le creneau du premier `rts`, borne a 400 mots ET AU DEBUT SUIVANT.

        La borne du debut suivant est indispensable : une fonction qui finit par un appel
        terminal (`jmp`, `bra`) n'a pas de `rts`, et sa signature debordait sur la suivante,
        qui n'est pas la meme dans les deux binaires. Le poseur de script en etait."""
        import bisect
        deb = self.debuts()
        i = bisect.bisect_right(deb, f)
        suivant = deb[i] if i < len(deb) else f + 800
        for k in range(400):
            a = f + 2 * k
            if a >= suivant or not self.lisible(a, 2):
                return a
            if self.u16(a) == 0x000B:
                return min(a + 4, suivant)
        return min(f + 800, suivant)

    def mots(self, f):
        """[(mot normalise, litteral ou None)] de la fonction."""
        out = []
        for a in range(f, self.fin_de(f), 2):
            w = self.u16(a)
            h = w >> 12
            if h == 0xD:
                out.append((w & 0xFF00, self.litteral(a)))
            elif h == 0x9:
                v = self.u16((a + 4 + (w & 0xFF) * 2)) if self.lisible(a + 4 + (w & 0xFF) * 2, 2) else 0
                out.append((w & 0xFF00, ("w", v)))
            elif w >> 8 == 0xC7:
                out.append((0xC700, None))
            elif h in (0xA, 0xB):
                out.append((h << 12, None))
            else:
                out.append((w, None))
        return out

    def signature(self, f, profonde=None):
        """La signature ; `profonde` = {adresse de code de ce binaire : nom commun}."""
        s = []
        for w, lit in self.mots(f):
            if isinstance(lit, tuple):
                s.append((w, lit[1]))
            elif lit is None:
                s.append((w,))
            elif self.est_code(lit):
                s.append((w, "code", profonde.get(lit) if profonde else None))
            else:
                s.append((w, "donnee"))
        return tuple(s)


def apparier(verbeux=False):
    """{adresse 2I : adresse NG} pour les fonctions de signature unique des deux cotes."""
    b2, bn = Binaire("2i"), Binaire("ng")
    lien = {}
    profonde2, profondeN = {}, {}

    for tour in range(4):
        sig_n = {}
        for f in bn.debuts():
            sig_n.setdefault(bn.signature(f, profondeN), []).append(f)
        sig_2 = {}
        for f in b2.debuts():
            sig_2.setdefault(b2.signature(f, profonde2), []).append(f)
        neuf = 0
        for s, fs in sig_2.items():
            if len(fs) == 1 and len(sig_n.get(s, ())) == 1 and len(s) >= 4:
                a2, an = fs[0], sig_n[s][0]
                if lien.get(a2) != an:
                    lien[a2] = an
                    neuf += 1
        # LE PREFIXE, quand la fonction entiere ne tombe pas juste : les 16 premiers mots,
        # uniques des deux cotes. Une fonction qui ne differe que par sa fin (un appel
        # terminal vers une voisine differente) est ainsi retrouvee.
        if tour >= 1:
            pre_n = {}
            for s, fs in sig_n.items():
                if len(s) >= 16:
                    for f in fs:
                        pre_n.setdefault(s[:16], []).append(f)
            pre_2 = {}
            for s, fs in sig_2.items():
                if len(s) >= 16:
                    for f in fs:
                        pre_2.setdefault(s[:16], []).append(f)
            for s, fs in pre_2.items():
                if len(fs) == 1 and len(pre_n.get(s, ())) == 1 and fs[0] not in lien:
                    an = pre_n[s][0]
                    if an not in lien.values():
                        lien[fs[0]] = an
                        neuf += 1
        profonde2 = {a2: "f%X" % a2 for a2 in lien}
        profondeN = {an: "f%X" % a2 for a2, an in lien.items()}
        if verbeux:
            print("tour %d : %d fonctions appariees (%d nouvelles)" % (tour, len(lien), neuf))
        if not neuf:
            break
    return lien, b2, bn


_CACHE = None


def lien():
    global _CACHE
    if _CACHE is None:
        import pickle
        chemin = os.path.join(os.path.dirname(os.path.abspath(__file__)), "apparier.pkl")
        if os.path.exists(chemin):
            _CACHE = pickle.load(open(chemin, "rb"))
        else:
            _CACHE = apparier()[0]
            pickle.dump(_CACHE, open(chemin, "wb"))
    return _CACHE


def main():
    import pickle
    l, b2, bn = apparier(verbeux=True)
    pickle.dump(l, open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "apparier.pkl"), "wb"))
    print("2I : %d debuts, NG : %d debuts, apparies : %d"
          % (len(b2.debuts()), len(bn.debuts()), len(l)))
    for a in sys.argv[1:]:
        v = int(a, 16)
        print("%08X (2I) -> %s (NG)" % (v, "%08X" % l[v] if v in l else "?"))


if __name__ == "__main__":
    main()
