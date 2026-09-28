# Les quatre jeux de données, avant de continuer

Demandés le 29/08/2026 : **le plan (2 sur 8), l'envoi de palette, la cadence des trois
décors dégénérés, puis les retournements et l'échelle.**

Tout ce qui suit est **lu** — dans le code SH-4 de `SF3_2ND.BIN` (base `0x8C010000`) ou
dans la RAM des dix-huit états Flycast. Rien n'y est déduit d'une image, et rien n'y a
demandé de lancer un jeu.

Le programme est `outils/donnees.py`, lanceur `donnees.cmd`, sortie complète dans
`DONNEES.txt`. Il se relit : chaque chiffre du présent document sort de lui.

---

## La boucle de dessin, désassemblée

`0x8C0F693C`, corps à `0x8C0F6A08`. `r5` = l'élément (16 octets), `r8` = le morceau
(16 octets), `r10 = r8 + 10`.

    plan    = (element[+0] >> 12) & 7                        0x8C0F6994
    nb      =  element[+0] & 0x0FFF      nombre de morceaux
    debut   =  element[+2] & 0x7FFF      premier morceau
    defil   =  0x8C7EFCCC + plan*4       {u16 x, u16 y}      0x8C0F69A2, 0x8C0F69B2

    largeur  = (morceau[+8]       & 127) + 1     en PIXELS   0x8C0F6A12, 0x8C0F6A24
    hauteur  = ((morceau[+8] >> 8) & 127) + 1    en PIXELS   0x8C0F6A14, 0x8C0F6A26
    tuiles_x = 1 << ((morceau[+10]       & 3) - 1)           0x8C0F6B04
    tuiles_y = 1 << (((morceau[+10] >> 2) & 3) - 1)          0x8C0F6B20

    x = (defil_x + element[+4] + morceau[+4] - largeur/2 si morceau[+10] & 0x0100) & 0x3FF
    y = (109 - defil_y - element[+6] - morceau[+6] - hauteur
             + hauteur/2 si morceau[+10] & 0x0200) & 0x3FF   0x8C0F6A90 .. 0x8C0F6AB8

Un morceau dont l'un des deux quartets bas de `+10` est nul **n'est pas dessiné**
(`0x8C0F6A88`).

**Trois corrections à `etat2.py`**, que le code impose :

| champ | ce que `etat2.py` dit | ce que le code fait |
|---|---|---|
| `l` / `h` | `l` = champ haut | **largeur = champ bas**, hauteur = champ haut |
| `centre_x` | bit `0x0200` | bit **`0x0100`** |
| `centre_y` | bit `0x0100` | bit **`0x0200`** |

Et une confirmation utile : **`element[+0] & 0x0FFF` est le nombre de morceaux**. Vérifié
sur les dix-huit états — l'élément 5 de `bg01` porte `0x2004`, soit plan 2 et quatre
morceaux, et ces quatre morceaux sont exactement le sprite 3 de `2i-b01-F_ETC34`
(tuiles 92, 88, 90, 53 ; champ 541 ; tailles 32×32, 16×32, 32×16, 16×16). **C'est la
ventilation, prise sur son image du milieu.**

---

## 1. LE PLAN

### Ce que le décor d'origine emploie

**Cinq plans, pas deux.** Les seize décors emploient les plans **0, 1, 2, 3 et 4** ;
`bg00` emploie en plus le plan 7. Jamais les plans 5 et 6.

| décor | p0 | p1 | p2 | p3 | p4 | autre |
|---|---|---|---|---|---|---|
| `bg00` gill | 1 | 1 | 19 | 17 | 1 | p7 : 1 |
| `bg01` alex | 5 | 1 | 11 | 21 | 1 | |
| `bg02` ryu | 1 | 1 | 22 | 14 | 1 | |
| `bg03` yun | 1 | 3 | 28 | 10 | 1 | |
| `bg04` dudley | 1 | 1 | 17 | 18 | 1 | |
| `bg05` necro | 1 | 1 | 29 | 10 | 1 | |
| `bg06` hugo | 1 | 1 | 22 | 14 | 1 | |
| `bg07` ibuki | 7 | 1 | 10 | 19 | 1 | |
| `bg08`+`bg09` elena | 7 | 1 | 15 | 1 | 1 | |
| `bg0a` oro | 1 | 3 | 20 | 8 | 1 | |
| `bg0b` yang | 1 | 1 | 22 | 15 | 1 | |
| `bg0c` ken | 3 | 1 | 15 | 22 | 1 | |
| `bg0d` sean | 1 | 1 | 17 | 19 | 1 | |
| `bg0e` urien | 7 | 1 | 10 | 19 | 1 | |
| `bg0f` la gorge | 8 | 1 | 10 | 18 | 1 | |

