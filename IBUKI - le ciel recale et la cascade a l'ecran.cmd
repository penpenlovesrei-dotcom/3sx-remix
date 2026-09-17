@echo off
rem IBUKI : le ciel recale et la cascade animee a l'ecran. Contient aussi la largeur.
rem A LANCER PAR DOUBLE-CLIC.

setlocal

copy /y "%~dp0build\3sx-ibuki.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
if errorlevel 1 (
  echo   ECHEC de la copie : le jeu tourne-t-il encore ?
  pause
  exit /b 1
)

set SRC=C:\Users\frede\OneDrive\Bureau\SEPTEMBRE\SF3\CrowdedStreet-3SX\resources
set DST=%APPDATA%\CrowdedStreet\3SX\resources
for %%S in (27 29 31 34) do (
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
echo   1. LES COINS NOIRS. Le plan du ciel etait cale 128
echo      colonnes trop a gauche : aux bornes de la camera,
echo      aucun plan ne peignait certains coins. Recale, il
echo      n'en reste aucun, a aucune position.
echo.
echo   2. LA CASCADE ANIMEE. On animait la vue de GAUCHE de
echo      la reserve, presque toujours hors champ ; c'est
echo      maintenant celle du CENTRE, qui est toujours a
echo      l'ecran. Elle doit bouger quelle que soit la camera.
echo.
echo   A REGARDER : va aux deux bouts du decor, et regarde
echo   la cascade derriere le temple.
echo.
echo   Tout le reste (largeur, Sean, Necro) est inchange depuis
echo   le dernier lanceur.
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
