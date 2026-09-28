> ## 29/08/2026 — LES SAVESTATES SONT SORTIS DE LA CHAINE
>
> **Tout ce qui suit et qui passe par `releves2/` est perimé.** La liste d'affichage, les
> positions, les sprites, les cadences et les palettes se lisent maintenant dans le
> **binaire et les assets du disque** — voir **`SANS-ETAT.md`**, qui fait foi.
>
> Validé a l'ecran : le petit obelisque de `bg00` et ses quatre figures animees, sans
> qu'un seul `.state` soit ouvert. C'est la condition pour New Generation, qui n'a aucun
> releve.
>
> Restent a decoder : les elements de decor STATIQUE du plan 2, et l'indexation par
> decor de la table des elements.

Chantier : **AJOUTER** les décors de Street Fighter III New Generation et 2nd Impact,
depuis le disque Dreamcast de Double Impact, **à** 3SX — le port natif de 3rd Strike.

Ajouter, pas repeindre. Une partie de la session précédente a été perdue à repeindre un
décor de 3S avec les pixels de 2I avant que Frédéric ne redresse la barre. Ne pas y
retourner : `tex_remix` sert de moyen, pas de but.

Clone de travail `C:\Temp3sx` (git, branche `tout-en-un`).
Matériel du chantier : `C:\Users\frede\Downloads\3sx-outils\dc-decors\`

Documents qui font foi, à lire en premier :

- `FORMAT-PVC.md` — le format `.pvc`, les conteneurs, la parallaxe, les scripts d'étage
- `ASSEMBLAGE.md` — l'assemblage des sprites et la règle des palettes
- `PALETTES-CONFIRMEES.md` — le tableau des palettes, décor par décor
- `CARTES-BG.md` — `bg_map_tbl` décodé, et **la règle de placement des pages de 3SX**
- `TESTER.md` — comment tester les sprites de décor, et ce qui doit sortir

---

## FAIT : quinze décors de 2nd Impact sont dans 3rd Strike (28/08/2026)

Les **étages 22 à 36** sont les décors de 2nd Impact, sélectionnables en versus à la suite
de ceux de 3rd Strike. `bg02`, le bain chaud de Suzaku sous la neige, a été le premier —
**entier, sans un trou, sans une bande, et avec les mêmes limites de terrain que sur
Dreamcast**, vérifié côte à côte avec Flycast.

| étage | décor | | étage | décor | | étage | décor |
|---|---|---|---|---|---|---|---|
| 22 | `bg00` gill | | 27 | `bg05` necro | | 32 | `bg0b` yang |
| 23 | `bg01` alex | | 28 | `bg06` hugo | | 33 | `bg0c` ken |
| 24 | `bg02` ryu | | 29 | `bg07` ibuki | | 34 | `bg0d` sean |
| 25 | `bg03` yun | | 30 | `bg09` elena | | 35 | `bg0e` urien |
| 26 | `bg04` dudley | | 31 | `bg0a` oro | | 36 | `bg0f` la gorge |

Vingt-six tables indexées par l'étage ont été étendues, dans neuf fichiers, relevées par
leurs **consommateurs** et non par leur taille — le jeu a 23 personnages *et* 23 étages.
`outils/ajouter_etages.py` le fait et le vérifie. Détail dans `FORMAT-PVC.md`.

La chaîne complète, chaque maillon mesuré :

1. **La coupe.** Une banque `.pvc` se coupe à `y = 512` : le haut est le plan lointain, le
   bas le plan proche. Vrai sur les 21 décors, sans exception.
2. **Le placement.** `scr_trans()` pose la page `i` en `x = (i & 7) * 128`,
   `y = 512 + (i >> 3) * 128`. Chaque demi-banque se pose donc à l'identique sur les
   32 pages d'un plan. `outils/bande3sx.py` le fait.
3. **Le masque.** L'étage 22 emprunte le bloc de l'**étage 10 (Yang)**, le seul dont les
   deux plans chargent 32 pages sur 32, et `bgtex_stage_gbix[22] = {0xFFFFFFFF, 0xFFFFFFFF}`.
   64 pages, aucun trou de masque.
4. **Le bogue du portage.** Une page était dessinée d'après la liste de rectangles de la
   page *de l'archive*, jamais mise à jour par un remplacement : partout où l'original
   était vide, nos pixels ne sortaient pas. Corrigé — voir `FORMAT-PVC.md`.
5. **Les limites de terrain.** `limit_tbl3[22] = { 0x140, 0x2C0 }`, calculé sur l'étendue
   de l'art. `bande3sx.py` sort ces deux nombres pour n'importe quel décor.

**Vérifié contre la planche de référence de 2nd Impact**, par corrélation de profils et
sans lancer le jeu : notre découpe sort à **0,865**, contre 0,59 pour une découpe décalée
de 512 et 0,00 pour la mauvaise moitié du plan. L'alignement trouvé — le plan de **124 à
896** — retombe à quatre pixels près sur les limites de terrain calculées, `128..896`. Deux
mesures indépendantes, le même résultat.

**Ce qui manque encore à l'image, et c'est connu :** les sprites de décor — les baigneurs,
la cascade animée. Ce sont des assets `F_ETC` et des images d'animation de la banque 1,
décodés (`ASSEMBLAGE.md`) mais pas encore posés.

---

## Ce qui est acquis — ne pas refaire

### Côté 2nd Impact : le format est entièrement percé

Le `.pvc` est une suite de 8192 tuiles de 16×16 à **palette locale**, entrelacées en ordre
de Morton, en deux banques de 1024×1024. Les 44 décors sont sortis dans `pvc-2i/` et
`pvc-ng/`, rendus dans `rendus/`. Conteneurs `.pk`, décompresseurs `F_ETCnn`, assemblage
des sprites, palettes : tout est décrit dans les trois documents ci-dessus, avec les preuves.

**Palettes** — `palette = base(décor) + offset`. Quinze décors sur quinze, table dans
`outils/bases.py`.

**Sprites** — le morceau de 8 octets se lit `{u16 tuile, u16 palette, u16 y, u16 code<<12 | x}` ;
le quartet `code` donne la taille en tuiles, **x et y sont des centres**, et les tuiles d'un
morceau se suivent **en colonnes**.

> **LES RETOURNEMENTS — bits 11 et 12 du champ palette du morceau, corrige le
> 29/08/2026 au soir.**
>
>     bit 12 (0x1000)  miroir horizontal        bit 11 (0x0800)  miroir vertical
>
> Ce sont les memes bits que dans l'enregistrement RAM, ou le dessin les lit en
> `0x8C0F6AC6` : `element[+9] ^ (morceau[+2] >> 8)`. **`assemblage.poser` les ignorait**,
> et la comparaison a la RAM les ignorait DES DEUX COTES -- c'etait ca, la circularite qui
> faisait dire "230 sur 230 exacts" a une mesure aveugle.
>
> Le retournement porte sur la case dans le morceau **et** sur les pixels de la tuile.
> 536 morceaux portent le miroir horizontal, 10 le vertical ; 136 sprites sur 2677 (5,1 %).
> Ils servent aux moities symetriques : le morceau miroir reprend la TUILE d'un autre
> morceau du meme sprite. Les ignorer posait deux fois la meme moitie.
>
> **Trouve grace a un sprite corrige a la main par Frederic** -- la femme de `bg05`, dont
> il avait mis quatre morceaux en miroir. Une reference qui ne vient ni de notre decodage
> ni de la RAM telle que nous la lisons : la seule qui pouvait casser la circularite.
>
> **LE SPRITE EST STOCKE TRANSPOSE — corrige le 29/08/2026.** Les deux champs de position
> s'echangent pour arriver a l'ecran :
>
>     image_x = champ Y du morceau        image_y = champ X du morceau
>     largeur = quartet BAS du code       hauteur = quartet HAUT
>
> Mesure contre la liste d'affichage en RAM, qui fait foi, sur les 797 morceaux
> appariables : la lecture transposee tient a **98,9 %** en x et **99,0 %** en y, la
> lecture directe -- celle qu'employait `assemblage.poser` -- a **18,9 %** et **17,3 %**.
> Et la taille se lit **directement** (bas = largeur) a 98,7 %, contre 54,5 % croisee ;
> `taille()` rendait les deux quartets a l'envers.
>
> Les deux erreurs se compensaient en partie : d'ou des sprites justes par hasard et
> d'autres en damier. `assemblage.poser` corrige rend **115 sprites sur 123 identiques
> pixel pour pixel** a ce que la RAM donne, contre aucun avant. Les huit restants sont
> les sprites **mis a l'echelle** (54x107 pour 32x64 : le x1,688 de DONNEES.md section 4).
> Tous les rendus de `rendus/sprites/` et `rendus/planches/` faits avant cette date sont
> a refaire.
>
> **LA LIMITE DE CETTE VERIFICATION, et elle est serieuse.** Un etat Flycast ne fige
> qu'**une image par element**. Les 123 sprites verifies sont donc une image par
> animation ; les autres -- 45 sur 46 pour `bg05` -- n'ont aucune reference. C'est
> precisement la que se trouvent les assemblages encore fautifs.
>
> **La moisson qui a leve la limite.** Le tampon de 32768 enregistrements garde les blocs
> des images PRECEDENTES : ce sont autant de references gratuites, sans nouvel etat. En le
> balayant en entier, et en n'appariant que les sprites d'au moins **deux** morceaux dont
> les tailles concordent -- un sprite d'un seul morceau s'apparie au hasard sur un numero
> de tuile, et c'est ce qui avait pollue la premiere mesure a 55 % --, on passe de 123 a
> **183 sprites verifiables**.
>
> **VERDICT FINAL, 29/08/2026 au soir : 230 sur 230, soit 100 %.** Frederic a sauvegarde
> quatre etats de plus (deux Hugo, deux Necro) : la moisson passe a **307 sprites**, dont
> 230 apparies de facon credible -- au moins trois morceaux, tuiles pas toutes egales,
> tailles concordantes. Les six echecs qui restaient a 98 % etaient tous des faux
> positifs : des sprites de deux morceaux a tuiles consecutives (113, 114), et un sprite
> dont les douze morceaux portent la tuile 0, apparie au bloc vide 512.
>
> **Les treize assets sont exacts.** `bg06` Hugo : 61 sur 61. `bg05` Necro : 61 sur 61.
>
> Etape par etape :
>
> **179 sur 183, soit 97,8 %.** Il restait une derniere faute a corriger pour y
> arriver : `y` n'etait **pas etendu en signe** alors que `x` l'etait. Un y negatif sortait
> a 4095 et la boite du sprite faisait 4096 de haut. Cinq des neuf derniers echecs etaient
> ceux-la.
>
> Les quatre qui semblaient resister -- `b02` 11, `b0a` 263, `b03` 213, `b05` 12 --
> etaient tous des faux appariements, pas des defauts. Un sprite de deux morceaux se
> reconnait sur deux numeros de tuile consecutifs, ce que n'importe quelle paire
> d'enregistrements voisins satisfait.
>
> **UNE PLANCHE DOIT ANCRER SES IMAGES SUR UNE ORIGINE COMMUNE.** `assemblage.poser`
> normalise chaque sprite sur SA boite englobante. Coller les images d'une animation
> chacune dans sa boite les fait sauter les unes par rapport aux autres, et l'oeil lit ce
> saut comme un assemblage casse -- c'est ce que Frederic voyait "en bas a droite" chez
> Hugo et Necro alors que les sprites concernes sont exacts contre la RAM. Le jeu, lui,
> les ancre toutes au meme point : l'element porte la position, le morceau son ecart.
> `planches.py` repose donc chaque image a son `(x0, y0)` dans un repere commun.
>
> **Corollaire pour la suite : ce qui parait mal assemble sur une planche ne l'est pas
> forcement.** La femme de `bg05` (sprites 207 a 211), dont le bandeau clair traverse le
> cote droit, a **quatre de ses cinq images exactes contre la RAM**. Ce bandeau est dans
> la donnee de la Dreamcast, pas dans notre assemblage.
>
> **Une fausse piste, ecartee** : "un sprite bien assemble pave son rectangle" ne vaut
> rien. 94 sprites ont des morceaux qui se recouvrent, mais `bg05` en compte 28 tout en
> etant exact contre la RAM. Le recouvrement est licite -- le jeu dessine dans l'ordre.
>
> **LA PALETTE D'UN SPRITE QUE PERSONNE NE MONTRE N'EST PAS CONNAISSABLE.** `planches.py`
> montre les 232 animations des quinze decors -- la version d'avant n'en montrait que 81,
> celles qu'un element de la liste d'affichage designait dans l'unique etat du decor. Pour
> les autres, la palette se deduit par la correspondance apprise (champ palette du morceau
> -> emplacement en RAM), univoque sur neuf decors sur treize. Quand meme ca manque, la
> planche rend le sprite en **GRIS FRANC** : la forme se valide, la couleur est annoncee
> inconnue. Deviner par ressemblance est l'impasse deja mesuree (la bonne palette sort
> 2311e sur 2715). Verifie sur `bg08` : la reference `reference-elena-vautour.png` montre
> un vautour brun et blanc la ou la palette deduite le rendait bleu.
>
> **Le remede aux deux manques -- palettes inconnues et sprites non verifiables -- est le
> meme : d'autres etats Flycast.** Chacun fige une image de plus par element, donc autant
> de palettes sures et de references d'assemblage en plus.

**Parallaxe** — huit plans de 16 octets à `0x8C84135C`, positions en 16.16 masquées à
`0x3FF`, donc **bouclage sur 1024 px**. Validation par image en `0x8C0FF84E` vers la table
`0x8C7EFCCC` que lit le dessin.

**États Flycast lisibles** — `outils/flycast.py`, `etat.py`, `recolte.py`. Les seize décors
d'étage sont relevés et archivés dans `releves/`.

### Côté 3SX : on sait ajouter un décor, et ça marche

Un **23e étage (index 22)** existe, est sélectionnable en versus après `RANDOM` sous le nom
`2ND IMPACT / WATERFALL GORGE`, se joue normalement — caméra, positions de départ, tout est
correct — et **Necro, dont il emprunte le fichier de textures, reste intact**.

Modifications dans `C:\Temp3sx` (tout compile, `-Werror`, code 0) :

- une vingtaine de tableaux étendus de `[22]` à `[23]`. **Attention, deux familles
  distinctes** : `bg_w.stage` choisit l'**entrée**, `bg_w.bg_index` choisit le **fond et son
  script**. Les deux ont été étendues, plus `ake_bg_off[20]→[23]` et `win_2000_tbl[18]→[23]`
  qui étaient déjà trop courts pour 22 étages.
- `stage/bg220.c` et `.h` — le script du nouvel étage : deux plans, aucun objet de décor.
- `ta_move_tbl[23]` avec `BG220` ; `bg_index_tbl[22] = {22,22,22}`.
- `spans[42] = { .start = 150, .length = 3 }` — l'étage 22 emprunte le bloc de chargement de
  l'**étage 10 (Yang)**, le seul dont les deux plans chargent 32 pages sur 32, et
  `bgtex_stage_gbix[22] = { 0xFFFFFFFF, 0xFFFFFFFF, 0 }`. 64 pages, aucun trou de masque.
  Une page que le masque ne donne pas n'est pas noire : le jeu y montre **ses propres
  pixels**. C'était ça, les bandes verticales aux extrémités.
- `sel_pl.c` — le sélecteur versus va de 0 à 22, en sautant 17 (vide) et 21 (bonus).
- `eff99.c` — `Letter_Data_99[5][23]`, les noms d'étage.
- `port/video/tex_remix.{c,h}` et `stage/bg.c` — **une clé par numéro de page** pour les
  étages au-delà des 22 d'origine :

      tex_remix/stage22/<liste>-<page>.tex

  C'est ce qui permet à l'étage 22 d'avoir ses propres pixels sans toucher celui dont il
  emprunte le fichier. `TexRemix_SetStage()` est appelé depuis `bg.c`.

**Pages de l'étage 22** : liste 132 = 28 pages (133 à 163), liste 196 = 22 pages (197 à 227).
`page = base_de_liste + i`, où `i` est l'indice de bit dans `bgtex_stage_gbix`. Certaines
manquent : l'atlas emprunté a des trous.

**Lanceurs** dans `C:\Temp3sx\build\application\bin\` :

| lanceur | rôle |
|---|---|
| **`Les 15 etages de 2nd Impact.cmd`** | **pose les quinze décors et lance le jeu** |
| `Etage 22 - test de placement (64 pages).cmd` | une couleur et un numéro par page |
| `Etage 22 - test uni (ou est le trou).cmd` | aplats et grille de 16 px, pour un défaut de rendu |
| `Etage 22 - releve des pages chargees.cmd` | dump neuf, dit ce que le jeu charge et ce qu'on couvre |
| `verifier-cartes.cmd` | rejoue la démonstration sur `bg_map_tbl` |
| `relever2.cmd` | relève les états Flycast (`releves2/`) — celui-ci est dans `dc-decors\` |
| `pools.cmd` | clé → asset `F_ETC` et contrôle des bornes — dans `dc-decors\` |
| `elements.cmd` | assemble et rend les éléments de décor — dans `dc-decors\` |
| **`tester.cmd`** | **rejoue toute la chaîne des sprites et rend un verdict** — voir `TESTER.md` |
| **`Les 15 etages de 2nd Impact AVEC SPRITES.cmd`** | **le jeu, décors et sprites** — dans `C:\Temp3sx\build\application\bin\` |

Le binaire qui fonctionne est celui de `build\application\bin\` ; après un `ninja`, copier
`build\3sx.exe` par-dessus. Compiler avec MSYS2/MinGW64 :
`PATH=/c/msys64/mingw64/bin:$PATH ninja` depuis `C:\Temp3sx\build`.

---

## Ce qui a échoué — et pourquoi

**L'image du décor ajouté n'est toujours pas bonne.** Quatre compositions successives,
quatre échecs, toujours la même cause : **on ne sait pas comment un atlas `.pvc` de 2nd
Impact se compose à l'écran.** Découper une bande de 1024×512 dans l'atlas en espérant que
ça tombe juste ne marche pas, et ne marchera pas.

Ce qui est mesuré et sûr côté 3SX, en revanche :

- un plan est une grille de **8 colonnes × 4 rangées** de pages de 128×128 ;
- **seules les rangées 2 et 3 sont visibles** — mesuré deux fois, sur le décor de Ken puis
  sur l'étage 22, par pages colorées et numérotées ;
- **rouge et bleu doivent être échangés** dans les `.tex` — mesuré, le bois chaud sortait
  bleu, corrigé par l'échange, validé à l'écran ;
- `bg_map_tbl` / `stageXXX_map[64]` est **décodé** — et ce n'était pas la clé. Voir
  `CARTES-BG.md`. Ce que ça a donné en revanche, lu dans le code de dessin :
  **page `i` d'un plan → `x = (i & 7) * 128`, `y = 512 + (i >> 3) * 128`**, dans un
  espace de 1024×1024 qui boucle. Composer un décor ajouté, c'est découper une image de
  1024×512 en 8×4 pages de 128×128 dans l'ordre de lecture.

Impasses déjà mesurées, ne pas y revenir :

1. Choisir une palette par lissage d'image : la bonne sort 2311e sur 2715.
2. Restreindre une palette de sprite à la « plage du décor » : elle donne les palettes du fond.
3. Les décors nettoyés de sfgalleries.net pour les couleurs : agrandis, inutilisables.
4. **Le dump de `tex_remix` est cumulatif** : une page déjà vue n'est plus réécrite, et les
   numéros de page sont réutilisés d'un décor à l'autre. Toujours repartir d'un dump neuf
   (`outils/dumpneuf.py --avant`) avant de conclure quoi que ce soit sur des empreintes.

---

## Ce qu'il faut faire maintenant

**Connaître les décors de 2nd Impact à 100 %.** C'est le verrou, et la condition d'une base
solide. On a les pixels et les palettes ; il manque la **composition** : quel morceau de
l'atlas va sur quel plan, à quelle place, avec quel défilement.

Trois pistes, par coût croissant :

**a) Le côté 3SX — ~~à faire en premier~~ FAIT, et clos.** `bg_map_tbl` ne place rien : il
classe, case de 32×32 par case de 32×32, ce qui est déjà placé — `0` rien, `1` opaque,
`2` troué. C'est le tri opaque / punch-through d'un moteur PowerVR, donnée morte dans ce
portage (`scr_bcm[]` est écrit et jamais relu). Et ce sont les données de *3rd Strike*,
pour ses propres étages : elles ne disent rien de 2nd Impact.
Ce que la piste a rapporté, et qui sert : **la règle de placement exacte, lue dans
`scr_trans()`** — voir `CARTES-BG.md` et `verifier-cartes.cmd`. Ne pas y revenir.

**b) Les états Flycast — engagée, et c'est la bonne.** `outils/etat2.py` lit maintenant la
**table des éléments de décor** (`0x8C72FCCC`, 16 octets : plan, index, x, y), les
**coefficients de parallaxe** (fiche d'objet `+16` / `+20`, en 16.16) et identifie le décor
**par les octets du conteneur restés en RAM**, exactement. Lancer `relever2.cmd`.
Voir la section « La composition, reprise le 27/08/2026 » de `FORMAT-PVC.md`.
**Attention : les étiquettes de `releves/` sont fausses** — celles de `releves2/` ne le sont
pas. Seize états, **les seize décors de 2nd Impact** — plus rien ne manque.
Les **coefficients de parallaxe sont confirmés** : `bg0f` est saisi deux fois, au neutre et
décalé, et le plan lointain bouge de 8 quand le proche bouge de 10 — ce que prédit 0,75.
Même résultat sur `bg0c`. Tableau complet dans `FORMAT-PVC.md`.
L'index d'un élément est **résolu** : il mène à un morceau de sprite prêt à poser —
`{u16 tuile, u16 ?, u16 x, u16 y, u16 (l-1)<<8|(h-1), u16 drapeaux<<8|code, u16 palette}`,
position absolue et taille explicite ; les drapeaux disent si `x` et `y` sont des centres.
Taille et `code` concordent **97,8 %** du temps sur les dix états. Ne reste que le **fond
de plan** : huit enregistrements par plan, et une texture liée ailleurs.

**c) Les scripts d'étage de 2I.** Table de quinze pointeurs à `0x8C6020AC`. Machines à états
écrites à la main : dernier recours — et le désassemblage a montré pourquoi. La composition
est dans une table **de RAM** (`0x8C72FCCC`), remplie au chargement : le code seul ne peut
pas la rendre. Ce que (c) a donné, en revanche, c'est de savoir lire cette table — donc (b).

**La composition est faite** — voir « Où se coupe une banque » dans `FORMAT-PVC.md` :
une banque à deux bandes se coupe à `y = 512`, le haut est le plan lointain, le bas le
plan proche, et chaque demi-banque se pose à l'identique sur les 32 pages d'un plan de
3SX. `outils/bande3sx.py` la découpe.

**Vue à l'écran le 27/08/2026 : elle tient.** Le décor sort d'un seul tenant, sans couture
et sans décalage. Les trous noirs qui restaient venaient du **décor choisi**, pas de la
découpe : `outils/couverture.py` mesure que la gorge `bg0f` laisse 42 % de noir dans la
zone jouée **même sous un masque plein**. Trois décors qui tiennent sont découpés et
prêts, chacun avec son lanceur : `bg06` 8,3 %, `bg0c` 11,2 %, `bg01` 13,0 %.

~~**Ensuite seulement**, refaire la composition de l'étage 22 et l'étendre aux autres décors.~~
**Fait.** Quinze étages, quinze décors, plus une bande aux extrémités.

---

## FAIT : les sprites de décor sont assemblés, colorés et placés (28/08/2026)

**Le verrou est levé : le champ `tuile` indexe le pool de tuiles d'un asset `F_ETCnn`,
et c'est la clé — le champ `+12` de l'enregistrement — qui dit lequel.** Percé en
désassemblant, vérifié sur les dix-sept états, puis mis en images.

### La chaîne, lue dans `SF3_2ND.BIN`

La boucle de dessin `0x8C0F693C` appelle `0x8C0F719E` avec trois arguments, pour chaque
tuile d'un morceau : la **palette**, la **tuile** (incrémentée d'une tuile à l'autre) et
la **clé** (`enr+12`). `0x8C0F719E` n'est qu'un cache — table de hachage de 32768 entrées
en `0x8C6E6918`, fiches de 16 octets en `0x8C6F6918` — dont l'identité tient sur 32 bits :

    (palette << 22) | ((clé & 127) << 15) | tuile

**La tuile n'a donc de sens que dans le contexte d'une clé.** En cas d'absence, le triplet
est empilé sur 6 octets dans la file `0x8C704E54`, que `0x8C0F6D30` vide ; le chargement se
fait en `0x8C0F6DC6` :

    bloc  = tuile >> 4          (>> 3 pour la seule clé 0x0160)
    rang  = tuile & 15
    fiche = 0x8C602384 + (clé & 0xFF) * 24        <- la table d'installation de fetc.py
    fn = fiche[+8] ; source = fiche[+12] ; fn(bloc, tampon, source)   -> 4096 octets
    la tuile 16x16 en 8 bits = tampon[rang * 256 : rang * 256 + 256]

Le dégonfleur `0x8C0F6548` lit `source` comme `{u32 nombre, u32 offsets[nombre]}`, offsets
relatifs à `source`, et écrit ses 4096 octets **à rebours** : c'est mot pour mot la
section 3 d'un `F_ETCnn`, et `blocs[i]` de `fetc.lire()` est exactement ce que le jeu
dégonfle. Le cache de blocs `0x8C0F648E` garde huit blocs de 4096 octets en `0x8C6DE900`.

**La table `0x8C602384` est la table d'installation des assets** déjà décrite en tête de
`fetc.py` : `+4` les données, `+8` la fonction, `+12` la section graphique, `+16` les
animations, `+20` **la clé elle-même** — qui se relit, entrée par entrée.

### La vérification

`pools.py` (lanceur `pools.cmd`) ne raconte pas ça, il le mesure. Pour chaque couple
(état, clé) il lit le nombre de blocs du pool et vérifie que **toutes** les tuiles
demandées y tombent : `187 sur 187`. Et il nomme l'asset par ses octets, pas par
déduction :

| clé | asset | | clé | asset |
|---|---|---|---|---|
| `0x0129` | `2i-b0c-F_ETC24` (ken) | | `0x0130` | `2i-b08-F_ETC31` |
| `0x012a` | `2i-b02-F_ETC25` (ryu) | | `0x0131` | `2i-b04-F_ETC32` (dudley) |
| `0x012b` | `2i-b03-F_ETC26` (yun) | | `0x0132` | `2i-b0a-F_ETC33` (oro) |
| `0x012c` | `2i-b0b-F_ETC27` (yang) | | `0x0133` | `2i-b01-F_ETC34` (alex) |
| `0x012d` | `2i-b05-F_ETC28` (necro) | | `0x0134` | `2i-b0d-F_ETC35` (sean) |
| `0x012e` | `2i-b06-F_ETC29` (hugo) | | `0x013a` | `2i-b00-F_ETC41` (gill) |
| `0x012f` | `2i-b08-F_ETC30` (elena) | | `0x0158` | `2i-b0e-F_ETC94` (urien) |

Une fiche vide veut dire que l'asset n'est plus résident : le tableau des morceaux n'est
pas effacé d'un étage à l'autre, et ces clés-là sont des restes. **La fiche pleine désigne
l'asset de l'étage en cours** — c'est ce qui confirme chaque ligne du tableau.

### La palette : ce qui manquait vraiment

Deux bits de l'octet `+9` de l'élément de la liste d'affichage, lus en `0x8C0F6A44` et
`0x8C0F6A64` :

- **bit 5 armé** : l'emplacement de palette vient du mot `+8` de **l'élément**, un seul
  pour tous ses morceaux ; **bit 5 éteint** : du champ `+2` du **morceau**.
- `(octet & 6) != 0` : emplacement `& 0x1FF`, palette de 128 octets — 64 couleurs ;
  sinon `| 0x200` et palette de 512 octets. Adresse `0x8C7AFCCC + emplacement * 128`
  (ou `+ (emplacement - 512) * 512` au-delà de `0x200`). Index 0 transparent.

C'est **ce bit 5** qui manquait. Pris sur le morceau pour tout le monde, les éléments à
octet `0x62` — la grande majorité — tombaient sur les emplacements 1 à 15, c'est-à-dire le
bloc des combattants, **identique dans les dix-sept états**. D'où des cascades rouges et
des temples orange. Corrigé, treize décors sortent avec leurs vraies couleurs.

Corollaire : `bases.py` n'est plus nécessaire pour colorier depuis un état — la palette se
lit en RAM. Ses bases restent déduites, et deux d'entre elles (`bg02` 1625, `bg03` 1631)
désignent le **bloc partagé** et non le bloc propre au décor.

### Le placement dans le plan

Le mot `+8` d'un morceau donne `hauteur = ((mot >> 8) & 127) + 1` et
`largeur = (mot & 127) + 1` — **l'inverse de ce que nommait `etat2.py`**, et c'est le
calcul du dessin qui le dit : le bit `0x0100` retire la moitié de ce champ à *y*, le bit
`0x0200` l'autre à *x*. À l'écran, `0x8C0F6A90` et `0x8C0F6AA6` donnent

    x = defil_x[plan] + elem.x + m.x - (largeur / 2 si 0x0200)
    y = 109 - defil_y[plan] - elem.y - m.y - hauteur + (hauteur / 2 si 0x0100)

L'axe y est **inversé**, origine 109. Le fond du même plan défile du même `defil`, donc
**dans le plan le défilement disparaît des deux côtés** :

    x = (elem.x + m.x - largeur/2) & 0x3FF
    y = (G - elem.y - m.y - hauteur + hauteur/2) & 0x3FF

**`109` n'est pas `G`, et c'est ce qui a cloché au premier essai dans le jeu.** `elem.y`
et `m.y` sont des **hauteurs au-dessus du sol**, et `109` est la ligne du sol **à
l'écran**. Dans la banque, la ligne du sol `G` est ailleurs : c'est la dernière ligne non
vide de la moitié basse, et elle se mesure décor par décor (1023 pour treize d'entre eux,
972 pour `bg05`, 1007 pour `bg0d`). Avec 109, tout le groupe se retrouvait centré sur
`y = 0`, à cheval sur le bouclage : chez Alex, deux bâtiments se posaient au sol du toit et
le château d'eau flottait dans le ciel ; chez Ryu, les baigneurs sortaient de la bande
visible et **on ne voyait aucun sprite**. Corrigé, `cuire.py` mesure `G` et le passe à
`elements.py`, et **aucun pixel de sprite ne tombe plus dans la moitié lointaine** sur les
treize décors — c'est l'épreuve 4 de `verifier.py`.

**Vérifié par superposition**, sans lancer le jeu : sur `bg03`, les étals, la charrette et
l'enseigne 九記 se posent sur la chaussée de `2i-bg03-banque0.png`, à la bonne échelle et
devant les bonnes boutiques ; sur `bg0b` les rochers et les figures sont sur le sol rouge
du temple, sur `bg06` la foule et les cordages sur le pont du navire. Les deux autres
conventions essayées les envoient dans le ciel.

`elements.py` (lanceur `elements.cmd`) sort, pour chaque état :
`rendus/elements/<décor>-eNNN.png` (chaque élément seul) et
`rendus/elements/<décor>-planN.png` (le plan de 1024x1024, prêt à superposer à la banque).
Planche de tous les décors : `rendus/elements/planche-tous.png`.

**Ce qu'on y voit** : les baigneurs de Ryu et ses cascades, l'étal 九記 et la foule de Yun,
les piétons et le feu de circulation de Dudley, le public et les cordages de Hugo, le
Bouddha, l'aquarium, le bambou et la grue de Yang, les palmiers de Sean, l'acacia et le feu
d'Elena, les chauves-souris et le perroquet d'Oro, les obélisques de Gill, le pilier
d'Urien. Treize décors sur quinze.

**Deux décors n'ont aucun asset `F_ETC` à eux** : `bg07` (Ibuki) et `bg0f` (la gorge).
Aucun élément de leur liste d'affichage ne renvoie à un pool nommé, et `sprites/` n'en
contient ni pour `b07` ni pour `b0f`. La cascade animée de la gorge est donc faite
autrement — tuiles animées dans le `.pvc`, ou cycle de palette : à établir.

---

## Ce qui reste, par ordre de valeur

~~**1. Cuire les sprites dans le plan, puis découper.**~~ **Fait le 28/08/2026.**
`outils/cuire.py` pose les plans de sprites sur la banque `.pvc` *avant* la coupe, et
`bande3sx.decouper()` prend une `surcouche`. **Il n'y avait rien à arbitrer** : les plans
de sprites sont dans le même repère de 1024×1024 que la banque, donc c'est le `y` d'un
sprite qui décide de quel côté de la coupe à `y = 512` il tombe — exactement comme pour
les pixels du fond. Aucun recadrage, aucune mise à l'échelle.

Les quinze étages sortent dans `etages2i-sprites/stageNN`, à côté de `etages2i/` qui reste
intact. **Les limites de terrain sont inchangées** après cuisson, donc aucune
recompilation : le lanceur ne copie que des `.tex`.

    C:\Temp3sx\build\application\bin\Les 15 etages de 2nd Impact AVEC SPRITES.cmd

Treize étages reçoivent des sprites ; `bg07` et `bg0f` n'en ont pas. Vérifié en relisant
les `.tex` écrits : l'étal 九記 est sur la chaussée de Yun, le jardin de rocaille et la
grue sur le sol du temple de Yang, la foule et les cordages sur le pont du navire de Hugo.

### Ce qui reste imparfait, constaté dans le jeu

**Un sprite cuit ne peut pas s'animer.** La ventilation de toit d'Alex — la boule
métallique — est un sprite (`bg01`, élément 5, plan 2, 48×48), pas un morceau du `.pvc` :
cuite dans le plan, elle est figée sur une image. C'est le prix de la voie courte, et
aucun réglage ne le lève.

**Mais l'autre voie est ouverte, et c'est mesuré — 28/08/2026.** 3SX sait animer un objet
de décor dans un étage ajouté. Voir « L'animation d'un objet de décor » ci-dessous.

**La correspondance plan d'affichage → moitié de la banque n'est pas mesurée.** Le jeu a
jusqu'à huit plans, la coupe n'en donne que deux, et **l'indice de plan n'ordonne pas la
profondeur de la même façon d'un décor à l'autre** : le pilier d'Urien est sur le plan 3
et il est au premier plan, les immeubles d'Alex sont sur le plan 3 et ils sont au fond.
`cuire.PLANS_LOINTAINS` est donc une **table remplie à l'œil**, pas une règle :

| décor | plan envoyé au lointain | pourquoi |
|---|---|---|
| `bg01` | 3 | les immeubles de la ville sont derrière le toit — constaté dans le jeu, corrigé, vérifié : ils s'alignent maintenant sur les autres gratte-ciel de la bande lointaine |

`bg03` plan 1 (l'intérieur sombre de la boutique) a été essayé en lointain : il se retrouve
en plein ciel, là où la bande lointaine n'a plus d'art. Laissé au sol, où il n'est qu'un
rectangle sombre derrière les étals.

**La mesure qui manque**, et qui remplacerait la table : la correspondance entre l'indice
de plan de la liste d'affichage et l'**objet de fond** (`releves2`, `coef_x` : 0,75 pour le
lointain, 1,0 pour le proche). Les deux existent dans l'état ; le lien entre eux n'est pas
localisé — il n'est pas dans les 32 premiers octets de la fiche d'objet de 144.

Le levier `python cuire.py --plans 2` existe mais il est trop brutal : il supprimerait le
pilier d'Urien et les obélisques de Gill, qui sont sur le plan 3 et au bon endroit.

**2. `bg0a` oro**, seul décor à garder 19 % de noir dans la zone vue, et ses trous sont au
milieu, pas aux bords. Et **`bg08`**, écarté du casting : sa bande jouée n'est pas à
l'endroit habituel (`0..416` et `496..832` quand tous les autres finissent au bas du plan).

**3. New Generation** — vingt-trois décors de plus dans `pvc-ng/`, même chaîne d'outils.
Aucun état Flycast de ce côté-là, donc pas de coefficients de parallaxe ; mais la règle de
coupe et le placement ne dépendent pas d'eux.

---

## FAIT : l'animation d'un objet de décor marche dans un étage ajouté (28/08/2026)

**Mesuré, pas supposé.** Un objet de décor animé naît, avance ses images et se dessine
dans l'étage 23. Le journal, une ligne par changement d'image :

    change: cg / trame / ecart  34526      1      1
    change: cg / trame / ecart  34452     50     49
    change: cg / trame / ecart  34454     51      1
    change: cg / trame / ecart  34456     52      1
    ...                          34508     78      1

Vingt-neuf images distinctes, **une par trame** après un maintien initial de 50. Le
mécanisme est acquis.

### La mécanique, telle qu'elle est dans le port

`eff05.c` — « Stage background objects ». Un objet tient en huit `s16` :

    { dead_f, plan, palette, x, y, z, index d'animation, sync }

- `scr_obj_num[bg_index]` : combien d'objets pour cet étage ;
- `scr_obj_data[bg_index]` : leur table ;
- `char_add[bg_index]` : la table d'animation où l'index va chercher son script.

### Les trois maillons qui manquaient à un étage ajouté

1. **`effect_05_init()` n'était pas appelé.** `bg220.c` ne le faisait pas ; tous les
   étages d'origine qui ont du décor animé l'appellent depuis leur init.
2. **Le groupe de graphiques n'était pas chargé.** Il l'est normalement par la liste de
   chargement de l'étage ; un étage ajouté emprunte celle d'un autre et ne l'a donc pas.
   `mtrans.c` ne s'en remet pas — il journalise « les données de trans ne sont pas
   valides » et **boucle à l'infini**. C'était ça, le « plantage au chargement ».
   `load_any_texture_patnum(cg_number, 2, 0)` avant le dessin le règle, et ne coûte rien
   si le groupe est déjà là.
3. **`char_move()` n'était pas appelé.** `eff05` et `eff06` ne l'appellent jamais : leurs
   objets sont **fixes par conception** — le mobilier, pas la vie. C'est `eff07` qui anime
   le décor de l'étage 1, et lui l'appelle à chaque trame.

### Ce qui a coûté trois parties pour rien

`cg_ctr` est un **compte à rebours de maintien**, pas un numéro d'image. L'avoir lu comme
une preuve que les images défilaient a fait conclure trop vite. Puis la fenêtre de trace
faisait 40 trames alors que le maintien de la première image en fait **50** : elle
s'arrêtait dix trames avant le premier changement, deux fois de suite.

**Ne pas journaliser un compteur : journaliser un changement.** Une ligne par changement,
avec la trame et l'écart, répond en une partie.

### Comment un objet de décor obtient ses pixels — percé le 28/08/2026

Tout est lu dans le code, et il n'y a plus d'inconnue de principe.

**Les groupes.** `texgrpdat[100]` (dans `texgroup_data.c`) donne, pour chacun des 85
groupes définis, son premier motif et son fichier. Chaque étage de 3rd Strike a le sien :
`bg00_A.bin`, `bg01.bin`, `bg02_A.bin`… `obj_group_table[cg]` dit à quel groupe appartient
un numéro de graphique.

**Un motif** est une suite de morceaux de 16×16, posés par déplacements relatifs
(`x = 0, y = -16` monte d'une case ; `x = -16, y = 112` change de colonne), lue dans la
table de trans du groupe. Relevé en jeu sur l'animation d'essai : ~27 morceaux par image,
étendue 64×128, et **un morceau « vide » qui revient partout** — le chip 34 — entre les
morceaux qui portent le dessin. **D'une image à l'autre, la grille ne change pas : seuls
changent les numéros de chip.** C'est exactement ça, l'animation.

**Le chip → le pixel**, dans `seqsStoreChip` (`mtrans.c:1690`) :

    u    = (code & 0x0F) * 16          colonne du chip dans la page
    v    =  code & 0xF0                ligne du chip dans la page
    page = gix + (code >> 8)           uv normalisés sur 256

Donc **une page de groupe fait 256×256, découpée en 16×16 chips de 16×16**.

**Et surtout — ces pages ne viennent PAS de l'archive.** Elles sont remplies à l'exécution,
morceau par morceau, dans `mtrans.c` vers la ligne 560 :

    size = (wh * wh) << 6;                               un chip 16×16 = 256 octets
    lz_ext_p6_fx(&((u8*)texptr)[1], mt->mltbuf, size);   décompresse dans mltbuf
    njReLoadTexturePartNumG(page, mltbuf, chip, size);   téléverse

C'est pour ça que les pages d'objet **n'apparaissent jamais dans le dump de `tex_remix`** :
elles ne passent pas par `ppgSetupTexChunk_3rd`. `tex_remix` ne peut donc rien pour elles,
et c'est la piste qu'il ne faut pas suivre.

`gix` vaut `mts_base[7].gix` = **80** pour le cache d'objets de décor, et la taille de ce
cache est `mts_OB_page[bg_w.stage]` — encore une table indexée par l'étage, déjà étendue à
37 entrées, `{1, 1}` pour les nôtres.

### Le point d'injection, et il tient en quelques lignes

**Un chip de 16×16 est 256 octets d'index sur 8 bits** — exactement le format de nos tuiles
`F_ETC` et `.pvc`. Il suffit donc, juste après `lz_ext_p6_fx`, de recopier **nos** 256
octets dans `mt->mltbuf` quand l'étage est un des nôtres et que le couple (groupe, chip)
est un de ceux qu'on veut remplacer. Ni format d'archive, ni nouveau groupe, ni `tex_remix`.

Ce qu'il reste à écrire, et c'est un vrai morceau, pas une ligne :

1. **Un exportateur** — nos tuiles rangées par (étage, groupe, chip), depuis
   `2i-bXX-F_ETCnn.bin` via `assemblage.py`, qui sait déjà poser un sprite en 16×16.
2. **Un chargeur** dans le port, appelé au chargement de l'étage.
3. **La substitution** dans `mtrans.c`, sous garde `bg_w.stage >= 22`.
4. **La palette** : le chip est dessiné avec `palo`, la palette de l'objet. Nos index
   doivent tomber sur une palette chargée — le champ palette de la fiche d'objet, à régler.
5. **Le choix du motif donneur** : sa grille décide de la forme. Pour la ventilation, 48×48
   = 3×3 chips, il faut un motif dont la grille en contienne autant.

**La ventilation est prête côté art** : sprites 2, 3 et 4 de `2i-b01-F_ETC34`, 48×48, la
boule métallique dans trois positions, rendues et vérifiées hors du jeu
(`rendus/elements/b01-sprites.png`).

**L'essai a été retiré** ; ce qui reste dans le code, c'est la **plomberie**, et elle ne
coûte rien tant que `scr_obj_num` vaut zéro pour un étage :

- `bg220.c` appelle `effect_05_init()` ;
- `eff05.c` appelle `char_move()` puis `load_any_texture_patnum()` — **dans cet ordre** —
  pour `bg_index >= 22` seulement. Mettre le chargement après le dessin regèle le jeu à
  la première trame : c'est la faute qui a produit le dernier gel ;
- `stg2200_data_tbl` reste comme fiche modèle, inactive.

Pour rallumer un objet : mettre `1` dans `scr_obj_num` à l'indice voulu. Rien d'autre.

**Vu à l'écran le 28/08/2026** : l'objet d'essai s'anime et se déplace dans l'étage 23,
par-dessus le décor. Son art était celui de 3rd Strike et sa palette n'était pas chargée,
donc un aplat gris — mais il bouge, et c'est tout ce que l'essai devait établir.

**Ce qui ne s'animera jamais par cette voie** : la ventilation de toit d'Alex telle qu'elle
est aujourd'hui. Elle est *peinte* dans la texture du plan par `cuire.py`. Un pixel de fond
ne s'anime pas ; il faut en refaire un objet.

---

## Les sprites de décor DESSINÉS PAR LE JEU (28/08/2026, soir)

La voie « cuisson » donne des sprites **immobiles** : un pixel peint dans la texture du
plan ne s'anime pas. Cette section est l'autre voie — l'objet de décor, dessiné par
`eff05.c`, qui peut s'animer.

### Ce qui marche, mesuré en jeu

1. **Un objet de décor naît, avance ses images et se dessine dans un étage ajouté.**
   Trois maillons manquaient à `bg220.c` / `eff05.c`, tous ajoutés :
   - `effect_05_init()` n'était pas appelé depuis le script d'étage ;
   - le groupe de graphiques n'était pas chargé — `mtrans.c` **boucle à l'infini** sinon
     (`load_any_texture_patnum(cg, 2, 0)`, **avant** le dessin, jamais après) ;
   - `char_move()` n'était pas appelé : `eff05` et `eff06` ne l'appellent **jamais**,
     leurs objets sont fixes par conception. C'est `eff07` qui anime.
2. **Nos pixels remplacent les siens.** Un chip est 16×16 en index 8 bits = **256 octets**,
   le format exact de nos tuiles. `mtrans.c` les décomprime dans `mt->mltbuf` puis les
   téléverse ; on y recopie les nôtres juste avant. Ces pages ne viennent **pas** de
   l'archive : `tex_remix` ne les voit jamais, c'est une fausse piste.
3. **La liste de morceaux est la nôtre.** `DecorObjets_Motif()` récrit l'entrée de la table
   de trans — elle est en RAM et modifiable, le moteur y écrit lui-même dans
   `search_trsptr`. L'objet ne dessine plus que nos neuf morceaux : plus rien du donneur
   ne peut transparaître. **C'est ce qui a supprimé le morceau de l'étage de Ken qui
   apparaissait chez Alex** — un élément que ce montage avait introduit, pas un défaut
   préexistant.
4. **Les octets d'un chip sont ENTRELACÉS**, pas linéaires. `ppgRenewDotDataSeqs` lit la
   source à travers `dctex_linear` : `dest(i,j) = src[T[j + i*32]]`. La table est
   construite par `ppgMakeConvTableTexDC` ; `objets.py` la reproduit et vérifie que c'est
   une permutation exacte de 0..255. Sans ça, la tuile sort en rayures.
5. **Écrire dans `ColorRAM` ne suffit pas** : il faut envoyer au matériel. **Pas** par
   `palUpdateGhostCP3` — la palette fantôme n'a qu'une poignée d'emplacements et
   l'appeler avec 300 sort du tableau (plantage). Passer par
   `ppgGetUsingPaletteHandle(NULL, n)`, qui vérifie toutes les bornes, puis
   `flLockPalette` / `SDL_memcpy` / `flUnlockPalette`.

### Le code, et où il est

- `src/port/video/decor_objets.{c,h}` — le module ; garde sur **l'objet** (le `WORK`
  marqué à sa naissance), jamais sur l'étage : la fonction de dessin est partagée avec
  les combattants, et garder sur `bg_w.stage` les couvre de blocs blancs.
- `src/port/video/decor_objets_data.c` — **généré** par `dc-decors/outils/objets.py`.
- `mtrans.c` — deux crochets seulement, dans `mlt_obj_trans_ext` et
  `mlt_obj_trans_cp3_ext`. **Attention : chacune de ces fonctions a DEUX chemins** — celui
  qui découvre un motif et celui qui le retrouve en cache. Les deux doivent employer la
  **même clé**, sinon `get_mltbuf16_ext` ne trouve pas et **boucle à l'infini**.
- `eff05.c` — `scr_obj_num[23] = 1`, `stg2200_data_tbl`, et les appels par image.

### Les cadences — `cadences.cmd` — RÉÉCRIT LE 29/08/2026

~~**La durée d'une image est portée par la répétition** : un même enregistrement répété *n*
fois tient *n* trames.~~ **Faux, et mesuré comme tel.** ~~Trois assets ont un flux
dégénéré — `b01` alex, `b0c` ken, `b0e` urien — et leur cadence est dans le script
d'étage.~~ **Faux aussi.** Voir `DONNEES.md`, section 3.

Ce qui reste vrai du paragraphe d'origine : les trois autres champs du format sont **nuls
dans les seize assets** — 0 sur 19 872, vérifié. La durée n'est donc nulle part dans le
fichier, pour personne. Et les images d'un même objet partagent bien leur **ancre**.

**La cadence est dans une table de scripts du binaire, en clair**, atteinte en trois
étages :

    0x8C5F9B38 + n*4     table maitresse, un pointeur par aire d'etage
    table -> [pointeurs] un par script
    script -> enregistrements de HUIT octets :
        octet 0 : commande -- 0x00 afficher, 0x01 fin, 0x0C debut de boucle, 0x0D fin
        octet 1 : la duree en trames
        u16 +6  : l'index global, celui de l'espace partage des F_ETCnn

**419 scripts, 3 614 images.** La distribution des durées est celle d'une table de trames :
94 % valent 16 trames ou moins, pics à 4, 6 et 8, maximum 250. Tout sprite cité par un
script est dans le flux de son asset — 100 % sur les quinze. L'inverse est faux : le flux
porte aussi du mobilier que rien n'anime.

**La ventilation d'Alex**, table `0x8C1226B8` : sprites 2, 3 et 4, ancre `(-48, -48)`,
**quatre trames chacun** — un tour en douze trames (`0x8C122704`). Le jeu garde une
variante rapide à une trame par image (`0x8C12272C`) ; ce qui choisit entre les deux n'est
pas établi.

### La position — elle était sous la main depuis le début

Dans la **liste d'affichage en RAM**, que `etat2.py` lit et que `releves2/` archive.
Chaque élément porte son plan et son `(x, y)` :

    bg01 element 5   plan 2  x=480 y=48    la ventilation
    bg02 element 7   plan 2  x=208 y=96    les baigneurs de Ryu
    bg03 element 6   plan 2  x=463 y=304   l'etal de Yun

### Le gel de l'etage 23 : trouve en lisant, corrige (28/08/2026, nuit)

**Trois defauts, tous lus dans le code, aucune partie lancee pour les trouver.** Le
correctif compile (`-Werror`, code 0) et les epreuves hors du jeu passent ; **il n'est pas
encore verifie a l'ecran**.

**1. LE GEL. L'identite d'un motif dans le cache est le numero de graphique du donneur, et
rien d'autre.** `mlt_obj_trans_cp3_ext` cherche par
`check_patcash_ex_trans(mt->cpat, cc.code)` ou `cc.code = (0 << 16) | wk->cg_number`. Le
premier chemin televerse les morceaux et note leurs emplacements dans `cp->map` ; le
second ne fait que les **chercher**, parmi ces emplacements-la seulement
(`makeup_tpu_free`), et `get_mltbuf16_ext` **boucle a l'infini** s'il ne trouve pas.

Or nos cles de morceau portent NOTRE image, qui avance toutes les quatre trames, alors que
le `cg_number` du donneur tient **cinquante trames** sur sa premiere image. A la cinquieme
trame : meme numero, donc chemin du cache, mais image 1 -- des cles que le premier chemin
n'a jamais enregistrees. **Gel, cinq trames apres la naissance de l'objet, c'est-a-dire a
l'entree de l'etage.**

Correctif : `DecorObjets_Identite()` remplace l'identite pour notre objet seul, par
`0x00D30000 | image`. Le numero du donneur en **sort** : notre motif est la meme grille de
3x3 pour tous ses numeros, et vingt-neuf numeros par trois images feraient 87 motifs pour
les **64** emplacements de `PatternCollection` -- `get_free_patcash_index` a lui aussi son
`while (1) {}`. Avec l'image seule : **trois motifs, vingt-sept morceaux sur 256**.

**2. LA PALETTE N'ETAIT PAS A L'EMPLACEMENT QU'ON CROYAIT.** Le chemin cp3 calcule

    palt = (trsptr->attr & 0x1FF) + palo

Les neuf bits bas de l'attribut du **morceau** s'**ajoutent** a `colcd`. Nos morceaux
portaient `0x0006`, herite du donneur : la palette lue etait la **306** quand nos couleurs
sont posees en 300. `ATTR_MORCEAU` est passe a zero -- le reste de l'attribut n'est lu que
par le masque `0xC000`, les retournements, qu'on ne veut pas non plus.

**3. ROUGE ET BLEU ETAIENT ECHANGES.** `ColorRAM` est en **ABGR1555**, pas en ARGB :
`palCreateGhost` met `palFormRam.rs = 0` et `palFormRam.bs = 10`, contre `rs = 10` et
`bs = 0` pour `palFormSrc`. `col_edit.c` le nomme au-dessus de `swatch_color` :
« red sits in the low bits and blue in the high ones [...] the same mistake that once
turned every fighter's skin blue, **and it passes every numeric check** ». C'est la meme
correction que celle deja faite sur les `.tex` du fond. L'echange se fait desormais dans
`DecorObjets_InstallerPalette` ; `objets.py` continue de sortir l'ARGB de la Dreamcast tel
quel, et son commentaire, qui affirmait le contraire, est corrige. **La preuve qu'il
invoquait etait un gris** -- invariant par l'echange, donc muet.

**L'ENVOI AU MATERIEL EST REVENU, et le motif qui l'avait fait retirer etait faux.**
`palUpdateGhostCP3(300, 1)` ne depasse pas : la palette fantome ne compte pas « une
poignee » d'emplacements mais **512**. `ppgSetupPalChunkDir` fait
`pch->total = SDL_Swap16BE(ppl->palettes)` -- un boutisme inverse -- et le `2` de
`palCreateGhost` devient `0x0200`. Le jeu lui-meme met a jour cette zone : `color_file[]`
porte des entrees `.data = 0x12C`, c'est-a-dire **300 exactement**. Contrairement a
`ppgGetUsingPaletteHandle`, cette fonction ne lit pas `ppg_w.cur` : elle prend la poignee
dans `col3rd_w.palCP3`, donc elle ne depend pas de la passe de dessin.

**Une garde de capacite en plus**, qui n'a rien coute : `DecorObjets_Motif` verifiait
« deja fait ? » en relisant la valeur 9 dans la table de trans, et n'a jamais verifie que
l'entree du donneur pouvait **contenir** neuf morceaux. Les entrees se suivent : une entree
plus courte aurait deborde sur la suivante, et une table de trans corrompue ne se voit
qu'ailleurs et plus tard. Marqueur propre, et refus d'ecrire si l'entree compte moins de
neuf morceaux.

**Les epreuves hors du jeu** (`verif`, rejouee a la main) : les neuf cases de la grille
existent pour les trois images, 27 cles distinctes plus une pour les vides sur 256, trois
identites sur 64, la palette a 64 entrees dont la premiere transparente, et l'echange
rouge/bleu est une involution exacte sur les 64.

**Le lanceur** : `LA VENTILATION - etage 23 Alex (gel corrige).cmd`. Il installe l'etage 23
**sans sprites cuits** (`etages2i/`, pas `etages2i-sprites/`) pour cet essai : tout ce qui
bouge sur le toit d'Alex est alors NOTRE objet, et rien d'autre. Il porte la prediction
ecrite avant la partie, et relit le journal apres.

### Ce qui manquait — presque tout est tombé le 29/08/2026

**Les quatre questions sont dans `DONNEES.md`**, avec le programme qui les rejoue
(`donnees.cmd`) et la sortie brute (`DONNEES.txt`).

- ~~**Le plan.**~~ **Résolu.** Les décors de 2I emploient **cinq** plans (0 à 4), et le
  lien plan → objet de parallaxe est `defil[plan k] == (−objet[k−1].x) & 0x3FF`, vérifié
  **35 fois sur 36**. La ventilation est sur le plan 2, coefficient **1,00**, le plan
  proche. **Un défaut** en tombe : elle porte `my_family = 1`, qui dans `BG220` est le plan
  **fixe** (`speed_x` y vaut 0) — elle resterait collée à l'écran pendant que le toit
  défile. Ce devrait être `my_family = 2`, le plan qui suit la caméra.
  **Et une différence, qui n'est pas un défaut** : nos deux plans donnent 0,00 et 1,00,
  quand les décors de 2I veulent 0,25–0,94 et 1,00. `bg2201_init00` ne pose pas `speed_x`,
  mais `bg0201_init00` et `bg0501_init00` des étages d'origine ne le posent pas non plus —
  `bgw[0]` est le plan fixe par conception, et la parallaxe de 3rd Strike vit sur `bgw[2]`,
  un troisième plan que nos étages n'ont pas. Poser `speed_x`/`speed_y` dans
  `bg2201_init00` est le levier ; les quinze couples mesurés sont dans `DONNEES.md`.
- ~~**La cadence des trois dégénérés.**~~ **Résolue**, et ils n'étaient pas dégénérés.
  Ventilation : **4 trames par image**, trois images, un tour en douze trames. Voir
  ci-dessus.
- ~~**Les retournements** : bits `0x100`/`0x200` du morceau.~~ **Ce ne sont pas des
  retournements**, ce sont les **centrages** — `0x0100` pour x, `0x0200` pour y. Le
  retournement, lui, est `element[+9] ^ (morceau[+2] >> 8)` : bit `0x08` vertical,
  bit `0x10` horizontal. Sur les 3 458 morceaux dessinés, **le vertical n'est jamais
  employé** et l'horizontal l'est à 13 %.
- ~~**L'échelle** : deux champs de 7 bits, unité non établie.~~ **Il n'y a pas de champ
  d'échelle.** Les deux champs de 7 bits sont la taille **en pixels à l'écran** ; la
  taille de la texture vient des quartets bas de `morceau[+10]`. L'échelle est le
  **rapport** des deux : 98,67 % à ×1, le reste isotrope de ×1,672 à ×2.
- **Le lien objet ↔ animation** : plus une heuristique. Un script porte ses images, et
  toutes partagent leur ancre.
- **La palette par objet** : la règle est complète (voir `DONNEES.md`, section 2 — le
  **bit 6** de l'octet `+9` manquait ici). L'emplacement de la ventilation est **93**. Un
  étage de 2I demande entre 8 et 22 emplacements ; le nôtre n'en emprunte qu'un (300),
  donc il ne peut pas porter plus d'un objet coloré.

---

## Les outils — dans `dc-decors\outils\`

| fichier | rôle |
|---|---|
| `sh4.py` | désassemblage SH-4, base 0x8C010000, résolution des pools |
| `cdi.py`, `getfile.py`, `decoupe.py`, `secteurs.py` | le disque et les conteneurs |
| `pvc.py`, `rendupvc.py`, `tout.py` | le décodeur `.pvc` et les rendus |
| `fetc.py`, `degonfle.py`, `sprites.py` | les assets `F_ETCnn` |
| `assemblage.py`, `bases.py`, `planche.py`, `toutsprites.py` | les sprites assemblés |
| `palettes.py`, `appariement.py`, `balayage.py`, `depuiscapture.py`, `choixpal.py` | les palettes |
| `flycast.py`, `etat.py`, `recolte.py` | les états sauvegardés Flycast |
| `dumpneuf.py`, `dumpdiff.py` | le dump de textures de 3SX |
| `etendre.py` | étend un tableau C indexé par étage, un seul à la fois |
| **`bandes.py`** | mesure les bandes de contenu d'un atlas — où se coupe une banque |
| **`bande3sx.py`** | **découpe un décor en pages `.tex` pour un plan de 3SX**, et calcule ses limites de terrain |
| **`couverture.py`** | quelle part de la zone jouée resterait noire, décor par décor, sous un masque donné |
| **`ajouter_etages.py`** | **étend les vingt-six tables indexées par l'étage**, et se relit |
| **`testpages.py`** | pages de test : une couleur et un numéro par page, pour voir où chacune tombe |
| **`pages22.py`** | ce que le jeu a vraiment chargé, comparé aux `.tex` posés |
| **`etat2.py`** | relevé d'un état Flycast : décor identifié **par les octets du conteneur**, coefficients de parallaxe, table des éléments |
| **`pools.py`** | **ce que le champ `tuile` indexe** : clé → asset `F_ETC`, et la vérification que toutes les tuiles tombent dans leur pool |
| **`elements.py`** | **assemble les éléments de décor d'un état** : tuiles, couleurs lues en RAM, position dans le plan |
| **`cadences.py`** | **les cadences**, lues dans les scripts du binaire : 419 scripts, 3 614 images |
| **`objets.py`** | exporte un sprite animé en tuiles **entrelacées** pour le moteur, plus sa palette |
| **`donnees.py`** | **le plan, la palette, la cadence, les drapeaux** — voir `DONNEES.md` |
| **`planches.py`** | **toutes les animations de fond, decor par decor** — 232 animations, 2385 images |
| **`animations.py`** | choisit une animation par etage et l'exporte pour 3SX |
| **`cuire.py`** | **cuit les sprites dans la banque `.pvc` et découpe les quinze étages** pour 3SX |
| `verifier.py` | rejoue les quatre épreuves et rend un verdict (`tester.cmd`) |

Le disque : `C:\Users\frede\Downloads\SF3.3 music\Street Fighter III - Double Impact.cdi`

---

## Méthode — ce qui a marché, et ce qui a coûté cher

**Aller lire le code plutôt que deviner.** Le `.pvc`, les décompresseurs, les palettes,
l'assemblage : quatre fois sur quatre percés en désassemblant. Les sessions perdues l'ont
été à empiler des hypothèses sur une image.

**Une mesure qui ne peut pas mentir vaut mieux que dix indices.** Les sommes de contrôle du
jeu, la consommation exacte du flux, le chevauchement à 2,35 % contre 15–23 %, les pages
colorées et numérotées : c'est ce qui a tranché à chaque fois.

**Se méfier de ses propres règles.** Le test de couverture, la progression des numéros de
palette, le choix par lissage : trois règles inventées en route, trois fois démenties par le
cas suivant. Quand deux mesures se contredisent, c'est la forme retrouvée dans les tuiles
qui décide.

**Vérifier avant de faire relancer le jeu.** Plusieurs parties ont été demandées pour rien :
empreintes prises dans un dump cumulatif, touche `F1` inventée alors que la fenêtre de
débogage n'existe pas en RELEASE, tableau annoncé étendu sans que le fichier ait été écrit.
Relire le journal, relire le fichier.

**Ne jamais filtrer la sortie de compilation** ni prendre le silence pour un succès.
`-Werror` attrape les discordances de taille entre `.h` et `.c` — c'est un allié.

**Frédéric corrige, et il a raison.** Le sac de frappe de Ryu pris pour un élément de décor,
deux fois. Le but même du chantier. Écouter la remarque avant de continuer.

**Livrer des lanceurs `.cmd`**, jamais de ligne de commande à recopier.