(nombre d'éléments de la liste d'affichage portés par chaque plan)

Les plans **1 et 4** ne portent qu'un élément chacun, et cet élément est un **fond de
plan** : son octet `+9` vaut `0x00`, sa palette vient du morceau et compte **256
couleurs**, aux emplacements 512 ou 1023. Le gros du décor est sur les plans **2 et 3**.

### Le lien plan → objet de fond — c'est mesuré, et c'est simple

C'était « la mesure qui manque » de `RELAIS.md`. La voici :

> **`defil[plan k] == (−objet[k−1].x) & 0x3FF`**, pour `k ≥ 1`. Le plan 0 ne défile jamais.

**Trente-cinq accords sur trente-six**, sur les seize décors. Le seul désaccord est
`bg05` plan 3 : 871 contre 876 attendus — cinq unités, parce que `objet.x` est lu en
`s16` à `+10` alors que le défilement sort de la position 16.16 complète. Ce n'est pas un
contre-exemple, c'est une troncature.

Deux états pris **caméra en mouvement** le prouvent sans ambiguïté, parce que les deux
objets y ont un `x` différent :

| état | plan 1 | plan 2 |
|---|---|---|
| `bg0f` (état 6) | défil 712 = objet 0, coef **0,75** | défil 714 = objet 1, coef **1,00** |
| `bg0c` (état 7) | défil 712 = objet 0, coef **0,75** | défil 714 = objet 1, coef **1,00** |
| `bg02` (état 0) | défil 704 = objet 0, coef **0,75** | défil 192 = objet 1, coef **1,00** |

Caméra centrée, les deux objets sont en `x = 320` et donnent le même défilement : la règle
se vérifie mais ne sépare plus. C'est pour ça qu'il fallait un état en mouvement.

### Les coefficients de parallaxe, décor par décor

| décor | objet 0 (→ plan 1) | objet 1 (→ plan 2) | objet 2 (→ plan 3) |
|---|---|---|---|
| `bg00` gill | 0,2500 / 0,6250 | 1,0000 / 1,0000 | — |
| `bg01` alex | **0,6250 / 0,7500** | 1,0000 / 1,0000 | — |
| `bg02` ryu | 0,7500 / 0,9375 | 1,0000 / 1,0000 | — |
| `bg03` yun | 0,8750 / 1,0625 | 1,0000 / 1,0000 | 0,0000 / 0,0000 |
| `bg04` dudley | 0,7500 / 0,8750 | 1,0000 / 1,0000 | — |
| `bg05` necro | 1,0000 / 1,0000 | 1,0000 / 1,0000 | 1,0000 / 1,0000 |
| `bg06` hugo | 0,7500 / 0,8750 | 1,0000 / 1,0000 | — |
| `bg07` ibuki | 0,6250 / 1,0000 | 1,0000 / 1,0000 | 0,2500 / 0,6250 |
| `bg08`+`bg09` | 0,5000 / 0,5000 | 1,0000 / 1,0000 | — |
| `bg0a` oro | 0,7500 / 0,8750 | 1,0000 / 1,0000 | 0,5000 / 0,9375 |
| `bg0b` yang | 0,8750 / 1,0625 | 1,0000 / 1,0000 | — |
| `bg0c` ken | 0,7500 / 0,7500 | 1,0000 / 1,0000 | — |
| `bg0d` sean | 0,9375 / 1,0000 | 1,0000 / 1,0000 | — |
| `bg0e` urien | 0,3750 / 0,7500 | 1,0000 / 1,0000 | — |
| `bg0f` la gorge | 0,7500 / 0,8750 | 1,0000 / 1,0000 | — |

