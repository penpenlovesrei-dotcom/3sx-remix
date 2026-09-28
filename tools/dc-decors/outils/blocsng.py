# -*- coding: utf-8 -*-
"""LE GRAPHE DES BLOCS DE DECOR DE NEW GENERATION -- qui charge quoi, et pour qui.

`chargeursng.py` suivait le modele de 2nd Impact : un script d'etage appelle un chargeur
avec `mov #arg,r4`. Sur NG ca ne rend qu'une attribution sur quatorze, et la raison se lit
dans le code : **l'argument n'est presque jamais une constante**. Il vient
    * d'un CHAMP de l'objet appelant  (`u16[objet + 62]`, `u16[objet + 52]`), ou
    * du FLUX du bloc en cours de lecture (`mov.w @r13,r5` dans la boucle d'un chargeur).

Autrement dit les blocs forment un ARBRE : un enregistrement charge nomme le bloc suivant.
Le sommet de l'arbre, lui, est bien appele par la routine de decor -- et c'est lui qui
donne l'appartenance.

Ce que fait cet outil :
  1. il recense tous les LECTEURS DE BLOCS (une boucle de `mov.w @rM+,rN`), et pour
     chacun d'ou vient son bloc : litteral en dur, ou `tableB[arg]` ;
  2. il releve, pour chaque lecteur, a quel offset d'objet part chaque champ -- c'est ce
     qui identifie les champs « index du bloc suivant » ;
  3. il part des quatorze routines de decor et propage : constante -> bloc, puis champ
     d'enregistrement -> bloc, jusqu'a saturation ;
  4. il verifie chaque attribution par une contrainte JOINTE, independante du chemin :
     les x des enregistrements doivent tenir dans la largeur du decor, et leur champ de
     palette sous le nombre de palettes que la bande charge.

    python blocsng.py
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sh4ng as sh4
import decorsng as N

D, B = sh4.D, sh4.BASE
FIN = B + len(D)
u16 = lambda a: struct.unpack_from('<H', D, a - B)[0]
s16 = lambda a: struct.unpack_from('<h', D, a - B)[0]
u32 = lambda a: struct.unpack_from('<I', D, a - B)[0]

lisible = lambda a, n=4: B <= a and a + n <= FIN
CODE = lambda v: 0x8C010000 <= v < 0x8C0F0000
DONNEES = lambda v: 0x8C0F0000 <= v < FIN
BLOCS = lambda v: 0x8C110000 <= v < 0x8C1C0000

CODE_LO, CODE_HI = 0x8C010000, 0x8C0F0000


def litteral(pc):
    op = u16(pc)
    if (op >> 12) != 0xD:
        return None
    pool = (pc & ~3) + 4 + (op & 0xFF) * 4
    return u32(pool) if lisible(pool) else None


def fonctions():
    """Les debuts de fonction : cibles de jsr/jmp par litteral, plus les bsr."""
    deb = set()
    charge = {}
    for c in range(CODE_LO, CODE_HI - 2, 2):
        op = u16(c)
        if (op >> 12) == 0xD:
            v = litteral(c)
            if v is not None:
                charge[(op >> 8) & 0xF] = v
        elif (op & 0xF0FF) in (0x400B, 0x402B):
            v = charge.get((op >> 8) & 0xF)
            if v is not None and CODE(v):
                deb.add(v)
        elif (op >> 12) == 0xB:
            d = op & 0xFFF
            if d & 0x800:
                d -= 0x1000
            t = c + 4 + d * 2
            if CODE(t):
                deb.add(t)
    return sorted(deb)


def champs(f, fin):
    """[(rang, offset objet)] : chaque `mov.w @rM+,rN` et le store qui le suit."""
    out = []
    r0 = None
    k = 0
    a = f
    while a < fin:
        w = u16(a)
        if (w & 0xFF00) == 0xE000:
            r0 = w & 0xFF
            r0 -= 0x100 if r0 > 0x7F else 0
        elif (w >> 12) == 0x9 and ((w >> 8) & 0xF) == 0:
            r0 = s16(a + 4 + (w & 0xFF) * 2)
        elif (w >> 12) == 0x7 and ((w >> 8) & 0xF) == 0:
            i = w & 0xFF
            i -= 0x100 if i > 0x7F else 0
            if r0 is not None:
                r0 += i
        elif (w & 0xF00F) == 0x6005:
            dest = None
            for p in range(a + 2, a + 0x18, 2):
                v = u16(p)
                if (v & 0xFF00) == 0xE000:
                    r0 = v & 0xFF
                    r0 -= 0x100 if r0 > 0x7F else 0
                elif (v >> 12) == 0x9 and ((v >> 8) & 0xF) == 0:
                    r0 = s16(p + 4 + (v & 0xFF) * 2)
                elif (v >> 12) == 0x7 and ((v >> 8) & 0xF) == 0:
                    i = v & 0xFF
                    i -= 0x100 if i > 0x7F else 0
                    if r0 is not None:
                        r0 += i
                elif (v & 0xF00F) == 0x0005:
                    dest = r0
                    break
                elif (v & 0xFF00) == 0x8100:
                    dest = (v & 0xF) * 2
                    break
            out.append((k, dest))
            k += 1
        a += 2
    return out


def lecteur(f, portee=0x220):
    """La fiche d'un lecteur de blocs, ou None.

    { 'tA', 'tB', 'dur', 'taille', 'champs' }  --  `tB` est deja ramene a son image
    lisible dans le fichier (voir `decorsng.reel`).
    """
    ch = champs(f, f + portee)
    if len(ch) < 4:
        return None
    r0 = None
    tA = tB = dur = None
    for c in range(f, min(f + 0xB0, FIN - 2), 2):
        op = u16(c)
        if (op >> 12) == 0xD:
            v = litteral(c)
            if v is None:
                continue
            if ((op >> 8) & 0xF) == 0:
                r0 = v
            elif BLOCS(v) and dur is None:
                dur = v
        elif (op & 0xF00F) == 0x000D and r0 is not None and tA is None and DONNEES(r0):
            tA = r0
        elif (op & 0xF00F) == 0x000E and r0 is not None and tB is None and DONNEES(r0):
            tB = r0
    if tB is None and dur is None:
        return None
    return dict(f=f, tA=tA, tB=N.reel(tB) if tB else None, dur=dur,
                taille=len(ch) * 2, champs=ch)


def appels(deb, fin):
    """[(site, cible, source de l'argument)] -- la source est ce qui compte ici.

    'const:N'       mov #N,r4/r5
    'objet+N'       mov.w @(N,objet),r5   -- l'index vient d'un champ de l'appelant
    'flux'          mov.w @r13,r5         -- l'index vient du bloc en cours de lecture
    None            indetermine
    """
    charge = {}
    out = []
    for c in range(deb, min(fin, FIN - 2), 2):
        op = u16(c)
        if (op >> 12) == 0xD:
            v = litteral(c)
            if v is not None:
                charge[(op >> 8) & 0xF] = v
        elif (op & 0xF0FF) in (0x400B, 0x402B) or (op >> 12) == 0xB:
            if (op >> 12) == 0xB:
                d = op & 0xFFF
                d -= 0x1000 if d & 0x800 else 0
                cible = c + 4 + d * 2
            else:
                cible = charge.get((op >> 8) & 0xF)
            if cible is None or not CODE(cible):
                continue
            out.append((c, cible, source_arg(c)))
    return out


def source_arg(site):
    """D'ou vient r5 (ou r4) au moment du saut."""
    r0 = None
    for p in [site + 2] + [site - 2 * k for k in range(1, 12)]:
        if p < B or p + 2 > FIN:
            continue
        w = u16(p)
        if (w & 0xFF00) == 0xE000:
            r0 = w & 0xFF
        elif (w >> 12) == 0x9 and ((w >> 8) & 0xF) == 0:
            r0 = u16(p + 4 + (w & 0xFF) * 2)
        elif (w & 0xFF00) in (0xE400, 0xE500):      # mov #imm,r4 / r5
            return ('const', w & 0xFF)
        elif (w & 0xF0FF) in (0x050D, 0x040D) and r0 is not None:
            return ('objet', r0)                    # mov.w @(r0,rN),r4/r5
        elif w in (0x6551, 0x6451, 0x65D1, 0x64D1): # mov.w @rN,r5 / @r13,r5
            return ('flux', None)
    return (None, None)



# ----------------------------------------------------------------------------------------
# LES LECTEURS INDEXES PAR L'ARGUMENT -- formules relevees a la main dans chaque fonction.
#
# Seuls ceux-la sont ATTRIBUABLES : leur bloc depend de l'argument que la routine de decor
# leur passe. Les autres portent un bloc en dur, le meme pour tous leurs appelants, et
# l'argument qu'on croit leur voir passer est en realite ecrase par le `mov #4,r4` du
# delay slot de leur appel a l'allocateur -- piege verifie sur 0x8C0A0C20 et 0x8C0B253C.
#
#   z = u8[contexte + 6], un compteur qui tourne sur 0..3 (0x8C085F5E fait `and #3`),
#   pose juste avant le dispatcher des scripts d'etage. Chaque couple (lecteur, arg) porte
#   donc QUATRE blocs, un par valeur de z.
INDEXES = {
    0x8C0A0070: dict(nb=0x8C1B0D58, ptr=0x8C4CC41C, pas_nb=8, pas_ptr=16, z=True, T=24),
    0x8C0AC75C: dict(nb=0x8C1B2E38, ptr=0x8C4CC62C, pas_nb=8, pas_ptr=16, z=True, T=18),
    0x8C0AC934: dict(nb=0x8C1B2F18, ptr=0x8C4CC67C, pas_nb=8, pas_ptr=16, z=True, T=18),
    0x8C0A21A4: dict(nb=0x8C1B1120, ptr=0x8C4CC4E8, pas_nb=2, pas_ptr=4, z=False, T=38),
    0x8C0A1A40: dict(nb=0x8C1B10D8, ptr=0x8C4CC4E0, pas_nb=2, pas_ptr=4, z=False, T=34),
    0x8C0A1318: dict(nb=None, ptr=0x8C4CC484, pas_ptr=4, z=False, T=32, un=1),
    0x8C0A7B9A: dict(nb=None, ptr=0x8C4CC53C, pas_ptr=4, z=False, T=16, un=1),
    0x8C0A8EE4: dict(nb=None, dur=0x8C1B2638, pas_ptr=24, z=False, T=24, un=1),
}

# Les lecteurs qui IGNORENT leur argument : leur bloc est le meme pour tout le monde.
GENERIQUES = {0x8C0A0C20: 0x8C1B0FF4, 0x8C0B253C: 0x8C1B33B4,
              0x8C09C83C: None, 0x8C09CA14: None}

FIN_ROUTINES = 0x8C08C7BE     # la derniere routine de decor s'arrete la
TABLE_ETAGES, NB_ETAGES = 0x8C189178, 19


def bloc(f, arg, z=0):
    """(nombre, pointeur) d'un lecteur indexe, ou (None, pointeur) s'il n'en charge qu'un."""
    d = INDEXES[f]
    if d.get('dur'):
        return d.get('un'), d['dur'] + arg * d['pas_ptr']
    p = u32(d['ptr'] + arg * d['pas_ptr'] + (z * 4 if d['z'] else 0))
    if d['nb'] is None:
        return d.get('un'), p
    n = u16(d['nb'] + arg * d['pas_nb'] + (z * 2 if d['z'] else 0))
    return n, p


def routines():
    """[(routine, debut, fin)] -- bornees les unes par les autres."""
    r = sorted({u32(TABLE_ETAGES + b * 4) for b in range(NB_ETAGES)})
    return [(a, a, r[i + 1] if i + 1 < len(r) else FIN_ROUTINES) for i, a in enumerate(r)]


def contiguite(f, args, z):
    """pointeur + nombre*T == pointeur suivant ? -- l'epreuve jointe."""
    d = INDEXES[f]
    ok = tot = 0
    for a in args:
        n, p = bloc(f, a, z)
        n2, q = bloc(f, a + 1, z)
        if n is None or not DONNEES(p) or not DONNEES(q) or n > 300:
            continue
        tot += 1
        if n and p + n * d['T'] == q:
            ok += 1
    return ok, tot


# Ou se lisent x et y dans l'enregistrement de chaque lecteur (octet DEPUIS LE POINTEUR),
# releve par `champs()` : le champ qui part en objet+102 est x, celui qui part en
# objet+106 est y.
#
# ATTENTION -- le `+2` de l'annuaire des elements ne vaut QUE pour l'annuaire. Le pointeur
# d'un bloc vise le champ 0 (qui part en objet+32) ; pour l'annuaire, l'usage de 2nd
# Impact appelle `pointeur+2` le debut du record, ce qui designe le champ 1. Appliquer ce
# `+2` aux autres lecteurs decale tout d'un champ : la premiere version de l'epreuve 2
# lisait les y comme des x et les palettes comme des y, et annoncait des x de 16 a 512
# alors qu'ils vont de -305 a 854.
XY = {0x8C0A0070: (6, 8), 0x8C0A1318: (6, 8), 0x8C0A7B9A: (6, 8), 0x8C0A8EE4: (6, 8),
      0x8C0AC75C: (6, 8), 0x8C0AC934: (6, 8), 0x8C0A21A4: (4, 6), 0x8C0A1A40: (8, 10)}


def tous_les_blocs(f, args):
    """{pointeur : nombre} pour les couples (arg, z) REELLEMENT attribues.

    On ne mesure que ce qu'on affirme : elargir aux arguments que personne ne passe
    ramenerait des entrees de table hors service, et l'epreuve n'en dirait plus rien.
    """
    out = {}
    d = INDEXES[f]
    for a in args:
        for z in (range(4) if d['z'] else [0]):
            n, p = bloc(f, a, z)
            if DONNEES(p) and n is not None and n <= 300:
                out[p] = max(out.get(p, 0), n)
    return out


def main():
    print("== 1. LES LECTEURS DE BLOCS INDEXES PAR L'ARGUMENT ==\n")
    print("%-10s %-10s %-10s %-7s %s"
          % ("lecteur", "nombres", "pointeurs", "record", "indexation"))
    for f, d in sorted(INDEXES.items()):
        print("  %08X %-10s %-10s %-7d %s"
              % (f, "%08X" % d['nb'] if d['nb'] else "-",
                 "%08X" % (d.get('ptr') or d['dur']), d['T'],
                 "(arg, z)" if d['z'] else
                 ("(arg), un seul enregistrement" if d.get('un') else "(arg)")))

    print("\n== 2. L'ATTRIBUTION, PAR L'APPELANT ET LUI SEUL ==")
    print("   appels pris DANS le corps de la routine de decor, profondeur 1\n")
    par_routine = {}
    for r, a, b in routines():
        par_routine[r] = sorted({(c, v, s) for s, c, (k, v) in appels(a, b)
                                 if c in INDEXES and k == 'const'})

    for r, a, b in routines():
        ds = sorted({d for d in range(N.NB_DECORS) for k in range(3)
                     if N.routine(N.bande(d, k)) == r})
        bs = sorted({N.bande(d, k) for d in range(N.NB_DECORS) for k in range(3)
                     if N.routine(N.bande(d, k)) == r})
        print("decor %-8s bande %-10s routine %08X"
              % (",".join(map(str, ds)), ",".join(map(str, bs)), r))
        if not par_routine[r]:
            print("      aucun bloc a chargeur -- ce decor n'a que ses elements")
        for c, v, site in par_routine[r]:
            if INDEXES[c]['z']:
                q = ["%s@%08X" % bloc(c, v, z) for z in range(4)]
                print("      %08X arg %-2d (appel %08X)  z0..3 : %s"
                      % (c, v, site, "  ".join(q)))
            else:
                n, p = bloc(c, v)
                print("      %08X arg %-2d (appel %08X)  %s@%08X"
                      % (c, v, site, n, p))

    args_par_lecteur = {}
    for r in par_routine:
        for c, v, _s in par_routine[r]:
            args_par_lecteur.setdefault(c, set()).add(v)
    # Les blocs atteints par l'ARBRE comptent aussi : ils viennent de la meme chaine,
    # un cran plus loin.
    for c, v in [(c, v) for r in par_routine for c, v, _ in par_routine[r]
                 if c == 0x8C0A1318]:
        _n, p = bloc(c, v)
        iB, iA = u16(p + 18), s16(p + 30)
        if iB != 0xFFFF:
            args_par_lecteur.setdefault(0x8C0A21A4, set()).add(iB)
        if 0 <= iA < 8:
            args_par_lecteur.setdefault(0x8C0A1A40, set()).add(iA)
            iB2 = u16(bloc(0x8C0A1A40, iA)[1] + 32)
            if iB2 != 0xFFFF:
                args_par_lecteur.setdefault(0x8C0A21A4, set()).add(iB2)

    print("\n== 3. EPREUVE JOINTE 1 : LA TABLE SE VALIDE-T-ELLE ELLE-MEME ? ==")
    print("   Les blocs, TRIES PAR ADRESSE, doivent se toucher :")
    print("   pointeur + nombre x taille == pointeur suivant.")
    print("   (Le tri est par adresse et non par argument : le sous-index z entrelace")
    print("    les couples, donc l'ordre des arguments n'est pas l'ordre memoire.)\n")
    for f in sorted(INDEXES):
        if INDEXES[f]['nb'] is None or f not in args_par_lecteur:
            continue
        T = INDEXES[f]['T']
        b = tous_les_blocs(f, args_par_lecteur[f])
        cl = sorted(b)
        ok = tot = 0
        for i in range(len(cl) - 1):
            if b[cl[i]] == 0:
                continue
            tot += 1
            if cl[i] + b[cl[i]] * T == cl[i + 1]:
                ok += 1
        print("   %08X  %d octets/record  %d/%d blocs contigus  (%d blocs distincts, "
              "%08X .. %08X)" % (f, T, ok, tot, len(cl), cl[0], cl[-1]))

    print("\n== 4. EPREUVE JOINTE 2 : LES POSITIONS SONT-ELLES PLAUSIBLES ? ==")
    print("   x et y bruts. Les blocs du chargeur B (0x8C0A21A4) sont RELATIFS a leur")
    print("   parent : leurs x negatifs sont normaux, voir NEW-GENERATION.md 9.3.")
    for f in sorted(INDEXES):
        if f not in args_par_lecteur:
            continue
        ox, oy = XY[f]
        T = INDEXES[f]['T']
        b = tous_les_blocs(f, args_par_lecteur[f])
        xs = []
        ys = []
        for p, n in b.items():
            if not n:
                continue
            for k in range(n or 1):
                a = p + k * T
                if not lisible(a + oy + 2, 2):
                    continue
                xs.append(s16(a + ox))
                ys.append(s16(a + oy))
        if not xs:
            continue
        hors = sum(1 for x, y in zip(xs, ys)
                   if not (-600 <= x <= 1400 and -400 <= y <= 1400))
        print("   %08X  %3d enregistrements   x %5d..%-5d  y %5d..%-5d   hors plage : %d"
              % (f, len(xs), min(xs), max(xs), min(ys), max(ys), hors))

    print("\n== 5. L'ARBRE : UN ENREGISTREMENT NOMME LE BLOC SUIVANT ==\n")
    print("   0x8C0A1318 : champ  9 (octets 18-19) -> objet+52 -> chargeur B")
    print("                champ 15 (octets 30-31) -> chargeur A, si >= 0")
    print("   0x8C0A1A40 : champ 16 (octets 32-33) -> objet+62 -> chargeur B\n")
    for r, a, b in routines():
        for c, v, site in par_routine[r]:
            if c != 0x8C0A1318:
                continue
            _n, p = bloc(c, v)
            iB, iA = u16(p + 18), s16(p + 30)
            ds = ",".join(str(d) for d in range(N.NB_DECORS) for k in range(3)
                          if N.routine(N.bande(d, k)) == r and k == 0)
            if iB == 0xFFFF:
                ligne = ("   decor %-5s 1318 arg %d = %08X  ->  aucun bloc B (-1)"
                         % (ds, v, p))
            else:
                nB, pB = bloc(0x8C0A21A4, iB)
                ligne = ("   decor %-5s 1318 arg %d = %08X  ->  B arg %d = %s@%08X"
                         % (ds, v, p, iB, nB, pB))
            if 0 <= iA < 8:
                nA, pA = bloc(0x8C0A1A40, iA)
                iB2 = u16(pA + 32)
                ligne += "  |  A arg %d = %s@%08X" % (iA, nA, pA)
                if iB2 != 0xFFFF:
                    nB2, pB2 = bloc(0x8C0A21A4, iB2)
                    ligne += " -> B arg %d = %s@%08X" % (iB2, nB2, pB2)
            print(ligne)


if __name__ == "__main__":
    main()
