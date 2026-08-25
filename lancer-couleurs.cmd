@echo off
rem Lance 3SX : choix de palette sur l'ecran de selection.

cd /d "%~dp0build\application\bin"

echo Lancement de 3SX...
echo.
echo Options ^> Display ^> CHAR. COLOR :
echo   Disabled / Custom / Start Button
echo.
echo Sur l'ecran de selection, en mode Start Button, START fait defiler :
echo   3RD STRIKE - NEW GENERATION - 2ND IMPACT - CUSTOM - COLOR EDIT
echo COLOR EDIT est a moitie eteint : il n'est pas encore selectionnable.
echo.
echo Placement : seul, P1 est en BAS A GAUCHE. A deux, P1 passe en
echo HAUT A GAUCHE et P2 s'affiche en BAS A DROITE.
echo.

3sx.exe > "%~dp03sx-couleurs.log" 2>&1

echo.
echo Termine. Log : %~dp03sx-couleurs.log
pause
