# -*- coding: utf-8 -*-
"""Sonde une REGION du binaire pour y reconnaitre des enregistrements d'objets animes.

C'est l'outil qui borne un bloc par les ECHECS FRANCS, sans rien regler a la vue. Il lit
la zone au format de l'annuaire -- 16 octets `{plan, drapeaux, x, y, palette, script,...}`
-- et pour chaque enregistrement il pose les questions qui tranchent :

  1. le script existe-t-il dans la table de scripts DE CE DECOR ?
  2. son index global tombe-t-il dans le `index_global` de l'asset F_ETC DU MEME DECOR ?
  3. le sprite s'assemble-t-il ?  (taille, morceaux)
  4. la palette du premier morceau tombe-t-elle dans la plage du decor ?

Une reponse NON a l'une des trois premieres est un echec franc : le bloc s'arrete la.

    python sonder_oro.py                       la zone de la piste, decor 9
    python sonder_oro.py 0x8C17E6B8 0x8C17E9E8 une autre fenetre
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import annuaire2i as AN
import assemblage as A
import bases
import poser2i as P
import sh4

_D, _B = sh4.D, sh4.BASE
u8 = lambda a: _D[a - _B]
u16 = lambda a: struct.unpack_from('<H', _D, a - _B)[0]
s16 = lambda a: struct.unpack_from('<h', _D, a - _B)[0]
u32 = lambda a: struct.unpack_from('<I', _D, a - _B)[0]

DECOR = 9
BG = "bg0a"


def script_images(decor, sc):
    """[(index global, duree)] d'un script -- la meme lecture qu'`animer2i`."""
    t, n = AN.table_scripts(decor)

    if not 0 <= sc < n:
        return None

    p = u32(t + sc * 4)
    out = []

    for k in range(96):
        cmd = u8(p + k * 8)
        duree = u8(p + k * 8 + 1)
        idx = u16(p + k * 8 + 6)

        if cmd == 0x01:
            break

        if cmd == 0x00 and duree:
            out.append((idx, duree))

    return out


def juger(decor, bg, adresse):
    """Le verdict d'un enregistrement de 16 octets : (ok, texte)."""
    plan = u16(adresse)
    drap = u16(adresse + 2)
    x = s16(adresse + 4)
    y = u16(adresse + 6)
    pal_el = u16(adresse + 8)
    sc = u16(adresse + 10)
    queue = " ".join("%04X" % u16(adresse + 12 + j * 2) for j in range(2))

    tete = ("%08X  plan %5d  drap %5d  x %6d  y %5d  pal %5d  sc %4d  [%s]"
            % (adresse, plan, drap, x, y, pal_el, sc, queue))

    _t, ns = AN.table_scripts(decor)

    if not 0 <= sc < ns:
        return False, tete + "  ECHEC script hors des %d scripts" % ns

    a, tuiles = P.asset(bases.ASSETS[bg])
    lo, hi = a["index_global"]
    ims = script_images(decor, sc)

    if not ims:
        return False, tete + "  ECHEC script vide"

    dedans = [i for i, _d in ims if lo <= i < lo + len(a["anims"])]

    if not dedans:
        return False, tete + ("  ECHEC index %s hors asset [%d, %d)"
                              % (ims[0][0], lo, hi))

    if len(dedans) < len(ims):
        return False, tete + ("  ECHEC %d image(s) sur %d hors asset"
                              % (len(ims) - len(dedans), len(ims)))

    offs = sorted({r[4] for r in a["anims"]})
    rec = a["anims"][dedans[0] - lo]
    n = offs.index(rec[4])
    sp = a["sprites"][n]
    pose = A.poser(sp, tuiles)

    if pose is None:
        return False, tete + "  ECHEC sprite %d n'assemble pas" % n

    b = bases.BASES_2I[bg]
    champ = sp["morceaux"][0][1]

    if (champ >> 9) not in b:
        return False, tete + "  ECHEC drapeau de palette %d inconnu" % (champ >> 9)

    num = b[champ >> 9] + (champ & 0x1FF)
    pals = sorted({b[m[1] >> 9] + (m[1] & 0x1FF)
                   for m in sp["morceaux"] if (m[1] >> 9) in b})

    return True, tete + ("  ->  %2d images  sprite %3d  %3dx%-3d  pal %s"
                         % (len(ims), n, pose[0].shape[1], pose[0].shape[0],
                            "-".join(str(v) for v in pals[:4])))


def main():
    if len(sys.argv) >= 3:
        deb, fin = int(sys.argv[1], 0), int(sys.argv[2], 0)
    else:
        deb, fin = 0x8C17E6B8, 0x8C17E9E8

    _t, ns = AN.table_scripts(DECOR)
    a, _tu = P.asset(bases.ASSETS[BG])
    lo, hi = a["index_global"]
    print("decor %d (%s) : %d scripts, asset index_global [%d, %d), %d animations"
          % (DECOR, BG, ns, lo, hi, len(a["anims"])))
    print("bloc connu : 0x8C17E928, 7 enregistrements\n")

    ad = deb
    while ad < fin:
        ok, texte = juger(DECOR, BG, ad)
        print(("   " if ok else " ! ") + texte)
        ad += 16


if __name__ == "__main__":
    main()
