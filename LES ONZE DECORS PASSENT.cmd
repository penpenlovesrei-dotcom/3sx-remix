@echo off
rem Le balayage systematique des onze decors, et ce qu'il a trouve.

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
echo   TU AVAIS RAISON : JE N'AVAIS PAS LA CONNAISSANCE
echo ==========================================================
echo.
echo   LA FAUTE TENAIT A UNE LIGNE. Mon inventaire marchait dans
echo   l'arbre d'appels de chaque routine d'etage avec UN SEUL
echo   ensemble « deja vu », partage entre toutes les bandes. Or
echo   les cinq gros chargeurs servent de huit a quatorze decors
echo   chacun : LE PREMIER DECOR QUI ATTEIGNAIT 8C028792 SE
echo   L'APPROPRIAIT, ET TOUS LES AUTRES LE PERDAIENT.
echo.
echo   Sean se retrouvait avec TROIS fonctions atteintes, aucune
echo   n'ecrivant un champ d'objet -- alors que ses trois objets
echo   viennent justement de ce chargeur.
echo.
echo   CORRIGE : 553 FONCTIONS AU LIEU DE 97. Un facteur 5,7.
echo   Toutes mes mesures « sur les 97 fonctions » etaient donc
echo   fausses, et je les ai refaites.
echo.
echo ----------------------------------------------------------
echo   CE QUE LE BALAYAGE COMPLET A TROUVE
echo ----------------------------------------------------------
echo.
echo   96 000 PIXELS DE CUISSON retires sous des sprites animes,
echo   sur huit decors -- dont 51 239 pour bg0b et 6 191 pour
echo   ORO, que tu n'avais jamais signales.
echo.
echo   QUATRE DECORS NE RECEVAIENT AUCUN NETTOYAGE (bg07, bg09,
echo   ORO, bg0f) : ils n'ont pas d'element dans l'annuaire, et
echo   la boucle sortait avant. Leurs objets sont pourtant poses.
echo.
echo   BG08 N'ETAIT JAMAIS NETTOYE : poser2i appelle son etage
echo   bg09 et les fiches l'appellent bg08. On apparie desormais
echo   par ETAGE, qui est sans ambiguite.
echo.
echo   ORO PERDAIT UN OBJET : son bloc 0x8C17DCFA n'avait pas de
echo   `sc2`, donc on lisait le repos -- script 15, ZERO image --
echo   au lieu de l'action, script 16, deux images.
echo.
echo   ET UNE DE MES PORTES ETAIT TROP LARGE : elle exigeait une
echo   carte de champs de TOUTE fonction atteinte, y compris les
echo   vingt-cinq utilitaires du moteur qui ne voient jamais un
echo   objet. Elle ne la demande plus qu'a celles qui ALLOUENT ou
echo   qui POSENT UN SCRIPT.
echo.
echo ----------------------------------------------------------
echo   L'ETAT, DECOR PAR DECOR
echo ----------------------------------------------------------
echo.
echo     bg00 bg01 bg02 bg03 bg04 bg05      les DOUZE PORTES
echo     bg06 bg08 bg0a bg0b bg0d           passent, pour les
echo                                        ONZE decors.
echo.
echo   Un piege de comparaison, note pour ne pas y retomber :
echo   « le code donne ce script et la chaine ne le pose pas »
echo   compte a tort l'autre moitie d'une paire repos/action.
echo   Sur sept ecarts releves, SIX etaient de ce type. Un seul
echo   etait un vrai manque -- celui d'Oro.
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER
echo ==========================================================
echo.
echo   TOUS LES ETAGES DE 22 A 36 ont vu leur page changer.
echo   Ce que je cherche a savoir :
echo.
echo     a. Plus aucune copie fixe sous un sprite anime, nulle
echo        part ?
echo     b. RIEN NE MANQUE ? C'est le risque de ce correctif, et
echo        il porte cette fois sur onze decors.
echo     c. ORO : un objet de plus (script 16), et 6 191 pixels
echo        de cuisson en moins.
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe les objets et
echo   montre la page seule.
echo.
pause

3sx.exe > "%~dp03sx-onze.log" 2>&1

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
type "%~dp03sx-onze.log"
echo.
pause
