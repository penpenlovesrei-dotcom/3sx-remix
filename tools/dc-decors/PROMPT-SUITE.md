# Relais — les décors de 2nd Impact et de New Generation dans 3SX

Chantier : **AJOUTER** les décors de Street Fighter III New Generation et 2nd Impact,
depuis le disque Dreamcast de Double Impact, **à** 3SX — le port natif de 3rd Strike.

Ajouter, pas repeindre.

Clone de travail `C:\Temp3sx` (git, branche `tout-en-un`).
Matériel du chantier : `C:\Users\frede\Downloads\3sx-outils\dc-decors\`

---

## LIS ÇA EN PREMIER, AVANT TOUT LE RESTE

### 1. ON N'EMPRUNTE PAS, ON FABRIQUE

Frédéric l'a demandé une dizaine de fois avant que ce soit fait. **Aucune ressource du jeu
ne doit être détournée pour porter quelque chose à nous** — ni une archive de pages, ni un
motif, ni une table de trans.

* Les pages ont leur archive : `outils/archive.py`, `resources/stages/1535..1549.bin`.
* Les objets animés ont **leur groupe** : `notre_trans` et `notre_texture` dans
  `decor_objets.c`, tendus au moteur par `DecorObjets_Groupe`.

Tout ce qui a été emprunté a fini par geler le moteur. La table de trans est **partagée**,
le `cg_number` du donneur **défile** trame après trame, et ses motifs n'ont ni la même
longueur ni les mêmes tailles de morceaux.

### 2. LES SAVESTATES SONT INTERDITS

**Aucun `.state` Flycast dans la chaîne. Jamais.** New Generation n'a aucun relevé : toute
règle tirée d'un état ne s'automatise pas, donc ne vaut rien pour la moitié du chantier.
Tout se lit dans `SF3_2ND.BIN` et les assets du disque.

`cuire.py`, `elements.py`, `animations.py` et `etat2.py` lisent encore les états — ils sont
**périmés**. Les outils vivants sont listés plus bas.

### 3. NE PAS S'ARRÊTER

Ne rendre la main que pour **une vraie question** ou **un essai à faire lancer**. Un
résultat, un rapport d'étape, un plan à valider n'en sont pas.

### 4. NE RIEN DÉPLACER QUI N'A PAS ÉTÉ SIGNALÉ

Une remarque sur un sprite ne vaut que pour celui-là.

### 5. LIRE LE CODE, PAS L'IMAGE — ET INSTRUMENTER AVANT D'ACCUSER

Ne jamais régler à la vue. Trois pannes de cette session ont été résolues par une trace,
après que trois hypothèses raisonnables se soient révélées fausses :

* le gel de fin de round n'était **pas** l'effet d'aube — `Round_Result & 0x980 = 0` ;
* le ciel de Gill dans les menus n'était **pas** le cache — c'était `TexRemix_SetStage`
  jamais annulé ;
* le gel d'Oro était le cache, et `fatal.log` l'a dit en toutes lettres.

Les journaux sont en place : `decor-objets.log`, `fin-de-round.log`, `fatal.log`, à côté
de l'exe. **Le lanceur les affiche à la fermeture du jeu.**

### 6. TOUJOURS UN LANCEUR `.cmd`

Jamais de ligne de commande à recopier. Le lanceur explique ce qui a changé, ce qu'il faut
faire, ce que je cherche, et affiche les journaux à la sortie.

---

## OÙ EN EST LE JEU

Compilation MSYS2/MinGW64 : `PATH=/c/msys64/mingw64/bin:$PATH ninja` depuis
`C:\Temp3sx\build`, puis recopier `build\3sx.exe` dans `build\application\bin\`.
**L'exe se verrouille quand le jeu tourne** — si `cp` dit « Device or resource busy »,
c'est qu'il faut le fermer.

Python : `C:\Users\frede\AppData\Local\Python\pythoncore-3.14-64\python.exe`.

### Ce qui marche, vu à l'écran

* **Quinze étages de 2nd Impact**, 22 à 36, en versus. Trois lignes à la sélection :
  `2ND IMPACT` / le nom du personnage / `2ND IMPACT BGxx`. Attention, l'étage 0 de 3S
  s'appelle aussi « GILL STAGE » : c'est la troisième ligne qui distingue.
* **Chaque étage a SA PROPRE archive de pages**, jusqu'à quatre plans, coefficients de
  parallaxe lus dans le binaire (table `0x8C1D4F48`).
* **Les éléments statiques des quinze étages** viennent de l'annuaire. Mesure : le binaire
  retrouve les positions des relevés **au pixel**, douze étages sur quinze inchangés.
* **Oro (31) a ses trois couches** — couchant, grotte du fond, grotte proche — et l'aube
  de fin de round tourne partout, avec son art.
* **Gill (22) : quatre objets animés. Oro (31) : sept.** Générés depuis le binaire.

### Les lanceurs

    GILL ET ORO - le cache double, les copies retirees.cmd    le dernier essai
    LES 15 ETAGES - elements depuis le binaire.cmd            les quinze etages
    MENUS - AVEC / SANS les objets animes.cmd                 l'interrupteur

`SF3_DECOR_OBJETS=0` coupe tous les objets animés sans toucher au décor — c'est
l'interrupteur qui répond à « ce défaut vient-il des objets ? ».

---

## LES OUTILS VIVANTS

| outil | rôle |
|---|---|
| `annuaire2i.py` | quel bloc d'éléments appartient à quel décor |
| `annuaire_animes.py` | **la sixième table de la série : les blocs d'objets ANIMÉS** |
| `situer_animes.py` | où un objet est vraiment, cherché dans la banque du disque |
| `peints.py` | quels sprites de l'asset sont peints dans les pages |
| `palette_peinte.py` | identifie un sprite peint **sans connaître sa palette**, et la déduit |
| `planche_sprites.py` | tous les sprites d'un asset sur une planche, pour les reconnaître |
| `planche_animes.py` | pose les candidats sur la banque, pour que l'œil tranche |
| `poser2i.py` | cuit les éléments **statiques** dans les pages des quinze étages |
| `poser22.py` | idem pour `bg00` seul, avec ses exceptions |
| `couches2i.py` | les couches de fond quand un décor en a plus de deux |
| `animer2i.py` | **génère les objets animés** dans `decor_objets_data.c` |
| `situer_objets.py` | replace un objet animé en identifiant son sprite dans l'asset |
| `etages.py` | les tables C des plans et les archives |

---

## CE QUI RESTE

### 1. Les autres objets animés d'Oro — le chantier immédiat

Oro a **trente-neuf animations** dans son asset ; on en pose sept. Il manque notamment
**les chats sur la plateforme de pierre et l'animation du perroquet** — le perroquet
visible est cuit dans la page, pas animé.

Son bloc d'objets animés est en **`0x8C17E928`, sept enregistrements de 16 octets**, au
format de l'annuaire `{plan, drapeaux, x, y, palette, script, ...}`. Il est borné par deux
échecs francs : `0x8C17E918` (index hors asset) avant, `0x8C17E998` (script 61, hors des
53 scripts d'Oro) après. **Les deux enregistrements d'après la rupture ont été essayés et
rejetés à l'écran** : un filet d'eau au pied de Ryu, un objet gris hors de propos.

**La piste :** la zone `0x8C17E7B8`–`0x8C17E8C8`, juste au-dessus, contient une longue
suite d'enregistrements qui résolvent tous proprement dans l'asset d'Oro, palettes dans sa
plage. Ce sont très probablement les autres **aires** du décor — 2nd Impact en a trois par
étage, et l'annuaire est indexé par aire. Y aller bloc par bloc, borner par les échecs
francs, et faire trancher par l'écran.

### 1 bis. LES VARIANTES DE DÉCOR — un chantier à part entière, jamais ouvert

**Un décor de 2nd Impact peut avoir trois versions**, et le jeu en change entre les rounds.
C'est le champ **aire** : toutes les tables sont indexées par `décor*3 + aire`, avec
`aire = u8[0x8C6AF304 + 5]`. Jusqu'ici la chaîne lisait **toujours l'aire 0** — donc pour
ces décors-là, on ne voyait qu'un tiers du contenu.

Relevé des décors dont les trois aires diffèrent réellement (nombres par aire) :

| décor | bande | éléments | second jeu |
|---|---|---|---|
| 6 | `bg06` Hugo | **2 / 3 / 3** | 4 / 4 / 4 — *pointeurs différents* |
| 8 | `bg08` Elena | **0 / 1 / 1** | **9 / 1 / 1** |
| 16 | `bg10` Hugo bis | **2 / 3 / 3** | **4 / 2 / 2** |

Les quatorze autres ont leurs trois aires identiques : rien à faire pour eux.

Hugo, en détail — ce n'est pas une répétition, c'est une **progression** :

    aire 0 : sprite 146 (512,144)   sprite 144 (464,78)
    aire 1 : sprite 149 (336,81)    sprite 152 (512,70)   sprite 144 (464,78)
    aire 2 : sprite 149 (336,81)    sprite 151 (448,56)   sprite 152 (512,70)

Le 146 n'existe qu'au premier round, le 151 qu'au dernier, et le 144 disparaît à la fin.
C'est la foule du stage qui évolue de manche en manche.

**Ce qui manque n'est pas la donnée, c'est le moteur.** L'extraction est immédiate — le
nombre et le pointeur se lisent par `décor*3 + aire`. Mais 3SX cuit **une** version des
pages par étage et n'a aucune notion d'aire. Il faut donc, au choix :

* trancher pour une aire et la cuire (le plus simple, et sans doute l'aire 0) ;
* ou porter la sélection par round dans le moteur, ce qui est un vrai petit chantier.

### 1 ter. LA PALETTE DU SPRITE 497 DE `bg0b` — mis de côté le 30/08

La figure féminine de l'étage 32 sort avec de mauvaises couleurs, et **cinq méthodes ont
échoué** — inutile de les refaire :

1. les 16 palettes que `bg0b` charge réellement (1085–1100) et ses 3 secondaires ;
2. les 2715 palettes du binaire sous contrainte du groupe d'offsets — 1800 bases valides ;
3. le classement par douceur du dégradé, critère objectif qui repère les vraies palettes ;
4. le sprite cherché peint dans les 21 décors de 2I — au mieux 80 %, sous le seuil ;
5. les 71 blocs de `B0B.PK` qui ressemblaient à des palettes — tous du bruit.

**Le fait structurel à retenir :** `bg0b` contient **78 sprites employant 45 index ou
plus**, alors que sa médiane est 15. Oro n'en a aucun, Ryu trois. Le sprite 497 est de
cette population — un niveau de détail de personnage, pas de décor. Et `bg0b` est le seul
décor dont l'offset maximal (129) déborde ses 16 palettes.

**Hypothèse à vérifier** : le bloc `0x8C17C250` attribué à Yang n'est pas un bloc d'objets
de décor. La piste restante est de désassembler le chemin des palettes de PERSONNAGES,
distinct de celui des décors qui est, lui, entièrement établi.

### 1 quater. L'ANIMATION PAR SUBSTITUTION DE PAGES — ✅ FAIT le 31/08/2026

> **Réglé pour Akuma.** La table cherchée ci-dessous existe et elle est lue :
> `0x8C17D8DC` pour les suites, `0x8C17D3DC` pour les **destinations**, qui donnent x et y
> au pixel près (`décalage = 4 × index du bloc 16×16`). Les appelants donnent
> l'appartenance : étage 15 → entrées 8, 9, 10. Les trois animations d'Akuma sont posées et
> compilées. Le mécanisme entier est dans `SANS-ETAT.md`.
>
> La substitution n'a **pas** été portée dans `tex_remix.c` : on en fait des objets animés
> de notre système, ce qui évite d'emprunter quoi que ce soit au jeu.
>
> **Reste de ce chantier :** les entrées 0, 4, 5, 6, 7, 11 appartiennent aux étages 7, 8
> et 9, qui ne sont pas encore montés. Et la vérification des quatre autres décors à trois
> demi-banques tient toujours.

*Ce qui suit est l'état d'avant, gardé pour la trace.*


**Ce n'est pas un cycle de palette, c'est un magasin d'images.** Le rendu des trois
demi-banques d'Akuma le montre sans ambiguïté :

* `b0 bas` — le rocher, la barque, le sol : le premier plan, **avec des trous** ;
* `b0 haut` — la canopée et le ciel : le fond ;
* `b1 haut` — **six variantes de la même cascade**, plus un rectangle aux braises orange.

La troisième banque n'est pas une couche. Ce sont les **images d'animation** : la cascade
qui coule et l'entrée de grotte qui vacille. Le décor a des trous, et ces pages viennent
les remplir tour à tour.

> **Une demi-banque non vide n'est donc pas forcément une couche.** Le tri se fait sur le
> contenu : une couche est une image continue, un magasin est fait de vignettes répétées.
> Poser un magasin comme couche donne une mosaïque et des rectangles noirs — c'est ce
> qu'Akuma faisait **depuis le début**, avant même le chantier des trois couches.

**À faire :** trouver dans le binaire la table qui dit quelle page du magasin remplace
quelle page du décor, et à quelle cadence — puis porter la substitution dans `tex_remix.c`,
qui sait déjà remplacer une page par son numéro (`TexRemix_SetStage`).

**À vérifier au passage :** les cinq autres décors à trois demi-banques (Necro, Hugo,
`bg07`, Ibuki, Oro). Oro est validé à l'écran, mais rien ne dit que les quatre autres
n'ont pas, eux aussi, un magasin là où on a posé une couche.

Sur le décor d'Akuma, Frédéric signale que **la cascade ne coule pas** et que **l'entrée de
la grotte devrait s'animer** (les braises orange de la capture Dreamcast). Or ce décor n'a
ni élément statique, ni objet animé, ni même d'asset F_ETC — c'est vérifié trois fois.

Donc ces mouvements ne viennent pas de sprites : ce sont des **cycles de palette**, et le
port ne les implémente pas du tout.

> **FAUX, corrigé le 31/08.** Ce ne sont pas des cycles de palette mais des **substitutions
> de pages**, et le mécanisme est explicite dans le binaire. La déduction « ni élément, ni
> objet, ni asset, donc palette » était un raisonnement par élimination sur une liste de
> possibilités incomplète — le genre d'erreur que seule la lecture du code corrige.

L'indice le plus net vient de Ryu : ses cascades emploient l'offset 25, et la banque
contient **cinq palettes consécutives** (379 à 383) qui ne diffèrent que par les teintes
de l'eau. Même chose chez Oro, où un plateau de douze palettes voisines était apparu. Ce
sont les images d'un cycle.

**À faire :** trouver dans le binaire la table qui décrit ces cycles — quelle palette, quelle
plage d'entrées, quelle cadence — puis porter le mécanisme dans `decor_objets.c`, qui sait
déjà écrire dans `ColorRAM` et appeler `palUpdateGhostCP3`.

### 2. Les treize autres étages n'ont toujours qu'un objet animé

Et sept d'entre eux n'en ont aucun. La table d'objets animés n'est connue que pour deux
décors :

    bg00   0x8C183DC8   4 enregistrements de 8 octets  {x, y, palette, script}
    bg0a   0x8C17E928   7 enregistrements de 16 octets {plan, drapeaux, x, y, pal, script}

Quatre pistes ont échoué pour les autres, à ne pas refaire :

* les dix tables de la série `0x8C5F9B38` — aucune ne porte les quatre objets de `bg00` ;
* le graphe d'appels du script d'étage (dispatcher `0x8C1D3FB4`) — seul le décor 0 atteint
  sa table à faible profondeur ; à la profondeur 4 on touche 2148 fonctions ;
* le balayage de la région par l'épreuve de l'asset — `bg0b` a 93 scripts et un span
  énorme, il avale tout ;
* la recherche d'un couple `(x, y)` connu — donne des coïncidences.

**Ce qui marche :** partir d'un élément dont on connaît la position par un autre chemin,
le retrouver dans la région, puis borner le bloc par les échecs francs et **vérifier les
palettes** — celles d'un décor sont groupées.

### 3. Les boucles d'animation de Gill — mis de côté par Frédéric

Les acolytes tournent la tête vers les combattants : leurs images sont des **orientations**
choisies par la position des joueurs, pas les étapes d'un cycle. Le champ `boucle` de
`DecorAnimation` fige une animation sur son image 0 ; `animer2i.py` le met à zéro quand le
profil des écarts est un **palindrome à maximum central**, ce qui attrape l'acolyte du
fond. Une pose balayée en aller simple lui ressemble encore à une boucle : le dictionnaire
`BOUCLE` d'`animer2i.py` permet de nommer les autres à la main.

### 4. Convertir `cuire.py`, `elements.py`, `animations.py` sur la chaîne sans état

### 5. New Generation — vingt-trois décors, `SF3_1ST.BIN` et `SFNG/`

C'est pour ça que tout a été fait sans savestate.

---

## LES PIÈGES DE CETTE SESSION, TOUS PAYÉS CHER

1. **La table de trans est partagée.** Y écrire sa grille et ne pas la rendre gèle le
   moteur — `get_mltbuf32_ext` journalise puis part en `while (1) {}`.
2. **`TexRemix_SetStage` n'était jamais annulé.** La substitution par NUMÉRO de page
   restait ouverte après l'étage : le ciel de Gill traversait les menus. `SetStage(-1)` à
   la fin du chargement.
3. **Le tas d'effets recycle ses emplacements.** Un pointeur `WORK` gardé après la mort de
   l'objet coïncide avec un objet des menus. `DecorObjets_Oublier`, accroché à
   `push_effect_work` et `effect_work_init`.
4. **Un pointeur gardé d'un étage à l'autre ne vaut rien** : les tables sont rechargées.
5. **`mts_OB_page[stage]`, pas `mts_base[7]`.** Le cache des objets de décor prend son
   nombre de pages dans une table **par étage**. Nos quinze héritaient de `{1, 1}` — 256
   morceaux — et neuf objets le remplissent. Gill `{3, 1}`, Oro `{4, 1}`.
6. **L'index 0 d'une palette est transparent par construction**, et la banque du binaire
   ne le sait pas : elle y met une vraie couleur. Sans le forcer à zéro, chaque sprite
   sort dans un carré noir opaque.
7. **Les bases de palette de `bases.py` sont déduites, donc faillibles.** Celle d'Oro
   valait 1674 et donnait des bleus ; la vraie est **1429**, trouvée en cherchant dans la
   banque une palette validée à l'écran — retrouvée à l'identique sur ses 64 couleurs.
   **Quand une couleur est fausse, chercher la palette validée dans la banque.**
8. **Le champ palette n'est pas constant sur un sprite** : chaque morceau garde la sienne,
   sinon du magenta `0xFC1F` sort là où la palette imposée n'a rien.

---

## LES DOCUMENTS

| fichier | rôle |
|---|---|
| **`SANS-ETAT.md`** | **la chaîne sans savestate — fait foi** |
| `RELAIS.md` | l'historique ; tout ce qui passe par `releves2/` est périmé |
| `DONNEES.md` | les quatre données de 2I |
| `ASSEMBLAGE.md` | l'assemblage des sprites et la règle des palettes |
| `PALETTES-CONFIRMEES.md` | les palettes établies — **à relire, celle d'Oro était fausse** |
| `FORMAT-PVC.md`, `CARTES-BG.md`, `TESTER.md` | le format, le placement, les épreuves |
