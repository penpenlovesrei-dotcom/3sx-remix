# Produire un décor de 2nd Impact sans aucun savestate

**29/08/2026 — la chaîne est complète et validée à l'écran.** Le petit obélisque de `bg00`
et ses quatre figures animées sortent du **binaire et des assets du disque**, sans qu'un
seul `.state` Flycast soit ouvert. C'est la condition pour transposer le chantier à New
Generation, qui n'a aucun relevé.

Ce document remplace la voie par relevés décrite dans `RELAIS.md`. Les états ne doivent
plus apparaître nulle part dans la chaîne.

---

## La chaîne, maillon par maillon

    table des elements       0x8C17B980+      enregistrements de 16 octets
        +0 plan   +2 drapeaux   +4 x (signe)   +6 y   +8 palette   +10 script
                    |
    table maitresse des scripts   0x8C5F9B38 + aire*4  ->  [pointeurs de scripts]
        AIRE = 3 x numero de decor  (bg00 -> aires 0,1,2)
        script -> enregistrements de 8 octets ; u16 +6 = index global
                    |
    asset F_ETCnn : anims[index global - span],  span = `index_global[0]`
        champ 1,2 = l'ANCRE       champ 4 = offset dans la table des sprites
        le RANG de cet offset parmi les offsets distincts = le numero de sprite
                    |
    assemblage.charger(asset) -> (asset, tuiles)   puis   assemblage.poser(sprite, tuiles)

### Les sept éléments de décor de `bg00`, tous résolus

**Rien ne manque pour Gill.** Deux tables se complètent : **trois** éléments statiques et
**quatre** figures animées. Les deux « étoiles filantes » qui figuraient ici sont le bloc
du décor 1 — voir plus bas, l'annuaire.

> Ne pas confondre avec le nombre brut d'éléments de la liste RAM (32 pour `bg00`) : il
> contient aussi les combattants et l'affichage. `rend_etat` n'en retenait que six, ceux
> dont les tuiles viennent de l'asset du décor.

**Table de 16 octets, `0x8C17B980` — trois enregistrements, plans 3 et 7 :**

| plan | element | script | sprite | taille | palettes | ce que c'est |
|---|---|---|---|---|---|---|
| 3 | 528, 80 | 7 | 56 | 144×75 | 842 + 867 | le temple d'horizon |
| 3 | 608, 152 | 8 | 57 | 121×111 | 848 + 850 | les obélisques |
| 7 | 496, 120 | 9 | 58 | 19×62 | 839 | le petit obélisque gris |

144×75 et 121×111 sont au pixel les tailles du temple et des obélisques mesurées par un
tout autre chemin.

> **Le bloc s'arrête là**, et c'est l'annuaire qui le dit : 48 octets. Les deux
> enregistrements suivants — les « étoiles filantes » en `0x8C17B9B0` et `0x8C17B9C0` —
> sont le bloc du **décor 1**, et Frédéric a tranché : elles appartiennent à la petite
> **scène d'introduction d'avant-combat** de 2nd Impact, que 3rd Strike n'a plus. On les
> ignore. Elles ont été retirées de la liste 260 de l'étage 22 le 29/08.

### Les éléments animés — une seconde table, de 8 octets

Pour `bg00`, à **`0x8C183DC8`**, quatre enregistrements `{u16 x, u16 y, u16 palette, u16 script}` :

| x, y | script | sprite | taille | palette |
|---|---|---|---|---|
| 320, 64 | 11 | 6 | 61×87 | **871** |
| 576, 72 | 12 | 29 | 49×72 | 872 |
| 208, 136 | 5 | 34 | 32×46 | 873 |
| 720, 96 | 6 | 44 | 39×39 | 874 |

Quatre figures, quatre palettes **consécutives**. Et 871 est la palette que
`PALETTES-CONFIRMEES.md` donne pour l'acolyte de `bg00` — recoupement par deux chemins
indépendants. Le bloc est encadré par des suites de comptage (0,0,1,1,2,2… et 16,17,18…)
qui appartiennent à une autre table.

**`animations.py` n'exportait qu'UNE animation par étage** ; le binaire en donne quatre
pour Gill.

---

## Les objets ANIMÉS — leur propre groupe, et leurs tables

Ils n'empruntent plus rien. `mlt_obj_trans_cp3_ext` ne demande que deux blocs, et
`decor_objets.c` les fabrique :

    table de TRANS      u32 offsets[], puis à offsets[n] : u16 nombre, puis les morceaux
                        en ÉCARTS (le moteur fait `x -= m.x` et `y += m.y`)
    table de TEXTURES   u32 offsets[], puis TEX { u8 wh, ... } ; wh = 0x49 -> 16x16, 256 o

`DecorObjets_Groupe` les tend au moteur à la place de celles du groupe donneur. Les octets
de données de la texture ne sont jamais lus : `DecorObjets_Tuile` rend toujours nos 256
octets, donc `lz_ext_p6_fx` n'est pas appelé — rien à compresser.

**Plusieurs objets par étage.** L'état est un tableau. Chaque objet a sa grille, sa
cadence, son emplacement de palette (`300 + rang`, et `my_col_code` suit) et sa place dans
les clés de cache :

    identité de motif   0x00D3 <<16 | rang <<6 | image
    clé de morceau      rang <<11 | image <<5 | case

### LE CHARGEUR D'OBJETS DE DÉCOR, lu dans le code — 30/08/2026

C'est le chemin qu'il fallait prendre depuis le début, et il commence à donner. La
fonction est **`0x8C02AA7C`**. Elle fait exactement ceci :

    r8  = arg2
    r4  = u16 [0x8C17DED4 + arg2*2]      LE NOMBRE d'objets ; si zero, on sort
    r14 = u32 [0x8C5F9F10 + arg2*4]      LE POINTEUR du bloc
    boucle r12 = 0 .. r4-1 :
        alloue un objet, puis lit le bloc en `mov.w @r14+` successifs
        et pose chaque u16 a un offset fixe de la structure (+102 = x, +106 = y, ...)
        x et y sont DECALES par le contexte : `objet[+102] += contexte[+102]`
        le script est resolu par  u32 [0x8C5F9B38 + (decor*3 + aire)*4]
        avec decor = u8 [0x8C6AF304 + 4]  et  aire = u8 [0x8C6AF304 + 5]

Quatre choses en sortent, toutes vérifiables :

* **`0x8C5F9F10` est une vraie table**, lue par le code à trois endroits. Son index
  n'est **pas** `décor*3 + aire` : il est **passé en argument** au spawner, qui le range
  dans le champ `+4` de l'objet, et les autres lecteurs font `table[objet[+4]] + 22`.
  Aucune constante 27, 28 ou 29 n'est jamais écrite dans ce champ, et le seul code qui
  calcule `décor*3 + aire` indexe la table des *scripts*, pas celle-ci.

  > **Le « bloc d'Oro à l'index 27 » était une illusion, et de ma main.** J'avais choisi
  > le début de la table pour que `0x8C17E916` y tombe sur 27, puis j'ai présenté « 27 =
  > 9×3 » comme une confirmation. C'est circulaire. Troisième fois que ce biais frappe
  > dans ce chantier — après la mesure sur les pages cuites et le bloc du décor 8 : **caler
  > une structure sur le résultat attendu, puis lire le résultat comme une preuve.**
* **`0x8C17DED4` donne le NOMBRE d'objets**, ce qu'on déduisait jusqu'ici du pointeur
  suivant. Recoupement : l'index 0 y annonce **16**, et ce sont exactement les 16
  premiers enregistrements de son bloc qui se résolvent dans l'asset de `bg00` ;
* **le format de l'enregistrement se lit dans la boucle**, champ par champ, au lieu d'être
  supposé. C'est ce qui permettra de rejeter un mauvais bloc *sans* essai à l'écran ;
* **il y a du code par décor.** Le spawner de `bg00`, `0x8C04AE04`, porte son adresse de
  table **en dur** (`mov.l 0x8c04ae68,r14` → `0x8C183DC8`). Il n'y a pas une table unique
  pour les dix-sept décors, et c'est pour ça qu'aucune recherche de motif ne convergeait.

### Le script d'étage d'Oro, déroulé en entier — et ce qu'il ne fait PAS

La table des scripts d'étage est **`0x8C1D3FB4`, dix-sept entrées**, et c'est vérifié :
l'entrée 0 est celle de `bg00` et elle charge bien son spawner `0x8C04AE04`. Celui d'Oro
est donc **`0x8C0DE0A4`**, et il se lit ainsi :

    8C0DE0A4  prologue : r13 = 0x8C6AF304 (decor/aire), r14 = 0x8C6AF750
        bsr 8C0DE1BA   phase 1 -- dispatcher a 2 etats, table 0x8C1D613C
        bsr 8C0DE0E4   phase 2 -- dispatcher a 3 etats, table 0x8C1D6130
        bsr 8C0DE334   phase 3
        puis 8C0D8BC0, 8C0D8A5A, et jmp 8C0D883C

Les trois états de la phase 2 sont `0x8C0DE10A`, `0x8C0DE166` (le son, `mov #99,r4`) et
`0x8C0DE1AC`. La phase 1 mène à `0x8C0DE240`, une sous-machine à trois branches.

