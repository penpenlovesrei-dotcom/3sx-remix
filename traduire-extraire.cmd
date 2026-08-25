@echo off
rem Extrait les citations, dialogues et fins de l'amont vers le catalogue a traduire.
rem Relancable : les blocs deja traduits sont conserves.

cd /d "%~dp0"

set AMONT=C:\3sx-up\src\sf33rd\Source\Game\message\en
if not exist "%AMONT%" goto pas_damont

python tools\msg_extract.py --source "%AMONT%" --sortie traduction\fr.txt
if errorlevel 1 goto rate

echo.
echo Le catalogue est dans traduction\fr.txt
echo   Les lignes qui commencent par = sont l'anglais, en lecture seule.
echo   Ecrivez la traduction sur les lignes qui suivent, une par ligne d'origine.
echo   Les accents s'ecrivent normalement : le generateur s'en occupe.
echo   Ne depassez pas la colonne 43.
echo.
echo Quand c'est rempli, meme partiellement : traduire-generer.cmd
pause
goto :eof

:pas_damont
echo.
echo Dossier amont introuvable :
echo   %AMONT%
echo.
echo Ce chantier est du code amont. Il faut un clone de crowded-street/3sx.
pause
goto :eof

:rate
echo.
echo Echec de l'extraction.
pause
