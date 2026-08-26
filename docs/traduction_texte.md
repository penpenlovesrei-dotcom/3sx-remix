# Traduire les citations, les dialogues et les fins

La méthode, et les outils qui la portent. Pour ce que la police sait dessiner et pourquoi
le périmètre s'arrête là, voir [traduction_police.md](traduction_police.md).

## État

**Le français est complet** : 540 messages, 986 lignes, les 20 personnages.
`traduction\fr.txt` est rempli, `traduction\message_fr\` est généré, et la chaîne passe
tous ses contrôles — 0 erreur, 0 alerte, 1158 lignes anglaises inchangées, 986 lignes
françaises relues sans faute, 118 fichiers compilés avec les flags du projet.

La langue est branchée et le build de test tourne — `C:\3sx-fr`, raccourci **3SX francais**
sur le bureau, voir la dernière section. **Le texte n'a encore été vu par personne à
l'écran** : le jeu se lance, c'est tout ce qui est vérifié.

## L'idée

Le traducteur n'écrit jamais de code et jamais d'échappement. Il remplit un fichier texte
en français accentué ordinaire ; un générateur produit les tables C, encode les accents, et
vérifie. Trois commandes, aucune ligne à recopier.

```
traduire-extraire.cmd     ->  traduction\fr.txt      (le catalogue à remplir)
        ... on traduit ...
