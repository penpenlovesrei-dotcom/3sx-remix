@echo off
rem Lance 3SX pour essayer PARRY THE BALL ! dans le menu TRAINING.

cd /d "%~dp0build\application\bin"

echo Lancement de 3SX...
echo.
echo Chemin : TRAINING (menu principal)
echo.
echo Le menu doit avoir QUATRE lignes au lieu de trois :
echo   NORMAL TRAINING
echo   PARRYING TRAINING
echo   PARRY THE BALL !     avec LVL 1 a LVL 10 a sa droite
echo   EXIT
echo.
echo Sur la ligne PARRY THE BALL, GAUCHE et DROITE changent le niveau.
echo L1 a L5 sont un jeu de trajectoires, L6 a L10 l'autre - c'est la
echo numerotation du jeu lui-meme.
echo.
echo Croix : on choisit SON personnage seulement. Le joueur 2 se
echo valide tout seul sur Sean, qui est celui qui lance les ballons.
echo.
echo A LA FIN DE L'ETAPE, le jeu se fige sur un petit menu :
echo   RETRY      relance l'etape
echo   LEVEL nn   gauche/droite change le niveau, Croix relance dessus
echo   EXIT       laisse le mode arcade reprendre son cours
echo.
echo A VERIFIER EN PRIORITE - c'est la premiere fois que je touche a
echo la machine a etats du jeu, et je ne peux pas y jouer :
echo   1. Les quatre lignes s'affichent sans se chevaucher, et le
echo      point d'exclamation se dessine (aucune autre chaine du menu
echo      n'en contient, donc la police n'est pas garantie).
echo   2. Le niveau change bien avec gauche/droite.
echo   3. Le bonus stage se lance - le plantage venait d'une double
echo      requete de chargement pour le joueur 2 - et se termine.
echo   4. NORMAL TRAINING et PARRYING TRAINING marchent toujours.
echo.

3sx.exe > "%~dp03sx-parry.log" 2>&1

echo.
echo --- ce que la sonde a vu ---
findstr /C:"[ball]" "%~dp03sx-parry.log"
echo ----------------------------
echo.
echo Log : %~dp03sx-parry.log
pause
