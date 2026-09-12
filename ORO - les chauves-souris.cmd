@echo off
rem La menagerie d'Oro : le premier morceau retrouve, en remontant le graphe d'appels.

cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   LES CHAUVES-SOURIS D'ORO
echo ==========================================================
echo.
echo   Sa menagerie etait le plus vieux trou du chantier : le
echo   catalogue des betes est etabli depuis des jours -- chats,
echo   chatons, perroquet, chien, chauves-souris -- mais AUCUN
echo   bloc ne les portait, et trois enregistrements essayes au
echo   jugé avaient ete rejetes a l'ecran.
echo.
echo   En voici quatre, et cette fois ce n'est pas un pari.
echo.
echo ----------------------------------------------------------
echo   COMMENT ELLES ONT ETE TROUVEES
echo ----------------------------------------------------------
echo.
echo   Toutes les recherches passees DESCENDAIENT depuis les
echo   scripts d'etage. Ce spawner n'est atteint par aucun
echo   chemin descendant.
echo.
echo   outils/remonter2i.py fait l'inverse, et c'est exact : une
echo   fonction n'est atteignable que si son adresse apparait
echo   quelque part -- comme litteral, ou DANS UNE TABLE DE
echo   POINTEURS. On part de la cible et on remonte jusqu'a
echo   tomber dans une routine d'etage.
echo.
echo   Douze spawners sur trente-deux sont ainsi atteints, la ou
echo   la descente n'en voyait que quatre.
echo.
echo ----------------------------------------------------------
echo   DEUX CHEMINS INDEPENDANTS DISENT « ORO »
echo ----------------------------------------------------------
echo.
echo   1. l'appelant : la BANDE 10, qui est le decor 9, Oro ;
echo   2. le spawner porte EN DUR la table de scripts
echo      0x8C12AB8C -- et c'est celle du decor 9.
echo.
echo   Ni l'un ni l'autre n'a servi a caler l'autre.
echo.
echo   Le script vient de la ROUTINE, pas du bloc : elle recopie
echo   quatre pointeurs sur la pile et les indexe par le `type`
echo   de l'objet, qui est le rang de l'enregistrement. Les
echo   quatre routines posent les scripts 35, 34, 34 et 34.
echo.
echo   Et le catalogue de la menagerie, etabli par les sprites
echo   eux-memes, donne les scripts 32 a 39 aux CHAUVES-SOURIS.
echo.
echo   Elles sont en 567/288, 396/320, 502/337 et 535/313 --
echo   HAUT dans la grotte. La routine ecrit leur position a
echo   chaque trame : elles se deplacent. On les pose a leur
echo   position de depart, comme partout ailleurs.
echo.
echo ----------------------------------------------------------
echo   CE QUE JE N'AJOUTE PAS, ET POURQUOI
echo ----------------------------------------------------------
echo.
echo   La remontee donne aussi un spawner a YUN (id 21, trois
echo   enregistrements, scripts 0, 2 et 4). Ses champs
echo   RESSEMBLENT a des positions -- 696/64, 752/84, 752/63 --
echo   mais sa routine ecrit +84 et +86 et se contente de LIRE
echo   +102 et +106. Autrement dit ces objets n'ont pas de
echo   position a eux : elle vient d'ailleurs. Les poser aux
echo   valeurs qui « ressemblent » serait un pari, et j'en ai
echo   deja fait trois sur cette menagerie. Je le laisse ecrit
echo   dans le document, pas dans le jeu.
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER
echo ==========================================================
echo.
echo   ORO (etage 31) est le SEUL decor qui change. Il passe de
echo   huit objets a douze.
echo.
echo     a. Vois-tu quatre petites figures HAUT dans la grotte,
echo        au-dessus de la vasque et des chutes ?
echo     b. Est-ce que ce sont des chauves-souris ?
echo     c. Leurs couleurs : elles emploient les palettes 79 et
echo        80 du bloc, sur la banque des BETES (base 1674).
echo        Fauves comme les chats, ou fausses ?
echo     d. Trois d'entre elles jouent la meme animation. Si tu
echo        n'en vois qu'une seule, dis-le -- ce serait la
echo        deduplication qui aurait mange les autres.
echo.
echo   TOUS LES AUTRES doivent etre identiques. Ses chats, son
echo   perroquet et son chien restent introuvables : ce sont les
echo   scripts 13, 16-19, 20-26 et 27-31, et aucun bloc ne les
echo   porte encore.
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe tous les objets
echo   animes sans toucher au decor.
echo.
pause

3sx.exe > "%~dp03sx-oro.log" 2>&1

echo.
echo ================= LES JOURNAUX =================
for %%F in (decor-objets.log fin-de-round.log fatal.log) do (
  if exist "%%F" (
    echo.
    echo ----- %%F -----
    type "%%F"
  )
)
echo.
echo ----- sortie du jeu -----
type "%~dp03sx-oro.log"
echo.
pause