traduire-generer.cmd      ->  traduction\message_fr\ (les tables C, vérifiées)
```

L'extraction est relançable : les blocs déjà traduits sont conservés. La génération aussi :
les blocs encore vides restent en anglais, donc on peut compiler et jouer à tout moment
avec une traduction partielle.

## Étape 1 — extraire

`traduire-extraire.cmd` lit `message/en/` du clone amont et écrit `traduction\fr.txt` :

```
[pl02win/msgWinPL02_22P]
= Range... Speed... Priority...
= Know and master all of your attacks!
> 
> 
```

Les lignes `=` sont l'anglais, en lecture seule. Une ligne `>` par ligne d'origine.
**540 blocs, 986 lignes** — les messages vides du jeu, qui sont les pauses des fins, ne
sont pas listés.

## Étape 2 — traduire

On écrit les accents normalement : `é`, `à`, `ç`, `ê`. Le fichier est en UTF-8.

Deux règles de forme :

- **Deux lignes par message, jamais plus**, et le nombre de lignes `>` d'un bloc ne change
  pas : il fixe le nombre de lignes affichées.
- **40 signes par ligne au maximum.** Une lettre accentuée occupe une colonne, comme les
  autres. Le jeu ajoute ensuite son propre retrait — 3 pour les citations et les fins, 2
  pour les dialogues — ce qui amène la ligne à la colonne 43, la plus à droite que
  l'anglais atteigne. L'en-tête du catalogue porte une règle graduée à 40.

Ce que le jeu ne sait pas dessiner est corrigé d'office, avec un avertissement :
`œ` → `oe`, `æ` → `ae`, `ÿ` → `y`, `ß` → `ss`, les apostrophes et guillemets
typographiques, les points de suspension, les tirets cadratins, les espaces insécables.

## Étape 3 — générer

`traduire-generer.cmd` encode, contrôle, écrit, puis relit. Il n'écrit rien tant qu'il
reste une **ERREUR** :

| | |
|---|---|
| ERREUR | un caractère que le jeu ne sait pas dessiner |
| ERREUR | un message de plus de 108 glyphes — au-delà, le jeu se fige |
| ERREUR | un aller-retour encodage/relecture qui ne retombe pas sur le texte d'origine |
| ERREUR | une ligne qui sort de la boîte de 48 colonnes |
| ERREUR | un nombre de lignes traduites différent de l'original |
| ALERTE | une ligne qui dépasse la colonne 43, retrait compris |
| ALERTE | une typographie corrigée |
| ALERTE | un bloc laissé vide, qui restera en anglais |

Chaque message nomme le bloc et la ligne.

Sortie : 118 fichiers — 58 paires `.c`/`.h` plus `msgtable_fr.c`/`.h`. Le `CMakeLists` de
l'amont fait `file(GLOB_RECURSE GAME_SRC CONFIGURE_DEPENDS src/*.c)`, donc **rien à
déclarer** : les fichiers déposés dans `src/.../message/fr/` sont compilés d'office.

Par défaut la génération écrit dans `traduction\message_fr\` et ne touche aucun clone.
Pour écrire directement dans un clone de travail, renseigner `CIBLE` en tête de
`traduire-generer.cmd`.

## L'encodage des accents

Les glyphes accentués sont dans la ROM, adressés par `src_han_alpha2` (effb6.c), une table
de jetons de deux octets : tête = accent, second octet = lettre. **Cette table est du code
source, pas de la donnée** — les jetons sont à nous.

Les jetons d'origine employaient `%` `)` `(` `^` `~` `,`. Quatre de ces têtes apparaissent
dans les textes anglais : `(A` y figure quatre fois, dans `(ALEX)` et compagnie. Les garder
aurait fait commencer « (ALEX) » par un `À`. Elles ont donc été remplacées par des octets
qui n'apparaissent dans **aucun** texte passant par `msgConvertObjNum` — vérifié sur les 58
fichiers de personnages plus `msgsysdir`, `msgextra` et `msgmenu` :

| tête | accent | exemple |
|---|---|---|
| `` ` `` | grave | `` `e `` → è |
| `*` | aigu | `*e` → é |
| `^` | circonflexe | `^e` → ê |
| `=` | tréma | `=e` → ë |
| `~` | tilde | `~n` → ñ |
| `;` | cédille | `;c` → ç |

`^` servait déjà de tête à deux octets dans le code et n'apparaît dans les textes que sous
la forme `^D`, jamais suivi d'une voyelle : le réutiliser pour le circonflexe ne casse rien.

Le traducteur ne voit jamais ces jetons. Ils n'apparaissent que dans les `.c` générés.

## Brancher la langue

Deux chantiers indépendants. Le premier rend les accents affichables, le second ajoute la
langue au menu.

### 1. Rendre les accents atteignables — `effb6.c`

`tools/msg_patch_effb6.py` produit le changement, ou l'applique directement :

```bash
python tools/msg_patch_effb6.py --source C:/3sx-up --sortie traduction/effb6-accents.patch
```

Deux modifications **indissociables** :

- `src_han_alpha2` est retokenisée avec les têtes ci-dessus.
- `msgConvertObjNum` essaie d'abord un jeton de deux octets sur les trois tables, puis
  retombe sur un octet seul. Avant, seul `^` ouvrait une paire et la recherche s'arrêtait à
  `han_adrs[1]`.

Prises ensemble, elles laissent le rendu anglais **rigoureusement identique** : aucune paire
formable par un texte anglais n'existe dans la nouvelle table. Prise seule, la seconde
casserait `(ALEX)`.

Ce n'est pas une supposition. `tools/msg_verifier.py` rejoue les deux lecteurs, l'ancien et
le nouveau, sur les **1158 lignes anglaises**, et compare les suites de numéros d'objet :
zéro différence. Il relit ensuite les **986 lignes générées** et remonte des numéros d'objet
vers les caractères : zéro faute. `traduire-generer.cmd` fait tourner ce contrôle à chaque
génération.

### 2. Ajouter la langue au menu

Rien de tout cela n'est nécessaire pour voir le texte français à l'écran — on peut d'abord
faire pointer `mess_tables` sur les tables françaises en dur, vérifier en jeu, et brancher
le menu ensuite.

- `structs.h` — l'énumération `Language` gagne une valeur, et `Language_Toggle`, qui est un
  `? :` binaire, devient un cycle.
- `effb6.c` — `mess_tables[6]` choisit `pl_mes_tbl` ou `pl_mes_tbl_fr` selon
  `mpp_w.language`. Les trois appelants (`effb8.c`, `effa6.c`, `efff9.c`) passent par
  `mess_tables` : rien à changer chez eux.
- `main.c` — `Get_Default_Language` lit déjà la locale SDL ; `"fr"` peut s'y ajouter.
- `menu.c` / `sel_data.c` — la ligne d'option affiche un nom de plus. **`FRANCAIS` sans
  cédille** : les lettres de menu sont en ASCII pur. Attention aux tables parallèles
  indexées par position — `Menu_Letter_Data`, `Slide_Pos_Data_61`, `Slide_Pos_Data_64`,
  `Letter_Data_64` — qui ne se plaignent jamais à la compilation.
- `sys_sub.c` — `save_w[].Language` doit accepter une valeur non binaire.
- `texgroup.c` — `checkSelObjFileLoaded` compare `omSelObjNowOnMemoryType == mpp_w.language`.
  Une troisième valeur tombe du côté `ef02_usa.bin`, ce qui est le bon comportement, mais
  recharge le fichier pour rien à chaque bascule entre deux langues latines.

## Où vit ce chantier

C'est du code **amont**. `C:\Temp3sx` est sur `251f025` et n'a même pas le sélecteur de
langue ; `C:\3sx-up` est le clone de référence, lu seulement, jamais écrit. La branche de
travail doit partir de l'amont, et la traduction a sa place dans une PR vers
`crowded-street/3sx`.

## Les outils

| | |
|---|---|
| `tools/msg_catalogue.py` | la forme des fichiers et l'encodage des accents, partagés |
| `tools/msg_extract.py` | `message/en/` → catalogue |
| `tools/msg_build.py` | catalogue → `message/<lang>/`, avec les contrôles |
| `tools/msg_patch_effb6.py` | le changement de `effb6.c` |
| `tools/msg_verifier.py` | rejoue les deux lecteurs et compare |

## Le build de test

`C:\3sx-fr` — clone de l'amont `513380f9`, les deux patches appliqués, `message/fr/` généré,
compilé en Release avec clang. Lancement par le raccourci **3SX francais** sur le bureau, ou
par `C:\3sx-fr\3SX-francais.cmd`.

La langue s'ajoute pour de bon plutôt que d'être forcée en dur : la ligne
`Options > Screen Adjust > LANGUAGE` fait maintenant défiler **EN, JP, FR**. Sur une machine
en français, `Get_Default_Language` lit la locale du système et FR est déjà choisi au
démarrage.

**Ce build a son propre profil**, dans `C:\3sx-fr\profil`. Ce n'est pas un détail de
confort : le choix de langue est écrit dans la sauvegarde, et `C:\3sx-up` ne connaît que EN
et JP. S'il relisait la valeur FR, il irait chercher `Letter_Data_64[9][2]`, qui vaut `NULL`
chez lui. Les resources sont partagées par une jonction, donc il n'y a toujours qu'une seule
copie de `SF33RD.AFS` sur le disque. Contrepartie : la sauvegarde du build de test est
vierge.

Les deux patches sont dans `traduction\` et s'appliquent à n'importe quel clone de la même
base :

| | |
|---|---|
| `effb6-accents.patch` | rend les lettres accentuées atteignables |
| `langue-fr.patch` | ajoute `LANG_FRENCH`, la ligne de menu, et le choix des tables |

`tools/msg_patch_effb6.py` et `tools/msg_patch_langue.py` les régénèrent, ou les appliquent
directement avec `--ecrire-dans <clone>`.
