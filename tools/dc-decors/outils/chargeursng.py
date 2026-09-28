# -*- coding: utf-8 -*-
"""A QUI APPARTIENT CHAQUE BLOC DE DECOR — New Generation (`SF3_1ST.BIN`).

Meme methode que `chargeurs2i.py`, et la meme regle : **l'appelant est la seule preuve
d'appartenance d'un bloc**.

    0x8C189178[bande]        le script d'etage
        dedans : jsr <chargeur>  avec  mov #arg,r4 (ou r5), souvent dans le DELAY SLOT
    <chargeur> : nombre = u16[tableA + arg*2]   pointeur = u32[tableB + arg*4]

LE PIEGE PROPRE A NEW GENERATION : LES TABLES DE POINTEURS SONT EN .bss
----------------------------------------------------------------------
Les literaux du code designent 0x8C4DE610, 0x8C4DE6B8, 0x8C4DE900... et **ces adresses
sont a zero dans le fichier** : elles tombent dans le trou 0x8C4D7D00..0x8C4EA000, que le
jeu remplit au demarrage. On y perdrait tout le chantier.

Leur IMAGE est dans le fichier, decalee de **0x12420** :

    .bss  0x8C4D7D00 .. 0x8C4EA000        image  0x8C4C58E0 .. 0x8C4D7BE0

Le decalage n'est pas suppose, il est mesure trois fois :
  * 0x8C4DE610 - 0x12420 = 0x8C4CC1F0, debut d'une serie de tables de 42 entrees (0xA8),
    exactement la « serie de dix tables » de 2I (qui, elle, en a 51) ;
  * 0x8C4DE6B8 - 0x12420 = 0x8C4CC298, dont la premiere entree vaut 0x8C1AEA78 -- c'est
    la fin exacte de la table de nombres 0x8C1AEA24 (42 x 2 octets). Idem pour le second
    jeu : 0x8C1AEF30 + 84 = 0x8C1AEF84, premiere entree de 0x8C4CC340 ;
  * 0x8C4DE908 - 0x12420 = 0x8C4CC4E8, et la contiguite y tombe juste au premier essai :
    16 x 38, 6 x 38, 2 x 38 octets. Une adresse fausse ne fait pas ca.

    python chargeursng.py
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sh4ng as sh4

D, B = sh4.D, sh4.BASE
u16 = lambda a: struct.unpack_from('<H', D, a - B)[0]
s16 = lambda a: struct.unpack_from('<h', D, a - B)[0]
u32 = lambda a: struct.unpack_from('<I', D, a - B)[0]
u8 = lambda a: D[a - B]

# La BONNE table est 0x8C189178 : c'est elle que le dispatcher 0x8C085F7E indexe par
# `u16[contexte + 74]` (le numero de bande), et son memcpy copie 76 octets = 19 entrees.
# 0x8C1A2534 (18 entrees, dispatcher 0x8C08D640) a la meme forme et n'est PAS celle-la :
# son index vient de `u16[objet + 44]`. Piste fermee, voir NEW-GENERATION.md.
TABLE_SCRIPTS = 0x8C189178
NB_ETAGES = 19
CONTEXTE = 0x8C552674            # +4 = decor, +5 = aire, +74 = bande  (2I : 0x8C6AF304)
SERIE = 0x8C4CC1F0               # image .data de la serie de tables, pas 0xA8
PAS_SERIE = 0xA8                 # 42 entrees = 14 decors x 3 aires
NB_DECORS = 14
FIN_SCRIPTS = 0x8C08D000

BSS_LO, BSS_HI, DELTA = 0x8C4D7D00, 0x8C4EA000, 0x12420

FIN_BIN = B + len(D)
lisible = lambda a, n=4: B <= a and a + n <= FIN_BIN
CODE = lambda v: 0x8C010000 <= v < 0x8C0F0000
DONNEES = lambda v: 0x8C0F0000 <= v < FIN_BIN


def reel(a):
    """L'adresse ou LIRE une table : les tables de .bss ont leur image plus bas."""
    return a - DELTA if BSS_LO <= a < BSS_HI else a


def scripts_detage():
    """[(debut, fin, etage)] tries par adresse."""
    t = sorted((u32(TABLE_SCRIPTS + k * 4), k) for k in range(NB_ETAGES))
    out = []
    for i, (ad, d) in enumerate(t):
        j = i + 1
        while j < len(t) and t[j][0] == ad:
            j += 1
        fin = t[j][0] if j < len(t) else FIN_SCRIPTS
        out.append((ad, fin, d))
    return out


def litteral(pc):
    op = u16(pc)
    if (op >> 12) != 0xD:
        return None
    pool = (pc & ~3) + 4 + (op & 0xFF) * 4
    return u32(pool) if lisible(pool) else None


def appels(deb, fin):
    """[(site, cible, arg4, arg5)] des jsr/jmp @rN du bloc."""
    charge = {}
    out = []
    for c in range(deb, min(fin, FIN_BIN - 2), 2):
        op = u16(c)
        if (op >> 12) == 0xD:
            v = litteral(c)
            if v is not None:
                charge[(op >> 8) & 0xF] = v
        elif (op & 0xF0FF) in (0x400B, 0x402B):
            cible = charge.get((op >> 8) & 0xF)
            if cible is None or not CODE(cible):
                continue
            args = {}
            for reg, base in ((4, 0xE400), (5, 0xE500)):
                for p in [c + 2] + [c - 2 * k for k in range(1, 10)]:
                    if p < B or p + 2 > FIN_BIN:
                        continue
                    o = u16(p)
                    if (o & 0xFF00) == base:
                        args[reg] = o & 0xFF
                        break
            out.append((c, cible, args.get(4), args.get(5)))
        # bsr : deplacement de 12 bits signes
        elif (op >> 12) == 0xB:
            d12 = op & 0xFFF
            if d12 & 0x800:
                d12 -= 0x1000
            cible = c + 4 + d12 * 2
            if CODE(cible):
                out.append((c, cible, None, None))
    for v in set(charge.values()):
        for cible in table_de_dispatch(v):
            out.append((None, cible, None, None))
    return out


