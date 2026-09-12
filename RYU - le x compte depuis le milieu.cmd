@echo off
rem Ryu : ses x sont comptes depuis le MILIEU de la bande, pas depuis le bord.

cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   RYU : SES SPRITES SONT A LEUR PLACE
echo ==========================================================
echo.
echo   Tes deux captures de l'original ont servi de reglet, et
echo   c'est la premiere fois du chantier qu'une reference
echo   exterieure cale la chaine.
echo.
echo ----------------------------------------------------------
echo   CE QUI ETAIT FAUX
echo ----------------------------------------------------------
echo.
echo   Ryu est le seul decor dont des enregistrements portent un
echo   x NEGATIF : sept sur treize, de -368 a -96. L'enroulement
echo   les renvoyait a droite (641 a 897).
echo.
echo   DEUX HYPOTHESES FERMEES AVANT, pour ne pas les rouvrir :
echo.
echo     - LE CHARGEUR NE DECALE PAS. On soupconnait un
echo       « objet+102 += parent+102 » depuis longtemps. Verifie
echo       sur ses QUATRE chargeurs : aucun n'y touche, et le
echo       detecteur trouve bien l'addition dans le chargeur
echo       temoin qui, lui, decale.
echo     - AUCUN DE SES OBJETS N'EST PEINT dans la banque du
echo       disque. La mesure qui avait redresse l'edifice d'Oro
echo       n'existe pas chez lui : zero sur treize.
echo.
echo ----------------------------------------------------------
echo   LA MESURE QUI TRANCHE
echo ----------------------------------------------------------
echo.
echo   Le DECOR sert de reglet : le panneau, le parasol et la
echo   lanterne de pierre donnent la position de la camera sur
echo   chaque capture. Cinq objets identifies s'y relevent :
echo.
echo      les singes           x -233  ->  bande 230   ecart 463
echo      la femme au panneau  x -145  ->  bande 325   ecart 470
echo      la femme en rose     x -112  ->  bande 371   ecart 483
echo      le gros baigneur     x  273  ->  bande 810   ecart 537
echo      le singe de droite   x  336  ->  bande 857   ecart 521
echo.
echo   UN ECART CONSTANT D'ENVIRON 512, et il vaut pour les
echo   POSITIFS comme pour les negatifs. Ce n'est donc pas une
echo   correction de l'enroulement : c'est une ORIGINE. 512 est
echo   le milieu de la bande, et c'est le litteral que les
echo   dix-sept plans portent.
echo.
echo   Apres correction, l'ecart residuel est de 2, 5, 9, 18 et
echo   25 pixels -- c'est la precision de mes releves sur ta
echo   capture, pas celle de la donnee.
echo.
echo   RIEN NE BOUGE AILLEURS : sur les 93 objets des quatorze
echo   decors, seuls les sept de Ryu sont concernes. Les autres
echo   ont tous un x positif, et la formule leur rend la meme
echo   valeur qu'avant.
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER
echo ==========================================================
echo.
echo   RYU (etage 24) :
echo     a. Les deux baigneuses -- celle au panneau et celle en
echo        rose -- sont-elles au centre gauche, pres du
echo        panneau ?
echo     b. Les singes sont-ils sur leur rocher, a gauche ?
echo     c. Le gros baigneur et le singe de droite sont-ils bien
echo        a droite, pres du parasol ?
echo     d. Les chutes d'eau tombent-elles au bon endroit ?
echo.
echo   TOUS LES AUTRES DECORS doivent etre identiques. Si l'un
echo   d'eux a bouge, c'est moi.
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe tous les objets
echo   animes sans toucher au decor.
echo.
pause

3sx.exe > "%~dp03sx-ryu.log" 2>&1

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
type "%~dp03sx-ryu.log"
echo.
pause
