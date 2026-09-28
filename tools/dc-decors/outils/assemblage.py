# -*- coding: utf-8 -*-
"""Assemblage des sprites F_ETCnn (SF3 Dreamcast) : pose les tuiles a leur place.

Percé en lisant le code SH-4 de SF3_2ND.BIN, dans la boucle de dessin 0x8C0F693C.

Le morceau de 8 octets de la section 2 se lit :
    u16  tuile      index global de tuile  (bloc = tuile >> 4, rang = tuile & 15)
    u16  palette    bits 0-8 palette, bits 9/11/12 drapeaux
    u16  y          coordonnee, 12 bits
    u16  code<<12 | x   x signe sur 12 bits

Le quartet `code` porte la **taille du morceau**, en tuiles :
    largeur = 1 << ((code & 3) - 1)      hauteur = 1 << (((code >> 2) & 3) - 1)
Soit 9 valeurs seulement -- 5,6,7,9,a,b,d,e,f -- exactement les 3x3 combinaisons
de 1, 2 et 4. Mesure : sur les 7313 sprites des deux jeux, l'ecart entre l'index
d'un morceau et celui du suivant vaut largeur x hauteur dans 96 % des cas
(24461 morceaux 1x1, 8042 de 2 tuiles, etc.).

Le meme champ existe dans l'enregistrement RAM de 16 octets que dessine
0x8C0F693C : a l'offset 10, `1 << ((v & 3) - 1)` et `1 << (((v >> 2) & 3) - 1)`
(0x8C0F6B06 et 0x8C0F6B20, avec r9 = 3). Les bits 0x100 et 0x200 y sont les
retournements.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
import fetc, degonfle

def s12(v):
    v &= 0xFFF
    return v - 0x1000 if v & 0x800 else v

def taille(code):
    """(largeur, hauteur) en tuiles pour le quartet de code.

    CORRIGE LE 29/08/2026, contre la RAM. Cette fonction rendait les deux quartets a
    l'envers. Le dessin lit, en 0x8C0F6B04 et 0x8C0F6B20 :

        largeur = 1 << ((v      & 3) - 1)      le quartet BAS
        hauteur = 1 << (((v >> 2) & 3) - 1)    le quartet HAUT

    Mesure sur les 797 morceaux que la liste d'affichage en RAM permet d'apparier :
    la lecture directe (bas = largeur) tient a **98,7 %**, la croisee a 54,5 %.
    """
    w = code & 3
    h = (code >> 2) & 3
    if w == 0 or h == 0:
        return None
    return 1 << (w - 1), 1 << (h - 1)

def charger(chemin):
    """Rend (asset, tuiles) : tuiles[i] = tableau 16x16 d'index sur 6 bits."""
    d = open(chemin, 'rb').read()
    r = fetc.lire(d)
    nb = len(r['blocs'])
    tuiles = []
    for k, b in enumerate(r['blocs']):
        octets, _ = degonfle.degonfler(b, souple=(k == nb - 1))
        a = np.frombuffer(octets, dtype=np.uint8)
        for t in range(16):
            tuiles.append(a[t*256:(t+1)*256].reshape(16, 16))
    return r, tuiles

def morceaux(sprite):
    """Rend la liste des morceaux decodes d'un sprite de la section 2."""
    out = []
    for m in sprite['morceaux']:
        code = m[3] >> 12
        t = taille(code)
        if t is None:
            continue
        # LES DEUX COORDONNEES SONT SIGNEES SUR 12 BITS. `y` etait lu brut : un y negatif
        # sortait a 4095 et la boite englobante du sprite faisait 4096 de haut. Corrige le
        # 29/08/2026 -- cinq des neuf sprites qui resistaient encore etaient ceux-la.
        out.append(dict(tuile=m[0], palette=m[1] & 0x1FF, drapeaux=m[1] >> 9,
                        # LES DEUX RETOURNEMENTS, bits 11 et 12 du champ palette. Ce sont
                        # les memes que dans l'enregistrement RAM, ou le dessin les lit en
                        # 0x8C0F6AC6 : `element[+9] ^ (morceau[+2] >> 8)`, bit 0x08 vertical
                        # et bit 0x10 horizontal -- soit les bits 11 et 12 du mot.
                        # 541 morceaux sur 15914 en portent un. Ils servent aux moities
                        # symetriques : le morceau miroir reprend la TUILE d'un autre
                        # morceau du meme sprite. Les ignorer, c'est poser deux fois la
                        # meme moitie -- et c'est ce que faisait cette fonction.
                        miroir_x=bool(m[1] & 0x1000), miroir_y=bool(m[1] & 0x0800),
                        x=s12(m[3]), y=s12(m[2]), largeur=t[0], hauteur=t[1], code=code))
    return out

