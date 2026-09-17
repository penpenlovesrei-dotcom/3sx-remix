@echo off
rem PREMIER EXE COMPILE SUR CETTE MACHINE : l'essai des couleurs + trois corrections.

copy /y "%~dp0build\3sx-15-09.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
if errorlevel 1 (
  echo   ECHEC : une instance du jeu verrouille le fichier.
  pause
  exit /b 1
)
cd /d "%~dp0build\application\bin"
set SF3_DECOR_OBJETS=
if exist fatal.log move /y fatal.log fatal-precedent.log >nul

echo ==========================================================
echo   LA LENTEUR CORRIGEE - exe compile le 15/09
echo ==========================================================
echo.
echo   Compile ici, pour la premiere fois, avec clang 22. C'est
echo   l'essai des couleurs du 06/09 avec exactement trois
echo   corrections, rien d'autre :
echo.
echo   1. ELENA noire      : table des plans reels completee
echo   2. HUGO qui figeait : cache des sprites de 2 a 4 pages
echo   3. LA LENTEUR       : chaque sprite renvoyait sa palette a
echo      la carte graphique a chaque image. Il ne l'envoie plus
echo      qu'a son apparition, ou si elle change.
echo.
echo   Sprites animes ACTIFS.
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER - en Versus, 2nd Impact
echo ==========================================================
echo.
echo     YUN STAGE et YANG STAGE : plus lents, ET couleurs des
echo                               sprites justes
echo     RYU, NECRO, HUGO, IBUKI, ORO, AKUMA STAGE :
echo                               etaient lents, ne doivent plus
echo     HUGO STAGE  : ne doit pas figer
echo     ELENA STAGE : le decor doit s'afficher
echo.
pause

3sx.exe > "%~dp0essai-15-09-sortie.log" 2>&1

copy /y fin-de-round.log "%~dp0essai-15-09-trace.log" >nul
copy /y decor-objets.log "%~dp0essai-15-09-objets.log" >nul

echo.
echo ================= VERIFICATION =================
findstr /c:"objets animes permis" "%~dp0essai-15-09-objets.log"
echo.
findstr /c:"etage " "%~dp0essai-15-09-trace.log"
echo.
if exist fatal.log (
  echo ----- fatal.log : LE JEU A FIGE -----
  type fatal.log
) else (
  echo   Pas de fatal.log : aucun blocage.
)
echo.
pause
