# -*- coding: utf-8 -*-
"""QUELS SPRITES DE DECOR DEPENDENT D'UN COMBATTANT -- 23/09/2026, pour les deux jeux.

Le chemin a ete etabli sur Elena 2 (New Generation, decor 15, id 85). Il se generalise, et
c'est ce que ce programme fait : pour chaque decor, il dit quels acteurs regardent un
combattant, et PAR QUEL CHEMIN.

LES TROIS CHEMINS
-----------------
1. **En dur** : la routine porte `plw + champ` en litteral et indexe par `muls.w` la taille
   d'un combattant (2I 1036, NG 984). C'est le cas de l'id 85 d'Elena 2, qui se pose a
   `plw[cote].xyz[0].pos - 64`.
2. **Par la racine** : `objet[+812]` designe la fiche de combattant
   (`0x8C551F28 + cote*886` en NG), et `racine[+818] & 1` donne le cote. La routine charge
   donc les deux constantes 812 et 818.
3. **Par la cible** : `objet[+12]` (`target_adrs`) pointe le createur ; pour un combattant
   c'est son ADVERSAIRE, pose en `0x8C015CBE` (NG) par l'initialisation des combattants.
   La routine fait `mov.l @(3,rm),rn` puis lit un champ de `WORK`.

LES TABLES
----------
    routines d'etage   2I 0x8C1D3FB4 + bande*4 (17)    NG 0x8C189178 + bande*4 (19)
    routines d'acteur  2I 0x8C179FDC + id*4 (196)      NG 0x8C1AD9F8 + id*4 (186)
    un spawner se reconnait a `mov #id,r0 ; mov.w r0,@(8,rn)`

    python dependances.py           les deux jeux
    python dependances.py ng        New Generation seulement
"""
import collections
import os
import struct
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)

import combattants as C
import declencheurs as D

JEUX = {
    "2I": dict(etages=(0x8C1D3FB4, 17), acteurs=(0x8C179FDC, 196),
               code=(0x8C010000, 0x8C120000), plw=C.PLW["2I"]),
    "NG": dict(etages=(0x8C189178, 19), acteurs=(0x8C1AD9F8, 186),
               code=(0x8C010000, 0x8C0F0000), plw=C.PLW["NG"]),
}

CHAMPS = {102: "son X", 106: "son Y", 84: "position_x", 86: "position_y",
          88: "position_z", 8: "quel personnage", 10: "le sens", 38: "son etat",
          54: "son etat precedent", 68: "le figement de coup", 70: "la secousse",
          0: "existe-t-il", 554: "sa couleur"}


def u32(mod, a):
    return struct.unpack_from("<I", mod.D, mod.a2o(a))[0]


def bornes(adresses, fin):
    """Chaque routine va jusqu'a la suivante, dans l'ordre des adresses."""
    tri = sorted(set(adresses))
    out = {}
    for i, a in enumerate(tri):
        out[a] = tri[i + 1] if i + 1 < len(tri) else min(a + 0x800, fin)
    return out


def constantes(mod, debut, fin):
    """Les constantes chargees en `mov.w @(d,pc),r0` dans la routine."""
    out = set()
    for a in range(debut, min(fin, debut + 0x1000), 2):
        w = mod.u16(mod.a2o(a))
        if (w & 0xFF00) == 0x9000 and ((w >> 8) & 15) == 0:
            out.add(mod.u16(mod.a2o(a + 4 + (w & 0xFF) * 2)))
        if (w & 0xFF00) == 0xE000 and ((w >> 8) & 15) == 0:
            out.add(w & 0xFF)
    return out


