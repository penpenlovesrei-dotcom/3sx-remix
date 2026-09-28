# -*- coding: utf-8 -*-
"""Les quatre jeux de donnees demandes avant de continuer : plan, palette, cadence, drapeaux.

Tout ce que ce programme affiche est LU -- dans le code SH-4 de `SF3_2ND.BIN` ou dans la
RAM des etats Flycast. Rien n'y est deduit d'une image.

LA BOUCLE DE DESSIN, DESASSEMBLEE (0x8C0F693C, corps a 0x8C0F6A08)
-----------------------------------------------------------------
    r5 = element (16 octets)          r8 = morceau (16 octets)     r10 = morceau + 10

    plan   = (element[+0] >> 12) & 7                       0x8C0F6994..0x8C0F6998
             -- (drapeaux >> 10) & 28 sert d'offset d'octet dans la table de defilement,
                quatre octets par plan, d'ou la division par quatre
    nb     =  element[+0] & 0x0FFF     nombre de morceaux    (verifie sur les 18 etats)
    debut  =  element[+2] & 0x7FFF     premier morceau
    defil  =  0x8C7EFCCC + plan*4      {u16 x, u16 y}        0x8C0F69A2, 0x8C0F69B2

    largeur = (morceau[+8]      & 127) + 1                  0x8C0F6A12, 0x8C0F6A24
    hauteur = ((morceau[+8]>>8) & 127) + 1                  0x8C0F6A14, 0x8C0F6A26
    tuiles_x = 1 << ((morceau[+10]      & 3) - 1)           0x8C0F6B04..0x8C0F6B0E
    tuiles_y = 1 << (((morceau[+10]>>2) & 3) - 1)           0x8C0F6B20..0x8C0F6B30
    -- un morceau dont l'un des deux quartets est nul n'est PAS dessine (0x8C0F6A88)

    x = (defil_x + element[+4] + morceau[+4] - (largeur/2 si morceau[+10] & 0x0100)) & 0x3FF
    y = (109 - defil_y - element[+6] - morceau[+6] - hauteur
             + (hauteur/2 si morceau[+10] & 0x0200)) & 0x3FF        0x8C0F6A90..0x8C0F6AB8

    retournement = element[+9] ^ (morceau[+2] >> 8)         0x8C0F6AC6
        bit 0x08 -> vertical    (y += hauteur)              0x8C0F6AE6..0x8C0F6AF6
        bit 0x10 -> horizontal  (x += largeur)              0x8C0F6AFA..0x8C0F6B00

    palette : si element[+9] & 0x20 -> brut = element[+8]   0x8C0F6A44 (bit 5)
              sinon                 -> brut = morceau[+2]   0x8C0F6A4A
              si element[+9] & 0x40 -> sel = element[+9] & 6        0x8C0F6A4E (bit 6)
              sinon                 -> sel = morceau[+2] & 0x0600   0x8C0F6A52
              sel != 0 -> emplacement = brut & 0x1FF, 64 couleurs   0x8C0F6A6C
              sel == 0 -> emplacement = (brut & 0x1FF) | 0x200, 256 couleurs
              adresse : 0x8C7AFCCC + emplacement * 128 (64 couleurs)

    lanceur : donnees.cmd
"""
import collections, glob, itertools, json, os, sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
RACINE = os.path.dirname(ICI)

import flycast as F, etat as E, fetc, sh4

DOS      = os.path.join(os.path.expanduser("~"), "Documents", "Dreamcast", "data")
MOTIF    = "Street Fighter III - Double Impact*.state"
PTR_ELEM = 0x8C602348          # -> la base de la liste d'affichage et des morceaux
DEFIL    = 0x8C7EFCCC          # 8 x {u16 x, u16 y}, ce que lit le dessin
ETAT     = 0x8C6AF304
OBJETS   = ETAT + 84           # 144 octets par objet de fond
NB_OBJ   = ETAT + 0x10
PALETTES = 0x8C7AFCCC          # juste apres les 32768 morceaux de 16 octets
INSTALL  = 0x8C602384          # 24 octets par asset : +8 fonction, +12 graphiques, +20 cle
IDX2ASS  = 0x8C60A6D4          # index global d'animation >> 2 -> numero d'asset


