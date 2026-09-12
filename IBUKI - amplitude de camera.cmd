@echo off
rem Ibuki (etage 29) : l'amplitude de camera, lue dans le code de 2nd Impact.

cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   IBUKI (etage 29) : L'AMPLITUDE DE CAMERA
echo ==========================================================
echo.
echo CE QUE LE CODE DE 2nd IMPACT DIT, EN 0x8C0D9C26
echo.
echo     r13 = 0                        borne basse
echo     r3  = u8 [0x8C841F3C]          un drapeau global
echo     r14 = 495  si drapeau != 0
echo     r14 = 383  si drapeau == 0
echo     puis  clamp(position, 0, r14)
echo.
echo   IL N'Y A AUCUNE LIMITE PAR ETAGE dans 2nd Impact. Deux
echo   amplitudes globales, et c'est tout. Les bornes elles-memes
echo   viennent de la position des deux combattants (joueur+96)
echo   et d'une demi-largeur par personnage -- une table indexee
echo   par joueur+856, avec un pas de 1036 entre les deux.
echo.
echo   Les limites que nos quinze etages portaient a la main sont
echo   donc des inventions. Le code n'en propose que deux.
echo.
echo LA CORRESPONDANCE QUI CALE TOUT
echo.
echo     383 de course  ->  0x140..0x2c0   le DEFAUT de 3rd Strike
echo     495 de course  ->  0x108..0x2F8   512 +/- 248
echo.
echo   La premiere tombe exactement sur la valeur que 3rd Strike
echo   emploie deja. La seconde est celle qu'on essaie ici.
echo.
echo   Ibuki passe de 448 a 496 pixels jouables. C'est PLUS LARGE
echo   qu'avant, dans le sens de ton « moins large que sur
echo   Dreamcast ».
echo.
echo CE QUE JE CHERCHE
echo.
echo   a. L'amplitude est-elle la bonne, maintenant ? En reculant
echo      les deux combattants aux bords opposes, atteins-tu les
echo      memes extremes que sur Dreamcast ?
echo   b. Si c'est encore trop etroit, c'est que le drapeau vaut
echo      0 et qu'il faut chercher ailleurs -- mais alors on
echo      serait a 384, encore moins. Donc si ca ne suffit pas,
echo      l'amplitude n'est pas la cause.
echo   c. La cascade qui apparait la ou la Dreamcast n'en a pas :
echo      est-ce que ca change ?
echo.
echo   RAPPEL : je n'ai touche QUE l'etage 29. Les quatorze autres
echo   gardent leurs valeurs, Akuma compris, qui est valide.
echo.
pause

3sx.exe > "%~dp03sx-ibuki.log" 2>&1

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
type "%~dp03sx-ibuki.log"
echo.
pause
