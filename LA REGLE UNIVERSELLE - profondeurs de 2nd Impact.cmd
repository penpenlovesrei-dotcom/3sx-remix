@echo off
rem LES PROFONDEURS DE 2ND IMPACT, LUES DANS LE BINAIRE : un seul essai pour les 17 decors.

copy /y "%~dp0build\3sx-table-2i.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
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
echo   LA REGLE UNIVERSELLE - profondeurs lues dans 2nd Impact
echo ==========================================================
echo.
echo   Fini les reglages decor par decor. 2nd Impact ecrit la
echo   profondeur de chaque couche de chaque decor dans une table
echo   de son binaire. Elle est lue telle quelle :
echo.
echo     - chaque plan prend la profondeur de SA couche dans 2I
echo       (94 et 84 presque partout, 104, 114 ou 120 ailleurs)
echo     - chaque sprite garde SA profondeur de 2I, sans rustine
echo       (le +16 et le recul des cascades sont retires)
echo.
echo   Controle sur les listes d'affichage de 2I : 255 paires
echo   couche/sprite sur 255 dans le bon ordre, 0 faute.
echo.
echo ==========================================================
echo   UN SEUL ESSAI - en Versus, les 17 decors de 2nd Impact
echo ==========================================================
echo.
echo     ORO   : cascades devant le couchant, DERRIERE les deux
echo             grottes - comme dans 2nd Impact.
echo     YUN   : sprites de droite visibles.
echo     YANG, NECRO, HUGO, IBUKI, ELENA : l'ordre peut changer.
echo     Tous les autres : ne doivent pas regresser.
echo.
echo   CE QUE CETTE REGLE NE REGLE PAS (a part) :
echo     la charrette de Yun, le perroquet d'Oro, les animations
echo     manquantes de Yang, la hauteur de Sean.
echo.
pause

3sx.exe > "%~dp0table-2i-sortie.log" 2>&1

copy /y fin-de-round.log "%~dp0table-2i-trace.log" >nul

echo.
echo ================= VERIFICATION =================
findstr /c:"etage " "%~dp0table-2i-trace.log"
echo.
if exist fatal.log (
  echo ----- fatal.log : LE JEU A FIGE -----
  type fatal.log
) else (
  echo   Pas de fatal.log : aucun blocage.
)
echo.
pause
