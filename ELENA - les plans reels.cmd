@echo off
rem ELENA NOIRE : use_real_scr oubliait les etages 56 et 57.

echo ==========================================================
echo   DEPLOIEMENT DE L'EXE CORRIGE
echo ==========================================================
echo.
copy /y "%~dp0build\3sx-plans-reels.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
if errorlevel 1 (
  echo   ECHEC : une instance du jeu verrouille le fichier.
  pause
  exit /b 1
)
echo   exe deploye : build\3sx-plans-reels.exe
echo   ^(l'original du 06/09 reste intact dans build\3sx.exe^)
echo.
cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   CE QUI A CHANGE : DEUX OCTETS
echo ==========================================================
echo.
echo   La trace disait, sur ELENA STAGE :
echo      etage 30, aire 0 -^> bg_index 56
echo      plans 2, plans reels 0
echo.
echo   Zero plan reel = rien de dessine = ecran noir.
echo.
echo   La table use_real_scr s'arretait a l'etage 55 : ses
echo   cases 56 et 57 valaient 0. use_scr, sa jumelle, les
echo   avait. Et l'aire 0 d'Elena lit justement la case 56.
echo.
echo   Corrige dans la source (bg_data.c) et dans l'exe.
echo   Rien d'autre ne change.
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER - en Versus
echo ==========================================================
echo.
echo     a. ELENA, 2nd Impact : le decor doit s'afficher.
echo        Puis l'objet au centre, en bas.
echo     b. ELENA, 2nd Impact, 2e variante : noire aussi avant.
echo        Avant-dernier etage de la liste, apres NG YANG 2.
echo     c. HUGO, 2nd Impact, 2e variante : noire aussi avant.
echo        Dernier etage de la liste.
echo.
echo   Tout le reste doit etre identique a avant.
echo.
pause

3sx.exe > "%~dp0plans-reels-sortie.log" 2>&1

copy /y fin-de-round.log "%~dp0plans-reels-trace.log" >nul

echo.
echo ================= LA TRACE =================
findstr /c:"etage " /c:"plans " "%~dp0plans-reels-trace.log"
if exist fatal.log (
  echo.
  echo ----- fatal.log -----
  type fatal.log
)
echo.
echo   Attendu : "plans reels 2" partout ou il y avait 0.
echo.
pause
