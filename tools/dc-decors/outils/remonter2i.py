# -*- coding: utf-8 -*-
"""QUI ATTEINT CETTE FONCTION, ET DEPUIS QUEL DECOR ? — le graphe d'appels A L'ENVERS.

LE PROBLEME
-----------
`effets2i.py` trouve trente-deux spawners qui lisent un bloc, et quatre seulement sont
atteints depuis un script d'etage par l'enumeration descendante de `chargeurs2i`. Les
vingt-huit autres ne sont pas forcement morts : ils peuvent etre atteints par un chemin
que la descente ne suit pas.

Descendre coute cher et rate des chemins ; **remonter est exact**. Une fonction n'est
atteignable que si son adresse apparait quelque part -- comme litteral, ou dans une table
de pointeurs. On part donc de la cible et on remonte jusqu'a tomber dans l'une des
dix-sept routines d'etage.

DEUX FACONS D'ETRE APPELE, ET IL FAUT LES DEUX
----------------------------------------------
1. **par litteral** : `mov.l <adresse>,r3 ; jsr @r3`. C'est ce que `sh4.pool_refs` trouve ;
2. **par table de pointeurs** : l'adresse est une entree d'une table, et c'est la TABLE
   qui est chargee par litteral. C'est ainsi que sont atteintes les routines d'effet
   (`0x8C179FDC`), les etats d'un script d'etage, et les routines par enregistrement des
   lecteurs. **Une table de pointeurs est un appel** -- l'oublier a deja fait conclure
   qu'un lecteur « ne posait pas de script ».

    python remonter2i.py 8C0281DC        d'ou cette fonction est-elle atteinte
    python remonter2i.py --spawners      tous les spawners a bloc, et leur origine
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import sh4
import spawners2i as S

D, B = sh4.D, sh4.BASE
FIN_BIN = B + len(D)

u16 = S.u16
u32 = S.u32
CODE = S.CODE
DONNEES = S.DONNEES

TABLE_EFFETS = 0x8C179FDC
NB_EFFETS = 196

_index = None


def index_des_mots():
    """{valeur u32 alignee: [adresses]} -- ou chaque adresse apparait dans le binaire.

    Un seul balayage, garde en memoire : la remontee en fait des milliers de lectures.
    """
    global _index
    if _index is not None:
        return _index

    _index = {}
    n = len(D) // 4
    vals = struct.unpack_from("<%dI" % n, D, 0)

    for i, v in enumerate(vals):
        if CODE(v) or DONNEES(v):
            _index.setdefault(v, []).append(B + i * 4)

    return _index


def charge_par(cible):
    """[(pc, registre)] des `mov.l @(disp,PC),rN` dont le litteral vaut `cible`.

    Meme travail que `sh4.pool_refs`, mais en passant par l'index des mots : celui-ci
    balaie le binaire UNE fois, la ou `pool_refs` le refouille a chaque appel. La
    remontee en fait des milliers.
    """
    out = []

    for pool in index_des_mots().get(cible, ()):
        if pool % 4:
            continue
        for ins in range(max(B, pool - 1100), pool, 2):
            w = u16(ins)
            if (w >> 12) != 0xD:
                continue
            if ((ins + 4) & ~3) + (w & 0xFF) * 4 == pool:
                out.append((ins, (w >> 8) & 0xF))

    return out


_bsr = None


def cibles_bsr():
    """{cible: [sites]} de tous les `bsr`/`bra` du code -- ils sont RELATIFS AU PC.

    LE TROISIEME CHEMIN D'APPEL, ET IL N'A PAS DE LITTERAL — 02/09/2026
    --------------------------------------------------------------------
    `bsr disp12` atteint +/- 4 Ko sans charger aucune adresse. Une fonction appelee
    seulement ainsi n'apparait NULLE PART dans le binaire : ni comme litteral, ni dans une
    table. La remontee concluait « aucun site d'appel » sur trois des cinq betes d'Oro,
    qui sont pourtant appelees depuis leur voisine immediate.
    """
    global _bsr
    if _bsr is not None:
        return _bsr

    _bsr = {}

    for c in range(0x8C010000, 0x8C120000, 2):
        op = u16(c)
        if (op & 0xF000) not in (0xA000, 0xB000):     # bra, bsr
            continue
        d = op & 0xFFF
        d = d - 0x1000 if d & 0x800 else d
        _bsr.setdefault(c + 4 + d * 2, []).append(c)

    return _bsr


def sites_dappel(cible, portee=26):
    """Les instructions qui appellent `cible` : par LITTERAL, ou par `bsr` relatif."""
    out = list(cibles_bsr().get(cible, ()))

    for pc, reg in charge_par(cible):
        for k in range(1, portee):
            c = pc + k * 2
            op = u16(c)
            if (op & 0xF0FF) in (0x400B, 0x402B) and ((op >> 8) & 0xF) == reg:
                out.append(c)
                break

    return out


def tables_contenant(cible, marge=64):
    """Les tables de pointeurs de CODE qui portent `cible`, et son rang dedans."""
    out = []

    for a in index_des_mots().get(cible, ()):
        # une table : des pointeurs de code de part et d'autre
        deb = a
        while deb - 4 >= B and CODE(u32(deb - 4)) and a - deb < marge * 4:
            deb -= 4
        fin = a
        while fin + 4 < FIN_BIN and CODE(u32(fin + 4)) and fin - a < marge * 4:
            fin += 4
        n = (fin - deb) // 4 + 1
        if n >= 2:
            out.append((deb, (a - deb) // 4, n))

    return out


def routines_detage():
    import chargeurs2i as CH
    return CH.scripts_detage()


def enclos(site):
    """La fonction qui contient ce site, par son prologue."""
    import effets2i as E
    return E.debut_de_fonction(site)


def remonter(cible, profondeur=5):
    """[(chaine, bande)] -- les chemins qui menent d'une routine d'etage a `cible`."""
    etages = routines_detage()

    def bande_de(a):
        for deb, fin, bande in etages:
            if deb <= a < fin:
                return bande
        return None

    trouves = []
    vus = {cible}
    front = [(cible, [cible])]

    for _ in range(profondeur):
        suivant = []

        for f, chemin in front:
            sites = list(sites_dappel(f))

            # et les tables qui portent `f` : le vrai appelant charge la TABLE
            for tdeb, _rang, _n in tables_contenant(f):
                sites += sites_dappel(tdeb, portee=40)
                for pc, _reg in charge_par(tdeb):
                    sites.append(pc)

            for s in sites:
                bande = bande_de(s)

                if bande is not None:
                    trouves.append((chemin + [s], bande))
                    continue

                g = enclos(s)

                if g is None or g in vus:
                    continue

                vus.add(g)
                suivant.append((g, chemin + [g]))

        if trouves or not suivant:
            break

        front = suivant

    return trouves


def main():
    import effets2i as E
    import chargeurs2i as CH

    b2d = CH.bande_vers_decor()

    if "--spawners" in sys.argv:
        cibles = []
        for i, fs in sorted(E.spawners().items()):
            for f in fs:
                if S.analyser(f) is not None:
                    cibles.append((i, f))
    else:
        cibles = [(None, int(a, 16)) for a in sys.argv[1:] if a[0] != "-"]

    if not cibles:
        print(__doc__)
        return

    print("%-5s %-10s %s" % ("id", "fonction", "d'ou elle est atteinte"))
    print("-" * 84)

    for i, f in cibles:
        ch = remonter(f)
        bandes = sorted({b for _c, b in ch})

        if bandes:
            quoi = ", ".join("bande %d (decor %s)" % (b, b2d.get(b)) for b in bandes)
            court = min((len(c) for c, _b in ch))
            quoi += "   [%d cran(s)]" % (court - 1)
        else:
            quoi = "AUCUN chemin depuis une routine d'etage"

        print("%-5s %08X   %s" % (i if i is not None else "-", f, quoi))


if __name__ == "__main__":
    main()
