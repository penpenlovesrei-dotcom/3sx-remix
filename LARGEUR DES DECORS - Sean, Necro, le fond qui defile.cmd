@echo off
rem LA LARGEUR DES DECORS, les doubles de Sean, le fond de Necro qui defile.
rem A LANCER PAR DOUBLE-CLIC.

setlocal

copy /y "%~dp0build\3sx-largeur.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
if errorlevel 1 (
  echo   ECHEC de la copie : le jeu tourne-t-il encore ?
  pause
  exit /b 1
)

set SRC=C:\Users\frede\OneDrive\Bureau\SEPTEMBRE\SF3\CrowdedStreet-3SX\resources
set DST=%APPDATA%\CrowdedStreet\3SX\resources
for %%S in (27 31 34) do (
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
echo   LA LARGEUR, LUE DANS LE BINAIRE D'ORIGINE
echo ==========================================================
echo.
echo   Chaque etage ajoute a MAINTENANT les bornes de camera
echo   du jeu d'origine, lues dans sa table, une paire par plan.
echo   Plus aucune n'est posee a la main.
echo.
echo     RYU      405 px de course  (j'en avais mis 639 : faux)
echo     NECRO    630 px  (429 avant) -- les chaines de gauche
echo              doivent enfin etre atteignables
echo     KEN 568   ALEX 506   DUDLEY 480   IBUKI 440
echo     GORGE 379  GILL 378  YUN 378  ELENA 378  ELENA1 380
echo     ORO 374  YANG 374  URIEN 374  SEAN 372  HUGO 368
echo.
echo   Les dix-neuf etages de New Generation aussi, lus dans
echo   LEUR binaire : de 352 a 679 px selon le decor.
echo.
echo   A VERIFIER : va au bout a GAUCHE et a DROITE sur RYU,
echo   NECRO, ORO, ELENA, HUGO -- ceux que j'avais elargis a
echo   tort la fois d'avant.
echo.
echo   NECRO garde son fond qui defile, son conducteur et ses
echo   trois pieces de machine. SEAN n'a plus de double.
echo.
pause

3sx.exe > "%~dp0largeur-sortie.log" 2>&1

copy /y fin-de-round.log "%~dp0largeur-trace.log" >nul

echo.
echo ================= VERIFICATION =================
findstr /c:"etage " "%~dp0largeur-trace.log"
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
