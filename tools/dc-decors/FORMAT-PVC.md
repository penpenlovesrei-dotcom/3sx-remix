# Le format .pvc — décors de Street Fighter III sur Dreamcast

Percé le 27/08/2026 en lisant le code SH-4 de `SF3_2ND.BIN`, pas en devinant.
Tout ce qui suit est vérifié, pas supposé.

## D'où vient la certitude

Trois vérifications indépendantes, chacune impossible à obtenir par hasard :

1. **La somme de contrôle du jeu lui-même.** Chaque exécutable porte, pour chaque `.pvc`,
   sa taille et une somme de mots de 32 bits. La routine qui la vérifie est à
   `0x8C0FF130` dans `SF3_2ND.BIN`. Recalculée sur nos extractions :
   **44 fichiers sur 44 exacts**, les deux jeux confondus.
2. **La consommation du flux.** Le décodeur s'arrête de lui-même après 8192 pages.
   Sur les 44 décors, il consomme le fichier **à l'octet près**.
3. **Le bilan des conteneurs.** Une fois toutes les parties comptées, les 33 `.pk`
   de décor des deux jeux s'expliquent **au secteur près**, sans reste.

## Le conteneur .PK

`bXX.pk` n'est pas un format à en-tête : c'est la **concaténation brute** des fichiers
de sa liste de chargement, chacun aligné sur un secteur de 2048 octets.
`bgXX.pvc` est toujours la première partie, à l'offset 0.

Un `.pk` porte deux sortes de parties : les `.pvc` (les textures) puis les assets
**`F_ETCnn`** — les sprites animés du décor, la fille qui passe, les badauds. Les trois
décors de 2nd Impact sans `F_ETC` (`bg07`, `bg0f`, `bg11`) sont exactement les trois
dont le `.pk` n'a pas de seconde partie.

Les listes sont dans l'exécutable. **Les deux jeux se chargent à 0x8C010000.**

| quoi | 2nd Impact (`SF3_2ND.BIN`) | New Generation (`SF3_1ST.BIN`) |
|---|---|---|
| noms `bXX.pk` | `0x8C610BCC` | `0x8C4D4B0C` |
| listes primaires (`.pvc`) | `0x8C610CC0` | `0x8C4D4BF4` |
| listes secondaires (`F_`) | `0x8C610D64` | `0x8C4D4CA0` |

- liste primaire : entrées de 12 octets `{char* nom, u32 taille, u32 somme}`
- liste secondaire : entrées de 12 octets `{u32 id, char* nom, u32 taille}` — **pas** de
  somme de contrôle, c'est la taille qui occupe le troisième champ

Les deux se terminent par une entrée nulle. `outils/decoupe.py` fait le découpage complet.

Un conteneur peut porter plusieurs décors. Chez 2nd Impact, `b08.pk` en porte deux
(`bg08` puis `bg09`) et la table `0x8C610E08` dit lequel prendre. Chez New Generation
c'est la règle plutôt que l'exception : `b08.pk` en porte trois — et ce sont les
**variantes d'heure du jour** du même lieu, `bg_set0b` de jour, `bg_set0c` au couchant,
`bg_set0d` de nuit sous la lune. `b04.pk` et `b0b.pk` portent un contenu identique.

Sur le disque, 2nd Impact nomme ses textures `bgNN.pvc`, New Generation `bg_setNN.pvc`
(plus `bg_s2_NN` et `bg_endNN`). `b09.pk`, `b12.pk` et `b15.pk` manquent chez 2nd Impact.

## Le .pvc lui-même

Décodeur d'origine : `0x8C0F81B4`. Adresse de destination d'une page : `0x8C0F8196`.

Le fichier est une suite de **8192 pages**, chacune une **tuile de 16×16 pixels**
(512 octets en sortie, `page << 9`). Deux banques : pages 0–4095 dans le premier
tampon, 4096–8191 dans le second. Chaque banque est une texture de **1024×1024**.

Pour chaque page, un `u16` d'en-tête `H` :

| `H` | sens |
|---|---|
| `0` | page vide — rien d'autre n'est lu |
| bit 15 armé | la page recopie la page `H & 0x7FFF` |
| sinon | `n = H` = **nombre de couleurs de la palette locale** |

Dans le dernier cas viennent `n` couleurs `u16` (ARGB1555), puis 256 pixels :

- `n <= 16` → **4 bits par pixel**, 128 octets. Dans chaque `u16`, les quartets
  sortent du poids fort vers le poids faible : bits 15‑12, 11‑8, 7‑4, 3‑0.
- `n > 16` → **8 bits par pixel**, 256 octets. Octet de poids fort d'abord.

Chaque tuile a donc sa propre palette : c'est ce qui rendait le fichier illisible
comme image, et ce qui explique l'absence de toute table de palette globale.

## La disposition

Les pages et les pixels sont **entrelacés (ordre de Morton)**, comme toute texture
PVR : sur l'indice global `page * 256 + i`, Y occupe les bits pairs et X les bits
impairs. Mesuré, pas supposé — cohérence entre lignes voisines 1,90 contre 4,59 en
linéaire ; aux coutures entre tuiles, 2,7 contre 21,7.

## Ce qu'on trouve dedans

Les décors sont découpés en couches : le ciel dans une banque, le sol et les
bâtiments dans l'autre. Certaines zones sont des **images d'animation** de 256×256
posées côte à côte (les cascades, le navire), et les pages recopiées servent à
dupliquer les zones identiques sans les stocker deux fois.

## Les outils

| fichier | rôle |
|---|---|
| `outils/pvc.py` | le décodeur, avec vérification de consommation |
| `outils/rendupvc.py` | rendu PNG d'un `.pvc` (deux banques) |
| `outils/decoupe.py` | découpe les `.pk` d'après les tables des deux exécutables |
| `outils/fetc.py` | lit un conteneur `F_ETCnn` (animations, sprites, blocs) |
| `outils/degonfle.py` | les deux décompresseurs des blocs graphiques |
| `outils/sprites.py` | sort les tuiles d'un asset `F_ETCnn` en PNG |
| `outils/palettes.py` | lit la banque de palettes de sprites d’un exécutable |
| `outils/appariement.py` | rattache chaque décor à sa plage de palettes |
| `outils/tout.py` | rend les 44 décors et la planche-contact |
| `outils/sh4.py` | désassemblage SH-4 de l'exécutable, base 0x8C010000 |
| `outils/assemblage.py` | **assemble un sprite** : pose les tuiles, une palette par morceau |
| `outils/bases.py` | base de palette par décor et par groupe de drapeaux |
| `outils/planche.py`, `outils/toutsprites.py` | planches des sprites assemblés |
| `outils/dispo.py` | mesure de la disposition (Morton contre linéaire) |
| `outils/secteurs.py` | empreinte par secteur, pour découper un `.pk` |

Les `.pvc` découpés sont dans `pvc-ng/` et `pvc-2i/` (23 + 21), les assets `F_` dans
`sprites/` (53 fichiers), les rendus dans `rendus/`.

## Le conteneur F_ETCnn — les sprites animés

Lu dans la fonction d'installation `0x8C0F6814`, qui range chaque asset dans une entrée
de 24 octets : `entrée+4` = les données, `entrée+12` = données + `hdr[0x14]`,
`entrée+16` = données + 32 − N×12.

En-tête de 32 octets. `hdr[0x00]` est le **premier index global d'animation** — il vaut
exactement ce que porte la table du jeu indexée par identifiant d'asset (vérifié sur
6 assets) — et `hdr[0x04]` le dernier plus un. `hdr[0x14]` est l'offset de la section
graphique. Le rôle de `hdr[0x10]` n'est pas établi.

| section | où | quoi |
|---|---|---|
| 1 | `0x20` | `hdr[4]−hdr[0]` enregistrements de 12 octets, une image d'animation chacun : `{u32 0, s16 x, s16 y, u32 offset}` — l'offset pointe l'entrée de section 2. Les répétitions sont les temps de maintien. |
| 2 | jusqu'à `hdr[0x14]` | entrées de **taille variable**, un sprite chacune : en-tête 8 octets `{u16, u16, u16, u16 nb de morceaux}` — les trois premiers champs sont constants pour tout l'asset, ce ne sont pas des dimensions — puis autant de morceaux de 8 octets, **entièrement décodés** dans `ASSEMBLAGE.md` |
| 3 | `hdr[0x14]` | `{u32 nombre, u32 offsets[nombre]}` puis les blocs graphiques ; offsets relatifs au début de la section |

Le parcours des sections 1 et 2 tombe **pile** sur la section 3 pour les **37 assets**
des deux jeux — c'est la vérification qui tient toute la disposition.

Au total : 16320 images d'animation, 7313 sprites, 3772 blocs graphiques.
`outils/fetc.py` lit tout ça.

### Les blocs graphiques

Deux décompresseurs, tous deux dans `SF3_2ND.BIN`, tous deux rendant **4096 octets
écrits à rebours** depuis la fin du tampon (`mov.b rX,@-r5`).

**Schéma A — `0x8C0F6548`.** Octets de commande, avec une table circulaire de
16 valeurs récentes initialisée à `1..16`, et `dernier` (initialisé à 17) qui retient
la dernière valeur émise.

| octet `b` | effet |
|---|---|
| `b & 0x80` | `(b & 7) + 1` copies de `table[(b >> 3) & 15]` ; `dernier` = cette valeur |
| `b & 0x40` | `(b & 31) + 1` copies de `dernier` si `b & 0x20`, sinon de `0` |
| sinon | littéral `b` (0..0x3F) écrit une fois, rangé dans la table, `dernier = b` |

**Schéma B — `0x8C0F663C`.** RLE à drapeaux : 512 tours de 8 sorties. Un octet de
contrôle par tour, dont le bit `k` dit s'il faut lire un nouvel octet avant la sortie
`k` ; sinon on répète le précédent. 512 × 8 = 4096.

Aucun champ connu ne dit lequel s'applique. On essaie : la double contrainte —
consommer tout le bloc **et** remplir exactement 4096 — tranche sans ambiguïté.
Sur les **3772 blocs** des deux jeux, 3688 relèvent du schéma A et 84 du schéma B,
**aucun échec**.