### Ce que ça donne dans 3SX — un défaut et une différence, lus dans `bg220.c`

`BG220` monte ses deux plans ainsi :

    bgw_ptr = &bg_w.bgw[1];  bg2202();   ->  bg_base_move_common   le plan de BASE
    bgw_ptr = &bg_w.bgw[0];  bg2201();   ->  bg_move_common        le plan a COEFFICIENT

`bg_base_x_move_check` établit le déplacement de référence (`bg_w.bg2_sp_x2`) ;
`bg_x_move_check` le multiplie par `bgw_ptr->speed_x`. Et `Bg_Family_Set` fait
`Family_Set_W(i + 1, …)` pour `bg_w.bgw[i]`. Donc :

| famille | plan de 3SX | rôle dans `BG220` |
|---|---|---|
| `my_family = 1` | `bgw[0]` | plan à coefficient — et `speed_x` y vaut **0**, donc **fixe** |
| `my_family = 2` | `bgw[1]` | plan de base — **suit la caméra**, coefficient 1,00 |

Et ce que `bg_x_move_check` fait de `speed_x` :

    bgw[0].xy[0].cal      = speed_x * bg_w.bg2_sp_x2      le deplacement, en 16.16
    bgw[0].xy[0].disp.pos += pos_x_work                   plus l'origine, 0x200

`speed_x` **est** le coefficient de parallaxe, en 16.16. `bg_initialize` le met à zéro pour
les sept plans, et `bg2201_init00` ne le repose pas : **`bgw[0]` de nos étages est donc
fixe**, `bgw[1]` suit la caméra à 1,00.

**Le défaut, un seul, et il est net.** La ventilation est sur le plan 2 de 2nd Impact, donc
sur l'objet 1, coefficient **1,00** : le plan qui suit la caméra. `stg2200_data_tbl`
(`eff05.c`) lui donne `my_family = 1`, c'est-à-dire **`bgw[0]`, le plan fixe**. Telle
quelle, la ventilation reste collée à l'écran pendant que le toit défile dessous. Ce
devrait être **`my_family = 2`**.

