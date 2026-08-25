@echo off
rem Inventorie les glyphes que les polices de 3SX savent dessiner, lus dans SF33RD.AFS.
rem Ecrit le compte rendu ici meme et les planches de glyphes dans docs\police\.

cd /d "%~dp0"

python tools\font_inventory.py --png docs\police
if errorlevel 1 goto rate

echo.
echo Compte rendu ci-dessus. Les planches sont dans docs\police\ :
echo   src_han_alpha.png   le latin de base, ce que l'anglais atteint deja
echo   src_han_alpha2.png  les 48 lettres accentuees, dessinees mais inatteignables
echo   menu_grande.png     les grandes lettres des menus
echo   menu_etroite.png    les lettres etroites des menus
echo.
echo Ce que les planches doivent montrer :
echo   1. src_han_alpha2 : des A E I O U et des a e i o u accentues, plus N n et C c.
echo   2. menu_*.png : de l'ASCII et rien d'autre, aucun accent.
echo.
echo Le detail est dans docs\traduction_police.md
pause
goto :eof

:rate
echo.
echo Echec. Si c'est Pillow qui manque : pip install pillow
echo Si c'est SF33RD.AFS : il est attendu dans
echo   %%APPDATA%%\CrowdedStreet\3SX\resources\SF33RD.AFS
pause
