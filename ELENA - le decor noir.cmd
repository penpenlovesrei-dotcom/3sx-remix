@echo off
rem Trace un passage sur ELENA STAGE (etage 30), dont le decor sort tout noir.
rem Ne modifie rien : lance le jeu tel quel et garde les journaux a part.

cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   ELENA - LE DECOR NOIR
echo ==========================================================
echo.
echo   Les pages de l'etage 30 sont intactes. Le noir vient du
echo   moteur, et le jeu note chaque plan qu'il allume : il me
echo   faut cette trace.
echo.
echo   A FAIRE :
echo     1. Versus, choisir l'etage  ELENA STAGE
echo     2. Jouer jusqu'a voir le decor noir (quelques secondes)
echo     3. Si possible, finir la manche : le decor change d'aire
echo     4. Quitter le jeu
echo.
pause

3sx.exe > "%~dp0elena-sortie.log" 2>&1

copy /y fin-de-round.log "%~dp0elena-trace.log" >nul
copy /y decor-objets.log "%~dp0elena-objets.log" >nul

echo.
echo ================= LA TRACE =================
findstr /v /c:"battement moteur" "%~dp0elena-trace.log"
echo.
echo   Garde dans C:\Temp3sx\elena-trace.log
echo   Dis-moi juste : c'est fait.
echo.
pause
