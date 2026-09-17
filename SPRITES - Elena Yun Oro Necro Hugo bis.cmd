@echo off
rem LES SPRITES DE 2ND IMPACT : Elena 1, Yun, Oro, Necro, Hugo bis.
rem A LANCER PAR DOUBLE-CLIC : il copie des pages dans le VRAI %APPDATA%.

setlocal
set SRC=C:\Users\frede\OneDrive\Bureau\SEPTEMBRE\SF3\CrowdedStreet-3SX\resources
set DST=%APPDATA%\CrowdedStreet\3SX\resources

copy /y "%~dp0build\3sx-sprites.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
if errorlevel 1 (
  echo   ECHEC : une instance du jeu verrouille le fichier.
  pause
  exit /b 1
)

for %%S in (27 30 31 56 57) do (
  robocopy "%SRC%\tex_remix\stage%%S" "%DST%\tex_remix\stage%%S" *.tex /R:1 /W:1 /NFL /NDL /NP /NJH /NJS >nul
  if errorlevel 8 goto echec
)
robocopy "%SRC%\stages" "%DST%\stages" 1569.bin /R:1 /W:1 /NFL /NDL /NP /NJH /NJS >nul
if errorlevel 8 goto echec

cd /d "%~dp0build\application\bin"
set SF3_DECOR_OBJETS=
set SF3_DECOR_Z=
set SF3_DECOR_VARIANTE=
if exist fatal.log move /y fatal.log fatal-precedent.log >nul

echo ==========================================================
echo   LES SPRITES DE 2ND IMPACT
echo ==========================================================
echo.
echo   A TESTER, en Versus :
echo.
echo     ELENA STAGE     la cascade : plus de trame decalee
echo     YUN STAGE       plus de charrette sur la foule
echo                     (un petit oiseau a sa place, en 712)
echo     ORO STAGE       un seul chien, plus de bloc de pierre
echo     NECRO STAGE     la dame en blouse blanche, peau rose ;
echo                     calmar et pieuvre violets DANS les bocaux ;
echo                     plus de copie de la dame ;
echo                     les chaines de gauche DEVANT les combattants
echo     2ND IMPACT BG10 (Hugo bis) : ses sprites sont la
echo.
echo   YANG et SEAN ne changent pas encore (sauf la couleur de
echo   la femme a l'eventail chez Yang).
echo.
pause

3sx.exe > "%~dp0sprites-sortie.log" 2>&1

copy /y fin-de-round.log "%~dp0sprites-trace.log" >nul

echo.
echo ================= VERIFICATION =================
findstr /c:"etage " "%~dp0sprites-trace.log"
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

:echec
echo   ECHEC de la copie.
pause
exit /b 1
