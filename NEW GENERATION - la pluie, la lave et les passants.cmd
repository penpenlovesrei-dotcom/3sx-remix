@echo off
rem NEW GENERATION : la pluie, la lave, les personnages du decor, et Yun jouable.
rem A LANCER PAR DOUBLE-CLIC.

setlocal

copy /y "%~dp0build\3sx-ng-vivant.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
if errorlevel 1 (
  echo   ECHEC de la copie : le jeu tourne-t-il encore ?
  pause
  exit /b 1
)

set SRC=C:\Users\frede\OneDrive\Bureau\SEPTEMBRE\SF3\CrowdedStreet-3SX\resources
set DST=%APPDATA%\CrowdedStreet\3SX\resources
for %%S in (37 38 39 40 41 42 43 44 45 46 47 48 49 50 51 52 53 54 55) do (
  robocopy "%SRC%\tex_remix\stage%%S" "%DST%\tex_remix\stage%%S" *.tex /R:1 /W:1 /NFL /NDL /NP /NJH /NJS >nul
  if errorlevel 8 (
    echo   ECHEC de la copie des pages.
    pause
    exit /b 1
  )
)
robocopy "%SRC%\stages" "%DST%\stages" 1550.bin 1551.bin 1557.bin /R:1 /W:1 /NFL /NDL /NP /NJH /NJS >nul
if errorlevel 8 (
  echo   ECHEC de la copie des archives d'etage.
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
echo   NEW GENERATION - LA PLUIE, LA LAVE ET LES PASSANTS
echo ==========================================================
echo.
echo   1. YUN 1 et YUN 2 : les joueurs repondent. Leurs etages
echo      lisaient les entrees des STAGES BONUS, hors bornes.
echo   2. DUDLEY 1 : la pluie tombe (huit vues, quatorze
echo      motifs d'intensite) et la caleche passe dans le
echo      tunnel de droite.
echo   3. GILL : l'horizon de lave est anime en entier.
echo   4. LES PASSANTS DU DECOR : Hong Kong (Yun 1, Yang 1),
echo      Necro (le conducteur), Hugo, Ryu, Ken, Oro.
echo   5. IBUKI 1 et 2 : le maitre, le colosse, le garcon et
echo      le ninja perche.
echo   6. DUDLEY 2 : les deux punks qui manquaient.
echo   7. ALEX : l'arriere de la voiture, dans le tunnel.
echo   8. SEAN : les immeubles de New York, le reflet dans la
echo      flaque, les deux costauds ; le motard de trop est
echo      revenu a cote de sa moto.
echo   9. YANG 2 et YUN 2 : le monsieur en vert.
echo  10. ELENA 1 : les cordes du pont (tendues), l'eau qui
echo      coule, l'oiseau pose.
echo.
echo   Joue-les, puis quitte le jeu.
echo.
pause

3sx.exe > "%~dp0ng4-sortie.log" 2>&1

copy /y fin-de-round.log "%~dp0ng4-trace.log" >nul

echo.
echo ================= VERIFICATION =================
findstr /c:"entree en round" /c:"combat, etage" "%~dp0ng4-trace.log"
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
