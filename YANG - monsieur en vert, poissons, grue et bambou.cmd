@echo off
rem YANG : le monsieur en vert, les poissons, la grue et le bambou devant. Contient Ibuki et la largeur.
rem A LANCER PAR DOUBLE-CLIC.

setlocal

copy /y "%~dp0build\3sx-yang.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
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
echo   YANG
echo ==========================================================
echo.
echo   1. LE MONSIEUR EN VERT : une seule figure, anime,
echo      entre le rocher sculpte et l'escalier.
echo   2. LES POISSONS : deux, dans l'aquarium de gauche.
echo   3. LA GRUE, a gauche : DEVANT les combattants.
echo   4. LE GRAND BAMBOU, a droite : DEVANT les combattants.
echo   La lanterne, le cabinet et le petit bambou sont aussi
echo   des objets maintenant, a leur place.
echo.
echo   Le cache de tuiles de Yang passe a quatre pages (il
echo   aurait deborde) ; Necro a quatre et Sean a deux, par
echo   precaution.
echo.
echo   Contient aussi Ibuki, la largeur, Sean et Necro.
echo.
pause

3sx.exe > "%~dp0yang-sortie.log" 2>&1

copy /y fin-de-round.log "%~dp0yang-trace.log" >nul

echo.
echo ================= VERIFICATION =================
findstr /c:"etage " "%~dp0yang-trace.log"
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
