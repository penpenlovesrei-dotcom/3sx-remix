# -*- coding: utf-8 -*-
"""Les deux bandes de 2nd Impact qui n'avaient jamais ete montees : `bg08` et `bg10`.

POURQUOI ELLES MANQUAIENT. `etages.py` monte quinze etages pour dix-sept bandes, et saute
ces deux-la. La raison tient dans la table `0x8C1D591C`, qui donne `(decor*3 + aire) ->
bande` et que le sous-agent a trouvee sur New Generation avant qu'on la verifie sur 2I :

    decor 0..7   ->  bandes 0..7        identite
    decor 8      ->  bandes 8, 9, 9     DEUX bandes pour un seul decor
    decor 9..14  ->  bandes 10..15      tout est decale d'un cran ensuite

**`bg08` et `bg09` sont les deux VARIANTES d'un meme decor**, l'aire 0 contre les aires 1
et 2. C'est exactement le « decalage d'index a partir de l'etage 10 » que `SANS-ETAT.md`
constatait sans l'expliquer, et c'est ce qui rend `bg08` invisible : le port ne montait que
`bg09`.

`bg10` est un autre cas : le decor 16 a sa propre bande, et il partage seulement sa banque
de palettes avec `bg06`. Ce n'est pas une variante, c'est un decor a part entiere.

Les deux prennent les etages **56 et 57**, apres les dix-neuf de New Generation. Leurs
macros s'appellent `ETAGES2IBIS_*` et se posent APRES `ETAGESNG_*` : les macros sont
positionnelles, en glisser dans `ETAGES2I_*` decalerait tout New Generation.

    python etages2ibis.py             # dit ce qu'il ferait
    python etages2ibis.py --ecrire    # pose l'include, les archives et les pages
"""

import io
import os
import struct
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
sys.path.insert(0, ICI)

import numpy as np

import archive
import bande3sx
import couches2i
import pvc
from rendupvc import SIDE, carte_morton

BIN = open(os.path.join(RACINE, "SF3_2ND.BIN"), "rb").read()
BASE = 0x8C010000
TABLE_COEF = 0x8C1D4F48
PAS_COEF = 0x20
PAGES_PAR_PLAN = 32

# (etage, bande, decor, ce que c'est)
BANDES = [
    (56, 0x08, 8, "l'aire 0 du decor 8 -- la VARIANTE de bg09"),
    (57, 0x10, 16, "le decor 16, une bande a lui seul"),
]
PREMIER_FICHIER = 1569


def u32(a):
    return struct.unpack_from("<I", BIN, a - BASE)[0]


def coefs(decor, k):
    a = TABLE_COEF + decor * PAS_COEF + k * 8
    return u32(a), u32(a + 4)


def demi_banque(bande, banque, moitie):
    src = os.path.join(RACINE, "pvc-2i", "bg%02x.pvc" % bande)
    pages, _u, _ = pvc.decode(open(src, "rb").read())
    arr = bande3sx.banque_rgba(pages, banque * 4096, carte_morton(SIDE))[0]
    demi = arr[:512] if moitie == "haut" else arr[512:]
    out = np.zeros((1024, 1024, 4), np.uint8)
    out[512:] = demi
    return out


# LA VARIANTE D'ELENA A QUATRE PLANS -- 16/09/2026. Voir `statiques2i.variante_elena` :
# sa seule couche utile est le ciel ; le reste du decor est fait d'ELEMENTS STATIQUES et
# d'un pont, ranges ici par profondeur et par vitesse. Tout ce qui suit est lu :
#
#   plan 0  le ciel et le lac      profondeur de sa couche (94)   objet 0 de la bande
#   plan 1  falaises et pont       profondeur des falaises (78)   1 / 1, plan de base
#   plan 2  le rocher du plan 3    profondeur de l'element (79)   objet 2, ecrit en dur
#   plan 3  arbres a cranes        profondeur des elements (20)   1 / 1
#
# Un element plus pres que 28 -- le premier `my_pr` des combattants -- passe devant eux : il
# lui faut son propre plan.
def plans_variante(bande):
    import etages as _E
    import statiques2i as ST
    els = ST.elements_second_jeu(bande)
    proche = [e["profondeur"] for e in els if e["plan"] == 2 and e["profondeur"] >= 28]
    tiers = [e["profondeur"] for e in els if e["plan"] == 3]
    devant = [e["profondeur"] for e in els if e["plan"] == 2 and e["profondeur"] < 28]
    commun = lambda v: max(set(v), key=v.count)
    z = [_E.profondeur_couche(bande, 0, "haut", _E.Z_LOIN_DEFAUT),
         commun(proche), commun(tiers), commun(devant)]
    # TROIS PAGES, COMME AVANT -- remis le 27/09/2026 au soir.
    #
    # J'etais passe a DIX dans la journee : `verifier_objets` mesurait alors 1295 morceaux
    # vivants pour 768, soit 169 %. Mais ce chiffre venait du DECOUPAGE A 32 CASES, qui
    # donnait 91 fiches a l'etage 56 ; depuis qu'il est recoupe a 64 il n'en a que 46, et le
    # budget de trois pages redevient tenable. Et surtout : Frederic voit le decor GLITCHE
    # depuis que j'ai gonfle les budgets d'Elena. La memoire d'un cache d'objets sort du meme
    # allocateur que les pages du decor -- on ne la gonfle pas sans avoir mesure ce qu'elle
    # coute aux pages.
    return dict(n=4, z=z, tiers=_E.ECRASEMENTS["bg09"], quatre=coefs(bande, 1), ob_page=(3, 1))


