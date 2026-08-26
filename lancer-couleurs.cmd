@echo off
rem Lance 3SX : COLOR EDIT avec choix du jeu de couleurs et SAVE par bouton.

cd /d "%~dp0build\application\bin"

echo Lancement de 3SX...
echo.
echo Options ^> Display ^> COLOR EDIT ^> un personnage
echo.
echo L'ecran porte maintenant trois valeurs :
echo   ligne du NOM   le bouton qui donne la couleur affichee (LP, MP...)
echo   COLOR          3RD STRIKE / NEW GEN / 2ND IMPACT / COLOR EDIT
echo   SAVE           le bouton sur lequel SAVE va ecrire
echo.
echo Commandes :
echo   Croix / Rond   descendent et remontent : lignes ^<-^> grille ^<-^> barres
echo   L1 / R1        change la couleur editee, et son nom de bouton
echo   L2 / R2        change la pose
echo   Gauche/Droite  sur la ligne COLOR : change le jeu de couleurs
echo                  sur la ligne SAVE  : change le bouton de destination
echo   Croix          sur la ligne SAVE  : ecrit le fichier
echo.
echo A verifier :
echo   1. Les trois valeurs s'affichent et changent bien.
echo   2. Sur COLOR, passer a NEW GEN ou 2ND IMPACT doit changer les
echo      couleurs du combattant. Un jeu non installe pour ce
echo      personnage doit etre SAUTE, jamais affiche a vide.
echo   3. Les noms de boutons vont LP MP HP LK MK HK LP+HP+MK,
echo      puis ST+LP a ST+HK, puis trois tirets.
echo.

3sx.exe > "%~dp03sx-couleurs.log" 2>&1

echo.
echo --- fichiers ecrits par SAVE ---
dir /b "%APPDATA%\CrowdedStreet\3SX\resources\pal_remix\color-edit" 2>nul || echo (aucun)
echo --------------------------------
echo.
echo Log : %~dp03sx-couleurs.log
pause
