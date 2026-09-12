@echo off
rem New Generation traite comme 2nd Impact : la profondeur lue, plus reglee.

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
echo   NEW GENERATION : LE MEME DEFAUT, LA MEME CORRECTION
echo ==========================================================
echo.
echo   NG posait 165 objets, et leur profondeur tenait en deux
echo   valeurs, toutes deux a l'oeil :
echo.
echo      plan 1  -^>  z = 92
echo      le reste -^>  z = 0
echo.
echo   Or l'enregistrement de NG porte les MEMES champs que
echo   celui de 2I -- +32, +558 my_family, +554 my_col_code,
echo   +102 x, +106 y, +88 palette, +456 script -- et le
echo   chargeur ecrit cette palette une SECONDE fois, en +556,
echo   my_priority.
echo.
echo   VERIFIE DANS SF3_1ST.BIN, sur trois lecteurs :
echo.
echo      8C0A0070    +88 ^<- r3   puis  +556 ^<- r3
echo      8C0AC75C    +88 ^<- r3   puis  +556 ^<- r3
echo      8C0AC934    +88 ^<- r3   puis  +556 ^<- r3
echo.
echo   Meme registre, ecritures consecutives : exactement le
echo   motif de 2nd Impact. Et l'echelle est la meme des deux
echo   cotes -- les fiches de combattant portent des my_pr de 28
echo   a 56, comme char_init_data2 de 3S.
echo.
echo   RESULTAT : 164 des 165 fiches de NG ont maintenant une
echo   profondeur LUE, et il y a 29 valeurs distinctes la ou il
echo   n'y en avait que deux.
echo.
echo   LA 165e RESTE A ZERO, et c'est dit : elle vient de
echo   8C0A1A40, le seul lecteur de NG qui n'ecrit PAS +556 --
echo   six champs au lieu de neuf. Son objet garde donc la
echo   profondeur du modele.
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER
echo ==========================================================
echo.
echo   LES DIX-NEUF ETAGES DE NEW GENERATION. Le changement est
echo   massif : chaque objet passe d'une profondeur inventee a
echo   la sienne. Les superpositions vont donc bouger PARTOUT.
echo.
echo     a. Les objets sont-ils dans le bon ordre les uns par
echo        rapport aux autres ?
echo     b. Certains passent devant les combattants -- il y a
echo        des profondeurs a 2, 18, 20, 22 -- alors que les
echo        combattants sont a 28-56. C'est ce que dit le code,
echo        mais c'est spectaculaire : dis-moi si ca te parait
echo        juste.
echo     c. Les cascades d'Oro NG (plan 1) changent aussi.
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe les objets.
echo.
pause

3sx.exe > "%~dp03sx-ng.log" 2>&1

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
type "%~dp03sx-ng.log"
echo.
pause