**Ce qui n'est PAS un défaut, et que j'avais annoncé à tort comme tel.** `bg2201_init00`
ne pose ni `speed_x` ni `speed_y` — mais `bg0501_init00`, `bg0201_init00` et leurs pareils
des étages d'origine ne les posent pas davantage. `bgw[0]` **est** le plan fixe par
conception ; la parallaxe des étages d'origine vit sur `bgw[2]`, un troisième plan piloté à
part par `sync_fam_set3` (c'est là que se trouvent les `0xE000` de `bg020` et `bg050`).
`BG220` reproduit donc fidèlement le motif à deux plans de 3rd Strike.

**Ce qui reste vrai, et c'est une différence, pas un bogue.** Nos deux plans donnent les
coefficients **0,00 et 1,00**. Les décors de 2nd Impact en veulent **0,25 à 0,94 et 1,00**.
Poser `speed_x` / `speed_y` dans `bg2201_init00` est le levier — le calcul ci-dessus montre
qu'il suffit — et les quinze couples mesurés sont ceux-ci, en 16.16 :

| décor | étage 3SX | `speed_x` | `speed_y` |
|---|---|---|---|
| `bg00` gill | 22 | `0x4000` | `0xA000` |
| `bg01` alex | 23 | `0xA000` | `0xC000` |
| `bg02` ryu | 24 | `0xC000` | `0xF000` |
| `bg03` yun | 25 | `0xE000` | `0x11000` |
| `bg04` dudley | 26 | `0xC000` | `0xE000` |
| `bg05` necro | 27 | `0x10000` | `0x10000` |
| `bg06` hugo | 28 | `0xC000` | `0xE000` |
| `bg07` ibuki | 29 | `0xA000` | `0x10000` |
| `bg09` elena | 30 | `0x8000` | `0x8000` |
| `bg0a` oro | 31 | `0xC000` | `0xE000` |
| `bg0b` yang | 32 | `0xE000` | `0x11000` |
| `bg0c` ken | 33 | `0xC000` | `0xC000` |
| `bg0d` sean | 34 | `0xF000` | `0x10000` |
| `bg0e` urien | 35 | `0x6000` | `0xC000` |
| `bg0f` la gorge | 36 | `0xC000` | `0xE000` |

Rien de tout cela n'est appliqué : c'est à arbitrer. Et poser ces vitesses **suppose** que
`bgw[0]` porte bien la moitié lointaine de l'art — ce qui est l'intention de la découpe,
mais n'a pas été vérifié dans le code de dessin.

---

## 2. LA PALETTE

### La règle, exacte

Lue en `0x8C0F6A42` .. `0x8C0F6A84`. Elle tient en quatre lignes :

    si element[+9] & 0x20 :  brut = element[+8]        (un seul pour tous les morceaux)
    sinon                 :  brut = morceau[+2]        (un par morceau)

    si element[+9] & 0x40 :  sel = element[+9] & 6
    sinon                 :  sel = morceau[+2] & 0x0600

    sel != 0 : emplacement = brut & 0x1FF           -> 64 couleurs, 128 octets
    sel == 0 : emplacement = (brut & 0x1FF) | 0x200 -> 256 couleurs, 512 octets

    adresse des couleurs : 0x8C7AFCCC + emplacement * 128        (64 couleurs)

`0x8C7AFCCC` est exactement la fin du tableau des morceaux : `0x8C72FCCC + 32768 × 16`.

Le **bit 6** manquait à `RELAIS.md`, qui donnait `(octet & 6) != 0` comme règle unique.
C'est vrai pour les octets `0x42`, `0x62`, `0x64`, `0x72` — mais pas pour `0x00`, où c'est
le champ `+2` du morceau, masqué à `0x0600`, qui décide. Et les éléments à `0x00` sont
précisément les **fonds de plan**, ceux qui prennent 256 couleurs.

### Ce qu'il faut charger, décor par décor

Emplacements distincts, tels que le jeu les lit :

| décor | nb | emplacements |
|---|---|---|
| `bg00` gill | 13 | 0, 8, 16, 59, 76, 87, 104, 108, 109, 111, 128, 512, 1023 |
| `bg01` alex | 9 | 0, 8, 16, 79, 89, **93**, 128, 512, 1023 |
| `bg02` ryu | 16 | 0, 1, 3, 8, 16, 79, 88, 89, 92, 93, 94, 95, 96, 128, 512, 1023 |
| `bg03` yun | 19 | 0, 1, 8, 16, 76, 77, 79, 80…86, 89, 91, 128, 512, 1023 |
| `bg04` dudley | 14 | 0, 8, 16, 79, 84, 90…95, 128, 512, 1023 |
| `bg05` necro | 22 | 0, 4, 7, 8, 16, 71, 72, 73, 76, 81, 82, 83, 86, 87, 89…93, 128, 512, 1023 |
| `bg06` hugo | 21 | 0, 5, 8, 16, 26, 59, 75, 79, 86, 87, 89, 90, 102, 104, 105, 107, 108, 109, 128, 512, 1023 |
| `bg07` ibuki | 8 | 0, 8, 16, 59, 79, 128, 512, 1023 |
| `bg08`+`bg09` | 11 | 0, 7, 8, 16, 65, 72, 76, 78, 87, 512, 1023 |
| `bg0a` oro | 14 | 0, 1, 7, 8, 16, 79, 80, 81, 88, 89, 91, 128, 512, 1023 |
| `bg0b` yang | 18 | 0, 1, 8, 16, 69…75, 78, 79, 80, 81, 128, 512, 1023 |
| `bg0c` ken | 9 | 0, 8, 16, 59, 79, 80, 128, 512, 1023 |
| `bg0d` sean | 16 | 0, 8, 16, 31, 59, 68, 76, 79, 82, 86, 94, 95, 96, 128, 512, 1023 |
| `bg0e` urien | 9 | 0, 8, 16, 59, 69, 79, 128, 512, 1023 |
| `bg0f` la gorge | 8 | 0, 8, 16, 59, 79, 128, 512, 1023 |

Les emplacements **0, 8, 16, 79, 128** reviennent chez tout le monde : ce sont les
combattants et l'affichage, pas le décor. Les emplacements du décor sont ceux de la plage
**59 à 128**, plus **512 et 1023** pour les deux fonds de plan.

**La ventilation d'Alex est à l'emplacement 93**, en 64 couleurs, adresse
`0x8C7AFCCC + 93 × 128 = 0x8C7B2CCC`. C'est ce que `objets.py` exporte déjà — sa règle
(« le mot `+8` de l'élément, masqué à `0x1FF` ») est la bonne pour cet élément-là.

### Côté 3SX, ce qui reste à faire de ces données

Rien de neuf sur l'envoi : le chemin est celui trouvé la nuit dernière — écrire dans
`ColorRAM[emplacement]` **en échangeant rouge et bleu** (`ColorRAM` est en ABGR1555), puis
`palUpdateGhostCP3(emplacement, 1)`. Ce que ces données ajoutent, c'est **combien** de
palettes il faut par étage : entre 8 et 22, dont deux de 256 couleurs pour les fonds. Un
étage ajouté qui n'emprunte qu'un seul emplacement (300) ne peut donc pas porter plus d'un
objet coloré.

---

## 3. LA CADENCE — et deux hypothèses écartées

### Épreuve A : la durée n'est pas dans l'enregistrement

Les trois champs que `fetc.py` note `?` sont nuls sur **19 872 champs** — les
6 624 enregistrements des seize assets, trois champs chacun, **zéro non nul**. La durée
d'une image n'est pas dans le fichier d'animation, sous aucune forme.

### Épreuve B : l'espace d'index est global, et se résout exactement

L'en-tête d'un `F_ETCnn` porte `(début, fin)` d'un **espace d'index global** partagé par
tous les assets. La résolution se lit dans le code :

    index >> 2  ->  octet en 0x8C60A6D4  ->  fiche de 24 octets en 0x8C602384

**Seize assets sur seize** : tout le span d'un asset tombe sur le même numéro de fiche, et
la clé lue en `fiche+20` est exactement celle du tableau de `RELAIS.md` (`0x0133` pour
`b01` alex, `0x0129` pour `b0c` ken, `0x0158` pour `b0e` urien). Le décompresseur est
`0x8C0F6548` pour tous.

| asset | span global | fiche | clé |
|---|---|---|---|
| `2i-b0c-F_ETC24` ken | 31168..31648 | 41 | `0x0129` |
| `2i-b02-F_ETC25` ryu | 31648..32064 | 42 | `0x012A` |
| `2i-b03-F_ETC26` yun | 32064..32704 | 43 | `0x012B` |
| `2i-b0b-F_ETC27` yang | 32704..33792 | 44 | `0x012C` |
| `2i-b05-F_ETC28` necro | 33792..34272 | 45 | `0x012D` |
| `2i-b06-F_ETC29` hugo | 34272..34656 | 46 | `0x012E` |
| `2i-b08-F_ETC30` | 34656..34992 | 47 | `0x012F` |
| `2i-b08-F_ETC31` | 34992..35536 | 48 | `0x0130` |
| `2i-b04-F_ETC32` dudley | 35536..35776 | 49 | `0x0131` |
| `2i-b0a-F_ETC33` oro | 35776..36384 | 50 | `0x0132` |
| **`2i-b01-F_ETC34` alex** | **36384..36960** | **51** | **`0x0133`** |
| `2i-b0d-F_ETC35` sean | 36960..37168 | 52 | `0x0134` |
| `2i-b00-F_ETC41` gill | 39824..39952 | 58 | `0x013A` |
| `2i-b0e-F_ETC94` urien | 45400..45448 | 88 | `0x0158` |
| `2i-b10-F_ETC100` | 45752..45816 | 94 | `0x015E` |

### Épreuve C : ce que les trois « dégénérés » contiennent vraiment

Le mot « dégénéré » cachait autre chose. Ces trois assets ne sont pas cassés : ils ont
**très peu de sprites**, et le flux est **complété jusqu'à un multiple de 16** en répétant
le dernier enregistrement.

`2i-b01-F_ETC34`, alex :

| ancre | sprite | répétitions |
|---|---|---|
| (−112, −96) | 0 | 1 |
| (0, −112) | 1 | 1 |
| **(−48, −48)** | **2** | **1** |
| **(−48, −48)** | **3** | **1** |
| **(−48, −48)** | **4** | **1** |
| (−54, −109) | 5 | **571** ← remplissage |

`b0c` ken : 6 sprites, remplissage de 475. `b0e` urien : 3 sprites, remplissage de 46.
Les trois totaux — 576, 480, 48 — sont des multiples de 16, comme les treize autres.

**Donc les trois images de la ventilation sont les sprites 2, 3 et 4, ancrés au même
point, une entrée chacun.** Le fichier ne porte aucune tenue pour elles.

### Épreuve D : la cadence n'est PAS dans le script d'étage

`RELAIS.md` supposait qu'elle s'y trouvait. Elle n'y est pas, et c'est mesuré : j'ai relevé
**toutes** les constantes chargées par le script de `bg01` (`0x8C0E9014`..`0x8C0E9498`,
33 constantes) et par les trois fonctions qu'il appelle à chaque trame
(`0x8C0E8D9A`, `0x8C0E8CF4`, `0x8C0E8BFE`).

**Aucune des quatre cibles n'y figure** : ni la liste d'affichage (`0x8C602348`), ni le
tableau des morceaux (`0x8C72FCCC`), ni la table d'installation des assets
(`0x8C602384`), ni la résolution index → asset (`0x8C60A6D4`).

Le script d'étage touche l'état du jeu (`0x8C6AF304`), l'objet de fond 0 (`0x8C6AF358`) et
la configuration des plans (`0x8C84142C`). Il pilote la **parallaxe** et les **phases
d'ambiance** — sa table à `0x8C1D93A4` donne huit phases de 1140, 240, 240, 240, 240, 480,
480 et 600 trames, soit 3 660 trames, une minute et une seconde. Ce n'est pas une
ventilation.

### Épreuve E : la cadence est dans une table de scripts, et la voici

Elle n'était ni dans le fichier ni dans le script d'étage. Elle est **en clair dans le
binaire**, dans une table de scripts d'animation, atteinte en trois étages :

    0x8C5F9B38 + n*4     table maitresse, un pointeur par aire d'etage
    table -> [pointeurs] un par script, jusqu'a un mot qui n'est pas une adresse
    script -> enregistrements de HUIT octets :

        octet 0 : la commande
        octet 1 : la DUREE en trames, pour la commande 0x00
        u16 +2  : nul
        u16 +4  : nul
        u16 +6  : l'index global -- celui de l'espace partage des F_ETCnn

Les commandes relevées : `0x00` afficher, `0x01` fin, `0x0C` début de boucle (le nombre de
tours est dans `index`), `0x0D` fin de boucle. `0x02` et `0xFF` sont vus, rôle non établi.

**La cadence de la ventilation d'Alex**, table `0x8C1226B8` :

| script | contenu | ancre |
|---|---|---|
| `0x8C1226D4` | sprite 0 — **11 trames** | (−112, −96) |
| `0x8C1226EC` | sprite 1 — **6 trames** | (0, −112) |
| **`0x8C122704`** | **sprites 2, 3, 4 — 4 trames chacun** | **(−48, −48)** |
| `0x8C12272C` | sprites 2, 3, 4 — 1 trame chacun | (−48, −48) |

Les sprites 2, 3 et 4 partagent l'ancre **(−48, −48)** — celle que `RELAIS.md` avait déjà
identifiée comme celle de la ventilation. **Un tour fait donc douze trames**, et le jeu
garde une variante rapide à trois trames. Ce qui choisit entre les deux n'est pas établi.

### Ce qui confirme le modèle

- **3 360 enregistrements d'affichage**, 419 scripts atteints par la table maîtresse,
  3 614 images.
- La distribution des durées est celle d'une table de trames : **94 % valent 16 trames ou
  moins**, avec des pics nets à 4, 6 et 8 ; le maximum est 250.
- **Tout sprite cité par un script est présent dans le flux de son asset** — 100 % sur les
  quinze assets (50/50 pour `bg00`, 116/116 pour `bg02`, 503/503 pour `bg0b`…). L'inverse
  est faux : le flux porte aussi du mobilier que rien n'anime.
- La répétition dans le flux, elle, **ne coïncide pas** avec la durée du script : zéro
  couple commun sur 222 pour `b02`, huit sur 629 pour `b0b`.

**Donc l'ancien modèle de `cadences.py` — « la répétition porte la durée » — est faux**, et
c'est ce qui avait fait appeler « dégénérés » trois assets qui ne le sont pas. `cadences.py`
est réécrit sur les scripts.

### Ce qui porte l'animation à l'écran

Mesuré sur les deux états de `bg0f` : entre les deux, **le champ `index` de trois éléments
change** (élément 8 : 12720 → 12752, et son nombre de morceaux passe de 17 à 19). L'élément
désigne un autre bloc de morceaux déjà résolus ; les blocs sont alloués par seizaines dans
un tampon de 32 768 enregistrements, et l'objet 1 du décor porte les curseurs d'allocation
(`+40` = `0x8C761CCC`, l'enregistrement 12 800).

Reste, pour la complétude et sans conséquence pour le portage : la fonction qui fait
avancer le curseur de script trame par trame. Le WORK animé porte son index global en
`+474` (lu en `0x8C0B2D0E`), et `0x8C0B2518(index, &clé)` rend le pointeur d'animations de
la fiche d'asset.

### Une méprise écartée en chemin

`releves2/bg0b-0.json` prétendait venir de `Street Fighter III - Double Impact.state`. Cet
état identifie `bg02`, avec 5 406 morceaux ; le fichier en portait 5 662, exactement ceux
de `bg0b-20.json`. C'était un doublon sous un faux nom, laissé par une exécution ancienne —
et comparé à `bg0b-20.json` il ne montrait aucune différence, ce qui faisait conclure à
tort que rien ne bouge entre deux instants. Il est dans `releves2/perimes/`.

---

## 4. RETOURNEMENTS ET ÉCHELLE

### Les retournements — résolus

`0x8C0F6AC6` : l'octet de retournement est

    element[+9]  XOR  (morceau[+2] >> 8)

exactement comme `wk->cg_flip ^ wk->rl_flag` dans 3SX. Deux bits :

| bit | effet | où |
|---|---|---|
| `0x08` | retournement **vertical** — `y += hauteur` | `0x8C0F6AE6` |
| `0x10` | retournement **horizontal** — `x += largeur` | `0x8C0F6AFA` |

Sur les 3 458 morceaux réellement dessinés des dix-huit états :

| valeur | ce que c'est | nombre |
|---|---|---|
| `0x00` | aucun | 3 006 (86,93 %) |
| `0x10` | horizontal | 452 (13,07 %) |

**Le retournement vertical n'est jamais employé** dans un décor de 2nd Impact.

Les bits `0x0100` et `0x0200` du morceau, que `RELAIS.md` listait comme « retournements
non résolus », ne sont pas des retournements : ce sont les **centrages**, et `etat2.py`
les nomme à l'envers (`0x0100` = x est un centre, `0x0200` = y est un centre).

### L'échelle — résolue, et il n'y a pas de champ d'échelle

Il n'existe **aucun** champ d'échelle. Deux tailles cohabitent :

- la taille **à l'écran**, en pixels : deux champs de 7 bits dans `morceau[+8]` ;
- la taille de la **texture**, en tuiles de 16 px : deux quartets dans `morceau[+10]`,
  valant `1 << (n−1)`, donc 1, 2 ou 4 tuiles.

**L'échelle est le rapport des deux.** Sur les 3 458 morceaux dessinés :

| échelle | nombre | exemple |
|---|---|---|
| ×1,000 | 3 412 (98,67 %) | 16 px pour 16 px |
| ×2,000 | 37 (1,07 %) | 128 px pour 64 px, 64 px pour 32 px |
| ×1,688 | 8 (0,23 %) | 27 px pour 16 px, 54 px pour 32 px |
| ×1,672 | 1 (0,03 %) | 107 px pour 64 px |

Elle est **isotrope** — le même facteur en x et en y, à la troncature près — et elle n'est
pas limitée aux puissances de deux : 27/16 = 1,6875. C'est un zoom continu, employé par
moins de 1,4 % des morceaux.

---

## Ce que ces données changent pour la suite

1. **Le plan.** Le lien plan → objet est établi (`plan k ← objet k−1`). Il en tombe
   **un défaut** : la ventilation est sur `my_family = 1`, qui est le plan **fixe**, alors
   qu'elle appartient au plan qui suit la caméra (`my_family = 2`). Et **une différence**
   qui n'est pas un défaut : nos deux plans donnent les coefficients 0,00 et 1,00 quand les
   décors de 2I en veulent 0,25–0,94 et 1,00. Les quinze couples sont au tableau.
2. **La palette.** La règle est complète, bit 6 compris. Un étage de 2nd Impact demande
   entre 8 et 22 emplacements ; l'emplacement de la ventilation est **93**.
3. **La cadence.** Trouvée : la ventilation tient **4 trames par image**, trois images,
   un tour en douze trames. Elle est dans une table de scripts du binaire, ni dans le
   `F_ETCnn` ni dans le script d'étage. `MAINTIEN_TRAMES` du portage valait déjà 4 — par
   chance, puisque la valeur avait été choisie au juger ; elle est maintenant lue.
4. **Retournements et échelle.** Résolus tous les deux. Le retournement vertical n'est
   jamais employé ; l'échelle est un rapport, isotrope, et concerne 1,3 % des morceaux.

## Corrections portées dans les outils le 29/08/2026

- **`etat2.py`** — `l`/`h` renommés `largeur`/`hauteur` et remis à l'endroit ; les deux
  bits de centrage remis à l'endroit. Vérifié : sur les **95 390** morceaux des dix-huit
  états, la différence est **exactement** la permutation attendue et rien d'autre.
  `releves2/` régénéré, `pools.py` rend toujours **187/187**.
- **`elements.py`** — mêmes deux bits. **Aucun rendu ne change** : sur les 3 458 morceaux
  dessinés, les deux bits sont *toujours égaux* (74,6 % à 1, 25,4 % à 0). C'est pour ça que
  les rendus étaient justes malgré l'erreur de nom — et c'est aussi pourquoi il fallait la
  corriger avant qu'un décor où ils diffèrent ne vienne la révéler.
- **`cadences.py`** — réécrit sur les scripts. L'ancien modèle (« la répétition porte la
  durée ») est réfuté par la mesure.
- **`objets.py`** — le commentaire sur le format de `ColorRAM` corrigé : elle est en ABGR.
- **`releves2/bg0b-0.json`** écarté dans `releves2/perimes/` : doublon sous un faux nom.
- **`RELAIS.md`** donnait la règle de palette sans le bit 6 : voir la section 2.

---

## Corrections du 29/08/2026 — lues dans le binaire

* **`0x8C6AF314` n'est PAS le nombre d'objets de fond.** Il vaut 2 pour `bg00`, dont
  l'objet 2 est pourtant reel : son coefficient **varie decor par decor** (0,875 pour
  bg00, 0,8125 pour bg01, 0 pour bg03), alors que ceux des objets 4 et 6 sont identiques
  dans les vingt et un etats — ces deux-la sont des valeurs par defaut.
* **Les coefficients de parallaxe sont dans le binaire**, table `0x8C1D4F48`, pas `0x20`,
  indexee par le numero de decor : premiere paire = objet 0, deuxieme = objet 1. Seize
  decors sur seize, `bg07`, `bg08` et `bg0f` compris — que les etats ne couvraient pas.
  Le `speed_y` du plan lointain qu'elle donne reproduit au bit pres le tableau de la
  section 1, releve tout autrement.
* **Le coefficient du plan supplementaire** est ecrit en dur par le script d'etage
  (`mov.l Rm,@(16,Rn)` / `@(20,Rn)`) : `bg01` 0,8125/0,875, `bg09` 0,75/0,75,
  `bg0e` 0,75/0,875. Sinon, le defaut de l'objet concerne — 0,875/0,875 pour l'objet 2,
  0,625/0,875 pour l'objet 6.
* **`plan` n'ordonne pas la profondeur** : la boucle `0x8C0F693C` dessine les elements
  dans l'ordre de la LISTE. Empiler par numero de plan est faux sur les vingt-six releves.

Voir `SANS-ETAT.md` pour la chaine complete sans savestate.
