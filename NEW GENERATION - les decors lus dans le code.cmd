@echo off
rem NEW GENERATION : les decors recomposes comme le Dreamcast les dessine (listes de rectangles).
rem A LANCER PAR DOUBLE-CLIC.

setlocal

copy /y "%~dp0build\3sx-ng-descripteurs.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
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
robocopy "%SRC%\stages" "%DST%\stages" 1551.bin /R:1 /W:1 /NFL /NDL /NP /NJH /NJS >nul
if errorlevel 8 (
  echo   ECHEC de la copie de l'archive d'Alex.
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
echo   NEW GENERATION - LES DECORS LUS DANS LE CODE
echo ==========================================================
echo.
echo   Le Dreamcast ne dessine pas les banques telles quelles :
echo   il pose des RECTANGLES pris dedans. Toutes les pages de
echo   NG sont refaites ainsi.
echo.
echo   1. IBUKI 1, 2, 3 : decor entier recompose. Cascade
echo      animee, lanternes, vent dans les bambous.
echo   2. ELENA 2 : cascade animee, pont en planches.
echo   3. ELENA 1 : le PONT (objet), les cordes a crane, l'eau
echo      de la riviere. Le ciel defile lentement.
echo   4. DUDLEY 1 : la rue, le ciel de nuit, la pluie devant
echo      les combattants (fixe pour l'instant).
echo   5. ALEX : un troisieme plan, le ciel du fond.
echo   6. GILL : l'horizon anime, raccorde au sol.
echo   7. RYU : cascade et fond animes. KEN, ORO, YUN, YANG :
echo      le ciel complet (la moitie droite manquait).
echo   8. PARTOUT : plus de bandes verticales aux bords.
echo   9. NECRO : les montagnes defilent derriere les vitres.
echo.
echo   YUN 1 et YUN 2 : joue-les, le journal dira pourquoi les
echo   joueurs ne bougent pas.
echo.
echo   Joue les decors ci-dessus, puis quitte le jeu.
echo.
pause

3sx.exe > "%~dp0ng3-sortie.log" 2>&1

copy /y fin-de-round.log "%~dp0ng3-trace.log" >nul

echo.
echo ================= VERIFICATION =================
findstr /c:"entree en round" /c:"combat, etage" "%~dp0ng3-trace.log"
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
