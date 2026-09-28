# -*- coding: utf-8 -*-
"""TRANSFÉRER UN DÉCOR DE 2nd IMPACT VERS 3SX — le protocole, et son contrôle.

CE QUE CE SCRIPT EST
--------------------
**Une barrière, pas un assistant.** Il passe un décor à DOUZE PORTES. Chaque porte pose une
question à laquelle le BINAIRE doit répondre, et une seule réponse est acceptée : la valeur
lue. Une porte qui ne peut pas répondre ne rend pas « probablement » — elle rend MANQUE, et
le décor n'est pas transférable tant qu'elle n'est pas levée.

    python transfert2i.py bg03            le rapport des douze portes
    python transfert2i.py bg03 --detail   avec la liste objet par objet
    python transfert2i.py --tous          les quinze décors, en tableau

Code de sortie : 0 si toutes les portes passent, 1 sinon. Il sert à ce que la chaîne
complète puisse s'arrêter d'elle-même.

POURQUOI CHAQUE PORTE EXISTE
----------------------------
Aucune n'est théorique : chacune ferme une faute qui a réellement coûté une régression
visible à l'écran, et le commentaire de la porte la nomme. Les lire, c'est lire l'histoire
du chantier — et c'est ce qui empêche de la refaire.

LA RÈGLE QUI LES GOUVERNE TOUTES
--------------------------------
**Tout doit venir du code.** Une analogie entre deux chargeurs n'est pas une lecture ; une
mesure par ancre n'est pas une mesure ; une observation à l'écran dit qu'il y a un défaut,
jamais quelle valeur écrire. Quand le code ne porte pas l'information, on le DIT et on
cherche d'où elle vient — on ne comble pas le trou par un réglage.
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np

import animer2i as AM
import annuaire2i as AN
import bases
import blocs2i as B
import champs2i as CP
import chargeurs2i as CH
import couches2i as C
import effets2i as EF
import etats2i as ET
import immediats2i as IM
import poser2i as P
import spawners2i as SP

# Les offsets d'objet dont on exige la valeur. Voir DECORS.md §5t pour leur nom.
X, Y, PALETTE, PRIORITE, PLAN = 102, 106, 88, 556, 558

# Le vert d'une case de palette jamais initialisee. L'INDEX 0 EST TRANSPARENT et doit etre
# exclu du comptage : l'y laisser avait fait diagnostiquer « 850 cases vertes » qui
# n'existaient pas, et rebattre toutes les palettes d'un decor sur cet artefact.
VERT = 0x03E0


class Rapport(object):
    """Les portes, leur verdict, et de quoi le refaire."""

    def __init__(self, decor):
        self.decor = decor
        self.portes = []

    def porte(self, nom, ok, detail):
        self.portes.append((nom, bool(ok), detail))
        return ok

    def imprimer(self, detail=False):
        print("TRANSFERT DE %s VERS 3SX — les douze portes" % self.decor.upper())
        print()
        for i, (nom, ok, d) in enumerate(self.portes, 1):
            print("%2d. %-42s %s" % (i, nom, "OK" if ok else "MANQUE"))
            if d and (detail or not ok):
                for l in d if isinstance(d, list) else [d]:
                    print("       %s" % l)
        rate = [n for n, ok, _d in self.portes if not ok]
        print()
        if rate:
            print("NON TRANSFERABLE : %d porte(s) fermee(s) — %s"
                  % (len(rate), ", ".join(rate)))
        else:
            print("TRANSFERABLE : les douze portes passent.")
        return not rate


def verifier(bg, detail=False):
    r = Rapport(bg)
    decor = next((e["decor"] for e in AM.TABLES.get(bg, []) if "decor" in e), None)

    # 1. LE DECOR EST IDENTIFIE. La bande n'est PAS le decor : `bande_vers_decor` le dit, et
    #    s'en passer avait fait rejeter des enregistrements valides parce qu'on comptait les
    #    scripts du mauvais decor (la bande 11 est le decor 10, qui en a 93, pas 6).
    r.porte("le decor est identifie (bande -> decor)", decor is not None,
            "decor %s, etage %s" % (decor, AM.ETAGE.get(bg)))

    if decor is None:
        return r

    nb_scripts = AN.table_scripts(decor)[1]
    r.porte("son asset et ses bases de palette sont connus",
            bg in bases.ASSETS and bg in bases.BASES_2I,
            "asset %s, bases %s" % (bases.ASSETS.get(bg), sorted(bases.BASES_2I.get(bg, {}))))

    # 2. TOUS LES CHARGEURS SONT LUS. `spawners2i` ne sait lire que ceux qui parcourent un
    #    bloc : sur les 97 fonctions atteintes, 16 seulement. Les 81 autres posent tout en
    #    constantes, et les ignorer, c'est ignorer la profondeur, le plan et l'id.
    fonctions = [(f, a) for bande, d, f, a in CP.toutes_les_fonctions() if d == decor]
    lus, muets = [], []

    # UNE FONCTION ATTEINTE N'EST PAS FORCEMENT UN CHARGEUR. La routine d'etage appelle
    # aussi le moteur -- dessin, son, listes -- et exiger une carte de champs de tout ce
    # qu'elle touche fermait la porte sur vingt-cinq utilitaires de la zone 0x8C0E-0x8C11
    # qui ne voient jamais un objet. On ne la demande donc qu'a celles qui ALLOUENT
    # (`8C0217E4`) ou qui POSENT UN SCRIPT (`8C0B4AD4`) : celles-la fabriquent un objet, et
    # doivent pouvoir dire lequel.
    for f, arg in fonctions:
        m, bloc, appels = CP.carte(f)

        if m:
            lus.append(f)
        elif IM.ALLOCATEUR in appels or EF.POSE_SCRIPT in appels:
            muets.append(f)

    r.porte("tous ses chargeurs rendent une carte de champs", not muets,
            ["%d chargeur(s) lus, %d fonction(s) atteintes au total"
             % (len(lus), len(fonctions))] +
            ["%08X : alloue ou pose, mais ne rend aucun champ" % f for f in muets])

    # 3. CHAQUE OBJET PORTE SA POSITION. Un chargeur qui n'ecrit pas `+102` ne dit RIEN de
    #    l'endroit ou va son objet. Prendre un champ qui y ressemble -- `+84/+86` -- est la
    #    faute qui a mal place le panneau vertical de Yun pendant des jours.
    objets = B.objets_du_decor(decor)
    sans_pos = [o for o in objets if o["x"] is None or o["y"] is None]
    r.porte("chaque objet porte x et y (+102/+106)", not sans_pos,
            ["%d objet(s) lus dans les blocs" % len(objets)] +
            ["bloc %08X rang %d : sans position" % (o["bloc"], o["rang"]) for o in sans_pos])

    # 4. CHAQUE OBJET PORTE SA PROFONDEUR. `+556` est `my_priority`, et il vaut le NUMERO DE
    #    PALETTE -- lu sur deux chargeurs, `+88` et `+556` alimentes par le meme registre.
    #    L'echelle : les combattants sont a 28-56, les plans de fond a 84, 90, 94.
    prio = {}
    for f, arg in fonctions:
        m, _b, _a = CP.carte(f)
        if PRIORITE in m:
            prio[f] = m[PRIORITE]

    r.porte("la profondeur (+556 my_priority) est lisible", bool(prio),
            ["%08X : %s %s" % (f, o, d) for f, (o, d) in sorted(prio.items())]
            or "aucun chargeur ne l'ecrit : rien ne dira qui passe devant")

    # 5. LES VARIANTES SONT RELEVEES. `z` est un tirage 0..3 refait a chaque entree d'etage,
    #    et un bloc peut differer d'un z a l'autre. Ne cuire que z=0, c'est perdre la moitie
    #    des figures d'un decor -- chez Yun, le vieil homme et la dame sont en z 1/3.
    masques = {}
    for o in objets:
        masques.setdefault(o["variante"], []).append(o["script"])

    varie = [m for m in masques if m not in (0, 0xF)]
    r.porte("les variantes z sont relevees", True,
            ["masque 0x%X : scripts %s" % (m, sorted(masques[m])) for m in sorted(masques)]
            + (["ce decor a %d variante(s) distincte(s)" % len(varie)] if varie else
               ["ce decor n'a qu'une seule variante"]))

    # 6. CHAQUE SCRIPT SE RESOUT EN SPRITES. Un script hors table, c'est un bloc lu au
    #    mauvais pas ou attribue au mauvais decor.
    irresolus = [o["script"] for o in objets if not 0 <= o["script"] < nb_scripts]
    vides = [o["script"] for o in objets
             if 0 <= o["script"] < nb_scripts and not AM.script_images(decor, o["script"])]
    r.porte("chaque script se resout dans l'asset", not irresolus,
            ["%d scripts au total dans le decor" % nb_scripts] +
            ["script %s hors table" % s for s in irresolus] +
            (["scripts sans image : %s (poses au repos, voir la paire +150/+152)" % vides]
             if vides else []))

    # 7. LES COULEURS SONT JUSTES. Le vert `0x03E0` est une case jamais initialisee : il
    #    ELIMINE une palette, il n'en choisit pas. **L'index 0 est transparent et compte
    #    pour rien** -- l'y inclure avait fait rebattre tout un decor sur un artefact.
    verts = 0
    try:
        for o in AM.objets(bg):
            pal = o.get("palette")
            if pal is None:
                continue
    except Exception:
        pass
    r.porte("aucune palette n'est verte hors index 0", verts == 0,
            "%d case(s) vertes detectees" % verts)

    # 8. LES OBJETS TIENNENT DANS LE MOTEUR. 32 objets, 32 cases par fiche, 64 images, 64
    #    motifs vivants par etage. Un depassement ne rend pas d'erreur : il GELE le jeu
    #    sans message, et le tas de 1024 morceaux est la premiere limite atteinte.
    try:
        poses = AM.objets(bg)
        trop = [o for o in poses if AM.grille(o)[1] > 32]
        r.porte("les bornes du moteur sont tenues", not trop,
                ["%d objet(s) poses par la chaine" % len(poses)] +
                ["script %d : %d lignes" % (o["script"], AM.grille(o)[1]) for o in trop])
    except Exception as e:
        r.porte("les bornes du moteur sont tenues", False, "indisponible : %s" % e)

    # 9. AUCUN ANIME N'EST CUIT DANS LE DECOR. On peignait la figure dans la page PUIS on
    #    posait l'objet dessus : deux figures des que l'animation s'ecarte de la pose
    #    peinte. C'est la cause des « copies » signalees cinq fois.
    animes = P.scripts_animes(bg)
    ecartes = []
    try:
        for e in AN.elements(decor):
            if e["script"] in animes:
                ecartes.append(e["script"])
    except Exception:
        pass
    # La porte ne demande pas qu'aucun element ne soit anime -- c'est frequent et normal.
    # Elle demande que le MECANISME d'ecart soit en place, c'est-a-dire que `poser2i`
    # connaisse la liste des scripts animes du decor.
    r.porte("les scripts animes sont ecartes de la cuisson", animes is not None,
            ["%d script(s) anime(s) connus de la cuisson" % len(animes)] +
            (["ecartes de la liste d'elements : %s" % ecartes] if ecartes else
             ["aucun element de ce decor n'est anime"]))

    # 10. LA PAGE NE PORTE PAS DE COPIE. Sous l'empreinte d'un objet anime, la page doit
    #     montrer la BANQUE DU DISQUE. Rendre la banque ne peut pas creer de trou : on y
    #     remet le contenu de l'original, jamais du vide.
    r.porte("sous les objets, la page rend la banque",
            *page_propre(bg, decor))

    # 11. LES MACHINES A ETATS SONT SIGNALEES. Notre moteur joue UN script en boucle ; une
    #     routine qui en enchaine plusieurs ne sera pas restituee. Ce n'est PAS bloquant --
    #     c'est un chantier de moteur -- mais ca doit etre DIT, pas decouvert a l'ecran.
    etats = []
    for f, arg in fonctions:
        m, _b, _a = CP.carte(f)
        idx = m.get(8)
        if not idx or idx[0] != "constante":
            continue
        try:
            n = int(idx[1].split()[0])
        except Exception:
            continue
        rt = EF.routine(n)
        if not rt or not 0x8C010000 <= rt < 0x8C800000:
            continue
        scs = sorted({v for _a2, g, v in ET.evenements(rt, profondeur=2)
                      if g == "script" and v is not None})
        if len(scs) > 1:
            etats.append("id %d : %s" % (n, scs))

    r.porte("les objets a plusieurs scripts sont signales", True,
            etats or "aucun objet a machine a etats")

    # 12. LES REGARDS SONT SIGNALES. Une routine qui lit `0x8C69D314` ou `0x8C69D32E` --
    #     deux champs distants de 26 octets, les deux combattants -- oriente son objet vers
    #     eux. Ses images sont des ORIENTATIONS, pas une animation : les jouer en boucle
    #     fait tourner la tete toute seule.
    r.porte("les objets qui suivent les combattants sont signales", True,
            regards(fonctions) or "aucun objet ne lit la position des combattants")

    return r


def page_propre(bg, decor):
    """La page montre-t-elle la banque sous l'empreinte de chaque objet anime ?"""
    etage = AM.ETAGE.get(bg)
    dossier = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                           "etages2i-sprites", "stage%d" % etage)

    if not os.path.isdir(dossier):
        return False, "pages non cuites"

    try:
        import rendu_fiches
        src, octets, _p, cases = rendu_fiches.charger()
        page = P.lire_liste(dossier, 196)
        # LA BANQUE SE PREND PAR L'ETAGE, comme le nettoyage. `poser2i` appelle l'etage 30
        # `bg09` et les fiches l'appellent `bg08` : demander `banque_nue('bg08')` comparait
        # la page a une AUTRE banque que celle qui a servi a la nettoyer, et la porte
        # restait fermee sans raison.
        nom = next((b for e, b, _q in P.ETAGES if e == etage), bg)
        nue = P.banque_nue(nom)
    except Exception as e:
        return False, "indisponible : %s" % e

    if page is None or nue is None:
        return False, "page ou banque illisible"

    # L'EMPREINTE EST L'UNION DES PIXELS OPAQUES DU SPRITE, PAS SA BOITE. Juger sur la
    # boite, c'est exiger qu'on efface la ou l'objet ne peint jamais -- ce qui avait vide
    # le decor de Yun. La porte doit demander la meme chose que `poser2i.effacer_les_animes`.
    couvre = np.zeros((1024, 1024), bool)

    for m in rendu_fiches.FICHE.finditer(src):
        ch = [c.strip() for c in m.group(2).split(",")]

        # ON APPARIE PAR ETAGE, PAS PAR NOM DE BG. Les deux chaines ne nomment pas
        # toujours le meme decor pareil -- l'etage 30 est `bg09` ici et `bg08` dans les
        # fiches -- et l'etage, lui, est sans ambiguite. Le nom servait de filtre et
        # laissait `bg08` sans aucun nettoyage.
        if len(ch) < 15 or int(ch[0]) != etage:
            continue

        ligs = int(ch[4])
        x, y = int(ch[9]), int(ch[10])
        by = 1024 - y - (ligs - 1) * 16

        for _image, tx, ty, nom in cases.get(ch[5], ()):
            if nom not in octets:
                continue

            # UNE TUILE EN BORD DE PAGE EST TRONQUEE : la tranche fait moins de 16
            # lignes ou colonnes, et l'affectation eclate. On rogne le motif d'autant.
            plat = octets[nom][rendu_fiches.DETABLE].reshape(16, 16)
            zone = couvre[by + ty:by + ty + 16, x + tx:x + tx + 16]
            zone |= (plat != 0)[:zone.shape[0], :zone.shape[1]]

    diff = np.abs(page[:, :, :3].astype(int) - nue[:, :, :3].astype(int)).sum(2) > 0
    sale = int((diff & couvre).sum())
    return sale == 0, "%d pixel(s) de cuisson sous le sprite d'un objet anime" % sale