**Un seul objet y est créé** : le spawner `0x8C03CE46` avec `mov #1,r4`, et sous condition
`aire == 1`. Rien d'autre.

> **Les objets de décor d'Oro ne sont donc PAS créés par son script d'étage**, contrairement
> à ceux de `bg00`. Le chemin est commun à tous les décors. Cela règle une question qui
> traînait depuis le début du chantier — et cela condamne la méthode « suivre le script
> d'étage » pour les seize autres décors : elle ne marche que pour `bg00`.

### LE DECALAGE D'INDEX APPARAIT A PARTIR DE L'ETAGE 10

Mesure sur quatre décors, par l'outil `accorder2i.py` — quelle table de scripts résout le
bloc, contre l'index du script d'étage qui l'appelle :

| bande | script d'étage | table de scripts | décalage |
|---|---|---|---|
| `bg02` Ryu | 2 | 2 | aucun |
| `bg03` Yun | 3 | 3 | aucun |
| `bg0a` Oro | 10 | 9 | **−1** |
| `bg0b` Yang | 11 | 10 | **−1** |

Le décalage n'est donc ni une erreur ni une exception d'Oro : il **apparaît à partir de
l'étage 10**, et il est constant ensuite. Un décor est sauté quelque part entre 3 et 10 —
probablement une entrée qui existe dans une table et pas dans l'autre. La cause n'est pas
établie ; le fait, si.

> **Ne pas supposer l'index : le mesurer.** `accorder2i.py` essaie les dix-sept tables et
> retient celle qui résout tout le bloc **avec beaucoup d'images**. C'est ce critère qui
> tranche : la bonne table rendait 106 images pour Ryu, les mauvaises une par objet.

### LA TABLE DES BASES DE PALETTES EST DANS LE BINAIRE — 30/08/2026

**Fin du tâtonnement sur les palettes.** La table de transferts est en **`0x8C1E4B50`**,
entrées de 12 octets `{source RAM, destination, taille}`, lue par `0x8C0EDFEA` avec un
index sur un octet (`table + idx*12`). Ses entrées **52 à 68** sont les dix-sept décors.

    numero de palette = (source - 0x02798000) / 128     nb de palettes = taille / 128

    52 -> 827  48pal  bg00     58 -> 1085 16pal  bg0b     64 -> 1412 17pal
    53 -> 927  31pal  bg01     59 -> 1117 26pal           65 -> 1446 17pal
    54 -> 936  24pal           60 -> 1117 24pal           66 -> 1319 23pal  bg08
    55 -> 984  35pal  bg0d     61 -> 1169 25pal  bg05     67 -> 1365 32pal
    56 -> 989  27pal  bg02     62 -> 1219 35pal  bg06     68 -> 1429 24pal  bg0a
    57 -> 1043 21pal           63 -> 1289 15pal

Les sept bases établies auparavant s'y retrouvent **toutes** — 827, 927, 1085, 1169, 1219,
1319, 1429. C'est ce qui valide la lecture.

> **Le NOMBRE de palettes est la contrainte qui manquait.** Un décor dont un sprite porte
> l'offset 32 a besoin d'au moins 33 palettes. Ça détermine `bg0d` **sans ambiguïté**
> (984, seule entrée assez grande), et ça réduit `bg02` à trois candidats — dont **989**
> ressort seule : ses couleurs sont, à un bit près, celles relevées sur la capture.
>
> `1625` pour Ryu et `1519` pour Sean étaient des **déductions**, et elles étaient fausses.

**Ce qui reste à apparier** : dix entrées sans bande attribuée (936, 989 pris, 1043, 1117
×2, 1289, 1412, 1446, 1365). La contrainte du nombre de palettes les réduit fortement ;
l'index de la table devrait donner le reste, et il se lit dans l'appelant.

### MESURER SUR UNE CAPTURE : LA METHODE, ET LE PIEGE OU JE SUIS TOMBE

La methode est bonne — c'est elle qui a donne la base d'Oro. Mais elle a une condition que
j'ai oubliee, et l'oubli a produit un faux positif net.

**Ce que j'ai fait, et qui est faux.** J'ai releve les couleurs des cascades sur
`reference-ryu.png`, puis compte, pour chaque palette de la banque, combien des couleurs
employees par le sprite s'y retrouvaient. Resultat : **23 sur 23** pour les palettes 379 a
383, et j'en ai tire la base 354. Or **dans la palette 379 tous les index employes valent
000000** : le test ne mesurait que la presence du noir dans la capture. Avec 354 les
chutes d'eau seraient invisibles.

**Les deux gardes-fous qui manquaient :**

* faire l'epreuve DANS LES DEUX SENS. « Les couleurs du sprite sont dans la capture » ne
  vaut rien seul ; il faut aussi « les couleurs de la zone sont dans la palette ». Sur
  Ryu, ce second test rend au mieux **5 sur 24** — aucune palette ne convient ;
* rejeter les palettes DEGENEREES aux index employes. Une palette noire passe tout.

**Et ce que l'echec apprend sur le decor :** les grandes cascades visibles sur la capture
sont **peintes dans le decor**, ce ne sont pas les objets animes. Avant de relever des
couleurs sur une capture, s'assurer que la zone montre bien l'OBJET et non l'art de fond.

> La base du groupe 12..25 de `bg02` **n'est donc pas trouvee**. Trois valeurs essayees,
> trois fausses : 1625 (noir et rouge), 1356 (bleu vif au lieu de gris bleutes), 354
> (invisible). On garde 1356, fausse mais visible.

### RYU : SES x SONT NEGATIFS, ET IL EST LE SEUL

Relevé sur six décors — Ryu est le seul dont les positions soient fausses, et le seul dont
les enregistrements portent des `x` négatifs :

    RYU     -368  208  -128  -145  -233  273  16  -288     positions FAUSSES
    ORO      816  800   792   224   320  352 840  720      justes
    YUN      463  523   272   336                          justes
    ALEX     480                                           juste

`(x + ancre + x0) & 0x3FF` enroule ces valeurs vers 656..1023, ce qui envoie a DROITE des
objets qui devraient etre a gauche. C'est la piste a suivre : soit l'enroulement n'est pas
le bon traitement, soit un decalage de contexte s'ajoute -- le chargeur generique
`0x8C02AA7C` fait `objet[+102] += contexte[+102]`, et cette addition n'a jamais ete portee
dans la chaine.

### RYU AUSSI A DEUX BANQUES DE PALETTES — 30/08/2026

Même structure qu'Oro, et le même symptôme. `bg02` a deux groupes d'offsets disjoints,
**0–5 et 12–25**, et aucun de ses 124 sprites ne les mélange. La base connue, 1625, ne vaut
que pour le premier ; appliquée au second elle rendait les cascades en **noir et rouge vif**
sur un décor pastel.

    bg02 : offsets  0..5  -> 1625      offsets 12..25 -> 1356

La seconde a été cherchée sous deux contraintes — tout le groupe doit tomber sur des
palettes valides, et l'offset 25 doit rendre de l'eau. Il reste un **plateau de 1356 à
1367**, douze valeurs qui donnent le même bleu clair : très probablement les teintes du
cycle qui anime l'eau qui coule. On prend le début du plateau.

> **À faire pour chaque décor avant de le générer** : compter les groupes d'offsets. Deux
> groupes disjoints = deux banques, et une seule base donnera des couleurs fausses sur la
> moitié des objets. C'est vrai d'Oro et de Ryu ; ce n'est probablement pas une exception.

### L'AIRE N'EST PAS UN DÉTAIL : C'EST LA VARIANTE DE ROUND — 30/08/2026

Toutes les tables de décor sont indexées par `décor*3 + aire`, et l'aire se lit dans la
globale de contexte, `u8[0x8C6AF304 + 5]`. **Toute la chaîne lit l'aire 0 depuis le début.**
Pour les décors dont les trois aires diffèrent, on ne voit donc qu'un tiers du décor.

Trois décors sont concernés, et trois seulement :

| décor | bande | éléments (aires 0/1/2) | second jeu |
|---|---|---|---|
| 6 | `bg06` Hugo | **2 / 3 / 3** | 4 / 4 / 4, pointeurs différents |
| 8 | `bg08` Elena | **0 / 1 / 1** | **9 / 1 / 1** |
| 16 | `bg10` | **2 / 3 / 3** | **4 / 2 / 2** |

Chez Hugo c'est une progression, pas une répétition : le sprite 146 n'existe qu'au premier
round, le 151 qu'au dernier, le 144 disparaît à la fin. Voir `PROMPT-SUITE.md`, chantier
1 bis.

> **La correspondance décor → bande est décalée d'un cran par rapport à ce que ce document
> affirmait.** Frédéric est formel : la vasque, la vapeur, les trois chutes d'eau et
> l'édifice de pierre sont à Oro — or ils viennent du bloc appelé par le « décor 10 ».
> `etages.py` numérote d'ailleurs `bg0a` = 10 (0x0a), pas 9, et `bg0b` est le stage de Yun
> et Yang à Hong Kong, où une vasque et des chutes d'eau n'ont rien à faire. Le test
> « quel asset couvre les scripts du décor » identifie l'asset d'une **table de scripts**,
> pas le propriétaire d'un **bloc** : il ne tranchait pas ce que je lui ai fait dire.