def appelees(mod, debut, fin, code, profondeur=0):
    """La routine ET CE QU'ELLE APPELLE -- une aide peut etre ailleurs.

    CE QUI M'A MANQUE (23/09/2026 au soir, sur la remarque de Frederic « le chien du decor
    d'Oro doit suivre des yeux Oro ou Elena ou Ibuki »). `chemins` ne lisait que les octets
    compris entre l'entree d'une routine et la suivante. Une routine qui va chercher un
    combattant dans une fonction d'aide posee ailleurs passait donc pour indifferente, et
    le releve annoncait « 0 dependent d'un combattant » sur des decors qui en ont.

    On suit `bsr` (relatif) et `jsr @rn` quand `rn` vient d'un litteral tout proche, sur
    `profondeur` niveaux, chaque cible etant lue sur 0x600 octets au plus.

    POURQUOI ZERO PAR DEFAUT. A profondeur 1, New Generation passe de 7 acteurs qui lisent
    la position d'un combattant a 22 : une aide partagee, appelee par tout un voisinage
    d'acteurs, les contamine tous. Trop large est aussi faux que trop etroit. La routine
    seule suffit des lors qu'on RESOUT LES CHAMPS -- ce qui manquait vraiment, et non la
    portee -- et le chien d'Oro comme l'acolyte de Gill sont trouves a profondeur 0.
    """
    vues = [(debut, min(fin, debut + 0x1000))]
    bord = list(vues)
    for _ in range(profondeur):
        neuf = []
        for d, f in bord:
            for a in range(d, f, 2):
                w = mod.u16(mod.a2o(a))
                c = None
                if w >> 12 == 0xB:                       # bsr
                    x = w & 0xFFF
                    c = a + 4 + (x - 0x1000 if x & 0x800 else x) * 2
                elif (w & 0xF0FF) in (0x400B, 0x402B):   # jsr @rn / jmp @rn
                    n = (w >> 8) & 15
                    for b in range(max(d, a - 0x20), a, 2):
                        x = mod.u16(mod.a2o(b))
                        if x >> 12 == 0xD and ((x >> 8) & 15) == n:
                            try:
                                c = u32(mod, ((b + 4) & ~3) + (x & 0xFF) * 4)
                            except Exception:
                                c = None
                if c is None or not (code[0] <= c < code[1]):
                    continue
                r = (c, min(code[1], c + 0x600))
                if r not in vues:
                    vues.append(r)
                    neuf.append(r)
        bord = neuf
    return vues


def chemins(mod, debut, fin, plw, code=(0x8C010000, 0x8C120000)):
    """Les chemins par lesquels la routine atteint un combattant."""
    import par_pointeur as PP
    base, taille = plw
    trouve = []
    zones = appelees(mod, debut, fin, code)

    # 1. en dur : un litteral dans plw
    champs = set()
    indexe = False
    for d, f in zones:
        for a in range(d, f, 2):
            w = mod.u16(mod.a2o(a))

            # LE COTE PAR ADDITION, pas seulement par multiplication. Le chien d'Oro
            # (`0x8C033392`) charge 1036 en `mov.w @(d,pc),r4` puis fait `add r4,r5` :
            # aucun `muls.w` n'apparait, et l'ancienne version le declarait indifferent.
            if (w & 0xFF00) == 0x9000:
                try:
                    if mod.u16(mod.a2o(a + 4 + (w & 0xFF) * 2)) == taille:
                        indexe = True
                except Exception:
                    pass
            if (w & 0xF00F) in (0x200F, 0x0007):        # muls.w / mul.l
                for b in range(max(d, a - 0x20), a + 4, 2):
                    x = mod.u16(mod.a2o(b))
                    if (x & 0xF000) != 0x9000:
                        continue
                    try:
                        if mod.u16(mod.a2o(b + 4 + (x & 0xFF) * 2)) == taille:
                            indexe = True
                    except Exception:
                        pass

            if w >> 12 != 0xD:
                continue
            try:
                v = u32(mod, ((a + 4) & ~3) + (w & 0xFF) * 4)
            except Exception:
                continue
            if not (base <= v < base + 2 * taille):
                continue
            # LES DEUX COTES ECRITS EN CLAIR valent un index : l'id 127 de NG porte
            # `0x8C543EC8` et `0x8C5442A0`, l'un derriere l'autre.
            if v - base >= taille:
                indexe = True
            depart = (v - base) % taille
            champs.add(depart)
            # ET CE QUE LE REGISTRE VA LIRE ENSUITE : un litteral sur la base ne dit rien
            # tant qu'on ne sait pas quel champ il sert. `mov #84,r0 ; mov.w @(r0,r5),r3`
            # donne le `position_x` du chien.
            for _s, off in PP.lectures(mod, (w >> 8) & 15, a + 2, min(a + 2 * 90, f)):
                champs.add((depart + off) % taille)

    if champs:
        trouve.append(("en dur" if indexe else "en dur (un seul cote)", sorted(champs)))

    cst = set()
    for d, f in zones:
        cst |= constantes(mod, d, f)

    # 2. par la racine
    if 812 in cst and 818 in cst:
        trouve.append(("par la racine", []))

    # 3. par la cible
    ch = []
    for d, f in zones:
        for a in range(d, f, 2):
            w = mod.u16(mod.a2o(a))
            if (w & 0xF00F) == 0x5003:            # mov.l @(3,rm),rn
                n = (w >> 8) & 15
                for _s, off in PP.lectures(mod, n, a + 2, min(a + 2 * 90, f)):
                    ch.append(off)
    if ch:
        trouve.append(("par la cible", sorted(set(ch))))

    return trouve


