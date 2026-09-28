# TRANSFERT ET REPRISE — 26/09/2026

Colle ce fichier en entier dans la première fenêtre du nouveau PC. Il remplace tout le
contexte. Tout ce dont le chantier a besoin est dans
`…\SEPTEMBRE\SF3` — **6,8 Go, 22 582 fichiers**, vérifié le 26/09 à 21h40.

---

## 1. CE QU'ON FAIT

Frédéric porte les **décors et les sprites animés de Street Fighter III : 2nd Impact (2I)
et New Generation (NG)**, lus sur les disques Dreamcast, dans **3SX**, un portage natif de
*3rd Strike*.

---

## 2. LE TRANSFERT — CE QUI EST DANS `SEPTEMBRE\SF3`, ET OÙ LE REMETTRE

| dans `SEPTEMBRE\SF3\…` | à remettre sur le nouveau PC en | quoi |
|---|---|---|
| `Temp3sx\` (1,2 Go, `.git` compris) | **`C:\Temp3sx`** | le port, branche `tout-en-un`, plus les lanceurs `.cmd` |
| `3sx-outils\dc-decors\` (545 Mo) | **`C:\Users\<toi>\Downloads\3sx-outils\dc-decors`** | les outils, les binaires DC, `DECORS.md` |
| `CrowdedStreet-3SX\` (1,0 Go) | **reste où il est** | les pages déployées + `SF33RD.AFS` (642 492 416 o) |

**Les trois chemins sont écrits en dur dans les outils.** Si tu changes le nom
d'utilisateur, il faut corriger :

    outils/pages_doublons.py      RACINE  = …\SEPTEMBRE\SF3\CrowdedStreet-3SX\resources\tex_remix
    outils/pages_8bits.py         RESSOURCES
    outils/couches2i.py           RESSOURCES (%APPDATA%\CrowdedStreet\3SX\resources\tex_remix)
    outils/etages.py              inc = "C:/Temp3sx/src/port/video/etages2i_plans.inc"
    outils/etagesng.py            inc = "C:/Temp3sx/src/port/video/etagesng_plans.inc"
    les lanceurs `.cmd`           SRC = …\SEPTEMBRE\SF3\CrowdedStreet-3SX\resources

**Ce qui n'a PAS été copié, parce que ça se régénère** : `outils\__cache_decors__`
(732 Mo), les `__pycache__`, et `C:\Temp3sx\build\CMakeFiles` (les objets). Le cache se
refait tout seul au premier `animer2i.py`, la première passe est juste plus lente.

**Ce qu'il faut installer sur le nouveau PC** :

* **MSYS2 / mingw64** — la compilation est `C:\msys64\mingw64\bin\ninja.exe` dans
  `C:\Temp3sx\build`. Il faudra relancer `cmake` une fois (les chemins du cache CMake sont
  absolus) puis `ninja`.
* **Python 3** avec `numpy` et `Pillow`, appelé par `py -3`.
* Le jeu tourne depuis `C:\Temp3sx\build\application\bin\3sx.exe` et lit
  `%APPDATA%\CrowdedStreet\3SX`.

**Remise en place, dans cet ordre** :

1. copier les trois dossiers ci-dessus ;
2. double-cliquer `C:\Temp3sx\REMETTRE LES ASSETS DU JEU.cmd` (fusion ~1,2 Go vers
   `%APPDATA%`, ne supprime rien) ;
3. double-cliquer `C:\Temp3sx\VERIFIER LES ASSETS.cmd` — il doit rendre l'empreinte
   `f9fa50f3a124ec9fa9465aa9c8546c2d867887eb39f711a070762a0324ba5604` ;
4. reconfigurer et recompiler, puis copier l'exe en `build\3sx-8bits.exe` ;
5. double-cliquer le lanceur du jour.

**Il n'est pas nécessaire de recompiler tout de suite** : `build\3sx-8bits.exe` est déjà
dans le transfert, daté du 26/09 09:55, 34 135 237 octets.

---

## 3. LES RÈGLES DE TRAVAIL — elles ne se négocient pas

1. **Répondre brièvement, en français.** Nommer les décors par leur personnage
   (« Ryu 2I », « Elena NG »), pas par `bg02` seul.
2. **Ne JAMAIS lancer le jeu**, ni aucun `.cmd` qui écrit dans `%APPDATA%`. C'est Frédéric
   qui lance et **lui seul qui juge sur l'image**.
3. Toute livraison est un **`.cmd` en CRLF, ASCII, double-cliquable**, à la racine de
   `C:\Temp3sx`. Il copie l'exe, copie les pages, explique ce qui a été fait, puis lance.
   Effacer le lanceur précédent.
4. **Lire le CODE, pas les images.** Une capture oriente ; le binaire donne la valeur.
   **Ce qui est lu, on le pose ; ce qui ne l'est pas, on l'omet. Toute invention est
   assumée et annoncée.**
5. **Son observation prévaut** sur le modèle. S'il dit que c'est faux, c'est faux.
6. **Un défaut signalé après une livraison est d'abord une régression** : lister TOUT ce
   qui a changé dans cette livraison avant de chercher ailleurs.
7. Ne pas déplacer ce qui n'a pas été signalé ; **ne pas défaire ce qui marche** ; ne
   jamais lancer un script qui efface « pour voir » ; **ne pas commiter sans qu'il le
   demande**.
8. **Les savestates sont interdits comme source.** Tout vient de `SF3_2ND.BIN`,
   `SF3_1ST.BIN` et des assets du disque.
9. **Vérifier la palette (`+554`, la règle RAM) en même temps que la position, AVANT de
   livrer.**
10. **`%APPDATA%\CrowdedStreet` est redirigé vers le conteneur de l'app Claude** : mesurer
    dans `SEPTEMBRE`, jamais dans AppData — les deux vues sont incohérentes.
11. **Ne pas s'arrêter avant que l'objectif soit atteint.** Pas de « prochain chantier ».
12. Les trouvailles se consignent dans `DECORS.md`, pas dans la conversation.
13. **Ne jamais modifier à la main un fichier généré** — `decor_objets_data.c`,
    `etages2i_plans.inc`, `etagesng_plans.inc`. On touche le générateur, on relance.
14. **Piège d'outillage** : les heredocs bash mangent les `\\` et les apostrophes. Écrire
    les scripts Python avec l'outil `Write`, jamais avec `<<'EOF'`.

**L'ordre de génération, il n'y en a pas d'autre** :

    py -3 animer2i.py --ecrire     (refait TOUT decor_objets_data.c)
    py -3 animerng.py --ecrire     (ajoute New Generation)

Relancer `animer2i` seul efface New Generation. `etages.py` et `etagesng.py --ecrire`
réécrivent les `.inc` et les archives de pages.

---

## 4. CE QUI VIENT D'ÊTRE LIVRÉ — EN ATTENTE DE SON VERDICT

Lanceur à la racine :
**`LES QUATRE DU 26-09 - Hugo, Ryu, Alex NG, la parallaxe.cmd`**

### a) Hugo — la variante par aire était juste, c'est la PAGE qui la cachait

Frédéric : « *je ne vois pas de différence sur les 2 variantes du stage d'Hugo* ». Le
mécanisme allait jusqu'au bout et les masques sont bien dans les fiches compilées
(`0x1`, `0x3`, `0x6`, `0x4`). **Les douze objets étaient peints dans la page déployée** —
une copie peinte ne change pas de manche.

    plan proche (liste 196) de l'étage 28, contre la banque du disque
    avant   13 387 px de différence, dix pages, x 256..896
    après    1 078 px — les deux éléments statiques que le binaire pose, et eux seuls

`poser2i.py bg06 --ecrire` rend **12 309 px** de cuisson à la banque. La page avait été
cuite le 04/09, les douze objets portés le 25 : le nettoyage n'avait jamais vu leur
empreinte. Même défaut que Ryu 2I la veille, même correction.

### b) Ryu 2I — les extrémités, c'est la caméra, pas le fond

Le fond est identique à la banque du disque **au pixel près**. Ce qu'on voit aux bords
n'est pas un fond faux, c'est un fond **absent**.

    le décor peint          x  128 .. 895
    0x0136..0x02C5 voyait   x  118 .. 900     10 px à gauche, 5 px à droite de vide
    0x0140..0x02C0 voit     x  128 .. 895     exactement la bande peinte

`0x140..0x2C0` n'est pas un réglage : c'est le défaut de 3rd Strike, et c'est la course de
383 que 2I impose lui-même (`0x8C0D9C26` borne la caméra à [0,383] ou [0,495] selon
`0x8C841F3C`, **sans table par étage**). `limit_tbl3[24]` y passe, aux trois aires.

### c) Alex NG — le passant en blanc traverse — ÉCART ASSUMÉ

La console le fait marcher **81 pixels**, et ça reste mesuré : `0x8C0A88A4` lit la parité
de `[+38]` ; l'objet k=3 a `[+38] = 4` (pair) et `[+52] = 400`, il part de 320 à
+1 px/trame. La longueur est prise **sur son jumeau** : k=4 part de 912 et s'arrête à
-192, soit 192 px au-delà du bord gauche ; le miroir donne 1023 + 192 = 1215, donc
**895 trames** au lieu de 81.

### d) Dudley — plus de parallaxe — ÉCART ASSUMÉ, CONTRE LES DEUX TABLES

Frédéric : « *les décors DUDLEY 2I et NG n'ont pas de parallaxe dans le jeu original* ».
**Les tables disent le contraire, et elles sont lues :**

    2I  0x8C1D4F48 + 4*0x20   bg04    objet 0 = 0,75 / 0,875
    NG  0x8C189BA0 + 7*0x20   bande 7 objet 0 = 1/1, objet 1 = 1/1, objet 2 = 0,75 / 1
    NG  0x8C189BA0 + 8*0x20   bande 8 objet 0 = 0,75 / 1,  objet 1 = 1/1

Aucune ne dit zéro. On pose 1/1 sur son observation, étages **26, 44, 45**, par
`etages.SANS_PARALLAXE` et `etagesng.SANS_PARALLAXE`.

---

## 5. CE QUI RESTE OUVERT

* **Les cinq parallaxes suspectes.** La paire **0,75 / 0,875** est la plus répandue de la
  table de 2I : quatre décors la portent à l'objet 0 — `bg04` (Dudley, confirmé faux par
  l'œil), `bg06`, `bg0a`, `bg0f`. Ça ressemble à une valeur initialisée que le script
  d'étage n'écrase pas. **À regarder** : étage 36 Akuma 2I et 47 Hugo NG (plan lointain),
  28 Hugo 2I, 31 Oro 2I et 53 Oro NG (plan supplémentaire). Ce qui trancherait : le
  balayage `mov.l Rm,@(0,Rn)` / `@(4,Rn)` sur chaque script d'étage, comme celui qui a
  donné les écrasements de l'objet 2 pour `bg01`, `bg09` et `bg0e`.
* **La transition de décor d'Elena — bloquée, et la raison est lue.** Une transition
  animée demande les DEUX bandes à l'écran en même temps. Or les vingt et un étages
  ajoutés partagent la même carte de pages (`bg_map_tbl`, le gabarit de l'étage 5) :
  Elena 1 (51) et Elena 2 (52) portent les MÊMES numéros, 132..163 et 196..227. Il faut
  d'abord **numéroter les pages par aire** (Ibuki 48/49/50, Dudley 44/45, Elena 51/52,
  Elena 2I 56/30), puis **lire** la transition dans NG : on ne sait pas encore si c'est un
  fondu, un panoramique ou un rideau.
* **Cinq décors 2I où la caméra sort de la bande peinte**, mesurés mais non touchés car
  non signalés : 22 Gill (16 px à gauche), 27 Necro (90/143), 33 Ken (51 à gauche),
  34 Sean et 35 Urien (111/53). Sean et Urien sont validés à l'écran malgré 111 px : leur
  plan d'œil n'est sans doute pas la liste 196.
* **L'étage 57 (`bg10`, Hugo bis)** porte très probablement les mêmes copies peintes que
  Hugo. Il n'a pas de banque nue dans `etages2i/` et n'est pas dans la liste de `poser2i`.
  Non mesuré.
* **Les quatorze spawners de New Generation non portés**, 58 appels. Le plus gros est
  `0x8C09F258` (25 appels, id 14, étages 40, 48, 49, 50, 52) : il pose `[+0]=1`, `[+8]=14`,
  `[+6]=16`, `[+4]=type` **et rien d'autre** — toute la conduite est dans la routine d'état
  `0x8C09CCC8`. Puis `0x8C0A5488` (9 appels, id 48), `0x8C0AC0D2` (6), `0x8C0AA894`
  (3, id 75), `0x8C0A03CC` (3, id 20), `0x8C031354` (3), `0x8C09E204` (2, id 11), et sept
  à un appel. **Ibuki en concentre la moitié** : cinq spawners, 24 appels (étages 48-50).
* **Le vol de l'oiseau d'Elena NG** (états 4 à 9) : position lue à l'exécution
  (`u16[0x8C552758 + 10]`), vitesse **et** accélération, échelle de 4 à 127. Et il change
  de profondeur trois fois (`0x8C0A64D4` → 79, `0x8C0A66DA` → 10, naissance 67) : une
  fiche n'a qu'UN `z`, il faudrait un **z par segment de trajet**. Non reproduit, déclaré.
* **Les quatre acteurs NG qui lisent le test de contact et ne sont pas portés** : ids 15,
  31, 32, 69. (29 et 75 le sont.)
* **TRAM STREET** et **TEMPLE**, dans l'écran de sélection, sont descriptifs et non
  officiels — offerts à correction, une ligne dans `eff99.c`.
* **`Random_Stage_Data`** (le tirage *arcade*, deux joueurs au hasard) ne contient encore
  que les étages 0–19. Le tirage VS, lui, a nos décors (`Etage_Au_Hasard[128]`).
* **`etages.morceaux_couche`** ne lit que le premier groupe du descripteur de couche.
  Format complet dans `DECORS.md` ; tous les décors mesurés n'ont qu'un groupe.

---

## 6. LES REPÈRES QU'IL FAUT AVOIR SOUS LA MAIN

### Les tables de 2nd Impact (`SF3_2ND.BIN`, base `0x8C010000`)

| quoi | où |
|---|---|
| table d'effets (id → routine) | `0x8C179FDC + id*4`, 196 entrées, répartiteur `0x8C0215E0` |
| table des aires (bande par manche) | `0x8C1D591C + décor*6 + aire*2` — **seul le décor 8 varie** : 8, 9, 9 |
| coefficients de parallaxe | `0x8C1D4F48 + décor*0x20 + objet*8`, deux u32 16.16 |
| bornes de caméra | **il n'y en a pas par étage** : `0x8C0D9C26`, [0,383] ou [0,495] |
| boîtes de rupture | `0x8C1D3ED4 + type*8` |
| spawners indexés sur le décor courant | `0x8C0233B6` et `0x8C02356A`, `u8[0x8C6AF308]` |

**Numérotation des décors** (ni celle des `pvc` ni celle des étages) : 0–7 = bg00–bg07,
**8 = bg08 ET bg09** (Elena, étages 56 et 30), 9 = bg0a Oro (31), 10 = bg0b Yang (32),
11 = bg0c Ken (33), 12 = bg0d Sean (34), 13 = bg0e Urien (35), **14 = bg0f Akuma (36)**,
**16 = bg10** le Hugo non terminé (étage 57), même table de scripts que Hugo `0x8C1281F8`.

**Étages 2I → personnage** : 22 Gill, 23 Alex, 24 Ryu, 25 Yun, 26 Dudley, 27 Necro,
28 Hugo, 29 Ibuki, 30 et 56 Elena, 31 Oro, 32 Yang, 33 Ken, 34 Sean, 35 Urien, 36 Akuma,
57 Hugo bis.

### Les tables de New Generation (`SF3_1ST.BIN`)

| quoi | où |
|---|---|
| table des acteurs (id → routine) | `0x8C1AD9F8 + id*4` |
| table des aires | `0x8C18A804 + décor*6 + aire*2` — **valeurs = bandes 0..18 ; étage = 37 + bande** |
| coefficients de parallaxe | `0x8C189BA0 + bande*0x20 + objet*8` |
| tables de scripts | statique `0x8C4CC1F0 + 12*décor + 4*aire`, copiée à l'exécution en `0x8C4DE610` |
| test de contact | `0x8C085A1E` — **compteur cumulé**, `u16[0x8C552620 + rang*2]` ; rang 5 ne réagit jamais ; le sous-test `0x8C085A94` veut `joueur[+38] == 1`, `14 <= joueur[+40] < 24` et un recouvrement de boîtes — **c'est un coup porté** |

**Yang partage les tables de scripts de Yun, croisées.**

### Les champs d'un objet (les deux jeux)

`+1` disp_flag · `+4` rang · `+8` id · `+36` état · `+38` · `+52` seuil · `+54` compte à
rebours · `+68` avance-script · `+88` palette · `+102`/`+106` x, y entiers · `+118` ·
`+124`/`+126` vitesse 16.16 · `+132`/`+136` accélération · `+148` compte à rebours ·
`+456` script · `+468` drapeau du pas courant · `+554` `my_col_code` · `+556` profondeur ·
`+558` plan · `+568`/`+570` échelle.

### Le port

* `DecorAnimation` (`src/port/video/decor_objets.h`) : initialisation **positionnelle**.
  Ordre : `… num, x, y, fam, z, boucle, variante, aires, [comportement, pas, suites,
  nb_suites], [trajet, nb_trajet, trajet_fin], [échelle ×4], [boîte]`. Ajouter un champ
  oblige à toucher les DEUX générateurs.
* Comportements : 1 CHIEN_DEBOUT, 2 CHIEN_COUCHE, 3 POISSON_ROUGE, 4 POISSON_NOIR,
  **5 TRAJET**, 6 SUR_COMBATTANT, 7 REGARD, 8 REACTIF, 9 RUPTURE.
* Un segment de trajet = **5 shorts** `{durée, vx, vy, suite, z}` ; `z = 0` garde celui de
  la fiche ; `suite = -1` ne change pas l'animation ; `vx = 256` vaut 1 px/trame.
* `aires` : masque de manches, bit 0 = manche 1, **0 = les trois**. Testé par
  `dans_la_variante` ; `aire_objets` avance dans `DecorObjets_MancheSuivante`, appelé par
  `Bg_Aire_Suivante` (bg_sub.c), lui-même appelé par `manage.c` sous `Switch_Screen(0)`.
* Limites : `OBJETS_MAX 56`, `FL_TEXTURE_MAX 512`, `FL_PALETTE_MAX 1088`,
  `SEQS_CHIP_MAX 4096`, 64 images par objet, 32 cases par grille, **128 motifs par étage**.
* `.tex` **v2** = en-tête 16 o (`'3STX'`, version 2, w, h) + 256 × 4 o de palette + un
  octet d'index par pixel. `tex_remix` lit les deux versions.
* Les pages d'une liste : `px, py = (i & 7) * 128, 512 + (i >> 3) * 128`, i de 0 à 31.
  Listes : 132 lointain, 196 proche, 260 troisième, 324 quatrième.
* `doublons.txt` : une page effacée parce qu'identique à une autre ; `tex_remix` s'en sert
  quand le chemin direct manque. `pages_doublons.py --annuler / --appliquer --etage N`
  **avant et après** toute réécriture de pages.
* Budgets de motifs 2I (sur 128) : `22:23 23:6 24:51 25:88 26:21 27:73 28:63 29:42 30:51
  31:79 32:94 33:6 34:12 35:4 56:102 57:38`. Fiches : **386 de 2I + 531 de NG = 917**.

---

## 7. PREMIÈRE CHOSE À FAIRE DANS LA NOUVELLE FENÊTRE

Remettre les trois dossiers en place (§ 2), puis lire `DECORS.md` — **au moins le dernier
chapitre, « LES QUATRE DE LA MANCHE DU 26/09 »** — et **attendre son verdict** sur le
lanceur `LES QUATRE DU 26-09`. Ne rien entreprendre d'autre avant qu'il parle : il juge
sur l'image, et ce qu'il verra oriente la suite.
