# -*- coding: utf-8 -*-
"""TOUT CE QUE LE BINAIRE DE NEW GENERATION DIT DE SES DECORS.

Le pendant de `chargeurs2i.py` + `annuaire2i.py` + `etages.py` pour `SF3_1ST.BIN`.
Chaque adresse ci-dessous a ete trouvee par la FORME puis validee par une contrainte
jointe ; le detail est dans `NEW-GENERATION.md`.

    python decorsng.py
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sh4ng as sh4

D, B = sh4.D, sh4.BASE
FIN = B + len(D)
u8 = lambda a: D[a - B]
u16 = lambda a: struct.unpack_from('<H', D, a - B)[0]
s16 = lambda a: struct.unpack_from('<h', D, a - B)[0]
u32 = lambda a: struct.unpack_from('<I', D, a - B)[0]

# --- les adresses etablies ------------------------------------------------------------
CONTEXTE = 0x8C552674          # +4 decor, +5 aire, +74 bande      (2I : 0x8C6AF304)
TABLE_ETAGES = 0x8C189178      # 19 entrees, lue en 0x8C085F88     (2I : 0x8C1D3FB4, 17)
NB_ETAGES = 19
TABLE_ETAGES2 = 0x8C1A2534     # 18 entrees, lue en 0x8C08D644     (second jeu)
SERIE = 0x8C4CC1F0             # image .data de la serie de tables (2I : 0x8C5F9B38)
PAS_SERIE = 0xA8               # 42 entrees = 14 decors x 3 aires  (2I : 0xCC = 51)
NB_DECORS = 14
BSS_LO, BSS_HI, DELTA = 0x8C4D7D00, 0x8C4EA000, 0x12420

NB_ELEMENTS = 0x8C1AEA24       # u16[(decor*3+aire)]   lue par 0x8C09C83C
PTR_ELEMENTS = SERIE + 1 * PAS_SERIE
NB_ELEMENTS2 = 0x8C1AEF30      # lue par 0x8C09CA14
PTR_ELEMENTS2 = SERIE + 2 * PAS_SERIE
TAILLE_ELEMENT = 18            # 9 x `mov.w @r14+` dans les deux lecteurs (2I : 16)

CHARGEURS = {                  # fonction : (nombres, pointeurs .bss, taille du record)
    0x8C0A1A40: (0x8C1B10D8, 0x8C4DE900, 34),
    0x8C0A21A4: (0x8C1B1120, 0x8C4DE908, 38),
}

TRANSFERTS = 0x8C1AAB7C        # entrees de 12 octets, lue par 0x8C095332
IDX_PALETTE = 0x8C18AC10       # index = u16[+ bande*2]            (2I : 0x8C1D5D38)
IDX_PALETTE2 = 0x8C18ABE4      # le second jeu (destination 0x12000)
PAL_RAM = 0x027B0000           # base RAM des palettes de NG. Le convertisseur
PAL_BIN = 0x8C1B8188           # RAM -> binaire est en 0x8C10E658 : bin = ram
                               # - 0x027B0000 + 0x8C1B8188 (offset fichier 0x1A8188)

PARALLAXE = 0x8C189BA0         # pas 0x20, indexee par la BANDE, lue en 0x8C088260
PAS_PARALLAXE = 0x20

ANIM_PAGES = 0x8C1B09C0        # k*20 : {plan, slot, suite, debut, fin}  lue en 0x8C09F2D4
ANIM_DEST = 0x8C1B061C         # k*2  : le decalage de destination       lue en 0x8C09F352
NB_ANIM = 11
SPAWNER_ANIM = 0x8C09F258

# etage -> routine de decor, et les entrees d'animation de pages que la routine demande
ANIM_PAR_ROUTINE = {0x8C089758: [1, 2, 3], 0x8C08ADBC: [9, 10, 4, 5, 6, 7, 8],
                    0x8C08B8B0: [0]}

# LE CHAINON QUI MANQUAIT : le decor n'est PAS la bande. Le code d'initialisation
# 0x8C088042 fait  `bande = u16[0x8C18A804 + (decor*3 + aire)*2]` puis l'ecrit en
# `ctx+74`. C'est la meme table qu'en 2I (0x8C1D591C), et elle explique du meme coup le
# « decalage d'index a partir de l'etage 10 » reste inexplique cote 2nd Impact.
DECOR_VERS_BANDE = 0x8C18A804


def reel(a):
    return a - DELTA if BSS_LO <= a < BSS_HI else a


def etages():
    return [u32(TABLE_ETAGES + k * 4) for k in range(NB_ETAGES)]


def bande(decor, aire=0):
    return u16(DECOR_VERS_BANDE + (decor * 3 + aire) * 2)


def routine(bande_):
    if not 0 <= bande_ < NB_ETAGES:
        return None
    return u32(TABLE_ETAGES + bande_ * 4)


def decor_de_routine():
    """routine -> [decors], par la table decor->bande et la table des etages."""
    out = {}
    for d in range(NB_DECORS):
        for a in range(3):
            r = routine(bande(d, a))
            if r is not None:
                out.setdefault(r, set()).add(d)
    return out


def element(a):
    """{plan, drapeaux, x, y, palette, script} d'un enregistrement (le pointeur de
    l'annuaire vaut deux octets AVANT le champ `plan`, comme en 2I)."""
    return dict(plan=u16(a), drap=u16(a + 2), x=s16(a + 4), y=s16(a + 6),
                pal=u16(a + 8), script=u16(a + 10),
                q=(u16(a + 12), u16(a + 14), u16(a + 16)))


def bloc_elements(tnb, tptr, decor, aire):
    n = u16(tnb + (decor * 3 + aire) * 2)
    p = u32(tptr + (decor * 3 + aire) * 4)
    return n, p, [element(p + 2 + k * TAILLE_ELEMENT) for k in range(n)]