def poses(mod, code):
    """Les sites `mov #id,r0 ; mov.w r0,@(8,rn)` : (adresse, id), tries.

    On ne remonte PAS a l'entree de la routine : un `rts` de sortie anticipee -- et les
    spawners en ont tous un -- ferait repartir la recherche au mauvais endroit. On garde
    l'adresse du site, et on rattache un site a une cible d'appel par la distance.
    """
    out = []
    for a in range(code[0], code[1], 2):
        w = mod.u16(mod.a2o(a))
        # UN ID SE CHARGE DE DEUX FACONS (complete le 23/09/2026 au soir) : par un
        # immediat `mov #id,r0` quand il tient sur un octet signe, et par le tas de
        # litteraux `mov.w @(d,pc),r0` quand il depasse 127. L'id 184 des acolytes de
        # Gill est du second genre (`0x8C04AE86`, litteral `0x8C04AEE4` = 184) : sans
        # cette branche, il fallait le rattraper par l'intervalle, et l'intervalle est
        # justement ce qui inventait des acteurs.
        if (w & 0xFF00) == 0xE000 and ((w >> 8) & 15) == 0:
            val = w & 0xFF
        elif (w & 0xFF00) == 0x9000 and ((w >> 8) & 15) == 0:
            try:
                val = mod.u16(mod.a2o(a + 4 + (w & 0xFF) * 2))
            except Exception:
                continue
            if val > 255:
                continue
        else:
            continue
        for k in range(1, 10):
            x = mod.u16(mod.a2o(a + 2 * k))
            if (x & 0xFF0F) == 0x8104:
                out.append((a, val))
                break
    return sorted(out)


def ids_de(poses_triees, cible, portee=0x300):
    """Les ids poses dans [cible, cible + portee)."""
    import bisect
    i = bisect.bisect_left(poses_triees, (cible, -1))
    out = set()
    while i < len(poses_triees) and poses_triees[i][0] < cible + portee:
        out.add(poses_triees[i][1])
        i += 1
    return out


