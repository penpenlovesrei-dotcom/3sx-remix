@echo off
rem Un .pk porte PLUSIEURS conteneurs F_ETC. On n'en lisait qu'un.

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
echo   LES 102 SPRITES HORS-ASSET SONT RETROUVES
echo ==========================================================
echo.
echo   Ils n'etaient nulle part ailleurs que dans le .pk de leur
echo   propre decor. UN .PK PORTE PLUSIEURS CONTENEURS F_ETC, et
echo   `asset_du_decor` ne rendait que celui qui couvre le plus
echo   de scripts. Tous les autres scripts du decor tombaient
echo   alors « hors de son asset ».
echo.
echo   Ou tombaient-ils vraiment, mesure sur les 102 :
echo.
echo      decor 2 et 11 (Ryu, Ken)   b03 : F_ETC25 rendu,
echo                                 images dans F_ETC24
echo      decor 8 (Elena)            b09 : F_ETC31 rendu,
echo                                 images dans F_ETC30
echo      decor 3 et 10 (Yun, Yang)  b04 et b0b se partagent
echo                                 F_ETC26 et F_ETC27
echo.
echo   La liste des conteneurs vient des TABLES DE L'EXECUTABLE,
echo   par decoupe.py -- pas d'une supposition. Et les vingt et
echo   un conteneurs de New Generation sont TOUS deja extraits :
echo   il n'y avait rien a sortir du disque.
echo.
echo ----------------------------------------------------------
echo   LE COMPTE, AVANT ET APRES
echo ----------------------------------------------------------
echo.
echo                                  avant   apres
echo      enregistrements du code       445     445
echo      RESOLUS en sprites            183     285
echo      images hors de tout conteneur 102       0
echo      objets poses a l'ecran        165     197
echo.
echo ----------------------------------------------------------
echo   ET DEUX FAUTES TROUVEES EN CHEMIN
echo ----------------------------------------------------------
echo.
echo   1. LE BUDGET DE NG NE COMPTAIT PAS LES MOTIFS. Il verifie
echo      les rangs (32) et les cases par trame (256), mais pas
echo      la collection de 64 motifs -- la limite que 2I
echo      controle depuis longtemps. En recuperant les 34
echo      premiers objets, l'etage 55 est monte a 76 motifs pour
echo      64. LE MOTEUR NE DIT RIEN DANS CE CAS : il part en
echo      boucle infinie. Ajoutee ; l'etage 55 tient maintenant
echo      exactement 64.
echo.
echo   2. LE PREFIXE DES SYMBOLES N'ETAIT PLUS UNIQUE. Depuis
echo      que deux objets peuvent partager un script a deux
echo      endroits, deux d'entre eux portaient le meme rang et
echo      le C sortait « redefinition of n00o1m1_i0_1_2 ». LA
echo      COMPILATION A ECHOUE, et mon `cp` a quand meme copie
echo      un exe perime -- je l'ai vu et corrige.
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER
echo ==========================================================
echo.
echo   LES DIX-NEUF ETAGES DE NEW GENERATION, encore : 32 objets
echo   de plus, et leur profondeur lue.
echo.
echo     a. Les nouveaux objets sont-ils a leur place ?
echo     b. Rien ne gele ? C'est le point critique : le budget
echo        de motifs vient d'etre ajoute, et s'il manque encore
echo        une limite, ca se verra par un blocage.
echo.
echo   RESTE CONNU ET NON RESOLU : dix cases de palette vertes
echo   employees sur l'etage ng05, et aucun decalage de base ne
echo   les supprime -- ce n'est donc pas une base fausse.
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe les objets.
echo.
pause

3sx.exe > "%~dp03sx-ng2.log" 2>&1

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
type "%~dp03sx-ng2.log"
echo.
pause
