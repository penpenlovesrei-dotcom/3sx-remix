# -*- coding: utf-8 -*-
"""QUELS APPELS UNE ROUTINE D'ETAGE FAIT VRAIMENT, pour une aire et un tirage donnes.

POURQUOI -- 16/09/2026
----------------------
Une routine de New Generation sert souvent PLUSIEURS bandes et choisit ses objets en
lisant le contexte : `u8[contexte + 5]` (l'aire) ou `u8[contexte + 6]` (le tirage `z`).
Celle de Yun (`0x8C089B1C`) pose la rue a l'aire 0 (bande 5) et le temple aux aires 1-2
(bande 6) ; celle de Yang fait l'inverse. `routineng.py` liste TOUS les appels, sans dire
lesquels s'executent : c'est ainsi que l'etage 55 recevait les objets de la rue.

COMMENT
-------
Une exploration des chemins, a la maniere d'un interprete abstrait tres petit :

  * un registre charge par `mov.l` avec l'adresse du contexte est suivi ; un
    `mov.b @(d,rN),r0` sur lui donne la valeur connue de l'octet `d` (4 decor, 5 aire,
    6 tirage) ;
  * `tst r0,r0`, `cmp/eq #k,r0`, `tst #k,r0` posent le bit T quand r0 est connu ;
  * `bt`/`bf` sur un T connu ne suivent qu'une branche, sinon les deux ;
  * `bra` saute, `rts` et `jmp` terminent ; chaque adresse n'est visitee qu'une fois par
    etat de registres connus.

Les appels (`jsr @rN` sur un litteral) atteints sont rendus avec leur r4 constant.

    python cheminng.py 5       ce que la bande 5 appelle, pour chaque z
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sh4ng as sh4
import decorsng as N

D, B = sh4.D, sh4.BASE
u16 = lambda a: struct.unpack_from('<H', D, a - B)[0]
u32 = lambda a: struct.unpack_from('<I', D, a - B)[0]
CONTEXTE = N.CONTEXTE


def litteral(pc):
    w = u16(pc)
    return u32((pc & ~3) + 4 + (w & 0xFF) * 4)


def s8(v):
    return v - 256 if v > 127 else v


def explorer(deb, fin, octets, plafond=6000):
    """{(site, cible, r4)} atteints depuis `deb` sans sortir de [deb, fin[.

    `octets` : {deplacement dans le contexte : valeur}, par exemple {5: 0, 6: 2}.
    """
    appels = set()
    vus = set()
    pile = [(deb, (), None, None)]      # pc, registres connus (tuple), T, r4
    pas = 0

    while pile and pas < plafond:
        pc, reg, t, r4 = pile.pop()
        cle = (pc, reg, t, r4)
        if cle in vus or not deb <= pc < fin:
            continue
        vus.add(cle)
        pas += 1
        r = dict(reg)
        w = u16(pc)
        h, n, m = w >> 12, (w >> 8) & 0xF, (w >> 4) & 0xF
        suivant = pc + 2

        def poser(k, v):
            if v is None:
                r.pop(k, None)
            else:
                r[k] = v

        if h == 0xD:                                     # mov.l @(d,pc),rn
            poser(n, ("l", litteral(pc)))
        elif h == 0xE:                                   # mov #imm,rn
            poser(n, ("k", s8(w & 0xFF)))
            if n == 4:
                r4 = s8(w & 0xFF)
        elif h == 0x9:                                   # mov.w @(d,pc),rn
            poser(n, ("k", u16(pc + 4 + (w & 0xFF) * 2)))
        elif (w & 0xF00F) == 0x6003:                     # mov rm,rn
            poser(n, r.get(m))
        elif (w & 0xFF00) == 0x8400:                     # mov.b @(d,rm),r0
            base = r.get((w >> 4) & 0xF)
            d = w & 0xF
            if base == ("l", CONTEXTE) and d in octets:
                poser(0, ("k", octets[d]))
            else:
                poser(0, None)
        elif (w & 0xF00F) == 0x6000:                     # mov.b @rm,rn
            base = r.get(m)
            if base == ("l", CONTEXTE + 5) or (base and base[0] == "l" and base[1] - CONTEXTE in octets):
                poser(n, ("k", octets[base[1] - CONTEXTE]))
            else:
                poser(n, None)
        elif (w & 0xF00F) == 0x2008 and n == m:          # tst rn,rn
            v = r.get(n)
            t = (v[1] == 0) if v and v[0] == "k" else None
        elif (w & 0xFF00) == 0x8800:                     # cmp/eq #imm,r0
            v = r.get(0)
            t = (v[1] == s8(w & 0xFF)) if v and v[0] == "k" else None
        elif (w & 0xFF00) == 0xC800:                     # tst #imm,r0
            v = r.get(0)
            t = ((v[1] & (w & 0xFF)) == 0) if v and v[0] == "k" else None
        elif (w & 0xF00F) == 0x3000:                     # cmp/eq rm,rn
            a, b = r.get(m), r.get(n)
            t = (a[1] == b[1]) if a and b and a[0] == b[0] == "k" else None
        elif (w & 0xFF00) in (0x8900, 0x8B00, 0x8D00, 0x8F00):   # bt bf bt/s bf/s
            d = s8(w & 0xFF)
            cible = pc + 4 + d * 2
            si_t = (w & 0xFF00) in (0x8900, 0x8D00)
            lent = (w & 0xFF00) in (0x8D00, 0x8F00)
            # le creneau d'un bt/s ou bf/s s'execute dans les deux cas : on l'approche en
            # l'ignorant, il ne porte presque jamais d'appel
            if t is None:
                pile.append((cible, tuple(sorted(r.items())), None, r4))
                pile.append((pc + (4 if lent else 2), tuple(sorted(r.items())), None, r4))
            else:
                prise = t if si_t else not t
                pile.append(((cible if prise else pc + (4 if lent else 2)),
                             tuple(sorted(r.items())), t, r4))
            continue
        elif (w & 0xF000) == 0xA000:                     # bra
            d = w & 0xFFF
            d = d - 0x1000 if d & 0x800 else d
            # le creneau d'abord : il peut poser r4
            w2 = u16(pc + 2)
            if (w2 & 0xFF00) == 0xE400:
                r4 = s8(w2 & 0xFF)
            pile.append((pc + 4 + d * 2, tuple(sorted(r.items())), t, r4))
            continue
        elif (w & 0xF0FF) in (0x400B, 0x402B):           # jsr / jmp
            v = r.get(n)
            w2 = u16(pc + 2)
            arg = s8(w2 & 0xFF) if (w2 & 0xFF00) == 0xE400 else r4
            if v and v[0] == "l":
                appels.add((pc, v[1], arg))
            if (w & 0xF0FF) == 0x402B:
                continue
            # apres un appel, r0..r7 sont perdus
            for k in range(8):
                r.pop(k, None)
            r4 = None
            t = None
            suivant = pc + 4
        elif w == 0x000B:                                # rts
            continue
        elif (w & 0xF000) == 0xB000:                     # bsr : on ne suit pas
            suivant = pc + 4
            for k in range(8):
                r.pop(k, None)
        else:
            # toute autre ecriture de registre le rend inconnu
            if h in (0x6, 0x5, 0x7, 0x3, 0x0, 0x4, 0xC):
                if h == 0x7:
                    v = r.get(n)
                    poser(n, ("k", v[1] + s8(w & 0xFF)) if v and v[0] == "k" else
                          ("l", v[1] + s8(w & 0xFF)) if v and v[0] == "l" else None)
                elif h in (0x6, 0x5, 0x3):
                    poser(n, None)
                elif h == 0xC:
                    poser(0, None)
                elif h == 0x0 and (w & 0xF) in (0xC, 0xD, 0xE):
                    poser(n, None)

        pile.append((suivant, tuple(sorted(r.items())), t, r4))

    return appels


def bornes(bande):
    t = sorted(set(u32(N.TABLE_ETAGES + k * 4) for k in range(N.NB_ETAGES)))
    deb = u32(N.TABLE_ETAGES + bande * 4)
    suiv = [a for a in t if a > deb]
    return deb, (suiv[0] if suiv else deb + 0x800)


def aires_de_bande(bande):
    """[(decor, aire)] qui menent a cette bande (`0x8C18A804`)."""
    out = []
    for d in range(N.NB_DECORS):
        for aire in range(3):
            if u16(0x8C18A804 + (d * 3 + aire) * 2) == bande:
                out.append((d, aire))
    return out


_ENTREES = {}


def entrees(deb, fin):
    """Les points d'entree de la routine : son debut, et toute adresse de [deb, fin[ que
    le binaire designe par un pointeur (les etats de la routine sont appeles par table)."""
    if (deb, fin) not in _ENTREES:
        pts = {deb}
        for o in range(0, len(D) - 4, 4):
            v = struct.unpack_from('<I', D, o)[0]
            if deb < v < fin and not v & 1:
                pts.add(v)
        _ENTREES[(deb, fin)] = sorted(pts)
    return _ENTREES[(deb, fin)]


def explorer_bande(bande, decor, aire, z):
    """Les appels de la routine de `bande` pour UN decor, UNE aire, UN tirage."""
    deb, fin = bornes(bande)
    tout = set()
    for e in entrees(deb, fin):
        tout |= explorer(e, fin, {4: decor, 5: aire, 6: z})
    return tout


def appels_de_bande(bande, z):
    deb, fin = bornes(bande)
    tout = set()
    for d, aire in aires_de_bande(bande):
        for e in entrees(deb, fin):
            tout |= explorer(e, fin, {4: d, 5: aire, 6: z})
    return tout


def main():
    bandes = [int(a) for a in sys.argv[1:]] or list(range(N.NB_ETAGES))
    for b in bandes:
        par_z = {z: appels_de_bande(b, z) for z in range(4)}
        tous = sorted(set().union(*par_z.values()))
        print("BANDE %d  %s" % (b, aires_de_bande(b)))
        for site, cible, arg in tous:
            zs = "".join(str(z) for z in range(4) if (site, cible, arg) in par_z[z])
            print("   %08X -> %08X r4=%s  z %s" % (site, cible, arg, zs))


if __name__ == "__main__":
    main()