def cibles_par_outil(nom, bande):
    """Les cibles d'appel de la routine d'etage, prises dans `routine2i` / `routineng`.

    Ces deux programmes sont valides depuis le 15/09 : ils bornent la routine, suivent les
    `jsr`, `jmp` ET `bsr`, et descendent d'un niveau dans les spawners. On ne refait pas ce
    travail -- on lit leur sortie.
    """
    import re
    import subprocess
    prog = "routine2i.py" if nom == "2I" else "routineng.py"
    r = subprocess.run([sys.executable, os.path.join(ICI, prog), str(bande)],
                       capture_output=True, text=True, timeout=600)
    out = []
    # SEULES LES LIGNES DE PREMIER NIVEAU COMPTENT (corrige le 23/09/2026 au soir).
    #
    # `routineng` indente : deux espaces pour un appel de la routine d'etage, quatre et
    # plus pour ce qu'il trouve EN DESCENDANT dans un spawner, y compris ses propres
    # etats (`dispatch -> 8C09E7E4`). Ces adresses-la ne creent rien : ce sont des
    # branchements internes. En les prenant pour des cibles, la regle de repli par
    # intervalle m'a fait annoncer un id 19 sur la bande 0 de New Generation -- alors que
    # le seul spawner de cette ligne, `0x8C09E3B6`, ecrit `mov #12,r0 ; mov.w r0,@(8,r4)`.
    #
    # Le meme filtre garde les acolytes de Gill : `8C0DBA78  -> 8C04AE04` est bien de
    # premier niveau.
    for ligne in r.stdout.splitlines():
        m = re.match(r"  ([0-9A-F]{8}) +-> ([0-9A-F]{8})", ligne)
        if not m:
            continue
        out.append(int(m.group(2), 16))
        # `routineng` ecrit "'id': 85", `routine2i` ecrit "{8: 72" -- le champ +8.
        i = re.search(r"'id': (\d+)|\{8: (\d+)", ligne)
        if i:
            out.append(("id", int(i.group(1) or i.group(2))))
    return out


def analyser(mod, nom):
    j = JEUX[nom]
    tab_e, nb_e = j["etages"]
    tab_a, nb_a = j["acteurs"]
    code = j["code"]

    acteurs = {i: u32(mod, tab_a + i * 4) for i in range(nb_a)}
    lim_a = bornes(acteurs.values(), code[1])
    etages = {b: u32(mod, tab_e + b * 4) for b in range(nb_e)}
    lim_e = bornes(etages.values(), code[1])

    ps = poses(mod, code)

    print("=" * 78)
    print("%s : %d decors, %d ids d'acteur" % (nom, nb_e, nb_a))
    print("=" * 78)

    for b in sorted(etages):
        deb = etages[b]
        ids = set()
        for c in cibles_par_outil(nom, b):
            if isinstance(c, tuple):
                ids.add(c[1])
                continue
            # LA REGLE EST HIERARCHIQUE -- 23/09/2026, apres deux erreurs de suite.
            #
            # 1. Si la cible ECRIT un id (`mov #id,r0 ; mov.w r0,@(8,rn)`), c'est lui, et
            #    on s'arrete la. `0x8C0277C4` ecrit l'id 14 ; il est SITUE dans
            #    l'intervalle de l'id 13, mais il ne cree pas d'id 13.
            # 2. Sinon seulement, la cible est un CHARGEUR DE BLOC : il n'ecrit aucun id
            #    et se contente d'etre dans la routine de l'acteur qu'il remplit. C'est le
            #    cas de `0x8C04AE04`, les acolytes de Gill, qui sont des id 184.
            #
            # L'ordre compte : la premiere version ne faisait que le 1 et manquait Gill,
            # la deuxieme ne faisait que le 2 et inventait des id 13.
            n = ids_de(ps, c, 0x120)
            if n:
                ids |= n
                continue
            for i, r in acteurs.items():
                if r <= c < lim_a.get(r, r):
                    ids.add(i)
        lignes = []
        for i in sorted(ids):
            if i not in acteurs:
                continue
            r = acteurs[i]
            ch = chemins(mod, r, lim_a.get(r, r + 0x400), j["plw"], code)
            if ch:
                d = []
                for quoi, offs in ch:
                    if offs:
                        d.append("%s (%s)" % (quoi, ", ".join(
                            "+%d %s" % (o, CHAMPS.get(o, "")) for o in offs)))
                    else:
                        d.append(quoi)
                lignes.append("      id %3d  routine %08X  :  %s" % (i, r, " ; ".join(d)))
        print("   bande %2d  routine %08X  -- %d acteurs crees, %d dependent d'un combattant"
              % (b, deb, len(ids), len(lignes)))
        for l in lignes:
            print(l)
    print()


def main():
    quoi = (sys.argv[1] if len(sys.argv) > 1 else "tout").lower()
    import sh4
    import sh4ng
    if quoi in ("tout", "2i"):
        analyser(sh4, "2I")
    if quoi in ("tout", "ng"):
        analyser(sh4ng, "NG")


if __name__ == "__main__":
    main()