def table_de_dispatch(v, mini=2, maxi=10):
    if not DONNEES(v) or not lisible(v, maxi * 4):
        return []
    out = []
    for k in range(maxi):
        c = u32(v + k * 4)
        if not CODE(c):
            break
        out.append(c)
    return out if len(out) >= mini else []


def champs(f, fin=0x200):
    """Le nombre de `mov.w @rM+,rN` de la boucle -- c'est la TAILLE du record."""
    return sum(1 for a in range(f, f + fin, 2) if (u16(a) & 0xF00F) == 0x6005)


def chargeur(f):
    """(tableA, tableB, taille) si `f` est un chargeur de bloc, sinon None."""
    r0 = None
    tA = tB = None
    for c in range(f, min(f + 0xA0, FIN_BIN - 2), 2):
        op = u16(c)
        if (op >> 12) == 0xD and ((op >> 8) & 0xF) == 0:
            r0 = litteral(c)
        elif (op & 0xF00F) == 0x000D and r0 is not None and tA is None:
            tA = r0
        elif (op & 0xF00F) == 0x000E and r0 is not None and tB is None:
            tB = r0
        if tA is not None and tB is not None:
            break
    if tA is None or tB is None or not DONNEES(tA) or not DONNEES(tB):
        return None
    return tA, reel(tB), champs(f) * 2


def contiguite(tA, tB, T, n=20):
    """Combien d'entrees verifient pointeur[i] + nombre[i]*T == pointeur[i+1]."""
    ok = tot = 0
    for k in range(n):
        if not lisible(tB + (k + 1) * 4) or not lisible(tA + k * 2, 2):
            continue
        p, q, c = u32(tB + k * 4), u32(tB + (k + 1) * 4), u16(tA + k * 2)
        if not (DONNEES(p) and DONNEES(q)) or c > 300:
            continue
        tot += 1
        if c and p + c * T == q:
            ok += 1
    return ok, tot


def aplati(deb, fin, profondeur=2):
    vues = set()
    out = list(appels(deb, fin))
    for _ in range(profondeur - 1):
        for _s, cible, _a, _b in list(out):
            if cible in vues:
                continue
            vues.add(cible)
            out += appels(cible, cible + 0x300)
    return out


def annuaire(k_table):
    """[(decor, aire, nombre, pointeur)] d'une table de la serie -- nombres a part."""
    t = SERIE + k_table * PAS_SERIE
    return [(d, a, u32(t + (d * 3 + a) * 4)) for d in range(NB_DECORS) for a in range(3)]


def main():
    print("NEW GENERATION -- les dix-neuf scripts d'etage (table %08X)\n" % TABLE_SCRIPTS)
    for deb, fin, d in sorted(scripts_detage(), key=lambda t: t[2]):
        print("   bande %2d  script %08X   (fin ~%08X)" % (d, deb, fin))

    vus = {}
    lignes = []
    for deb, fin, d in scripts_detage():
        for site, cible, a4, a5 in aplati(deb, fin, 3):
            f = chargeur(cible)
            if f is None:
                continue
            tA, tB, T = f
            for arg in [x for x in (a4, a5) if x is not None]:
                if not lisible(tA + arg * 2, 2) or not lisible(tB + arg * 4):
                    continue
                nb = u16(tA + arg * 2)
                bloc = u32(tB + arg * 4)
                if not DONNEES(bloc) or not (0 < nb <= 200):
                    continue
                if (d, bloc) in [(l[0], l[4]) for l in lignes]:
                    continue
                vus[cible] = (tA, tB, T)
                lignes.append((d, cible, arg, nb, bloc, site))

    print("\n%-6s %-10s %-4s %-4s %-10s %s"
          % ("bande", "chargeur", "arg", "nb", "bloc", "appele en"))
    for d, cible, arg, nb, bloc, site in sorted(lignes):
        print("  %2d   %08X   %-4d %-4d %08X   %s"
              % (d, cible, arg, nb, bloc, "%08X" % site if site else "(dispatch)"))

    print("\nLes chargeurs rencontres :")
    for f, (tA, tB, T) in sorted(vus.items()):
        ok, tot = contiguite(tA, tB, T)
        print("   %08X  nombres %08X  pointeurs %08X  %d octets/record  "
              "(%d/%d entrees contigues)" % (f, tA, tB, T, ok, tot))

    print("\nLA SERIE DE TABLES %08X, pas %02X (42 entrees = %d decors x 3 aires)"
          % (SERIE, PAS_SERIE, NB_DECORS))
    for k in range(12):
        t = SERIE + k * PAS_SERIE
        v = [u32(t + i * 4) for i in range(42)]
        print("   table %2d  %08X  %2d valeurs distinctes  %08X .. %08X"
              % (k, t, len(set(v)), min(v), max(v)))


if __name__ == "__main__":
    main()
