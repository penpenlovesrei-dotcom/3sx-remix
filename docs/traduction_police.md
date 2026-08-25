# Ce que les polices de 3SX savent écrire

Inventaire fait avant d'écrire quoi que ce soit d'une couche multilingue, parce qu'une langue
accentuée ne vaut la peine d'être codée que si le jeu sait dessiner ses lettres.

Tout ce qui suit est lu dans `SF33RD.AFS` et dans le code, pas déduit. Pour refaire la mesure :

```
inventaire-police.cmd
```

qui écrit son compte rendu à l'écran et les planches de glyphes dans `docs\police\`.

## Réponse courte

Le périmètre visé est le texte de jeu : **citations de victoire, dialogues d'avant-combat, fins**.
Tous les trois passent par la même police et la même conversion, et **les accents y sont déjà
dessinés** : 48 lettres latines accentuées présentes dans la ROM, jamais affichées, parce que deux
verrous dans `effb6.c` les rendent inatteignables. Les lever tient en quelques lignes.

Les libellés de menu, eux, sont en ASCII pur : deux jeux de 96 glyphes, `0x20` à `0x7F`, et le
groupe de textures s'arrête juste après le 96ᵉ. C'est hors périmètre, sauf pour un point — le nom
de la langue dans la ligne d'option devra s'écrire sans accents.

## Ce que la ligne Japanese/English change, et ce qu'elle ne change pas

Vérifié sur l'amont `513380f9`. `mpp_w.language` n'est lu qu'à cinq endroits, et **aucun ne touche
au texte** :

| endroit | effet |
|---|---|
| `texgroup.c` `checkSelObjFileLoaded` | échange le fichier `ef02_usa.bin` (groupe 23) contre `ef02.bin` (groupe 98) |
| `eff76.c` `chkNameAkuma` | le nom d'Akuma, `AKUMA` ou `GOUKI` |
| `effk6.c` `chkNameSuv` | le nom du personnage 20, même principe |
| `eff35.c` | deux bannières, `c_type` 5 et 7 |
| `sys_sub.c` | persiste le choix dans la sauvegarde |

Les tables de messages ne sont indexées **que par personnage** : `pl_mes_tbl[20]`, `pl_tlk_tbl[20]`,
`pl_end_tbl[20]`, toutes en `_usa`. Il n'existe pas de jeu japonais de ces textes dans le portage —
`message/` ne contient qu'un dossier, `en/`.

**Les citations et les fins restent donc en anglais quelle que soit la position de l'option.**
Ce que l'option change est graphique : l'écran de sélection, les plaques de noms, deux bannières.
Les deux variantes de `ef02` portent d'ailleurs le même alphabet ASCII aux emplacements des lettres
de menu, seulement redessiné.

C'est plutôt une bonne nouvelle pour le chantier : il n'y a pas de mécanique existante à
détourner ni à ménager, et le texte visé vit entièrement dans des tables C.

## La police des messages — groupe 38, fichier AFS 1458

1792 objets, `cg` 0x7F30 à 0x862F. `get_message_conn_data` (effb6.c) lit le texte octet par
octet, `msgConvertObjNum` le convertit en numéro d'objet, et `set_conn_sprite` le dessine.

Six appelants, dont les trois du périmètre :

| appelant | `kind` | table | ce que c'est |
|---|---|---|---|
| `effb8.c:39` | 0 | `pl_mes_tbl` | **citations de victoire** |
| `effa6.c:121` | 1 | `pl_tlk_tbl` | **dialogues d'avant-combat** |
| `efff9.c:161` | 2 | `pl_end_tbl` | **fins** |
| `eff18.c:51` | 3 | `msgSysDirTbl` | textes système |
| `eff45.c:114` | variable | selon le message | ROUND 1, K.O., etc. |
| `effb6.c:337` | — | — | visionneuse de l'object test, pilotée par les globales `ot_*` |

Les trois qui nous intéressent tombent donc tous dans le même convertisseur, avec le même
`hzsel = 0`. Une seule correction les débloque tous les trois.

La conversion consulte trois tables de jetons, `han_adrs[3]` (effb6.c:306) :

| # | table | jetons définis | ce que c'est |
|---|---|---|---|
| 0 | `src_han_kata` | 11 | les chiffres `0`–`9` et le tiret |
| 1 | `src_han_alpha` | 73 | latin de base : `a`–`z`, `A`–`Z`, ponctuation, `$ % & ¢ £ ¥` |
| 2 | `src_han_alpha2` | **48** | **les lettres accentuées** |

