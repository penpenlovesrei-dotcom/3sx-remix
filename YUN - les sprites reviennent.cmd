@echo off
rem Deux fautes de moi : la boite prise pour l'empreinte, et l'echelle des profondeurs.

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
echo   « IL MANQUE TOUS LES SPRITES » : DEUX FAUTES, LES DEUX
echo   DE MOI
echo ==========================================================
echo.
echo   1. J'AI PRIS LA BOITE POUR L'EMPREINTE.
echo.
echo      Un objet a une grille -- 5 cases sur 6, par exemple --
echo      mais son sprite n'en remplit qu'une partie. J'effacais
echo      la BOITE entiere, donc aussi la ou l'objet ne peint
echo      JAMAIS rien. Tout ce qu'une cuisson ancienne avait
echo      pose dans le reste de la boite partait, sans que rien
echo      ne le remplace.
echo.
echo      Maintenant l'empreinte est l'UNION DES PIXELS OPAQUES
echo      du sprite sur toutes ses images. Controle : 21 552
echo      pixels changent sur la page, et ZERO hors de
echo      l'empreinte d'un sprite.
echo.
echo      Corollaire trouve au passage : on n'efface PAS
echo      l'empreinte d'un element ecarte. L'element et l'objet
echo      ne sont pas au meme endroit -- la charrette est
echo      element en 303 et objet en 536. L'effacer retirait une
echo      charrette qu'aucun objet ne remplace.
echo.
echo   2. J'AI REPORTE LES PROFONDEURS DE 2I TELLES QUELLES.
echo.
echo      J'avais lu, et c'etait juste : cages 90, charrette 74,
echo      fumeur 91. Mais dans NOTRE moteur les plans de fond
echo      sont a 84, 90 et 94, et un z plus grand est plus loin.
echo      Un objet a 90 ou 91 passe donc DERRIERE le plan
echo      proche : il disparait.
echo.
echo      La valeur est bonne, c'est le REPERE qui differe. Tant
echo      que la correspondance entre les deux echelles n'est
echo      pas etablie -- et elle ne l'est pas -- je remets 0,
echo      qui veut dire « la profondeur du modele ».
echo.
echo ----------------------------------------------------------
echo   LE SCRIPT DE TRANSFERT QUE TU AS DEMANDE
echo ----------------------------------------------------------
echo.
echo   outils/transfert2i.py passe un decor a DOUZE PORTES et
echo   rend un code de sortie. Chaque porte pose une question a
echo   laquelle le BINAIRE doit repondre ; une porte sans
echo   reponse rend MANQUE, pas « probablement ».
echo.
echo      1  le decor est identifie (bande =/= decor)
echo      2  asset et bases de palette connus
echo      3  tous les chargeurs rendent leur carte de champs
echo      4  chaque objet porte x et y (+102/+106)
echo      5  la profondeur (+556 my_priority) est lisible
echo      6  les variantes z sont relevees
echo      7  chaque script se resout en sprites
echo      8  aucune palette verte hors index 0
echo      9  les bornes du moteur sont tenues
echo     10  les scripts animes sont ecartes de la cuisson
echo     11  sous le sprite d'un objet, la page rend la banque
echo     12  les objets a plusieurs scripts sont signales
echo     13  ceux qui suivent les combattants aussi
echo.
echo   YUN LES PASSE TOUTES. C'est ce qui me permet de te
echo   redonner ce build sans te faire deviner.
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER
echo ==========================================================
echo.
echo     a. Les sprites sont-ils revenus -- cages, fumeur,
echo        charrette, vieil homme, dame en rose ?
echo     b. Plus de copie fixe sous eux ?
echo     c. Le panneau vertical est-il a droite, en 852 ?
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe les objets et
echo   montre la page seule -- sous eux, elle porte desormais le
echo   decor du disque, pas notre cuisson.
echo.
pause

3sx.exe > "%~dp03sx-retour.log" 2>&1

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
type "%~dp03sx-retour.log"
echo.
pause