Les 4096 octets sont **16 tuiles de 16×16 en 8 bits**, lues **ligne par ligne** —
pas d'entrelacement, contrairement aux pages `.pvc` (mesuré : cohérence 3,69 en
linéaire contre 5,60 en Morton, sur 4456 tuiles). `outils/sprites.py` les sort en PNG.

### La banque de palettes

Les tuiles sont des index sur 6 bits ; les couleurs sont **dans l'exécutable**, trouvées
en remontant la chaîne d'écriture de la palette RAM du PowerVR :

| adresse | rôle |
|---|---|
| `0x8C619CB0` | routine Katana : écrit `r5` entrées `u16` à `0x005F9000 + index*4` |
| `0x8C0F594A` | la vidange : 8 emplacements, **64 entrées par appel** |
| `0x8C0F59AA` | adresse d'une palette : `0x8C1E9AEC + offset − 0x02798000` |

64 couleurs par palette, en ARGB1555, 128 octets — ce qui colle exactement aux index
sur 6 bits.

| jeu | offset fichier | adresse | palettes |
|---|---|---|---|
| `SF3_2ND.BIN` | `0x1D9AEC` | `0x8C1E9AEC` | 2715 |
| `SF3_1ST.BIN` | `0x1A8188` | `0x8C1B8188` | 2661 |

`outils/palettes.py` les lit. Le rendu `rendus/palettes-2i.png` montre ce qu'on attend
d'une banque de sprites : teintes de peau, rampes de ciel, dégradés de gris, blocs
magenta de réserve.

### Quelle palette va avec quel décor

La banque est **rangée par décor**, en plages contiguës et croissantes. Le test ne
regarde aucune image : pour chaque palette, on compte la proportion de ses 64 couleurs
qui apparaissent **exactement** (même valeur ARGB1555) dans le décor. Les palettes d'un
décor sortent à ~100 %, contre **8 % de moyenne** sur la banque.

Deux confirmations tombent seules et n'ont pas été cherchées : `bg_set05` et `bg_set11`
partagent leur plage, `bg06` et `bg10` aussi — exactement les décors que le découpage
des conteneurs avait trouvés dupliqués. Une méthode fausse n'aurait aucune raison de
retrouver ça.

New Generation, strictement ordonné :

| décor | plage | décor | plage |
|---|---|---|---|
| `bg_set00` | 0–24 | `bg_set09` | 510–528 |
| `bg_set01` | 113–134 | `bg_set0a` | 576–607 |
| `bg_set02` | 168–185 | `bg_set0c` | 644–659 |
| `bg_set03` | 218–250 | `bg_set0d` | 678–693 |
| `bg_set05` | 338–353 | `bg_set0b` | 712–727 |
| `bg_set06` | 380–383 | `bg_set0f` | 792–823 |
| `bg_set07` | 412–436 | `bg_set10` | 856–877 |
| `bg_set08` | 462–476 | | |

2nd Impact : `bg00` 828–870, `bg01` 927–…, `bg03` 1043–1058, `bg04` 1117–1142,
`bg05` 1169–1189, `bg06` 1219–1244, `bg07` 1289–1303, `bg08` 1325–1337,
`bg09` 1365–1392, `bg0a` 1431–1444, `bg0b` 1085–1088, `bg0c` 1477–1496,
`bg0d` 1519–1547, `bg0e` 1608–1613, `bg0f` 2144–2158.

`outils/appariement.py` produit ce tableau.

### Le chemin PowerVR, et pourquoi l'index n'existe pas dans les données

Les tuiles de sprite sont dessinées en **PAL8** (format 6, constante `0x30000000`). Le
sélecteur de palette du mot de contrôle vaut `0x04000000`, soit la **banque 2** — la
constante est dans le pool des fonctions de palette elles-mêmes, à `0x8C0F59D0`. Or la
banque 2 commence à l'entrée 512 de la palette RAM, exactement là où commencent les
8 emplacements. Les index des tuiles vont de 0 à 63, donc une tuile lit toujours le
premier quart de la banque que son mot de contrôle désigne.

La palette RAM du PowerVR (`0x005F9000`, 1024 entrées de 32 bits) est remplie par deux
chemins distincts :

| entrées | chemin |
|---|---|
| 0–511 | **envoi en bloc** de 512 entrées depuis `0x8C84FFC0`, fonction `0x8C0F607C`, appel final à `0x8C0F61C0` |
| 512–1023 | **8 emplacements de 64 entrées**, vidange `0x8C0F594A`, source `0x8C7AFCCC + emplacement × 128` |

La table des 8 emplacements est à `0x8C6D6BAC`, son setter à `0x8C0F598E`. La routine
d'écriture est celle de Katana, `0x8C619CB0` : elle écrit `r5` entrées `u16` à
`0x005F9000 + index × 4`, masquées par `0xA0000000`.

**Seul l'emplacement 0 est écrit en cours de partie**, par deux appelants :
`0x8C0BFDC8` avec la constante 64, et `0x8C0DB5DE` avec une valeur qui part de 64 et
s'incrémente à chaque image — un cyclage de couleurs, pas une sélection de sprite.

Les couleurs passent par `0x8C0F6048`, qui convertit depuis la **palette RAM propre au
jeu**, à `0x8C828CD0` (dix références dans le binaire : c'est la zone de travail façon
CPS3, celle que les fondus et les cyclages modifient).

**D'où la conclusion :** il n'y a pas d'index de palette figé dans les données de sprite
parce que la palette est résolue **à l'exécution**, à travers la palette RAM du jeu. La
banque de l'exécutable n'est que la source ; ce qui atteint le PowerVR est ce que
l'étage a chargé et éventuellement modifié. Le lien exploitable statiquement est donc
la plage par décor mesurée plus haut — et c'est le bon niveau de granularité, pas un
pis-aller.

### Les palettes de personnage

Notées ici parce qu'elles resserviront, même si elles ne concernent pas les décors.

`0x8C0F59AA` donne l'adresse d'une palette : `0x8C1E9AEC + offset − 0x02798000`. Autrement
dit la palette `N` vit, dans l'espace d'adressage façon CPS3, à `0x02798000 + N × 128`.
C'est sous cette forme qu'elle est référencée dans les tables.

**Table 1 — `0x1CB850`** (adresse `0x8C1DB850`), 3230 enregistrements de 12 octets :

    { u32 adresse de palette, u32 offset de destination, u32 taille }

2875 ont une taille de 128, soit une palette. Elle se découpe en **112 listes**, une
nouvelle commençant chaque fois que la destination repasse à 0 — une liste par
personnage et par couleur. Destinations de 0 à `0x5500`.

**Table 2 — `0x1D4FD0`**, environ 111 enregistrements, même format mais **transferts
multiples** : tailles de 384 à 4480, toutes multiples de 128, destinations `0x2800` à
`0x3200`.

Aucune des deux ne touche aux plages de décor : **aucun pointeur du binaire** ne tombe
dedans. Ces tables sont purement personnage.

## Vérification contre une source extérieure

Les décors nettoyés de sfgalleries.net ont servi de contrôle indépendant.

**Ils sont inutilisables pour les palettes** — mesuré, pas supposé : leurs fichiers sont
préfixés `upscaled-`, et seulement **1,2 %** (vignette) et **0,9 %** (version 1080) de
leurs pixels tombent sur la grille 5 bits de l'ARGB1555, contre **74,4 %** pour une
capture Flycast. Une image de 2549×1080 y porte 339 514 couleurs distinctes : chaque
pixel a été recalculé.

**Mais ils valident l'assemblage.** Comparé au décor de Ryu (`bg02`), mon rendu place
exactement les mêmes éléments : l'arbre enneigé, la formation rocheuse, le panneau, le
parasol rouge, le ponton. Le décodage `.pvc`, l'entrelacement de Morton et la séparation
des banques sont donc justes, confirmés par une source qui n'a rien à voir avec ce
travail.

Deux écarts, tous deux instructifs : les **baigneurs manquent** de mon rendu (ce sont des
sprites `F_ETC25`, pas du décor), et les montagnes lointaines y forment une **bande
séparée** — le plan de parallaxe, rangé à part dans l'atlas.

**Et la structure des conteneurs se confirme.** La galerie nomme deux images « Elena
round 1 » et « round 2 » : ce sont exactement mes `bg08` et `bg09`, les deux `.pvc` de
`B08.PK`. Un conteneur qui porte plusieurs `.pvc` porte donc les **rounds successifs**
d'un même décor. Les perches à crânes du round 1, absentes de mon rendu, sont dans
`F_ETC30`/`F_ETC31` — cohérent.

## Le défilement des plans — la parallaxe

Trouvé en remontant depuis la table `0x8C7EFCCC` que lit la boucle de dessin.

**Huit plans, seize octets chacun, à `0x8C84135C` :**

    { s32 x, s32 x_précédent, s32 y, s32 y_précédent }     -- en virgule fixe 16.16

Les parties entières sont masquées par `0x3FF` : chaque plan **boucle sur 1024 pixels**,
soit exactement une banque `.pvc`. C'est la même arithmétique que les tilemaps du CPS3.

| adresse | rôle |
|---|---|
| `0x8C0FF7DC` | remet les huit plans à zéro |
| `0x8C0FF7F8` | `poser_plan(n, x, y)` — écrit la position courante **et** la précédente |
| `0x8C0FF814` | `poser_courant(n, x, y)` — n'écrit que la courante ; **14 appelants**, c'est celui qui déplace les plans à chaque image |
| `0x8C0FF828` | `avancer_plan(n, dx, dy)` en 16.16, avec masque `0x3FF` — **aucun appelant, code mort** |
| `0x8C0FF84E` | la validation par image |

La validation, appelée depuis `0x8C0AD324`, fait pour chacun des huit plans :

    table[n].x = (offset_X_global + (x_précédent >> 16) - caméra_X) & 0x3FF
    table[n].y = (offset_Y_global + (y_précédent >> 16) + caméra_Y - 2) & 0x3FF
    x_précédent = x   ;   y_précédent = y