def elements(ram, base, n=48):
    out = []
    for i in range(n):
        a = base + i * 16
        w = [F.u16(ram, a + k) for k in range(0, 16, 2)]
        if not any(w):
            continue
        out.append(dict(i=i, drapeaux=w[0], plan=(w[0] >> 12) & 7, nb=w[0] & 0x0FFF,
                        debut=w[1] & 0x7FFF, x=w[2], y=w[3], mot8=w[4],
                        octet9=(w[4] >> 8) & 0xFF))
    return out


def morceau(ram, base, i):
    a = base + i * 16
    w = [F.u16(ram, a + k) for k in range(0, 16, 2)]
    tx, ty = w[5] & 3, (w[5] >> 2) & 3
    return dict(i=i, tuile=w[0], champ2=w[1], x=w[2], y=w[3], mot8=w[4], mot10=w[5],
                cle=w[6],
                largeur=(w[4] & 127) + 1, hauteur=((w[4] >> 8) & 127) + 1,
                tuiles_x=(1 << (tx - 1)) if tx else 0,
                tuiles_y=(1 << (ty - 1)) if ty else 0,
                centre_x=bool(w[5] & 0x0100), centre_y=bool(w[5] & 0x0200),
                dessine=bool(tx and ty))


def emplacement_palette(el, m):
    """La regle exacte du dessin, 0x8C0F6A42 .. 0x8C0F6A84."""
    o9 = el["octet9"]
    brut = el["mot8"] if (o9 & 0x20) else m["champ2"]
    sel = (o9 & 6) if (o9 & 0x40) else (m["champ2"] & 0x0600)
    if sel:
        return brut & 0x1FF, 64
    return (brut & 0x1FF) | 0x200, 256


def temoins():
    """Les temoins de pvc-2i qui identifient un decor par ses octets -- comme etat2.py."""
    brut = {}
    for rep in ("pvc-2i", "pvc-ng"):
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


def releve(chemin, t):
    ram, _ = F.lire_ram(chemin, E.EXE)
    base = F.u32(ram, PTR_ELEM)
    n = F.u16(ram, NB_OBJ)
    return dict(
        nom=os.path.basename(chemin),
        decors=[k for k, bs in t.items() if all(ram.find(b) != -1 for b in bs)],
        ram=ram, base=base,
        objets=[dict(n=k, x=F.s16(ram, OBJETS + k * 144 + 10), y=F.s16(ram, OBJETS + k * 144 + 12),
                     cx=F.u32(ram, OBJETS + k * 144 + 16) / 65536.0,
                     cy=F.u32(ram, OBJETS + k * 144 + 20) / 65536.0)
                for k in range(max(n, 0))],
        defil=[dict(n=k, x=F.u16(ram, DEFIL + k * 4), y=F.u16(ram, DEFIL + k * 4 + 2))
               for k in range(8)],
        elements=elements(ram, base))


