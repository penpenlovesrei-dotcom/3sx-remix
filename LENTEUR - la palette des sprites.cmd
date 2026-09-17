@echo off
rem DIAGNOSTIC DE LENTEUR : sprites animes ACTIFS, mais leur palette n'est plus
rem renvoyee au GPU a chaque trame. Exe de diagnostic, pas une correction.

copy /y "%~dp0build\3sx-diag-palette.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
if errorlevel 1 (
  echo   ECHEC : une instance du jeu verrouille le fichier.
  pause
  exit /b 1
)
cd /d "%~dp0build\application\bin"
set SF3_DECOR_OBJETS=

echo ==========================================================
echo   LENTEUR - LA PALETTE DES SPRITES
echo ==========================================================
echo.
echo   Sans les sprites animes, Yun et Yang ne sont plus lents.
echo   Le suspect : chaque sprite renvoie sa palette de couleurs
echo   a la carte graphique A CHAQUE IMAGE, et le moteur detruit
echo   puis recree une texture a chaque envoi. Sur Yun, des
echo   centaines de fois par seconde, pour une palette qui ne
echo   change pas.
echo.
echo   Cet exe garde les sprites animes, mais ne fait plus cet
echo   envoi. LES COULEURS DES SPRITES PEUVENT ETRE FAUSSES :
echo   n'en tiens pas compte, regarde seulement la vitesse.
echo.
echo   A tester en Versus :
echo     YUN STAGE   (2nd Impact)
echo     YANG STAGE  (2nd Impact)
echo.
echo   Plus lent du tout = c'est la palette, je corrige.
echo   Encore lent       = ce n'est pas elle, je cherche ailleurs.
echo.
pause

3sx.exe > "%~dp0diag-palette-sortie.log" 2>&1

copy /y decor-objets.log "%~dp0diag-palette-objets.log" >nul

echo.
echo ================= VERIFICATION =================
findstr /c:"objets animes permis" "%~dp0diag-palette-objets.log"
echo   attendu : "objets animes permis : 1"  (sprites actifs)
echo.
pause
