# L'assemblage des sprites de décor — percé le 27/08/2026

Le verrou est levé. Un asset `F_ETCnn` ne rend plus un réservoir de tuiles en désordre :
les tuiles se posent à leur place et les objets sont identifiables.

Percé en lisant le code SH-4 de `SF3_2ND.BIN`, pas en essayant des dispositions.

## Le morceau de 8 octets, en entier

Un sprite de la section 2 est un en-tête de 8 octets `{u16, u16, u16, u16 nb de morceaux}`
suivi de `nb` morceaux de 8 octets. Les trois premiers champs de l'en-tête sont
**constants pour tout l'asset** — ce ne sont pas des dimensions.

Chaque morceau se lit :

| octets | champ | sens |
|---|---|---|
| 0–1 | `u16` | **index de tuile** — bloc = `index >> 4`, rang dans le bloc = `index & 15` |
| 2–3 | `u16` | **palette** : bits 0–8 l'offset, bits 9/11/12 les drapeaux |
| 4–5 | `u16` | **y**, sur 12 bits |
| 6–7 | `u16` | `code << 12 | x`, **x signé sur 12 bits** |

### Le quartet `code` porte la taille

    largeur = 1 << (((code >> 2) & 3) - 1)      hauteur = 1 << ((code & 3) - 1)

Seules neuf valeurs apparaissent — `5,6,7,9,a,b,d,e,f` — soit exactement les 3×3
combinaisons de 1, 2 et 4 tuiles. Ni `0`, ni `4`, ni `8`, ni `c` : les deux paires de
bits ne valent jamais zéro.

**Mesure qui tranche.** Sur les 7313 sprites des deux jeux, l'écart entre l'index d'un
morceau et celui du suivant vaut `largeur × hauteur` dans la très grande majorité des
cas, code par code :

| code | l × h | écart dominant | occurrences |
|---|---|---|---|
| `5` | 1×1 | 1 | 11570 |
| `6` | 1×2 | 2 | 5136 |
| `7` | 1×4 | 4 | 1201 |
| `9` | 2×1 | 2 | 4201 |
| `a` | 2×2 | 4 | 3611 |
| `b` | 2×4 | 8 | 948 |
| `d` | 4×1 | 4 | 1022 |
| `e` | 4×2 | 8 | 840 |
| `f` | 4×4 | 16 | 719 |

### Le même champ existe dans l'enregistrement RAM

La boucle de dessin `0x8C0F693C` travaille sur des enregistrements de 16 octets. À
l'offset 10 elle fait exactement le même calcul, deux fois :

    8C0F6B06  mov.w @r10,r3 ; and r9,r3 ; add #-1,r3 ; shad r3,r2     (r9 = 3, r2 = 1)
    8C0F6B20  mov.w @r10,r3 ; shar ; shar ; and r9,r3 ; add #-1,r3 ; shad r3,r1

`1 << ((v & 3) - 1)` et `1 << (((v >> 2) & 3) - 1)`. Les bits `0x100` et `0x200` du même
mot sont les retournements.

### x et y sont des **centres**, pas des coins

    coin = (x - 8 × largeur, y - 8 × hauteur)

C'est la mesure qui l'impose, et l'écart est massif. Sur tous les sprites de 2nd Impact,
en comptant les tuiles couvertes deux fois par les rectangles de morceaux :

| convention | chevauchement | remplissage |
|---|---|---|
| l = `code & 3`, coin | 18,70 % | 17,7 % |
| l = `code & 3`, centre | 15,10 % | 19,1 % |
| l = `code >> 2`, coin | 22,74 % | 18,8 % |
| **l = `code >> 2`, centre** | **2,35 %** | **24,4 %** |

Un facteur six à dix. Le code SH-4 dit la même chose : `0x8C0F6A28` pose
`r7 = -(largeur >> 1)` et `r11 = -(hauteur >> 1)` avant d'ajouter la position.

### Les tuiles d'un morceau se suivent **en colonnes**

Tuile `index + n` avec `n` parcourant d'abord la hauteur, puis la largeur — comme le
CPS3. Vérifié à l'œil sur un morceau 2×4 d'Oro : en colonnes le nuage et la falaise sont
continus, en lignes tout est haché.