# ---------------------------------------------------------------- 1. LE PLAN
def le_plan(rs):
    print("=" * 78)
    print("1. LE PLAN -- quels plans un decor de 2nd Impact emploie vraiment")
    print("=" * 78)
    print()
    print("plan = (element[+0] >> 12) & 7, lu en 0x8C0F6994. Le defilement du plan se")
    print("prend en 0x8C7EFCCC + plan*4. Un plan sans element n'existe pas pour le decor.")
    print()
    print("decor  | plans porteurs d elements (nombre d elements)      | plans distincts")
    print("-------+----------------------------------------------------+----------------")
    for r in rs:
        if not r["decors"]:
            continue
        par = collections.Counter(e["plan"] for e in r["elements"] if e["nb"])
        txt = "  ".join("p%d:%2d" % (p, par[p]) for p in sorted(par))
        print("%-6s | %-50s | %d" % ("+".join(r["decors"]), txt, len(par)))
    print()
    print("LE LIEN plan -> objet de fond (le coefficient de parallaxe).")
    print("Regle lue dans les donnees : defil_x[plan] == (-objet.x) & 0x3FF.")
    print("Elle ne separe deux objets que si leur x differe -- c'est-a-dire camera en")
    print("mouvement. Deux etats l'etablissent ; ailleurs elle confirme sans separer.")
    print()
    for r in rs:
        if not r["decors"]:
            continue
        plans_actifs = sorted({e["plan"] for e in r["elements"] if e["nb"]})
        lignes = []
        for p in plans_actifs:
            dx = r["defil"][p]["x"]
            cands = [o for o in r["objets"] if ((-o["x"]) & 0x3FF) == dx]
            if not cands:
                q = "defil_x=%3d  aucun objet (plan fixe)" % dx
            elif len(cands) == 1:
                o = cands[0]
                q = "defil_x=%3d  objet %d  coef %.4f/%.4f" % (dx, o["n"], o["cx"], o["cy"])
            else:
                q = "defil_x=%3d  %d objets ex aequo (%s)" % (
                    dx, len(cands), ", ".join("%d:%.2f" % (o["n"], o["cx"]) for o in cands))
            lignes.append("      plan %d : %s" % (p, q))
        print("   %s  (%s)" % ("+".join(r["decors"]), r["nom"]))
        print("\n".join(lignes))
    print()


# ------------------------------------------------------------ 2. LA PALETTE
def la_palette(rs):
    print("=" * 78)
    print("2. LA PALETTE -- quel emplacement, et ou sont les couleurs")
    print("=" * 78)
    print()
    print("Regle exacte, 0x8C0F6A42..0x8C0F6A84 (voir l en-tete du fichier).")
    print("Adresse des 64 couleurs : 0x8C7AFCCC + emplacement * 128, en ARGB1555.")
    print()
    print("decor  | element | octet9 | source     | emplacement | couleurs")
    print("-------+---------+--------+------------+-------------+---------")
    besoins = {}
    for r in rs:
        if not r["decors"]:
            continue
        nom = "+".join(r["decors"])
        vus = collections.OrderedDict()
        for el in r["elements"]:
            if not el["nb"]:
                continue
            m = morceau(r["ram"], r["base"], el["debut"])
            emp, nc = emplacement_palette(el, m)
            src = "element+8" if (el["octet9"] & 0x20) else "morceau+2"
            vus.setdefault((emp, nc, src, el["octet9"]), []).append(el["i"])
        besoins[nom] = vus
        for (emp, nc, src, o9), els in vus.items():
            print("%-6s | %-7s | 0x%02X   | %-10s | %11d | %d"
                  % (nom, ",".join(str(x) for x in els[:6]) + ("..." if len(els) > 6 else ""),
                     o9, src, emp, nc))
    print()
    print("CE QU IL FAUT CHARGER, decor par decor -- emplacements distincts :")
    for nom, vus in besoins.items():
        emps = sorted({e for e, _n, _s, _o in vus})
        print("   %-6s %2d emplacement(s) : %s" % (nom, len(emps), emps))
    print()
    return besoins


def couleurs(ram, emplacement):
    a = PALETTES + emplacement * 128
    return [F.u16(ram, a + i * 2) for i in range(64)]


