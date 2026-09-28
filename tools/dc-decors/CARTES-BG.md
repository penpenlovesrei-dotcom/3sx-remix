# `bg_map_tbl` / `stageXXX_map[64]` — décodé, et écarté

Décodé le 27/08/2026 en lisant `src/sf33rd/Source/Game/stage/bg.c` et en confrontant
`bg_data.c` à lui-même. Aucun émulateur, aucune partie lancée.

`outils/cartesbg.py` rejoue toute la démonstration ; `verifier-cartes.cmd` la lance.

## Le verdict, d'abord

**La carte ne place rien.** Elle ne dit pas où atterrit une page. Elle classe, case par
case, ce qui est *déjà* placé : rien / opaque / troué.

Et la question « où atterrit chaque page » n'avait pas besoin d'elle : elle est écrite en
toutes lettres dans le code de dessin. Voir plus bas — c'est la seule chose de cette page
qui serve directement au chantier.

## Ce que contient une carte

64 mots de 16 bits, **2 bits par case**, donc **512 cases**.

Sur les 42 cartes du jeu — 21504 cases — la valeur 3 **n'apparaît pas une seule fois** :

| valeur | occurrences |
|---|---|
| 0 | 9814 |
| 1 | 9246 |
| 2 | 2444 |
| 3 | **0** |

Un champ de 2 bits qui ne prend que trois valeurs sur 21504 tirages, ce n'est pas un
hasard. La découpe en 2 bits est la bonne, et l'état 3 n'existe pas.

## Ce que valent 0, 1 et 2

Le rang du plan tranche tout seul :

| rang du plan | cases à 1 | cases à 2 | part de 2 |
|---|---|---|---|
| plan 0 (le fond) | 6514 | 509 | **7 %** |
| plan 1 (l'avant-plan) | 2106 | 1912 | **48 %** |
| plan 2 | 522 | 81 | 13 % |

Et les cas extrêmes ne laissent pas de place au doute :

- **aucune** case à 2 chez DUDLEY plan 0, YANG plan 0, CHUN-LI plan 0, BONUS2 ;
- **aucune** case à 1 chez YANG plan 1 (450 cases, toutes à 2) et ELENA plan 1.

Un fond est opaque de bout en bout ; un avant-plan est troué de bout en bout. Donc :

| valeur | sens |
|---|---|
| 0 | rien à dessiner |
| 1 | opaque |
| 2 | comporte du transparent |

C'est exactement le tri dont a besoin un moteur PowerVR pour ranger un morceau dans la
liste *opaque* ou la liste *punch-through*, et sauter les vides. Le portage PS2 n'en avait
plus l'usage : **`scr_bcm[]` est écrit par `Bg_Texture_Load_EX()` et n'est jamais relu
nulle part.** C'est de la donnée morte, héritée d'un moteur antérieur.

## La granularité : deux mots par page

Preuve par les écrans fixes, dont `bgtex_etc_gbix` est simple et sans remaniement.
Règle testée : *les mots `2c` et `2c+1` décrivent la page dont le bit gbix vaut `c`.*

| écran | carte | gbix | dessiné sans page | page sans dessin |
|---|---|---|---|---|
| win/lose | `win_lose_map` | `0xFFFF` | **0** | **0** |
| select | `select_map` | `0xFFFF` | **0** | **0** |
| rank | `rank_map` | `0xF0F0` | 4 | 4 |

`win_lose_map` et `select_map` tombent juste **dans les deux sens, zéro écart** : 16 pages
chargées, 16 pages dessinées, les mêmes. `rank_map` décale de quatre — et c'est attendu,
c'est le seul écran dont `Bg_Texture_Load2()` remanie l'ordre des morceaux par
`etcBgGixCnvTable`.

Donc : **1 page = 2 mots = 16 cases**, et une case fait **32×32 pixels** dans une page de
128×128.

## Ce qui n'est pas résolu, et qu'il faut dire

Deux choses restent ouvertes. Elles ne bloquent rien, mais il ne faut pas les croire
acquises :

1. **L'ordre des 16 cases à l'intérieur d'une page.** Ligne par ligne, colonne par
   colonne, par demi-pages : rien dans les données de 3SX ne départage. Les formes
   obtenues sont des peignes quelle que soit la lecture, ce qui veut dire que la question
   est mal posée à ce stade.

2. **Les cartes d'étage débordent des pages chargées.** Les étages dont
   `bgtex_stage_gbix` vaut `0xFFFFFFFF` tombent juste (YUN, DUDLEY, HUGO, YANG, AKUMA,
   REMY : zéro écart). Ceux dont le masque est ajouré débordent, et **toujours sur les
   colonnes 0 et 7** — NECRO et TWELVE (`0x7E7E7E7E`) dessinent 0, 7, 8, 15, 16, 23, 24
   sans page en face. La carte décrit un plan entier de 8 colonnes ; l'atlas PS2 ne charge
   que les colonnes dont il se sert. **La carte est plus vieille que ce portage.**

Contre-preuve mesurée, pour mémoire : sur le décor de Ken reconstruit depuis un vidage
`tex_remix` (32 pages, 1024×512), on compte **69 cellules de 32×32 d'une seule couleur**
contre **70 cases à 0** dans `stage110_map` — le compte y est presque, mais les positions
ne se correspondent pas. La carte n'est pas alignée sur le jeu de pages du PS2.

## La règle de placement — celle qui sert

Lue dans `stage/bg.c`, `scr_trans()` et `bgDrawOneScreen()`, identique dans les huit
branches du `switch (tokusyu_stage)` :

    gbix = ((y >> 7) << 3) + (x >> 7) + gixbase       gixbase = bgnm * 64 + 100
    for (y = yy[0]; y < yy[1]; y += 128)
      for (x = xx[0]; x < xx[1]; x += 128)

et `Bg_Texture_Load_EX()` charge le i-ème bit à 1 de `bgtex_stage_gbix[étage][plan]` sous
le numéro `bgnm * 64 + 132 + i`. Comme 132 = 100 + 32 :

> **page i d'un plan → `x = (i & 7) * 128`, `y = 512 + (i >> 3) * 128`**

`x` et `y` sont bornés à `0x3FF` : l'espace de défilement d'un plan fait **1024×1024 et
boucle**. Les 32 pages occupent sa **moitié basse** — 8 colonnes sur 4 rangées, remplies
dans l'ordre de lecture par numéro de bit croissant, `i = 0` en haut à gauche.

Le bit `i` est compté **depuis le bit de poids fort** (`mask = 0x80000000; mask >>= 1`).

C'est la réponse complète à « où atterrit chaque page », et elle ne doit rien à la carte.
Pour composer un décor ajouté : découper une image de 1024×512 en 8×4 pages de 128×128
dans l'ordre de lecture, et les livrer comme pages 0 à 31 du plan.

## Ce que ça change pour le chantier

Rien du côté de 2nd Impact. Les cartes sont les données de *3rd Strike*, pour ses propres
étages ; elles ne disent rien des décors de 2I. La piste (a) de `RELAIS.md` est close :
elle a livré la règle de placement — proprement, depuis le code — et rien de plus.

La composition des décors de 2I reste à prendre par les pistes (b) états Flycast ou
(c) scripts d'étage à `0x8C6020AC`.
