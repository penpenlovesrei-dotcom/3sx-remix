# -*- coding: utf-8 -*-
"""TOUT CE QUE LE BINAIRE DE 2nd IMPACT DIT DES DECORS, dans un seul fichier machine.

POURQUOI CET OUTIL EXISTE
-------------------------
Ce qu'on savait des decors etait disperse dans de la PROSE -- `SANS-ETAT.md`, `BILAN.md`,
des commentaires de code, des mesures refaites a chaque session et parfois refaites FAUX.
Frederic l'a dit le 02/09 : « ces donnees, tu les sauvegardes bien dans un fichier ? »
Non, pas assez. D'ou ceci.

Le fichier `DONNEES-2I.json` est **regenere depuis le binaire**, jamais saisi a la main :
le relancer suffit a verifier que rien n'a bouge, et il sert de reference commune aux
autres outils au lieu de tables recopiees.

    python inventaire.py            ecrit DONNEES-2I.json et resume

CE QU'IL PORTE, ET D'OU CA VIENT
--------------------------------
* **les deux jeux de palettes** -- 2I en a deux, comme New Generation :
      0x8C1D5D38  jeu 1, destination 0x02000
      0x8C1D5D16  jeu 2, destination 0x12000   (34 octets avant, soit 17 bandes x 2)
  Les bases du groupe de drapeaux 9 avaient ete calees a l'oeil ; treize decors sur
  quatorze confirment le jeu 2 par sa destination ;
* **la table decor -> bande** `0x8C1D591C`, qui explique le decalage d'index ;
* **les scripts d'animation** de chaque decor, et lesquels se resolvent dans son asset ;
* **les formats d'enregistrement**, lus dans le code des lecteurs et non supposes.
"""
import io
import json
import os
import struct
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
BIN = os.path.join(RACINE, "SF3_2ND.BIN")
SORTIE = os.path.join(RACINE, "DONNEES-2I.json")

D = open(BIN, "rb").read()
BASE = 0x8C010000
FIN = BASE + len(D)

TRANSFERTS = 0x8C1E4B50
IDX_JEU1 = 0x8C1D5D38
# LA TABLE DU SECOND JEU EST EN 0x8C1D5D14, PAS 0x8C1D5D16 — corrige le 02/09/2026.
#
# L'epreuve qui l'avait validee etait faible : « la destination vaut 0x12000 ». Elle dit
# qu'on est tombe dans le second bloc, pas qu'on est tombe sur la bonne ENTREE -- une
# coherence qui prouve un decoupage et non un role, exactement le piege que ces documents
# nomment eux-memes.
#
# New Generation en donne une bien plus forte : chaque bande range **2 x nb palettes
# consecutives**, donc `base2 == base1 + nb1` ET `nb2 == nb1`. Deux egalites, dix-sept
# bandes. En balayant les adresses candidates :
#
#     0x8C1D5D14   17 bandes sur 17
#     0x8C1D5D16    0 bande  sur 17   <- ce qu'on lisait
#
# Decalee de deux octets, elle donnait a chaque bande le second jeu de la SUIVANTE, et la
# bande 16 tombait meme hors du bloc (destination 0x4080). Le controle le plus parlant :
# `bg00` a 48 palettes au premier jeu, et son second en avait « 31 ».
IDX_JEU2 = 0x8C1D5D14
DECOR_VERS_BANDE = 0x8C1D591C
RAM_PALETTES = 0x02798000

# La couleur de remplissage des cases de palette NON INITIALISEES. C'est un detecteur :
# un pixel de cette couleur denonce une palette fausse, sans avoir besoin d'une capture.
VERT_VIDE = 0x03E0


def u16(a):
    return struct.unpack_from("<H", D, a - BASE)[0]


def s16(a):
    v = u16(a)
    return v - 65536 if v > 32767 else v


def u32(a):
    return struct.unpack_from("<I", D, a - BASE)[0]


