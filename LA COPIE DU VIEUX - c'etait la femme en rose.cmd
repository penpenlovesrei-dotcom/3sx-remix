@echo off
rem Les personnages animes sont AUSSI peints dans le decor : l'objet doit les recouvrir.

cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   LA COPIE VENAIT DE SEIZE PIXELS
echo ==========================================================
echo.
echo   Tu as dit : « les 2 personnages devant le tram sont
echo   animes mais on voit la copie du vieux ». Ce n'etait pas
echo   le vieux -- c'etait LA FEMME EN ROSE, rendue deux fois.
echo.
echo ----------------------------------------------------------
echo   TROIS PISTES FERMEES AVANT LA BONNE
echo ----------------------------------------------------------
echo.
echo   Je les ecris pour qu'on ne les rouvre pas :
echo.
echo     - CE N'EST PAS UNE FUITE DE VARIANTE. Les masques 0x5
echo       et 0xA s'excluent, et j'ai relu le filtre des deux
echo       cotes du moteur : il est juste.
echo     - AUCUN SCRIPT N'EST POSE DEUX FOIS. Verifie sur les
echo       quatorze objets de Yun.
echo     - LES PAGES CUITES NE SONT PAS PERIMEES. Recuire Yun
echo       ne change AUCUN pixel.
echo.
echo ----------------------------------------------------------
echo   LA MESURE QUI TRANCHE
echo ----------------------------------------------------------
echo.
echo   UN PERSONNAGE ANIME EST SOUVENT AUSSI PEINT dans le
echo   decor, a l'arret, a sa place exacte : l'objet est cense
echo   le recouvrir. Sa position y est donc une mesure.
echo.
echo   Je cherchais depuis le debut dans la BANQUE DU DISQUE,
echo   ou la figure est eclatee en tuiles -- elle n'y apparait
echo   jamais d'un seul tenant, et je trouvais zero. Il fallait
echo   chercher dans la PAGE ASSEMBLEE.
echo.
echo      script  pose en   peint en
echo      6,16,26  303,288,208  idem      100 %%
echo      7        672          672        97 %%
echo      28       320          320        90 %%
echo      33 le vieil homme  480    480    96 %%
echo      31 LA FEMME EN ROSE  496  512    <-- SEIZE PIXELS
echo.
echo   Les cinq premiers VALIDENT LA FORMULE au passage. Seule
echo   la femme etait a cote, et on la voyait donc en double.
echo.
echo ----------------------------------------------------------
echo   DUDLEY : DEUX QUESTIONS EN SUSPENS, REPONDUES
echo ----------------------------------------------------------
echo.
echo   LE FEU A BIEN SA PHASE ORANGE : c'est l'IMAGE 3 du
echo   script 0. Si tu ne l'as jamais vu oranger, c'est un
echo   probleme de cadence, pas une phase manquante.
echo.
echo   LES « DEUX AUTRES PUNKS » N'EN FONT QU'UN. Les scripts 6
echo   et 7 sont le MEME personnage -- leur image 7 est
echo   identique au pixel pres. Le troisieme punk, celui au
echo   blouson Union Jack, c'est le script 10 : il est PEINT en
echo   736, il n'a qu'une seule image, il est donc statique de
echo   droit. Il n'y a rien a poser.
echo.
echo   ET LE PUNK DE GAUCHE PASSE DEVANT, comme tu l'as
echo   demande. A DIRE FRANCHEMENT : c'est ton observation, pas
echo   une lecture du binaire. Rien dans l'enregistrement ne
echo   donne cet ordre -- j'ai force la profondeur du script 6.
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER
echo ==========================================================
echo.
echo   YUN (etage 25) :
echo     a. Le vieil homme et la femme en rose : UN SEUL de
echo        chaque, et animes ?
echo     b. Ils sont dans la VARIANTE z 1/3. Si tu ne les vois
echo        pas, relance -- une entree sur deux tombe sur 0 ou
echo        2. SF3_DECOR_VARIANTE=1 les force.
echo.
echo   DUDLEY (etage 26) :
echo     c. Le punk de gauche est-il maintenant devant celui du
echo        centre ?
echo     d. Le feu passe-t-il au orange ?
echo.
echo   ORO (etage 31) doit etre inchange : sa mesure a lui est
echo   la seule autre, et j'ai touche a la facon dont elle
echo   s'applique aux morceaux. Si son edifice de pierre a
echo   bouge, c'est moi.
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe tous les objets
echo   animes sans toucher au decor.
echo.
pause

3sx.exe > "%~dp03sx-copie.log" 2>&1

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
type "%~dp03sx-copie.log"
echo.
pause
