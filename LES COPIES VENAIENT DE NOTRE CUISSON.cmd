@echo off
rem On cuisait dans le decor ce que le code anime. On n'efface QUE ces empreintes-la.

echo ==========================================================
echo   DEPLOIEMENT DE L'EXE
echo ==========================================================
echo.
copy /y "%~dp0build\3sx.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
if errorlevel 1 (
  echo   ECHEC : une instance du jeu verrouille le fichier.
  echo   Ferme-la et relance ce lanceur.
  pause
  exit /b 1
)
for %%F in ("%~dp0build\application\bin\3sx.exe") do echo   exe deploye, %%~tF
echo.

cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   LES COPIES ETAIENT DE MOI
echo ==========================================================
echo.
echo   Tu les as signalees cinq fois. J'ai cherche une carte de
echo   tuiles que 2I n'a pas, une position qui etait juste, un
echo   filtre de variantes qui marchait. La cause etait dans
echo   NOTRE cuisson.
echo.
echo   LA MESURE. On compare la demi-banque BRUTE du disque a
echo   notre page cuite :
echo.
echo      banque 0 bas   la scene SANS le vieil homme ni la dame
echo      page 196       la meme scene AVEC les deux, peints
echo.
echo   On peignait la figure dans le decor, PUIS on posait
echo   l'objet anime par-dessus. Deux figures des que
echo   l'animation s'ecarte de la pose peinte.
echo.
echo   CONTROLE, image par image : notre objet ne peint JAMAIS
echo   un pixel hors de la figure -- zero sur les douze images.
echo   Tout l'ecart est de couleur et croit avec la trame. C'est
echo   l'animation, pas un decalage.
echo.
echo ----------------------------------------------------------
echo   LE CORRECTIF, ET LA FAUSSE PISTE QUE TU AS ARRETEE
echo ----------------------------------------------------------
echo.
echo   poser2i fait deux choses :
echo.
echo     1. il n'ecrit plus un element dont le script est pose
echo        par animer2i ;
echo     2. il REND LA BANQUE NUE sous l'empreinte de chaque
echo        objet anime, lue dans le C COMPILE -- donc
echo        exactement la surface que le moteur recouvre.
echo.
echo   Le point 2 etait indispensable : les figures en double
echo   avaient ete cuites par une passe ANTERIEURE, avec un
echo   annuaire qui comptait plus d'elements. Rien dans la liste
echo   d'aujourd'hui ne les effacait.
echo.
echo   MA PREMIERE VERSION REPARTAIT DE LA BANQUE POUR TOUTE LA
echo   PAGE. Elle emportait alors ce qu'une cuisson ancienne
echo   avait pose et qu'AUCUN objet ne remplace. Tu l'as arretee
echo   d'une phrase, et tu avais raison. On n'efface plus que
echo   des empreintes.
echo.
echo   LE CONTROLE QUI REND LA CHOSE SURE : 27 448 pixels
echo   changent sur la page de Yun, et LES 27 448 RENDENT
echo   EXACTEMENT LA BANQUE DU DISQUE. Zero va ailleurs. Rendre
echo   la banque ne peut pas creer de trou -- on y remet le
echo   contenu de l'original, jamais du vide.
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER
echo ==========================================================
echo.
echo   YUN (etage 25) :
echo     a. Plus aucune copie fixe sous les sprites animes ?
echo     b. Rien ne manque ?
echo     c. Le vieil homme et la dame sont dans la variante
echo        z 1/3 : SF3_DECOR_VARIANTE=1 les force.
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe les objets
echo   animes. Il montre desormais la page telle que le disque
echo   la porte sous eux -- c'est le bon moyen de voir ce qui
echo   est cuit et ce qui est pose.
echo.
pause

3sx.exe > "%~dp03sx-cuisson.log" 2>&1

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
type "%~dp03sx-cuisson.log"
echo.
pause
