@echo off
rem NEW GENERATION : les decors revus avec ce qu'on a appris sur 2I.
rem A LANCER PAR DOUBLE-CLIC.

setlocal

copy /y "%~dp0build\3sx-ng.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
if errorlevel 1 (
  echo   ECHEC de la copie : le jeu tourne-t-il encore ?
  pause
  exit /b 1
)

cd /d "%~dp0build\application\bin"
set SF3_DECOR_OBJETS=
set SF3_DECOR_Z=
set SF3_DECOR_VARIANTE=
if exist jalons.on del jalons.on
if exist fatal.log move /y fatal.log fatal-precedent.log >nul

echo ==========================================================
echo   NEW GENERATION - REVUE DES DECORS
echo ==========================================================
echo.
echo   PARTOUT : chaque decor ne pose plus que les objets de SON
echo   round (la rue et le temple de Hong Kong ne sont plus
echo   melanges), une seule variante a la fois, plus de debris
echo   poses d'avance.
echo.
echo   1. RYU et KEN (Japon) : les objets sont decales d'une
echo      demi-bande, comme Ryu 2I valide : singes, femme au
echo      panneau, baigneurs a leur place.
echo   2. DUDLEY 1 et 2 (Londres) : meme regle. Le grand
echo      immeuble au-dessus du pub, la maison a colombages sur
echo      le mur du pont, la voiture, la boite aux lettres. La
echo      tour du fond defile avec le plan lointain.
echo   3. HUGO (Munich, la tente) : meme regle. La chope pend
echo      au navire, la banderole sur l'escalier, les poteaux
echo      sur le quai, les gens sur la place.
echo   4. ORO : le perroquet, le chien (debout avec Ibuki,
echo      Elena ou Oro, couche sinon), la chatte et ses
echo      chatons, les chauves-souris.
echo   5. YUN et YANG, la rue : la cage et ses quatre oiseaux,
echo      le fumeur, les passants.
echo   6. YUN et YANG, le temple : les statues, l'aquarium.
echo      Le code de NG met les poissons DERRIERE la vitre :
echo      dis-moi si tu les vois dans l'original.
echo   7. ALEX, ELENA 1 et 2 : les objets lointains defilent
echo      avec leur plan.
echo.
echo   Joue ces decors (au moins Ryu, Dudley 2, Hugo, Oro),
echo   puis quitte le jeu.
echo.
pause

3sx.exe > "%~dp0ng-sortie.log" 2>&1

copy /y fin-de-round.log "%~dp0ng-trace.log" >nul

echo.
echo ================= VERIFICATION =================
findstr /c:"etage " /c:"variante" /c:"combattants" "%~dp0ng-trace.log"
echo.
if exist fatal.log (
  echo ----- fatal.log : LE JEU A FIGE -----
  type fatal.log
) else (
  echo   Pas de fatal.log : aucun blocage.
)
echo.
pause
exit /b 0
