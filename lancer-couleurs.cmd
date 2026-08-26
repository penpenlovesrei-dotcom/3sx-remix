@echo off
rem Lance 3SX apres la remontee des 27 commits d'amont.
rem Les tables de menu ont ete realignees : c'est ce qu'il faut verifier.

cd /d "%~dp0build\application\bin"

echo Lancement de 3SX...
echo.
echo A VERIFIER EN PRIORITE - un decalage de table donne un libelle
echo faux, jamais un plantage, donc seul l'oeil peut le voir :
echo.
echo   1. Options ^> Display : les huit lignes portent leur nom
echo      (SCREEN ADJUST, RESOLUTION, CHAR. COLOR, BACKGROUNDS,
echo       HUD, ARTWORKS, COLOR EDIT, EXIT) et leurs valeurs.
echo   2. COLOR EDIT ^> un personnage : le NOM du personnage est le bon,
echo      les captions R G B sont R G B, les lignes COLOR et SAVE
echo      portent leurs valeurs.
echo   3. Options ^> Sound : les rangees et leurs valeurs, la ligne
echo      BGM TYPE, et EXIT qui sort bien.
echo   4. Les ecrans Custom (musiques, decors, couleurs) s'ouvrent
echo      depuis les bonnes lignes.
echo   5. L'amont a ajoute un selecteur de LANGUE : voir ou il est.
echo.

3sx.exe > "%~dp03sx-couleurs.log" 2>&1

echo.
echo Log : %~dp03sx-couleurs.log
pause
