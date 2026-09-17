@echo off
rem Les plans reculent de 16, les cascades avec eux : Yun garde sa correction, Oro retrouve ses chutes.

copy /y "%~dp0build\3sx-plans-16.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
if errorlevel 1 (
  echo   ECHEC : une instance du jeu verrouille le fichier.
  pause
  exit /b 1
)
cd /d "%~dp0build\application\bin"
set SF3_DECOR_OBJETS=
set SF3_DECOR_Z=
if exist fatal.log move /y fatal.log fatal-precedent.log >nul

echo ==========================================================
echo   LES PLANS DERRIERE, LES CASCADES A LEUR PLACE
echo ==========================================================
echo.
echo   L'essai precedent mettait TOUS les sprites devant les
echo   plans. C'etait juste pour Yun, faux pour les chutes d'eau
echo   d'Oro. Or les cascades sont les SEULS sprites de 2nd
echo   Impact poses sur un plan lointain :
echo      Ibuki, Oro, Akuma.
echo.
echo   Correction : les plans reculent de 16, et les cascades
echo   reculent de 16 avec eux. Elles retrouvent exactement leur
echo   place d'avant ; les autres sprites passent devant, comme
echo   chez Yun.
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER - en Versus, 2nd Impact
echo ==========================================================
echo.
echo     ORO   : les chutes d'eau reviennent sur le bon plan.
echo     IBUKI et AKUMA : leurs cascades n'ont pas bouge.
echo     YUN   : les sprites de droite restent visibles.
echo.
echo     Si tu as le temps : GILL, ALEX, DUDLEY, HUGO, KEN,
echo     URIEN doivent rester OK.
echo.
pause

3sx.exe > "%~dp0plans-16-sortie.log" 2>&1

copy /y fin-de-round.log "%~dp0plans-16-trace.log" >nul

echo.
echo ================= VERIFICATION =================
findstr /c:"etage " "%~dp0plans-16-trace.log"
echo.
if exist fatal.log (
  echo ----- fatal.log : LE JEU A FIGE -----
  type fatal.log
) else (
  echo   Pas de fatal.log : aucun blocage.
)
echo.
pause