def plans(bande, decor):
    if bande == 0x08:
        return plans_variante(bande)
    import etages as _E
    # QUATRE PAGES DE CACHE POUR HUGO BIS -- 16/09/2026 : il recoit ses objets (onze fiches,
    # dont la foule de Hugo). Hugo (etage 28) en demande 556 morceaux au pire, pour 1024.
    z = [_E.profondeur_couche(decor, 0, "haut", _E.Z_LOIN_DEFAUT),
         _E.profondeur_couche(decor, 0, "bas", _E.Z_PROCHE_DEFAUT)]

    # HUGO BIS EST LE MEME DECOR QUE HUGO -- sa couche proche ne dessine, elle aussi, que
    # x 0..511, et sa droite est l'element statique de profondeur 82. Voir
    # `etages.Z_PROCHE_ELEMENT`.
    nom = "bg%02x" % decor

    if nom in _E.Z_PROCHE_ELEMENT:
        z[1] = _E.Z_PROCHE_ELEMENT[nom]

    return dict(n=2, z=z,
                tiers=None, quatre=None, ob_page=(4, 1) if bande == 0x10 else (1, 1))


def ecrire_include(sortie):
    P_ = {b: plans(b, d) for _e, b, d, _q in BANDES}
    L = []
    L.append("/* Genere par dc-decors/outils/etages2ibis.py -- ne pas modifier a la main.")
    L.append(" *")
    L.append(" * Les deux bandes de 2nd Impact que `etages.py` ne montait pas : `bg08`")
    L.append(" * (l'aire 0 du decor 8, dont `bg09` est l'aire 1) et `bg10` (le decor 16).")
    L.append(" * Etages 56 et 57, apres les dix-neuf de New Generation.")
    L.append(" *")
    L.append(" * La table 0x8C1D591C de 2nd Impact donne (decor*3 + aire) -> bande, et dit")
    L.append(" * que le decor 8 porte les bandes 8, 9 et 9 : `bg08` est la VARIANTE du pont.")
    L.append(" * Elle a son etage entier (56) ; `bg_index_tbl[30]` ne la renvoie plus. */")
    L.append("")
    L.append("#define ETAGES2IBIS_USE_SCR \\")
    L.append("    " + ", ".join(str(P_[b]["n"]) for _e, b, _d, _q in BANDES))
    L.append("")
    L.append("#define ETAGES2IBIS_BGW_NUMBER \\")
    L.append("    " + ", ".join("{ %s }" % ", ".join(str(k + 1) for k in range(P_[b]["n"]))
                                for _e, b, _d, _q in BANDES))
    L.append("")
    L.append("#define ETAGES2IBIS_PRIORITY \\")
    # Lues dans SF3_2ND.BIN : table des couches 0x8C601EE8, elements statiques (+556).
    def mot(z):
        o = list(z) + [0] * (4 - len(z))
        return (o[0] << 24) | (o[1] << 16) | (o[2] << 8) | o[3]
    L.append("    " + ", ".join("0x%08X" % mot(P_[b]["z"]) for _e, b, _d, _q in BANDES))
    L.append("")
    L.append("#define ETAGES2IBIS_GBIX \\")
    L.append("    " + ", ".join("{ %s }" % ", ".join(["0xFFFFFFFF"] * P_[b]["n"])
                                for _e, b, _d, _q in BANDES))
    L.append("")
    L.append("#define ETAGES2IBIS_INDEX_TBL \\")
    L.append("    " + ", ".join("{ %d, %d, %d }" % (e, e, e) for e, _b, _d, _q in BANDES))
    L.append("")
    # Mesurees sur la page du plan de base -- voir `limites.py`.
    import limites
    L.append("#define ETAGES2IBIS_LIMIT \\")
    L.append("    " + ", ".join("{ %s }" % limites.trio(e) for e, _b, _d, _q in BANDES))
    L.append("")
    L.append("#define ETAGES2IBIS_MSP \\")
    L.append("    " + ", ".join(
        "{ { 0x%X, 0x%X }, { 0x10000, 0x10000 }, { 0x%X, 0x%X } }"
        % (coefs(d, 0) + (P_[b]["tiers"] or (0, 0)))
        for _e, b, d, _q in BANDES))
    L.append("")
    L.append("#define ETAGES2IBIS_OPAQUE \\")
    L.append("    " + ", ".join("0x80" for _ in BANDES))
    L.append("")
    L.append("#define ETAGES2IBIS_BGRW_ON \\")
    L.append("    " + ", ".join("{ -1, -1, -1, -1, -1, -1, -1, -1 }" for _ in BANDES))
    L.append("")
    L.append("#define ETAGES2IBIS_OB_PAGE \\")
    # La variante porte 20 fiches (herbes, deux cordes a crane) : 528 morceaux sur toutes
    # leurs images. Trois pages de 256 les tiennent meme si toutes vivaient a la fois.
    L.append("    " + ", ".join("{ %d, %d }" % P_[b]["ob_page"] for _e, b, _d, _q in BANDES))
    L.append("")
    L.append("#define ETAGES2IBIS_AKE_BG_OFF \\")
    L.append("    " + ", ".join(str((1 << P_[b]["n"]) - 1) for _e, b, _d, _q in BANDES))
    L.append("")
    for quoi, idx in (("X", 0), ("Y", 1)):
        L.append("#define ETAGES2IBIS_SPEED_%s_LOIN \\" % quoi)
        L.append("    " + ", ".join("[%d] = 0x%X" % (e, coefs(d, 0)[idx])
                                    for e, _b, d, _q in BANDES))
        L.append("")
    for nom in ("tiers", "quatre"):
        for quoi, idx in (("X", 0), ("Y", 1)):
            ent = ["[%d] = 0x%X" % (e, P_[b][nom][idx]) for e, b, _d, _q in BANDES if P_[b][nom]]
            L.append("#define ETAGES2IBIS_SPEED_%s_%s \\" % (quoi, nom.upper()))
            L.append("    " + (", ".join(ent) if ent else "[56] = 0"))
            L.append("")
    io.open(sortie, "w", encoding="utf-8").write("\n".join(L) + "\n")


