@echo off
rem Verifie que SF33RD.AFS est au bon endroit et qu'il est le bon fichier.
rem Ne copie rien, ne supprime rien. A LANCER PAR DOUBLE-CLIC.

setlocal
set AFS=%APPDATA%\CrowdedStreet\3SX\resources\SF33RD.AFS
set ATTENDU=f9fa50f3a124ec9fa9465aa9c8546c2d867887eb39f711a070762a0324ba5604

echo ==========================================================
echo   VERIFICATION DES ASSETS
echo ==========================================================
echo.
echo   fichier : %AFS%
echo.
if not exist "%AFS%" (
  echo   ABSENT. La copie n'a pas abouti.
  echo.
  pause
  exit /b 1
)
for %%F in ("%AFS%") do echo   taille  : %%~zF octets   ^(attendu 642492416^)
echo.
echo   Calcul de l'empreinte, une trentaine de secondes...
echo.
set OBTENU=
for /f "usebackq delims=" %%H in (`certutil -hashfile "%AFS%" SHA256 ^| findstr /v /c:":"`) do (
  if not defined OBTENU set OBTENU=%%H
)
set OBTENU=%OBTENU: =%
echo     attendu : %ATTENDU%
echo     obtenu  : %OBTENU%
echo.
if /i "%OBTENU%"=="%ATTENDU%" (
  echo   ------------------------------------------------------
  echo   C'EST LE BON FICHIER, AU BON ENDROIT.
  echo   ------------------------------------------------------
  echo.
  echo   Lance l'essai qui attend depuis le 06/09 :
  echo      C:\Temp3sx\LES COULEURS - LE TROISIEME TRANSFERT.cmd
) else (
  echo   L'EMPREINTE NE CORRESPOND PAS. Dis-le moi avant de
  echo   relancer l'essai.
)
echo.
pause
