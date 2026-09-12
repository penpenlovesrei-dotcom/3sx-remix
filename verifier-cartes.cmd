@echo off
rem Rejoue la demonstration sur bg_map_tbl / stageXXX_map[64].
rem Sans argument : la demonstration. Avec  cartes  : les 42 cartes dessinees.
setlocal
set OUTILS=C:\Users\frede\Downloads\3sx-outils\dc-decors\outils
cd /d "%OUTILS%"
if /i "%~1"=="cartes" (
    python cartesbg.py --cartes
) else (
    python cartesbg.py
)
echo.
pause
