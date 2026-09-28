# Tester les sprites de décor de 2nd Impact

Un seul lanceur : **`tester.cmd`**, à la racine de `dc-decors\`.

Il ne lance pas le jeu. Tout se mesure sur les états Flycast et sur les fichiers du
disque, et les quatre épreuves peuvent échouer.

    tester.cmd
      1. python elements.py    -- réassemble les éléments des dix-sept états
      2. python verifier.py    -- les trois épreuves mesurables, puis les images
      3. ouvre la planche et les superpositions

Il faut les états Flycast dans `%USERPROFILE%\Documents\Dreamcast\data\`
(`Street Fighter III - Double Impact*.state`) et les relevés de `releves2/`,
que `relever2.cmd json` régénère si besoin.

---

## Ce qui doit sortir

### 1. Les bornes du pool

    187 sur 187 couples (etat, cle)
    REUSSI

C'est **l'épreuve qui porte la découverte**. Pour chaque couple (état, clé), le
programme lit dans la fiche `0x8C602384 + (clé & 0xFF) * 24` le nombre de blocs de
l'asset, et vérifie que la plus grande tuile demandée y tombe : `tuile >> 4 < nombre`.

Si le champ `tuile` indexait autre chose — un atlas commun, la banque `.pvc`, un pool à
base non nulle — des milliers de tuiles sortiraient des bornes. Aucune ne sort.

### 2. La clé se relit dans sa fiche

    284 sur 284 fiches
    REUSSI

Le champ `+20` de la fiche vaut la clé elle-même. C'est ce qui prouve que la table
`0x8C602384` est bien celle qu'on croit, et pas un tableau voisin qui aurait l'air juste.

### 3. L'asset se nomme par ses octets

Les 256 premiers octets de la section graphique lue **en RAM** doivent se retrouver tels
quels dans un fichier de `sprites/`. Correspondance exacte, pas une ressemblance.

    0x0129 ( 41)  2i-b0c-F_ETC24        0x0130 ( 48)  2i-b08-F_ETC31
    0x012a ( 42)  2i-b02-F_ETC25        0x0131 ( 49)  2i-b04-F_ETC32
    0x012b ( 43)  2i-b03-F_ETC26        0x0132 ( 50)  2i-b0a-F_ETC33
    0x012c ( 44)  2i-b0b-F_ETC27        0x0133 ( 51)  2i-b01-F_ETC34
    0x012d ( 45)  2i-b05-F_ETC28        0x0134 ( 52)  2i-b0d-F_ETC35
    0x012e ( 46)  2i-b06-F_ETC29 (+b10) 0x013a ( 58)  2i-b00-F_ETC41
    0x012f ( 47)  2i-b08-F_ETC30        0x0158 ( 88)  2i-b0e-F_ETC94

    14 cles nommees
    REUSSI

`F_ETC29` sort deux fois parce que `bg06` et `bg10` sont le même décor — c'est déjà
connu, et c'est la seule ambiguïté.

### 4. Le sol

    13 decors, 0 pixel en haut
    REUSSI

Aucun pixel de sprite ne doit tomber dans la moitié **haute** de la banque : les éléments
de décor se tiennent sur le sol du plan proche. C'est l'épreuve qui a manqué au premier
essai dans le jeu — le `109` du code de dessin est la ligne du sol **à l'écran**, pas dans
la banque, et tout le groupe se retrouvait à cheval sur le bouclage à `y = 0`.

### 5. Les images — à juger à l'œil

Quatre fichiers s'ouvrent tout seuls. Ce qu'il faut y voir :

| image | ce qui doit s'y voir |
|---|---|
| `planche-tous.png` | **treize décors**, un par ligne : les baigneurs et les cascades de Ryu, l'étal 九記 et la foule de Yun, les piétons et le feu de Dudley, le public et les cordages de Hugo, le Bouddha et la grue de Yang, les palmiers de Sean, l'acacia et le feu d'Elena, les chauves-souris d'Oro, les obélisques de Gill, le pilier d'Urien |
| `superpose-bg03.png` | les étals, la charrette et l'enseigne 九記 **posés sur la chaussée**, à la bonne échelle, devant les bonnes boutiques |
| `superpose-bg0b.png` | les rochers, le Bouddha et les figures **sur le sol rouge du temple** |
| `superpose-bg06.png` | la foule et les cordages **sur le pont du navire** |
| `superpose-bg02.png` | les baigneurs au bord du bassin. Ici le plan **boucle** : le ponton finit vers `y = 1000` et les baigneurs reprennent vers `y = 0`. Contigus, pas décalés |

Ce qui signerait un échec : des objets dans le ciel, à mi-hauteur dans le vide, ou à une
échelle qui ne colle pas au décor. Ce sont les trois autres conventions de placement
essayées, et elles se voient au premier coup d'œil.

Sur les couleurs, deux décors restent discutables — `bg05` (necro), rose et mauve, et
`bg0e` (urien), rouge et orange. Les deux scènes sont violemment éclairées dans le jeu,
donc ce n'est pas forcément faux ; ce n'est pas confirmé pour autant.

---

## Ce que le test ne couvre pas

- **`bg07` (Ibuki) et `bg0f` (la gorge) n'apparaissent pas**, et c'est normal : aucun
  élément de leur liste d'affichage ne renvoie à un pool nommé, et `sprites/` ne contient
  ni `b07` ni `b0f`. La cascade animée de la gorge est faite autrement — à établir.
- **Rien n'est encore cuit dans le plan ni découpé** : `tester.cmd` vérifie l'assemblage
  et le placement, pas le rendu dans 3SX. Les plans de
  `rendus/elements/<décor>-planN.png` sont dans le même repère de 1024×1024 que les
  banques `.pvc`, mais il reste à trancher quels plans de sprites vont sur le lointain et
  lesquels sur le proche avant d'appeler `bande3sx.py`.

## Tester dans le jeu

    C:\Temp3sx\build\application\bin\Les 15 etages de 2nd Impact AVEC SPRITES.cmd

Il installe `etages2i-sprites\stageNN` dans `tex_remix` et lance 3SX. Mode **versus**,
faire défiler le stage après le dernier de 3rd Strike : les quinze se suivent.
Pour revenir aux décors nus, relancer `Les 15 etages de 2nd Impact.cmd`.

Les pages se régénèrent depuis `dc-decors\outils` :

    python cuire.py               tous les plans
    python cuire.py --plans 2     seulement le plan 2, si le rectangle noir de Yun gêne

## Voir un décor en particulier

    elements.cmd bg0b

Sort `rendus/elements/bg0b-eNNN.png` (chaque élément seul, dans ses propres coordonnées)
et `rendus/elements/bg0b-planN.png` (le plan de 1024×1024).

Et pour le seul tableau clé → asset, sans rien reconstruire :

    pools.cmd
