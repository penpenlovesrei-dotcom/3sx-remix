# Les décors de Street Fighter III : New Generation, lus dans `SF3_1ST.BIN`

**31/08/2026.** Le même travail que `SANS-ETAT.md` a fait sur 2nd Impact, refait sur New
Generation. Tout ce qui suit sort du binaire seul — aucun savestate, aucun essai à
l'écran, le jeu n'a pas été lancé.

Outils écrits pour ça, dans `outils/` :

* `sh4ng.py` — le désassembleur/lecteur, base **0x8C010000** comme pour 2I ;
* `chargeursng.py` — l'attribution des blocs par l'appelant, calquée sur `chargeurs2i.py` ;
  elle ne suffit pas sur NG, et le §3.3 dit pourquoi ;
* `blocsng.py` — **le graphe des blocs de décor** : les lecteurs, l'attribution par
  l'appelant, l'arbre des index, et les deux épreuves jointes qui la valident ;
* `decorsng.py` — **l'outil à lancer** : il sort les six tableaux de ce document.

> **Le matériel graphique de NG EST extrait.** `pvc-ng/` contient `bg_set00.pvc` à
> `bg_set13.pvc` (20 fichiers) plus `bg_s2_01/02/04.pvc`, et `SFNG/` contient
> `B00.PK`..`B0B.PK` et `B10.PK`..`B13.PK`. Rien n'a été inventé de ce côté.

---

## 0. LE VERROU DU CHANTIER : LES TABLES DE POINTEURS SONT EN `.bss`

C'est la seule vraie différence de forme avec 2nd Impact, et elle bloque tout si on ne la
voit pas. Le code de NG désigne ses tables par des littéraux **0x8C4DE610, 0x8C4DE6B8,
0x8C4DE760, 0x8C4DE900…** — et **ces adresses sont à zéro dans le fichier**. Elles tombent
dans le trou `0x8C4D7D00 .. 0x8C4EA000` (74 496 octets), que le jeu remplit au démarrage.
Pendant une bonne partie de la recherche, chaque piste se terminait sur des zéros.

**Leur image est dans le fichier, décalée de `0x12420` :**

    .bss   0x8C4D7D00 .. 0x8C4EA000        image   0x8C4C58E0 .. 0x8C4D7BE0

    table lue par le code        ou la LIRE dans le fichier
    0x8C4DE610  scripts          0x8C4CC1F0
    0x8C4DE6B8  elements         0x8C4CC298
    0x8C4DE760  elements, jeu 2  0x8C4CC340
    0x8C4DE900  chargeur A       0x8C4CC4E0
    0x8C4DE908  chargeur B       0x8C4CC4E8

**Comment le décalage a été vérifié** — trois fois, chacune indépendante de la précédente :

1. `0x8C4DE610 − 0x12420 = 0x8C4CC1F0` tombe sur le **début d'une série de tables de 42
   entrées, pas 0xA8**, exactement la « série de dix tables » de 2I (qui, elle, en a 51) ;
2. `0x8C4DE6B8 − 0x12420 = 0x8C4CC298` a pour première entrée **0x8C1AEA78**, qui est la
   fin exacte de la table de nombres `0x8C1AEA24` (42 × 2 octets). Idem pour le second jeu :
   `0x8C1AEF30 + 84 = 0x8C1AEF84`, première entrée de `0x8C4CC340`. Deux coïncidences au
   bit près ;
3. `0x8C4DE908 − 0x12420 = 0x8C4CC4E8` : la contiguïté `pointeur[i] + nombre[i]×38 ==
   pointeur[i+1]` y tombe juste sur **16 × 38, 6 × 38, 2 × 38, 5 × 38, 8 × 38**. Une
   adresse fausse ne fait pas ça.

Je n'ai **pas** trouvé le code qui effectue la copie ; le décalage est établi par ses
effets, pas par la routine d'initialisation. C'est la seule chose ici qui repose sur une
inférence plutôt que sur une lecture directe — mais les trois recoupements ci-dessus ne
laissent guère de place au doute.

---

## 1. LES DÉCORS DE NEW GENERATION ET LEUR NUMÉRO DE BANDE

**Il y a 19 bandes (0..18) et 14 décors (0..13), et ce ne sont pas les mêmes index.**
C'est le point que 2nd Impact n'avait jamais réglé, et le binaire de NG le donne
explicitement.

Le code d'initialisation d'étage `0x8C088042` fait, mot pour mot :

    decor = u8 [0x8C552674 + 4]      aire = u8 [0x8C552674 + 5]
    bande = u16 [0x8C18A804 + (decor*3 + aire)*2]
    u16 [0x8C552674 + 74] = bande

`0x8C552674` est le contexte global de NG (l'équivalent de `0x8C6AF304` en 2I : 163
références dans le code contre 214) ; `+4` le décor, `+5` l'aire, `+74` la bande.

**La table décor → bande, `0x8C18A804` :**

| décor | bandes (aire 0 / 1 / 2) | | décor | bandes |
|---|---|---|---|---|
| 0 | 0 / 0 / 0 | | 7 | **11 / 12 / 13** |
| 1 | 1 / 1 / 1 | | 8 | **14 / 15 / 15** |
| 2 | **3 / 4 / 4** | | 9 | 16 / 16 / 16 |
| 3 | **5 / 6 / 6** | | 10 | **18 / 17 / 17** |
| 4 | **7 / 8 / 8** | | 11 | **4 / 3 / 3** |
| 5 | 9 / 9 / 9 | | 12 | 2 / 2 / 2 |
| 6 | 10 / 10 / 10 | | 13 | 19 — *aucun script, aucun élément* |

Six décors changent de bande d'un round à l'autre (décor 7 en change à chaque round).
Décors 2 et 11 sont le même décor avec les bandes **inversées**, décors 3 et 10 aussi —
et leurs blocs d'éléments sont les mêmes, dans l'ordre inverse : c'est la vérification
croisée qui confirme la lecture.

> **Et ça règle une question laissée ouverte sur 2nd Impact.** La même table existe en 2I,
> en **`0x8C1D591C`**, lue par `0x8C0DA3E2`. Elle dit : décor 8 → bandes **8 / 9 / 9**, et
> tous les décors suivants sont décalés d'un cran (décor 9 → bande 10, décor 10 → bande
> 11…). C'est exactement le « décalage d'index qui apparaît à partir de l'étage 10 » que
> `SANS-ETAT.md` constatait sans l'expliquer. **`bg08` et `bg09` sont deux bandes d'un seul
> décor.** À reporter dans le document de 2I.

### La bande k, c'est `bg_setNN` avec NN = k en hexadécimal

Établi par un descripteur de fichier et deux recoupements :

* le binaire porte la table des noms de fichiers en **`0x8C1B74F4`** (entrées de 16
  octets : `bg_set00.pvc`, `bg_set01.pvc`, … `bg_set13.pvc`), et une table de descripteurs
  de 12 octets en **`0x8C4CCB04`** (image `.data` ; jumelle `.bss` `0x8C4DEF24`) dont les
  vingt premières entrées pointent sur ces vingt noms, dans l'ordre ;
* `bg_set12.pvc` est **octet pour octet identique** à `bg_set06.pvc` (md5
  `90e314273693d1a6716892b838baa22d`) — et la bande 18 (0x12) porte exactement le même
  index de palette que la bande 6 (58) ;
* `bg_set11.pvc` fait **exactement la même taille** que `bg_set05.pvc` (301 848 octets) —
  et la bande 17 (0x11) porte le même index de palette que la bande 5 (57).

