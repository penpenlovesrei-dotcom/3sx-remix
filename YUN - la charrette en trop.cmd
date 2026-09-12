@echo off
rem Le sprite qui passait devant le fumeur : c'etait une charrette posee deux fois.

cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   YUN : LA CHARRETTE ETAIT POSEE DEUX FOIS
echo ==========================================================
echo.
echo   Tu as dit : « le personnage a droite est anime mais un
echo   sprite est devant lui ». C'est une CHARRETTE de marchand
echo   (160 x 112), et deux objets la rendaient :
echo.
echo      l'id 21, enregistrement 2  ->  pose en bx 576
echo      l'id 22                    ->  pose en bx 536
echo.
echo   Le fumeur anime est en bx 728. La premiere s'etale de 576
echo   a 736 et LE RECOUVRE ; la seconde de 536 a 696 et
echo   s'arrete juste avant lui. J'ai donc ecarte la premiere.
echo.
echo   A DIRE FRANCHEMENT : c'est un ARBITRAGE, pas une lecture.
echo   Les deux enregistrements existent bel et bien dans le
echo   binaire et je n'ai pas su etablir lequel le jeu emploie.
echo   Ce qui est mesure, c'est que l'une recouvre le fumeur et
echo   l'autre non. Si la charrette est maintenant au mauvais
echo   endroit, c'est que j'ai garde la mauvaise : dis-le et
echo   j'echange.
echo.
echo ----------------------------------------------------------
echo   POURQUOI LES AUTRES NE SONT PAS ANIMES
echo ----------------------------------------------------------
echo.
echo   J'ai rendu les sprites et je les ai regardes, pour ne pas
echo   te faire deviner. Ce qu'on pose chez Yun :
echo.
echo      script 28  DEUX PERSONNAGES ACCROUPIS  <- tes 2
echo                 personnages devant le tram
echo      script 7   LES CAGES A OISEAUX
echo      script 24  LE FUMEUR (anime, 7 images)
echo      script 2   la charrette      script 0  un panneau
echo      script 4   des paniers       script 1  une table
echo.
echo   ET VOICI LA CAUSE, mesuree dans le binaire :
echo.
echo      script 28 (les 2 personnages) -^> UNE SEULE IMAGE
echo      script 7  (les cages)         -^> UNE SEULE IMAGE
echo      script 24 (le fumeur)         -^> SEPT images
echo.
echo   Leurs scripts ne contiennent qu'une image, suivie de la
echo   commande de fin. Ce n'est pas notre lecteur qui tronque :
echo   j'ai relu les octets bruts. Leur animation ne vient donc
echo   PAS du script -- elle vient de la machine a etats de leur
echo   routine, qui change de script au fil du temps.
echo.
echo   Notre moteur, lui, joue UN script en boucle. C'est la
echo   limite, et elle est structurelle : pour animer ces
echo   deux-la il faudrait enchainer plusieurs scripts.
echo.
echo   J'ai verifie si les scripts voisins (27 et 29) etaient
echo   d'autres poses du meme couple, pour les concatener : NON,
echo   ce sont d'autres personnages. Je ne les ai donc pas
echo   colles bout a bout.
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER
echo ==========================================================
echo.
echo     a. Le fumeur est-il degage ? Plus rien devant lui ?
echo     b. La charrette restante est-elle a sa place ?
echo     c. Les cages et les 2 personnages sont toujours figes
echo        -- c'est attendu, voir ci-dessus. Confirme juste
echo        qu'ils sont au bon ENDROIT.
echo.
echo   Je t'envoie aussi les planches de sprites rendues, pour
echo   que tu confirmes que j'ai bien identifie qui est qui.
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe tous les objets
echo   animes sans toucher au decor.
echo.
pause

3sx.exe > "%~dp03sx-yun.log" 2>&1

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
type "%~dp03sx-yun.log"
echo.
pause
