@echo off
rem Genere les tables francaises depuis le catalogue traduit, apres verification.
rem Les blocs non traduits restent en anglais : on peut generer a tout moment.

rem --- Ou ecrire -------------------------------------------------------------
rem Vide  : dans traduction\message_fr\, sans toucher a aucun clone.
rem Sinon : la racine du clone de travail, et les fichiers vont directement dans
rem         son src\sf33rd\Source\Game\message\fr\. Exemple :
rem             set CIBLE=C:\3sx-fr
set CIBLE=
rem ---------------------------------------------------------------------------

cd /d "%~dp0"

rem C:\3sx-up est le clone de reference, lu seulement, jamais ecrit.
set AMONT=C:\3sx-up\src\sf33rd\Source\Game\message\en
if not exist "%AMONT%" goto pas_damont
if not exist traduction\fr.txt goto pas_de_catalogue

if "%CIBLE%"=="" (
    set SORTIE=%~dp0traduction\message_fr
) else (
    set SORTIE=%CIBLE%\src\sf33rd\Source\Game\message\fr
)

python tools\msg_build.py --catalogue traduction\fr.txt --lang fr ^
    --source "%AMONT%" --sortie "%SORTIE%"
if errorlevel 1 goto refuse

echo.
echo --- Relecture par le lecteur du jeu -------------------------------------
python tools\msg_verifier.py --amont C:\3sx-up --genere "%SORTIE%"
if errorlevel 1 goto relecture_ratee
echo -------------------------------------------------------------------------

echo.
echo Genere dans %SORTIE%
if "%CIBLE%"=="" (
    echo.
    echo Aucun clone n'a ete touche. Pour compiler, copiez ce dossier dans
    echo   ^<clone^>\src\sf33rd\Source\Game\message\fr
    echo ou renseignez CIBLE en tete de ce fichier.
) else (
    echo Le CMakeLists de l'amont prend ces fichiers tout seul.
)
echo.
echo Il reste a brancher la langue dans le code : voir la section
echo "Brancher la langue" de docs\traduction_texte.md
pause
goto :eof

:pas_damont
echo.
echo Clone amont introuvable : %AMONT%
pause
goto :eof

:pas_de_catalogue
echo.
echo Pas de catalogue. Lancez d'abord traduire-extraire.cmd
pause
goto :eof

:refuse
echo.
echo Rien n'a ete ecrit : il reste des ERREUR ci-dessus.
echo Chacune donne le bloc et la ligne. Corrigez traduction\fr.txt et relancez.
pause
goto :eof

:relecture_ratee
echo.
echo Les fichiers sont ecrits, MAIS la relecture ne retombe pas sur le texte
echo attendu. Ne compilez pas ca : les lignes fautives sont listees ci-dessus.
pause