`bg_set13.pvc` est le vingtième fichier : c'est la bande 19, celle du décor 13, qui n'a ni
script d'étage (la table n'a que 19 entrées) ni le moindre élément. Décor de remplissage.

### LES DIX-NEUF BANDES SONT NOMMÉES DANS LE BINAIRE — 31/08/2026

~~« Quel personnage va avec quel décor n'est pas établi. »~~ **Si : le binaire porte la
liste.** Table de chaînes de **12 octets en `0x8C1B7E98`**, indexée par le numéro de bande
(c'est une liste de menu de mise au point ; `0x8C1B7E14` porte à côté la liste des
personnages et `0x8C1B7FDC` celle des fins).

| bande | nom | décor(aire) | | bande | nom | décor(aire) |
|---|---|---|---|---|---|---|
| 0 | `H.S.(GILL)` | 0 | | 10 | `MUN (HUGO)` | 6 |
| 1 | `N.Y.(ALEX)` | 1 | | 11 | `JAP(IBUK1)` | 7(0) |
| 2 | `N.Y.(SEAN)` | 12 | | 12 | `JAP(IBUK2)` | 7(1) |
| 3 | `JAPAN(RYU)` | 2(0), 11(1,2) | | 13 | `JAP(IBUK3)` | 7(2) |
| 4 | `JAPAN(KEN)` | 2(1,2), 11(0) | | 14 | `NAI(ELEN1)` | 8(0) |
| 5 | `H.K.(YUN1)` | 3(0) | | 15 | `NAI(ELEN2)` | 8(1,2) |
| 6 | `H.K.(YUN2)` | 3(1,2) | | 16 | `AMAZO(ORO)` | 9 |
| 7 | `LOND(DUD1)` | 4(0) | | 17 | `H.K (YAN1)` | 10(1,2) |
| 8 | `LOND(DUD2)` | 4(1,2) | | 18 | `H.K (YAN2)` | 10(0) |
| 9 | `MOSC(NECR)` | 5 | | 19 | `SELECT` | 13 |

> **Ces noms recoupent, un par un, tout ce que la structure disait — et rien n'a été calé
> sur eux.** C'est le contrôle le plus large du chantier :
>
> * **le décor 2 et le décor 11 sont Ryu et Ken**, deux personnages qui partagent le stage
>   du Japon avec deux bandes échangées entre les rounds. La table `0x8C18A804` le disait
>   déjà, sans les noms ;
> * **les décors 3 et 10 sont Yun et Yang**, qui partagent le stage de Hong Kong. C'est
>   *exactement* pourquoi leurs deux routines émettent la même séquence de blocs (§3.3,
>   épreuve 1) : ce recoupement, que je présentais comme une coïncidence trop grosse pour
>   être fortuite, a maintenant sa cause ;
> * **le décor 7 est Ibuki, avec trois bandes** — et c'est lui qui porte **sept** des onze
>   animations de pages (§5), ce qui est cohérent avec les cascades de son stage ;
> * **la bande 19 est `SELECT`**, l'écran de sélection : ce n'est pas un décor de combat.
>   D'où le décor 13 sans le moindre élément, avec des pointeurs nuls, et sans script
>   d'étage. Le vingtième `.pvc`, `bg_set13.pvc`, est donc l'écran de sélection ;
> * et la bande k porte bien `bg_set` + k **en hexadécimal**, ce qui confirme une
>   troisième fois le §1.

**Ce qui reste flou** : `H.K.(YUN1)` / `H.K.(YUN2)` et `H.K (YAN1)` / `H.K (YAN2)` sont
quatre bandes distinctes pour un seul lieu — quatre versions du même décor de Hong Kong.
Laquelle est « jour » ou « nuit », je ne le sais pas ; le binaire ne le dit pas.

---

## 2. LA TABLE DES SCRIPTS D'ÉTAGE

**`0x8C189178`, dix-neuf entrées.**

Le dispatcher est `0x8C085F7E`, byte pour byte le même code que celui de 2I
(`0x8C0D82DA`) : il recopie la table sur la pile, puis

    script = pile[ u16[contexte + 74] ]       (le numero de BANDE)

Le nombre d'entrées n'est pas déduit : **le `memcpy` en `0x8C085F8C` copie 76 octets**,
soit 19 × 4. (En 2I le même `memcpy` copie 68 octets = 17 × 4, et 2I a bien 17 entrées.)

| bande | script | décor(aire) qui l'emploient |
|---|---|---|
| 0 | `0x8C088EB8` | 0(0,1,2) |
| 1 | `0x8C08933C` | 1(0,1,2) |
| 2 | `0x8C08BFE0` | 12(0,1,2) |
| 3 | `0x8C089758` | 2(0), 11(1), 11(2) |
| 4 | `0x8C08C3E8` | 2(1), 2(2), 11(0) |
| 5 | `0x8C089B1C` | 3(0) |
| 6 | `0x8C089B1C` | 3(1), 3(2) |
| 7 | `0x8C08A3F8` | 4(0) |
| 8 | `0x8C08A3F8` | 4(1), 4(2) |
| 9 | `0x8C08A758` | 5(0,1,2) |
| 10 | `0x8C08AAF8` | 6(0,1,2) |
| 11 | `0x8C08ADBC` | 7(0) |
| 12 | `0x8C08ADBC` | 7(1) |
| 13 | `0x8C08ADBC` | 7(2) |
| 14 | `0x8C08B280` | 8(0) |
| 15 | `0x8C08B8B0` | 8(1), 8(2) |
| 16 | `0x8C08BBE8` | 9(0,1,2) |
| 17 | `0x8C089F8C` | 10(1), 10(2) |
| 18 | `0x8C089F8C` | 10(0) |

Dix-neuf entrées, **quatorze scripts distincts** — un par décor, et c'est la première
confirmation du chiffre 14.

**Il existe une seconde table par étage, `0x8C1A2534`, dix-huit entrées** (`memcpy` de 72
octets en `0x8C08D650`), lue par `0x8C08D640` avec un index pris dans l'objet lui-même
(`u16[obj+44]`), pas dans le contexte. 2nd Impact en a une aussi (`0x8C1D915C`, 17
entrées). Je ne sais pas ce qu'elle pilote ; **elle n'est pas la table des décors**, et
c'est en la prenant pour telle que j'ai perdu du temps.

---

## 3. LES CHARGEURS DE BLOCS ET LES BLOCS DE CHAQUE DÉCOR

### 3.1 L'annuaire des éléments — deux jeux, comme en 2I

Deux fonctions, `0x8C09C83C` et `0x8C09CA14`, **strictement du même moule** que les
`0x8C0233B6` / `0x8C02356A` de 2nd Impact (même prologue, même `mov #5,r5 ; add r13,r5 ;
mov.b @(4,r13),r0`) :

    nombre   = u16 [tableA + decor*6 + aire*2]
    pointeur = u32 [tableB + decor*12 + aire*4]        (soit (decor*3 + aire))

| jeu | nombres | pointeurs (.bss) | à lire en |
|---|---|---|---|
| 1 | `0x8C1AEA24` | `0x8C4DE6B8` | **`0x8C4CC298`** |
| 2 | `0x8C1AEF30` | `0x8C4DE760` | **`0x8C4CC340`** |

**L'enregistrement fait 18 octets, pas 16.** Ce n'est pas supposé : les deux boucles
comptent **neuf** `mov.w @r14+,r3` (contre huit en 2I), et les champs partent aux mêmes
offsets d'objet qu'en 2I — `#3 → objet+102` (x), `#4 → objet+106` (y). Comme en 2I, le
pointeur de l'annuaire vaut **deux octets avant** le champ `plan` :

    plan  drapeaux  x (signe)  y  palette  script  +3 mots

