# BILAN — ce qui est su, ce qui est supposé, ce qui manque

*01/09/2026, après une session où j'ai cassé deux fois ce qui marchait. Écrit à la demande
de Frédéric : « TU DOIS pouvoir intégrer un décor dans 3S au premier essai et sans erreur.
Fais le bilan de ce qui te manque ou qui t'est inconnu. »*

---

## 0. Pourquoi j'ai échoué ce soir — la cause est unique

Les trois erreurs de la soirée (Sean dégradé, Necro déplacé alors qu'il n'était pas
signalé, sprites effacés) ont **une seule cause** :

> **Je n'ai jamais vérifié dans quel sens un `bank_y` croissant déplace un sprite à
> l'écran.** J'ai raisonné à partir des commentaires du code, obtenu deux fois des
> conclusions opposées, et corrigé dans les deux sens sans jamais mesurer.

Ce n'est pas un détail de calcul, c'est le socle : **toute la chaîne de position se réduit
à un axe dont j'ignore l'orientation.** Tant qu'il n'est pas établi, chaque « correction »
de hauteur est un tirage à pile ou face — et j'en ai fait trois.

Le reste de ce bilan sépare ce qui tient de ce qui n'est qu'une supposition.

---

## 1. CE QUI EST SÛR — mesuré, et recoupé par au moins deux chemins

| acquis | preuve |
|---|---|
| L'index de `0x8C1D3FB4` est la **BANDE**, pas le décor | 16/17 blocs résolvent à 100 % contre 14/17 ; redresse les deux échecs ; confirme par le calcul le bloc d'Oro tranché à l'œil |
| Le décor 8 de 2I porte les bandes 8/9/9 (`0x8C1D591C`) | lu dans le binaire, explique le « décalage à partir de l'étage 10 » |
| Trois décors seulement ont des éléments variables par aire : **6, 8, 16** | balayage des 17 décors ; le 16 partage les pointeurs du 6 |
| Le chemin du singe de Sean, de bout en bout | 4 recoupements indépendants : sprite 18 égal 2560/2560, durées identiques au C, signature `x736 y208 script7` **unique dans tout le binaire**, position recalculée identique |
| La chaîne reproduit les 3 positions de `bg00` validées à l'écran | temple 384,863 / obélisques 608,759 / petit obélisque 464,839 — au pixel |
| `char_add[37]` était la cause du gel de NG | corrigé, NG s'affiche |
| Douze banques sur quatorze finissent à la ligne **1023** | `bg0d` 1007, `bg05` 972 |
| Chez `bg05`, cette dernière ligne n'est **pas un sol** | 6 px de large ; son plan proche est un premier plan découpé |
| **Aucun élément n'est peint dans sa banque** | testé sur les 30 éléments des 14 décors : **0 correspondance** |

---

## 2. CE QUI N'EST VALIDÉ QUE SUR UN SEUL CAS

**La chaîne de position entière ne repose que sur `bg00`.** C'est le seul décor dont des
positions ont été validées à l'écran, et elles l'ont été il y a plusieurs jours.

    bank_x = element.x + ancre_x + x0
    bank_y = sol - element.y + ancre_y + y0
    y      = 1024 - bank_y - (ligs - 1) * 16

Chaque terme de ces trois lignes est **supposé général** alors qu'il n'est vérifié que sur
quatre sprites d'un seul décor. En particulier :

* `sol` : mesuré par décor comme « dernière ligne non vide ». Ça vaut 1023 douze fois, et
  ça tombe juste sur `bg00`. **Rien ne prouve que ce soit le sol** — c'est « où s'arrête le
  dessin », et le cas `bg05` montre que les deux diffèrent ;
* `(ligs-1)*16` : le facteur de grille, établi sur l'acolyte de Gill (6 rangées) ;
* `ancre_y + y0` : « l'acolyte se tient debout (-96), le filet d'Oro pend (0) ». Deux cas.

---

## 3. CE QUI EST INCONNU — la liste des trous, par ordre de gravité

### 3.1 ~~LE SENS DE L'AXE VERTICAL~~ — RÉSOLU LE 02/09/2026

L'acolyte de `bg00` — seul sprite dont la position soit validée à l'écran (288, 81), et
figé sur son image 0 — a été déplacé à `y 113`. **Réponse de Frédéric : « monté ».** Donc :

    position_y ↑  ->  vers le HAUT
    bank_y     ↑  ->  vers le BAS      (y = 1024 - bank_y - (ligs-1)*16)
    sol        ↑  ->  vers le BAS

**Un sprite trop haut se corrige en AUGMENTANT `sol`.** C'est l'inverse de ce que j'avais
conclu en fin de session du 01/09, et c'est pourquoi l'annulation de ce soir-là était elle
aussi une erreur : revenir à la mesure remontait Sean et Necro, déjà trop hauts.

`sol` est donc la **constante 1023** pour les quatorze décors. Ce qui reste vrai de la
mesure : deux banques ne PEIGNENT pas jusqu'en bas (`bg0d` 1007, `bg05` 972), ce qui est
une autre question — celle du §3.2.

> **La leçon de méthode, et elle a coûté trois régressions** : un axe a deux sens, donc une
> chance sur deux. Il ne se déduit pas d'un commentaire, il se mesure — et l'essai qui le
> mesure prend trente secondes.

### 3.2 LA POSITION VERTICALE DU PLAN — la cause du défaut de Sean

La voiture, son conducteur et le personnage à genou du décor de Sean sont **peints dans la
banque** (vérifié), et pourtant trop hauts à l'écran. Ce n'est donc pas la chaîne des
sprites : c'est le plan lui-même qui est mal placé.

Ce que je n'ai **pas** trouvé, après quatre approches :