# ------------------------------------------------------------ 3. LA CADENCE
def la_cadence():
    print("=" * 78)
    print("3. LA CADENCE -- ce que le flux porte, et ce qu il ne porte pas")
    print("=" * 78)
    print()
    assets = {}
    for p in sorted(glob.glob(os.path.join(RACINE, "sprites", "2i-b*.bin"))):
        assets[os.path.basename(p)[:-4]] = fetc.lire(open(p, "rb").read())

    print("EPREUVE A -- les trois champs que fetc.py notait `?` portent-ils une duree ?")
    n = nz = 0
    for r in assets.values():
        for c0, _x, _y, c3, _sp, c5 in r["anims"]:
            n += 1
            nz += (c0 != 0) + (c3 != 0) + (c5 != 0)
    print("   %d enregistrements, %d champs non nuls sur %d. La duree n y est pas."
          % (n, nz, n * 3))
    print()

    print("EPREUVE B -- l espace d index est-il global, et se resout-il en assets ?")
    print("   index global >> 2 -> octet en 0x8C60A6D4 -> fiche de 24 octets en 0x8C602384")
    print()
    print("   asset                  span global      no  cle    fonction     accord")
    ok = 0
    for nom, r in sorted(assets.items(), key=lambda t: t[1]["index_global"]):
        a, b = r["index_global"]
        n0 = sh4.D[sh4.a2o(IDX2ASS) + (a >> 2)]
        n1 = sh4.D[sh4.a2o(IDX2ASS) + ((b - 1) >> 2)]
        cle = sh4.u32(sh4.a2o(INSTALL) + n0 * 24 + 20) & 0xFFFF
        fn = sh4.u32(sh4.a2o(INSTALL) + n0 * 24 + 8)
        bon = (n0 == n1)
        ok += bon
        print("   %-22s %5d..%-5d  %3d  0x%04X 0x%08X  %s"
              % (nom, a, b, n0, cle, fn, "oui" if bon else "NON"))
    print("   %d assets sur %d : tout le span d un asset tombe sur le meme numero." % (ok, len(assets)))
    print()

    print("EPREUVE C -- le flux des trois decors dits degeneres")
    for nom in ("2i-b01-F_ETC34", "2i-b0c-F_ETC24", "2i-b0e-F_ETC94"):
        r = assets[nom]
        o = 0x20 + len(r["anims"]) * 12
        par_off = {}
        for i, sp in enumerate(r["sprites"]):
            par_off[o] = i
            o += 8 + len(sp["morceaux"]) * 8
        print("   %s -- %d enregistrements, %d sprites" % (nom, len(r["anims"]), len(r["sprites"])))
        for cle, g in itertools.groupby(r["anims"]):
            _c0, x, y, _c3, spo, _c5 = cle
            print("      ancre (%5d,%5d)  sprite %-3s  repete %d fois"
                  % (x, y, par_off.get(spo, "?"), len(list(g))))
    print()


def ou_la_cadence_n_est_pas():
    """Ce que le script d etage touche -- et ce qu il ne touche pas."""
    print("EPREUVE D -- la cadence est-elle dans le script d etage, comme suppose ?")
    print("   Toutes les constantes chargees par le script de bg01 et par les trois")
    print("   fonctions qu il appelle a chaque trame :")
    print()
    cibles = {0x8C602348: "la liste d affichage", 0x8C72FCCC: "les morceaux",
              0x8C602384: "la table d installation des assets",
              0x8C60A6D4: "index global -> asset"}
    zones = [("script bg01", 0x8C0E9014, 0x8C0E9498),
             ("0x8C0E8D9A par trame", 0x8C0E8D9A, 0x8C0E8E90),
             ("0x8C0E8CF4 par trame", 0x8C0E8CF4, 0x8C0E8D9A),
             ("0x8C0E8BFE par trame", 0x8C0E8BFE, 0x8C0E8CF4)]
    trouve = False
    for nom, a0, a1 in zones:
        vus = set()
        for a in range(a0, a1, 2):
            w = sh4.u16(sh4.a2o(a))
            if (w >> 12) == 0xD:
                t = ((a + 4) & ~3) + (w & 0xFF) * 4
                if sh4.BASE <= t < sh4.BASE + len(sh4.D):
                    vus.add(sh4.u32(sh4.a2o(t)))
        touche = [v for v in vus if v in cibles]
        print("   %-22s %2d constantes -- %s" % (
            nom, len(vus),
            ", ".join(cibles[v] for v in touche) if touche else "AUCUNE des quatre cibles"))
        trouve = trouve or bool(touche)
    print()
    print("   Verdict : %s" % (
        "le script touche la liste" if trouve else
        "le script d etage ne touche NI la liste d affichage NI la table des assets.\n"
        "            La cadence n y est donc pas. L hypothese de RELAIS.md est refutee."))
    print()


