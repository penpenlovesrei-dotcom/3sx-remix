@echo off
rem YUN : les sprites de droite naissent mais ne se voient pas. Sont-ils caches par un plan ?

copy /y "%~dp0build\3sx-diag-z.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
if errorlevel 1 (
  echo   ECHEC : une instance du jeu verrouille le fichier.
  pause
  exit /b 1
)
cd /d "%~dp0build\application\bin"
set SF3_DECOR_OBJETS=
set SF3_DECOR_Z=20

echo ==========================================================
echo   YUN - LES SPRITES DE DROITE SONT-ILS CACHES ?
echo ==========================================================
echo.
echo   Le journal le prouve : les sprites de la moitie droite de
echo   YUN NAISSENT, a leur place exacte. Ils ne se voient pas.
echo   Le seul visible, le panneau vertical, est aussi le seul
echo   dessine tout devant.
echo.
echo   ESSAI DE DIAGNOSTIC : tous les sprites de decor sont mis
echo   au PREMIER PLAN, devant le decor et devant les combattants.
echo   C'est volontairement faux : ne juge pas la superposition.
echo.
echo   A regarder en Versus :  YUN STAGE  (2nd Impact)
echo.
echo   Les sprites de droite APPARAISSENT = un plan du decor les
echo                                        cachait.
echo   Toujours absents                   = autre cause.
echo.
pause

3sx.exe > "%~dp0yun-z-sortie.log" 2>&1

copy /y decor-objets.log "%~dp0yun-z-objets.log" >nul

echo.
echo ================= VERIFICATION =================
findstr /c:"profondeur forcee" /c:"objets animes permis" "%~dp0yun-z-objets.log"
echo   attendu : "profondeur forcee : 20"
echo.
pause
