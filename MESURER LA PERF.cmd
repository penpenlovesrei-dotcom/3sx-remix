@echo off
rem Mesure CPU / GPU / RAM pendant une partie du fork, et verdict a la fermeture du jeu.
rem A LANCER PAR DOUBLE-CLIC : le jeu ecrit dans %APPDATA% (REPRISE.md, regle 12).
setlocal
title 3SX fork - mesurer la perf

echo ==========================================================
echo   MESURER LA PERF DU FORK
echo ==========================================================
echo.
echo   Lance build\application\bin\3sx.exe, mesure CPU, GPU et RAM
echo   pendant que vous jouez, et donne le facteur limitant quand
echo   vous fermez le jeu. Compare avec la build officielle
echo   (C:\3sx-officiel) et garde un historique des mesures dans
echo   essais\perf\historique.csv.
echo.
echo   AVANT : chargeur branche, application Claude fermee.
echo.
echo   1  le fork tel quel (config actuel)
echo   2  render-scale 1 le temps de la mesure (config remis apres)
echo   3  sans les objets animes (SF3_DECOR_OBJETS=0)
echo   4  render-scale 1 ET sans les objets animes
echo   5  le fork tel quel, en rendu OpenGL
echo   6  render-scale 4, l'ancien reglage (config remis apres)
echo.
choice /c 123456 /n /m "  Votre choix (1-6) : "
set N=%errorlevel%
set ARGS=
if %N%==2 set ARGS=-RenderScale 1
if %N%==3 set ARGS=-SansObjets
if %N%==4 set ARGS=-RenderScale 1 -SansObjets
if %N%==5 set ARGS=-Rendu opengl
if %N%==6 set ARGS=-RenderScale 4

powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0tools\mesurer_perf.ps1" -Build fork %ARGS%
echo.
pause
