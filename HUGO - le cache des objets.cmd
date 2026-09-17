@echo off
rem HUGO (2nd Impact) figeait le jeu : cache des objets trop petit.

echo ==========================================================
echo   DEPLOIEMENT DE L'EXE CORRIGE
echo ==========================================================
echo.
copy /y "%~dp0build\3sx-hugo-cache.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
if errorlevel 1 (
  echo   ECHEC : une instance du jeu verrouille le fichier.
  pause
  exit /b 1
)
echo   exe deploye : build\3sx-hugo-cache.exe
echo   Il garde la correction d'Elena. L'original du 06/09 reste
echo   intact dans build\3sx.exe.
echo.
cd /d "%~dp0build\application\bin"
if exist fatal.log move /y fatal.log fatal-precedent.log >nul

echo ==========================================================
echo   CE QUI A CHANGE
echo ==========================================================
echo.
echo   Le decor d'HUGO porte 16 objets animes. Au pire, 556
echo   morceaux restent en memoire a la fois ; son cache en
echo   tenait 512. A 108 %%, le jeu se figeait :
echo      "le cache CG est plein" ^(fatal.log^)
echo.
echo   Cache passe de 2 a 4 pages : 54 %%, comme Ibuki, Oro et
echo   Akuma. Hugo etait le SEUL decor de 2nd Impact au-dessus
echo   de 100 %%. Rien d'autre ne change.
echo.
echo ==========================================================
echo   DEUX FACONS DE LANCER
echo ==========================================================
echo.
echo   1 = NORMAL
echo       HUGO STAGE (2nd Impact) : ne doit plus figer.
echo.
echo   2 = OBJETS ANIMES COUPES  (pour la lenteur)
echo       Aller sur YANG STAGE et YUN STAGE (2nd Impact),
echo       les plus lents. Si la lenteur disparait, ce sont
echo       nos objets animes qui la causent. Sinon, non.
echo.
choice /c 12 /m "Mode"
set MODE=%errorlevel%
set SF3_DECOR_OBJETS=
if "%MODE%"=="2" (
  set SF3_DECOR_OBJETS=0
  echo.
  echo   Objets animes COUPES pour ce lancement.
)
echo.
pause

3sx.exe > "%~dp0hugo-sortie.log" 2>&1

copy /y fin-de-round.log "%~dp0hugo-trace.log" >nul

echo.
echo ================= LES ETAGES JOUES =================
findstr /c:"etage " "%~dp0hugo-trace.log"
echo.
if exist fatal.log (
  echo ----- fatal.log : LE JEU A FIGE -----
  type fatal.log
) else (
  echo   Pas de fatal.log : aucun blocage.
)
echo.
pause
