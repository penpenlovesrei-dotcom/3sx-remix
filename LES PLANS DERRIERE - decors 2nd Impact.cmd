@echo off
rem Les plans des decors 2nd Impact passent DERRIERE tous les sprites, comme dans 2I.

copy /y "%~dp0build\3sx-plans-derriere.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
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
echo   LES PLANS DERRIERE LES SPRITES - decors 2nd Impact
echo ==========================================================
echo.
echo   LU DANS LE BINAIRE DE 2ND IMPACT : le decor y est dessine
echo   a une profondeur quasi nulle, sans rien par plan. Tout le
echo   decor est donc DERRIERE tous les sprites, et l'ordre des
echo   plans ne tient qu'a leur rang.
echo.
echo   Chez nous, les plans etaient a 84 et 94 -- des valeurs de
echo   3rd Strike -- alors que les sprites de 2I vont jusqu'a 95.
echo   Chez Yun, cages, etal et enseignes passaient derriere le
echo   batiment rouge.
echo.
echo   Les plans passent a 120-123, dans le meme ordre qu'avant.
echo   Seuls les 17 decors de 2nd Impact changent. Rien d'autre.
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER - en Versus, 2nd Impact
echo ==========================================================
echo.
echo     YUN : les sprites de droite (etal, cages, fumeur,
echo           enseignes) doivent etre visibles, devant le
echo           batiment. La charrette en trop sera ENCORE la :
echo           c'est un autre defaut, traite apres.
echo.
echo     ORO, YANG, SEAN : leur ordre de sprites peut changer.
echo.
echo     GILL, ALEX, RYU, DUDLEY, HUGO, KEN, URIEN, AKUMA :
echo           etaient OK. Ils doivent le rester.
echo.
pause

3sx.exe > "%~dp0plans-derriere-sortie.log" 2>&1

copy /y fin-de-round.log "%~dp0plans-derriere-trace.log" >nul

echo.
echo ================= VERIFICATION =================
findstr /c:"etage " "%~dp0plans-derriere-trace.log"
echo.
if exist fatal.log (
  echo ----- fatal.log : LE JEU A FIGE -----
  type fatal.log
) else (
  echo   Pas de fatal.log : aucun blocage.
)
echo.
pause