Contrôle indépendant : posé à `pointeur+2` avec un pas de 18, le jeu 2 se lit sans dérive
sur **69 enregistrements consécutifs** ; à un pas de 16 il déraille au deuxième.

**Les blocs, par décor** (`decorsng.py`, section 2) :

| décor | bandes | jeu 1 (nb@bloc, aires 0/1/2) | jeu 2 |
|---|---|---|---|
| 0 | 0 | 5 @ `8C1AEA78` | 10 @ `8C1AEF84` |
| 1 | 1 | 4 @ `8C1AEAD2` | 8 @ `8C1AF038` |
| 2 | 3/4/4 | 1 @ `8C1AEB1C` puis 4 @ `8C1AEB40` | 4 @ `8C1AF0EC` puis 11 @ `8C1AF134` |
| 3 | 5/6/6 | 6 @ `8C1AEB88` puis 3 @ `8C1AEBF4` | 7 @ `8C1AF1FA` puis 3 @ `8C1AF278` |
| 4 | 7/8/8 | 3 @ `8C1AEC2A` puis 5 @ `8C1AEC60` | 12 @ `8C1AF2AE` puis 15 @ `8C1AF386` |
| 5 | 9 | 9 @ `8C1AECBA` | 17 @ `8C1AF494` |
| 6 | 10 | 7 @ `8C1AED5C`, 6 @ `8C1AEDDA`, 4 @ `8C1AEE46` | 9 @ `8C1AF5C6`, 7 @ `8C1AF668` |
| 7 | 11/12/13 | 2 @ `8C1AEE8E` | 2 @ `8C1AF6E6` |
| 8 | 14/15/15 | 0, puis 4 @ `8C1AEEC4` | 9 @ `8C1AF70A` puis 2 @ `8C1AF7AC` |
| 9 | 16 | 2 @ `8C1AEF0C` | 10 @ `8C1AF7D0` |
| 10 | 18/17/17 | 3 @ `8C1AEBF4` puis 6 @ `8C1AEB88` | 3 @ `8C1AF278` puis 7 @ `8C1AF1FA` |
| 11 | 4/3/3 | 4 @ `8C1AEB40` puis 1 @ `8C1AEB1C` | 11 @ `8C1AF134` puis 4 @ `8C1AF0EC` |
| 12 | 2 | 0 | 2 @ `8C1AF0C8` |
| 13 | 19 | 0 (pointeur nul) | 0 (pointeur nul) |

L'**appelant fait foi** : ces blocs sont attribués par la table lue par `0x8C09C83C` /
`0x8C09CA14` avec l'index `décor*3 + aire` du contexte, pas par proximité d'adresse.

**Un décor est concerné par l'aire chez NG bien plus qu'en 2I** : six décors ont des blocs
différents selon le round (2, 3, 4, 6, 8, 10, 11), là où 2nd Impact n'en avait que trois.

Le détail des enregistrements (plan, drapeaux, x, y, palette, script) sort de
`decorsng.py`, section 3.

### 3.2 Les deux chargeurs à table (les objets de décor animés)

Deux fonctions du même moule que `0x8C025A9A` / `0x8C02AA7C` de 2I — index en `r5`,
nombre sur 16 bits, pointeur sur 32 bits, contexte en `r11`/`r12` :

| chargeur | nombres | pointeurs (.bss) | à lire en | record |
|---|---|---|---|---|
| `0x8C0A1A40` | `0x8C1B10D8` | `0x8C4DE900` | `0x8C4CC4E0` | **34 octets** (17 champs) |
| `0x8C0A21A4` | `0x8C1B1120` | `0x8C4DE908` | `0x8C4CC4E8` | **38 octets** (19 champs) |

Le chargeur B se valide tout seul par contiguïté :

| arg | nb | bloc | |
|---|---|---|---|
| 0 | 16 | `0x8C1B112E` | contigu |
| 1 | 6 | `0x8C1B138E` | contigu |
| 2 | 2 | `0x8C1B1472` | contigu |
| 3 | 0 | `0x8C1B14BE` | — |
| 4 | 5 | `0x8C1B14E4` | contigu |
| 5 | 8 | `0x8C1B15A2` | contigu |
| 6 | 1 | `0x8C1B16D2` | — |