## La vérification qui ne ment pas

L'acolyte de Gill (`F_ETC41`, sprites 9 et 10, palette 871) sort **identique** à
`reference-gill-acolyte.png`, une capture Flycast découpée à la main : capuche blanche,
étoile noire, robe verte, écharpe mauve, bras croisés. Rien d'ajusté pour l'occasion.

La comète du même asset (palette 827) sort en quatre images d'animation, tête brillante
et traînée diagonale continue d'un morceau à l'autre.

## Les palettes : `base + offset`

Le champ palette d'un morceau **n'est pas un numéro de la banque**. C'est
`drapeaux << 9 | offset`, et la palette réelle vaut

    banque[ base(décor, drapeaux) + offset ]

Les drapeaux observés sont `1` (bit 9), `5` (9+11), `9` (9+12) et `13` (9+11+12) —
quatre groupes, quatre bases possibles par décor.

**C'est vérifié, pas supposé.** Chaque base explique plusieurs palettes confirmées à la
fois, exactement, sans reste :

| décor | base (drapeau 1) | palettes confirmées expliquées |
|---|---|---|
| `bg00` gill | 827 | 827+0 = **827**, 827+44 = **871** |
| `bg01` alex | 927 | 927+25 = **952** |
| `bg02` ryu | 1625 | +1 = **1626**, +5 = **1630** |
| `bg03` yun | 1631 | +2 = **1633**, +3 = **1634** |
| `bg04` dudley | 1641 | +1 +2 +4 +5 = **1642 1643 1645 1646** |
| `bg05` necro | 1169 | 1169+10 = **1179** |
| `bg06` hugo | 1219 | 1219+23 = **1242** |
| `bg08` elena r1 | 1319 | +1 +3 +5 +7 = **1320 1322 1324 1326** |
| `bg0a` oro | 1674 | +0 +2 +3 = **1674 1676 1677** |
| `bg0b` yang | 1085 | +5 +7 +9 +10 +11 = **1090 1092 1094 1095 1096** |
| `bg0d` sean | 1519 | 1519+31 = **1550** |

et pour le drapeau 9 : `bg05` 1647+2 = **1649**, `bg06` 1652+2/+3/+9 = **1654 1655 1661**,
`bg08` 1663+0 = **1663** (le vautour), `bg0b` 1638+0 = **1638**.

Quinze palettes établies indépendamment, par correspondance exacte de couleurs contre
des captures, retombent toutes sur une poignée de bases. Ce n'est pas un hasard.

### D'où viennent ces bases

De la table de transferts de palettes de `SF3_2ND.BIN`, à partir de **`0x1D4DBC`**,
enregistrements de 12 octets :

    { u32 destination (offset, /128 = emplacement), u32 adresse de palette, u32 taille }

L'adresse de palette est dans l'espace façon CPS3 : `0x02798000 + N × 128`, donc
`N = (adresse − 0x02798000) / 128` est le numéro dans la banque de l'exécutable.

Toutes les bases du tableau ci-dessus sont la source d'un de ces enregistrements. Deux
familles s'y lisent :

- **le bloc propre au décor**, 64 palettes : sources 827, 927, 936, 984, 989, 1043, 1085,
  1117, 1169, 1219, 1289, 1319, 1365, 1412, 1429, 1446, **1477**, 1519, **1607**, 2144 —
  vingt-et-une entrées pour les vingt-et-un décors, et elles coïncident avec les plages de
  fond mesurées par `appariement.py` ;
- **un bloc partagé** de 80 à 100 palettes, sources 1625, 1631, 1638, 1641, 1647, 1652,
  1663, 1667, 1674 — les figures humaines, badauds et baigneurs, que plusieurs décors
  se partagent.

Selon le décor, le drapeau 1 désigne l'un ou l'autre. **La table qui dit lequel n'est pas
encore localisée** : la résolution passe par une table RAM de 512 octets à `0x8C6D57E0`
(lue en `0x8C0F6A6E`, palette → emplacement matériel), remplie au chargement de l'étage
par la routine `0x8C0F5A4E`. Les bases ci-dessus sont donc **déduites**, pas lues.

### Ken et Urien : ce que l'assemblage en dit

