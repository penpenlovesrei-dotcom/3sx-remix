# -*- coding: utf-8 -*-
"""Releve d'un etat Flycast de Double Impact -- version 2.

Ce que celui-ci ajoute a `etat.py` :

* **l'identification du decor par les octets du conteneur**, et non par le bloc de
  palettes. Le `.pk` charge reste en RAM ; on y cherche quatre temoins de 1024 octets
  riches et uniques pris dans chaque `.pvc`. C'est une correspondance exacte, pas une
  heuristique -- les etiquettes de `releves/` sont fausses, celles-ci ne le sont pas.
* **la fiche complete des objets de fond** (144 octets), et non seulement x et y.
  Les deux mots de 16.16 en `+16` et `+20` ont la forme et l'encodage des coefficients
  de parallaxe : le plan de premier plan vaut exactement 0x10000 dans neuf etats sur dix.
* **la table de 16 octets** pointee par `0x8C602348`, celle que `0x8C0F6988` indexe par
  le champ `+2` d'un objet : `{u16 drapeaux, u16 index, u16 x, u16 y, u16 ...}`.
  Le plan d'un element s'y lit `(drapeaux >> 10) & 28`, huit plans de quatre octets.

    python etat2.py            # les dix etats, un resume par etat
    python etat2.py --json     # ecrit releves2/<decor>.json
"""
import glob, json, os, struct, sys

import flycast as F
import etat as E

DOS     = os.path.join(os.path.expanduser("~"), "Documents", "Dreamcast", "data")
MOTIF   = "Street Fighter III - Double Impact*.state"
RACINE  = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SORTIE  = os.path.join(RACINE, "releves2")

ETAT    = 0x8C6AF304      # structure d'etat du jeu
NB      = ETAT + 0x10     # nombre d'objets de fond
OBJETS  = ETAT + 84       # tableau d'objets, 144 octets par entree
PLANS   = 0x8C84135C      # 8 x 16 octets : x, x_prec, y, y_prec en 16.16
DEFIL   = 0x8C7EFCCC      # 8 x {u16 x, u16 y} : ce que lit le dessin
CONFIG  = 0x8C84142C      # 8 x 10 octets
PTR_ELEM = 0x8C602348     # pointeur vers la table de 16 octets par element


def etats():
    return sorted(glob.glob(os.path.join(DOS, MOTIF)))


