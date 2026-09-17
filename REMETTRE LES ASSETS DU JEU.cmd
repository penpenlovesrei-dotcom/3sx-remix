@echo off
rem Remet les assets du jeu dans le VRAI %APPDATA%.
rem A LANCER PAR DOUBLE-CLIC. Lance par un agent, %APPDATA% pointe
rem vers le bac a sable de l'application et le jeu n'y voit rien.
rem Ne fait que COPIER et FUSIONNER : robocopy /E, aucune suppression.

setlocal
set SRC=C:\Users\frede\OneDrive\Bureau\SEPTEMBRE\SF3\CrowdedStreet-3SX
set DST=%APPDATA%\CrowdedStreet\3SX
set ATTENDU=f9fa50f3a124ec9fa9465aa9c8546c2d867887eb39f711a070762a0324ba5604

echo ==========================================================
echo   LES ASSETS DU JEU, DANS LE BON APPDATA
echo ==========================================================
echo.
echo   source : %SRC%
echo   vers   : %DST%
echo.
echo   Environ 1,2 Go. Fusion, rien n'est supprime.
echo.
if not exist "%SRC%" (
  echo   ARRET : la source est introuvable.
  pause
  exit /b 1
)
choice /c ON /m "Copier"
if errorlevel 2 (
  echo Rien n'a ete copie.
  pause
  exit /b 0
)
echo.
echo   Copie en cours...
robocopy "%SRC%" "%DST%" /E /R:1 /W:1 /NFL /NDL /NP /NJH /NJS >nul
if errorlevel 8 (
  echo   ECHEC de la copie.
  pause
  exit /b 1
)
echo   Copie faite.
echo.
echo ==========================================================
echo   VERIFICATION
echo ==========================================================
echo.
if not exist "%DST%\resources\SF33RD.AFS" (
  echo   MANQUE TOUJOURS : %DST%\resources\SF33RD.AFS
  pause
  exit /b 1
)
echo   AFS present. Calcul de l'empreinte, patiente...
echo.
set OBTENU=
for /f "usebackq delims=" %%H in (`certutil -hashfile "%DST%\resources\SF33RD.AFS" SHA256 ^| findstr /v /c:":"`) do (
  if not defined OBTENU set OBTENU=%%H
)
set OBTENU=%OBTENU: =%
echo     attendu : %ATTENDU%
echo     obtenu  : %OBTENU%
echo.
if /i "%OBTENU%"=="%ATTENDU%" (
  echo   ------------------------------------------------------
  echo   C'EST BON. Le jeu ne redemandera plus l'ISO.
  echo   ------------------------------------------------------
  echo.
  echo   Tu peux lancer l'essai qui attend depuis le 06/09 :
  echo      C:\Temp3sx\LES COULEURS - LE TROISIEME TRANSFERT.cmd
) else (
  echo   L'EMPREINTE NE CORRESPOND PAS. Ne relance pas l'essai,
  echo   dis-le moi : le fichier copie n'est pas le bon.
)
echo.
pause