(Le chargeur A ne tient que sur ses args 0 et 1, `0x8C1B10DC` et `0x8C1B10FE`, 1
enregistrement chacun ; à partir de l'arg 2 sa table recouvre celle de B et la taille de
34 ne colle plus. À ne pas employer au-delà de l'arg 1.)

> **Cette section disait « l'attribution de ces blocs-là n'est PAS faite ». Elle l'est
> maintenant** — voir le §3.3 ci-dessous, qui la remplace. Ce qui était juste et qui reste :
> les quatre appels de B en `0x8C0A1310`, `0x8C0A17AE`, `0x8C0A18BA`, `0x8C0A1A04` ne
> passent pas de constante. Ce qui était faux : j'en concluais qu'aucun chemin ne menait à
> l'appartenance. Le chemin existe, il ne passe simplement pas par une constante.
>
> Reste vrai aussi, et vérifié à nouveau avec des bornes propres et une profondeur de 4 :
> **bande 2 (décor 12) → chargeur B, arg 6, bloc `0x8C1B16D2`**, appelé en `0x8C0A8398`,
> dans la fonction `0x8C0A836C` — que la routine `0x8C08BFE0` du décor 12 est la **seule**
> des quatorze à atteindre.

---

### 3.3 L'ATTRIBUTION DES BLOCS À CHARGEUR — 31/08/2026

**Ce qui bloquait, et pourquoi c'était une erreur de méthode.** `chargeursng.py` cherchait
le motif de 2nd Impact : un script d'étage appelle un chargeur avec `mov #arg,r4`. Sur
New Generation ça ne rend presque rien, et le code dit pourquoi — **l'argument n'est
souvent pas une constante** :

    0x8C0A1310  jmp <chargeur B>   avec  r5 = u16[objet + 52]
    0x8C0A17AE  jsr <chargeur B>   avec  r5 = u16[objet + 62]
    0x8C0A18BA, 0x8C0A1A04  idem
    0x8C0A13E8  jsr <chargeur A>   avec  r5 = mot suivant du bloc en cours de lecture

Autrement dit **les blocs forment un arbre** : un enregistrement déjà chargé nomme le bloc
suivant. Chercher une constante au sommet ne pouvait donner que le sommet.

**Le sommet, lui, est bien appelé avec une constante — depuis le corps même de la routine
de décor.** Il fallait deux corrections pour le voir :

1. **borner chaque routine.** Les quatorze routines se suivent en mémoire
   (`0x8C088EB8` … `0x8C08C3E8`) ; une fenêtre fixe de `0x260` octets déborde sur la
   suivante et attribue ses appels au mauvais décor. *Première version fausse de ce
   tableau, faite comme ça : elle donnait à quatre décors des blocs qui ne sont pas à eux.*
2. **écarter les lecteurs qui ignorent leur argument.** `0x8C0A0C20` et `0x8C0B253C`
   portent un bloc en dur et **écrasent `r4`** dès leur premier appel (`jsr <alloc> ;
   mov #4,r4` dans le delay slot). La constante qu'on croit leur voir passer ne va nulle
   part. Ce sont des fonctions génériques, leur bloc n'appartient à personne.

**Les huit lecteurs réellement indexés par l'argument**, formules relevées à la main dans
chaque fonction :

| lecteur | nombres | pointeurs (image `.data`) | record | indexation |
|---|---|---|---|---|
| `0x8C0A0070` | `0x8C1B0D58` | `0x8C4CC41C` | 24 o | `arg*8 + z*2` / `arg*16 + z*4` |
| `0x8C0AC75C` | `0x8C1B2E38` | `0x8C4CC62C` | 18 o | `arg*8 + z*2` / `arg*16 + z*4` |
| `0x8C0AC934` | `0x8C1B2F18` | `0x8C4CC67C` | 18 o | `arg*8 + z*2` / `arg*16 + z*4` |
| `0x8C0A21A4` (B) | `0x8C1B1120` | `0x8C4CC4E8` | 38 o | `arg*2` / `arg*4` |
| `0x8C0A1A40` (A) | `0x8C1B10D8` | `0x8C4CC4E0` | 34 o | `arg*2` / `arg*4` |
| `0x8C0A1318` | — | `0x8C4CC484` | 32 o | `arg*4`, **un seul** enregistrement |
| `0x8C0A7B9A` | — | `0x8C4CC53C` | 16 o | `arg*4`, un seul enregistrement |
| `0x8C0A8EE4` | — | en dur `0x8C1B2638` | 24 o | `bloc + arg*24`, un seul |

> **`z` est une quatrième dimension qu'on aurait ratée.** Trois de ces lecteurs indexent
> aussi par `z = u8[contexte + 6]`, un compteur qui tourne sur 0..3 (`0x8C085F5E` fait
> `and #3`), posé juste avant le dispatcher des scripts d'étage. **Chaque couple
> (lecteur, argument) porte donc quatre blocs**, et trois décors s'en servent réellement
> pour changer d'objets — voir la colonne `z0..3` ci-dessous.

**L'attribution, par l'appelant et lui seul** (`blocsng.py`, section 2 — appels pris dans
le corps de la routine, profondeur 1) :

| décor | bande(s) | routine | blocs |
|---|---|---|---|
| 0 | 0 | `0x8C088EB8` | *aucun — que ses 5 + 10 éléments* |
| 1 | 1 | `0x8C08933C` | *aucun* |
| 2, 11 | 3 | `0x8C089758` | `0070` arg 0 → 1@`8C1B0D88` (identique aux 4 z) |
| 2, 11 | 4 | `0x8C08C3E8` | `0070` arg 1 → 3@`8C1B0DA0` ; `C934` arg 4 → 3@`8C1B3060` |
| 3 | 5, 6 | `0x8C089B1C` | `0070` arg 2 → 2@`8C1B0DE8` (z0,2) / 2@`8C1B0E18` (z1,3) ; `1318` args 0,1,2 → `8C1B1038`, `8C1B1058`, `8C1B1078` ; `7B9A` arg 0 → 1@`8C1B24C4` ; `C75C` arg 2 → 1@`8C1B2ECE` |
| 4 | 7, 8 | `0x8C08A3F8` | `8EE4` arg 0 → 1@`8C1B2638` |
| 5 | 9 | `0x8C08A758` | `0070` arg 5 → 1@`8C1B0F20` |
| 6 | 10 | `0x8C08AAF8` | `0070` arg 3 → 4@`8C1B0E48` (z0,1) / 4@`8C1B0EA8` (z2,3) ; `C75C` arg 3 → 1@`8C1B2EE0` (z0,1), rien (z2,3) |
| 7 | 11, 12, 13 | `0x8C08ADBC` | *aucun — mais sept animations de pages, cf. §5* |
| 8 | 14 | `0x8C08B280` | *aucun* |
| 8 | 15 | `0x8C08B8B0` | `C75C` arg 4 → 2@`8C1B2EF2` (z0-2), rien (z3) ; `C934` arg 1 → 4@`8C1B2F52` (z0,1) / 3@`8C1B2F9A` (z2) / 1@`8C1B2FD0` (z3) |
| 9 | 16 | `0x8C08BBE8` | `0070` arg 4 → 1@`8C1B0F08` |
| 10 | 17, 18 | `0x8C089F8C` | **exactement les mêmes que le décor 3** |
| 12 | 2 | `0x8C08BFE0` | `1318` args 3,4 → `8C1B1098`, `8C1B10B8` ; `C75C` arg 1 → rien (z0) / 1@`8C1B2E74` / 1@`8C1B2E86` / 3@`8C1B2E98` ; `C934` arg 2 → 2@`8C1B2FE2` / 1@`8C1B3006` / 1@`8C1B3018` / 1@`8C1B302A` ; **chargeur B arg 6 → 1@`8C1B16D2`** (via `0x8C0A836C`) |
| 13 | 19 | *aucun script* | — |

**Et l'arbre, un cran plus loin.** L'enregistrement de `0x8C0A1318` (32 octets) porte deux
index : le champ 9 (octets 18-19), qui part en `objet+52` et désigne un bloc du chargeur
B ; et le champ 15 (octets 30-31), qui désigne un bloc du chargeur A quand il est ≥ 0.
L'enregistrement du chargeur A (34 octets) porte à son tour, au champ 16 (octets 32-33),
un index de bloc du chargeur B, qu'il range en `objet+62`.

| décor | `1318` | → chargeur B | → chargeur A | → B (2e cran) |
|---|---|---|---|---|
| 3 et 10 | arg 0 = `8C1B1038` | arg 0 = 16@`8C1B112E` | — | — |
| 3 et 10 | arg 1 = `8C1B1058` | arg 1 = 6@`8C1B138E` | arg 0 = 1@`8C1B10DC` | arg 5 = 8@`8C1B15A2` |
| 3 et 10 | arg 2 = `8C1B1078` | arg 2 = 2@`8C1B1472` | — | — |
| 12 | arg 3 = `8C1B1098` | −1, aucun | arg 1 = 1@`8C1B10FE` | −1, aucun |
| 12 | arg 4 = `8C1B10B8` | −1, aucun | — | — |

Les sept blocs du chargeur B sont donc tous placés : args 0, 1, 2, 5 au décor 3 (et à son
jumeau le décor 10), arg 6 au décor 12. Restent les args 3 (nombre nul) et 4, que rien
n'atteint — voir « ce qui n'est pas établi » plus bas.

#### Les trois épreuves qui valident tout ça

**1. Le recoupement qui ne devait rien à cette chaîne — décor 3 et décor 10.** Les deux
routines `0x8C089B1C` et `0x8C089F8C` sont deux blocs de code distincts, écrits l'un après
l'autre dans le binaire, et elles émettent **exactement la même séquence** de sept appels
avec les mêmes arguments. Or que ces deux décors soient le même décor à bandes échangées
vient d'une **autre** table, `0x8C18A804`, lue au §1 sans rien savoir des chargeurs. Deux
chemins indépendants, une seule conclusion. (Même chose, en négatif, pour les décors 2/11 :
leurs deux bandes ont deux routines et des blocs *différents* — ce sont deux rounds au
décor différent, et le tableau le montre.)

**2. La table se valide elle-même.** Blocs triés **par adresse** (et non par argument : le
sous-index `z` entrelace les couples, donc l'ordre des arguments n'est pas l'ordre
mémoire), `pointeur + nombre × taille == pointeur suivant` :

| lecteur | taille | contigus |
|---|---|---|
| `0x8C0A0070` | 24 o | **7 / 7** |
| `0x8C0A1A40` | 34 o | **1 / 1** |
| `0x8C0A21A4` | 38 o | 2 / 3 |
| `0x8C0AC75C` | 18 o | **5 / 5** |
| `0x8C0AC934` | 18 o | 6 / 7 |

**3. Les positions.** Sur les **84 enregistrements** ainsi attribués, `x` et `y` sont
lisibles à l'octet 6 et 8 depuis le pointeur (octets 4 et 6 pour le chargeur B, 8 et 10
pour le A — le champ qui part en `objet+102` est x, celui qui part en `objet+106` est y).
Résultat : **x entre −305 et 854, y entre 16 et 183, zéro valeur hors plage** — les blocs
du chargeur B mis à part, qui sont relatifs et dont les x bruts vont de −163 à 171. À titre
de témoin, la même mesure faite sur les entrées de table que *personne* n'appelle rend des
`x` de −32768 et +24576 : le test discrimine bel et bien les entrées en service des cases
mortes.