avec `table` = `0x8C7EFCCC`, caméra X en `0x8C69CFEE`, caméra Y en `0x8C69CFF0`, et les
décalages globaux en `0x8C69CFF2` et `0x8C69CFF4`.

Côté dessin, `0x8C0F6988` choisit le plan par `(drapeaux >> 10) & 28` — huit plans de
quatre octets — et ajoute `table[n].x` et `table[n].y` à la position de l'objet.

**Le facteur de parallaxe n'est donc pas une donnée.** Il n'existe pas de table de
vitesses : chaque étage appelle `poser_courant` avec une position qu'il **calcule**. Le
coefficient est dans le code de l'étage.

## Les scripts d'étage

Une table de **quinze pointeurs de code** à `0x8C6020B0`, lue depuis `0x8C0E7FBC`,
`0x8C0E801E`, `0x8C0E8382`, `0x8C0E8408` et `0x8C0E8712` :

    8C0E9014  8C0E9498  8C0E9B74  8C0EA0F4  8C0EA538  8C0EAE58  8C0EB1F4  8C0EB688
    8C0EB9A0  8C0E9B74  8C0EBDF0  8C0EC338  8C0ECBFC  8C0ECFD4  8C0ECFD4

Deux doublons — `8C0E9B74` en positions 2 et 9, `8C0ECFD4` en 13 et 14.

**L'index est le numéro d'étage.** La table des conteneurs de `0x8C610BCC` porte
**vingt-et-une** entrées indexées par étage, et `b08.pk` y apparaît **deux fois**, aux
index 8 et 9 — les deux rounds d'Elena, qui partagent le conteneur mais pas le `.pvc`.
Le reste est une correspondance directe : index `n` → `bXX.pk` → `bgXX.pvc`.

En appliquant la même indexation à la table des scripts (`0x8C6020AC`, seize entrées,
0 à 15, donc `bg00` à `bg0f`) :

| index | décor | script |
|---|---|---|
| 0 | `bg00` gill | `0x8C0FE2D8` |
| 1 | `bg01` alex | `0x8C0E9014` |
| 2 | `bg02` ryu | `0x8C0E9498` |
| 3 | `bg03` yun | `0x8C0E9B74` |
| 4 | `bg04` dudley | `0x8C0EA0F4` |
| 5 | `bg05` necro | `0x8C0EA538` |
| 6 | `bg06` hugo | `0x8C0EAE58` |
| 7 | `bg07` ibuki | `0x8C0EB1F4` |
| 8 | `bg08` elena r1 | `0x8C0EB688` |
| 9 | `bg09` elena r2 | `0x8C0EB9A0` |
| 10 | `bg0a` oro | `0x8C0E9B74` *(partagé avec yun)* |
| 11 | `bg0b` yang | `0x8C0EBDF0` |
| 12 | **`bg0c` ken** | **`0x8C0EC338`** |
| 13 | `bg0d` sean | `0x8C0ECBFC` |
| 14 | `bg0e` urien | `0x8C0ECFD4` |
| 15 | `bg0f` | `0x8C0ECFD4` *(partagé avec urien)* |

C'est une **hypothèse structurelle**, pas une lecture : elle repose sur l'alignement des
deux tables et sur le fait qu'`bg0f`, décor sans aucun sprite, partage son script avec
un voisin. Elle reste à confirmer. Le script de Ken, `0x8C0EC338`, est celui qui compte
le plus de créations d'objet des treize (sept), ce qui va dans le bon sens : son décor
porte six sprites.

Chaque entrée est une **machine à états appelée par image**, écrite à la main : un état
en `+2`, une sous-étape en `+4`, une minuterie en `+10` alimentée par une table de durées
`u16`, et des appels à des sous-routines. C'est là que vivent, indissociablement, le
défilement des plans **et** l'apparition des sprites de décor — position, plan, et index
d'animation.

### Où vit le placement des plans — et ce que j'ai cru à tort

**Correction.** J'avais annoncé que la disposition des plans était « des données » dans un
tableau de descripteurs de 144 octets, et qu'il suffirait de trouver qui le remplit pour
avoir les quinze décors d'un coup. **C'est faux.** Le tableau de 144 octets à
`struct + 84` est le **tableau d'objets général du jeu** — 214 références dans le binaire —
et non une structure de décor. Il n'existe pas de table par étage à extraire.

Ce qui est établi, en revanche :

| élément | où |
|---|---|
| structure d'état du jeu | `0x8C6AF304` |
| nombre de plans / objets de fond de l'étage | `struct + 0x10`, **écrit par le code** (ex. `= 1` en `0x8C0E74DA`) |
| tableau d'objets | `struct + 84`, **144 octets** par objet ; x en `+10`, y en `+12` |
| positions de défilement | `0x8C84135C`, 16 octets par plan (voir la section précédente) |
| configuration par plan | `0x8C84142C`, **10 octets** par plan ; `0x8C0FFB54(n, a, b)` y écrit `rec[4] = (a << 6) | b` |

Les six crochets appelés **une fois par script** : `0x8C0E87A0`, `0x8C0E87F8`,
`0x8C0E8A8C`, `0x8C0E8BFE`, `0x8C0E8CF4`, `0x8C0E8D9A`. `0x8C0E8BFE` pose les plans à
partir du tableau d'objets ; `0x8C0E8A8C` les configure, avec `(n, 0, 31)`.

Les objets naissent de `0x8C046A38(id)` — **55 appels** depuis les scripts, dont
seulement 25 avec un identifiant immédiat (0 à 7, et un 29) ; les autres viennent de
variables. L'identifiant indexe un tableau de 2048 octets par entrée (pool `0x8C046AF0`).

**Conclusion : le placement est dans le code, réparti sur les quinze scripts. Il n'y a pas
de raccourci statique.**

### La bonne voie est l'émulateur, pas le désassemblage

Le tableau d'objets est en RAM à `0x8C6AF304 + 84`, 144 octets par entrée, x en `+10` et
y en `+12` ; le nombre de plans est en `struct + 0x10` ; les positions de défilement en
`0x8C84135C`, 16 octets par plan. Tout est lisible **dans un état sauvegardé Flycast**.

Relever ces trois zones une fois par étage donne, pour les quinze décors, le nombre de
plans, leur position et leur défilement réels — sans désassembler une seule machine à
états.

### L'outil est fait et il marche

    outils/flycast.py   lit un etat Flycast et rend les 16 Mo de RAM
    outils/etat.py      le releve : plans, objets de fond, palettes
    etat.cmd            le lanceur

Un état Flycast est un en-tête `FLYSAVE1`, une vignette PNG, puis une charge utile
**`#RZIPv`** : des tranches zlib de 1 Mo précédées de leur longueur. La RAM est repérée
**par signature** et non par offset — l'exécutable étant chargé à `0x8C010000`, les
premiers octets de `SF3_2ND.BIN` apparaissent tels quels dans le flux, ce qui donne la
base sans rien supposer du format.

Validé sur les deux états déjà présents dans `Documents\Dreamcast\data` : l'un est
l'étage d'Elena, l'autre celui de Ken (identifiés par le bloc de palettes chargé).

Relevé de l'étage de Ken :

| plan | position x | y | défilement x | y |
|---|---|---|---|---|
| 1 | 491,000 | 768,000 | 491 | 766 |
| 2 | 420,000 | 768,000 | 420 | 766 |

deux objets de fond, en x = 533 et 604.

### Et la banque de palettes en RAM donne la règle, mesurée

À `0x8C7AFCCC`, 128 octets par emplacement, les palettes de l'étage sont **identiques
octet pour octet** à celles de la banque de l'exécutable. Le relevé les regroupe en
suites à écart constant — c'est-à-dire directement `palette = base + emplacement` :

    etat de Ken   : emplacements  64 a  78  ->  palettes 1477 a 1491
    etat d'Elena  : emplacements  72 a  83  ->  palettes 1327 a 1338

**L'emplacement 64 correspond à la base du bloc du décor** (1477 pour `bg0c`, 1319 pour
`bg08`). Étalonnage sur Elena, dont quatre palettes sont confirmées par capture : ses
offsets de fichier 1, 3, 5 et 7 donnent 1320, 1322, 1324 et 1326, soit exactement
`emplacement 64 + offset`. La correspondance **`emplacement = 64 + offset du fichier`**
tient donc sur quatre points indépendants.

Les autres suites, aux emplacements 144 à 260, sont les autres groupes de drapeaux.

### Récolte des dix états (27/08/2026)

`outils/recolte.py` vide chaque état de sa substance dans `releves/` — un `.json` par
étage — pour que les emplacements de sauvegarde, limités à dix, redeviennent
réutilisables. Étage identifié automatiquement par le bloc de palettes chargé.

Couverts : `bg02` ryu, `bg03` yun, `bg04` dudley, `bg05` necro, `bg06` hugo, `bg07` ibuki,
`bg08` elena r1 (deux fois), `bg09` elena r2, `bg0a` oro.

**Manquent : `bg00` gill, `bg01` alex, `bg0b` yang, `bg0c` ken, `bg0d` sean, `bg0e` urien.**

Deux trous de la table décor → bloc de palettes sont comblés au passage :
**`bg02` = 989** et **`bg0a` = 1429**, qui ne figuraient pas dans le relevé de
`appariement.py`.

### Ce que ces dix états ne donnent pas : les coefficients de parallaxe

Huit des dix montrent tous les plans à `x = 704` — la position neutre du début de round.
Seuls l'ancien état d'Elena (693 / 514 / 562) et celui de Ryu (704 / 192) portent un
défilement réel. La récolte donne donc la **disposition initiale**, pas les facteurs.

Et les variables de caméra que le désassemblage désignait (`0x8C69CFEE`, `0x8C69CFF0`)
valent **zéro** dans les dix états : ce ne sont pas la caméra, seulement des décalages.

**Protocole qui s'en passe.** Deux états sur le *même* décor, l'un les combattants poussés
dans le coin gauche, l'autre dans le coin droit. L'écart de position de chaque plan entre
les deux, divisé par celui du plan de premier plan — qui suit la caméra au rapport 1 —
donne le coefficient de parallaxe directement, sans avoir à trouver la caméra.


