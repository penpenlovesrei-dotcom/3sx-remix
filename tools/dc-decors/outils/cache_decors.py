# -*- coding: utf-8 -*-
"""UN CACHE PAR DECOR, POUR NE PAS REFAIRE LES TRENTE-DEUX A CHAQUE ESSAI -- 25/09/2026.

POURQUOI
--------
Frederic, le 25/09 : « *tes actions sont tres longues* », puis « *pourquoi c'est aussi
long ?* ». Mesure, avant d'ecrire une ligne :

    animer2i.py     13 decors de 2nd Impact       ~2 min
    animerng.py     19 bandes de New Generation   ~3 min, dont 67 s rien que pour
                                                  preparer les pages animees (20 s par
                                                  bande d'Ibuki)
    couchesng.py    les pages des 19 bandes       ~1 min

Chaque decor est calcule INDEPENDAMMENT des autres -- decodage des sprites, decoupe en
tuiles, groupes de palettes -- et seule la fin est globale (l'index `decor_anim_par_etage`
et l'ecriture du `.c`, qui coutent une seconde). Corriger UN decor recalculait donc les
trente et un autres pour rien.

LE PIEGE, ET C'EST LE SEUL
--------------------------
Un cache qui ne se perime pas sert de vieilles donnees EN SILENCE. C'est exactement la
faute qui a ampute New Generation le 24/09 -- 771 fiches tombees a 246 sans que rien ne le
dise, trouve seulement parce que Frederic a signale un decor casse.

La cle porte donc DEUX choses :

  1. **l'empreinte des outils** : le contenu de tous les `.py` qui transforment une donnee
     en C, plus le binaire de la console. Un seul octet qui change, et tout se recalcule.

  2. **ce que le decor consomme vraiment** : pour New Generation, les enregistrements que
     `objetsng.enregistrements(bande)` rend, serialises. C'est ce qui permet de corriger
     `objetsng.py` sans tout refaire : si les enregistrements d'une bande n'ont pas bouge,
     sa sortie ne peut pas avoir bouge non plus.

C'est pour ca que les producteurs d'enregistrements sont ECARTES de l'empreinte de NG
(`SANS_EFFET["ng"]`) : leur influence passe ENTIEREMENT par ces enregistrements, qui sont
deja dans la cle. Si un jour l'un d'eux agit ailleurs, il faut le retirer de cette liste.

Pour 2nd Impact il n'y a pas de module d'enregistrements separe -- les tables sont DANS
`animer2i.py` -- donc l'empreinte porte tous les `.py` sauf ceux de New Generation, que
`animer2i` n'importe pas (verifie : aucun `import ...ng` dans `animer2i.py`).

ET ON LE DIT
------------
Chaque passage imprime, decor par decor, `cache` ou `calcule`. Un resultat faux reste donc
tracable. `--froid` refait tout sans lire le cache ; `--sans-cache` n'ecrit rien non plus.

    py -3 animerng.py --ecrire            avec le cache
    py -3 animerng.py --ecrire --froid    tout recalculer, et reecrire le cache
"""

import hashlib
import io
import os
import pickle
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
RACINE = os.path.dirname(ICI)
DOSSIER = os.path.join(ICI, "__cache_decors__")

BINAIRES = {"2i": "SF3_2ND.BIN", "ng": "SF3_1ST.BIN"}

# LES MODULES QUI N'ENTRENT PAS DANS L'EMPREINTE, ET POURQUOI.
#
# `ng` : les producteurs d'enregistrements. Tout ce qu'ils changent se voit dans
#        `objetsng.enregistrements(bande)`, qui est serialise dans la cle. Les recalculer
#        coute 9,5 s pour les dix-neuf bandes -- c'est le prix d'une cle honnete.
#
# `2i` : les outils de New Generation, qu'`animer2i` n'importe pas. Verifie le 25/09 :
#        `grep "import .*ng" animer2i.py` ne rend rien, et sa fermeture d'imports ne
#        contient aucun fichier en `ng.py`.
SANS_EFFET = {
    "ng": {"objetsng.py", "cheminng.py", "routineng.py", "decorsng.py", "apparier.py",
           "spawners2i.py", "immediats2i.py", "chargeurs2i.py", "blocsng.py",
           "exportng.py"},
    "2i": set(),
}