def transfert(index):
    """{base, nb, destination} d'une entree de la table de transferts."""
    e = TRANSFERTS + index * 12
    return dict(base=(u32(e) - RAM_PALETTES) // 128,
                nb=u32(e + 8) // 128,
                destination=u32(e + 4))


BANDES = {"bg00": 0, "bg01": 1, "bg02": 2, "bg03": 3, "bg04": 4, "bg05": 5,
          "bg06": 6, "bg08": 8, "bg0a": 10, "bg0b": 11, "bg0c": 12, "bg0d": 13,
          "bg0e": 14, "bg0f": 15, "bg10": 16}


def palettes_du_decor(bg):
    bd = BANDES[bg]
    j1 = transfert(u16(IDX_JEU1 + bd * 2))
    j2 = transfert(u16(IDX_JEU2 + bd * 2))
    return dict(bande=bd, jeu1=j1, jeu2=j2)


def decor_vers_bande():
    """(decor, aire) -> bande. Le decor 8 porte les bandes 8, 9 et 9."""
    return {d: [u16(DECOR_VERS_BANDE + (d * 3 + a) * 2) for a in range(3)]
            for d in range(17)}


# LES FORMATS D'ENREGISTREMENT, LUS DANS LE CODE DES LECTEURS.
#
# Le spawner dedie de Hugo, `0x8C036480`, a ete desassemble le 02/09 : neuf `mov.w @r14+`
# de deux octets, donc 18 par enregistrement, et chaque champ va a un offset d'objet que
# le code donne en clair (`mov #N,r0` puis `mov.w r3,@(r0,r4)`) :
#
#     champ 0 -> objet+32                 champ 5 -> objet+88   PALETTE
#     champ 1 -> objet+558   PLAN         champ 6 -> objet+456  SCRIPT
#     champ 2 -> objet+554   DRAPEAUX     champ 7 -> objet+68
#     champ 3 -> objet+102   X            champ 8 -> objet+118
#     champ 4 -> objet+106   Y
#
# Les deux offsets 558 et 556 ne sont pas devines : ils sont charges par un `mov.w
# @(disp,PC)` dont le litteral vaut 558 et 556, et 554 = 558-4, 456 = 556-100.
FORMATS = {
    "annuaire_elements": dict(pas=16, depuis_pointeur=2,
                              champs=dict(plan=0, drapeaux=2, x=4, y=6, palette=8, script=10)),
    "chargeur_0x8C025A9A": dict(pas=16, depuis_pointeur=2,
                                champs=dict(plan=0, drapeaux=2, x=4, y=6, palette=8, script=10)),
    "chargeur_0x8C02E1FE": dict(pas=16, depuis_pointeur=2,
                                champs=dict(plan=0, drapeaux=2, x=4, y=6, palette=8, script=10)),
    "spawner_dedie_18o": dict(pas=18, depuis_pointeur=0,
                              champs=dict(inconnu32=0, plan=2, drapeaux=4, x=6, y=8,
                                          palette=10, script=12, inconnu68=14,
                                          inconnu118=16),
                              lu_dans="0x8C036480, desassemble le 02/09/2026"),
}

# Les spawners dedies et le bloc qu'ils portent EN DUR, releves par `chargeurs2i.py`.
SPAWNERS = {
    "bg00": [("0x8C0258DA", "0x8C17C190"), ("0x8C04AE04", "0x8C183DC8")],
    "bg01": [("0x8C0323F0", "0x8C17F2D8")],
    "bg02": [("0x8C036688", "0x8C17F5B8")],
    "bg03": [("0x8C02936E", "0x8C123DA0")],
    "bg04": [("0x8C0323F0", "0x8C17F2D8")],
    "bg06": [("0x8C036480", "0x8C17F54C")],
    "bg08": [("0x8C03CBCC", "0x8C17FD04")],
    "bg10": [("0x8C02C68A", "0x8C17E4C0")],
}


