@echo off
rem Les chatons : ce n'est pas la routine d'etage qui les cree, c'est leur mere.

cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   LES CHATONS D'ORO -- C'EST LA MERE QUI LES FAIT
echo ==========================================================
echo.
echo   Hier je te disais qu'aucun appelant ne creait les chatons
echo   animes, et que sans appelant je ne poserais pas de
echo   position. La raison etait ailleurs, et elle est simple :
echo.
echo   ILS NE SONT PAS CREES PAR LA ROUTINE D'ETAGE.
echo   Le spawner du CHAT les cree, en dernier geste, au site
echo   0x8C033966 -- `jsr 0x8C033ACC`. La chatte fait ses
echo   chatons.
echo.
echo   Ma remontee ne cherchait qu'un chemin jusqu'aux dix-sept
echo   routines d'etage. Elle declarait « aucun chemin » alors
echo   que le chemin passe par un FRERE.
echo.
echo ----------------------------------------------------------
echo   CE QU'ILS SONT
echo ----------------------------------------------------------
echo.
echo   id 73, x 493, y 81, palette 75, plan 2, script 17
echo   (douze images). Tout en immediats, et la meme table de
echo   scripts 0x8C12AB8C que le reste de la menagerie.
echo.
echo   ILS SONT A COTE DE LEUR MERE, qui est en 411, 80. Ce
echo   recoupement ne coute rien et il dit beaucoup.
echo.
echo   LA MENAGERIE EST DONC COMPLETE :
echo.
echo      le gros chat        411, 80    script 13
echo      les chatons         493, 81    script 17
echo      le chien            700, 56    script 29
echo      le perroquet        672, 114   script 20
echo      quatre chauves-souris, haut dans la grotte
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER
echo ==========================================================
echo.
echo   ORO (etage 31) passe de quinze objets a seize.
echo.
echo     a. Vois-tu les chatons JUSTE A COTE du gros chat ?
echo     b. Toute la menagerie est-elle a sa place, et aux
echo        bonnes couleurs ? C'est la premiere fois qu'elle est
echo        au complet.
echo.
echo   NOTE : les deux chatons FIXES sont cuits depuis longtemps
echo   comme element statique. Si tu vois deux paires de
echo   chatons, l'une est la copie cuite et l'autre l'objet
echo   anime -- dis-le moi, on choisira laquelle garder.
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe tous les objets
echo   animes sans toucher au decor.
echo.
pause

3sx.exe > "%~dp03sx-chatons.log" 2>&1

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
type "%~dp03sx-chatons.log"
echo.
pause