### LE NOMBRE D'ÉLÉMENTS NE SE DÉDUIT PAS : IL SE LIT — 30/08/2026

`annuaire2i.py` calcule le nombre d'éléments d'un décor par `(pointeur suivant − pointeur)
/ 16`. **Le code, lui, le lit dans une table.** La fonction `0x8C0233B6`, appelée par
quatorze scripts d'étage, s'indexe toute seule sur la globale de contexte :

    decor = u8 [0x8C6AF304 + 4]        aire = u8 [0x8C6AF304 + 5]
    nombre   = u16 [0x8C17B918 + (decor*3 + aire)*2]
    pointeur = u32 [0x8C5F9C04 + (decor*3 + aire)*4]

`0x8C5F9C04` est bien l'annuaire des éléments qu'on emploie déjà — mais **`0x8C17B918` est
sa table de nombres, et elle n'était pas connue.**

La déduction tombe juste sur treize décors et **faux sur quatre** :

| décor | le code dit | on déduisait |
|---|---|---|
| **9 — `bg0a` Oro** | **0** | 1 |
| 13 — `bg0e` Urien | 1 | 7 |
| 14, 15 — remplissage | 0 | 2 |

> **Oro n'a AUCUN élément statique.** Les chatons cuits sur sa plate-forme, à `(400,903)`,
> viennent d'un enregistrement qui ne lui appartient pas — le même genre d'emprunt que le
> bloc de Yang. Et Urien reçoit six éléments de trop.

À corriger dans `annuaire2i.py` : prendre le nombre dans `0x8C17B918`, ne plus le déduire.

### L'ATTRIBUTION DES DIX-SEPT DÉCORS, PAR LE CODE — `outils/chargeurs2i.py`

L'outil suit la seule chaîne qui dise la vérité, et il la suit tout seul :

    0x8C1D3FB4[decor]  ->  le script d'etage
        dedans : jsr <chargeur>  avec  mov #arg,r4   (souvent dans le DELAY SLOT)
    <chargeur> :  nombre = u16[tableA + arg*2]   bloc = u32[tableB + arg*4]

**Deux chargeurs à table**, tous deux en enregistrements de 16 octets :

    0x8C025A9A   nombres 0x8C17C1F8   pointeurs 0x8C5F9DF8
    0x8C02E1FE   nombres 0x8C17E794   pointeurs 0x8C5F9F64

| décor | bande | bloc(s) et nombre |
|---|---|---|
| 0 | `bg00` Gill | `0x8C183DC8` (4, **en dur**), `0x8C17C190` (en dur) |
| 1 | `bg01` Alex | `0x8C17F2D8` (en dur) |
| 2 | `bg02` Ryu | `0x8C17C20E` (2), `0x8C17E7A6` (6), `0x8C17F5B8` (en dur) |
| 3 | `bg03` Yun | `0x8C17C22E` (2), `0x8C17E806` (2), + trois en dur |
| 4 | `bg04` Dudley | `0x8C17E826` (1), `0x8C17F2D8` (en dur) |
| 5 | `bg05` Necro | `0x8C17C25E` (5), `0x8C17E836` (10) |
| 6 | `bg06` Hugo | `0x8C17C2AE` (2), `0x8C17E8D6` (3), `0x8C17F54C` (en dur) |
| 8 | `bg08` Elena | `0x8C17FD04` (en dur) |
| **9** | **`bg0a` Oro** | **`0x8C17C30E` — UN seul enregistrement** |
| 10 | `bg0b` Yang | `0x8C17C31E` (1), **`0x8C17E916` (8)** |
| 11 | `bg0c` Ken | `0x8C17C24E` (1), `0x8C17E996` (1) |
| 13 | `bg0e` Urien | `0x8C17E9A6` (2) |
| 16 | `bg10` | `0x8C17C2EE` (2), `0x8C17E906` (1), `0x8C17E4C0` (en dur) |

> **La méthode se valide elle-même** : le bloc de Gill, `0x8C183DC8`, ressort tout seul du
> côté « spawner dédié », alors qu'il avait fallu des jours pour le trouver à la main.
>
> **Et Oro n'a qu'un seul objet de décor.** Ses chatons, son perroquet et son chien ne sont
> donc pas des objets de ce type — c'est à chercher ailleurs, mais plus à l'aveugle.

Trois fonctions portent un bloc et sont appelées par sept à quatorze décors — `0x8C0233B6`,
`0x8C02356A`, `0x8C028792`. Elles sont **génériques** : leur bloc n'appartient à aucun
décor en particulier, et le prendre pour une attribution serait refaire l'erreur du bloc de
Yang. Les décors 7, 12, 14 et 15 n'ont aucun bloc.

### L'ANIMATION DE PAGES — le mécanisme, et comment on la pose — 30/08/2026

**Certains décors n'animent pas des sprites, mais des PAGES.** `bg_data.c` porte le
mécanisme d'origine :

    bgrw_on[stage][8]   -> index dans bgrw_data_tbl, -1 = fin
    bgrw_data_tbl[rw]   -> { bg_num (le plan), rwgbix (la page SOURCE), rw_ptr }
    rw_ptr              -> [duree, page cible, duree, page cible, ...] termine par -1,
                           et la suite BOUCLE (`bg.c`, autour de la ligne 690)

Les pages source sont chargées à part, `rewrite_scr[stage]` d'entre elles, à l'index
`0x64`. **Nos quinze étages ont `bgrw_on = {-1, ...}`** : aucune animation de page. C'est
la cause de « la cascade ne coule pas » et de « l'entrée de la grotte manque ».

> **La deuxième banque d'un `.pvc` peut être un MAGASIN et non une couche.** Chez Akuma
> elle porte six variantes de la même cascade et une page aux braises. La poser comme plan
> donne une mosaïque et des rectangles noirs.

**Comment l'entrée de grotte a été posée** — et la méthode vaut pour les autres :

1. repérer la page du magasin : chez Akuma la **page 22**, seule page chaude des 32
   (teinte R47 V48 B27 contre du vert partout) ;
2. compter les images empilées : deux de 80×64, **1068 pixels de différence** entre elles ;
3. trouver le trou correspondant dans le plan : `ndimage.label` sur le transparent du
   premier plan donne **un seul trou intérieur, 688,320, de 80×64** — exactement la taille ;
4. en faire un **objet animé de notre système** plutôt que de porter `bgrw_data_tbl` : les
   tuiles viennent des pages, la palette se déduit des couleurs employées (33 ici, la
   limite est 63), et `animer2i.PAGES_ANIMEES` s'en charge.

### LE MÉCANISME DE 2nd IMPACT, EN ENTIER — 31/08/2026

Il n'y avait pas à deviner : 2nd Impact porte le même mécanisme, et son binaire le donne
complet. **On n'a plus besoin de chercher les trous à tâtons : la destination est écrite.**

    0x8C0277C4(k)        cree l'objet d'animation de pages ; k va en +4 de l'objet
    0x8C17D8DC + k*20    { s32 plan, s32 slot, s16* suite, u8* debut, u8* fin }
    la suite             des paires [duree, page], terminee par -1, et elle BOUCLE
    0x8C17D3DC + k*2     le decalage de DESTINATION

et ce décalage vaut

    decalage = 4 * (index du bloc 16x16 dans un plan large de 1024)
    d'ou   x = (index % 64) * 16     y = (index / 64) * 16

**L'appelant donne l'appartenance, et lui seul** — comme pour les blocs. En suivant les
`jsr` depuis les dix-sept scripts d'étage, registre par registre :

| étage | entrées | ce que c'est |
|---|---|---|
| 7 | 4, 5, 11 | — |
| 8 | 6, 7 | — |
| 9 | 0 | — |
| 15 (Akuma) | 8, 9, 10 | les deux cascades et l'entrée de la grotte |

> **L'INDEX D'ÉTAGE EST L'INDEX DE BANDE.** Longtemps supposé, maintenant établi : les neuf
> index de base secondaire que les scripts passent en dur tombent tous sur la palette de la
> bande de même numéro — étage 2 → bg02, 3 → bg03, 4 → bg04, 5 → bg05, 6 → bg06, 8 → bg08,
> 10 → bg0a, 11 → bg0b. **Huit sur huit.** C'est ce qui autorise à lire `0x8C1D3FB4` comme
> une table de bandes, et donc à dire que l'étage 15 est bg0f.
>
> Au passage : la base de palette de bg0f est **2144, 15 palettes**. Elle manquait.

**Les trois animations d'Akuma**, toutes à 4 trames par image :

| entrée | plan | destination | grille dans le magasin | images |
|---|---|---|---|---|
| 8 | 0 (lointain) | bloc 1289 → x144 y320 | 0,0 — 2 col × 3 lig de 304×144 | 6 |
| 9 | 0 (lointain) | bloc 1113 → x400 y272 | 768,0 — 4 col × 1 lig de 48×128 | 4 |
| 10 | 1 (proche) | bloc 1323 → x688 y320 | 768,256 — 1 col × 2 lig de 80×64 | 2 |

