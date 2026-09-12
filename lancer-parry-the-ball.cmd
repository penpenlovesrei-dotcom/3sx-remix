@echo off
rem Lance 3SX pour essayer PARRY THE BALL ! dans le menu TRAINING.

cd /d "%~dp0build\application\bin"

echo Lancement de 3SX...
echo.
echo Chemin : TRAINING (menu principal)
echo.
echo Le menu a QUATRE lignes :
echo   NORMAL TRAINING
echo   PARRYING TRAINING
echo   PARRY THE BALL !     avec LVL 1 a LVL 5 a sa droite
echo   EXIT
echo.
echo Gauche/droite sur cette ligne changent le niveau. Cinq et non dix :
echo les cinq autres motifs sont un second jeu, pas la suite de l'echelle.
echo.
echo Croix : on choisit SON personnage seulement. Sean est d'office en
echo face, et l'ecran de choix d'adversaire ne doit plus se montrer.
echo.
echo A LA FIN DE L'ETAPE, le jeu se fige sur un menu :
echo   RETRY      relance l'etape
echo   LEVEL n    gauche/droite change le niveau, Croix relance dessus
echo   EXIT       revient a l'ecran titre
echo.
echo A VERIFIER :
echo   1. L'ecran de choix d'adversaire ne se montre plus du tout.
echo   2. LVL s'arrete a 5, et la difficulte suit le numero.
echo   3. Le menu de fin s'affiche, ses trois lignes repondent.
echo   4. NORMAL TRAINING et PARRYING TRAINING marchent toujours.
echo.

3sx.exe > "%~dp03sx-parry.log" 2>&1

echo.
echo Log : %~dp03sx-parry.log
pause
