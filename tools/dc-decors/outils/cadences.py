# -*- coding: utf-8 -*-
"""Les cadences des sprites de decor de 2nd Impact : quelle image, tenue combien de trames.

TROUVE LE 29/08/2026, ET CA CORRIGE CE QUE CE FICHIER DISAIT
-----------------------------------------------------------
La version precedente tirait la duree d'une image de la **repetition** d'un enregistrement
dans la section 1 d'un `F_ETCnn`. C'etait faux, et trois decors -- `b01` alex, `b0c` ken,
`b0e` urien -- le montraient deja : leur flux ne liste chaque sprite qu'une fois. On en
avait conclu qu'ils etaient "degeneres" et que leur cadence etait dans le script d'etage.
Ni l'un ni l'autre.

**La cadence est dans une table de scripts, en clair dans le binaire.** Trois etages :

    0x8C5F9B38 + n*4     table maitresse, un pointeur par aire d'etage (souvent trois
                         pointeurs identiques par decor, mais pas toujours -- bg08 et
                         bg09 se partagent des entrees). On n'y indexe donc pas : on
                         parcourt les tables distinctes et on les NOMME par les assets
                         que leurs scripts citent.

    table -> [pointeurs] un pointeur par script, jusqu'a un mot qui n'est pas une adresse

    script -> suite d'enregistrements de HUIT octets :

        octet 0 : la commande
        octet 1 : la DUREE en trames, pour la commande 0x00
        u16 +2  : nul
        u16 +4  : nul
        u16 +6  : l'index global, celui de l'espace partage des `F_ETCnn`

    Les commandes relevees :

        0x00  afficher l'image `index` pendant `duree` trames
        0x01  fin du script
        0x0C  debut de boucle -- `index` porte le nombre de tours
        0x0D  fin de boucle
        0xFF        vu, role non etabli

    CORRIGE LE 23/09/2026, EN LISANT L'INTERPRETE :

    * le premier u16 d'un enregistrement vaut `commande | duree << 8`. L'interprete
      compare ce mot a 256 : en dessous c'est un OPCODE (duree nulle), au-dessus c'est
      une IMAGE. La commande 0x00 elle-meme ne fait rien -- son gestionnaire rend 1 et
      on avance ; tout l'affichage est dans le chemin des durees.
    * **la commande 0x02 n'existe pas** : ce sont les huit octets d'EN-TETE du script
      suivant, dont le premier mot est le pas d'avance de l'index (2). `poser_script`
      les lit en descendant depuis `script - 2` (2I 0x8C0B4FD8).
    * la commande 0x01 ne se contente pas de finir : elle rappelle `poser_script`, et
      c'est ce qui fait boucler l'animation sans rien d'exterieur.
    * la duree est tenue dans `objet[+469]`, l'octet haut du mot recopie en `+468` par
      le copieur d'enregistrement (2I 0x8C0B7324) ; elle est decrementee d'une trame
      par 2I 0x8C0B51F2 / NG 0x8C0337C2.

L'index global se resout comme partout ailleurs (voir DONNEES.md) :

    index >> 2 -> octet en 0x8C60A6D4 -> fiche de 24 octets en 0x8C602384

et, dans l'asset, `index - debut_du_span` est le numero d'**enregistrement** de la
section 1 -- pas le numero de sprite. C'est l'enregistrement qui porte l'ancre (x, y) et
qui designe le sprite par son offset.

CE QUI CONFIRME LE MODELE
-------------------------
* **3360 enregistrements d'affichage**, 537 scripts, dont 386 a deux images ou plus.
* **Toute** l'etendue des durees est celle d'une table de trames : 94 % valent 16 trames
  ou moins, avec des pics nets a 4, 6 et 8 ; le maximum est 250.
* **Tout sprite cite par un script est dans le flux de son asset** -- 100 % sur les
  quinze assets. L'inverse est faux : le flux porte aussi du mobilier, jamais anime.
* La repetition dans le flux, elle, ne coincide **pas** avec la duree du script : zero
  couple commun sur 222 pour `b02`, huit sur 629 pour `b0b`. La repetition n'est donc pas
  la duree, et le flux n'est pas un script.

    python cadences.py            toutes les cadences, table par table
    python cadences.py b01        seulement les tables qui citent cet asset
    lanceur : cadences.cmd
"""
import glob, itertools, os, sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)
RACINE = os.path.dirname(ICI)

import sh4

MAITRESSE = 0x8C5F9B38          # un pointeur par aire d'etage
NB_AIRES = 64
FIN = 0x01                      # commande de fin de script


def dans_le_binaire(v):
    return sh4.BASE <= v < sh4.BASE + len(sh4.D)