**Les deux mesures se rejoignent.** Ces trois destinations calculées tombent *exactement*
sur les trois seules fenêtres entièrement transparentes des plans, celles que la recherche
de trous avait élues séparément. Rien à arbitrer.

**La découpe du magasin se mesure aussi**, et sans ambiguïté : les six tuiles de 304×144
s'écartent de **0,6 à 1,1** les unes des autres, contre **~70** pour deux découpes au hasard
du même bloc. Un facteur soixante-dix. Même méthode pour les deux autres : 4 colonnes de
48×128 donnent 0,52 contre 31 et 41 pour les autres découpes ; 2 lignes de 80×64 donnent
2,0 contre 29.

> **La corrélation, elle, ne sert à rien ici.** Chercher la trame dans le plan par
> glissement donne un meilleur écart de 51 contre 74 en médiane — aucun minimum franc, et
> pour l'entrée de la grotte elle désigne un endroit *faux*. La raison est simple : les
> trames ne sont pas peintes dans le plan, leur emplacement y est **vide**.

**La contrainte de cache se contourne en servant, pas en retaillant.** La grande cascade
fait 19×9 = 171 cases quand la clé `rang<<11 | image<<5 | case` n'en porte que 32. Elle est
donc découpée en **sept objets voisins** de 3 cases de large, qui se rejoignent au pixel
près. Chacun bâtit sa **propre palette** sur sa seule tranche — ce qui règle du même coup
ses 81 couleurs sur toute la largeur, quand une palette n'en tient que 63.

Et `by` est le y **dans son propre plan**, celui que donne l'index de bloc : `y = 512 - by
- (ligs-1)*16`. L'entrée de la grotte portait 832, mesuré dans la banque entière ; c'est la
même chose pour la moitié basse (1024−832 = 512−320) mais faux pour la moitié haute, où le
plan lointain serait sorti à 576, bien au-delà de l'écran.

**Ce qui reste à trancher :** `famille` et `z` des objets du plan lointain. Le binaire ne
les donne pas — ce sont des grandeurs de notre moteur. Posés à 1 et 92 par analogie avec la
grotte d'Oro, à vérifier à l'écran.

### IBUKI — un magasin qui est AUSSI la couche — 31/08/2026

`bg07` a le même défaut qu'Akuma, mais pas la même solution. Sa `banque 0 haut` porte six
trames de la même cascade (deux bandes de 816×245, trois colonnes de 272) : écarts mutuels
**1,7 à 2,4 contre 92** pour des découpes au hasard. On la posait telle quelle comme plan
de fond, d'où la mosaïque.

**Mais ce n'est pas un magasin à part comme chez Akuma : c'est le plan 0 lui-même.** Deux
mesures le disent :

1. **Aucune largeur de plan ne fait tomber les destinations sur une fenêtre libre.** Testé
   de 32 à 128 blocs : toutes tombent sur du contenu, occupé à 56–91 %. Chez Akuma les
   trois destinations étaient des trous exacts — c'était le cas particulier, pas la règle.
   Une réécriture *remplace* normalement du contenu.
2. **Les deux destinations tombent chacune dans une vignette, et dans deux vignettes
   distinctes sur les six** — (368,144) dans celle de (272,11), (224,336) dans celle de
   (0,267). Le plan porte donc réellement **deux cascades**, à ces deux places, et les
   quatre autres vignettes sont la **réserve d'animation**.

D'où la fabrication (`couches2i.FABRIQUER`) : effacer la réserve, garder les deux cascades
à leur place, laisser le petit bâtiment aux bambous.

> **Une demi-banque peut donc être trois choses**, pas deux : une couche, un magasin à part
> (Akuma), ou **une couche qui garde sa propre réserve hors champ** (Ibuki). Le tri se fait
> sur les destinations, pas sur l'aspect.

### LA TABLE `0x8C1D54E0` — CE N'EST **PAS** LES LIMITES DE CAMÉRA — 31/08/2026

**Piste fermée, et l'erreur de raisonnement vaut d'être notée.** La table a bien douze
octets par étage, deux paires en `x` puis une en `y`, et elle est **cohérente** : sur les
dix-sept étages, la seconde paire vaut exactement la première rétrécie de 56 pixels de
chaque côté (Gill 272+56=328 et 752−56=696 ; Alex 202+56=258 et 816−56=760 ; Ibuki
328+56=384 et 688−56=632).

> **Cette cohérence ne prouvait que la cohérence.** J'en ai conclu le *rôle* de la table —
> qu'elle alimentait `limit_tbl3` — alors qu'elle n'établissait que sa structure. Posée sur
> Ibuki, elle rend le niveau **plus étroit que sur Dreamcast**. Frédéric l'a vu tout de
> suite. Les 448 px du port sont plus proches du vrai que les 360 que j'en tirais.
>
> Une table interne cohérente n'est pas une table identifiée. Il fallait une mesure
> *externe* — une capture Dreamcast — avant d'y toucher.

Les valeurs, pour mémoire, si la table se révèle être autre chose (une zone de mort, des
bornes de collision, un cadrage d'intro) :

| décor | étage | paire 1 | paire 2 | y |
|---|---|---|---|---|

| décor | étage | plan 0 | plan 1 | y |
|---|---|---|---|---|
| bg00 gill | 22 | 272..752 | 328..696 | 160..176 |
| bg01 alex | 23 | 202..816 | 258..760 | 160..176 |
| bg02 ryu | 24 | 322..696 | 378..640 | 144..160 |
| bg03 yun | 25 | 290..730 | 346..674 | 160..176 |
| bg04 dudley | 26 | 340..692 | 396..636 | 160..176 |
| bg05 necro | 27 | 340..696 | 396..640 | 144..160 |
| bg06 hugo | 28 | 324..684 | 380..628 | 144..160 |
| bg07 ibuki | 29 | 328..688 | 384..632 | 144..160 |
| bg09 elena | 30 | 328..700 | 384..644 | 160..176 |
| bg0a oro | 31 | 328..700 | 384..644 | 160..176 |
| bg0b yang | 32 | 328..700 | 384..644 | 160..176 |
| bg0c ken | 33 | −336..352 | −281..297 | 80..128 |
| bg0d sean | 34 | 304..692 | 360..636 | 208..208 |
| bg0e urien | 35 | 322..700 | 376..646 | 224..224 |
| bg0f akuma | 36 | 209..756 | 265..700 | 208..208 |

**Rien n'a été gardé de cet essai** : `limit_tbl3[29]` est revenu à 288..736 / y 240.

### LE VRAI BORNAGE DE CAMÉRA — `0x8C0D9C26` — 31/08/2026

**2nd Impact n'a aucune limite par étage.** Le code borne la caméra ainsi :

    r13 = 0                        borne basse
    r3  = u8 [0x8C841F3C]          un drapeau global
    r14 = 495  si drapeau != 0     (littéral 0x8C0D9C74)
    r14 = 383  si drapeau == 0     (littéral 0x8C0D9C76)
    clamp(position, 0, r14)

Les bornes elles-mêmes sont dérivées des **deux combattants** : pour chaque joueur,
`demi = u16[table + u16[joueur+856] * 2]` puis `bord = u16[joueur+96] ± demi`. Le pas entre
les structures des deux joueurs est **1036**.

> **La correspondance qui cale tout : 383 de course tombe exactement sur le défaut de
> 3rd Strike, `{0x140, 0x2c0}` = 320..704.** L'autre valeur, 495, donne 512 ± 248 =
> `{0x108, 0x2F8}`, soit 496 de course.

Les limites que nos quinze étages portent à la main sont donc des **inventions** : le code
n'en propose que deux. Le drapeau `0x8C841F3C` est lu en 105 endroits et écrit en quatre ;
l'un d'eux (`0x8C0D302C`) y met 1 sans condition. Ce qu'il distingue reste à établir.

### ET DEUX AUTRES PISTES FERMÉES

* **L'origine des plans n'est pas une donnée par étage.** Le littéral posé en `+26` (le
  champ que l'accumulateur incrémente) vaut **512 pour les dix-sept étages**, sans
  exception. Et `bg220.c`, qui gère nos étages ajoutés, pose déjà `0x200` = 512. Rien à
  porter, rien à corriger.
* **L'affectation des coefficients de parallaxe est juste** : ciel 0,25 (objet 2),
  cascades 0,625 (objet 0), temple 1,0 (objet 1).

Reste mesuré, et non expliqué : avec la caméra à 288..736, la bande de plan 0 exposée va
de **x 180 à x 844** — 664 pixels, qui traversent les trois colonnes de cellules
(0–271, 272–543, 544–815). C'est pourquoi une cascade apparaît presque partout.

### CE QUI BORNE UN OBJET ANIMÉ : LE NOMBRE DE MORCEAUX, PAS LA TAILLE DU TAS

Monter les **deux** cascades d'Ibuki fige le jeu sur `ＣＧ展開エラー　１６×１６`.
`get_mltbuf16_ext` cherche un morceau que le chemin de téléversement n'a pas posé, et part
en `while (1) {}`. La trace le nomme : `code 0x00d3181f` — objet 3, image 0, case 31 — avec
**43 emplacements** seulement dans la collection.

`mts_OB_page[étage][0] * 256` ne règle donc pas tout. Ce qui compte est le nombre de
**morceaux distincts vivants** : `objets × cases × images`.

| | objets | cases/trame | morceaux distincts | |
|---|---|---|---|---|
| Akuma 36 | 9 | 215 | 1458 | marche |
| Ibuki, deux cascades | 18 | 544 | 3456 | **fige** |
| Ibuki, une cascade | 9 | 272 | 1728 | à l'essai |

La règle pratique : rester près de la configuration éprouvée d'Akuma. Un objet large se
sert en morceaux voisins, mais chaque morceau multiplie le compte par son nombre d'images.

### TROIS PISTES FERMÉES SUR IBUKI, pour ne pas les rouvrir

1. **Les pages ne sont pas tassées.** Retirer les pages vides et resserrer coupe le temple
   en deux et mélange les cascades. La disposition des demi-banques est la bonne.
2. **2nd Impact n'a pas de table de masques par plan.** Recherchée sur tout le binaire en
   exigeant que les popcounts égalent les pages non vides mesurées : zéro correspondance.
3. **Effacer quatre des six vignettes de `banque 0 haut` ne change rien à l'écran** —
   elles ne sont pas dans le champ. Ce n'était donc pas une mosaïque visible, et
   `couches2i.FABRIQUER` est reparti vide.

**Ce qui reste sur Ibuki :** animer les deux cascades (six trames, 4 par image — identifiées
mais non générées, on valide la place d'abord : c'est ~1 Mo de tuiles), et caler l'entrée 11
(plan 1, deux images à cadence irrégulière, sans doute les fenêtres du bâtiment) dont la
destination ne tombe pas où on l'attendait.

### CORRECTION : le bloc `0x8C17E918` EST BIEN CELUI D'ORO

La section qui suit a conclu qu'il appartenait à Yang. **C'est faux, et l'écran le dit** :
la vasque, la vapeur, les trois chutes d'eau et l'édifice de pierre sont ceux d'Oro,
Frédéric est formel, et la combinaison `bloc 0x8C17E918 + asset bg0a + table de scripts du
décor 9` les rend exactement.

Ce qui reste vrai et non expliqué : **le bloc est appelé par le script d'étage d'index 10,
alors que la table de scripts qui le résout est celle d'index 9.** Les deux tables ne sont
donc pas indexées de la même façon — et c'est ce décalage, pas l'appartenance du bloc, qui
est à percer. Lire la suite comme le raisonnement qui a échoué, pas comme un acquis.

### LE BLOC `0x8C17E918` N'EST PAS CELUI D'ORO — c'est celui de YANG (30/08/2026) — FAUX

Le code le dit sans détour. Le chargeur `0x8C02E1FE` est appelé par **neuf** scripts
d'étage, chacun avec son argument, et l'argument désigne l'entrée de sa table :

| arg | appelé depuis le script du | bloc | nb |
|---|---|---|---|
| 0 | décor 2 — `bg02`, Ryu | `0x8C17E7A8` | 6 |
| 1 | décor 3 — `bg03`, Yun | `0x8C17E808` | 2 |
| 2 | décor 4 — `bg04`, Dudley | `0x8C17E828` | 1 |
| 3 | décor 5 — `bg05`, Necro | `0x8C17E838` | 10 |
| 4 | décor 6 — `bg06`, Hugo | `0x8C17E8D8` | 3 |
| 5 | décor 16 — `bg10` | `0x8C17E908` | 1 |
| **6** | **décor 10 — `bg0b`, Yang** | **`0x8C17E918`** | **8** |
| 7 | décor 11 — `bg0c`, Ken | `0x8C17E998` | 1 |
| 8 | décor 13 — `bg0e`, Urien | `0x8C17E9A6` | 2 |

    nombre = u16 [0x8C17E794 + arg*2]      pointeur = u32 [0x8C5F9F64 + arg*4]

Les nombres et les pointeurs sont **contigus sur les huit premières entrées** en
enregistrements de 16 octets : la table se valide elle-même.

> **Les huit objets affichés sur l'étage d'Oro depuis le début du chantier sont ceux de
> YANG**, rendus avec l'asset et les palettes d'Oro. Ils avaient l'air plausibles parce que
> les deux décors sont des grottes.

> ### ET VOICI POURQUOI L'ÉPREUVE DE L'ASSET NE VALAIT RIEN
>
> Mesure faite sur cinq blocs : **chacun se résout à 100 % dans le décor que le code lui
> donne, ET à 100 % dans Oro.** Six sur six, dix sur dix, huit sur huit — des deux côtés.
> L'épreuve « le script se résout dans l'asset du décor » ne discrimine donc **rien du
> tout**, pas seulement pour `bg0b`. Tout ce qui a été attribué par elle est à reprendre :
> seul l'appelant du chargeur dit à qui un bloc appartient.

### LA CHAÎNE D'ORO, ÉTABLIE PAR LE CODE — et le format n'est pas celui qu'on croyait

L'état 0 du script d'étage se termine par `mov #6,r4 ; jmp @r2` avec `r2 = 0x8C025A9A`.
Cette fonction est un **chargeur d'objets de décor**, du même modèle que le générique :

    0x8C1D3FB4[9]  = 0x8C0DE0A4              le script d'etage d'Oro
        etat 0 -> 0x8C025A9A avec arg = 6
    0x8C025A9A :
        nombre = u16 [0x8C17C1F8 + arg*2]  =  1
        bloc   = u32 [0x8C5F9DF8 + arg*4]  =  0x8C17C30E
        scripts= u32 [0x8C5F9B38 + (decor*3 + aire)*4]

