# -*- coding: utf-8 -*-
"""L'ETAT DE LA DECOMPILATION DES DECORS, EN CHIFFRES -- 29/09/2026.

Frederic : « *mais tu as decode quoi depuis la version dreamcast ? je me tue a te demander
de decompiler TOUT ce qui touche aux decors et CE N EST TOUJOURS PAS FAIT* ».

Il a raison, et le defaut n'est pas seulement d'avoir decode trop peu : c'est de n'avoir
jamais su COMBIEN. Chaque correction partait d'un defaut signale, remontait une routine, et
s'arretait la. Personne n'a jamais pose la carte entiere sur la table.

Cet outil la pose. Il ne corrige rien ; il COMPTE, par bande, ce que la chaine sait lire et
ce qu'elle laisse tomber, sur les quatre choses qui font un decor :

    1. les APPELS de la routine d'etage      -- qui cree quoi
    2. les ROUTINES D'OBJET                  -- ce que chaque id fait ensuite
    3. les DESCRIPTEURS DE SCENE             -- comment les pages sont composees
    4. les COMMANDES DE SCRIPT               -- ce qu'un script sait faire

    py -3 inventaire_decors.py            les dix-neuf bandes de New Generation
    py -3 inventaire_decors.py --2i       les quinze decors de 2nd Impact
    py -3 inventaire_decors.py --detail   avec la liste des appels non lus
"""
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

NOMS_NG = {0: "GILL", 1: "ALEX", 2: "SEAN", 3: "RYU", 4: "KEN", 5: "YUN 1", 6: "YUN 2",
           7: "DUDLEY 1", 8: "DUDLEY 2", 9: "NECRO", 10: "HUGO", 11: "IBUKI 1",
           12: "IBUKI 2", 13: "IBUKI 3", 14: "ELENA 1", 15: "ELENA 2", 16: "ORO",
           17: "YANG 1", 18: "YANG 2"}

TABLE_ROUTINES_NG = 0x8C1ADA10
TABLE_COMMANDES_2I = 0x8C1C5BC8


def inventaire_ng(detail=False):
    import routineng as RN          # bascule le binaire sur SF3_1ST.BIN
    import animerng as A
    import annuaireng as ANG
    import descripteursng as DN
    import objetsng as ON
    import sh4ng as N

    sp = ANG.spans()
    total = dict(appels=0, lus=0, objets=0, ids=set(), ids_lus=set())

    print("%-4s %-10s %6s %6s %7s   %s"
          % ("b.", "nom", "appels", "lus", "objets", "ce qui n'est pas lu"))
    print("-" * 96)

    for bande in range(19):
        enregs, inconnus = ON.enregistrements(bande)
        obj, _nom, _i = A.objets(bande, sp)
        n_app = len(enregs) + len(inconnus)

        total["appels"] += n_app
        total["lus"] += len(enregs)
        total["objets"] += len(obj)

        # les ids que ces appels mettent en jeu
        for site, cible, arg, zs, imm in inconnus:
            if isinstance(imm, dict) and imm.get("id") is not None:
                total["ids"].add(imm["id"])

        for e, _src in enregs:
            if e.get("id") is not None:
                total["ids"].add(e["id"])
                total["ids_lus"].add(e["id"])

        manque = ", ".join(sorted({"id %s" % imm["id"] if isinstance(imm, dict)
                                   and imm.get("id") is not None else "%08X" % cible
                                   for site, cible, arg, zs, imm in inconnus}))
        print("%-4d %-10s %6d %6d %7d   %s"
              % (bande, NOMS_NG[bande], n_app, len(enregs), len(obj), manque[:46]))

        if detail and inconnus:
            for site, cible, arg, zs, imm in inconnus:
                print("         %08X -> %08X  r4=%-5s %s" % (site, cible, arg, imm))

    print("-" * 96)
    print("APPELS DES ROUTINES D'ETAGE : %d lus sur %d  (%.0f %%)"
          % (total["lus"], total["appels"], 100.0 * total["lus"] / max(1, total["appels"])))
    print("OBJETS EMIS : %d" % total["objets"])

    # 2. les routines d'objet
    codes = [N.U32(TABLE_ROUTINES_NG + i * 4) for i in range(186)]
    valides = [i for i, v in enumerate(codes) if 0x8C020000 <= v < 0x8C1A0000]
    print("ROUTINES D'OBJET (table %08X) : %d entrees valides ; nos decors en mettent %d en"
          " jeu, dont %d sont lues"
          % (TABLE_ROUTINES_NG, len(valides), len(total["ids"]), len(total["ids_lus"])))
    reste = sorted(total["ids"] - total["ids_lus"])

    if reste:
        print("   pas lues : %s" % ", ".join(str(i) for i in reste))

    # 3. les descripteurs de scene
    propres = [b for b in sorted(DN.CAS) if DN.CAS[b]["base"] != [DN.DEFAUT]]
    print("DESCRIPTEURS DE SCENE : %d bandes sur 19 ont une liste propre (%s) ; les autres"
          " prennent la liste par defaut %08X"
          % (len(propres), ", ".join(str(b) for b in propres), DN.DEFAUT))
    return total


def inventaire_commandes():
    """La table des commandes de script de 2I, et ce qu'on en sait."""
    import sh4

    connues = {0x01: "relance au debut",
               0x02: "relance a l'enregistrement mot3 - 2",
               0x0C: "ouvre une boucle, compte dans mot3",
               0x0D: "ferme la boucle",
               0x29: "DEPLACE : axe en +2, pas signe en +4, / 256 pixels"}
    print()
    print("COMMANDES DE SCRIPT (table %08X)" % TABLE_COMMANDES_2I)
    vues = {}

    for k in range(64):
        v = sh4.u32(sh4.a2o(TABLE_COMMANDES_2I + k * 4))

        if 0x8C020000 <= v < 0x8C1A0000:
            vues[k] = v

    print("   %d entrees pointent sur du code ; %d sont lues et ecrites :"
          % (len(vues), len(connues)))

    for k in sorted(vues):
        note = connues.get(k)
        print("      0x%02X -> %08X%s" % (k, vues[k], ("   " + note) if note else "   ?"))

    return vues, connues


def main():
    detail = "--detail" in sys.argv

    if "--2i" in sys.argv:
        inventaire_commandes()
        return 0

    inventaire_ng(detail)
    inventaire_commandes()
    return 0


if __name__ == "__main__":
    sys.exit(main())
