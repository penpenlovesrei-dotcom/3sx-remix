@echo off
rem ORO DE REFERENCE : l'etat d'avant les changements de plans et de palette.

copy /y "%~dp0build\3sx-hugo-cache.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
if errorlevel 1 (
  echo   ECHEC : une instance du jeu verrouille le fichier.
  pause
  exit /b 1
)
cd /d "%~dp0build\application\bin"
set SF3_DECOR_OBJETS=
set SF3_DECOR_Z=

echo ==========================================================
echo   ORO DE REFERENCE - l'etat d'AVANT
echo ==========================================================
echo.
echo   Cet exe est l'essai des couleurs avec seulement les
echo   corrections d'Elena et d'Hugo, qui ne touchent pas Oro :
echo     - les ANCIENS plans,
echo     - la palette renvoyee a chaque image.
echo   IL SERA LENT, c'est normal : c'est l'ancienne palette.
echo.
echo ==========================================================
echo   DEUX QUESTIONS - en Versus, ORO STAGE (2nd Impact)
echo ==========================================================
echo.
echo     1. Les CASCADES sont-elles visibles ? Devant ou derriere
echo        quoi ?
echo.
echo     2. La palette du PERROQUET est-elle juste ?
echo        Si oui, c'est mon optimisation de palette qui la casse.
echo        Si non, le defaut est plus ancien.
echo.
pause

3sx.exe > "%~dp0oro-reference-sortie.log" 2>&1

echo.
echo   Fini. Reponds aux deux questions.
echo.
pause