def main():
    import bases
    import fetc
    import annuaire2i as AN
    import poser2i as P
    import sh4

    def u8b(a):
        return sh4.D[sh4.a2o(a)]

    out = dict(
        binaire="SF3_2ND.BIN",
        adresses=dict(transferts=hex(TRANSFERTS), index_jeu1=hex(IDX_JEU1),
                      index_jeu2=hex(IDX_JEU2), decor_vers_bande=hex(DECOR_VERS_BANDE),
                      ram_palettes=hex(RAM_PALETTES),
                      table_maitresse_scripts="0x8C5F9B38",
                      scripts_etage="0x8C1D3FB4 (indexee par la BANDE, pas le decor)"),
        vert_case_vide=hex(VERT_VIDE),
        formats=FORMATS,
        spawners_dedies=SPAWNERS,
        decor_vers_bande=decor_vers_bande(),
        decors={},
    )

    par_bg = P.decor_de_chaque_bloc()

    # DEUX DECORS N'ONT PAS DE BLOC STATIQUE, ET LE TABLEAU LES PERDAIT.
    #
    # `decor_de_chaque_bloc` nomme un decor par le bloc d'ELEMENTS que son script d'etage
    # charge. `bg08` et `bg0a` n'en ont aucun (le code dit zero element pour Oro), donc ils
    # n'y figurent pas -- et l'inventaire les sortait a « 0 script, 0 element », comme s'ils
    # etaient vides. Ils ne le sont pas : leurs objets ANIMES sont poses, et leur numero de
    # decor est etabli par l'appelant de leur chargeur, ce que `animer2i.TABLES` porte.
    import animer2i as AM

    for bg, blocs in AM.TABLES.items():
        par_bg.setdefault(bg, blocs[0]["decor"])

    for bg in sorted(bases.ASSETS):
        d = par_bg.get(bg)
        info = dict(asset=bases.ASSETS[bg], decor=d, palettes=palettes_du_decor(bg))

        chemin = os.path.join(RACINE, "sprites", bases.ASSETS[bg])
        a = fetc.lire(open(chemin, "rb").read())
        lo, hi = a["index_global"]
        info["sprites_dans_asset"] = len(a["sprites"])
        info["anims_dans_asset"] = len(a["anims"])
        info["index_global"] = [lo, hi]

        if d is not None:
            t, n = AN.table_scripts(d)
            info["table_scripts"] = hex(t)
            scripts = {}

            for sc in range(n):
                p = u32(t + sc * 4)
                im = []
                for k in range(96):
                    cmd, duree, idx = u8b(p + k * 8), u8b(p + k * 8 + 1), u16(p + k * 8 + 6)
                    if cmd == 0x01:
                        break
                    if cmd == 0x00 and duree:
                        im.append(idx)
                if im:
                    scripts[sc] = dict(images=len(im),
                                       dans_asset=sum(1 for i in im if lo <= i < hi))
            info["scripts"] = scripts
            info["elements_jeu1"] = len(AN.elements(d))
            info["elements_jeu2"] = u16(0x8C17BBC4 + d * 3 * 2)

        out["decors"][bg] = info

    io.open(SORTIE, "w", encoding="utf-8").write(
        json.dumps(out, indent=1, ensure_ascii=False, sort_keys=True))

    print("ecrit %s" % SORTIE)
    print()
    print("decor | asset | scripts | resolus | poses par la chaine | elements j1+j2")
    print("--------------------------------------------------------------------------")
    for bg, i in sorted(out["decors"].items()):
        sc = i.get("scripts", {})
        res = sum(1 for v in sc.values() if v["images"] and v["dans_asset"] == v["images"])
        print("  %-5s %5d   %4d      %4d                      %d + %d"
              % (bg, i["sprites_dans_asset"], len(sc), res,
                 i.get("elements_jeu1", 0), i.get("elements_jeu2", 0)))


if __name__ == "__main__":
    main()