def main():
    ecrire = "--ecrire" in sys.argv

    for etage, bande, decor, quoi in BANDES:
        cx, cy = coefs(decor, 0)
        print("etage %d  bg%02x  (decor %d)  %.4g / %.4g   %s"
              % (etage, bande, decor, cx / 65536, cy / 65536, quoi))
        for liste, (banque, moitie) in ((132, (0, "haut")), (196, (0, "bas"))):
            plan = demi_banque(bande, banque, moitie)
            print("   liste %3d  <-  banque %d %-4s  %7d px"
                  % (liste, banque, moitie, int((plan[:, :, 3] > 0).sum())))
            if ecrire:
                couches2i.ecrire_liste(
                    os.path.join(RACINE, "etages2i-sprites", "stage%d" % etage),
                    plan, liste)

    if not ecrire:
        print("\nRien n'a ete ecrit. `--ecrire` pour poser l'include, les archives et les pages.")
        return 0

    inc = "C:/Temp3sx/src/port/video/etages2ibis_plans.inc"
    ecrire_include(inc)
    print("\ninclude C ecrit : %s" % inc)

    dossier = os.path.join(os.environ.get("APPDATA", ""), "CrowdedStreet", "3SX",
                           "resources", "stages")
    os.makedirs(dossier, exist_ok=True)
    for i, (_e, _b, _d, _q) in enumerate(BANDES):
        archive.ecrire(2 * PAGES_PAR_PLAN,
                       os.path.join(dossier, "%d.bin" % (PREMIER_FICHIER + i)))
    print("%d archives ecrites dans %s" % (len(BANDES), dossier))
    return 0


if __name__ == "__main__":
    sys.exit(main())
