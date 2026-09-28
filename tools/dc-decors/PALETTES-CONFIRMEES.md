# Palettes de sprites — 2nd Impact

Établi contre des captures d'écran Flycast, par correspondance **exacte** de couleurs.
Outil : `outils/balayage.py`.

> **27/08/2026 — la règle est trouvée, et elle rend ce tableau prévisible.**
> Le champ palette d'un morceau de sprite vaut `drapeaux << 9 | offset` ; la palette
> réelle est **`base(décor, drapeaux) + offset`**. Les quinze palettes confirmées
> ci-dessous retombent toutes, exactement, sur une poignée de bases — qui sont les
> sources des transferts de la table `0x1D4DBC` de `SF3_2ND.BIN`.
> Table des bases : `outils/bases.py`. Démonstration : `ASSEMBLAGE.md`.

## La règle, découverte en route

**Un asset `F_ETCnn` n'utilise pas une palette mais une plage** — chaque figure a la
sienne. Les deux baigneuses de `bg02` partagent la 1626, le personnage de la terrasse
prend la 1630 ; sur le navire de Hugo, la femme en rose, l'homme à la casquette verte et
l'homme au manteau brun tirent sur trois palettes différentes. Chercher « la » palette
d'un asset n'a pas de sens.

## Le tableau

| décor | nom | palettes de sprite |
|---|---|---|
| `bg00` | **gill** | **871** (l'acolyte), **827** (l'étoile filante) |
| `bg01` | **alex** | 952 |
| `bg02` | **ryu** | **1626**, 1630 |
| `bg03` | **yun** | **1633**, 1634 |
| `bg04` | **dudley** | **1642**, 1643, 1645, 1646 |
| `bg05` | **necro** | **1649**, 1650, 1179 |
| `bg06` / `bg10` | **hugo** | 1654, 1655, 1657, 1659, **1660**, 1661, 1242 |
| `bg07` | **ibuki** | aucun asset `F_ETC` |
| `bg08` | **elena_round1** | 1320, 1322, 1324, **1326** (les perches à crânes) et **1663** (le vautour) |
| `bg09` | **elena_round2** | *aucun sprite visible — voir plus bas* |
| `bg0a` | **oro** | 1674, 1676, **1677** |
| `bg0b` | **yang** | **1090**, 1092, 1094, 1095, 1096, **1638**, 1639 |
| `bg0c` | **ken** | **1486**, 1492, 1493 |
| `bg0d` | **sean** | **1550** |
| `bg0e` | **urien** | **1612** (le grand pilier de pierre) |
| `bg0f`, `bg11`, `bg13`, `bg14`, `bg16` | — | aucun asset `F_ETC` |
| — | **bonus_game** (`F_ETC100`) | **2317** *(globale, hors décor)* |

En gras : la palette la plus employée du décor.

Les numéros **1789 à 1800** reviennent dans presque tous les décors, à raison d'une ou
deux fenêtres : c'est un bloc partagé, sans doute l'interface. Les numéros **bas
(< 500)** sont les combattants — 24 est le Ryu violet, 210 et 214 reviennent partout.

**Ken et Urien : on sait enfin quoi chercher.** L'assemblage a montré ce que sont leurs
sprites : chez Urien des **ruines de pierre** (colonnes, arche, moellons). Chez Ken, en revanche,
ce ne sont **pas** les accessoires du ponton : le vélo, les bancs, les fleurs, le panneau
et les chaises sont tous dans `bg0c.pvc`. Les six sprites y sont petits et abstraits —
barres verticales, bloc rayé, arcs fins, bandes empilées, longues courbes, un glyphe
katakana. Ni l'un ni l'autre n'est un passant, ce qui explique qu'ils n'aient pas été
repérés en jouant.

**Urien est confirmé : 1612.** Sur `cap-urien2.png`, le grand pilier de pierre du premier
plan droit est le seul élément hors décor de l'écran ; ses douze couleurs donnent 11/12
pour la palette 1612 contre 4/12 à la suivante, et les index touchés (17 à 31) forment
une rampe contiguë. `1612 = 1607 + 5`, exactement ce que la règle `base + offset`
prédisait — le premier cas où elle a devancé la capture.

