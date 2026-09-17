@echo off
rem IBUKI : une seule cascade, a sa hauteur ; le temple au fond a droite ; les lanternes. Contient Yang, la largeur, Sean et Necro.
rem A LANCER PAR DOUBLE-CLIC.

setlocal

copy /y "%~dp0build\3sx-ibuki2.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
if errorlevel 1 (
  echo   ECHEC de la copie : le jeu tourne-t-il encore ?
  pause
  exit /b 1
)

set SRC=C:\Users\frede\OneDrive\Bureau\SEPTEMBRE\SF3\CrowdedStreet-3SX\resources
set DST=%APPDATA%\CrowdedStreet\3SX\resources
for %%S in (27 29 31 32 34) do (
  robocopy "%SRC%\tex_remix\stage%%S" "%DST%\tex_remix\stage%%S" *.tex /R:1 /W:1 /NFL /NDL /NP /NJH /NJS >nul
  if errorlevel 8 (
    echo   ECHEC de la copie des pages.
    pause
    exit /b 1
  )
)

cd /d "%~dp0build\application\bin"
set SF3_DECOR_OBJETS=
set SF3_DECOR_Z=
set SF3_DECOR_VARIANTE=
if exist fatal.log move /y fatal.log fatal-precedent.log >nul

echo ==========================================================
echo   IBUKI
echo ==========================================================
echo.
echo   1. UNE SEULE CASCADE, a gauche, animee, et plus haute
echo      qu'avant (80 lignes).
echo   2. PLUS DE CASCADE A DROITE : a sa place, au fond, la
echo      montagne et le TEMPLE.
echo   3. LE CIEL a sa place d'origine.
echo   4. LES LANTERNES de la cabane, a gauche, scintillent.
echo.
echo   Contient aussi Yang, la largeur, Sean et Necro.
echo.
pause

3sx.exe > "%~dp0ibuki-sortie.log" 2>&1

copy /y fin-de-round.log "%~dp0ibuki-trace.log" >nul

echo.
echo ================= VERIFICATION =================
findstr /c:"etage " "%~dp0ibuki-trace.log"
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