def assets():
    """Pour chaque `F_ETCnn` sorti : son span global et ses enregistrements de section 1."""
    import fetc
    out = {}
    for p in sorted(glob.glob(os.path.join(RACINE, "sprites", "2i-b*.bin"))):
        nom = os.path.basename(p)[:-4]
        r = fetc.lire(open(p, "rb").read())
        o = 0x20 + len(r["anims"]) * 12
        par_offset = {}
        for i, sp in enumerate(r["sprites"]):
            par_offset[o] = i
            o += 8 + len(sp["morceaux"]) * 8
        out[nom] = dict(span=r["index_global"],
                        enr=[(a[1], a[2], par_offset.get(a[4])) for a in r["anims"]])
    return out


def resout(ass, idx):
    """index global -> (asset, numero d'enregistrement, ancre x, ancre y, sprite)."""
    for nom, d in ass.items():
        a, b = d["span"]
        if a <= idx < b:
            k = idx - a
            if k < len(d["enr"]):
                x, y, sp = d["enr"][k]
                return nom, k, x, y, sp
            return nom, k, None, None, None
    return None, None, None, None, None


def script(adresse, ass, maxi=64):
    """Un script : la suite de ses enregistrements, jusqu'a la commande de fin."""
    out = []
    for k in range(maxi):
        o = sh4.a2o(adresse + k * 8)
        if o + 8 > len(sh4.D):
            break
        cmd, duree = sh4.D[o], sh4.D[o + 1]
        idx = sh4.u16(o + 6)
        if cmd == FIN:
            break
        if cmd == 0x00 and duree:
            out.append(dict(cmd=cmd, duree=duree, index=idx, resolu=resout(ass, idx)))
        else:
            out.append(dict(cmd=cmd, duree=duree, index=idx, resolu=(None,) * 5))
    return out


def tables(ass):
    """Les tables de scripts distinctes, nommees par les assets qu'elles citent."""
    vues = []
    for n in range(NB_AIRES):
        t = sh4.u32(sh4.a2o(MAITRESSE + n * 4))
        if not dans_le_binaire(t) or t in [v["adresse"] for v in vues]:
            continue
        scripts = []
        for k in range(64):
            p = sh4.u32(sh4.a2o(t + k * 4))
            if not dans_le_binaire(p):
                break
            scripts.append((p, script(p, ass)))
        noms = set()
        for _p, s in scripts:
            for e in s:
                if e["resolu"][0]:
                    noms.add(e["resolu"][0])
        if scripts:
            vues.append(dict(adresse=t, aire=n, scripts=scripts, assets=sorted(noms)))
    return vues


def main():
    filtre = sys.argv[1] if len(sys.argv) > 1 else None
    ass = assets()
    print("Les cadences des sprites de decor de 2nd Impact")
    print("lues dans les scripts du binaire, pas dans les repetitions du flux\n")
    ntab = nscr = nimg = 0
    for t in tables(ass):
        if filtre and not any(filtre in a for a in t["assets"]):
            continue
        ntab += 1
        print("=" * 78)
        print("table 0x%08X  (aire %d)  assets cites : %s"
              % (t["adresse"], t["aire"], ", ".join(t["assets"]) or "aucun"))
        for p, s in t["scripts"]:
            nscr += 1
            images = [e for e in s if e["cmd"] == 0x00]
            connues = [e for e in images if e["resolu"][0]]
            nimg += len(images)
            if not images:
                print("   0x%08X : aucune image (commandes seules)" % p)
                continue
            total = sum(e["duree"] for e in images)
            ancres = {(e["resolu"][2], e["resolu"][3]) for e in connues}
            boucle = " ; boucle x%d" % next(
                (e["index"] for e in s if e["cmd"] == 0x0C), 0) if any(
                e["cmd"] == 0x0C for e in s) else ""
            print("   0x%08X : %d image(s), %d trames en tout%s%s"
                  % (p, len(images), total, boucle,
                     ("  ancre%s %s" % ("" if len(ancres) == 1 else "s",
                                        " ".join("(%s,%s)" % a for a in sorted(ancres))))
                     if ancres else "  (asset hors de sprites/)"))
            for e in images:
                nom, k, x, y, sp = e["resolu"]
                if nom:
                    print("        sprite %-4s (enr %4d de %-22s) pendant %3d trames"
                          % (sp, k, nom, e["duree"]))
                else:
                    print("        index global %-6d (asset non extrait)      pendant %3d trames"
                          % (e["index"], e["duree"]))
        print()
    print("=" * 78)
    print("%d tables, %d scripts, %d images" % (ntab, nscr, nimg))


if __name__ == "__main__":
    main()