Un jeton est une paire d'octets ASCII : l'octet de tête est l'accent, le second la lettre.

| tête | accent | lettres disponibles |
|---|---|---|
| `%` | tréma | `A E I O U a e i o u` |
| `)` | aigu | `A E I O U a e i o u` |
| `(` | grave | `A E I O U a e i o u` |
| `^` | circonflexe | `A E I O U a e i o u` |
| `~` | tilde | `A N O a n o` |
| `,` | cédille | `C c` |

Ces correspondances sont relevées sur les glyphes rendus, pas supposées : voir
`docs\police\src_han_alpha2.png`, où `%e` donne bien `ë` et `)e` bien `é`.

### Les deux verrous

Le chemin anglais est celui où `hzSel` vaut 0. Il vaut toujours 0 : `get_message_conn_data`
écrit `hzsel = 0` en dur (effb6.c:382), et c'est le seul appelant de `msgConvertObjNum`. Toute
la branche `hzSel != 0`, qui elle explore les trois tables, est du code mort dans ce portage.

Dans ce chemin, deux choses ferment la porte :

1. **effb6.c:495** — `for (i = 0; i < 2; i++)` : la recherche s'arrête à `han_adrs[1]`.
   `src_han_alpha2` n'est jamais consultée.
2. **effb6.c:480** — `if (moji[0] == 0x5E)` : seul `^` ouvre un jeton de deux octets. `%`, `)`,
   `(`, `~` et `,` sont lus comme des caractères isolés, donc `)e` serait rendu « `)` puis `e` ».

Un jeton introuvable ne fait pas d'erreur : il devient une espace (`goto one`). Rien ne se voit
à la compilation, et à l'écran ça ressemble à un trou de mise en page.

### Le piège si on lève le second verrou naïvement

Les textes anglais actuels utilisent déjà les octets de tête comme caractères ordinaires.
Relevé sur les 1881 chaînes de `message/en/` :

| paire | occurrences | exemple |
|---|---|---|
| `, ` | 189 | virgule suivie d'une espace |
| `) ` | 20 | fin de parenthèse |
| `(A` | 4 | `(ALEX)` et compagnie |
| `(I` | 3 | |
| `(N` | 3 | |
| `(H` `(T` `(R` `(S` `(L` `(B` `(D` `(Y` `(.` | 1 à 2 | |

`(A` et `(I` sont **aussi** des jetons valides (`À`, `Ì`). Décréter « une tête d'accent ouvre
toujours un jeton de deux octets » transformerait `(ALEX)` en `ÀLEX)`. Le paramètre `hzSel`,
inutilisé aujourd'hui, est le point d'accroche naturel pour n'ouvrir les accents que sur les
langues qui les demandent, sans toucher au rendu de l'anglais.

## Ce qu'il y a à traduire, et la place disponible

Relevé sur `message/en/` de l'amont :

| | fichiers | lignes | signes |
|---|---|---|---|
| citations de victoire | 20 | 766 | 15 676 |
| dialogues d'avant-combat | 18 | 242 | 9 876 |
| fins | 20 | 555 | 24 664 |
| **total** | **58** | **1 563** | **50 216** |

Akuma et Q n'ont pas de dialogue d'avant-combat, d'où les 18 fichiers.

Deux limites à connaître avant d'écrire une ligne :

- **108 glyphes par message, sinon le jeu se fige.** `get_message_conn_data` empile un `CONN` par
  glyphe non-espace dans un `CONN conn[108]`, et tombe sur `while (1) {}` dès que le compteur
  dépasse 108 — après avoir déjà écrit `conn[108]`, soit un élément au-delà du tableau. Le
  compteur court sur **toutes les lignes** d'un message, pas sur une ligne.
  Marge actuelle : le message le plus chargé du jeu fait **64 glyphes sur 108** (`msgEndPL00_13`).
  Il reste donc de quoi allonger de 69 % dans le pire cas. Ce n'est pas le mur.
- **La largeur de ligne, elle, est le vrai mur.** Chaque glyphe avance de 8 px, sans retour à la
  ligne automatique et sans découpe : une ligne trop longue sort de la boîte. L'anglais tient dans
  **35 glyphes** au maximum, et aucun message ne dépasse 2 lignes. C'est la contrainte de
  rédaction : deux lignes, 35 signes chacune.