> **CHIFFRES CORRIGÉS LE 31/08.** Cette épreuve annonçait d'abord « x entre 16 et 512 ».
> C'était faux : j'appliquais aux blocs des chargeurs le `+2` qui ne vaut que pour
> l'annuaire des éléments, et je lisais donc les `y` comme des `x` et les palettes comme
> des `y`. Voir le §9.1. **Une fois corrigé, les `x` sont bien des coordonnées de bande**
> (des centaines), et non des petites valeurs suspectes.

> **Ce que cette épreuve prouve, et ce qu'elle ne prouve pas.** Elle établit que les
> couples (lecteur, argument) retenus désignent de **vrais** enregistrements, et non des
> cases de table hors service. Elle ne dit **rien** de l'appartenance : c'est l'appelant, et
> lui seul, qui la donne. Le décalage des `x` du chargeur B est établi au §9.3 : c'est le
> **parent**, pas le contexte.

---

## 4. LA CHAÎNE DES PALETTES

Le lecteur de la table de transferts est **`0x8C095332`**, byte pour byte le même code que
`0x8C0EDFBE` en 2I, avec un index sur un octet. La chaîne :

    bande = u16 [0x8C552674 + 74]
    index = u16 [0x8C18AC10 + bande*2]                (2I : 0x8C1D5D38)
    entree = 0x8C1AAB7C + index*12 = { source RAM, destination, taille }
    palette = (source - 0x027B0000) / 128       nb = taille / 128

**Deux confirmations que la table de transferts est bien `0x8C1AAB7C` :** elle est chargée
par les quatre mêmes sites qu'en 2I (`0x8C09533A`, `0x8C09537A`, `0x8C0953C0`,
`0x8C095402` contre `0x8C0EDFC6`, `0x8C0EE006`, `0x8C0EE04C`, `0x8C0EE08E`), et les
dix-sept décors y occupent **les entrées 52 à 68 — exactement le même intervalle qu'en
2nd Impact**.

**La base RAM des palettes de NG est `0x027B0000`, pas `0x02798000`.** Le convertisseur
RAM → binaire est en `0x8C10E658` : pour une adresse ≥ `0x0158D280`,
`binaire = ram − 0x027B0000 + 0x8C1B8188`. La banque de couleurs de NG est donc à
**`0x8C1B8188`, offset fichier `0x1A8188`** (2I : `0x8C1E9AEC`, offset `0x1D9AEC`).

| bande | index | base | nb | second jeu (dst 0x12000) : base, nb |
|---|---|---|---|---|
| 0 | 52 | 0 | 25 | 25, 25 |
| 1 | 53 | 112 | 28 | 140, 28 |
| 2 | 54 | 168 | 24 | 192, 24 |
| 3 | 55 | 216 | 35 | 251, 35 |
| 4 | 56 | 286 | 26 | 312, 26 |
| 5 | 57 | 338 | 21 | 359, 21 |
| 6 | 58 | 380 | 16 | 396, 16 |
| 7 | 59 | 412 | 25 | 437, 25 |
| 8 | 60 | 462 | 24 | 486, 24 |
| 9 | 61 | 510 | 25 | 535, 25 |
| 10 | 62 | 572 | 36 | 608, 36 |
| 11 | 63 | 712 | 17 | 729, 17 |
| 12 | 64 | 644 | 17 | 661, 17 |
| 13 | 65 | 678 | 17 | 695, 17 |
| 14 | 66 | 746 | 23 | 769, 23 |
| 15 | 67 | 792 | 32 | 824, 32 |
| 16 | 68 | 856 | 24 | 880, 24 |
| 17 | 57 | 338 | 21 | 359, 21 |
| 18 | 58 | 380 | 16 | 396, 16 |

**La contrainte jointe qui valide la lecture :** le second jeu (table d'index
`0x8C18ABE4`, destination `0x12000`) tombe, pour **les dix-sept bandes sans exception**,
sur `base1 + nb1`. Autrement dit chaque bande stocke `2 × nb` palettes consécutives, et
les deux tables d'index se recoupent au numéro près. Aucune des deux n'a été calée sur
l'autre.

Deuxième recoupement : les entrées 54 (936, 24 palettes), 55 (984, 35), 64 (1412, 17) et
65 (1446, 17) de la table de 2nd Impact sont, source et taille comprises, **les mêmes
octets** que les entrées de même index chez NG. Les deux jeux partagent des transferts.

> **Ce qui n'est pas vérifié :** que le numéro de palette ainsi calculé soit celui qu'il
> faut donner au moteur de 3SX. Sur 2I, la base était confirmée par des couleurs relevées
> à l'écran ; ici, aucune image de New Generation n'a été rendue. La chaîne est correcte
> *dans les termes du binaire de NG* ; la conversion vers la numérotation CPS3 du portage
> reste à éprouver.

---

## 5. LES ANIMATIONS DE PAGES

Le mécanisme est identique à celui de 2nd Impact, et NG en a **onze** entrées (2I en a
douze) :

    0x8C09F258 (k)         cree l'objet ; k va en u8[objet+4]
    0x8C09F2A0             le gestionnaire : lit 0x8C1B09C0 + k*20
    0x8C1B09C0 + k*20      { s32 plan, s32 slot, s16* suite, u8* debut, u8* fin }
    0x8C1B061C + k*2       le decalage de DESTINATION
    la suite               des paires [duree, page], terminee par -1, et elle BOUCLE

et, comme en 2I, `décalage = 4 × (index du bloc 16×16 dans un plan large de 1024)`, d'où
`x = (index % 64) × 16` et `y = (index / 64) × 16`.

**Comment ça a été trouvé :** un balayage du binaire cherchant des enregistrements de 20
octets `{petit entier, petit entier, pointeur, pointeur, pointeur}` avec `début < fin`.
Une seule réponse dans chaque binaire — `0x8C17D8DC` (12 entrées) pour 2I, `0x8C1B09C0`
(11) pour NG. La table des destinations se lit ensuite dans les deux sites qui la chargent
(`0x8C09F352` et `0x8C09F546`), exactement comme en 2I (`0x8C0278BE` et `0x8C027AAC`).

**L'appelant donne l'appartenance**, et il est lisible en clair : les trois routines de
décor concernées appellent le spawner avec des constantes en série.

| entrée | plan | slot | destination | bloc | x, y | images | demandée par |
|---|---|---|---|---|---|---|---|
| 0 | 0 | 0 | 5728 | 1432 | 384, 352 | 12 | bande 15 (décor 8, aires 1-2), en `0x8C08B96A` |
| 1 | 0 | 0 | 6524 | 1631 | 496, 400 | 3 | bande 3 (décor 2 aire 0 / 11 aires 1-2), en `0x8C089988` |
| 2 | 0 | 1 | 6292 | 1573 | 592, 384 | 3 | bande 3 |
| 3 | 2 | 2 | 5508 | 1377 | 528, 336 | 3 | bande 3 |
| 4 | 0 | 0 | 5768 | 1442 | 544, 352 | 6 | bandes 11-13 (décor 7), en `0x8C08B054` |
| 5 | 0 | 1 | 5268 | 1317 | 592, 320 | 6 | bandes 11-13 |
| 6 | 0 | 2 | 3488 | 872 | 640, 208 | 6 | bandes 11-13 |
| 7 | 0 | 3 | 2728 | 682 | 672, 160 | 6 | bandes 11-13 |
| 8 | 0 | 4 | 2764 | 691 | 816, 160 | 6 | bandes 11-13 |
| 9 | 1 | 6 | 6584 | 1646 | 736, 400 | 26 | bandes 11-13, en `0x8C08B04C` |
| 10 | 1 | 7 | 5656 | 1414 | 96, 352 | 26 | bandes 11-13 |

