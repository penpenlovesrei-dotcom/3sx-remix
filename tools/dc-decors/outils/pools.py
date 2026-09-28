# -*- coding: utf-8 -*-
"""Ce que le champ `tuile` d'un morceau indexe -- etabli, puis mesure.

LA CHAINE, lue dans SF3_2ND.BIN
-------------------------------
La boucle de dessin `0x8C0F693C` prend un enregistrement de 16 octets et, pour chaque
tuile du morceau, appelle `0x8C0F719E` avec trois arguments :

    r4 = palette      <- mot a `enr+2`, masque 0x1FF (c'est le champ palette du fichier)
    r5 = tuile        <- mot a `enr+0`, **incremente d'une tuile a l'autre**
    r6 = cle          <- mot a `enr+12`

`0x8C0F719E` n'est qu'un cache : table de hachage de 32768 entrees en `0x8C6E6918`,
enregistrements de 16 octets en `0x8C6F6918`, identite sur 32 bits

    (palette << 22) | ((cle & 127) << 15) | tuile

-- donc **la tuile tient sur 15 bits et n'a de sens que dans le contexte d'une cle**.
En cas d'absence, le triplet {cle, palette, tuile} est empile sur 6 octets dans la file
`0x8C704E54`, que `0x8C0F6D30` vide ; le chargement se fait en `0x8C0F6DC6` :

    bloc     = tuile >> 4          (>> 3 si la cle vaut 0x0160)
    rang     = tuile & 15
    fiche    = 0x8C602384 + (cle & 0xFF) * 24
    fn       = fiche[+8]  ; source = fiche[+12]
    fn(bloc, tampon, source)                       -> 4096 octets degonfles
    tuile 8 bits = tampon[rang * 256 : rang * 256 + 256]      (16x16, ligne par ligne)

Le degonfleur `0x8C0F6548` lit `source` comme `{u32 nombre, u32 offsets[nombre]}`, les
offsets etant relatifs a `source`, et ecrit ses 4096 octets **a rebours**. C'est mot pour
mot la section 3 d'un asset `F_ETCnn` (`fetc.py`), et `blocs[i]` de `fetc.lire()` est
exactement ce que `fn(i, ...)` degonfle.

Le cache de blocs `0x8C0F648E` garde huit blocs de 4096 octets en `0x8C6DE900`.

DONC
----
    tuile = bloc * 16 + rang, dans le **pool de tuiles de l'asset F_ETC** que designe
    l'octet bas de `enr+12`. Base zero : la tuile 0 est la premiere tuile du bloc 0.

La table `0x8C602384` est la table d'installation des assets decrite en tete de
`fetc.py` : `+4` les donnees, `+8` la fonction, `+12` les donnees + `hdr[0x14]`
(la section graphique), `+16` les animations, `+20` la cle elle-meme.

CE QUE CE PROGRAMME FAIT
------------------------
Il ne raconte pas ce qui precede, il le verifie sur les dix-sept etats Flycast :

1. pour chaque cle employee par les morceaux, il lit la fiche, suit `+12`, y lit le
   nombre de blocs, et **verifie que toutes les tuiles employees tombent dedans**
   (`tuile >> 4 < nombre de blocs`) -- une prediction qui peut echouer ;
2. il identifie l'asset **par ses octets**, en cherchant la section graphique de la RAM
   dans les fichiers de `sprites/` -- correspondance exacte, pas une heuristique.

    lanceur : pools.cmd
"""
import glob, json, os, struct, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import flycast as F
import etat as E

ICI     = os.path.dirname(os.path.abspath(__file__))
RACINE  = os.path.dirname(ICI)
DOS     = os.path.join(os.path.expanduser("~"), "Documents", "Dreamcast", "data")
MOTIF   = "Street Fighter III - Double Impact*.state"

FICHES  = 0x8C602384      # table d'installation des assets, 24 octets par entree
NB_FICHES = 256
CLE_DEMI = 0x0160         # la seule cle dont le bloc se prend en tuile >> 3


