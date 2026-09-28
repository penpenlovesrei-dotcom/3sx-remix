# -*- coding: utf-8 -*-
"""LA MACHINE À ÉTATS D'UN OBJET — quels scripts il enchaîne, et dans quel ordre.

POURQUOI CET OUTIL EXISTE
-------------------------
Plusieurs objets de décor ont un script d'**une seule image** : les cages à oiseaux de Yun,
les deux personnages accroupis devant le tram, le repos du vieil homme. Notre moteur joue
un script en boucle, et ces objets restent donc figés — alors qu'ils bougent dans
l'original. Frédéric l'a signalé plusieurs fois, dont « où sont les oiseaux animés dans les
cages ? ».

Leur animation ne vient pas du script : elle vient de la **routine** de l'objet, qui change
de script au fil du temps. `objet+36` est son `routine_no`, et aucun spawner ne l'écrit —
tout objet naît donc dans l'état 0, puis sa routine le fait avancer.

CE QU'IL LIT, ET CE QU'IL NE DEVINE PAS
---------------------------------------
Dans la routine de l'objet (celle que son `id` désigne dans `0x8C179FDC`) et dans ce
qu'elle appelle, il relève deux choses, chacune avec son adresse :

  * les **poses de script** — un appel à `0x8C0B4AD4`, dont `r6` porte le numéro ;
  * les **transitions** — l'écriture d'une constante en `objet+36`.

Il les rend dans l'ordre des adresses, ce qui donne la suite telle que le code la présente.
Il ne reconstitue PAS le graphe : une valeur qu'il ne sait pas est dite inconnue.

    python etats2i.py 23              l'id 23, les cages de Yun
    python etats2i.py --spawner 0x8C02936E
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import effets2i as EF
import immediats2i as IM
import spawners2i as SP

u16 = SP.u16

ROUTINE_NO = 36           # objet+36, le `routine_no` du WORK
SCRIPT = 456
POSEUR = EF.POSE_SCRIPT   # 0x8C0B4AD4 : objet+454 = r5, objet+456 = r6


def evenements(f, profondeur=1, vus=None):
    """[(adresse, genre, valeur)] : poses de script et transitions d'état.

    `genre` vaut "script" ou "etat". La valeur est `None` quand le registre source n'était
    pas une constante -- on ne la remplace jamais par une supposition.
    """
    vus = set() if vus is None else vus

    if f in vus:
        return []

    vus.add(f)
    fin = SP.fin_de_fonction(f)
    saut = SP.pools(f, fin)
    val = {}
    obj = {4: 0}
    out = []
    c = f

    while c < fin:
        if c in saut:
            c += 2
            continue

        op = u16(c)
        n = (op >> 8) & 0xF
        m = (op >> 4) & 0xF

        if (op >> 12) == 0xD:
            val[n] = SP.litteral_l(c)
            obj.pop(n, None)
        elif (op >> 12) == 0x9:
            val[n] = SP.litteral_w(c)
            obj.pop(n, None)
        elif (op & 0xF000) == 0xE000:
            v = op & 0xFF
            val[n] = v - 256 if v > 127 else v
            obj.pop(n, None)
        elif (op & 0xF000) == 0x7000:
            v = op & 0xFF
            v = v - 256 if v > 127 else v
            val[n] = None if val.get(n) is None else val[n] + v
            if n in obj:
                obj[n] += v
        elif (op & 0xF00F) == 0x6003:
            val[n] = val.get(m)
            if m in obj:
                obj[n] = obj[m]
            else:
                obj.pop(n, None)
        elif (op & 0xF00F) in (0x6000, 0x6001, 0x6002, 0x6004, 0x6005, 0x6006):
            val[n] = None
            obj.pop(n, None)
        elif (op & 0xF00F) in (0x000C, 0x000D, 0x000E):
            val[n] = None
            obj.pop(n, None)

        # --- la pose d'un script ------------------------------------------------------
        elif (op & 0xF0FF) == 0x400B:                     # jsr @rN
            cible = val.get(n)

            if cible == POSEUR:
                out.append((c, "script", val.get(6)))
            elif cible and profondeur > 0:
                out.extend(evenements(cible, profondeur - 1, vus))

        # --- une transition d'etat ----------------------------------------------------
        elif (op & 0xF00F) in (0x0004, 0x0005):           # mov.b/w rM,@(r0,rN)
            if n not in obj and val.get(0) in IM.OFFSETS | {ROUTINE_NO}:
                obj[n] = 0

            if n in obj and obj[n] + (val.get(0) or -1) == ROUTINE_NO:
                out.append((c, "etat", val.get(m)))

        elif (op & 0xFF00) in (0x8000, 0x8100):           # mov.b/w r0,@(disp,rN)
            rb = (op >> 4) & 0xF
            d = (op & 0xF) * (2 if (op & 0xFF00) == 0x8100 else 1)

            if rb in obj and obj[rb] + d == ROUTINE_NO:
                out.append((c, "etat", val.get(0)))

        c += 2

    return out


def decrire(idx):
    f = EF.routine(idx)
    print("ID %d   routine %08X" % (idx, f))

    # `SP.DONNEES` teste une zone de DONNEES : une routine est du CODE, et le test la
    # rejetait toujours. Ici on veut seulement une adresse plausible du binaire.
    if not f or not 0x8C010000 <= f < 0x8C800000:
        print("   pas de routine")
        return

    ev = sorted(set(evenements(f)))

    if not ev:
        print("   aucune pose de script ni transition reconnue")
        return

    etat = 0
    for a, genre, v in ev:
        if genre == "etat":
            print("   %08X   passe a l'etat %s" % (a, "?" if v is None else v))
            etat = v
        else:
            print("   %08X   pose le script %s%s"
                  % (a, "?" if v is None else v,
                     "   (etat %s)" % etat if etat is not None else ""))

    scripts = sorted({v for _a, g, v in ev if g == "script" and v is not None})
    etats = sorted({v for _a, g, v in ev if g == "etat" and v is not None})
    print("   -> scripts posés : %s" % (scripts or "aucun"))
    print("   -> etats atteints : %s" % (etats or "aucun"))


def main():
    args = sys.argv[1:]

    if "--spawner" in args:
        s = int(args[args.index("--spawner") + 1], 0)
        ecrits, _ap, _fi = IM.analyser(s)
        idx = ecrits.get(8)
        print("spawner %08X : il pose l'id %s" % (s, idx))

        if idx is not None:
            print()
            decrire(idx)
        return

    if not args:
        args = ["23"]

    for x in args:
        decrire(int(x, 0))
        print()


if __name__ == "__main__":
    main()