Les onze entrées sont toutes réclamées, et par trois décors seulement — le décor 7 (bandes
11/12/13) en prend sept à lui seul, dont deux longues suites de 26 images à cadence
irrégulière. Les autres décors n'animent aucune page.

> **Ce qui n'est pas fait :** découper le magasin d'images. Comme sur Akuma en 2I, il
> faudra mesurer la grille dans la demi-banque du `.pvc` avant de générer quoi que ce
> soit. Les destinations, elles, sont écrites — il n'y a pas de trous à chercher à tâtons.

---

## 6. LES COEFFICIENTS DE PARALLAXE

**`0x8C189BA0`, pas `0x20`, indexée par la BANDE** (et non par le décor — c'est une
différence avec 2I, où `0x8C1D4F48` est indexée par le décor). Quatre paires de `u32` en
16.16 par ligne : les objets 0 à 3.

Trouvée par la forme (une table de pas 0x20 dont les mots +8 et +12 valent `0x00010000`
sur toutes les lignes), puis confirmée par l'appelant : `0x8C088260` la charge, et
`0x8C088282` l'indexe par `u16[contexte+74] × 0x20`, soit la bande.

| bande | objet 0 | objet 1 | objet 2 | objet 3 |
|---|---|---|---|---|
| 0 | 0,875 / 1 | 1 / 1 | 0 / 0 | 1 / 1 |
| 1 | 0,875 / 0,875 | 1 / 1 | 0,625 / 1 | — |
| 2 | 0,625 / 0,9375 | 1 / 1 | — | — |
| 3 | 0,875 / 0,75 | 1 / 1 | 0,25 / 0,625 | — |
| 4 | 0,75 / 1 | 1 / 1 | 0,5 / 0,6875 | — |
| 5 | 0,875 / 0,875 | 1 / 1 | 0,75 / 0,9375 | — |
| 6 | 0,875 / 1,0625 | 1 / 1 | — | — |
| 7 | 1 / 1 | 1 / 1 | 0,75 / 1 | — |
| 8 | 0,75 / 1 | 1 / 1 | — | — |
| 9 | 1 / 1 | 1 / 1 | 1 / 1 | — |
| 10 | 0,75 / 0,875 | 1 / 1 | — | — |
| 11 | 0,75 / 1 | 1 / 1 | 0,5 / 0,625 | — |
| 12 | 0,75 / 1 | 1 / 1 | 0,5 / 0,625 | — |
| 13 | 0,75 / 1 | 1 / 1 | 0,5 / 0,625 | — |
| 14 | 0,0625 / 0,5 | 1 / 1 | — | — |
| 15 | 0,5 / 0,5 | 1 / 1 | — | — |
| 16 | 0,75 / 0,875 | 1 / 1 | 0,5 / 0,9375 | — |
| 17 | 0,875 / 0,875 | 1 / 1 | 0,75 / 0,9375 | — |
| 18 | 0,875 / 1,0625 | 1 / 1 | — | — |

L'objet 1 vaut 1 / 1 partout : c'est le plan de base, comme en 2I. Dix bandes sur dix-neuf
ont un troisième plan.

> **Non vérifié :** que « objet 0 = plan lointain, objet 1 = plan proche, objet 2 = plan
> supplémentaire » vaille aussi pour NG. C'est la convention retenue pour 2I dans
> `etages.py`, et les valeurs sont cohérentes avec elle, mais rien ici ne la prouve. Sur
> 2I, la règle « le plus lent est le plus loin » a dû être corrigée à l'écran pour `bg0a`.

Il existe aussi une structure par bande et par plan en **`0x8C18A3F8`**, indexée
`bande*48 + plan*12` (lue en `0x8C0882E6`). Je n'ai pas déterminé ce qu'elle porte.

---

## 7. PISTES FERMÉES ET RÉSULTATS NÉGATIFS

1. **`0x8C1A2534` n'est pas la table des décors.** Dix-huit entrées, même forme que la
   bonne, lue par un dispatcher du même moule (`0x8C08D640`), et son `memcpy` de 72 octets
   confirme joliment ses dix-huit entrées. Elle est **cohérente et fausse** pour cet
   usage : son index vient de `u16[objet+44]`, pas du contexte. La bonne est `0x8C189178`,
   lue par `0x8C085F7E`, index `u16[contexte+74]`. *Encore une cohérence interne qui ne
   prouvait que le découpage.*

2. **« Le rang de la routine par ordre d'adresse donne le numéro de décor » — faux.** Les
   quatorze scripts distincts sont bien en correspondance 1:1 avec les quatorze décors
   (chacun appelle une fois l'annuaire, dans l'ordre des adresses), et j'ai failli
   conclure que le rang était le numéro. La table `0x8C18A804` dit le contraire : le
   décor 4, par exemple, est le script `0x8C08A3F8`, qui est cinquième par l'adresse.
   *L'ordre d'apparition n'est pas une numérotation.*

3. **Il n'existe pas de table bande → décor.** Cherchée sur tout le binaire en exigeant
   qu'elle regroupe les bandes exactement comme les scripts les regroupent (5-6, 7-8,
   11-12-13, 17-18) et qu'elle porte quatorze valeurs distinctes : **zéro correspondance**,
   en octets comme en `u16`. La relation ne va que dans le sens décor → bande.

4. **Le décor ne se déduit pas du numéro d'étage.** Les seules écritures de `contexte+4`
   sur un chemin lisible sont en `0x8C086194` et `0x8C0861BE`, et elles prennent leur
   valeur dans une table de progression `{décor, aire}` en `0x8C1891C4` — laquelle est
   **identique octet pour octet à celle de 2nd Impact** (`0x8C1D3FF8`) et ne couvre que
   les décors 0 à 9 plus le 12. C'est le séquenceur de la démo, pas le chemin de jeu. Je
   ne l'ai pas suivi plus loin.

5. **Les tables `0x8C4DE6xx` ne sont pas initialisées par du code repérable.** Aucune
   écriture par littéral, aucun descripteur `{destination, source, taille}` visant le trou
   `.bss`. Le décalage `0x12420` est établi par ses effets (voir §0), pas par la routine.
   Si quelqu'un veut la trouver, ce n'est pas par les littéraux qu'il faut chercher.

6. ~~**Les blocs des deux chargeurs à table ne sont pas attribués.**~~ **Levé le 31/08**,
   voir §3.3. Ce qui restait à comprendre : sur NG l'argument d'un chargeur vient presque
   toujours d'un champ de l'objet appelant ou du flux du bloc en cours de lecture, jamais
   d'une constante. Chercher `mov #arg,r4` ne pouvait donner que le sommet de l'arbre.

7. **Une fenêtre fixe autour d'une routine de décor donne de FAUSSES attributions.** Les
   quatorze routines se suivent en mémoire ; un balayage de `0x260` octets à partir de
   chacune déborde sur la suivante. Ma première version du tableau du §3.3, faite ainsi,
   donnait à quatre décors des blocs qui ne sont pas à eux — et elle était parfaitement
   cohérente d'aspect. Toujours borner une routine par la suivante.

