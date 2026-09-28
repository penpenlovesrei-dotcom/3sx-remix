# -*- coding: utf-8 -*-
"""CE QUE LA ROUTINE D'ETAGE D'UNE BANDE CREE, lu appel par appel -- 15/09/2026, nuit.

Pour chaque `jsr`/`jmp` de la routine (bornee par la suivante dans `0x8C1D3FB4`) :
la cible, la constante passee dans r4, et -- si la cible est un chargeur ou un spawner que
`spawners2i.analyser` sait lire -- ses enregistrements par tirage `z`, decodes par la carte
de ses champs (x en +102, y en +106, script en +456 ou +150/+152, palette en +88, plan en
+558). S'y ajoute la TABLE DE SCRIPTS que la cible pose en dur, rapportee a la table du
decor : l'id 22 de Yun pose `table + 42`, et lire son script dans la table du decor
donnait une charrette au lieu d'un oiseau.

Les objets a IMMEDIATS (tout en constantes) sont rendus par `immediats2i.analyser`.

    python routine2i.py 5          la bande 5 (Necro)
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import annuaire2i as AN
import chargeurs2i as CH
import immediats2i as IM
import sh4
import spawners2i as SP

u16 = lambda a: sh4.u16(sh4.a2o(a))
u32 = lambda a: sh4.u32(sh4.a2o(a))
s16 = lambda v: v - 65536 if v is not None and v > 32767 else v

ROUTINES = 0x8C1D3FB4
CHAMPS = {102: "x", 106: "y", 456: "script", 150: "repos", 152: "action", 88: "pal", 558: "plan",
          556: "prio"}


def tables_de_decor():
    t = {}
    for d in range(17):
        for aire in range(3):
            t.setdefault(u32(AN.SCRIPTS + (d * 3 + aire) * 4), []).append((d, aire))
    return t


TABLES = tables_de_decor()


def table_en_dur(f, fin):
    """[(table du decor, (decor, aire), entree)] des tables de scripts chargees par la cible."""
    out = []
    bases = sorted(TABLES)
    for pc in range(f, fin, 2):
        w = u16(pc)
        if (w & 0xF000) == 0xD000:
            v = u32((pc & ~3) + 4 + (w & 0xFF) * 4)
            if 0x8C122000 <= v < 0x8C132000:
                b = max([x for x in bases if x <= v])
                out.append((b, TABLES[b][0], (v - b) // 4))
    return sorted(set(out))


def bornes(bande):
    t = sorted(u32(ROUTINES + k * 4) for k in range(17))
    deb = u32(ROUTINES + bande * 4)
    suiv = [a for a in t if a > deb]
    return deb, (suiv[0] if suiv else deb + 0x800)


# LES QUATRE CHARGEURS A TABLE, dont `spawners2i` ne resout pas les tables : lues ici.
# (table des nombres, table des pointeurs, indexe par l'argument ou par decor*3+aire)
# Leurs enregistrements de 16 octets commencent a pointeur + 2 pour les deux premiers.
A_TABLE = {
    0x8C02E1FE: (0x8C17E794, 0x8C5F9F64, "arg", 2),
    0x8C025A9A: (0x8C17C1F8, 0x8C5F9DF8, "arg", 2),
    0x8C0233B6: (0x8C17B918, 0x8C5F9C04, "decor", 0),
    0x8C02356A: (0x8C17BBC4, 0x8C5F9CD0, "decor", 0),
}


def enregistrements_a_table(cible, arg, bande):
    import etages as E
    tn, tp, mode, dec = A_TABLE[cible]
    if mode == "arg":
        i = arg or 0
    else:
        d, aire = E.decor_et_aire(bande)
        i = d * 3 + aire
    nb, p = u16(tn + i * 2), u32(tp + i * 4)
    out = []
    for k in range(nb):
        b = p + dec + k * 16 - (0 if dec else 0)
        w = [u16(b + 2 * j - (0 if dec else -0)) for j in range(8)]
        if dec:      # pointeur + 2 : plan, drapeaux, x, y, palette, script
            out.append((b, dict(plan=w[0], drap=w[1], x=s16(w[2]), y=s16(w[3]), pal=w[4], script=w[5], suite=w[6:])))
        else:        # le chargeur d'elements : +2 plan, +6 x, +8 y, +10 prio, +12 script
            out.append((b, dict(plan=w[1], x=s16(w[3]), y=s16(w[4]), prio=w[5], script=w[6])))
    return i, nb, p, out


def decrire(bande, profondeur=0, deb=None, fin=None, vus=None):
    if deb is None:
        deb, fin = bornes(bande)
        print("BANDE %d  routine %08X..%08X" % (bande, deb, fin))
    vus = set() if vus is None else vus
    marge = "  " * (profondeur + 1)
    for site, cible, arg in CH.appels(deb, fin):
        if (cible, arg) in vus:
            continue
        vus.add((cible, arg))
        f_fin = SP.fin_de_fonction(cible) or cible + 0x200
        tab = table_en_dur(cible, f_fin)
        ligne = marge + "%s  -> %08X  r4=%s" % ("%08X" % site if site else "dispatch", cible, arg)
        if tab:
            ligne += "  table " + ", ".join("%s+%d" % (da, k) for _b, da, k in tab)
        if cible in A_TABLE:
            i, nb, p, recs = enregistrements_a_table(cible, arg, bande)
            print(ligne + "  CHARGEUR A TABLE  index %d : %d enregistrement(s) en %08X" % (i, nb, p))
            for b, v in recs:
                print(marge + "     %08X  %s" % (b, v))
            continue
        try:
            a = SP.analyser(cible)
        except Exception:
            a = None
        if a and a.get("champs"):
            ou = {off: rang for rang, off in a["champs"]}
            noms = [CHAMPS[o] for o in sorted(ou) if o in CHAMPS]
            print(ligne + "  pas %s  champs %s" % (a["pas"], noms))
            try:
                lots = SP.blocs(a, arg if arg is not None else 0)
            except Exception as e:
                lots = []
                print("      blocs illisibles : %s" % e)
            deja = {}
            for z, nb, p in lots:
                cle = (nb, p)
                deja.setdefault(cle, []).append(z)
            for (nb, p), zs in deja.items():
                print("      z %s : %s enregistrement(s) en %08X" % ("".join(map(str, zs)), nb, p or 0))
                for i in range(nb or 0):
                    b = p + i * a["pas"]
                    vals = {CHAMPS[o]: s16(u16(b + ou[o] * 2)) for o in ou if o in CHAMPS}
                    print("         %d  %08X  %s" % (i, b, vals))
        else:
            try:
                ecrits, _ap, _fi = IM.analyser(cible)
            except Exception:
                ecrits = {}
            imm = {CHAMPS.get(o, o): s16(v) for o, v in sorted(ecrits.items())
                   if o in CHAMPS or o == 8}
            print(ligne + ("  immediats %s" % imm if imm else ""))
            if imm.get(8) is not None and profondeur < 2:
                decrire(bande, profondeur + 1, cible, f_fin, vus)


if __name__ == "__main__":
    for b in sys.argv[1:]:
        decrire(int(b, 0))
        print()