## Ce qui reste ouvert

- **Laquelle de ces palettes va avec quel sprite.** Il n'existe pas d'index figé (voir
  le chemin PowerVR ci-dessus). Ce qu'il faudrait pour le résoudre en général, c'est
  reconstituer le contenu de la palette RAM du jeu (`0x8C828CD0`) au chargement d'un
  étage — code qui la remplit, ou relevé en émulateur.

  En pratique, **une capture d'écran suffit** : voir la méthode ci-dessous, elle a donné
  une réponse certaine du premier coup.

### Retrouver une palette depuis une capture d'écran

Méthode validée sur un cas à réponse connue. Elle marche même avec des scanlines, qui ne
font qu'assombrir des lignes entières :

1. isoler les pixels de l'élément dans la capture ;
2. les regrouper par **teinte** (chaque pixel divisé par son canal maximum) et garder,
   dans chaque famille, le pixel le plus clair — les scanlines n'assombrissent jamais
   au-delà de la vraie couleur ;
3. quantifier sur la grille 5 bits de l'ARGB1555 ;
4. chercher dans les 2715 palettes celle qui contient le plus de couleurs de la rampe.

Exemple : la bannière **BONUS GAME** de `F_ETC100` donne la rampe
(66,197,0) → (90,222,8) → (115,222,8) → (148,239,0) → (181,239,0) → (197,255,33).
Une seule palette la porte : **2317**. Rendu vérifié contre la capture, identique —
vert vif, dégradé jaune-vert, contour noir, le « 0 » cyan.

### Deux corrections que ce cas impose

**Tous les assets `F_` ne prennent pas une palette de leur décor.** La palette 2317 est
**hors** de la plage de `bg10` (1219–1244). `F_ETC100` est une bannière globale, chargée
avec l'étage sans lui appartenir. La plage par décor vaut pour les sprites propres à un
décor, pas pour les éléments d'interface.

**Le choix par lissage ne vaut rien.** Sur ce cas à réponse connue, il classe la bonne
palette **2311e sur 2715** — et son filtre d'injectivité l'avait même exclue d'office,
une vraie palette de sprite ayant tout à fait le droit de donner la même couleur à deux
index. Méthode abandonnée, mesurée fausse.
- La déduction directe est exclue : **aucune** des 80 tuiles testées n'apparaît dans le
  décor de son étage, les sprites sont des dessins distincts.
- ~~**L'assemblage des sprites.**~~ **Percé** le 27/08/2026 — voir `ASSEMBLAGE.md`.
  Le morceau de 8 octets se lit `{u16 tuile, u16 palette, u16 y, u16 code<<12 | x}` ;
  le quartet `code` porte la taille en tuiles (`l = 1 << (((code>>2)&3)-1)`,
  `h = 1 << ((code&3)-1)`), `x` et `y` sont des **centres**, et les tuiles d'un morceau
  se suivent **en colonnes**. Vérifié contre une capture : l'acolyte de Gill sort
  identique à `reference-gill-acolyte.png`.
- ~~**Laquelle de ces palettes va avec quel sprite.**~~ Largement résolu : le champ
  palette d'un morceau est `drapeaux << 9 | offset`, et la palette vaut
  `base(décor, drapeaux) + offset`. Les bases sortent de la table de transferts à
  `0x1D4DBC`. Voir `ASSEMBLAGE.md`. Reste à localiser la table qui associe un décor à
  ses quatre bases.
- Le rôle de `hdr[0x10]` dans l'en-tête `F_ETCnn`.
- ~~La logique de défilement des plans côté Dreamcast~~ — **localisée**, voir la section
  « Le défilement des plans » ci-dessus. Ce qui reste, ce sont les **quinze scripts
  d'étage** : coefficients de parallaxe et placement des sprites de décor y sont mêlés au
  code.

---

## La composition, reprise le 27/08/2026 — ce qui est trouvé, ce qui reste

Trois choses lues dans le code, une quatrième vue à l'image, et une correction qui compte.

### 1. D'où viennent les 704 / 768 — `0x8C0E8BFE` décodé

La boucle fait, pour chaque objet de fond `n` de 0 à `état[0x10]-1` :

    poser_plan(n + 1, (-objet[n].x) & 0x3FF, (768 - objet[n].y) & 0x3FF)

`768` est un **immédiat dans le code** (`mov.w #0x0300`), pas une donnée. Les objets de
fond sont tous à `x = 320, y = 0` : d'où `(-320) & 0x3FF = 704` et `768 - 0 = 768`, les
valeurs qu'on retrouve dans tous les relevés. Vérifié au chiffre près.

**Ce ne sont donc pas des données d'étage.** C'est la position neutre de début de round,
la même partout ; le défilement réel est posé image par image par `poser_courant`.

Et l'objet `n` alimente le plan `n + 1` : le plan 0 n'est jamais un décor.

### 2. Comment un élément de décor est placé — `0x8C0F6988` décodé

Pour chaque élément de la liste :

| champ | sens |
|---|---|
| `+0` u16 | drapeaux ; le **plan** est `(drapeaux >> 10) & 28`, huit plans de quatre octets |
| `+2` u16 | index, masqué `0xFF7F`, dans une table de **16 octets par entrée** |
| `+4` u16 | x — auquel le dessin ajoute `table_defil[plan].x` |
| `+6` u16 | y — auquel il ajoute `table_defil[plan].y` |
| `+8`, `+9` | encore deux champs, non établis |

La table de 16 octets est pointée par la **variable** `0x8C602348`, valeur initiale
`0x8C72FCCC` — donc **en RAM**, remplie au chargement de l'étage. C'est là que vit la
composition, et c'est pour ça que le désassemblage seul ne pouvait pas la donner.

### 3. Les coefficients de parallaxe sont dans la fiche de l'objet

La fiche de 144 octets porte, en `+16` et `+20`, deux mots en **16.16** :

| décor | plan 0 | plan 1 | plan 2 |
|---|---|---|---|
| `bg00` | 0,2500 / 0,6250 | 1,0 / 1,0 | |
| `bg01` | 0,6250 / 0,7500 | 1,0 / 1,0 | |
| `bg03` | 0,8750 / 1,0625 | 1,0 / 1,0 | 0,0 / 0,0 |
| `bg08` | 0,5000 / 0,5000 | 1,0 / 1,0 | |
| `bg0a` | 0,7500 / 0,8750 | 1,0 / 1,0 | 0,5 / 0,9375 |
| `bg0b` | 0,8750 / 1,0625 | 1,0 / 1,0 | |
| `bg0d` | 0,9375 / 1,0 | 1,0 / 1,0 | |
| `bg0e` | 0,3750 / 0,7500 | 1,0 / 1,0 | |
| `bg0f` | 0,7500 / 0,8750 | 1,0 / 1,0 | |

Le plan de premier plan vaut **exactement `0x10000`** dans les neuf états, et les autres
sont des multiples de `0x2000` — la forme et l'encodage exacts du `msp[étage][plan][2]`
de 3rd Strike. **Ce n'est pas encore prouvé** : il y faudrait deux états du même décor à
des positions de caméra différentes, le protocole décrit plus haut. Mais la note « le
facteur de parallaxe n'est pas une donnée » était trop pessimiste : il est bien dans une
fiche, seulement dans une fiche de RAM.

### 4. Le repère vertical est le même que celui de 3SX

Vu à l'image : `rendus/2i-b0c-banque0.png` découpé à `(704, 768)` sur 384×224 tombe pile
sur un morceau cohérent de la jetée de Ken — la poupe du bateau, le banc, la jardinière.
La banque `.pvc` est bien un plan de 1024×1024 qui boucle, et l'origine `(704, 768)` est
la bonne. La banque 1 de `bg0c` est **entièrement vide** : le décor tient dans une seule
banque, sa bande de ciel et sa bande de sol à des `y` différents.

Et côté 3SX, les pages jouées d'un plan sont à `y = 768..1023` (`CARTES-BG.md`). **Les
deux moteurs ancrent la bande jouée au même endroit d'un plan de 1024 qui boucle.** C'est
le raccord qui permettra de poser une bande de 2I dans un plan de 3SX.

### La correction : les étiquettes de `releves/` sont fausses

L'identification par le bloc de palettes se trompe. Sur les dix états, elle attribuait
dix-neuf décors, dont **ryu, dudley, necro, hugo, ibuki et ken** — aucun des six n'y est.

L'identification exacte se fait par les **octets du conteneur, restés en RAM** : quatre
témoins de 1024 octets riches et uniques pris dans chaque `.pvc`, cherchés tels quels.
Neuf états sur dix sortent avec les quatre témoins d'un seul décor, et zéro pour tous les
autres — il n'y a pas de place pour le doute.

| état | décor |
|---|---|
| `.state` | `bg0b` |
| `_1` | **non identifié** — son conteneur n'est plus en RAM |
| `_2` | `bg03` |
| `_3` | `bg0d` |
| `_4` | `bg0e` |
| `_5` | `bg0f` |
| `_6` | `bg00` |
| `_7` | `bg01` |
| `_8` | `bg08` **et** `bg09` — les deux rounds d'Elena, même `.pk` |
| `_9` | `bg0a` |

**Manquent donc : `bg02` ryu, `bg04` dudley, `bg05` necro, `bg06` hugo, `bg07` ibuki,
`bg0c` ken.** Il faut six états de plus, et `releves/` ne les remplace pas.

`outils/etat2.py` fait tout ça ; `relever2.cmd` le lance ; `releves2/` porte le résultat.

### 5. Ce que désigne l'index : le morceau, déjà résolu

L'index `+2` d'un élément mène à `*(0x8C602348) + index * 16` — dans le même tableau de
32768 entrées de 16 octets, qui va de `0x8C72FCCC` à `0x8C7AFCCC`, où commence la palette
RAM. Chaque entrée est un **morceau de sprite déjà résolu** :

    { u16 tuile, u16 ?, u16 x, u16 y,
      u16 (l-1) << 8 | (h-1), u16 type << 8 | code, u16 emplacement de palette, u16 0 }

