@echo off
rem SEAN ET NECRO : les elements qui manquaient, et le calage du sol de Sean.
rem A LANCER PAR DOUBLE-CLIC.

setlocal

copy /y "%~dp0build\3sx-sean-necro.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
if errorlevel 1 (
  echo   ECHEC de la copie : le jeu tourne-t-il encore ?
  pause
  exit /b 1
)

cd /d "%~dp0build\application\bin"
set SF3_DECOR_OBJETS=
set SF3_DECOR_Z=
set SF3_DECOR_VARIANTE=
if exist fatal.log move /y fatal.log fatal-precedent.log >nul

echo ==========================================================
echo   SEAN ET NECRO
echo ==========================================================
echo.
echo   A TESTER, en Versus :
echo.
echo     SEAN BG0D   le grand palmier penche a enfin ses palmes
echo                 la voiture a son conducteur
echo                 l'homme a genou, le petit palmier, le poteau
echo                 les singes descendent de 16 px : celui de
echo                 gauche est ASSIS sur sa caisse
echo.
echo     NECRO BG05  le CONDUCTEUR est au pupitre de la machine
echo                 (homme en blouse grise, penche, au centre)
echo                 la machine du fond a ses trois pieces
echo                 (tuyau, tete rouge du broyeur, bouche du four)
echo.
echo   Les chaines de gauche : dis-moi si tu les vois en allant
echo   tout a fait a GAUCHE du decor. Le code les met au bord.
echo.
echo   Le defilement en boucle du fond n'est PAS fait.
echo.
pause

3sx.exe > "%~dp0sean-necro-sortie.log" 2>&1

copy /y fin-de-round.log "%~dp0sean-necro-trace.log" >nul

echo.
echo ================= VERIFICATION =================
findstr /c:"etage " "%~dp0sean-necro-trace.log"
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
