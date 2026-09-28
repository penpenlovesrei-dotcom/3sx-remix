# -*- coding: utf-8 -*-
"""L'annuaire des elements de decor de 2nd Impact : quel bloc appartient a quel decor.

C'ETAIT LE VERROU DU CHANTIER, ET IL EST DANS LA SUITE IMMEDIATE DE LA TABLE MAITRESSE.

`0x8C5F9B38` n'est pas une table isolee : c'est la premiere d'une SERIE de dix tables de
51 entrees (17 decors x 3 aires), posees bout a bout. La deuxieme est l'annuaire.

    0x8C5F9B38 + 0*204   les scripts d'animation          -> 0x8C12xxxx
    0x8C5F9B38 + 1*204   LES ELEMENTS DE DECOR            -> 0x8C17Bxxx
    0x8C5F9B38 + 2*204   un second jeu d'elements         -> 0x8C17Bxxx
    ... huit autres, jusqu'a 0x8C5FA330 ou la serie s'arrete

C'est pour ca qu'aucun pointeur ne semblait viser les blocs : on les cherchait ailleurs.
Le pointeur d'un decor vaut **deux octets avant** son premier enregistrement, et le bloc
va jusqu'au pointeur distinct suivant :

    debut = annuaire[aire] + 2      nb = (suivant - annuaire[aire]) / 16

L'EPREUVE QUI DISCRIMINE, LA OU LE SPAN SEUL NE DISCRIMINAIT PAS
---------------------------------------------------------------
Le numero de script d'un enregistrement s'entend dans la table de scripts **de ce
decor-la** (`0x8C5F9B38 + aire*4`), pas dans celle du decor 0. L'index global qu'il rend
doit alors tomber dans le `index_global` de l'asset F_ETC **du meme decor**. Sur les
decors 0 a 12 : **trente elements, trente dans leur propre asset, zero ailleurs.**

    decor  0 -> b00   3 elements      decor  7 -> aucun
    decor  1 -> b01   2               decor  8 -> aucun
    decor  2 -> b02   2               decor  9 -> b0a   1
    decor  3 -> b03   4               decor 10 -> b0b   2
    decor  4 -> b04   2               decor 11 -> b0c   5
    decor  5 -> b05   3               decor 12 -> b0d   2
    decor  6 -> b06   2               decor 13 -> b0e   1
                                      decor 16 -> le bloc de b06 (bg10 = hugo bis)

Les decors 14 et 15 reprennent le pointeur du decor 1 et n'ont qu'un script : ce sont des
entrees de remplissage, pas des decors.

CE QUE CA CORRIGE SUR `bg00`
----------------------------
`bg00` a **trois** elements statiques -- le temple, les obelisques, le petit obelisque --
et non cinq. Les deux "etoiles filantes" en 0x8C17B9B0 et 0x8C17B9C0 sont le bloc du
**decor 1**. Elles avaient ete resolues avec la table de scripts du decor 0 et la base de
palette de `bg00`, d'ou le 827 qui semblait les confirmer.

    python annuaire2i.py            # les blocs des dix-sept decors
"""
import glob
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import fetc
import sh4

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)

SERIE = 0x8C5F9B38          # la premiere des dix tables
NB_AIRES = 51               # 17 decors x 3 aires
SCRIPTS = SERIE + 0 * NB_AIRES * 4
ELEMENTS = SERIE + 1 * NB_AIRES * 4
SECONDS = SERIE + 2 * NB_AIRES * 4

_D, _B = sh4.D, sh4.BASE
u32 = lambda a: struct.unpack_from('<I', _D, a - _B)[0]
u16 = lambda a: struct.unpack_from('<H', _D, a - _B)[0]
s16 = lambda a: struct.unpack_from('<h', _D, a - _B)[0]


def table_scripts(decor):
    """(adresse de la table de scripts du decor, nombre de scripts)."""
    t = u32(SCRIPTS + decor * 3 * 4)
    n = 0
    while n < 128 and 0x8C010000 <= u32(t + n * 4) < 0x8C645580:
        n += 1
    return t, n


