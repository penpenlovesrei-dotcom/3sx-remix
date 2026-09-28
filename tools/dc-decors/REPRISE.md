# PROMPT DE REPRISE -- 25/09/2026, fin de journee

## A relire en premier

`DECORS.md` dans `C:/Users/frede/Downloads/3sx-outils/dc-decors/` -- c'est le dossier qui
fait foi. Les deux dernieres sections sont celles du jour.

## Les consignes de Frederic, qui ne changent pas

* **Reponds brievement, en francais**, et nomme les decors par leur personnage.
* **NE LANCE JAMAIS le jeu**, ni aucun `.cmd` qui ecrit dans `%APPDATA%`. Frederic lance ;
  **lui seul juge sur l'image**.
* Livre toujours un `.cmd` **CRLF, ASCII, double-cliquable**, a la racine de `C:/Temp3sx`.
* Les sources deployees vont dans
  `OneDrive/Bureau/SEPTEMBRE/SF3/CrowdedStreet-3SX/resources` ; c'est le lanceur qui recopie.
* **Lis le CODE, pas les images.** Une capture oriente, le binaire donne la valeur.
* **Son observation prevaut** sur le modele.
* Ne deplace pas ce qui n'a pas ete signale ; **ne defais pas ce qui marche** ; ne lance
  jamais un script qui efface « pour voir » ; **ne commite pas sans qu'on te le demande**.
* Les savestates sont interdites comme source : tout se lit dans `SF3_2ND.BIN` /
  `SF3_1ST.BIN` et les fichiers du disque.
* Consigne dans des fichiers, pas en prose.
* Resynchronise les outils vers `SEPTEMBRE/SF3/3sx-outils/dc-decors/outils` et `DECORS.md`
  vers `SEPTEMBRE/SF3/3sx-outils/dc-decors/`.
* **Ne t'arrete pas avant que l'objectif soit atteint.**
* **Ce qui est lu, tu le poses ; ce qui ne l'est pas, tu l'omets. N'invente jamais. Toute
  invention doit etre assumee et annoncee.**
* **Verifie la palette (par `+554`, la regle RAM) en meme temps que la position, AVANT de
  livrer.**
* Attention : `%APPDATA%/CrowdedStreet` est **redirige vers le conteneur de l'application
  Claude**. Toute mesure prise la-bas melange deux vues et ne veut rien dire. Mesure dans
  SEPTEMBRE.

## Ou on en est

Branche `tout-en-un`, dans `C:/Temp3sx`. Construction : `C:/msys64/mingw64/bin/ninja.exe`
dans `C:/Temp3sx/build`.

Lanceur courant : **`HUIT BITS - tous nos decors au format du jeu.cmd`**, executable
`build/3sx-8bits.exe`.

### Livre aujourd'hui, en attente de verdict

1. **Tous nos decors sont passes en huit bits.** Format `.tex` **version 2** : entete de
   16 octets, puis 256 entrees de quatre octets, puis un indice par pixel. 2550 pages
   converties, chacune relue et comparee a l'originale avant ecriture. 159,4 Mo -> 42,4 Mo.
   Cote C : `bits->bitdepth = 1`, et une `propre_palette` par texture qui passe avant celle
   du jeu (`sdl_gpu_renderer.c` et `opengl_renderer.c`). Outil : `outils/pages_8bits.py`,
   et `bande3sx.ecrire_tex` emet desormais la version 2 d'office.
2. **Le crash d'Ibuki en fin de round est corrige** : `Bg_Aire_Suivante` appelle maintenant
   `Bg_Close()` avant de remettre `bg_routine = 0`. `Bg_TexInit` ne libere rien -- il ne
   fait que repointer `ppgBgList[i].tex` -- donc on chargeait un second jeu de 96 pages
   par-dessus le premier sans rendre les poignees du premier. Ibuki est la seule a
   recharger DEUX fois (48, 49, 50), d'ou elle seule plantait. **Non teste par Frederic.**

### CE QU'IL FAUT FAIRE EN PREMIER

**Le decor d'Alex, deux defauts signales sur capture :**

> « probleme de decor pour alex ; il manque le plan derriere le clochard, et le passant
> passe devant lui au lieu de derriere le clochard »

Ce qui est **lu**, dans `src/port/video/decor_objets_data.c`, lignes 194895 a 194912
(les objets `"ng01"`, etage 38) :

    clochard     script  8, 0x8C1AF0B6   x 752  y 103  famille 3  z  90
    passant      script 34, 0x8C0A88D6   x 280  y  96  famille 2  z  85
    passant      script 34, 0x8C0A88D6   x 872  y  96  famille 2  z  86
    gratte-ciel  script  2, 0x8C1AF038   x 674  y 130  famille 1  z 104
    gratte-ciel  script  2, 0x8C1AF038   x 738  y 130  famille 1  z 104

**Un z PLUS GRAND est plus LOIN** (echelle de `stage_priority`). Le clochard est a 90, les
passants a 85 et 86 : **ils sont donc bien devant lui**, exactement ce que Frederic voit.
Le code et son observation disent la meme chose ; c'est la VALEUR qui est fausse.

**Ce qui reste a lire, et qui n'a PAS ete fait :**

* la **profondeur reelle des passants sur la Dreamcast** -- champ `+556` de l'objet,
  `+558` pour le plan. Les deux passants sont des entrees EN DUR dans
  `outils/objetsng.py`, cles `(0x8C0A88D6, 3)` et `(0x8C0A88D6, 4)`, ou `plan=2` a ete
  **ecrit a la main**. C'est cette valeur qu'il faut aller lire au lieu de la supposer.
* **le plan manquant derriere le clochard.** La note du 24/09 disait que le trou des
  colonnes 746 a 804 est la fente de la ruelle, « couverte par l'element gratte-ciel
  (script 2, plan 3, prof 104) ». Les deux entrees gratte-ciel sont a x 674 et x 738,
  4 colonnes de 16 = 64 pixels, soit 738..802. Verifier si elles couvrent vraiment, si
  elles sont dessinees, et si leur z de 104 ne les place pas derriere un plan opaque.

Outils : `d2i.py` / `dng.py` / `sh4ng.py` pour le desassemblage, `outils/objetsng.py` pour
les objets, `outils/descripteursng.py` pour les plans. Table des acteurs NG : `0x8C1ADA10`.
Contexte NG : `0x8C552674`.

### Ce qui attend aussi le verdict

* **Alex** : l'origine verticale (couche 0 remontee de 34 lignes), les deux passants, le
  clochard fige.
* **Sean** : les deux voitures et l'homme a la mallette.
* **Les sept decors a aires**, qui changent de manche en manche : Ryu/Ken (40 <-> 41),
  Yun (42 -> 43), Dudley (44 -> 45), Ibuki (48 -> 49 -> 50), Elena (51 -> 52),
  Yang (55 -> 54). **Yang commence par Yang 2** : si le jeu le propose par l'etage 54,
  rien n'alternera -- regarder alors comment l'etage est choisi.

### Chantiers mesures mais NON ouverts

* Donner des numeros de page distincts aux etages ajoutes, pour tenir plusieurs aires en
  memoire a la fois. Tous partagent aujourd'hui `bg_map_tbl`, le modele de l'etage 5.
* Elena 1, l'oiseau perche (id 53) : dix etats decodes, mais il demande un comportement de
  portage nouveau.
