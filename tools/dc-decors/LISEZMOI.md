# `dc-decors` — la chaîne qui porte les décors de Dreamcast dans 3SX

Ces cent trente-deux scripts lisent les deux binaires de *Street Fighter III* sur Dreamcast —
`SF3_1ST.BIN` (New Generation) et `SF3_2ND.BIN` (2nd Impact) — et en tirent ce qu'il faut
pour rejouer leurs trente-quatre décors dans le port : les pages de fond, les objets animés,
les profondeurs, les vitesses de parallaxe.

**Ce dossier ne porte que la méthode.** Les données du jeu n'y sont pas, et n'y seront pas.

## Ce qui n'est pas là, et comment on le retrouve

| Ce qui manque | D'où ça vient |
|---|---|
| `SF3_1ST.BIN`, `SF3_2ND.BIN` | le disque *Street Fighter III — Double Impact* (`cdi.py`) |
| `pvc-2i/`, `pvc-ng/` | les banques de tuiles, extraites du même disque |
| `outils/*.json`, `outils/*.pkl` | des relevés faits **dans** ces binaires (`blocsng.py`, `apparier.py`…) |
| `etages2i-sprites/`, `etagesng-sprites/` | les pages `.tex`, cuites par `couches*.py` et `statiques2i.py` |
| `outils/__cache_decors__/` | le cache de `cache_decors.py` — 879 Mo, rejouable |
| `src/port/video/decor_objets_data.c` | cuit par `animer2i.py` puis `animerng.py` |

C'est la même règle que pour `decor_objets_data.c`, écrite dans le `.gitignore` à la racine :
le dépôt porte le code qui intègre les données de Capcom, jamais les données.

## L'ordre de génération

Il n'est pas commutatif — `animer2i.py` **écrit** le fichier, `animerng.py` y **ajoute** :

```
py -3 animer2i.py --ecrire
py -3 animerng.py --ecrire
```

Les pages de fond :

```
py -3 couches2i.py --ecrire          # les couches de 2nd Impact
py -3 statiques2i.py --ecrire        # les éléments statiques, et Elena 1
py -3 statiques2i.py --variante --ecrire
py -3 couchesng.py --ecrire          # les dix-neuf de New Generation
```

Les tables de plans, qui produisent les `.inc` du port :

```
py -3 etages.py
py -3 etagesng.py --ecrire
```

## Où tout est écrit

**[`DECORS.md`](DECORS.md)** — cinq cent trente-huit kilo-octets, tenu au fil du chantier.
Chaque correction y est datée, avec l'adresse lue dans le binaire, la mesure qui l'a décidée,
et — quand quelque chose est approché — l'approximation nommée avec ses chiffres. C'est là
qu'il faut aller avant de toucher quoi que ce soit ici.

**[`REPRISE.md`](REPRISE.md)** — par où reprendre après une interruption.

## Les chemins

Plusieurs scripts portent encore des chemins absolus vers la machine d'origine
(`C:\Users\frede\Desktop\SF3\…`). Ils sont à reprendre le jour où quelqu'un d'autre s'en
sert ; ils sont signalés par un `RESSOURCES`, un `RACINE` ou un `DEPLOIEMENT` en tête de
fichier.