* pas de table de décalage vertical par étage dans le binaire (balayages u8 et u16 : du
  bruit) ;
* pas de constante de position Y dans les scripts d'étage ;
* `bg_prm[].bg_v_shift` est **accumulé** par le défilement, pas posé par étage ;
* `bgw_ptr->pos_y_work = 0` dans `bg220.c`, comme les étages d'origine.

**Reste à faire** : décompiler le code de fond de 2I (les fonctions `bg00xx`, pas les
scripts d'étage) pour voir ce qu'il pose en Y à l'init d'un plan. C'est le seul endroit que
je n'ai pas ouvert.

### 3.2 bis LES SPRITES NON POSÉS — où ils sont, et ce qui bloque — 02/09/2026

**Mesure sur Hugo (`bg06`, décor 6), le plus atteint :**

    37 scripts dans sa table          5 posés          31 résolus a 100 % dans son asset

Les 31 se résolvent parfaitement — ce ne sont donc pas des cases mortes, c'est sa foule.

**Ce qui ne marche PAS pour les retrouver**, et il faut le savoir : parcourir les tables de
blocs en retenant ceux qui « se résolvent » dans l'asset du décor. Testé : les blocs de
Necro, d'Oro et de Sean se résolvent aussi à 100 % chez Hugo. C'est le piège que
`SANS-ETAT` signale déjà — **seul l'appelant fait foi**.

**La vraie piste : le SPAWNER DÉDIÉ.** `chargeurs2i` le nomme depuis le début sans que la
chaîne l'exploite :

    decor 6   0x8C036480  porte  0x8C17F54C   (9 champs lus)

Le désassemblage confirme le format : **neuf `mov.w` de 2 octets, donc des enregistrements
de 18 octets**, et les offsets d'objet écrits sont ceux de la convention connue —

    objet+102 = x      objet+106 = y      objet+88 = palette

**CE QUI MANQUE POUR POSER** : l'ORDRE des neuf champs dans le bloc. Sans lui, lire
`0x8C17F54C` donne plusieurs découpages tous « plausibles » (mesuré : 24 lectures
crédibles au pas de 18 selon le décalage), et en choisir un serait exactement l'erreur que
ce document dénonce. Il faut finir le désassemblage de `0x8C036500..0x8C036550` en décodant
correctement les `mov.w @(disp,r14)` — le décodeur employé le 02/09 les confondait avec
`mov.w @r14`.

Les mêmes spawners dédiés existent pour Gill, Alex, Ryu, Yun et Dudley
(`0x8C0258DA`, `0x8C0323F0`, `0x8C036688`, `0x8C02936E`) : le format une fois établi les
débloque tous.

### 3.3 LE SECOND JEU D'ÉLÉMENTS N'EST JAMAIS POSÉ — 26 éléments manquants

`poser2i` ne lit que `AN.elements(d)`, c'est-à-dire le **jeu 1**. Le jeu 2
(`0x8C17BBC4` / la 3ᵉ table de la série) est ignoré :

    bg02 3   bg03 5   bg04 2   bg05 2   bg06 4   bg0b 3   bg0d 3   bg10 4   = 26

C'est très probablement pourquoi Sean « manque des sprites » : il a **5 éléments**
(2 + 3), et nous n'en posons que 2.

### 3.4 CE QUI EST SUPPOSÉ SANS PREUVE

| supposition | pourquoi c'est fragile |
|---|---|
| la répartition des plans (banque 0 haut/bas, banque 1 haut) | établie « à l'œil sur le contenu », dit `couches2i` lui-même |
| `famille` et `z` par plan pour NG | portés de la règle d'Oro 2I, jamais vus à l'écran sur NG |
| les palettes de NG | la chaîne est complète *dans les termes du binaire de NG*, rien n'a été rendu |
| `BASES_2I['bg0d'] = 1519` | la doc dit que l'entrée 55 vaut **984** ; les deux ne peuvent pas être vraies |
| le budget 32 rangs / 256 cases | déduit des bornes, jamais éprouvé — aucun étage chargé n'a été vu |

### 3.5 CE QUI EST CONNU COMME MANQUANT

* les animaux d'Oro (2I **et** NG) : leur bloc n'a jamais été trouvé ;
* deux objets de NG écartés pour dépassement du nombre d'images (90 et 96 contre 64) ;
* les variantes d'aire (décors 6, 8, 16) : mesurées, jamais intégrées — coûteraient
  quatre étages de plus ;
* la ménagerie et le ciel décentré d'Oro NG, signalés ce soir, non diagnostiqués.

---

## 4. CE QU'IL FAUDRAIT POUR INTÉGRER UN DÉCOR DU PREMIER COUP

Dans l'ordre, et chacun est un préalable au suivant :

1. **Établir le sens de l'axe** (§3.1) — un essai, trente secondes.
2. **Se donner une référence vérifiable par décor.** Aujourd'hui il n'y en a aucune hors
   `bg00`, et le test « l'élément est-il peint là où on le calcule » a rendu 0/30. Sans
   référence, *toute* correction de position est un tâtonnement — c'est la leçon de la
   soirée. Piste : rendre le décor complet et le comparer à une capture Dreamcast **une
   fois pour toutes**, sur un décor, pour caler la chaîne ; ensuite elle vaut pour tous.
3. **Poser le second jeu d'éléments** (§3.3) — 26 éléments, mécanique déjà écrite.
4. **Trouver la position verticale du plan** (§3.2) — décompiler le code de fond de 2I.

Tant que 1 et 2 ne sont pas faits, je ne peux **pas** garantir un décor juste du premier
coup, et il vaut mieux que je le dise que de continuer à corriger au jugé.