def poser(sprite, tuiles, colonne=True, yhaut=True):
    """Pose les tuiles d'un sprite. Rend (image d'index, masque, x0, y0).

    colonne : les tuiles d'un morceau se suivent en colonnes (comme le CPS3).
    yhaut   : y compte vers le haut (l'ecran a l'axe inverse, cf. 0x8C0F6AA6).
    """
    ms = morceaux(sprite)
    if not ms:
        return None
    # LE SPRITE EST STOCKE TRANSPOSE, et c'est ce qui manquait a cette fonction.
    # Corrige le 29/08/2026 contre la liste d'affichage en RAM, qui fait foi :
    #
    #     image_x = champ Y du morceau        image_y = champ X du morceau
    #
    # Mesure sur les 797 morceaux appariables : la lecture transposee tient a 98,9 %
    # en x et 99,0 % en y, la lecture directe -- celle d'avant -- a 18,9 % et 17,3 %.
    # Et sur la ventilation d'Alex, le sprite ainsi assemble est identique **pixel pour
    # pixel** (2304 sur 2304) a celui que la RAM donne.
    #
    # C'est cette erreur-la qui mettait les morceaux en damier. Elle se compensait en
    # partie avec celle de `taille`, d'ou des sprites justes par hasard et d'autres non.
    boites = []
    for m in ms:
        px, py = m['y'] - 8*m['largeur'], m['x'] - 8*m['hauteur']
        boites.append((px, py, m['largeur']*16, m['hauteur']*16))
    x0 = min(b[0] for b in boites); y0 = min(b[1] for b in boites)
    x1 = max(b[0]+b[2] for b in boites); y1 = max(b[1]+b[3] for b in boites)
    img = np.zeros((y1-y0, x1-x0), dtype=np.uint8)
    msk = np.zeros((y1-y0, x1-x0), dtype=bool)
    for m, (px, py, _, _) in zip(ms, boites):
        n = 0
        rng = ([(i, j) for i in range(m['largeur']) for j in range(m['hauteur'])]
               if colonne else
               [(i, j) for j in range(m['hauteur']) for i in range(m['largeur'])])
        for i, j in rng:
            k = m['tuile'] + n; n += 1
            if k >= len(tuiles):
                continue
            t = tuiles[k]
            # Le retournement porte sur la CASE dans le morceau **et** sur les pixels de
            # la tuile. `i` indexe l'axe x de l'ecran, `j` l'axe y.
            ii, jj = i, j
            if m['miroir_x']:
                ii = m['largeur'] - 1 - i
                t = t[:, ::-1]
            if m['miroir_y']:
                jj = m['hauteur'] - 1 - j
                t = t[::-1, :]
            a, b = py - y0 + jj*16, px - x0 + ii*16
            zone = img[a:a+16, b:b+16]
            mzone = msk[a:a+16, b:b+16]
            neuf = (t != 0)
            zone[neuf] = t[neuf]
            mzone[neuf] = True
    return img, msk, x0, y0

def couleur(img, msk, pal):
    """pal : tableau (64,3). Rend un RGBA."""
    out = np.zeros(img.shape + (4,), dtype=np.uint8)
    out[..., :3] = pal[np.clip(img, 0, len(pal)-1)]
    out[..., 3] = msk * 255
    return out

def poser_couleur(sprite, tuiles, banque, base, bases=None, colonne=True):
    """Assemble un sprite en RGBA, **chaque morceau avec sa propre palette**.

    banque : tableau (n, 64, 3) rendu par palettes.lire
    base   : numero de palette du groupe de drapeaux 1 (le principal)
    bases  : dict drapeau -> base, pour les autres groupes -- ou bien une FONCTION
             `(drapeaux, offset) -> numero`, quand une base par groupe de drapeaux ne
             suffit pas. Oro est dans ce cas : ses deux banques se separent par l'offset
             du morceau, pas par ses drapeaux. Voir `bases.numero`.
    """
    if callable(bases):
        resoudre = bases
    else:
        _b = dict(bases or {})
        _b.setdefault(1, base)
        resoudre = lambda dr, off: _b[dr] + off if dr in _b else None
    ms = morceaux(sprite)
    if not ms:
        return None
    # Transpose, comme dans `poser` -- voir le commentaire la-bas.
    bo = [(m['y'] - 8*m['largeur'], m['x'] - 8*m['hauteur']) for m in ms]
    x0 = min(b[0] for b in bo); y0 = min(b[1] for b in bo)
    x1 = max(b[0] + 16*m['largeur'] for b, m in zip(bo, ms))
    y1 = max(b[1] + 16*m['hauteur'] for b, m in zip(bo, ms))
    out = np.zeros((y1-y0, x1-x0, 4), dtype=np.uint8)
    for m, (px, py) in zip(ms, bo):
        num = resoudre(m['drapeaux'], m['palette'])
        if num is None:
            continue
        if not (0 <= num < len(banque)):
            continue
        pal = banque[num]
        n = 0
        for i in range(m['largeur']):
            for j in range(m['hauteur']):
                k = m['tuile'] + n; n += 1
                if k >= len(tuiles):
                    continue
                t = tuiles[k]
                # LES RETOURNEMENTS, comme dans `poser`. Ils manquaient ici : cette
                # fonction posait deux fois la meme moitie des sprites symetriques. Sans
                # effet sur les neuf elements de `bg00`, qui n'en portent aucun.
                ii, jj = i, j
                if m['miroir_x']:
                    ii = m['largeur'] - 1 - i
                    t = t[:, ::-1]
                if m['miroir_y']:
                    jj = m['hauteur'] - 1 - j
                    t = t[::-1, :]
                a, c = py - y0 + jj*16, px - x0 + ii*16
                neuf = (t != 0)
                zone = out[a:a+16, c:c+16]
                zone[..., :3][neuf] = pal[t[neuf]]
                zone[..., 3][neuf] = 255
    return out, x0, y0


