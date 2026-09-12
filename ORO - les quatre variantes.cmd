@echo off
setlocal
rem Les quatre variantes de la menagerie d'Oro, tirees par z comme dans 2nd Impact.

cd /d "%~dp0build\application\bin"

:menu
cls
echo ==========================================================
echo   LES QUATRE VARIANTES DE LA MENAGERIE D'ORO
echo ==========================================================
echo.
echo   Tu avais vu sur des videos deux versions du decor, avec
echo   les sprites qui changent. Le binaire le confirme mot pour
echo   mot : le script d'etage d'Oro repartit, en 0x8C0DE5D2,
echo   sur u8[0x8C6AF30A] -- contexte+6, LE TIRAGE z, refait a
echo   chaque entree d'etage.
echo.
echo      z 0 : LE CHIEN seul
echo      z 1 : le chat, les chatons ET le chien
echo      z 2 : le chat et les chatons, SANS le chien
echo      z 3 : LE CHIEN seul
echo.
echo   Le perroquet et les quatre chauves-souris sont crees
echo   AVANT le repartiteur : ils sont de toutes les variantes.
echo.
echo   LES QUATRE SONT MAINTENANT CUITES. Chaque fiche porte un
echo   masque de variantes, et c'est le MOTEUR qui tire -- une
echo   fois par etage, comme le jeu. Ce menu force le tirage
echo   pour que tu puisses les voir a la demande.
echo.
echo   Etage 31, ce que chaque variante montre :
echo      z 0 -^> 17 objets     z 1 -^> 19 objets
echo      z 2 -^> 17 objets     z 3 -^> 17 objets
echo.
echo ----------------------------------------------------------
echo    0 . le chien seul
echo    1 . tout : le chat, les chatons, le chien
echo    2 . le chat et les chatons, sans le chien
echo    3 . le chien seul (meme composition que 0)
echo    H . au hasard, comme le jeu le fait
echo    Q . quitter
echo ----------------------------------------------------------
echo.
set "choix="
set /p "choix=Quelle variante ? "

if /i "%choix%"=="Q" goto :eof
if /i "%choix%"=="H" (
  set "SF3_DECOR_VARIANTE="
  echo.
  echo   Tirage au sort par le moteur. La variante retenue est
  echo   ecrite dans decor-objets.log.
  goto :lancer
)
if "%choix%"=="0" goto :fixe
if "%choix%"=="1" goto :fixe
if "%choix%"=="2" goto :fixe
if "%choix%"=="3" goto :fixe
echo   Reponse non comprise.
pause
goto :menu

:fixe
set "SF3_DECOR_VARIANTE=%choix%"
echo.
echo   Variante %choix% forcee.

:lancer
echo.
echo   CE QUE JE TE DEMANDE DE REGARDER
echo.
echo     a. La composition correspond-elle a ce que le menu
echo        annonce ? (le chien present ou absent, le chat et
echo        les chatons presents ou absents)
echo     b. Retrouves-tu les deux versions vues sur les videos ?
echo     c. Le perroquet et les chauves-souris doivent etre la
echo        DANS LES QUATRE. S'ils disparaissent, c'est moi.
echo.
pause

3sx.exe > "%~dp03sx-oro-variante.log" 2>&1

echo.
echo ================= LES JOURNAUX =================
for %%F in (decor-objets.log fin-de-round.log fatal.log) do (
  if exist "%%F" (
    echo.
    echo ----- %%F -----
    type "%%F"
  )
)
echo.
echo ----- sortie du jeu -----
type "%~dp03sx-oro-variante.log"
echo.
pause
goto :menu
