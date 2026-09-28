# -*- coding: utf-8 -*-
"""CE QUE LA ROUTINE D'ETAGE D'UNE BANDE DE NEW GENERATION CREE -- 16/09/2026.

Le pendant de `routine2i.py`, et il en reprend les lecteurs. `spawners2i`, `immediats2i`
et `chargeurs2i` lisent le binaire A L'IMPORT (`D = sh4.D`) : on leur donne celui de NG
avant de les importer, et on corrige les trois constantes qui different --

    le tireur du tas     2I 0x8C0217E4   NG 0x8C09AFA4   (apparie par `apparier.py`)
    le contexte          2I 0x8C6AF304   NG 0x8C552674   (+4 decor, +5 aire, +6 z)
    la fin du code       2I 0x8C120000   NG 0x8C0F0000   (les blocs de NG commencent en 0x8C11)

Chaque cible est aussi nommee par son JUMEAU de 2I quand `apparier.py` le connait : c'est
ce qui transpose d'un coup ce qu'on a lu la-bas (le poseur de script, les poissons de Yang,
les oiseaux de Yun...).

    python routineng.py 16         la bande 16 (Oro)
    python routineng.py            les dix-neuf
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import sh4
import sh4ng

# LA BASCULE : avant tout import d'un lecteur de 2I.
sh4.D = sh4ng.D
sh4.PATH = sh4ng.PATH

import chargeurs2i as CH  # noqa: E402
import spawners2i as SP  # noqa: E402
import immediats2i as IM  # noqa: E402
import decorsng as N  # noqa: E402
import apparier as AP  # noqa: E402

FIN_CODE = 0x8C0F0000
for m in (CH, SP):
    m.CODE = lambda v: 0x8C010000 <= v < FIN_CODE
    m.DONNEES = lambda v, f=SP.FIN_BIN: FIN_CODE <= v < f
SP.CONTEXTE = 0x8C552674
IM.ALLOCATEUR = 0x8C09AFA4

u16, u32 = SP.u16, SP.u32
s16 = lambda v: v - 65536 if v is not None and v > 32767 else v

CHAMPS = {102: "x", 106: "y", 456: "script", 150: "repos", 152: "action", 88: "pal",
          558: "plan", 556: "prio", 554: "col", 8: "id", 10: "miroir", 364: "table"}

_JUMEAUX = None


def jumeau(ng):
    """L'adresse 2I de la fonction NG `ng`, ou None."""
    global _JUMEAUX
    if _JUMEAUX is None:
        _JUMEAUX = {v: k for k, v in AP.lien().items()}
    return _JUMEAUX.get(ng)


def bornes(bande):
    t = sorted(set(u32(N.TABLE_ETAGES + k * 4) for k in range(N.NB_ETAGES)))
    deb = u32(N.TABLE_ETAGES + bande * 4)
    suiv = [a for a in t if a > deb]
    return deb, (suiv[0] if suiv else deb + 0x800)


def immediats(cible):
    try:
        ecrits, appels, _ = IM.analyser(cible)
    except Exception:
        return {}, []
    out = {}
    for o, v in sorted(ecrits.items()):
        if o in CHAMPS:
            out[CHAMPS[o]] = ("0x%08X" % v) if (v is not None and o == 364) else s16(v)
    return out, appels


def decrire(bande, deb=None, fin=None, profondeur=0, vus=None, sortie=None):
    """Imprime et rend [(site, cible, arg, jumeau 2I, champs immediats, lots)]."""
    if deb is None:
        deb, fin = bornes(bande)
        print("BANDE %d  routine %08X..%08X" % (bande, deb, fin))
    vus = set() if vus is None else vus
    sortie = [] if sortie is None else sortie
    marge = "  " * (profondeur + 1)
    for site, cible, arg in CH.appels(deb, fin):
        if (cible, arg) in vus:
            continue
        vus.add((cible, arg))
        j = jumeau(cible)
        ligne = marge + "%s -> %08X r4=%s%s" % ("%08X" % site if site else "dispatch", cible, arg,
                                                "  [2I %08X]" % j if j else "")
        lots = []
        try:
            a = SP.analyser(cible)
        except Exception:
            a = None
        if a and a.get("champs"):
            ou = {off: rang for rang, off in a["champs"]}
            try:
                bl = SP.blocs(a, arg if arg is not None else 0)
            except Exception:
                bl = []
            vus_bl = {}
            for z, nb, p in bl:
                vus_bl.setdefault((nb, p), []).append(z)
            print(ligne + "  BLOC pas %s champs %s" % (a["pas"], sorted(str(CHAMPS.get(o, o)) for o in ou)))
            for (nb, p), zs in vus_bl.items():
                print(marge + "    z %s : %s enregistrement(s) en %s" % ("".join(map(str, zs)), nb, "%08X" % p if p else "?"))
                for i in range(nb or 0):
                    b = p + i * a["pas"]
                    vals = {CHAMPS[o]: s16(u16(b + ou[o] * 2)) for o in ou if o in CHAMPS}
                    lots.append((zs, b, vals))
                    print(marge + "       %d %08X %s" % (i, b, vals))
            sortie.append((site, cible, arg, j, {}, lots))
            continue
        imm, sous = immediats(cible)
        if imm.get("id") is not None or imm.get("x") is not None:
            print(ligne + "  IMMEDIATS %s" % imm)
        else:
            print(ligne)
        sortie.append((site, cible, arg, j, imm, []))
        # un spawner a immediats en appelle d'autres (la chatte fait ses chatons)
        if imm and profondeur < 2:
            f_fin = SP.fin_de_fonction(cible)
            decrire(bande, cible, f_fin, profondeur + 1, vus, sortie)
    return sortie


def main():
    bandes = [int(a) for a in sys.argv[1:]] or list(range(N.NB_ETAGES))
    for b in bandes:
        decrire(b)
        print()


if __name__ == "__main__":
    main()