Leurs éléments animés sont rares à l'écran et Frédéric ne les avait pas trouvés en
jouant. L'assemblage dit maintenant à quoi ils ressemblent — et confirme que **ce ne
sont pas des passants** :

- **`bg0e` urien — CONFIRMÉ, palette 1612.** Un seul offset, `5`, et la base du bloc du
  décor est 1607 : `1607 + 5 = 1612`, exactement ce que la règle prédisait. Vérifié sur
  `cap-urien2.png` : le **grand pilier de pierre** au premier plan à droite est le seul
  élément de l'écran, hors HUD et combattants, dont les couleurs sont absentes de
  `bg0e.pvc`. Ses douze couleurs donnent **11/12 pour la palette 1612**, la suivante à
  4/12 — et les index touchés, **17 à 31**, forment une rampe contiguë, toute comprise
  dans les index qu'emploient réellement les tuiles du sprite. C'est le premier cas où la
  règle `base + offset` a **prédit** une palette avant qu'une capture ne la confirme.
- **`bg0c` ken** — offsets `9`, `15`, `16`. **La base n'est pas déterminée, et les
  éléments ne sont pas ceux que j'avais annoncés.** Le vélo, les bancs, les fleurs, le
  panneau « CRC » et les chaises sont **dans le fond** : le rendu de `bg0c.pvc` les
  contient tous, avec le Golden Gate, l'enseigne « SEAFOOD RESTAURANT SAN FRANCISCO » et
  le yacht « KEN MASTERS ». Les six sprites de `F_ETC24` sont autre chose, et ils sont
  petits : 128×48, 32×48, 32×48, 16×64, 112×112 et 16×16. En valeurs d'index, ce sont
  des **barres verticales de hauteurs inégales**, un **bloc rayé**, des **arcs fins**,
  des **bandes horizontales empilées**, de **longues lignes courbes** et un **glyphe
  katakana**. Rien qui ressemble à un mobilier de ponton.

#### Correction — la mesure de parenté de couleurs ne vaut rien ici

J'avais annoncé `bg0c` → 1486, 1492, 1493 en m'appuyant sur la part des couleurs du
sprite présentes dans le `.pvc` du décor (45,6 % pour la base 1477). **Cette mesure ne
discrimine pas.** Vérification sur `cap-ken2.png` : le banc rouge du ponton, qui est du
**fond pur**, obtient **100 %**. Un score élevé ne distingue donc pas un sprite du décor
d'un morceau de décor.

Un balayage de la banque entière contre `cap-ken2.png` — pour chaque base, la part des
couleurs distinctes des sprites qui apparaissent exactement dans la capture, en écartant
les palettes dégénérées à moins de 70 couleurs — place le maximum vers **1463–1479**
(1463 : 97,7 % ; 1472 : 87,2 % ; 1479 : 72,1 % ; moyenne 10,3 %), pas sur 1477 (47,7 %).
Les palettes voisines d'un même bloc partageant beaucoup de couleurs, la mesure ne
tranche pas à l'unité près.

**Ce qui manque pour conclure :** une capture où un sprite de `bg0c` est visible.
`cap-ken2.png` et `cap-ken3.png` n'en contiennent aucun. La carte des pixels dont la
couleur est absente de `bg0c.pvc` n'y montre que le HUD, les deux combattants, et — dans
`cap-ken3.png` — **la sacoche violette du vélo, qui appartient à Ryu** : ses couleurs
sortent sur les palettes 211 et 24, c'est-à-dire des palettes de combattant (< 500), et
Ryu porte le gi violet dans ce combat. C'est exactement le piège du sac de frappe du toit
d'Alex, que Frédéric avait déjà relevé.

Reste la possibilité que les sprites soient bien à l'écran mais **partagent leurs
couleurs avec le fond** — la carte est aveugle dans ce cas. Vu leur forme (barres fines,
arcs, un glyphe), ce sont des éléments discrets ; il faudra les repérer à l'œil.

## Les outils

| fichier | rôle |
|---|---|
| `outils/assemblage.py` | décode les morceaux et pose les tuiles ; `poser_couleur` colorie **chaque morceau avec sa propre palette** |
| `outils/bases.py` | la table des bases de palette par décor et par drapeau |
| `outils/planche.py` | planche des sprites assemblés d'un asset |
| `outils/toutsprites.py` | rend les planches des seize assets de 2nd Impact |

