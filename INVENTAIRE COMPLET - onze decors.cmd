@echo off
rem L'inventaire complet des quinze decors, et ce qu'il restait a trouver.

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
echo   NON, JE N'AVAIS PAS FINI. VOICI CE QUI MANQUAIT.
echo ==========================================================
echo.
echo   1. LE PARCOURS PARTAGEAIT SON « DEJA VU » ENTRE LES
echo      BANDES. Les cinq gros chargeurs servent de huit a
echo      quatorze decors chacun : le premier qui atteignait
echo      8C028792 se l'appropriait, les autres le perdaient.
echo      Sean n'avait plus que TROIS fonctions atteintes.
echo      Corrige : 553 FONCTIONS AU LIEU DE 97.
echo.
echo   2. QUATRE DECORS NE RECEVAIENT AUCUN NETTOYAGE de page
echo      (bg07, bg09, ORO, bg0f) : pas d'element dans
echo      l'annuaire, donc la boucle sortait avant. Leurs objets
echo      sont pourtant poses.
echo.
echo   3. BG08 N'ETAIT JAMAIS NETTOYE : les deux chaines ne le
echo      nomment pas pareil (bg08 / bg09). On apparie desormais
echo      par ETAGE.
echo.
echo   4. ORO PERDAIT UN OBJET : son bloc 0x8C17DCFA n'avait pas
echo      de `sc2`, donc on lisait le repos -- script 15, ZERO
echo      image -- au lieu de l'action, script 16.
echo.
echo   5. ET HUGO PERDAIT LE SIEN, invisible aux DEUX
echo      inventaires : `blocs2i` ne lit que les chargeurs a
echo      bloc, et la recherche « script en constante » ne le
echo      voyait pas non plus, parce que son script n'est nulle
echo      part dans le spawner.
echo.
echo      Il a fallu chainer les trois outils : 8C031B56 alloue,
echo      pose l'id 63, et ecrit x 816, y 52, palette 74 en
echo      constantes ; puis sa ROUTINE (8C031918) pose trois
echo      scripts -- 30 (une image), 32 (trois) et 34 (VINGT ET
echo      UNE). On prend le plus riche.
echo.
echo ----------------------------------------------------------
echo   CE QUI EST MAINTENANT ETABLI
echo ----------------------------------------------------------
echo.
echo   Les ONZE decors passent les DOUZE PORTES.
echo   167 fiches, 96 000 pixels de cuisson retires.
echo.
echo   Et les decors 11, 13 et 16 n'ont RIEN de plus : le bloc
echo   que je croyais au 11 appartient au 12 (meme bloc atteint
echo   par deux bandes), et le 16 est le Hugo bis que je viens
echo   d'ajouter. Ce n'est pas une lacune, c'est une mesure.
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER
echo ==========================================================
echo.
echo   TOUS LES ETAGES ont change. Deux objets NOUVEAUX :
echo.
echo     a. ORO (31)  : un objet de plus, script 16.
echo     b. HUGO (28) : un objet de plus en x 816, script 34,
echo        vingt et une images.
echo     c. Et partout : plus aucune copie fixe sous un sprite
echo        anime -- ni rien qui manque.
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe les objets.
echo.
pause

3sx.exe > "%~dp03sx-inventaire.log" 2>&1

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
type "%~dp03sx-inventaire.log"
echo.
pause