# ------------------------------------------- 4. RETOURNEMENTS ET ECHELLE
def drapeaux_et_echelle(rs):
    print("=" * 78)
    print("4. RETOURNEMENTS ET ECHELLE")
    print("=" * 78)
    print()
    print("RETOURNEMENT -- 0x8C0F6AC6 : octet = element[+9] ^ (morceau[+2] >> 8)")
    print("   bit 0x08 : retournement vertical    (0x8C0F6AE6, y += hauteur)")
    print("   bit 0x10 : retournement horizontal  (0x8C0F6AFA, x += largeur)")
    print()
    print("CENTRAGE -- morceau[+10], teste en 0x8C0F6A22 et 0x8C0F6A36")
    print("   bit 0x0100 : x est un centre  ->  x -= largeur/2")
    print("   bit 0x0200 : y est un centre  ->  y += hauteur/2")
    print("   (etat2.py nomme ces deux bits a l envers)")
    print()
    print("TAILLE -- morceau[+8] : largeur = (mot & 127)+1, hauteur = ((mot>>8) & 127)+1")
    print("   en PIXELS. etat2.py nomme `l` et `h` a l envers.")
    print()
    print("ECHELLE -- il n existe AUCUN champ d echelle. La taille de la texture vient")
    print("   des quartets bas de morceau[+10] : 1 << (n-1) tuiles de 16 px. L echelle")
    print("   est le rapport entre les deux, et il n est pas toujours 1.")
    print()
    cat = collections.Counter()
    ex = collections.defaultdict(list)
    flips = collections.Counter()
    for r in rs:
        for el in r["elements"]:
            for k in range(el["nb"]):
                m = morceau(r["ram"], r["base"], el["debut"] + k)
                if not m["dessine"]:
                    continue
                f = (el["octet9"] ^ (m["champ2"] >> 8)) & 0x18
                flips[f] += 1
                pw, ph = m["tuiles_x"] * 16, m["tuiles_y"] * 16
                sx = m["largeur"] / float(pw)
                sy = m["hauteur"] / float(ph)
                k2 = (round(sx, 3), round(sy, 3))
                cat[k2] += 1
                if len(ex[k2]) < 2:
                    ex[k2].append((m["mot8"], m["mot10"], m["largeur"], pw, m["hauteur"], ph))
    n = sum(cat.values())
    print("   sur %d morceaux reellement dessines, tous etats confondus :" % n)
    for k, v in cat.most_common(10):
        e = ex[k][0]
        print("      echelle x%.3f y%.3f : %6d (%5.2f %%)   ex. %3dpx/%3dpx  %3dpx/%3dpx"
              % (k[0], k[1], v, 100.0 * v / n, e[2], e[3], e[4], e[5]))
    print()
    print("   retournements observes (element[+9] ^ (morceau[+2]>>8)) & 0x18 :")
    for f, v in flips.most_common():
        quoi = []
        if f & 8: quoi.append("vertical")
        if f & 0x10: quoi.append("horizontal")
        print("      0x%02X %-22s %6d (%5.2f %%)"
              % (f, "+".join(quoi) if quoi else "aucun", v, 100.0 * v / n))
    print()


def main():
    t = temoins()
    rs = [releve(c, t) for c in sorted(glob.glob(os.path.join(DOS, MOTIF)))]
    le_plan(rs)
    la_palette(rs)
    la_cadence()
    ou_la_cadence_n_est_pas()
    drapeaux_et_echelle(rs)


if __name__ == "__main__":
    main()
