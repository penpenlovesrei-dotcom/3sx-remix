@echo off
setlocal
cd /d "%~dp0build\application\bin"
if exist "jalons.on" del "jalons.on"

echo ==========================================================
echo   LE SENS DE L'AXE VERTICAL -- UN SEUL ESSAI, TRENTE
echo   SECONDES, ET TOUTE LA CHAINE DEVIENT ORIENTABLE
echo ==========================================================
echo.
echo POURQUOI CET ESSAI
echo.
echo   J'ai deplace la hauteur des sprites trois fois ce soir, et
echo   les trois fois au jugé -- dont sur NECRO, que tu n'avais
echo   pas signale. La cause est unique et je l'ecris en clair :
echo.
echo     JE N'AI JAMAIS VERIFIE DANS QUEL SENS UN `position_y`
echo     CROISSANT DEPLACE UN SPRITE A L'ECRAN.
echo.
echo   Les deux lectures se defendent dans le code -- `bg.c`
echo   applique `njScale(0, 1, -1, 1)` qui inverse le y, mais
echo   `scr_trans` capture `BgMATRIX` AVANT -- et j'ai conclu
echo   dans les deux sens le meme soir. Toute la chaine de
echo   position se reduit a cet axe. Sans lui, chaque correction
echo   de hauteur est un tirage a pile ou face, et j'en ai fait
echo   trois.
echo.
echo CE QUI A ETE CHANGE, ET RIEN D'AUTRE
echo.
echo   L'ACOLYTE DE GILL, etage 22. C'est le seul sprite du port
echo   dont la position soit VALIDEE A L'ECRAN -- 288, 81 -- et
echo   il est FIGE sur son image 0 : impossible de le confondre.
echo.
echo     sa fiche passe de  y 81  a  y 113   (+32)
echo.
echo   Aucun autre sprite, aucun autre etage n'est touche.
echo.
echo CE QUE JE TE DEMANDE DE REGARDER
echo.
echo   VERSUS, etage 22 (GILL). L'acolyte est la figure
echo   encapuchonnee a l'etoile, celle qui se tient debout pres
echo   du temple.
echo.
echo   UNE SEULE QUESTION :
echo.
echo     est-il MONTE ou DESCENDU d'environ 32 pixels ?
echo.
echo   -^> S'il a MONTE  : `position_y` croissant va vers le HAUT.
echo   -^> S'il a DESCENDU : il va vers le BAS.
echo.
echo   Dis-moi juste « monte » ou « descendu ». Avec ca je remets
echo   sa valeur a 81 et je sais enfin dans quel sens corriger
echo   Sean -- au lieu de le deviner.
echo.
echo   (Si tu ne le vois pas bouger du tout, c'est une reponse
echo   aussi, et elle serait tres instructive : ca voudrait dire
echo   que la fiche n'est pas ce qui place l'objet.)
echo.
pause

3sx.exe > "%~dp03sx-axe.log" 2>&1

echo.
echo ================= LES JOURNAUX =================
for %%F in (fin-de-round.log decor-objets.log fatal.log) do (
  if exist "%%F" (
    echo.
    echo ----- %%F -----
    type "%%F"
  )
)
echo.
pause
