@echo off
rem L'ordre de dessin et la profondeur sortent maintenant de +556, lu dans le binaire.

echo ==========================================================
echo   DEPLOIEMENT DE L'EXE
echo ==========================================================
echo.
copy /y "%~dp0build\3sx.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
if errorlevel 1 (
  echo   ECHEC : une instance du jeu verrouille le fichier.
  pause
  exit /b 1
)
for %%F in ("%~dp0build\application\bin\3sx.exe") do echo   exe deploye, %%~tF
echo.

cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   L'ORDRE DE DESSIN VIENT DE +556, PLUS DE MOI
echo ==========================================================
echo.
echo   Tu avais raison sur les deux points, et la donnee existait
echo   dans le binaire : `+556 my_priority`, qui vaut le numero
echo   de palette. Voici Yun, du plus loin au plus pres :
echo.
echo      95  script 5      86  script 17     76  script 26
echo      93  script 6      85  script 20     75  script 33
echo      93  script 4      80  script 28     74  script 2
echo      92  script 27     77  script 22     23  script 0
echo      91  script 24     77  script 16
echo      90  script 7      76  script 31
echo.
echo   1. L'ETAL DEVANT LES CAGES. Les paniers sont a 93, les
echo      cages a 90 : LES CAGES SONT PLUS PRES. Les fiches sont
echo      maintenant triees par priorite DECROISSANTE, donc les
echo      cages se dessinent apres les paniers, et par-dessus.
echo.
echo   2. LE PANNEAU DEVANT LES COMBATTANTS. Sa priorite est 23,
echo      et `char_init_data2` donne aux combattants un my_pr de
echo      28 a 56. 23 est plus petit, donc plus pres : il passe
echo      devant eux. Je lui donne z=23, la valeur du binaire.
echo.
echo   LA REGLE QUE J'APPLIQUE, ET SA LIMITE. En dessous de 80,
echo   je reporte la priorite telle quelle : un z plus petit est
echo   plus pres, il ne peut RIEN cacher. Au-dessus de 80, je ne
echo   la reporte pas -- nos plans de fond sont a 84, 90 et 94,
echo   et un objet a 90 passerait derriere eux et disparaitrait.
echo   C'est l'erreur qui avait vide le decor. Ceux-la gardent la
echo   profondeur du modele, et c'est l'ORDRE des fiches qui les
echo   departage.
echo.
echo ----------------------------------------------------------
echo   LES OISEAUX : CE QUE J'AI TROUVE, ET CE QUI MANQUE
echo ----------------------------------------------------------
echo.
echo   LA CAGE EST VIDE. Je l'ai rendue a 6x : le script 7, ce
echo   sont trois cages en osier, et il n'y a AUCUN oiseau
echo   dedans. Ils sont donc un objet a part.
echo.
echo   LEURS SPRITES EXISTENT : scripts 37 (un oiseau en vol, 2
echo   images), 42 (4 images) et 44 (8 images).
echo.
echo   ET VOICI OU JE BUTE, honnetement :
echo     - aucun chargeur de Yun ne pose 37, 42 ni 44 ;
echo     - la ROUTINE des cages (8C0291EC) ne cree aucun oiseau :
echo       j'ai suivi ses appels sur trois niveaux ;
echo     - deux routines de la table des 196 posent 42 et 44 --
echo       les index 82 et 97 -- mais je n'ai pas etabli qu'elles
echo       appartiennent a Yun. Le numero de script est PROPRE A
echo       CHAQUE DECOR, donc « script 42 » chez un autre decor
echo       est un autre sprite.
echo.
echo   Je ne comblerai pas ce trou par une supposition.
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER
echo ==========================================================
echo.
echo     a. Les cages passent-elles devant les paniers ?
echo     b. Le panneau vertical est-il devant les combattants ?
echo     c. Le vieil homme (75), la dame (76) et la charrette
echo        (74) sont-ils au bon plan les uns par rapport aux
echo        autres ?
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe les objets.
echo.
pause

3sx.exe > "%~dp03sx-prof.log" 2>&1

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
type "%~dp03sx-prof.log"
echo.
pause
