# -*- coding: utf-8 -*-
"""LES 196 ROUTINES D'EFFET DE 2nd IMPACT, DEPOUILLEES — qui fabrique un objet de decor.

LA TABLE, ET COMMENT ON LA LIT
------------------------------
Un objet de 2nd Impact est le meme `WORK` que le port porte en C. `objet+8` est son **id**,
et il indexe la table des routines d'effet, **`0x8C179FDC`**, lue par le repartiteur
`0x8C0215E0` :

    mov.w @(8,r14),r0 ; shll2 r0 ; mov.l @(r0,r10),r3 ; jsr @r3 ; mov r14,r4

avec `r10 = 0x8C179FDC` et `r11 = 0x8C6466EC`, le tas d'objets de 2048 octets.

CE QUE CET OUTIL CHERCHE
------------------------
Un objet de decor de NOTRE espece est un objet dont la routine finit par ecrire un numero
de script en `objet+456`. On le determine sans rien supposer :

1. **tous les spawners** : on balaie le binaire pour `mov.w r0,@(8,rN)` avec un `r0`
   constant connu -- toute fonction qui pose un `id` en dur EST un spawner, et la
   constante donne l'id ;
2. **la routine de cet id** se lit dans la table ;
3. **ecrit-elle `+456` ?** en suivant les appels, ET LES TABLES DE POINTEURS. C'est le
   point qui avait fait conclure faux : la routine qui pose le script n'est atteinte que
   par une table (`0x8C5F9FB4` pour l'id 66, `0x8C5F9EA4` pour l'id 18), jamais par un
   litteral. **Une table de pointeurs est un appel.**

    python effets2i.py            le depouillement complet
    python effets2i.py --decor    seulement ceux qui posent un script
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
lisible = S.lisible

TABLE_EFFETS = 0x8C179FDC
NB_EFFETS = 196
TAS_OBJETS = 0x8C6466EC
POSE_SCRIPT = 0x8C0B4AD4      # objet+454 = r5 ; objet+456 = r6, le numero de script


def routine(idx):
    return u32(TABLE_EFFETS + idx * 4)


def debut_de_fonction(site, recul=0x400, ecart=8):
    """Le debut de la fonction qui contient `site`, par son prologue.

    LE PROLOGUE EST ENTRELACE, ET C'EST LE PIEGE — 02/09/2026
    ----------------------------------------------------------
    Une fonction SH-4 empile ses registres sauvegardes, mais le compilateur GLISSE
    d'autres instructions entre les `mov.l rM,@-r15`. Chez Elena :

        8C03CBCC  mov.l r14,@-r15
        8C03CBCE  mov   #0,r14        <- pas un empilement
        8C03CBD0  mov.l r13,@-r15
        8C03CBD2  mov.l r12,@-r15
        8C03CBD4  mov   #1,r12        <- ni celui-la
        8C03CBD6  mov.l r11,@-r15
        ...

    S'arreter au premier intrus rend une adresse INTERNE a la fonction -- et personne ne
    charge cette adresse-la, puisque les appelants visent l'entree. La remontee concluait
    donc « aucun chemin » sur des spawners dont on connait le decor par ailleurs.

    On prend donc le PLUS ANCIEN empilement d'une grappe : on remonte tant que
    l'empilement precedent est a moins de `ecart` octets.
    """
    pousses = []

    for c in range(site, max(B, site - recul), -2):
        # mov.l rM,@-r15 = 0010 1111 mmmm 0110
        if (u16(c) & 0xFF0F) == 0x2F06:
            pousses.append(c)

    if not pousses:
        return None

    deb = pousses[0]
    for c in pousses[1:]:
        if deb - c <= ecart:
            deb = c
        else:
            break

    return deb


def appelees(f, profondeur=2, vus=None):
    """Les fonctions atteintes depuis `f` -- par litteral ET PAR TABLE DE POINTEURS."""
    if vus is None:
        vus = set()
    if f in vus or not CODE(f) or profondeur < 0:
        return vus
    vus.add(f)

    fin = S.fin_de_fonction(f)
    suites = []

    for c in range(f, fin, 2):
        if (u16(c) >> 12) != 0xD:
            continue
        v = S.litteral_l(c)
        if v is None:
            continue
        if CODE(v):
            suites.append(v)
        elif DONNEES(v):
            # UNE TABLE DE POINTEURS EST UN APPEL. C'est le maillon qui manquait : la
            # routine par enregistrement n'est atteinte que comme ca.
            for k in range(16):
                if not lisible(v + k * 4):
                    break
                p = u32(v + k * 4)
                if not CODE(p):
                    break
                suites.append(p)

    for x in suites:
        appelees(x, profondeur - 1, vus)

    return vus


def source_du_script(f, profondeur=2):
    """A quel offset d'objet la routine prend-elle son numero de script ?

    `0x8C0B4AD4` ecrit `objet+456 = r6`. On cherche donc les appels a cette fonction et
    l'offset charge dans r6 juste avant -- `mov.w @(r0,r14),r6` avec r0 suivi.

    Rend l'ensemble des offsets trouves. Vide = cette routine ne pose pas de script.
    """
    out = set()

    for g in appelees(f, profondeur):
        fin = S.fin_de_fonction(g)
        r0 = None

        for c in range(g, fin, 2):
            op = u16(c)
            n = (op >> 8) & 0xF

            if (op & 0xFF00) == 0xE000:                 # mov #imm,r0
                v = op & 0xFF
                r0 = v - 256 if v > 127 else v
            elif (op & 0xFF00) == 0x9000:               # mov.w @(disp,PC),r0
                r0 = S.litteral_w(c)
            elif (op & 0xFF00) == 0x7000:               # add #imm,r0
                v = op & 0xFF
                if r0 is not None:
                    r0 += v - 256 if v > 127 else v
            # mov.w @(r0,rM),r6 = 0000 0110 mmmm 1101
            elif (op & 0xF00F) == 0x000D and n == 6 and r0 is not None:
                # un appel a POSE_SCRIPT dans les huit instructions qui suivent ?
                for k in range(1, 9):
                    if S.litteral_l(c + 2 * k) == POSE_SCRIPT:
                        out.add(r0)
                        break

    return out


def ecrit_offset(f, cible=456, profondeur=3, vus=None):
    """La fonction, ses appelees ET LES TABLES DE POINTEURS qu'elle charge ecrivent-elles
    `objet+cible` ?

    Les tables sont suivies : c'est la seule facon d'atteindre la routine par
    enregistrement, et c'est ce qui manquait au premier balayage.
    """
    if vus is None:
        vus = set()
    if f in vus or not CODE(f) or profondeur < 0:
        return False
    vus.add(f)

    fin = S.fin_de_fonction(f)
    r0 = None
    suites = []

    c = f
    while c < fin:
        op = u16(c)
        n = (op >> 8) & 0xF

        if (op >> 12) == 0xE:                       # mov #imm,rN
            v = op & 0xFF
            if n == 0:
                r0 = v - 256 if v > 127 else v
        elif (op >> 12) == 0x9:                     # mov.w @(disp,PC),rN
            v = S.litteral_w(c)
            if n == 0:
                r0 = v
        elif (op >> 12) == 0xD:                     # mov.l @(disp,PC),rN
            v = S.litteral_l(c)
            if n == 0:
                r0 = None
            if v is not None:
                if CODE(v):
                    suites.append(v)
                elif DONNEES(v):
                    # une table de pointeurs de CODE est un APPEL
                    for k in range(16):
                        if not lisible(v + k * 4):
                            break
                        p = u32(v + k * 4)
                        if not CODE(p):
                            break
                        suites.append(p)
        elif (op & 0xF000) == 0x7000 and n == 0:    # add #imm,r0
            v = op & 0xFF
            if r0 is not None:
                r0 += v - 256 if v > 127 else v
        elif (op & 0xF00F) in (0x0005, 0x0004, 0x0006):   # mov.x rM,@(r0,rN)
            if r0 == cible:
                return True

        c += 2

    if f == POSE_SCRIPT:
        return True

    for s in suites:
        if ecrit_offset(s, cible, profondeur - 1, vus):
            return True

    return False


def spawners():
    """{id: [fonctions]} -- toute fonction qui ecrit un `id` CONSTANT en `objet+8`.

    Le motif est celui des trois spawners connus : `mov #N,r0 ; mov.w r0,@(8,rN)`, soit
    l'opcode 0x81n4. On remonte au prologue pour nommer la fonction.
    """
    out = {}

    for c in range(0x8C010000, 0x8C120000, 2):
        op = u16(c)

        # mov.w r0,@(disp,rN) avec disp*2 == 8  ->  1000 0001 nnnn 0100
        if (op & 0xFF0F) != 0x8104:
            continue

        # la valeur de r0, posee dans les six instructions precedentes
        v = None
        for p in range(c - 2, max(B, c - 24), -2):
            o = u16(p)
            if (o & 0xFF00) == 0xE000:              # mov #imm,r0
                v = o & 0xFF
                break
            if (o & 0xFF00) == 0x9000:              # mov.w @(disp,PC),r0
                v = S.litteral_w(p)
                break
            if (o & 0xF00F) == 0x6003 and ((o >> 8) & 0xF) == 0:
                break                               # r0 vient d'un registre : on renonce

        if v is None or not 0 <= v < NB_EFFETS:
            continue

        f = debut_de_fonction(c)

        if f is None:
            continue

        out.setdefault(v, [])
        if f not in out[v]:
            out[v].append(f)

    return out


def main():
    import chargeurs2i as CH

    sp = spawners()
    b2d = CH.bande_vers_decor()

    # qui appelle quoi, depuis les scripts d'etage -- l'appelant fait foi
    appelants = {}
    for deb, fin, bande in CH.scripts_detage():
        aplat = list(CH.appels(deb, fin))
        vues = set()
        for _s, cible, _a in list(aplat):
            if cible in vues:
                continue
            vues.add(cible)
            aplat += CH.appels(cible, CH.fin_de_fonction(cible))
        for site, cible, arg in aplat:
            proprio = CH.decor_du_site(site)
            if proprio is not None and proprio != bande:
                continue
            appelants.setdefault(cible, []).append((bande, arg))

    print("La table des routines d'effet de 2nd Impact : %08X, %d entrees." % (TABLE_EFFETS, NB_EFFETS))
    print()
    print("On ne retient qu'un spawner qui LIT UN BLOC (`mov.w @rM+`) : c'est ce qui")
    print("distingue un objet fabrique depuis des DONNEES d'un objet cree par du code.")
    print()
    print("%-5s %-10s %-5s %-9s %-22s %s"
          % ("id", "spawner", "pas", "script", "bloc / tables", "appele par"))
    print("-" * 100)

    lus = 0
    atteints = 0
    inconnus = []

    for i in sorted(sp):
        for f in sp[i]:
            a = S.analyser(f)

            if a is None:
                continue                       # ne lit aucun bloc : pas notre affaire

            lus += 1
            src = source_du_script(routine(i)) if CODE(routine(i)) else set()
            champs = dict((o, r) for r, o in a["champs"])
            # le script est-il DANS le bloc, ou pose par la routine ?
            if 456 in champs:
                dit = "bloc, octet %d" % (champs[456] * 2)
            elif src:
                # l'offset d'objet -> l'octet du bloc qui l'alimente
                oct = [str(r * 2) for r, o in a["champs"] if o in src]
                dit = ("routine, octet %s" % ",".join(oct)) if oct else                       ("routine, +%s" % ",".join(str(o) for o in sorted(src)))
            else:
                dit = "-"

            if a["bloc"] is not None:
                ou = "en dur %s" % S._txt(a["bloc"])
            else:
                ou = "%s / %s" % (S._txt(a["nombres"]), S._txt(a["pointeurs"]))

            qui = ", ".join("b%d(d%s) arg %s" % (b, b2d.get(b), g)
                            for b, g in appelants.get(f, []))
            if qui:
                atteints += 1
            elif dit != "-":
                inconnus.append((i, f, dit))

            print("%-5d %08X   %-5d %-9s %-22s %s"
                  % (i, f, a["pas"], dit, ou[:22], qui))

    print()
    print("%d spawners lisent un bloc ; %d sont atteints depuis un script d'etage."
          % (lus, atteints))
    print()
    print("CEUX QUI POSENT UN SCRIPT ET QUE RIEN N'ATTEINT -- la piste a suivre :")
    for i, f, dit in inconnus:
        print("   id %-4d %08X   script %s" % (i, f, dit))


if __name__ == "__main__":
    main()
