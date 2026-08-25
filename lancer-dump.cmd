@echo off
rem Lance 3SX avec tex-remix-dump actif et garde la sortie dans un log.
rem Le jeu doit demarrer depuis son dossier d'installation : shaders et assets y vivent.

cd /d "%~dp0build\application\bin"

echo Lancement de 3SX...
echo Va sur l'ecran de selection et balaye le curseur sur tous les personnages,
echo puis quitte le jeu normalement (pas par le gestionnaire des taches).
echo.

3sx.exe > "%~dp03sx-dump.log" 2>&1

echo.
echo Termine. Log : %~dp03sx-dump.log
echo Manifeste : %%APPDATA%%\CrowdedStreet\3SX\resources\tex_remix\dump\manifest.txt
pause
