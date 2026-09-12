@echo off
rem bg0c, bg0e, bg07, bg09, bg0f : ce qu'ils avaient, et ou ca s'arrete.

echo ==========================================================
echo   DEPLOIEMENT DE L'EXE
echo ==========================================================
echo.
copy /y "%~dp0build\3sx.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
if errorlevel 1 (
  echo   ECHEC : une instance du jeu verrouille le fichier.
  pause
  exit /b 1
)
for %%F in ("%~dp0build\application\bin\3sx.exe") do echo   exe deploye, %%~tF
echo.

cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   LES DECORS SANS ENTREE : DEUX AJOUTES, TROIS BLOQUES
echo ==========================================================
echo.
echo   BG0C (etage 33) EST AJOUTE. Son objet vient du chargeur
echo   partage 8C025A9A, dont l'argument n'est pas capture au
echo   site d'appel -- il vaut DECOR - 1, la convention etablie
echo   avec les tables 8C17C1F8 / 8C5F9DF8. Un objet, script 2
echo   en x 480, palette 83.
echo.
echo   BG0E (etage 35) EST DECRIT, MAIS PAS POSABLE. Le code lui
echo   donne ONZE objets sur TROIS variantes de z, dont deux
echo   richement animes -- le script 15 a seize images, le 26 en
echo   a neuf :
echo.
echo      z0 : scripts 17, 4, 19, 26, 27, 24
echo      z1 : scripts 20, 22, 4, 15, 24
echo      z2 : scripts 20, 21, 22, 15, 24
echo.
echo   ET VOICI OU CA BUTE, et ce n'est plus du code : LEURS
echo   SPRITES NE SONT DANS AUCUN ASSET EXTRAIT. Les index de
echo   leurs images tombent entre 43594 et 43823, or l'asset de
echo   bg0e ne couvre que 45400 a 45448. Aucun des seize
echo   conteneurs F_ETC extraits ne les contient.
echo.
echo   BG07, BG09 ET BG0F N'ONT AUCUN ASSET DU TOUT. Ils ne sont
echo   meme pas des cles de la table. Rien a poser tant que
echo   leurs conteneurs ne sont pas extraits du disque.
echo.
echo   IL FAUDRAIT DONC EXTRAIRE D'AUTRES F_ETC de la
echo   Dreamcast. Les seize qu'on a portent les numeros 24 a 35,
echo   41, 94 et 100 ; les manquants sont dans le disque, qui
echo   n'est pas dans cet arbre de travail. C'est une tache
echo   d'extraction, plus de lecture de code.
echo.
echo ----------------------------------------------------------
echo   ET UN CONFLIT REEL, TRANCHE PAR LA DONNEE
echo ----------------------------------------------------------
echo.
echo   Les bandes 12 et 13 appellent toutes deux 8C028792 avec
echo   l'argument 7 : le meme bloc se retrouvait attribue aux
echo   decors 11 ET 12. Un seul peut l'avoir, et c'est la donnee
echo   qui tranche -- son script 9 a huit images chez le 12 et
echo   n'existe pas chez le 11, qui n'en compte que six.
echo.
echo   `blocs2i` ecarte desormais tout enregistrement dont le
echo   script est hors de la table du decor.
echo.
echo ==========================================================
echo   L'ETAT : TREIZE DECORS PASSENT LES DOUZE PORTES
echo ==========================================================
echo.
echo     bg00 bg01 bg02 bg03 bg04 bg05 bg06
echo     bg08 bg0a bg0b bg0c bg0d bg0e
echo.
echo   168 fiches. Ce que je te demande de regarder :
echo.
echo     a. L'ETAGE 33 a un objet de plus (script 2, en x 480).
echo     b. Partout ailleurs : rien ne doit avoir bouge.
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe les objets.
echo.
pause

3sx.exe > "%~dp03sx-quatre.log" 2>&1

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
type "%~dp03sx-quatre.log"
echo.
pause