C'est exactement le morceau de 8 octets d'`ASSEMBLAGE.md`, mais avec la **position
absolue** et la **taille explicite** — le travail de centrage et d'addition de la position
d'objet est déjà fait par le jeu.

**La preuve, et elle est massive :** la taille explicite et le quartet `code` disent la
même chose deux fois. Sur les dix états, **54609 morceaux sur 54678 concordent**. Les 69
écarts sont des sprites mis à l'échelle, et rien d'autre. Les onze tailles rencontrées
sont exactement les onze que le `code` autorise.

**Correction.** J'avais pris l'octet haut de `+10` pour un « type ». C'est un jeu de
**drapeaux** : le bit 8 dit que `y` est un centre, le bit 9 que `x` en est un — les masques
`0x0100` et `0x0200` sont testés séparément en `0x8C0F6A08`. Un morceau à drapeaux `0x00`
est un morceau normal dont `x` et `y` sont le **coin**. Le décompte honnête, liste
d'affichage écartée : **54769 concordances contre 1216 écarts, 97,8 %.**

Reste, non identifié, un groupe de **huit enregistrements par fond de plan** — et
seulement pour les index `0x3140`, `0x3150`, `0x3160`, ceux des fonds :

    w0 = w1 = w2 = 0    w3 = 127, 255, 383, 511, 639, 767, 895, 1023
    w4 = 0x7F00         w5 = 0x000C / 0x001C / 0x003C    w6 = emplacement de palette

`w3` avance de 128 : ce sont les **huit colonnes du plan**, dernier `x` de chacune. Mais
l'arithmétique du dessin en tire `l = 128, h = 1`, ce qui ne fait pas un fond, et aucun
champ ne nomme de texture. Le fond de plan est donc lié ailleurs — le suspect est
l'enregistrement de configuration `0x8C84142C + n*10`, dont le `+4` vaut `(a << 6) | b`,
soit 31.

### Ce qu'il reste à faire, précisément

1. Les huit enregistrements par fond de plan, et où la texture du fond est liée —
   commencer par `0x8C84142C + n*10`, `+4`.
2. Six états de plus : `bg02` ryu, `bg04` dudley, `bg05` necro, `bg06` hugo, `bg07` ibuki,
   `bg0c` ken.
3. Confirmer les coefficients de parallaxe par deux états du même décor, caméra à gauche
   puis à droite.

---

## Où se coupe une banque — la règle, mesurée sur les 21 décors

`outils/bandes.py` mesure les **bandes de contenu** d'un atlas : où commencent et
finissent les lignes non vides d'une banque de 1024×1024.

Le résultat ne souffre aucune exception sur les 21 décors de 2nd Impact :

> **Une banque à deux bandes se coupe à `y = 512`.** La bande du haut finit à 512 ou
> avant, celle du bas commence à 512 ou après.

| décor | bande haute | bande basse |
|---|---|---|
| `bg00` | 112..432 | 528..1024 |
| `bg01` | 0..480 | 726..1024 |
| `bg02` | 112..**512** | 699..1024 |
| `bg03` | 0..496 | **512**..1024 |
| `bg04` | 80..400 | 568..1024 |
| `bg05` | 0..**512** | 618..973 |
| `bg07` | 11..**512** | 528..1024 |
| `bg0a` | 288..432 | 526..1024 |
| `bg0c` | 0..496 | 628..1024 |
| `bg0d` | 0..368 | 644..1008 |
| `bg0e` | 64..464 | 712..1024 |
| `bg0f` | 46..464 | 528..1024 |
| `bg10` | 0..448 | 606..1024 |

Quatre décors (`bg06`, `bg09`, `bg0b`, `bg11`) n'ont qu'une bande, qui occupe la banque
entière. Aucun décor n'a de bande qui **traverse** 512.

**La bande du haut est le plan lointain, celle du bas le plan proche.** Et 3SX tient
exactement 1024×512 par plan, à `y = 512..1023` (`CARTES-BG.md`). Donc :

> chaque demi-banque se pose **à l'identique** sur les 32 pages d'un plan de 3SX —
> la moitié basse telle quelle, la moitié haute remontée de 512.

Aucun recadrage, aucun décalage choisi à la main. C'est `outils/bande3sx.py`.

### Ce que faisaient les quatre compositions ratées

En cherchant les pixels de `stage22/*.tex` dans les atlas, on retrouve la découpe
précédente : plan lointain pris dans la bande **du haut** (bon), mais aux `y` **−16, 0,
64, 192** selon les pages, avec des `x` décalés de +16, −64, +192, et plusieurs pages
recopiées de la même source. Le plan proche, lui, était pris à `y = 704..768`, et une
seule page — la 22 — tombait juste, à l'écart `(0, 0)`.

C'était de la découpe à l'œil, page par page. La règle ci-dessus n'en laisse pas la
possibilité.

### Ce que le masque emprunté ne peut pas porter

L'étage 22 emprunte le fichier de Necro, donc son masque de pages. Pour la gorge `bg0f` :

- plan lointain, `0x7E7E7E7E` : colonnes 1 à 6 des quatre rangées. La bande haute de
  `bg0f` tient en `x 144..848`, soit les colonnes 1 à 6 — **elle passe entière** ;
- plan proche, `0x424FEFFF` : dans la zone jouée (rangées 2 et 3), il manque la page
  **rangée 2, colonne 3**. Un rectangle noir de 128×128 y est attendu.

### Ce que la première partie a montré : la découpe est bonne, le décor ne l'était pas

Vu à l'écran le 27/08/2026 : la gorge `bg0f` sort d'un seul tenant, sans couture et sans
décalage — la règle tient. Mais il restait de grands trous noirs, plus que le seul attendu.

`outils/couverture.py` les explique sans rien supposer : il mesure, décor par décor, la
part de la **zone jouée** (rangées 2 et 3) qui resterait noire une fois les deux plans
empilés.

| décor | sous le masque de Necro | sous un masque plein |
|---|---|---|
| `bg06` hugo | **8,3 %** | 8,3 % |
| `bg0c` ken | **11,2 %** | 4,8 % |
| `bg01` alex | **13,0 %** | 1,6 % |
| `bg04` dudley | 15,6 % | 15,6 % |
| `bg02` ryu | 18,8 % | **0,0 %** |
| … | | |
| `bg0f` **la gorge** | **42,2 %** | **42,0 %** |

La colonne de droite tranche : pour `bg0f`, le masque emprunté ne coûte **rien** —
42,2 contre 42,0. Les trous sont **dans son art**, pas dans le masque. Son décor ne fait
que 768 px de large dans un plan de 1024, et sa bande haute est creuse là où on la
regarde. C'était le décor qui n'allait pas.

À l'inverse `bg02` et `bg11` sont pleins à 100 % sous un masque plein : eux sont bridés
par le masque, et gagneraient à emprunter le fichier d'un autre étage.

Trois décors sont découpés et prêts, avec leur lanceur : `bande22-bg06`, `bande22-bg0c`,
`bande22-bg01`.

### Ne plus emprunter un décor troué — emprunter celui qui ne l'est pas

Frédéric, 27/08/2026 : *« pourquoi on s'entête à recouvrir un décor existant, pour ne pas
en créer un vierge et ensuite le remplir ? »* Il a raison, et la réponse était à un
chiffre de distance.

Ce qui forçait l'emprunt n'était pas le fichier de textures : c'était
**`bgtex_stage_gbix[22]`**, recopié de Necro, qui décide quelles pages existent. Une page
que le masque ne donne pas n'est pas noire — le jeu y montre **ses propres pixels**. Ce
sont les bandes verticales aux extrémités et les grands aplats.

Or c'est une table de `bg_data.c`, qu'on contrôle. Il suffisait de trouver un étage dont
les deux plans chargent 32 pages sur 32. Il n'y en a **qu'un** : l'étage 10, Yang,
`{ 0xFFFFFFFF, 0xFFFFFFFF }`.

Trois lignes, et une reconstruction :

| fichier | avant | après |
|---|---|---|
| `gd3rd_data.c`, `spans[42]` | `{125, 3}` — bloc de l'étage 5 | `{150, 3}` — bloc de l'étage 10 |
| `bg_data.c`, `bgtex_stage_gbix[22]` | `{0x7E7E7E7E, 0x424FEFFF}` | `{0xFFFFFFFF, 0xFFFFFFFF}` |
| `bg_data.c`, `use_family[22]` | 32 | 0 |

**64 pages au lieu de 46, et plus un seul trou de masque.** La zone jouée de `bg02`,
`bg01` et `bg0c` sort entière et sans couture. Les jeux de pages sont dans
`plein22-bg02`, `plein22-bg01`, `plein22-bg0c`, découpés avec
`bande3sx.py <décor> 132:0xFFFFFFFF:haut 196:0xFFFFFFFF:bas <dossier>`.

`tokusyu_stage` reste à 0 pour l'étage 22 — il est choisi sur `bg_w.stage` et seuls les
étages 3, 7, 10 et 19 en sortent — donc l'animation de pages de Yang ne s'applique pas.
Et comme les clés de `tex_remix` sont **par numéro de page** au-delà des 22 étages
d'origine, le décor de Yang reste intact, exactement comme celui de Necro l'était.

### Deux problèmes distincts, et ce qui est déjà écarté

Le masque plein n'a pas suffi. Ce qui reste se sépare en deux, et il ne faut pas les
confondre.

**Les bandes verticales aux extrémités — expliquées et mesurées.** L'art de `bg02` fait
**768 px de large dans un plan de 1024**. Dans la zone jouée, son plan proche est
transparent à **100 %** aux colonnes 0 et 7 de la rangée 2, et à 50 % de la rangée 3 :
le plan lointain, lui opaque partout, y montre son ciel. Ce n'est pas un problème de
texture, c'est que **la caméra va plus loin que l'art de 2nd Impact**. Sur Dreamcast les
limites de défilement l'en empêchent ; ici elles viennent des données de l'étage 5.

**Les rectangles pâles — pas encore expliqués, mais quatre pistes écartées :**