def _est_de_ng(nom):
    return nom.endswith("ng.py") or nom.endswith("_ng.py")


def fichiers(famille):
    """Les `.py` d'`outils` qui comptent pour cette famille, tries."""
    out = []
    for nom in sorted(os.listdir(ICI)):
        if not nom.endswith(".py"):
            continue
        if nom in SANS_EFFET.get(famille, ()):
            continue
        if famille == "2i" and _est_de_ng(nom):
            continue
        out.append(nom)
    return out


_EMPREINTES = {}


def empreinte(famille):
    """sha1 du contenu de tous les outils qui comptent, plus le binaire de la console."""
    if famille in _EMPREINTES:
        return _EMPREINTES[famille]

    h = hashlib.sha1()

    for nom in fichiers(famille):
        h.update(nom.encode("utf-8"))
        h.update(io.open(os.path.join(ICI, nom), "rb").read())

    b = os.path.join(RACINE, BINAIRES[famille])
    if os.path.exists(b):
        h.update(b"BIN")
        h.update(hashlib.sha1(io.open(b, "rb").read()).digest())

    _EMPREINTES[famille] = h.hexdigest()
    return _EMPREINTES[famille]


def cle(famille, quoi, extra=b""):
    """La cle d'un decor : l'empreinte des outils, son numero, ce qu'il consomme."""
    h = hashlib.sha1()
    h.update(empreinte(famille).encode("ascii"))
    h.update(str(quoi).encode("utf-8"))
    h.update(extra if isinstance(extra, bytes) else str(extra).encode("utf-8"))
    return "%s-%s-%s" % (famille, quoi, h.hexdigest()[:16])


def froid():
    return "--froid" in sys.argv


def muet():
    return "--sans-cache" in sys.argv


def lire(c):
    """La valeur rangee sous cette cle, ou None."""
    if froid() or muet():
        return None
    p = os.path.join(DOSSIER, c + ".pkl")
    if not os.path.exists(p):
        return None
    try:
        with io.open(p, "rb") as f:
            return pickle.load(f)
    except Exception as exc:
        # Un cache illisible n'est jamais une raison de produire un C faux : on le dit
        # et on recalcule.
        print("   CACHE illisible (%s) : on recalcule" % exc)
        return None


def ecrire(c, valeur):
    if muet():
        return
    if not os.path.isdir(DOSSIER):
        os.makedirs(DOSSIER)
    p = os.path.join(DOSSIER, c + ".pkl")
    tmp = p + ".tmp"
    with io.open(tmp, "wb") as f:
        pickle.dump(valeur, f, protocol=2)
    if os.path.exists(p):
        os.remove(p)
    os.rename(tmp, p)


def signature_enregistrements(enregs):
    """Ce qu'une bande consomme, en texte stable.

    On serialise TOUT ce que l'enregistrement porte, pas une selection de champs : un
    champ oublie serait un decor fige sur une vieille version. Les valeurs qui ne sont
    pas du JSON (tuples, numpy) passent par `repr`, ce qui reste stable d'un passage a
    l'autre parce qu'elles sortent des memes lectures du binaire.
    """
    import json

    def net(v):
        if isinstance(v, dict):
            return {str(k): net(x) for k, x in sorted(v.items(), key=lambda kv: str(kv[0]))}
        if isinstance(v, (list, tuple)):
            return [net(x) for x in v]
        if isinstance(v, (int, float, bool)) or v is None:
            return v
        if isinstance(v, str):
            return v
        return repr(v)

    return json.dumps([net(e) for e, _src in enregs], sort_keys=True).encode("utf-8")