**Ken est réglé lui aussi : 1486, 1492, 1493.** Lu dans un état sauvegardé Flycast de son
étage. La banque de palettes en RAM (`0x8C7AFCCC`, 128 octets par emplacement) y porte le
bloc du décor sur les emplacements **64 à 84**, correspondant exactement aux palettes
**1477 à 1497** — la plage de `bg0c`. L'emplacement vaut `64 + offset du fichier`, règle
étalonnée sur trois décors dont les palettes étaient déjà confirmées par capture :
Elena (offsets 3 et 5 → 1322 et 1324), Sean (offset 31 → 1550) et Yang (offset 10 → 1095).
Les offsets 9, 15 et 16 de Ken tombent donc sur 1486, 1492 et 1493 ; seul 1486 est lu
octet pour octet, les deux autres occupent des emplacements dont la RAM avait été modifiée
en cours de partie (fondu ou cyclage) mais leur position dans la suite ne laisse pas de
choix.

Mon premier chiffre était donc le bon. Le retrait était pourtant justifié : la mesure sur
laquelle il reposait ne valait rien, et il a fallu lire la RAM pour trancher.

**Et une mesure de plus est tombée.** J'avais cru pouvoir trancher par la part des
couleurs du sprite présentes dans le `.pvc` du décor. Sur `cap-ken2.png`, le banc rouge
du ponton — du **fond pur** — obtient 100 %. Cette mesure ne distingue pas un sprite d'un
morceau de décor ; elle rejoint la liste des règles inventées en route et démenties.

Une progression se dessine pour une partie des décors : `bg02` 1626 < `bg03` 1633 <
`bg05` 1649 < `bg06` 1654–1661 < `bg0a` 1674–1677. Mais `bg01` (952), `bg0b` (1095),
`bg08` (1320–1326) et `bg0d` (1550) sortent de cette série. Ce n'est pas une règle —
et on sait maintenant pourquoi : la série 1625–1680 est un **bloc partagé** de figures
humaines que plusieurs décors se prêtent, tandis que 952, 1095, 1320 et 1550 viennent
du **bloc propre** à leur décor.

**La taille du bloc suit celle de l'asset.** `bg08` (Elena) en occupe six et porte deux
assets ; `bg0b` (Yang) en occupe sept répartis sur deux blocs et porte `F_ETC27`, le plus
gros de 2nd Impact (307 Ko). Ces deux décors s'identifient d'ailleurs moins bien que les
autres contre leur `.pvc` — 46 % et 37 % contre 60–90 % ailleurs. Ce n'est pas un défaut
de la méthode : une grande part de ces scènes est dessinée **en sprites**, pas dans le
fond. Le faible taux est l'information.

**Le balayage est aveugle quand un sprite partage ses couleurs avec le fond.** Il ne
retient que les couleurs *absentes* du `.pvc` ; un sprite aux teintes proches du décor
ne produit alors aucune fenêtre. C'est arrivé sur Gill : deux captures n'ont rien donné
alors que l'acolyte en robe verte était bien visible. Le recours : découper la figure à
la main, prendre **toutes** ses couleurs, et trancher avec le test de couverture
ci-dessous — la bonne palette sortait à 11/20 avec 3 % de couverture, les suivantes à
7/20 avec 84 % (les briques dorées du temple derrière la figure).

**Distinguer une palette de fond d'une palette de sprite.** Le test de couverture par les
couleurs du `.pvc`, inutile pour *trouver* un sprite, sert à *écarter* un fond :
au-delà de ~40 % c'est en général un fond, au niveau du bruit (8,6 % de moyenne) c'est un
sprite. Utile quand un balayage rend deux blocs éloignés, comme sur `bg0b`.

**Mais ce test a des faux positifs, et l'étoile filante de Gill en est un.** Sa palette
827 couvre **64 %** de `bg00` — le test la dirait « de fond ». Elle est pourtant bien
celle d'un sprite : la comète est peinte **exprès aux teintes du ciel**, vert et cyan.
Deux mesures s'y sont trompées d'affilée : la couverture, et le fait que 92,7 % des
pixels de la traînée ont une couleur présente dans le `.pvc`.