8. **Un `mov #imm,r4` près d'un `jsr` ne prouve pas que la fonction reçoit un argument.**
   `0x8C0A0C20` et `0x8C0B253C` écrasent `r4` par le `mov #4,r4` du delay slot de leur
   appel à l'allocateur, avant tout usage. Leur bloc en dur est le même pour tous leurs
   appelants. Il faut vérifier que l'argument atteint vraiment l'adresse du bloc.

9. **La recherche de chargeurs par la forme, restreinte au code `0x8C010000..0x8C0F0000`,
   rate la moitié du binaire.** NG a du code jusqu'à `0x8C160000` au moins (`0x8C10E658`,
   `0x8C143xxx`…), et un second module chargé en `0x8C4EA0E0`. La borne de
   `chargeurs2i.py` n'est pas transposable telle quelle.

---

## 8. CE QUI RESTE À FAIRE

* **Nommer les décors.** Rien dans le binaire ne donne le personnage ; il faudra une
  capture ou un rendu des `.pvc`.
* **Les args 3 et 4 du chargeur B** (`0x8C1B14BE`, nombre nul, et `0x8C1B14E4`, 5
  enregistrements) ne sont atteints par aucun chemin trouvé. L'arg 3 porte zéro
  enregistrement et est sans doute une case morte ; l'arg 4, lui, existe et manque de
  propriétaire. À chercher du côté des champs `objet+62` des enregistrements du chargeur A
  que personne n'appelle encore.
* **Ce que `z = u8[contexte + 6]` représente vraiment.** C'est un compteur 0..3 remis à
  `and #3` en `0x8C085F5E`, et trois décors changent d'objets selon sa valeur. Round ?
  Variante aléatoire ? Heure ? Non établi — et ça change ce qu'il faut cuire.
* **La signification des champs autres que x, y, palette et script** dans les
  enregistrements de 18, 24, 30 et 38 octets. `blocsng.champs()` donne l'offset d'objet de
  chacun ; leur rôle, non.
* **Découper les magasins d'images** des onze animations de pages, comme il a fallu le
  faire pour Akuma en 2I.
* **Éprouver la numérotation des palettes** : la chaîne est complète dans les termes de
  NG, mais rien n'a été rendu à l'écran.
* Vérifier ce que porte `0x8C18A3F8` (par bande et par plan, 12 octets).
* **Reporter dans `SANS-ETAT.md`** la table `0x8C1D591C` de 2nd Impact : elle explique le
  décalage d'index à partir de l'étage 10, et elle dit que `bg08` et `bg09` sont deux
  bandes d'un seul décor.

---

## 8 bis. LE GEL DE NEW GENERATION — RÉSOLU LE 01/09/2026

**Cause : `u32* char_add[37]`, dans `eff05.c`.**

`effect_05_init` fait `ewk->wu.char_table[0] = char_add[bg_w.bg_index]`. Le tableau couvrait
les indices 0 à 36 — les 22 d'origine plus les 15 étages de 2nd Impact. **New Generation
occupe 37 à 57.** On lisait donc ce qui suit le tableau, et `set_char_move_init` — appelé dès
la première trame de dessin, dans le `case 0` de `effect_05_move` — déréférençait un pointeur
pris au hasard. Porté à 58.

`scr_obj_num` et `scr_obj_data`, indexés par le **même** `bg_index`, avaient déjà été portés à
58 ; seul celui-là était resté en arrière, et le commentaire de `scr_obj_data` décrit
pourtant ce piège exact.

**Pourquoi ça a résisté si longtemps** — le défaut ne ressemblait à rien de stable : tantôt un
gel muet, tantôt un crash sec, selon ce qui traînait en mémoire. Ni `fatal.log`, ni trace, et
le décor **entièrement chargé** juste avant, ce que les journaux montraient à chaque essai.
Et ça explique que ce soit *tout* New Generation et jamais 2nd Impact, dont le `bg_index`
tient sous 37.

**Deux pistes ouvertes puis fermées**, à ne pas rouvrir :

* aucun `while (1)` de `mtrans.c` — ils sont tous précédés d'un `flLogOut`, qui écrit
  `fatal.log` **et tue le jeu** ; pas de `fatal.log` = ce n'est aucun d'eux ;
* la liste chaînée des effets n'est **pas** cyclique — le garde-fou posé pour ça (compteur
  dans `move_effect_work`) n'a jamais parlé, et il reste en place.

**Ce qui reste en garde** : un test de bornes dans `effect_05_init` écrit dans
`fin-de-round.log` au lieu de laisser lire hors du tableau, et `char_add` porte sa taille
dans `eff05.h`. L'audit des 31 tableaux indexés par `bg_index`/`stage` n'en trouve aucun
autre trop court.

**L'outillage de diagnostic** est dans `port/video/jalon.c` : jalons le long de la trame,
journal réécrit à chaque trame et alterné entre `jalons-a.log` et `jalons-b.log`. Désarmés par
défaut ; le lanceur `GEL ETAGE 38` les rallume en créant le fichier témoin `jalons.on`.

---

## 9. POUR L'INTÉGRATION — 31/08/2026

### 9.1 Le fichier machine : `outils/ng_blocs.json`

Produit par **`outils/exportng.py`** (qui ne fait que consommer `blocsng.py` et
`decorsng.py`). Contenu :

* `bandes` — les vingt bandes, leur nom, leur script d'étage, leur `.pvc` ;
* `lecteurs` — pour chacun des dix lecteurs : taille d'enregistrement, tables, mode
  d'indexation, **la carte champ → offset d'objet**, et les champs qui enchaînent sur un
  autre bloc ;
* `decors` — pour chacun des quatorze : ses bandes et leurs noms, ses routines, sa table
  de scripts d'animation, ses **éléments** (deux jeux, par aire) et ses **blocs**
  (lecteur, argument, `z`, adresse, nombre, parent éventuel), chaque enregistrement donné
  avec son adresse, ses champs bruts *et* les six champs nommés.

Comptes : **14 décors, 91 blocs à chargeur (213 enregistrements), 232 éléments.**

> **Deux pièges de lecture, à connaître avant de générer du C :**
>
> 1. **Le pointeur d'un bloc vise le champ 0, pas le champ `plan`.** Le champ 0 part en
>    `objet+32` ; `plan` est le champ 1, deux octets plus loin. L'usage établi sur 2nd
>    Impact — « le premier enregistrement est à `pointeur + 2` » — désigne le même octet,
>    mais ne vaut que pour l'annuaire des éléments. **Appliqué aux autres lecteurs, ce
>    `+2` décale tout d'un champ** : c'est l'erreur qui m'a fait écrire, au §3.3, que les
>    x tenaient entre 16 et 512 — je lisais les y, et les y étaient les palettes. Le
>    tableau des positions du §3.3 est donc faux ; celui du §9.3 le remplace.
> 2. **Le rang d'un champ ne veut rien dire d'un lecteur à l'autre** ; l'offset d'objet,
>    si. Les dix lecteurs n'ont ni le même nombre de champs ni le même ordre, mais
>    partout :
>
>        +558 plan   +554 drapeaux   +102 x   +106 y   +88 palette   +456 script
>
>    (`+456 = script` se vérifie sur 2nd Impact : dans son annuaire des éléments, le champ
>    qui part en `+456` est le sixième mot, celui que `SANS-ETAT.md` nomme `script`.)

### 9.2 Ce qu'est `z` : un TIRAGE, pas un round

    0x8C085F4E :  u8[ctx+0] += 1
                  u8[ctx+6]  = 0x8C0191C0()        <- le retour du generateur
                  u8[ctx+6]  = u8[ctx+6] & 3
                  puis jsr 0x8C088018, l'init d'etage