def palette(bande, table=IDX_PALETTE):
    idx = u16(table + bande * 2)
    a = TRANSFERTS + idx * 12
    src, dst, taille = u32(a), u32(a + 4), u32(a + 8)
    return idx, src, dst, taille, (src - PAL_RAM) // 128, taille // 128


def coefs(bande, k):
    a = PARALLAXE + bande * PAS_PARALLAXE + k * 8
    return u32(a), u32(a + 4)


def main():
    rout = decor_de_routine()
    print("== 1. LES DIX-NEUF BANDES (table %08X, memcpy de 76 octets en 0x8C085F8C) =="
          % TABLE_ETAGES)
    print("%-6s %-10s %-12s %-6s %-24s %s"
          % ("bande", "script", "decor(aire)", "palidx", "palette (nb, base)",
             "parallaxe obj0"))
    for b in range(NB_ETAGES):
        r = u32(TABLE_ETAGES + b * 4)
        idx, src, dst, t, base, nb = palette(b)
        idx2, _s2, _d2, _t2, base2, nb2 = palette(b, IDX_PALETTE2)
        cx, cy = coefs(b, 0)
        qui = ",".join("%d(%d)" % (d, a) for d in range(NB_DECORS) for a in range(3)
                       if bande(d, a) == b)
        print("  %2d   %08X   %-12s %-6d %-24s %.4g / %.4g"
              % (b, r, qui, idx, "%d a %d puis %d a %d" % (nb, base, nb2, base2),
                 cx / 65536.0, cy / 65536.0))

    print("\n== 2. LES QUATORZE DECORS, LEURS BANDES ET LEURS ELEMENTS ==")
    print("%-6s %-12s %-10s %-24s %s"
          % ("decor", "bandes", "script", "jeu 1 (nb@bloc)", "jeu 2 (nb@bloc)"))
    for d in range(NB_DECORS):
        l1, l2 = [], []
        for a in range(3):
            n1, p1, _ = bloc_elements(NB_ELEMENTS, PTR_ELEMENTS, d, a)
            n2, p2, _ = bloc_elements(NB_ELEMENTS2, PTR_ELEMENTS2, d, a)
            l1.append("%d@%08X" % (n1, p1))
            l2.append("%d@%08X" % (n2, p2))
        uni = lambda L: " ".join(sorted(set(L), key=L.index))
        bs = [bande(d, a) for a in range(3)]
        rs = sorted({routine(x) for x in bs} - {None})
        print("  %2d   %-12s %-10s %-24s %s"
              % (d, "/".join(str(x) for x in bs),
                 " ".join("%08X" % x for x in rs)[:10], uni(l1), uni(l2)))

    print("\n== 3. LES ELEMENTS, AIRE 0, JEU 1 ==")
    for d in range(NB_DECORS):
        n, p, recs = bloc_elements(NB_ELEMENTS, PTR_ELEMENTS, d, 0)
        if not n:
            continue
        print("  decor %2d  bloc %08X  %d elements" % (d, p, n))
        for e in recs:
            print("      plan %d  drap %5d  x %5d  y %4d  pal %3d  script %3d"
                  % (e['plan'], e['drap'], e['x'], e['y'], e['pal'], e['script']))

    print("\n== 4. LES DEUX CHARGEURS A TABLE ==")
    for f, (tA, tB, T) in sorted(CHARGEURS.items()):
        t = reel(tB)
        print("  %08X  nombres %08X  pointeurs %08X (.bss %08X)  %d octets/record"
              % (f, tA, t, tB, T))
        for k in range(10):
            n, p = u16(tA + k * 2), u32(t + k * 4)
            if not (0x8C0F0000 <= p < FIN):
                break
            q = u32(t + (k + 1) * 4)
            mark = "  contigu" if (0x8C0F0000 <= q < FIN and p + n * T == q) else ""
            print("     arg %-2d  nb %-4d bloc %08X%s" % (k, n, p, mark))

    print("\n== 5. L'ANIMATION DE PAGES (%08X, %d entrees ; destinations %08X) =="
          % (ANIM_PAGES, NB_ANIM, ANIM_DEST))
    par_etage = {}
    for r, ks in ANIM_PAR_ROUTINE.items():
        for b in range(NB_ETAGES):
            if u32(TABLE_ETAGES + b * 4) == r:
                par_etage.setdefault(b, []).extend(ks)
    for k in range(NB_ANIM):
        a = ANIM_PAGES + k * 20
        plan, slot, suite, deb, fin = struct.unpack_from('<5I', D, a - B)
        dec = u16(ANIM_DEST + k * 2)
        i = dec // 4
        qui = [b for b, ks in par_etage.items() if k in ks]
        pa = []
        p = suite
        while s16(p) >= 0 and len(pa) < 40:
            pa.append((s16(p), s16(p + 2)))
            p += 4
        print("  %2d  plan %d slot %d  dest %5d -> bloc %4d (x %3d, y %3d)  %d images  "
              "etages %s" % (k, plan, slot, dec, i, (i % 64) * 16, (i // 64) * 16,
                             len(pa), qui))

    print("\n== 6. LA PARALLAXE, PAR BANDE (%08X, pas %02X) ==" % (PARALLAXE, PAS_PARALLAXE))
    print("%-6s %s" % ("bande", "objets 0 a 3 (coef x / coef y)"))
    for b in range(NB_ETAGES):
        v = []
        for k in range(4):
            cx, cy = coefs(b, k)
            v.append("%.4g/%.4g" % (cx / 65536.0, cy / 65536.0))
        print("  %2d   %s" % (b, "   ".join(v)))


if __name__ == "__main__":
    main()
