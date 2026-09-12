@echo off
rem Ce lanceur DEPLOIE l'exe lui-meme : plus de version perimee possible.

echo ==========================================================
echo   DEPLOIEMENT DE L'EXE
echo ==========================================================
echo.
if not exist "%~dp0build\3sx.exe" (
  echo   ERREUR : build\3sx.exe est introuvable.
  pause
  exit /b 1
)
copy /y "%~dp0build\3sx.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
if errorlevel 1 (
  echo   ECHEC DE LA COPIE -- une autre instance du jeu est
  echo   ouverte et VERROUILLE le fichier. Ferme-la, puis
  echo   relance ce lanceur.
  echo.
  pause
  exit /b 1
)
echo   exe deploye.
echo.
for %%F in ("%~dp0build\application\bin\3sx.exe") do echo   date du binaire : %%~tF
echo.

cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   POURQUOI JE T'AI FAIT TOURNER EN ROND
echo ==========================================================
echo.
echo   Tu as raison de t'arreter. Quatre fautes, nommees :
echo.
echo   1. J'AI DEPLACE LA FEMME EN ROSE SUR UN ACCORD A 69 %%,
echo      alors que j'avais ecrit la regle « jamais en dessous
echo      de 90 %% » dans le meme fichier, dix lignes plus haut.
echo.
echo   2. J'AI RETIRE LES CAGES AU LIEU DU PANNEAU. J'ai
echo      identifie « le sprite devant le fumeur » en comparant
echo      des boites englobantes au lieu de REGARDER. Les cages
echo      sont bien dans l'original -- elles y sont PEINTES, ce
echo      qui rend leur retrait juste, mais par accident.
echo.
echo   3. IBUKI ET ORO : je n'ai RIEN CHANGE et j'ai livre des
echo      mesures en le presentant comme un resultat.
echo.
echo   4. ET LA PLUS GRAVE : « le binaire dit 696 » etait FAUX.
echo.
echo ----------------------------------------------------------
echo   CE QUE J'AI TROUVE EN CHERCHANT MON ERREUR
echo ----------------------------------------------------------
echo.
echo   Le bloc du panneau est REEL -- le spawner 0x8C028E62 le
echo   lit, dix octets, trois tours. Mais voici ses champs, lus
echo   dans le code :
echo.
echo        champ 0  -^>  +456   le script
echo        champ 1  -^>  +84
echo        champ 2  -^>  +86
echo        champ 3  -^>  +556
echo.
echo   LA POSITION D'UN OBJET EST EN +102 / +106. Ce spawner ne
echo   l'ecrit JAMAIS. Que +84/+86 soit la position, c'etait une
echo   ANALOGIE avec les spawners voisins -- pas une lecture.
echo   Et tes captures la contredisent trois fois de suite.
echo.
echo   J'AI DONC RETIRE LES DEUX OBJETS QUI EN VENAIENT : le
echo   panneau vertical (script 0) et les paniers (script 4,
echo   peints de toute facon). Le fumeur est degage. Ils
echo   reviendront quand je saurai LIRE leur position.
echo.
echo ----------------------------------------------------------
echo   ET UNE MESURE QUI RELIE TES TROIS PLAINTES
echo ----------------------------------------------------------
echo.
echo   J'ai mesure, pour les dix-sept etages, les colonnes ou
echo   AUCUN plan ne peint rien. HUIT ETAGES ONT LA BANDE
echo   TRONQUEE AUX DEUX BOUTS :
echo.
echo      22, 36, 57   vides de 0-127 et 896-1023   256 px
echo      25, 32, 34, 35  vides de 32-127 et 896-1023  224 px
echo      56           vide de 0-255 et 768-1023    512 px
echo      26           vide de 944-1023              80 px
echo.
echo      23, 24, 27, 28, 29, 30, 31, 33 : COMPLETS
echo.
echo   YUN (25) EST DANS LE LOT. Sa page s'arrete a 896, et ta
echo   capture Dreamcast montre le panneau et la suite des
echo   portes rouges precisement LA. Le panneau n'a pas de
echo   place chez nous parce que le decor n'a pas ete extrait
echo   jusqu'au bout.
echo.
echo   IBUKI (29), EN REVANCHE, EST COMPLET a l'union de ses
echo   trois plans. Ce que j'ai dit la derniere fois etait donc
echo   trop rapide : ses bandes noires ne viennent pas d'un
echo   trou d'extraction, mais du fait que chaque plan defile a
echo   sa propre vitesse -- le trou d'un plan expose le plan
echo   suivant a un ENDROIT DECALE, qui peut etre vide lui
echo   aussi. C'est un defaut de parallaxe, pas de donnee, et
echo   je ne l'ai pas encore corrige.
echo.
echo ==========================================================
echo   CE QUE JE TE PROPOSE
echo ==========================================================
echo.
echo   Le vrai chantier n'est pas d'ajuster des objets un par
echo   un : c'est L'EXTRACTION TRONQUEE, qui touche huit etages
echo   d'un coup et explique le panneau sans place.
echo.
echo   Dis-moi si je pars la-dessus, ou si tu preferes qu'on
echo   reprenne Ibuki d'abord.
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe tous les objets
echo   animes sans toucher au decor.
echo.
pause

3sx.exe > "%~dp03sx-pause.log" 2>&1

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
type "%~dp03sx-pause.log"
echo.
pause