La seule vérification qui ne trompe pas est de **retrouver la forme dans les tuiles** :
en rendant `F_ETC41` avec la 827, les quatre images d'animation de la comète sortent,
tête brillante et queue. Quand couverture et appartenance des couleurs se contredisent,
c'est le rendu des tuiles qui tranche.

## Le cas `elena_round2`

Ses sprites sont chargés — `F_ETC30` et `F_ETC31` sont dans le même conteneur, partagés
avec le round 1 — mais **aucun n'apparaît à l'écran**. Vérifié sur trois captures, dont
une au bord droit du stage :

- la **cascade** est du décor : 99,8 % de ses pixels ont leur couleur dans `bg09.pvc`,
  et les palettes qui sortent (1380, 1388–1392) couvrent 91 à 95 % ;
- le **feu** est du décor : aucune flamme dans les tuiles des deux assets ;
- sur toute la zone de jeu, les couleurs hors décor sont **celles des combattants** —
  la carnation d'Elena et le gi violet de Ryu.

Les perches à crânes et le vautour, que ces mêmes assets dessinent au round 1, ne sont
pas repris au round 2. Ce n'est donc pas un échec de mesure : il n'y a rien à trouver.

Les palettes de **fond** de ce décor sont **1380 à 1392**.

## Les décors sans sprite

Leur conteneur ne porte aucun asset `F_ETC` — il n'y a rien à apparier.

**2nd Impact :** `bg07` (Ibuki), `bg0f`, `bg11`, `bg13`, `bg14`, `bg16`.

**New Generation :** `bg_set13`, `bg_s2_01`, `bg_s2_02`, `bg_s2_04`, et les seize décors
de fin et d'ouverture (`bg_end00` à `bg_end0c`, `bg_ope00`).

Note : le balayage trouve malgré tout la palette 1800 sur `bg07` et 1807 sur `bg0c`, à
raison de deux ou trois fenêtres. Ces numéros appartiennent au bloc partagé 1789–1810,
donc probablement à l'interface — pas à un sprite de décor.

## La méthode

1. Capture Flycast **à l'échelle native, sans lissage**. Les scanlines passent ; un
   agrandissement bicubique est fatal. L'émulateur étend les 5 bits par
   `(v << 3) | (v >> 2)`, donc les couleurs sont exactes.
2. Identifier le décor : comparer les couleurs de la capture aux `.pvc` (cache dans
   `outils/couleurs-2i.pkl`). Le bon décor sort à 60–90 %, les autres sous 30 %.
3. Balayer par fenêtres, en ne gardant que les couleurs **absentes du `.pvc`** — donc
   appartenant à un sprite et non au fond. Pour chaque fenêtre, la palette qui les
   contient exactement.

## Pièges mesurés

**La plage de fond ne contraint pas les sprites.** Un test de couverture des couleurs du
`.pvc` trouve les palettes du **fond**. Les palettes de sprite y sont au niveau du bruit
(1095 couvre 6,2 % de `bg0b`, moyenne 7,7 %). Ne pas s'en servir.

**Le choix par lissage d'image ne vaut rien** : sur `F_ETC100`, il classe la bonne
palette 2311e sur 2715.

**Attention aux combattants.** Le sac de frappe violet du toit d'Alex appartient au
sprite de Ryu, et ses cinq violets sont identiques à ceux de son gi — l'appariement
partait sur la palette 24, celle du personnage. Toujours vérifier qu'une couleur
« de décor » n'est pas celle d'un combattant.

**Se fier à la rampe, pas au compte.** Un score de 6/14 peut être juste si les
manquantes sont des mélanges — la baigneuse de `bg02` vue à travers la vapeur. Les
couleurs trouvées doivent occuper des **index consécutifs** : la rampe rose est aux
index 41–45, la robe mauve de `bg03` aux 41–46. Un dégradé d'ombrage est toujours rangé
ainsi ; une coïncidence ne l'est jamais.