def fiche(ram, k):
    a = FICHES + k * 24
    w = [F.u32(ram, a + i) for i in range(0, 24, 4)]
    return dict(k=k, drapeau=w[0], donnees=w[1], fn=w[2],
                graphique=w[3], anims=w[4], cle=w[5])


def nb_blocs(ram, p):
    """Le premier u32 de la section graphique : le nombre de blocs."""
    if not (0x8C000000 <= p < 0x8D000000):
        return None
    n = F.u32(ram, p)
    return n if 0 < n < 100000 else None


def assets():
    """Les assets F_ETC extraits, par nom -> octets de leur section graphique."""
    import fetc
    out = {}
    for c in sorted(glob.glob(os.path.join(RACINE, "sprites", "*.bin"))):
        d = open(c, "rb").read()
        try:
            s3 = struct.unpack_from("<8I", d, 0)[5]
        except struct.error:
            continue
        if 0 < s3 < len(d):
            out[os.path.basename(c)[:-4]] = d[s3:]
    return out


def nomme(temoin, ass):
    """Le nom de l'asset dont la section graphique commence par `temoin`."""
    return [n for n, d in ass.items() if d[:len(temoin)] == temoin]


def etats():
    return sorted(glob.glob(os.path.join(DOS, MOTIF)))


def morceaux_json(nom_etat):
    """Les morceaux deja releves pour cet etat, s'ils existent."""
    for c in glob.glob(os.path.join(RACINE, "releves2", "*.json")):
        r = json.load(open(c, encoding="utf-8"))
        if r["etat"] == nom_etat:
            return r["decors"], r["morceaux"]
    return None, None


def main():
    ass = assets()
    print(f"{len(ass)} assets F_ETC extraits dans sprites/\n")
    total = bon = 0
    recap = {}
    for chemin in etats():
        nom_etat = os.path.basename(chemin)
        decors, ms = morceaux_json(nom_etat)
        if ms is None:
            print(f"{nom_etat} : pas de releve dans releves2/, ignore")
            continue
        ram, _ = F.lire_ram(chemin, E.EXE)
        # les cles employees, et pour chacune la plus grande tuile demandee
        par_cle = {}
        for m in ms:
            c = m["palette"]          # nom historique du champ enr+12 : c'est la cle
            t = m["tuile"]
            d = par_cle.setdefault(c, dict(n=0, tmax=-1))
            d["n"] += 1
            d["tmax"] = max(d["tmax"], t)
        print(f"=== {nom_etat}   {'+'.join(decors) or 'inconnu'} ===")
        for c in sorted(par_cle):
            f = fiche(ram, c & 0xFF)
            nb = nb_blocs(ram, f["graphique"])
            d = par_cle[c]
            pas = 3 if c == CLE_DEMI else 4
            bloc_max = d["tmax"] >> pas
            temoin = ram[f["graphique"] - F.BASE_RAM:
                         f["graphique"] - F.BASE_RAM + 256] if nb else b""
            noms = nomme(temoin, ass) if nb else []
            if nb is not None:
                total += 1
                ok = bloc_max < nb
                bon += ok
                verdict = "ok" if ok else "HORS BORNES"
            else:
                verdict = "fiche vide"
            recap.setdefault(c, set()).update(noms)
            print(f"  cle {c:#06x} ({c & 0xFF:3d})  {d['n']:5d} morceaux  "
                  f"tuile max {d['tmax']:5d} -> bloc {bloc_max:4d} / "
                  f"{nb if nb is not None else '-':>4}  {verdict:11s} "
                  f"cle inscrite {f['cle']:#06x}  {', '.join(noms) or ''}")
        print()
    print(f"\nToutes tuiles dans les bornes de leur pool : {bon}/{total} couples "
          f"(etat, cle)\n")
    print("Cle -> asset, sur l'ensemble des etats :")
    for c in sorted(recap):
        if recap[c]:
            print(f"  {c:#06x} ({c & 0xFF:3d})  {', '.join(sorted(recap[c]))}")


if __name__ == "__main__":
    main()
