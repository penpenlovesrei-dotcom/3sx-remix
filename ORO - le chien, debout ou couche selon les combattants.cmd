@echo off
rem ORO : le chien a deux places, et ce sont les combattants qui choisissent.
rem A LANCER PAR DOUBLE-CLIC.

setlocal

copy /y "%~dp0build\3sx-chien.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
if errorlevel 1 (
  echo   ECHEC de la copie : le jeu tourne-t-il encore ?
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
echo   ORO - LE CHIEN
echo ==========================================================
echo.
echo   Dans 2I, le chien lit les deux combattants :
echo.
echo   * un des joueurs est IBUKI, ELENA ou ORO :
echo     le chien est DEBOUT, plus a gauche (608). Il suit du
echo     regard son prefere (Oro avant Ibuki et Elena), remue
echo     la queue quand cet ami se tient juste devant lui, et
echo     ABOIE quand un combattant lance un coup special.
echo.
echo   * sinon : le chien est COUCHE, a droite (700). Il leve
echo     la tete de temps en temps, et se redresse sur un coup
echo     special.
echo.
echo   Il reste absent dans la variante 2 (chat et chatons).
echo.
echo   Variante du decor :
echo     0 = au hasard, comme 2I
echo     1 = variante 0 : le chien seul
echo     2 = variante 1 : le chat, les chatons et le chien
echo.
choice /c 012 /n /m "  Ton choix (0, 1 ou 2) : "
if errorlevel 3 (
  set SF3_DECOR_VARIANTE=1
) else if errorlevel 2 (
  set SF3_DECOR_VARIANTE=0
)
echo.
echo   Joue deux matchs sur le decor d'Oro : un avec Ibuki,
echo   Elena ou Oro, un sans. Puis quitte le jeu.
echo.
pause

3sx.exe > "%~dp0chien-sortie.log" 2>&1

copy /y fin-de-round.log "%~dp0chien-trace.log" >nul

echo.
echo ================= VERIFICATION =================
findstr /c:"variante" /c:"combattants" "%~dp0chien-trace.log"
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