| piste | écartée par |
|---|---|
| une mauvaise règle d'alpha | mesuré : `bit 15 = 1` **exactement** là où le pixel n'est pas `0x0000` — 40,9 % + 59,1 % = 100,0 % sur `bg02` |
| des pages non remplacées | le journal du jeu : **64 substitutions**, aucun avertissement |
| une liste de décor qu'on ne remplace pas | le manifeste du dump : listes 132 et 196, 32 pages chacune, **toutes couvertes**, aucune autre |
| des trous dans nos propres fichiers | mesuré hors du jeu : hors bords et bande de ciel, le plan proche n'a aucune transparence éparse |

Il reste donc le **placement** : le jeu met nos pages ailleurs que là où je les calcule.
`outils/testpages.py` fabrique 64 pages numérotées — teinte par colonne, clarté par
rangée, indice de bit en gros — et le lanceur `Etage 22 - test de placement (64 pages)`
les pose. Quatre captures (centre, fond gauche, fond droit, en saut) diront quelles
rangées sont vraiment à l'écran et où passe le bord du plan.

### Ce que les pages numérotées ont tranché

Premier test, 64 pages colorées et numérotées, quatre captures :

1. **Les rangées à l'écran sont bien la 2 et la 3.** Toutes les étiquettes lues disent
   `r2` ou `r3`. La règle de placement `y = 512 + (i >> 3) * 128` est confirmée à l'écran.
2. **Seul le plan proche (L196) se voit.** Aucune étiquette `L132` n'apparaît : les pages
   de test sont opaques, donc le plan lointain est entièrement couvert. Dans un décor, il
   ne se montre que par les trous du plan proche.
3. **Les petits carrés sont là aussi avec les pages de test.** Ils ne viennent donc pas
   des pixels de 2nd Impact, ni de l'alpha, ni du découpage : c'est le rendu.
4. **La caméra atteint bien la colonne 0** — capture à fond à gauche, étiquette
   `L196 r2 c0`. Ce qui confirme le diagnostic des bandes verticales : l'art de 2I fait
   768 px de large, la caméra va jusqu'à 1024.

Le premier jeu de pages avait un défaut : **les deux plans partageaient les mêmes
couleurs**, donc un carré étranger pouvait venir de l'un comme de l'autre. Corrigé —
`testpages.py` donne au plan lointain une famille gris-bleu et au plan proche des teintes
vives, plus un damier de 16 px en haut de chaque page pour voir un décalage interne.

### Les petits carrés : ce n'est pas nous, c'est le rendu

Deuxième test, chaque plan avec sa propre famille de couleurs. Verdict sans ambiguïté :

- les carrés sont **gris-bleu**, la famille du plan lointain → **le plan lointain traverse
  le plan proche** ;
- ils font **16×16 texels** — le damier de 16 px posé en haut de chaque page a servi de
  règle ;
- ils sont **au même endroit dans chaque page**, capture à gauche comme au centre.

Et surtout, vérifié **dans les fichiers, sans lancer le jeu** : les 32 pages de test du
plan proche sont **alpha 255 partout**, pas un pixel transparent. Le trou n'est donc ni
dans notre découpe, ni dans notre alpha, ni dans les pixels de 2nd Impact — il est percé
par le chemin de texture du portage.

Ce qui a été relu et écarté au passage : `flPS2ConvertContext` ne travaille pas par blocs
et le halving d'alpha du PS2 a déjà été retiré ; `flPS2ConvertTextureFromContext` ne fait
qu'un `memcpy` ou une conversion pixel à pixel ; `ppgSetupTexChunk_3rd` ne touche pas aux
pixels après la substitution. Le journal du jeu ne signale rien : 64 substitutions,
aucun avertissement.

Reste à savoir **quelle case de 16×16** est percée. `test22uni` répond : plan lointain
magenta uni, plan proche vert uni avec une **grille blanche tous les 16 px**, une règle
graduée posée sur l'image. Lanceur `Etage 22 - test uni (ou est le trou)`.

### Ce que la grille a donné, et où ça s'arrête

Plan lointain magenta uni, plan proche vert avec une règle graduée tous les 16 px :

- les taches magenta **tombent pile dans les cases de la grille** — elles sont donc
  alignées sur la **texture**, pas sur l'écran ;
- il y en a **une ou deux par page de 128×128**, aux mêmes cases d'une page à l'autre ;
- espacement horizontal d'environ 7 à 8 cases, soit une page.

Une texture opaque qui laisse voir la couleur de l'autre plan à une case près, alignée sur
la page : la mémoire de la page proche **contient** des pixels de la page lointaine. Ce
n'est pas de la transparence, c'est le contenu.

Le chemin a été relu de bout en bout et rien n'y touche aux pixels :
`ppgSetupTexChunk_3rd` → `TexRemix_Substitute` → `flCreateTextureHandle` →
`flPS2ConvertTextureFromContext` (memcpy ou conversion pixel à pixel, sans blocs) →
`flPS2CreateTextureHandle` → `Renderer_CreateTexture` → `glTexImage2D` du tampon entier.
L'allocateur `plmemRegisterS` a été relu aussi : ses deux sens de remplissage vérifient
bien la place avant de poser un bloc, et il tombe en erreur fatale s'il manque de place —
il ne peut donc pas recouvrir deux blocs en silence par épuisement.

**Ce que ça veut dire pour le chantier.** La découpe est bonne. La coupe à `y = 512`, le
placement `x = (i & 7) * 128, y = 512 + (i >> 3) * 128`, le masque plein : tout tient, et
les pages de test le prouvent — les rangées lues à l'écran sont bien la 2 et la 3, et nos
fichiers sont **alpha 255 partout**. Ce qui reste est un défaut du portage, indépendant de
2nd Impact.

**Prédiction à vérifier, et elle ne coûte rien :** si c'est bien le portage, le remix du
ponton de Ken — cent pages de 32 bits posées par empreinte, pas par numéro — doit montrer
les mêmes carrés de 16×16. Le lanceur existe déjà : `Remix - ponton de Ken.cmd`. S'il les
montre, le défaut est antérieur à ce chantier et n'a jamais été vu ; s'il ne les montre
pas, la différence est dans le chemin **par numéro** des étages ajoutés.

### « Ces trous n'existaient pas au début »

Remarque de Frédéric, 28/08/2026 — et elle change la question. Si le défaut est apparu,
c'est qu'il vient de quelque chose qu'on a changé, pas du portage depuis toujours.

Ce qui a bougé sur l'étage 22 dans cette session, et rien d'autre :

| | avant | après |
|---|---|---|
| `spans[42]` | bloc de l'étage 5 (Necro) | bloc de l'étage 10 (Yang) |
| `bgtex_stage_gbix[22]` | `0x7E7E7E7E / 0x424FEFFF`, 46 pages | `0xFFFFFFFF / 0xFFFFFFFF`, 64 pages |
| `use_family[22]` | 32 | 0 |

Deux binaires sont donc posés côte à côte dans `build\application\bin` :
**`3sx-necro.exe`** (l'emprunt d'origine) et **`3sx-plein.exe`** (le nouveau). Le lanceur
`Bissection - le meme test avec l emprunt d origine` passe **le même test uni** sur les
deux, l'un après l'autre — `test22uni-necro` pour le premier, `test22uni` pour le second.

- Trous dans les deux → le défaut est ancien et n'a rien à voir avec l'emprunt.
- Trous seulement dans le plein → c'est le bloc de Yang ou le masque à 32 pages, et le
  remède est dans les trois lignes du tableau ci-dessus.

Les sources restent au masque plein : la bissection se fait avec les deux binaires déjà
construits, pas en laissant l'arbre à moitié défait.

### Le trou de 16×16 : trouvé, et corrigé

La bissection a répondu : **les carrés sont là dans les deux binaires**. Ce qui change entre
Necro et Yang, ce sont les grandes zones — celles-là suivent le masque. Les carrés, non.
Le changement d'emprunt ne les avait donc pas créés.

La cause est dans `ppgWriteQuadUseTrans`, `Source/Common/PPGFile.c` :

    transTotal = ((ppg->transNums >> 8) & 0xFF) | ((ppg->transNums & 0xFF) << 8);
    if (transTotal != 0) {
        for (i = 0; i < transTotal; i++) {
            iPoint = *tran++;  cofsXY = *tran++;
            xs = (cofsXY >> 4) + 1;   ys = (cofsXY & 0xF) + 1;
            sx = iPoint % ppgw;       sy = iPoint / ppgw;
            ...  ppgWriteQuadOnly2(qvtx, col, ...);
        }
        return 1;
    }

**Une page n'est pas dessinée d'un seul quad.** Son en-tête porte une liste de rectangles —
une grille de 8×8 blocs de 16×16 sur une page de 128×128, `xs` et `ys` allant de 1 à 16 —
et seuls ceux-là sont dessinés. Ce que la page laissait vide n'est jamais mis à l'écran.

Cette liste décrit **la page de l'archive**. Un remplacement change les pixels, pas la
liste : là où l'original était vide, nos pixels ne sortent jamais et le plan derrière
apparaît, en carrés de 16×16, alignés sur la page. Exactement ce que la grille a montré.

C'est aussi pourquoi ça ne se voyait pas « au début » : avec deux vrais décors empilés, un
trou de 16×16 laisse voir de l'image plausible. Il n'a saute aux yeux que le jour où le
plan lointain est devenu un aplat — le ciel de `bg02`, puis le magenta du test.

**Le remède**, trois endroits :

| fichier | quoi |
|---|---|
| `port/video/tex_remix.c/.h` | `TexRemix_HandleIsReplacement()` — marque les poignées qui portent un remplacement, que le dump soit actif ou non |
| `Source/Common/PPGFile.c` | `ppgWriteQuadUseTrans` saute la liste pour ces poignées : un remplacement porte son propre alpha et couvre la page, il a droit à un seul quad |
| `AcrSDK/ps2/flps2vram.c` | `flCreateTextureHandle` efface la marque à chaque création, pour qu'une poignée recyclée ne garde pas celle d'avant |

Compilé avec `-Werror`, code 0. Lanceur `Etage 22 - le trou de 16x16 corrige`.

