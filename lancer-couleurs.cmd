@echo off
rem 3SX tout-en-un : musique, couleurs et francais dans un seul binaire.

cd /d "%~dp0build\application\bin"

echo Lancement de 3SX...
echo.
echo LES TROIS CHANTIERS SONT DANS CE BINAIRE :
echo.
echo   Musique   Options ^> Sound ^> BGM TYPE, et l'ecran Custom
echo   Couleurs  Options ^> Display ^> CHAR. COLOR et COLOR EDIT
echo             plus le cycle START sur l'ecran de selection
echo   Francais  Options ^> Screen Adjust ^> LANGUAGE : EN, JP, FR
echo             (citations, dialogues d'avant-combat et fins)
echo.
echo A VERIFIER - la remontee d'amont a realigne les tables de menu,
echo et un decalage donne un libelle faux, jamais un plantage :
echo.
echo   1. Les lignes de Display portent leur nom et leurs valeurs.
echo   2. COLOR EDIT : bon personnage, captions R G B, lignes
echo      COLOR et SAVE avec leurs valeurs.
echo   3. Options ^> Sound : rangees, BGM TYPE, et EXIT qui sort.
echo   4. LANGUAGE sur FR : les fins et les dialogues en francais,
echo      accents compris.
echo.
echo ATTENTION : la sauvegarde retient la langue. Un binaire qui ne
echo connait pas FR et qui relit ce profil lirait une entree vide.
echo.

3sx.exe > "%~dp03sx-couleurs.log" 2>&1

echo.
echo Log : %~dp03sx-couleurs.log
pause