## Les lettres des menus — hors périmètre, sauf pour un mot

Traduire les menus n'est pas le but ici. Ce qui suit ne compte que pour **le nom de la langue
dans la ligne d'option**, qui, lui, s'écrit forcément avec ces lettres-là.

Groupe 23, fichier AFS 1454. `eff61.c`, `eff64.c`, `eff51.c` et `eff63.c` écrivent tous
`chr = base + octet` : **l'octet ASCII
brut sert d'index**, sans table de conversion. Deux bases :

| base | jeu | glyphes | plage d'octets |
|---|---|---|---|
| `0x7047` | grandes lettres | 96 | `0x20`–`0x7F` |
| `0x70A7` | lettres étroites | 96 | `0x20`–`0x7F` |

Les deux jeux se suivent — `0x70A7 = 0x7047 + 0x60` — et le groupe finit à `cg 0x7126`, c'est-à-dire
exactement au 96ᵉ glyphe du second. **Un octet ≥ 0x80 ne désigne aucun objet** : `obj_group_table`
y renvoie le groupe 0, et `mlt_obj_disp` sort sans rien dessiner.

Voir `docs\police\menu_grande.png` et `docs\police\menu_etroite.png` : ASCII imprimable complet,
zéro accent.

Donc : `FRANCAIS` sans cédille sur la ligne d'option. En capitales c'est l'usage typographique
courant, et c'est déjà le registre de ces menus. Ajouter un 97ᵉ glyphe demanderait d'écrire dans
`SF33RD.AFS` — `tex_remix` ne sait que remplacer une page existante, pas en ajouter une.

## Ce que ça donne par langue, pour le texte long

| langue | verdict |
|---|---|
| italien | complet |
| portugais | complet (`ã õ ç` compris) |
| espagnol | lettres complètes ; manquent `¿` et `¡` |
| français | manquent `ÿ`, `œ` et `æ` |
| allemand | manque `ß` |

Le français est donc jouable à un détail près : `œ` (« cœur », « sœur », « œil »). L'écrire `oe`
est une entorse acceptable dans un jeu ; c'est un arbitrage, pas un obstacle.

## Ce qu'il reste de place

`src_han_alpha2` compte 128 emplacements dont 80 vides, tous pointant sur la tuile blanche 91.
Les numéros d'objet existent donc déjà pour `œ`, `ß`, `¿` et le reste — ce qui manque, ce sont
les tuiles, et les ajouter veut dire écrire dans `SF33RD.AFS`. Contrairement aux menus, le mur
n'est pas l'adressage.

## La forme du chantier, une fois le périmètre réduit

Traduire seulement les citations, les dialogues et les fins n'oblige à toucher **ni aux images ni
à l'archive**. Tout vit dans des tables C et dans deux fonctions.

1. `effb6.c` — ouvrir les accents. La boucle `i < 2` devient `i < 3`, et les six octets de tête
   ouvrent un jeton de deux octets. Sous condition, pour ne pas changer le rendu de l'anglais
   (voir le piège `(ALEX)` plus haut) : `hzSel`, aujourd'hui toujours nul, est l'accroche.
2. `message/<lang>/` — 58 fichiers calqués sur `en/`, 1 563 lignes. Deux lignes de 35 signes par
   message, jamais plus.
3. `msgtable_en.c` — `pl_mes_tbl`, `pl_tlk_tbl`, `pl_end_tbl` deviennent indexés par langue.
   Les trois appelants (`effb8.c`, `effa6.c`, `efff9.c`) passent par `mess_tables`, donc rien à
   changer chez eux.
4. `structs.h` + `main.c` — l'énumération `Language` gagne une valeur et `Language_Toggle`, qui
   est un `? :` binaire, devient un cycle.
5. `menu.c` / `sel_data.c` — la ligne d'option affiche un nom de plus. Attention aux tables
   parallèles indexées par position, qui ne se plaignent jamais à la compilation.
6. `sys_sub.c` — `save_w[].Language` doit accepter une valeur non binaire.
7. `checkSelObjFileLoaded` — la comparaison `omSelObjNowOnMemoryType == mpp_w.language` range
   toute langue autre que le japonais du côté `ef02_usa.bin`, ce qui est le bon comportement,
   mais recharge le fichier pour rien à chaque bascule entre deux langues latines.

Rien là-dedans ne relève du mod : c'est du code amont, et sa place est dans une PR vers
`crowded-street/3sx`.