**Confirmé à l'écran.** Le même jeu de 46 pages, avant et après :

- avant : des carrés de 16×16 partout, dans chaque page ;
- après : **plus un seul**, et un unique rectangle magenta de 128×128.

Ce rectangle-là n'est pas un défaut : c'est la page **rangée 2, colonne 3**, la seule que
le masque de Necro ne fournit pas dans la zone jouée — annoncée bien avant de la voir. Le
jeu de pages laissé en place datait de la bissection ; le binaire, lui, demande les 64 du
masque plein. Les deux remis d'accord, il ne reste rien.

### Les bandes verticales : la caméra, pas la texture

Une fois le trou de 16×16 bouché, le décor sort entier — mais il restait une bande à
chaque bout. Mesure de la couverture du plan proche de `bg02` dans la zone jouée, par
colonne de 32 px :

| x | couverture |
|---|---|
| 0..127 | **25 %** |
| 128..255 | 56 à 79 % |
| 256..895 | 84 à 100 % |
| 896..1023 | **25 %** |

L'art de 2nd Impact fait **768 px de large — x 128 à 896 — dans un plan qui en fait 1024**.
Aux colonnes 0 et 7 il n'y a presque rien, et le plan lointain s'y voit.

La caméra est centrée sur `0x200` et la fenêtre fait 384 px : elle montre donc le plan de
`l_limit2 - 192` à `r_limit2 + 192`. Avec les limites de l'étage 5, `0x110` et `0x2F0`,
elle allait de **80 à 944** — 48 px de trop de chaque côté, exactement la largeur des
bandes observées.

    limit_tbl3[22] : { 0x110, 0x2F0 }  ->  { 0x140, 0x2C0 }

soit 128 à 896 : l'art, et pas un pixel de plus. Le terrain est un peu plus court, c'est
le prix d'un décor de 768 px.

**`bande3sx.py` calcule maintenant ces deux nombres** pour n'importe quel décor : il mesure
l'étendue en x de la zone jouée et en déduit les limites. `bg02` demande
`{ 0x140, 0x2C0 }` ; `bg01` et `bg0c`, dont l'art occupe les 1024 px, se contentent de
`{ 0xC0, 0x340 }` — les limites de `bg02` leur vont aussi, elles sont seulement plus
serrées que nécessaire.

### Vérifié contre l'original (28/08/2026)

Côte à côte avec Flycast, même décor, même moment : le cadrage est le même et **la caméra
bute au même endroit**. Les limites `{ 0x140, 0x2C0 }`, calculées sur l'étendue de l'art
et non réglées à l'œil, tombent sur celles de la Dreamcast.

Ce que 3SX ne montre pas encore, et qui est du sprite, pas du décor : la **cascade animée**
à gauche et les **baigneurs**. Images d'animation de la banque 1 et assets `F_ETC` — format
décodé dans `ASSEMBLAGE.md`, placement encore à faire.

## Les coefficients de parallaxe — confirmés, et **les seize décors**

Seize états sauvegardés, identifiés par les octets du conteneur restés en RAM.
`outils/etat2.py`, `relever2.cmd`, `releves2/`.

| décor | | plans | coefficients (x / y) par plan |
|---|---|---|---|
| `bg00` | gill | 2 | 0,25 / 0,625 — 1 / 1 |
| `bg01` | alex | 2 | 0,625 / 0,75 — 1 / 1 |
| `bg02` | ryu | 2 | 0,75 / 0,9375 — 1 / 1 |
| `bg03` | yun | 3 | 0,875 / 1,0625 — 1 / 1 — 0 / 0 |
| `bg04` | dudley | 2 | 0,75 / 0,875 — 1 / 1 |
| `bg05` | necro | 3 | 1 / 1 — 1 / 1 — 1 / 1 |
| `bg06` | hugo | 2 | 0,75 / 0,875 — 1 / 1 |
| `bg07` | ibuki | 3 | 0,625 / 1 — 1 / 1 — 0,25 / 0,625 |
| `bg08`+`bg09` | elena | 2 | 0,5 / 0,5 — 1 / 1 |
| `bg0a` | oro | 3 | 0,75 / 0,875 — 1 / 1 — 0,5 / 0,9375 |
| `bg0b` | yang | 2 | 0,875 / 1,0625 — 1 / 1 |
| `bg0c` | ken | 2 | 0,75 / 0,75 — 1 / 1 |
| `bg0d` | sean | 2 | 0,9375 / 1 — 1 / 1 |
| `bg0e` | urien | 2 | 0,375 / 0,75 — 1 / 1 |
| `bg0f` | la gorge | 2 | 0,75 / 0,875 — 1 / 1 |

**Les seize décors de 2nd Impact y sont.** Reste un état non identifié — son conteneur
n'est plus en RAM ; ce n'est pas un décor manquant, c'est un état de trop.

À noter sur `bg02` : son plan proche est ancré en `x = 832` et non `320`, donc à `192` et
non `704`. C'est le seul décor dans ce cas sur les seize. Le script d'étage y place ses
plans autrement — à garder en tête avant de le découper, l'origine n'y est pas la même.

### La confirmation, et elle est tombée toute seule

Le protocole demandait deux états du même décor à des caméras différentes. Deux états
l'ont fourni sans qu'on les cherche : `bg0f` est saisi **deux fois**, une au neutre et une
décalée, et `bg0c` est décalé lui aussi.

| | plan lointain | plan proche |
|---|---|---|
| coefficient | **0,75** | **1,0** |
| position au neutre | 704 | 704 |
| position décalée (`bg0f`, `bg0c`) | **712** | **714** |
| déplacement | **+8** | **+10** |

Le plan proche bouge de 10, le lointain de 8. Un coefficient de 0,75 prédit 7,5, arrondi
à 8 — les positions sont entières. **Deux décors indépendants, le même résultat.**

Le champ `+16` / `+20` de la fiche d'objet est donc bien le **coefficient de parallaxe**.
Ce n'est plus une hypothèse. La résolution reste grossière — 10 px de course ne séparent
pas 0,75 de 0,8 — mais elle sépare sans peine 0,75 de 0,5 ou de 1,0, et c'est la nature du
champ qui était en question.

### `bg02` : l'ancrage à 832 ne décale pas la découpe (28/08/2026)

`bg02` est le seul des seize dont le plan proche est ancré en `x = 832` — donc posé à
`192` — quand les quinze autres sont à `320` / `704`. Il fallait savoir si sa bande jouée
était décalée d'un demi-plan.

Mesure, sans lancer le jeu : on corrèle le **profil de colonnes** de notre découpe avec
celui de la planche de référence de 2nd Impact (`galerie/upscaled-sfiii-2i-ryu-1080.png`),
en cherchant la largeur et le décalage qui alignent le mieux.

| ce qu'on corrèle | corrélation | alignement trouvé |
|---|---|---|
| **notre découpe** | **0,865** | **x 124..896** |
| la même, décalée de 512 (témoin) | 0,588 | x 624..1220 |
| la même, retournée (témoin) | 0,596 | — |
| la moitié haute du plan (témoin) | 0,000 | — |

**La découpe est juste.** Les trois témoins sont loin derrière : la méthode discrimine, et
elle choisit notre découpe sans hésiter.

Et elle donne un second résultat qu'on n'était pas allé chercher : la planche de référence
couvre le plan de **124 à 896**, quand l'art mesuré s'étend de **128 à 896**. Quatre pixels
d'écart, sur une image agrandie. C'est **la confirmation indépendante de
`limit_tbl3[22] = { 0x140, 0x2C0 }`**, qui donne exactement 128..896 — deux mesures qui
n'ont rien en commun et qui tombent au même endroit.

L'ancrage à 832 est donc une propriété du placement **à l'écran** chez 2nd Impact, où la
position d'objet et l'offset de plan se compensent. Il ne dit rien de la disposition dans
l'atlas, et la règle de découpe vaut pour les seize décors sans exception.

## Quinze étages ajoutés (28/08/2026)

Passer d'un étage ajouté à quinze, ce n'est pas quinze fois le même travail : c'est un
seul travail, celui des **tables parallèles**. Le jeu en a **vingt-six** indexées par
`bg_w.stage` ou `bg_w.bg_index`, dans **neuf fichiers** — et en oublier une suffit à faire
lire n'importe quoi.

Elles ont été relevées par leurs **consommateurs** :

    grep -rn "\[bg_w\.stage\]\|\[bg_w\.bg_index\]" --include=*.c src/

et non par leur taille, parce que le jeu a **23 personnages et 23 étages** : `ag_sel_table`
et `char_init_data` font toutes deux `[23]` et n'ont rien à voir. C'est le piège de ce
projet, et la seule façon de ne pas y tomber est de suivre l'index, pas la dimension.

| fichier | tables |
|---|---|
| `stage/bg_data.c` | `use_scr`, `use_real_scr`, `use_family`, `rewrite_scr`, `stage_bgw_number`, `msp`, `bgtex_stage_gbix`, `stage_priority`, `stage_opaque`, `bgrw_on`, `ake_bg_off`, `limit_tbl3`, `bg_index_tbl`, `bg_map_tbl` |
| `stage/tate00.c` | `ta_move_tbl` |
| `rendering/texcash.c` | `mts_OB_page` |
| `effect/eff05.c` | `scr_obj_num`, `scr_obj_data`, `char_add` |
| `effect/eff06.c` | `scr_obj_num6`, `scr_obj_data6` |
| `effect/effc9.c` | `ag_sel_table` |
| `effect/eff64.c` | `Background_Buff` |
| `animation/appear.c` | `smoke_check` |
| `animation/win_pl.c` | `win_2000_tbl` |
| `sound/se.c` | `BGM_Stage_Data` |

Plus les noms (`eff99.c`, `Letter_Data_99[5][23]` → `[5][37]`), les blocs de chargement
(`gd3rd_data.c`, `spans[]`), et la borne du sélecteur versus (`sel_pl.c`, `VS_STAGE_MAX`).

**Un défaut trouvé au passage :** `Background_Buff` est indexé par `bg_w.stage` et ne
faisait que **20** entrées. L'étage 22 le débordait déjà, silencieusement, depuis la
session précédente.