> ### IL N'Y A PAS UN FORMAT D'ENREGISTREMENT, IL Y EN A UN PAR CHARGEUR
>
> Les huit `mov.w @r14+` de chaque boucle donnent le format, et **les deux chargeurs connus
> ne le rangent pas pareil** :
>
> | u16 | `0x8C02AA7C` (générique) | `0x8C025A9A` (Oro) |
> |---|---|---|
> | #0 | … | objet+32 |
> | #1 | … | objet+558 |
> | #2 | **x** (objet+102) | objet+554 |
> | #3 | **y** (objet+106) | **x** (objet+102) |
> | #4 | objet+88 | **y** (objet+106) |
>
> Autrement dit : **x à l'offset +4 pour l'un, +6 pour l'autre.** Toute la chaîne actuelle
> — annuaire, `poser2i`, `animer2i` — suppose `+4`. Pour Oro, son propre chargeur dit `+6`.
> C'est à vérifier avant d'aller plus loin, et ça se vérifie sans essai à l'écran.

**L'anomalie à lever :** ce chemin ne donne qu'**un seul** objet pour Oro, et cet
enregistrement ne se résout dans aucun des deux formats. Il y a donc au moins un autre
chargeur — `0x8C0277C4`, appelé juste avant avec `mov #0,r4`, est le candidat immédiat :
c'est une fonction propre à Oro, et elle porte `0x8C17D3DC` et `0x8C17D8DC`.

**Ancien objectif, atteint :** le code commun qui crée les objets de décor de l'étage courant,
et d'où il tire son index. Le point de départ est la globale **`0x8C6AF304`** — `+4` le
décor, `+5` l'aire — et le motif à suivre est un spawner appelé avec un index dérivé
d'elle. Ce qu'il ne faut PAS refaire : chercher `décor*3 + aire`, qui n'indexe que la
table des scripts.

**Ancien objectif, sans objet :** l'appelant qui fournit `arg2` pour Oro. Les deux appels connus
de `0x8C02AA7C` passent une constante (`mov #3,r5`). Il faut donc remonter au code d'étage
d'Oro, comme on l'avait fait pour `bg00`. C'est là, et seulement là, que se trouvent ses
chatons, son perroquet et son chien — et non dans un bloc deviné.

### Une piste qui n'a PAS abouti — 30/08/2026, à ne pas refaire telle quelle

Il y a autour de `0x8C5F9F34` une table dont plusieurs pointeurs valent **exactement
enregistrement − 2**, comme celui de l'annuaire des éléments, et qui borne joliment des
blocs de 16 octets :

    8C17E7A6 -> 8C17E7A8    8C17E836 -> 8C17E838    8C17E916 -> 8C17E918
    8C17E806 -> 8C17E808    8C17E8D6 -> 8C17E8D8    8C17E996 -> 8C17E998

J'en ai conclu que c'était l'annuaire des objets animés. **C'est faux, et ça a coûté un
essai.** Deux mesures le disent :

* recalée pour que le décor 9 tombe sur `0x8C17E916` — son bloc validé à l'écran —, elle
  ne résout proprement que trois décors voisins sur quatorze ;
* le pointeur qu'elle donne au décor 9 dans son alignement d'origine, `0x8C031D9A`, ne
  pointe pas sur des enregistrements du tout : plan 57384, x 20258, script 35079.

Un seul acquis en sort, et il tient : **le bloc d'Oro compte huit enregistrements et non
sept**. `0x8C17E918` avait été écarté à tort — son script 0 se résout, quatorze images.