def temoins(reps=("pvc-2i", "pvc-ng")):
    """Quatre blocs de 1024 octets par decor : riches, et uniques a l'ensemble."""
    brut = {}
    for rep in reps:
        for p in sorted(glob.glob(os.path.join(RACINE, rep, "*.pvc"))):
            brut[os.path.basename(p)[:-4]] = open(p, "rb").read()

    def unique(b):
        return sum(1 for d in brut.values() if d.find(b) != -1) == 1

    t = {}
    for nom, d in brut.items():
        pris = []
        for k in range(1, 20):
            o = (len(d) * k // 20) & ~1
            b = d[o:o + 1024]
            if len(b) == 1024 and len(set(b)) >= 100 and unique(b):
                pris.append(b)
            if len(pris) == 4:
                break
        if pris:
            t[nom] = pris
    return t


def decor(ram, t):
    """Le decor dont *tous* les temoins sont en RAM. Plusieurs si le .pk en porte plusieurs."""
    return [n for n, bs in t.items() if all(ram.find(b) != -1 for b in bs)]


def objet(ram, k):
    o = OBJETS + k * 144
    return dict(n=k,
                x=F.s16(ram, o + 10), y=F.s16(ram, o + 12),
                coef_x=F.u32(ram, o + 16) / 65536.0,
                coef_y=F.u32(ram, o + 20) / 65536.0,
                mots=[F.u16(ram, o + i) for i in range(0, 32, 2)])


def morceaux(ram, imax=32768):
    """Les enregistrements de 16 octets reellement dessines cette image.

    Un enregistrement est un **morceau de sprite deja resolu** : le meme contenu que le
    morceau de 8 octets d'ASSEMBLAGE.md, mais avec la position absolue et la taille
    explicite.

        {u16 tuile, u16 palette, u16 x, u16 y, u16 (h-1)<<8 | (l-1),
         u16 drapeaux<<8 | code, u16 cle du pool, u16 0}

    ATTENTION aux deux noms de champ que ce programme sort : `champ1` est la **palette**
    et `palette` est la **cle du pool de tuiles** -- c'est-a-dire ce qui designe l'asset
    F_ETC ou lire la tuile (voir ASSEMBLAGE.md et outils/pools.py). Ces deux noms-la
    restent tels quels : `pools.py` les lit dans les JSON de releves2/.

    CORRIGE LE 29/08/2026, contre le desassemblage (voir DONNEES.md).

    * `l` et `h` sortaient a l'envers, et ils sont renommes `largeur` et `hauteur` pour
      qu'on ne puisse plus s'y tromper. Le dessin fait, en 0x8C0F6A12 et 0x8C0F6A24 :

          largeur = (mot+8       & 127) + 1        le champ BAS
          hauteur = ((mot+8 >> 8) & 127) + 1       le champ HAUT

      Les deux sont en **pixels a l'ecran**, et non en tuiles : la taille de la texture
      vient des quartets bas du mot +10, et le rapport des deux est l'echelle.
    * Les deux bits de centrage etaient echanges. Le code teste `0x0100` en 0x8C0F6A22
      pour retirer la moitie de la **largeur** a x, et `0x0200` en 0x8C0F6A36 pour la
      moitie de la **hauteur** a y. Donc `0x0100` = x est un centre, `0x0200` = y en est
      un -- l'inverse de ce qui etait ecrit ici.

      Cette permutation-la n'avait **aucun effet mesurable** : sur les 3458 morceaux
      dessines des dix-huit etats, les deux bits sont **toujours egaux** (74,6 % a 1,
      25,4 % a 0). C'est pour ca que les rendus de elements.py etaient justes malgre
      l'erreur de nom -- et c'est aussi pour ca qu'il faut la corriger avant qu'un decor
      ou les deux different ne vienne la reveler.

    Le dessin tire la taille du champ `+8`, pas du `code`. Les deux se recoupent
    **98,7 %** du temps sur les morceaux reellement dessines ; le reste est une echelle
    veritable, isotrope, allant de x1,672 a x2.

    Les entrees 0 a 47 du tableau sont la liste d'affichage, pas des morceaux.
    """
    base = F.u32(ram, PTR_ELEM)
    o0 = base - F.BASE_RAM
    out = []
    for i in range(imax):
        o = o0 + i * 16
        w = [ram[o + k] | (ram[o + k + 1] << 8) for k in range(0, 16, 2)]
        if i < 64 or not any(w):
            continue
        code = w[5] & 0xFF
        if not ((code >> 2) & 3) or not (code & 3):
            continue                          # pas un morceau (fonds de plan compris)
        out.append(dict(i=i, tuile=w[0], champ1=w[1], x=w[2], y=w[3],
                        largeur=(w[4] & 127) + 1, hauteur=((w[4] >> 8) & 127) + 1,
                        centre_x=bool(w[5] & 0x0100), centre_y=bool(w[5] & 0x0200),
                        code=code, palette=w[6]))
    return base, out


def elements(ram, n=32):
    base = F.u32(ram, PTR_ELEM)
    out = []
    for i in range(n):
        a = base + i * 16
        d = F.u16(ram, a)
        out.append(dict(i=i, drapeaux=d, plan=((d >> 10) & 28) // 4,
                        index=F.u16(ram, a + 2),
                        x=F.u16(ram, a + 4), y=F.u16(ram, a + 6),
                        w=F.u16(ram, a + 8)))
    return base, out


def releve(chemin, t):
    ram, _ = F.lire_ram(chemin, E.EXE)
    n = F.u16(ram, NB)
    base, elts = elements(ram)
    return dict(etat=os.path.basename(chemin),
                decors=decor(ram, t),
                nb_objets=n,
                objets=[objet(ram, k) for k in range(max(n, 0))],
                plans=[dict(n=k,
                            x=F.s32(ram, PLANS + k * 16) / 65536.0,
                            y=F.s32(ram, PLANS + k * 16 + 8) / 65536.0,
                            defil_x=F.u16(ram, DEFIL + k * 4),
                            defil_y=F.u16(ram, DEFIL + k * 4 + 2),
                            config=F.u16(ram, CONFIG + k * 10 + 4))
                       for k in range(8)],
                base_elements=hex(base),
                elements=elts,
                morceaux=morceaux(ram)[1])


def main():
    t = temoins()
    ecrire = "--json" in sys.argv
    if ecrire:
        os.makedirs(SORTIE, exist_ok=True)
    for chemin in etats():
        r = releve(chemin, t)
        nom = "+".join(r["decors"]) or "inconnu"
        print(f"{r['etat']:48s} {nom:16s} {r['nb_objets']} plans")
        for o in r["objets"]:
            print(f"    objet {o['n']}  x={o['x']:4d} y={o['y']:4d}"
                  f"   coefficients {o['coef_x']:.4f} / {o['coef_y']:.4f}")
        for p in r["plans"][:4]:
            print(f"    plan  {p['n']}  position {p['x']:8.1f},{p['y']:8.1f}"
                  f"   defilement {p['defil_x']:4d},{p['defil_y']:4d}   config {p['config']}")
        m = r["morceaux"]
        print(f"    {len(m)} morceaux dessines ; tailles "
              f"{sorted({(x['largeur'], x['hauteur']) for x in m})}")
        vus = [e for e in r["elements"] if e["drapeaux"] not in (0x0010, 0x0000)][:8]
        for e in vus:
            print(f"    element {e['i']:2d} plan {e['plan']}  index {e['index']:#06x}"
                  f"  x={e['x']:4d} y={e['y']:4d}  drapeaux {e['drapeaux']:#06x}")
        if ecrire:
            # Deux etats peuvent porter le meme decor -- c'est meme ce qu'on cherche pour
            # confirmer les coefficients. Le suffixe de l'etat entre donc dans le nom.
            suf = os.path.splitext(r["etat"])[0].split("Impact")[-1].strip("_ ") or "0"
            f = os.path.join(SORTIE, f"{(nom or 'inconnu').replace('+', '-')}-{suf}.json")
            json.dump(r, open(f, "w", encoding="utf-8"), indent=1)
        print()


if __name__ == "__main__":
    main()