`outils/ajouter_etages.py` fait tout ça et se relit : chaque table est vérifiée après
coup, taille déclarée **et** nombre d'éléments. Vingt-cinq sur vingt-cinq conformes.

Chaque étage ajouté est une **copie de l'étage 22** — même script `BG220`, deux plans,
masque plein. Ne changent que trois choses : le nom affiché, `bg_index_tbl` (chacun son
fond) et `limit_tbl3`, calculé par `bande3sx.py` sur l'étendue de l'art.

| étage | décor | | étage | décor | | étage | décor |
|---|---|---|---|---|---|---|---|
| 22 | `bg00` gill | | 27 | `bg05` necro | | 32 | `bg0b` yang |
| 23 | `bg01` alex | | 28 | `bg06` hugo | | 33 | `bg0c` ken |
| 24 | `bg02` ryu | | 29 | `bg07` ibuki | | 34 | `bg0d` sean |
| 25 | `bg03` yun | | 30 | `bg09` elena | | 35 | `bg0e` urien |
| 26 | `bg04` dudley | | 31 | `bg0a` oro | | 36 | `bg0f` la gorge |

`bg08` est écarté : sa bande jouée n'est pas à l'endroit habituel — ses deux bandes sont à
`0..416` et `496..832` quand tous les autres finissent au bas du plan. Elena reste
représentée par `bg09`.

Les pages sont dans `etages2i/stage22` à `stage36`, 64 par étage, 64 Mo en tout. Le
lanceur `Les 15 etages de 2nd Impact` les pose. `TexRemix_ReservedBytes()` a été élargi
aux étages 22 à 37.

### Le plan lointain ne vient pas toujours de la même banque

Vu à l'écran sur `bg09` : de grands trous et une bande bleue à l'extrême droite. La mesure
le confirme — 20,6 % de noir dans la zone jouée, et la colonne 6 vide **sur les deux
plans**.

La cause : la règle « la banque 0 se coupe à `y = 512`, le haut est le plan lointain » ne
vaut que pour les décors dont la banque 0 porte **deux bandes**. Quand elle n'en porte
qu'une, continue sur les 1024 px, la couper en deux revient à scinder une seule image — et
c'est la **banque 1** qui porte le plan lointain.

Ça se mesure, décor par décor : on garde la banque qui laisse le moins de noir, et on
regarde l'image avant de trancher.

| décor | plan lointain en banque 0 | en banque 1 | retenu |
|---|---|---|---|
| `bg07` ibuki | 20,5 % | **9,6 %** | banque 1 |
| `bg09` elena | 20,6 % | **2,9 %** | banque 1 |
| `bg0a` oro | 22,7 % | **19,3 %** | banque 1 |
| `bg0f` la gorge | 42,0 % | **21,0 %** | banque 1 |
| les onze autres | le meilleur | — | banque 0 |

`bande3sx.py` prend maintenant la banque par plan : `132:0xFFFFFFFF:haut:1`.

**Un défaut de l'outil corrigé au passage.** `banque_rgba` avait un repli : « si le bit 15
n'est armé nulle part, la banque est opaque ». Sur une banque **entièrement vide** —
celle de `bg0b` — il la rendait noire opaque, et faisait croire qu'elle portait un plan.
La règle est maintenant celle qui a été mesurée : **transparent si et seulement si le pixel
vaut `0x0000`**, sans repli.

### Ce qui reste noir, une fois la caméra prise en compte

Le pourcentage sur le plan entier n'est pas ce qu'on voit : la caméra ne sort pas de
`limit_tbl3`. Recompté dans la plage réellement visible :

| noir vu | décors |
|---|---|
| 0 % | `bg02` ryu, `bg03` yun, `bg0b` yang |
| 1 à 5 % | `bg01` alex, `bg0a` oro, `bg0e` urien, `bg09` elena, `bg0c` ken, `bg0f` gorge, `bg00` gill |
| 7 à 10 % | `bg05` necro, `bg0d` sean, `bg06` hugo, `bg07` ibuki |
| **16 %** | **`bg04` dudley** — le seul qui reste à regarder |

`bg04` a l'art le plus large (x 0..1024, donc la caméra voit tout le plan) et ses trous
sont au milieu, pas aux bords. La banque 1 ne l'améliore pas (28,8 %). C'est probablement
un décalage vertical, comme `bg08`.

### Les bandes verticales, vérifiées sur les quinze

Alex et Dudley les montraient encore. La cause était dans mon calcul des limites, pas dans
le jeu : `bande3sx.py` **arrondissait les bords de l'art aux pages de 128**. Sur `bg01`
alex, le plan proche est à **0 %** en `x 0..63` et `960..1023` ; l'arrondi ramenait ces
bords à `0` et `1024`, et la caméra allait donc chercher deux colonnes vides.

La règle est maintenant celle qui décrit le défaut : **la plus grande plage continue,
autour du centre `0x200`, où le plan proche n'a pas une seule colonne vide.** Sans arrondi.

    plein = (plan proche de la zone jouee).mean(0) > 0
    x0 = la premiere colonne vide a gauche de 512, x1 la premiere a droite
    l = x0 + 192,  r = x1 - 192          (la fenetre fait 384 px, centree)

Contrôle sur les quinze, colonne par colonne, dans la plage réellement visible :

| étage | décor | plage vue | colonnes vides | couverture mini | noir |
|---|---|---|---|---|---|
| 22 | `bg00` gill | 128..896 | **0** | 44 % | 3,6 % |
| 23 | `bg01` alex | 64..960 | **0** | 44 % | 0,0 % |
| 24 | `bg02` ryu | 0..1024 | **0** | 25 % | 0,0 % |
| 25 | `bg03` yun | 128..896 | **0** | 51 % | 0,0 % |
| 26 | `bg04` dudley | 80..944 | **0** | 51 % | 0,0 % |
| 27 | `bg05` necro | 127..940 | **0** | 0,4 % | 7,5 % |
| 28 | `bg06` hugo | 0..1024 | **0** | 20 % | 8,3 % |
| 29 | `bg07` ibuki | 96..928 | **0** | 42 % | 3,9 % |
| 30 | `bg09` elena | 0..768 | **0** | 17 % | 2,3 % |
| 31 | `bg0a` oro | 0..1024 | **0** | 25 % | **19,3 %** |
| 32 | `bg0b` yang | 128..896 | **0** | 99 % | 0,0 % |
| 33 | `bg0c` ken | 31..992 | **0** | 0,4 % | 0,6 % |
| 34 | `bg0d` sean | 128..896 | **0** | 63 % | 7,4 % |
| 35 | `bg0e` urien | 128..896 | **0** | 27 % | 0,8 % |
| 36 | `bg0f` la gorge | 128..896 | **0** | 24 % | 6,1 % |

**Aucune colonne vide sur aucun des quinze.** Plus de bande possible, par construction.

Deux décors gardent une colonne à peine couverte — `bg05` et `bg0c`, 0,4 % — c'est une
colonne d'un pixel, pas une bande. Et `bg0a` oro garde **19,3 %** de noir dans la zone
vue : ses trous sont au milieu, pas aux bords. C'est le seul qui reste à regarder, avec
`bg04` dudley dont le noir est désormais tombé à zéro.

### Et un art continu peut quand même déborder

Hugo montrait encore un problème aux deux bouts — mais pas une bande du plan lointain :
**les voiles de son navire**, en gros plan, sur toute la hauteur. Son art est continu de
`x 0` à `x 1024`, donc aucune colonne vide, et pourtant la caméra sort du décor.

Ce qui touche le bord du plan n'y est pas par hasard : c'est du remplissage que le jeu
d'origine ne montre pas. Trois faits le disent :

- **treize décors sur quinze** s'arrêtent d'eux-mêmes entre `x 128` et `x 896` ;
- la planche de référence de 2nd Impact donne **124..896** sur `bg02` ;
- et `bg02`, dont l'art court de 0 à 1024, rabattu à `128..896`, retombe **exactement** sur
  les limites `{ 0x140, 0x2C0 }` vérifiées côte à côte avec la Dreamcast.

Règle ajoutée : **si l'art atteint `0` ou `1024`, on le rabat à `128` ou `896`.** Quatre
décors sont concernés — `bg02`, `bg06`, `bg09`, `bg0a` — et les onze autres gardent leur
étendue mesurée, y compris `bg01` alex (64..960) et `bg0c` ken (31..992), qui ne touchent
pas le bord et n'ont rien montré.

### Ce qui reste sur Ken et Yun n'est pas la découpe

Deux décors gardent une anomalie une fois les bandes réglées. Mesurées, elles disent la
même chose.

**Ken**, 4,8 % de noir dans la zone jouée : les trous sont aux colonnes extrêmes du plan —
hors caméra — plus une tache autour de `x 192..223`, `y 320..384`, celle qu'on voit près du
vélo et du banc. Sa banque 1 est vide, il n'y a donc pas d'autre plan pour la couvrir.

**Yun** : un rectangle de contenu clair, en bas à gauche, qui ne s'accorde pas avec le sol
autour. Il est dans le **plan proche lui-même**, pas dans un trou — le plan proche y
couvre 73 %, et l'endroit n'est pas transparent.

Est-ce notre découpe ? Non, et ça se mesure. Les ruptures les plus fortes de l'image, dans
cette bande, tombent aux colonnes **195 et 303** et aux lignes **399 à 419**. Aucune n'est
un multiple de 128. **Le rectangle n'est pas aligné sur une page** : il est rangé comme ça
dans l'atlas, ce n'est pas une page qu'on aurait mal posée.

C'est donc la même chose des deux côtés : le `.pvc` porte des morceaux de décor **là où ils
sont rangés**, pas là où le jeu les dessine. Le jeu les pose en objets, aux positions que
donne la table de RAM déjà décodée — `{u16 tuile, u16 ?, u16 x, u16 y, u16 taille,
u16 drapeaux, u16 palette}`. Cuire l'atlas tel quel les laisse à leur place de stockage.

C'est exactement le chantier des **sprites de décor**, et ces deux anomalies en sont la
première manifestation visible.