> ### `resout()` seul ne discrimine RIEN, et c'est le piège du chantier
>
> J'ai attribué à Oro le bloc `0x8C17E838` parce que ses dix enregistrements se résolvent
> tous dans son asset, avec des palettes dans sa plage. **Il se résout aussi 10/10 dans
> l'asset du décor 8**, à qui il appartient. Ses bêtes posées sur Oro sortaient empilées
> en x 336, 339, 323, 321 — vu à l'écran. C'est le même avertissement que le span de
> `bg0b`, mais il vaut pour *tous* les décors : qu'un bloc se résolve ne dit pas qu'il est
> à vous. Il faut un second chemin — une position mesurée, un recoupement — avant de
> générer quoi que ce soit.

**La clé de cache borne la grille à 32 cases.** `decor_objets.c` forme
`cle = rang << 11 | image << 5 | case` : cinq bits pour la case, six pour l'image, cinq
pour le rang. `0x8C17E858` (sprite 81, 7 × 6 = 42 cases) est écarté pour ça, et l'outil le
dit au lieu de le taire.

### La ménagerie d'Oro : ce qu'elle est, et ce qui reste à trouver

Le catalogue est établi, et il vient des sprites eux-mêmes (`planche_sprites.py`) :

| script | images | sprites | ce que c'est |
|---|---|---|---|
| 13 | 22 | 136–148 | **le gros chat couché de dos** — c'est sa QUEUE qui bouge |
| 51 | 9 | 149–152 | le gros chat qui se redresse |
| 14 | 1 | 153 | **deux chatons, fixes** — déjà cuits, élément `0x8C17BB34` |
| 16–19 | 12–16 | 154–191 | **les chatons animés** |
| 20–26 | 4–46 | 192–208 | **le perroquet** — 24 sur son perchoir, 26 à l'envol |
| 27–31, 40, 41 | 1–14 | 210–239 | **le chien** — 27 debout, 41 qui se lève |
| 32–39 | 1–9 | 240–257 | les chauves-souris |

Trois enregistrements ont été essayés pour les poser — `0x8C17BDB2` (chat), `0x8C17BD50`
(perroquet), `0x8C17BD40` (chien) — et **rejetés à l'écran** : « le perroquet et le chat ne
sont pas à leur place, le chien au premier plan non plus ». Ils venaient d'un bloc choisi
sur la seule dispersion de ses x, faute de mesure. Un pari, donc, et perdu.

**Ce qui manque est le bloc, pas les bêtes.** Et il ne se trouvera pas par `resout()` :

* aucun animal d'Oro n'est peint dans la banque du disque — `peints.py`, les deux banques
  de palettes, ne trouve que l'édifice de pierre. Il n'y a donc **aucune position mesurée**
  pour eux, contrairement à l'édifice ;
* la recherche a été faite en entier pour les scripts 14, 16, 17, 18, 19, 21, 22, 23 et 51 :
  **tout** enregistrement de 16 octets du binaire qui les poserait à ±24 px de la
  plate-forme. Un seul répond, `0x8C17BB34`, l'élément statique des deux chatons — et il
  tombe **au pixel** sur l'attendu, ce qui valide la formule de placement par un chemin
  qui ne l'avait pas encore éprouvée.

Les tables d'objets animés connues :

    bg00   0x8C183DC8   4 enregistrements de 8 octets   {x, y, palette, script}
                        litteral de code en 0x8C04AE68
    bg0a   0x8C17E918   8 de 16 octets                  le format de l'annuaire
                        0x8C17E916 n'apparait qu'UNE fois dans le binaire, en 0x8C5F9F7C

`outils/animer2i.py` génère tout, et l'épreuve qui le valide : il rend `288, 81` pour
l'acolyte de Gill — la valeur vérifiée à l'écran, retrouvée depuis le binaire seul.

## Les palettes

    numero = base(decor, drapeaux) + offset      avec le champ palette du MORCEAU
             drapeaux = champ >> 9    offset = champ & 0x1FF
    couleurs = banque du binaire, offset 0x1D9AEC, 2715 palettes de 64 couleurs RGB555

Adresse confirmée par `0x8C0F59AA` : `r4 + 0x8C1E9AEC - 0x02798000`. Bases dans
`outils/bases.py`, vérifiées ici : l'acolyte, offset 44, donne **871**.

### Un décor peut avoir DEUX banques, et Oro en a deux — 30/08/2026

On a cherché *la* base d'Oro, et les deux candidates se contredisaient à l'écran : 1674
rendait la chute d'eau bleue, 1429 rendait le chien vert fluo. **Les deux sont justes**, et
c'est l'**offset du morceau** qui les sépare, pas ses drapeaux :

    offsets 16..20  ->  1429    la grotte : la vasque, la vapeur, les chutes, l'édifice
    offsets  0.. 3  ->  1674    les bêtes : les chats, le perroquet, le chien, les
                                chauves-souris

Ce n'est pas un réglage : **aucun des 272 sprites de l'asset ne mélange les deux groupes**,
et la coupure tombe pile entre le sprite 135 et le sprite 136. Chaque banque tient par une
mesure indépendante — 1429 par l'édifice de pierre peint dans la banque du disque (palette
1446 relue sur 17 index sur 18, offset 17), 1674 par les couleurs des bêtes, qui sont
celles de la capture du jeu. `bases.numero(décor, drapeaux, offset)` les démêle ;
`BASES_2I` seul ne le pouvait pas.

> **Un aplat passe toutes les épreuves de recoloriage.** L'épreuve « la page est-elle un
> recoloriage cohérent du sprite ? » se satisfait d'une plage d'une seule couleur : tous
> les index y tombent sur cette couleur-là, l'application existe, l'accord vaut 100 % et
> ça ne prouve rien. Une version sans ce garde-fou a « trouvé » cent quarante sprites
> d'Oro peints dans ses pages, presque tous calés sur une ligne vide. Ce qui sépare les
> deux, c'est le nombre de **couleurs distinctes** : un vrai sprite en montre presque
> autant que d'index. C'est le paramètre `distinctes` de `palette_peinte.accord`.

> **Ne jamais mesurer sur les pages cuites.** Elles portent déjà ce que nos outils y ont
> posé — les chats de `poser2i.py` y sont, avec la base du jour où on les a cuits, et le
> perroquet y est resté d'une cuisson encore plus ancienne. Y lire une position ou une
> palette, c'est se relire soi-même. **C'est la banque du `.pvc` qui fait foi**, et c'est
> ce que rend `situer_animes.pages()`. Sur Oro, un seul objet y est vraiment peint :
> l'édifice de pierre.

Trois pièges mesurés :

* **Prendre la palette de l'ÉLÉMENT au lieu du morceau** donne un emplacement faux — 913
  au lieu de 839 pour l'obélisque — et un dégradé plat qui ne varie que par le bleu.
* **Le champ n'est pas constant sur un sprite : chaque morceau garde LA SIENNE.** Le
  temple d'horizon en a deux — 842 sur deux de ses dix-sept morceaux, 867 sur les quinze
  autres — et les obélisques aussi, 848 et 850. Imposer celle du premier morceau à tout
  le sprite sort 29 pixels de magenta sur le temple et 123 sur les obélisques, vus à
  l'écran le 29/08. C'est `assemblage.poser_couleur` qui fait ça, pas `poser`.
* **Une palette peut avoir ses premières entrées en magenta `0xFC1F` sans être fausse.**
  L'obélisque n'emploie que les index 7 à 15 et 27 à 31 ; les six magenta ne le concernent
  pas. Vérifier quels index le sprite utilise avant de conclure.

---

## Le placement

### Un sprite CUIT dans une page

    x = (element.x + ancre_x + x0) & 0x3FF
    y = (sol - element.y + ancre_y + y0) & 0x3FF        sol = 1023 pour treize decors

**L'ancre vient du SCRIPT**, pas de la boîte d'une image : elle est identique sur toutes
les images de l'animation, ce qui est la propriété qu'une ancre doit avoir. Pour l'acolyte
de `bg00` elle vaut `(-32, -80)`.

**Et elle ne suffit pas : il y a `(x0, y0)`.** `assemblage.poser` rend
`(image, masque, x0, y0)`, où `(x0, y0)` est le coin de la boîte **dans le repère du
sprite** — c'est écrit dans la fonction, `x0 = min(m['y'] - 8*largeur)`. L'ancre mène de
l'élément à l'origine du sprite, `(x0, y0)` mène de cette origine au coin de l'image :
**les deux s'ajoutent**. `x0` vaut zéro sur les sept éléments de `bg00`, d'où un `x` juste
même en l'oubliant ; `y0` non, et c'est de ces valeurs-là que trois d'entre eux étaient
trop bas.

Positions validées à l'écran pour `bg00`, à ne pas retoucher :

| figure | liste | banque | y0 | source |
|---|---|---|---|---|
| acolyte (element 320,64) | 196 | **288, 863** | -16 | binaire |
| element 576,72 | 196 | 544, 879 | 0 | binaire |
| element 208,136 | 196 | 184, 831 | 0 | binaire |
| element 720,96 | 196 | 696, 879 | 0 | binaire |
| temple (element 528,80) | 260 | **384, 863** | -32 | binaire |
| obélisques (element 608,152) | 260 | 608, 759 | -16 | binaire, **`y0` pas appliqué** |
| petit obélisque (element 496,120) | 324 | 464, 839 | 0 | binaire |

