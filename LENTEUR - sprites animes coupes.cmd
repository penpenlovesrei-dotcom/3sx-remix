@echo off
rem LENTEUR : meme jeu, SANS aucun sprite anime de decor.
rem Coupure sans condition, verifiee dans le journal a la fin.

copy /y "%~dp0build\3sx-hugo-cache.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
if errorlevel 1 (
  echo   ECHEC : une instance du jeu verrouille le fichier.
  pause
  exit /b 1
)
cd /d "%~dp0build\application\bin"

set SF3_DECOR_OBJETS=0

echo ==========================================================
echo   LENTEUR - SPRITES ANIMES COUPES
echo ==========================================================
echo.
echo   Le lanceur precedent ne coupait RIEN : un bug a moi.
echo   Celui-ci coupe toujours.
echo.
echo   Tu dois voir le decor FIXE : aucun sprite qui bouge.
echo   Si un sprite bouge, arrete et dis-le moi.
echo.
echo   A tester en Versus :
echo     YUN STAGE   (2nd Impact)
echo     YANG STAGE  (2nd Impact)
echo.
echo   Encore lent  = les sprites animes ne sont pas la cause.
echo   Plus lent du tout = ce sont eux.
echo.
pause

3sx.exe > "%~dp0lenteur-sortie.log" 2>&1

copy /y decor-objets.log "%~dp0lenteur-objets.log" >nul

echo.
echo ================= VERIFICATION =================
findstr /c:"objets animes permis" "%~dp0lenteur-objets.log"
echo   attendu : "objets animes permis : 0"
echo.
pause