def poser_1555(sprite, tuiles, banque_brute, base, bases=None, avec_source=False,
               huit_bits=False):
    """Comme `poser_couleur`, mais rend les valeurs ARGB1555 au lieu du RGB.

    POURQUOI IL LE FAUT. Un sprite peut melanger PLUSIEURS palettes entre ses morceaux --
    vingt et un chez Hugo, onze chez Yang, et leurs morceaux tirent sur deux banques
    eloignees (1221 et 1654). `animer2i` n'emettait qu'une palette par objet, celle du
    PREMIER morceau : tous les autres sortaient avec des couleurs fausses. C'est ce que
    Frederic voyait sur Hugo, Ryu, Yun et Yang.

    En rendant les couleurs elles-memes, on peut ensuite construire une palette EFFECTIVE
    par objet -- les couleurs reellement employees, reindexees. Mesure : aucun objet du
    port n'en emploie plus de 56, donc les 63 emplacements suffisent toujours.

    Rend `(u16 (h, w), x0, y0)`, la valeur 0 valant transparent.

    AVEC LA PROVENANCE -- `avec_source=True` rend `(image, source, x0, y0)`, ou `source`
    porte le NUMERO DE PALETTE qui a ecrit chaque pixel (0 = aucun). C'est ce qui permet
    de servir un sprite en PLUSIEURS palettes quand ses couleurs depassent les 63 d'une
    seule : on partage les pixels selon la palette qui les a peints, et non selon leur
    couleur.

    HUIT BITS -- 22/09/2026, les immeubles de Sean (id 44). Leurs index vont jusqu'a
    255 : la palette tient QUATRE emplacements consecutifs, et l'index se lit
    `[index // 64][index % 64]`. La provenance devient `num + index // 64`, ce qui fait
    que `groupes_palette` decoupe le sprite par quart de palette, et non en bloc.

    **La provenance se releve PENDANT la composition, pas apres.** Les morceaux se
    recouvrent -- le dernier ecrit gagne -- et rejouer la pose morceau par morceau, palette
    par palette, ferait apparaitre DEUX fois les pixels recouverts, une fois dans chaque
    couche. Ecrite ici, `source` suit exactement la meme regle d'ecrasement que `out` : la
    somme des couches redonne l'image au pixel pres.
    """
    if callable(bases):
        resoudre = bases
    else:
        _b = dict(bases or {})
        _b.setdefault(1, base)
        resoudre = lambda dr, off: _b[dr] + off if dr in _b else None

    ms = morceaux(sprite)

    if not ms:
        return None

    bo = [(m['y'] - 8 * m['largeur'], m['x'] - 8 * m['hauteur']) for m in ms]
    x0 = min(b[0] for b in bo)
    y0 = min(b[1] for b in bo)
    x1 = max(b[0] + 16 * m['largeur'] for b, m in zip(bo, ms))
    y1 = max(b[1] + 16 * m['hauteur'] for b, m in zip(bo, ms))
    out = np.zeros((y1 - y0, x1 - x0), dtype=np.uint16)
    src = np.zeros((y1 - y0, x1 - x0), dtype=np.uint16)

    for m, (px, py) in zip(ms, bo):
        num = resoudre(m['drapeaux'], m['palette'])

        if num is None or not (0 <= num < len(banque_brute)):
            continue

        if huit_bits:
            if num + 4 > len(banque_brute):
                continue
            pal = banque_brute[num:num + 4].reshape(256)
        else:
            pal = banque_brute[num]
        n = 0

        for i in range(m['largeur']):
            for j in range(m['hauteur']):
                k = m['tuile'] + n
                n += 1

                if k >= len(tuiles):
                    continue

                t = tuiles[k]
                ii, jj = i, j

                if m['miroir_x']:
                    ii = m['largeur'] - 1 - i
                    t = t[:, ::-1]

                if m['miroir_y']:
                    jj = m['hauteur'] - 1 - j
                    t = t[::-1, :]

                a, c = py - y0 + jj * 16, px - x0 + ii * 16
                neuf = (t != 0)
                zone = out[a:a + 16, c:c + 16]
                # une couleur ARGB1555 nulle serait indistinguable du vide : on force le
                # bit d'opacite, que `palettes.opaque` confirme etre a 1 sur ces entrees.
                zone[neuf] = pal[t[neuf]] | 0x8000
                if huit_bits:
                    src[a:a + 16, c:c + 16][neuf] = num + (t[neuf] >> 6)
                else:
                    src[a:a + 16, c:c + 16][neuf] = num

    if avec_source:
        return out, src, x0, y0

    return out, x0, y0