L'outil est `outils/poser22.py`, et il recuit les listes 196, 260 et 324 d'un trait.

> **Contrôle par un chemin indépendant.** Les pages cuites du 29/08 à 12:12, celles dont
> la copie de l'acolyte était bien placée, posaient le temple en 384,863, les obélisques
> en 608,743 et l'acolyte en 288,863. La règle avec `(x0, y0)` rend ces trois positions
> **au pixel** ; sans lui elle rendait 895, 759 et 879.
>
> **Ne déplacer que ce qui est explicitement signalé.** Seuls le temple et l'acolyte
> l'ont été. Les obélisques gardent donc un `y` calculé **sans** `y0` — c'est le `SANS_Y0`
> en tête de `poser22.py`. L'appliquer les remonterait de 16, exactement sur la position
> validée du 12:12. À lever quand Frédéric le dira.



### Un objet ANIMÉ, dessiné par `eff05`

Sa fiche dans `decor_objets_data.c` porte `x` et `y`, qui deviennent `position_x` et
`position_y`. **`suzi_sync_pos_set` ne les transforme pas** quand `sync_suzi = 0` : ils
passent tels quels.

L'asymétrie est du côté des PAGES : `scr_trans` capture `BgMATRIX` **avant** d'appliquer
`njTranslate(0, 0, 1024.0, ...)` puis `njScale(0, 1, -1, 1)`, qui ne touchent que le `y`.

    page a `bank_y`  ->  apparait en  1024 - bank_y
    objet            ->  apparait en  position_y + base_y

**`base_y` vaut ZERO**, et c'est lu : `disp_pos_trans_entry_s` -> `sort_push_request4` ->
`Mtrans_use_trans_mode(wk, 0)`. C'est le chemin exact d'un objet de décor.

**Mais la position de l'objet n'est pas celle du haut de son image.** La grille du motif
met la rangée d'image `lig` en `(ligs-1-lig)*16` — c'est `y_moteur` dans
`decor_objets.c`, l'involution qui remet le sprite à l'endroit — et `mtrans.c` pose un
morceau de `cy-16` à `cy`. La rangée 0 est donc en `position_y + (ligs-1)*16`. D'où :

    position_x = bank_x
    position_y = 1024 - bank_y - (ligs - 1) * 16

Pour l'acolyte de `bg00` : six rangées, `x = 288`, `y = 1024 - 863 - 80 = 81`. **Vérifié
à l'écran le 29/08 : l'objet animé est exactement sur sa copie cuite.** C'est le terme
`(ligs-1)*16` qui manquait ; sans lui, 64 était trop bas de 17 px et 145 trop haut de 64.

### Et d'où vient `bank_y` pour un objet animé

`animations.py` écrivait `y = element.y` **brut** — une hauteur au-dessus du sol de 2nd
Impact, pas une ordonnée du moteur. Les huit objets s'animaient donc correctement sans
jamais être à leur place. `outils/situer_objets.py` les recalcule, et il n'a besoin de
rien d'autre que l'asset :

1. **il identifie le sprite** en comparant l'image 0 de l'animation — désentrelacée
   depuis `decor_objets_data.c` — aux sprites assemblés du décor. Ce n'est pas une
   corrélation, c'est une **égalité** : 6144 pixels sur 6144 pour Gill, 2048 sur 2048
   pour Oro, et pareil pour les six autres ;
2. le sprite donne son **ancre**, `assemblage.poser` donne **`(x0, y0)`** ;
3. `bank_y = sol - element.y + ancre_y + y0`, puis la formule ci-dessus.

> **Il n'y a pas d'écart constant, et c'est le piège.** L'acolyte de Gill a
> `ancre_y + y0 = -96`, la hauteur de sa grille : il se tient **debout** sur son point.
> Le filet d'eau d'Oro a **0** : il **pend**. Une règle d'écart fixe — le « +17 » que
> quatre décors semblaient confirmer — se trompe de 64 pixels sur le second.

L'outil garde le `element.y` d'origine en commentaire dans le fichier C, ce qui le rend
rejouable.

## L'indexation par décor — RÉSOLUE le 29/08/2026

Elle était dans la **suite immédiate de la table maîtresse**. `0x8C5F9B38` n'est pas une
table isolée : c'est la première d'une **série de dix tables de 51 entrées** (17 décors ×
3 aires), posées bout à bout. La deuxième est l'annuaire des éléments.

    0x8C5F9B38 + 0*204   les scripts d'animation      -> 0x8C12xxxx
    0x8C5F9B38 + 1*204   LES ÉLÉMENTS DE DÉCOR        -> 0x8C17Bxxx
    0x8C5F9B38 + 2*204   un second jeu d'éléments     -> 0x8C17Bxxx
    ... huit autres, jusqu'à 0x8C5FA330 où la série s'arrête

Voilà pourquoi aucun pointeur ne semblait viser les blocs : on les cherchait ailleurs. Le
pointeur d'un décor vaut **deux octets avant** son premier enregistrement, et le bloc va
jusqu'au pointeur distinct suivant :

    debut = annuaire[aire] + 2       nb = (suivant - annuaire[aire]) / 16

**L'épreuve qui discrimine**, là où le span seul ne discriminait pas : le numéro de script
s'entend dans la table de scripts **de ce décor-là** (`0x8C5F9B38 + aire*4`), pas dans
celle du décor 0. L'index global obtenu doit alors tomber dans le `index_global` de
l'asset F_ETC **du même décor**. Sur les décors 0 à 12 : **trente éléments, trente dans
leur propre asset, zéro ailleurs.**

| décor | asset | éléments | | décor | asset | éléments |
|---|---|---|---|---|---|---|
| 0 | b00 | 3 | | 8 | — | 0 |
| 1 | b01 | 2 | | 9 | b0a | 1 |
| 2 | b02 | 2 | | 10 | b0b | 2 |
| 3 | b03 | 4 | | 11 | b0c | 5 |
| 4 | b04 | 2 | | 12 | b0d | 2 |
| 5 | b05 | 3 | | 13 | b0e | 1 |
| 6 | b06 | 2 | | 16 | b06 | 2 (bg10 = hugo bis) |
| 7 | — | 0 | | 14, 15 | remplissage | — |

L'outil est `outils/annuaire2i.py`.

> ### Et `bg00` a TROIS éléments statiques, pas cinq
>
> Le temple, les obélisques, le petit obélisque. **Les deux « étoiles filantes » en
> `0x8C17B9B0` et `0x8C17B9C0` sont le bloc du décor 1**, résolues par erreur avec la
> table de scripts du décor 0 et la base de palette de `bg00` — d'où le 827 qui semblait
> les confirmer. Elles sont encore dans la liste 260 de l'étage 22, en attendant l'avis
> de Frédéric : elles n'ont pas été signalées.

## Ce qui reste

Convertir `cuire.py`, `elements.py` et `animations.py` sur cette chaîne, cuire les quinze
étages depuis l'annuaire, puis New Generation (`SF3_1ST.BIN`, `SFNG/`), qui n'a aucun
relevé et pour qui tout ceci a été fait.

**Encore par le code de l'étage, pas par l'annuaire** : la table de 8 octets des figures
animées. Celle de `bg00` est en `0x8C183DC8`, et cette adresse n'apparaît qu'une fois dans
le binaire, comme littéral en `0x8C04AE68`. Aucune des dix tables de la série ne la porte.


---

## LES ACQUIS DU 31/08/2026 — CE QUE NEW GENERATION A APPRIS A 2nd IMPACT

### LES DERNIERS DECORS DE 2I, ET UNE ATTRIBUTION QUI ETAIT FAUSSE — 01/09/2026

**`chargeurs2i.py` debordait, exactement comme `chargeursng.py` avant sa correction.** A la
profondeur 2 il balayait `cible .. cible + 0x200` en aveugle ; quand la fonction appelee est
plus courte, la fenetre mord sur la suivante et ramasse ses appels. Les scripts d'etage de 2I
se suivent en memoire (340 a 1672 octets), donc un cran suffit.

Le symptome qui l'a trahi : **un meme site d'appel attribue a deux decors** — `0x8C0DEB7A`
aux decors 12 et 13, `0x8C0DF198` aux decors 13 et 16. Un site n'est que dans une routine.
En bornant les dix-sept routines par la suivante, ils tombent dans les decors **13**, **16**
et **16**.

Corrige par deux gardes joints : la fenetre s'arrete au premier `rts`, et un site qui tombe
dans la routine d'un *autre* decor est refuse quoi qu'il arrive. La sortie corrigee redonne
**exactement** le tableau d'attribution de ce document — qui, lui, etait juste.

### `sol` N'ETAIT PAS LE SOL — 01/09/2026

**Signale par Frederic sur Sean : « le singe anime est sur sa copie, les sprites sont trop
haut ».** L'alignement objet/copie ne prouvait rien : les deux chaines partagent `sol`, donc
elles s'accordaient entre elles et se trompaient ensemble.

`poser2i.sol()` se lisait :

    """La ligne du sol dans la banque : derniere ligne non vide de la moitie basse."""