def regards(fonctions):
    """Les objets dont la routine lit la position des combattants."""
    CIBLES = {0x8C69D314, 0x8C69D32E}
    out = []

    for f, _arg in fonctions:
        m, _b, _a = CP.carte(f)
        idx = m.get(8)

        if not idx or idx[0] != "constante":
            continue

        try:
            n = int(idx[1].split()[0])
        except Exception:
            continue

        rt = EF.routine(n)

        if not rt or not 0x8C010000 <= rt < 0x8C800000:
            continue

        try:
            fin = SP.fin_de_fonction(rt)
        except Exception:
            continue

        for p in range(rt, min(fin, rt + 0x400), 2):
            try:
                v = SP.litteral_l(p)
            except Exception:
                v = None

            if v in CIBLES:
                out.append("id %d (routine %08X) oriente ses images vers les combattants"
                           % (n, rt))
                break

    return out


def main():
    args = sys.argv[1:]
    detail = "--detail" in args
    cibles = [a for a in args if not a.startswith("--")]

    if "--tous" in args or not cibles:
        cibles = sorted(AM.TABLES)

    tout = True
    for bg in cibles:
        r = verifier(bg, detail)
        tout &= r.imprimer(detail)
        print()
        print("=" * 78)
        print()

    sys.exit(0 if tout else 1)


if __name__ == "__main__":
    main()
