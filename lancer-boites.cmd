@echo off
rem Lance 3SX avec art-remix-boxes : les portraits de l'ecran de selection
rem sont remplaces par un rectangle plat, a la place exacte des chips.

cd /d "%~dp0build\application\bin"

echo Lancement de 3SX...
echo.
echo A regarder, sur l'ecran de selection :
echo   - un rectangle plein a la place de chaque grande illustration
echo   - MAGENTA pour un cote, CYAN pour l'autre
echo   - il doit couvrir exactement l'illustration, glisser et sortir comme elle
echo.

3sx.exe > "%~dp03sx-boites.log" 2>&1

echo.
echo Termine. Log : %~dp03sx-boites.log
pause