Ce n'est pas le sol, c'est **ou s'arrete le dessin**. Or `element.y` est une hauteur
*au-dessus du sol*, et le sol du repere ne depend pas de ce que le decor a peint.

    douze decors sur quatorze  ->  1023   (dont bg00, valide a l'ecran)
    bg0d  Sean                 ->  1007
    bg05  Necro                ->   972

Sur Sean ces 16 pixels remontaient **tout** ce qu'on pose. `sol` est desormais la constante
`SOL_REPERE = 1023`. **`bg05` garde la mesure** (`SOL_MESURE`) : il n'a pas ete signale et
ses quinze objets sont en place — on ne deplace pas ce qui n'a pas ete signale.

> **La mesure qui a confirme avant de corriger**, et non l'inverse : les deux singes ne sont
> peints dans AUCUNE banque du `.pvc`. La « copie » etait donc notre propre cuisson, et on
> l'a retrouvee a la banque **736, 799** — soit exactement `1007 - 208`, le calcul avec
> l'ancien `sol`. La donnee disait le defaut avant qu'on touche a quoi que ce soit.

Cette copie etait un **residu de l'ancienne chaine a savestates** que plus aucun outil ne
regenere ; la laisser aurait fait un doublon decale de 16 px. Effacee (469 px -> 0), avec
sauvegardes `etages2i-sprites/stage34-avant-sol` et `resources/tex_remix/stage34-avant-sol`.

> **Les `.tex` doivent etre DEPLOYES.** Le jeu les lit dans
> `%APPDATA%/CrowdedStreet/3SX/resources/tex_remix/stage<N>/`, pas dans `dc-decors/`.
> Ceux de l'etage 34 dataient du 29/08 : sans la copie, la correction ne serait jamais
> arrivee a l'ecran.

### ET LA VRAIE CAUSE, TROUVEE EN CHERCHANT LE SINGE DE SEAN

**L'INDEX DE `0x8C1D3FB4` EST LA BANDE, PAS LE DECOR.** C'est ca, le « decalage d'index a
partir de l'etage 10 » que ce document constatait depuis le debut sans l'expliquer, et que
la correction du bornage ci-dessus ne faisait qu'effleurer.

La table `0x8C1D591C` donne `(decor*3 + aire) -> bande` et dit que **le decor 8 porte les
bandes 8, 9 et 9** : au-dela, `bande = decor + 1`. Tout l'outillage appelait « decor »
l'index de la table des scripts d'etage — d'ou un cran d'ecart sur la moitie des decors.

**La mesure qui tranche**, les deux lectures mises en concurrence sur les dix-sept blocs :
combien resolvent **100 %** de leurs images dans l'asset du decor suppose ?

| lecture | blocs a 100 % |
|---|---|
| « index = decor » | 14 / 17 |
| **« index = bande »** | **16 / 17** |

Elle ne gagne pas aux points, elle **redresse les deux echecs** :

    index 13 : lu decor 13 (Urien) ->  0/19   -- rien ne se resout
               lu bande 13 -> decor 12 (Sean) -> 46/46
    index 11 : lu decor 11 (Ken)   ->  0/0
               lu bande 11 -> decor 10 (Yang) ->  8/8 et 4/4

Et l'index 10 passe de 4/4 et 8/8 a **16/16 et 82/82** — le critere « beaucoup d'images »
qu'`accorder2i.py` emploie deja. **Ce que Frederic avait tranche a l'ecran est donc confirme
par le calcul** : `0x8C17E918` est bien le bloc d'Oro, appele depuis la BANDE 10.

> **Ce qui est corrige plus haut dans ce document** : « le bloc est appele par le script
> d'etage d'index 10, alors que la table de scripts qui le resout est celle d'index 9 — et
> c'est ce decalage qui est a percer ». Il est perce : l'index 10 est une **bande**, et la
> bande 10 EST le decor 9.

### LE CHEMIN DU SINGE DE SEAN, DE BOUT EN BOUT

Etabli par deux chaines independantes qui se recoupent au pixel et a la trame pres :

    0x8C1D3FB4[13]        bande 13 = bg0d = SEAN (decor 12)
      -> script d'etage 0x8C0DEAD8
         dispatcher, table d'etats 0x8C1D6184, etat 0 = 0x8C0DEB22
           en 0x8C0DEB7A : chargeur 0x8C02E1FE, arg 8
             nombre = u16[0x8C17E794 + 8*2] = 2
             bloc   = u32[0x8C5F9F64 + 8*4] = 0x8C17E9A6
               +2  : script 6, 30 images          -- PAS ENCORE POSE
               +18 : script 7, x 736 y 208 pal 72 -- LE SINGE
    resolu par la table de scripts du decor 12, 0x8C122774

**Les recoupements**, aucun n'ayant servi a caler l'autre :

* le sprite 18 de l'asset `bg0d` **egale** l'image 0 de la fiche : 2560 pixels sur 2560 ;
* le script 7 porte les durees `6,6,6,6 8,8,8,8 10,10,10,10 8,8,8,8` — **exactement** les
  `a34_durees` du C — et quatre images distinctes repetees quatre fois ;
* l'enregistrement `x 736, y 208, script 7` est **le seul du binaire entier** a cette
  signature ;
* la position recalculee depuis l'asset retombe sur `y 161`, la valeur de la fiche.

Le singe n'etait donc pas une invention : il etait juste **sans provenance ecrite**, parce
que l'outillage cherchait son bloc chez le mauvais proprietaire.

**Le bilan des derniers decors, avec la bonne lecture :**

| etage | bande | perso | decor | blocs que le CODE donne | poses |
|---|---|---|---|---|---|
| 26 | `bg04` | Dudley | 4 | `8C17E826` (1) | **0** |
| 30 | `bg09` | Elena | 8 | `8C17C30E` (1) | **0** |
| 33 | `bg0c` | Ken | 11 | *aucun* | 0 |
| 34 | `bg0d` | **Sean** | 12 | `8C17E9A6` (**2**) | **1** |
| 35 | `bg0e` | Urien | 13 | *aucun* | 0 |

Ken et Urien n'ont **aucun** bloc — leurs objets supposes venaient du decalage. Restent
**trois objets a poser** : un chez Dudley, un chez Elena, et le second de Sean (script 6,
30 images).

### La table decor -> bande, `0x8C1D591C`, et le fameux « decalage a partir de l'etage 10 »

Trouvee d'abord sur New Generation (`0x8C18A804`), verifiee ensuite sur 2I. Elle donne
`(decor * 3 + aire) -> bande`, et elle est lue par `0x8C0DA3E2` :

| decor | bandes (aire 0 / 1 / 2) |
|---|---|
| 0 a 7 | identite |
| **8** | **8 / 9 / 9** |
| 9 a 14 | 10 a 15 -- tout est decale d'un cran |

**`bg08` et `bg09` sont deux bandes d'UN SEUL decor.** C'est exactement le decalage que ce
document constatait sans l'expliquer (« Oro etage 10 -> table 9, Yang etage 11 -> table
10 »). Le mecanisme des variantes existait deja dans le port -- `bg_index_tbl[etage][aire]`,
une ligne dans `bg_sub.c` -- il n'y manquait que la donnee.

> **Attention a ne pas confondre deux indexations.** La table des scripts d'etage
> `0x8C1D3FB4` est indexee par la **bande** (verifie : les neuf index de palette passes en
> dur tombent tous sur la bande de meme numero, huit sur huit). La table ci-dessus est
> indexee par le **decor**. Les deux coexistent.

### Deux corrections au format des blocs

* **Le pointeur d'un bloc de chargeur vise le champ 0, pas le champ `plan`.** Le `+2` ne
  vaut que pour l'annuaire des elements. Applique aux blocs, il decale tout d'un champ.
* **`objet[+102] += parent[+102]`, et le parent est l'OBJET APPELANT, pas le contexte.**
  Ce document ecrivait « contexte ». Verifie sur NG (`0x8C0A2262`), ou le parent est `r10`,
  premier argument de l'appel.

### Le bornage de camera, et la piste fermee

`0x8C0D9C26` : 2nd Impact n'a **aucune limite par etage**. Il borne a `[0, 495]` ou
`[0, 383]` selon le drapeau global `0x8C841F3C`, les bornes venant de la position des deux
combattants (`joueur+96`) et d'une demi-largeur par personnage (table indexee par
`joueur+856`, pas de 1036 entre les deux joueurs). **383 de course tombe exactement sur le
defaut de 3rd Strike, `{0x140, 0x2c0}`.**

> **PISTE FERMEE : `0x8C1D54E0` n'est pas la table des limites.** Elle est coherente -- sa
> seconde paire vaut la premiere retrecie de 56 px sur les dix-sept etages -- mais posee
> sur Ibuki elle rend le niveau plus etroit que sur Dreamcast. **Une coherence interne
> prouve un decoupage, pas un role.**

### L'origine des plans : rien a porter

Le litteral pose en `+26` (le champ que l'accumulateur incremente chaque trame) vaut
**512 pour les dix-sept etages**, sans exception. Et `bg220.c` pose deja `0x200` = 512.
La position d'un plan est **accumulee** (`@(26, plan) += coefficient x deplacement`), pas
recalculee depuis une position absolue.
