@echo off
rem SEAN et ORO : decor remonte, ligne noire et pixels blancs ; bloc de pierre, perroquet. Mesure de la vitesse.
rem A LANCER PAR DOUBLE-CLIC.

setlocal

copy /y "%~dp0build\3sx-sean-oro.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
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
if exist jalons.on del jalons.on
if exist fatal.log move /y fatal.log fatal-precedent.log >nul

echo ==========================================================
echo   SEAN ET ORO
echo ==========================================================
echo.
echo   SEAN
echo   1. Tout le decor REMONTE de 16 lignes (la page et ses
echo      personnages ensemble).
echo   2. Plus de colonne noire dans le pare-brise de la voiture
echo      jaune, plus de pixels blancs au pied de la table.
echo.
echo   ORO
echo   3. Le BLOC DE PIERRE du mur de la grotte est anime.
echo   4. Le PERROQUET : tete verte, face orange, aile bleue.
echo   5. Le chien : absent dans UNE des quatre variantes du
echo      decor (chat et chatons sans chien), comme dans 2I.
echo      Le journal dira laquelle est sortie.
echo.
echo   LA VITESSE : aucune sonde n'etait armee. Le journal note
echo   maintenant, chaque seconde, le temps reel et le temps de
echo   calcul des images. Joue normalement, puis quitte le jeu.
echo.
pause

3sx.exe > "%~dp0sean-oro-sortie.log" 2>&1

copy /y fin-de-round.log "%~dp0sean-oro-trace.log" >nul

echo.
echo ================= VERIFICATION =================
findstr /c:"etage " /c:"variante" "%~dp0sean-oro-trace.log"
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
