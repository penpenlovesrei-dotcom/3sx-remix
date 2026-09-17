@echo off
rem YANG : les deux poissons nagent. YUN : quatre oiseaux dans les cages.
rem A LANCER PAR DOUBLE-CLIC.

setlocal

copy /y "%~dp0build\3sx-poissons.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
if errorlevel 1 (
  echo   ECHEC de la copie : le jeu tourne-t-il encore ?
  pause
  exit /b 1
)

cd /d "%~dp0build\application\bin"
set SF3_DECOR_OBJETS=
set SF3_DECOR_Z=
set SF3_DECOR_VARIANTE=
if exist jalons.on del jalons.on
if exist fatal.log move /y fatal.log fatal-precedent.log >nul

echo ==========================================================
echo   YANG ET YUN
echo ==========================================================
echo.
echo   YANG - l'aquarium
echo   1. Le poisson ROUGE fait des allers-retours a mi-hauteur,
echo      avec un demi-tour a chaque bout.
echo   2. Le poisson NOIR fait le tour de l'aquarium : il nage
echo      dans le haut (droite, gauche, droite), tourne, plonge
echo      vers les rochers, file a gauche au fond, puis remonte.
echo      Un tour complet dure environ 35 secondes.
echo      Les deux s'arretent pendant la pause.
echo.
echo   YUN - les cages
echo   3. QUATRE oiseaux perches au lieu d'un : deux dans la
echo      cage carree, un dans chaque etage de la cage ronde.
echo      Ils sont dessines ajoures : les barreaux passent devant.
echo.
echo   ORO - le chien doit se comporter comme avant (ses images
echo   sont maintenant rangees autrement).
echo.
echo   Joue un match chez Yang (reste au moins 40 secondes), un
echo   chez Yun, puis quitte le jeu.
echo.
pause

3sx.exe > "%~dp0yang-yun-sortie.log" 2>&1

copy /y fin-de-round.log "%~dp0yang-yun-trace.log" >nul

echo.
echo ================= VERIFICATION =================
findstr /c:"etage " /c:"variante" "%~dp0yang-yun-trace.log"
echo.
if exist fatal.log (
  echo ----- fatal.log : LE JEU A FIGE -----
  type fatal.log
) else (
  echo   Pas de fatal.log : aucun blocage.
)
echo.
pause
exit /b 0