et `0x8C0191C0` est un **générateur pseudo-aléatoire à table** :

    compteur = u16[0x8C549504] ; compteur = (compteur + 1) & 63 ; u16[0x8C549504] = compteur
    return u16[0x8C153C04 + compteur*2]

**La table de 64 entrées en `0x8C153C04` contient chaque valeur de 0 à 15 exactement
quatre fois** — donc, après `& 3`, exactement **seize occurrences de chacun des restes
0, 1, 2, 3**. C'est un tirage uniforme, refait à chaque entrée d'étage, et le compteur
boucle sur 64 appels. La table est **identique octet pour octet dans 2nd Impact**
(`0x8C161C88`, atteinte par `0x8C016934`) : c'est le `rand` maison des deux jeux.

> **Donc `z` n'est pas le numéro de round.** Les quatre blocs d'un couple (lecteur,
> argument) sont **quatre variantes équiprobables du même décor**, tirées au sort à
> l'entrée. Pour l'intégration : soit n'en cuire qu'une (`z = 0`), soit les cuire toutes
> et tirer. Quatre décors seulement s'en servent réellement pour changer d'objets —
> **3 / 10** (Yun-Yang), **6** (Hugo), **8 bande 15** (Elena) et **12** (Sean), dont les
> quatre `z` diffèrent en nombre *et* en adresse.

*Ce que je n'établis pas :* si `ctx+6` est écrit par un chemin que je n'ai pas vu (je n'ai
trouvé que ces trois accès, tous dans la même séquence), et si le tirage est refait entre
deux rounds ou seulement à l'entrée du stage. La séquence est placée juste avant le
dispatcher des scripts d'étage, ce qui plaide pour « à chaque entrée » — mais je ne l'ai
pas suivie jusqu'à son appelant.

### 9.3 La formule de position

Un seul lecteur décale ses enregistrements, et c'est **le chargeur B `0x8C0A21A4`** :

    0x8C0A2262   objet[+102] += parent[+102]        (x)
    0x8C0A2270   objet[+106] += parent[+106]        (y)

`parent` est `r10`, c'est-à-dire le **premier argument de l'appel** — l'objet appelant, et
non le contexte. C'est le même code, à l'instruction près, que le chargeur générique
`0x8C02AA7C` de 2nd Impact (`0x8C02AB24` / `0x8C02AB32`), que `SANS-ETAT.md` décrit comme
`objet[+102] += contexte[+102]` : **c'est le parent, pas le contexte.** À corriger là-bas
aussi.

    lecteurs 0x8C09C83C, 0x8C09CA14, 0x8C0A0070, 0x8C0A1318,
             0x8C0A1A40, 0x8C0A7B9A, 0x8C0A8EE4, 0x8C0AC75C, 0x8C0AC934
        ->  x et y ABSOLUS, dans le repere de la bande

    lecteur  0x8C0A21A4 (chargeur B)
        ->  x_final = x_bloc + x_parent      y_final = y_bloc + y_parent
            parent = l'objet de 0x8C0A1318 (index dans son champ 9, range en objet+52)
                     ou celui du chargeur A (champ 16, range en objet+62)

**L'épreuve qui le confirme**, mesurée sur le JSON :

| | enregistrements | x | y |
|---|---|---|---|
| blocs absolus | 148 | −305 … 854 | 16 … 183 |
| blocs du chargeur B, **bruts** | 65 | −163 … 171 | 0 … 161 |
| les mêmes, **après addition du parent** | 67 | −80 … 1199 | 94 … 200 |

Bruts, les x du chargeur B sont massivement négatifs — absurdes pour une position.
Additionnés au parent, **64 sur 67 tombent dans la fenêtre `0..1023` de la bande**. Les
éléments, eux, donnent x −394 … 908 : le même ordre de grandeur que les blocs absolus, et
que les valeurs relevées sur 2nd Impact.

*Ce que je n'établis pas :* les trois enregistrements qui sortent de `0..1023` (jusqu'à
1199). Sur 2nd Impact la chaîne applique un enroulement `& 0x3FF` en fin de course ; je
n'ai pas cherché son équivalent dans NG. Ne pas conclure à un mauvais appariement avant
d'avoir regardé ça.

### 9.4 La chaîne des scripts — un premier maillon, pas la chaîne entière

La **première** des dix tables de la série porte les scripts d'animation, par
`(décor*3 + aire)` :

    table0 = 0x8C4CC1F0        (image .data de 0x8C4DE610)
    script_ptr = u32 [ u32[table0 + (decor*3 + aire)*4] + script*4 ]

où `script` est le champ de l'enregistrement qui part en `objet+456`. C'est le code de
`0x8C09C94C` (annuaire) et de `0x8C0A1400` (`0x8C0A1318`) qui range la table dans l'objet ;
le numéro l'indexe ensuite.

| décor | table de scripts (aires 0 / 1 / 2) |
|---|---|
| 0 Gill | `8C0CE4BC` ×3 |
| 1 Alex | `8C0CEC00` ×3 |
| 2 Ryu / 11 Ken | `8C0D1338` / `8C0D1EEC` / `8C0D1EEC` — et le décor 11 les a **échangées** |
| 3 Yun / 10 Yang | `8C0D30E4` / `8C0D4174` / `8C0D4174` — idem, échangées |
| 4 Dudley | `8C0D5ED4` ×3 |
| 5 Necro | `8C0D6630` ×3 |
| 6 Hugo | `8C0D7B28` ×3 |
| 7 Ibuki | `8C0D8AA4` ×3 |
| 8 Elena | `8C0D9618` / `8C0D9E88` ×2 |
| 9 Oro | `8C0DB160` ×3 |
| 12 Sean | `8C0CF7D8` ×3 |
| 13 SELECT | `00000000` — nul, comme il se doit |

Chaque table est une suite de `u32` pointant sur des scripts espacés de 24 octets
(`0x8C0CE620`, `+0x18`, `+0x18`…).

**Les fichiers d'assets sont nommés dans le binaire** : `b00.pk` … `b0b.pk` et `b10.pk` …
`b13.pk` (chaînes en `0x8C2111F4`, descripteurs référencés depuis `0x8C4D4B0C`) — soit
exactement les seize fichiers de `SFNG/`. À côté : `c00.pk`…`c0e.pk` (les personnages),
`e00.pk`… (les fins), `x00.pk`.

> **PISTE OUVERTE, ET JE M'ARRÊTE LÀ.** Seize `.pk` pour vingt bandes : la numérotation des
> `bNN.pk` **n'est pas** celle des bandes (il manque `b0c`…`b0f`). Je n'ai remonté ni le
> descripteur qui choisit le fichier, ni le format interne du `.pk`, ni comment un script
> de 24 octets mène à une image. **L'équivalent de `fetc.py` et `assemblage.py` pour NG
> reste entièrement à écrire** — ce qui est acquis ici, c'est le premier maillon
> (`script` → `script_ptr`) et l'inventaire des fichiers.

### 9.5 Ce que l'intégration ne doit PAS faire

* **Ne pas appliquer le `+2` de l'annuaire aux blocs des chargeurs** (§9.1).
* **Ne pas traiter `z` comme un round** (§9.2).
* **Ne pas décaler les blocs absolus.** Seul le chargeur B se décale, et par son parent.
* **Ne pas déduire l'appartenance d'un bloc de son adresse.** Les blocs de Yun-Yang et de
  Ryu-Ken sont partagés entre deux décors, et ceux de Sean sont mêlés aux autres dans la
  même plage.