Lanceurs : `rendre-sprites.cmd` (tout), `sprite.cmd` (un asset).
Les planches sont dans `rendus/sprites/`.

## Ce que le champ `tuile` indexe — percé le 28/08/2026

    bloc  = tuile >> 4          (>> 3 pour la seule clé 0x0160)
    rang  = tuile & 15
    fiche = 0x8C602384 + (clé & 0xFF) * 24
    fiche[+8](bloc, tampon, fiche[+12])   -> 4096 octets
    la tuile 16x16 en 8 bits = tampon[rang * 256 : rang * 256 + 256]

La table `0x8C602384` est la table d'installation des assets décrite en tête de `fetc.py`.
`fiche[+12]` pointe la **section 3** d'un `F_ETCnn`, que `0x8C0F6548` lit comme
`{u32 nombre, u32 offsets[nombre]}` et dégonfle à rebours : `blocs[i]` de `fetc.lire()`
est exactement ce que le jeu obtient. Huit blocs de 4096 octets sont gardés en cache
(`0x8C0F648E`, tampons en `0x8C6DE900`).

Entre les deux, `0x8C0F719E` n'est qu'une table de hachage de textures, dont l'identité
sur 32 bits `(palette << 22) | ((clé & 127) << 15) | tuile` dit tout : **une tuile n'a de
sens que dans le contexte d'une clé.**

Mesuré, pas raconté : `pools.py` vérifie que toutes les tuiles demandées tombent dans le
nombre de blocs de leur pool — **187 couples (état, clé) sur 187** — et nomme chaque asset
par ses octets. Le tableau clé → asset est dans `RELAIS.md`.
`elements.py` assemble et colorie ; les planches sont dans `rendus/elements/`.

## Ce qui reste ouvert

- **La table qui associe un décor à ses quatre bases de palette.** Elle n'est plus
  nécessaire pour colorier depuis un état — la palette se lit en RAM, ci-dessus — mais
  elle le reste pour partir du fichier seul. `0x8C6D57E0` est vide dans les états relevés :
  ce n'est pas elle.
- **Les retournements.** Les bits `0x100` et `0x200` de l'enregistrement RAM sont des
  retournements ; on n'a pas établi quel bit du fichier les porte. Les bits 11 et 12 du
  champ palette en sont les candidats, mais ils servent aussi de sélecteur de groupe.
- **L'échelle.** Le dessinateur RAM lit à l'offset 8 deux champs de 7 bits, `(v & 127) + 1`
  et `((v >> 8) & 127) + 1`, qui participent au calcul de la position en `0x8C0F6A90`.
  Leur unité n'est pas établie ; l'acolyte apparaît plus grand à l'écran que dans le
  rendu brut, il y a sans doute un facteur d'agrandissement.
- Le rôle de `hdr[0x10]` dans l'en-tête `F_ETCnn`, toujours pas établi.

---

## Le même morceau, résolu en RAM (27/08/2026)

Le morceau de 8 octets décrit ci-dessus est la forme **rangée sur le disque**. En RAM, le
jeu en tient une version **déjà résolue**, sur 16 octets, dans un tableau de 32768 entrées
pointé par la variable `0x8C602348` (valeur `0x8C72FCCC`, soit 512 Ko qui s'arrêtent pile
là où commence la palette RAM `0x8C7AFCCC`) :

    { u16 tuile, u16 palette, u16 x, u16 y,
      u16 h-1 << 8 | l-1, u16 drapeaux << 8 | code, u16 clé, u16 0 }

**Corrigé le 28/08/2026** — les deux derniers champs n'étaient pas nommés comme il faut,
et la taille était à l'envers. Le désassemblage tranche :

- `x` et `y` sont **absolus**, dans le plan de 1024 qui boucle ;
- le mot `+8` porte la taille **en pixels**, et c'est de lui, non du `code`, que le dessin
  la tire (`0x8C0F6A08`) : `hauteur = ((w4 >> 8) & 127) + 1`, `largeur = (w4 & 127) + 1`.
  **C'est l'inverse de ce qui était écrit ici** : le bit `0x0100` retranche la moitié du
  premier à *y*, le bit `0x0200` la moitié du second à *x* — un centre en *y* se retire
  d'une demi-hauteur, pas d'une demi-largeur ;
