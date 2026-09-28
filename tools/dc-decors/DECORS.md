# LES DÉCORS — le document unique

*Le but : extraire les décors de **2nd Impact** et de **New Generation** depuis les
disques Dreamcast et les intégrer à 3SX **sans aucune action de l'utilisateur**. Ce
fichier dit où on en est de cet objectif, ce qui est établi et par quelle mesure, ce que
chaque outil fait, et ce qui reste à automatiser.*

**Il fait foi.** Les autres fichiers du dossier sont des journaux de session : ils gardent
le détail des chemins suivis — y compris ceux qui n'ont pas abouti — et l'un d'eux porte
même une section marquée FAUX qu'il faut lire comme un raisonnement raté. En cas de
contradiction, c'est **ce fichier-ci** et `DONNEES-2I.json` qui tranchent.

| fichier | ce qu'il garde encore d'utile |
|---|---|
| `DONNEES-2I.json` | **les données machine**, régénérées depuis le binaire par `outils/inventaire.py` |
| `outils/ng_blocs.json` | l'équivalent pour New Generation (`outils/exportng.py`) |
| `SANS-ETAT.md` | le détail des désassemblages de 2I, et **les pistes fermées** |
| `NEW-GENERATION.md` | idem pour NG, et le décalage `.bss` de `0x12420` |
| `BILAN.md`, `REPRISE.md` | l'historique des régressions et les règles de travail |
| `ASSEMBLAGE.md`, `FORMAT-PVC.md` | les formats de fichier, inchangés |

---

## 1. OÙ EN EST L'AUTOMATISATION

La chaîne va **du binaire au C compilé** sans état Flycast, sans relevé, sans capture. Ce
qui suit est mesuré, pas estimé.

| | 2nd Impact | New Generation |
|---|---|---|
| étages ajoutés | 22–36, plus 56–57 | 37–55 |
| décors / bandes | 14 décors, 17 bandes | 14 décors, 19 bandes + `SELECT` |
| scripts d'animation résolus dans leur asset | **392** | 213 enregistrements |
| objets animés réellement posés | **94** (160 fiches) | 165 fiches |
| éléments statiques cuits | 30 (jeu 1) | — |

**Le trou principal est là** : 392 scripts se résolvent, 94 sont posés. Ce n'est pas un
problème d'outil mais d'**attribution** — savoir quel bloc d'objets appartient à quel
décor. Voir §6.

### Ce qui demande encore une main humaine

Par ordre de coût, et c'est la liste à vider pour atteindre le but :

1. **Les grilles des magasins d'images** (`animer2i.PAGES_ANIMEES`) — `sx, sy, larg,
   haut, nc, nl` sont mesurés à la main, décor par décor. La méthode est établie (§5f) et
   automatisable : l'écart mutuel des vignettes départage la bonne découpe d'un facteur
   30 à 70. Onze animations de pages attendent chez NG, aucune n'est faite.
2. **`famille` et `z`** (`animer2i.FAMILLE`, `Z`) — la matrice de défilement et l'ordre de
   dessin. Ce sont des grandeurs de NOTRE moteur, le binaire ne les donne pas. Aujourd'hui
   une constante par décor, avec une exception à la main pour Oro.
3. **Les positions par `MESURE`** — une seule aujourd'hui (l'édifice d'Oro), mais chaque
   fois qu'une position est fausse elle se corrige ainsi. Tant que la chaîne de position
   n'est validée que sur `bg00` (§6), ça restera.
4. **Le déploiement des `.tex`** — le jeu lit
   `%APPDATA%\CrowdedStreet\3SX\resources\tex_remix\stage<N>\`, pas le dossier de travail.
   Un `poser2i --ecrire` sans déploiement ne se voit pas à l'écran. **À intégrer dans
   l'outil.**
5. **`animer2i.TABLES`** — les adresses de blocs y sont recopiées à la main alors que
   `chargeurs2i.py` sait les produire. Le brancher supprimerait une transcription.
6. **New Generation n'a pas d'`assemblage.py`** — le premier maillon (`script` →
   `script_ptr`) est acquis, mais ni le format interne des `.pk`, ni le chemin d'un script
   de 24 octets vers une image. C'est le plus gros morceau restant côté NG.

---

## 2. LA CHAÎNE, MAILLON PAR MAILLON

Les deux jeux ont la **même architecture**. Les adresses diffèrent, la forme non.

    contexte global            2I 0x8C6AF304        NG 0x8C552674
        +4 décor   +5 aire   (+74 bande, chez NG)   +6 z chez NG (un TIRAGE, pas un round)
                    |
    décor -> bande             2I 0x8C1D591C        NG 0x8C18A804
        index (décor*3 + aire) ; le décor 8 de 2I porte les bandes 8/9/9
                    |
    scripts d'étage            2I 0x8C1D3FB4 (17)   NG 0x8C189178 (19)
        INDEXÉE PAR LA BANDE, pas par le décor
                    |
    éléments statiques         2I nombres 0x8C17B918, pointeurs 0x8C5F9C04
        NG jeu 1 0x8C1AEA24 / 0x8C4CC298 ; jeu 2 0x8C1AEF30 / 0x8C4CC340
        2I : 16 octets, premier enregistrement à pointeur+2
        NG : 18 octets
                    |
    objets animés : les CHARGEURS À TABLE, atteints depuis le script d'étage
        2I  0x8C025A9A  nombres 0x8C17C1F8  pointeurs 0x8C5F9DF8
            0x8C02E1FE  nombres 0x8C17E794  pointeurs 0x8C5F9F64
            + des spawners DÉDIÉS qui portent leur bloc en dur
        NG  huit lecteurs, cf. NEW-GENERATION.md §3.3 -- et les blocs y forment un ARBRE
                    |
    table maîtresse des scripts  2I 0x8C5F9B38 + (décor*3 + aire)*4
        NG 0x8C4CC1F0 (image .data de 0x8C4DE610)
        script -> enregistrements de 8 octets ; u16 +6 = index global
                    |
    asset F_ETCnn : anims[index global - span]
        champs 1,2 = l'ANCRE   champ 4 = offset dans la table des sprites
        le RANG de cet offset parmi les offsets distincts = le numéro de sprite
                    |
    assemblage.charger -> (asset, tuiles)   puis   assemblage.poser / poser_1555

**Les offsets d'objet sont les mêmes partout, et c'est eux qui identifient un champ** —
pas son rang, qui change d'un lecteur à l'autre :

    +558 plan   +554 drapeaux   +102 x   +106 y   +88 palette   +456 script

**Un bloc n'a pas forcément de champ `script`.** Quand il n'en a pas, c'est la ROUTINE de
l'objet qui le pose, en le lisant à un autre offset — et le chemin passe par une table de
pointeurs, jamais par un littéral (§5g). Ne pas conclure d'un bloc sans `+456` que ses
objets ne sont pas des animés : c'est l'erreur qu'il a fallu défaire.

**Le `+2`** ne vaut que pour l'annuaire des éléments. Appliqué aux blocs des chargeurs il
décale tout d'un champ.

**`objet[+102] += parent[+102]`** — le parent est l'**objet appelant**, pas le contexte.
Un seul lecteur décale ainsi (le chargeur B de NG, `0x8C0A21A4` ; `0x8C02AA7C` en 2I).

### Le format des `.bss` de New Generation

Les tables de pointeurs de NG sont en `.bss` et valent zéro dans le fichier. **Leur image
est décalée de `0x12420`** : `0x8C4DE610 → 0x8C4CC1F0`. Établi par trois recoupements
indépendants, cf. `NEW-GENERATION.md` §0.

---

## 3. LES PALETTES — la partie qui a le plus coûté

### 3a. La chaîne

    bande     = la bande du décor
    index     = u16 [0x8C1D5D38 + bande*2]          (NG : 0x8C18AC10)
    entrée    = 0x8C1E4B50 + index*12               { source RAM, destination, taille }
    palette   = (source - 0x02798000) / 128         nb = taille / 128
    couleurs  = binaire, offset 0x1D9AEC, 2715 palettes de 64 en ARGB1555

NG : base RAM `0x027B0000`, banque en `0x8C1B8188` (offset fichier `0x1A8188`).

### 3b. UN DÉCOR CHARGE DEUX BANQUES, ET C'EST L'OFFSET QUI LES SÉPARE

C'est la règle générale, pas une exception d'Oro :

    le groupe d'offsets BAS   -> le transfert SECONDAIRE, passé EN DUR par le script d'étage
    le groupe d'offsets HAUT  -> le PREMIER JEU, l'index lu par la bande

Trois mesures concordent, et aucune n'a servi à caler les autres :

* **la destination.** Sur les neuf transferts secondaires connus, **huit** ont pour
  destination exactement `0x2000 + nb1 * 128` — la suite immédiate du premier jeu dans la
  palette RAM. Une adresse au hasard ne fait pas ça ;
* **le détecteur de vert**, index 0 exclu (§3c) : `bg03` passe de 12518 pixels verts à
  **zéro**, `bg06` de 23092 à **zéro**. En sens inverse, le groupe HAUT est propre avec le
  premier jeu et sale avec le secondaire (`bg0a` 16..20 : 0 contre 17826) ;
* **le nombre de palettes** du transfert borne le groupe qu'il peut servir. C'est lui qui
  écarte le secondaire pour `bg05` (5 palettes pour 25 offsets) et `bg08` (4 pour 8).

Et la règle **retrouve toute seule le 1674 d'Oro**, la seule valeur de ce groupe qui ait
été validée à l'écran. C'est le contrôle le plus fort dont on dispose.

L'outil est **`outils/banques2i.py`**, et il refait ces trois épreuves d'un trait.

### 3c. LE DÉTECTEUR DE VERT, ET SES DEUX CONDITIONS

Une case de palette **jamais écrite** se reconnaît à ses **canaux** : rouge et bleu nuls,
vert non nul — `(v & 0x7C1F) == 0 and (v & 0x03E0) != 0`. Un pixel qui tombe dessus dénonce
une palette fausse, sans capture.

> **CE N'EST PAS UNE VALEUR UNIQUE, ET C'EST LA CORRECTION DU 05/09.** Le détecteur testait
> `== 0x03E0` (g = 248). L'objet `n05o19` de New Generation tombe sur **`0x0280`** (g = 160)
> — vert lui aussi, d'une autre valeur. Le détecteur annonçait donc **zéro vert** avec 474
> pixels verts à l'écran, et la même prémisse masquait **3 207 pixels verts en 2I** alors
> qu'on croyait le jeu propre. Une prémisse étroite ne donne pas un résultat prudent : elle
> donne un résultat faux, et net.

> **L'INDEX 0 EST EXCLU.** Il est transparent et n'est jamais peint. C'est en le comptant
> que la session du 02/09 a cru voir « 850 cases vertes » chez Hugo et a rejeté la bonne
> base. Index 0 exclu, la mesure change de camp.

**Il élimine, il ne choisit pas** : sur les 2715 palettes de la banque, 1932 passent le
test pour `bg06`. Ne jamais en tirer une attribution seule.

### 3c-bis. UNE DESTINATION, PLUSIEURS ENTRÉES : C'EST LÀ QUE SONT LES VARIANTES

La table de transferts se lit **en entier** — 2I a des entrées valides jusqu'à l'index 205,
NG jusqu'à 148, avec des trous. *Un balayage qui s'arrête à la première entrée invalide en
rate les deux tiers, et c'est ce qui a fait conclure qu'aucun transfert n'avait la
destination contiguë de la bande 5 de NG. Il y en a un, et un seul.*

Une fois la table entière lue, la structure saute aux yeux : **plusieurs entrées écrivent à
la même destination**. Ce sont les variantes de l'étage — le même emplacement de palette
RAM, rempli différemment selon le tirage.

| destination | entrées | ce que c'est |
|---|---|---|
| `0x2000` / `0x12000` | 20 et 21 | le premier et le second jeu, une par bande |
| `0x2C00` (2I, Oro) | idx108 base 1674 nb 4, **idx105 base 2184 nb 8**, idx134 base 1760 nb 1 | trois variantes |
| `0x2300`…`0x2800` (2I) | trois entrées de `nb` 1 chacune | neuf emplacements à trois variantes |
| `0x2880` (NG) | idx13..18 plus idx109/110/111 (nb 17) | neuf entrées |

Entre 1674 et 2184, **63 des 64 cases diffèrent** : ce ne sont pas des doublons.

Notre portage aplatit les variantes en un seul étage. Un objet est donc peint avec la
palette de la variante à laquelle il appartient, et un `BANQUES_2I` qui mélange deux bases
sur un même décor est la lecture juste, pas une incohérence.

### 3c-quater. LES INDEX NE SONT PAS « EN DUR » : IL Y A TROIS TABLES

Le chargeur d'étage lit la bande, puis indexe **trois tables d'affilée** et appelle le même
transfert pour chacune (2I `0x8C0DA450`, NG `0x8C03ABC6`) :

| | 2nd Impact | New Generation | index |
|---|---|---|---|
| le second jeu, dst `0x12000` | `0x8C1D5D14` | `0x8C18ABE4` | `bande*2` |
| le premier jeu, dst `0x2000` | `0x8C1D5D38` | `0x8C18AC10` | `bande*2` |
| **le secondaire** | **`0x8C1D5D66`** | **`0x8C18AC46`** | **`(bande-1)*2`** |

La troisième est indexée par `bande - 1` (le code saute la lecture pour la bande 0). Elle
rend **les neuf valeurs qu'on avait relevées une à une** dans les scripts d'étage — les
neuf exactes — et **sept bandes de plus** qu'on croyait sans secondaire. `EN_DUR` était la
copie manuelle d'une table qui existe.

> **`52 + bande` EST UNE SUPPOSITION, ET ELLE CASSE.** On calculait l'index du premier jeu
> au lieu de le lire. Les entrées se suivent bien pour les bandes 0 à 16, mais NG en a
> **dix-neuf** : `52 + 17` tombe sur l'entrée 69, le second jeu de la bande 0. La bande 17
> sortait avec la base 25 au lieu de 338, et le balayage lui comptait **64 476 pixels verts
> qui n'existaient pas**.

### 3c-quinquies. UN DÉCOR PORTE PLUSIEURS BANDES, ET L'AIRE NE DIT PAS LAQUELLE

    2I : bande = u16[0x8C1D591C + decor*6 + aire*2]      trois aires par décor
    NG : d["bandes"], une entrée par aire

Seize décors de 2I rendent trois fois la même bande ; **le décor 8 rend `[8, 9, 9]`**. En
NG, plusieurs décors en portent deux — celui de `ng05` a `[5, 6, 6]`.

On peignait tout avec la première. `n05o9` — la lanterne — sortait 236 pixels verts ainsi,
et propre avec l'autre.

> **PRENDRE `bandes[aire]` NE MARCHE PAS, ET C'EST MESURÉ.** Ça corrige le décor 3
> (`[5, 6, 6]`) et ça casse le décor 10 (`[18, 17, 17]`) : deux objets propres y repassent à
> 70 et 116 verts. Les bandes 5 et 17 chargent la **même** base (338), 6 et 18 aussi (380) :
> dans les deux décors les objets concernés veulent 380. La liste n'est donc pas dans
> l'ordre des aires.

La règle appliquée est celle que le détecteur autorise — **éliminer** : on garde
`bandes[0]`, et on ne passe à une autre bande **du même décor** que si elle est propre là où
la première ne l'est pas. Aucun candidat n'est inventé.

**Résultat : 4 437 pixels verts posés → 0.**

### 3c-ter. LE TROISIÈME TRANSFERT DE LA BANDE 5 DE NEW GENERATION

Frédéric : « les couleurs sont fausses ». Les trois critères de §3b, tous concordants :

* **la destination** — `0x2A80` = `0x2000 + 21*128`, la suite immédiate du premier jeu.
  **Une seule** entrée de la table y écrit : l'index 106, base 1397 ;
* **le détecteur** — offsets 0 à 8 : **14 713** pixels verts avec le premier jeu, autant
  avec le second, **zéro** avec 1397. Aucun des sept offsets peints n'y résiste ;
* **le nombre** — `nb` = 9 borne exactement le groupe 0..8.

La bande 5 est **la seule des dix-neuf** dans ce cas : partout ailleurs le premier jeu est
déjà propre, ou l'entrée qui tombe sur la destination contiguë est sale — elle sert une
autre bande, et la coïncidence de destination ne suffit pas.

Les deux derniers récalcitrants — `bg08` objet 0 (458 px) et `ng05` objet 9 (236 px) — ne
tenaient pas au transfert mais à la **bande** : voir §3c-quinquies. **Le compte final est
zéro.**

### 3d. « DRAPEAU 9 » N'EST PAS UNE BANQUE : C'EST LE BIT DE MIROIR

Le champ palette d'un morceau vaut `drapeaux << 9 | offset`. Sur les quatorze assets,
`drapeaux` ne prend que **quatre** valeurs, et leurs bits sont ceux que
`assemblage.morceaux` lit comme retournements :

| drapeaux | morceaux | bit 11 | bit 12 | soit |
|---|---|---|---|---|
| 1 | 12499 | | | aucun retournement |
| 5 | 3 | oui | | miroir vertical |
| 9 | **512** | | oui | **miroir horizontal** |
| 13 | 4 | oui | oui | les deux |

Il n'y a pas de cinquième valeur. **L'épreuve qui tranche** : les quatre figures animées de
`bg00` ont les palettes 871 à 874 — établi par deux chemins indépendants, et 871 validée à
l'écran. Leurs morceaux portent **tous** le drapeau 1, offsets 44 à 47, et `827 + offset`
les rend exactement.

Ce que la fausse seconde base faisait : elle envoyait les 512 morceaux retournés chercher
leurs couleurs dans une palette lointaine — 1304 au lieu de 1219 chez Hugo. Un vêtement
dont la moitié est un morceau miroir sortait d'une couleur sans rapport avec l'autre.

### 3e. LA TABLE DU SECOND JEU EST EN `0x8C1D5D14`

Pas `0x8C1D5D16`. L'épreuve qui l'avait validée — « la destination vaut 0x12000 » — dit
seulement qu'on est tombé dans le second bloc, pas sur la bonne **entrée**. Celle de New
Generation est bien plus forte : chaque bande range `2 × nb` palettes consécutives, donc
`base2 == base1 + nb1` **et** `nb2 == nb1`.

    0x8C1D5D14   17 bandes sur 17
    0x8C1D5D16    0 bande  sur 17     <- ce qu'on lisait

Décalée de deux octets, elle donnait à chaque bande le second jeu de la **suivante**.

### 3f. Trois pièges mesurés

* **la palette est celle du MORCEAU, pas de l'élément** — 913 au lieu de 839 pour
  l'obélisque ;
* **elle n'est pas constante sur un sprite** : le temple d'horizon en mélange deux (842 et
  867), les obélisques aussi. Imposer celle du premier morceau sort 29 pixels de magenta ;
* **des premières entrées en magenta `0xFC1F` ne rendent pas une palette fausse** :
  l'obélisque n'emploie que les index 7 à 15 et 27 à 31.

---

## 4. LES OBJETS ANIMÉS — les bornes du moteur

Elles ne se voient nulle part dans le générateur et **chacune se paie par un gel sans
message**. `outils/verifier_objets.py` les vérifie toutes sur le C produit.

| borne | valeur | d'où elle vient |
|---|---|---|
| objets par étage | **32** | `clé = rang<<11 \| image<<5 \| case`, cinq bits de rang |
| cases par objet | **32** | cinq bits de case dans la même clé |
| images par objet | **64** | six bits d'image |
| cases de `NotreTrans` | 64 | `decor_objets.c` |
| **motifs vivants par étage** | **64** | `PatternCollection` ; identité `rang<<6 \| image` |
| morceaux dans le tas | **1024** | `x16_map[4][16]`, quatre pages |
| durée de vie d'un motif | 12 trames | `mts_base[7].life16` |
| couleurs par palette | **63** | 64 entrées, l'index 0 transparent |

**Ce qui compte n'est pas le total mais ce qui est VIVANT** : seules les images vues dans
les douze dernières trames occupent un emplacement, et un objet qui ne **boucle** pas
reste sur son image 0 — il n'occupe qu'une identité, quel qu'en soit le nombre d'images.

> **C'est la borne des MOTIFS qui a gelé Ibuki, pas celle du tas.** La trace le disait en
> toutes lettres — « 43 emplacements seulement dans la collection ». Akuma en demande 26
> et Ibuki à une cascade 27 : les deux marchent. Ibuki à deux cascades en demandait plus
> de cent. `animer2i` tient désormais ce budget par étage et **écarte un objet entier en
> le disant**, au lieu de laisser le moteur partir en `while (1)`.

### On SERT, on ne retaille pas

Deux découpages, et ils se composent :

* **spatial** — `animer2i.morceaux_objet` : au-delà de 32 cases, l'objet est servi en
  objets **voisins** qui se rejoignent au pixel, chacun décalé de `col0*16` ;
* **chromatique** — `animer2i.groupes_palette` : au-delà de 63 couleurs, il est servi en
  objets **superposés**, chacun avec sa palette, chacun ne dessinant que les pixels qui
  lui reviennent.

> **Le partage chromatique se fait par PROVENANCE, pas par couleur**, et c'est ce qui le
> rend sûr : une palette source ne porte que 63 couleurs utiles, donc une couche bâtie sur
> une palette source tient **toujours** — ce n'est pas une espérance, c'est une borne. Et
> chaque pixel n'a qu'une provenance, celle relevée **pendant** la composition, là où le
> recouvrement des morceaux se décide : les couches forment donc une partition. Vérifié :
> leur somme redonne l'image au pixel près, sur tous les objets du port. Partager par
> couleur aurait sorti deux fois les pixels recouverts, et l'ordre de dessin de deux objets
> de même `z` ne les départage pas.

`assemblage.poser_1555(..., avec_source=True)` rend la provenance.

### Les cases vides ne coûtent plus un morceau

`DecorObjets_Tuile` rend `tuile_vide` sous `CLE_VIDE` — une seule entrée partagée — pour
toute case que la table ne couvre pas. Le générateur les saute donc, et **`nb_tuiles` n'est
plus `nb_images * cols * ligs`** : c'est la borne de boucle de `DecorObjets_Tuile`,
l'annoncer trop grand lui ferait lire au-delà du tableau.

---

## 5. CE QUI EST ÉTABLI, ET PAR QUELLE MESURE

| acquis | la mesure |
|---|---|
| l'index de `0x8C1D3FB4` est la **BANDE** | 16/17 blocs résolvent à 100 % contre 14/17, et ça redresse les deux échecs |
| le décor 8 de 2I porte les bandes 8/9/9 | `0x8C1D591C`, lue par `0x8C0DA3E2` ; explique le « décalage à partir de l'étage 10 » |
| `drapeaux` = les bits de miroir | quatre valeurs, bits exacts ; Gill 871–874 tout en drapeau 1 |
| la table du second jeu est en `0x8C1D5D14` | 17/17 contre 0/17 sur `base2 = base1+nb1` et `nb2 = nb1` |
| deux banques par décor, séparées par l'offset | destination contiguë 8/9, détecteur 23092→0, et Oro retrouvé |
| le sens de l'axe vertical | l'acolyte de `bg00` déplacé à `y 113` : « monté ». `sol ↑ → BAS` |
| le chemin du singe de Sean | 4 recoupements : sprite égal 2560/2560, durées identiques, signature unique, position recalculée |
| `char_add[37]` → 58 | c'était le gel de New Generation |
| les 19 bandes de NG sont **nommées** dans le binaire | table de chaînes `0x8C1B7E98` ; recoupe la structure une par une |
| `z` de NG est un **TIRAGE**, pas un round | `0x8C0191C0`, table de 64 entrées, chaque valeur 0..15 quatre fois |
| les couches de palette forment une partition | leur somme redonne l'image au pixel, sur tous les objets |
| les bornes du moteur | `verifier_objets.py`, 253 fiches, aucune faute |

### 5e. LES SPAWNERS DÉDIÉS, LUS DANS LEUR CODE — `outils/spawners2i.py`

Un spawner ne se devine pas : l'outil le désassemble et en sort quatre choses.

1. **La carte des champs.** Le corps écrit chaque champ à un offset d'objet donné en
   clair (`mov #102,r0 ; mov.w @r14+,r3 ; mov.w r3,@(r0,r4)`). On suit `r0` et on apparie.
   La taille de l'enregistrement est le nombre de champs × 2 — jamais supposée.
2. **Comment le bloc est atteint** : en dur, en dur indexé par l'argument
   (`0x8C17F2D8 + arg*24` chez Alex), ou par deux tables.
3. **Le nombre de tours**, lu dans la comparaison qui précède le branchement arrière.
4. **`z`**, reconnu au seul endroit où il se lit : `mov.b @(6,contexte)`.

| spawner | pas | bloc | appelé par |
|---|---|---|---|
| `0x8C04AE04` | 8 | en dur `0x8C183DC8`, boucle ×4 | bande 0 Gill |
| `0x8C0258DA` | 10 | en dur `0x8C17C190`, boucle ×4 | bande 0 Gill |
| `0x8C03CBCC` | 8 | en dur `0x8C17FD04`, boucle ×4 | bande 8 Elena |
| `0x8C0323F0` | 24 | `0x8C17F2D8 + arg*24`, un par appel | bandes 1 Alex, 4 Dudley |
| `0x8C036480` | 18 | tables `0x8C17F54C` / `0x8C5FA00C` | bande 3 Yun (arg 2), 6 Hugo (arg 3) |
| `0x8C036688` | 18 | tables `0x8C17F5B8` / `0x8C5FA05C` | bande 2 Ryu (arg 0) |
| `0x8C028792` | 22 | tables `0x8C17DB38` / `0x8C5F9E24` | 7 bandes, chacune son argument |

> **`0x8C17F54C` N'EST PAS UN BLOC : c'est une table de NOMBRES.** La chaîne la lisait
> comme des enregistrements, à `0x8C17F54C + 38`, et en tirait quatre objets pour Hugo. Or
> le spawner n'est appelé que **deux fois dans tout le binaire**, et chaque appelant a
> **un** enregistrement : un des quatre était celui de Yun, deux n'appartenaient à
> personne (l'argument 4, que rien n'atteint).

> **ET `z` EXISTE AUSSI EN 2nd IMPACT.** `z = u8[0x8C6AF304 + 6]`, exactement comme NG.
> C'est un tirage uniforme sur 0..3 refait à chaque entrée d'étage — le générateur et sa
> table de 64 entrées sont **identiques octet pour octet dans les deux jeux**. Chaque
> couple (spawner, argument) porte donc quatre variantes ; on ne cuit que `z = 0`.

> ~~**Un spawner sans champ `+456` ne fait pas d'objet animé de notre espèce.**~~
> **FAUX, levé le 02/09** : le chemin est plus long d'un cran. Voir §5g.

**Deux pièges opposés sur les bornes de fonction**, et les deux ont coûté :

* une **fenêtre fixe** déborde sur la suivante et lui vole ses appels ;
* le **premier `rts` n'est pas la fin** — le SH-4 sort tôt. `0x8C0323F0` teste
  l'allocation et rend `-1` vingt octets avant le corps qui lit le bloc. S'arrêter là
  faisait conclure « cette fonction ne lit aucun bloc ».

La règle qui tient les deux bouts : suivre les branchements, retenir la cible la plus
lointaine, et n'accepter un `rts` que s'il n'est **pas enjambé**.

### 5g. UN OBJET EST UN `WORK`, ET SON `id` CHOISIT SA ROUTINE

C'est le maillon qui manquait pour deux lecteurs sur trois. L'objet de 2nd Impact est le
**même `WORK`** que le port porte en C (`src/structs.h`) — la disposition se recoupe
champ par champ avec ce que les spawners écrivent :

    +0 be_flag   +1 disp_flag   +4 type   +6 work_id   +8 id
    +32 dead_f   +36 routine_no[8]   +52 old_rno[8]   +68 hit_stop   +72 cgromtype

**`+8` est l'`id`**, et il indexe la table des routines d'effet de 2nd Impact —
**`0x8C179FDC`, 196 entrées** — lue par le répartiteur `0x8C0215E0` :

    mov.w @(8,r14),r0 ; shll2 r0 ; mov.l @(r0,r10),r3 ; jsr @r3 ; mov r14,r4

avec `r10 = 0x8C179FDC` et `r11 = 0x8C6466EC`, le tas d'objets de 2048 octets — le même
littéral que les spawners emploient pour allouer.

> **La table se valide elle-même** : chaque spawner est écrit **juste après sa routine**.
> id 18 → `0x8C028510` puis le spawner `0x8C028792` ; id 66 → `0x8C03215C` puis
> `0x8C0323F0` ; id 87 → `0x8C0363A4` puis `0x8C036480`. Trois sur trois.

**Et la routine en appelle une autre, choisie par un champ du bloc** (`+38`) :

    mov #38,r0 ; mov.w @(r0,r14),r3 ; mov.l @(r0,<table>),r2 ; jsr @r2

    id 66 -> table 0x8C5F9FB4 (4 entrées, dont deux `rts` nus)
    id 18 -> table 0x8C5F9EA4 (2 entrées)

C'est **cette** routine qui pose le script, en appelant `0x8C0B4AD4` :

    objet+454 = r5        objet+456 = r6, LE NUMERO DE SCRIPT

et `r6` est lu dans l'objet — `+52` (`old_rno[0]`) pour l'id 66, `+150` pour l'id 18.
**Les deux tombent sur le même endroit du bloc : l'OCTET 12** de l'enregistrement, qui
fait 24 octets dans les deux cas.

> **Pourquoi le balayage ne l'avait pas vue** : cette routine n'est atteinte que par une
> table, jamais par un littéral de code. Un scan qui suit les `jsr` par leurs littéraux la
> rate, même en profondeur 3 — et conclut « n'écrit pas `+456` ». La leçon vaut au-delà
> d'ici : **une table de pointeurs est un appel**, et il faut la suivre comme tel.

L'épreuve : les scripts ainsi lus se résolvent **dans l'asset de leur propre décor** —
Alex 2 et 3, Dudley 4 et 5, et neuf des onze enregistrements de l'id 18. Les deux qui ne
se résolvent pas rendent **zéro image** : il n'y avait rien à poser.

Au passage, l'entrée `bg01` lisait déjà son script à l'octet 12 : elle était juste, et
c'est maintenant établi au lieu d'être un heureux hasard.

### 5h. LA TABLE DES 196 EFFETS, DÉPOUILLÉE — `outils/effets2i.py`

L'outil balaie tout le binaire à la recherche des **spawners** : toute fonction qui écrit
un `id` **constant** en `objet+8`. Il en trouve pour 176 des 196 ids. Il ne retient
ensuite que ceux qui **lisent un bloc** (`mov.w @rM+`) — ce qui sépare un objet fabriqué
depuis des **données** d'un objet créé par du code : il en reste **trente-deux**.

Et de ces trente-deux, **quatre** sont atteints depuis un script d'étage :

| id | spawner | pas | d'où vient le script | appelé par |
|---|---|---|---|---|
| 18 | `0x8C028792` | 24 | routine, octet 12 | 7 bandes |
| **25** | **`0x8C029B00`** | **30** | **bloc, octet 12** | **bande 11 (Yang), args 0, 1, 2** |
| 66 | `0x8C0323F0` | 24 | routine, octet 12 | bandes 1 (Alex), 4 (Dudley) |
| 87 | `0x8C036480` | 18 | bloc, octet 12 | bandes 3 (Yun), 6 (Hugo) |

**L'id 25 était le seul encore inexploité.** Son bloc vaut `u32[0x8C5F9EAC + arg*4]`, un
enregistrement par appel, et Yang l'appelle **trois fois** — sites `0x8C0DCAB6`,
`0x8C0DCABA`, `0x8C0DCABE`, dans sa propre routine. Scripts 65, 63 et 3, une image
chacun : des poses fixes. Yang passe de 2 objets à 5, alors que son asset est le plus
riche des quatorze (602 sprites, 93 scripts résolus).

Les vingt-huit autres spawners à bloc ne sont atteints par **aucun** script d'étage. C'est
la piste qui reste : soit ils appartiennent à des écrans hors combat, soit ils sont
atteints par un chemin que l'énumération d'appels ne suit pas encore.

### 5i. LES VARIANTES `z` — pourquoi on cuit `z = 0`

Chaque couple (lecteur, argument) porte quatre blocs, tirés au sort à l'entrée de l'étage.
Sur les **dix couples** qu'un script d'étage atteint, **deux seulement** portent des blocs
réellement différents :

| | z 0 | z 1 | z 2 | z 3 |
|---|---|---|---|---|
| Yun `0x8C028792` arg 2 | script 19 | **rien** | script 19 | **rien** |
| Hugo `0x8C028792` arg 3 | 7, 9, 11 | 7, 5, 11 | 7, 11, 13 | 7, 5, 11 |

`z = 0` est donc le plus riche chez Yun et à égalité chez Hugo, dont les quatre variantes
donnent trois objets et ne diffèrent que par **un** sprite. Poser leur union montrerait
trois figures là où le jeu n'en montre qu'une.

> **Le choix n'est plus un défaut, c'est un résultat.** Et ce qu'on ne montre pas est
> chiffré : deux sprites de Hugo (scripts 5 et 13) ne sont jamais vus.

### 5j. REMONTER LE GRAPHE D'APPELS — `outils/remonter2i.py`

**Descendre coûte cher et rate des chemins ; remonter est exact.** Une fonction n'est
atteignable que si son adresse apparaît quelque part — comme littéral, ou **dans une table
de pointeurs**. On part de la cible et on remonte jusqu'à tomber dans l'une des dix-sept
routines d'étage.

Le résultat : **douze** des trente-deux spawners à bloc sont atteints, là où l'énumération
descendante n'en voyait que quatre.

> **Deux défauts de bornage l'empêchaient de marcher, et ils sont opposés.** Le prologue
> d'une fonction SH-4 est **entrelacé** avec d'autres instructions — chez Elena,
> `mov.l r14,@-r15 ; mov #0,r14 ; mov.l r13,@-r15 ; …`. S'arrêter au premier intrus rend
> une adresse **interne**, que personne ne charge : la remontée concluait « aucun chemin »
> sur des spawners dont on connaît le décor par ailleurs. On prend donc le plus ancien
> empilement d'une **grappe**.

### 5k. LES CHAUVES-SOURIS D'ORO — la ménagerie entamée

Le plus vieux trou du chantier : le catalogue des bêtes d'Oro est établi depuis longtemps
(chats, chatons, perroquet, chien, chauves-souris) mais **aucun bloc ne les portait**, et
trois enregistrements essayés au jugé avaient été rejetés à l'écran.

L'id **74**, spawner `0x8C033FC2`, n'est atteint par aucun chemin descendant. La remontée
le donne à la **bande 10 — le décor 9, Oro**. Et le spawner porte **en dur** la table de
scripts `0x8C12AB8C`, qui est celle du décor 9 : **deux chemins indépendants, la même
réponse**, et aucun n'a servi à caler l'autre.

    bloc 0x8C17F38C, 4 enregistrements de SIX octets : { x, y, palette }

Ni plan (le spawner écrit `mov #2` en dur) ni script. Le script vient de la **routine**,
qui recopie quatre pointeurs sur la pile et les indexe par le `type` de l'objet — lequel
est le rang de l'enregistrement (`mov.b r11,@(4,r4)`, r11 étant le compteur de boucle).
Les quatre routines posent les scripts **35, 34, 34, 34**, et le catalogue donne les
scripts 32 à 39 aux **chauves-souris**.

Positions : 567/288, 396/320, 502/337, 535/313 — haut dans la grotte. La routine écrit
`+102`/`+106` à chaque trame : elles se déplacent. On les pose à leur position de départ.

> **Trois bêtes disparaissaient en silence.** `objets()` écarte un script déjà vu — une
> garde utile contre les vrais doublons (les deux blocs d'Oro partagent les scripts 6, 8
> et 9) mais trop large ici : trois chauves-souris DISTINCTES jouent le script 34 à des
> places différentes. D'où la clé `doublons` sur le bloc, plutôt qu'un changement de règle
> qui aurait touché ce qui est validé.

**Ce que je n'ajoute pas.** La remontée donne aussi un spawner à Yun (id 21, trois
enregistrements, scripts 0, 2, 4). Ses champs *ressemblent* à des positions — 696/64,
752/84, 752/63 — mais sa routine **écrit** `+84`/`+86` et se contente de **lire**
`+102`/`+106` : ces objets n'ont pas de position à eux. Les poser aux valeurs qui
ressemblent serait un pari, et la ménagerie en a déjà coûté trois.

### 5l. LA MÉNAGERIE D'ORO — elle n'a AUCUN bloc

C'était la plus vieille énigme du chantier, et la réponse est qu'on cherchait une chose
qui n'existe pas. Le chat, le chien et le perroquet n'ont **pas d'enregistrement** : leur
spawner écrit `x`, `y`, `palette`, `plan` et la table de scripts en **immédiats**, et le
numéro de script est posé par la **routine** de l'objet. Trois enregistrements avaient été
essayés au jugé et rejetés à l'écran — il n'y en avait pas à trouver.

**La routine d'étage d'Oro, `0x8C0DE548` (bande 10), les appelle en clair :**

| site | id | spawner | x, y | palette | script | ce que c'est |
|---|---|---|---|---|---|---|
| `0x8C0DE5C2` | 74 | `0x8C033FC2` | *bloc* | | 35, 34×3 | les chauves-souris |
| `0x8C0DE5CE` | 55 | `0x8C030546` | 672, 114 | 86 | **20** | **le perroquet** |
| `0x8C0DE5FA` | 72 | `0x8C0338E8` | 411, 80 | 75 | **13** | **le gros chat** |
| `0x8C0DE61A` | 71 | `0x8C03369E` | 700, 56 | 74 | **29** | **le chien** |
| *par le chat* | 73 | `0x8C033ACC` | 493, 81 | 75 | **17** | **les chatons** |

**Trois attributions indépendantes concordent**, et aucune n'a servi à caler les autres :

1. **l'appelant** — la routine de la bande 10, qui est le décor 9 ;
2. **le littéral** — chaque spawner porte en dur la table de scripts `0x8C12AB8C`, celle du
   décor 9. C'est d'ailleurs en cherchant qui charge cette table qu'on les a trouvés : six
   sites, dont cinq dans des fonctions qui ne lisent **aucun** bloc — le signe ;
3. **le catalogue** — les scripts posés tombent sur la ménagerie établie il y a des jours
   par les sprites eux-mêmes : id 72 → 13 et 51 (le chat couché puis qui se redresse),
   id 71 → 29, 30, 40, 41 (le chien), id 55 → 20, 21, 26 (le perroquet).

Le script retenu est celui du **premier état** de la routine — le premier appel à
`0x8C0B4AD4` dans l'ordre des adresses. Le contrôle est les chauves-souris : la même
lecture y rend le script 35, celui qu'on avait établi à la main par un autre chemin.

> **`bsr` est relatif au PC et n'écrit aucune adresse.** Une fonction appelée ainsi
> n'apparaît nulle part dans le binaire — ni littéral, ni table. C'est le troisième chemin
> d'appel, et `remonter2i` le manquait. Il faut aussi se méfier de l'adresse d'entrée : la
> mienne était décalée de deux octets, ce qui suffisait à ne trouver aucun site.

#### C'est la mère qui fait les chatons

Aucun appelant ne menait à l'id 73, et pour cause : **il n'est pas appelé depuis la
routine d'étage**. Le spawner du **chat** le crée, en dernier geste, au site `0x8C033966`
(`jsr 0x8C033ACC`). La chatte fait ses chatons.

Leur spawner écrit tout en immédiats et porte la même table `0x8C12AB8C` : id 73, x 493,
y 81, palette 75, plan 2, script 17. **Ils sont à côté de leur mère**, qui est en 411, 80 —
un recoupement qui ne coûte rien et qui dit beaucoup.

#### La ménagerie a QUATRE variantes, et c'est `z` qui choisit

Frédéric l'a vu sur des vidéos avant qu'on le lise : *« j'ai 2 versions du décor, avec les
sprites qui changent »*. Le répartiteur est en clair dans la routine d'étage, en
`0x8C0DE5D2`, et il lit `u8[0x8C6AF30A]` — **contexte+6, le tirage `z`** :

| `z` | ce qui est créé |
|---|---|
| 0 | **le chien** seul |
| 1 | le chat + les chatons, **puis** le chien |
| 2 | le chat + les chatons, **sans** le chien (`jmp`, pas `jsr`) |
| 3 | **le chien** seul |

Le perroquet et les chauves-souris sont appelés **avant** le répartiteur : eux sont de
toutes les variantes.

**On cuit LES QUATRE, et c'est le moteur qui tire.** Chaque fiche porte un masque
`variante` — un bit par valeur de `z` — et `DecorObjets_Combien` ne compte que celles du
tirage courant :

    le chat, les chatons  -> z 1 et 2      0b0110 = 0x6
    le chien              -> z 0, 1 et 3   0b1011 = 0xB
    le perroquet, les chauves-souris, et TOUT le reste du port  ->  0xF

Le tirage se fait **une fois par étage**, pas par trame ni par round : s'il changeait en
cours de route, `DecorObjets_Combien` renverrait un autre compte entre deux appels et les
**rangs glisseraient** — or le rang est dans la clé de cache et dans l'emplacement de
palette. Les objets se dessineraient l'un à la place de l'autre.

`SF3_DECOR_VARIANTE=0..3` force le tirage ; le lanceur `ORO - les quatre variantes.cmd`
en fait un menu. Étage 31 : z 1 rend 19 objets, les trois autres 17.

> **Et le budget de motifs se compte PAR VARIANTE**, pas sur l'étage entier : le tableau
> porte les quatre, le moteur n'en montre qu'une. Additionner tout surestimerait la charge
> et ferait écarter des objets sans raison. `verifier_objets` prend la variante la plus
> chargée — pour Oro, z 1 avec 46 motifs sur 64.

> **Une observation extérieure a précédé la lecture, et elle l'a orientée juste.** C'est le
> seul cas du chantier où une vidéo a dit quelque chose que le binaire confirmait ensuite
> mot pour mot. Elle n'a servi qu'à savoir où regarder — la valeur, elle, est lue.

> **La leçon** : un objet peut être créé par un autre objet, et non par la routine
> d'étage. Une recherche qui ne remonte que jusqu'aux dix-sept routines déclare « aucun
> chemin » alors que le chemin passe par un frère. Les deux chatons *fixes*, eux, sont
> cuits depuis longtemps comme élément statique — ce sont deux choses différentes.

### 5m. L'ARBRE DES SPAWNERS DE YUN — et ce que Frédéric voyait manquer

*« Pour le décor de Yun, manquent les animations des 2 personnages devant le tram et
celles du personnage à droite qui fume et des oiseaux dans les cages à droite. »*

Ils sont tous derrière **un** spawner que la chaîne ignorait, et qui en appelle **trois
autres** — le même motif que la chatte d'Oro qui fait ses chatons :

    routine d'etage de la bande 3, site 0x8C0DC68E
       -> 0x8C02936E   id 23   x 672, y 48,  palette 90
            -> 0x8C028E62   id 21   TROIS objets, bloc 0x8C17DD58
            -> 0x8C02912C   id 22   x 712, y 56,  palette 74
            -> 0x8C02962E   id 24   x 728, y 48,  palette 91

Les six sont entre x 672 et 752 — **à droite de la bande**, ce qui recoupe la description.
Les trois spawners portent la table de scripts du décor 3 (`0x8C123DA0`) en dur.

> **`+84`/`+86` EST la position, et ça se mesure.** Le bloc de l'id 21 envoie son x et son
> y en `objet+84`/`+86` au lieu de `+102`/`+106`, et j'avais refusé de les poser pour ça —
> « des valeurs qui ressemblent à des positions » ne suffit pas. La preuve est venue des
> spawners voisins : les ids 22 et 24 écrivent **la même valeur aux deux endroits**
> (712/56 en `+84`/`+86` *et* en `+102`/`+106`). Ce n'est pas une ressemblance, c'est un
> doublon écrit par le code.

**L'état de naissance est le 0, et c'est mesuré** : aucun spawner de 2nd Impact n'écrit
`objet+36`. La règle « le premier appel au poseur dans l'ordre des adresses » qui avait
servi pour Oro est donc remplacée par la lecture du **répartiteur** — `cmp/eq #n ; bt`
sur `routine_no[0]` — qui donne l'état 0 sans dépendre de l'ordre du code.

> **Et le poseur est chargé AVANT le répartiteur.** Une branche d'état ne contient qu'un
> `jsr @rN` ; il faut amorcer le suivi du registre depuis la tête de la routine, sinon on
> ne voit aucun appel et on conclut « pas de script ».

**CE QUI RESTE FIGÉ, ET POURQUOI.** Frédéric, à l'écran : *« les 2 personnages devant le
tram et les oiseaux dans la cage ne sont pas animés »*. J'ai rendu les sprites et je les ai
regardés : le script 28 est bien **les deux personnages accroupis**, le script 7 **les
cages à oiseaux**, le script 24 **le fumeur**.

    script 28  ->  UNE image, puis la commande de fin
    script  7  ->  UNE image
    script 24  ->  SEPT images   (le fumeur, celui qui s'anime)

Les octets bruts le disent : ce n'est pas le lecteur qui tronque. **Leur animation ne vient
pas du script**, elle vient de la machine à états de leur routine, qui change de script au
fil du temps. Notre moteur joue un script en boucle — c'est une limite structurelle.

J'ai vérifié si les scripts voisins (27, 29) étaient d'autres poses du même couple, pour
les concaténer : **non**, ce sont d'autres personnages. Rien n'a été collé bout à bout.

**LA CHARRETTE ÉTAIT POSÉE DEUX FOIS.** *« Un sprite est devant lui »* : le script 2 est une
charrette de 160×112, rendue par le 2ᵉ enregistrement de l'id 21 (bx 576) **et** par l'id 22
(bx 536). Le fumeur est en bx 728 : la première s'étale jusqu'à 736 et le recouvre, la
seconde s'arrête à 696. On garde la seconde.

> **C'est un ARBITRAGE, pas une lecture**, et il faut que ça se voie : les deux
> enregistrements existent dans le binaire et je n'ai pas su établir lequel le jeu emploie.
> Ce qui est mesuré, c'est que l'une recouvre le fumeur et l'autre non.

**Un bloc reste dehors** : `0x8C02942E` lit trois enregistrements (scripts 8, 9, 11 — dix,
trois et sept images, en 752/104, 752/96 et 672/80), et **rien ne l'appelle** — ni
littéral, ni `bsr`, ni table, sur tout le binaire.

### 5n. RYU — deux hypothèses fermées

**Il ne manque pas d'objets.** En descendant tout l'arbre de ses spawners, aucun bloc qu'on
n'exploite déjà. Ses treize objets sont posés.

**Son `x` est compté depuis le MILIEU de la bande — résolu le 03/09.** Sept de ses treize
objets ont un `x` négatif — il est le seul décor dans ce cas — et l'enroulement `& 0x3FF`
les renvoyait à droite :

| script | x brut | posé en |
|---|---|---|
| 1 | −368 | 641 |
| 5 | −128 | 817 |
| 10 | −145 | 832 |
| 14 | −233 | 760 |
| 4 | −288 | 689 |
| 7 | −96 | 897 |
| 8 | −112 | 881 |

Deux pistes fermées avant la bonne :

* `SANS-ETAT.md` soupçonnait qu'« un décalage de contexte s'ajoute — le chargeur générique
  fait `objet[+102] += parent[+102]` ». **Aucun des quatre chargeurs de Ryu n'ajoute quoi
  que ce soit à `+102`**, et le détecteur trouve bien l'addition dans `0x8C02AA7C`, le
  chargeur témoin qui, lui, décale ;
* **aucun de ses objets n'est peint dans la banque du disque** — zéro sur treize. La
  mesure qui avait redressé l'édifice d'Oro n'existe pas chez lui.

#### La mesure qui tranche : le décor sert de réglet

Frédéric a fourni deux captures de l'original à deux positions de caméra. Le **décor** y
donne l'échelle — le panneau 湯, le parasol, la lanterne de pierre situent la caméra — et
cinq objets identifiés s'y relèvent :

| objet | `x` signé | bande mesurée | écart |
|---|---|---|---|
| les singes | −233 | 230 | 463 |
| la femme au panneau | −145 | 325 | 470 |
| la femme en rose | −112 | 371 | 483 |
| le gros baigneur | **+273** | 810 | 537 |
| le singe de droite | **+336** | 857 | 521 |

**Un écart constant d'environ 512, et il vaut pour les positifs comme pour les négatifs.**
Ce n'est donc pas une correction de l'enroulement : c'est une **origine**. 512 est le
milieu de la bande, et c'est le littéral que les dix-sept plans portent en `+26`.

Écart résiduel après correction : 2, 5, 9, 18 et 25 pixels — la précision de relevés faits
à l'œil sur une capture, pas celle de la donnée. `animer2i.DECALAGE_X` porte la constante.

> **C'est la première fois qu'une référence extérieure cale la chaîne**, et `BILAN.md` la
> réclamait depuis le 01/09 : « rendre le décor complet et le comparer à une capture, une
> fois pour toutes ». Elle ne vaut que pour Ryu tant qu'un autre décor ne l'a pas demandée
> — sur les 93 objets des quatorze décors, **seuls ses sept** changent de place, les autres
> ayant tous un `x` positif.

Ce qui a changé chez lui : sa **banque de palettes basse**, offsets 0..5 → **1625** au lieu
de 989 (§3b). Le détecteur de vert est muet sur ce groupe, mais la destination contiguë et
le nombre de palettes le désignent, et c'est la valeur que les documents donnent depuis le
30/08 sans l'avoir appliquée.

### 5o. UN ENREGISTREMENT PORTE DEUX SCRIPTS — repos et action

C'est la cause de « *les 2 personnages devant le tram et les oiseaux dans la cage ne sont
pas animés* », et elle tient en un champ qu'on ne lisait pas.

Les blocs du chargeur `0x8C028792` (id 18) ont un champ de plus, deux octets après le
script : il part en `objet+152` quand le premier part en `+150`, et **il vaut toujours le
premier plus un**. C'est une paire **(repos, action)** que la routine alterne :

| décor | repos `+150` | action `+152` |
|---|---|---|
| Yun | 32 — **zéro image** | **33** — 12 images (le vieil homme au panier) |
| Yun | 30 — **zéro image** | **31** — 12 images (la femme en rose) |
| Yun | 21 — zéro image | 22 — 24 images |
| Dudley | 2 — une image | 3 — 9 images (le monsieur à la canne) |
| Hugo | 7 — 10 images | 8 — 19 images |
| Sean | 8 — 3 images | 9 — 8 images |
| Ryu, Necro | *le repos est déjà le plus riche* | inchangés |

On posait le **repos**. Notre moteur ne jouant qu'un script, on prend désormais **le plus
riche des deux** (`sc2` dans `animer2i.TABLES`).

> **Et la capture a servi à ça, pas à mesurer.** Frédéric a montré les deux personnages ;
> j'ai rendu les 45 sprites de Yun (`outils/planche_scripts.py`) pour les identifier —
> scripts 33 et 31 — puis j'ai lu le binaire. L'image dit *où regarder*, jamais *quoi
> écrire*.

**Et ils vivent dans la variante `z` 1/3**, qu'on ne cuisait pas : `0x8C028792` arg 2 a deux
blocs distincts, `0x8C17DBC0` (z 0 et 2) et `0x8C17DBF0` (z 1 et 3). Les deux sont
maintenant cuits avec leur masque, comme la ménagerie d'Oro.

**Dudley** gagne aussi un **punk au skateboard** : sa routine d'étage appelle `0x8C032B32`
(site `0x8C0DCD62`, argument 0), un spawner à immédiats jamais exploité — id 68, x 672,
y 47, palette 75, script 6.

**Ce qui reste chez lui** : les deux autres punks (scripts 5, 7, 10) — rien dans son arbre
ne les crée ; et la **phase orange du feu**, qui n'est pas une image du script 0 (sept
images, verte à la première) mais sans doute un autre état de sa routine.

> **Les deux corrigés le 04/09**, par la mesure du §5p. Le **feu a bien sa phase orange** :
> c'est l'**image 3** du script 0 — la vignette la montre jaune. Et les « deux autres
> punks » n'en font qu'un : les scripts **6 et 7 sont le même personnage** (leur image 7
> est identique au pixel près), et le troisième punk, celui au blouson Union Jack, est le
> **script 10** — **peint** en 736,879 à 99 %, une seule image, donc statique de droit.

### 5p. LA PAGE ASSEMBLÉE EST UN RÉGLET — et la banque brute n'en est pas un

**Un personnage animé est souvent AUSSI peint dans le décor**, à l'arrêt, à sa place
exacte : l'objet est censé le recouvrir. Sa position y est donc une **mesure**, en
coordonnées de bande, qui ne dépend ni de la caméra ni d'une capture.

**LE PIÈGE, ET IL A COÛTÉ UNE DEMI-JOURNÉE.** `situer_animes.pages()` cherche par défaut
dans la **banque du disque** — et là, la figure est éclatée en tuiles : elle n'apparaît
nulle part d'un seul tenant, et la recherche rend **zéro sur treize**. On en avait conclu,
pour Ryu comme pour Yun, qu'« aucun de leurs objets n'est peint ». C'était faux : il faut
chercher dans la **PAGE ASSEMBLÉE** (`poser2i.lire_liste`), où elle est contiguë.

La circularité que redoutait le docstring de `situer_animes` ne joue que pour ce que *nous*
avons cuit dans la page ; l'art qui vient du disque, lui, est une référence légitime.

Ce que ça donne chez Yun — et les cinq premiers **valident la formule** :

| script | posé en | peint en | |
|---|---|---|---|
| 6, 16, 26 | 303, 288, 208 | idem | **100 %** |
| 7 | 672 | 672 | 97 % |
| 28 | 320 | 320 | 90 % |
| 33 — le vieil homme | 480 | 480 | 84 % au balayage |
| 31 — la femme en rose | 496 | 496 | **69 %** — trop bas pour conclure |

#### UNE MESURE PAR ANCRE N'EST PAS UNE MESURE — et ça a coûté une régression

`situer_animes.chercher` trouve sa pose par un **pixel d'ancre** : le plus rare de l'image.
C'est rapide, et ça n'a de sens **que si l'objet est peint à l'identique**. Dès que la
figure peinte diffère un peu de la nôtre — autre trame, autre palette — l'ancre tombe sur
un pixel isolé et rend une position qui n'est pas la bonne.

L'ancre disait la femme en rose peinte en **512** ; j'ai déplacé l'objet de seize pixels.
Un **balayage complet**, qui compte les pixels identiques à chaque décalage, dit **496** —
sa position calculée. Frédéric a vu la régression aussitôt : *« Yun, c'est pire »*.
Annulé.

> **LA RÈGLE : on ne déplace un objet que sur un accord FRANC, mesuré par balayage.**
> En dessous de ~90 %, la figure peinte n'est pas la nôtre et ne dit rien de sa place.

Trois hypothèses restent **fermées**, et il faut les laisser fermées : ce n'est ni une
fuite du filtre de variantes (les masques 0x5 et 0xA s'excluent, et le filtre est juste des
deux côtés), ni un script posé deux fois (aucun doublon sur les quatorze), ni une page
cuite périmée (recuire Yun ne change **aucun** pixel, et les `.tex` déployés sont
identiques au bit près à ceux du dossier de travail).

**Et `MESURE` écrasait le décalage des morceaux** : elle rendait le même `bx` à toutes les
tranches d'un objet découpé, qui se seraient superposées. Elle ajoute maintenant
`col0 * 16`.

### 5r. `rendu_fiches.py` — rendre l'étage DEPUIS LE C, tuiles comprises

`apercu_etage.py` relit les positions dans `decor_objets_data.c` mais redessine les images
depuis les sprites du disque : il reste une hypothèse entre lui et le jeu. **`rendu_fiches.py`
n'en fait aucune** — il décode les 256 octets de chaque `DecorTuile`, les dépose à la case
que le moteur en déduit, et colore avec la palette de la fiche. C'est ce que le jeu
téléverse.

C'est lui qui a montré que **nos données sont justes** chez Yun : un seul vieil homme, une
seule femme, à leur place. Le doublement vient de ce que le décor **peint déjà** ces
personnages et que l'objet ne les recouvre qu'à 84 % et 69 %.

Deux pièges de format, mesurés :

* l'entrelacement s'inverse par **indexation directe par `TABLE`** (`plat[k] = out[TABLE[k]]`),
  pas par la permutation inverse — celle-ci rend des rayures ;
* le `y` d'une `DecorTuile` est en **repère image** (`lig * 16`), pas en repère moteur :
  c'est le moteur qui le retourne au moment de chercher, `y_moteur` étant une involution.
  Le retourner à la lecture sort l'objet en tranches empilées à l'envers.

Le journal du jeu (`decor-objets.log`) recoupe le tout : vingt objets marqués pour Yun, aux
`x`/`y`/`famille`/`z` exacts des fiches.

### 5q. `Z_OBJET` — départager deux objets d'un même plan

`Z` donne la profondeur d'un **plan** ; elle ne peut rien quand deux objets le partagent.
Ils reçoivent alors tous deux le 0 qui veut dire « garde celle du modèle » (80), et l'ordre
de rendu ne tient plus qu'à leur rang dans la fiche. `Z_OBJET[decor][script]` force la
profondeur d'un objet nommé — **un `z` plus petit est plus près**.

Premier emploi : les deux punks de Dudley se chevauchent sur 48 pixels (672‑768 et
720‑784), et Frédéric a relevé sur l'original que **celui de gauche passe devant**. C'est
une observation de sa part, pas une lecture du binaire, et c'est écrit tel quel dans la
table.

### 5s. LES TABLES DES CHARGEURS — retrouvées par leurs littéraux

`spawners2i.analyser` rend souvent « nombres u16 [?] » ou « bloc EN DUR a [0 + arg*4] » :
l'interpréteur symbolique perd la **base** de la table. Elle est pourtant dans la fonction,
parmi ses littéraux — et la forme est constante :

| | nombres | pointeurs | enregistrement |
|---|---|---|---|
| `8C0233B6` | `8C17B918` | `8C5F9C04` | 16 o |
| `8C02356A` | `8C17BBC4` | `8C5F9CD0` | 16 o |
| `8C028792` | `8C17DB38` | `8C5F9E24` | 24 o |
| `8C025A9A` | `8C17C1F8` | `8C5F9DF8` | 16 o |
| `8C02E1FE` | `8C17E794` | `8C5F9F64` | 16 o |

Une base en `0x8C17xxxx` pour les nombres, une en `0x8C5F9xxx` pour les pointeurs. Deux
indexations coexistent : `nombres[arg*8 + z*2]` / `pointeurs[arg*16 + z*4]` (quatre
variantes de `z` par argument) pour les trois premiers, et `nombres[arg*2]` /
`pointeurs[arg*4]` pour les deux derniers.

**ET L'ARGUMENT N'EST PAS LE DÉCOR** : c'est un index compact sur les décors qui emploient
ce chargeur, différent d'un chargeur à l'autre. Il se lit au site d'appel (`chargeurs2i.appels`),
jamais ne se déduit.

> **UNE INDEXATION QUI « MARCHE » NE PROUVE RIEN.** Il faut une contre-épreuve extérieure :
> `8C0233B6` arg 2 rend exactement les quatre éléments statiques de Yun (383,32 / 413,69 /
> 479,64 / 576,64) que `poser2i` cuit déjà ; `8C02356A` arg 3 rend le punk Union Jack de
> Dudley en x 736, position mesurée au balayage à 99 % ; `8C025A9A` arg 1 et `8C02E1FE`
> arg 1 rendent les quatre premiers objets de Yun déjà posés, au pixel près.

**Ce que ça a donné.** `8C02356A` était le seul vraiment inexploité chez Yun : il porte le
**panneau vertical en x 852** (palette 23) — que trois corrections successives avaient
cherché en vain — et remet les paniers en 640 au lieu de 752. Les deux derniers,
`8C025A9A` et `8C02E1FE`, étaient **déjà exploités** sous les adresses `0x8C17C230` et
`0x8C17E808` de `TABLES` : chacune vaut son pointeur + 2.

#### L'ENREGISTREMENT EST LE MÊME PARTOUT — et il commence AU pointeur

J'ai d'abord cru que ces deux chargeurs décalaient leurs enregistrements de deux octets et
que le modèle « sortait du bruit » sur la moitié des décors. **Les deux étaient faux**, et
la cause de l'un comme de l'autre est la même : une liste de champs à sept entrées, gardée
d'une sonde précédente, à laquelle manquait le premier mot (`+32`). Les mots bruts le
montrent d'un coup d'œil, et ils sont uniformes sur les seize décors :

```
word0  0001/0000  -> +32          word4  y
word1  0002       -> +558 plan    word5  palette
word2  2040/2055  -> +554 drap.   word6  script
word3  x                          word7  0000 -> +118
```

**Une fois l'alignement juste, 30 enregistrements sur 36 décodent, et 12 objets nouveaux
apparaissent** (décors 9, 10 et 16). Les six restants ne sont pas des échecs du modèle :

* **cinq sont Ryu (décor 2), et leur `x` est NÉGATIF** — −368, −288, −233, −145, −128.
  C'est la propriété établie le 03/09 : Ryu est le seul décor dont les `x` sont comptés
  depuis le milieu de la bande. Mon épreuve de validité refusait tout `x` ≥ 1024, c'est-à-dire
  le complément à deux. Recoupement : le `script 14 en x −233` est celui des **singes**,
  relevé au même chiffre sur la capture Flycast. Voir la table de `DECALAGE_X` ;
* **un est la bande 11**, qui demande les scripts 68 et 61 alors que le décor 11 n'en a que
  6. Ce n'est pas le modèle : c'est que **la bande 11 n'a pas de décor identifié** — la
  correspondance de `chargeurs2i` s'arrête à bg10 = 16. L'index de `0x8C1D3FB4` est la
  bande, pas le décor.

> LA LEÇON, et elle vaut au-delà d'ici : **une épreuve de validité qui rejette écarte aussi
> ce qu'on n'a pas prévu.** Ici elle a masqué la seule propriété déjà connue et documentée
> du chantier. Toujours réafficher ce qu'une épreuve refuse, au lieu de compter les échecs.

### 5t. LA PROFONDEUR EST `+556`, ET ELLE VAUT LE NUMÉRO DE PALETTE

J'avais écrit ici que « aucun chargeur n'écrit la profondeur ». **C'était faux deux fois** :
je l'avais cherchée à `+76`, offset calculé dans une structure du port de 140 octets qui
n'a rien à voir avec l'objet de 2I.

**L'ancre qui nomme tout** : les trois spawners à immédiats de Yun écrivent `0x4200` en
`+552` — exactement la constante que `eff05.c` pose dans `my_col_mode`. En alignant les
deux, les champs suivants se nomment seuls, et `charid.c` le confirme une troisième fois :
il pose `my_col_mode`, `my_col_code`, `my_priority`, `my_family` **dans cet ordre**.

| offset 2I | champ | valeur chez Yun |
|---|---|---|
| `+552` | `my_col_mode` | `0x4200` |
| `+554` | `my_col_code` | `0x2040` / `0x2055` |
| **`+556`** | **`my_priority`** | 90 cages, 91 fumeur, 74 charrette |
| `+558` | `my_family` | 2 |

**ET `my_priority` EST LE NUMÉRO DE PALETTE.** Lu dans le code, sur deux chargeurs
différents : `+88` et `+556` sont alimentés par **le même registre**, en écritures
consécutives.

```
8C02936E   +556 <- r1        8C02356A   +88  <- r3
           +88  <- r1                   +556 <- r3
```

La profondeur de chaque objet du chantier est donc une donnée qu'on lit déjà partout.

**L'ÉCHELLE, pour savoir à quoi la comparer** : `char_init_data2` donne aux combattants un
`my_pr` de **0x1C à 0x38, soit 28 à 56** — et un `my_col_mode` de `0x4200`, comme nos
objets. Les plans de fond sont à 84, 90 et 94. Un objet à 23 — le panneau vertical de Yun —
passe donc **devant les combattants**, ce que Frédéric avait relevé à l'écran.

### 5u. `champs2i.py` — la carte complète, bloc ET constantes

Un chargeur remplit son objet de deux façons, et deux outils n'en voyaient chacun que la
moitié. `champs2i.py` les réunit et dit, pour chaque offset, s'il vient d'un enregistrement
(avec son octet) ou d'une constante (avec sa valeur).

Ce que la carte incomplète coûtait, mesuré sur les **97 fonctions** atteintes par une
routine d'étage — dont **seules 16 lisent un bloc** :

| offset | absent de la carte de |
|---|---|
| `+364` | 16 chargeurs sur 16 |
| `+556` `my_priority` | **12 sur 16** |
| `+552`, `+6`, `+8` | 15 sur 16 |
| `+554`, `+558` | 6 et 5 |

> **Piège de `immediats2i`** : une lecture mémoire détruit la constante d'un registre. Sans
> ce traitement, l'outil annonçait `0x17E4` comme `my_priority` de `8C02356A` — le bas de
> l'adresse de l'allocateur, restée dans le registre.

### 5v. LA BANDE N'EST PAS LE DÉCOR — et la bande 11 est le décor 10

Le tableau `bande_vers_decor` n'a **aucun trou** : 0→0 … 8→8, **9→8**, 10→9, **11→10**,
12→11, 13→12, 14→13, 15→14, 16→16. J'avais conclu qu'un enregistrement était invalide
parce qu'il demandait les scripts 68 et 61 « pour le décor 11, qui n'en a que 6 » : la
bande 11 est le décor **10**, qui en a 93. Le modèle marche partout.

### 5w. LES « COPIES » SONT NOTRE CUISSON — le disque ne les contient pas

Frédéric a signalé cinq fois des copies fixes du vieil homme et de la dame en rose, sous
leurs sprites animés. J'ai cherché la cause partout sauf au bon endroit : dans une carte de
tuiles que 2I n'a pas, dans une position d'objet qui était juste, dans un filtre de
variantes qui marchait.

**La mesure qui tranche** : on compare la demi-banque BRUTE du disque à notre page cuite.

```
banque 0 bas    la scène SANS le vieil homme ni la dame
page 196        la même scène AVEC les deux, peints dedans
40 660 pixels de différence, colonnes 128-463, 480-575, 624-783
```

480 et 512, ce sont exactement leurs positions. **C'est `poser2i` qui les cuit** comme
éléments statiques, alors que le jeu les crée comme objets animés. On les peignait, puis on
posait l'objet par-dessus : d'où deux figures dès que l'animation s'écarte de la pose
peinte.

Contrôle complémentaire, image par image : notre objet ne peint **jamais** un pixel hors de
la figure (`forme+` = 0 sur les douze images) ; tout l'écart est de couleur, et il croît
avec la trame — 108 pixels à l'image 1, 2381 à l'image 5. C'est l'animation, pas un
décalage.

> **La règle qui en sort** : un script que le CODE pose comme objet animé ne doit jamais
> être cuit comme élément statique. Les deux chemins doivent se partager la liste des
> scripts, pas l'ignorer chacun de son côté.

#### LE CORRECTIF, ET LA FAUSSE PISTE QU'IL A FALLU DÉFAIRE

`poser2i` fait maintenant deux choses, et la seconde est celle qui compte :

1. il **n'écrit plus** un élément dont le script est posé par `animer2i` (`scripts_animes`,
   import tardif — `animer2i` importe ce module) ;
2. il **rend la banque nue sous l'empreinte de chaque objet animé**, lue dans le C
   **compilé**, donc exactement la surface que le moteur va recouvrir.

Le point 2 est indispensable : les figures que Frédéric voyait en double avaient été cuites
par une passe **antérieure**, avec un annuaire qui comptait plus d'éléments. Rien dans la
liste d'aujourd'hui ne les efface.

**Ma première version repartait de la banque pour toute la page** (`--refaire`). Elle
effaçait alors ce qu'une cuisson ancienne avait posé et qu'**aucun objet ne remplace** —
Frédéric l'a arrêtée d'une phrase : « il est évident que si un élément cuit et qu'aucun
objet ne le pose, il faut le garder ». On n'efface donc que des empreintes.

**Le contrôle qui rend la chose sûre** : sur Yun, 27 448 pixels changent, et **les 27 448
rendent exactement la banque du disque, zéro va ailleurs**. Rendre la banque ne peut pas
créer de trou — on y remet le contenu de l'original, jamais du vide.

### 5x. `etats2i.py` — la machine à états d'un objet

Un objet ne joue pas un script : sa **routine** en enchaîne plusieurs. `objet+36` est son
`routine_no`, et aucun spawner ne l'écrit — tout objet naît donc dans l'état 0. L'outil
relève, dans la routine que l'`id` désigne dans `0x8C179FDC` et dans ce qu'elle appelle,
les appels au poseur `0x8C0B4AD4` (`r6` = le script) et les écritures d'une constante en
`+36`.

Premier résultat, chez Yun : l'**id 23** — les cages — enchaîne **7 → 12 → 34**. Le script
7 est la cage intacte (une image), le **12 est la cage qui se brise** (treize images), le
34 est vide. Notre moteur, qui joue un seul script en boucle, ne montrera jamais la
destruction.

#### LES OISEAUX N'ANIMENT PAS LA CAGE INTACTE — ils s'en échappent

La planche des 45 scripts de Yun les montre : **37** est un oiseau en vol (2 images), **42**
et **44** des oiseaux posés (4 et 8 images). Et le reste du décor de la cage est là aussi :
**8** la cage ronde qui roule (10 images), **9** la cage écrasée (3), **11**, **36**, **38**,
**40** les barreaux qui tombent.

L'id 23 a un **second spawner**, `0x8C02942E`, que rien n'exploitait : même `my_priority` 90
et même `my_col_code` que les cages, un bloc en dur à `0x8C17DDA8`, trois enregistrements —
scripts **8** en 752,104, **9** en 752,96 et **11** en 672,80 — avec des champs `+134 =
0x8000` et `+136 = 0xFFFF` qui ont tout d'une vitesse. Ce sont les **débris projetés**.

Les oiseaux eux-mêmes viennent des ids **82** (`8C035940`, script 42) et **97**
(`8C03852E`, scripts 44 et 45), et `remonter2i` est formel : **aucune routine d'étage ne les
atteint**. Ils sont créés par la routine d'un autre objet.

> **Donc il n'y a pas d'oiseaux animés dans la cage intacte.** Toute cette machinerie est
> celle d'un décor DESTRUCTIBLE : intacte (7) → frappée → elle éclate (12) → les débris
> volent (8, 9, 11) → les oiseaux s'échappent (37, 42, 44). Le script 7 n'a qu'une image
> pour cette raison, et non parce qu'il nous manquerait une animation.

> Pour lire l'`id`, il a fallu passer `immediats2i` en **deux passes** : la base de l'objet
> se reconnaît à un `@(r0,rN)` dont le `r0` est un offset connu, donc tout ce qui s'écrit
> AVANT ce premier repère était perdu — et `+6` comme `+8` s'écrivent en tête.

### 5y. LE « DÉJÀ VU » ÉTAIT PARTAGÉ ENTRE LES BANDES — 97 fonctions au lieu de 553

La faute la plus coûteuse de l'inventaire, et elle tenait à une ligne. `toutes_les_fonctions`
marchait dans l'arbre d'appels de chaque routine d'étage avec **un seul ensemble « déjà
vu »**, partagé entre toutes les bandes. Or les cinq gros chargeurs servent de huit à
quatorze décors chacun : **le premier décor qui atteignait `8C028792` se l'appropriait, et
tous les autres le perdaient.**

Sean (bande 13) se retrouvait ainsi avec trois fonctions atteintes, aucune n'écrivant un
champ d'objet — alors que ses trois objets viennent précisément de ce chargeur.

En rendant l'ensemble local à chaque bande : **553 fonctions au lieu de 97**, un facteur
5,7. Toutes les mesures « sur les 97 fonctions » d'avant cette correction sont à refaire.

> **La règle** : un ensemble « déjà vu » ne se partage jamais entre deux parcours qui
> répondent à des questions différentes. Ici la question était « que ce décor atteint-il »,
> et la réponse dépend du décor.

### 5z. LE BALAYAGE DES ONZE DÉCORS, ET CE QU'IL A TROUVÉ

`transfert2i.py --tous` passe chaque décor aux douze portes. Ce que la première passe
complète a corrigé :

* **96 000 pixels de cuisson** retirés sous des sprites animés, sur huit décors — dont
  **51 239 pour `bg0b`** et 6 191 pour Oro, que personne n'avait signalés ;
* **quatre décors ne recevaient aucun nettoyage** (`bg07`, `bg09`, `bg0a`, `bg0f`) : ils
  n'ont pas d'élément dans l'annuaire, et la boucle sortait avant le nettoyage. Or leurs
  objets sont bel et bien posés ;
* **`bg08` n'était jamais nettoyé** : `poser2i` appelle son étage `bg09` et les fiches
  l'appellent `bg08`. On apparie désormais par **étage**, qui est sans ambiguïté ;
* **Oro perdait un objet** : son bloc `0x8C17DCFA` n'avait pas `sc2`, donc on lisait le
  repos (script 15, **zéro image**) au lieu de l'action (script 16, deux images) ;
* une porte trop large — elle exigeait une carte de champs de **toute** fonction atteinte,
  y compris les vingt-cinq utilitaires du moteur (zone `0x8C0E`-`0x8C11`) qui ne voient
  jamais un objet. Elle ne la demande plus qu'à celles qui **allouent** (`8C0217E4`) ou
  **posent un script** (`8C0B4AD4`).

**Les onze décors passent maintenant les douze portes.**

> Un piège de comparaison, noté pour ne pas y retomber : « le code donne ce script et la
> chaîne ne le pose pas » compte à tort **l'autre moitié d'une paire repos/action**. Sur
> sept écarts relevés, six étaient de ce type — un seul était un vrai manque.

### 5f. Découper un magasin d'images

La méthode, et elle est automatisable : les vignettes d'une même animation ont un **écart
mutuel** très inférieur à celui de deux découpes au hasard du même bloc. Mesuré chez
Akuma : 0,6 à 1,1 contre ~70 — un facteur soixante-dix. La corrélation, elle, ne sert à
rien : les trames ne sont pas peintes dans le plan, leur emplacement y est vide.

**Une demi-banque peut être trois choses** : une couche, un magasin à part (Akuma), ou une
couche qui garde sa réserve hors champ (Ibuki). Le tri se fait sur les **destinations**,
pas sur l'aspect.

---

## 6. LES DONNÉES VALIDÉES, DÉCOR PAR DÉCOR (2nd Impact)

Régénérable : `python outils/inventaire.py` écrit `DONNEES-2I.json`.
`python outils/banques2i.py` refait la colonne des palettes.

| décor | bande | étage | asset | sprites | scripts résolus | éléments j1+j2 | base HAUTE | banque BASSE | objets posés / fiches |
|---|---|---|---|---|---|---|---|---|---|
| `bg00` Gill | 0 | 22 | F_ETC41 | 59 | 12 / 13 | 3 + 0 | 827 (48) | — | 7 / 7 |
| `bg01` Alex | 1 | 23 | F_ETC34 | 6 | 4 / 4 | 2 + 0 | 927 (31) | — | 1 / 1 |
| `bg02` Ryu | 2 | 24 | F_ETC25 | 125 | 24 / 24 | 2 + 3 | 989 (27) | **1625** (0..5) | 13 / 14 |
| `bg03` Yun | 3 | 25 | F_ETC26 | 239 | 38 / 38 | 4 + 5 | 1043 (21) | **1631** (0..6) | 14 / 22 |
| `bg04` Dudley | 4 | 26 | F_ETC32 | 80 | 11 / 11 | 2 + 2 | 1117 (26) | **1641** (0..5) | 5 / 5 |
| `bg05` Necro | 5 | 27 | F_ETC28 | 303 | 39 / 39 | 3 + 2 | 1169 (25) | — | 17 / 17 |
| `bg06` Hugo | 6 | 28 | F_ETC29 | 223 | 36 / 36 | 2 + 4 | 1219 (35) | **1652** (0..11) | 9 / 13 |
| `bg07` Ibuki | 7 | 29 | — | — | — | — | 1289 (15) | — | pages : 9 |
| `bg08` Elena | 8 | 30 | F_ETC30 | 131 | 32 / 32 | 0 + 9 | 1319 (23) | — | 4 / 22 |
| `bg0a` Oro | 10 | 31 | F_ETC33 | 272 | 51 / 52 | 0 + 1 | 1429 (24) | **1674** (0..3) | 16 / 19 |
| `bg0b` Yang | 11 | 32 | F_ETC27 | 602 | 93 / 93 | 2 + 3 | 1085 (16) | — | 5 / 18 |
| `bg0c` Ken | 12 | 33 | F_ETC24 | 6 | 5 / 6 | 5 + 0 | 1477 (21) | — | 0 / 0 |
| `bg0d` Sean | 13 | 34 | F_ETC35 | 50 | 10 / 10 | 2 + 3 | 1519 (33) | — | 3 / 3 |
| `bg0e` Urien | 14 | 35 | F_ETC94 | 3 | 1 / 58 | 1 + 0 | 1607 (8) | — | 0 / 0 |
| `bg0f` Akuma | 15 | 36 | — | — | — | — | 2144 (15) | — | pages : 9 |
| `bg10` Hugo bis | 16 | 57 | F_ETC29 | 223 | 36 / 36 | 2 + 4 | 1219 (35) | **1652** (0..11) | — |

*En italique* : mesuré, non appliqué — le détecteur est muet sur ces deux-là (zéro vert des
deux côtés) et rien n'a été signalé à l'écran. La règle du §3b les désigne pourtant.

**Ken et Urien n'ont aucun bloc d'objets** : les objets qu'on leur prêtait venaient du
décalage bande/décor.

### New Generation

19 bandes → étages **37 + bande**, soit 37 à 55. La bande 19 est `SELECT`, pas un décor.
Le détail est dans `outils/ng_blocs.json` : 14 décors, 91 blocs à chargeur (213
enregistrements), 232 éléments, et les noms des bandes lus dans le binaire.

**Rien de NG n'a été éprouvé à l'écran côté couleurs** : la chaîne est complète *dans les
termes du binaire de NG*, la conversion vers la numérotation du portage reste à valider.

---

## 7. CE QUI RESTE — chiffré, dans l'ordre

1. **L'attribution des blocs restants.** 392 scripts se résolvent, 94 objets sont posés.
   Les trois lecteurs sont lus (§5e, §5g) ; ce qui reste :
   * **`0x8C02C68A`** (`bg10`) — son indexation n'est pas résolue par l'interprète ;
   * les **vingt spawners à bloc que même la remontée n'atteint pas** (§5j) : soit ils
     appartiennent à des écrans hors combat, soit leur appelant passe par un registre ;
   * **Yun id 21** — trois objets dont la position vient d'ailleurs (§5k) ;
   * le **quatrième objet d'Elena**, écarté faute de place dans la collection de motifs ;
   * les **variantes `z`** : deux sprites de Hugo (scripts 5 et 13) ne sont jamais vus
     (§5i) — c'est mesuré, et assumé.
2. **Le second jeu d'éléments** — 26 éléments jamais posés ; `poser2i` ne lit que le jeu 1.
   Chez Elena c'est 9 éléments sur 9, chez Sean 3 sur 5.
3. **La ménagerie d'Oro** — 51 scripts résolus, 8 objets posés. Le catalogue des bêtes est
   établi (chat, chatons, perroquet, chien, chauves-souris) ; **c'est leur bloc qui manque**,
   et il ne se trouvera pas par `resout()`.
4. **La position verticale du plan** — la voiture et le conducteur de Sean sont peints dans
   la banque et pourtant trop hauts. Reste à décompiler le code de fond `bg00xx`.
5. **Une référence vérifiable par décor.** La chaîne de position n'est validée que sur
   `bg00`, et le test « l'élément est-il peint là où on le calcule » rend **0/30** ailleurs.
   Tant que ça dure, toute correction de hauteur est un tâtonnement.
6. **Les magasins d'images de NG** — onze animations de pages, aucune découpée.
7. **`assemblage.py` pour NG** — le format des `.pk` et le chemin script → image.
8. **Les variantes d'aire** des décors 6, 8 et 16 : quatre étages de plus, déjà mesurées.
9. **PORTER LA MACHINE À ÉTATS DANS LE MOTEUR** — chantier de MOTEUR, pas d'extraction, et
   **ce n'est pas la priorité**. Notre `DecorAnimation` joue UN script en boucle ; le jeu,
   lui, en enchaîne plusieurs par objet. Trois comportements en dépendent, et les trois sont
   déjà lus dans le code (§5x) :
   * **les objets qui se brisent au contact** — 14 routines sur 196 posent plusieurs
     scripts. Chez Yun : la charrette (0, 1, 2), les cages (7, 12, 34) et le fumeur
     (23, 24), dont on ne pose qu'un ;
   * **les débris projetés** — l'id 23 a un second spawner, `0x8C02942E`, bloc `0x8C17DDA8`,
     trois enregistrements avec des champs `+134 = 0x8000` et `+136 = 0xFFFF` qui ont tout
     d'une vitesse ; et les oiseaux qui s'échappent (ids 82 et 97, scripts 42, 44, 45) ;
   * **les regards qui suivent les combattants** — signature : la routine lit `0x8C69D314`
     ou `0x8C69D32E`, deux champs distants de 26 octets, les deux joueurs. **80 routines
     sur 196** les lisent. Contre-épreuve : les deux routines des acolytes de Gill (ids 11
     et 184), dont on savait déjà que les images sont des orientations, en font partie.

---

## 8. LES OUTILS, ET LEUR ORDRE

Python : `C:/Users/frede/AppData/Local/Python/pythoncore-3.14-64/python.exe`
(`python` seul est un stub du Store qui ne rend rien.)

### Inventaire — à lancer AVANT toute correction

```
inventaire.py             écrit DONNEES-2I.json depuis le binaire
banques2i.py              les banques de palettes, et laquelle pour quels offsets
spawners2i.py             les spawners dedies : format, tables, indexation, nb de tours
remonter2i.py             le graphe d'appels A L'ENVERS : qui atteint cette fonction
effets2i.py               les 196 routines d'effet : qui fabrique un objet de decor
planches.py animes 2i     les sprites animés, par étage
planches.py stages 2i     les plans de chaque étage
planches.py assets        TOUS les sprites de chaque asset, numérotés
chargeurs2i.py            l'attribution des blocs par l'appelant
blocsng.py / decorsng.py  idem pour New Generation
planche_scripts.py        tous les scripts d'un décor, pour IDENTIFIER qui est qui
apercu_etage.py           l'étage rendu, objets compris, sans lancer le jeu
```

**`apercu_etage.py` est la vérification la moins chère qui existe** : il relit les fiches
dans `decor_objets_data.c` — donc ce qui est *compilé*, pas ce que le générateur croit
avoir écrit — et compose l'étage. Il prend `APERCU_BG`, `APERCU_DECOR`, `APERCU_ETAGE`,
`APERCU_LISTES` (les listes varient d'un étage à l'autre : Yun n'a que 132 et 196, Oro en a
trois) et `APERCU_VARIANTE` (0 à 3, ou −1 pour tout superposer).

> Deux défauts corrigés le 04/09, tous deux **silencieux** : son expression comptait les
> champs de la fiche et a cessé de coller le jour où `variante` s'y est ajouté — il rendait
> alors un étage *sans aucun objet*, comme s'il n'en avait pas ; et il redessinait le
> sprite **entier** à chaque morceau d'un objet découpé, ce qui faisait voir en double des
> objets qui ne l'étaient pas. C'est ce faux doublon qui m'a fait chercher longtemps du
> mauvais côté.

### Génération — **l'ordre compte**

```
etages.py --ecrire        etagesng.py --ecrire      etages2ibis.py --ecrire
couches2i.py --ecrire     couchesng.py --ecrire
poser2i.py --ecrire       # cuit les ÉLÉMENTS statiques dans les pages
animer2i.py --ecrire      # RÉCRIT decor_objets_data.c en entier
animerng.py --ecrire      # AJOUTE New Generation par-dessus
verifier_objets.py        # relit le C et vérifie les bornes du moteur
```

**`animer2i` avant `animerng`**, toujours : le second ajoute au fichier que le premier
refait. Dans le désordre, ce sont des symboles redéfinis.

**Et les `.tex` doivent être DÉPLOYÉS** dans
`%APPDATA%\CrowdedStreet\3SX\resources\tex_remix\stage<N>\`.

### Compiler

```
cd C:\Temp3sx\build && cmake --build .
```

Ne **jamais** filtrer la sortie et toujours tester le code de sortie ; puis
`cp 3sx.exe application/bin/3sx.exe`.

---

## 9. LES PIÈGES — chacun a déjà coûté une régression

1. **Une cohérence prouve un découpage, pas un rôle.** Six fois : `0x8C1D54E0`,
   `0x8C1A2534`, « le rang donne le décor », `sol` mesuré, `resout()` seul, et la table du
   second jeu validée sur sa seule destination.
2. **Un axe se MESURE.** Trois régressions le 01/09 faute d'un essai de trente secondes.
3. **Le premier `rts` n'est pas la fin d'une fonction** — le SH-4 sort tôt. Suivre les
   branchements et n'accepter qu'un `rts` non enjambé.
4. **`resout()` ne discrimine RIEN.** Les blocs de Necro, d'Oro et de Sean se résolvent
   tous à 100 % chez Hugo. **Seul l'appelant fait foi.**
7. **Une fenêtre fixe autour d'une routine donne de fausses attributions.** Le symptôme :
   un même site d'appel attribué à deux décors. Borner chaque routine par la suivante.
8. **Caler une structure sur le résultat attendu, puis lire le résultat comme une preuve.**
   Trois fois — dont « le bloc d'Oro à l'index 27 ».
9. **Un outil muet n'a pas forcément rien trouvé.** `situer_objets.py` annonçait « rien à
   corriger » alors que son motif ne reconnaissait plus aucune des 188 fiches.
10. **Ne jamais mesurer sur les pages cuites** : elles portent déjà ce que nos outils y ont
   posé. C'est la banque du `.pvc` qui fait foi.
11. **Un aplat passe toutes les épreuves de recoloriage.** Compter les couleurs distinctes.
12. **L'index 0 est transparent** — l'inclure dans une mesure de couleur fausse tout, et
   c'est ce qui a fait rejeter la bonne base de Hugo.

## 10. LE DIAGNOSTIC QUAND ÇA GÈLE SANS MESSAGE

1. **`fatal.log` d'abord** : `flLogOut` l'écrit puis TUE le jeu. Pas de `fatal.log` = ce
   n'est aucun `while (1)` de `mtrans.c`.
2. **Le battement de `sdl_app.c`** compte les tours de la boucle de trame.
3. **Les jalons** (`port/video/jalon.c`) : un fichier par trame, alternés — au gel, l'un
   porte la trame morte, l'autre une trame saine. Désarmés par défaut.
4. **`verifier_objets.py`** attrape à froid les trois bornes qui gèlent : `nb_tuiles`,
   `OBJETS_MAX`, et les morceaux vivants.

Aucun débogueur n'est installé, et **ne pas risquer un `pacman`** sur ce MSYS2.

---

## 11. L'ORDRE DE DESSIN — la règle universelle (15/09/2026, nuit)

Écrit après une journée de corrections décor par décor qui se défaisaient l'une l'autre
(Yun réparé, Oro cassé). Frédéric : *« tu dois trouver une règle universelle »*.

### Ce qui est mesuré dans SF3_2ND.BIN

* **Le décor n'a pas de table de profondeur par plan** (pas de `stage_priority` : recherche
  en mots et en octets, validée sur l'exe de 3SX où la table sort).
* **Boucle de dessin du décor `0x8C0F693C`** : chaque morceau reçoit en +28 une profondeur
  partie de 0.0 et augmentée de 2⁻¹⁸ par morceau (`0x36800000`, `0x8C0F6CB2`) ; le
  consommateur `0x8C0F6FCE` la passe telle quelle à `0x8C61AE72`. **La profondeur d'un
  morceau de décor est son RANG dans la liste d'éléments.**
* Les chargeurs d'objets écrivent la même valeur en +88 et +556 (`0x8C02936E` : 90, 90) —
  `position_z` et `my_priority`, comme `eff05`.
* Les morceaux alloués aux éléments (12608, 12624, 12640…) ne suivent pas l'ordre de la
  liste : **la liste est réordonnée**.

### Ce que disent les 27 relevés (outil `outils/ordre2i.py`)

**Une seule liste : couches, éléments statiques et objets, par profondeur décroissante.**
27 relevés sur 27, sans contradiction interne :

    Oro   [C0] [C3] 95 95 [C1] 90 86 [C2] 80 79 79 79 74 [C4]
    Yun   [C0] [C3] [C1] 95 [C1] 93 93 91 90 86 80 77 76 76 75 74 [C4]
    Yang  [C0] [C1] [C2] 90 87 86 84 81 [C4]
    Necro [C0] [C3] [C1] [C2] 76 76 75 75 ... [C4]

* **Les couches du décor n'ont pas une profondeur fixe par plan** : le plan 2 est entre 80
  et 86 chez Oro, au-dessus de 90 chez Yang. Chaque décor fixe les siennes.
* **13 décors sur 15 : toutes les couches derrière tous les objets.** Seuls Yun et Oro ont
  une couche intercalée.
* `[C0]` (morceaux 512, 16) et `[C4]` (12656, 8) sont identiques dans tous les décors :
  couches du moteur, pas du décor.
* **Les éléments statiques sont dans la liste, à leur profondeur** (Yun : 383,32 / 413,69 /
  479,64 / 576,64, entre les objets). La chaîne les CUIT dans les pages : ils prennent la
  profondeur du plan. C'est faux par principe.

### Ce qui en découle pour Oro (seul décor aux encadrements serrés)

    couchant (C3, objet 2)      > 95
    cascades                      95   <- derrière les deux grottes, devant le couchant
    grotte du fond (C1, obj 0)  entre 90 et 95
    objets                        90, 86 (le perroquet)
    grotte proche (C2, obj 1)   entre 80 et 86   <- 84, la valeur d'origine de 3S
    objets                        80, 79, 79, 79, 74

C'est exactement le commentaire d'`eff05` : la chute d'eau « défile avec la grotte du fond
et doit se dessiner juste devant le couchant ».

### LA SOURCE, TROUVÉE DANS LE BINAIRE (16/09)

* **`0x8C0B46DA`** — un objet dépose sa requête : `jsr 0x8C10A030` alloue l'élément, puis
  drapeaux = … | `objet[+0x22E]` << 12 (**le plan de l'élément est la famille**), x = +84,
  y = +86, **profondeur = `objet[+0x22C]` en +16**, puis **`jsr 0x8C10A2D2`, l'insertion
  triée**, profondeur dans r5.
* **`0x8C10B070`** construit les couches depuis des données : `[plan, PROFONDEUR,
  (3 mots par morceau)…, -1]…, -1` ; x = y = 0 ; profondeur en +16 ; insérées par
  `0x8C10B192` → `0x8C10A2D2`.
* **`TABLE_COUCHES = 0x8C601EE8`** : `table[décor × 16 + k × 4]` → couche k (`0x8C0DA62C`,
  `0x8C0DAC8C`, dans l'initialisation des plans). **La couche k dessine la demi-banque k**
  (k = banque × 2 + bas).
* Couche commune du plan 4 : `0x8C1D4B62`, profondeur **69**.

| décor | couches (plan 2I, profondeur) |
|---|---|
| Gill, Necro, Ibuki, Oro, Ken, Sean | (1, 94) (2, 84) (3, 104) |
| Alex, Ryu, Dudley, Hugo, Elena, Urien, Akuma, Hugo 2ᵉ var. | (1, 94) (2, 84) |
| **Yun** | (1, 104) (1, 94) (3, 114) |
| **Yang** | (1, 114) (2, 104) |
| **Elena 2ᵉ var. (bg08)** | (1, 94) (2, 120) |

**Contrôle** : les profondeurs générées pour 3SX reproduisent l'ordre des 27 relevés —
**255 paires couche/objet sur 255**, 0 faute, sur les 10 décors où elles se croisent.

**Appliqué** : `etages.py` (`couches_2i`, `profondeur_couche`, `DEFAUT_PAR_COUCHE`),
`etages2ibis.py` ; `eff05.c` n'ajoute plus rien aux objets. Exe `buildsx-table-2i.exe`,
lanceur `LA REGLE UNIVERSELLE - profondeurs de 2nd Impact.cmd`.

### Ce qui reste ouvert

* ~~Où 2I range la profondeur de chaque couche.~~ Trouvé, ci-dessus. Notes de recherche : Ni table par décor, ni chargeur d'objet
  (`champs2i --decor 10` : aucun ne pose de profondeur sans position), ni l'initialisation
  des plans (`0x8C0DA6FC` : coefficients `0x8C1D4F48`, bornes `0x8C1D557C`), ni la mise à
  jour du défilement (`0x8C0D877A`). Le trieur de la liste n'est pas trouvé.
* ~~La profondeur des éléments statiques.~~ Trouvée, ci-dessous.
* La règle d'ordre ne règle PAS : la charrette en trop (création), le perroquet (palette,
  déjà faux avant tout changement), les 13 animations manquantes de Yang (extraction),
  Sean (position verticale).

### LES ÉLÉMENTS STATIQUES — leur profondeur est dans l'enregistrement (16/09)

Le chargeur `0x8C0233B6` (et `0x8C02356A` pour le second jeu) lit l'enregistrement de 16
octets mot par mot, dans cet ordre :

    +0 -> +32    +2 -> +558 PLAN    +4 -> +554    +6 -> +102 x    +8 -> +106 y
    +10 -> +88 ET +556 PROFONDEUR   +12 -> +456 script   +14 -> +118

`+556` est ce que la requête de dessin `0x8C0B46DA` passe au tri. Les « constantes
inconnues » de `champs2i` étaient donc une lecture d'enregistrement.

**Gill, Alex, Elena, Urien : les six éléments des plans 3 et 7 valent 86**, entre la
couche du fond (94) et la couche proche (84) — le relevé de Gill le montre aussi :
`[C1] plan7 plan3 plan3 [C2]`. Appliqué par `etages.profondeur_elements`.

**À profondeur égale**, 2I insère en tête de seau : le dernier demandé est dessiné le premier,
donc derrière (Gill : plan 7 avant les plans 3). 3SX dessine ses plans 0..3 avec un test
`<=` : le plan 3 passerait devant. Le quatrième plan de Gill prend donc 87.

**Contrôle** : la chaîne générique (asset trouvé par `index_global`, palette par le
transfert de la bande) repeint les pages déjà validées au pixel — Alex 16 763/16 763,
Urien 17 265/17 265, plan 7 de Gill 919/919 ; le plan 3 de Gill diffère par la seule
figure gelée sur l'ancienne règle (`poser2i.SANS_Y0`). Outil `statiques2i.py`.

### UNE DEMI-BANQUE SANS COUCHE EST UNE RÉSERVE — Elena 2nd Impact

La table des couches est aussi la liste de ce qui EST une couche. La bande 9 (Elena) n'en a
que deux : sa banque 1 haut, que `couches2i` posait en plan lointain, est la **réserve de
l'animation de pages 0** — neuf trames de 320×160, recopiées dans le trou de la couche du
fond (320×160 en 256,352). D'où la mosaïque vue dans ce trou. Refait :

    liste 132  banque 0 haut + trame 0 dans le trou   94   vitesse 0,5 (objet 0)
    liste 196  inchangée                              84
    liste 260  l'élément du plan 3 (x 384 y 96)       86   vitesse 0,75 (écrasement)

La cascade est fixe (sa première trame). Hugo (bande 6) a la même réserve en plan lointain,
cachée par son plafond et validée à l'écran : pas touché. L'entrée 0 dit « destination x 384 »
quand le trou est en 256 : ce sont les couches de la bande 9 qui sont décalées de 128 — voir
« ELENA 1 : LE DÉCOR DÉCALÉ DE 128 » plus bas.

### NEW GENERATION : LA MÊME TABLE, RETROUVÉE PAR LES OCTETS (16/09)

Les routines de 2I se retrouvent octet pour octet dans `SF3_1ST.BIN` :

| | 2nd Impact | New Generation |
|---|---|---|
| constructeur de couches | `0x8C10B070` | `0x8C146714` |
| insertion triée | `0x8C10A2D2` | `0x8C145976` |
| table des couches | `0x8C601EE8` | `0x8C4DDBA4` (.bss, image `0x8C4CB784`) |

lue par `0x8C088200`, `table[bande × 16 + k × 4]`, bande en `+74`.

| bande NG | couches (plan, profondeur) |
|---|---|
| Gill | (1,94) (2,84) (3,104) (4,102) — banque 1 vide |
| Alex, Ryu, Ken, Necro, Ibuki ×3, Oro | (1,94) (2,84) (3,104) |
| **Sean** | (1,114) (2,94) |
| **Yun 1, Yang 1** | (1,104) (1,94) (3,114) |
| **Yun 2, Yang 2** | (1,114) (2,104) |
| **Dudley 1** | **(1,20)** (2,84) (3,104) — la couche 0 est la PLUIE, devant les combattants |
| **Dudley 2** | (1,104) (2,84) |
| Hugo, Elena 2 | (1,94) (2,84) — leur banque 1 est une réserve |
| Elena 1 | (1,94) (2,120) |

Appliqué par `etagesng.profondeur_liste` : chaque plan prend la profondeur de la couche qui
dessine sa demi-banque. Les objets de NG portaient déjà la leur (`+556`, `animerng`). Les
bascules d'ordre qui en résultent sont celles déjà validées en 2I (Yun, Oro), plus la pluie.

Lanceur `LES PLANS LUS DANS LE BINAIRE - 2nd Impact et New Generation.cmd`.

### ELENA, LA VARIANTE DU PONT (`bg08`, étage 56) — refaite depuis le code (16/09)

Référence extérieure : `apercu-3elena.png` (Flycast), manche 1 = le pont au-dessus du lac,
manche 2 = Elena 1. Le décor 8 porte les deux bandes ; **ce qui appartient à laquelle se lit
aux sites d'appel**, dans les routines d'étage (`0x8C1D3FB4`, indexée par bande) :

| bande 8 (`0x8C0DDA1C`…) | bande 9 (`0x8C0DE0A4`…) |
|---|---|
| spawner dédié `0x8C03CBCC` (herbes, cordes à crâne) | chargeur `0x8C025A9A` arg 6 (`0x8C17C310`) |
| statiques jeu 1 (0) **et jeu 2 (9)** | statiques jeu 1 (l'arbre) |
| pont `0x8C03CE46` (objet 123) | animation de pages 0 |
| animations de pages 6 et 7 | |

* **Une seule couche utile** : banque 0 haut (94), le ciel. La couche 1 (120) est vide ; la
  banque 0 bas est la réserve du lac.
* **Le lac** : entrées 6 (144×16 en 416,416) et 7 (320×64 en 352,432) remplissent la bande vide
  de 80 lignes sous la montagne. Les blocs qui changent entre trames tombent exactement sur ces
  destinations : les trames sont à leur place horizontale. Posé fixe (trame 0).
* **Les 9 statiques du jeu 2** : falaises (78), rocher violet du plan 3 (79), arbres morts à
  crânes (**20, devant les combattants**). Les éléments à `y` négatif sont sous le sol : coupés,
  pas repliés.
* **Le pont** : sprite 0 (768×48), script 0, plan 2, profondeur 76. Le spawner n'écrit pas sa
  position. Il est posé au centre (x 512), et sa hauteur est calée sur la capture : plancher à
  la même hauteur d'écran que celui d'Elena 1 (ligne 452), d'où y 40. Dans 2I il tombe en fin
  de manche (vitesses `0x8C17FD24`), ce que 3SX ne joue pas.
* 3SX : 4 plans — ciel 94 (0,0625/0,5), falaises+pont 78 (1), rocher 79 (0,75), arbres 20
  (1) ; 20 fiches d'objets, cache 3 pages. Outils `statiques2i.py --variante`,
  `etages2ibis.py`, `animer2i` (bloc `etage=56`, comptage par étage).

**`bg_index_tbl[30]` redevient `{30,30,30}`.** La variante par aire n'était portée qu'à moitié :
pages, profondeurs et plans suivaient `bg_w.stage`, objets et familles `bg_index`. L'étage 30
montrait les pages d'Elena 1 avec les plans et les objets (aucun) de la variante, et toujours
en aire 0. Chacune a maintenant son étage entier.

### LES ANIMATIONS DE PAGES DES DEUX ELENA — et le gel du pont (16/09)

**Le gel** : « ＣＧキャッシュバッファが一杯になりました » = `get_free_patcash_index`,
`PatternCollection` pleine (64). Le pont a 20 fiches qui changent d'image toutes les 4 trames ;
une identité vit 12 trames après son dernier dessin, donc **4** vivantes par fiche au pire
moment, 80. `animer2i.motifs_vivants` en comptait 3 (60, admis) : corrigé. Le moteur passe à
`PATTERN_COLLECTION_MAX 128` (`structs.h`, `mtrans.c`, `texcash.c` ; allocation par `sizeof`,
~14 Ko par cache). Simulation du cache sur les 29 étages à objets : aucun ne dépasse ; Yang 2
de New Generation (83) aurait figé lui aussi. `animerng` garde volontairement l'ancien compte
pour ne pas changer sa sélection.

**Ce que fait une animation de pages dans 2I** (routine de l'objet 14, `0x8C027806`) : pour
chaque bloc du masque, `cellule = (cellule & 0xFE00) | page` — elle change la **feuille de
texture** de la cellule de la tuilemap, pas la tuile. `fin` pointe sur `{largeur, hauteur}`
en blocs, `debut` sur le masque. La table page → trame n'est pas dans le fichier : les trames
se mesurent, dans l'ordre des pages triées (même règle qu'Akuma, validée).

| entrée | étage | trames | suite |
|---|---|---|---|
| 0 | 30 Elena 1 | **12** : 9 en banque 1 (3×3 de 320×160) + **3 tournées d'un quart de tour** en banque 0, colonne x 864, lignes 64–1023 | 12 pas de 5 trames |
| 6 | 56 pont | 4 bandes 144×16 en (416, 512+16k) | 18 pas, aller-retour |
| 7 | 56 pont | 4 trames 320×64 en (352, 576+64k) | 18 pas, aller-retour |

L'ordre de la cascade est le cycle le plus continu, à pas constant (1,12–1,14). Son sens n'est
pas lisible dans les images. `animer2i.PAGES_ANIMEES["bg08"]` (`entree`, `trames`, `pvc`,
`etage`), fiches groupées par étage ; étage 30 en 4 pages de cache (856 morceaux au pire).

**Encore ouvert** : le pont ne tombe pas en fin de manche. (L'écart de la destination de
l'entrée 0 est expliqué dans la section suivante.)

### ELENA 1 : LE DÉCOR DÉCALÉ DE 128, LE FEU, ET LES CORDES FIGÉES (15/09, nuit)

Retour de Frédéric sur l'exe précédent : « Elena 1, décor cassé, aucune animation de la
cascade » ; « le pont OK, mais les cordes tournent en boucle ». Quatre défauts, lus dans le code
et vérifiés sur la capture Flycast `cap-elena2.png`.

**1. Les couches de la bande 9 sont posées 128 plus à droite que la banque.** Deux mesures
indépendantes :

* le binaire : l'entrée 0 écrit sa trame en x 384 (`0x8C17D3DC`), le trou est en 256 dans la
  banque ;
* la capture, ramenée à 384×224 et comparée aux pages par balayage : la couche proche se cale
  en x 26 de la banque (écart moyen 10/255, les voisins à 18+), quand le feu — un objet, en
  coordonnées du monde, 511 − 240 = 271 — la place en 154. Pages décalées de 128, les trois
  plans tombent sur les vitesses de 3SX à cette caméra : proche 154, lointain **237** (prévu
  320 + (154−320)×0,5 = 237), élément du plan 3 **194** (prévu 195,5).

Rien dans les morceaux de couche (`0x8C601EE8`) ni dans la routine d'étage ne porte ce 128 en
clair : **la source n'est pas trouvée**, la valeur est mesurée deux fois. La variante du pont
(bande 8) ne l'a pas : ses trames du lac tombent à leur x. `statiques2i.DECALAGE_ELENA` roule
les listes 132 et 196 ; les éléments statiques et les objets, en coordonnées du monde, ne
bougent pas ; la fiche de la cascade prend la destination lue (x 384).

C'est ce qui « cassait » le décor : l'éléphant de pierre (peint dans la banque 0 bas) sortait
à gauche du feu, et la cascade se voyait là où 2I montre l'éléphant.

**2. L'objet d'Elena 1 était lu dans la mauvaise table.** Le chargeur `0x8C025A9A` arg 6
(`0x8C17C310`, script 1) est appelé par la bande 9 : son script se lit dans la table de
l'aire 1 (`0x8C1299DC`), son image dans F_ETC31, ses palettes à partir de 1365. `animer2i` le
lisait avec la table et l'asset du décor (aire 0, F_ETC30) : une falaise du pont, une image,
posée à l'étage 30. Le script 1 de l'aire 1 est **le feu** : dix images de huit trames,
144×128 en 271 — exactement là où il était cuit, figé, dans la page. Bloc `bg08` : champs
`aire`, `asset`, `base_palette`. La page proche est désormais la banque nue (roulée) ; le feu
n'y est plus cuit.

**3. Herbes et cordes à crâne (id 122, routine `0x8C03CAD8`) ne jouent pas pendant le
combat.** État 0 : pose le script ; état 1 : **n'avance pas** et attend `u16[0x8C6B0AA4] ≠ 0` ;
état 2 : joue le script une fois ; état 3 : attend `u16[0x8C6AF3E8+6] ≥ 2` puis s'efface.
`0x8C6B0AA4` appartient au pont (id 123) : zéro à sa naissance, un quand sa chute passe sous
y 40. Tant que le pont tient, les quatre restent sur l'image 0. Bloc champ `fige`.
Budget de l'étage 56 : 93 motifs → 34.

**4. À profondeur égale, le plan gagne : la cascade et le lac étaient cachés.** Le journal
les montrait changer d'image, l'écran jamais. Le plan est dessiné à `PrioBase[z]` ; chaque
morceau d'objet ajoute 1/65536 à la matrice (`appRenewTempPriority_1_Chip` dans
`seqsStoreChip`), et `PrioBase[z]` en garde la trace. Les morceaux d'un objet de même `z` que
le plan sont donc un peu plus loin que lui, et `LESS_OR_EQUAL` les refuse partout où le plan
est opaque. Akuma passait parce que son plan est transparent sous ses cascades (10 % opaque) ;
sous les trames d'Elena, la trame 0 est peinte dans la page (100 %). `animer2i.fiche_page` :
les animations décrites par `trames` prennent **z du plan − 1** (93). Les autres étages ne
changent pas.

Contrôle : la scène recomposée depuis les pages déployées et les tuiles compilées, à la caméra
de la capture, redonne la capture (éléphant, feu, cascade, arbres). Cache : Elena 1 630
morceaux vivants au pire sur 1024, le pont 423 sur 768. Seules les fiches des deux Elena
changent (375 fiches, NG identique).

Reste un défaut possible d'un pixel : le trou de la banque va jusqu'en x 415, le sprite du feu
s'arrête en 414. Non vérifiable sur la capture (Elena le couvre).

Lanceur `ELENA - le feu, la cascade et les cordes.cmd`, exe `build/3sx-elena-feu.exe`.

### LES SPRITES : table décalée, palette RAM, cuissons périmées (16/09)

Retour de Frédéric : Elena 1 « une frame décalée » ; Yun « enlever la charrette » ; Oro « le petit
bloc de pierre à supprimer, 2 chiens au lieu d'un » ; Necro « sprites de gauche pas à leur place,
mauvaise couleur, copie de la dame » ; Hugo bis « aucun sprite » ; Sean, Yang à reprendre.

**Outil nouveau : `outils/routine2i.py <bande>`** — tout ce que la routine d'étage crée, appel par
appel : les quatre chargeurs à table décodés (y compris les éléments des deux jeux), les spawners
à blocs par tirage `z`, les spawners à immédiats et ceux qu'ils appellent, et **la table de scripts
que chaque cible pose en dur, rapportée à celle du décor**.

**1. Une table de scripts peut être décalée.** L'id 22 de Yun pose `0x8C123E48` = table du décor 3
**+ 42** (l'id 21 : +36). Son script 2 est donc le 44 du décor, et celui qu'il pose au repos
(`mov #0,r6`, `0x8C029006`) le **42** : un oiseau de 16×16. On lisait le script 2 du décor : la
charrette, posée sur la foule. La charrette du jeu 1 d'éléments (479/64) est réelle et reste.

**2. La palette d'un objet est celle de son emplacement RAM.** `+554` = `my_col_code` ; ses 9 bits
bas sont l'emplacement de la palette RAM (0x40 = 64 = dst 0x2000 / 128), et le morceau d'offset `o`
lit `emplacement + o`. Les trois transferts du chargeur d'étage (§3c-quater) disent quelle palette
du binaire occupe chaque emplacement — `outils/palettes_ram2i.py`. La règle **retrouve seule** les
valeurs validées (Yun 1631 et 1063, Oro 1674, Hugo 1652, Dudley 1642) et donne `0x2059` = 64+25,
le **transfert secondaire de Necro** (1647..1651), à la dame et aux bocaux : rendus, ils ont les
couleurs de la capture 2I (blouse blanche, peau rose, pieuvre violette). Même cas pour la femme à
l'éventail de Yang (`0x2050`, 1639). Appliquée à `PALETTES_RAM` (bg03, bg05, bg0b, bg0d, bg10) ;
ailleurs elle rend les mêmes palettes sauf trois cas non tranchés, laissés tels quels (Ryu
script 7, Hugo id 63, le perroquet d'Oro).

**3. Les pages proches portaient des cuissons périmées.** `poser2i` repart de la page en place et
n'efface pas ce qu'une ancienne passe a peint. Oro : un chien couché, l'édifice et les chatons
(les « 2 chiens ») — aucun n'est un élément du code. Necro : la dame, le calmar et la pieuvre SUR
leurs bocaux, les chaînes. `statiques2i.py --refaire` repart de `poser2i.banque_nue` et ne peint
que les éléments du code restés au plan proche (priorité ≥ 28).

**4. Necro, le second jeu d'éléments est devant les combattants.** `0x8C02356A` : chaînes (script 0,
168/16) et tuyaux (17, 880/16), priorité **2**. Posés en objets, à 2.

**5. Oro.** L'édifice animé (enregistrement 7 de `0x8C02E1FE` arg 6, plan 2, priorité 90) est
**derrière** le plan proche (84) : son sol en couvre 687 px sur 721, le chien le reste. `MESURE`
le mettait dans la grotte du fond, à côté du chien : retiré (`EXCLUS`). Le chien a deux places
selon les personnages (`0x8C033750` : 608/53 si l'un est le 7, 8 ou 9, sinon 700/56). La routine
d'étage (`0x8C0DE5D2`) n'appelle `0x8C028792` arg 4 et `0x8C025A9A` arg 7 (script 19, ajouté) que
pour z 1 et 2.

**6. Hugo bis (étage 57)** : entrée `bg10` neuve — deux jeux d'éléments en objets (deux devant les
combattants), id 63, `0x8C025A9A` arg 5, `0x8C02E1FE` arg 5 ; table de Hugo, asset F_ETC29 ; cache
4 pages. `0x8C02C68A` arg 0 reste non lu.

**7. Elena 1, la trame décalée** : les trois trames tournées commencent en 80/400/720, pas
64/384/704 — la trame fait 304 de large, et c'est la fin de sa case de 320.

**Encore ouvert** : Yang — id 29 (les poissons de l'aquarium, `0x8C02B356`, tables +82/+86), la
grue et le grand bambou à priorité 20/23 (devant, cuits derrière), et l'origine du vieil homme en
vert cuit dans la page, présent sur la capture 2I ; la machine à états des statues (id 25, scripts
65/66/70/72…) n'est pas lue. Sean : les positions du code coïncident avec les objets et les
cuissons ; il faut savoir quels sprites Frédéric voit déplacés.

Cache : Necro 310/512, Oro 374/1024, Yun 471/768, Hugo bis 418/1024. Lanceur
`SPRITES - Elena Yun Oro Necro Hugo bis.cmd`, exe `build/3sx-sprites.exe`.

## LA LARGEUR DES DÉCORS, LES CUISSONS EN DOUBLE, LE FOND QUI DÉFILE (16/09, soir)

Frédéric, sur une capture de Sean : « *une partie des sprites sont décalés vers le haut de
1 ou 2 pixels, le conducteur et le personnage à genou sont doubles* » ; sur Necro : « *le
décor n'est pas aussi large que dans la version dreamcast, on ne peut pas aller au bout
des extrémités droite et gauche. Corrige et vérifie pour tous les autres décors* ».

### 1. La largeur : la table est dans le binaire, et le chargeur la lit sous nos yeux

**Ma première réponse était fausse et Frédéric l'a vue tout de suite** : « *je viens de
tester Ryu, ça ne va pas du tout* ». J'avais mesuré les pages — *première colonne peinte +
192, dernière − 192* — et la règle retombait pourtant sur Gill, Dudley et Ken. Elle donnait
639 px de course à Ryu, qui peint sa bande entière. **La page dit jusqu'où le décor existe,
pas jusqu'où le jeu laisse aller.**

`0x8C0DA7A0` charge `[0x8C0DA864] = 0x8C1D557C`, ajoute `bande * 48 + plan * 12`, et écrit
six mots d'affilée avec `mov.w @r4+,r1` :

    +104 l_limit    +100 r_limit    +106 l_limit2    +102 r_limit2    +108 y_limit
    +110 y_limit2

Ce sont exactement les champs, et l'ordre, de `limit_tbl3` côté 3rd Strike. Puis, si
`u8[0x8C841F3C]` n'est pas nul, `0x8C0DA7F8` recopie `l_limit`/`r_limit` par-dessus
`l_limit2`/`r_limit2` : **la paire large remplace l'étroite**.

C'est la paire large qui correspond à ce qui est validé à l'écran :

| étage | table de 2I | ce qui était posé |
|---|---|---|
| Dudley | 0x110..0x2f0 | 0x110..0x2f0 — au pixel près |
| Gill | 0x142..0x2bc | 0x140..0x2c0 |
| Alex | 0x102..0x2fc | 0x100..0x300 |
| Ken | 0x0e4..0x31c | 0x0df..0x320 |

La paire étroite, elle, donnerait 270 px à Gill : personne n'a jamais joué comme ça.

**Des bornes négatives sont comptées depuis le milieu de la bande.** Ryu y est
(−202..203), comme ses objets le sont déjà (`animer2i.DECALAGE_X`), et six bandes de New
Generation aussi. Une position de caméra ne peut pas être négative : le signe est la marque
de l'origine, on ajoute 512.

**New Generation a la même table**, au même chargeur : `0x8C0883A8 -> 0x8C18A3F8`, lue dans
son propre binaire. Les dix-neuf étages portaient tous 0x140..0x2c0 ; ils vont de 352 à
679 px de course.

La course, par étage : Necro 630, Ken 568, Alex 506, Dudley 480, Ibuki 440, Ryu 405, Gorge
379, Elena 1 380, Gill / Yun / Elena 378, Oro / Yang / Urien 374, Sean 372, Hugo et Hugo
bis 368. Outil `limites.py`.

**Ce qui n'est pas repris** : les `y_limit` de la table (144 à 304 selon le décor) restent
à 0xF0. Toucher à la verticale en même temps que l'horizontale, c'est ne plus savoir
laquelle des deux a bougé.

### 2. Sean : les trous de sa banque sont un étalon

Sa banque **n'est pas peinte** sous ses éléments statiques : elle est **découpée à leur
silhouette**, et le jeu pose l'objet dans le trou. En cherchant, pour chacun, l'écart où sa
silhouette couvre le trou et rien d'autre :

| élément | place calculée | trou |
|---|---|---|
| le conducteur | 575,863 | 576,864 |
| le petit palmier | 367,751 | 368,752 |
| le poteau | 662,895 | 663,896 |
| l'homme à genou | 655,911 | 656,912 |

**Les quatre disent le même pixel** : `animer2i.AJUSTEMENT["bg0d"] = (1, 1)`. D'où il vient,
je ne sais pas — la formule est celle des treize autres décors.

Et le décalage de seize : `couches2i.demi_banque` descend la moitié basse de `bg0d` de
16 px pour que son dessin touche 1023, mais les objets restaient posés sur `SOL_REPERE`.
`poser2i.sol` ajoute maintenant `decalage_sol`. Les treize autres décors ont un recalage
nul : rien ne bouge chez eux.

### 3. Un élément du code se POSE, il ne se peint pas

« *le conducteur et le personnage à genou sont doubles* » : les pages de Sean et de Necro
portaient **déjà** ces figures, cuites par une ancienne passe de `poser2i`, pendant
qu'`animer2i` les posait en objets. Seize pixels séparaient les deux. `statiques2i.REFAITES`
refait les deux pages depuis la banque nue, sans rien y ajouter. Poser plutôt que peindre
rend à l'élément sa profondeur (75, devant la couche à 84) et évite qu'une passe laisse un
dessin que la suivante ne sait plus effacer.

### 4. Le conducteur du train de Necro

Deux créateurs à immédiats que rien n'atteignait : `0x8C023756` (id 7) et `0x8C0238DC`
(id 8), appelés depuis sa routine d'étage. Ils n'écrivent **ni `+102` ni `+106`** : leur
position est en `+84`/`+86`, masquée par `0x3FF` — (463, 77) et (432, 118). Le reste est en
dur : `+552` = 0x4200, `+554` = **89** et 0x2040, `+558` = 2, `+556` = 64. Leur table de
scripts est celle du décor décalée de 34 et de 18, et leur script 0 est donc le 34 et le 18.
Avec l'emplacement 89 l'homme sort en blouse grise, penché sur le pupitre.

Les trois éléments de son premier jeu (`0x8C0233B6`, index 15) manquaient aussi : le tuyau,
la tête rouge du broyeur et la bouche du four.

### 5. Le fond de Necro défile, et il boucle

Sa routine d'étage, à `0x8C0DD0E8`, retire **cinq pixels par trame** à `xy[0].disp.pos` et
`wxy[0].disp.pos` de son plan lointain : l'installation avance, la chaîne de montagnes
passe derrière la vitre. Côté port, ces deux champs sont recalculés à chaque trame ; le
seul terme qui survit est `pos_x_work`, et c'est lui qu'on décrémente (`bg220_derive_x`).

Un plan qui défile sans fin doit **se répéter**. `scr_trans` écrêtait les colonnes à
[0, 0x3FF] — « la page s'arrête là » — ce qui est juste pour un plan qui suit la caméra et
faux pour un plan qui défile. `bg_boucle_x` lève l'écrêtage pour ce plan-là, et
`bgDrawOneScreen` replie l'index de vignette sur `x & 0x3FF`. Les autres plans ne changent
pas d'un pixel : leurs colonnes sont déjà dans l'intervalle, où le masque est l'identité.

### 6. Trente-deux objets par étage n'était pas une loi de la nature

Necro en demande 34. La borne venait de la clé du cache de tuiles, `rang << 11 | image << 5
| case`, qui ne laissait que cinq bits au rang — et le compte était écrêté **en silence**.
La clé est maintenant un **rang de morceau dans l'étage** : chaque objet reçoit une base, la
somme des `nb_images * cols * ligs` de ceux qui le précèdent. Les clés restent uniques et
tiennent dans les seize bits — le plus chargé, Elena 1, en compte 7 194 sur 65 534.
`OBJETS_MAX` passe à 48.

## IBUKI BG07 : CE QUI EST ETABLI, ET LE NŒUD QUI RESTE (16/09, nuit)

Frédéric : « *décor à reprendre dans son ensemble* ».

### Ce que le décor porte vraiment

`banque 0 haut` n'est pas une couche de paysage : c'est **six vues presque identiques de la
cascade**, 272x245, en trois colonnes et deux rangées (0..815 en x, 11..501 en y), plus une
bande séparée en 864..1023 — les bambous et la cabane. Le port la monte telle quelle en
troisième plan : **la mosaïque se voit à l'écran**, avec ses arêtes noires.

C'est le même cas qu'Elena, où la réserve d'animation était montée en plan lointain.

### Les trois animations, lues dans le binaire

Sa routine d'étage (`0x8C0DD6C8`) ne crée aucun sprite : elle appelle trois fois
`0x8C0277C4` avec les types **4, 5 et 11**, qui sont trois entrées de la table d'animations
de pages `0x8C17D8DC` — celle qu'`animer2i.entree_de_pages` sait déjà lire :

| entrée | plan | taille | destination | suite |
|---|---|---|---|---|
| 4 | 0 | 144x288 | 368,144 | 6 images, 4 trames chacune (pages 69, 73..77) |
| 5 | 0 | 144x96 | 224,336 | les mêmes 6 images |
| 11 | 1 | 80x64 | 112,352 | 26 pas alternant les pages 64 et 71 — un scintillement |

Le port n'en porte **qu'une**, et elle est fausse : elle anime des vignettes entières de
272x245 à une place devinée (`PAGES_ANIMEES["bg07"]`), du temps où l'on ne savait pas lire
ces entrées.

### Le nœud, suivi jusqu'au moteur de rendu (16/09)

Frédéric : « *pourquoi tu ne vois pas ça dans le code ?* » puis « *suis la liste d'affichage
jusqu'au découpage en quadrilatères* ». Fait. Outil ajouté : `fpu_sh4.py`, qui décode les
instructions flottantes du SH-4 que `sh4.disasm` rendait en `???`.

**1. Le lecteur de couche.** `0x8C10B070` lit `{plan, profondeur, (3 mots) × N, −1}`.
Chaque groupe devient une requête (plan en `(plan & 7) << 12`, profondeur en `+16`), chaque
triplet une entrée de seize octets `{0, 0, 0, A, B, (C & 15) | couche << 4}` dans la liste
`0x8C72FCCC`. `0x8C10A2F8` aplatit la liste triée en commandes de seize octets.

**2. Le moteur de la liste** (`0x8C0F697C`). Pour une entrée, `+4` est X, `+6` est Y, `+8`
est une **taille** — `(mot & 0x7F) + 1` en largeur, `(mot >> 8 & 0x7F) + 1` en hauteur —,
`+10` choisit deux classes d'échelle dans une table flottante `[1.0, 1.0, 0.5, 0.25]`
(`0x8C1E8F14`), et les positions sont repliées sur 1024 (`& 0x3FF`).

**3. Mais une entrée de couche ne dessine rien.** Quand `+10 & 3` vaut 0 — le cas des
quatre triplets —, le moteur saute en `0x8C0F6CA2` et appelle `0x8C0F56BC`, qui se contente
de ranger la profondeur de la couche `(+10 >> 4) & 3` dans `0x8C6D6B94`. **Les deux
premiers mots de l'enregistrement ne servent pas au dessin.** Ils ne peuvent donc pas être
ce qui cache la réserve d'Ibuki — ce que les deux essais de découpe avaient montré par
l'image (ils ajoutaient du noir au lieu d'en ôter).

**4. Les plans sont dessinés ailleurs** (`0x8C0F84E6`), avec la profondeur rangée plus haut.
Chaque plan est une texture de **1024 × 512 qui se répète** dans les deux sens : colonne de
gauche `(x + 1) & 0x3FF`, ligne du haut `(y + 20) & 0x1FF`, fenêtre de 384 × 224, et un
dessin en deux morceaux quand la ligne dépasse 288 (le repli vertical). Notre port, lui,
dessine des pages de 1024 × 1024 écrêtées.

**5. Les « pages » d'une animation sont des images entières**, pas des vignettes de
texture : chez Elena, les pages 80 à 91 sont les douze trames de 304×160 que la mesure a
trouvées (neuf en banque 1, trois tournées en banque 0). Leur place dans le `.pvc` ne se
calcule pas depuis le numéro — elle se mesure. Chez Ibuki, les entrées 4 et 5 partagent
les six mêmes pages (69, 73 à 77) : **ce sont les six vues de la cascade**.

### Ce qui a été corrigé, par la mesure

**Le vide ne ment pas.** Le moteur de fond ne masque rien : l'art est fait pour ne jamais
laisser de trou. J'ai donc simulé l'écran — les trois plans à leur parallaxe, une fenêtre de
384×224, neuf positions entre les deux bornes de caméra — et compté les pixels où aucun plan
ne peint.

* Décaler le temple ou la cascade ne change rien. Décaler le **ciel** (banque 1 haut) les
  supprime **tous**, pour tout décalage de 120 à 456 colonnes, et d'aucune autre façon.
  128 est le bord de l'intervalle et l'écart déjà mesuré sur Elena. `couches2i.DECALAGE`
  roule la page de −128 (la fenêtre doit lire 128 colonnes plus à droite). Necro, Hugo et
  Oro, soumis à la même mesure, n'ont aucun vide sans décalage.

* **Les six vues sont six trames** : découpées au masque de l'entrée 4 (la crête courbe,
  144×288) et de l'entrée 5 (le bassin, 144×96, décalé de −144, +192), elles s'écartent de
  3 à 7 niveaux entre elles, et la crête se retrouve avec un pas de 272 sur les deux
  rangées. Posées aux destinations lues, elles tombent à côté ; mais **les deux destinations
  sont décalées du même écart (−32, −112)** par rapport à la crête et au bassin de la vue
  (272, 256). Et c'est la vue que la caméra montre : le plan défile à 0,625 et sa fenêtre
  couvre les colonnes 181 à 840. L'animation tournait sur la vue (0, 267), hors champ sauf
  à l'extrême gauche : elle tourne maintenant sur la vue du centre, au même coût de cache.

Ce qui n'est pas expliqué : d'où viennent les deux écarts, 128 pour le ciel et (−32, −112)
pour les destinations. Ils sont mesurés, et le second est vérifié deux fois.

> **Dépassé le 16/09** : les deux écarts étaient des artefacts de la mosaïque. Le moteur de
> décor pose la scène par rectangles — voir « LE DESCRIPTEUR DE SCÈNE » plus bas.

## YANG BG0B : LE MONSIEUR EN VERT, LES POISSONS, LA GRUE ET LE BAMBOU (16/09)

Frédéric : « *monsieur en vert mal affiché, poissons manquants dans l'aquarium, un objet côté
gauche doit être devant les combattants, la plante à droite doit être devant les
combattants* ».

**Tout était cuit.** Aucun des cinq éléments de Yang (les deux chargeurs, index 30) n'est
dans la banque d'origine : la page les portait tous, à sa propre profondeur, avec un
monsieur en vert **brouillé** — deux têtes, des blocs décalés. Même cas que Sean et Necro :
la page repart de la banque nue (`statiques2i.REFAITES`) et tout est posé en objet.

| élément | position | profondeur | |
|---|---|---|---|
| la lanterne (script 0) | 512/176 | 84 | |
| **la grue** (script 1) | 352/21 | **20** | devant les combattants ; cuite à 84, elle passait même derrière le rocher sculpté (81) |
| le cabinet (script 2) | 288/32 | 88 | le pied de l'aquarium |
| le petit bambou (script 9) | 512/128 | 103 | |
| **le grand bambou** (script 62) | 736/24 | **23** | devant les combattants |

**Le monsieur en vert** est l'id 28, créé par `0x8C02AE4E`, que `routine2i` ne voyait pas
parce qu'il est appelé par pointeur (`0x8C02A434`). Tout est en dur : x 496, y 64, `+556` =
83, `+554` = 0x50, et `+0x16C` = la table du décor + 76 — la seule référence à
`0x8C124F60` du binaire. Ses scripts sont les 76 à 81 (19, 8, 20, 7, 41 et 24 images) ; on
pose l'attente, le 76. Avec l'emplacement 0x50 il sort en robe verte, moustache, mains
jointes : la figure de la capture.

**Les poissons** sont l'id 29, `0x8C02B356` : deux enregistrements `{x, y, profondeur}`, le
premier avec la table + 82, le second avec la table + 86 (`tst r13` en `0x8C02B3D2`),
`+554` = 0x50. (240,136) et (128,148), profondeur 86 : dans l'aquarium, qui est l'objet du
script 61.

**Les trois « statues »** du chargeur `0x8C029B00` sont des machines à états : leurs
enregistrements portent trois scripts de plus — (70, 72, 66), (69, 73, 64), (22, 74, 0) —
qui sont le rocher sculpté, le guerrier vert et le personnage de droite **brisés** au fil
du combat. Seul le premier état est posé.

**Le cache de tuiles** : 574 morceaux vivants au pire pour les 512 des deux pages de Yang,
soit 112 % — Hugo figeait à 108 %. Yang passe à quatre pages (56 %) ; Necro à quatre (77 % →
38 %) et Sean à deux (78 % → 39 %), par précaution. `texcash.c`.


## LE DESCRIPTEUR DE SCÈNE : CE QUE 2I DESSINE VRAIMENT (16/09) — Ibuki refait

Frédéric, sur Ibuki : « *la cascade de gauche est animée mais elle est beaucoup trop basse, la
cascade de droite est en trop, un temple à droite en arrière-plan manquant* ».

### Le nœud, dénoué

L'animation de pages de 2I (`0x8C027806`) écrit `(case & 0xFE00) | page` dans une grille de
cases de quatre octets, 64 de large : la grille d'une **couche CPS3**, que 2I émule (registres
en `0x8C7EFCEC`, seize octets par couche). Mais 2I **ne dessine pas ces cases**. Son moteur de
décor, `0x8C0F8D94` (entrées 0 à 22 de la table `0x8C60A0B0`), choisit selon le décor une
**liste de rectangles** et la passe à `0x8C0F8AE0` :

| octets | champ |
|---|---|
| +0 | couche (le registre 0..3) ; −1 termine |
| +4, +8 | x dans la scène, largeur |
| +12, +16 | y dans la scène, hauteur |
| +20 | texture : la banque 0 ou 1 du `.pvc` |
| +24, +28 | u, v : le coin dans la banque |
| +32, +36 | drapeaux (+32 = 1 : la trame est tournée, chez Elena) |

Écran x = x − ((défilement x + 1) & 0x3FF), écran y = y − ((défilement y + 20) & 0x3FF), et
chaque rectangle est redessiné à +1024 en x et en y : la scène boucle. **La banque n'est qu'un
atlas.** L'ancienne piste `0x8C0F84E6` (un plan = la texture entière) n'est prise que par deux
chemins particuliers : ce n'est pas le dessin des décors.

La table de sauts (`0x8C0F8DC8`, dix-huit décalages depuis `0x8C0F8DBC`) est indexée par le
numéro de décor (`+74` de l'étage). **Douze décors ont l'identité** — `0x8C603888` (deux
couches) ou `0x8C603900` (trois) :

    (couche 0, x 0, 1024, y 512, 512, banque 0, u 0, v 0)     la banque 0 haut
    (couche 1, x 0, 1024, y 512, 512, banque 0, u 0, v 512)   la banque 0 bas
    (couche 2, x 0, 1024, y 512, 512, banque 1, u 0, v 0)     la banque 1 haut

C'est la convention du port (moitié haute sur les lignes 512 à 1023 de la page) : voilà
pourquoi elle marche. Le décor 16 a la même, à trois couches. **Cinq décors ont un descripteur
propre**, et une animation de pages y choisit simplement un descripteur de plus, dessiné
par-dessus la base (la page courante est dans `0x8C71866C` + 4k) :

| décor | base | ce qui s'anime |
|---|---|---|
| 6 Hugo | `0x8C604918[octet 0x8C6B0B20]` | huit états des bateaux (couche 1, 448,640) |
| 7 Ibuki | `0x8C60495C` | pages 69, 73..77 → une vue de cascade ; 64/71 → la cabane |
| 8 le pont | `0x8C604DBC` | les reflets du lac (256,928) et (256,944) |
| 9 Elena 1 | `0x8C6050B4` | pages 80..91 → une trame en 384,864 ; la bande du bas |
| 15 Akuma | `0x8C605614` | six trames en 144,832 ; quatre en 400,784 ; deux en 688,832 |

**Ce que les descripteurs expliquent après coup** : le décalage de 128 d'Elena 1 (sa couche 0
est posée en x 128, « la source n'est pas trouvée » plus haut), l'ordre de ses trames
(colonne par colonne) et ses trois trames tournées (drapeau +32) ; la cascade d'Akuma en
144,832. Les mesures tombaient juste.

### Ibuki, par le descripteur

    couche 0 (milieu, 94)   banque 1 (0..367)    en 496,512   la montagne et le TEMPLE
                            six vues 272x256     en 224,688   empilées, la dernière dessus
    couche 1 (proche, 84)   banque 0 bas         à l'identité
                            banque 0 haut (832..) en 64,512   la seconde cabane
    couche 2 (fond, 104)    banque 1 (384..1023) en 192,512   le ciel

Le port montait la banque telle quelle : deux cascades côte à côte (celle de droite « en
trop »), la cascade animée 80 lignes trop bas (sa vue commence en 267, le descripteur la pose
en 688 − 512 + 11 = 187), et la montagne au temple dans le ciel, à gauche, où la caméra ne
passe presque jamais. Le « ciel décalé de 128 » bouchait un vide que la mosaïque créait : il
est retiré, et le vide aussi (simulation : aucun pixel vide aux deux bornes ni en saut).

* `descripteurs2i.py` (nouveau) lit les descripteurs et compose une page ;
  `statiques2i.py --ibuki --ecrire` écrit les listes 132, 196 et 260 de l'étage 29.
  `couches2i` garde les couches d'Ibuki (pour les profondeurs) mais ne les écrit plus.
* La page proche ne change que de 843 pixels : la seconde cabane, qui ne diffère de la
  première que par **les lanternes** — et tous ces pixels tombent dans le masque de
  l'entrée 11 (80×64 en 112,352). Contrôle indépendant de la lecture.
* `animer2i.PAGES_ANIMEES["bg07"]` : la cascade (six vues 272×256, ordre des pages, en
  224,176 du plan) et **le scintillement des lanternes** (entrée 11, pages 64 → la cabane du
  haut, 71 → celle du bas, 26 pas). Budget 42/128, cache 608/1024 (59 %).
* L'écart (−32, −112) mesuré la veille était celui des masques CPS3 ; la scène du Dreamcast
  est à −(0, 512) des coordonnées de la grille, ce que les lanternes confirment au pixel.

Lanceur `IBUKI - une cascade, le temple et les lanternes.cmd`, exe `build/3sx-ibuki2.exe`.
Sauvegarde : `avant-ibuki2/` (pages et données).

### Piste ouverte : la bande du bas d'Elena 1

La base d'Elena 1 ne pose pas les lignes 960..1023 de sa couche proche : un descripteur de
plus (`0x8C60560C[+4 de 0x8C71866C]`) y met la banque 0 (0,512) en version 0 — les falaises
seules — ou (0,960) en version 1 — **des planches**. La routine du décor 9 (`0x8C0DE240`,
sous-table `0x8C1D6130`) met la version 0 au départ quand `+5` de `0x8C6AF304` vaut 1, et
passe à la 1 quand `u16[0x8C6B0AA4]` (la chute du pont) devient non nul, avec le son 119.
Le port montre la version 1 dès le début. Frédéric a validé Elena : **rien n'est changé**, à
vérifier sur une comparaison.


## SEAN, ORO, ET LA LENTEUR (16/09, soir)

Frédéric : Ibuki OK. « *SEAN : tout le décor est affiché trop bas par rapport aux combattants, une
colonne de pixels noirs au niveau de la voiture jaune, des pixels blancs au niveau de la table* » ;
« *ORO : l'animation du bloc de pierre incrusté dans le mur de la grotte est manquante, la couleur
du perroquet est mauvaise, le chien a disparu* » ; « *tout le jeu est devenu lent, c'est lié à une
sonde activée ?* »

### Sean : seize lignes de trop, un pixel de trop

* **Le décalage de 16 est retiré** (`poser2i.decalage_sol` rend 0). Le descripteur de Sean est
  l'identité : 2I pose sa moitié basse ligne pour ligne, et si son dessin s'arrête en 1007, c'est
  ainsi que 2I le montre. La page et les objets remontent ensemble (`sol` suit) ; les trois autres
  pages refaites (Necro, Oro, Yang) ne changent pas d'un pixel.
* **La colonne noire et les pixels blancs ont la même cause.** Recomposé depuis la page et les
  tuiles compilées, avec chaque décalage d'un pixel : seul **+1 en x** découvre une colonne seule —
  le bord gauche du trou du conducteur, en x 608, 21 lignes, la colonne de la capture. La table
  n'est pas découpée, mais la page porte sous elle un pavé clair uni que la table recouvre :
  décalée à droite, elle en découvre le bord gauche, là où Frédéric a entouré les pixels blancs.
  Le moteur place donc déjà nos objets un pixel à droite des plans (comme 2I, `x − (défilement + 1)`),
  et `AJUSTEMENT` le comptait deux fois : **(0, +1)** au lieu de (+1, +1). La verticale reste.

### Oro

* **Le bloc de pierre** : l'édifice animé (script 9, 32×32, deux images) retrouve sa place
  mesurée dans la grotte du fond (`MESURE`, 704,896, famille 3) ; `EXCLUS` est vide. Le « petit
  bloc à supprimer » du 16/09 était la copie périmée cuite dans la page proche, effacée le même
  jour par `REFAITES`.
* **Le perroquet** : son spawner écrit `+554` = 0x2058, comme le chien, le chat et les chatons —
  l'emplacement 88, rempli par le transfert secondaire (idx 108, 1674..1677). La chaîne lui
  donnait 2187 (idx 105). `bg0a` entre dans `PALETTES_RAM` ; c'est la seule palette d'Oro qui
  change. Rendu : tête verte, face orange, aile bleue, comme `reference-oro-perroquet.png`.
* **Le chien** est posé (variantes z 0, 1, 3). La variante 2 de 2I (le chat et les chatons, sans
  chien) est tirée une fois sur quatre. Le tirage est maintenant écrit aussi dans
  `fin-de-round.log` (« variante de décor N (étage 31) »), pour trancher sur la prochaine partie.

### La lenteur

Aucune sonde n'était armée : les jalons ne s'arment que sur `jalons.on` (absent), les autres
journaux sont bornés. Mesure sur la partie d'Ibuki : environ 24 960 trames du moteur en 498 s, soit
environ **50 images/s** pour 59,6 attendues — mais les parties précédentes, mesurées de la même
façon (et la mesure compte les pauses et le chargement), donnaient 51 à 56. Rien ne distingue
encore une régression d'un effet de la machine.

Le battement du moteur (`sdl_app.c`, une ligne par seconde dans `fin-de-round.log`) porte
maintenant **la durée réelle des 60 trames** (1007 ms attendues) et **le temps de calcul moyen
par trame**, plus une ligne « pointe » quand une trame a dépassé 16,8 ms. La prochaine partie dira
si le jeu est lent, sur quel décor, et si c'est le calcul.

Lanceur `SEAN ET ORO - decor remonte, bloc de pierre, perroquet.cmd`, exe
`build/3sx-sean-oro.exe`. Sauvegardes : `avant-sean2/`, `avant-oro2/`.


## LE CHIEN D'ORO ET LES VARIANTES DE SON DÉCOR (16/09)

Frédéric, après la partie : Sean **validé** ; chez Oro le bloc de pierre et le perroquet sont
bons, *« le chien est revenu mais il n'est peut-être pas à la bonne place. Ce stage doit avoir
des variantes qu'il faudrait identifier »*. Il avait raison sur les deux points.

### Les variantes d'Oro, toutes lues dans le code

| ce qui varie | qui choisit | où c'est lu |
|---|---|---|
| le chat, les chatons, l'objet id 18 arg 4, `0x8C025A9A` arg 7 | le tirage `z` (1 et 2) | répartiteur `0x8C0DE5D2` |
| le chien existe | le tirage `z` (0, 1 et 3) | même répartiteur |
| **le chien debout en 608 ou couché en 700** | **les combattants** | spawner `0x8C03369E` |
| l'intro du premier round (la caméra descend) | un des joueurs est Oro, et c'est le premier round | `0x8C0DE758`, `0x8C0DE7E2` |
| la luminosité de la palette 108 | `u16[0x8C6AF34E]` via `0x8C1D5D88` (non tranché) | `0x8C0DE584` |

Le perroquet et les chauves-souris ne varient pas. Les autres routines d'étage qui lisent les
combattants (Yun, Yang, Necro, le pont d'Elena) ne s'en servent que pour **l'intro du premier
round** : Yun contre Yang, ou un personnage chez lui. Deux objets d'effet (id 37 et 94) lisent
aussi les personnages ; ils n'appartiennent à aucun décor.

### Le chien : deux routines, et le port jouait un mélange des deux

Le spawner lit le personnage des deux joueurs (`plw + 0x358`) et leur **humeur** dans
`0x8C17F364` (Ibuki 1, Elena 1, Oro 2, les autres 0) :

* **un ami présent** → type 0, **x 608, y 53**, routine `0x8C03331C` : le chien **debout** ;
* **sinon** → type 1, **x 700, y 56**, routine `0x8C03360C` : le chien **couché**.

Le port posait le **script 29**, l'aboiement du chien debout, **à la place du chien couché**.
Le « premier état » d'une routine ne suffisait pas : il y en a deux.

**Debout**, trois états (`+36`) :

0. **le regard** — `0x8C03334A` choisit 1, 3 ou 5 selon le combattant de plus grande humeur
   (x < 448, < 624, au-delà), ou la caméra à égalité (`bgw[1].xy[0].disp.pos` < 544, < 624).
   `0x8C0B4B90` entre dans le script 28 à l'enregistrement `r7 − 1` : images 36163, 36164, 36166.
   Le script n'est pas avancé : l'image est **tenue**. Un changement de regard tient dix trames.
1. **l'aboiement** — script 29, sur `0x8C0D7EFC`.
2. **la queue** — script 30, quand le regard est de face et qu'un ami est à moins de 32 pixels
   (`0x8C0335C4`) ; un coup spécial l'interrompt pour l'aboiement.

**Couché** : le script 40, qui boucle de lui-même, et le script 41 sur `0x8C0D7EFC`.

**`0x8C0D7EFC` est un coup spécial** : un joueur en `routine_no[1] == 4` et `routine_no[2] >= 16`.
Dans 3SX, `plmain_lv_02` range l'état 4 comme l'**attaque**, et `plpat.c` envoie les
`routine_no[2]` de 16 et plus vers la table des coups spéciaux.

### Les scripts se déroulent : ce que `script_images` ne voyait pas

Un enregistrement fait huit octets `{drapeaux, durée, …, image}` et c'est la **durée** qui décide
(`0x8C0B5218`) : non nulle, c'est une image, et son premier octet part en `+0x1D4` (le bit 0
marque la **fin**, que les routines attendent) ; nulle, c'est une commande (`0x8C1C5BC8`) —
`0x01` reprend le script au début, `0x0C`/`0x0D` ouvrent et ferment une boucle dont le compte
est au mot 6. `script_images` saute les commandes, donc joue chaque boucle **une fois**, et
s'arrête au premier `0x01` même quand il porte une durée. `script_deroule` fait le compte juste.

### Ce qui est fait

* **Le masque de variante porte les combattants** : bit `0x10` = aucun ami du décor, `0x20` = un
  ami. `decor_objets.c` (`humeur_du_decor`, `dans_la_variante`) ; le tirage est refait si les
  combattants changent sur le même étage. Le journal de fin de round écrit les deux
  personnages et « ami du décor ».
* **Les objets à comportement** : champ `comportement` et bornes `suite1`/`suite2` dans la fiche
  (écrits seulement pour eux, le C complète à zéro). `conduire` joue la machine à états ; l'état
  n'avance que dans `DecorObjets_Avancer`, donc l'image reste stable pendant le dessin.
* **Chien debout** : 46 images (3 regards, la queue 22, l'aboiement 21), 2 morceaux. **Chien
  couché** : 25 images (repos 12, réveil 13).
* `verifier_objets.py` : borne à 48 (celle du C depuis le 16/09) et budget compté par
  (variante, combattants). Rien à signaler. Cache d'Oro au pire : 49 % (les deux chiens comptés).
* Rendu depuis le C : `chien-oro-avant-apres.png` (scratchpad).

Lanceur `ORO - le chien, debout ou couche selon les combattants.cmd`, exe
`build/3sx-chien.exe`. Sauvegarde : `avant-chien/`.

### La vitesse, mesurée (partie Sean et Oro du 16/09)

Le jeu tient **60 images/s** : 1006 ms pour 60 trames, sur les menus comme en combat. Le calcul
moyen est de 3 à 5 ms par trame dans les menus, **8 à 10 ms chez Oro, 10 à 13 ms chez Sean**,
pour 16,8 ms disponibles. Les « quelques ralentissements » sont des **pointes** : 650 à 740 ms à
l'entrée d'un étage (le chargement), mais aussi **en plein combat** — 237, 199 et 190 ms chez
Sean, 53 ms chez Oro, 215 ms chez Yang. Leur cause n'est pas encore isolée.


## YANG : LES POISSONS NAGENT ; YUN : QUATRE OISEAUX (16/09, nuit)

Frédéric : Oro **validé**. *« YANG BG0B : vérifie le 2ème poisson noir dans l'aquarium ;
YUN BG03 : il y a peut-être plusieurs oiseaux dans la cage, vérifie. »*

### Les poissons de Yang (id 29) : deux, et ils nagent

Le spawner `0x8C02B356` en crée exactement **deux** (`mov #2,r12`), le `type` valant le rang ; la
routine `0x8C02AEEC` choisit par ce `type`. Aucun autre objet de Yang n'utilise leurs images.
Le port les posait **immobiles**, chacun sur son premier script.

**Le rouge** (`0x8C02AF90`, état `+38`), né en 240,136 :

| état | script | ce qu'il fait |
|---|---|---|
| 1 | 82, boucle | nage à gauche à −0,375 px/trame (`0xA000` étendu) jusqu'à x < 160 |
| 2 | 83 | demi-tour, jusqu'à la marque de fin |
| 3 | 84, boucle | nage à droite à +0,375 jusqu'à x > 240 |
| 4 | 85 | demi-tour, puis retour à 1 |

**Le noir** (`0x8C02B0C8`, état `+40`), né en 128,148 — il avance son script **en tête** de trame :

| état | script | mouvement | sortie |
|---|---|---|---|
| 1 | 86 | +0,25 en x | x > 256 |
| 2 | 86 | −0,25 | x < 128 |
| 3 | 86 | +0,25 | x > 256 → script 87 |
| 4 | 87 | — | fin → 88, vitesses −0,25 et −0,3125 |
| 5 | 88 | diagonale vers le bas | y < 112 → 89 |
| 6 | 89 | — | fin → 90 |
| 7 | 90 | −0,25 | x < 160 → 91 |
| 8 | 91 | — | fin → 92, vitesses −0,25 et +0,5 |
| 9 | 92 | diagonale vers le haut | y > 151 → état 1, script 86 |

Le `y` de 2I monte : 148 est dans le haut du bac, 112 près des rochers. Un premier tour dure
environ 2 110 trames (35 s), les suivants un peu moins (il repart de x 141). Mouvements :
`0x8C0D7AD6` (`a[0] += d[0] ; x += a[0]`) et `0x8C0D7B5A` pour y ; accélérations toutes nulles.
Une borne n'écrit que le **mot haut** (`mov.w r4,@(102,…)`) : la fraction reste.

**L'image marquée d'un demi-tour ne se voit pas** : la routine lit la marque juste après
l'avance et pose le script suivant dans la même trame. Le chien, lui, change d'état à la trame
suivante (l'image marquée dure une trame), et un poisson qui nage ignore la marque (l'image
dure son temps, puis `0x01` relance). `script_deroule(…, fin=)` : `"une"`, `"sans"`, `"boucle"`.

### Les oiseaux de Yun : quatre, pas un

La cage (id 23, `0x8C02936E`) crée trois objets de l'**id 21** par `0x8C028E62`, en plus de
l'oiseau de l'id 22 déjà posé. Bloc de dix octets `{script, x, y, priorité, retournement}` en
`0x8C17DD58`, table du décor **+ 36**, vitesses et accélérations en `0x8C17DD78` :

| script | position | |
|---|---|---|
| 36 | 696,64 | dans la cage carrée, avec l'oiseau 42 de l'id 22 (712,56) |
| 38 | 752,84 | étage du haut de la cage ronde |
| 40 | 752,63 | étage du bas, **retourné** (`+10` = 1) |

**Le retrait du 04/09 reposait sur une lecture fausse** : ce spawner écrit bien la position, en
`+102` et `+106` (sites `0x8C028F14`, `0x8C028F24`), à côté de `+84/+86`. Le « panneau » et les
« paniers » n'existaient pas — son script 0 est le 36 du décor.

Leur routine (`0x8C028CE8`) les laisse **perchés** tant que la cage n'est pas frappée
(`u16[0x8C6AF288 + 16]`), puis ils s'envolent (37, 39, 41) et sortent de l'écran. Le port ne
brise pas la cage : ils restent perchés, script en boucle, boucles internes déroulées. Leurs
images sont **ajourées** : les barreaux passent entre leurs pixels. La cage (script 7) est vide.

Le retournement se fait dans le générateur (`miroir`) : 2I pose le pixel d'écart `dx` en
`−dx − 1`, donc l'image se retourne et son bord gauche passe en `−(gauche + largeur)`.

### Ce qui change dans la mécanique

* **Les pas** : un objet à comportement porte `pas` (image, durée) et `suites` (premier pas de
  chaque suite, puis la fin) au lieu de `suite1`/`suite2`. Les pas renvoient à des images
  **distinctes** : le poisson noir enchaîne 66 images et l'identité de motif n'en code que 64 ;
  il en garde 53. Le chien d'Oro passe de 46 à 15 images, sans changer de conduite.
* **Le déplacement** : `DecorObjets_Position` rend la position de la trame ; `eff05.c` l'écrit
  dans `xyz` juste avant `disp_pos_trans_entry_s`, qui la relit.
* **La pause** : les comportements se figent sur `EXE_flag || Game_pause || EXE_obroll`, comme
  `effect_07_move` (2I teste `u8[0x8C6A27D4]`).
* `animer2i` : `deroule` (boucles déroulées) et `miroir` pour les objets simples.
* `verifier_objets.py` accepte les champs nommés en fin de fiche. Rien à signaler ; cache au
  pire : Yun 62 %, Yang 56 %, Oro 47 %.
* Rendus (scratchpad) : `poissons-yang.png` (la conduite simulée comme le C, dessinée depuis les
  tuiles), `oiseaux-yun-avant-apres.png`, `oiseaux-seuls.png`.

Lanceur `YANG ET YUN - les poissons nagent, quatre oiseaux.cmd`, exe `build/3sx-poissons.exe`.
Sauvegarde : `avant-poissons/`.

**Validé par Frédéric** (16/09, nuit) : les poissons de Yang, les quatre oiseaux de Yun et le
chien d'Oro. Partie sans blocage ; Oro joué avec Elena (ami du décor 1, chien debout).


## NEW GENERATION REVUE AVEC CE QUE 2I A APPRIS (16-17/09)

Les objets de NG portent les **mêmes numéros** que ceux de 2I (table d'effets `0x8C1ADA10`
contre `0x8C179FDC`), et beaucoup de spawners sont identiques octet pour octet. Ce qui a été
lu et validé en 2I se transpose donc. Outils : `apparier.py` (appariement des fonctions 2I ↔
NG), `routineng.py`, `cheminng.py` (quels appels une routine d'étage fait pour une aire et un
tirage), `palettes_ramng.py`, `objetsng.py`, `animerng.py` (réécrit), `mesure_origine_ng.py`.

### Les défauts corrigés, tous connus de 2I

1. **Par bande, pas par décor.** `animerng` posait tous les enregistrements d'un décor sur sa
   première bande : la rue et le temple de Hong Kong sur le même étage. Les éléments sont
   maintenant ceux de l'aire, les appels ceux que la routine fait vraiment (`cheminng`,
   exploration des chemins avec `u8[0x8C552674 + 4/5/6]` connus).
2. **Les variantes `z`** portent leur masque, au lieu d'être toutes posées à la fois.
3. **Les débris** du chargeur B (`0x8C0A21A4`, créés quand le parent est frappé, position
   relative au parent) ne sont plus posés. Les enfants du chargeur A le sont si leur parent
   l'est ; leur `x` est absolu (le chargeur écrit `+102` tel quel, la routine id 26 ne lit le
   parent, `+0x32C`, que pour se synchroniser).
4. **Repos / action** (`0x8C0A0070`) : on joue le plus riche des deux scripts.
5. **Les objets à valeurs en dur** transposés de 2I : la ménagerie d'Oro (perroquet, chien,
   chatte et chatons, chauves-souris), la cage de la rue de Hong Kong (quatre oiseaux, le
   fumeur), les poissons du temple (comportements 3 et 4).
6. **Les palettes RAM** : la règle de 2I avec les tables de NG (`palettes_ramng.py`) ; elle
   retrouve seule la base 1397 de la bande 5, trouvée autrefois au détecteur de vert.
7. **Le budget** compte les morceaux vivants au pire (870) au lieu de 256 cases par trame.
8. **L'humeur du chien** vaut pour l'étage 53 : même spawner (`0x8C0A9F06`), même table
   (`0x8C1B2B08` = `0x8C17F364` de 2I).

### L'origine du `x` : la règle de Ryu 2I, pour trois décors de NG

Le décor 2 de NG **est** le décor de Ryu 2I : mêmes enregistrements, mêmes `x` (−233 les
singes, −145 la femme au panneau, −112 la femme en rose, 273 le gros baigneur). Son `x` se
compte donc depuis le milieu de la bande (+512). Deux autres décors ont la même signature —
tous leurs `x` sous 512, beaucoup de négatifs : **Londres** (décor 4, bandes 7-8, `x` de −352 à
479) et **la tente de Munich** (décor 6, bande 10, de −367 à 201). Le 11 (Ken) copie le 2.

| étage | à `x` (enroulé) | à `x` + 512 |
|---|---|---|
| Ryu/Ken (40, 41) | copies peintes 0 à 10 % | **39 à 51 %** sur cinq objets |
| Dudley 2 (45) | immeubles en l'air | l'immeuble prolonge le pub, la maison à colombages se pose sur le mur du pont |
| Hugo (47) | objets aux bords | la chope pend au navire, la banderole sur l'escalier, les poteaux sur le quai |
| Sean, New York (39) | drapeau, escaliers, bouche d'incendie en place | tout décalé : **pas de décalage** |

**Seul le plan 2 est décalé** : la tour du fond de Londres (plan lointain, `x` 479) est au
point de fuite sans décalage, et sort de sa couche avec. Mesure : `mesure_origine_ng.py`
(trou ou copie peinte sous chaque objet, pages brutes du disque).

**Dudley 1 (44)** : sa banque est rangée autrement (la façade du pub en haut) et le rendu ne
permet pas de trancher ; il suit la règle de Dudley 2.

### La famille : celle de la liste qui porte le plan de l'objet

`mlt_obj_matrix` prend `BgMATRIX[my_family]`, `BgMATRIX[n + 1]` étant la matrice de `bgw[n]` :
famille 1 = liste 132, 2 = 196, 3 = 260. Or `etagesng.fiche()` ne range pas les plans de NG
dans le même ordre partout : la bande 7 met son plan 3 (lointain, priorité 104) en liste 132,
la bande 14 son plan 2. L'ancienne règle (« plan 1 et trois plans → famille 3 ») ne valait que
pour les bandes rangées comme Oro. La nouvelle (`famille_du_plan`) rend la même chose pour Oro
et Ibuki, et remet sur leur plan : la tour de Londres (bandes 7, 8), le gratte-ciel lointain
d'Alex (bande 1, plan 3 sans couche : famille de coefficient le plus proche), les objets
d'Elena 1 (bande 14) et le lointain d'Elena 2 (bande 15). Nécro (bande 9) passe en famille 3,
sans effet visible : ses trois coefficients valent 1.

Le gratte-ciel d'Alex a `z` 104 : dans le jeu il ne se voit qu'à travers la trouée entre les
immeubles. Les rendus, qui ignorent `z`, le montrent par-dessus.

### Ce qui reste

* **Les poissons du temple** (Yun 2, Yang 2) : le code de NG les dessine **derrière** la
  vitre de l'aquarium (priorité 87 contre 86), l'inverse de 2I. Posé comme le code ; à
  confirmer sur l'original.
* **Une trentaine d'appels à valeurs en dur non lus** (liste en fin de `animerng.py`) : id 64
  à New York, 65 et 68 à Londres, 115 et 117 chez Ken, 14, 48, 82, 83 chez Ibuki, 45, 53, 56,
  122, 123 chez Elena…
* **Le budget** laisse encore de grands objets de côté, et trois scripts de plus de 64 images.
* **Les onze animations de pages** (cascades d'Ibuki, Ryu, Elena) et les descripteurs de scène.

Lanceur `NEW GENERATION - revue des decors.cmd`, exe `build/3sx-ng.exe`. Sauvegardes :
`avant-ng/`, `avant-origine/`.

---

## NEW GENERATION : LES DÉCORS LUS DANS LE CODE (17/09, après-midi)

Retour de Frédéric sur la revue NG : Gill, Dudley 1, Ibuki ×3 et Elena 2 « cassés », Alex
« arrière-plan à revoir », ciels de Ryu, Ken et Oro incomplets, Elena 1 « uniquement
l'arrière-plan », Necro sans défilement, bandes verticales aux bords.

### Le moteur de décor de NG : des listes de rectangles, comme 2I

NG émule la CPS3. Sa liste d'affichage (`0x8C613004`) porte, pour chaque couche, des ordres
« dessine la carte n » avec des bandes de lignes (table `0x8C4DDBA4`, remplie par
`0x8C146714` : groupes `{plan, profondeur}` puis triplets `{fin, hauteur<<8, drapeaux}`).
**Le Dreamcast ne lit pas ces bandes** : l'interprète `0x8C110BD4` n'en tire que la
profondeur (`0x8C10E3B0` écrit `0x8C5BA154[n]`). Les cartes sont dessinées par
`0x8C10FBCC`, qui parcourt des **listes de rectangles de 20 octets** :

| octets | champ |
|---|---|
| +0 u16 | couche (0..3) ; 0xFFFF termine |
| +2, +3 u8 | x/16, largeur/16 |
| +4, +5 u8 | y/16, hauteur/16 |
| +6 u16 | texture : banque 0 ou 1 du `.pvc` (2, 3 : textures calculées) |
| +8, +10 u16 | u/16, v/16 |
| +12 i32 | attribut CPS3 (couleur, fondu) |
| +16, +17 u8 | ligne défilante (sol en perspective), drapeau de dessin |

Chaque rectangle est redessiné à +1024 : la scène boucle. Le choix des listes est
`0x8C10FEDC`, table de sauts indexée par **la bande** (`u32[0x8C4DF128]`). Une page
d'animation (`u32[0x8C5BD3E4 + 4k]`) ou la carte posée sur une couche choisit une liste de
plus. Les listes sont dans l'image initialisée du `.bss` (fichier −0x12420).

Ce que les listes disent, bande par bande :

* **liste par défaut `0x8C4DF2D8`** (Ken, Yun 1, Necro, Hugo, Oro, Yang 1) : la couche 2 est
  faite du quart haut gauche de la banque 1 (x 0..511) **et de son quart bas gauche**
  (x 512..1023). C'est le ciel « manquant à droite » de Ken et d'Oro.
* **Gill** : la couche 1 n'est que le sol (v 960) ; la couche 0 alterne deux cartes et un
  décalage de 512 lignes (routine id 12, table `0x8C1AFE1C`, 12 trames) : quatre vues de
  l'horizon (v 256, 384, 512, 640).
* **Alex** : couche 0 = le quart haut gauche posé en x 512 ; couche 2 (profondeur 104,
  objet 2 à 0,625) = le ciel, quart haut droit. Alex a maintenant **trois plans**.
* **Ryu** : couche 0 en deux morceaux (les réserves x 0..127 et 496..623 ne sont pas
  posées), cascade 128×256 en 496,768 (entrée 1) ; couche 2 = 320×256 en 192,672 plus un
  morceau animé 256×256 en 512,672 (entrée 3).
* **Dudley 1** : rue (couche 1), ciel de nuit (couche 2), **pluie** (couche 0, profondeur 20,
  quatre cartes × deux décalages, routine id 11, tables `0x8C1AFC24`/`0x8C1AFCE4`).
* **Ibuki 1/2/3** : dix rectangles de base, le vent (id 48 : couche 0 deux cartes × deux
  décalages, table `0x8C1B21A4` ; couche 1 quatre cartes, `0x8C1B221C`), la cascade
  (entrée 4, deux séries selon le défilement vertical), deux clignotements (entrées 9, 10).
* **Elena 1** : une seule couche, le ciel et la savane (banque 0 haut, lignes défilantes en
  bas). Tout le premier plan est fait d'objets.
* **Elena 2** : cascade (entrée 0, douze vues 304×160), bas de la couche 1 selon sa carte :
  **planches** (sa propre carte, le départ) ou falaises seules (après la chute).

Outil : `outils/descripteursng.py` (`CAS`, `ETATS`, `ANIMATIONS`, `page()`).

### Ce qui a changé dans la chaîne

* `couchesng.py` écrit les pages depuis `descripteursng.page()` — dans le dossier de travail
  et dans `SEPTEMBRE\...\CrowdedStreet-3SX\resources\tex_remix`, **pas** dans `%APPDATA%`.
  Les retouches à la main du matin (ciels pavés de Ryu, Ken, Oro, masque de Gill) sont
  remplacées. Sauvegarde de toutes les pages d'avant : scratchpad `pages-avant-desc/`.
* **Les onze animations de pages** sont des objets (`outils/pagesng.py`) : ils ne couvrent que
  les cases qui changent, coupés en morceaux de ≤ 64 cases et ≤ 63 couleurs, famille et
  profondeur de leur plan (un cran devant). Quand un pas laisse transparent ce que le pas 0
  peint (le vent), les cases sont **retirées de la page** (`pagesng_gardees.json`, lu par
  `couchesng`). Budget : les animations de rang 0 d'abord, puis les objets, puis le rang 1.
  Écartés : le vent de la couche 1 d'Ibuki (984 morceaux) ; la pluie de Dudley 1 (plein
  écran) n'est pas tentée, elle est fixe.
* `etagesng.objets` compte les couches que les listes dessinent (le 3e plan d'Alex) ;
  `etagesng.fiche` n'échange plus les plans d'Elena 1 (le ciel sur le plan lent à 0,0625,
  les objets du plan 2 sur la base) ; à coefficient égal, la base est la couche la plus
  proche de 84 et le lointain la plus profonde (Necro : les montagnes sur `bgw[0]`).
  Archive `1551.bin` passée à 96 pages (copie de `1553.bin`).
* `bg.c` : **tous les plans de NG bouclent** (`bg_boucle_x`) — les bandes verticales aux bords
  venaient de l'écrêtage à [0, 0x3FF] (Ken va de −10 à 1052). `bg220.c` : Necro NG (étage 46)
  recule de 5 pixels par trame (`0x8C08A970`, les mêmes instructions que 2I).
* Cache des objets NG : **10 pages** (`PATTERN_PAGES16_MAX`, `ETAGESNG_OB_PAGE`, gix 80..90),
  `MORCEAUX_MAX` 2175, `TAS_NG` 2560.

### Elena 1 est la variante du pont de 2I

Mêmes ids, mêmes enregistrements (scripts + 1), même ciel lent. Ajoutés (`objetsng.EN_DUR`,
clé `(spawner, arg)` possible) : **le pont** (id 123, type 0 : descend de y 384 à 40 puis lève
`u16[0x8C553E0C]` ; posé en 512,40), **les herbes et cordes** (id 122, `0x8C1B33B4`, jouées
une fois : dernière image, option `image_finale`), **l'eau de la rivière** (id 45, script 8,
plan 1, une image toutes les 33 trames, `x` compté du milieu : option `dx`). Elle bouche au
pixel le trou transparent de la banque. Le type 1 du pont (Elena 2) n'est pas posé : son pont
est dans la page.

### Mesuré, pas lu

**Le ciel de Gill est descendu de 80 lignes** (`descripteursng.DECALAGE_Y`). Sa couche 0 finit
à la ligne 879, le sol commence en 960, et les éléments de lave (plan 2) posent en 943..959.
Les bandes de lignes disent le même écart (couche 0 depuis 144, couche 1 jusqu'à 64). Le
décalage vertical qui les rapproche dans le jeu n'est pas retrouvé.

### Ce qui reste

* La pluie de Dudley 1 (fixe), le vent de la couche 1 d'Ibuki.
* Elena 1 : ids 53 et 56 (des animaux à machine à états, tables `0x8C0D9670`, `0x8C0D9658`).
* Sean : la flaque (ids 44, 61, 64) ; les autres objets en dur (Alex 69/64, Dudley 65/68,
  Ibuki 82/75/83/20, Hugo 63, Necro 7, Elena 2 85). Ken 115/117 sont des effets communs.
* Les lignes défilantes (sol en perspective d'Elena 1, `ligne` = 1) ne sont pas émulées.
* Yun 1/2 : sondes posées (`manage.c`, `game.c`), journal attendu.

Lanceur `NEW GENERATION - les decors lus dans le code.cmd`, exe
`build/3sx-ng-descripteurs.exe`.

## NEW GENERATION : LA PLUIE, LA LAVE ET LES PASSANTS (18/09)

Réponse à la deuxième revue de Frédéric. Trois mécaniques nouvelles, et une vingtaine
d'objets lus dans le code.

### 1. Yun 1 et Yun 2 : les joueurs ne répondaient pas

`app_type_tbl[20][20][22]` (`app_data.c`) est indexée par l'ÉTAGE, et elle n'a que 22
colonnes. `appear_data_init_set` la lisait avec `bg_w.stage`, donc **hors bornes** pour les
trente-six étages ajoutés : `[joueur][adversaire][42]` tombe sur `[joueur][adversaire+1][20]`.
Or les colonnes 20 et 21 sont **les stages bonus** — entrée 28 et 27 pour les 400 couples de
combattants. Les étages 42 et 43 (Yun 1 et Yun 2), et eux seuls, tiraient donc l'entrée d'un
stage bonus : les joueurs y entraient comme devant la voiture à casser.

Les étages ajoutés prennent maintenant la **colonne 1**. C'est l'une des cinq (1, 8, 11, 17,
18) dont aucune case ne s'écarte de la valeur commune, dans les deux tables : ni entrée à
domicile (Gill en 0, Sean en 12, qui testent `bg_w.stage` en dur), ni attente d'un décor de
3rd Strike.

### 2. Les plans animés : la pluie de Londres et l'horizon de Gill

Deux animations changent une **couche entière**, sur les 1024 colonnes :

| décor | routine | vues | cadence |
|---|---|---|---|
| Dudley 1, la pluie | id 11 `0x8C09DFBC` | 4 cartes × 2 copies = **8** | 14 motifs d'intensité (`0x8C1AFCE4` → `0x8C1AFC24`), 3 à 7 trames par pas |
| Gill, l'horizon | id 12 `0x8C09E298` | 2 cartes × 2 copies = **4** | 12 trames par pas |

Les quatre cartes de pluie sont quatre textures de la banque (u 0, 256, 512, 768) ; le
décalage de 512 lignes montre l'autre copie de la scène. **Les 32 puces changent à chaque
pas** : en objets animés il faudrait plus de deux mille morceaux, et l'horizon de Gill n'en
posait que ce qui tenait dans le budget — « il manque plusieurs grosses vagues de lave ».

On se sert du mécanisme que 3rd Strike a déjà : la **liste de réécriture** (`rewrite_scr`,
`ppgRwBgList`, chargée avec l'étage en `(plans*64) + 0x64`), que `bgrw` emploie une puce à la
fois. Ici le plan entier bascule : une vue = 32 pages, et `bgDrawOneScreen` déplace l'index
de puce vers la liste de réécriture (`bg.c`, `Plan_Anime`). La suite (durée, vue) est celle
du jeu ; `plansng.py` écrit les pages et `etagesng_pages.inc`.

* archives agrandies : `1550.bin` 160 pages (64 + 96), `1557.bin` 320 pages (96 + 224) ;
* `FL_TEXTURE_MAX` passe de 256 à **512** : l'étage seul dépassait les 256 poignées.

### 3. Le trajet : un objet qui se déplace, décrit par une table

`DecorAnimation.trajet` = `{ durée, vx, vy, suite }` par segment, vitesses en 1/256 de pixel
par trame, et la liste boucle sur son premier segment — où l'objet retrouve sa position de
naissance. Comportement 5 dans `decor_objets.c`.

* **la calèche de Dudley 1** (id 65, `0x8C0A8970`) : 600 trames sous le tunnel, 196 trames à
  −1,125 pixel, puis −1 pixel jusqu'à passer sous x 48, et tout recommence. Le jeu la
  **rétrécit** en chemin (`+0x238`/`+0x23A`, 55/64 au départ, un cran toutes les 7 trames) :
  notre moteur ne met pas un objet à l'échelle, elle garde sa taille.
* **l'eau de la rivière d'Elena 1** (id 45) : elle glisse d'un demi-pixel par trame et revient
  toutes les 33 trames, quand son script avance d'une image.

### 4. Les objets lus dans le code

| décor | objet | ce que dit le code |
|---|---|---|
| tous | lecteur `0x8C0A0070` (id 18) | **deux scripts**, `+150` (repos) et `+152` (action), et pas de `+456` : ses 36 blocs étaient sautés faute de script. Les passants de Hong Kong (Yun 1, Yang 1), la foule de Hugo, le personnage de Necro, ceux de Ryu, Ken et Oro. |
| Necro | id 7 `0x8C09CBF8` + id 8 | le conducteur en 463,77 (script 34) et son voisin en 432,118 (script 18) — les mêmes qu'en 2I, octet pour octet |
| Ibuki 1 et 2 | id 82 → ids 77, 78, 79, 80 | le maître (320,52), le colosse (512,51), le garçon (480,51) et le ninja perché (496,322). Les deux derniers n'existent que dans l'aire 0 (`0x8C0AB874`) ; dans l'aire 1 les deux premiers prennent le script 4 de leur table. |
| Dudley 2 | id 68 `0x8C0A961C`, id 66 (bloc) | les deux punks : 672,47 (script 17) et 720,96 (script 15/16) |
| Alex | id 69 `0x8C0A9806` | l'arrière de la voiture, 192,48, script 16 |
| Sean | id 44 `0x8C0A4C38` | **quatorze immeubles de New York**, bloc `0x8C1B1DA4`, table `0x8C0D1080` (images dans F_ETC35). Le reflet dans la flaque est le script 1 (528,8, profondeur 95 : derrière la rue, vu par le trou). Les plans 3 et 5 n'ont pas de couche — coefficient nul, ou hors de la table : ils suivent le plan le plus lent. |
| Sean, variante 0 | ids 61 et 62 | les deux costauds, 392,58 et 448,58 |
| Yun 2, Yang 2 | id 28, enfant 0 du vase | le monsieur en vert, 496,64, script 76 — `0x8C0A1A6C` le crée quand l'index d'enfant vaut 0 |
| Elena 1 | id 53 | l'oiseau posé, 656,48, script 22 (il s'envole au bout de 148 trames : pas repris) |

**Un enfant n'existe que là où son parent existe**, et son `x` suit le drapeau `+118`. Le
motard de Sean (script 18) était posé dans les quatre variantes et en x −304 — « personnage de
droite à revoir, n'existe pas normalement ». `+118 = 1` marque exactement les objets dont le x
se compte du milieu de la bande (tous ceux de Ryu, de Londres et de la fête de Hugo le
portent) : il est en 208, à côté de sa moto, et seulement dans la variante 3.

**Les cordes du pont d'Elena 1** restent sur leur PREMIÈRE image (corde tendue). On posait la
dernière : la corde à terre, après la chute du pont. C'est ce que 2I pose aussi.

### Ce qui reste

* Ibuki 3 n'a pas de personnage dans le code : ses objets sont des nuages (id 83, plan 3) et
  de petits sprites tirés au hasard (id 20 → id 67), tous mobiles.
* Elena 1, l'id 56 : un oiseau qui entre par la gauche (x −256) ; hors champ tant qu'il ne
  vole pas.
* Le vent sur la couche 1 d'Ibuki (984 morceaux) ; les passants mobiles d'Alex et de Sean
  (id 64, quatre comportements de marche) ; la mise à l'échelle de la calèche.
* Les bandes verticales de Ryu et Ken : aucune colonne vide dans le modèle, aux deux butées
  et caméra levée. À revoir sur une capture.
* Yang 1, les fenêtres de droite : la page porte bien le bleu (les portes du temple), même
  dans l'ordre de profondeur. À revoir sur une capture.

## NEW GENERATION : LES VERDICTS DU 19/09, TRAITÉS (22/09)

Réponse à la troisième revue de Frédéric (`REPRISE-2026-09-19.md`, section 1). Ce qui
suit est fait, régénéré et compilé : exe `build/3sx-ng-revue3.exe`, lanceur
`NEW GENERATION - Sean en couleurs, la lave de Gill, les bords de Ryu et Ken.cmd`.

### 1. Sean, l'arrière-plan aux couleurs glitchées — LA BASE DE PALETTE, MESURÉE

Les quatorze immeubles de New York (id 44, bloc `0x8C1B1DA4`, table `0x8C0D1080`) sont des
sprites **à huit bits** : leurs index montent à 255, et aucun autre objet de NG ne dépasse
63. Le port les coloriait avec une seule palette de 64 : les index > 63 lisaient les
emplacements voisins, d'où les aplats jaunes et mauves.

Une palette de 256 couleurs, c'est **quatre emplacements consécutifs**, et l'offset du
morceau les compte par banque de 256. La base manquait. Elle a été trouvée par la mesure :
chaque base candidate notée par **l'écart de couleur moyen entre pixels voisins** — une
palette fausse hache l'image. Sur les 560 bases autour des transferts que la bande exécute
vraiment, le minimum est net :

| base | écart moyen |
|---|---|
| **192** — second transfert de la bande 2 | **2,63** |
| 168 — premier transfert | 3,97 |
| tout le reste | ~6 |

Et 192 est *exactement* la base du second transfert (`0x8C18ABE4`, entrée 71, destination
`0x12000` = emplacement 576, 24 palettes) : les quatre offsets des immeubles (0, 1, 2, 4)
y tombent tous dedans — 576..579, 580..583, 584..587, 592..595. C'est cette concordance qui
tranche, pas le seul minimum.

**Le balayage complet des 27 763 palettes du binaire ne vaut rien** : il rend des dizaines
de bases à écart 0,000, qui sont des palettes VIDES — une image toute noire ne hache rien.
Il faut borner aux transferts de la bande. Le détecteur de vert ne départage pas ici :
aucun vert dans les candidats de tête.

**Le budget.** Découper ces sprites par quart de palette donnait **71 fiches à Sean pour les
56 places d'`OBJETS_MAX`** (mesuré par `verifier_objets`), et monter `OBJETS_MAX` mangerait
le tas d'effets du jeu (128 en tout). On sert donc chaque immeuble en UNE fiche, avec sa
palette effective ramenée aux **63 couleurs les plus peintes**, chaque autre envoyée sur la
plus proche. L'écart moyen mesuré va de **0,00 à 0,32 sur 93** (trois canaux de 5 bits) :
ces palettes de 256 sont pleines de quasi-doublons. Sean retombe à 51 fiches, et
`verifier_objets` dit « Rien à signaler ».

Outils : `assemblage.poser_1555(huit_bits=True)`, `animerng.num_de_morceau_8bits`,
`animerng.bloc_c_1555` (réduction), `animerng.groupes_palette` (pas de découpage pour un
sprite à huit bits).

### 2. Ibuki, le réverbère devant les bambous — NEW GENERATION NE LE POSE NULLE PART

L'élément `0x8C1AEEA0` (plan 5, x 288, y 96, profondeur 73, script 1) **sort de la table de
parallaxe**. Lu dans le binaire :

* `0x8C0862CC` : un objet va chercher sa table de défilement par ligne en
  `contexte[+128 + (plan − 1) × 144]` — **le plan p lit l'entrée p − 1** ;
* la table de coefficients `0x8C189BA0` a un **pas de 32 octets par bande**, soit
  **quatre** entrées de huit : une bande de NG n'a jamais plus de quatre plans ;
* `0x8C088042` pose `contexte[+16] = u16[0x8C18965C + bande × 2]` — 2 ou 3 selon la bande,
  exactement le nombre d'entrées non nulles — et les deux boucles d'initialisation des plans
  (`0x8C0881A8`, `0x8C088242`) s'y arrêtent. Ibuki (bandes 11, 12, 13) : **trois plans**.

Plan 5 n'a donc ni coefficient, ni couche, ni matrice. `objetsng` écarte les éléments de
plan > 4 (`PLANS_MAX`), et lui seul sort — les trois étages d'Ibuki.

**On n'écarte PAS les plans 3 et 4 sur une bande qui n'en déclare que deux** : leur entrée
existe (coefficient nul, un plan fixe), et comme ces éléments ont `+118 = 0`, `0x8C086316`
ne va jamais chercher leur table de défilement — leur position est leur position de fiche.
C'est le cas de la rivière d'Elena 1 (`0x8C1AF79A`) et d'un objet d'Elena 2
(`0x8C1AF7AC`), que Frédéric a validés le 18/09. La règle large les aurait retirés.

### 3. Ryu et Ken, les bandes verticales — les butées resserrées

`limites.sans_bande()` (écrit le 19/09) est appliqué : `etagesng_plans.inc` régénéré par
`E.ecrire_include([E.fiche(b) for b in range(19)], ...)`, et **le diff ne porte que sur
`ETAGESNG_LIMIT`, sur deux étages** :

    Ryu (bande 3, plan 1)   0x013A..0x02C4  ->  0x0140..0x02C0   (320..704)
    Ken (bande 4, plan 1)   0x00B6..0x035D  ->  0x00C0..0x0340   (192..832)

**Correction de `limites.py`** : la note disait que `0x8C0DA7F8` recopie la paire large sur
l'étroite « si `u8[0x8C841F3C]` n'est pas nul ». C'est l'inverse : `0x8C0DA7F4` fait
`tst r2,r2 ; bf 0x8C0DA814`, et `bf` **saute** la recopie quand l'octet n'est pas nul —
donc la recopie a lieu quand il est NUL. New Generation a les mêmes instructions en
`0x8C08833A`. La conclusion, elle, ne change pas : c'est la paire large qu'on garde.

### 4. Gill — les vagues de lave passent, et le budget a dû bouger

Les cinq vagues (id 47) et les six gerbes (id 19) écrites le 19/09 portent la demande de
Gill à **2221 morceaux**. `MORCEAUX_MAX` valait 2175 (dix pages, 2560 morceaux, 15 % de
marge) : le budget écartait Gill de 46 morceaux et rendait alors **son plus gros élément**
(script 3, quatre fiches, 161 morceaux) — un objet qui marche aujourd'hui. `MORCEAUX_MAX`
passe à **2240**, soit 12,5 % de marge ; 2221 sur 2560, c'est 87 % du cache, loin des 108 %
qui faisaient figer Hugo. Mesure d'après coup (`verifier_objets`) : **1769 morceaux
vivants** sur l'étage 37. Gill passe de 33 à 48 fiches.

Le repli par objet (`animerng.fiche`) est en place : seuls `n00o8` et `n00o9` changent.

### 5. Hugo — l'étage 47 est retiré de la sélection

`Handicap_Stage_Move_Sub` saute 47 comme il saute déjà 17 et 21, dans les deux sens. Les
noms d'`eff99.c` et les fichiers de Hugo restent en place ; il n'est simplement plus
proposable. `VS_STAGE_MAX` ne bouge pas.

### 6. Dudley 1, le chargement très long — une part, pas tout

Mesuré : **320 pages déployées pour l'étage 44, dont 177 distinctes** (les autres étages :
96 pages, 50 à 69 distinctes). Deux coûts ôtés, tous deux dans `tex_remix.c` :

* l'**empreinte** de chaque page (FNV-1a, octet par octet sur toute la page) était calculée
  même pour un étage ajouté, qui retrouve ses pages PAR NUMÉRO et n'en a aucun besoin. Elle
  n'est plus prise que pour le vidage, ou quand la recherche par numéro n'a rien donné ;
* la **trace par page remplacée** passe de INFO à DEBUG : c'étaient 320 lignes de journal
  à chaque entrée dans le décor.

**Ce qui reste le gros morceau** : 177 pages distinctes sur 320, donc environ 45 % de
lectures et de téléversements en double. Les dédoublonner demande une table
`(vue, puce) -> page` dans `bg.c` et dans `plansng.py` ; ce n'est pas fait.

### Les réponses aux trois questions

* **Yun 1 contre Yang 1, Yun 2 contre Yang 2** (`0x8C18A804`, décor -> bande par aire,
  l'aire suivant le round). Yun (décor 3) : round 1 = Yun 1 (bande 5), rounds 2 et 3 =
  Yun 2 (bande 6). Yang (décor 10) : round 1 = Yang 2 (bande 18), rounds 2 et 3 = Yang 1
  (bande 17).
  * **Yun 2 = Yang 2** : `bg_set06.pvc` et `bg_set12.pvc` sont identiques octet pour octet,
    même palette (58), mêmes objets. Ce sont deux noms pour le même décor.
  * **Yun 1 et Yang 1** : même palette (57), mêmes objets, et leurs `.pvc` ne diffèrent que
    par la banque 1 — **le ciel**. Celui de Yang 1 est rempli de bleu plus bas et plus à
    droite (x 128..511 lignes 288..511, et x 0..383 lignes 800..1007). C'est ce ciel qu'on
    voit par les fenêtres du temple. **Le modèle dit donc l'inverse de ce que Frédéric a
    vu** (il voit les fenêtres de Yang 1 noires, le modèle les donne bleues) : deux
    captures, les fenêtres de Yun 1 et celles de Yang 1, trancheraient.
* **Les quatre variantes de Sean — CONFIRMÉ POUR NEW GENERATION.** `0x8C085F4E`, à chaque
  entrée d'étage : le compteur `contexte[+0]` avance d'un, puis `jsr 0x8C0191C0` — un
  compteur de 16 bits qui avance, masqué à 63, indexe une table de 64 mots
  (`0x8C153C04`) — et le résultat est rangé en `contexte[+6]`, aussitôt réduit par
  `and #3`. La suite des 64 tirages est
  `1013212012012332033300332131123030111221303212201122300012230030` : **seize 0, seize 1,
  seize 2 et seize 3**, donc uniforme sur son cycle. C'est un tirage par entrée d'étage,
  comme en 2I. Le port fait pareil (`tirer_la_variante`, `rand() & 3` une fois par étage et
  par couple de combattants ; `SF3_DECOR_VARIANTE=0..3` la force). Chez Sean : variante 0 =
  les deux costauds, variante 3 = le motard à côté de sa moto.
* **Hugo** : ébauche du décor de 2I, inaccessible dans NG — il est le n° 6 de la liste de
  mise au point `0x8C1B7E00` mais pas jouable. Retiré de la sélection (§5).

### Ce qui reste ouvert

* **Dudley 1** : le rétrécissement de la calèche (le moteur du port ne met pas un objet à
  l'échelle ; `mlt_obj_matrix` sait le faire, il faut le pivot de `DecorObjets_Position` et
  la loi de `0x8C0A8970`, `+0x238`/`+0x23A`), et les 143 pages en double au chargement.
* **Elena 1** : les oiseaux qui volent au loin. Le spawner est lu (`0x8C0A707A`, id 56,
  x −256 avec `+118 = 1` donc compté du milieu, y 112, plan 1, profondeur 81, `+554` = 87,
  table `0x8C0D9658`, `+52 = 108`), mais le script n'est pas résolu : il est posé par
  `0x8C03324C`, qu'il faut lire.
* **Alex**, le rectangle de pixels noirs vers x 268, y 126 ; **Necro** et **Yun 1 / Yang 1**,
  la femme d'un pixel. Pas regardés. (**Gill**, la ligne de pixels en bas d'écran :
  trouvée le 22/09, voir la section suivante.)
* **Ibuki**, le vent de la couche 1 (984 morceaux) : toujours hors budget.

### GILL, LA LIGNE DE PIXELS EN BAS D'ÉCRAN — TROUVÉE (22/09, sur capture)

Elle était « non trouvée » le 19/09. La capture de Frédéric la donne.

**Mesuré sur l'image.** La fenêtre montre les 224 lignes du jeu étirées sur 288 (64 lignes
doublées, voisin le plus proche) ; la ligne fautive est la **175ᵉ des 224**, visible sur
**290 colonnes sur 384** — les 94 autres sont celles que les combattants couvrent. Sa
couleur moyenne est **(213, 119, 76)**, celle des lignes juste au-dessus et juste en
dessous **(90, 38, 15)**. Sa corrélation avec ses deux voisines est nulle (0,12 à 0,28,
certaines négatives) : **ce n'est pas un mélange, c'est une autre couche**.

**Et l'autre couche se nomme.** Dans les pages déployées de l'étage 37 :

| | couleur moyenne |
|---|---|
| horizon (liste 132), lignes de scène 948..959 | (175, 90, 72) — la lave |
| sol (liste 196), à partir de 960 | (89, 37, 14) — la roche |

La ligne est de la lave entre deux lignes de roche : **le sol est dessiné un pixel trop
bas, et par la fente on voit l'horizon.**

**La cause est dans la géométrie des couches, pas dans l'artwork.** L'horizon de Gill peint
jusqu'à la ligne de scène 959 et plus rien après ; le sol commence à 960 et rien avant. Les
deux **se touchent sans se recouvrir d'un seul pixel**. Il suffit d'un pixel de jeu dans
l'arrondi du moteur pour ouvrir la fente.

**Gill est le seul des dix-neuf étages dans ce cas** — mesure sur les 19 : partout ailleurs
les couches se chevauchent de plusieurs dizaines de lignes (Alex 512..1007 contre 584..1023,
Ibuki 624..911 contre 528..1023, etc.). C'est pour ça que la ligne ne se voyait que chez
Gill.

**Correction** : `couchesng.recoller()` détecte une jonction sans recouvrement entre deux
couches d'un même étage et donne une ligne de recouvrement à la couche **la plus proche**
(z le plus petit), en recopiant sa première ligne peinte une ligne plus haut. Le sol de
Gill couvre maintenant 959..1023. Là où le moteur ne se trompe pas, le sol ne fait que
gagner un pixel sur l'horizon qu'il cachait déjà ; là où il se trompe, il bouche la fente.
Aucun autre étage n'est touché (le message le dit à la génération).

Ce que ça ne dit pas : **d'où vient le pixel de décalage dans le moteur**. Les deux plans
de Gill ont le même coefficient vertical (`msp[1] = 0x10000`) et passent par le même
`Bg_Family_Set` ; la divergence est plus bas, dans l'accumulateur 16.16 de `xy[1].disp.pos`
ou dans le placement du quad. Le recouvrement la rend inoffensive, il ne l'explique pas.

### SEAN : LES DEUX MOITIÉS HORIZONTALES DU DÉCOR (22/09) — MESURÉ, PAS RÉSOLU

Frédéric, sur la capture du 22/09 : « *les 2 moitiés horizontales du décor n'ont pas la
même palette de couleur* ». Il a raison, et la coupure est nette : au zoom, une ligne
horizontale traverse la neige de bord à bord, le gris-mauve au-dessus, le rose-lavande en
dessous.

**Ce que le descripteur de scène dit.** Sean (bande 2) n'a que DEUX rectangles, tous deux
dans la banque 0 de `bg_set02.pvc`, tous deux posés en scène (0, 512) sur 1024 × 512 :

| couche | u, v | plan | profondeur | coefficient x | drapeau (+17) |
|---|---|---|---|---|---|
| 0 | 0, 0 (moitié HAUTE de la banque) | 1 | 114 (le plus loin) | 0,625 | **1** |
| 1 | 0, 512 (moitié BASSE) | 2 | 94 | 1,0 | 0 |

**Les couleurs viennent du `.pvc`, pas de nous.** Les banques de NG sont en ARGB1555
DIRECT : aucune palette n'est choisie de notre côté pour ces pages, contrairement aux
objets. Et l'attribut CPS3 du rectangle (+12) vaut `0x240` sur **145 des 146 rectangles**
des dix-neuf étages : il ne teinte pas une couche plutôt qu'une autre. Mesure des deux
moitiés de la banque : la haute est à (137, 93, 169), mauve ; la basse à (116, 89, 112),
chaude. La corrélation de leurs luminances là où les deux peignent est de −0,12 : ce ne
sont pas deux versions colorées d'un même dessin, ce sont deux dessins.

**Où tombe la coupure.** La couche lointaine peint la scène de 512 à **895** et plus rien
après (ses douze dernières lignes font 336 px chacune et se répètent par période 10) ; la
couche proche peint de 584 à 1023, et ne devient franchement opaque qu'à partir de 923. Au
dessus de 895, le lointain mauve bouche les trous du proche ; en dessous, il n'y a plus que
le proche. C'est la ligne que Frédéric voit.

**Le seul champ qui distingue les deux couches, et que nous ignorons, est le drapeau
`+17`.** Relevé sur les dix-neuf bandes : il vaut 1 sur **exactement la couche la plus
lointaine** de presque chaque bande (33 rectangles sur 146), 0 sur les autres. Gill est le
seul à l'avoir sur DEUX couches — et c'est aussi le seul décor dont personne n'a jamais
signalé les couleurs. `descripteursng.composer()` ne le lit pas. Reste à lire ce que
`0x8C10FBCC` en fait.

**Ce qui trancherait sans lire le code** : est-ce que la coupure GLISSE quand la caméra
bouge ? Les deux couches défilent à 0,625 et 1,0 ; si les deux moitiés se décalent l'une
par rapport à l'autre, c'est bien une couche posée là où elle ne devrait pas être, et pas
un traitement de couleur qui nous manque.

### LE DRAPEAU `+17` D'UN RECTANGLE DE SCÈNE : LU (22/09)

Frédéric : « *lis `0x8C10FBCC` pour savoir ce que fait le drapeau* ». Fait, jusqu'au
matériel. La chaîne :

1. **`0x8C10FD1C`** — dans le dessinateur de rectangles, `mov #17,r0 ; mov.b @(r0,r14),r3`
   puis `mov.l r3,@-r15` : l'octet `+17` de l'enregistrement est **empilé** comme troisième
   argument de pile du constructeur de quadrilatères `0x8C10F8A2` (les deux autres étant la
   largeur et le nombre de bandes de lignes).
2. **`0x8C10FAD2`** — le constructeur le relit en `@(156, r15)`, fait `tst r7,r7 ; movt r7` :
   il passe donc **`drapeau == 0`** en `r7` à la routine `0x8C4F0F34`.
3. **`0x8C4F0F34`** — `tst r7,r7 ; bt` : deux branches qui appellent le MÊME réglage
   `0x8C4FE0A0` avec deux mots différents, puis deux fermetures de liste différentes :

   | drapeau | mot de réglage | fermeture |
   |---|---|---|
   | **0** | `0x0210000A` | `0x8C4FD730`, qui lit `+20` du contexte `0x8C4FD820` |
   | **1** | `0x0008000A` | `0x8C4FD684`, qui lit `+16` du même contexte |

4. **`0x8C4EF412`** (même famille que `0x8C4FE0A0`) montre où vont les bits du mot : ceux
   de masque `0x020000FF` dans le mot `+144` du contexte, ceux de masque `0x00180000` dans
   le mot `+152`. Les deux mots ne diffèrent donc que par **le bit 25** et par **le bit 20
   contre le bit 19**.

Dans le mot TSP du PowerVR2, le bit 20 est *Use Alpha* et le bit 19 *Ignore Texture Alpha*,
et les deux fermetures sont deux **listes d'affichage** distinctes (l'opaque et la
translucide). D'où la lecture :

> **`drapeau = 1` : le rectangle est dessiné OPAQUE, l'alpha de la texture ignoré, dans la
> liste opaque. `drapeau = 0` : il est dessiné avec l'alpha, dans la liste translucide.**

**Le relevé le confirme sans exception** : sur les 146 rectangles des dix-neuf étages, les
33 qui portent le drapeau sont **toujours ceux de la couche la plus lointaine** — le fond
opaque — et tous les autres sont les couches posées par-dessus. Chez Gill les rectangles
sont serrés (le sol est y 960 sur 64 lignes) ; chez Sean le fond est un 1024 × 512 plein.

**Ce que ça change pour notre chaîne, et pourquoi on ne l'applique pas.** Pour une couche
au drapeau 1, un texel `0x0000` est NOIR et non transparent : `bande3sx.banque_rgba` y perce
un trou. Mesuré, ça ferait basculer jusqu'à **524 288 pixels** sur un étage (Hugo), 409 600
chez Necro, 448 256 chez Oro. Mais ces couches sont **les plus lointaines** : rien n'est
derrière elles, et un trou y montre déjà du noir. Le changement serait donc invisible pour
un risque considérable sur des décors que Frédéric a validés. On note la règle, on ne la
pose pas.

**Et ce n'est PAS la cause des deux moitiés de Sean.** Les deux couches de Sean se
distinguent bien par ce drapeau (fond opaque en haut, couche alpha en bas), mais le drapeau
ne teinte rien : il choisit une liste et un mode d'alpha. La différence de couleur est dans
le `.pvc` lui-même. Contrôle : corrélation croisée des deux demi-banques sur tous les
décalages verticaux de −200 à +200 lignes — le maximum est **0,21**. Ce ne sont pas deux
versions colorées d'un même dessin ; ce sont deux dessins.

### `0x8C10FB64` : L'ATTRIBUT D'UN RECTANGLE EST UN CODE COULEUR, ET IL TRANCHE POUR SEAN (22/09, soir)

Lu instruction par instruction :

    r6 = attribut & 0x01FF                  <- les neuf bits bas
    r0 = (attribut & 0x0600) ? r6 : r6 * 4
    octet = u8[0x8C5B8DA0 + r0]
    si (octet & 0x40) == 0 : pas de fondu   (jmp 0x8C4F1390)
    n = octet & 0x1F ; f = n / 31.0
    si (octet & 0x20) : couleur 0xFFFFFFFF (BLANC), force f
    sinon              : couleur 0xFF000000 (NOIR),  force 1 - f
    jmp 0x8C4F13C0

La table `0x8C5B8DA0` est écrite par **`0x8C10E712`** : `table[adresse_palette >> 7]` sur
`(taille + 63) >> 6` entrées — **un octet de fondu par emplacement de palette de 64
couleurs**, mis à jour chaque fois que le côté CPS3 écrit cette plage. C'est le fondu par
banque de la CPS3.

**Donc les neuf bits bas de l'attribut sont l'EMPLACEMENT DE PALETTE RAM d'une couche,
exactement comme `+554` pour un objet.** Les deux couches de Sean portent `0x240` :
emplacement **64** — la destination du **premier** transfert de la bande 2 (`0x2000`),
base **168** dans le binaire.

### Les deux moitiés de Sean : des OBJETS en haut, des PAGES en bas

Mesure sur l'écran composé (`ecran_ng`, étage 39) : les lignes 0 à 110 sont peintes par les
**objets**, jusqu'à 384 colonnes sur 384 ; les lignes 112 à 223 par les **pages**, 250 à 350
colonnes sur 384. La coupure est nette entre la ligne 104 et la ligne 112. Ce sont les deux
moitiés que Frédéric voit — les immeubles contre les couches, pas une couche contre l'autre.

**Correction** : `animerng.num_de_morceau_8bits` prend maintenant la base du **premier**
transfert (168 pour la bande 2) et non du second (192). Les immeubles tirent sur la même
banque que les couches de leur décor, ce que le décor dit lui-même par son code couleur.

Contrôle par la mesure : coloriés depuis 168, les immeubles ont pour moyenne (95, 64, 91)
contre (137, 93, 169) pour la page lointaine — qui porte la même ville ; depuis 192 ils
tombent à (61, 40, 58). Écart total aux trois canaux : **148 contre 240**.

**Ce que la première mesure disait, et pourquoi on ne la suit pas.** Noter chaque base par
l'écart de couleur moyen entre pixels voisins donnait 2,63 à la base 192 et 3,97 à la
base 168. Ce critère ne dit que la RÉGULARITÉ d'une palette, pas sa justesse : il préfère la
plus plate. Le code couleur des couches, lui, se lit dans le décor.

### LA ZONE NOIRE DE SEAN, ET CE QUE LE DRAPEAU `+17` RÉPARE (22/09, nuit)

Frédéric : « *il manque une partie du décor à gauche (zone noire)* ». Mesuré sur la
capture : un **coin noir en biseau**, 23 px de large et 9 de haut, bord gauche vertical,
hypoténuse descendante — à l'écran lignes 143 à 151, colonnes 327 à 348, caméra à la butée
gauche.

**Le modèle le reproduit**, au même endroit et à la même forme ; ce n'est donc pas le
moteur, c'est nos pages. Et dans les pages, la mesure est nette :

    couche lointaine (liste 132)   peint la scène 512..895, puis plus rien
    couche proche    (liste 196)   ne commence qu'à 924, et son bord haut est en biseau

Entre les deux, **vingt-huit lignes que personne ne peint**. Le biseau vient du bord de la
couche proche. Dans la **variante 0** les deux costauds (ids 61 et 62, 392,58 et 448,58) se
tiennent juste là et le cachent ; dans les variantes 1, 2 et 3 il se voit. C'est pour ça
qu'il n'apparaît pas à tous les coups.

**Le drapeau `+17` dit quoi en faire.** La couche lointaine le porte : c'est le **fond
opaque**, dessiné sur TOUT son rectangle, alpha de texture ignoré. Or son rectangle descend
jusqu'à la ligne 1023 alors que son art s'arrête à 895. `couchesng.prolonger_le_fond()`
prolonge donc chaque colonne du fond jusqu'au bas de son rectangle, en recopiant son dernier
pixel peint. Pas de garde sur les autres couches : elles ne défilent pas à la même vitesse,
donc une même colonne de scène n'y désigne pas le même endroit de l'écran — et la garde est
inutile, puisque la couche au drapeau est la plus lointaine de l'étage. Ce qu'on ajoute ne
peut remplacer que du noir.

Onze étages sont prolongés (Sean 144 750 px, Dudley 2 193 536, Yun 1 172 032, Necro 114 688,
Oro 70 400, Dudley 1 26 880, Elena 1 24 576, Ibuki 2 et 3 16 896 chacun, Yang 1 12 288,
Ibuki 1 6 144).

### Les jonctions, colonne par colonne — et le rectangle noir d'Alex

`couchesng.recoller()` ne regardait que les bornes **globales** d'une couche : le seul cas de
Gill. Il travaille maintenant **colonne par colonne**, et comble tout intervalle d'au plus
quatre lignes entre le bas d'une couche et le haut d'une autre, en recopiant vers le haut le
premier pixel peint de la plus proche (un intervalle nul — deux couches qui se touchent — vaut
quand même une ligne de recouvrement : c'est le cas de Gill).

Trois étages en sortent :

| étage | colonnes | ce que c'était |
|---|---|---|
| Gill | 960 | la ligne de lave en bas d'écran |
| **Alex** | **2** | le petit rectangle de pixels noirs **près de la rampe de l'escalier** — ligne 110, colonnes 266 à 273, le « vers x 268 » du verdict du 18/09 |
| Sean | 9 | le haut du biseau |

Après quoi, plus aucun pixel non peint sur les dix-neuf étages, aux deux butées de caméra et
au milieu, dans les quatre variantes.

### VERDICT DU 22/09 AU SOIR : LE FOND PROLONGÉ EST RETIRÉ

Frédéric, sur l'essai : « *le triangle est passé de noir à bleu. Correction très
mauvaise.* » Prolonger le fond opaque jusqu'au bas de son rectangle en recopiant sa
dernière ligne peinte donne un **aplat** de cette couleur — chez Sean, un biseau bleu à la
place d'un biseau noir. **`couchesng.prolonger_le_fond()` est retiré**, les pages sont
réécrites, et l'état déployé est revenu à celui d'avant l'essai : le biseau de Sean est de
nouveau noir (127 px, variantes 1, 2 et 3).

Ce qui RESTE en place, et qu'il n'a pas jugé mauvais : `recoller()` colonne par colonne —
Gill (960 colonnes, la ligne de lave), Alex (2 colonnes) et Sean (9 colonnes, le haut du
biseau).

**Sa piste, à reprendre :** *« les arrière-plans ne sont-ils pas tout simplement mal
positionnés ? »* Elle tient debout, et elle a un précédent dans ce document : le ciel de
Gill est **descendu de 80 lignes** (`descripteursng.DECALAGE_Y`), une valeur mesurée à
l'écran dont il est écrit noir sur blanc que « le décalage vertical qui les rapproche dans
le jeu n'est pas retrouvé ». Chez Sean, le même genre de décalage refermerait les
vingt-huit lignes de 896 à 923 sans rien inventer : l'art de la couche lointaine fait
384 lignes dans un rectangle qui en déclare 512, et rien ne dit qu'il se pose en haut de ce
rectangle. À chercher du côté de ce qui fixe l'origine verticale d'un plan — `0x8C10FBCC`
lit `+4` (y/16) et `+5` (hauteur/16) du rectangle, mais le moteur DC dessine un plan comme
une texture 1024 × 512 qui **se répète** avec une ligne du haut en `(y + 20) & 0x1FF`
(§ « LE DESCRIPTEUR DE SCÈNE »). Ces vingt lignes et ce repli sur 512 n'ont jamais été
vérifiés côté New Generation.

---

### LE `1024 × 512` ET LE `& 0x1FF` SONT PÉRIMÉS — À NE PAS REPORTER SUR NG (23/09)

Frédéric, le 22/09 au soir : « *le moteur DC dessine un plan comme une texture 1024 × 512 qui
se répète, avec une ligne du haut en `(y + 20) & 0x1FF`* ». La phrase vient d'ici, du point 4
du 16/09 — **et elle a été corrigée douze lignes plus bas dans cette même section**, le même
jour. Ce qui fait foi :

> « Écran x = x − ((défilement x + 1) & 0x3FF), écran y = y − ((défilement y + 20) & 0x3FF),
> et chaque rectangle est redessiné à +1024 en x et en y : la scène boucle. **La banque n'est
> qu'un atlas.** L'ancienne piste `0x8C0F84E6` (un plan = la texture entière) n'est prise que
> par deux chemins particuliers : ce n'est pas le dessin des décors. »

Donc, pour la vérification côté New Generation : **pas d'équivalent de `0x8C0F84E6` à
chercher, pas de repli sur 512, pas de masque `& 0x1FF`.** La scène boucle sur 1024, comme
nos pages. Ce qui reste vrai de la question de Frédéric, et qui n'a jamais été vérifié en NG,
c'est le **`+20` appliqué au défilement vertical** (et le `+1` en x).

**CE QUI A ÉTÉ FAIT POUR 2I, ET PAS POUR NG.** Sa question du 23/09 : « *ça a été fait pour
2I ?* » — oui. Le descripteur de 2I a été lu jusqu'à la formule d'écran, et c'est cette
lecture qui a permis de vider `couches2i.FABRIQUER` et `couches2i.DECALAGE`, tous deux `{}`
aujourd'hui : le décalage de 128 colonnes du ciel d'Ibuki, trouvé en bouchant des vides, est
tombé dès que le descripteur a montré que « *le vide que le décalage bouchait venait de la
mosaïque elle-même* ». **La lecture a tué le réglage à l'œil.**

Côté NG, la moitié du travail est faite : `0x8C10FBCC` (les listes de rectangles de 20
octets), `0x8C10FEDC` (la table de sauts par bande), les onze champs, le drapeau `+17`,
l'attribut `+12`. **La moitié qui manque est la formule d'écran** : `descripteursng.poser()`
pose chaque rectangle à son `x`, `y` bruts et replie sur 1024, sans aucun `+1`, sans aucun
`+20` — personne n'a ouvert le calcul des sommets dans `0x8C10FBCC`. C'est là, et nulle part
ailleurs, que se trouvent les 80 lignes de Gill (`descripteursng.DECALAGE_Y`, mesurée à
l'œil) et les 28 de Sean.

---

## LE RASTÉRISEUR DE PLANS DE NEW GENERATION, DE BOUT EN BOUT (23/09)

Demandé par Frédéric. Lu dans `SF3_1ST.BIN`, sans capture.

### 1. `0x8C10FBCC` — la boucle

    couches : n = 0..3, contexte = 0x8C6D3024 + 16 n
       +0  u16  défilement x        +2  u16  défilement y        +6  u16  drapeaux
       drapeau 0x8000 : la couche est sautée (0x8C10FC00)
       drapeau 0x4000 : défilement par ligne autorisé (0x8C10FC9E)
    profondeur de la couche : flottant en 0x8C5BA154 + 4 n, passé en fr4
    rectangles : 20 octets, +0 = couche, 0xFFFF termine (0x8C10FEA2 : `add #20,r14`)

Les deux constantes sont posées à l'entrée, **avant toute boucle** (`r8 = 0x3FF`,
`r9 = 0x400`) :

    8C10FC0C  mov.w @r2,r1        ; défilement x
    8C10FC10  add #1,r1           ; + 1
    8C10FC30  and r8,r1           ; & 0x3FF
    8C10FC18  mov.w @(2,r2),r0    ; défilement y
    8C10FC20  add #20,r4          ; + 20
    8C10FC22  and r8,r4           ; & 0x3FF

### 2. Le calcul d'écran (`0x8C10FDA8`, chemin normal)

    écran x = (champ +2) × 16 − ((défilement x +  1) & 0x3FF)
    écran y = (champ +4) × 16 − ((défilement y + 20) & 0x3FF)
    largeur = (champ +3) × 16     hauteur = (champ +5) × 16
    u       = (champ +8) × 16     v       = (champ +10) × 16

**Quatre appels** à `0x8C10F8A2`, pas deux : (x, y), (x, y+1024), (x+1024, y),
(x+1024, y+1024). La scène boucle sur 1024 dans les deux sens.

### 3. Le chemin par ligne (`0x8C10FCB2`)

Pris seulement si le drapeau `0x4000` de la couche est mis **et** `u32[0x8C4DF130]` est nul.
Le rectangle est alors découpé en bandes de `r11` lignes — `r11 = 1` si son octet `+16` est
nul (ligne par ligne), sinon toute sa hauteur —, et chaque bande reçoit son propre décalage
horizontal, lu dans `0x8C613004 + banque × 4096 + ligne × 4` (`u16` au début de chaque
quadruplet), **ajouté au défilement x avant le masque** :

    écran x = x × 16 − ((défilement x + 1 + décalage de la ligne) & 0x3FF)

Deux appels seulement ici : (x, y) et (x+1024, y).

### 4. `0x8C10F8A2` — le constructeur de quadrilatères

Échelles flottantes en `0x8C4DEE3C` (x) et `0x8C4DEE40` (y). Le quadrilatère est **écrêté à
384 × 224** — les quatre constantes sont `0.0`, `384.0` (`0x8C10F9B0`), `0.0`, `224.0`
(`0x8C10F9B4`) — et les `u`, `v` sont recoupés au prorata (`fdiv` en `0x8C10F96E`). La pile
porte largeur, hauteur, puis le drapeau `+17` (relu en `@(156,r15)`).

**Il n'y a AUCUN repli sur 512 nulle part dans cette chaîne, et aucun masque `& 0x1FF`.**

### 5. Le défilement d'une couche, d'où il vient (`0x8C13B2E8`)

    registres CPS3 émulés : 0x8C724758 + 16 n    (+6 = x, +14 = y, le y est NIÉ)
    x : reg(+6)  + u16[0x8C7246CE] + un global,           puis & 0x3FF
    y : −reg(+14) + u16[0x8C7246C4] + 4
        ou, si l'octet 0x8C4D7CC5 est nul :
        −reg(+14) + u16[0x8C7246C4] + u16[0x8C7246D0] − 260
    le résultat est recopié en 0x8C6D3024 + 16 n, que lit le rastériseur

### VERDICT SUR LA PISTE DU 22/09

**Le `+20` existe, le `1024 × 512` et le `& 0x1FF` n'existent pas.** New Generation calcule
exactement comme 2nd Impact, à l'instruction près.

**Et le `+20` n'explique ni les 80 de Gill ni les 28 de Sean.** Deux raisons, toutes deux
lues :

1. **Aucun terme de la correction ne dépend de la couche.** Le `+1`, le `+20`, les globaux
   `0x8C7246C4/CE/D0`, le `−260` : pas un seul n'est indexé par `n`. Une constante commune
   aux quatre couches ne peut pas creuser un écart *entre* deux couches du même étage.
2. **Le port n'a pas à la porter.** 2I applique le même `+1` / `+20`, et
   `descripteurs2i.composer` pose ses rectangles à leur `x`, `y` bruts, `couches2i.DECALAGE`
   vide — décors validés par Frédéric. Si un `−20` manquait, les dix-neuf décors de 2I
   seraient tous décalés de vingt lignes.

### CE QUE LA LECTURE APPREND QUAND MÊME

**Les couches sont des repères INDÉPENDANTS.** Chacune a son propre défilement (registre
CPS3 `+14`). Chez GILL, la couche 0 occupe la scène 0..879 et la couche 1 la scène 960..1023 :
ce n'est pas un trou de 80 lignes, ce sont deux systèmes de coordonnées différents. Le `80`
de `descripteursng.DECALAGE_Y` est donc la **différence de défilement entre les deux
couches**, et elle se lit dans le registre `0x8C724758 + 16 n + 14`, pas dans le descripteur.
Vérifié au passage : la table de pas de Gill (`0x8C1AFE1C`, id 12) ne contient que
`(0,512,12) (0,0,12) (1,512,12) (1,0,12)` — pas de 80 non plus.

**CHEZ SEAN, le biseau noir est noir sur Dreamcast aussi.** Son descripteur est l'identité :
couche 0 = banque 0, `v 0..511`, scène 512..1023 ; couche 1 = banque 0, `v 512..1023`, scène
512..1023. L'art de la couche 0 s'arrête à `v 383`, et **`v 384..511` est noir dans la banque,
RGB 0 sous l'alpha 0** (mesuré : maximum `[0 0 0]` sur les quatre blocs). Avec le drapeau
`+17 = 1` — *Ignore Texture Alpha* — la Dreamcast peint donc bien du noir sur ces lignes.
Conclusion : **la Dreamcast ne descend jamais jusque-là.** Ce que le port montre de trop, ce
sont des lignes que la caméra de Sean n'atteint pas sur la vraie machine. C'est le
**défilement de la couche**, pas la page — ce qui rejoint le « *mal positionnés* » de
Frédéric, mais le coupable est le coefficient de la couche, pas un décalage global.

### LE PROCHAIN ADRESSAGE, SANS AMBIGUÏTÉ

Ce qui reste à ouvrir est ce qui **écrit** `0x8C724758 + 16 n + 14` par étage et par couche :
l'interprète de plans `0x8C110BD4` (celui qui remplit déjà la profondeur en `0x8C5BA154` via
`0x8C10E3B0`). C'est là, et nulle part ailleurs, que se trouvent les 80 de Gill et la limite
basse de Sean.

---

## `0x8C110BD4` OUVERT, ET LE FICHIER DE REGISTRES DE NG (23/09)

### Ce que fait `0x8C110BD4`

Ce n'est pas lui qui pose les plans : c'est l'interprete des ELEMENTS. Pour chaque fiche il
lit son plan dans les bits 10..12 de son mot `+0`, va chercher le defilement de ce plan, et
lui ajoute les coordonnees propres de la fiche :

    8C110C30  shad r3,r0        ; mot +0 >> 10
    8C110C32  and r0,r4         ; & 28  ->  plan * 4
    8C110C3C  mov.w @(r0,r2),r3 ; u16[0x8C6D3004 + plan*4]      defilement x
    8C110C46  add r0,r3         ; + s16 @(4, fiche)             son x
    8C110C4C  mov.w @(r0,r4),r2 ; u16[0x8C6D3004 + plan*4 + 2]  defilement y
    8C110C50  add r0,r2         ; + s16 @(6, fiche)             son y

Il ne touche aucun registre de defilement : il le CONSOMME. La profondeur qu'il tire de la
table des couches (`0x8C10E3B0` -> `0x8C5BA154`) est sa seule sortie vers le decor.

### LE FICHIER DE REGISTRES, ENFIN COMPLET

`0x8C7246D8 + 16 p`, **un seul tableau contigu de douze entrees de seize octets** :

| p | ce que c'est | qui le lit |
|---|---|---|
| 0..7 | les huit plans d'elements | `0x8C13AEF2` |
| 8, 12, 16, 20 (= `0x8C724758 + 64 n`… voir ci-dessous) | les quatre couches de decor | `0x8C13B2E8` |

    +6  s16   defilement x du plan
    +14 s16   defilement y du plan
    +0/+4 et +8/+12 : double tampon (la valeur courante recopiee sur la precedente)

Les deux remplisseurs ecrivent dans deux tables voisines que lisent les deux dessinateurs :

    0x8C13AEF2  plans 0..7   ->  0x8C6D3004 + 4 p    {u16 x, u16 y}   (lu par 0x8C110BD4)
        x = (u16[0x8C7246C6] + (reg+6  - u16[0x8C7246C2])) & 0x3FF
        y = (u16[0x8C7246C8] + (reg+14 + u16[0x8C7246C4]) - 2) & 0x3FF

    0x8C13B2E8  couches 0..3 ->  0x8C6D3024 + 16 n   (lu par 0x8C10FBCC)
        registres en 0x8C724758 + 16 n, memes champs +6 et +14

`0x8C039588` ne fait que remettre les quatre entrees de couche a zero (64 octets).

**Aucune ecriture du champ `+14` par adresse litterale n'existe dans tout le module
`0x8C13Axxx`-`0x8C13Bxxx`** (balayage des opcodes `mov.w r0,@(6|14,rn)` : zero occurrence).
Les registres sont donc ecrits par adresse calculee, du cote de l'emulation des registres
CPS3 -- c'est la qu'il faudra aller.

### UNE PISTE ESSAYEE ET REJETEE : LA TABLE DES COUCHES

Chaque couche de `0x8C4DDBA4` porte, apres `[plan, profondeur]`, des triplets
`{fin, hauteur << 8, drapeaux}`. En lisant une bande comme `fin - hauteur .. fin`, la fenetre
de la couche tombe **exactement** juste chez Gill :

    couche 0 : (255,111) (383,127) (511,127)  ->  144..511, soit 368 lignes
               son art fait 368 lignes (scene 0..367)
    couche 1 : (64,64)                        ->    0..64,  soit  64 lignes
               son art fait  64 lignes (scene 960..1023)

et l'ecart entre les deux origines vaut `(0 - 144) - (960 - 0) = -80` **mod 1024** :
les 80 de `descripteursng.DECALAGE_Y`, au pixel pres.

**Mais la regle ne tient pas sur les autres etages.** Applique aux dix-neuf bandes, le meme
calcul reclame une correction non nulle presque partout -- Ryu 464 / 512 / 576, Ken
336 / 512 / 416, Alex 384 / 496 -- alors que ces decors sont valides par Frederic sans aucun
decalage. La coincidence de Gill n'en fait donc pas une source. **Piste fermee** : ne pas la
rouvrir sans avoir d'abord lu ce que `fin` et `hauteur` veulent dire dans le constructeur
`0x8C146714`.

Les 80 de Gill restent donc mesures, et le prochain endroit ou chercher est l'ecriture des
registres CPS3 `0x8C7246D8 + 16 p + 14`.

---

## QUI ECRIT `0x8C7246D8 + 16 p + 14` : LA CHAINE COMPLETE, NG ET 2I (23/09)

Question de Frederic. Reponse : **deux poseurs, dans le module des registres**, et le
balayage d'opcodes du matin qui n'avait rien trouve etait MAL MASQUE (`w & 0xF0FF` au lieu
de `w & 0xFF0F` pour `MOV.W R0,@(disp,Rn)` = `1000 0001 nnnn dddd`).

### Les poseurs

    NG 0x8C13AE9C   poser_plan(p, x, y)      base 0x8C7246D8 + 16 p
    NG 0x8C13AEB8   poser_plan_prec(p, x, y) +2 et +10 seulement
    NG 0x8C13AECC   ajouter_plan(p, dx, dy)  accumule en +0 / +8 (32 bits)
    NG 0x8C13AE84   raz des huit plans
    NG 0x8C13B234   poser_couche(n, x, y)    base 0x8C724758 + 16 n
    NG 0x8C13B24C   poser_couche_x(n, x)
    NG 0x8C13B25E   poser_couche_y(n, y)
    NG 0x8C13B218   raz des quatre couches

`poser_plan` et `poser_couche` ecrivent les MEMES quatre champs : `+2` et `+6` recoivent x,
`+10` et `+14` recoivent y. Le `+14` cherche est donc toujours ecrit en meme temps que le
`+10` -- il n'y a pas de chemin qui ne touche que lui.

### Les appelants, et la formule de chacun

**Les plans d'elements** -- `0x8C0911B0`, boucle sur les `etage[+16]` plans :

    fiche  = 0x8C552674 + 84 + 144 k
    poser_plan(p = k + 1,
               x = (-fiche[+10]) & 0x3FF,
               y = (768 - (fiche[+12] & 0x3FF)) & 0x3FF)

(`0x8C091120` fait le meme calcul pour un seul plan.) Et en amont,
`fiche[+10] = ((fiche[+140] & 0x3FF) - etage[+40]) & 0x3FF`, `fiche[+12] = fiche[+142] & 0x3FF`
(`0x8C0911F8` et `0x8C09123C`). Le registre `p = k + 1` : le plan 0 du fichier n'est jamais
ecrit, les plans de jeu occupent `p = 1..7`.

**Les couches de decor** -- `0x8C091288`, une couche a la fois :

    poser_couche(n = fiche[+2],
                 x = (fiche[+26] & 0x3FF) - etage[+40],
                 y = fiche[+30])            <-- BRUT, sans le 768

**L'asymetrie est reelle et lue** : un plan d'elements recoit `768 - position`, une couche de
decor recoit `position` telle quelle. Le rasterisenur, lui, fait `ecran y = y - ((defilement
+ 20) & 0x3FF)` tandis que l'interprete d'elements (`0x8C110BD4`) fait `ecran y = defilement
+ y de la fiche`. Les deux reperes ne coincident que si la scene de la couche vaut celle de
l'element **plus 788**.

**Cas particuliers** : Ibuki ecrit `0x8C724766` (couche 0, `+14`) en dur, depuis `0x8C09F464`
et `0x8C09F600`. `0x8C09E194`, `0x8C09E2FE` et `0x8C0A5306` appellent `poser_couche_y`.
`0x8C0BA348` appelle `poser_couche`.

### D'ou vient `fiche[+30]`

    0x8C0882CE   a l'initialisation : fiche[+30] = 0
    0x8C088682   a l'entree d'etage : fiche[+26] = fiche[+72], fiche[+30] = fiche[+74]
                 (et +34, +38 recoivent la meme chose)
    ensuite      le SCRIPT du decor l'ecrit : fiche[+52] = u32[0x8C189EA0 + decor*16 + 4k]

**Et pour GILL (decor 0) les quatre pointeurs de script sont NULS.** Sa position verticale
est donc posee par la routine de l'etage elle-meme, pas par un script de plan. C'est le seul
maillon qui manque encore, et c'est le dernier.

### La fiche de plan, telle qu'elle est maintenant lue

    etage = 0x8C552674 (NG) / 0x8C6AF304 (2I)
      +16  nombre de plans        +40  origine x de la camera
      +74  numero de decor        +84 + 144 k : la fiche du plan k

    fiche +2    numero de couche de decor (passe a poser_couche)
          +10   defilement x calcule       +12  defilement y calcule
          +16   coefficient x (16.16)      +20  coefficient y
          +26   position x                 +30  position y      <-- LA VALEUR
          +52   pointeur de script
          +72   position x de depart       +74  position y de depart
          +100..+110  bornes (l_limit, r_limit, l_limit2, r_limit2, y_limit, y_limit2),
                      table 0x8C18A3F8 + decor*48 + plan*12 -- c'est `limit_tbl3`
          +140  position x + tremblement   +142 position y + tremblement
                (tables de secousse 0x8C18A9DC en x, 0x8C18AAE0 en y, indexees par +42 / +44)

### LE MEME TRAVAIL POUR 2nd IMPACT : FAIT, ET C'EST LE MEME CODE

Les cinq routines existent dans `SF3_2ND.BIN`, **octet pour octet** (retrouvees par leurs
suites d'opcodes, pas par adresse) :

| role | New Generation | 2nd Impact |
|---|---|---|
| poser_plan | `0x8C13AE9C` | `0x8C0FF7F8` |
| poser_couche | `0x8C13B234` | `0x8C0FFB90` |
| boucle des plans d'elements | `0x8C0911B0` | `0x8C0E8C7E` |
| ecriture d'une couche | `0x8C091288` | `0x8C0E8D40` |
| copie depart -> position | `0x8C088682` | `0x8C0DAFA4` |
| remplisseur des plans | `0x8C13AF16` | `0x8C0FF872` |
| remplisseur des couches | `0x8C13B3F2` | `0x8C0FFD4E` |

    fichier de registres   NG 0x8C7246D8 + 16 p   2I 0x8C84135C + 16 p
    couches (p = 8..11)    NG 0x8C724758 + 16 n   2I 0x8C8413DC + 16 n
    structure d'etage      NG 0x8C552674          2I 0x8C6AF304

Meme disposition, meme decalage de 128 octets entre les plans et les couches, memes champs.
**Les deux jeux partagent ce moteur en entier** : ce qui sera compris d'un cote vaudra de
l'autre, et reciproquement.

---

## LA ROUTINE QUI POSE LE `+30` DE GILL : `0x8C09E298` (23/09)

Trouvee par le seul chemin qui ne pouvait pas mentir : **qui charge la table de pas de Gill**
(`0x8C1AFE1C`, id 12). Un seul site, `0x8C09E2A8`, et la routine qui l'entoure est la sienne.

Elle a trois etats, choisis par son champ `+36`. A l'etat d'initialisation :

    8C09E2EC  mov.l 0x8c09e3e4,r3   ; r3 = 0x8C5526C8 = etage + 84 = la fiche du PLAN 0
    8C09E2EE  mov.w @(12,r3),r0     ; le defilement y du plan 0 -- la camera
    8C09E2F2  mov.w @(2,r13),r0     ; r13 = 0x8C1AFE1C + 6*pas : le DECALAGE du pas
    8C09E2F4  add r2,r0             ; y = camera + decalage
    8C09E304  jmp 0x8C13B25E        ; poser_couche_y(couche 0, y)

et a l'etat courant (`0x8C09E368`) la meme chose avec `fiche[0][+142]` (la position plus le
tremblement) masquee a `0x3FF`, par `0x8C13B28E`.

**Gill ne passe donc pas par `fiche[+30]` pour sa couche 0.** Sa routine ecrit le registre
de couche directement, et la valeur est *la camera plus le decalage du pas* -- et les pas de
`0x8C1AFE1C` valent `(carte 0, +512) (0, 0) (1, +512) (1, 0)`, douze trames chacun. C'est
exactement le `decalage=512` que `descripteursng.ETATS[0]` porte deja. Sa couche 1, elle,
passe par le chemin general `0x8C091288`.

Reste que **le 80 n'est toujours pas dans ce qu'on a lu** : la routine n'ajoute que 0 ou 512.
`DECALAGE_Y` reste une valeur mesuree, mais on sait maintenant qu'elle ne peut venir ni du
descripteur, ni de la table des couches, ni de la table de pas, ni du `+20` de la camera :
il ne reste que le defilement propre de la couche 1 (son coefficient et sa borne `y_limit`).

---

## LES SPRITES ANIMES DES DECORS : CADENCES ET DECLENCHEURS, 2I ET NG (23/09)

Demande de Frederic, sur le modele de ce qui avait ete fait pour l'etage d'Oro.

### 1. LES CADENCES -- New Generation rejoint 2nd Impact

`cadences.py` lisait les scripts de 2I depuis le 29/08. Son pendant **`cadencesng.py`**
est ecrit : meme format d'enregistrement (huit octets `{cmd, duree, 0, 0, index global}`),
meme resolution de l'index par le span des `F_ETCnn`, seule la table maitresse change --

    2I : 0x8C5F9B38 + aire*4                 (64 aires bout a bout)
    NG : 0x8C4CC1F0 + (decor*3 + aire)*4     (dix-neuf decors, trois aires)

| | 2nd Impact | New Generation |
|---|---|---|
| tables distinctes | 21 | 22 |
| scripts | 419 | 491 |
| images | 3 614 | 4 144 |
| duree la plus frequente | **6 trames** (765 fois) | **6 trames** (958 fois) |
| ensuite | 4 (676), 8 (526), 3 (329), 2 (289) | 8 (738), 4 (573), 2 (387), 3 (292) |
| duree min / max | 1 / 250 | 1 / 250 |
| images de 16 trames ou moins | 94,1 % | 93,3 % |
| boucles `0x0C` | 45 | 63 |
| tours de boucle | 2 (x20), 3 (x17), 4 (x3), 5, 8, 10 (x2), 16 | 2 (x27), 3 (x25), 4 (x6), 5 (x3), 9, 10 |

**Les deux jeux ont la meme horloge d'animation** : une image tenue six trames, des boucles
de deux ou trois tours. Les releves complets sont dans `cadences-2i.txt` (4 086 lignes) et
`cadences-ng.txt` (4 682 lignes).

### 2. LE SCRIPT N'EST PAS UNE LISTE D'IMAGES : C'EST UNE MACHINE

L'octet 0 d'un enregistrement n'est pas un simple « affiche » : c'est un **opcode**, et il y
a une table de gestionnaires.

    2I : 0x8C1C5BC8, **137 gestionnaires**, le premier en 0x8C0B529C
    NG : 0x8C155518, **116 gestionnaires**, le premier en 0x8C033858

Le gestionnaire recoit `r4` = l'objet, `r5` = l'enregistrement de huit octets. La cmd 2
(`0x8C0B530C` en 2I), par exemple, multiplie `enr[+6] - 2` par un champ de l'objet et range
le produit dans un autre : ce n'est pas une image, c'est un calcul.

Les opcodes **reellement employes** par les scripts de decor :

| opcode | 2I | NG | ce qu'on en sait |
|---|---|---|---|
| `0x00` | 3 614 | 4 144 | affiche `index` pendant `duree` trames |
| `0x01` | -- | -- | fin de script |
| `0x02` | 57 | 63 | calcul sur un champ de l'objet (`0x8C0B530C`) |
| `0x03` a `0x08` | 2 chacun | 2 chacun | |
| `0x09` | 9 | 0 | |
| `0x0C` / `0x0D` | 45 / 44 | 63 / 61 | debut / fin de boucle, `index` = le nombre de tours |
| `0x0E` / `0x0F` | 2 / 2 | 5 / 3 | |
| `0x28` (40) | 2 | 0 | **2I seulement** |
| `0x29` (41) | 29 | 24 | |
| `0x2A` (42) | **149** | 0 | **2I seulement, et tres employe** |
| `0x2B` (43) | 11 | 6 | |
| `0x32` (50) | 15 | 0 | **2I seulement** |
| `0xFF` | 19 | 1 | |

**New Generation a 116 opcodes, 2nd Impact en a 137** : le moteur d'animation a ete etendu
entre les deux jeux, et les trois opcodes que NG ignore (`0x28`, `0x2A`, `0x32`) sont
exactement ceux qui manquent a ses scripts. C'est une verification croisee gratuite.

### 3. CE QUI CHANGE DE SCRIPT : LE POSEUR, ET SES APPELANTS

    2I 0x8C0B4AD4   poser_script(objet r4, table r5, script r6)
    NG 0x8C03324C   le meme, octet pour octet (retrouve par ses opcodes)

        objet[+454] = table          objet[+456] = script
        objet[+448] = u32[ u32[objet + 364 + table*4] + script*4 ]
        puis douze u16 remis a zero a partir de objet[+468]

(`0x8C03324C` etait deja nomme dans ce document -- « les oiseaux lointains d'Elena 1,
script pose par `0x8C03324C` » : la lecture retombe dessus par un autre chemin.)

Toute animation qui change vient d'un appel a ce poseur. Dans la region des acteurs de
decor : **208 sites en 2I, 186 en NG** (`declencheurs.py`, releve dans `declencheurs.txt`).

Et la forme d'un acteur est toujours la meme -- `0x8C020254` la montre en clair :

    mov #40,r0 ; mov.w @(r0,r3),r2 ; add #-16,r2 ; shll2 r2 ; mov.l @(r0,r2),r3 ; jmp @r3

**`objet[+40]` est le numero d'etat**, moins 16, qui indexe la table de sauts de l'acteur.
C'est la machine a etats : un etat = un script + une condition de sortie.

### 4. CE QUE LES ACTEURS CONSULTENT

Les adresses lues par les routines qui appellent le poseur, classees par le nombre de
routines qui les lisent :

| 2I | NG | lu par | ce que c'est |
|---|---|---|---|
| `0x8C6466EC` | `0x8C554668` | 73 / 83 | **le tableau des acteurs**, 2 048 octets par place (le spawner du chat d'Oro le porte en dur) |
| `0x8C69D314` | `0x8C545260` | 85 / 78 | **le gel de trame** : `mov.w @r ; tst ; bt continuer ; bra sortir`. Six ecritures seulement en 2I. Toute animation de decor s'arrete avec le jeu -- et **la routine de couche de Gill le lit aussi** (`0x8C09E308`) |
| `0x8C69D32E` | `0x8C54527A` | 83 / 77 | mot d'echange, 46 ecritures |
| `0x8C6AF304` | `0x8C552674` | 20 / 16 | le contexte d'etage (`+4` decor, `+5` aire, `+6` le tirage `z`) |
| `0x8C6A27D4` | -- | 46 | le verrou « ne pas creer » teste a l'entree des spawners |
| `0x8C0217E4` | `0x8C09AFA4` | -- | le tireur de place dans le tas |

### 5. L'INVENTAIRE DES ACTEURS A IMMEDIATS -- LE CRITERE D'ORO, GENERALISE

Le chat d'Oro n'a pas d'enregistrement : son spawner ecrit tout en constantes **et porte la
table de scripts de son decor en dur**. C'est ce litteral qui l'avait fait trouver. Applique
aux 21 tables de 2I et aux 22 de NG, il rend l'inventaire complet de ces acteurs :

    2nd Impact
      table 8C122368  decor  0  ->  8C0259FC  8C04AEF4
      table 8C122F78  decor 11  ->  8C028A5C
      table 8C123DA0  decor  3  ->  8C029534  8C0296F0
      table 8C1281F8  decors 6 et 16 -> 8C031BFC
      table 8C129180  decor  8  ->  8C02E550  8C02E610  8C03CC94  8C03CEFC
      table 8C1299DC  decor  8  ->  8C036210  8C0363A0
      table 8C12AB8C  decor  9  ->  8C0305E8  8C0337B4  8C033988  8C033B84  8C0340A4   (ORO)
      table 8C131050  decor 13  ->  quinze sites, de 8C02580C a 8C04C658

    New Generation
      table 8C0CE4BC  decor  0  ->  8C0A5250
      table 8C0CEC00  decor  1  ->  8C0A98DC  8C0A9B3C
      table 8C0D30E4  decors 3 et 10 -> 8C0A0D04  8C0A0DEC  8C0A0F74
      table 8C0D5ED4  decor  4  ->  8C0A8C74
      table 8C0D7B28  decor  6  ->  8C0A849C
      table 8C0D9618  decor  8  ->  8C0A4E88  8C0B2628  8C0B2868
      table 8C0D9E88  decor  8  ->  8C0AC548  8C0AC6CC
      table 8C0DB160  decor  9  ->  8C0A6F08  8C0AA008  8C0AA1B8  8C0AA384  8C0AA88C

Les cinq sites du decor 9 de 2I sont la menagerie d'Oro, deja lue -- **le releve les rend
sans rien savoir d'elle**, ce qui valide le critere. Le decor 13 de 2I, avec ses quinze
sites, est le plus peuple du jeu et n'a jamais ete ouvert. Le decor 9 de NG en a cinq.

### 6. CE QUI RESTE, ET C'EST NOMME

Les conditions elles-memes -- « suit les combattants des yeux », « sursaute quand on
tombe » -- sont les **gardes** des sauts d'etat de ces machines. On a le poseur, les 394
sites d'appel, la forme de la machine (`objet[+40]`), et les etats partages. Ce qui manque
est la **carte des structures de combattant** : tant qu'on ne sait pas quelle adresse porte
le x, le y et l'etat d'un joueur, on ne peut pas dire d'une comparaison qu'elle regarde un
combattant. C'est le prochain geste, et il est unique pour les deux jeux.

    outils/cadencesng.py      les cadences de NG           -> cadences-ng.txt
    outils/cadences.py        les cadences de 2I           -> cadences-2i.txt
    outils/declencheurs.py    les appelants du poseur      -> declencheurs.txt

---

## LA CARTE DES STRUCTURES DE COMBATTANT (23/09)

### Comment elle a ete trouvee : par la MULTIPLICATION

Les balayages precedents cherchaient des decalages (`shll8 ; shll2 ; shll`) et ne rendaient
qu'une chose : le tas des acteurs, 2 048 octets par place. **Un tableau dont l'element n'est
pas une puissance de deux ne s'indexe pas comme ca** -- il s'indexe par `muls.w`. En
balayant les `muls.w` dont la constante vient d'un litteral et dont une base de RAM est
chargee autour, une seule adresse ressort dans chaque binaire :

    2nd Impact       plw = 0x8C645590, **1 036 octets** par combattant, 60 sites
    New Generation   plw = 0x8C543EC8, **984 octets** par combattant, 46 sites

et c'est exactement l'adresse que le balayage des champs de position avait deja signalee
sans qu'on sache l'interpreter (lue en `+84` **et** en `+102`).

Les combattants ne sont donc **pas** dans le tas des acteurs : ils ont leur propre tableau.

### Le combattant est un `WORK`, comme un sprite de decor

Les offsets cites en dur sur `plw[0]` sont ceux-la memes que ce chantier avait releves sur
les objets de decor :

| offset | 2I | NG | ce que le chantier en disait deja |
|---|---|---|---|
| +0 | 212 | 146 | -- |
| +3 | 24 | 28 | -- |
| +8 | 2 | 2 | -- |
| +38 | 1 | 1 | -- |
| +84 | -- | 2 | -- |
| +88 | 1 | 1 | **la profondeur d'un objet** |
| +102 | 2 | 2 | **le x d'un objet** |
| +158 | 7 | 8 | -- |
| +456 | 2 | 2 | **le script d'un objet** |
| +554 | 1 | 1 | **le code couleur d'un objet** |

Deux familles, un seul en-tete. Et cet en-tete **est celui de 3rd Strike, champ pour
champ**. La preuve tient dans un detail du port : dans `src/structs.h`, `XY` fait QUATRE
octets (`{s16 low; s16 pos}`, en union avec un `s32 cal`), donc `xyz[0].disp.pos` tombe en
**+102** et `xyz[1].disp.pos` en **+106**. Ce sont, au pixel pres, les offsets mesures dans
les binaires Dreamcast des semaines avant qu'on ouvre le port.

    (les offsets se lisent avec clang, en 32 bits, sans rien executer :
     clang --target=i686-unknown-none-elf -I src -Xclang -fdump-record-layouts -fsyntax-only)

### La carte

    +0   s8  be_flag        existe              +36  s16[8] routine_no  **L'ETAT**
    +1   s8  disp_flag      se dessine          +52  s16[8] old_rno
    +2   u8  blink_timing                       +68  s16 hit_stop   **LE FIGEMENT DE COUP**
    +3   u8  operator                           +70  s16 hit_quake  **LA SECOUSSE**
    +4   u8  type                               +72  s8  cgromtype
    +5   u8  charset_id                         +73  u8  kage_flag      l'ombre
    +6   s16 work_id                            +74..82 kage_hx/hy/prio/width/char
    +8   s16 id             **LE PERSONNAGE**   +84  s16 position_x
    +10  s8  rl_flag        **LE SENS**         +86  s16 position_y
    +11  s8  rl_waza                            +88  s16 position_z
    +12  void* target_adrs  **L'ADVERSAIRE**    +90..94 next_x/y/z
    +16  void* hit_adrs     ce qui l'a touche   +96  s16 scr_mv_x
    +20  void* dmg_adrs     ce qui l'a blesse   +98  s16 scr_mv_y
    +24  s16 before         chainage            +100 XY[3] xyz
    +26  s16 myself         son indice          +102     xyz[0].pos  **X**
    +28  s16 behind                             +106     xyz[1].pos  **Y**
    +30  s16 listix         sa liste (0..7)     +110     xyz[2].pos  Z
    +32  s16 dead_f                             +112 s16[3] old_pos
    +34  s16 timing                             +118 s16 sync_suzi

Au-dela de ~170 les deux moteurs divergent : 3rd Strike a insere des champs (sa
`char_table` est en +428, celle de la Dreamcast en +364). Les offsets qui valent pour la
Dreamcast sont ceux que ce chantier a mesures -- `+364` les tables de scripts, `+448` le
script courant, `+454`/`+456` table et numero, `+554`/`+556`/`+558` couleur, profondeur,
plan.

### Le tas des acteurs, au complet

C'est la SEULE famille de 2 048 octets dans chacun des deux binaires (verifie par balayage
de tous les couples base/pas) :

    2I  0x8C6466EC .. 0x8C6866EB   128 places de 2 048 octets
        0x8C6866F0   la pile des places libres, 128 u16
        0x8C6867F0   le nombre de places libres
        0x8C6867F2 + 2*liste   la tete des HUIT listes
        0x8C686802 + 2*liste   la queue
        0x8C0217E4   le tireur de place            NG 0x8C09AFA4
    NG  0x8C554668, meme disposition

Les huit listes ne sont pas des categories : le perroquet d'Oro est cree dans la liste 0,
son chat dans la liste 4.

### CE QUE LES ACTEURS DE DECOR LISENT D'UN COMBATTANT

C'est la reponse a la question des declencheurs. Les routines de la region des decors qui
portent une adresse de combattant en dur, et le champ qu'elles lisent :

| champ | 2I | NG |
|---|---|---|
| `+0` be_flag (le combattant existe) | 31 routines | 45 |
| `+3` operator | 7 | 12 |
| `+8` id (quel personnage) | 1 (`0x8C038474`) | 2 (`0x8C099DC4`, `0x8C0AE5FC`) |
| `+38` **routine_no[1], l'etat du combattant** | -- | 1 (`0x8C099E50`) |
| `+84` position_x | -- | 2 (`0x8C0AAF20`, `0x8C0B21DC`) |
| `+102` **xyz[0].pos, le X** | 2 (`0x8C0373B2`, `0x8C04ACC8`) | 2 (`0x8C0AB6F0`, `0x8C0AD6BE`) |
| `+456` numero de script | 2 | 2 |
| `+554` code couleur | 1 | 1 |

**Un exemple, lu en entier** -- `0x8C0AB6F0`, New Generation :

    8C0AB6F0  mov.l 0x8c0ab7c0,r0   ; r0 = 0x8C543F2E = plw + 102 = le X d'un combattant
    8C0AB6F2  muls.w r1,r2          ; r1 = cote * 984
    8C0AB6F6  mov.w @(r0,r1),r2     ; r2 = plw[cote].xyz[0].pos
    8C0AB6FA  add #-64,r2           ; soixante-quatre unites a sa gauche
    8C0AB6FC  mov.w r2,@r3          ; et c'est la que l'objet est pose

Un objet de decor qui se place **par rapport au combattant**. C'est la mecanique que
Frederic decrivait, prise sur le fait.

### CE QUI RESTE

Les huit routines de NG et les six de 2I listees ci-dessus sont les acteurs **qui lisent un
combattant par adresse en dur**. Il en existe d'autres qui passent par `target_adrs` (`+12`)
ou par un pointeur range dans leur propre fiche : ceux-la ne se voient pas dans ce releve.
Le prochain geste est de les attraper par le pointeur, maintenant qu'on sait ce qu'est un
combattant et ou il vit.

    outils/combattants.py     la carte, et qui lit les combattants

---

## LES ACTEURS QUI LISENT UN COMBATTANT PAR POINTEUR (23/09)

Le releve de `combattants.py` n'attrapait que ceux qui portent `plw + champ` en dur.
Frederic : « attrape ceux qui passent par `target_adrs` ». Fait -- `outils/par_pointeur.py`,
releve dans `par_pointeur.txt`.

### La methode

Les trois pointeurs de l'en-tete `WORK` sont en `+12` (`target_adrs`), `+16` (`hit_adrs`) et
`+20` (`dmg_adrs`). On cherche donc `mov.l @(3|4|5, rm), rn` dans la region des acteurs, puis
**on suit le registre** : il passe par `mov rm,rn`, il est range dans la pile
(`mov.l rn,@(d,r15)`) et relu plus loin. Un suivi naif sur vingt instructions ne rendait
presque rien ; avec la propagation registres + pile sur quatre-vingt-dix, le releve s'ouvre.
Chaque offset atteint est ensuite nomme par la carte du `WORK`.

### CE QU'ILS VONT CHERCHER

| pointeur | champ | 2I | NG |
|---|---|---|---|
| `target_adrs` | `+8` id -- **quel personnage** | `0x8C038DB6` `0x8C039D82` `0x8C02D5C4` | `0x8C0AFA8E` |
| `target_adrs` | `+10` rl_flag -- **le sens ou il regarde** | `0x8C026B72` `0x8C026FAC` | -- |
| `target_adrs` | `+38` routine_no[1] -- **son etat** | `0x8C042016` `0x8C0448C0` | `0x8C0ABCB0` `0x8C0B77F2` `0x8C0B9B78` |
| `target_adrs` | `+54` old_rno[1] -- **son etat PRECEDENT** | -- | `0x8C0ABAA0` `0x8C0ABCB0` |
| `target_adrs` | `+84`/`+86`/`+88` position | `0x8C020650` `0x8C0474E6` | `0x8C0BC6E2` |
| `target_adrs` | `+102` xyz.X | `0x8C020082` `0x8C02BCE6` `0x8C038DB6` | -- |
| `target_adrs` | `+554` code couleur | `0x8C02279E` `0x8C022BE8` `0x8C039AB6` | `0x8C0AF804` `0x8C0AFA8E` |
| `hit_adrs` | `+4` `+6` `+38` `+68` `+102` `+106` | `0x8C0266B6` | `0x8C09EEF2` |
| `dmg_adrs` | `+0` be_flag, `+34` timing | `0x8C027978`.. | `0x8C09F40C`.. |

**`+54`, c'est l'etat PRECEDENT.** Lire `+38` et `+54` ensemble, c'est detecter un
CHANGEMENT d'etat -- exactement « le personnage reagit a ce que fait le combattant ».

### DEUX ARCHETYPES, LUS EN ENTIER

**1. Le receveur de coup** -- 2I `0x8C0266B6`, NG `0x8C09EEF2`, le meme en deux binaires.
Par `hit_adrs`, il lit d'un coup `+4` type, `+6` work_id, `+38` l'etat, **`+68` hit_stop**,
`+102` X et `+106` Y. C'est la fiche de ce qui vient de le toucher, position comprise :
la mecanique d'un element qui se brise au contact.

**2. Le guetteur d'etat** -- NG `0x8C0ABCA6`, dans une routine qui pose un script :

    8C0ABCAE  mov r4,r14              ; la fiche de l'acteur
    8C0ABCB0  mov.l @(12,r14),r5      ; r5 = sa cible
    8C0ABCB2  mov #38,r0
    8C0ABCB4  mov.w @(r0,r5),r3       ; r3 = cible->routine_no[1] : SON ETAT
    8C0ABCB8  cmp/gt r2,r3            ; etat > 2 ?
    8C0ABCBA  bf 0x8C0ABD40           ; sinon, rien
    ...                               ; sinon : compteur++, disp_flag = 1, et un script est pose

**Un sprite de decor qui ne se montre et ne s'anime que lorsque l'etat de sa cible depasse
2.** C'est un declencheur, lu dans le binaire.

### CE QUI N'EST PAS PROUVE, ET QUI RESTE

**Que la cible SOIT un combattant.** Les offsets atteints sont ceux d'un combattant, et ils
n'auraient pas de sens sur autre chose -- mais le balayage de « qui ecrit `+12` avec une
adresse de `plw` » ne rend rien dans la region des decors : les deux sites de 2I sont des
faux positifs (des mots de table de litteraux lus comme du code) et celui de NG
(`0x8C098B1A`) **efface** un pointeur, `plw[cote] + 868` en etant le porteur.

La piste est ouverte, et elle est nette : le createur d'objet **recopie la cible de son
createur** -- 2I `0x8C038DB6` fait `mov.l @(12,r4),r5` sur la fiche source avant de remplir
la nouvelle. La cible se PROPAGE le long de la chaine de creation. Il faut donc remonter
cette chaine depuis le premier createur pour prouver qu'elle part d'un `plw`, et non la
chercher au point d'arrivee.

> **Deux avertissements de methode**, pour ne pas y revenir. Le balayage d'opcodes ne
> distingue pas le code des tables de litteraux : tout site isole doit etre desassemble
> avant d'etre cru. Et `debut_de_routine` remonte au `rts` precedent, ce qui est une
> approximation : un site marque « hors d'une routine a script » ne prouve pas qu'il n'en
> est pas.

    outils/par_pointeur.py    les lecteurs par pointeur   -> par_pointeur.txt

---

# LE MOTEUR D'ANIMATION DES SPRITES DE DECOR, DE BOUT EN BOUT (23/09)

Frederic : « remonte la chaine de creation depuis le premier createur, ne t'arrete pas tant
que tu n'es pas alle au bout ». Ce qui suit est ce qui a ete LU. Ce qui ne l'est pas est dit
a la fin.

## 1. LA CHAINE DE CREATION

    repartiteur d'etage
      -> routine du decor
        -> SPAWNER               tire une place, remplit la fiche, pose la table de scripts
          -> 0x8C0862C0 (NG)     accroche la fiche a son plan, si l'enregistrement le dit
            -> poser_script      2I 0x8C0B4AD4   NG 0x8C03324C
              -> chaque trame : le pas d'acteur -> l'interprete

**Le spawner, lu champ par champ** (NG `0x8C0AC7F8`, l'archetype) :

    exts.w r4,r4 ; shll8 ; shll2 ; shll ; add 0x8C554668  ->  fiche = tas + place * 2048
    mov.b r12,@r4                     +0    be_flag
    mov #87,r0 ; mov.w r0,@(8,r4)     +8    L'ID DE L'ACTEUR
    mov #16,r0 ; mov.w r0,@(6,r4)     +6    work_id
    mov #72,r0 ; mov.b r12,@(r0,r4)   +72   cgromtype
    mov.b r0,@(10,r4)                 +10   rl_flag
    mov.w r8,@(552,r4)                +552
    mov.b r0,@(4,r4)                  +4    type

puis **l'enregistrement est verse champ par champ, dans cet ordre**, par `mov.w @r14+,r3` :

    +32        +558 plan     +554 couleur     +102 x     +106 y
    +88 et +556 profondeur (ecrite deux fois)     +456 script     +68     +118

Neuf mots, dix-huit octets : c'est exactement la carte que ce chantier avait etablie a
l'usage, et elle est maintenant **lue dans l'ordre du code**, pas deduite.

**La table de scripts est posee la** :

    r3 = 0x8C4DE610 + decor*12 ; r1 = u32[r3 + aire*4] ; objet[+364] = r1

`0x8C4DE610 - 0x12420 = 0x8C4CC1F0` : c'est la table maitresse que `cadencesng.py` emploie,
a l'image du `.bss` pres. La chaine se referme sur elle-meme.

**`0x8C0862C0`** ne fait quelque chose que si le dernier champ de l'enregistrement, `+118`,
vaut 1 : il accroche alors la fiche a son plan (`objet[+120]`, tableau `0x8C5526F4`,
144 octets par plan). C'est le lien de parallaxe.

## 2. LES DEUX LIENS DE PARENTE -- ET LA REPONSE SUR `target_adrs`

Un acteur qui en cree un autre lui laisse deux choses :

    objet[+12]  = target_adrs = LE CREATEUR LUI-MEME    (`mov.l r1,@(12,r4)`, r1 = @r15)
    objet[+812] = LA RACINE, heritee telle quelle       (`objet[+812] = createur[+812]`)

Vu en clair chez NG `0x8C0ABBB6` : `r3 = createur[+812] ; nouveau[+812] = r3`, puis
`nouveau[+12] = createur`. **La cible se propage de generation en generation** -- ce que la
note du matin supposait, et qui est maintenant ecrit.

Consequence : quand un acteur lit `target_adrs->routine_no[1]`, **il lit l'etat de celui qui
l'a fait naitre**. Si la racine de la chaine est un combattant, toute la descendance le
regarde. Et la racine EST un combattant au moins une fois : l'id 85 de NG (`0x8C0AB52C`) se
pose a `plw[cote].xyz[0].pos - 64`. Les id 85, 86 et 87 sortent de trois spawners voisins,
`0x8C0AC4CC`, `0x8C0AC664`, `0x8C0AC802`.

## 3. LA MACHINE A ETATS D'UN ACTEUR

    table des routines par id  : NG 0x8C1AD9F8 + id*4  (186 entrees ; l'id 18 est la
                                                        routine de couche de Gill)
    etat de l'acteur           : objet[+38] = routine_no[1]
    table de sauts de l'acteur : propre a chacun (l'id 87 a 0x8C4DEA3C, image 0x8C4CC61C)

Un exemple complet, l'id 87 de NG :

    0x8C0ABC24  r4 = objet[+812]              ; la racine de la chaine
                dispatch sur racine->routine_no[0]   (0, 1, 2)
    etat 1      si 0x8C545260 (le gel de trame) et 0x8C54527A sont nuls :
                jsr table[0x8C4DEA3C + objet[+38]*4]  ; son propre etat
    etat 2      0x8C0ABCA6 :
                r5 = objet[+12]               ; sa cible = son createur
                si cible->routine_no[1] > 2 : ; L'ETAT DE LA CIBLE
                    compteur++ ; disp_flag = 1 ; un script est pose

Deux niveaux de condition : **l'etat de la racine** choisit la branche, **l'etat de la
cible** declenche l'animation.

## 4. L'INTERPRETE DE SCRIPT

**Deux moteurs**, choisis par `objet[+496] & 4096` dans le pas de trame (2I `0x8C018FD6`) :

    bit mis   -> 0x8C0B5060
    bit clair -> 0x8C0B4F9C

Meme forme tous les deux. Les champs :

    +364  char_table -- les tables de scripts       +448  le script courant
    +452  l'index dans le script, EN MOTS DE 4 OCTETS
    +460  le pas d'avance (2 mots = un enregistrement de 8 octets)
    +454  numero de table     +456  numero de script
    +264, +260, +262, +468, +492, +324, +999, +1012 : l'etat de marche

**La boucle** (2I, `0x8C0B50DC`) :

    r13 = objet[+448] + objet[+452]*4
    u16 = @r13
    si u16 >= 256  -> 0x8C0B5124
    sinon          -> jsr table_des_commandes[u16]   (r4 = objet)
                      si le gestionnaire rend 0 : on sort, la trame est consommee
                      sinon : objet[+452] += objet[+460] et on recommence

**LE SEUIL DE 256, C'EST LA DUREE.** Le premier u16 d'un enregistrement vaut
`commande | duree << 8`. Une duree nulle laisse un petit nombre : c'est un OPCODE. Une duree
non nulle met le mot au-dessus de 256 : c'est une IMAGE. Verifie sur les octets bruts --
`00 04 00 00 00 00 90 9b` donne `0x0400`, commande 0 duree 4 ; `01 00 ...` donne 1, la fin ;
`32 00 ... 03 00` donne 50 avec l'argument 3.

**La commande 0x00 elle-meme ne fait rien** : son gestionnaire (`0x8C0B529C`) est
`rts ; mov #1,r0` -- il rend 1, donc on avance. Tout l'affichage est dans le chemin des
durees.

**Les tables de commandes** : 2I `0x8C1C5BC8`, 137 gestionnaires, le premier en
`0x8C0B529C` ; NG `0x8C155518`, 116, le premier en `0x8C033858`. Le gestionnaire recoit
`r4` = l'objet et `r13` = l'enregistrement, et **sa valeur de retour est le contrat** :
0 = la trame est consommee, non nul = passer a l'enregistrement suivant.

La commande 1 n'est pas un simple arret : `0x8C0B52A0` relit trois champs de la fiche et
rappelle `0x8C0B4B90(objet, table, script, ...)` -- **elle repose un script**. C'est la
boucle d'animation, et c'est pourquoi un script de decor tourne indefiniment sans que rien
ne le relance de l'exterieur.

## 5. CE QUI RESTE, ET C'EST BORNE

* **Le detail des 137 (2I) et 116 (NG) gestionnaires.** Quinze opcodes seulement sont
  employes par les scripts de decor. Trois sont lus : `0x00` avance, `0x01` repose le
  script, `0x02` calcule sur un champ. **Les autres ne le sont pas**, et le plus employe de
  2I -- `0x2A`, 149 fois, absent de NG -- en fait partie.
* **Ou la duree est DECOMPTEE.** Le seuil de 256 est lu, la valeur de la duree aussi, mais la
  routine qui la retient d'une trame a l'autre n'a pas ete isolee : elle n'est ni dans
  `0x8C0B5060` ni dans les deux copieurs de champs qu'il appelle (`0x8C0B72E0`, `0x8C0B7296`).
* **Le second moteur `0x8C0B4F9C`** : meme forme, pas lu ligne a ligne, et on ne sait pas
  quel genre d'acteur porte le bit 4096.
* **Le lien racine -> combattant n'est etabli que pour une famille** (les id 85 a 87 de NG).
  Pour les autres, la racine n'a pas ete remontee jusqu'a un `plw`.

> **Le crible qui a deverrouille tout cela** : un spawner se trouve par
> `mov #id,r0 ; mov.w r0,@(8,rn)`. La regle retrouve d'un coup les quatre spawners d'Oro
> deja connus -- id 72 en `0x8C033916`, id 71 en `0x8C0336EC`, id 55 en `0x8C030568`, id 74
> en `0x8C034022` -- sans rien savoir d'eux, et elle donne ceux de New Generation dans la
> foulee. C'est le meilleur crible du chantier pour cette famille.

---

## LA BOUCLE EST FERMEE : LE DECOMPTE DE TRAMES ET L'EN-TETE DE SCRIPT (23/09, suite)

Les deux trous laisses par la section precedente sont combles. Le moteur d'animation des
sprites de decor est maintenant lu de la premiere a la derniere trame.

### 1. L'EN-TETE DE HUIT OCTETS AVANT CHAQUE SCRIPT

`poser_script` ne lit pas que le script : il lit les **huit octets qui le precedent**.

    r5 = objet[+448] ; add #-2,r5
    mov.w @r5,r3 ; mov.w r3,@-r4      ; objet[+466] = u16[script - 2]
    ... quatre fois, en descendant ...
    mov.w r2,@-r4                     ; objet[+460] = u16[script - 8]   <-- LE PAS

Et `objet[+460]` est **le pas d'avance de l'index**. Sur les scripts de 2nd Impact ces huit
octets valent `02 00 00 00 00 00 00 00` : **le pas vaut 2**, soit deux mots de quatre
octets, soit un enregistrement de huit.

**Consequence sur ce que `cadences.py` appelait « la commande 0x02 ».** Ce n'est pas une
commande : c'est l'en-tete du script SUIVANT, pose juste apres le `0x01` qui termine le
precedent. Les 57 occurrences de 2I et les 63 de NG sont des en-tetes, pas des ordres.

### 2. LE DECOMPTE DE TRAMES

    2I  0x8C0B51F2        NG  0x8C0337C2      (meme logique, NG en plus simple)

        r0 = 469
        mov.b @(r0,r4),r3 ; add #-1,r3 ; mov.b r3,@(r0,r4)   ; objet[+469] -= 1
        tst r3,r3 ; si NON NUL : rts          ; l'image tient encore
        sinon : bsr 0x8C0B5218                ; avancer dans le script

**`objet[+469]` est le nombre de trames qui restent a l'image courante.** Il est decremente
une fois par trame, et c'est tout le mecanisme.

### 3. D'OU VIENT LA DUREE : LA COPIE DE L'ENREGISTREMENT

Quand le parcours rencontre un enregistrement dont le premier mot vaut 256 ou plus -- une
IMAGE --, il saute au copieur `0x8C0B7324` (2I), qui **recopie l'enregistrement entier dans
la fiche**, a partir de `objet[+468]`, sur `objet[+460]` mots de quatre octets :

    r6 = objet[+448] + objet[+452]*4       ; l'enregistrement
    r5 = objet + 468                       ; la zone de copie
    boucle : mov.w @r6+,r3 ; mov.w r3,@r5 ; add #2,r5     (deux mots par tour)

Et comme le premier mot vaut `commande | duree << 8`, en petit-boutien :

    objet[+468] = la commande (0)      objet[+469] = LA DUREE
    objet[+470], +472                  objet[+474] = L'INDEX GLOBAL DU SPRITE

Verifie sur les octets : `00 04 00 00 00 00 90 9b` donne commande 0, duree 4, index
`0x9B90`. **La copie de l'enregistrement EST l'installation de la duree.** Il n'y a pas de
champ de minuterie separe : l'octet haut du mot copie fait office de compteur, et il est
decremente sur place.

### 4. LE CYCLE COMPLET, TRAME PAR TRAME

    installation   poser_script(objet, table, script)
                     objet[+448] = char_table[table][script]
                     objet[+460] = u16[script - 8]        (le pas, en-tete)
                     objet[+452] = pas * (objet[+264] - 2)  (l'index, juste avant le depart)
                     objet[+468..] = 0                    (la zone de copie)

    chaque trame   objet[+469] -= 1
                   si encore > 0 : rien de plus, l'image tient

    a zero         on avance : index += pas ; on lit u16 = @(script + index*4)
                     u16 <  256  -> jsr table_des_commandes[u16] (r4 = objet)
                                    rend non nul : on avance encore
                                    rend zero    : la trame est consommee, on s'arrete
                     u16 >= 256  -> c'est une IMAGE : le copieur verse l'enregistrement
                                    en objet[+468..], ce qui recharge objet[+469] avec la
                                    duree et objet[+474] avec l'index du sprite. Fin.

    fin de script  la commande 0x01 rappelle poser_script : **l'animation boucle d'elle-meme**,
                   rien d'exterieur ne la relance.

C'est tout. Une image tenue six trames -- la valeur la plus frequente des deux jeux -- c'est
`objet[+469]` qui part de 6 et descend a zero, six fois rien.

### CE QUI RESTE VRAIMENT

* **Les gestionnaires de commande, un par un.** Quinze opcodes sont employes par les decors ;
  quatre sont lus (`0x00` avance, `0x01` reboucle, `0x02` est en fait un en-tete, et le
  calcul de `0x8C0B530C`). Le plus employe de 2I, `0x2A` (149 fois, absent de NG), ne l'est
  pas.
* **Le second moteur** `0x8C0B4F9C`, choisi quand `objet[+496] & 4096` est nul : meme forme,
  pas lu ligne a ligne.
* **Le decompte de NG** est en `0x8C0337C2` et non pas au jumeau octet pour octet du 2I : les
  deux moteurs ont divergé entre les deux jeux (137 opcodes contre 116), et il faut le
  verifier la ou on s'appuie dessus.

---

## LES GESTIONNAIRES, LUS -- ET LE JEU D'OPCODES CORRIGE (23/09, fin)

### 1. LA MOITIE DE CE QU'ON APPELAIT « COMMANDES » N'EN SONT PAS

En sortant un enregistrement brut pour chaque valeur relevee, tout s'eclaire :

    cmd 0x02 : 02 00 00 00 00 00 04 00      duree 0  -> opcode... non : EN-TETE
    cmd 0x03 : 03 02 00 00 00 00 09 7f      duree 2  -> IMAGE
    cmd 0x09 : 09 06 00 00 00 00 bb 9b      duree 6  -> IMAGE
    cmd 0xFF : ff 02 00 00 00 00 24 8e      duree 2  -> IMAGE
    cmd 0x0C : 0c 00 00 00 00 00 02 00      duree 0  -> OPCODE (boucle, 2 tours)
    cmd 0x2A : 2a 00 00 00 00 00 00 01      duree 0  -> OPCODE (deplacer en Y de 1 pixel)

**`0x00`, `0x03` a `0x09` et `0xFF` ne sont pas des opcodes** : ce sont des enregistrements
d'IMAGE dont l'octet BAS est un drapeau. L'interprete ne regarde que le mot entier
(`commande | duree << 8`) : des que la duree n'est pas nulle, le mot depasse 256 et part au
copieur. Le drapeau reste dans `objet[+468]`, ou le dessinateur le relit.

**`0x02` n'est pas un opcode non plus** : c'est l'en-tete de huit octets du script suivant.

Il reste donc **dix vrais opcodes** dans les scripts de decor.

### 2. LES DIX, LUS UN PAR UN (2nd Impact, table `0x8C1C5BC8`)

| opcode | gestionnaire | ce qu'il fait |
|---|---|---|
| `0x01` | `0x8C0B52A0` | fin : rappelle `poser_script` -- **l'animation reboucle d'elle-meme** |
| `0x0C` | `0x8C0B54EA` | **debut de boucle 1** : sauve table/script/index en `+188`/`+190`/`+192`, charge le compteur `+186` |
| `0x0D` | `0x8C0B5536` | **fin de boucle 1** : `+186` -= 1 ; s'il reste des tours, restaure `+188`/`+190`/`+192` |
| `0x0E` / `0x0F` | `0x8C0B5576` / `0x8C0B55E8` | **la meme paire, compteur `+194`** : une seconde boucle, imbriquee |
| `0x28` | `0x8C0B5998` | **deplacer en X ET en Y** (mot 2 = dx, mot 3 = dy) |
| `0x29` | `0x8C0B5A64` | **deplacer en X** (mot 2) |
| `0x2A` | `0x8C0B5AEE` | **deplacer en Y** (mot 3) -- 149 emplois en 2I, le plus courant |
| `0x2B` | `0x8C0B5B30` | **appeler un effet** : `table[mot 1]` dans `0x8C17A2EC`, **51 entrees**, parametre `mot 2 & 0xFF` |
| `0x32` | `0x8C0B5C62` | **saut relatif en arriere** : `objet[+452] -= objet[+460] * (mot 3 + 1)` |

**Le deplacement, en detail.** Les trois opcodes de mouvement ajoutent `valeur << 8` a un
entier 32 bits :

    objet[+100] = xyz[0].cal   le X en 16.16        objet[+104] = xyz[1].cal   le Y

donc **256 = un pixel**. Le `2a 00 ... 00 01` d'exemple porte `mot 3 = 0x0100` : un pixel
vers le bas. Le `29 00 ... 04 00` porte `mot 2 = 0x0400` : quatre pixels. Et **le X respecte
le sens du sprite** -- `mov.b @(10,r4),r0 ; tst r0,r0` : `rl_flag` decide si on ajoute ou si
on soustrait. Le mot 1 choisit un mode (0, 2, autre).

**Le nombre de tours d'une boucle peut etre une variable.** Si le bit `0x4000` du mot 3 est
mis, `0x0C` ne prend pas le mot 3 comme compte : il va chercher `objet[+330 + (mot3 & 15)*2]`.
Une animation peut donc tourner un nombre de fois decide ailleurs -- par la routine de
l'acteur, donc par un declencheur.

**`0x2B` est le pont vers le reste du jeu.** Sa table de 51 entrees appelle du code de jeu
ordinaire ; l'entree 3, `0x8C0252CC`, commence par `jsr 0x8C0217E4` avec `r4 = 4` --
**c'est le tireur de place : elle CREE un acteur**, dans la liste 4, celle des animaux
d'Oro. Un script d'animation peut donc faire naitre un sprite. C'est « la chatte fait ses
chatons », mais commande depuis le script.

### 3. LES DEUX MOTEURS, DEPARTAGES

`objet[+496] & 4096`, teste en `0x8C018FD6` :

* **bit mis -> `0x8C0B5060`** : il applique le script DEMANDE (`+260` -> `+454`,
  `+262` -> `+456`, `+264` = le rang de depart), **puis parcourt** jusqu'a la premiere image.
  Il touche `+452` (l'index), `+999`, `+324`, `+1012`, et la constante 256.
* **bit clair -> `0x8C0B4F9C`** : le meme debut, **sans le parcours**. Il ne touche jamais
  `+452`. Il installe, et c'est tout.

La difference est lisible dans leurs jeux de constantes, et c'est sur ca qu'elle est
etablie -- pas sur une lecture ligne a ligne du second.

### 4. LA RACINE D'UNE CHAINE DE CREATION EST ATTEIGNABLE

    plw + 904  (2nd Impact, 0x8C645918)      plw + 868  (New Generation, 0x8C54422C)

Ce champ est **lu comme un POINTEUR** (`mov.l @(r0,r1)`) en 2I comme en NG, sur la moitie de
ses sites. C'est **le `WORK` que possede le combattant**. NG `0x8C098B1A` efface d'ailleurs
`ce_WORK->target_adrs`, ce qui ne se comprend que s'il s'agit bien d'une fiche.

Une chaine de creation partie d'un combattant a donc pour racine ce `WORK`-la, et
`objet[+812]` le transmet de generation en generation. Un acteur de decor qui lit
`target_adrs->routine_no[1]` lit alors, de proche en proche, **l'etat du combattant**.

> **Ce qui n'est toujours pas prouve** : qu'une chaine de decor PARTICULIERE remonte
> jusqu'a ce champ. Le balayage « une adresse de combattant calculee puis rangee » rend
> vingt sites en 2I et trois en NG, mais ceux que j'ai desassembles sont des faux positifs
> de la fenetre de recherche. Le chainon existe et est nomme ; il n'a pas ete suivi d'un
> bout a l'autre sur un decor donne.

---

## LA CHAINE SUIVIE JUSQU'AU COMBATTANT : ELENA 2, L'ID 85 (23/09, fin)

Frederic : « suis la chaine d'un decor jusqu'au combattant ». Voici celle d'**Elena 2**
(bande 15, New Generation), de la table d'etage jusqu'au `plw`, chaque maillon desassemble.

### La table des routines d'etage, au passage

    0x8C189170 + (decor + 2) * 4   ->  la routine de l'etage

Les deux premieres entrees sont autre chose ; a partir de la troisieme c'est un decor par
entree. **La preuve est Ibuki** : les decors 11, 12 et 13, qui partagent tout, tombent sur
les entrees 13, 14 et 15 -- `0x8C08ADBC` trois fois. Elena 2 est le decor 15, entree 17,
routine **`0x8C08B8B0`**.

### Les sept maillons

    1. REPARTITEUR        0x8C189170 + 17*4  ->  0x8C08B8B0      (decor 15, Elena 2)

    2. ROUTINE D'ETAGE    0x8C08B984  jsr 0x8C0AC4AA
                          immediats : id 85, pal 79, x 604, y 94, plan 2,
                                      table de scripts 0x8C0D9E88

    3. SPAWNER            0x8C0AC4AA  jsr 0x8C09AFA4 (r4 = 4)     tire une place, liste 4
                                      fiche = 0x8C554668 + place * 2048
                          0x8C0AC51A  jsr 0x8C0AC614              -> cree l'ID 86
                          chaque enfant herite  +812 = la racine,  +12 = son createur

    4. ROUTINE DE L'ACTEUR   0x8C1AD9F8 + 85*4  ->  0x8C0AB52C
                          r4 = objet[+812]                 ; la racine
                          dispatch sur racine->routine_no[0]  (0, 1, 2)
                          etat 0 : si 0x8C545260 (le gel) et 0x8C54527A sont nuls,
                                   jsr table[0x8C4DE9F0 + objet[+38]*4]   ; son propre etat

    5. UN ETAT : L'ANIMATION      0x8C0AB66C
                          jsr 0x8C0337C2       ; LE DECOMPTE DE TRAME du moteur d'animation
                          objet[+56] -= 1 ; a zero : disp_flag = 0, routine_no[1]++,
                          objet[+56] = 16

    6. UN AUTRE ETAT : LE PLACEMENT     0x8C0AB6A8
                          r3 = objet[+812] ; @r15 = r3          ; la racine, mise de cote
                          objet[+56] -= 1 ; quand il passe sous zero :
                            routine_no[1]++ ; jsr 0x8C03324C(objet, table 0, script 2)
                            objet[+1] = 1                       ; disp_flag : il apparait

    7. ET LA, LE COMBATTANT            0x8C0AB6E2
                          r2 = @r15                    ; la racine
                          r2 = racine[+818]            ; LE NUMERO DU COMBATTANT (0 ou 1)
                          muls.w 984, r2               ; * sizeof(plw)
                          r0 = 0x8C543F2E              ; = plw + 102
                          r2 = u16[r0 + cote*984]      ; SON X  (xyz[0].pos)
                          add #-64                     ; soixante-quatre unites a sa gauche
                          mov.w r2,@r3                 ; et l'objet se pose la

**La chaine est entiere** : repartiteur -> routine d'etage -> spawner -> place dans le tas ->
routine de l'acteur -> etat -> `objet[+812]` -> `racine[+818]` -> `plw[cote]` -> son X.

### Ce que ca resout au passage

`DECORS.md` portait depuis des jours, dans « ce qui reste », la ligne « *les autres objets en
dur (... Elena 2 85)* ». **L'id 85 d'Elena 2 est un objet qui se pose par rapport au
combattant** : c'est pour ca qu'aucun enregistrement ne donnait sa position, et pourquoi la
chercher dans un bloc ne pouvait pas marcher. Sa position n'existe pas dans les donnees --
elle se calcule a chaque partie, a 64 unites a gauche du joueur.

C'est le meme genre de piege que la menagerie d'Oro, et le meme remede : lire le spawner.

### Le seul maillon encore ouvert

**Qui ecrit `racine[+818]`**, le numero du combattant. Quatorze sites l'ecrivent en NG ; les
deux du moteur (`0x8C0B7204`, `0x8C0B721E`) le posent depuis un registre (`r9`, `r12`) dans
une routine dont l'entree n'a pas ete isolee -- elle est atteinte par branchement, pas par
un prologue. Le champ est nomme, sa lecture est prouvee, son ecriture ne l'est pas.

Et l'autre bout est connu : **`plw + 868` (NG) / `plw + 904` (2I) est un pointeur vers le
`WORK` que possede le combattant**. Si la racine d'une chaine est ce `WORK`-la, alors
`racine[+818]` est naturellement son propre numero. C'est coherent, ce n'est pas lu.

---

## QUI ECRIT `racine[+818]` -- ET LA PREUVE QUE `target_adrs` EST UN COMBATTANT (23/09)

Le maillon laisse ouvert la derniere fois est ferme, et il a ouvert le precedent avec lui.

### 1. CE QU'EST `+818` : LE NUMERO DU COMBATTANT

`0x8C034F3A` le montre sans ambiguite. La routine choisit une fiche de combattant de deux
facons :

    8C034F3A  r5 = 0x8C551F28            ; le tableau des fiches de combattant
    8C034F3C  cmp/eq #1,r0               ; r0 = objet[+6] (work_id) vaut 1 ?
       oui :  r0 = objet[+8] ; muls.w 886,r0         ; indexe par l'ID
       non :  r0 = objet[+818] ; and #1 ; mul.l 886  ; indexe par LE COTE
    8C034F54  r0 += r5                   ; 0x8C551F28 + n*886

**`objet[+818] & 1` est le cote, 0 ou 1.** Et le tableau `0x8C551F28`, 886 octets par
entree, n'a que deux entrees utiles : `0x8C551F28` et `0x8C55229E`. La troisieme,
`0x8C552614`, est deja la zone de l'etage -- le contexte `0x8C552674` s'y trouve, 96 octets
plus loin.

### 2. QUI L'ECRIT : LES SPAWNERS, AVEC L'ID

Trois sites posent `+8` (l'id) **et** `+818` (le cote) sur la meme fiche neuve :

    0x8C0AF410 / 0x8C0AF416   id 104, cote pris sur la pile (`mov.w @r15,r3`)
    0x8C0A5E34 / 0x8C0A5E80
    0x8C0B762E / 0x8C0B764E

Le spawner recoit donc le cote en parametre et le pose dans la fiche. C'est ce champ que
l'acteur ira relire, de proche en proche, pour savoir **de quel combattant il depend**.

### 3. LA RACINE D'UN COMBATTANT EST SA PROPRE FICHE

`0x8C08326C`, appele deux fois -- `0x8C015CCA` et `0x8C015D76`, l'initialisation des
combattants :

    8C083284  r0 = objet[+8]                    ; le cote (pose juste avant, 0x8C015C82)
    8C08328E  muls.w 886, r0
    8C083292  r3 = 0x8C551F28 + cote*886
    8C083294  objet[+812] = r3                  ; LA RACINE

Le `WORK` d'un combattant a donc pour racine **sa propre fiche de combattant**, et cette
fiche porte le `+818` que toute sa descendance ira lire.

### 4. ET LA PREUVE QUE `target_adrs` EST UN COMBATTANT

Elle est a deux instructions de la :

    8C015CB2  r2 = 0x8C543EC8                   ; plw
    8C015CB4  r0 = (cote + 1) & 1               ; L'AUTRE
    8C015CB6  mul.l 984, r0
    8C015CBC  r0 = plw + autre*984
    8C015CBE  mov.l r0,@(12,r14)                ; objet[+12] = target_adrs

**`target_adrs` d'un combattant est l'adresse de son ADVERSAIRE dans `plw`.** Une adresse de
`plw` rangee dans `target_adrs`, ecrite en clair. C'est exactement ce que le balayage du
matin n'avait pas su trouver -- il cherchait dans la region des decors, et le site est dans
l'initialisation des combattants, en `0x8C015Cxx`.

### CE QUE CA DONNE, BOUT A BOUT

    initialisation du combattant n   (0x8C015C78)
        WORK[+8]   = n                                  le cote
        WORK[+12]  = plw + ((n+1)&1) * 984              SON ADVERSAIRE
        WORK[+812] = 0x8C551F28 + n * 886               SA FICHE -- la racine
        WORK[+820] = ...

    creation d'un acteur de decor
        objet[+12]  = son createur          (`mov.l r1,@(12,r4)`)
        objet[+812] = le createur, ou la racine heritee (`objet[+812] = createur[+812]`)
        objet[+818] = le cote, quand le spawner le recoit (0x8C0AF416 et deux autres)

    l'acteur, chaque trame
        racine = objet[+812] ; cote = racine[+818] & 1
        x du combattant = u16[plw + 102 + cote*984]

**Le chemin est continu du combattant au sprite de decor, et chaque fleche est lue.**

> **Une remarque de methode, parce qu'elle a coute deux journees.** J'ai cherche
> `target_adrs <- plw` dans la region des decors, parce que c'est la que vivent les acteurs.
> Le site est ailleurs : dans le code des combattants, qui pose le lien une fois pour toutes
> au debut du round. **Quand un lien n'apparait pas du cote qui le lit, il faut le chercher
> du cote qui l'ecrit** -- et le cote qui l'ecrit n'est pas forcement dans le meme module.

---

## APPLIQUE A TOUS LES DECORS : QUI REGARDE UN COMBATTANT (23/09)

Le chemin etabli sur Elena 2 se generalise, et `outils/dependances.py` le fait tourner sur
les trente-six decors des deux jeux. Releve complet dans `dependances.txt`.

### Les deux tables qui manquaient

    routines d'etage    2I 0x8C1D3FB4 + bande*4 (17)    NG 0x8C189178 + bande*4 (19)
    routines d'acteur   2I 0x8C179FDC + id*4 (196)      NG 0x8C1AD9F8 + id*4 (186)

La table des acteurs de 2I est nouvelle. Elle se verifie sur la menagerie d'Oro : les ids
55, 71, 72, 73, 74 y ont des routines contigues (`0x8C03021C`, `0x8C0332CC`, `0x8C0337C4`,
`0x8C033994`, `0x8C033B8C`), chacune juste avant son spawner -- la meme disposition qu'en NG.

### Les trois chemins cherches

1. **En dur** : un litteral `plw + champ` dans la routine **et** un `muls.w` par la taille
   d'un combattant (2I 1036, NG 984). Sans l'index, un litteral egal a la base ne prouve
   rien, et le programme le dit.
2. **Par la racine** : la routine charge 812 **et** 818 -- `objet[+812]` designe la fiche de
   combattant, `racine[+818] & 1` donne le cote.
3. **Par la cible** : `mov.l @(3,rm),rn` puis une lecture a un champ de `WORK`, en suivant
   le registre a travers les copies et la pile.

### LE RESULTAT

**Sur les ids d'acteur du jeu entier**, 25 des 196 de 2nd Impact et 35 des 186 de New
Generation lisent un combattant. Mais la question n'est pas la : c'est **lesquels sont
crees par une routine d'etage**, donc appartiennent au decor.

| | ids qui lisent un combattant | dont crees par une routine d'etage |
|---|---|---|
| 2nd Impact | 25 sur 196 | **aucun** |
| New Generation | 35 sur 186 | **douze** |

**2nd Impact n'a aucun sprite de decor qui regarde un combattant.** Ses vingt-cinq lecteurs
sont tous des effets du cote combattant -- l'id 32 est pose en `0x8C02BC8C`, l'id 94 en
`0x8C03794A`, et aucune des dix-sept routines d'etage ne les cree. La verification croisee
est la menagerie d'Oro : le programme lui rend exactement les ids 55, 56, 71, 72, 73, 74,
ceux que ce document porte depuis des semaines, et **aucun des six ne lit un combattant**.
Le chat, le chien et le perroquet vivent leur vie.

**New Generation, elle, en a douze**, et voici lesquels :

| decor | id | chemin |
|---|---|---|
| Alex (1), Sean (2) | 64 | en dur |
| Sean (2) | 44 | en dur |
| Sean (2), Yun 1/2 (5,6), Necro (10), Elena 2 (15), Yang 1/2 (17,18) | **87** | **par la cible** : `+38` son etat, `+54` son etat precedent |
| Sean (2), Ken (4), Elena 2 (15) | 88 | en dur (`+820`) |
| Ryu (7,8) | 67 | en dur |
| Hugo (9) | 8 | par la racine ; par la cible |
| Ibuki (11,12,13) | 83 | en dur (`+84` position_x) ; par la racine |
| Ibuki (11,12,13), **Elena 2 (15)** | **85** | **en dur** : `+102`, son X |
| Ibuki (11,12,13), Elena 2 (15) | 86 | par la cible : `+54` son etat precedent |
| Elena 1 (14) | 45 | en dur |
| Oro (16) | 72, 74 | en dur (sans index -- faible) |

**L'id 87 est le plus repandu : sept decors.** C'est le guetteur d'etat lu en entier le
23/09 (`0x8C0ABC24`, etat 2 en `0x8C0ABCA6`) : il ne se montre que si l'etat de sa cible
depasse 2. Et lire `+38` **avec** `+54` -- l'etat courant et l'etat precedent -- c'est
detecter un CHANGEMENT d'etat. Sept decors de New Generation ont un sprite qui reagit a ce
que fait un combattant.

**L'id 85 est celui d'Elena 2**, deja lu ligne a ligne : il se pose a
`plw[cote].xyz[0].pos - 64`. Il sert aussi aux trois Ibuki.

### CE QUE CA CHANGE POUR LE PORT

Ces douze-la ne peuvent pas etre poses par un enregistrement : **leur position ou leur
apparition depend du combattant**, donc de la partie. C'est l'explication de la ligne « les
autres objets en dur » qui trainait dans « ce qui reste » -- Elena 2 85, Ibuki 83, Sean 44.
Ils n'ont pas de position dans les donnees parce qu'ils n'en ont pas du tout.

### LES BORNES DU RELEVE, DITES

* La liste des acteurs d'un etage vient de `routine2i` / `routineng`, qui suivent `jsr`,
  `jmp`, `bsr` et descendent **d'un niveau** dans les spawners. Un acteur cree deux niveaux
  plus bas n'y figure pas.
* « en dur (sans index) » signale un litteral `plw` sans `muls.w` : c'est peut-etre une
  coincidence d'adresse, et les deux ids d'Oro sont dans ce cas.
* Le chemin « par la racine » est detecte sur la presence des deux constantes 812 et 818
  dans la meme routine, pas sur le flot de donnees.

    outils/dependances.py      ->  dependances.txt

---

## ET DANS 3SX ? NON -- L'ETAT DES LIEUX, CHIFFRE (23/09)

Question de Frederic. Croisement des trente couples (decor, id) dependants d'un combattant
avec les **519 fiches New Generation** de `decor_objets_data.c`.

| | |
|---|---|
| couples (decor, id) qui lisent un combattant | **30** |
| **absents du port** -- aucune fiche | **27** |
| presents | 3 : Hugo id 8, Elena 1 id 45, Oro id 72 |
| presents ET traites comme dependants | **1** (Elena 1 id 45, et pas pour la bonne raison) |

* **Hugo id 8** et **Oro id 72** : `variante 0xF`, `comportement 0` -- des objets ordinaires.
* **Elena 1 id 45** porte `comportement 5` (`TRAJET`), un trajet FIXE de `{33, -128, 0, -1}`.
  Le port lui fait refaire le meme aller-retour toutes les 33 trames ; le binaire, lui, le
  fait dependre d'un combattant. Le comportement est la, la cause n'est pas la bonne.

**Les seules fiches NG que le port fait dependre des combattants** sont, toutes causes
confondues :

    bande  6  id  29   comportement 4     le poisson noir, transpose de Yang 2I
    bande  7  id  65   comportement 5     un trajet fixe
    bande 14  id  45   comportement 5     un trajet fixe
    bande 16  id  71   variante 0x3F      LES BITS 0x10|0x20 : la mecanique du chien d'Oro
    bande 18  id  29   comportement 4     le poisson noir

Une seule -- l'id 71 d'Oro NG -- emploie vraiment le lien aux combattants, et c'est
l'heritage direct du chien d'Oro de 2nd Impact, ecrit bien avant cette lecture.

### LE PORT LE DIT LUI-MEME

`decor_objets.h`, champ `boucle`, ecrit le 29/08 :

> « Les acolytes de Gill tournent la tete vers les combattants : leurs images sont des
> ORIENTATIONS choisies par la position des joueurs, pas des etapes d'un cycle. [...]
> **Suivre le regard des combattants demanderait de choisir l'image d'apres leur position,
> ce que rien ici ne sait faire.** »

Le constat etait juste et il tenait de l'observation. Ce qui manquait etait le MECANISME.
Il est la maintenant : `objet[+812]` -> `racine[+818] & 1` -> `plw[cote]`, ou bien
`objet[+12]` -> `target_adrs`, et les champs `+102` (X), `+38`/`+54` (l'etat et le
precedent), `+68` (le figement de coup).

### CE QUE CA EXPLIQUE RETROSPECTIVEMENT

La ligne « **les autres objets en dur** » qui trainait dans « ce qui reste » -- Alex 69/**64**,
Dudley 65/68, Ibuki 82/75/**83**/20, Hugo 63, Necro 7, **Elena 2 85** -- recoupe la liste des
dependants sur au moins trois entrees : **64, 83, 85**. Ils n'ont jamais eu d'enregistrement
a trouver, pour la meme raison que le chat d'Oro n'en avait pas : **leur position se calcule
a partir du combattant, elle n'existe pas dans les donnees.**

### LE PLUS PETIT PAS UTILE

Le port sait deja faire un `comportement` -- cinq machines a etats tournent dans
`decor_objets.c`. Il lui manque **la lecture d'un combattant**. Deux champs suffiraient pour
les douze ids :

    le cote          -> pour l'id 85 : x = plw[cote].x - 64
    l'etat, +38 et +54  -> pour l'id 87, le plus repandu (sept decors) : se montrer quand
                           l'etat depasse 2, c'est-a-dire quand le combattant fait quelque
                           chose

Cote 3SX ces deux valeurs sont a portee de main -- le port EST le code de 3rd Strike, ou
`plw[i].wu.routine_no[1]` et `plw[i].wu.xyz[0].disp.pos` sont des champs nommes. **La
difficulte n'etait pas de les lire, c'etait de savoir lesquels.**

---

## APPLIQUE DANS 3SX : LA REGLE DE LA DUREE (23/09)

Ce que l'interprete a appris le 23/09 est maintenant dans la chaine.

### Le defaut

`script_images`, dans `animer2i.py` et `animerng.py`, ne gardait un enregistrement que si
son PREMIER OCTET etait nul :

    if cmd == 0x00 and duree:
        out.append((idx, duree))

L'interprete de la Dreamcast (`0x8C0B50DC`) ne fait pas ca : il compare le PREMIER MOT a
256. Ce mot vaut `premier octet | duree << 8` -- des que la duree n'est pas nulle, le mot
depasse 256 et l'enregistrement est une IMAGE, **quel que soit son premier octet**. Celui-ci
n'est qu'un drapeau, recopie dans la fiche en `+468` pour la routine de l'objet.

    if duree:
        out.append((idx, duree))
        continue
    if cmd == 0x01:
        break

**88 images etaient perdues en 2nd Impact, 67 en New Generation** : tous les drapeaux 2,
3 a 9, et 0xFF.

### Et les opcodes que `script_deroule` refusait

Il levait une exception sur tout ce qui n'etait ni `0x01` ni `0x0C`/`0x0D`. Les cinq autres
sont maintenant traites, avec ce que la lecture du 23/09 en a dit :

    0x0E / 0x0F        la SECONDE boucle, compteur `+194`, imbriquee
    0x32               un saut relatif en arriere de (mot 3 + 1) enregistrements
    0x28 0x29 0x2A     deplacer en X et/ou Y -- passes : ils ne changent pas l'image
    0x2B               appeler un effet -- passe

### CE QUE CA CHANGE, MESURE

    avant 758 fiches, apres 760.  12 nouvelles, 10 disparues, **123 dont le nombre
    d'images change**.

* **Etage 25 (`bg03`) est le plus remue** : `a25o7` passe de 12 a 36 images, `a25o8` de 12
  a 31, `a25o16` de 1 a 19, tandis que `a25o13` tombe de 13 a 1 et `a25o18` de 7 a 4. Ce
  n'est pas seulement des images retrouvees : `animer2i.py` **choisit entre deux scripts
  celui qui a le plus d'images** (`1550`), et cette longueur etait fausse. Le choix bascule
  donc sur plusieurs objets.
* **Etages 42 et 54** (`ng05`, `ng11`, les deux memes decors) : quatre objets apparaissent,
  trois disparaissent.
* **Etage 51** (`ng0e`, Elena 1) : `n14o5m1`, 36 images, apparait.
* **Partout ailleurs** : une image de plus sur une animation -- un mouvement plus complet.

`verifier_objets.py` finit par « Rien a signaler » : bornes, index et tables se recoupent,
et aucun etage ne depasse son budget (le plus charge, l'etage 31, tient 78 motifs sur 128).

### LA SORTIE

    buildsx-anim-corrigees.exe
    "ANIMATIONS CORRIGEES - 2I et NG.cmd"     CRLF, ASCII, a double-cliquer

Le retour arriere est immediat, tout est garde :

    outilsnimer2i.py.avant23    outilsnimerng.py.avant23
    src\portideo\decor_objets_data.c.avant23

> **Ce qui n'est PAS dans cette livraison** : les douze acteurs de New Generation qui
> dependent d'un combattant. Vingt-sept des trente couples (decor, id) n'ont aucune fiche
> dans le port, et leur ajouter une position qui n'existe pas dans les donnees est un autre
> chantier -- celui de la section « ET DANS 3SX ? ».

---

## LE REGARD DES ACOLYTES DE GILL, LU ET PORTE (23/09)

Frederic, pendant que la chaine tournait : « *dans le decor de Gill 2I, l'acolyte du milieu
suit clairement du regard l'un des deux ou les deux combattants* ». Il a raison, et le
mecanisme etait a trois sauts de la.

### Comment on y est arrive

Le releve `dependances.py` disait « **2nd Impact : aucun sprite de decor cree par une
routine d'etage ne regarde un combattant** ». C'etait faux, et voici pourquoi : `routine2i`
ne descend que d'UN niveau dans les spawners, et les acolytes sont crees par un chargeur de
bloc, pas par un spawner a immediats. Leur id n'apparaissait donc nulle part.

Le chemin qui a marche :

1. `routine2i.py 0` montre que la routine de Gill appelle **`0x8C04AE04`** avec le bloc
   `0x8C183DC8`, quatre enregistrements : (320,64 script 11), (576,72 script 12),
   (208,136 script 5), (720,96 script 6) -- les quatre acolytes.
2. `0x8C04AE04` tombe dans la routine de **l'id 184** (`0x8C04AA54`..`0x8C04AEF8`), que le
   recensement avait deja signalee comme lisant `plw + 102`.
3. Et le site, `0x8C04ACC2` :

        r0 = objet[+54]                  le cote
        muls.w 1036,r0                   * sizeof(plw)
        r4 = u16[plw + 102 + cote*1036]  LE X DU COMBATTANT
        shad #-6,r4                      >> 6 : des tranches de 64 pixels
        and #15,r4                       seize tranches
        r0 = u16[0x8C183DA8 + r4*2]      L'ORIENTATION

**La table est posee juste avant les enregistrements des acolytes** --
`0x8C183DA8 + 32 = 0x8C183DC8` -- et c'est la meilleure preuve qu'elle leur appartient :

    0 0 0 0 0 0 1 1 2 2 3 3 4 4 5 5

Six orientations. La tete reste de face tant que le combattant est dans le tiers gauche de
la scene, puis tourne d'un cran tous les 128 pixels.

**Ce n'est pas une animation, et c'est pour ca que le port les figeait.** Le champ `boucle`
de `decor_objets.h` le disait depuis le 29/08 -- « *leurs images sont des ORIENTATIONS
choisies par la position des joueurs [...] ce que rien ici ne sait faire* ». Maintenant si.

### Ce qui est porte

**`REGARD`, comportement 7** dans `decor_objets.c` :

    image = REGARD_TABLE[(plw[cote].wu.xyz[0].disp.pos >> 6) & 15]

Il n'a ni `pas` ni `suites` : `image_conduite` rend directement `nos[k].regard`, le champ
que le chien d'Oro employait deja. Le generateur marque les quatre enregistrements du bloc
`0x8C183DC8` (`REGARD_BLOCS` dans `animer2i.py`).

**`SUR_COMBATTANT`, comportement 6** : l'id 85 de New Generation (Elena 2, etage 52), le
premier objet du port dont la position ne vient PAS des donnees. Sa routine le pose a
`plw[cote].xyz[0].pos - 64`. Trois fiches ecrites (l'objet est decoupe en trois morceaux).

### LE COTE N'EST PAS LU, ET C'EST LE SEUL POINT

Les deux routines prennent le combattant que leur chaine de creation designe --
`objet[+54]` pour l'acolyte, `racine[+818]` pour l'id 85. Le port n'a pas cette chaine.
**On prend le joueur 1**, et c'est une ligne dans chaque comportement (`REGARD_COTE`,
`SUR_COMBATTANT_COTE`).

### Deux defauts du generateur, corriges au passage

* `animer2i.fiche` ecrivait `len(o["bornes"]) - 1` sans verifier : un comportement SANS
  suites la faisait tomber. Il ecrit maintenant `NULL, NULL, 0`, comme le fait deja
  `animerng` pour un TRAJET.
* le meme, pour la table des pas.

### LA SORTIE

    build\3sx-regard.exe
    "LE REGARD DES ACOLYTES - et les animations corrigees.cmd"   CRLF, ASCII

    238 fiches de 2I + 525 de NG = 763.  verifier_objets : « Rien a signaler ».

Gardes pour le retour arriere : `animer2i.py.avant23`, `animerng.py.avant23`,
`objetsng.py.avant23`, `decor_objets.c.avant23`, `decor_objets_data.c.avant23`.

> **Et la lecon sur le releve** : « aucun en 2I » voulait dire « aucun que MON crible
> attrape ». Les acolytes de Gill etaient dans le binaire depuis le debut, a trois sauts
> d'une routine que le recensement avait deja nommee. **Un releve automatique ne vaut que
> ce que vaut son chemin d'acces, et il faut le dire avec le resultat.**

---

## LE CRIBLE CORRIGE, ET CE QU'IL TROUVE EN PLUS (23/09)

Les acolytes de Gill ont montre le defaut de `dependances.py` : il n'attrapait un acteur
que par son ID, et un id ne se voit que quand un spawner l'ecrit en constante. **Les
acolytes sortent d'un CHARGEUR DE BLOC** (`0x8C04AE04`), qui n'ecrit aucun id -- il est
simplement SITUE DANS la routine de l'id 184.

La correction tient en trois lignes : toute cible d'appel d'une routine d'etage qui tombe
dans l'intervalle d'une routine d'acteur designe cet acteur.

    for i, r in acteurs.items():
        if r <= c < lim_a.get(r, r):
            ids.add(i)

Le crible retrouve alors les acolytes tout seul -- **et deux autres familles que le premier
relevé avait manquees.**

### CE QUI CHANGE AU RELEVE

| | avant | apres |
|---|---|---|
| 2nd Impact, decors avec un sprite qui regarde un combattant | **0** | **5** |
| New Generation | 12 couples | **16** |

**2nd Impact -- les deux familles :**

* **id 184** (`0x8C04AA54`), bande 0 : les quatre acolytes de Gill. `en dur (+102 son X)`.
  Lu en entier, porte, livre -- voir la section precedente.
* **id 13** (`0x8C025BC8`), bandes **7, 8, 9 et 15** : quatre decors. Son site
  `0x8C026FA4` fait

        r4 = objet[+champ] ; r4 = r4->[+12]     la cible
        r5 = objet[+102]                        SON x a lui
        r3 = cible[+102]                        le x de la cible
        cmp/gt r3,r5                            suis-je a droite d'elle ?
        r0 = objet[+10]                         mon sens
        ... r2 = +1 ou -1 selon le sens

  **Il se compare en X a sa cible et en tire un signe.** Ce n'est pas un regard : c'est un
  deplacement ou une orientation qui suit. Il n'est PAS lu jusqu'au bout.

**New Generation -- ce qui s'ajoute :**

* **id 100** (`0x8C0AD470`), bandes 0 et 1 : le jumeau exact de l'id 94 de 2I. Il lit le X
  du combattant (`0x8C0AD6BE`) et **le range en `objet[+60]`**, puis indexe une table de
  trente-deux entrees (`0x8C1B3154`) par un AUTRE champ (`objet[+64] >> 5`). Ce n'est donc
  pas le regard simple de l'acolyte : le X sert ailleurs. Pas lu jusqu'au bout non plus.

### LA LECON, ET ELLE VAUT POUR TOUT LE CHANTIER

Le premier relevé disait « **2nd Impact : aucun** ». Il aurait fallu ecrire « aucun que mon
crible attrape ». Les acolytes de Gill etaient dans le binaire depuis le debut, a trois
sauts d'une routine que le recensement avait **deja nommee** (l'id 184 figurait dans la
liste des vingt-cinq lecteurs de `plw`). Ce qui manquait etait le chemin de l'etage jusqu'a
elle.

> **Un releve automatique ne vaut que ce que vaut son chemin d'acces, et il faut le dire
> AVEC le resultat, pas apres.** Et c'est l'oeil de Frederic qui a ouvert la faille : il a
> vu bouger une tete que le port figeait.

    outils/dependances.py   ->  dependances.txt      (ancienne version : .avant23)

---

## LES DEUX CIBLES : L'ID 13 N'EXISTE PAS, L'ID 100 EST UN GENERATEUR (23/09)

Frederic a demande les deux cibles nommees la veille. Voici ce qu'elles sont.

### 1. L'ID 13 DE 2nd IMPACT : C'ETAIT MON ARTEFACT

`dependances.py` le donnait sur quatre decors (bandes 7, 8, 9, 15). C'est faux, et la faute
est dans mon crible. Les appels en cause sont

    8C0DD7E0 -> 8C0277C4  r4=4   immediats {8: 14}
    8C0DDB7E -> 8C0277C4  r4=6   immediats {8: 14}
    ...

**`0x8C0277C4` ECRIT l'id 14.** Il tombe dans l'intervalle de la routine de l'id 13
(`0x8C025BC8`..`0x8C027806`) parce que le spawner d'un acteur est pose juste avant sa
routine -- mais il ne cree pas d'id 13. Ma correction de la veille, qui attribuait un
acteur par l'intervalle, l'inventait.

**LA REGLE EST HIERARCHIQUE**, et elle est maintenant dans l'outil :

    1. si la cible ECRIT un id (`mov #id,r0 ; mov.w r0,@(8,rn)`), c'est lui, on s'arrete ;
    2. sinon seulement, la cible est un CHARGEUR DE BLOC et l'acteur est celui dont la
       routine la contient -- le cas des acolytes de Gill (`0x8C04AE04`, id 184).

L'ordre compte : la premiere version ne faisait que le 1 et manquait Gill, la deuxieme ne
faisait que le 2 et inventait des id 13.

**Le relevé corrigé donne, pour 2nd Impact, UNE SEULE famille dependante d'un combattant :
l'id 184, les acolytes de Gill.** Celle que Frederic a vue, et qui est portee.

### 2. L'ID 100 DE NEW GENERATION : LU JUSQU'AU BOUT

Huit sites, sur les bandes 0, 1, 7, 8 et les trois Ibuki. Sa routine `0x8C0AD470`, a
`0x8C0AD6B2` :

    r2 = objet[+818]                     le cote
    muls.w 984,r2                        * sizeof(plw)
    r1 = u16[0x8C543F2E + cote*984]      LE X DU COMBATTANT   (plw + 102)
    objet[+60] = r1                      il le RANGE
    r0 = objet[+64] ; shad #-5 ; and #31 trente-deux tranches de 32
    r2 = u16[0x8C1B3154 + idx*2]         une HAUTEUR
    objet[+52] = r2
    ...
    jsr 0x8C038DBA(r4 = objet, r5, r6, r7)   LE CREATEUR GENERIQUE

La table `0x8C1B3154` monte par paliers :

    16 16 16 32 32 32 48 48 48 56 56 56 64 64 64 72 72 72 72 80 80 80 88 88 88 96 96 96
    104 104 104 104

**L'id 100 n'est pas une animation : c'est un GENERATEUR.** Il prend le X d'un combattant,
en tire une hauteur par paliers, et **fait naitre un objet** a cet endroit -- par le meme
createur `0x8C038DBA` que l'id 85 d'Elena 2.

### POURQUOI IL N'EST PAS PORTE

**Le port ne sait pas creer un objet en cours de partie.** `decor_objets.c` travaille sur
une liste de fiches FIXE, etablie au chargement de l'etage : le rang d'un objet entre dans
la cle du cache de motifs, dans l'emplacement de sa palette et dans son ordre de dessin.
C'est ecrit noir sur blanc dans la note sur les variantes d'Oro -- « *s'il changeait en
cours de route, `DecorObjets_Combien` renverrait un autre compte entre deux appels et les
rangs glisseraient* ».

Porter l'id 100 demande donc une **creation dynamique**, c'est-a-dire un rang qui n'est plus
fixe. Ce n'est pas une correction d'animation : c'est un changement d'architecture du
module, et il touche ce qui marche. **Je ne l'ai pas fait.**

### CE QUI RESTE VRAI APRES CES DEUX CIBLES

| | sprites de decor dependant d'un combattant | portes |
|---|---|---|
| 2nd Impact | **1 famille** : id 184, les acolytes de Gill | **oui** |
| New Generation | id 85 (Elena 2, Ibuki), 87, 86, 88, 44, 64, 67, 83, 8, 127, **100** | **id 85 seul** |

L'id 87 -- sept decors, le guetteur d'etat -- reste le plus gros morceau accessible : il ne
cree rien, il se montre ou se cache selon l'etat de sa cible. C'est la prochaine cible
utile, et elle ne demande pas de creation dynamique.

---

## UN SEUL DES QUATRE ACOLYTES REGARDE -- ET CE QUE L'ID 13 ET L'ID 19 SONT VRAIMENT (23/09 au soir)

Frederic, apres l'exe precedent : « *dans Gill 2I, l'acolyte central suit bien des yeux les
combattants mais les autres personnages n'ont plus aucune animation* ». Il a raison sur les
deux moities de la phrase, et les deux viennent de la meme faute : **j'avais marque REGARD
les quatre enregistrements du bloc, alors que le binaire n'en designe qu'un.**

### 1. LE CHARGEUR NUMEROTE LES ACOLYTES, ET LA ROUTINE REPARTIT DESSUS

Le chargeur du bloc (`0x8C04AE04`) ecrit en `objet[+52]` **l'indice de sa boucle** :

    8C04AE82  add #52,r3            r3 = objet + 52
    8C04AE9A  mov.w r11,@r3         objet[+52] = r11
    8C04AEB6  add #1,r11            0, 1, 2, 3

et l'id 184 (`0x8C04AA54`) repartit la-dessus **avant toute autre chose** :

| indice | enregistrement | x | script | ou il va | ce qu'il fait |
|---|---|---|---|---|---|
| 0 | `8C183DC8` | 320 | 11 | `8C04AA92` | `mov #11,r6` puis le poseur ORDINAIRE `0x8C0B4AD4` |
| **1** | **`8C183DD0`** | **576** | **12** | **`8C04AB88`** | **le regard** |
| 2 | `8C183DD8` | 208 | 5 | `8C04AD0C` | `objet[+456]`, le script de son enregistrement |
| 3 | `8C183DE0` | 720 | 6 | `8C04AD0C` | idem |

Seul l'indice 1 passe par `0x8C04ACB2`. Les trois autres posent un script et le laissent se
derouler : **ce sont des animations ordinaires**, et les figer etait l'erreur.

### 2. LE REGARD N'EST PAS UNE IMAGE, C'EST UNE ETAPE DE SCRIPT

    8C04ACC4  mov.w @(2,r5),r0          r0 = objet[+54], le cote
    8C04ACC6  muls.w 1036,r0            * sizeof(plw)
    8C04ACCC  mov.w @(r0,r4),r4         r4 = plw[cote] + 102 : LE X DU COMBATTANT
    8C04ACCE  shad #-6,r4               par tranches de 64
    8C04ACD0  and #15,r4                seize tranches
    8C04ACD8  mov.w @(r0,r1),r0         r0 = u16[0x8C183DA8 + i*2]
                                        0 0 0 0 0 0 1 1 2 2 3 3 4 4 5 5
    8C04ACDC  mov.w r0,@(4,r5)          objet[+56] = l'orientation
    8C04ACE4  cmp/eq r0,r3              la meme qu'a la trame d'avant (+58) ? alors RIEN
    8C04ACF0  mov #12,r6                LE SCRIPT 12
    8C04ACF4  mov.w @(r0,r14),r7        r7 = l'orientation
    8C04ACF6  add #1,r7
    8C04ACF8  jsr 0x8C0B4B90            poser(objet, table 0, script 12, etape r7-1)

`0x8C0B4B90` n'est pas le poseur ordinaire : il prend une **etape de depart** (`add #-1,r7`
puis autant d'avances). L'orientation est donc un NUMERO D'ETAPE dans le script 12 -- ce que
le port rend exactement en prenant l'image de ce rang, et le script 12 a justement six
images pour six orientations.

### 3. LA REGLE DU PALINDROME EST RETIREE

`est_une_boucle` gelait sur l'image 0 toute suite dont les ecarts dessinent un palindrome.
Elle ne servait qu'a **un seul objet de tout 2nd Impact** : l'acolyte 0 de Gill

    0 86 89 147 189 259 351 382 351 259 189 147 89 86

Le binaire tranche : l'indice 0 pose son script 11 par le poseur ordinaire. Un palindrome est
normal pour une tete qui part et revient. La fonction rend `True` et ne decide plus rien.
**C'est la mesure qui cede devant la lecture, pas l'inverse.**

### 4. L'ID 13 ET L'ID 19 : J'AVAIS ANNONCE UN RECEVEUR DE COUP QUI N'EXISTE PAS

J'avais dit que la famille « *un element du decor qui se brise au contact d'une chute* »
etait l'id 13 de 2I (`0x8C0266B6`) et l'id 19 de NG (`0x8C09EEF2`), qui lisent par `hit_adrs`
le type, l'etat, `hit_stop` et le X de ce qui les touche. **C'est faux.** Les deux sites sont
le meme prologue :

    8C0266B6  mov.l @(16,r15),r4
    8C09EEF2  mov.l @(16,r15),r4

`@(16,r15)` est **la pile**, pas un objet. `mov.l @(16,rn),r4` et `mov.l @(16,r15),r4` ont la
meme forme, et `par_pointeur.py` ne filtrait pas `r15` : tout prologue qui range son `r4` en
pile et le relit passait pour un acteur qui lit `hit_adrs`. Le filtre est pose
(`if ((w >> 4) & 15) == 15: continue`), et le releve refait :

**IL NE RESTE, DANS LES DEUX JEUX, AUCUNE LECTURE DE COMBATTANT PAR `hit_adrs` AUTRE QUE `+0`
(existe-t-il) ET UN `+40` EN 2I.** Aucun sprite de decor ne se brise au contact d'un
combattant par ce chemin. Si le mecanisme existe, il passe ailleurs -- et il n'est pas dans ce
que les routines d'acteur lisent par pointeur.

Ce que les deux routines SONT, pour memoire :

* **2I id 13** (`0x8C025BC8`..`0x8C027806`). Son unique spawner, `0x8C02767C`, n'est appele
  que depuis `0x8C01FDC4` -- **au-dessous de la premiere routine d'acteur** (`0x8C021DA8`),
  donc par le moteur, jamais par une routine d'etage. **Ce n'est pas un sprite de decor.** Sa
  seule dependance a un combattant est `target_adrs[+10]`, le sens.
* **NG id 19** (`0x8C09E4B8`..`0x8C09F29A`). Un acteur d'EFFET pilote par un descripteur en
  `objet[+736]` : l'etat 0 recopie le descripteur (`+2`, `+4`, `+12`, `+15`, `+16`, `+18`),
  l'etat 1 remet `hit_stop` positif, verifie le gel de trame `0x8C545260` puis saute dans la
  table `0x8C1B05DC` indexee par le type, l'etat 2 le libere. Il est cree par l'id 53,
  lui-meme cree par la bande 14 -- **pas par la bande 0 comme je l'avais ecrit.**

### 5. DEUX CORRECTIONS D'OUTIL QUI EXPLIQUENT CES DEUX ERREURS

**`dependances.py`, les cibles de premier niveau.** `routineng` indente : deux espaces pour un
appel de la routine d'etage, quatre et plus pour ce qu'il trouve en descendant, **y compris
les etats internes d'un acteur** (`dispatch -> 8C09E7E4`). Ces adresses-la ne creent rien. En
les prenant pour des cibles, le repli par intervalle inventait un id 19 sur la bande 0 --
alors que le seul spawner de cette ligne, `0x8C09E3B6`, ecrit `mov #12`.

**`dependances.py`, les ids du tas de litteraux.** Un id ne se charge pas toujours par
`mov #id,r0` : au-dela de 127 il vient de `mov.w @(d,pc),r0`. L'id 184 des acolytes est de ce
genre (`0x8C04AE76`). `poses()` lit maintenant les deux formes, et l'id 184 est trouve **par
son ecriture** au lieu d'etre rattrape par l'intervalle -- l'intervalle etant justement ce qui
inventait des acteurs.

### 6. LE BILAN DEMANDE : QUI SUIT LES COMBATTANTS DES YEUX

La signature d'un regard est etroite, et elle ne se confond avec rien : **lire le X d'un
combattant, en tirer un numero par tranches, et s'en servir comme ETAPE d'un script**, avec la
garde « seulement si ca a change » et la memoire de l'etape precedente.

| jeu | acteur | decors | etat |
|---|---|---|---|
| 2nd Impact | **id 184** (`0x8C04AA54`) | **Gill**, et un seul acolyte sur quatre | **porte** |
| New Generation | **id 127** (`0x8C0B2118`) | **Yun 1, Yun 2, Yang 1, Yang 2** (bandes 5, 6, 17, 18) | **absent du port** |

Et c'est tout. Les autres acteurs qui touchent a un combattant ne regardent pas :

| acteur | ce qu'il lit | ce qu'il en fait |
|---|---|---|
| NG id 85 (Elena 2, Ibuki) | `plw + 102` | une POSITION -- c'est SUR_COMBATTANT, porte |
| NG id 100 (huit bandes) | `plw + 102` | une hauteur par paliers, puis il CREE un objet |
| NG id 83 (les trois Ibuki) | `plw + 84` | il range le X en `objet[+52]` avec un compte a rebours de 40 |
| NG id 87 (sept bandes) | `cible[+38]`, `[+54]` | il se MONTRE ou se cache -- c'est REACTIF, au choix |
| NG id 88, 44, 45, 64, 67 | `+0`, `+3`, `+820` | ils testent l'existence ou le personnage, rien de plus |

L'id 127 a exactement la meme forme que l'acolyte de Gill, en plus complet :

    8C0B21DC  r0 = 0x8C543F1C           plw + 84, position_x
    8C0B21E6  r6 = u16[plw + 84 + cote*984]
    8C0B21EA  cmp/ge r2,r4              contre les bornes de 0x8C1B339E, par tranches de 10
    8C0B21F4  objet[+52] = la tranche
    8C0B2296  mov.b @(10,r14),r0        rl_flag : si l'objet est retourne,
    8C0B22A6  r2 = u16[0x8C1B3394 + etat*2]   la tranche est MIROITEE
    8C0B22B2  cmp/eq                    la meme qu'avant (+54) ? alors RIEN
    8C0B22CC  jsr 0x8C033304            poser(objet, 0, objet[+58], etape r7-1)

`0x8C033304` est le jumeau exact de `0x8C0B4B90`. C'est un regard, et il a en plus le miroir
que Gill n'a pas.

**Pourquoi il n'est pas porte.** Aucune fiche de `ng05`, `ng06`, `ng11` ou `ng12` ne vient de
cette chaine : les trente objets de `ng05` viennent de `0x8C0A0C20` (ids 21 a 24),
`0x8C0A0070` (id 18), `0x8C0AC75C` (id 87) et des listes d'elements `0x8C1AEB88` /
`0x8C1AF1FA`. L'id 127 n'y est pas, et ce n'est pas un oubli du releve : la bande appelle
`0x8C0B2454`, qui cree **un objet par combattant**, `objet[+812]` pointant le `plw` lui-meme,
et sous condition du PERSONNAGE choisi :

    8C0B2314  mov.w @(r0,r12),r0        r0 = plw[+820], le personnage
    8C0B2316  cmp/eq #10,r0
    8C0B2322  cmp/eq #3,r0              Yun et Yang

C'est la meme mecanique que les « amis du decor » du chien d'Oro, mais elle cree ici des
objets que la liste de fiches du port ne connait pas. **Cela rejoint, et explique, ce que
Frederic avait note bien avant** : « *Pour le decor de Yun, manquent les animations des 2
personnages devant le tram* ». Ce ne sont pas des animations manquantes : ce sont deux objets
qui n'existent pas dans le port.

### 7. CE QUI EST FAIT, CE QUI NE L'EST PAS

* **Fait** : l'acolyte 1 de Gill regarde ; les acolytes 0, 2 et 3 jouent de nouveau leurs
  scripts 11, 5 et 6 ; les 155 images retrouvees par la regle des durees restent en place ;
  l'objet d'Elena 2 se pose sur le joueur ; les onze sprites reactifs restent au choix.
* **Pas fait** : les deux guetteurs de Yun et Yang (id 127). Ils demandent une creation
  conditionnee par le personnage des combattants, donc des objets qui n'existent pas toujours
  -- ce que le rang fixe du port interdit, comme pour l'id 100.
* **Ecarte, avec preuve** : le sprite qui se brise au contact. Aucune routine d'acteur des deux
  jeux ne lit un combattant par `hit_adrs`.

---

## LE CHIEN D'ORO MANQUAIT A MON BILAN -- DEUX BOGUES DANS `chemins()` (23/09, tard)

Frederic : « *c'est faux, le chien du decor d'Oro doit suivre des yeux Oro ou Elena ou
Ibuki* ». Il a raison, et le chien est **deja porte** depuis des semaines
(`decor_objets.c`, `regard_du_chien`). C'est mon RELEVE qui l'avait perdu, et il l'avait
perdu pour deux raisons precises, toutes deux dans `dependances.chemins()`.

### BOGUE 1 : `any(o for o in champs)` est faux quand le seul champ est 0

L'ancienne version rassemblait les offsets des litteraux tombant dans `plw`, puis ecrivait

    if indexe or any(o for o in champs):

Le chien charge **la base** de `plw` (`0x8C645590`, litteral en `0x8C0333EC`) et rien
d'autre : `champs == {0}`. `any({0})` vaut **False**. Le seul acteur de 2nd Impact qui suit
un combattant des yeux en dehors de Gill tombait donc dans le trou d'un `any` sur un
ensemble qui contient zero.

### BOGUE 2 : le cote ne se prend pas toujours par multiplication

L'ancienne version n'acceptait un litteral de `plw` que si la routine indexait par
`muls.w`/`mul.l` avec la taille d'un combattant. Le chien **ajoute** :

    8C033392  mov.w 0x8c0333c0,r4       r4 = 040C = 1036, sizeof(plw)
    8C033396  mov #84,r0
    8C033398  add r4,r2                 r2 = plw + 1036 : LE DEUXIEME COMBATTANT
    8C03339A  mov.w @(r0,r2),r3         r3 = plw[1].position_x

Aucun `muls.w`. `indexe` restait faux.

### ET CE QUI MANQUAIT VRAIMENT : RESOUDRE LE CHAMP

Un litteral sur la base de `plw` ne dit rien tant qu'on ne sait pas quel champ il sert.
`chemins()` propage maintenant le registre avec `par_pointeur.lectures()` : le chien donne
`+84 position_x`, l'acolyte de Gill `+102`. **C'est la resolution du champ, pas la portee,
qui manquait.** J'ai aussi ecrit `appelees()`, qui suit `bsr` et `jsr @rn` -- mais il reste
a **profondeur 0** par defaut : a profondeur 1, New Generation passe de 7 acteurs lisant la
position d'un combattant a 22, une aide partagee contaminant tout un voisinage. Trop large
est aussi faux que trop etroit.

### LE CHIEN, LU DANS LE BINAIRE

`0x8C03334A` rend 1, 3 ou 5 -- gauche, face, droite :

    8C033350  mov.w @(2,r5),r0          r0 = objet[+54], l'humeur du joueur 2
    8C033352  mov.w @r5,r3              r3 = objet[+52], l'humeur du joueur 1
    8C033356  cmp/eq r0,r3              A EGALITE, la camera :
    8C03335E  mov.w @(26,r4),r0             r4 = 0x8C6AF3E8, bg_w ; seuils 544 et 624
    8C03337C  cmp/gt r0,r2              SINON le combattant de plus grande humeur
    8C033382  mov.w @(r0,r5),r3         plw[cote].position_x
    8C033384  cmp/ge 448,r3             < 448  -> 1  (il regarde a gauche)
    8C03338A  cmp/ge 624,r3             < 624  -> 3  (de face)
    8C0333B4  mov #5,r0                 sinon  -> 5  (a droite)

Les trois seuils sont dans le tas juste apres : `0x8C0333BA` = 624, `0x8C0333BC` = 544,
`0x8C0333BE` = 448. **Ce sont exactement les constantes de `regard_du_chien` dans
`decor_objets.c`.** Le port est fidele ; il l'etait avant ce releve.

Le chien existe dans LES DEUX jeux : 2nd Impact **id 71** (`0x8C0332CC`, bande 10, fiche
`bg0a` etage 31, x 608) et New Generation **id 77** (`0x8C0A9B44`, bande 16, fiche `ng10`
etage 53). Le chargeur de NG (`0x8C0A9F60`) lit `plw[0][+820]` et `plw[0][+1804]` -- les
personnages des deux joueurs -- et range leurs humeurs, prises dans la table
`0x8C1B2B08`, en `objet[+52]` et `objet[+54]`. C'est `humeur_du_decor` du port, au mot pres.

### LE BILAN REFAIT : QUI SUIT LES COMBATTANTS DES YEUX

| jeu | decor | acteur | ce qu'il lit | porte ? |
|---|---|---|---|---|
| 2nd Impact | **Oro** (bande 10, `bg0a` 31) | **id 71**, le chien debout | `+84` par l'humeur | **oui**, comportement 1 |
| 2nd Impact | **Gill** (bande 0, `bg00` 22) | **id 184**, un acolyte sur quatre | `+102` par tranches de 64 | **oui**, comportement 7 |
| New Generation | **Oro** (bande 16, `ng10` 53) | **id 77**, le meme chien | `+84` par l'humeur | **oui**, comportements 1 et 2 |
| New Generation | **Yun 1/2, Yang 1/2** (5, 6, 17, 18) | **id 127** (`0x8C0B2118`) | `+84` par bornes, avec miroir | **non** |

Et les autres lecteurs de position, qui ne regardent pas :

| acteur | decors | ce qu'il en fait |
|---|---|---|
| NG id 85 | Elena 2 | une POSITION -- SUR_COMBATTANT, porte |
| NG id 100 | huit bandes | une hauteur par paliers, puis il CREE un objet |
| NG id 83 | les trois Ibuki | il range le X en `objet[+52]` avec un compte a rebours de 40 |

**LA LECON, ET ELLE EST LA MEME QUE LA VEILLE.** Un releve automatique ne vaut que son
chemin d'acces, et deux fois de suite c'est Frederic qui a vu ce que l'outil taisait : les
acolytes de Gill d'abord, le chien d'Oro ensuite. Le silence d'un outil n'est pas un fait.
Quand il dit « aucun », il faut aller chercher un cas qu'on SAIT vrai et verifier qu'il le
trouve -- ici, le chien etait deja porte, la verification coutait deux minutes, et je ne
l'ai pas faite.

### CE QUI RESTE, ET QUI EST DU MEME GENRE

**`bg08` etage 56 : vingt sprites figes sur l'image 0, et c'est lu, pas devine.** Les
herbes et les cordes du pont sont l'id 122 (`0x8C03CAD8`) : leur etat 1 **n'avance pas le
script** et attend `u16[0x8C6B0AA4] != 0`. Ce mot appartient au pont, l'id 123
(`0x8C03CC98`) : zero a sa naissance, **un quand le pont tombe** et que son `y` passe sous
40 (`0x8C03CD2C`). Le port ne pose jamais ce declencheur : les vingt fiches portent donc
`boucle = 0` et restent sur leur premiere image, pour toujours.

C'est exactement la famille que Frederic avait nommee au depart -- « *des elements du decor
qui se brisent au contact d'une chute* » -- sauf que la chute est celle du PONT, pas d'un
combattant. Et c'est faisable : le port sait deja cacher et montrer (REACTIF), il lui
manque l'etat du pont.

### CE QUE LE PONT EST VRAIMENT, ET LA DECISION DE FREDERIC (23/09, en fin de journee)

Frederic, qui connait le jeu : « *l'animation du pont bg08 se declenche en fin du 1er round
et sert de transition pour afficher le 2eme decor d'Elena pour le 2eme round* ».

Cela recoupe exactement ce que le binaire dit, et lui donne son sens : l'id 123 fait tomber
le pont, son `y` passe sous 40, `u16[0x8C6B0AA4]` passe a un, et les vingt herbes et cordes
de l'id 122 deroulent alors leur script **une seule fois**. Ce n'est donc pas une boucle de
decor : c'est une TRANSITION DE MANCHE.

Trois degres, et ils ne coutent pas la meme chose :

1. **Faire tomber le pont en fin de manche 1.** Faisable sans rien casser. Le declencheur du
   port n'a pas besoin d'imiter le `y` du pont : 3SX connait la fin de manche nativement. Et
   les vingt fiches existent deja, figees sur leur image 0 -- il suffit de les laisser
   derouler. C'est REACTIF avec l'interrupteur dans l'autre sens : le rang ne bouge pas.
2. **S'arreter la**, donc une transition qui ne mene nulle part, le decor de la manche 1
   restant en place.
3. **L'enchainement reel, decor 1 -> decor 2 a la manche 2.** Les deux bandes d'Elena sont
   deux etages 3SX distincts, avec leurs pages de tuiles et leurs palettes, charges une fois
   a l'entree du combat. Il faudrait que le chargeur d'etage sache RECHARGER en cours de
   match. 3rd Strike n'a aucun etage qui change de manche en manche ; rien ne dit que le port
   ait une porte pour ca, et je ne l'ai pas encore cherchee.

**DECISION DE FREDERIC : le point 3 est remis a plus tard, et d'ici la ON NE DECLENCHE PAS
le pont ni les cordes.** Les vingt fiches de `bg08` etage 56 restent donc `boucle = 0`,
figees sur leur image 0 -- non par ignorance, mais parce qu'une transition qui ne mene nulle
part serait pire que l'immobilite. `decor_objets.c` n'est pas touche.

A reprendre dans l'ordre le jour ou on y revient : d'abord chercher si 3SX peut recharger un
etage en cours de match ; si oui, le point 1 et le point 3 se font ensemble ; si non, on
rediscute du point 2.

---

## ETAT AU SOIR DU 23/09 : LES CINQ QUESTIONS DE FREDERIC, ET CE QUI RESTE

Le prompt de reprise complet est dans `REPRISE-2026-09-23.md`, aux deux endroits. Cette
section-ci est le resume qui fait foi.

### LES CINQ QUESTIONS, REPONDUES SANS ARRANGEMENT

**1. Les nouvelles informations sur les positions des decors ont-elles ete appliquees ?**
**Non, et il n'y avait rien a appliquer.** La lecture du rastériseur de NG de bout en bout a
CONFIRME la formule deja en place (`x*16 - ((defilement x + 1) & 0x3FF)`, idem en y avec
+20, quatre passes a ±1024, coupe a 384x224) et TUE l'hypothese `1024x512` / `&0x1FF`. Le
`+1` et le `+20` sont des constantes de camera, les memes pour tous les decors : ils ne
peuvent pas expliquer les 80 de Gill. **L'origine du decalage vertical de Gill reste
inconnue**, la piste `0x8C4DDBA4` ayant ete rejetee (elle donne bien -80 pour Gill mais
exige des corrections non nulles sur des etages valides). Les 28 lignes de Sean sont
peut-etre la meme mecanique. **Ouvert depuis le 17/09.**

**2. Les animations des elements qui se brisent au contact d'une chute sont-elles
appliquees ?** **Non**, et la famille que j'avais annoncee n'existait pas : l'id 13 de 2I et
l'id 19 de NG etaient un faux positif de `par_pointeur.py`, qui lisait `mov.l @(16,r15),r4`
-- une relecture de PILE -- comme un acces par `hit_adrs`. Outil corrige, releve refait :
**aucune routine d'acteur des deux jeux ne lit un combattant par `hit_adrs`.** Le seul objet
de cette forme est le pont d'Elena (`bg08` etage 56, vingt sprites), que Frederic a demande
de **ne pas declencher** tant que l'enchainement de ses deux decors n'est pas regle.

**3. Existe-t-il d'autres animations qui se declenchent sous condition ?** **Oui**, sept
familles, dont quatre sont portees. Le tableau complet est en §2.3 de
`REPRISE-2026-09-23.md`. Ce qui n'est pas porte : l'id 127 (Yun et Yang, conditionne au
personnage choisi), l'id 100 (il CREE un objet), l'id 88 (quatre variables globales que je
n'ai pas su nommer), et le pont d'Elena. **Et une zone non lue que je signale plutot que de
la taire : 2I id 68 (`0x8C032970`, Dudley) et NG id 74 (`0x8C0A9484`) lisent `+38 son etat`
et `+468`.** C'est le premier endroit a ouvrir pour completer la liste.

**4. Les timings des animations classiques ont-ils ete verifies ?** **La regle l'est, le
resultat ne l'est pas.** Le format est lu (premier u16 = `commande | duree<<8` ; duree non
nulle = IMAGE), les opcodes de boucle et le saut arriere sont decodes, et la correction a
rendu 88 images en 2I et 67 en NG. Mais **aucune animation n'a ete comparee image par image
avec le jeu**. Et l'**etage 25 (`bg03`) est le plus remue** : `a25o7` 12 -> 36 images,
`a25o8` 12 -> 31, `a25o13` 13 -> 1. Il peut etre abime plutot qu'ameliore. **Le verdict de
Frederic sur l'image est necessaire avant d'aller plus loin.**

**5. Le zoom de la caleche de Dudley, et la lenteur de chargement de ce decor ?** **Jamais
regarde.** Deux mesures sont neanmoins tombees, et elles ecartent les deux causes les plus
evidentes :

* **Le port n'a aucune echelle par objet.** La fiche porte une `famille` (la matrice, donc
  le defilement) et un `z` (l'ordre de dessin), rien qui redimensionne. Un zoom demande
  autre chose que ce que `decor_objets.c` sait faire.
* **La lenteur ne vient ni de nos objets ni de nos pages.** Dudley en 2I est `bg04`, etage
  26 : **5 objets, 589 tuiles, budget de motifs 16 sur 128, 64 pages pour 4,3 Mo** -- un des
  plus legers du lot, contre 78 pour Oro et 128 pages pour Gill. La cause est ailleurs :
  l'archive d'etage, le travail de palette, ou la mise en place des plans. **C'est un point
  de depart, pas une reponse**, et il faut d'abord savoir si Frederic parle de Dudley en 2nd
  Impact ou de sa bande dans New Generation.

### CE QUI RESTE, PAR ORDRE

1. **Le verdict de Frederic** sur l'etage 25 et sur les onze sprites reactifs (choix 2 du
   lanceur). Rien ne doit avancer avant : les deux peuvent demander un retour en arriere.
2. L'origine du decalage vertical de Gill, puis les 28 lignes de Sean.
3. 2I id 68 et NG id 74 : les deux conditionnels non lus.
4. Le rechargement d'etage en cours de match -- s'il existe, le pont d'Elena et
   l'enchainement de ses deux decors deviennent faisables ensemble.
5. La caleche de Dudley : d'abord savoir de quel decor on parle, et si la caleche est un
   objet ou un plan.
6. Les quatre variables globales de l'id 88 : tant qu'elles ne sont pas nommees, ne rien
   implementer.
7. L'id 127 et l'id 100, qui butent tous deux sur le RANG FIXE du port : un objet ne peut ni
   naitre ni disparaitre en cours de partie, son rang entrant dans la cle du cache de
   motifs, dans l'emplacement de sa palette et dans l'ordre de dessin. C'est un changement
   d'architecture du module, pas une correction d'animation.

### LA LECON DE LA JOURNEE, ET ELLE A COUTE DEUX FOIS

**Le silence d'un outil n'est pas un fait.** Deux fois de suite, c'est Frederic qui a vu ce
que le releve taisait : les acolytes de Gill d'abord, le chien d'Oro ensuite. Dans les deux
cas l'outil disait « aucun », et dans les deux cas il suffisait de prendre un cas que je
SAVAIS vrai -- le chien etait deja porte -- pour voir que l'outil ne le retrouvait pas. La
verification coutait deux minutes. **Quand un releve automatique dit « aucun », il faut
l'eprouver sur un cas connu avant d'en annoncer le resultat.**

---

## DUDLEY : LA LENTEUR EST TROUVEE, LE ZOOM NE L'EST PAS (23/09, tard)

Cinquieme question de Frederic : « *le zoom de la caleche de Dudley est reproductible ? Ce
decor se charge tres lentement, quelle en est l'origine ?* »

### 1. QUEL DECOR -- IL Y EN A TROIS

| jeu | decor | bande | etage 3SX | fiche |
|---|---|---|---|---|
| 2nd Impact | Dudley | 4 | **26** | `bg04` |
| New Generation | Londres, manche 1 | 7 | **44** | `ng07` |
| New Generation | Londres, manche 2 | 8 | **45** | `ng08` |

**C'est l'etage 44 qui est lent, et lui seul.** Les deux manches du meme personnage donnent
la mesure sans rien supposer : la manche 2 est un etage ORDINAIRE.

### 2. LA LENTEUR : 320 PAGES CONTRE 64, ET LA CAUSE EST NOMMEE DANS LES DONNEES

Les pages d'un etage ajoute vivent dans `resources/tex_remix/stage<N>/<liste>-<page>.tex`,
64 Ko chacune. En les comptant par liste :

| etage | listes | pages | poids |
|---|---|---|---|
| **44 Londres 1** | 132 x32, 196 x32, **260 x32**, **292 x224** | **320** | **20,0 Mo** |
| 37 Gill NG | 132 x32, 196 x32, 228 x96 | 160 | 10,0 Mo |
| 22 Gill 2I | — | 128 | 8,0 Mo |
| **45 Londres 2** | 132 x32, 196 x32 | **64** | **4,0 Mo** |

Un etage ordinaire, c'est **deux listes de 32 pages = 64**. Londres 1 en a trois, **plus une
liste animee de 224 pages**. Et cette liste est ecrite noir sur blanc dans
`etagesng_pages.inc` :

    /* la pluie de Londres (id 11) : quatre cartes, deux copies */
    static const s16 ng_plan_anime_44_2[] = { ... };
    #define ETAGESNG_PLANS_ANIMES \
        [37] = { { 0, 4, 0, ng_plan_anime_37_0 } }, \
        [44] = { { 2, 8, 0, ng_plan_anime_44_2 } }

**Huit vues** pour le plan 2 de Londres, chaque vue etant un jeu complet de 32 pages de
reecriture : la base plus sept vues de plus = **224 pages**. Gill, avec ses quatre vues
(96 pages de plan anime), donne 160 au total. **Le modele colle exactement sur les deux.**

`tex_remix.c` connaissait deja le symptome et en avait retire un cout le 22/09 (l'empreinte
n'est plus calculee page par page quand l'etage retrouve les siennes par numero). Ce qui
reste est intrinseque : **320 lectures, 320 decodages et 320 televersements a chaque entree
dans le decor**, puisque `Bg_Close` rend les poignees d'un etage avant d'en charger un
autre. La reserve du pool vaut d'ailleurs `2 x le plus gros dossier`, et le plus gros
dossier, c'est celui-la.

Mesure de la seule lecture disque, cache chaud :

    stage45   64 fichiers   4,0 Mo    45 ms
    stage22  128 fichiers   8,0 Mo   126 ms
    stage37  160 fichiers  10,0 Mo   119 ms
    stage44  320 fichiers  20,0 Mo   172 ms

**La lecture seule ne suffit pas a expliquer « tres lentement » : le gros du temps est dans
le decodage et le televersement des 320 pages**, pas dans le disque. C'est la quantite de
pages qui compte, pas les octets.

### 3. ET 45 % DE CES PAGES SONT DES DOUBLONS OCTET POUR OCTET

En comparant les empreintes MD5 du contenu :

| liste | pages | distinctes | doublons |
|---|---|---|---|
| 132 | 32 | 24 | 8 |
| 196 | 32 | 17 | 15 |
| 260 | 32 | 18 | 14 |
| **292 (la pluie)** | **224** | **119** | **105** |
| **tout l'etage** | **320** | **177** | **143 (45 %)** |

Un groupe compte **vingt-quatre copies identiques**. Les sept blocs de 32 pages de la pluie
sont bien distincts PRIS COMME BLOCS -- aucune vue n'est la copie d'une autre -- mais **page
par page**, la pluie ne couvre qu'une partie de chaque page et tout ce qu'elle ne touche pas
se repete d'une vue a l'autre.

**Et ce n'est pas propre a Dudley** : 64 % de doublons a l'etage 37 (Gill NG), 61 % a
l'etage 22, 38 % a l'etage 45. Sur les **255,6 Mo** des quarante etages, il y a la un
gisement.

**Le gain chiffre d'une deduplication par contenu : l'etage 44 passerait de 320 pages /
20,0 Mo a 177 pages / 11,1 Mo**, soit 45 % de lectures, de decodages et de televersements en
moins a chaque entree. Il faudrait que l'exportateur ecrive une page par contenu distinct
plus un index `page -> fichier`, et que `TexRemix_Substitute` consulte cet index. **Ce n'est
pas fait : ca touche le chargeur, qui marche. A demander avant.**

### 4. LE ZOOM : TROIS MESURES QUI ECARTENT LES EXPLICATIONS SIMPLES

**Aucun objet de Dudley ne grandit.** Le plus gros objet anime de Londres 1 est `n07o13`
(id 65, chargeur `0x8C0A8BCC`, en 416,64) : **huit images, 342 tuiles, grille 9x7**. Mesure
de l'etendue de chaque image :

    image 0 : 42 tuiles, 144 x 112 px      image 4 : 42 tuiles, 144 x 112 px
    image 1 : 43 tuiles, 144 x 112 px      image 5 : 43 tuiles, 144 x 112 px
    image 2 : 43 tuiles, 144 x 112 px      image 6 : 43 tuiles, 144 x 112 px
    image 3 : 43 tuiles, 144 x 112 px      image 7 : 43 tuiles, 144 x 112 px

**Huit images de taille rigoureusement identique : c'est un cycle, pas un zoom.** Les objets
de Dudley en 2nd Impact disent la meme chose (`a26o2` : dix images toutes en 80x96 ;
`a26o1` : 64x64 et 64x80 en alternance, une respiration, pas une croissance).

**La routine de l'id 65 ne met aucune echelle** : sur tout son intervalle
(`0x8C0A7814`..`0x8C0A7B08`), **zero instruction FPU et zero multiplication entiere**. Elle
ne peut pas redimensionner quoi que ce soit.

**Le rastériseur de plans de NG n'a pas d'echelle non plus** : lu de bout en bout le 23/09,
il fait `ecran x = x * 16 - ((defilement x + 1) & 0x3FF)`, quatre passes a ±1024, et le
constructeur de quads `0x8C10F8A2` se contente de couper a 384x224.

**Et le port n'a aucune echelle par objet** : une fiche porte une `famille` (la matrice, donc
le defilement) et un `z` (l'ordre de dessin), rien qui redimensionne.

**Donc : le zoom n'est ni dans les images, ni dans la routine de l'objet, ni dans le
rastériseur de plans.** Il reste trois endroits possibles, et il faut savoir LEQUEL avant de
chercher : la camera du jeu (3rd Strike zoome deja la vue selon l'ecart des combattants),
un descripteur de scene particulier, ou une mecanique que je n'ai pas encore ouverte.
**Question a Frederic : qu'est-ce qui grossit exactement -- la caleche seule, ou tout le
decor avec elle ?** La reponse designe l'endroit.

---

## LES PAGES EN DOUBLE, RETIREES -- ET LA CALECHE, QUE J'AVAIS DEJA LUE (23/09, tard)

### 1. LA CALECHE : C'ETAIT DANS CE DOCUMENT, ECRIT PAR MOI LE 22/09

Frederic : « *pour la caleche, c'est toi qui m'a signale une reduction de taille de la
caleche* ». Il a raison, et c'est ecrit plus haut dans ce meme fichier :

> « la caleche de Dudley 1 (id 65) : 600 trames sous le tunnel, 196 trames a -1,125 pixel,
> puis -1 pixel jusqu'a passer sous x 48, et tout recommence. Le jeu la **retrecit** en
> chemin (`+0x238`/`+0x23A`) : notre moteur ne met pas un objet a l'echelle, elle garde sa
> taille. »

et, dans « Ce qui reste ouvert » : « *Dudley 1 : le retrecissement de la caleche (...) et
les 143 pages en double au chargement* ». **Les deux moities de la cinquieme question
etaient deja dans le dossier, avec le meme chiffre de 143.** Je ne les ai pas retrouvees en
repondant, et j'ai repondu « jamais regarde ». C'est la meme faute que la veille, dans
l'autre sens : hier je faisais confiance au silence d'un outil, aujourd'hui j'ai ignore ce
que mon propre dossier disait.

**La loi, maintenant lue au mot pres** (`0x8C0A8970`, et son jumeau `0x8C0A7814` pour un
autre objet de Londres -- les deux chargent la constante 570) :

    8C0A89C8  mov #64,r3                 le y de naissance
    8C0A89CA  mov #55,r4                 L'ECHELLE DE DEPART
    8C0A89F6  mov.w 0x8c0a8a60,r0        r0 = 570
    8C0A89F8  mov.w r4,@(r0,r14)         objet[+570] = 55
    8C0A89FA  add #-2,r0
    8C0A89FE  mov.w r4,@(r0,r14)         objet[+568] = 55   -- les deux partent ensemble

    8C0A8B08  mov.w @r3,r0 ; and #7,r0 ; mov.w r0,@r3      un compteur modulo 8
    8C0A8B14  cmp/eq #7,r0                                  une fois sur huit,
    8C0A8B1A  mov.w @(r0,r14),r2   (r0 = 570)
    8C0A8B1C  tst r2,r2 ; bt                                si deja zero, on s'arrete
    8C0A8B22  add #-1,r2 ; mov.w r2,@(r0,r14)               +570 -= 1
    8C0A8B26  add #-2,r0
    8C0A8B2A  add #-1,r3 ; mov.w r3,@(r0,r14)               +568 -= 1

**`+568` et `+570` partent tous deux de 55 et perdent 1 toutes les huit trames, jusqu'a
zero.** La caleche retrecit donc d'un cinquante-cinquieme par huit trames sur 440 trames.

**Et une inquietude levee au passage.** Le spawner de la caleche ecrit `+8 = 65`
(`0x8C0A8BF6`) mais vit dans l'intervalle de l'id 71 : j'ai craint que la table d'acteurs de
NG soit decalee, ce qui aurait invalide toutes les attributions de la journee. **Elle ne
l'est pas** : `ac[65]` (`0x8C0A7814`) charge la constante 570 en quatre endroits, `ac[71]`
en deux. Londres a simplement PLUSIEURS objets qui retrecissent, et le spawner d'un acteur
est pose dans l'intervalle du suivant, comme en 2nd Impact. Rien a refaire.

**Ce qu'il faudrait pour le porter** : `mlt_obj_matrix` sait mettre un objet a l'echelle ; il
manque le pivot dans `DecorObjets_Position` et le passage de l'echelle dans la fiche. **Non
fait.**

### 2. LA DEDUPLICATION : FAITE, VERIFIEE, REVERSIBLE

Demandee par Frederic. Le releve, sur les trente-huit dossiers d'etage :

    3488 pages   210,1 Mo   ->   2021 pages   118,3 Mo      44 % de moins
    1467 pages sur 3488 etaient des doublons OCTET POUR OCTET

Tous les etages en profitent, pas seulement Dudley : 88 doublons a l'etage 56, 103 a
l'etage 37, 78 a l'etage 22, 42 a l'etage 51. **Dudley 1 passe de 320 pages / 20,0 Mo a
177 / 11,1 Mo.** Sur les dix-neuf etages de New Generation, 1888 pages avant, 1046 apres.

**L'outil** : `outils/pages_doublons.py`, trois modes -- `--releve` (ne touche rien),
`--appliquer`, `--annuler`. Il garde un fichier par contenu distinct, efface les copies, et
ecrit a cote un `doublons.txt` :

    de_liste de_page vers_liste vers_page

**L'index est ecrit AVANT le premier effacement** : si l'ecriture echoue, rien n'est perdu.
Et `--annuler` recopie les canoniques sous les noms effaces, ce qui remet l'etage a
l'identique -- le contenu efface etant, par construction, le meme au bit pres.

**Le chargeur** : `tex_remix.c` lit `doublons.txt` **une fois par etage, et seulement quand
le chemin direct manque**. Un etage non deduplique ne paie rien ; une installation qui garde
ses doublons se comporte exactement comme avant. C'est ce qui rend le changement sans
risque.

**LA VERIFICATION, faite avant de livrer.** Les empreintes MD5 des 3488 pages ont ete
relevees avant l'operation, puis chaque nom d'origine a ete recherche apres -- soit comme
fichier, soit par l'index :

    introuvables       : 0
    contenu different  : 0

**Chaque page d'origine se retrouve, octet pour octet.**

**Le lanceur efface les anciennes copies du cote de l'installation.** `robocopy` n'efface
rien tout seul : sans cela, les doublons deja installes dans `%APPDATA%` seraient trouves
AVANT l'index et la deduplication ne se verrait pas. Le lanceur lit donc chaque
`doublons.txt` et retire une par une les pages qui y sont nommees -- et rien d'autre. Il ne
touche que les etages 37 a 55, ceux qu'il deploie deja : **les etages de 2nd Impact, valides
par Frederic, ne sont pas touches.**

Livre : `LES PAGES EN DOUBLE - Dudley allege.cmd`, exe `build/3sx-doublons.exe`.
Sauvegarde du chargeur : `tex_remix.c.avant-doublons`.

---

## L'ECHELLE DE LA CALECHE, PORTEE -- LE PORT SAVAIT DEJA LE FAIRE (23/09, tard)

### 1. LE NEUTRE EST 63, DES DEUX COTES

`mlt_obj_matrix`, dans `mtrans.c`, porte depuis toujours :

    if (wk->my_mr_flag) {
        njScale(NULL, (1.0f / 64.0f) * (wk->my_mr.size.x + 1),
                      (1.0f / 64.0f) * (wk->my_mr.size.y + 1), 1.0f);
    }

**Le neutre est donc 63** : `(63 + 1) / 64 = 1,0`. Et le code de dessin du Dreamcast fait,
sur le meme champ, `add #-63,r2` (`0x8C032F28`) avant d'indexer ses tables. **Meme champ,
meme unite, meme neutre.** Il ne manquait rien au port : il manquait de s'en servir.

C'est ce qui m'avait echappe quand j'ai repondu « le port n'a aucune echelle par objet ».
La phrase etait vraie de `decor_objets.c` et fausse du moteur qui le dessine.

### 2. LA LOI, RELUE AU MOT PRES

    8C0A89CA  mov #55,r4                    L'ECHELLE DE DEPART
    8C0A89DE  mov.l 0x8c0a8a6c,r3           r3 = FFFEE000 = -73728 = -1,125 pixel en 16.16
    8C0A89F8  mov.w r4,@(r0,r14)  (r0=570)  objet[+570] = 55
    8C0A89FE  mov.w r4,@(r0,r14)  (r0=568)  objet[+568] = 55

    -- etat 0 : 600 trames immobile, sous le tunnel (objet[+52] compte a rebours)
    -- etat 1 : 196 trames a -1,125 pixel ; la sortie pose +124 = FFFF0000, soit -1 pixel
    -- etat 2 : il roule, et LUI SEUL retrecit :

    8C0A8AC8  r3 = objet[+102] ; cmp/ge 48  X >= 48 ?
    8C0A8AD8  objet[+36] = 0                NON -> routine_no[0] = 0, TOUT RECOMMENCE
    8C0A8AFC  objet[+52] += 1
    8C0A8B0A  and #7,r0                     le compteur va de 0 a 7
    8C0A8B14  cmp/eq #7,r0                  une fois toutes les HUIT trames
    8C0A8B22  objet[+570] -= 1              ... et on s'arrete a zero
    8C0A8B2A  objet[+568] -= 1

**Correction a la note du 22/09** : j'y avais ecrit « un cran toutes les sept trames ». Le
compteur va de 0 a 7 : il y a **huit** trames par cran. Et le « 55/64 au depart » melait
deux choses -- 55 est l'echelle, 64 est le `y` de naissance (`mov #64,r3` juste avant).

**Le compte** : l'etat 2 dure 148 trames (de x 195,5 a x 48 a un pixel par trame), soit
**18 crans**. L'echelle va donc de 55 a 37, c'est-a-dire de **56/64 = 87,5 %** a
**38/64 = 59 %**. Ce n'est pas une disparition : c'est la perspective d'une caleche qui
remonte la rue.

### 3. CE QUI A ETE POSE DANS LE PORT

| ou | quoi |
|---|---|
| `decor_objets.h` | trois champs au bout de `DecorAnimation` : `echelle` (0 = aucune), `echelle_pas` (trames par cran), `echelle_seg` (le segment de trajet ou elle decroit, -1 = tous) |
| `decor_objets.c` | `nos[k].echelle` et `nos[k].echelle_trame` ; `avancer_echelle(k)` appelee a chaque trame ; `DecorObjets_Echelle(work, &taille)` |
| `eff05.c` | pose `my_mr_flag` et `my_mr.size` quand l'objet retrecit, **et les efface sinon** -- le `WORK` vient du tas d'effets et il est recycle |
| `objetsng.py` | la fiche de la caleche recoit `echelle=55, echelle_pas=8, echelle_seg=2` |
| `animerng.py` | l'emetteur ecrit les quatre champs, en remplissant les neutres de ce qui les precede : une initialisation positionnelle l'exige |

### 3 bis. UN PIEGE QUE LA CALECHE A TENDU : ELLE EST SERVIE EN DEUX MORCEAUX

Elle fait **dix colonnes**, et le cache n'en prend que soixante-quatre cases : `morceaux_objet`
la sert donc en deux fiches voisines, neuf colonnes en x 928 et une en x 1072. Or `njScale`
agit **autour du point ou `njTranslate` vient de poser l'objet**. Mis a l'echelle chacun
autour du sien, les deux morceaux se seraient ecartes de `(1 - echelle) x 144`, soit
**58 pixels** au plus petit : la caleche coupee en deux, avec un trou au milieu.

D'ou un quatrieme champ, `echelle_ecart` -- l'ecart de ce morceau au premier du groupe,
`col0 * 16` -- et, dans `DecorObjets_Position` :

    *x -= ((63 - nos[k].echelle) * a->echelle_ecart) / 64;

Le premier morceau porte zero et ne bouge pas ; le second suit exactement le bord droit du
premier. A l'echelle de naissance (56/64), le decalage vaut 18 pixels, et c'est bien la
difference entre 1072 et `928 + 0,875 x 144 = 1054`. Un objet d'un seul morceau porte zero
et n'est pas concerne.

**Le trajet, lui, etait deja la** : `comportement=5` et
`[(600, 0, 0, -1), (196, -288, 0, -1), (148, -256, 0, -1)]`, pose lors d'une session
precedente, et les 148 trames que je viens de recalculer tombent sur la meme valeur. Il ne
manquait que l'echelle.

**`echelle_seg = 2`** rend fidelement le fait que le Dreamcast ne compte ses crans que dans
l'etat 2 : sous le tunnel et au demarrage, la caleche garde sa taille. Et la boucle du
trajet remet l'echelle de naissance, comme le fait la remise a zero de `routine_no[0]`
quand la caleche passe sous x 48.

### 4. CE QUE CA OUVRE

Le champ est generique : **tout objet de decor peut maintenant etre mis a l'echelle**, et
plusieurs en ont besoin. Les deux routines de Londres chargent la constante 570 -- `ac[65]`
en quatre endroits, `ac[71]` en deux -- et le releve du 23/09 a trouve la meme constante
dans une trentaine de routines des deux jeux. Aucune n'est portee : seule la caleche l'est,
parce que sa loi est lue.

---

## CE QUI SE BRISE AU CONTACT D'UNE CHUTE : CINQ CHEMINS SUIVIS CHEZ HUGO, YUN ET YANG (23/09, tard)

Frederic : « *recherche dans les decors d'Hugo, Yun et Yang (il y a peut-etre d'autres
decors concernes, a verifier a posteriori)* ».

**LE CRIBLE A ETE EPROUVE AVANT D'ETRE CRU**, cette fois. `ruptures.py` cherche la figure du
pont d'Elena -- un mot de RAM qu'un acteur ECRIT et qu'un autre LIT -- et, lance sur la
bande 8, il retrouve tout seul :

    bande  8 Elena      8 acteurs
       8C6B0AA4  ecrit par id 123, lu par id 122

C'est exactement le mecanisme connu. Le crible fonctionne.

### LES CINQ CHEMINS, ET LEUR RESULTAT

| chemin | ce qu'il attraperait | Hugo, Yun, Yang |
|---|---|---|
| 1. un mot de RAM ecrit par un acteur, lu par un autre (`ruptures.py`) | le pont d'Elena, retrouve | **rien**, dans les deux jeux |
| 2. un acteur qui lit un combattant (`dependances.py`, champs resolus) | le chien d'Oro, l'acolyte de Gill | **rien** -- seulement `+856`/`+820`, le PERSONNAGE choisi |
| 3. **la routine d'ETAGE** qui lit un combattant (jamais teste jusqu'ici) | une rupture pilotee par l'etage | **rien** : Yun et Yang lisent `plw+0` et `+856`, c'est-a-dire les « amis du decor » |
| 4. un opcode de script inconnu | une rupture pilotee par le script | **rien** : Hugo et Yang n'emploient que `0x01`, `0x0C`, `0x0D` ; Yun ajoute `0x02` |
| 5. un acteur qui ECRIT chez un autre objet, par `+12` ou `+812` | une rupture sans mot global | **rien**, dans les deux jeux |

**Le chemin 3 etait un trou reel de mon releve** : je n'avais jamais applique `chemins()`
aux dix-sept routines d'etage, seulement aux acteurs. Il est comble, et il ne donne rien de
plus -- mais il a fallu le combler pour pouvoir le dire.

**L'opcode `0x02`, seule inconnue, n'est pas une rupture.** Son gestionnaire est
`0x8C0B530C` (table des commandes `0x8C1C5BC8`, entree 2) :

    8C0B530E  r0 = u16[script + 6]      le troisieme mot de l'enregistrement
    8C0B5316  add #-2,r0
    8C0B531A  muls.w r3,r0              r3 = le pas
    8C0B531E  u16[objet + index] = macl

C'est un **saut absolu** -- `index = pas x (mot3 - 2)` -- le frere de `0x32`, qui saute en
arriere. Il est maintenant nomme.

### L'HISTOGRAMME DES OPCODES, PAR DECOR

Il n'existait pas ; il servira ailleurs. En 2nd Impact :

    Gill     13 scripts  {01:13, 32:2}
    Ryu      24 scripts  {01:24, 0C:5, 0D:5}
    Yun      45 scripts  {01:45, 02:2, 0C:3, 0D:3}
    Dudley   11 scripts  {01:11, 29:11}          <- la caleche et les punks se deplacent
    Necro    39 scripts  {01:39, 0C:3, 0D:3, 2B:6}
    Hugo     37 scripts  {01:37, 0C:8, 0D:8}
    Elena    32 scripts  {01:32, 2B:1}
    Elena 1  53 scripts  {01:53, 02:1, 0C:10, 0D:10}
    Oro      93 scripts  {01:93, 02:3, 0C:4, 0D:4}
    Yang      6 scripts  {01:5, 0C:4, 0D:4}
    Sean     58 scripts  {01:58, 02:6, 0C:5, 0D:5, 28:2, 29:18, 2A:149, 2B:5, 32:13}
    Hugo bis 37 scripts  {01:37, 0C:8, 0D:8}

**Sean est de loin le plus riche** -- 149 deplacements en y, treize sauts arriere -- et
Necro est le seul, avec Sean et Elena, a appeler des effets (`0x2B`). New Generation donne
la meme image ; son decor 12 porte un `0x03` isole, seul opcode encore sans nom des deux
jeux.

### CE QUE JE NE SAIS PAS, ET LA QUESTION A POSER

**Aucun des cinq chemins ne trouve de rupture chez Hugo, Yun ni Yang.** Mais la lecon du
jour interdit d'en conclure qu'il n'y en a pas : deux fois aujourd'hui, le silence d'un
outil etait le silence de l'outil, pas celui du jeu.

Ce que les cinq chemins ne couvriraient PAS, et qu'il faudra ouvrir si Frederic confirme :

* une rupture qui vient du **systeme d'effets des combattants** et non du decor -- le jeu
  ferait naitre les debris depuis le code du personnage, en consultant l'etage ; rien de
  cela ne passerait par une routine de decor ;
* un objet **que le port ne pose meme pas**. Yang n'en pose que 5 sur 18, Yun 14 sur 22,
  Hugo 9 sur 13 : si l'element qui se brise est dans le reste, il n'est ni dans mes fiches
  ni dans ma liste d'acteurs ;
* une rupture qui n'est qu'un **changement de script** decide a la naissance selon une
  variable de partie, comme l'id 88 dont les quatre variables restent sans nom.

**La question a poser a Frederic** : dans quel decor exactement, et **qu'est-ce qui se
brise** -- un objet identifiable (une caisse, une enseigne, une vitre), et sous quel coup ?
La reponse designe le chemin ; sans elle, je cherche a l'aveugle dans les cinq.

### VALIDE PAR FREDERIC : LA CALECHE (23/09, au soir)

> « *caleche validee pour le decor de Dudley* »

L'echelle est donc juste **a l'image**, et avec elle trois choses qui ne l'etaient que sur
le papier :

* la **loi** -- depart a 56/64, un cran toutes les HUIT trames, et seulement pendant qu'elle
  roule ;
* le **recollage des deux morceaux** (`echelle_ecart`) : aucune fente n'a ete signalee, donc
  la correction `x -= (63 - taille) * ecart / 64` tombe juste ;
* et, par ricochet, **la deduplication des pages** : Frederic a vu ce decor, qui est
  justement celui qui passe de 320 pages a 177 par l'index `doublons.txt`. Rien n'y manque.

Le champ `echelle` est generique et n'attend plus que des lois lues : une trentaine de
routines des deux jeux chargent la meme constante 570.

---

## LE TONNEAU DE HUGO : CE QUI SE BRISE AU CONTACT D'UNE CHUTE, LU DE BOUT EN BOUT (23/09, au soir)

Frederic : « *dans le decor d'Hugo, le tonneau a l'extremite droite du decor se brise* ».
Une phrase, et tout tombe.

### 1. L'OBJET

L'objet le plus a droite de `bg06` (etage 28) est `a28o0`, en **x 797** (son second morceau
en 845), **vingt-trois images**, grille 3x9 -- et il ne vient pas d'un bloc de donnees comme
les autres : son chargeur est **`0x8C031B56`**, en dur dans la routine de l'**id 63**
(`0x8C031918`..`0x8C031C04`), qui a **sept etats**. Vingt-trois images et sept etats pour un
tonneau : c'est une rupture.

### 2. LE DECLENCHEUR

L'etat 1 de l'id 63 appelle `0x8C0D7D74` et, **des qu'il rend autre chose que zero**, passe
a l'etat 2 et pose le **script 32** :

    8C0319EC  jsr 0x8C0D7D74            r4 = objet, r5 = 0
    8C0319F2  bf 0x8c0319f8             r0 != 0 -> on casse
    8C0319FC  routine_no[0] += 1
    8C031A00  mov #32,r6 ; jsr 0x8C0B4AD4    LE SCRIPT DE RUPTURE

`0x8C0D7D74` est **une aide partagee, posee dans la region des etages** -- hors de
l'intervalle de tout acteur. Elle fait, pour chacun des deux combattants :

    8C0D7DAE  bsr 0x8C0D7DFC(objet, plw[0])
    8C0D7DB2  u16[0x8C6AF288 + type*2] += r0
    8C0D7DC4  bsr 0x8C0D7DFC(objet, plw[1])
    8C0D7DCC  u16[0x8C6AF288 + type*2] += r0
    8C0D7DD4  rend u16[0x8C6AF288 + type*2]

et `0x8C0D7DFC` est **LA CONDITION**, en clair :

    8C0D7E08  r0 = plw[+38]             routine_no[1], L'ETAT DU COMBATTANT
    8C0D7E0A  cmp/eq #1,r0              etat 1 ?
    8C0D7E10  r4 = plw[+40]             routine_no[2], LE SOUS-ETAT
    8C0D7E14  cmp/ge #14,r4             >= 14 ?
    8C0D7E1A  cmp/ge #24,r4             < 24 ?          -> LA CHUTE
    8C0D7E22  r7 = 0x8C1D3ED4 + objet[+4]*8      LA BOITE DE L'OBJET
    8C0D7E2E  r6 = 0x8C1D3F2C + plw[+856]*8      LA BOITE DU PERSONNAGE
    8C0D7E3C  jsr 0x8C0B9ED0            LE RECOUVREMENT
                                        rend 1 si les deux se touchent

**Un combattant dans l'etat 1, sous-etat 14 a 23 -- sa chute -- dont la boite recouvre celle
de l'objet.** C'est mot pour mot ce que Frederic decrivait depuis le debut.

`0x8C0B9ED0` est le test de recouvrement generique : il prend deux `WORK` et deux boites
`{x, largeur, y, hauteur}`, retourne le x selon `rl_flag` (+10), ajoute `+102` et `+106` de
chacun, et compare les deux rectangles.

Les boites sont a la main dans le binaire, **une par type d'objet** :

    type 0 : x -159, larg 48, y 65, haut 93        type 5 : 33, 81, 58, 44
    type 1 : 90, 63, 98, 45                        type 6 : -53, 39, 20, 25
    type 2 : 5, 61, 41, 40                         type 7 : 6, 64, 33, 69
    type 3 : -117, 87, 19, 42                      type 8 : 12, 61, 16, 28
    type 4 : -135, 25, 18, 37                      type 9, 10 : -28, 17, 21, 36

et **une par personnage** (`0x8C1D3F2C`), parce qu'Hugo ne tombe pas comme Ibuki :

    perso 0 : -11, 56, 33, 38     perso 3 : -18, 42, 36, 32
    perso 1 : -11, 56, 35, 53     perso 4 : -24, 48, 40, 48
    perso 2 : -13, 47, 50, 38     perso 5 : -21, 48, 37, 42

Deux gardes : le **type 5 ne casse jamais** (`cmp/eq #5` en tete, rend 0), et tant que
`u8[0x8C6A27D4]` est non nul le compteur n'avance plus -- on rend seulement l'accumule.

### 3. QUI S'EN SERT -- ET FREDERIC AVAIT NOMME LES TROIS BONS

`0x8C0D7D74` a **onze sites d'appel dans cinq acteurs** : id 9, 23, 25, 26 et 63. En
rattachant ces acteurs aux bandes :

| bande | decor | acteur qui casse |
|---|---|---|
| 3 | **Yun** | id 23 |
| 6 | **Hugo** | **id 63** -- le tonneau |
| 11 | **Yang** | id 25, quatre sites d'appel |
| 16 | Hugo bis | id 63, le meme |

**Hugo, Yun, Yang. Exactement les trois decors qu'il avait nommes, et rien d'autre en 2nd
Impact.**

**NEW GENERATION A LE MEME MECANISME** : `0x8C0D7DFC` a pour jumeau `0x8C085A94`,
`0x8C0B9ED0` a pour jumeau `0x8C0373B0`, et le test de contact y est **`0x8C085A1E`**, avec
douze sites d'appel dans les acteurs 15, 29, 31, 32, 69 et 75. En suivant les creations de
seconde generation, il sert sur les bandes **5 et 6 (Yun), 17 et 18 (Yang), 10 (Hugo, la
tente de Munich)**, et aussi **1 (Alex)** et **2**. C'est la reponse a son « *il y a
peut-etre d'autres decors concernes* » : oui, deux de plus, et en New Generation.

### 4. POURQUOI MES CINQ CHEMINS L'AVAIENT MANQUE

**Parce que le test n'est pas dans l'acteur.** `0x8C0D7D74` vit dans la region des etages,
hors de l'intervalle de tout acteur ; `chemins()` a profondeur 0 ne lit que les octets de
l'acteur, et il n'y a la aucune reference a `plw`. Verifie apres coup :

    profondeur 0 :  id 23, 25, 63 -> champs []
    profondeur 1 :  id 23, 25, 63 -> champs [..., +38 son etat, +40, ...]

**La profondeur 1 les aurait trouves, et je l'avais desactivee** le matin meme, parce
qu'elle faisait passer New Generation de 7 acteurs a 22 : une aide de DESSIN, partagee par
tout un voisinage, noyait le signal. J'ai choisi une portee, et ce choix a coute l'autre
famille.

**La lecon n'est pas « toujours plus large ».** Une passe a profondeur 1 rendue telle quelle
est illisible -- je l'ai essayee ce soir, tous les acteurs de toutes les bandes ressortent
avec le meme jeu de champs. La lecon est que **la bonne unite n'est ni l'acteur ni son
voisinage : c'est la FONCTION NOMMEE**. Des que `0x8C0D7D74` a un nom, ses onze appelants se
lisent en une ligne et sans bruit. Chercher « qui lit un combattant » etait la mauvaise
question ; « qui appelle le test de contact » est la bonne.

C'est pour ca que `ruptures.py` cherche desormais les appelants de cette fonction-la, et non
plus une figure.

### 5. CE QU'IL FAUDRAIT POUR LE PORTER

Tout est lu, rien n'est porte. Il faudrait :

* la condition, qui est directement disponible dans 3SX : `plw[n].wu.routine_no[1] == 1` et
  `14 <= routine_no[2] < 24` ;
* les deux boites, a transcrire dans la fiche (celle de l'objet) et dans une table par
  personnage ;
* le recouvrement, qui est dix lignes ;
* et **le script de rupture**, qui existe deja dans les donnees -- le 32 pour le tonneau --
  mais que le port ne pose pas : il faudrait un comportement de plus, du genre de REACTIF,
  qui passe d'un script a l'autre une seule fois et ne revient pas.

---

## RUPTURE PORTEE : LE TONNEAU DE HUGO SE BRISE (23/09, nuit)

### 1. CE QUE FREDERIC A DIT, ET QUI TOMBE JUSTE

> « la destruction ne se joue pas en boucle, mais une seule fois, avec la derniere image de
> l'animation persistante »

Le binaire dit exactement cela, et mieux : les scripts du tonneau sont

    script 31 :  1 image  (34473, 4 trames)          INTACT
    script 32 :  4 pas    34473, 34513, 34514, 34514 LA RUPTURE
    script 33 :  1 image  (34514, 8)                 LE TONNEAU BRISE, AU REPOS
    script 30 :  1 image  (34521, 200)               DETRUIT
    script 34 : 23 images 34515..34524                LA SECONDE destruction

**La derniere image du script 32 EST le script 33.** Tenir la derniere image de la rupture
donne donc le tonneau brise, au pixel pres, sans avoir a enchainer quoi que ce soit. C'est
ce que fait `derouler(k, 0)` du port, qui s'arrete sur le dernier pas et y reste.

**ET LE PORT POSAIT LE SCRIPT 34** -- la SECONDE destruction, vingt-trois images -- **en
boucle**. Le tonneau rejouait sa ruine sans fin. C'est corrige : il pose le 31.

### 2. CE QUI EST POSE

| ou | quoi |
|---|---|
| `decor_objets.h` | `s32 boite[4]` au bout de `DecorAnimation` : `{ x, largeur, y, hauteur }` DANS LE REPERE DE LA FICHE, 0 quand l'objet ne se brise pas |
| `decor_objets.c` | `RUPTURE` (comportement 9), `BOITE_PERSO[16][4]`, `boites_se_touchent` (`0x8C0B9ED0`), `chute_sur` (`0x8C0D7DFC`), `rupture` |
| `animer2i.py` | le tonneau : `script=31`, `comportement=9`, `suites=[31, (32, "une")]`, `boite=(6, 64, 33, 69)` ; l'emetteur met la boite dans le repere de la fiche |

**La condition**, telle qu'elle est dans le C :

    plw[i].wu.routine_no[1] == 1  et  14 <= routine_no[2] < 24
    et la boite de `My_char[i]`, decalee de son `xyz[0]/xyz[1]` et retournee par `rl_flag`,
    recouvre celle de l'objet.

**LE REPERE.** Le Dreamcast range la boite relative a `objet[+102]`/`+106` ; la fiche du
port compte autrement. Le generateur fait donc la conversion une fois pour toutes :

    boite_x = (x + DECALAGE_X + ajx + boite_dc_x) & 0x3FF
    boite_y = 1024 - ((sol - y - boite_dc_y + ajy) & 0x3FF)

Le tonneau, boite `(6, 64, 33, 69)` posee en 816,52, sort en **x 822..886, y 86..155** --
dans sa fiche, qui va de 813 a 909 en x et de 65 a 209 en y. Le controle tient parce que
`DecorObjets_Position` ecrit deja `anim->y` dans `xyz[1].disp.pos` : **la fiche et les
combattants partagent le repere**, ce que SUR_COMBATTANT avait deja etabli chez Elena 2.

### 3. CE QUI N'EST PAS PORTE, ET POURQUOI

**La seconde rupture.** Le tonneau en a deux : un compteur a 2 fait poser le script 34, puis
un effet (`0x8C02AA7C`, argument 6 -- les debris). Et l'etat 0 choisit meme le script de
DEPART sur ce compteur, **qui survit a la manche** : intact (31), fele (33), detruit (30).
Le port pose toujours l'objet intact et n'a qu'une rupture. C'est ce qui se voit ; le reste
demande un etat de partie que le port n'a pas.

### 4. LES AUTRES, IDENTIFIES ET PRETS

Frederic : « *pour les decors de Yun et Yang, ce sont les cages d'oiseaux et la statue qui
se brisent* », et « *pour Alex, je ne sais pas quel objet du decor est destructible* ».

| jeu | decor | acteur | type | boite | script de rupture |
|---|---|---|---|---|---|
| 2I | **Hugo** | id 63 | 7 | `(6, 64, 33, 69)` | 32 -- **PORTE** |
| 2I | **Yun** (les cages) | id 23 | **8** | `(12, 61, 16, 28)` | **12** |
| 2I | **Yang** (la statue) | id 25 | dans l'enregistrement | -- | quatre sites |
| NG | **Alex** | id 75 | **6** | `(-53, 39, 20, 25)` | par `+38 += 1` |

**Yun est pret** : le type 8 est ecrit en dur (`0x8C0293DE`, `mov #8,r0 ; mov.b r0,@(4,r14)`)
et la rupture pose le script 12 (`0x8C029290`). Il ne manque que de savoir laquelle de ses
fiches est la cage.

**Yang est le plus riche** : son spawner prend le type DANS L'ENREGISTREMENT
(`0x8C029B64`, `mov.b @r15,r0`), donc chacun de ses objets a sa propre boite, et l'acteur a
**quatre sites d'appel** au test de contact.

**Alex ne pose pas de script** : il incremente son propre `+38` tant que `u16[0x8C55262C]`
le depasse, donc il a PLUSIEURS etages de destruction, dont le nombre est une donnee de
partie. Son objet est de type 6, boite `(-53, 39, 20, 25)` -- **c'est cette boite qui dira
quel objet de son decor est destructible**, puisqu'elle doit tomber dans la fiche d'un seul
d'entre eux.

**Et les tables de New Generation sont IDENTIQUES a celles de 2nd Impact** : boites d'objets
en `0x8C1890B0` contre `0x8C1D3ED4`, boites de personnages en `0x8C189108` contre
`0x8C1D3F2C`, mêmes valeurs. Une seule table sert les deux jeux, et `BOITE_PERSO` du port
l'est deja.

---

## LES QUATRE DECORS QUI SE BRISENT, ET LA MEMOIRE ENTRE LES MANCHES (23/09, nuit)

### 1. YUN -- LA CAGE D'OISEAUX

Creee par la routine d'etage en **672, 48, palette 90** -- et ce document notait deja
« cages 90 » depuis le 04/09. Son etat 1 (`0x8C029280`) appelle le test de contact et pose
le script 12 (`0x8C029290`). Son type est ecrit en dur par le spawner (`0x8C0293DE`,
`mov #8,r0`), d'ou la boite du type 8.

    script  7 :  1 image   32117          INTACTE
    script 12 : 14 images  32273..32285   LA RUPTURE, qui tient sa derniere image
    script 34 :  1 image   32105          BRISEE, a la manche suivante

### 2. YANG -- LES TROIS STATUES

Ce document le savait depuis le 16/09 sans en tirer la consequence :

> « leurs enregistrements portent trois scripts de plus -- (70, 72, 66), (69, 73, 64),
> (22, 74, 0) -- qui sont le rocher sculpte, le guerrier vert et le personnage de droite
> BRISES au fil du combat. Seul le premier etat est pose. »

L'id 25 a **quatre sites d'appel** au test de contact ; chacun avance d'un cran et pose le
script suivant (`objet[+54]`). **Le type, qui choisit la boite, est l'ARGUMENT de l'appel**
-- `0x8C029B0C` range `r4` et `0x8C029B64` le recopie en `+4` -- donc 0, 1 et 2 dans l'ordre
des trois appels de la routine d'etage (`0x8C0DCAB6`, `ABA`, `ABE`).

| statue | intact | ruptures | boite |
|---|---|---|---|
| le rocher sculpte | 65 (33027) | 70 (33029), 72 (33026) | type 0 : `-159, 48, 65, 93` |
| le guerrier vert | 63 (33025) | 69 (33030), 73 (33028) | type 1 : `90, 63, 98, 45` |
| le personnage de droite | 3 (32710) | **22 (13 images)**, 74 (32892) | type 2 : `5, 61, 41, 40` |

**Deux pieges, ecartes en lisant les images.** Le troisieme script des deux premieres (66,
64) porte LA MEME image que le deuxieme : c'est l'etat de repos, pas un cran de plus. Et le
`0` de la troisieme n'est pas le script 0 -- la lanterne -- mais un « aucun ».

**UN OPCODE DE PLUS.** Le script 72 du rocher emploie le `0x02`, que `script_deroule` ne
connaissait pas et sur lequel il levait une erreur. Il est maintenant lu : son gestionnaire
`0x8C0B530C` fait `index = pas x (mot3 - 2)`, un **saut absolu**, le frere du `0x32` qui
saute en arriere. On le traite comme un `0x01`. **La statue de Yang est le premier objet
porte qui s'en sert.**

### 3. ALEX -- L'ARRIERE DE LA VOITURE

Frederic : « *pour Alex, je ne sais pas quel objet du decor est destructible* ». C'est
celui-ci -- et `objetsng.py` le disait deja, ecrit lors d'une session precedente : « *sa
routine pose le script 16 a sa naissance, puis **19 quand la voiture est frappee*** ».

Sa particularite est qu'**elle encaisse** : ses trois premiers crans portent la meme image.

    scripts 16, 17, 18 : 22077   la voiture intacte
    script  19         : 22078   l'arriere enfonce

Sa routine (`0x8C0A97B6`) ne pose pas de script : elle fait `objet[+38] += 1` tant que
`u16[0x8C55262C]` depasse son etat, et chaque cran est un script consecutif.

### 4. LE COMPORTEMENT, GENERALISE

`RUPTURE` porte maintenant **une suite par cran de destruction**. La suite 0 est l'objet
intact et elle boucle ; les suivantes se jouent une fois et tiennent leur derniere image.

**On n'avance qu'au FRANCHISSEMENT du contact.** Une chute dure plusieurs trames, et compter
chacune aurait consomme les quatre crans d'Alex en un quart de seconde. Le Dreamcast, lui,
accumule un compteur et le compare a des seuils : meme effet, moins de machinerie.

| decor | objet | crans |
|---|---|---|
| Hugo | le tonneau | 2 |
| Yun | la cage d'oiseaux | 2 |
| Yang | **trois statues** | 2 chacune |
| Alex (NG) | l'arriere de la voiture | 4 |

### 5. LA MEMOIRE ENTRE LES MANCHES

**Rien n'efface le compteur du Dreamcast entre deux manches.** Sa seule remise a zero est
`0x8C0D7E58` -- onze entrees mises a zero -- et elle n'est appelee que depuis `0x8C0C1606`,
une fonction de mise en place de PARTIE qui pose aussi le mode de jeu. Un objet brise le
reste donc jusqu'au combat suivant, et c'est pour ca que l'etat 0 du tonneau choisit son
script de depart sur ce compteur : intact (31), fele (33), detruit (30).

Le port refait ses objets a chaque manche. On garde donc le cran atteint dans un tableau a
part, **indexe par le RANG de l'objet dans l'etage** -- lequel ne bouge pas d'une manche a
l'autre, puisqu'il est deja la cle du cache de motifs.

**Quand l'effacer.** `Round_num` vaut 0 au debut d'un combat et monte a chaque manche
(`game.c`, `manage.c`) : il suffit de voir qu'il a RECULE. On efface donc quand l'etage
change ou quand la manche recule -- le meme moment que `0x8C0C1606`.

Et un objet deja brise **reprend a la FIN de sa suite**, sur l'image qui reste, pas au debut
de son animation de rupture qu'on a deja vue.

**Une divergence assumee** : le Dreamcast repose parfois un script DIFFERENT a la manche
suivante plutot que la derniere image de la rupture. Pour le tonneau et les statues c'est
la meme image (le 33 de Hugo vaut la derniere du 32, le 66 de Yang vaut la derniere du 72)
-- pour la cage de Yun, le script 34 (32105) n'est pas la derniere image du 12 (32285). La
cage brisee de la manche 2 sera donc celle de la fin de la manche 1. C'est un pixel de
difference dans une pose fixe ; je le note plutot que d'ajouter une suite pour ca.

### VALIDE, SAUF YANG -- ET LA TABLE DES PERSONNAGES ETAIT COURTE DE QUATRE (24/09)

> « je valide les destructions des elements du decor sauf pour Yang ou je n'ai pu rien
> detruire »

**Une faute certaine, trouvee en cherchant pourquoi.** `BOITE_PERSO` n'avait que SEIZE
entrees, recopiees telles quelles de `0x8C1D3F2C`. Et c'est normal que le Dreamcast s'arrete
la : **2nd Impact s'arrete a Chun-Li**. 3rd Strike ajoute quatre personnages -- Makoto, Q,
Twelve, Remy, indices 16 a 19 -- qui n'avaient donc aucune boite, et le garde
`perso >= 16 -> continue` **sautait le test pour eux**. Joue avec l'un des quatre, rien ne
pouvait se briser, nulle part et sur aucun decor.

La table passe a vingt ; les quatre derniers recoivent la boite la plus repandue
(`-13, 47, 50, 38`, celle de Ryu, Hugo, Elena, Ken, Sean, Akuma et Chun-Li), faute d'une
valeur lue. C'est la seule invention de tout ce travail, et elle est signalee comme telle.

**Si Yang resiste encore**, une trace bornee a trente chutes ecrit dans le journal les deux
rectangles et leur recouvrement : le premier coup d'oeil dira si l'objet est hors de portee
ou si c'est le contact qui ne se declare pas. Les trois statues sont bien emises -- verifie
dans `decor_objets_data.c` : rocher en x 353..401, guerrier 617..680, personnage 756..817,
toutes trois avec `comportement 9` et trois suites.

### LES JETS DE HUGO : UNE QUESTION, PAS UNE CORRECTION

> « Pour le decor de Hugo, a droite, les jets sortants des tonneaux ne sont pas sur le bon
> plan. »

Je ne corrige pas a l'aveugle, parce que ce document interdit exactement ca : « *un z a
l'oeil qui contredit une valeur lue n'a aucune raison de rester* ».

Ce que les donnees disent de Hugo : **tous ses objets sont en famille 2**, et leurs
profondeurs se tiennent entre 74 et 76 -- SAUF DEUX, a **83** :

    element 688,73   script 18   7 images   z 83
    element 606,105  script 28   8 images   z 83

Le plan proche de Hugo est a **84** (`(1,94) (2,84)`). Ces deux objets sont donc a UNE UNITE
devant lui, ce qui est fragile : la moindre difference d'echelle entre les deux jeux les
fait basculer derriere.

Trois lectures possibles, et il faut savoir laquelle avant de toucher :

1. **les jets sont ces deux objets** -- alors leur z de 83 est trop proche du plan et il faut
   etablir la correspondance des echelles, pas le deplacer a l'oeil ;
2. **les jets etaient le script 34** que je viens de retirer du tonneau (la SECONDE ruine,
   vingt-trois images, que le port jouait en boucle) -- alors ils ont disparu, pas change de
   plan ;
3. **les jets sont peints dans la page**, pas un objet -- alors c'est la profondeur d'une
   couche, un autre chantier.

**A demander a Frederic** : les jets sont-ils toujours la, et bougent-ils avec le meme
defilement que les tonneaux ?

---

## DEUX FAUTES ET UNE IDENTIFICATION (24/09)

### 1. LE TONNEAU DE HUGO SORTAIT BLEU

Frederic, capture a l'appui : « *la couleur du tonneau n'est pas bonne* », « *il est bleu
au lieu de beige* ». C'etait **la troisieme des exceptions laissees ouvertes le 16/09** --
le commentaire de `PALETTES_RAM` les nommait sans les trancher : « *Ryu script 7, Hugo id
63, le perroquet d'Oro* ». Le perroquet a ete tranche ce jour-la ; le tonneau attendait.

Il se lit sans rien deviner. Son spawner `0x8C031B56` ecrit en constante

    mov #74,r1 ; [556] = 74      la profondeur
    [88] = 74                    la palette du champ 5
    [554] = 0x2040               MY_COL_CODE -- l'emplacement 64

et l'emplacement 64 de la bande 6 est rempli par **1219 et suivantes**. Le premier morceau
du tonneau est a l'offset 11 : **palette 1230**.

`BANQUES_2I["bg06"]` rangeait, lui, tout offset 0..11 sur `1652 + offset`, donc 1663. Les
deux banques se mesurent, et l'ecart ne laisse aucun doute :

| palette | couleurs chaudes | froides | rouge maximum |
|---|---|---|---|
| **1663** (l'ancienne) | 1 sur 16 | **13 sur 16** | 19 / 31 |
| **1230** (celle du code) | 41 sur 41 | **0** | **31 / 31** |

1230 est une rampe complete, de `R04 G02 B01` a `R31 G31 B19` : le beige du chene.

**ET LE MEME TONNEAU ETAIT DEJA JUSTE DANS BG10.** Hugo bis (Munich) est dans
`PALETTES_RAM` depuis le debut : sa fiche `a57o6` portait **1230**, quand `a28o0` portait
1663. Le meme objet, le meme asset, le meme spawner, deux couleurs. La preuve etait dans
nos propres donnees depuis des semaines.

**Les deux regles ne se contredisent nulle part** : les autres objets de `bg06` ont
`+554 = 0x2064`, l'emplacement 100, que le meme chargeur remplit avec 1652.. L'ancienne
rangeait par OFFSET ce qui se range par EMPLACEMENT ; la ou un seul emplacement sert, les
deux donnent le meme resultat. `bg06` rejoint donc la liste, et la regeneration ne change
que **deux fiches sur 246** -- `a28o0` et `a28o0m1`, verifie ligne a ligne.

### 2. LA MEMOIRE ENTRE LES MANCHES NE S'EFFACAIT JAMAIS

Frederic : « *yang 0B, la statue de gauche reste brisee meme en relancant un nouveau
match* ». La faute est entiere, et elle est de raisonnement.

J'effacais quand **la manche avait recule** : `(s32)Round_num < degat_manche`. Or
`DecorObjets_Marquer` ne passe qu'a la **mise en place de l'etage** -- `bg2202_init00`
appelle `effect_05_init`, et c'est tout. Le compteur de manche y vaut **toujours zero**, la
valeur gardee valait zero elle aussi, et `0 < 0` est faux. **Rien n'etait jamais efface.**

Le bon test etait sous la main : `Round_num` est remis a zero a l'entree d'un combat
(`game.c`, trois sites) et monte a chaque manche (`manage.c`, `Round_num++` juste avant
`Quick_Entry`). **Le voir a zero, c'est etre a la premiere manche d'un combat -- et nulle
part ailleurs.** C'est desormais la condition, et elle vaut que les objets renaissent a
chaque manche ou une seule fois par combat : les deux hypotheses donnent le meme resultat,
ce qui etait justement ce que l'ancien test ne supportait pas.

C'est le meme moment que `0x8C0C1606` du Dreamcast.

### 3. YANG SE BRISE -- LA TABLE COURTE ETAIT BIEN LA CAUSE

Puisqu'une statue de Yang reste brisee, c'est qu'elle s'est brisee. **`BOITE_PERSO` etendue
de seize a vingt entrees etait donc bien la cause** : Makoto, Q, Twelve et Remy n'avaient
aucune boite, et le test etait saute pour eux -- dans tous les decors.

### 4. LES JETS DE BIERE SONT NOMMES

`rendu_fiches.py 28 bg06 --nu` -- qui dessine les tuiles emises, pas les sprites du
disque -- tranche la question de l'identite :

| fiche | script | x | ce que c'est |
|---|---|---|---|
| `a28o5` | 18 | 688 | **l'arc de biere**, un jet dore qui retombe |
| `a28o2` | 28 | 606 | **la chope levee** du buveur, biere debordante |

Ce sont **les seuls objets du decor a la profondeur 83** ; tout le reste est entre 74 et
76. La lecture n° 2 est donc ecartee (ils n'etaient pas le script 34), et la n° 3 aussi :
ce sont bien des objets, pas de la peinture de page.

**Reste la profondeur, et je ne la deplace pas a l'oeil.** 83 est la valeur du binaire ; le
plan proche de Hugo est a 84 (`ETAGES2I_PRIORITY`, etage 28 : `0x68545E00`, soit 104, 84 et
94). Les jets sont donc a une unite devant le plan proche, et derriere tout le reste. Une
seule question tranche ce qui cloche :

* s'ils passent devant **les combattants** (qui sont vers 64), c'est notre profondeur qui
  n'est pas appliquee -- le defaut est dans le moteur ;
* s'ils passent devant **les gros tonneaux de droite**, alors ces tonneaux sont peints dans
  le plan proche, et c'est la profondeur du PLAN qu'il faut reprendre.

---

## LES POTEAUX, LES CORDES ET LES JETS DE HUGO (24/09)

Frederic : « *les jets et les combattants sont devant les 2 poteaux et la corde qui les
relie au lieu d'etre derriere. De plus, les jets devraient etre derriere les 2 autres
poteaux et la 2eme corde qui les relie* ».

### 1. OU SONT LES POTEAUX : DANS LE PLAN PROCHE, VERIFIE EN LE DESSINANT SEUL

La couche a ete dessinee **seule**, sans les autres et sans les objets, pour ne rien
supposer. La demi-banque **basse de la banque 0** -- notre liste 196 -- porte le quai, **les
deux barrieres a cordes**, les gros tonneaux de droite et le plancher. Les deux autres
listes ne portent ni poteau ni corde : la 132 (banque 1 haut) est le champ de voiles des
navires, la 260 (banque 0 haut) le ciel et le plan d'eau.

### 2. SA PROFONDEUR EST 84, ET ELLE EST UNIQUE

`0x8C601EE8`, decor 6, couche 1 : **plan 2, profondeur 84**.

Le format de la couche a ete relu a cette occasion, parce qu'il autorisait une echappatoire.
`0x8C10B070` boucle ainsi :

    r4 = r14 ; tant que u16[r4] != -1 :
        r4 += 4                         plan, profondeur
        tant que u16[r4] != -1 : r4 += 6    un morceau de 3 mots
        r4 += 2

C'est-a-dire **`[plan, profondeur, (3 mots)*, -1]` repete, termine par -1** : une couche
PEUT porter plusieurs groupes, donc plusieurs profondeurs. Ce n'etait pas note. Verifie
pour Hugo et Hugo bis : **un seul groupe chacune**.

    k0  plan 1  profondeur 94  : (255, 0x6F00, 12) (383, 0x7F00, 12) (511, 0x7F00, 12)
    k1  plan 2  profondeur 84  : (127, 0x7F00, 28) (255, 0x7F00, 28) (383, ...) (511, ...)

**Une seule profondeur pour tout ce que la couche porte.** On ne peut donc pas en mettre une
barriere devant et l'autre derriere : ce n'est pas un reglage qu'on rate, c'est une
structure qui ne le permet pas.

### 3. LES COMBATTANTS SONT A 28..56 -- DANS LES DEUX JEUX

`char_init_data2` de 3SX donne `my_pr` de **0x1C a 0x38**, soit 28 a 56. La meme table, aux
**memes valeurs et dans le meme ordre**, est dans `SF3_2ND.BIN` a **`0x8C5FB0EA`**, pas de
0x6C, reconnaissable a ses voisins invariants (`my_cm` 0x4200, `my_cc` 0x2000, `my_fm` 2).

Conséquence : **rien du decor de Hugo n'est devant les combattants, dans aucun des deux
jeux.** Ses couches sont a 84 et 94, ses elements statiques a 76 et 82, ses objets de 74 a
83. Nos propres notes le disaient deja sans qu'on en tire la consequence -- le commentaire
de `SF3_DECOR_Z` : « *20 met tous nos objets devant les plans (84, 90, 94) ET DEVANT LES
COMBATTANTS* ».

### 4. LES JETS A 83 : UN CRAN DEVANT LE PLAN, ET C'EST LU

`a28o5` (script 18, x 688) est l'arc de biere, `a28o2` (script 28, x 606) la chope levee du
buveur -- identifies en dessinant les tuiles emises. Seuls objets du decor a **83** ; le
plan proche est a **84**. Ils passent donc devant les poteaux, et 2nd Impact ne dit rien
d'autre.

### 5. CE QUI RESTE OUVERT, ET QU'IL NE FAUT PAS MAQUILLER

Ce que Frederic decrit **ne se deduit pas des tables**. Deux issues, et aucune ne se tranche
en poussant un chiffre :

1. **La profondeur du PLAN PROCHE est a reprendre.** C'est l'issue que designe sa reponse a
   la question du 24/09 au matin : les jets passent devant les poteaux, et les poteaux sont
   peints dans le plan proche. Mais 84 est lu, pas devine, et les 27 releves de liste
   d'affichage l'ont confirme sur 255 paires couche/objet -- **sans jamais croiser un
   COMBATTANT**. C'est precisement le trou de ce controle.
2. **Hugo aurait un avant-plan que nous ne dessinons pas.** 3rd Strike en a (son etage 10
   porte un plan a `0x14` = 20, devant les combattants) ; la table de 2I n'en donne aucun a
   Hugo. Reste la couche commune du plan 4 (`0x8C1D4B62`, profondeur 69), que le port ne
   dessine pas du tout -- a ouvrir.

**En attendant, `SF3_DECOR_JETS`** met les deux jets a la profondeur qu'on lui donne (85 =
derriere le plan proche). C'est un diagnostic pour juger sur l'image, pas une correction :
si le 85 est le bon, alors c'est la profondeur du PLAN qu'il faut reprendre, et ce sera une
lecture a faire.

---

## J'AI AMPUTE NEW GENERATION EN REGENERANT 2ND IMPACT (24/09)

### 1. LA FAUTE

`decor_objets_data.c` est ecrit par **DEUX** outils :

    animer2i.py --ecrire     ECRIT LE FICHIER A NEUF     246 fiches
    animerng.py --ecrire     AJOUTE les siennes ensuite  525 fiches   -> 771

En relancant le premier pour la palette du tonneau de Hugo, et pas le second, j'ai laisse le
port **sans aucun objet anime sur les dix-neuf etages de New Generation**. Deux lanceurs sont
partis avec cette amputation.

Frederic, apres les deux essais : « *aucun des 2 lanceurs ne donne le bon resultat, revoie
le code du jeu* », puis « *pour le decor de sean NG, a priori, il n'y a pas de paralax* ».
**C'est cette seconde phrase qui a trouve la faute** : Sean est l'etage 39, et le haut de son
decor est fait d'OBJETS, pas d'une couche -- sans eux, plus rien ne defile a sa vitesse.

### 2. CE QUI AURAIT DU M'ALERTER, ET QUE JE N'AI PAS REGARDE

* le compte de fiches est passe de **771 a 246** -- je l'avais sous les yeux dans le diff et
  je l'ai mis sur le compte de l'expression reguliere ;
* l'executable est tombe de **33 Mo a 12 Mo** ;
* les etages presents dans le fichier sont passes de `22..57` a `22..36, 56, 57`.

Rien dans la chaine ne le signalait : la compilation passe, le jeu se lance, les decors sont
simplement vides. **C'est la panne la plus silencieuse rencontree jusqu'ici.**

### 3. LA REPARATION, ET LA GARDE

`animerng.py --ecrire` relance : **771 fiches**, comparees une a une a la sauvegarde
`.avant-pal06` -- aucune disparue, aucune nouvelle, et **deux seules valeurs changees**,
la palette du tonneau (1663 -> 1230). Exe reconstruit a 33 Mo.

`animer2i.py` dit maintenant, en toutes lettres et a chaque ecriture :

    ATTENTION : New Generation N'EST PAS dans ce fichier.
    Relance MAINTENANT :  py -3 animerng.py --ecrire

**La lecon** : un outil qui ecrit A NEUF un fichier qu'un autre COMPLETE doit le dire
lui-meme. Compter les fiches avant et apres n'est pas un luxe -- le diff les comptait, et
j'ai explique l'ecart au lieu de le verifier.

### 4. CE QUE LA RELECTURE DU MOTEUR A QUAND MEME DONNE

Cherchant la faute du cote des profondeurs, j'ai lu quatre choses qui restent vraies.

**a. Le format des couches autorise plusieurs profondeurs, et on ne s'en sert pas.**
`0x8C10B070` boucle `[plan, profondeur, (3 mots)*, -1]` **repete**, termine par `-1` : une
couche PEUT porter plusieurs groupes. Chaque morceau devient un element de 16 octets dont le
troisieme mot est masque par `and #15` puis recoit le numero de plan en bits 4-5. Verifie
pour Hugo et Hugo bis : **un seul groupe chacune** (94 et 84).

**b. 2nd Impact monte un QUATRIEME plan, a la profondeur 69.** `0x8C0DA9B6` :
`mov.l 0x8C1D4B62,r6 ; jsr 0x8C10B070` avec `r4 = 3`. La couche est **commune a tous les
decors**, plan 4, profondeur 69, huit morceaux couvrant 1024. Le port ne monte que trois
plans pour ces etages (`ETAGES2I_USE_SCR` = 3 pour Hugo) et laisse `bg_priority[3]` a son
defaut de 3rd Strike, 70. **69 tombe pile entre les combattants (28..56) et tous les objets
de Hugo (74..83)** -- c'est la seule tranche ou quelque chose passerait devant les jets et
derriere les combattants. Pour Hugo ce plan serait vide (sa demi-banque 1 basse l'est),
mais la mecanique existe et n'est pas portee.

**c. Notre plan le plus lointain chez Hugo n'est pas une couche.** La demi-banque 1 haute
(notre liste 132) porte **le meme navire repete huit fois** : c'est un MAGASIN d'images, au
sens du critere deja pose pour Akuma (« une couche est une image continue, un magasin est
fait de vignettes repetees »). La table des couches de 2I n'a **aucune entree** pour elle --
c'est pour ca qu'il a fallu inventer sa profondeur (104). Nous dessinons un plan que 2nd
Impact ne dessine pas.

**d. Les combattants sont a 28..56 dans les deux jeux, et le decor de Hugo n'a rien devant
eux.** La routine d'etage de la bande 6 a ete relue en entier : ses sept chargeurs
(`0x8C0233B6`, `0x8C02356A`, `0x8C025A9A`, `0x8C028792`, `0x8C02E1FE`, `0x8C031B56`,
`0x8C036480`) ne creent aucun objet hors de 74..83. Les couches sont a 94 et 84, les
elements statiques a 76 et 82.

**Et pourtant ca existe ailleurs** : `etagesng.py` note que **la couche 0 de Dudley 1, la
pluie de Londres, est a 20 -- devant les combattants**. Le mecanisme est donc bien dans les
donnees quand un decor le demande ; Hugo ne le demande pas.

---

## SEAN NG : LA PARALLAXE QUI NE DEVAIT PAS EXISTER (24/09)

Frederic : « *pour le decor NG de Sean, il y a toujours la parallaxe qui ne devrait pas
exister, qui montre le triangle noir qu'on ne devrait pas voir* ».

### 1. LE DESSIN TRANCHE

Ses deux couches ont ete dessinees, puis ses cinquante et une fiches posees dessus
(`sean-complet.png`). **Ses quatorze objets de plans 3 et 5 sont les gratte-ciel du fond de
la rue.** Ils se rangent entre l'immeuble peint de gauche et celui de droite, leurs pieds
touchent le trottoir de la couche proche, et l'un d'eux vient combler **l'arc creuse dans la
facade de droite**. C'est une seule scene continue avec la rue.

Le releve est net : sur les cinquante et une fiches de l'etage 39, **toutes** celles de
famille 1 sont de plan 3 (neuf, z 100) ou de plan 5 (cinq, z 103-104). Aucune n'est de plan
1, celui de la couche du ciel. Le partage ne laisse aucune place au doute.

### 2. LA FAUTE, ET D'OU ELLE VENAIT

`famille_du_plan` portait depuis le 18/09 une branche :

> « UN PLAN SANS COUCHE, AUTRE QUE LE 2 : les immeubles de Sean (plans 3 et 5).
> L'initialisation des plans (`0x8C088242`) leur donne un coefficient nul, ou aucun (le plan
> 5 est hors de la table) : ils ne suivent pas la rue. On les met sur le plan le plus lent de
> la bande, le seul qui reste presque fixe. »

Le plan le plus lent de Sean est le ciel, a **0,625** ; la rue va a **1,0**. Les gratte-ciel
glissaient donc sur elle a chaque mouvement de camera, et l'arc de la facade se decouvrait.
**Le triangle noir de Frederic, c'est cet arc.**

Le defaut documente deux lignes plus bas -- « *un plan introuvable ou ambigu garde la
famille 2* » -- etait le bon pour lui.

**La lecon** : le raisonnement du 18/09 n'etait pas absurde (un plan hors table n'a pas de
coefficient), mais il concluait « presque fixe » sans jamais regarder ce que ces objets
DESSINENT. Un objet qui continue une scene peinte appartient au plan de cette scene, et ca
se voit en le posant dessus.

### 3. CE QUI CHANGE, ET CE QUI NE CHANGE PAS

`SANS_COUCHE_SUIT_LA_RUE = {2}` dans `animerng.py`. **La bande 2 seule** : c'est la seule ou
la mesure existe.

**Quatre autres etages passent par la meme branche et ne sont PAS touches** : 38 (plan 3,
2 fiches), 44 (plan 3, 2), 51 (plan 3, 3), 52 (plan 3 et sans plan, 6). Meme construction,
meme soupcon -- a juger un par un, sur l'image.

Regeneration verifiee fiche par fiche : **seize** changent sur 771, et rien d'autre --
les quatorze de Sean (la famille SEULE ; ni position, ni profondeur, ni palette) et les deux
du tonneau de Hugo.

### 4. LES JETS DE HUGO : LA REPONSE PAR L'ABSURDE

« *Les jets ne sont plus presents* » : c'etait le choix 2, qui les posait a 85. **A 85 ils
passent derriere la couche proche, opaque a cet endroit : invisibles.** A 83, ils sont devant
les poteaux.

Et c'est ce qui tranche : **il n'existe aucune profondeur qui les mette derriere les poteaux
et devant les gros tonneaux**, puisque les poteaux, les deux cordes et les tonneaux sont
peints dans **la meme page**, a 84. La question n'est donc pas la profondeur des jets.

Ils reviennent a 83, la valeur lue. Et le decor de Hugo se reprend **par les PLANS**, comme
Sean vient de le montrer -- pas par les profondeurs. Les pistes ouvertes, dans l'ordre :

1. **notre plan le plus lointain n'est pas une couche** (la demi-banque 1 haute porte le meme
   navire huit fois : un magasin, pas un plan) -- nous dessinons ce que 2I ne dessine pas ;
2. **2I monte un quatrieme plan a la profondeur 69** (`0x8C1D4B62`, commun a tous les decors)
   que le port ne monte pas ;
3. et la question qui reste entiere : **qu'est-ce qui, chez Hugo, passe devant les
   combattants ?** Rien dans ses donnees ne le fait -- alors que chez Dudley 1 en NG, la
   pluie de Londres est a 20, devant eux.

---

## LE GEL A LA SECONDE ENTREE DANS UN ETAGE (24/09)

Frederic : « *crash du decor de Sean NG* ». Ce n'etait pas sa famille, et la trace posee le
17/09 pour ce genre de cas a fait exactement son travail :

    GEL 16x16 : code 0x00d303ce (groupe 0xd3), 1 emplacements occupes

### 1. CE QUE LA LIGNE DIT

Le groupe **0xD3 est le notre** (`GROUPE_A_NOUS`), la cle **974** est celle d'un de nos
morceaux, et **la collection de motifs trouvee n'en contenait QU'UN**. Ce n'etait donc pas la
bonne collection -- pas un debordement de cache, une collection etrangere.

`check_patcash_ex_trans` cherche l'identite dans `mt->cpat`, **une liste plate de
soixante-quatre entrees qui survit au changement d'etage**. Le TAS DE MORCEAUX, lui, repart a
zero quand l'etage se recharge.

A la **seconde** entree dans le meme etage, l'objet `k` en est a la meme image qu'a la
premiere : **meme identite**. Le moteur la retrouve (`ix >= 0`), prend le chemin qui ne
televerse rien, restreint la recherche aux emplacements que cette entree avait pris
(`makeup_tpu_free`) -- des emplacements qui ne portent plus rien --, `get_mltbuf16_ext` ne
trouve pas, journalise, et **boucle a l'infini**.

Le journal le confirme : la ligne `[texture] stage 39: 13 duplicate pages` precede
immediatement le gel, et `fin-de-round.log` montre un premier combat sur l'etage 39 aux
trames 2640 a 3180. **Il a fallu entrer deux fois.**

### 2. LA CORRECTION

L'identite tenait sur seize bits : l'image sur huit, le rang sur six (`OBJETS_MAX` = 56).
**Les deux bits hauts etaient libres.** Ils comptent desormais les mises en place d'etage,
modulo quatre, incrementees la ou le tas d'effets repart a zero (`DecorObjets_Marquer(NULL)`,
c'est-a-dire `effect_work_init`). Une identite de la visite precedente ne peut plus etre
retrouvee, et les entrees mortes vieillissent et se font reprendre normalement.

### 3. CE QUE CE N'ETAIT PAS, ET COMMENT JE LE SAIS

**Pas la famille de Sean.** `my_family` n'est lu qu'a **un seul endroit** de tout le moteur,
`mlt_obj_matrix` (`mtrans.c`), pour choisir la matrice de defilement. Il n'entre ni dans
l'identite (`GROUPE | generation | rang | image`), ni dans la cle de morceau
(`cle_base + image * cases + case`), ni dans le choix du cache (`my_mts`, qui vaut 7 pour
tous nos objets). Verifie par recherche exhaustive sur l'arbre.

**Le gel etait donc la avant, et il valait pour TOUS les etages ajoutes** -- il attendait
qu'on entre deux fois de suite dans le meme decor. C'est une condition qu'aucun de nos essais
n'avait remplie : on lance, on regarde un decor, on quitte.

**La lecon** : une trace posee pour un gel precedent (le 17/09, `TraceFin`) a donne la
reponse en une ligne, six jours plus tard, sur un gel qui n'avait rien a voir. Les traces
bornees ne coutent rien et elles survivent a la panne qu'elles n'attendaient pas.

---

## LE GEL AU COUP DE PIED : LES CINQ REACTIFS DE SEAN (24/09)

Frederic : « *crash encore juste en appuyant sur le bouton coup de pied fort* ». Meme ligne
de trace que le gel precedent, et c'est **« 1 emplacement »** qui donne tout :

    GEL 16x16 : code 0x00d303ce (groupe 0xd3), 1 emplacements occupes

### 1. LA LECTURE

La collection de motifs retrouvee ne contenait **qu'un seul morceau**. Or le seul morceau
qu'un de nos objets puisse televerser a lui tout seul, c'est `tuile_vide` sous `CLE_VIDE` --
la case vide partagee.

L'etage 39 porte **cinq objets REACTIF** (comportement 8). Au repos, `DecorObjets_Tuile`
leur rend du vide pour TOUTES leurs cases : la collection de leur identite se cree donc avec
**une seule case**.

Mais `DecorObjets_Identite` ne portait que **le rang et l'image** -- et chez un REACTIF
**l'image avance normalement** : `image_conduite` rend -1 pour lui, parce que c'est son
AFFICHAGE qui depend du combattant, pas son image.

Coup de pied fort : `plw[0].wu.routine_no[1]` passe au-dessus de 2, `regard` passe a 1,
l'objet se montre. **Meme rang, meme image, meme identite.** `check_patcash_ex_trans` la
retrouve, `makeup_tpu_free` restreint la recherche a l'unique emplacement de la case vide,
`get_mltbuf16_ext` cherche la cle 974, ne trouve pas, journalise et **boucle a l'infini**.

### 2. LA CORRECTION

Le test « ce morceau ne dessine rien » est sorti de `DecorObjets_Tuile` dans une fonction,
`ne_dessine_rien(k)`, et **l'identite le porte** : bit 24 du code, un des huit bits hauts
qui etaient libres au-dessus de `GROUPE_A_NOUS`.

    code = GROUPE_A_NOUS | (rien << 24) | (generation << 14) | (rang << 8) | image

**C'est la meme faute que le 17/09, dans l'autre sens.** Ce jour-la l'identite ne portait
pas notre image et le gel venait de notre cadence ; aujourd'hui elle ne portait pas notre
visibilite. La regle, enfin ecrite en clair : **l'identite doit porter TOUT ce qui change
l'ensemble des morceaux televerses, et rien de moins.**

### 3. POURQUOI IL A FALLU UN MOIS POUR LE RENCONTRER

**Il ne se voit qu'avec `SF3_DECOR_REACTIF=1`** -- le choix 2 du lanceur. Par defaut
`reactif_permis()` est faux, `regard` est force a 1, les sprites reactifs sont toujours
visibles, et le bit vaut zero en permanence : aucune identite ne change, aucun gel. Tous nos
essais precedents passaient par le choix 1.

### 4. ET LA GENERATION D'HIER

Elle reste, et je la separe honnetement : **ce n'etait pas elle**. Le gel de la veille avait
le meme code et le meme « 1 emplacement » -- c'etait deja celui-ci. La generation repare une
autre faute, reelle mais non observee : la liste des soixante-quatre collections survit au
rechargement d'un etage alors que le tas de morceaux, lui, repart a zero.

---

## J'AI CORRIGE LE GEL PAR LE MAUVAIS BOUT (24/09, suite)

Frederic : « *encore crash* ». Et cette fois **aucun journal** : pas de `fatal.log`, pas de
trace, la sortie s'arretant net sur `[texture] stage 39: 13 duplicate pages`.

### 1. LE DIAGNOSTIC ETAIT BON, LA CORRECTION NE L'ETAIT PAS

Les cinq REACTIF de Sean se dessinaient **vide** au repos, d'ou une collection de motifs
d'une seule case, retrouvee ensuite quand l'objet se montrait. Ca, c'etait juste.

Mais j'ai corrige en mettant la visibilite **DANS l'identite** (un bit de plus), ce qui
**double le nombre d'identites des reactifs**. Soigner une saturation de cache en ajoutant
des entrees dans ce cache ne pouvait pas tenir, et le jeu est mort a l'entree de l'etage.

**La regle que je n'avais pas appliquee** : quand une correction consiste a decrire une
situation genante, se demander d'abord si on peut la SUPPRIMER.

### 2. LA VRAIE

**Un REACTIF que personne n'a declenche n'est plus dessine du tout.** `eff05` ne le passe
plus a `disp_pos_trans_entry_s` :

    if (DecorObjets_Dessine(&ewk->wu)) {
        disp_pos_trans_entry_s(ewk);
    }

Il n'a donc ni morceau, ni collection, ni identite cette trame-la. Rien a retrouver, rien a
confondre -- et le cache ne se remplit plus de cases vides. Le test « ne dessine rien » vit
en un seul endroit (`ne_dessine_rien`), lu par `DecorObjets_Dessine` et par
`DecorObjets_Tuile`.

L'identite redevient `GROUPE | generation | rang | image`.

### 3. ET UN PLANTAGE DUR NE MOURRA PLUS MUET

C'est ce qui a coute ce tour : **le port n'avait aucun gestionnaire pour une vraie faute de
memoire**. `fatal_error` ne sert que sur les chemins que le jeu connait (`flLogOut`, les
gels `while (1)`). Une violation d'acces faisait disparaitre le processus sans une ligne.

`install_crash_handler()` pose `SetUnhandledExceptionFilter` avant tout le reste dans
`Main_Init`, et reutilise le dumpeur de symboles de `fatal_error` : la trace aura la meme
forme et le lanceur la trouvera dans `fatal.log` comme les autres.

**La lecon, et elle vaut pour la suite** : avant de corriger a l'aveugle une panne qui ne
parle pas, poser de quoi la faire parler. Deux allers-retours ont ete perdus faute d'une
dizaine de lignes qui existaient deja ailleurs dans le fichier.

---

## LE TAMPON DE MORCEAUX : 1024 PLACES, 2268 DEMANDES (24/09)

Frederic : « *encore et toujours crash, tu as casse le jeu entier ou juste ce decor ?* ».
Question juste, et il a fallu un gestionnaire de plantage pour pouvoir y repondre.

### 1. CE QUE LE DERNIER RECOURS A DONNE

    Fatal error: plantage dur : code 0xC0000005 a l'adresse 00007ff788d57215

`0xC0000005` : violation d'acces. Pas un gel, pas un cache plein -- **une ecriture hors
bornes**. Et l'adresse absolue ne servait a rien, Windows deplacant l'image a chaque
lancement : le gestionnaire donne desormais l'ECART au debut du module.

### 2. LA MESURE

`seqsGetUseMemorySize()` rend `0xD000` = 53248 octets. Un `Sprite2` fait **52 octets**
(deux `Vec3`, deux `TexCoord`, trois `u32`). **53248 / 52 = 1024 exactement**, et
`seqsStoreChip` garde ce chiffre (`sprTotal > 0x400`).

Nos etages en demandent bien davantage, et ca se compte sans rien lancer -- la somme des
`cols * ligs` de tous les objets vivants d'une variante :

| etage | morceaux par trame | | etage | morceaux par trame |
|---|---|---|---|---|
| 51 | **2236** | | 39 (Sean) | **2025** |
| 37 | **2043** | | 47 | 1453 |

**Trois etages au-dessus du double du tampon.**

### 3. ET L'ORDRE ETAIT MAUVAIS

    chip = &seqs_w.chip[seqs_w.sprTotal];   /* on ECRIT */
    ...
    seqs_w.sprTotal += 1;
    if (seqs_w.sprTotal > 0x400) { flLogOut(...); while (1) {} }   /* on CONTROLE */

Au 1025e morceau, le moteur posait **52 octets apres la fin du bloc**, puis seulement s'en
apercevait. Une ecriture hors bornes dans le tas, a chaque trame. Selon ce qui suivait dans
le tas, ca figeait proprement (le message japonais) ou ca tuait le processus sans un mot --
ce qu'on a vu.

### 4. LA CORRECTION

`SEQS_CHIP_MAX = 4096`, le tampon dimensionne dessus (`SEQS_CHIP_MAX * sizeof(Sprite2)`,
208 Ko au lieu de 52), et **le controle passe AVANT l'ecriture**. C'est le meme genre de
releve que `PATTERN_PAGES16_MAX` (4 -> 10) et `PATTERN_COLLECTION_MAX` (64 -> 128) : les
bornes de la console ne tiennent pas nos decors.

### 5. LA PART DE RESPONSABILITE, ET LA PORTEE

**C'est moi qui ai amene la charge** : cinquante et un objets animes chez Sean la ou le jeu
en prevoyait une poignee. Mais le defaut -- ecrire avant de controler -- etait la depuis
toujours, en embuscade derriere le premier etage un peu charge.

**Portee de tout ce qui a ete ajoute** : les vingt-deux etages d'origine ne dependent de
rien de nous. Tout passe par `bg_index >= 22` dans `eff05.c` -- et le dernier appel qui
avait deborde hors de ce test (`DecorObjets_Dessine`) y est rentre. Les seules exceptions
sont `DecorObjets_Oublier`, de la comptabilite qui parcourt notre table, et le gestionnaire
de plantage, qui n'ecrit que lorsque tout est deja perdu.

---

## UNE COUCHE NE DESSINE PAS TOUTE LA LARGEUR -- LES POTEAUX DE HUGO (24/09)

Frederic, trois fois de suite : « *les poteaux et la corde ne sont toujours pas sur le bon
plan* ». Il avait raison trois fois, et je cherchais du cote des objets alors que la faute
etait dans la COUCHE.

### 1. LE MORCEAU D'UNE COUCHE PORTE UN X DE FIN

Le format relu le 24/09 -- `[plan, profondeur, (3 mots par morceau), -1]` -- laissait trois
mots par morceau sans emploi. **Le premier est un x de fin, par tranches de 128 pixels.**
Le releve des dix-sept decors le demontre sans code a lire :

| decor | couche | morceaux | x de fin | largeur |
|---|---|---|---|---|
| 9 | 1 | 8 | 127 … 1023 | **1024, toute la bande** |
| 8 | 0 | 6 | 127…511, 895, 1023 | **avec un TROU** |
| la plupart | — | 4 | 127, 255, 383, 511 | **512 seulement** |

Le trou du decor 8 est la preuve decisive : une liste de tranches, pas un compte.

### 2. HUGO N'EN DESSINE QUE LA MOITIE GAUCHE

    decor 6 couche 1 : plan 2, profondeur 84, 4 morceaux -> x 0..511

Or **les deux poteaux, les deux cordes, les gros tonneaux et le plancher sont entre x 600
et x 900**. La couche proche ne les dessine pas.

### 3. CE QUI LES DESSINE EST A 82

Son chargeur d'elements statiques, lu en clair :

    element 0 : plan 2, x 512, y 144, PROFONDEUR 82, script 17
    element 1 : plan 2, x 464, y  78, profondeur 76, script 4

**82, et le premier commence exactement la ou la couche s'arrete.** Les deux jets sont a
**83** : en 2nd Impact ils passent donc DERRIERE les poteaux. C'est mot pour mot ce que
Frederic decrivait depuis le 24/09 au matin.

Notre chaine cuit ces elements **dans** la page proche, qui porte 84 -- et un objet a 83
passait devant. **Un cran.**

### 4. LA CORRECTION

`Z_PROCHE_ELEMENT = {"bg06": 82, "bg10": 82}` dans `etages.py`, suivi par `etages2ibis.py`
pour Hugo bis. **Un seul octet change dans toute la table des profondeurs** :

    etage 28 : 0x68545E00 -> 0x68525E00
    etage 57 : 0x5E540000 -> 0x5E520000

Rien d'autre chez Hugo n'est a 82 ni a 83 -- ses objets sont a 74, 75, 76 et 83, ses autres
couches a 94 et 104 : **le cran ne deplace que les deux jets**, et dans le sens demande.

### 5. CE QUI RESTE OUVERT

Frederic disait aussi que **les combattants** devraient passer derriere la premiere paire de
poteaux. A 82 ils restent devant, puisqu'ils sont a 28..56 -- la meme table, aux memes
valeurs, dans les deux binaires. Pour les mettre derriere il faudrait un element a moins de
28, et Hugo n'en a pas. A reprendre s'il le confirme.

**Et la lecon, qui vaut pour les seize autres decors** : `couches2i.py` ecrit la demi-banque
ENTIERE comme couche, alors que 2nd Impact n'en dessine parfois que 512 pixels, voire avec
un trou. Partout ailleurs ca se voit peu -- les elements statiques prolongent la couche a
une profondeur voisine -- mais la regle est fausse, et elle attend d'etre reprise
proprement : une couche par tranche, a la profondeur que la tranche merite.

---

## LE SECOND JEU D'ELEMENTS STATIQUES -- LES POTEAUX DE HUGO, ENFIN (24/09, soir)

Frederic, quatre fois : « *les 2 poteaux et la corde doivent etre au premier plan* », puis
« *ton interpretation du code est fausse ou lacunaire* ». Les deux, et voici les deux.

### 1. CE QUI ETAIT FAUX

Le matin meme j'avais lu le premier mot d'un morceau de couche comme **un x de fin** et
conclu que la couche proche de Hugo ne dessinait que x 0..511. **C'est un y**, et la
correction qui en sortait (couche proche a 82) est defaite.

### 2. CE QUI ETAIT LACUNAIRE -- ET C'ETAIT L'ESSENTIEL

**Il y a DEUX jeux d'elements statiques, et la chaine n'en lisait qu'un.**

    premier jeu : nombres 0x8C17B918, pointeurs 0x8C5F9C04   -- lu par etages.py
    second  jeu : nombres 0x8C17BBC4, pointeurs 0x8C5F9CD0   -- lu par PERSONNE,
                  sauf `statiques2i.elements_second_jeu`, et seulement pour la
                  variante d'Elena (bg08)

Le second jeu de Hugo :

| x, y | profondeur | script | ce que c'est |
|---|---|---|---|
| 224, 12 | **20** | 19 | la paire de poteaux de gauche |
| 666, 62 | 74 | 26 | — |
| **686, 25** | **19** | **27** | **les deux poteaux et leur corde**, x 686 a 926 |
| 624, 145 | 82 | 24 | — |

**19 et 20 : devant les combattants**, qui sont a 28..56 dans les deux binaires.

### 3. LA PREUVE ETAIT CHEZ LE JUMEAU

**Hugo bis (etage 57) les pose deja** -- sa fiche `a57o4` porte **z 19**, en trois morceaux
a x 686, 782 et 878. Et en dessinant les deux pages proches SEULES, cote a cote :

* **stage 57 : ni poteau ni corde dans la page** -- barriques, eau, planches, rien d'autre ;
* **stage 28 : poteaux et corde peints dedans**, donc a 84, derriere tout le monde.

Hugo ne posait qu'un objet en dur, son tonneau (`0x8C031B56`) ; ses six elements restaient
dans la page. Il en porte maintenant les six, aux memes profondeurs que Hugo bis, et passe
de 16 a **26 fiches**.

La copie peinte dans la banque reste : elle est exactement sous le sprite et disparait des
que celui-ci passe. C'est ce que fait le Dreamcast, dont la banque de `bg06` porte les deux.

### 4. `couches2i.py` : LA REGLE EST FAUSSE, LA COUPER AUSSI

Frederic : « *corrige couches2i.py qui ecrit la demi-banque entiere comme couche partout* ».

Le lecteur est ecrit (`etages.morceaux_couche`) : le morceau donne `[y - hauteur + 1, y]`.
Et **avant de couper quoi que ce soit**, les tranches ont ete croisees avec les lignes
reellement peintes de chaque demi-banque :

| couche | lignes peintes | tranches | pixels dedans |
|---|---|---|---|
| bg0a k0 (Oro) | 0..431 | 64..207 | **0 %** |
| bg0a k2 (Oro) | 304..411 | 64..207 | **0 %** |
| bg05 k2 (Necro) | 288..399 | 128..255 | **0 %** |
| bg08 k1 (Elena) | 0..511 | 382..383 | **0 %** |
| bg06 k0 (Hugo) | 0..511 | 144..511 | 71 % |
| la plupart | — | 0..511 | 100 % |

**Zero pour cent.** Couper aurait efface tout le fond d'Oro -- le couchant et la grotte --,
valide en septembre. Une couche ne peut pas dessiner 0 % de sa demi-banque : **la tranche
n'est pas un intervalle de lignes de banque**.

Ce qu'elle est, la mesure le suggere : **une bande d'ecran**. Necro a une tranche de 128
lignes pour un contenu de 112, Oro une de 144 pour 432. La tranche dit OU le plan peint, et
le defilement y fait passer la banque. Un plan qui ne peint qu'une bande de l'ecran n'est
pas modelise dans le port ; c'est un chantier a part, et il lui faudra une observation pour
partir.

`couches2i.tranches` **mesure et signale** desormais, decor par decor, sans couper. La regle
fausse est bornee et ecrite.

**La lecon** : la correction qui consiste a couper ce qu'on croit superflu doit etre mesuree
contre ce qui est reellement peint AVANT d'etre posee. Trente secondes de croisement ont
evite de casser cinq decors.

---

## LES OISEAUX D'ELENA 1 : L'ACTEUR EST LU, LA VOLEE RESTE (24/09, soir)

Frederic : « *les oiseaux volant au loin (quelques pixels blancs) sont manquants* », puis,
apres une premiere version : « *ne devine rien, j'en ai marre de repeter cette phrase* ».
Il a raison : la vitesse de cette premiere version etait inventee. Elle est retiree.

### 1. CE QUI EST LU -- ET POSE

**Le createur `0x8C0A707A` etait VU par la chaine et jamais emis** : `animerng` le listait
dans ses appels de routine d'etage (`bande 14  8C08B404 -> 8C0A707A`) sans lui faire de
fiche, faute d'entree dans `objetsng`.

    id 56, routine 0x8C0A5A14, plan 1 (le lointain), profondeur 81, palette 81, +554 = 87
    naissance en x -256, y 112 -- il entre par la gauche, hors ecran
    +364 = 0x8C0D9658 : une table de HUIT scripts de battement d'ailes

Les huit, lus enregistrement par enregistrement (8 octets, `{drapeaux, duree, .., image}`) :

| # | images | durees |
|---|---|---|
| 0 | 20576..20582 | 14 partout -- **le vol lent, celui du lointain** |
| 1 | 20576..20582 | 10 8 7 7 8 7 6 |
| 2 | 20569..20575 | 8 8 8 8 8 7 7 |
| 3 | 20562..20568 | 6 6 6 6 2 7 7, puis 20562 |
| 4 | 20555..20561 | 6 7 7 7 6 6 6 |
| 5 | 20555..20561 | douze pas |
| 6 | 20504..20515 | treize pas, le dernier marque |
| 7 | 20537..20543 | 9 10 9 10 10 11 8 |

C'est le **script 0** qui est pose : sept images, le battement le plus lent.

### 2. CE QUI N'EST PAS LU -- ET QU'ON NE MET DONC PAS

**Le vol.** La routine avance `+100 += +124 * n` et accelere `+124 += +132 * n`, et change
d'etat quand `x` (+102) atteint `+70`. Or **ni `+124` ni `+132` ne sont jamais ecrits** --
verifie en desassemblant le createur ET les onze etats de la routine en entier.

Ils viennent d'ailleurs, et l'ailleurs est trouve :

    0x8C0A5CF8   monte UNE VOLEE
                 remplit une liste de SIX entrees d'id 57 (l'autre acteur d'oiseau,
                 routine 0x8C0A5F5C)
                 pose sur la pile x = +/-256, et deux constantes en 16.16 :
                     +/-0x8000    = 0,5
                     +/-0x140000  = 20,0
                 le signe vient du drapeau 0x8C549409 -- la volee traverse dans un sens
                 ou dans l'autre
                 puis cree un PARENT d'id 63, `col` 0x2040
                 une table a pas de 13 en 0x8C160F04 porte le reste
    appelee depuis le site reference en 0x8C04C348

**Laquelle des deux constantes est la vitesse et laquelle la borne, la lecture ne le dit
pas encore. On ne choisit donc pas.** L'oiseau est pose a sa naissance lue, il bat des
ailes, et il ne voyage pas tant que la volee n'est pas decodee.

### 3. LA REGLE, ECRITE UNE BONNE FOIS

**Ce qui est lu, on le pose ; ce qui ne l'est pas, on l'omet.** Une omission se voit et se
corrige ; une invention se voit aussi, mais elle coute un aller-retour et elle use la
confiance. Les quatre boites de personnages du 24/09 etaient une invention ASSUMEE et
ANNONCEE -- c'est la seule forme acceptable, et elle doit rester rare.

---

## ELENA 1 (NG, BANDE 14, ETAGE 51) : TOUTES LES ANIMATIONS, DECODEES (24/09, nuit)

Frederic : « *redecode toutes les animations autour du stage 1 d'Elena, ne devine rien* ».
Voici le relevé complet, et **la faute de lecture qui l'avait empeche**.

### 0. LA FAUTE : LA TABLE DES ACTEURS

J'employais **`0x8C1AD9F8`** comme table des acteurs de New Generation. **C'est
`0x8C1ADA10`** -- six entrees plus loin, celle qu'`objetsng` emploie depuis toujours. Tout
ce que j'ai lu le 24/09 dans l'apres-midi portait donc sur l'acteur 50 et non sur le 56 :

    lue a tort   id 56 -> 0x8C0A5A14   (c'est l'acteur 50)
    la vraie     id 56 -> 0x8C0A6F10

D'ou la conclusion fausse « la vitesse n'est jamais ecrite », et la volee de six oiseaux
avec ses constantes 0,5 et 20,0, qui appartient a un autre decor. **Verifier une table par
trois de ses entrees connues avant de s'en servir** -- ici `id 45 -> 0x8C0A4D34`,
`id 65 -> 0x8C0A8970`, `id 122 -> 0x8C0B248C`, tous trois deja dans le dossier.

### 1. TOUT CE QUE LA ROUTINE D'ETAGE CREE -- BALAYAGE EXHAUSTIF

Seize appels. **Cinq creent un objet, onze n'en creent aucun** (verifie par
`immediats2i.analyser`, aucun n'ecrit `+8`) :

| appelee | id | x, y | plan | profondeur |
|---|---|---|---|---|
| `0x8C0A4DD8` | 45 | -4, 80 | 1 | 100 |
| `0x8C0A6864` | 53 | 656, 48 | 2 | 67 |
| `0x8C0A707A` | **56** | **-256, 112** | **1** | **81** |
| `0x8C0B253C` | 122 | quatre fois | 2 | 20 et 77 |
| `0x8C0B27BA` | 123 | 512, 40 | 2 | 76 |

Aucun element **jeu1** pour cette bande ; **neuf elements jeu2** (`0x8C1AF70A` a
`0x8C1AF79A`). Dix-sept enregistrements en tout, **quarante-huit fiches** apres decoupe.

### 2. CHAQUE ANIMATION, COMPAREE AU BINAIRE

Douze conformes au script lu. Quatre ecarts, tous expliques :

| objet | binaire | emis | pourquoi |
|---|---|---|---|
| id 122, sc 9-12 | 13 images de 4 | 1 | `fige` : l'etat 1 de `0x8C0B248C` n'avance pas le script tant que le pont tient -- la corde tendue, image 0 |
| id 45, sc 8 | durees 6 | durees 33 | sa routine n'avance le script que toutes les 33 trames |
| id 53, sc 22 | 13 images + commande `0x2B` + 9 | 36 | boucles deroulees |

### 3. LES OISEAUX QUI TRAVERSENT (id 56) -- PORTES, TOUT EST LU

`0x8C0A6F10` copie huit octets de `0x8C1B2308` sur la pile : **deux etats**.

| ou | ce qui est ecrit |
|---|---|
| spawner `0x8C0A707A` | `[+52] = 108`, x -256, y 112, plan 1, profondeur 81, palette 81, `+554` = 87, table `0x8C0D9658` |
| etat 0 `0x8C0A6F7C` | `[+52] -= 1` ; sous zero -> etat 1 |
| etat 1, sous-etat 0 `0x8C0A6FBE` | `[+562] = 1`, `[+568] = [+570] = 12`, **`[+124] = 0x2500`**, **`[+132] = 0`** |
| etat 1, sous-etat 1 `0x8C0A6FE2` | avance le script ; si **`[+102] > 510`** -> sous-etat 2 ; sinon `0x8C0857B0`, qui fait `[+124] += [+132]` puis `[+100] += [+124]` |
| etat 1, sous-etat 2 `0x8C0A7040` | `[+36] = 0`, `[+38] = 0`, `[+102] = -256`, `[+106] = 112`, **`[+52] = 600`**, et `0x8C03324C(objet, 0, 0)` repose le script 0 |

**Le cycle, en chiffres lus** : attente 108 trames (la premiere fois) puis 600 a chaque
tour ; vol de -256 a 510, soit **766 pixels**, a **0x2500 = 0,14453125 pixel par trame**,
acceleration nulle, soit **5300 trames**.

`0x2500 >> 8` fait **37**, et le TRAJET du port compte en 1/256 de pixel par trame
(`px += seg[1] << 8`) : 37 y redonne 0x2500 **exactement**, sans arrondi.

    trajet = [(600, 0, 0, -1), (5300, 37, 0, -1)]

**La seule difference assumee** : le trajet boucle, il ne distingue pas la premiere attente
(108) des suivantes (600). On pose 600, le regime permanent ; l'ecart ne joue qu'une fois.

**ET LE REPLI.** Le moteur de NG dessine en `[+84] = [+102] & 0x3FF` : la bande fait 1024,
ce qui sort d'un bord revient par l'autre. Les oiseaux naissent en -256, donc **768**, et
traversent 766 pixels : sans repli ils sortiraient de la page a 1494. `DecorObjets_Position`
replie desormais l'abscisse d'un trajet. Les autres objets a trajet restent dans
[0, 1024] -- la caleche de Dudley va de 416 vers 48, l'eau d'Elena de 412 a 428 -- et le
masque ne change rien pour eux.

Le sprite est **une volee entiere dans une seule image** de 80x64, sept images de 14 trames
(script 0 de `0x8C0D9658`), images 20576..20582. Rendu et verifie a l'oeil sur les tuiles
emises.

### 4. L'OISEAU POSE (id 53) -- DECODE, PAS ENCORE PORTABLE

`0x8C0A63F0`, **dix etats**. Le dossier disait « attend 148 trames » : **c'etait l'OFFSET
du champ, pas la duree**. La valeur est **120**.

| etat | ce qu'il fait |
|---|---|
| 0 `0x8C0A6470` | pose le script 0 de sa table (= le 22), `[+148] = 120`, `[+1] = 1` |
| 1 `0x8C0A6490` | `[+148] -= 1` ; sous zero -> etat 2 |
| 2 `0x8C0A64AC` | avance le script ; a l'image 2, **`[+556] = [+88] = 79`** (il passe devant) -> etat 3 |
| 3 `0x8C0A6500` | avance ; au retour a l'image 0, `[+1] = 0` -> etat 4 |
| 4 `0x8C0A653E` | `[+52] = 67`, pose le **script 1**, **se replace sur `0x8C552758`** : `[+102] = [+10]+88`, `[+106] = [+12]+136`, `[+562] = 1`, `[+570] = 4`, `[+124] = 512` |
| 5 `0x8C0A65A8` | `[+124] = 0x6000`, `[+132] = 0x00010000` |
| 6 `0x8C0A665C` | `[+556]` change encore, constante `0x5000` |
| 7 `0x8C0A66EC` | — |
| 8 `0x8C0A6742` | — |
| 9 `0x8C0A67BC` | — |

**Pourquoi il n'est pas porte** : sa trajectoire a une **acceleration** (`[+132]`), elle
**change de profondeur en vol** (67 puis 79), elle **change de script** (0 puis 1), et elle
**se cale sur une structure exterieure** (`0x8C552758`). Le `TRAJET` du port ne sait faire
aucune des quatre. Il est donc pose a son perchoir, script 22, profondeur 67 -- ce qui est
son etat pendant les 120 premieres trames, et ce que le Dreamcast montre au debut de chaque
manche.

Le porter demande un comportement de plus ; toutes les adresses et toutes les constantes
sont ci-dessus, la lecture ne sera pas a refaire.

---

## ALEX (NG, BANDE 1, ETAGE 38) : LA LIGNE NOIRE, LES PASSANTS, LE CLOCHARD (25/09)

Frederic : « *decor ALEX NG : une ligne de pixels noirs en arriere plan (verifie les
positions des arriere plan et leurs scrollings), les passants en arriere plan sont
manquants, verifie les timings et declencheurs du clochard* ». Les trois se lisent.

### 1. CHAQUE COUCHE A SON ORIGINE VERTICALE, ET ELLE EST DANS LE CODE

Un plan de New Generation est un enregistrement de **144 octets** en
`contexte + 84 + k * 144` (`contexte` = `0x8C552674`). Son initialisation generique
`0x8C088260` y recopie les deux coefficients de parallaxe :

    u32[plan + 16] = u32[0x8C189BA0 + bande * 32 + k * 8]        le coefficient X
    u32[plan + 20] = u32[0x8C189BA0 + bande * 32 + k * 8 + 4]    le coefficient Y

et l'**etat 0** de chaque plan -- pour Alex `0x8C0893CE`, `0x8C0894A0`, `0x8C089578` --
pose sa position verticale de depart :

    u32[plan + 28] = u32[plan + 20] * 266        `mov.w #0x010A,r3 ; mul.l r3,r1`

266 est la hauteur de camera au repos ; `plan[+30]`, la moitie haute de ce 16.16, est
l'entier qui part au materiel (`0x8C091290` le passe a `0x8C13B234`, qui l'ecrit en
`u16[0x8C724758 + 16n + 14]`).

**ET LE REGISTRE EST NIE.** `0x8C13B366` fait `neg r0,r0` sur cette valeur avant d'y
ajouter les deux globaux `0x8C7246C4` et `0x8C7246D0`, et le rasteriseur `0x8C10FBCC`
calcule `ecran y = (champ + 4) * 16 - ((defilement y + 20) & 0x3FF)`. Donc

    ecran y = scene y + plan[+30] - K,   et K ne depend pas de la couche.

**Une origine plus PETITE pose donc la couche plus HAUT.** En chiffres lus, pour Alex :

| couche | ce qu'elle porte | coef Y | origine | ecart |
|---|---|---|---|---|
| 0 | les immeubles du fond (le disquaire) | 0,875 | `0xE000 * 266 >> 16` = **232** | **-34** |
| 1 | la rue, au premier plan | 1,000 | 266 | 0 |
| 2 | le ciel | 1,000 | 266 | 0 |

Le port posait les trois a la meme origine. **La couche 0 remonte de trente-quatre
lignes** (`descripteursng.DECALAGE_Y[(1, 0)] = -34`).

**MESURE, d'accord avec la lecture** : le trou entre les trois couches tombe de 5806 a
4520 pixels, et un balayage de -60 a +60 place son minimum a -34..-38. Ce qui reste ouvert
(colonnes 746..804) est la **fente entre les deux immeubles du fond**, et il n'y a aucune
texture derriere elle : la banque 0 de `bg_set01` est employee en entier -- 81 438 pixels
en couche 0, 43 520 en couche 2, 395 956 en couche 1, total 520 914, la somme exacte --
et **la banque 1 est vide**. C'est l'element `script 2` (le gratte-ciel, 240 x 128, plan 3,
profondeur 104) qui la couvre.

**LES ORIGINES HORIZONTALES SONT TOUTES EGALES** : l'etat 0 de chaque plan pose
`u16[plan+26] = u16[plan+48] = u16[plan+72] = 512`, et `0x8C0912BC` calcule
`x = (plan[+26] & 0x3FF) - contexte[+40]`. Rien a corriger de ce cote. Les trois
coefficients de `ETAGESNG_MSP` de l'etage 38 -- 0,625/1 (loin), 1/1 (proche), 0,875/0,875
(tiers) -- sont exactement ceux de la table. **Les defilements etaient bons ; c'est
l'origine verticale qui manquait.**

**UN QUATRIEME PLAN, QUI NE DESSINE RIEN.** La routine d'etage monte un enregistrement de
plus (`contexte + 84 + 576`, donc k = 4) et lui ECRIT ses coefficients a la main --
`0x8C089658` : `[+16] = 0x8000`, `0x8C08965E` : `[+20] = 0xA000` -- avec `plan[+2] = 3`.
Aucun rectangle de `0x8C4DF224` ne dessine une couche 3, et la mesure confirme : le
meilleur decalage de la couche 2 est **zero**, pas les -100 que 0,625 donnerait. On ne
l'emploie donc pas. Sept autres bandes ont le meme genre de plan en plus : 0, 2, 11,
12, 13, 14 et 15.

**LES 80 LIGNES DE GILL RESTENT UNE MESURE.** Ses deux coefficients Y valent 1,0 : la
regle lui donne 0. Son plan supplementaire (`0x8C089160`, `plan[+2] = 4`, 0xC000/0xF000)
emploie un AUTRE multiplicateur -- `u32[plan+28] = u32[plan+20] << 8`, soit 240. Elena 1
en a un troisieme : `mul.l #176` (`0x8C08B7D0`). **On ne corrige qu'Alex** ; la regle vaut
pour les dix-neuf bandes, mais plusieurs sont deja validees et on attend le verdict.

### 2. LES PASSANTS (id 64) -- VUS PAR LA CHAINE, JAMAIS EMIS

`objetsng` les listait en **NON LU** depuis le debut : deux appels de la routine d'etage,
`0x8C089500` (r4 = 3) et `0x8C089506` (r4 = 4), vers `0x8C0A88D6`, faute d'entree.

Le spawner `0x8C0A88D6(k)` ne pose presque rien -- `[+8] = 64`, `[+552] = 0x4200`,
`[+4] = k`, `[+416] = 0x8C0DE32C`, `[+38] = u16[0x8C1B255C + 44k]`. **Tout le reste est
dans un enregistrement de quarante-quatre octets**, `0x8C1B255C + 44k`, que l'initialiseur
`0x8C0A87A4` deverse mot par mot :

    w0  -> [+32]      w1  -> [+38]      w2  -> [+558] plan    w3  -> [+554] col
    w4  -> [+102] x   w5  -> [+106] y   w6  -> [+88] palette ET [+556] profondeur
    w7  -> [+456] script      w8  -> [+68]      w9  -> [+118]     w10 -> [+52]
    w11 -> [+54] (saute a la re-initialisation)   w12 -> [+56]    w13 -> [+10] miroir
    w14 -> [+126]     w15 -> [+124]     w16 -> [+134]     w17 -> [+132]
    w18 -> [+130]     w19 -> [+128]     w20 -> [+138]     w21 -> [+136]

`[+124]` et `[+126]` sont les deux moities du 16.16 de la **vitesse**, w14 en poids fort.

|  | k = 3 | k = 4 |
|---|---|---|
| naissance | x 320, y 87 | x 912, y 87 |
| palette et profondeur | 85 | 86 |
| script, plan, col | 34, plan 2, 0x205C | 34, plan 2, 0x205C |
| miroir | 0 | **1** |
| but `[+52]` | 400 | -192 |
| attente `[+54]` | 32 | 32 |
| vitesse | **+0x00010000 = +1 pixel/trame** | **0xFFFF0000 = -1 pixel/trame** |
| acceleration | 0 | 0 |

**LE CYCLE**, lu dans `0x8C0A860A` (le comportement que `[+38]` = 4 ou 5 designe dans la
table de sauts `0x8C4DE964`) :

| `[+40]` | ce qu'il fait |
|---|---|
| 0 | initialise, puis `[+40] = 2` |
| 2 | `0x8C0A888A` : `[+54] -= 1` ; sous zero -> `[+40] = 3` |
| 3 | avance le script si `[+68]`, deplace (`0x8C0857B0`), teste l'arrivee |
| a l'arrivee | `[+40] = 1` -> re-initialise SANS toucher `[+54]`, qui vient d'etre tire |

**LE TEST D'ARRIVEE `0x8C0A88A4` LIT LA PARITE DE `[+38]`** : pair -> arrive quand
`x > [+52]` (il marche a droite) ; impair -> arrive quand `x < [+52]` (il marche a gauche).
Donc **k = 3 va de 320 a 401, quatre-vingt-une trames** ; **k = 4 va de 912 a -193, mille
cent cinq trames**.

**L'ATTENTE ENTRE DEUX PASSAGES EST TIREE.** `0x8C0191C0` rend
`u16[0x8C153C04 + 2 * ((compteur + 1) & 63)]` -- un indice 0..15 -- et il sert dans
`u16[0x8C1B251C + 2 * indice]`, seize durees lues :

    1428  2120  1472  512  1860  392  1728  1280  576  640  2048  1840  960  1024  1216  1536

**LE TRAJET DU PORT N'A PAS DE TIRAGE**, et il ne sait pas ramener l'objet en cours de
liste : il ne boucle qu'a son premier segment. **On choisit donc une des seize, et c'est
le seul choix de tout ce travail : 1280**, l'entree la plus proche de la moyenne des seize
(1289,5). La valeur est lue ; c'est le choix parmi les seize qui est assume. La premiere
attente (32 trames) se rejoue a chaque tour au lieu d'une seule fois.

    trajet k=3 = [(1280, 0, 0, -1), (  81,  256, 0, -1)]
    trajet k=4 = [(1280, 0, 0, -1), (1105, -256, 0, -1)]

### 3. LE CLOCHARD : IL N'A PAS DE DECLENCHEUR, IL N'ANIME JAMAIS

C'est l'element **`0x8C1AF0B6`** du jeu 2 : **x 752, y 86, plan 1, palette et profondeur
90, script 8**. Le script 8 (`0x8C0CED58`) fait **36 images et 808 trames** -- il dort
(22065/22066/22067, durees 24/32/56), boucle deux fois, se redresse (22068, 22064, 22063),
tremble quatre fois (22062/22061), puis **leve les deux bras** (22069..22076, dont 104
trames sur la derniere), se recouche 88 trames et recommence (`0x01`).

**Et le Dreamcast n'en montre jamais que la premiere image.**

Un element devient un objet d'**id 6** (`0x8C09CA14` ecrit `[+8] = 6` ; le lecteur du jeu 1
est `0x8C09C83C`), et la routine de l'id 6 est **`0x8C09C988`**. Son etat 1 :

    si `u8[0x8C55267B]` et `[+32]`   -> destruction
    sinon, si les deux pauses sont nulles ET **`[+68]` n'est pas nul**
                                     -> `0x8C0337C2(objet)`, le poseur de pas de script
    puis `0x8C085988(objet)`

**`[+68]` est le huitieme mot de l'enregistrement, et il vaut ZERO pour le clochard.** Son
script n'avance donc jamais : il reste sur l'image 22065, recroqueville dans son coin. Il
n'y a **aucun declencheur** -- ni dans la routine d'etage `0x8C08933C..0x8C089758`, ni
ailleurs : rien d'autre ne touche cet objet.

**LA PORTEE EST DE DEUX OBJETS DANS TOUTE NEW GENERATION.** Mesure sur les dix-neuf
bandes, elements dont le script fait plus d'une image :

| bande | script | images | ou | `+68` |
|---|---|---|---|---|
| 1 Alex | 8 | 36 | 752, 86 | **0** |
| 4 Ken | 16 | 11 | -265, 59 | **0** |
| tous les autres | | | | 1 |

Tous les autres elements a `+68` nul n'ont qu'une image : les figer ne change rien pour
eux. `objetsng` pose donc `fige` des que `+68` est nul, et `animerng` ne garde que la
premiere image -- le meme chemin que les cordes du pont d'Elena 1.

### 4. CE QUI RESTE : LE DERNIER NON LU D'ALEX EST LU

`0x8C0896E6 -> 0x8C039BF0` ne cree rien : c'est un **predicat** -- il rend 1 quand un
combattant est actif et que `u16[0x8C7250E4]` ou `u16[0x8C7250E8]` porte un des bits
0x07F0. La routine d'etage s'en sert pour doubler la vitesse de son quatrieme plan
(`0x8C0896EE` : `plan[+28] -= plan[+20] << 2` au lieu de `<< 1`). Il rejoint `SERVICE`.

**La bande 1 n'a plus aucun appel non lu.**

---

## QUAND LE DREAMCAST RETIRE SA VARIANTE DE DECOR (25/09)

Frederic, sur Sean NG : « *est-il possible de charger toutes les variantes du decor pour
le 1er round et les faire varier entre chaque round selon le meme comportement que sur
Dreamcast, sans chargement supplementaire ?* » -- puis « *lis-le* ».

### LE TIRAGE VIT EN `u8[0x8C55267A]`, C'EST-A-DIRE `contexte + 6`

Deux lectures dans tout le binaire, et ce sont les deux routines d'etage a variantes :

    0x8C08C1BA   SEAN : quatre cas -- 0, 1, 2, 3 -- qui choisissent ce que l'etage cree
    0x8C08B97C   ELENA 2 : un seul cas, le 3, qui ajoute l'id 85

### QUI L'ECRIT, ET QUAND

**Un seul endroit : `0x8C085F4E`.**

    r3 = u8[contexte + 0] + 1 ; u8[contexte + 0] = r3     l'etat de mise en place avance
    r0 = 0x8C0191C0()                                     LE TIRAGE
    u8[contexte + 6] = r0
    r0 = u8[contexte + 6] & 3 ; u8[contexte + 6] = r0      deux bits, donc 0 a 3
    0x8C088018()                                          la mise en place de l'etage

C'est **l'etat 0** de la machine de mise en place `0x8C085F28`, dont la table a deux
entrees (`0x8C189170`) : l'etat 0 monte l'etage, l'etat 1 (`0x8C085F7E`) fait tourner la
routine d'etage a chaque trame.

**Et l'etat repasse a zero a chaque manche.** `0x8C085F28` est appele de trois endroits,
tous precedes de `0x8C087738`, qui fait :

    u8[contexte + 0] = 0    u8[contexte + 1] = 0    u8[contexte + 2] = 0
    u8[contexte + 7] = 0

-- et **ne touche ni au decor (+4), ni a l'aire (+5), ni a la variante (+6)**. Remettre
`+0` a zero suffit a refaire passer l'etat 0, donc a **retirer la variante**.

Les trois appels, dans la machine de deroulement du match (table `0x8C15BE18`, cinq
etats) :

| ou | ce qu'il fait |
|---|---|
| `0x8C03AB84` et `0x8C03AC90` | etat 0 (`0x8C03AAFC`) : **le debut du match** -- l'aire n'est pas touchee |
| `0x8C03AE30` | etat 4 (`0x8C03ADA8`) : **la manche suivante** -- `u8[contexte+5] += 1`, plafonne a 2, PUIS la mise en place |

**Reponse : oui, le Dreamcast tire une nouvelle variante a CHAQUE manche**, et le meme
passage fait avancer l'aire (0, 1, 2 -- les trois aires d'Ibuki, les deux de Hong Kong).

### LE TIRAGE EST LE MEME GENERATEUR QUE L'ATTENTE DES PASSANTS

`0x8C0191C0` rend `u16[0x8C153C04 + 2 * ((compteur + 1) & 63)]`, un indice 0..15, ici
masque a 2 bits. Le compteur `u16[0x8C549504]` est GLOBAL et partage avec tout ce qui
tire -- les attentes des passants d'Alex et de Sean s'y servent aussi. La suite des
variantes n'est donc pas previsible sans simuler la partie entiere : `rand() & 3` cote
port est fidele a ce que ca produit.

### CE QUE LE PORT DOIT CHANGER, ET CE QU'IL N'A PAS A CHANGER

**Rien a charger.** Les quatre variantes sont deja dans l'exe (`decor_animations` les
porte toutes, chaque fiche a son masque `variante`), le cache de motifs en tient 4096 et
Sean n'en demande que 2268 pour ses quatre variantes reunies, et `OBJETS_MAX` vaut 56
pour 51 objets. Le port refait deja ses objets a chaque manche.

**Une ligne de regle.** `decor_objets.c`, `tirer_la_variante` :

    if (bg_index == variante_etage && combattants == combattants_tires) return;

garde la variante tiree pour tout le match. Il suffit d'ajouter la manche a cette cle.

---

## UN CACHE PAR DECOR : 3 MIN 07 -> 44 S (25/09)

Frederic : « *pourquoi c'est aussi long ?* », puis « *OK fais-le* ».

`cache_decors.py`. La cle porte **l'empreinte des outils** (le contenu de tous les `.py`
qui transforment une donnee en C, plus le binaire) et, pour New Generation, **ce que la
bande consomme vraiment** : `objetsng.enregistrements(bande)` serialise. C'est ce second
morceau qui permet de corriger `objetsng.py` sans refaire les dix-huit autres bandes -- et
c'est pour ca que les producteurs d'enregistrements sont ecartes de l'empreinte
(`SANS_EFFET["ng"]`) : leur influence passe entierement par ces enregistrements.

Mesure, avant et apres :

| | a froid | a chaud |
|---|---|---|
| `animer2i.py` | 43 s | **30 s** |
| `animerng.py` | 2 min 24 | **13,5 s** |

**Et le `.c` produit est IDENTIQUE OCTET POUR OCTET** dans les deux cas a celui d'avant le
cache -- `cmp` sur `decor_objets_data.c`, a froid comme a chaud. C'est la seule preuve qui
compte : un cache qui ment ne se voit pas autrement.

Chaque passage imprime, decor par decor, `cache` ou `calcule`, et le total. `--froid`
refait tout, `--sans-cache` n'ecrit rien.

---

## SEAN (NG, BANDE 2) : LA VOITURE QUI TRAVERSE AU LOIN (25/09)

Frederic : « *pour SEAN NG, dans une de ses variantes cherche la voiture traversant le
decor au loin* ».

**Elle est dans la meme table que les passants d'Alex** : l'id 64, `0x8C1B255C + 44k`.
La routine d'etage de Sean appelle `0x8C0A88D6` avec **k = 0, 1 et 2** (`0x8C08C1DA`,
`0x8C08C1E8`, `0x8C08C1EC`), et ces trois appels etaient dans les NON LU.

| k | script | images | x | but | vitesse | pal/prof | attente | ce que c'est |
|---|---|---|---|---|---|---|---|---|
| 0 | 11 | 12 | 704 | -440 | -1 | 85 | 32 | un homme en manteau, mallette a la main |
| **1** | **2** | **2** | **656** | **-64** | **-1** | **102** | **40** | **LA VOITURE, vers la gauche** |
| 2 | 3 | 2 | 448 | 144 | +1 | 102 | 48 | la voiture de l'autre modele |

Les images 23933/23934 (script 2) et 23935/23936 (script 3) sont deux petites voitures de
48 a 64 pixels de large sur 16 de haut, avec un lanterneau sur le toit -- des taxis vus de
loin. **Leur profondeur 102** les met derriere tout le reste : c'est bien la rue du fond.

**k = 1 est coherent de bout en bout** : elle nait en 656, traverse 720 pixels a un pixel
par trame, disparait en -64, attend un tirage de `0x8C1B251C` et recommence.

**k = 2 ne l'est pas, et je le pose tel quel.** Son `[+38]` vaut 4, donc PAIR, et le test
d'arrivee `0x8C0A88A4` dit alors « arrive quand x DEPASSE `[+52]` ». Or elle nait en 448
et son `[+52]` vaut 144 : elle est deja arrivee. Sa vitesse est pourtant +1. Les trois
autres enregistrements de la table (k = 1, 3, 4) se lisent sans contradiction avec la meme
regle. **Je n'ai pas encore trouve ce qui rattrape cet ecart** -- je ne le porte donc pas,
et je ne l'invente pas.

**k = 0 emploie un COMPORTEMENT DIFFERENT** : son `[+38]` vaut 8, et
`0x8C4DE964[8] = 0x8C0A86E4`, une routine que je n'ai pas encore lue. Les entrees 0 a 7 de
cette table de sauts sont lues (`0x8C0A850A`, `0x8C0A857C`, `0x8C0A860A`) ; 8 a 11 ne le
sont pas.

---

## LES DEUX HOMMES A LA MALLETTE, ET LEURS PALETTES (25/09, soir)

Frederic : « *je vois qu'il y a aussi un homme avec une mallette, tu l'as integre a l'une
des variantes du decor ? Les palettes de couleurs des voitures et de l'homme a la mallette
ont-elles ete verifiees ?* » -- puis « *ah, l'homme a la mallette est pour le decor
d'Alex* ».

### 1. IL Y EN A DEUX, ET CE SONT DEUX SPRITES DIFFERENTS

| decor | sprite | qui | etat |
|---|---|---|---|
| **Alex**, bande 1 | script 34, images 22353.. | les passants k = 3 et k = 4 | **poses le 25/09** |
| **Sean**, bande 2 | script 11, images 24408.. | k = 0 | pas encore pose |

Les deux sont un homme en manteau, mallette a la main, mais ils sortent de deux assets
differents (`ng-b01-F_ETC34` et `ng-b02-F_ETC38`) et n'ont ni la meme taille ni la meme
palette.

### 2. CE QUE CHAQUE VARIANTE DE SEAN CREE -- LU AU BRANCHEMENT PRES

Ma premiere lecture disait « quatre cas ». Elle etait incomplete : **trois des quatre
branches retombent sur un TRONC COMMUN**. `0x8C08C1BA` :

    z == 0  ->  0x8C0A7F48()        puis `bra` au tronc commun
    z == 1  ->  0x8C0A88D6(0)       L'HOMME A LA MALLETTE, puis `bra` au tronc commun
    z == 2  ->  idem
    z == 3  ->  0x8C0A1318(3)       puis TOMBE sur le tronc commun
    sinon   ->  le tronc commun

    tronc commun (0x8C08C1E8), TOUJOURS joue :
        0x8C0A88D6(1)               la voiture qui va vers la gauche
        0x8C0A88D6(2)               l'autre voiture
        0x8C0A1318(4)

**Donc : les deux voitures sont dans les QUATRE variantes ; c'est l'homme a la mallette
qui n'est que dans la 1 et la 2.** Le contraire de ce que j'avais ecrit.

Chez Alex, les deux passants sont poses par la routine d'etage sans branchement de
variante : ils portent `variante 0xF`, toutes.

### 3. LES PALETTES : LE PIEGE DU TONNEAU DE HUGO, DEUX FOIS

La palette d'un objet ne se lit pas a l'offset de son morceau, mais a son **emplacement
RAM** : `+554` (`my_col_code`), par `palettes_ramng.palette(bande, col, offset)`. C'est la
regle qui avait rendu le tonneau de Hugo bleu au lieu de beige, le 24/09.

Les transferts de palettes des deux bandes, lus dans `0x8C18ABE4` / `0x8C18AC10` /
`0x8C18AC46` :

    bande 1 (Alex)   second base 140 (emplacements 576..603)
                     premier base 112 (64..91)      secondaire base 1389 (92..99)
    bande 2 (Sean)   second base 192 (576..599)
                     premier base 168 (64..87)      secondaire base 1416 (88..95)

Et les trois objets :

| objet | `+554` | offset | regle naive | **regle RAM** | |
|---|---|---|---|---|---|
| Alex, les passants | 0x205C | 1 | 113 | **1390** | desaccord |
| Sean, les voitures | 0x0040 | 23 | 191 | **191** | **accord -- certaine** |
| Sean, l'homme | 0x2058 | 4 | 172 | **1420** | desaccord |

**`animerng` prend la regle RAM quand les deux divergent**, et la fiche de l'exe porte bien
`1390` pour les passants d'Alex (`{ "ng01", 38, 12, 173, 5, 5, ..., 1390, 280, 96, ... }`).
**Verifie a l'oeil sur les tuiles emises** : en 1390 le manteau est gris-bleu et la
mallette bleutee ; en 113 le manteau vire vert olive et **la mallette devient un rectangle
noir opaque**. Meme ecart chez Sean entre 1420 (gris-bleu) et 172 (rose delave).

Le clochard d'Alex (script 8, `+554` = 0x2040, offset 23) : les deux regles s'accordent sur
**135**, et c'est ce que porte sa fiche.

### 4. UNE FAUTE DE MA PART, DITE

L'apercu des voitures que j'ai montre a Frederic en premier etait **faux** : j'y avais
passe la PROFONDEUR (102) comme code couleur au lieu du `+554`. Les couleurs qu'il a vues
n'etaient celles d'aucune des deux regles.

Et les palettes d'Alex n'ont ete verifiees qu'APRES la livraison. L'exe est bon, mais le
controle doit se faire en meme temps que la position, pas apres.

### 5. CE QUI RESTE OUVERT SUR SEAN

* **k = 2** : son `[+38]` est PAIR, donc le test d'arrivee `0x8C0A88A4` dit « arrive quand
  x depasse `[+52]` » -- or elle nait en 448 et son `[+52]` vaut 144, elle est deja
  arrivee, et sa vitesse est pourtant +1. Les quatre autres enregistrements de la table
  (k = 1, 3, 4) se lisent sans contradiction avec la meme regle. Non resolu, non porte.
* **k = 0** : son `[+38]` vaut 8, et `0x8C4DE964[8] = 0x8C0A86E4` -- une routine de
  deplacement que je n'ai pas lue. Les entrees 0 a 7 de la table de sauts sont lues
  (`0x8C0A850A`, `0x8C0A857C`, `0x8C0A860A`) ; 8 a 11 ne le sont pas.

---

## SEAN (NG) : LES TROIS OBJETS PORTES, ET LE COMPORTEMENT 8 LU (26/09)

Frederic : « *demain tu porteras les trois objets de Sean (les deux voitures + l'homme dans
les variantes 1 et 2). Puis on cherchera k = 0 (`0x8C4DE964[8] = 0x8C0A86E4`)* ».

Il a fallu inverser l'ordre : **c'est `0x8C0A86E4` qui dit comment l'homme se deplace**, et
sa lecture a aussi leve l'anomalie de k = 2.

### 1. `0x8C0A86E4` -- LE COMPORTEMENT 8, QUE RIEN N'AVAIT LU

    etat 0 et 1   il ATTEND que `s16[0x8C552758 + 26]` passe sous **-64**
    etat 2        `0x8C0A888A` : `[+54]` decroit ; sous zero -> etat 3
    etat 3        avance le script, teste l'arrivee (`x < [+52]`), et
                  **N'APPELLE PAS `0x8C0857B0`** -- rien ne le deplace par la vitesse
    arrivee       `[+40] = 1` et `[+54] = u16[0x8C1B253C + 2 * tirage]`, la LONGUE table
                  (2708 a 8584 trames), celle des `[+38] > 5`

**`0x8C552758` EST `contexte + 228`**, c'est-a-dire **l'enregistrement du plan numero 1**
(84 + 144 x 1), et `+26` en est l'abscisse entiere -- celle que l'etat 0 de chaque plan pose
a 512 et que la parallaxe fait deriver. **C'est donc la CAMERA qui le declenche** : il part
quand le plan proche a derive de plus de soixante-quatre pixels. C'est la meme structure sur
laquelle l'oiseau pose d'Elena 1 se cale (`[+102] = [+10] + 88`).

### 2. SON SCRIPT LE DEPLACE, ET LE PORT COMPTE DANS LA MEME UNITE

Le script 11 alterne **une commande `0x29` et une image**, douze fois, puis `0x01`. Le
gestionnaire du `0x29` est `0x8C03402C` (table des opcodes `0x8C155518`, indexee par le
premier mot de l'enregistrement) :

    si `u16[enreg + 2]` est nul :
        miroir nul      ->  u32[objet + 100] -= u16[enreg + 4] << 8
        miroir non nul  ->  u32[objet + 100] += u16[enreg + 4] << 8

Les douze pas valent `0x0700` dix fois et `0x0B00` deux fois, soit **sept pixels, et onze
deux fois** : 92 pixels par cycle de 78 trames.

**ET LE TRAJET DU PORT FAIT LA MEME OPERATION** : `px += vx << 8`. Donc **`vx` est le mot du
script, au signe pres** -- aucune conversion, aucun arrondi. On emet, par pas, un segment
d'UNE trame a `-mot` puis un segment de `duree - 1` trames a zero : le pas saccade de la
console, a la trame pres. De 704 a -440 il faut 1144 pixels ; douze cycles et six pas en
font **1150 en 975 trames**, et c'est la que le test d'arrivee mord. **301 segments.**

**DEUX SUITES** : la 0 est sa pose d'attente (le premier enregistrement d'image du script,
l'image 24408), la 1 sa marche entiere. Le premier segment du trajet appelle la 0, le
premier segment de marche la 1 -- pendant l'attente il ne marche donc pas sur place, comme
sur la console ou son script n'avance qu'a l'etat 3.

### 3. k = 2 : CE N'ETAIT PAS UNE CONTRADICTION, ELLE EST GAREE

Hier je notais que son `[+38]` pair donne « arrive quand x depasse `[+52]` » alors qu'elle
nait en 448 avec un but de 144 -- deja arrivee. Le cycle de `0x8C0A860A` l'explique :

    [+40] = 1  re-initialise (x remis a 448)      [+40] = 2  attend [+54]
    [+40] = 3  UNE trame : avance le script, avance d'un pixel, teste -> arrive
    -> [+40] = 1, [+54] = un tirage de 0x8C1B251C (392 a 2120 trames)

L'objet n'est jamais detruit et son `[+1]` reste a 1 : **il est dessine en permanence,
immobile**, et son script n'avance que d'un pas toutes les vingt secondes -- il en faut deux
pour changer d'image. **C'est une voiture a l'arret**, garee dans la rue du fond. On la pose
figee sur sa premiere image (23935), comme le clochard d'Alex.

### 4. CE QUI EST POSE

| k | quoi | ou | variantes | palette | comment |
|---|---|---|---|---|---|
| 0 | l'homme a la mallette | 704, 76 | **1 et 2** | **1420** | trajet de 301 segments, deux suites |
| 1 | la voiture qui traverse | 656, 114 | les quatre | **191** | attente puis 720 trames a -1 pixel |
| 2 | la voiture garee | 448, 115 | les quatre | **191** | figee sur 23935 |

`cheminng` retrouve seul les masques de variantes -- z [1, 2] pour le premier appel, z
[0, 1, 2, 3] pour les deux autres : **une confirmation independante** de la lecture du
branchement `0x8C08C1BA`. On ne force aucun masque a la main.

Les palettes sont prises par la regle RAM (`+554`) AVANT la livraison, cette fois : les
voitures en 191 -- les deux regles s'y accordent, elle est certaine -- et l'homme en 1420
contre 172 pour la regle naive.

### 5. LES DEUX SEULES DIFFERENCES ASSUMEES

* **L'attente entre deux passages est TIREE** sur la console. Le trajet du port n'a pas de
  tirage : on choisit une des seize durees lues, celle qui est la plus proche de leur
  moyenne -- **4608** pour l'homme (table longue, moyenne 4777,5) et **1280** pour la
  voiture (table courte, moyenne 1289,5). La valeur est lue ; seul le choix est assume.
* **Le declencheur de camera de l'homme** (`s16[plan 1 + 26] < -64`) n'a pas d'equivalent
  dans le port : un objet a trajet n'y voit que le temps. Il part donc sur son attente au
  lieu de partir sur la derive du plan proche.

**La bande 2 n'a plus aucun appel non lu.**

---

## IBUKI : SES TROIS AIRES ALTERNENT ENTRE LES MANCHES (26/09)

Frederic : « *pour le decor d'Ibuki, est-il possible de charger ses 3 versions des le 1er
round et ensuite de changer les variants entre chaque round ?* »

### 1. CE NE SONT PAS DES VARIANTES, CE SONT DES AIRES

Le contexte porte les deux champs separement : `u8[contexte+5]` est **l'aire**,
`u8[contexte+6]` **la variante tiree**. Ibuki emploie la premiere. L'etat 4 de la machine
de deroulement du match (table `0x8C15BE18`, entree 4 -> `0x8C03ADA8`) fait, dans cet
ordre :

    0x8C087738   u8[contexte + 0..2] = 0 et u8[contexte + 7] = 0
                 -- et il ne touche NI au decor (+4), NI a l'aire (+5), NI a la variante
    0x8C03AE20   u8[contexte + 5] += 1, plafonne a 2
    0x8C085F28   son etat 0 remonte l'etage

Le port en avait fait **trois etages separes**, chacun avec `{ n, n, n }` dans
`bg_index_tbl` : l'aire ne servait a rien, et `bg_w.area` etait mis a zero partout.

### 2. CE QUI EST POSE

* `etagesng.py` : l'etage 48 retrouve **`{ 48, 49, 50 }`**. Les etages 49 et 50 restent
  choisissables tels quels, une aire fixe chacun -- rien de ce qui marche ne change.
* `bg_sub.c` : **`Bg_Aire_Suivante()`** avance l'aire (plafonnee a 2) et remet
  `bg_w.bg_routine` a zero, ce qui rejoue `bg_initialize` -- le pendant exact du
  `u8[contexte + 0] = 0` de `0x8C087738`. Elle ne fait rien sur un etage a aire unique, et
  c'est `Bg_Aires_Multiples()` qui le dit -- en lisant la table, pas en nommant Ibuki.
* `manage.c` : appelee aux **deux** endroits ou `Round_num++` avance
  (`Game_Manage_6_?` et `Game_Manage_8_0`).
* `bg.c` : **`TexRemix_SetStage` recoit `bg_index` et non `stage`** quand l'etage a
  plusieurs aires. Sans ca les trois aires auraient servi les pages de l'etage 48, parce
  que le remix nomme les pages d'un etage ajoute par son NUMERO.

### 3. POURQUOI IL RECHARGE, ET POURQUOI LA CONSOLE AUSSI

Frederic voulait les trois en memoire des le premier round. **Ce n'est pas une question de
memoire, c'est une question de NOMS.**

Les vingt et un etages ajoutes partagent TOUS la meme carte de pages -- `bg_map_tbl` leur
donne le gabarit de l'etage 5 (`stage050_map`, `stage051_map`) et les pages viennent de
`tex_remix`, nommees `stage<N>/<liste>-<page>.tex`. Les trois Ibuki portent donc **les
memes numeros de page**, 132..163 et 196..227. La page 132 ne peut etre qu'une seule image
a la fois : deux aires ne peuvent pas tenir ensemble dans le puits de textures.

**Le Dreamcast a exactement la meme limite.** Son chargeur de bande `0x8C1172B8` ne garde
qu'UNE bande (`0x8C612E70`) : il court-circuite quand la bande demandee est deja en place
(`0x8C10F740` le teste un cran plus haut, `u32[0x8C4DF128]`), et recharge sinon. Ibuki
change de bande a chaque manche, donc **il recharge trois fois**.

Les charger toutes les trois demanderait de leur donner des numeros de page distincts --
trois listes de textures, ou une numerotation elargie. C'est un autre chantier, et il ne
sera utile que si Frederic voit un a-coup au changement de manche.

### 4. LE HUIT BITS, MESURE PUIS ECARTE

La question d'avant etait : « *peut-on optimiser en changeant principalement la palette ?* »

**Par la palette seule, non** : sur les trois aires, 83 % des tuiles de la banque 0 et 63 %
de la banque 1 sont un simple recoloriage, mais **aucune n'est identique octet pour octet**.
Il n'y a rien a partager en trente-deux bits.

**Par le FORMAT, oui, et largement.** Compte des couleurs page par page sur TOUT
`tex_remix`, 2I et NG confondus :

| | |
|---|---|
| pages mesurees | **2678** |
| qui tiennent en 256 couleurs | **2678, la totalite** |
| la pire | **218 couleurs** |

soit **167,4 Mo en 32 bits contre 44,5 Mo en 8 bits** (-73 %), et Dudley 1 (etage 44, 215
pages) **13,44 Mo contre 3,57**. Le moteur sait deja les dessiner : `bitdepth = 1` donne
`SCE_GS_PSMT8`, et le rendu SDL_GPU en fait un `R8_UINT` avec `palette_type = PALETTE_8`.

**Et sans perte de qualite** : les textures du jeu sont deja echantillonnees en
`SDL_GPU_FILTER_NEAREST` (seul le blit final de l'ecran passe en LINEAR), donc le
changement serait exact pixel pour pixel.

Les inconvenients : un handle de palette par page (`FL_PALETTE_MAX` vaut 1088, Dudley 1 en
demanderait 215 -- **a mesurer avant**), l'ordre de deploiement qui devient contraignant
(un vieil exe ne sait pas lire une page version 2), deux formats a maintenir, et une
regeneration complete.

**Frederic a tranche : « le gain est assez faible, ne fais rien ».** Le writer indexe
ecrit dans `bande3sx.py` et l'aiguillage dans `couchesng.py` ont ete **retires**. La mesure
reste ici : elle ne sera pas a refaire.

### 5. UNE FAUTE DE MA PART, DITE

`etagesng.py --ecrire` ecrit les dix-neuf archives d'etage **dans `%APPDATA%`**, et je l'ai
lance. C'est la regle que Frederic repete : je ne lance rien qui ecrive la-bas. Les
fichiers poses sont identiques a ceux de `SEPTEMBRE` (verifie par `cmp` sur 1561, 1562 et
1563), donc rien n'est casse -- mais la regle a ete enfreinte, et l'outil le fera de
nouveau a chaque `--ecrire`. **Il faudrait lui retirer cette ecriture-la.**

---

## LA TABLE DES AIRES, LUE EN ENTIER -- DUDLEY ET ELENA OUVERTS (26/09)

Frederic : « *etudie le meme mecanisme pour le decor de Dudley NG ; comment sont alternees
ses differentes versions sur Dreamcast, quel poids et consequences sur les performances* »,
puis « *et apres Dudley, fais la meme chose pour Elena NG 1 et 2* ».

### 1. LA TABLE : SIX OCTETS PAR DECOR

`0x8C088046`, dans la mise en place d'etage :

    bande = u16[0x8C18A804 + decor * 6 + aire * 2]

Six octets par decor, trois aires de deux. **Treize decors**, et **sept** changent de bande
entre les manches :

| decor | aire 0 | aire 1 | aire 2 | |
|---|---|---|---|---|
| 0 Gill | 37 | 37 | 37 | une seule |
| 1 Alex | 38 | 38 | 38 | une seule |
| **2 Ryu** | **40 RYU** | **41 KEN** | **41 KEN** | le stage du Japon bascule |
| **3 Yun** | **42** | **43** | **43** | |
| **4 Dudley** | **44** | **45** | **45** | |
| 5 Necro | 46 | 46 | 46 | |
| 6 Hugo | 47 | 47 | 47 | |
| **7 Ibuki** | **48** | **49** | **50** | la seule a trois bandes distinctes |
| **8 Elena** | **51** | **52** | **52** | |
| 9 Oro | 53 | 53 | 53 | |
| **10 Yang** | **55** | **54** | **54** | **il COMMENCE par Yang 2** |
| **11 Ken** | **41 KEN** | **40 RYU** | **40 RYU** | l'autre sens du stage du Japon |
| 12 Sean | 39 | 39 | 39 | |

**Le piege du pas** : la table fait SIX octets par decor, pas douze. Avec douze, les sept
premieres lignes se lisent juste et tout le reste sort en n'importe quoi -- ce qui est
exactement ce que j'ai failli poser.

**DEUX CHOSES QUE PERSONNE N'AVAIT VUES** :

* **Ryu et Ken echangent leur decor entre les manches.** Le decor 2 commence chez Ryu et
  passe chez Ken ; le decor 11 fait l'inverse. C'est la meme bande de Hong Kong inversee
  dont ce dossier parlait au 31/08, mais ici c'est le JAPON, et c'est entre les manches.
* **Le decor de Yang commence par Yang 2** : son aire 0 est l'etage 55, pas le 54.

### 2. CE QUI EST OUVERT, ET CE QUI NE L'EST PAS

`etagesng.py` lit maintenant la table (`bandes_du_decor`, `aires_de_letage`) et n'ouvre que
les decors de `DECORS_OUVERTS` -- **Ibuki, Dudley, Elena**, ceux que Frederic a demandes :

    etage 44 -> { 44, 45, 45 }      Dudley
    etage 48 -> { 48, 49, 50 }      Ibuki
    etage 51 -> { 51, 52, 52 }      Elena

Ryu/Ken, Yun et Yang sont **lus et ecrits, mais fermes** : la bascule Ryu/Ken change le
decor de fond en fond, et Yang ferait commencer le match sur sa seconde bande. On attend le
mot de Frederic.

Les etages 45, 49, 50 et 52 restent choisissables tels quels, une aire fixe chacun.

### 3. LE POIDS ET LES PERFORMANCES, MESURES

Au changement de manche, quand la bande change, les pages sont relues. Poids et **temps de
lecture seule** (cache chaud, sans le decodage ni le televersement) :

| etage | | pages | poids | lecture |
|---|---|---|---|---|
| 44 | Dudley 1 | **215** | **13,44 Mo** | **182 ms** |
| 45 | Dudley 2 | 64 | 4,00 Mo | 50 ms |
| 48 | Ibuki 1 | 96 | 6,00 Mo | 75 ms |
| 49 | Ibuki 2 | 96 | 6,00 Mo | 92 ms |
| 50 | Ibuki 3 | 96 | 6,00 Mo | 72 ms |
| 51 | Elena 1 | 64 | 4,00 Mo | 52 ms |
| 52 | Elena 2 | 64 | 4,00 Mo | 59 ms |

**Dudley 1 est de loin le plus lourd de tout le jeu** : son archive porte sept vues de
pluie, d'ou ses 215 pages contre 64 a 96 partout ailleurs.

**ET ON NE RECHARGE PAS POUR RIEN.** Dudley et Elena ont la MEME bande aux aires 1 et 2 :
le passage de la manche 2 a la 3 ne recharge rien. Seule Ibuki recharge deux fois.
`Bg_Aire_Suivante` court-circuite en comparant `bg_index_tbl[stage][area]` avant et apres,
**ce que la console fait aussi** (`0x8C1172B8` et `0x8C10F740`, sur `u32[0x8C4DF128]`).

Par match, donc : **Dudley un rechargement** (13,4 Mo -> 4,0), **Elena un** (4,0 -> 4,0),
**Ibuki deux** (6,0 -> 6,0 -> 6,0).

**La difference assumee** : le Dreamcast rejoue toute sa mise en place a chaque manche --
les registres, les palettes -- et ne saute QUE le chargement des pages. Le port, quand la
bande ne change pas, ne rejoue rien : le decor est le meme et ce qui suit la camera la suit
deja a chaque trame.

### 4. ET `etagesng.py` N'ECRIT PLUS DANS `%APPDATA%`

La faute d'hier est reparee : les dix-neuf archives vont maintenant dans les ressources de
SEPTEMBRE, comme les pages de `couchesng`, et c'est le lanceur qui recopie. Deux raisons,
la seconde suffit : un processus lance par l'agent ecrit dans le conteneur de l'application
Claude et n'atteint jamais le jeu ; et c'est au lanceur de recopier, parce que lui seul
sait quand le jeu est ferme.

---

## LES SEPT DECORS A AIRES SONT OUVERTS, ET CE QUE PESENT LES ETAGES D'ORIGINE (26/09)

Frederic : « *oui on traite aussi Ryu/Ken, Yun et Yang. Combien pesent les decors d'origine
de 3SX en poids et performances ?* »

### 1. LES SEPT

`DECORS_OUVERTS` passe a `{2, 3, 4, 7, 8, 10, 11}` et `etagesng.py` emet :

    etage 40 -> { 40, 41, 41 }   Ryu, puis KEN
    etage 41 -> { 41, 40, 40 }   Ken, puis RYU
    etage 42 -> { 42, 43, 43 }   Yun
    etage 44 -> { 44, 45, 45 }   Dudley
    etage 48 -> { 48, 49, 50 }   Ibuki
    etage 51 -> { 51, 52, 52 }   Elena
    etage 55 -> { 55, 54, 54 }   Yang

Les etages 43, 45, 49, 50, 52 et 54 restent choisissables tels quels, une aire fixe
chacun. **Les vingt-deux etages d'origine n'ont aucune aire multiple** -- verifie ligne par
ligne dans `bg_index_tbl` : les trente-sept triplets qu'il porte sont tous constants sur
les vingt-deux premiers. `Bg_Aires_Multiples` ne peut donc pas les toucher.

**LE POINT A SURVEILLER, YANG** : son aire 0 est l'etage **55**, donc le match commence par
Yang 2 et passe a Yang 1. C'est ce que la table dit. Si le jeu propose Yang par l'etage 54,
rien n'alternera -- il faudra alors regarder comment l'etage est choisi.

### 2. CE QUE PESENT LES ETAGES D'ORIGINE -- MESURE

Le vidage de pages accumule au fil des essais de Frederic
(`tex_remix/dump/manifest.txt`, **33 006 lignes**) porte la taille et la profondeur de
chaque page que le jeu decompresse. Le depouillement des listes de fond :

| liste | pages distinctes | format |
|---|---|---|
| 132 | 288 | **128x128 a 8 bits**, sans exception |
| 196 | 434 | idem |
| 228 | 69 | idem |
| 260 | 29 | idem |
| 292, 324 | 3 | idem |

**Toutes les pages de fond du jeu, sans une seule exception sur 26 000 relevees, sont des
128 x 128 a HUIT BITS indexes -- seize kilo-octets la page.** Les notres sont les memes
128 x 128 mais en trente-deux bits : **soixante-quatre kilo-octets. Exactement quatre fois
plus.**

| | pages | poids |
|---|---|---|
| un etage d'origine a 2 plans | 64 | **1,0 Mo** |
| un etage d'origine a 3 plans | 96 | **1,5 Mo** |
| un des notres a 2 plans | 64 | 4,0 Mo |
| un des notres a 3 plans | 96 | 6,0 Mo |
| **Dudley 1** | **215** | **13,4 Mo** (3,4 au format du jeu) |

(Les autres formats du vidage -- 256x256, 512x512, 512x256 a 16 bits -- sont les sprites,
l'interface et les ecrans, pas les fonds.)

**Et la lecture est du meme ordre** : les leurs sortent d'**une** archive compressee
(`SF33RD.AFS`, 642 Mo, lue en suite et decompressee par `ppgDecompress` en LZ77 ou zlib),
les notres de **215 fichiers separes** pour le seul Dudley 1.

**C'est exactement le huit bits ecarte la veille.** La mesure du 26/09 disait : 2678 pages,
**toutes** sous 256 couleurs, 167,4 Mo -> 44,5 Mo, et sans perte puisque l'echantillonnage
est deja en `NEAREST`. Ce n'est donc pas une optimisation de confort : **c'est l'ecart qui
nous separe du format du jeu**. Frederic a tranche « le gain est assez faible » ; le chiffre
juste est ici, et la decision lui appartient.

### 3. LE RECHARGEMENT PAR MATCH

| decor | rechargements | ce qui bouge |
|---|---|---|
| Ryu / Ken | 1 | 40 <-> 41 |
| Yun | 1 | 42 -> 43 |
| **Dudley** | **1** | **44 (13,4 Mo) -> 45 (4,0 Mo)** |
| **Ibuki** | **2** | 48 -> 49 -> 50, 6,0 Mo chaque fois |
| Elena | 1 | 51 -> 52 |
| Yang | 1 | 55 -> 54 |

Le court-circuit de `Bg_Aire_Suivante` fait que les aires 1 et 2, identiques partout sauf
chez Ibuki, ne rechargent rien.

---

## TOUS NOS DECORS PASSENT EN HUIT BITS (25/09)

Frederic : « *donc pour etre coherent, tous les decors de NG et 2I doivent etre en 8 bits,
n'est ce pas ?* », puis « *ok, passe tous nos decors en 8 bits* ».

### 0. D'ABORD, UNE MESURE QUI ETAIT FAUSSE

Mes deux comptes des pages se contredisaient -- 3151 d'un cote, 2518 de l'autre. La cause :
**`%APPDATA%/CrowdedStreet` est redirige vers le conteneur de l'application Claude**
(`AppData/Local/Packages/Claude_pzs8sxrjxfjjc/LocalCache/Roaming/...`). Sur le seul
`stage37`, `ls` voit 80 `.tex`, `os.listdir` en voit 57, et Python repond `False` a
`exists("196-210.tex")` pendant que `md5sum` lit le fichier. **Les deux comptes etaient
faux**, parce qu'ils melangeaient deux vues du meme dossier.

Tout ce qui suit est mesure dans `SEPTEMBRE/SF3/CrowdedStreet-3SX/resources`, la source
que le lanceur recopie. C'est la meme raison qui interdit d'y ecrire. Le compte juste :
**2550 fichiers `.tex` distincts**, pour **3151 pages** chargees par le jeu -- l'ecart est
le dedoublonnage, et `doublons.txt` fait le pont.

### 1. CE QUE LE JEU CHARGE, LUI

`tex_remix/dump/manifest.txt`, depouille par liste de fond :

| liste | entrees | format |
|---|---|---|
| 132 | 7180 | **128x128 a 8 bpp** |
| 196 | 4696 | idem |
| 228 | 252 | idem |
| 260 | 2776 | idem |
| 292 | 2 | idem |
| 324 | 1312 | idem |

**Aucune exception.** Toute page de fond de 3SX est un 128x128 indexe a huit bits, seize
kilo-octets. Les notres etaient les memes 128x128 en trente-deux bits, soixante-quatre
kilo-octets : **les seuls objets de cette profondeur dans tout le jeu**. Les 256x256 a
4 bits et les 512x256 a 16 bits du vidage sont les sprites et l'interface, listes 0 et
590 et plus -- pas les fonds.

### 2. ET C'EST SANS PERTE

Compte sur les **2550 pages distinctes** : **aucune ne depasse 256 couleurs**. Les pires :

    206 couleurs   stage24  196-226.tex
    203 couleurs   stage22  196-223.tex
    195 couleurs   stage34  196-215.tex

Pire page de Dudley 1 : **97**. Pire page d'Ibuki : **82**. Il n'y a donc **aucune
quantification** a faire -- un index par couleur, rien d'autre -- et l'echantillonnage
etait deja en `NEAREST`.

Un detail qui compte : un pixel a alpha nul est **jete par le nuanceur**
(`if (color.a == 0.0) discard;`). Les ramener tous a la meme valeur ne change rien a
l'image et n'occupe qu'un seul emplacement de palette au lieu d'un par teinte invisible.
C'est la seule normalisation qu'on s'autorise, et elle est declaree.

### 3. LE FORMAT, VERSION 2

    0     '3STX'
    4     2
    8     largeur
    12    hauteur
    16    256 entrees de quatre octets
    1040  largeur * hauteur indices

**La palette garde les octets tels que la version 1 les posait par pixel.** C'est la clef
de la surete : ces octets traversent ensuite le meme `.bgra` du nuanceur
(`palette8.frag.hlsl` et `direct.frag.hlsl` appliquent le MEME swizzle), donc l'image
sortie est la meme sans avoir a raisonner sur l'ordre des composantes.

La version 1 reste lue : une page qui depasserait 256 couleurs la garderait, et
`art_remix`, qui a son propre chargeur, n'est pas concerne.

### 4. LA VOIE, DU FICHIER AU GPU

`tex_remix.c` pose `bits->bitdepth = 1` au lieu de 4. Ensuite tout existait deja :

* `flPS2GetTextureInfoFromContext` : `bitdepth 1 -> SCE_GS_PSMT8` ;
* `flPS2GetTextureSize(PSMT8, w, h, 1)` = **`w * h`** exactement -- verifie, parce que
  `flPS2ConvertTextureFromContext` fait un `flMemcpy` de cette taille depuis NOTRE tampon :
  un octet de trop et on lisait hors du tampon ;
* ce `memcpy` recopie le PSMT8 **tel quel, sans entrelacer** ;
* `SDLGPURenderer_CreateTexture` : `PSMT8 -> R8_UINT` + `PALETTE_8`.

**Le seul vrai chantier etait la palette.** Une texture indexee est tiree a travers
`palettes[quad->palette_index]`, c'est-a-dire la palette que le JEU a preparee pour la
page d'origine -- qui n'a rien a voir avec la notre. Donc :

* `tex_remix` garde la palette de la page qu'il vient de substituer et la rend **une seule
  fois** (`TexRemix_TakeReplacementPalette`). Une seule case suffit parce que
  `TexRemix_Substitute` est appelee dans `ppgSetupTexChunk_3rd` **juste avant**
  `flCreateTextureHandle`, qui appelle lui-meme `Renderer_CreateTexture` : rien ne
  s'intercale. Le « une seule fois » est ce qui empeche une texture creee plus tard
  d'heriter d'une palette qui n'est pas la sienne ;
* `_Texture` gagne un champ `propre_palette`, cree en 256x1 au format meme des pages en
  couleur pleine, et qui **passe avant** celle du jeu au moment du tirage ;
* le repli OpenGL recoit le meme champ, en `GL_TEXTURE_1D` televerse en `GL_BGRA`.

### 5. LE POIDS

| | avant | apres |
|---|---|---|
| une page | 64 Ko | **17 Ko** |
| un decor a 2 plans | 4,0 Mo | **1,1 Mo** |
| un decor a 3 plans | 6,0 Mo | **1,6 Mo** |
| **Dudley 1** | **13,4 Mo** | **3,6 Mo** |
| **nos 2550 pages** | **159,4 Mo** | **42,4 Mo** |

Dudley 1 etait le plus lourd du jeu et celui qui risquait de s'a-couper au changement de
manche ; il pese maintenant moins qu'un de nos decors ordinaires d'hier. Le meme quart
s'applique a la memoire video et au transfert vers la carte, pas seulement au disque.

### 6. CE QUI A ETE VERIFIE AVANT D'ECRIRE

* `pages_8bits.py` **relit chaque page depuis ses indices et la compare a l'originale
  AVANT de la remplacer**. 2550 sur 2550, octet pour octet. Rien n'aurait ete ecrit sur un
  ecart.
* Verification independante en plus : **1867** pages comparees aux copies version 1
  encore presentes dans `%APPDATA%` -- toutes identiques. Les **26** qui different sont
  des copies datees du **22/09** restees en place alors que la source avait ete regeneree
  depuis (`stage38` surtout) ; ce ne sont pas des erreurs de conversion, et ces 26 la sont
  justement celles que la relecture sur place avait deja validees.
* La construction passe (`ninja`, sortie 0), et `bande3sx.ecrire_tex` emet desormais la
  version 2 d'office -- une regeneration garde donc les huit bits sans rien avoir a
  repasser.

**Ce qui reste a juger, c'est l'image, et c'est Frederic qui la juge.**

---

## LE CRASH DE DUDLEY ENTRE LES MANCHES, ET CE QUI EST LU CHEZ ALEX (25/09)

Frederic : « *fait le decor d'alex et corrige le crash du decor de dudley entre les
round 1 et 2* ».

### 1. DEUX CRASHES DIFFERENTS, PAS UN

**Ibuki** (corrige plus tot dans la journee) : repasser par l'etat 0 rejoue
`bg_initialize`, donc `Bg_Texture_Load_EX`, qui commence par `Bg_TexInit` -- lequel ne
fait que REPOINTER `ppgBgList[i].tex` et ne libere rien. `fatal.log` le disait :
`ppgSetupTexChunk_1st: Texture is already in use`. `Bg_Aire_Suivante` appelle maintenant
`Bg_Close()` avant de recharger.

**Dudley** : autre cause, aucun message. La trace `fin-de-round.log` montre le
rechargement mene a son terme (`TexRemix_SetStage 45` puis `-1`), et
`pages-manquantes.log` s'arrete au milieu du second chargement -- ixNum 260..451 la ou le
premier avait fait 292..515.

**LA CAUSE, LUE** : les tables par etage -- `stage_bgw_number`, `bg_map_tbl`,
`use_real_scr`, `rewrite_scr`, `bgtex_stage_gbix`, `stage_priority`, `stage_opaque` --
etaient lues en `bg_w.stage`, qui **ne change pas** d'une aire a l'autre. Mais
`bg_w.scrno` vient de `use_real_scr[bg_w.bg_index]`, qui change. `ETAGESNG_USE_SCR` :

| decor | aire 0 | aire 1 | aire 2 | |
|---|---|---|---|---|
| Ryu/Ken | 40 -> 3 | 41 -> 3 | | identique |
| **Yun** | **42 -> 3** | **43 -> 2** | | **DIFFERENT** |
| **Dudley** | **44 -> 3** | **45 -> 2** | | **DIFFERENT** |
| Ibuki | 48 -> 3 | 49 -> 3 | 50 -> 3 | identique |
| Elena | 51 -> 2 | 52 -> 2 | | identique |
| **Yang** | **55 -> 2** | **54 -> 3** | | **DIFFERENT** |

La boucle de chargement tournait `bg_w.scrno` fois (2) pendant que `scr_bcm` en
remplissait `use_real_scr[bg_w.stage]` (3) : le troisieme plan gardait sa carte alors que
son morceau de texture n'etait plus charge. Et comme `stg` sert ensuite de base a la liste
de reecriture, `(stg * 64) + 0x64` glissait de **soixante-quatre** d'une aire a l'autre --
la pluie de Dudley allait chercher ses pages ailleurs.

**Les trois qui passaient dans la trace sont exactement les trois a nombre de plans
constant.** Yun et Yang tombaient aussi, sans avoir ete essayes.

`Bg_Plans_Source()` dans `bg.c` rend `bg_index` quand l'etage a plusieurs aires, `stage`
sinon ; les sept lectures et l'animation de plan y passent. Une aire est un decor a part
entiere -- l'etage 45 est choisissable tel quel -- donc ses tables sont les siennes.

### 2. ALEX : CE QUI EST LU, ET CE QUI NE L'EST PAS

Frederic : « *il manque le plan derriere le clochard, et le passant passe devant lui au
lieu de derriere le clochard* ».

**Lu dans `SF3_1ST.BIN`.** L'enregistrement d'element fait `w1 = plan`, `w3 = x`,
`w4 = y`, `w5 = profondeur`, `w6 = script` :

    clochard     0x8C1AF0B6   plan 1   x 752   y  86   prof  90   script  8
    gratte-ciel  0x8C1AF038   plan 3   x 674   y 113   prof 104   script  2

Et la table des acteurs id 64 (`0x8C1B255C + 44k`, `w2 = plan`, `w6 = palette ET
profondeur`) :

    passant k=3   plan 2   x 320   y 87   prof 85   script 34
    passant k=4   plan 2   x 912   y 87   prof 86   script 34   miroir

**Le port porte exactement ces valeurs.** Le defaut n'est donc pas une erreur de
transcription.

Priorites des plans d'Alex, `ETAGESNG_PRIORITY` entree 38 = `0x68545E00` :
**plan 0 -> 104, plan 1 -> 84, plan 2 -> 94**.

Ordre de dessin obtenu (un z plus grand est plus loin) :

    84  liste 196 (la rue, pleine largeur)
    85  passant k=3
    86  passant k=4
    90  clochard
    94  liste 260
    104 liste 132

Les passants passent donc devant le clochard -- ce que Frederic voit, et ce que les
valeurs de la console disent.

**DEUX PISTES ECARTEES, MESUREES :**

* *Conflit de profondeur du gratte-ciel* (z 104 = priorite de son plan) : le nuanceur
  compare en `LESS_OR_EQUAL`, l'egalite PASSE. Ecarte.
* *Trou dans les pages* : mesure colonne par colonne sur les trois listes de l'etage 38,
  **aucune colonne vide entre 740 et 810**. La liste 132 est peuplee de 560 a 831, la 260
  de 640 a 895, la 196 sur toute la largeur. Il n'y a pas de trou derriere le clochard.

**CE QUI RESTE A TRANCHER** : la correspondance entre le **plan Dreamcast** (1, 2, 3), la
**famille** du port et l'**index de `bg_priority`**. Le port donne au clochard (plan DC 1)
la famille 3, donc `bg_priority[2] = 94` ; aux passants (plan DC 2) la famille 2, donc
`bg_priority[1] = 84` ; au gratte-ciel (plan DC 3) la famille 1, donc
`bg_priority[0] = 104`. C'est `famille_du_plan` dans `animerng.py` qui decide, par
coefficient de defilement. **Si cette correspondance est inversee pour Alex, les trois
objets defilent avec le mauvais plan** -- et c'est la seule chose qui n'a pas ete
verifiee. C'est par la qu'il faut reprendre.

---

## DUDLEY REPLACE, ET ALEX TOUJOURS OUVERT (25/09, troisieme passe)

Frederic : « *rien n'a ete fait pour alex, pour dudley, le 2eme round est glitche avec les
2 combattants colles sur le cote gauche du decor au debut de round et plein de defauts
dans le decor* », puis « *ton rendu n'est pas bon* ».

### 1. DUDLEY : MA CORRECTION DEPLACAIT LE PROBLEME

Je rechargeais en repassant par `bg_w.bg_routine = 0`, donc par `bg_initialize`. Or
`bg_initialize` fait bien plus que charger : il remet les **sept couches a zero** --
`pos_x_work`, `pos_y_work`, `xy[].cal`, `wxy[].cal`, `hos_xy[].cal`, les vitesses,
`zuubun` -- plus `bg_f_x`, `bg_f_y`, `max_x`, `scr_stop`. Le decor repartait de son bord
gauche pendant que les combattants restaient ou ils etaient : c'est exactement ce que
Frederic voit.

**La console ne fait pas ca non plus.** `0x8C088018` remet les registres de defilement et
charge la bande, rien de plus ; ce qui suit la camera la suit deja a chaque trame.

`Bg_Aire_Suivante` fait donc desormais, et seulement : `Bg_Close()`, `Bg_Off_R(7)`, poser
`bg_index` / `scno` / `scrno` / `bg_opaque` de la nouvelle aire, `Bg_Texture_Load_EX()`,
`Bg_Kakikae_Set()`. **Aucune position n'est touchee.**

### 2. UNE CONSEQUENCE DU HUIT BITS QUI AVAIT ETE OUBLIEE

Les outils ne savaient plus lire nos pages : `ecran_ng.lire_tex` decoupait
`w * h * 4` octets apres l'entete. Il lit maintenant les deux versions. **Tout outil qui
lit un `.tex` doit etre verifie de la meme facon** -- le seul autre decodeur est
`pages_8bits.py`, qui les connait deja.

### 3. ALEX : CE QUI EST ECARTE, ET CE QUI RESTE

**Ecarte, mesure :**

* les valeurs, relues dans `SF3_1ST.BIN` -- clochard plan 1 prof 90, passants plan 2
  prof 85 et 86, gratte-ciel plan 3 prof 104 ; le port les porte exactement ;
* la correspondance plan -> famille, confirmee par les coefficients de defilement :
  plan 3 -> liste 132 a 0,625 (z 104), plan 2 -> liste 196 a 1,0 (z 84), plan 1 ->
  liste 260 a 0,875 (z 94). `couches_ng(1)` donne `(1, 94) (2, 84) (3, 104)`, et
  `bg_priority` de l'etage 38 (`0x68545E00`) donne 104 / 84 / 94 : les trois concordent ;
* un trou dans les pages : **aucune colonne vide entre 740 et 810** sur les trois listes ;
* le conflit de profondeur du gratte-ciel (z 104 = priorite de son plan) : le nuanceur
  compare en `LESS_OR_EQUAL`, l'egalite PASSE ;
* le « plan sans couche » de Sean : Alex a bien ses trois couches, la branche n'est pas
  prise. La piste a ete ouverte puis **annulee**.

**Et un rendu qui ne vaut rien** : `ecran_ng.py` a servi a composer l'ecran d'Alex, et
Frederic a tranche -- « ton rendu n'est pas bon ». Il MODELISE le defilement au lieu de
le mesurer ; il ne peut pas servir de preuve. Il ne sera plus produit comme tel.

**CE QUI RESTE** : le defaut est au dessin, et il faut savoir QUELLE couche. D'ou
`SF3_PLAN_SEUL` dans `Bg_Texture_Load_EX` -- 0, 1 ou 2 n'en laisse qu'une allumee, dans
le style de `SF3_DECOR_Z`. Lanceur : **`ALEX - quelle couche manque.cmd`**, qui demande le
numero et lance. Trois essais, et celle qui ne montre rien est la coupable.

---

## ALEX : C'ETAIT MON DECALAGE DE 34 LIGNES, PAS LE PIETON (25/09)

Frederic : « *avant l'ajout du pieton, le decor etait convenablement affiche. Trouve
comment l'afficher correctement a nouveau* ».

**C'est la phrase qui a tout donne.** Les passants et le decalage vertical d'Alex etaient
dans la MEME livraison ; il attribuait le defaut au pieton parce que c'est ce qui se
voyait. Ce n'etait pas lui.

### LA MESURE

Sur les pages deployees de l'etage 38, ligne par ligne :

    liste 260 : contenu aux lignes de scene 562..941
                (donc 596..975 avant le decalage de -34)

`DECALAGE_Y[(1, 0)] = -34` passait par **`np.roll`**, qui ENROULE : les 34 lignes du haut
de la bande -- vides chez Alex -- repassent en bas. Le contenu de la liste 260 s'arretait
donc 34 lignes trop haut, et il n'y avait plus rien en dessous.

**Or le clochard est sur cette liste** : plan DC 1 -> famille 3 -> liste 260, confirme par
le coefficient de defilement 0,875. Et il est a hauteur de sol (y 86). **Les 34 lignes
manquantes etaient exactement derriere lui.**

### CE QUI ETAIT JUSTE, ET CE QUI NE L'ETAIT PAS

La derivation reste bonne -- `u32[plan+28] = u32[plan+20] * 266`, donc couche 0 a
`0xE000 * 266 >> 16` = 232 contre 266, soit **34 lignes plus haut**. Ce qui etait faux,
c'est l'ENDROIT : la console ecrit `u32[plan+28]`, un **registre de position du plan**.
Rouler les pixels dans la page n'est pas la meme chose des que la bande n'est pas pleine
sur ses 1024 lignes -- et celle d'Alex ne l'est pas.

La ligne noire que ce decalage corrigeait peut donc revenir. Si elle revient, **elle se
reprend par l'origine du plan, pas par la texture**.

### CE QUI A ETE FAIT

* `DECALAGE_Y` d'Alex retire (`descripteursng.py`) ; Gill (0, 0) : 80 garde le sien,
  Frederic l'a valide.
* `couchesng.py` accepte maintenant un numero de bande : `python couchesng.py 1 --ecrire`.
  Regenerer les dix-neuf pour une seule reecrirait des pages deja validees.
* Les 96 pages d'Alex regenerees, en **version 2 du `.tex`** (huit bits), puis
  rededuplquees (`pages_doublons.py --etage 38 --appliquer` : 49 pages effacees, index de
  49 lignes). Verifie : la liste 260 est revenue en 596..975.

### CE QUI RESTE

Les deux passants n'ont pas bouge : leurs valeurs sont celles de la console (plan 2,
profondeur 85 et 86, lues en `0x8C1B25E0` et `0x8C1B260C`), et le clochard 90. L'ordre
qu'ils donnent est celui de la Dreamcast. **Mais le clochard paraissait 34 lignes trop bas
sur son plan** : c'est peut-etre ce que Frederic lisait comme « le passant passe devant
lui ». A rejuger une fois le plan revenu.

### LEcON

Quatre pistes avaient ete ouvertes et fermees avant celle-ci -- conflit de profondeur,
trou dans les pages, « plan sans couche », correspondance plan/famille -- toutes mesurees,
toutes fausses. Aucune n'aurait ete ouverte si j'avais commence par la question que
Frederic a posee lui-meme : **qu'est-ce qui a change dans la meme livraison ?** Le defaut
etait une regression, pas un manque.

---

## LA TRANSITION D'AIRE : LE MOMENT, ET LES SPRITES (25/09)

Frederic : « *la transition entre les decors entre 2 rounds a lieu trop tot, elle devrait
avoir lieu pendant l'ecran noir entre les rounds. Apres le changement entre 2 round, les
anciens sprites animes restent, et les nouveaux sprites a afficher ne sont pas chargés* ».

### 1. LE MOMENT

`Bg_Aire_Suivante` etait appelee juste apres `Round_num++`, a DEUX endroits --
`Game_Manage_6th` case 1 et `Game_Manage_8_0`. Le decor changeait donc sous les yeux du
joueur, pendant que le vainqueur posait encore.

**Le bon instant est `Game_Manage_9th`, dans le bloc `if (Switch_Screen(0))`.**
`Switch_Screen` ne rend vrai que quand `WipeOut` a fini : l'ecran est alors **entierement
couvert**. C'est le seul instant ou un rechargement ne se voit pas, et il tombe juste avant
que la manche suivante soit armee.

Les deux chemins d'avant y passent tous les deux : l'etat 6 met `C_No[0] = 7`, qui mene a
8 puis a 9. Et la manche qui TERMINE le match sort en `C_No[1] == 0` sans jamais y venir --
ce qui est juste : on ne recharge pas un decor qu'on quitte.

### 2. LES SPRITES -- UN SEUL DEFAUT, PAS DEUX

« Les anciens restent » et « les nouveaux ne sont pas charges » ont la **meme cause**. Les
objets de decor naissent UNE FOIS, dans `bg2202_init00` (`bg220.c`), a la mise en place de
l'etage. Changer d'aire change `bg_w.bg_index`, donc la liste que `DecorObjets_Combien` et
`scr_obj_data` designent -- mais personne ne rendait les anciens ni n'appelait
`effect_05_init` pour les nouveaux.

`effect_05_rendre` (nouveau, dans `eff05.c`) parcourt la **liste d'effets 4** et rend tout
ce qui porte notre signature -- `id` 5 et `work_id` 0x10, ce que `effect_05_init` est seul
a poser. Le maillon suivant est lu AVANT de rendre celui-ci : la liste est chainee et
`push_effect_work` la recoud.

`push_effect_work` appelle deja `DecorObjets_Oublier`, donc le rang et l'emplacement de
palette suivent sans rien ajouter.

### 3. ET UNE GENERATION D'IDENTITE DE PLUS

`DecorObjets_Identite` porte l'image (8 bits), le rang (6) et **deux bits de generation**.
Le commentaire de `decor_objets.c` dit pourquoi ils existent : quand le tas de morceaux
repart a zero mais que l'identite ne change pas, `makeup_tpu_free` restreint la recherche
aux emplacements que l'ancienne entree occupait -- des emplacements qui ne portent plus
rien -- et **`get_mltbuf16_ext` boucle a l'infini**.

Une aire qui change est une mise en place neuve : elle merite sa generation, exactement
comme une entree d'etage. `DecorObjets_Oublier(NULL)` fait les deux (vide les fiches et
incremente la generation), et il est appele entre le chargement des pages et
`effect_05_init`.

### L'ORDRE FINAL DE `Bg_Aire_Suivante`

    effect_05_rendre()       les objets de l'aire precedente
    Bg_Close()               les poignees de texture
    Bg_Off_R(7)              les couches (leur nombre peut changer)
    bg_index / scno / scrno / bg_opaque de la nouvelle aire
    Bg_Texture_Load_EX()     les pages
    Bg_Kakikae_Set()         la liste de reecriture
    DecorObjets_Oublier(NULL) generation suivante
    effect_05_init()         les objets de la nouvelle aire

**Aucune position de couche n'est touchee** -- c'est la lecon du 2eme round de Dudley.

---

## LA CLE DE TUILE PORTE MAINTENANT LA GENERATION (25/09)

Frederic : « *transition OK, mais 2 round glitche* », sur Dudley.

### CE QUI ETAIT DEJA BON

Le journal de la partie le dit sans ambiguite :

    tous les objets oublies : le tas repart a zero
    etage 45 : variante de decor 3, ami 0
    marque objet 0 : etage 45, 1 images ... jusqu'a 31

Les 32 objets de l'etage 45 naissent, aux bons x, y, z, aucun `ECARTE`. Et
`fin-de-round.log` donne « effets libres 82 » avant, « 77 » apres -- exactement les cinq
objets de plus que l'etage 45 compte (27 contre 32). **Le rendu et la re-creation
marchent.**

### LA CAUSE : DES CLES QUI SE RENCONTRENT

`DecorObjets_Tuile` construit sa cle ainsi :

    *cle = nos[k].cle_base + image * (cols * ligs) + case

et `cle_base` est **la somme des morceaux des objets qui precedent celui-ci DANS SON
ETAGE**. Deux etages donnent donc des bases differentes pour le meme rang -- mais rien
n'empeche deux cles de coincider d'une aire a l'autre. Or le cache de motifs garde les
tuiles de l'aire qu'on vient de quitter : **l'objet 3 de l'etage 45 retrouvait celles de
l'objet 3 de l'etage 44**.

`DecorObjets_Identite` portait deja deux bits de generation -- c'est ce qui evite le gel
de `get_mltbuf16_ext` -- mais **la cle de TUILE n'en portait aucun**.

### LA CORRECTION, ET POURQUOI UN SEUL BIT

    base += (s32)(generation & 1u) * 32768;

Une mise en place prend la moitie basse de l'espace des cles, la suivante la haute ; deux
aires qui se succedent ne peuvent plus se rencontrer.

**Un seul bit, et c'est mesure.** L'espace de cles par etage, les pires :

    etage 52   17373
    etage 40   13754
    etage 47   11314
    etage 48   10526

Quatre generations a 16384 deborderaient : 3 * 16384 + 17373 = 66525 > 65535. Deux a
32768 tiennent : au pire 32768 + 17373 = **50141**, et `CLE_VIDE` (65535) reste hors de
portee. Une collision ne redeviendrait possible qu'entre une mise en place et la SUIVANTE
DE LA SUIVANTE -- deux manches plus tard, quand le cache a vieilli.

### AU PASSAGE, DEUX FAUSSES PISTES FERMEES

* `offset 65535` dans le journal des morceaux n'est PAS un echec de placement : c'est une
  case de grille vide. L'objet 2 d'Alex a 15 cases pour 11 tuiles, donc 4 a 65535.
* `Clear_texcash_work` ne sert pas a la mise en place d'etage -- son seul appelant est
  `checkSelObjFileLoaded`, pour les ressources de langue. Le cache de motifs vieillit
  tout seul par son compteur `time` ; il n'y a rien a vider a la main.

---

## L'ECRAN DE SELECTION EST NETTOYE (25/09)

Frederic : « *supprime les variants puisqu'ils se declenchent automatiquement maintenant,
et reunis ryu et ken pour le new gen* ».

### CE QUE `bg_index_tbl` DIT

    { 40, 41, 41 }   Ryu, puis KEN      -> garder 40, sauter 41
    { 42, 43, 43 }   Yun                -> garder 42, sauter 43
    { 44, 45, 45 }   Dudley             -> garder 44, sauter 45
    { 48, 49, 50 }   Ibuki, ses TROIS   -> garder 48, sauter 49 et 50
    { 51, 52, 52 }   Elena              -> garder 51, sauter 52
    { 55, 54, 54 }   Yang               -> garder 55, sauter 54

**ATTENTION A YANG** : c'est le **55** qu'on garde, pas le 54. Son aire 0 EST l'etage 55 --
la console commence par celui-la. Garder le 54 aurait donne un decor fixe. Frederic avait
raison de le citer ; **Yun etait le meme cas**, en plus simple.

**RYU ET KEN SE REUNISSENT** : le decor 2 commence chez Ryu et passe chez Ken, le decor 11
fait l'inverse. Deux entrees pour la meme paire ; l'etage 40 la donne en entier.

### CE QUI RESTE

New Generation passe de dix-neuf entrees a **onze** :

    37 NG GILL      42 NG YUN        51 NG ELENA
    38 NG ALEX      44 NG DUDLEY     53 NG ORO
    39 NG SEAN      46 NG NECRO      55 NG YANG
    40 NG RYU KEN   48 NG IBUKI

Total selectionnable : **48** entrees contre 55. Les fichiers des etages retires restent en
place ; on ne les propose plus, c'est tout.

Les noms perdent leur numero (`NG YUN 1` -> `NG YUN`), et l'etage 40 devient `NG RYU KEN`.
Le `&` est evite : `Setup_Letter_99` fait `chr = old_cgnum + *ptr`, donc le glyphe depend
du jeu de tuiles -- on s'en tient aux lettres et aux espaces.

### DEUX POINTS DE METHODE

* **Une boucle, plus une suite de `if`.** Ibuki saute DEUX etages de suite (49 et 50) : une
  comparaison par etage ne peut pas franchir une paire, elle s'arrete au milieu.
  `Etage_Non_Propose` est une fonction, et la navigation boucle dessus.
* **Les quinze etages ajoutes de 2nd Impact (22 a 36) n'ont aucune aire multiple** -- ils
  ne generent pas de table d'index (`ETAGES2I_INDEX_TBL` n'existe pas) -- donc il n'y a
  rien a y reunir.

### ET UNE CHOSE VUE EN PASSANT, NON FAITE

`Random_Stage_Data[2][32]` ne contient que des etages **0 a 19**. L'entree RANDOM ne tire
donc **que parmi les vingt d'origine** : aucun de nos trente-six decors ajoutes ne peut
sortir au hasard. Rien a corriger du fait du nettoyage -- mais c'est une porte ouverte si
Frederic veut que le hasard les inclue.

---

## LE TIRAGE RANDOM PORTE NOS DECORS (25/09)

Frederic : « *oui, ajoute nos decors au tirage RANDOM* ».

`Random_Stage_Data[2][32]` ne contenait que des etages **0 a 19** : aucun de nos
trente-six ajouts ne pouvait sortir au hasard.

### LES QUARANTE-CINQ ETAGES DU TIRAGE

Exactement ceux que la selection propose :

    0 a 16, 18, 19    les dix-neuf d'origine (17 est vide, 20 EST le RANDOM)
    22 a 36           les quinze de 2nd Impact
    37 38 39 40 42 44 46 48 51 53 55   les onze de New Generation

Les huit etages de New Generation ecartes par `Etage_Non_Propose` le sont aussi ici : ce
sont des AIRES, elles s'enchainent toutes seules de manche en manche, et les tirer
separement donnerait un decor qui ne changerait jamais.

### CE QUI N'ETAIT PAS TRIVIAL : LA LARGEUR DU TIRAGE

`random_32()` rend une valeur **0 a 31** -- trop etroit pour quarante-cinq etages. Et
**on ne peut pas appeler le generateur deux fois** : ce port garde le compte des tirages
pour rester d'accord avec la borne (c'est ce que dit le commentaire de `ta0_init00` a
propos de `random_16`), et un appel de plus decalerait toute la suite.

La sortie : `random_32` avance `Random_ix32`, un index de **0 a 127** (`&= 0x7F`), et cet
index est un `s16` global **sauvegarde dans l'etat reseau** (`game_state.c`), donc partage
et deterministe. On appelle donc `random_32()` exactement comme avant -- le generateur
avance du meme cran -- et **c'est son index qu'on lit**.

La table est alors batie comme `random_tbl_32` l'est elle-meme : **128 cases**, lues par
`Random_ix32 & 0x7F`.

    const u8 Etage_Au_Hasard[128]

Chaque etage y sort **deux ou trois fois**, et **deux cases voisines ne portent jamais le
meme** : deux tirages de suite ne peuvent pas rendre le meme decor. Graine fixe, table
reproductible -- `outils/tirage.py`.

### CE QUI N'EST PAS TOUCHE

`Random_Stage_Data` reste tel quel : il sert encore au tirage de l'**arcade**, quand les
deux joueurs prennent le personnage aleatoire (`My_char[0] == 17 && My_char[1] == 17`).
Celui-la n'a pas ete demande.

---

## LES SIX CHANTIERS, ET LES FICHES DE L'ECRAN DE SELECTION (25/09)

### 1. ALEX : LE PIETON FIGE SON IMAGE PENDANT L'ATTENTE -- CORRIGE

Frederic : « *une fois sur 2 le pieton disparait trop tot* ».

L'etat 2 de la routine (`0x8C0A888A`) ne fait QUE decrementer `[+54]` : il n'avance pas le
script. Le passant tient donc son image pendant toute l'attente, et ne s'anime qu'en
etat 3. Mes deux fiches n'avaient pas de suites -- ils **marchaient sur place** 1280 trames
puis sautaient en arriere. Deux suites le reglent : `[[(34, 0)], 34]`, l'image du pas 0
tenue, puis le script entier.

**CE QUI RESTE LA VALEUR DE LA CONSOLE**, et qui n'est pas touche. `0x8C0A88A4`
desassemble :

    tst #1, [+38]  ->  PAIR : arrive quand s16[+102] >  [+52]
                       IMPAIR : arrive quand s16[+102] <  [+52]

    k=3  [+38] = 4  [+52] =  400  part de 320 a +1 px/trame  ->   81 trames
    k=4  [+38] = 5  [+52] = -192  part de 912 a -1 px/trame  -> 1105 trames

Et le script 34 (`0x8C0CF770`, table d'Alex `0x8C0CEC00`) ne porte **aucune commande
`0x29`** : douze images, rien d'autre. C'est donc bien la console qui fait marcher l'un
81 pixels et l'autre 1105. Le faire traverser serait un ecart assume, pas une correction.

### 2. ELENA 1 : L'OISEAU CHANGE DE PROFONDEUR -- LU, PAS PORTE

Frederic : « *sur certaines frames il doit etre derriere le ponton* ». Il a raison, et
c'est ecrit dans le binaire. La routine `0x8C0A63F0` **ecrit `[+556]`** a deux endroits :

    0x8C0A64D4   mov #79   ->  DERRIERE le ponton (qui est a 78)
    0x8C0A66DA   mov #10   ->  devant tout, et [+88] = 10 avec

A la naissance il est a **67**. Trois profondeurs.

**CE QUE LE PORT NE SAIT PAS FAIRE** : une fiche n'a qu'UN `z`. Le mecanisme existe pour
l'animation -- les `suites` par segment de trajet -- mais pas pour la profondeur. Il faut
un **z par segment de trajet**, plus le decodage des durees des phases de l'oiseau. Les
valeurs sont lues ; le chantier est nomme et n'est pas fait.

### 3. YANG / YUN : LA SOURCE ELLE-MEME DIFFERE

Frederic : « *YANG NG 1 fenetres de droite sont noires mais pas bleues* ».

Mesure sur les pages deployees, ligne par ligne, et sur la source avant decoupe :

    YUN 1  (etage 42, bande 5)  plan lointain : lignes 512..799   221184 px
    YANG 1 (etage 54, bande 17) plan lointain : lignes 512..1007  380928 px

Les fenetres sont des **trous dans le plan proche**. Chez Yang le plan lointain descend
assez bas pour les remplir de bleu ; chez Yun il s'arrete deux cents lignes plus haut et
elles restent noires. Les deux plans lointains sont **entierement bleus**, pas un pixel
noir (mesure sur la composante B contre R et G).

Et les objets des deux etages sont **identiques** : Yang partage les tables de scripts de
Yun, croisees. La table statique est `0x8C4CC1F0 + 12 * decor + 4 * aire`, copiee a
l'execution en `0x8C4DE610` :

    decor  3 Yun  : 0x8C0D30E4  0x8C0D4174  0x8C0D4174
    decor 10 Yang : 0x8C0D4174  0x8C0D30E4  0x8C0D30E4

Notre conversion est donc fidele des deux cotes. **Le noir de Yun vient du disque.**

### 4. RYU 2I BG02 : LE SIGNE ETAIT DEJA FAIT

Sept elements de l'etage 24 ont un x negatif -- le seul decor de 2nd Impact dans ce cas :
-128, -288, -96, -368, -233, -145, -112.

J'ai cru tenir la cause et j'ai signe la lecture dans `blocs2i.lire` puis dans
`animer2i.objets`. **C'etait redondant** : `animer2i` signe deja plus bas
(`x_signe = o["x"] - 65536 if o["x"] > 32767`) et applique `DECALAGE_X["bg02"] = 512`. Et
modulo 1024, -128 et 65408 sont le meme point -- la fiche ne bouge pas d'un pixel. **Les
deux changements ont ete retires** plutot que de laisser un commentaire qui ment.

Ce qui reste mesure : **l'etage 24 est le seul de 2nd Impact dont l'art couvre les 1024
colonnes** ; tous les autres s'arretent a 128..895. La cause du defaut n'est pas trouvee.

### 5. LES DECLENCHEURS, ET CE QUI N'EST PAS PORTE

Quatre comportements du port dependent des combattants : **REACTIF** (11 objets, etages
39, 42, 47, 52, 54), **RUPTURE** (28, etages 25, 28, 32, 38, 57), **SUR_COMBATTANT** (3,
etage 52), **REGARD** (1, etage 22) -- plus les chiens, qui lisent le personnage des
joueurs a leur naissance.

Cote New Generation, le test de contact `0x8C085A1E` a **onze sites d'appel** :
`0x8C09D044`, `0x8C0A0BD8`, `0x8C0A1098`, `0x8C0A1198`, `0x8C0A1298`, `0x8C0A1878`,
`0x8C0A1994`, `0x8C0A1AA8`, `0x8C0A834C`, `0x8C0A847C`, `0x8C0A9844` (Alex, sa voiture).

Le rapport NON LU de la chaine compte **121 appels sur 33 cibles**. Tout le reste vise des
services (VRAM, defilement, palettes, `0x8C13xxxx` / `0x8C145xxx`). **Ce qui n'est pas
porte** :

| cible | appels | ce que c'est |
|---|---|---|
| `0x8C09F258` | **25** | id 14. Le spawner ne pose que `[+0]=1`, `[+8]=14`, `[+6]=16`, `[+4]=r4` : **toute la conduite est dans une routine d'etat** (`0x8C09F29A`, repartiteur sur `[+36]`). |
| `0x8C0A5488` | 7 | a lire |
| `0x8C0B168C` / `0x8C0B13C0` | 1 + 1 | ids 117 et 115, chez **Sean** : x 512 et 496, table `0x8C0DE6D8`, scripts 7 et 6, palette 10, profondeur 10, plan 1 |

### 6. LES TIMINGS : 493 FICHES VERIFIEES, ZERO ANOMALIE

Chaque tableau `_durees` emis a ete compare au script du binaire, en retrouvant la table
par `0x8C4CC1F0 + 12 * decor + 4 * aire` et le decor par la table des aires
(`0x8C18A804 + decor * 6 + aire * 2`, **dont les valeurs sont des bandes 0..18** : l'etage
vaut 37 + bande). 70 sommes different, et chacune s'explique :

    37   objet reduit a UNE image (fige, ou pose balayee)
    15   cycle aligne sur 72 trames
     9   plus d'images emises que le script n'en tient
     7   tronque : moins d'images, debut identique
     2   a regarder -- et les deux sont volontaires

Les deux derniers : la marche de l'homme de Sean (`_marche_du_script` decoupe la premiere
trame) et **la riviere d'Elena**, dont la routine impose 33 trames par image quoi qu'en
dise le script -- c'est lu dans `0x8C0A4D34` et documente depuis le 18/09.

**Aucune anomalie de timing reelle.**

### 7. L'ECRAN DE SELECTION, AU MODELE DE 3rd STRIKE

`Letter_Data_99` porte cinq lignes ; les trois qui comptent sont **2 = PAYS**, **3 = nom
du stage**, **4 = `<PERSONNAGE> STAGE`**. Les trente-six etages ajoutes ont maintenant les
trois, au meme modele, avec le jeu en quatrieme ligne :

    22 UNKNOWN   GILL STAGE         GILL 2ND IMPACT
    23 AMERICA   MANHATTAN ROOFTOP  ALEX 2ND IMPACT
    24 JAPAN     TOKYO STREET       RYU 2ND IMPACT
    25 HONG KONG SHOPPING DISTRICT  YUN 2ND IMPACT
    26 ENGLAND   MAIN STREET        DUDLEY 2ND IMPACT
    27 RUSSIA    RAILROAD           NECRO 2ND IMPACT
    28 GERMANY   MUNICH             HUGO 2ND IMPACT
    29 JAPAN     A ROAD IN KYOTO    IBUKI 2ND IMPACT
    30 KENYA     SAVANNA            ELENA 2ND IMPACT
    31 BRAZIL    AMAZON             ORO 2ND IMPACT
    32 HONG KONG SHOPPING DISTRICT  YANG 2ND IMPACT
    33 AMERICA   SAN FRANCISCO BAY  KEN 2ND IMPACT
    34 BRAZIL    SAO PAULO          SEAN 2ND IMPACT
    35 EGYPT     CAIRO              URIEN 2ND IMPACT
    36 UNKNOWN   THE GORGE          2ND IMPACT
    37 HIGH SEAS MEDITERRANEAN SEA  GILL NEW GEN
    38 AMERICA   BACK ALLEY         ALEX NEW GEN
    39 AMERICA   NEW YORK STREET    SEAN NEW GEN
    40 JAPAN     JAPANESE INN       RYU AND KEN NEW GEN
    42 HONG KONG TRAM STREET        YUN NEW GEN
    44 ENGLAND   LONDON STREET      DUDLEY NEW GEN
    46 RUSSIA    RAILROAD           NECRO NEW GEN
    48 JAPAN     NINJA VILLAGE      IBUKI NEW GEN
    51 KENYA     NAIROBI            ELENA NEW GEN
    53 BRAZIL    AMAZON             ORO NEW GEN
    55 HONG KONG TEMPLE             YANG NEW GEN

Les vingt-deux etages d'origine ne sont pas touches. Les etages ecartes de la selection
(41, 43, 45, 47, 49, 50, 52, 54) gardent leurs fiches : elles ne s'affichent plus.

**D'OU VIENNENT CES NOMS, ET CE QUI EST ASSUME.** Les pays de New Generation etaient deja
dans la table. Les villes et les lieux viennent de recherches en ligne (Street Fighter
Wiki, sfgalleries.net, un fil ResetEra sur les decors de NG et 2I). **TRAM STREET** et
**TEMPLE** ne viennent d'aucune source : ils decrivent ce que **nos propres pages**
montrent pour Yun et Yang. Ce ne sont donc pas des noms officiels, et c'est dit ici plutot
que passe sous silence -- ils se changent en une ligne dans `eff99.c`.

Une remarque de methode : `Setup_Letter_99` fait `chr = old_cgnum + *ptr`, donc le glyphe
depend du jeu de tuiles. On s'en tient aux lettres, aux chiffres et aux espaces -- pas de
`&` ni de `/`.

---

## LE Z PAR SEGMENT, ELENA 2I, ET LES FICHES DE SELECTION (25/09)

### 1. UN SEGMENT DE TRAJET PORTE SA PROFONDEUR

Frederic : « *fais le z par segment pour l'oiseau d'Elena* ».

Un segment valait `{ duree, vx, vy, suite }`. Il vaut maintenant
**`{ duree, vx, vy, suite, z }`**, et **zero garde la profondeur de la fiche** -- les neuf
autres trajets du jeu ne changent pas d'un pixel, ce qui est verifie sur le fichier emis.

Cote port : `TRAJET_CHAMPS` vaut 5, `trajet_segment` avance de 5, et
`profondeur_du_segment` ecrit `my_priority` et `position_z` du `WORK` quand le segment
porte un z. Cote chaine : `animerng` emet cinq champs et complete a zero les trajets
ecrits a quatre.

### 2. CE QUE LA ROUTINE DE L'OISEAU DIT -- `0x8C0A63F0`

Une machine a **dix etats** sur `[+36]` :

| etat | duree | ce qu'il fait |
|---|---|---|
| 0 | 1 trame | `[+1] = 1`, pose le script 0 (= le 22), `[+148] = 120` |
| 1 | 120 trames | decompte `[+148]`. **Il n'avance pas le script** : l'oiseau reste fige sur son image 0 |
| 2 | | avance le script jusqu'a ce que le DRAPEAU du pas courant (`[+468]`) vaille 2, puis **`0x8C0A64D4 : [+556] = 79`** et `[+88] = 79` |
| 3 | | avance tant que le drapeau est 0 ; au premier drapeau non nul, `[+1] = 0` -- **il disparait** |
| 4 a 9 | | le vol, avec en 8 **`0x8C0A66DA : [+556] = 10`** |

**79 est derriere le ponton, qui est a 78.** C'est exactement ce que Frederic decrit.

### 3. LE DECOUPAGE, LU DANS LE SCRIPT 22

`0x8C0D9C00` (table d'Elena `0x8C0D9618`), 38 pas :

    pas  0..11  drapeau 0   6 trames   images 20504..20515   le perchoir
    pas 12      drapeau 1   6 trames
    pas 13      drapeau 0x2B  duree 0 : une COMMANDE, zero trame
    pas 14..15  drapeau 0   6 et 8 trames
    pas 16      DRAPEAU 2   1 trame    <- l'etat 2 s'arrete ici, cumul 92
    pas 17..35  drapeau 0   9 trames   images 20518..20536   l'envol
    pas 36      drapeau 1   2 trames   <- l'etat 3 s'arrete ici, cumul 264

D'ou les trois segments, et la chaine les a recomptes seule (1, 92, 172) :

    121 trames  z 67   l'image du pas 0, tenue   (1 de l'etat 0 + 120 de l'etat 1)
     92 trames  z 67   les pas 0 a 15
    172 trames  z 79   les pas 16 a 35           <- DERRIERE LE PONTON

`92 = 12*6 + 6 + 6 + 8` et `172 = 1 + 19*9`.

`plage_du_script(table, sc, debut, fin)` est neuf dans `animerng` : une suite peut
desormais tenir une **plage de pas avec leurs durees**. La forme liste
(`[(script, pas), ...]`) ne donnait qu'une trame par pas, ce qui n'allait pas ici -- le
perchoir tient six trames par image et l'envol neuf.

**CE QUI N'EST PAS FAIT, ET POURQUOI.** Le vol (etats 4 a 9) n'est pas reproduit : il se
positionne sur `u16[0x8C552758 + 10]` et `+12`, une adresse lue a l'execution, et pose
`[+124]`/`[+128]` = 512 avec `[+132]`/`[+136]` = +/-320 -- une vitesse ET une
acceleration. Un trajet a vitesse constante ne sait pas rendre ca. La disparition de
l'etat 3 non plus : le trajet reboucle sur le perchoir. C'est plus proche de la console
qu'avant, ou l'oiseau tournait ses 36 images a une seule profondeur, mais **ce n'est pas
la console**.

### 4. ELENA 2nd IMPACT ENCHAINE SES DEUX BANDES

Frederic : « *comme pour NG, les 2 versions des decors de elena second impact doivent
s'enchainer entre les 2 rounds* ».

La table d'aires de 2nd Impact, `0x8C1D591C + decor * 6 + aire * 2`, lue en entier :

| decor | bandes | |
|---|---|---|
| **8** | **8, 9, 9** | Elena : `bg08` puis `bg09` |
| 14 Urien | 15, 15, 15 | |
| 15 Gouki | 15, 15, 15 | la meme bande qu'Urien |
| tous les autres | constantes | |

**Un seul decor de 2nd Impact change de bande entre les manches**, et c'est Elena.
`bg08` est notre etage **56**, `bg09` l'etage **30**. Donc
`bg_index_tbl[30] = { 56, 30, 30 }`.

**C'est la forme qu'on avait du abandonner le 16/09** -- le portage ne suivait alors l'aire
qu'a moitie, `Bg_Texture_Load` prenant pages, profondeurs et plans a `bg_w.stage` pendant
que les objets suivaient `bg_index`. `Bg_Plans_Source` (25/09) a regle ca : toutes les
tables de plans suivent `bg_index` des qu'un etage a plusieurs aires. La bascule revient
donc, et dans le sens de la console.

**ET ELLE CHANGE DE NOMBRE DE PLANS** : l'etage 56 en a **quatre** (`ETAGES2IBIS_USE_SCR`
= 4, 2), l'etage 30 en a **trois**. `Bg_Aire_Suivante` eteint desormais les **quatre**
couches (`Bg_Off_R(0xF)`) et non trois -- sans quoi la quatrieme serait restee allumee sur
un plan qui n'existe plus.

### 5. LES FICHES DE L'ECRAN DE SELECTION

Frederic : « *unknown/the gorge est le decor 2I de akuma* », « *unknown BG10 est un decor
de hugo non finalise, il est a supprimer* », « *mets les mentions 2nd impact et new gen
entre parentheses* ».

* l'etage 36 devient **JAPAN / THE GORGE / AKUMA (2ND IMPACT)** ;
* l'etage **57** (`bg10`, le decor de Hugo non finalise) n'est plus propose ;
* l'etage **56** non plus : c'est l'aire 0 d'Elena 2I, que l'etage 30 donne maintenant en
  premiere manche ;
* les mentions de jeu passent entre parentheses, pour nos trente-six etages seulement.

`Etage_Non_Propose` ecarte donc 17, 21, 41, 43, 45, 47, 49, 50, 52, 54, **56** et **57** :
**46 entrees**, les vingt d'origine comprises.

---

## RYU 2I, L'OISEAU QUI NE S'EFFACE PAS, ET L'INVENTAIRE DES DECLENCHEURS (25/09)

### 1. RYU 2I : CE N'ETAIT PAS LES OBJETS, C'ETAIT LE FOND

Frederic : « *decor ryu 2I, il y a toujours des anomalies aux extremites du decor et des
sprites en trop ou mal places, alors qu'ils ont deja ete correctement positionnes* ».

**Les deux moities de la phrase sont vraies, et c'est la cle.** Les objets etaient bien
places ; le FOND portait une SECONDE copie des memes sprites, cuite **512 pixels a cote**.

`cuire.py` (via `elements.rend_etat`) pose chaque element a `(e["x"] + x) & 0x3FF` --
**sans le signe et sans `DECALAGE_X`**, que `animer2i.fiche` applique, lui, depuis le
03/09. Ryu est le seul decor de 2nd Impact dont les `x` se comptent depuis le milieu de la
bande : la cuisson et les fiches se contredisaient donc, pour lui seul.

Mesure, page par page, des pages deployees contre la banque du disque :

    plan lointain (liste 132)  :     0 pixel de difference
    plan proche   (liste 196)  : 9 891 pixels, en NEUF taches

    x   18..101   4 795 px   -> +512 : 530..613   la fiche a24o6 est en 528
    x  211..233     695 px   -> +512 : 723..745   a24o9 / a24o1 en 720
    x  267..284     331 px   -> +512 : 779..796   a24o5 en 785
    x  696..748     559 px   -> +512 : 184..236   a24o7 en 177
    x  768..804     523 px   -> +512 : 256..292   a24o4 en 248
    x  834..930   2 256 px   -> +512 : 322..418   a24o3 en 320, a24o10 en 385
    x  948..997     732 px   -> +512 : 436..485   LES DEUX BAIGNEURS DU BASSIN

**D'ou les deux defauts a la fois** : le double, et le double AUX EXTREMITES -- ce qui
devait etre au centre tombait a `x 18` ou `x 997`.

Le fond de l'etage 24 est desormais **identique a la banque du disque au pixel pres**, sur
ses deux plans (0 difference sur 524 288 pixels chacun). Les 32 pages de la liste 196
viennent de `etages2i/stage24` et non plus de `etages2i-sprites/stage24`.

### 2. ET LE DECALAGE DE 512 EST ENFIN MESURE, PLUS RELEVE

Il venait d'un releve au pixel sur une capture (03/09), avec une dispersion de 74 pixels
qui laissait jusqu'a +-37 d'erreur par objet. **Il se lit maintenant dans la banque du
disque** : trois des sprites de Ryu y sont peints, et `situer_animes.chercher` les y
retrouve.

| script | formule + 512 | peint en | ecart |
|---|---|---|---|
| 0 | 591 | **592** | +1 |
| 6 | 720 | **720** | 0 |
| 7 | 385 | **384** | -1 |

Trois sur trois a un pixel -- le pixel deja connu depuis Sean. Le decalage est donc juste,
et c'est la cuisson qui ne l'appliquait pas.

### 3. CINQ OBJETS DE RYU QUI MANQUAIENT -- DEUX SPAWNERS INVISIBLES

En cherchant ce que la cuisson posait, deux spawners apparaissent que le balayage ne
voyait pas. Ils suivent le **meme moule** que `0x8C02E1FE` (pas 16, champs `+32`, `+558`,
`+554`, `+102`, `+106`, `+88`, `+456`, `+118`) mais **s'indexent sur le DECOR COURANT**,
`u8[0x8C6AF308]`, et non sur l'argument du chargeur :

    0x8C0233B6   nb = u16[0x8C17B918 + decor*6 + z*2]   bloc = u32[0x8C5F9C04 + decor*12 + z*4]
    0x8C02356A   nb = u16[0x8C17BBC4 + decor*6 + z*2]   bloc = u32[0x8C5F9CD0 + decor*12 + z*4]

Pour le decor 2 : **2 objets** en `0x8C17B9CE` (scripts 17 et 23, x -17 et -89) et **3** en
`0x8C17BC2E` (scripts 15, 16, 22, x -217, -265, 264). Les deux baigneurs du bassin sont le
script 23. Ryu passe de **13 a 18 objets**, son budget de motifs de 44 a 51 sur 128.

**LES AUTRES DECORS EN ONT AUSSI, ET ILS NE SONT PAS PORTES** -- 30 objets pour le premier
spawner (decors 0, 1, 3, 4, 5, 6, 10, 11, 12, 13, 16) et 36 pour le second (3, 4, 5, 6, 8,
9, 10, 12, 16). `inventaire_spawners.py` les marquait deja « *** IGNORE *** » ; ils le
restent, faute d'une demande.

### 4. L'OISEAU D'ELENA NE TOURNE PLUS EN BOUCLE

Frederic : « *l'oiseau du decor d'elena NG a toujours une animation qui tourne en boucle* ».
Le 25/09 au matin j'avais corrige sa PROFONDEUR, pas sa boucle. La boucle venait du trajet,
qui reboucle par construction. **La routine, elle, ne reboucle pas : elle l'efface.**

    etat 3, 0x8C0A6526   objet[+1] = 0      disp_flag : il DISPARAIT

et l'etat 4 attend **quatre** conditions globales avant le vol (`0x8C085B08` :
`u8[0x8C545295]`, `u16[0x8C5452E6] == 1`, `s16[0x8C5493AC] >= 2`, `u8[0x8C5493B4]`). Le vol
fini, l'etat 9 passe a l'etat 10, qui **detruit** l'objet (`0x8C032578` puis `0x8C09B12E`).
Le perchoir ne revient jamais.

`DecorAnimation` porte donc `trajet_fin` : au bout du dernier segment, l'objet s'eteint et
`reste_trajet` vaut `TRAJET_FINI` -- ni script, ni position, ni segment ne bougent plus.
L'oiseau joue ses 121 + 92 + 172 trames puis s'efface. **Les dix autres trajets du jeu
portent 0** et bouclent comme avant ; c'est verifie sur le fichier emis.

### 5. LE TEST DE CONTACT DE NEW GENERATION, LU AU MOT PRES

`0x8C085A1E(objet, r5)` ne rend pas un booleen : il rend **un compteur cumule**,
`u16[0x8C552620 + rang*2]`, ou `rang` est `u8[objet+4]`.

* **le rang 5 ne reagit jamais** : `cmp/eq #5` en tete, retour 0 ;
* le test n'a lieu que si `r5 != 0` **ou** `u8[0x8C543EC3] != 0` ; sinon la fonction se
  contente de relire le compteur ;
* il est fait pour les DEUX joueurs, `0x8C543EC8` et `0x8C5442A0`, et les deux resultats
  **s'ajoutent** au compteur.

Le sous-test, `0x8C085A94(objet, joueur)`, veut **trois** choses :

    u16[joueur+38] == 1                      le combattant est dans l'etat 1
    14 <= u16[joueur+40] < 24                son action est dans la plage 14..23
    0x8C0373B0(joueur, boite_objet, boite_joueur) != 0

les deux boites etant `0x8C1890B0 + rang*20` pour l'objet et
`0x8C189108 + u16[joueur+820]*20` pour le combattant. **C'est un coup porte, pas un
contact de corps.**

**LES ONZE SITES D'APPEL SE PARTAGENT SIX ACTEURS**, et non onze :

| routine | id | sites | porte ? |
|---|---|---|---|
| `0x8C09CE18` | 15 | `0x8C09D044` | non |
| `0x8C0A0AC8` | 29 | `0x8C0A0BD8` | **oui** -- les poissons, etages 43 et 55 |
| `0x8C0A0F78` | 31 | `0x8C0A1098`, `0x8C0A1198`, `0x8C0A1298` | non |
| `0x8C0A1438` | 32 | `0x8C0A1878`, `0x8C0A1994`, `0x8C0A1AA8` | non |
| `0x8C0A8248` | 69 | `0x8C0A834C`, `0x8C0A847C` | non |
| `0x8C0A96E4` | 75 | `0x8C0A9844` | **oui** -- le spawner `0x8C0A9806`, etage 38 |

### 6. L'INVENTAIRE DES APPELS DE NEW GENERATION -- LE CHIFFRE DU 25/09 ETAIT FAUX

J'avais ecrit « **121 appels sur 33 cibles** ». Le balayage complet des dix-neuf scripts
d'etage en donne **736 sur 164**. Le chiffre precedent etait partiel et il est retire.

**Les spawners qu'un script d'etage atteint et que la chaine n'exploite pas** -- ceux qui
allouent un objet (`0x8C09AFA4`) et dont aucune fiche ne porte l'adresse :

| spawner | appels | id | etages |
|---|---|---|---|
| `0x8C09F258` | **25** | 14 | 40, 48, 49, 50, 52 |
| `0x8C0A5488` | 9 | **48** | 48, 49, 50 |
| `0x8C0AC0D2` | 6 | ? | 48, 49, 50 |
| `0x8C0AA894` | 3 | 75 | 48, 49, 50 |
| `0x8C0A03CC` | 3 | 20 | 48, 49, 50 |
| `0x8C031354` | 3 | ? | 48, 49, 50 |
| `0x8C09E204` | 2 | 11 | 44, 45 |
| `0x8C0B168C` | 1 | ? | 41 |
| `0x8C0B13C0` | 1 | ? | 41 |
| `0x8C0ACBD4` | 1 | 89 | 41 |
| `0x8C0A83E4` | 1 | 63 | 47 |
| `0x8C0A2C94` | 1 | 34 | 40 |
| `0x8C09E3B6` | 1 | 12 | 37 |
| `0x8C03121C` | 1 | ? | 40 |

**Quatorze spawners, 58 appels.** Trois autres que j'avais comptes sont en fait exploites
(`0x8C0AC75C` 11 fiches, `0x8C0AC934` 12, `0x8C0A7B9A` 2).

**IBUKI EN CONCENTRE LA MOITIE** : cinq spawners et 24 appels sur ses trois aires (48, 49,
50). C'est le decor de New Generation le plus degarni, et de loin.

**CE QUE `0x8C09F258` FAIT, ET POURQUOI IL EST DUR.** Lu :

    0x8C09F25C   jsr 0x8C09AFA4(3)          alloue, priorite 3
    0x8C09F284   objet[+0] = 1
    0x8C09F286   objet[+8] = 14             l'id
    0x8C09F28A   objet[+6] = 16
    0x8C09F28E   objet[+4] = r4             LE TYPE, passe en argument

**Et rien d'autre** : ni position, ni script, ni palette, ni plan. Tout est dans la routine
d'etat de l'id 14 (`0x8C09CCC8`, table des acteurs `0x8C1AD9F8 + 14*4`), un repartiteur sur
`[+36]`. Le porter demande donc de decoder cette routine **pour chacun des types appeles**,
et non de lire un bloc de donnees. `0x8C0A5488` est du meme moule : `objet[+8] = 48`,
`objet[+4] = r4`, puis une suite qui depend du type.

### 7. UN FORMAT RELU AU PASSAGE : LES MORCEAUX D'UNE COUCHE

`etages.morceaux_couche` ne lisait que la **premiere** colonne du descripteur, et c'est ce
qui avait fait conclure, le 24/09, que « la tranche n'est pas un intervalle de lignes de la
banque ». `0x8C10B070` donne la vraie forme :

    [groupe] : 2 shorts d'en-tete = (PLAN, PROFONDEUR)
               puis des morceaux de 3 shorts, termines par -1
               puis 2 octets de saut
    la liste des groupes se termine par -1

Le morceau va en `+6`, `+8`, `+10` d'un enregistrement de 16 octets dont `+0`, `+2` et `+4`
sont mis a **zero** : il n'a donc pas de `x`. L'en-tete donne bien le plan et la profondeur
(`(1, 94)`, `(2, 84)`, `(3, 104)`), ce que `DEFAUT_PAR_COUCHE` posait deja.

Et il dit une chose vraie sur Ryu : sa **couche 0 n'a que trois morceaux** (y 255, 383,
511) la ou les autres decors en ont quatre -- elle ne peint pas les lignes 0..127. La
banque y porte 17 664 pixels de ciel. `morceaux_couche` n'a pas ete touche : il est juste
pour tous les decors a un seul groupe, ce qui est le cas de tous ceux mesures.

---

## LES DEUX SPAWNERS INDEXES SUR LE DECOR COURANT (25/09)

Frederic : « *porte les 66 objets manquants des autres decors 2I* ».

### 1. POURQUOI LE BALAYAGE NE LES VOYAIT PAS

`0x8C0233B6` et `0x8C02356A` suivent exactement le moule de `0x8C02E1FE` -- pas 16, champs
`+32`, `+558`, `+554`, `+102`, `+106`, `+88`, `+456`, `+118` -- mais ils lisent leurs deux
tables avec **`u8[0x8C6AF308]`, le DECOR COURANT**, et non avec l'argument du chargeur :

    0x8C0233B6   nb   = u16[0x8C17B918 + decor*6 + aire*2]
                 bloc = u32[0x8C5F9C04 + decor*12 + aire*4]
    0x8C02356A   nb   = u16[0x8C17BBC4 + decor*6 + aire*2]
                 bloc = u32[0x8C5F9CD0 + decor*12 + aire*4]

`spawners2i.blocs` cherche un bloc a partir de l'argument : il ne rendait donc rien, et
`inventaire_spawners.py` les marquait « *** IGNORE *** » depuis le debut sans qu'on sache
ce qu'ils portaient. Le `*6` et le `*12` disent **trois aires**, et ce sont bien les trois
manches.

### 2. LA NUMEROTATION DES DECORS, ETABLIE

Elle ne suit ni les `pvc` ni les etages, et deux pieges l'ont montree :

| decor | pvc | etage | comment on le sait |
|---|---|---|---|
| 8 | bg08 / bg09 | **56 et 30** | `bande_vers_decor` rend 8 pour les bandes 8 ET 9 ; et c'est le seul decor dont la table donne des blocs differents par aire -- exactement ce que `0x8C1D591C` dit d'Elena |
| 9 | bg0a | 31 | Oro |
| 10 | bg0b | 32 | Yang |
| 11 | bg0c | 33 | Ken |
| 12 | bg0d | 34 | Sean |
| 13 | bg0e | 35 | Urien |
| 14 | bg0f | 36 | Akuma -- **rien dans ces deux tables** |
| 16 | bg10 | 57 | **la meme table de scripts que Hugo, `0x8C1281F8`** : c'est le Hugo non finalise |

`etages.ETAGES` numerote les BANDES (bg0a = 15 pour bg0f), `animer2i.TABLES` les DECORS.
Les deux coexistent et ne doivent pas etre confondues.

### 3. CE QUI ETAIT DEJA LA, ET CE QUI MANQUAIT VRAIMENT

Les deux spawners portent **78 enregistrements**. Compares a `decor_objets_data.c` sur
`(etage, script)` -- deux fiches du meme etage qui portent le meme script sont le meme
objet, par quelque voie qu'il soit arrive :

    36 y etaient deja   Sean et Yang les avaient en commentaire depuis le 16/09
                        (« 8C0DEB64 0x8C0233B6 jeu 1 index 36 : 575/128 script 3... »),
                        bg10 les avait en `immediats`, Necro et Yun aussi
    42 manquaient

**Trente sont poses.** Un de plus a ete ecarte par le generateur, et a juste titre : le
bloc `0x8C17BE32` du second spawner porte le MEME objet que `0x8C17BB22` du premier pour
les aires 1 et 2 d'Elena (script 2, x 384, y 96, plan 3) -- deux spawners, un seul objet.

| etage | decor | posés | scripts |
|---|---|---|---|
| 22 | Gill | 3 | 7, 8, 9 |
| 23 | Alex | 2 | 1, 0 |
| 25 | Yun | 4 | 14, 1, 2, 3 |
| 26 | Dudley | 4 | 9, 8, 1, 10 |
| 30 | Elena (aires 1-2) | 1 | 2 |
| 31 | Oro | 1 | 7 |
| 33 | Ken | 4 | 0, 4, 3, 1 (le rang 2, script 2, etait deja porte) |
| 35 | Urien | 1 | 32 |
| **56** | **Elena, aire 0** | **9** | 2, 13, 3, 14, 4, 5, 6, 7, 12 |

Les fiches de 2nd Impact passent de **261 a 378**.

**LES NEUF D'ELENA 1 SONT LES PAROIS DE LA GORGE ET LES ARBRES A CORDES.** La note du
17/09 disait : « la bande 14 n'a qu'une couche, le ciel lent ; tout le premier plan est
fait d'objets, et deux manquaient ». Il en manquait neuf de plus, et ce sont eux -- le
rendu des fiches les montre aux deux extremites, avec les herbes et les cranes.

### 4. LES DOUZE QUI RESTENT DEHORS, ET POURQUOI

**Hugo (etage 28) et bg10 (etage 57) changent d'objets ENTRE LES MANCHES sans changer de
bande** -- c'est nouveau, et c'est lu :

    aire 0   0x8C17BA9E : scripts 17, 4        0x8C17BD1E : 19, 26, 27, 24
    aire 1   0x8C17BABE : scripts 20, 22, 4    0x8C17BD5E : 15, 26, 27, 24
    aire 2   0x8C17BAEE : scripts 20, 21, 22   0x8C17BD5E : 15, 26, 27, 24

Le port suit l'aire quand elle change de BANDE : c'est Elena, et `Bg_Aire_Suivante` le
fait. Ici la bande ne change pas, et rien ne distingue les trois aires d'un meme etage --
`variante_courante` est un TIRAGE (`rand() & 3`), pas l'aire. On pose donc l'aire 0 et on
laisse les douze autres dehors, plutot que de les afficher en permanence : **un sprite en
trop est exactement le defaut que Frederic signalait sur Ryu.**

Akuma (decor 14) n'a rien dans ces deux tables ; bg10 recoit les memes blocs que Hugo et
les avait deja en `immediats`.

### 5. UNE CORRECTION DU GENERATEUR : LA CLE DE DOUBLON PORTE L'ETAGE

`objets()` ecartait un script deja vu DANS LE DECOR. Or le decor 8 est **deux etages** --
56 pour l'aire 0, 30 pour les aires 1 et 2 -- et leurs objets se ressemblent : le script 2
de l'etage 56, en x 720, etait ecarte parce que l'etage 30 en avait deja un, en x 384.
Deux objets distincts sur deux etages : ce n'etait pas un doublon. La cle vaut maintenant
`(etage, script)`, et **les decors a un seul etage ne changent pas d'un pixel**.

### 6. LES BUDGETS DE MOTIFS APRES COUP

    22:23  23:6  24:51  25:88  26:21  27:73  28:59  29:42
    30:51  31:79  32:94  33:6  34:12  35:4  56:102  57:34

Sur 128. Le plus charge est desormais **Elena 1 (102)**, devant Yang (94) et Yun (88).
Aucun etage ne deborde, et aucun objet n'a ete ecarte pour cette raison.

---

## UNE VARIANTE PAR AIRE : LES DOUZE OBJETS DE HUGO (26/09)

Frederic : « *porte aussi les douze de hugo, ajoute une variante par aire* ».

### 1. LE CHAMP

`DecorAnimation` porte `aires`, un masque de manches pose juste apres `variante` :
bit 0 = manche 1, bit 1 = manche 2, bit 2 = manche 3. **Zero veut dire les trois**, et
c'est la valeur de tout le reste du jeu -- les 531 fiches de New Generation et les 370
autres de 2nd Impact ne changent pas d'un pixel.

`dans_la_variante` le teste en plus du masque de variante. Les deux ne se confondent pas :
`variante` est TIREE (`rand() & 3`, plus les bits 0x10/0x20 des combattants), `aires` est
la manche.

### 2. POURQUOI PAS `bg_w.area`

Parce qu'il n'avance pas partout, et qu'il sert a autre chose.

* `Bg_Aire_Suivante` sortait avant l'increment quand `Bg_Aires_Multiples()` est faux --
  donc pour les 37 etages dont la bande ne change pas, `bg_w.area` reste a 0 ;
* et `appear.c` le lit (`if (bg_w.area) ap_work = 0;`) pour **couper les entrees
  scenarisees a partir de la manche 2**. L'avancer partout aurait change les entrees de
  tous les etages -- un effet de bord non demande.

Les objets ont donc leur propre compteur, `aire_objets`, remis a zero par
`tirer_la_variante`, qui sait deja reconnaitre un nouveau match (bg_index **et**
combattants). `Bg_Aire_Suivante` l'avance pour tous les etages, et ne refait naitre les
objets d'un etage a bande unique que si `DecorObjets_ChangeParAire` dit qu'au moins un
d'entre eux porte un masque -- les quarante autres etages ne rechargent rien.

### 3. CE QUE HUGO FAIT, LU DANS SES DEUX BLOCS

    aire 0   0x8C17BA9E : sc 17, 4        0x8C17BD1E : sc 19, 26, 27, 24
    aire 1   0x8C17BABE : sc 20, 22, 4    0x8C17BD5E : sc 15, 26, 27, 24
    aire 2   0x8C17BAEE : sc 20, 21, 22   0x8C17BD5E : les memes

D'ou, objet par objet -- et c'est ce que les fiches portent :

| script | x, y | masque | ce que ca veut dire |
|---|---|---|---|
| 17 | 512, 144 | **0x1** | manche 1 seule |
| 4 | 464, 78 | **0x3** | manches 1 et 2 |
| 20 | 336, 81 | **0x6** | manches 2 et 3 |
| 22 | 512, 70 | **0x6** | manches 2 et 3 |
| 21 | 448, 56 | **0x4** | manche 3 seule |
| 19 | 224, 12 | **0x1** | manche 1 seule |
| 15 | 688, 56 | **0x6** | manches 2 et 3 |
| 26, 27, 24 | | 0 | les trois |

**bg10 partage ses blocs**, avec une difference lue : son second spawner n'a que DEUX
enregistrements aux aires 1 et 2 (`0x8C17BEC0` : sc 15 et 24), donc ses scripts 26 et 27
portent **0x1** la ou ceux de Hugo portent 0.

Quatre objets sont neufs (sc 20, 21, 22 et 15) ; les six autres etaient deja poses et ne
recevaient que leur masque -- sans lui, les scripts 17 et 19 restaient a l'ecran pendant
les manches 2 et 3, ou la console les remplace.

### 4. LES CHIFFRES

Les fiches de 2nd Impact passent de **378 a 386**. Budgets de motifs apres coup :

    22:23  23:6  24:51  25:88  26:21  27:73  28:63  29:42
    30:51  31:79  32:94  33:6   34:12  35:4   56:102 57:38

Hugo passe de 59 a 63, bg10 de 34 a 38. Aucun etage ne deborde les 128.

### 5. CE QUI RESTE OUVERT

* **Akuma (decor 14)** n'a rien dans ces deux tables : verifie, ce n'est pas un oubli.
* Les **quatorze spawners de New Generation** non portes (58 appels) restent dehors, dont
  `0x8C09F258` (25 appels, id 14) dont toute la conduite est dans une routine d'etat.
* La **table `0x8C1D591C`** dit que seul le decor 8 change de BANDE entre les manches ;
  ces deux spawners montrent que Hugo change d'OBJETS sans changer de bande. Les autres
  decors ont ete verifies : aucun autre n'est dans ce cas.

---

## LES QUATRE DE LA MANCHE DU 26/09 : HUGO, RYU, ALEX NG, ET LA PARALLAXE

Verdict de Frederic sur le lanceur `HUGO - une variante par aire` : « *je ne vois pas de
difference sur les 2 variantes du stage d'Hugo. Elena NG est corrige. Ryu 2I est corrige
au niveau des sprites mais pas des extremites du decor. Le passant du decor (celui
habille en blanc) de Alex NG n'est pas corrige* ».

### 1. HUGO : LA VARIANTE PAR AIRE ETAIT JUSTE, C'EST LA PAGE QUI LA CACHAIT

La chaine est bonne de bout en bout -- `manage.c` appelle `Bg_Aire_Suivante` sous
`Switch_Screen(0)`, qui avance `aire_objets` puis refait naitre les objets, et les masques
sont bien dans les fiches compilees : `0x1`, `0x3`, `0x6`, `0x4` sur les neuf objets de
l'etage 28. **Le defaut n'est pas dans le mecanisme, il est dans le fond.**

Les douze objets de Hugo etaient **peints dans la page deployee**. Mesure, plan proche
(liste 196) de l'etage 28, pages deployees contre la banque du disque :

    avant   13 387 pixels de difference, sur dix pages, x 256..896
    apres    1 078 pixels -- les deux elements statiques que le binaire pose, et eux seuls

`poser2i.py bg06` rend **12 309 px de cuisson a la banque** : l'empreinte des vingt-huit
fiches de l'etage, lue dans `decor_objets_data.c`. La page avait ete cuite le 04/09, les
douze objets n'ont ete portes que le 25 : le nettoyage n'avait jamais vu leur empreinte.
Une copie peinte ne change pas de manche -- d'ou « aucune difference ».

C'est le meme defaut que Ryu 2I la veille, et la meme correction.

**L'etage 57 (`bg10`, le Hugo non termine) n'a pas de banque nue dans `etages2i/` et n'est
pas dans la liste de `poser2i` : il partage les blocs de Hugo et porte donc tres
probablement les memes copies peintes. Non mesure, non corrige, nomme.**

### 2. RYU 2I : LES EXTREMITES, C'EST LA CAMERA, PAS LE FOND

Le fond est juste, et il l'est au pixel : les 32 pages de la liste 196 de l'etage 24 sont
identiques a la banque du disque. Ce qu'on voit aux bords n'est pas un fond faux, c'est un
fond **absent** -- la camera sort de ce que la bande peint.

Mesure, sur les pages deployees, bande a hauteur des combattants (y 384..447 de la
demi-banque basse) :

    le decor peint          x  128 .. 895
    0x0136..0x02C5 voit     x  118 .. 900     10 px a gauche, 5 px a droite de vide
    0x0140..0x02C0 voit     x  128 .. 895     exactement la bande peinte

Et `0x140..0x2C0` n'est pas un reglage : c'est le defaut de 3rd Strike, et c'est la course
de 383 que 2nd Impact impose lui-meme (`0x8C0D9C26` borne la camera a [0, 383] ou
[0, 495] selon `0x8C841F3C`, sans table par etage). `limit_tbl3[24]` passe donc aux trois
aires a `{ 0x0140, 0x02C0 }`.

**LA MEME MESURE SUR LES QUATORZE AUTRES**, et elle n'a pas ete appliquee -- ce n'est pas
signale :

    etage 22 Gill     peint 128..895   voit 112..884    16 px a gauche
    etage 24 Ryu      peint 128..895   voit 118..900    10 a gauche, 5 a droite  -> CORRIGE
    etage 26 Dudley   peint  80..943   voit  80..943    rien
    etage 27 Necro    peint 100..865   voit  10..1008   90 a gauche, 143 a droite
    etage 33 Ken      peint  32..991   voit -19..984    51 a gauche
    etage 34 Sean     peint 128..895   voit  17..948    111 a gauche, 53 a droite
    etage 35 Urien    peint 128..895   voit  17..948    111 a gauche, 53 a droite

Les huit autres ne debordent pas. Sean et Urien sont valides a l'ecran malgre 111 px :
c'est le signe que leur plan d'oeil n'est pas la liste 196, ou que la camera n'y va jamais.

### 3. ALEX NG : LE PASSANT EN BLANC TRAVERSE -- ECART ASSUME, ET DEMANDE

La console le fait marcher **81 pixels** : `0x8C0A88A4` lit la parite de `[+38]`, l'objet
k=3 a `[+38] = 4` (pair) et `[+52] = 400`, il part de 320 a +1 px/trame. C'est mesure et
ca reste ecrit. **Le faire traverser est donc un ecart, pas une correction de lecture.**

La longueur n'est pas inventee, elle est prise sur son jumeau : k=4 part de 912 et
s'arrete a -192, soit 192 px au-dela du bord gauche de la bande. Le miroir donne a k=3 une
arrivee a 1023 + 192 = 1215, donc **895 trames** a +1 px/trame au lieu de 81.

### 4. LA PARALLAXE DE DUDLEY -- ECART ASSUME, CONTRE LES DEUX TABLES

Frederic : « *les decors DUDLEY 2I et NG n'ont pas de parallaxe dans le jeu original* ».

**Les deux tables disent le contraire, et elles sont lues :**

    2I  0x8C1D4F48 + 4*0x20   bg04   objet 0 = 0x0C000 / 0x0E000   0,75 / 0,875
    NG  0x8C189BA0 + 7*0x20   b. 7   objet 0 = 1/1, objet 1 = 1/1, objet 2 = 0,75 / 1
    NG  0x8C189BA0 + 8*0x20   b. 8   objet 0 = 0,75 / 1,  objet 1 = 1/1

La bande 7 met deja son objet 0 a 1/1 ; c'est son objet 2, a 0,75, que la regle « le plus
lointain est le plus petit coefficient » envoie au plan lointain. Les deux aires de Dudley
NG ne disent donc pas la meme chose, et aucune des trois lectures ne dit zero.

On pose 1/1 sur son observation, pour les etages **26, 44 et 45**, par
`etages.SANS_PARALLAXE` et `etagesng.SANS_PARALLAXE` -- jamais a la main dans les `.inc`.

### 5. LES AUTRES DECORS QUI PARALLAXENT -- LA LISTE, ET LES SUSPECTS

Ce que le port applique aujourd'hui au plan lointain, apres l'ecart de Dudley. Tout ce qui
n'est pas 1 / 1 parallaxe :

    2I   22 Gill 0,25/0,625   23 Alex 0,625/0,75    24 Ryu 0,75/0,9375
         25 Yun 0,875/1,062   26 Dudley 1/1         27 Necro 1/1
         28 Hugo (couches)    29 Ibuki 0,25/0,625   30 Elena 0,5/0,5
         31 Oro 0,5/0,9375    32 Yang 0,875/1,062   33 Ken 0,75/0,75
         34 Sean 0,9375/1     35 Urien 0,375/0,75   36 Akuma 0,75/0,875

    NG   37 0,875/1     38 0,625/1      39 0,625/0,9375  40 0,25/0,625
         41 0,5/0,6875  42 0,75/0,9375  43 0,875/1,062   44 1/1   45 1/1
         46 Necro 1/1   47 Hugo 0,75/0,875             48, 49, 50 Ibuki 0,5/0,625
         51 Elena1 0,0625/0,5           52 Elena2 0,5/0,5
         53 Oro 0,5/0,9375  54 Yang1 0,75/0,9375  55 Yang2 0,875/1,062

**LES SUSPECTS, ET POURQUOI.** La paire **0,75 / 0,875** est la plus repandue de la table
de 2I : quatre decors la portent a l'objet 0 -- `bg04` (Dudley), `bg06` (Hugo), `bg0a`
(Oro) et `bg0f` (Akuma). Une valeur partagee par quatre ressemble a une valeur
**initialisee que le script d'etage n'ecrase pas**, comme les defauts deja constates aux
objets 2, 4 et 6. Dudley vient d'etre confirme par l'oeil. Restent, dans le meme cas :

    etage 36  Akuma 2I     plan lointain       0,75 / 0,875
    etage 47  Hugo NG      plan lointain       0,75 / 0,875
    etage 28  Hugo 2I      plan supplementaire 0,75 / 0,875
    etage 31  Oro 2I       plan supplementaire 0,75 / 0,875
    etage 53  Oro NG       plan supplementaire 0,75 / 0,875

**Ce sont des suspects, pas un verdict** : rien n'a ete desassemble. Ce qui trancherait,
c'est le script d'etage de chacun -- le meme balayage `mov.l Rm,@(0,Rn)` / `@(4,Rn)` qui a
donne les ecrasements de l'objet 2 pour `bg01`, `bg09` et `bg0e`, refait sur l'objet 0.
Tant qu'il n'est pas fait, l'oeil tranche : ces cinq-la sont a regarder.

### 6. LA TRANSITION DE DECOR D'ELENA -- CE QUI BLOQUE, LU

Frederic : « *il y a une animation de transition de decor entre ELENA 1 et ELENA 2 entre
les 2 premiers rounds, c'est reproductible dans 3S ?* »

**Pas en l'etat, et la raison est ecrite dans `bg_sub.c`.** Une transition animee demande
que les DEUX bandes soient a l'ecran en meme temps, donc chargees en meme temps. Or les
vingt et un etages ajoutes partagent TOUS la meme carte de pages (`bg_map_tbl`, le gabarit
de l'etage 5) : Elena 1 (bande 14, etage 51) et Elena 2 (bande 15, etage 52) portent les
MEMES numeros de page, 132..163 et 196..227. **La page 132 ne peut etre qu'une seule
image** ; les deux bandes ne peuvent pas cohabiter dans le puits de textures.

Le port fait donc ce que le chargeur du Dreamcast fait, mais sans le fondu : il echange la
bande pendant que `WipeOut` couvre l'ecran (`Switch_Screen(0)`), ce qui est le seul instant
ou un rechargement ne se voit pas.

**CE QU'IL FAUDRAIT, dans l'ordre :** donner des numeros de page distincts aux bandes d'un
meme etage a aires multiples (Ibuki 48/49/50, Dudley 44/45, Elena 51/52, Elena 2I 56/30) --
c'est le chantier deja nomme dans `bg_sub.c` --, puis lire la transition elle-meme dans New
Generation, ce qui n'a pas ete fait : on ne sait pas encore si c'est un fondu, un
panoramique de camera ou un rideau.

## LE GEL DE DUDLEY 2I : UN BUDGET PAR ÉTAGE, ET LE CONTRÔLE QUI MENTAIT (27/09)

Le verdict de Frédéric sur la manche du 26/09 : **les bords de Ryu 2I sont bons**, **la
parallaxe de Dudley est bien supprimée**, le passant blanc d'Alex NG **n'est pas corrigé**,
et **Dudley 2I gèle en fin de combat**.

### Ce que le gel disait de lui-même

`build/application/bin/fatal.log`, écrit à la seconde où le jeu s'est arrêté :

    ppgSetupTexChunk_1st: Texture is already in use
    ＣＧキャッシュが一杯になりました。×１６　ＥＸＴ２

Le message vient de `mtrans.c:2058`, dans `get_mltbuf16_ext_2`. La fonction cherche un
emplacement de motif 16×16 dans la réserve « ext 2 », n'en trouve plus, et finit par

    while (1) {}

donc **un gel, pas un plantage** — et pas une fenêtre d'erreur : seul `fatal.log` le dit.
`fin-de-round.log` s'arrête net à la trame 33060, sept secondes après un `Round_Result
0x0008`, et l'étage 26 avait été chargé 1440 trames plus tôt, variante 2.

### La cause : un budget par étage, et le sien datait d'un seul objet

`texcash.c` porte `mts_OB_page[58][2]`, **le nombre de pages de morceaux que le cache
d'objets de décor reçoit PAR ÉTAGE** — `make_texcash_work` la lit pour `mts[7]`, pas
`mts_base[7]`. Une page vaut 256 morceaux de 16×16 (`mltnum16 = page16 << 8`) et 64 de
32×32. L'entrée de l'étage 26 disait :

    { 1, 1 } /* etage 26 dudley : 1 objet, 6 cases -- le feu de circulation */

Or depuis les deux spawners indexés sur le décor courant (25/09), **Dudley porte dix
objets** : grilles 4×5, 2×11, 2×11, 2×3, 5×5, 4×5, 5×6, 5×6, 5×6 et 1×6, soit 211 cases par
trame, dont cinq objets animés de 7, 13, 10, 9 et 9 images. `verifier_objets` mesure
**218 morceaux vivants** dans la fenêtre de douze trames la plus chargée : **85 % de sa page
unique**. C'est le même défaut qu'Hugo le 15/09 (108 % de deux pages), et personne n'avait
levé son budget en lui donnant ses objets.

    etage 26 : UNE page -> QUATRE. 218 sur 1024 = 21 %.

**La parallaxe n'y est pour rien** : le seul changement du 26/09 pour cet étage est
`SPEED_X_LOIN`/`SPEED_Y_LOIN` à `0x10000` au lieu de `0xC000`/`0xE000` dans
`etages2i_plans.inc`, deux multiplicateurs de défilement. Elle est validée à l'œil et elle
n'a pas été touchée.

### Pourquoi 85 % suffit à geler : le modèle sous-compte

Deux choses que `vivants()` ne compte pas, et il faut les avoir en tête à chaque budget :

1. **la clé du cache est `(code, palette)`** — `get_mltbuf16_ext_2(mt, cc.code, palt, …)` :
   le même morceau sous deux palettes prend **deux** emplacements ;
2. **au changement d'aire**, `Bg_Aire_Suivante` refait naître les objets de la manche
   suivante alors que ceux de la précédente occupent encore leur emplacement pendant les
   douze trames de `life16`. Les deux jeux se touchent.

C'est pour ça que le gel arrive **en fin de combat** et pas pendant.

### Le contrôle mentait, et il a trouvé deux autres cas

`verifier_objets.py` comparait les morceaux vivants à une **constante** : `TAS = 1024` pour
tout 2nd Impact, `TAS_NG = 2560` pour New Generation. Il disait donc de Dudley « 218 sur
1024, 21 %, tout va bien » alors que son tas n'en tenait que 256. Il lit maintenant le
budget **réel** là où le build le pose — le tableau de `texcash.c`, et les deux macros
générées qu'il épelle (`ETAGESNG_OB_PAGE` dans `etagesng_plans.inc`,
`ETAGES2IBIS_OB_PAGE` dans `etages2ibis_plans.inc`) — et il prévient **dès 75 %**, parce que
le modèle sous-compte et que 85 % a suffi.

Il a trouvé deux étages aussitôt :

    etage 25 Yun       616 sur  768 =  80 %  ->  quatre pages, 60 %
    etage 56 Elena 2I 1295 sur  768 = 169 %  ->  dix pages, 50 %

Elena 2I aurait gelé à coup sûr. Son budget est généré : c'est `plans_variante` dans
`etages2ibis.py` qui rendait `ob_page=(3, 1)`, corrigé à `(10, 1)` — la borne de
`PATTERN_PAGES16_MAX`, que les dix-neuf étages de New Generation prennent déjà. L'include a
été régénéré **par le générateur**, en n'appelant que `ecrire_include` : une seule ligne a
changé, sans toucher aux archives ni aux pages.

**Ce qui reste, et qui n'est pas touché** : l'étage 56 porte **91 fiches pour les 56 places
d'`OBJETS_MAX`**, donc 35 objets sont écartés en silence. Après correction, les étages les
plus près de la ligne sont 30 (72 %), 37 (69 %), 51 (66 %), 28 (65 %) et 24 (64 %).

### Alex NG : le passant blanc, et c'était mon ordre de segments

Le trajet était juste et la longueur mesurée ; c'est l'**ordre** qui était faux. La liste
boucle **sur son premier segment**, et j'y avais mis l'attente ENTRE DEUX PASSAGES, 1280
trames — **vingt et une secondes** plantées avant son premier pas. Un round se finit avant.

On ne peut pas la mettre en queue : la position de dessin est masquée,

    decor_objets.c : *x = (nos[k].anim->x + (nos[k].px >> 16)) & 0x3FF;

la bande fait 1024 et ce qui sort d'un bord revient par l'autre. Le passant arrive à 1215,
soit **191 à l'écran** : il attendrait ses 1280 trames planté en vue, à gauche.

Le premier segment porte donc la **première** attente de la console, **32 trames**, celle de
`[+54]` de l'enregistrement, qui est lue :

    n01o9_trajet  = { 32, 0, 0, 0, 0,  895,  256, 0, 1, 0 }   k=3, le blanc
    n01o10_trajet = { 32, 0, 0, 0, 0, 1105, -256, 0, 1, 0 }   k=4, son jumeau

**L'écart est là, et il est assumé** : entre deux passages le port attend 32 trames au lieu
des 1280 tirées parmi seize (`u16[0x8C1B251C + 2 * indice]`), donc les deux passants
traversent toutes les 15,5 secondes au lieu d'une fois ou deux par round. Les seize durées
restent écrites dans `objetsng.py` : remettre 1280 en tête fait reperdre le premier passage.

### Le build

`CMakeFiles/` n'était pas dans le transfert : il a fallu relancer `cmake .` une fois dans
`C:\Temp3sx\build` avant `ninja`. Reconstruction complète, **705 étapes, aucun avertissement,
aucune erreur**. Cliché du jour : `build/3sx-27-09.exe`, 34 516 723 octets. Chronologie
vérifiée — `texcash.c` 11:43, l'include 11:48, `decor_objets_data.c` 11:49, l'exe 11:53.

La régénération de la donnée a suivi l'ordre imposé, `animer2i.py --ecrire` puis
`animerng.py --ecrire` : 386 fiches de 2I + 531 de NG = **917**, comme avant, et le fichier
n'a perdu que **quatre octets** — exactement les deux `1280` devenus `32`.

## ELENA 2I AU CHANGEMENT DE BANDE, ET LES PASSANTS D'ALEX AU BON RYTHME (27/09, soir)

Verdict de Frédéric sur la livraison du matin : **Dudley 2I tient un combat entier** et **le
décor de Hugo varie d'une manche à l'autre** — les deux sont acquis. Restent deux choses :
Elena 2I « plante toujours entre le 1er et le 2e round, et au 1er round il manque des cordes
du ponton », et chez Alex « il y en a plusieurs maintenant, qui viennent de droite et de
gauche, dont un seul disparaît en pleine animation. Respecte le nombre et la fréquence
d'apparition des passants de la version dreamcast. »

### Elena 2I : le tas rétrécissait au changement de bande

Elena est **le seul décor de 2nd Impact qui change de BANDE entre les manches** — table des
aires `0x8C1D591C`, décor 8 : bandes 8, 9, 9, soit l'étage 56 à la manche 1 puis l'étage 30.
C'est exactement là que ça plante.

Le matin, l'étage 56 était passé à dix pages de cache (2560 morceaux) et l'étage 30 était
resté à quatre (1024). **Le tas rétrécissait donc au changement de bande**, au moment même
où les morceaux de la manche précédente vivent encore les douze trames de `life16`. L'étage
30 passe à dix pages, et la règle se retient :

> **Les deux bandes d'un même décor portent le même budget de morceaux.** Il n'y a qu'Elena
> dans 2nd Impact ; New Generation donne déjà dix pages à tous ses étages, donc le cas ne s'y
> pose pas.

### Le gel est maintenant instrumenté, et il nommera sa cause

Trois causes restaient possibles et je ne voulais pas en choisir une au jugé. `mtrans.c`,
juste avant le `while (1) {}` de `get_mltbuf16_ext_2`, écrit désormais dans `fin-de-round.log`
et dans `fatal.log` :

    etage <celui dont la reserve a ete taillee>, <utilises> morceaux sur <total>,
    libres <n>, palette <p>, code bas <c>

et les trois lectures se séparent :

    utilises = total, libres 0   la reserve est trop petite
    utilises < total, libres 0   une entree de `cpat` a ete retrouvee mais ses
                                 emplacements sont vides -- le piege du 24/09
    utilises monte a code egal   la palette double les emplacements (la cle est
                                 `(code, palt)`, pas `code` seul)

Deux pièges d'outillage au passage, qui ont coûté deux compilations : **`TraceFin` n'est pas
variadique** — `void TraceFin(const char* fmt, s32 a, s32 b, s32 c)`, exactement trois
entiers — et **`flLogOut` est déclaré `__dead2`**, il peut ne pas revenir : la trace doit
donc passer AVANT lui. Et `bg_w` n'est pas visible depuis `mtrans.c` : c'est
`mts_ob_curr_stage` qu'on lit, la variable que `make_texcash_work` écrivait depuis toujours
**sans que personne ne la lise**. Elle dit l'étage dont la réserve a été taillée, ce qui est
précisément ce qu'on veut savoir quand un décor change de bande.

### Les cordes du ponton : c'est un choix, pas un défaut

L'étage 56 porte **quatre-vingt-onze objets** et le port n'en montre que `OBJETS_MAX` = 56.
L'écrêtage de `DecorObjets_Combien` garde les 56 **premiers** de la variante, et les 35
écartés sont, dans l'ordre du tableau :

    scripts 13 et 14, NEUF instances chacun  (element 752,96 et 272,96)  <- les cordes
    plus les trois reflets du lac (entrees 6 et 7 du magasin de la banque 0)

Ce sont exactement les objets portés le 25/09. La borne est **double**, et c'est pour ça que
je ne l'ai pas levée seul :

1. **le rang tient sur six bits** dans l'identité de motif —
   `code = GROUPE | generation << 14 | rang << 8 | image` — donc **64 au plus**, jamais 91 ;
   et la génération sur deux bits est ce qui a corrigé le gel de la seconde entrée (24/09) ;
2. **chaque objet de décor prend une place au tas d'effets du jeu** (`EFFECT_MAX` = 128) : à
   56 il en reste 72 au jeu, à 64 il n'en resterait que 64.

Trois voies, et **le rang fixe l'emplacement de palette** (`+ k` à partir du premier), donc
toute réorganisation change les couleurs de l'étage et demande une revalidation à l'œil :

* monter `OBJETS_MAX` à 64 : huit objets de plus, huit places d'effet en moins pour le jeu ;
* garder 56 et remonter les cordes dans l'ordre : elles reviennent, autre chose part ;
* entrelacer les instances au lieu de les grouper par script, pour que chaque élément garde
  quelques copies plutôt que des éléments entiers disparaissent.

### Alex NG : le masque expliquait la disparition ET donnait la mesure

« Un seul disparaît en pleine animation » : c'est le repli de la position de dessin,
`*x = (anim->x + (px >> 16)) & 0x3FF`. Avec 895 trames, le passant blanc finissait à 1215,
soit **191 à l'écran — encore en vue** — et le bouclage de sa liste le ramenait d'un coup à
320. Un saut, vu comme une disparition. Son jumeau finissait à -193, soit 831, et sautait de
même.

D'où la mesure : **une marche d'exactement une largeur de bande**, 1024 trames à 1 px/trame.
`320 + 1024 = 1344`, et `1344 & 0x3FF = 320` ; `912 - 1024 = -112`, et `-112 & 0x3FF = 912`.
L'objet revient sur sa naissance, et le bouclage ne déplace plus rien.

    n01o9_trajet  = { 32, 0, 0, 0, 0,  1024,  256, 0, 1, 0,  392, 0, 0, 0, 0 }
    n01o10_trajet = { 32, 0, 0, 0, 0,  1024, -256, 0, 1, 0,  512, 0, 0, 0, 0 }

**L'attente est passée en queue**, où elle ne se voit pas : l'objet y est déjà sur sa
naissance, debout, image tenue — c'est mot pour mot ce que fait la console, dont l'état 2
(`0x8C0A888A`) ne décrémente que `[+54]` sans avancer le script. Le premier segment garde la
première attente de la console, 32 trames.

**La fréquence est celle de la console, et elle se calcule** : là-bas un passage coûte
l'attente tirée plus la marche, soit 1289,5 + 81 = 1370 trames en moyenne, une apparition
toutes les 22,8 secondes par passant. Ici 32 + 1024 + 392 = 1448 trames (24,1 s) pour k=3 et
32 + 1024 + 512 = 1568 (26,1 s) pour k=4. **Les deux attentes de queue sont différentes
exprès** : avec la même, les deux passants marcheraient éternellement ensemble — ce que
Frédéric a vu — alors que la console les tire séparément ; deux cycles qui ne se divisent pas
les font dériver. 392 et 512 sont deux des seize durées lues (`u16[0x8C1B251C + 2 * indice]`)
et le choix parmi les seize est assumé, comme l'était celui de 1280. **Le nombre, lui, est
celui de la console : deux passants.**

Cliché du soir : `build/3sx-27-09-soir.exe`, 34 516 836 octets.

## 2I RATTRAPE NEW GENERATION : LA TRANCHE A DEUX BORNES (27/09, fin de journée)

Verdicts de Frédéric : **Dudley 2I tient un combat entier**, **le décor de Hugo varie d'une
manche à l'autre**, **le décor d'Alex NG est validé**, et **Elena 2I ne plante plus** — les
dix pages données à l'étage 30 ont réglé le gel du changement de bande. Restent deux
choses : « *au 1er round il manque des cordes du ponton* » et « *le décor du 2e round est
glitché* ».

### La question qui a tout débloqué

Sur les cordes, j'avais posé trois voies — monter `OBJETS_MAX`, réordonner, entrelacer — et
Frédéric a répondu autre chose : « *de mémoire on ne cuit plus rien dans le jeu* », puis
**« pourquoi ne pas faire comme pour les autres décors ? »**.

La réponse était dans `animerng.py`, écrite le 17/09 :

    # LES CASES D'UN RANG : 64 DEPUIS LE 17/09/2026. Les 32 venaient de la cle de cache
    # `rang << 11 | image << 5 | case` ; elle n'existe plus [...] `animer2i` garde 32 :
    # 2I est valide.

**2nd Impact avait été laissé en arrière exprès.** Son générateur découpait encore les objets
trop larges en tranches de 32 cases, au nom d'une clé de cache supprimée le 16/09 ; la seule
borne restante est `CASES_MAX` de `decor_objets.c`, qui vaut **64**. New Generation est passé
à 64 le lendemain, 2I non, pour ne pas déranger ce qui était validé.

C'est ce décalage qui coûtait les cordes. **L'étage 56 ne porte pas 91 objets : il en porte
quinze** (`a56o1` à `a56o14`, plus deux plans), découpés en **76 morceaux** de deux colonnes.
`OBJETS_MAX` n'en montre que 56, donc trente-cinq tombaient — dont les vingt herbes et cordes
du pont (id 122) et les neuf « arbres à cordes ». New Generation sert les **mêmes quatre
éléments** (720,64 / 304,64 / 784,32 / 240,32) en **quatre fiches entières**, `2×9` et `4×11`.

### La tranche a DEUX bornes, et la seconde se compte

Le premier essai à 64 a tué la génération :

    bg0f en 0,0, morceau 7 : 67 couleurs, une palette n'en tient que 63

C'est `indexer` (`animer2i.py`) qui s'arrête, sur un **plan** d'Akuma. Une tranche ne porte
qu'**une** palette de 64 entrées dont la première est transparente : **63 couleurs**. Plus la
tranche est large, plus elle doit en faire tenir. Voilà la vraie raison des 32, que le
commentaire de 2I n'avait jamais écrite.

`morceaux_de_page` part donc désormais de la tranche la plus large que le cache autorise et
la **rétrécit de moitié tant qu'une tranche dépasse 63 couleurs** — la largeur se mesure au
lieu d'être choisie pour la pire page. La fonction reçoit `decor` pour pouvoir composer les
images et compter.

### Ce que le recoupage donne

    fiches de 2I        386  ->  268
    etage 56             91  ->   46   (pour 56 places : plus rien n'est ecrete)
    cordes du pont       20  ->   10   morceaux, TOUS gardes
    motifs de l'etage 56 102  ->   53   sur 128
    objets ecartes faute de palette :   ZERO

Et les budgets de morceaux retombent partout : 25 passe de 80 % à 60 % de son tas, 32 de
34 % à 34 % avec deux fois moins de fiches, 56 tient à 50 % de ses dix pages. `OBJETS_MAX`
**reste à 56** — le jeu garde ses 72 places d'effet sur les 128 d'`EFFECT_MAX` — rien n'est
cuit, et les cordes restent des **objets**, prêts pour la chute du pont le jour où on la
déclenchera.

**CE QU'IL FAUT REGARDER : les quinze décors de 2nd Impact ont leurs RANGS DÉPLACÉS.** Les
pixels ne changent pas — les morceaux se rejoignent au pixel près, c'est la même composition
tranchée autrement — mais le rang fixe l'emplacement de palette (`+ k` à partir du premier),
et tout a bougé. Gill, Alex, Ryu, Yun, Dudley, Necro, Hugo, Ibuki, Elena, Oro, Yang, Ken,
Sean, Urien, Akuma sont tous à revoir, y compris ceux qui étaient validés. New Generation n'a
pas bougé d'un octet.

### Le décor glitché du 2e round : ce qui est déjà lu

La capture montre **deux bandes à la fois** — l'éléphant de la bande 9 à gauche, la cascade
de la bande 8 à droite, frontière verticale nette. Le journal montre pourtant un changement
de bande propre : `etage 30, aire 0 -> bg_index 56`, `Bg_Off_R 0x000f`,
`TexRemix_SetStage 30`, `manche suivante : aire 1 -> bg_index 30`.

Ce qui est établi :

* `TexRemix_SetStage` ne fait que **noter** l'étage ; la substitution n'a lieu qu'au moment
  où le moteur **téléverse** une page. Une page qu'il croit déjà résidente n'est jamais
  redemandée, et `tex_remix` n'est pas consulté.
* les index de texture valent `stg * 64 + 0x84`, où `stg` est **l'index du premier plan
  utilisé**, pas un numéro d'étage : les deux bandes d'un même décor demandent donc **les
  mêmes index**.
* `pages-manquantes.log` compte **1408 pages non installées**, toutes à `accnum 96,
  textures 96`. C'est `PPGFile.c:1038` : quand l'archive n'a plus de textures à donner, la
  page n'est pas installée et les pixels précédents restent. Le commentaire du port le disait
  déjà — « dès qu'un étage réclame un plan de plus que son donneur n'en a ».

Ce qui n'est **pas** établi : quel étage affame l'archive. Une trace a donc été posée dans
`bg.c`, juste avant le chargement des pages de réécriture — elle écrit l'étage, son plan de
base, le nombre de pages de réécriture demandées et ce que l'archive a déjà consommé. Le
prochain essai d'Elena tranchera entre les deux voies : renuméroter les pages par aire, ou
forcer le re-téléversement.

Cliché : `build/3sx-27-09-recoupe.exe`, 34 458 626 octets.

### CORRECTION, LE JOUR MÊME : la largeur ne se change pas pour tout le monde

Ce qui précède décrit un `CASES_MAX` passé à 64 **globalement**, et annonce que les quinze
décors de 2nd Impact sont à revoir. **C'était une erreur, et Frédéric l'a vue tout de
suite** : « *je ne comprends pas ce que tu as fait, pourquoi tu as modifié des décors qui
fonctionnaient ?* »

Le défaut ne touchait qu'**un** étage, le 56. Changer une constante globale pour le corriger
déplaçait les rangs — donc les emplacements de palette — de quatorze décors déjà validés.
C'est précisément « défaire ce qui marche ».

La largeur est donc une **liste nommée**, dans `animer2i.py` :

    CASES_MAX    = 32        # la largeur de tout le monde
    CASES_LARGES = {56}      # les etages qui ont droit a 64, avec leur raison

`morceaux_objet(o, etage)` et `morceaux_de_page(o, decor, etage)` prennent l'étage et
demandent `cases_max_de(etage)`. **On n'élargit un décor que le jour où `verifier_objets`
montre qu'`OBJETS_MAX` l'écrête, et on le regarde seul.**

Vérifié par empreinte, étage par étage, sur toutes les lignes qui portent leur préfixe —
tuiles, durées, palettes, fiches — en SHA-256 contre le fichier d'avant :

    22 23 24 25 26 27 28 29 30 31 32 33 34 35 36 57   tous IDENTIQUES
    56                                                 DIFFERENT, le seul

Le compte le recoupe : 386 − 91 + 46 = **341 fiches de 2I**, et les budgets de motifs sont
revenus à leurs valeurs d'avant partout (22:23, 24:51, 25:88, 32:94…) sauf 56, qui passe de
102 à 53. New Generation n'a pas été touché.

Ce qu'Elena 2I gagne, et elle seule : **91 fiches → 46** pour 56 places, les cordes du pont
de **20 morceaux → 10, toutes gardées**, zéro objet écarté. `OBJETS_MAX` reste à 56, le jeu
garde ses 72 places d'effet sur 128, rien n'est cuit, et les cordes restent des objets.

Cliché : `build/3sx-27-09-elena.exe`, 34 496 165 octets.

## ELENA 2I : LA BASCULE N'ÉTAIT SUIVIE QU'À MOITIÉ, DEUX FOIS (27/09, nuit)

Frédéric, sur le décor glitché du 2e round : **« ce décor fonctionnait correctement, retrouve
comment »**. Il avait raison, et la réponse était écrite dans nos propres commentaires.

### Comment il fonctionnait

`bg_index_tbl[30]` valait **`{ 30, 30, 30 }`** : Elena 2I restait sur la même bande les trois
manches. Un seul chargement, aucun mélange possible.

Cette bascule avait **déjà été retirée le 16/09**, et `bg_data.c` dit pourquoi :

> « C'est exactement la forme qu'on avait dû abandonner le 16/09 — le portage ne suivait
> alors l'aire qu'**à moitié**, `Bg_Texture_Load` prenant pages, profondeurs et plans à
> `bg_w.stage` pendant que les objets suivaient `bg_index`. »

Elle est revenue le **25/09**, quand `Bg_Plans_Source` a fait suivre `bg_index` à **toutes
les tables de plans**. Sauf qu'elle n'était toujours suivie qu'à moitié : **l'archive de
pages, elle, suit encore `bg_w.stage`**.

### Ce que la trace a mesuré

    etage 56, plan de base 4, pages de reecriture 0   deja consommees 96
    etage 30, plan de base 3, pages de reecriture 0   deja consommees 96

`Push_LDREQ_Queue_BG(bg_w.stage)` (menu.c, et quatre autres sites) prend `color_file[30]`,
donc le fichier **1543.bin — 96 textures, trois plans**. Or la bande 56 de la première manche
en a **quatre** et en demande 128. Son archive `1569.bin` en contient bien 128 (vérifié :
`pTEX` comptés), mais elle n'est jamais chargée.

Les 32 pages du quatrième plan ne sont donc jamais installées — `ppgSetupTexChunk_2nd` rend
la main dès que `textures <= accnum`, et `pages-manquantes.log` en comptait 1408 sur la
session. Leurs emplacements gardent ce qu'ils contenaient, et à la manche 2 les deux bandes
se voient à la fois.

**Les pages de réécriture n'y étaient pour rien** : la trace dit `pages de reecriture 0`.
C'était une fausse piste, et c'est la mesure qui l'a écartée.

### La correction

`Bg_Archive_Source(etage)` (bg_sub.c) rend la bande qui demande **le plus de plans** parmi
les trois aires, et `Push_LDREQ_Queue_BG` l'appelle. Pour tout étage dont les trois aires
sont la même — tous les autres — elle rend l'étage **inchangé, par construction**. Seule
Elena 2I charge désormais `1569.bin` et ses quatre plans ; les deux bandes prennent leurs
pixels dans `tex_remix` comme avant.

**Le repli tient en une ligne** : `bg_data.c`, `{ 56, 30, 30 }` → `{ 30, 30, 30 }`. On
retrouve l'état du 16/09, celui qui marchait, au prix de la transition du pont.

Cliché : `build/3sx-27-09-archive.exe`, 34 496 713 octets. Compilation : 104 étapes, aucun
avertissement.


## Elena 1 refaite par son descripteur de scène — 28/09/2026

Frédéric, après une semaine d'essais qui n'ont rien donné : « *arrête de chercher,
reconstruit correctement le décor, tu as une capture d'écran, la version dreamcast,
l'exemple de la version NG. Inclus aussi les animations de sprites.* »

La version NG était la bonne piste, et elle se **mesure**. J'ai assemblé les pages que le
jeu charge vraiment — `resources/tex_remix/stage<N>`, pas le dossier de travail — et relevé
les bornes peintes :

| plan | Elena NG (étage 52) | Elena 2I (étage 30), avant |
|---|---|---|
| liste 132 | 393 216 px, colonnes 128..895, **0 creuse** | 464 896 px, colonnes 0..1023, **96 creuses** |
| liste 196 | 183 383 px, colonnes 128..895, lignes 585..1023 | 291 964 px, colonnes 0..1023, 96 creuses |

**La scène d'Elena fait 768 de large, posée en 128.** La nôtre montait la demi-banque
entière (1024) et la faisait **tourner** de 128 (`statiques2i.DECALAGE_ELENA`). Le décalage
était le bon ; la rotation, non : elle ramenait les colonnes 896..1023 de la banque sur la
scène 0..127, et laissait 96 colonnes vides au milieu — le rectangle de la capture.

Et ces colonnes-là ne sont pas du décor. Mes propres notes du 15/09
(`animer2i.PAGES_ANIMEES["bg08"]`) les désignent : ce sont les **trois trames tournées** de
la cascade, rangées en x 864 de la banque. On collait un bout de cascade au bord de la page,
et on laissait un trou à côté.

### Le descripteur, lu

`descripteurs2i.py` annonce depuis le 16/09 que « *cinq décors en ont un propre : Hugo (6),
IBUKI (7), les deux Elena (8, 9) et Akuma (15)* ». Seul Ibuki avait été fait. Les cas 8 et 9
du moteur de décor sont désassemblés :

    cas 9 (0x8C0F8EB8), la chute -- notre étage 30
        mov.l  0x8C0F8F84,r4 ; bsr 0x8C0F8AE0      la base
        mov.l  @r14,r13 ; add #-80,r13             emplacement 0 : page - 80
        cmp/pz ... cmp/ge #12 ... mov #0,r13       borné à 0..11, sinon 0
        mov.l  0x8C0F8F88,r0 ; mov.l @(r0,r4),r4   TABLE de douze descripteurs
        mov.l  @(4,r14),r14 ; ... cmp/ge #2 ...    emplacement 1 : borné à 0..1
        mov.l  0x8C0F8F8C,r0 ; mov.l @(r0,r4),r4   TABLE de deux descripteurs

et la base tient en quatre rectangles :

    couche 0  scène  128,512   768x352  <- banque 0    0,0     le ciel, la falaise
    couche 0  scène  128,864   256x160  <- banque 0    0,352   le bas à gauche du trou
    couche 0  scène  704,864   192x160  <- banque 0  576,352   le bas à droite du trou
    couche 1  scène  128,576   768x384  <- banque 0    0,576   le plan proche

**Trois choses que la demi-banque nue ne pouvait pas donner.**

1. **La scène fait 768, posée en 128** — plus de rotation, plus de trou.
2. **Le plan proche commence en 576, pas en 512.** Les lignes 512..575 de la banque sont la
   *réserve* du bord de l'eau ; montées en couche, elles posaient une bande de 768 × 64 en
   **haut** du plan proche, flottant au-dessus des arbres avec rien dessous.
3. **Le bas du plan proche est une animation à deux états** : la scène 128,960 (768 × 64)
   prend la banque en v 512 **ou** v 960 selon l'emplacement 1. On y montait v 960 en dur.

Sur ce dernier point, le relevé des douze entrées d'animation de pages de 2I tranche :
aucune ne pilote l'emplacement 1 du décor 9 (les entrées 2, 5, 7 et 9 y sont, mais leurs
pages sortent des bornes 0..1 du cas 9, donc l'index retombe sur 0). **L'état 0 est le
permanent** — c'est lui qu'on cuit.

Le trou de 320 × 160 en scène 384,864 est laissé par la base elle-même : elle peint
128..383 et 704..895 sur ces lignes, pas le milieu. L'entrée 0 (`dest` 384,352 lu dans
`0x8C17D3DC`, 304 × 160) vient l'y remplir, et le descripteur confirme le x 384 au pixel.

### Le résultat, mesuré

| plan | Elena 2I (étage 30), après |
|---|---|
| liste 132 | **393 216 px**, colonnes 128..895, **0 creuse**, lignes 512..1023 |
| liste 196 | 166 120 px, colonnes 128..895, lignes **585**..1023 |

Soit, au pixel près pour la 132 et à la ligne près pour la 196, **la géométrie d'Elena NG**.

Objets animés régénérés dans la foulée : `animer2i.py --ecrire` puis `animerng.py --ecrire`,
341 + 531 = 872 fiches.

**L'étage 56 (le pont) n'est pas touché.** Frédéric l'a validé le 27/09, et son descripteur
(cas 8 : base en 256,512 de 512 × 416, la bande de 16 en 928, celle de 64 en 944) confirme
ce que `statiques2i.variante_elena` fait déjà. Aucun autre décor n'est modifié.

**À reprendre** : les entrées 1 (dest scène 496,912, 112 × 80, pages 89/96/97) et 2 (dest
scène 592,896, 32 × 16, pages 82/92/93) tombent toutes deux **dans** le rectangle de la
cascade d'Elena 1, mais leurs pages ne correspondent à aucun indice de ses tables. Elles ne
sont attribuées à aucun décor : régulier n'est pas identifié, et on n'invente pas.

Cliché : `build/3sx-28-09-elena-descripteur.exe`, 34 496 713 octets.


## La ligne noire d'Alex — et les dix-huit autres — 28/09/2026

Frédéric : « *ALEX une ligne noire en arrière plan notifiée plein de fois mais jamais
traitée* ». Mesure, sur la banque que le descripteur de NG désigne pour sa couche 2 :

    bg_set01, banque 0, u 512..1023, v 0..255  (le rectangle du ciel)
        43 520 px peints, tous dans u 560..831, v 0..159. Le reste est VIDE.

Le plan le plus lointain d'Alex est **un timbre de 272 × 160 dans une page de 1024 × 512** —
huit pour cent. Partout où les deux plans plus proches ne couvrent pas, l'écran montre le
noir, et l'endroit le plus visible est la ruelle entre les deux immeubles du fond (scène
x 779..807), deux à trois colonnes sur 240 lignes : **la ligne noire**.

Ce fichier le disait déjà sans en tirer la conséquence, dans la note du drapeau `+17` de
`descripteursng.py` : « *ces couches n'ont rien derrière elles, un trou y montre déjà du
noir* ». Les trois rectangles d'Alex portent d'ailleurs `drapeau = 0` (liste translucide,
alpha respecté) et la couleur sous l'alpha nul est **noir pur, une seule valeur** : rien à
espérer du côté de l'opacité forcée.

### Ce n'est pas un cas isolé

    étage 37 GILL     171 008 px vides      étage 47 HUGO      194 831
    étage 38 ALEX     480 768               étage 48 IBUKI 1   336 896
    étage 39 SEAN     218 877               étage 49 IBUKI 2   358 400
    étage 40 RYU      386 048               étage 50 IBUKI 3   358 400
    étage 41 KEN      165 888               étage 51 ELENA 1    74 286
    étage 42 YUN 1    303 104               étage 52 ELENA 2   131 072
    étage 43 YUN 2    131 072               étage 53 ORO       448 256
    étage 44 DUDLEY 1 324 249               étage 54 YANG 1    143 360
    étage 45 DUDLEY 2 324 249               étage 55 YANG 2    131 072
    étage 46 NECRO    409 600

**Les dix-neuf.** Et c'est la même famille que trois verdicts qu'on traînait : « KEN variant
bain à ciel ouvert : les extrémités gauche et droite ne sont pas affichées (décor pas assez
large) » (28/09), « KEN ciel à droite manquant » et « ORO le ciel ne couvre pas toute la
zone » (17/09).

### La correction

`couchesng.combler_le_fond(plan)` : chaque pixel vide de la **liste 132 seule** prend la
couleur du pixel **peint le plus proche** de la même page (transformée de distance
euclidienne). Aucune couleur n'est inventée — un ciel en dégradé se prolonge en dégradé, un
fond qui couvre déjà tout n'est pas touché — et rien ne peut disparaître, puisqu'on n'écrit
que là où il n'y avait rien.

**Et seulement la couche la plus lointaine.** Les plans du milieu et de devant doivent garder
leurs trous : c'est par eux qu'on voit ce qu'il y a derrière.

Contrôle de format : aucune page ne dépasse 256 couleurs après remplissage — les 19 étages
restent en `.tex` version 2 (8 bits, 17 424 o). Poids total de `tex_remix` : 52,3 Mo.

Une ligne à retirer si le verdict est mauvais : l'appel dans `couchesng.main`.


## La commande 0x29 est un déplacement — 28/09/2026

Frédéric : « *DUDLEY, dans le variant de jour, le punk de gauche marche vers l'arrière puis
fait un saut vers l'avant* ».

Son script — le 17 de la bande 8, le punk au skate, id 68 — porte douze enregistrements de
durée nulle que `script_images` traversait sans rien en faire :

    8C0D62D0  29 00 00 00 00 04 00 00
    8C0D6368  29 00 00 00 00 F4 00 00

Le gestionnaire de la commande `0x29` est l'entrée 41 de la table `0x8C1C5BC8`,
**`0x8C0B5A64`**, et il se lit entièrement :

    mov.w @(2,r5),r0     le mot +2 choisit l'AXE : 0 -> x, 2 -> y
    mov.b @(10,r4),r0    l'octet +10 de l'objet est son MIROIR
    mov.w @(4,r5),r0     le mot +4, SIGNÉ, est le pas
    shll8 r0 ; add/sub   u32[objet + 100] += pas << 8   (soustrait si l'objet est miroité)

`u32[+100]` est le x en 16.16 — son entier est `[+102]`, ce qu'`objetsng` avait lu sur Alex.
Donc `pas << 8` vaut **`pas / 256` pixels**, et les trois valeurs du punk se lisent :
`0x0400` = +4, `0x0800` = +8, `0xF400` = **−12**.

Somme sur son script : **+48 sur les huit premières commandes, −48 sur les quatre
dernières**. Le punk roule en avant puis revient, et il retombe exactement sur sa place. On
ne jouait ni l'un ni l'autre : restaient les images, dont les quatre dernières (21340..21343)
sont dessinées pour un corps qui a reculé de 48 pixels. **D'où le saut.**

La correction est un `trajet` dérivé du script (`animerng.trajet_du_script`) : un segment
par image, `{ durée, vx, vy, -1, 0 }`, vx en 1/256 de pixel par trame — l'unité même du
champ. Vingt-huit segments pour le punk, somme 2/256 de pixel par tour (l'arrondi).

**On ne le pose que si la somme est nulle.** Le contrat de `trajet` (`decor_objets.c`) est
que « la liste boucle sur son premier segment, où l'objet retrouve sa position de
naissance ». Le seul autre script de NG qui porte des `0x29` est le **11 de SEAN** (bande 2,
x 704) : **+92 pixels par tour**. Sa routine d'origine doit le replacer, et on ne sait pas
encore où — laissé tel quel.

**Un défaut d'émission trouvé au passage** : `animerng` écrivait le pointeur de trajet sans
avoir écrit les champs de comportement qui le précèdent. Tous les objets à trajet en avaient
un jusqu'ici, et le défaut ne se voyait pas ; le punk, dont le trajet vient de son script,
n'en a pas — son trajet partait dans le champ `comportement`. Même garde que pour `echelle`
et `boite`.

## Le vent d'Ibuki, servi en partie — 28/09/2026

Frédéric : « *IBUKI les bambous de gauche qui ne bougent pas sous l'effet du vent, il faut
ajouter cette animation* ». Elle existe, elle est lue depuis le 17/09, et elle était **jetée
en entier** par le budget :

| étage | pris par le reste | le vent sur la couche 1 | total |
|---|---|---|---|
| 48 | 20 rangs, 1893 morceaux | 7 rangs, 984 morceaux, 21 motifs | **2877** / 2240 |
| 49 | 17 rangs, 1542 morceaux | idem | **2526** / 2240 |
| 50 | 14 rangs, 1464 morceaux | idem | **2448** / 2240 |

Les rangs (27 sur 56) et les motifs (103 sur 128) passaient largement : seul le compte de
MORCEAUX bloquait, et de peu.

Or une animation de pages est déjà **découpée en tranches de colonnes**
(`pagesng.morceler`), et chaque tranche est un objet à part entière : rien n'oblige à les
prendre toutes. `budget_pages` en garde donc autant qu'il en tient, **de la gauche vers la
droite** — ce sont les bambous de gauche.

    étage 48   1 tranche sur 7    rangs 21/56  morceaux 2070/2240  motifs 85/128
    étage 49   4 tranches sur 7   rangs 21/56  morceaux 2229/2240  motifs 64/128
    étage 50   4 tranches sur 7   rangs 18/56  morceaux 2151/2240  motifs 61/128

## SEAN : deux réponses, pas deux corrections — 28/09/2026

* « *le passant en blanc du décor d'Alex est présent dans le décor (à supprimer ?)* » — le
  décor de Sean appelle **trois fois** le même engendreur qu'Alex, `0x8C0A88D6` (id 64),
  avec ses propres enregistrements et ses propres scripts (2, 3 et 11), aux x 448, 656 et
  704. Ce n'est pas une fuite du décor d'Alex : **New Generation met bien ce passant chez
  Sean**. À supprimer seulement si tu le décides.
* « *les variants ne changent plus entre les rounds ?* » — la table des aires
  (`0x8C18A804`, six octets par décor) donne à Sean **la même bande pour ses trois aires**,
  comme Gill, Alex, Necro, Hugo et Oro. Les sept qui changent sont Ryu, Yun, Dudley, Ibuki,
  Elena, Yang et Ken. Sean n'a jamais eu de variante.

## Ce qui reste de la liste du 28/09

* **ALEX, la ligne noire** — localisée au pixel : la ruelle entre les deux immeubles du
  fond, scène x 779..807, lignes 672..910. Son plan du fond ne peint que 43 520 px sur
  524 288. Le bouchage général du fond la fermerait, mais son **gratte-ciel** (script 2,
  plan 3, priorité 104) est à la MÊME profondeur que ce plan, et `animer2i` a mesuré qu'à
  profondeur égale c'est le plan qui gagne : le boucher effacerait le gratte-ciel. La suite
  est de **cuire les fiches statiques du fond DANS la page du fond** — elles ne bougent pas,
  même plan, même famille, même profondeur — puis de boucher. Quatre étages sont dans ce
  cas : 38, 40, 44 et 45 (`couchesng.SANS_BOUCHAGE`).
* **RYU, les pétales de sakura** — sa routine d'étage fait deux appels qu'`objetsng` ne sait
  pas lire : `0x8C09F258` **trois fois** (r4 = 1, 2, 3, id 14) et `0x8C0A2C94` une fois
  (id 34). Les deux sont des engendreurs de la même forme que ceux déjà lus (`[+0] = 1`,
  `[+8] = id`, `[+6] = 16`, `[+4] = l'argument`). Ce sont les seuls candidats.
* **KEN, les inscriptions sur les rochers** ; **DUDLEY, la parallaxe et les quelques pixels
  de trop** ; **ORO, le chaton qui reboucle et le perroquet qui ne s'envole plus** — pas
  encore ouverts.

Cliché : `build/3sx-28-09-ng-vent-punk.exe`, 35 331 837 octets.


## Le chaton d'Oro : son introduction ne passe qu'une fois — 28/09/2026

Frédéric : « *ORO l'animation d'un chaton tourne en boucle alors que ses premières phases
d'animation ne doivent être réalisées qu'une seule fois* ».

Un script de 2I ou de NG se termine par une commande, et il y en a **deux** :

    0x01   reprend à l'enregistrement 0         tout le script reboucle
    0x02   reprend à l'enregistrement mot3 - 2  ce qui précède ne passe qu'UNE fois

Le `0x02` était déjà lu le 23/09 pour la statue de Yang (`animer2i.script_deroule` :
« `index = pas x (mot3 - 2)` », gestionnaire `0x8C0B530C`, table `0x8C1C5BC8`) — mais traité
comme un `0x01` : « *il boucle : on le traite comme un `0x01`, qui relance le script* ». Il
boucle, oui, **mais pas au même endroit**.

Le script 17 du chaton, vingt-cinq images, se termine par :

    25  COMMANDE 0x02   mots ['0x0002', '0x0000', '0x0000', '0x000E']

`mot3 - 2` = 12 : le Dreamcast rejoue à partir de l'enregistrement 12. Les douze premières
images — la pose de **103 trames**, puis les bâillements (21761/21762 alternés) — sont une
entrée en scène. Le port les rejouait indéfiniment.

La fiche porte maintenant `depart_boucle`, et `image_de_la_trame` joue l'introduction sur
ses propres trames avant de ne faire tourner que la queue du script. Trois objets de New
Generation sont concernés :

    étage 53  ORO      script 17   12 images sur 25 jouées une seule fois
    étage 42  YUN 1    script 24    2 images sur 7
    étage 54  YANG 1   script 24    2 images sur 7

**Le perroquet n'est pas fait.** Son envol n'est pas une commande de script : ce sont les
scripts 21 et 26 que sa routine (id 55) pose dans d'autres états. À reprendre par la
routine.

Cliché : `build/3sx-28-09-ng-quatre-corrections.exe`, 35 339 517 octets. Compilation : huit
étapes, aucun avertissement.


## La ligne noire d'Alex, fermée par l'ordre de dessin — 28/09/2026

Le bouchage du fond (chapitre précédent) laissait quatre étages de côté, dont Alex, parce
qu'un objet s'y dessine **à travers** la page du fond. La cause n'était pas le bouchage,
c'était l'**ordre de dessin**.

Le gratte-ciel d'Alex (`0x8C1AF038`, script 2, plan 3, deux fiches de 64 × 240 en x 674 et
738) couvre la ruelle au pixel — c'était déjà écrit le 25/09. Mais sa profondeur, **104**,
est celle de sa propre page : la liste 132 d'Alex porte la couche 2, plan 3, profondeur 104.
Sur la console les deux sont dans deux listes d'affichage successives et l'objet passe
après ; ici, `animer2i` a mesuré le 15/09 qu'à profondeur égale **c'est le plan qui gagne**.

Tant que la page était pleine de trous, on voyait le gratte-ciel *à travers*. En la
bouchant, il aurait disparu.

`animerng.famille_et_z` rend donc l'ordre de la console, **d'un seul cran** : un objet dont
le plan est celui de la couche la plus lointaine et dont la profondeur lui est égale passe à
`z - 1`. Il reste derrière tout le reste — le plan du milieu d'Alex est à 94 — il ne fait que
passer devant sa page. **Deux fiches sur les 540 de New Generation.** `SANS_BOUCHAGE` est
vide, les dix-neuf étages sont bouchés.

## La parallaxe de Dudley, remise — 28/09/2026

Le 26/09, Frédéric : « *les décors DUDLEY 2I et NG n'ont pas de parallaxe dans le jeu
original* ». Les trois tables disaient le contraire ; c'est écrit au chapitre du 26/09, et
l'écart a été posé quand même, **annoncé comme un écart**.

Le 28/09 : « *DUDLEY remettre le paralaxe* ». La table reprend ses droits.

    étage 26  Dudley 2I   0,75 / 0,875   0x8C1D4F48 + 4 * 0x20
    étage 44  Dudley 1    0,75 / 1       0x8C189BA0 + 7 * 0x20
    étage 45  Dudley 2    0,75 / 1       0x8C189BA0 + 8 * 0x20

`etages.SANS_PARALLAXE` et `etagesng.SANS_PARALLAXE` restent, **vides**, avec leur histoire
au-dessus : c'est là que se poserait le prochain écart.

**Les quelques pixels de trop** ne sont pas dans la page : le descripteur de la bande 8 est
l'identité, `scene 0,512 1024x512` pile. Ce sont les bornes de caméra — autre chantier.

## Les pétales de Ryu : quatre pistes, aucune qui tienne — 28/09/2026

La routine d'étage de Ryu fait quatre appels qu'`objetsng` ne lit pas. Les quatre sont
suivis :

* **`0x8C09F258` (id 14, appelé trois fois, r4 = 1, 2, 3)** — sa table est `0x8C1B09C0`,
  c'est-à-dire **`descripteursng.ENTREES_PAGES`** : ce n'est pas un semeur, c'est le
  **pilote des animations de pages**. Il crée les entrées 1, 2 et 3, et
  `descripteursng._animations` n'en déclare que deux. L'**entrée 2** (plan 0, emplacement 1,
  pages 82, 92, 93) manque — mais le cas 3 du moteur de décor ne branche que sur les
  emplacements 0 et 2 (six listes de variantes consécutives, `0x8C4DF3DC` à `0x8C4DF4A4`,
  pas neuf). Rien ne la dessine : ce ne sont pas les pétales.
* **`0x8C0A2C94` (id 34)** — son état 0 est gardé par quatre variables globales et par
  `[+88] > 69` avant de faire quoi que ce soit : un événement rare, pas une chute continue.
* **`0x8C03121C`** — il crée **deux** works de **genre 7** (`mov #7,r4` deux fois), pas le
  genre 3 des objets de décor, sous la garde `u16[0x8C03133C] == 0`. C'est le seul candidat
  qui reste, et c'est là qu'il faut reprendre.

## Les deux objets invisibles de Ken — 28/09/2026

Sa routine appelle `0x8C0B168C` (id 117) et `0x8C0B13C0` (id 115) : plan 1, priorité 10,
palette 10, table `0x8C0DE6D8`, scripts 7 et 6, en x 512 et 496. Les deux indexent une table
de **54 octets par enregistrement** (`mov #54 ; muls.w`) qui reste à lire, et surtout les
deux écrivent `mov.b r0,@(1,r4)` avec r0 nul : **`disp_flag = 0`, ils naissent invisibles**,
comme les objets réactifs déjà lus le 23/09. Ce sont des objets à déclencheur.

## L'envol du perroquet — 28/09/2026

Son engendreur est lu depuis le 16/09 (id 55, `0x8C0A6E66`, x 672, y 114, palette 86,
script 20) et le catalogue donne ses trois scripts : **20, 21 et 26**. L'envol est un autre
état de sa routine, avec un déclencheur. Le port sait jouer une suite (`suites`), un trajet
(`trajet`), réagir à l'état d'un combattant (`REACTIF`) — mais pas encore « jouer une fois,
sur déclencheur, puis disparaître ». C'est le mécanisme qui manque, et il servirait aussi
aux deux objets de Ken.

Cliché : `build/3sx-28-09-sept-corrections.exe`, 35 339 517 octets.


## La table des routines d'objet de NG, retrouvée — 28/09/2026

Elle était nommée dans `objetsng.py` depuis le 16/09 (« *table `0x8C1ADA10` contre
`0x8C179FDC`* ») mais jamais employée. Retrouvée par un crible mécanique — un engendreur et
la routine de son id vivent dans le même quartier de code — et confirmée par un point connu
d'ailleurs : `objetsng` note que **la calèche de Dudley 1 est l'id 65, routine
`0x8C0A8970`**, et c'est exactement `T[65]`.

    id  14 -> 8C09F29A   id  64 -> 8C0A84A4   id  71 -> 8C0A9B44   id 115 -> 8C0B102C
    id  34 -> 8C0A2CDC   id  65 -> 8C0A8970   id  72 -> 8C0AA018   id 117 -> 8C0B1618
    id  55 -> 8C0A6B54   id  68 -> 8C0A9484   id  73 -> 8C0AA1C4

C'est l'outil qui manquait pour lire n'importe quel objet de décor de New Generation.

## Le perroquet d'Oro, lu en entier — 28/09/2026

Frédéric : « *le perroquet peut s'envoler dans la version d'origine, ce qui n'est plus le
cas ici* ». Sa routine est `0x8C0A6B54`. Elle copie trois pointeurs sur la pile et dispatche
sur `[+36]` :

    état 0  0x8C0A6B96   perché
    état 1  0x8C0A6BEA   le vol : six sous-états, table 0x8C1B22F0
    état 2  0x8C0A6E42   il revient : [+36] = 0 et [+38] = 0

**LE DÉCLENCHEUR EST LE DRAPEAU DE FIN DE SCRIPT.** L'état 0 pose le script 20
(`mov #20,r6`), met `disp_flag` à 1, puis à chaque trame avance le script et teste
`objet[+468]` — l'octet de drapeau de l'image courante, celui qu'`animer2i` a lu le
23/09. Dès qu'il n'est pas nul, il passe à l'état 1.

Et il se voit dans le script 20 (`0x8C0DBB60`, 51 enregistrements) :

    enr. 0       COMMANDE 0x0C, compte 3      ouvre une boucle
    enr. 1..44   le repos, drapeaux 0         1417 trames par tour
    enr. 45      COMMANDE 0x0D                ferme la boucle
    enr. 46, 47  deux images de plus
    enr. 48      image 21805, durée 5, DRAPEAU 0x01   <- L'ENVOL PART ICI
    enr. 49      COMMANDE 0x01                relance

Le sous-état 0 du vol pose le **script 21** (six images de quatre trames, les battements
d'ailes) et écrit quatre champs, tous lus :

    [+124] = 0x00018000   +1,5 pixel par trame
    [+128] = 128          +0,00195  (l'accélération)
    [+132] = 10240        +0,15625
    [+136] = 512          +0,0078

Le sous-état 1 avance, compare `[+102]` (le x) à **912**, puis tire au sort
(`0x8C0191C0`, `tst #1`) ; les autres bornes du vol sont 864, 352 et 384. Le **script 26**
(dix pas, 153 trames, drapeau 1 au pas 7) est le retour.

**LE VOL N'EST PAS REPRODUIT, ET C'EST LA MÊME RAISON QUE POUR L'OISEAU D'ELENA 1** : un
`trajet` à vitesse constante ne rend pas une accélération, et la branche est tirée au sort.
C'est dit, pas comblé — comme le 25/09. Ce qui le débloquerait est une accélération par
segment de trajet, ou un déclencheur « jouer une fois puis revenir ».

## Les deux objets de Ken : ils ne sont pas dans le fichier — 28/09/2026

`0x8C0B168C` (id 117) et `0x8C0B13C0` (id 115) indexent une table de **54 octets** par
enregistrement dont la base est `0x8C553E40` — **au-delà de la fin du binaire**, et même
au-delà après le décalage `.bss` de `descripteursng` (`- 0x12420`). C'est une structure de
RAM, remplie à l'exécution : elle n'est pas lisible statiquement.

Les deux écrivent par ailleurs `mov.b r0,@(1,r4)` avec r0 nul — **`disp_flag = 0`, ils
naissent invisibles**, comme les objets réactifs lus le 23/09. Ce sont des objets à
déclencheur, et leur cible vient d'une chaîne de création que le port n'a pas.

## Les pétales de Ryu : les huit scripts que personne ne joue — 28/09/2026

Le dépouillement complet de la table de scripts de Ryu (`0x8C0D1338`) contre les six objets
que la chaîne émet donne ceci :

    script  2   4 images  24 trames  sprites 30492..30495
    script  3   4 images  24 trames  sprites 30500..30503
    script  4   4 images  24 trames  sprites 30508..30511
    script  5   4 images  24 trames  sprites 30516..30519
    script  6   4 images  36 trames  sprites 30488..30491
    script  7   4 images  36 trames  sprites 30496..30499
    script  8   4 images  32 trames  sprites 30504..30507
    script  9   4 images  36 trames  sprites 30512..30515

**Huit animations de quatre images, sur un bloc de trente-deux sprites contigus**
(30488..30519) que rien d'autre du décor n'emploie — le reste de ses scripts vit dans
16838..17269. Huit pétales qui voltigent, quatre images chacun. **Ce sont elles.**

Et l'appel non lu `0x8C03121C` les désigne : il charge `mov.w 0x8C031332,r9` = **30488**,
puis boucle `r13` de 0 à **32** en écrivant `30488 + r13` dans `objet[+474]` et en
interrogeant chaque indice (`0x8C03164A`). Ce n'est pas un semeur : c'est le **balayage des
trente-deux sprites du sakura**.

**Ce qui manque pour les poser** : leur position de départ et leur chute. Les deux vivent
dans les tableaux `.bss` `0x8C549870` et `0x8C5498D0`, remplis à l'exécution. On peut poser
les huit animations en objets avec un trajet de chute — les images, les durées et les
sprites sont lus — mais **la trajectoire serait inventée**, et ce décor est par ailleurs
validé. À trancher par Frédéric avant de l'écrire.


## Le sakura de Ryu, de bout en bout — 28/09/2026

Frédéric : « *RYU et Ken variant rue : il manque les feuilles de sakura qui tombent des
arbres* », puis, après un premier abandon : « *continue à chercher, tu as le code de la
version dreamcast sous la main. Les réponses y sont.* » Elles y étaient.

### Ce qui a mis sur la piste

Le dépouillement de la table de scripts de Ryu (`0x8C0D1338`) contre les six objets que la
chaîne émettait laissait **huit scripts que personne ne joue** — les 2 à 9, quatre images
chacun, sur un bloc de **trente-deux sprites contigus** (30488..30519) qu'aucun autre script
du décor n'emploie (le reste vit dans 16838..17269).

### La chaîne, lue bout à bout

    0x8C089970 -> 0x8C03121C   monte les 32 sprites du sakura dans le pool de tuiles
                               (mov.w 0x8C031332,r9 = 30488, boucle de 0 à 32) et dépose
                               leurs emplacements dans 0x8C549870 et 0x8C5498D0.
                               Son jumeau 0x8C03135C les redescend.
    0x8C08999A -> 0x8C0A2C94   L'ÉMETTEUR (id 34). À chaque réveil il tire une rangée de
                               sept indices — 0x8C1B1754 pour les pétales proches (valeurs
                               0..10), 0x8C1B17C4 pour les lointaines (11..21) — en pose
                               1 à 7, puis attend un délai pris dans 0x8C1B1834 (10, 24,
                               28, 34, 40, 48, 60, 78, 88, 94, 108, 114).
    0x8C0A2FBC                 LE POSEUR. Objet de genre 3, id 35, plan 2, +554 = 0x204E,
                               et il déverse un des VINGT-DEUX enregistrements de
                               0x8C1B1874, douze octets chacun :

    mot 0 -> [+84] et [+102]   x            mot 3 -> [+456]   le script, 0 à 3
    mot 1 -> [+86] et [+106]   y            mot 4 -> [+156]   un délai
    mot 2 -> [+556] et [+88]   la profondeur  mot 5 -> [+160]  le y d'arrivée

puis `[+164]` = 0 pour les indices < 11, 1 au-delà, et surtout **`[+364]`, la table de
scripts de l'objet**, qui prend `0x8C0D1340` près et `0x8C0D1350` loin.

### Et les huit scripts se referment là

La table de Ryu est `0x8C0D1338`. Donc `0x8C0D1340` est son **entrée 2** et `0x8C0D1350` son
**entrée 6**. Un script `n` de 0 à 3 est le script **n + 2** pour un pétale proche et
**n + 6** pour un lointain : les 2 à 5 et les 6 à 9. Exactement les huit.

### La chute, lue aussi

`0x8C0A32FC` tire une paire dans `0x8C1B197C`, indexée par `[+164]`, et la pose en `[+128]`
(vitesse y) et `[+136]` (accélération y). L'état 1 du pétale (`0x8C0A318A`) intègre par
`0x8C085850` — `[+128] += [+136]` puis `[+104] += [+128]` — et s'arrête quand `[+106]`
atteint `[+160]`.

    pétales proches    ([+164] = 0)   vitesse -0,078 à -0,305   accél. -0,004 à -0,018
    pétales lointaines ([+164] = 1)   vitesse -0,016 à -0,180   accél. -0,000 à -0,014

`y` décroît quand le pétale descend — `sol` monte, c'est la règle de l'axe vertical.

### Les vingt-deux points

    #   x     y   prof  script  chute  durée
    0  -288  288   22     5      250    212      11  -304  384   90    6    312   333
    1  -208  304   73     4      239    207      12  -264  368   90    7    296   324
    2  -184  264   22     2      230    202      13  -160  240   90    8    168   240
    3  -120  264   22     3      228    201      14   -80  304   90    9    232   285
    4  -128  408   73     5      346    253      15     0  336   90    7    264   305
    5     0  320   22     2      283    227      16    80  344   90    6    272   310
    6    32  312   22     4      276    224      17   -48  400   90    8    328   342
    7  -256  272   22     5      234    204      18  -288  361   90    6    289   320
    8  -232  274   73     4      209    192      19  -244  377   90    7    305   329
    9  -169  312   22     2      278    225      20   -98  276   90    9    204   266
    10  -92  296   22     3      260    216      21    36  323   90    7    251   297

### Ce qui est approché, et c'est dit

Trois choses sont tirées au sort sur la console et figées ici : **le couple de vitesse** (on
prend le neuvième des trente-deux, celui du milieu : −0,227 / −0,009 près, −0,102 / −0,005
loin), **le nombre de pétales servis à la fois** (1 à 7) et **le délai entre deux lâchers**.
La durée de chaque chute se calcule alors de la hauteur lue et de ce couple, et `trajet` la
joue à vitesse constante — une chute uniforme au lieu d'une chute qui s'accélère.

Les vingt-deux tiennent toutes : **31 rangs sur 56, 673 morceaux sur 2240, 89 motifs sur
128**. Aucune écartée.

### Ce que Ken n'a pas encore

Ses deux objets invisibles lisent une table de 54 octets en `0x8C553E40`, de la RAM — mais
**le remplisseur est dans le code** : c'est sa propre routine d'étage, en `0x8C08C732`, qui
appelle `0x8C08D4CA` pour chaque enregistrement, avec les tables `0x8C4DE414` et
`0x8C4DE434`. C'est là qu'il faut reprendre.

Cliché : `build/3sx-28-09-sakura.exe`, 35 385 859 octets. Compilation propre.


## Le perroquet d'Oro s'envole — 28/09/2026

Tout était lu au chapitre précédent ; il restait à le poser. Rappel de la lecture :

* le déclencheur est le **drapeau de fin de script**, `objet[+468]`, que le script 20 porte à
  son enregistrement 48 — après les **trois tours** de sa boucle `0x0C`/`0x0D`, soit
  **4358 trames de perchoir**, soixante-douze secondes ;
* le vol pose le **script 21** (six images de quatre trames) et écrit
  `[+124]` = +1,5 px/trame, `[+132]` = +0,15625 (l'accélération x), `[+128]` = +0,00195,
  `[+136]` = +0,0078 ; il s'arrête quand `[+102]` dépasse **912**, soit 240 pixels depuis
  672 : **quarante-huit trames**.

### Ce qui est posé

`comportement=5` (TRAJET), `suites=[20, 21]`, et sept segments :

    (4358,    0,  -,  suite 0)   le perchoir, script 20
    (   8,  544,  -9, suite 1)   l'envol, script 21
    (   8,  864, -24, -1)
    (   8, 1184, -40, -1)
    (   8, 1504, -56, -1)
    (   8, 1824, -72, -1)
    (   8, 2144, -88, -1)

`vx` et `vy` sont en 1/256 de pixel par trame ; chaque segment porte la **vitesse moyenne**
de son intervalle sous l'accélération lue. Total 252 pixels au lieu de 240 — douze de trop,
hors champ de toute façon. Le retour (état 2) n'est pas rendu : le trajet boucle, et
l'oiseau retrouve son perchoir d'un coup, hors de l'écran. `suite` vaut −1 sur les segments
2 à 6 pour ne pas relancer le battement d'ailes toutes les huit trames.

Le budget d'Oro ne bouge pas : **23 rangs sur 56, 700 morceaux sur 2240, 72 motifs sur 128**.

## Les deux objets de Ken — 28/09/2026

Frédéric : « *variant bain à ciel ouvert : il manque les inscriptions sur les rochers* ». Sa
routine d'étage fait deux appels que la chaîne listait en NON LU, et les deux engendreurs se
lisent **entièrement**, en immédiats :

    0x8C0B13C0 (id 115)   [+102] = 496, [+86] = 80 et [+104] = 0x00500000,
                          [+88] et [+556] = 10, [+456] = 6, [+364] = 0x8C0DE6D8,
                          [+558] = 1, [+554] = 67
    0x8C0B168C (id 117)   x 512, [+86] = 104 et [+104] = 0x00680000, même profondeur,
                          même palette, même plan, même col, [+456] = 7

`0x8C0DE6D8` est la table de scripts de Ken **sans décalage** — contrairement aux pétales de
Ryu, dont la table était décalée de 2 et de 6.

### Et leurs scripts ne sont joués par personne

Le dépouillement de la table de Ken contre ses vingt-et-un objets laisse les **scripts 6 et
7** de côté, et ils vivent sur un **bloc de sprites à eux** (25641..25760) — le reste de ses
objets est dans 22832..23695 et 4798..4830. La même signature que les huit scripts du sakura.

    script 6   48 images  12240 trames   255 trames par image : très lent
    script 7   12 images   3060 trames

### Ils naissent invisibles

Les deux écrivent `mov.b r0,@(1,r4)` avec r0 nul — **`disp_flag` à zéro**, comme les objets
réactifs lus le 23/09 : le Dreamcast ne les montre que lorsqu'une condition tient. Le port
garde le défaut déjà choisi pour cette famille (visibles ; `SF3_DECOR_REACTIF=1` donne
l'autre lecture), et c'est Frédéric qui tranche sur l'image — y compris sur la question de
savoir si ce sont bien ses inscriptions.

**Leur table de 54 octets (`0x8C553E40`) n'a finalement servi à rien.** Elle est construite
en RAM par la routine d'étage (`0x8C08C732` la remplit, `0x8C08D4CA` la retouche), mais elle
ne porte **aucun** des champs ci-dessus : position, profondeur, script, plan et table sont
tous des immédiats des engendreurs. La piste « c'est de la RAM, donc illisible » était une
fausse borne.

Budget de Ken : **24 rangs sur 56, 648 morceaux sur 2240, 63 motifs sur 128**. Rien d'écarté.

Cliché : `build/3sx-28-09-sakura-perroquet-ken.exe`, 35 355 215 octets. 905 fiches
(341 de 2I + 564 de New Generation).
