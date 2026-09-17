@echo off
rem Taille d'origine stricte : 384x224, rendu ET fenetre.
rem A LANCER PAR DOUBLE-CLIC, LE JEU FERME.

setlocal
set CFG=%APPDATA%\CrowdedStreet\3SX\config

echo ==========================================================
echo   384 x 224 - LA TAILLE D'ORIGINE STRICTE
echo ==========================================================
echo.
if not exist "%CFG%" (
  echo   Config introuvable : %CFG%
  pause
  exit /b 1
)
echo   ----- AVANT -----
findstr /i "render-scale window-width window-height fullscreen" "%CFG%"
echo.
echo   render-scale  = 1     rendu interne 384x224
echo   window-width  = 384   fenetre 384x224, un pixel pour
echo   window-height = 224   un pixel, aucune mise a l'echelle
echo   fullscreen    = false
echo.
echo   Le jeu ne relit ces valeurs qu'au demarrage.
echo.
choice /c ON /m "Appliquer"
if errorlevel 2 (
  echo Rien n'a ete change.
  pause
  exit /b 0
)
echo.
copy /y "%CFG%" "%CFG%.avant-resolution" >nul
powershell -NoProfile -Command "$p=$env:APPDATA+'\CrowdedStreet\3SX\config'; $t=Get-Content -Raw -LiteralPath $p; $t=[regex]::Replace($t,'(?m)^[ \t]*render-scale[ \t]*=.*$','render-scale = 1'); $t=[regex]::Replace($t,'(?m)^[ \t]*window-width[ \t]*=.*$','window-width = 384'); $t=[regex]::Replace($t,'(?m)^[ \t]*window-height[ \t]*=.*$','window-height = 224'); $t=[regex]::Replace($t,'(?m)^[ \t]*fullscreen[ \t]*=.*$','fullscreen = false'); Set-Content -LiteralPath $p -Value $t -NoNewline -Encoding utf8"
echo   ----- APRES -----
findstr /i "render-scale window-width window-height fullscreen" "%CFG%"
echo.
echo   Attendu : 1 / 384 / 224 / false
echo   Ancien fichier garde : %CFG%.avant-resolution
echo.
echo   Relance :
echo      C:\Temp3sx\LES COULEURS - LE TROISIEME TRANSFERT.cmd
echo.
pause
