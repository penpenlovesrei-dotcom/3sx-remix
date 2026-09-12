@echo off
rem +556 = my_priority. Trouve en alignant +552 sur my_col_mode.

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
echo   J'AVAIS DIT QUE LA PROFONDEUR N'ETAIT PAS DANS LES
echo   DONNEES. C'ETAIT FAUX.
echo ==========================================================
echo.
echo   Je l'avais cherchee a +76, un offset que j'avais calcule
echo   dans une structure du port qui fait 140 octets et n'a
echo   rien a voir avec l'objet de 2I. Toute la conclusion qui
echo   en decoulait tombe.
echo.
echo ----------------------------------------------------------
echo   L'ANCRE QUI NOMME TOUT
echo ----------------------------------------------------------
echo.
echo   J'ai ecrit l'analyseur des spawners a immediats que tu
echo   as demande. Il rejoue la fonction instruction par
echo   instruction et releve chaque constante ecrite dans
echo   l'objet. Les trois spawners sans bloc de Yun -- les
echo   cages, la charrette, le fumeur -- ecrivent TOUS 0x4200
echo   en +552.
echo.
echo   0x4200, c'est exactement ce que eff05.c pose dans
echo   my_col_mode. En alignant les deux, les champs suivants
echo   se nomment seuls :
echo.
echo        +552  my_col_mode  (0x4200)
echo        +554  my_col_code
echo        +556  my_priority   ^<-- LA PROFONDEUR
echo        +558  my_family     ^<-- notre « plan », qui vaut 2
echo.
echo   ET LES VALEURS REPONDENT A CE QUE TU VOIS :
echo.
echo        les cages     +556 = 90
echo        le fumeur     +556 = 91
echo        la charrette  +556 = 74
echo.
echo   Un z plus GRAND est plus LOIN. Les cages (90) passent
echo   donc devant le fumeur (91), et la charrette (74) devant
echo   les deux. C'est ton observation, mais la valeur vient du
echo   binaire -- je ne l'ai pas reglee.
echo.
echo ----------------------------------------------------------
echo   CE QUI N'EST PAS ENCORE FAIT, ET POURQUOI
echo ----------------------------------------------------------
echo.
echo   LE PANNEAU AU PREMIER PLAN. Sa profondeur devrait venir
echo   de son bloc. Le nouvel outil montre que le chargeur
echo   0x8C02356A ECRIT bien +556 -- mais spawners2i ne le liste
echo   pas dans ses champs. Il manque un champ a sa carte, le
echo   meme defaut que l'enregistrement de 24 octets qu'il
echo   lisait comme 22. C'est le prochain pas, et il est precis.
echo.
echo   LES OISEAUX. Le script 7, ce sont les deux cages, UNE
echo   image, sans oiseau dedans. Leur animation est un autre
echo   objet que rien de ce que j'ai decode ne cree.
echo.
echo   LES COPIES DU VIEUX ET DE LA DAME. Ce n'est pas un
echo   probleme d'objet : la page du decor contient leurs images
echo   fixes et l'objet anime passe par-dessus sans les couvrir
echo   a toutes les trames. Meme defaut de composition des pages
echo   que les bandes noires d'Ibuki.
echo.
echo   LE PUNK DE DUDLEY reste un reglage a l'oeil : son bloc de
echo   24 octets ne donne pas +556.
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER
echo ==========================================================
echo.
echo   YUN (25), et lui seul :
echo     a. Les cages sont-elles DEVANT le fumeur ?
echo     b. Le conflit entre les cages et l'etal jaune est-il
echo        resolu ?
echo     c. La charrette est-elle devant les deux ?
echo.
echo   Le panneau n'a PAS bouge : il est toujours en 852, sur le
echo   plan des autres. C'est le prochain pas.
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe tous les objets
echo   animes sans toucher au decor.
echo.
pause

3sx.exe > "%~dp03sx-prio.log" 2>&1

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
type "%~dp03sx-prio.log"
echo.
pause