def index_global(decor, script):
    """L'index global d'animation de la premiere image d'un script."""
    t, n = table_scripts(decor)
    if not 0 <= script < n:
        return None
    return u16(u32(t + script * 4) + 6)


def _bornes(annuaire):
    return sorted({u32(annuaire + k * 4) for k in range(NB_AIRES)})


# LE NOMBRE D'ELEMENTS SE LIT, IL NE SE DEDUIT PAS -- 30/08/2026.
#
# Le chargeur `0x8C0233B6`, appele par quatorze scripts d'etage, s'indexe tout seul sur la
# globale de contexte `0x8C6AF304` (+4 le decor, +5 l'aire) et lit DEUX tables :
#
#     nombre   = u16 [0x8C17B918 + (decor*3 + aire)*2]
#     pointeur = u32 [0x8C5F9C04 + (decor*3 + aire)*4]      <- c'est `ELEMENTS`
#
# Le second jeu d'elements a les siennes, lues par `0x8C02356A` de la meme facon.
#
# La deduction par l'ecart entre pointeurs tombait juste sur treize decors et **faux sur
# quatre** : Oro se voyait attribuer 1 element alors qu'il en a **zero**, Urien 7 au lieu
# de 1, et les deux entrees de remplissage 2 au lieu de 0. Les chats poses sur la
# plate-forme d'Oro venaient de la.
NOMBRES = {ELEMENTS: 0x8C17B918, SECONDS: 0x8C17BBC4}


def bloc(decor, annuaire=ELEMENTS, aire=0, fin_zone=None):
    """(adresse du premier enregistrement, nombre d'enregistrements de 16 octets)."""
    i = decor * 3 + aire
    p = u32(annuaire + i * 4)
    table = NOMBRES.get(annuaire)

    if table is not None:
        return p + 2, u16(table + i * 2)

    # Les annuaires dont on n'a pas encore trouve la table de nombres : on retombe sur
    # l'ecart entre pointeurs, en sachant que c'est une approximation.
    bornes = _bornes(annuaire)
    j = bornes.index(p)

    if j + 1 < len(bornes):
        suiv = bornes[j + 1]
    else:
        suiv = fin_zone if fin_zone is not None else min(_bornes(SECONDS))

    return p + 2, max(0, (suiv - p) // 16)


def elements(decor, annuaire=ELEMENTS):
    """Les elements de decor d'un decor : plan, x signe, y, palette, script."""
    deb, n = bloc(decor, annuaire)
    out = []
    for k in range(n):
        ad = deb + k * 16
        out.append(dict(adresse=ad, plan=u16(ad), drapeaux=u16(ad + 2),
                        x=s16(ad + 4), y=u16(ad + 6),
                        palette=u16(ad + 8), script=u16(ad + 10)))
    return out


def spans_des_assets():
    """nom d'asset -> (premier index global, dernier + 1)."""
    out = {}
    for c in sorted(glob.glob(os.path.join(RACINE, "sprites", "2i-*.bin"))):
        out[os.path.basename(c)[:-4]] = fetc.lire(open(c, "rb").read())["index_global"]
    return out


def main():
    spans = spans_des_assets()
    tot = bons = 0
    for d in range(17):
        els = elements(d)
        _t, ns = table_scripts(d)
        print("decor %2d  bloc %08X  %d element(s)  %d scripts"
              % (d, bloc(d)[0], len(els), ns))
        for e in els:
            g = index_global(d, e["script"])
            if g is None:
                print("      script %d HORS TABLE" % e["script"])
                tot += 1
                continue
            qui = [n for n, (lo, hi) in spans.items() if lo <= g < hi]
            tot += 1
            bons += bool(qui)
            print("      plan %d  x %5d  y %3d  pal %3d  script %2d  ->  index %5d  %s"
                  % (e["plan"], e["x"], e["y"], e["palette"], e["script"], g,
                     ", ".join(qui) or "AUCUN"))
    print("\n%d elements, %d resolus dans un asset de 2nd Impact" % (tot, bons))


if __name__ == "__main__":
    main()