- `+2` est la **palette** — c'est le champ palette du fichier, `drapeaux << 9 | offset`,
  passé tel quel ;
- `+12` n'est **pas** un emplacement de palette : c'est la **clé du pool de tuiles**.
  Son octet bas indexe la table d'installation des assets `0x8C602384`, et c'est elle qui
  dit dans quel `F_ETCnn` lire la tuile. Voir « Ce que le champ `tuile` indexe » plus haut.

### D'où vient vraiment l'emplacement de palette

De l'**élément** de la liste d'affichage, pas toujours du morceau. `0x8C0F6A44` teste le
**bit 5** de l'octet `+9` de l'élément :

- bit armé : l'emplacement est le mot `+8` de l'élément, un seul pour tous ses morceaux ;
- bit éteint : c'est le champ `+2` du morceau.

Puis `0x8C0F6A64` teste `octet & 6` : non nul, l'emplacement vaut `source & 0x1FF` et la
palette fait 128 octets (64 couleurs) ; nul, il vaut `(source & 0x1FF) | 0x200` et la
palette fait 512 octets. L'adresse est `0x8C7AFCCC + emplacement * 128`, ou
`0x8C7AFCCC + (emplacement - 512) * 512` au-delà de `0x200` (`0x8C0F6E3A`).

Sans ce bit 5, les éléments à octet `0x62` — la grande majorité — tombent sur les
emplacements 1 à 15, c'est-à-dire le bloc des combattants, **identique dans les dix-sept
états** : d'où des cascades rouges et des temples orange.

### Les deux drapeaux, et ce qu'ils disent des centres

L'octet haut de `+10` ne prend que deux valeurs sur les dix états : **`0x03` (54678 fois)
et `0x00` (2772 fois)**. Le code de dessin les teste bit à bit, avec les masques `0x0100`
et `0x0200` :

| bit | masque | effet dans `0x8C0F6A08` |
|---|---|---|
| 8 | `0x0100` | retranche `h / 2` — **y est un centre** |
| 9 | `0x0200` | retranche `l / 2` — **x est un centre** |

C'est la règle « x et y sont des centres » de la section précédente, mais **conditionnelle** :
quand l'octet haut vaut `0x00`, les deux bits sont éteints et `x`, `y` sont le **coin**.
Les coordonnées sont ensuite masquées à `0x03FF`, la boucle de 1024.

Dans l'octet bas, seuls les **bits 0 à 3** portent la taille — bits 0–1 la hauteur, bits 2–3
la largeur. Les bits 4 à 7 sont d'autres drapeaux : on rencontre `0x45`, `0x49`, `0x4D`,
`0x59`… qui sont les mêmes tailles avec le bit 6 armé.

### La vérification

La taille explicite et le quartet `code` disent la même chose deux fois. Sur les dix états,
en écartant la liste d'affichage : **54769 morceaux concordent, 1216 non — 97,8 %.**
Les écarts se concentrent sur les enregistrements à drapeaux `0x00`, et sur 69 sprites mis
à l'échelle dont le champ `+2` change.

Les onze tailles rencontrées sont exactement les onze que le `code` autorise :
16×16, 16×32, 16×64, 32×16, 32×32, 32×64, 64×16, 64×32, 64×64, plus les deux mises à
l'échelle.

Le champ `+2` est constant pour tous les morceaux d'un même sprite (`0x02D4`, `0x0273`,
`0x0200`, `0x01FF`…) et change avec la mise à l'échelle : son rôle n'est pas établi.

### Ce qui n'est pas un morceau

Les entrées **0 à 47** du tableau sont la **liste d'affichage** de l'image, pas des
morceaux : `{u16 drapeaux, u16 index, u16 x, u16 y, …}`, le plan se lisant
`(drapeaux >> 10) & 28`. Elle se termine au premier enregistrement dont le bit 15 est armé
(`cmp/pz` en `0x8C0F697E`).

`outils/etat2.py` lit tout ça ; `relever2.cmd` le lance.
