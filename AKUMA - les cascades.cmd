@echo off
rem Les deux cascades d'Akuma et l'entree de la grotte, animees.

cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   AKUMA (etage 36) : LES CASCADES
echo ==========================================================
echo.
echo CE QUE J'AI TROUVE DANS LE JEU
echo.
echo   Le mecanisme d'animation de pages de 2nd Impact est
echo   sorti en entier du binaire, et il est le meme qu'en
echo   3rd Strike :
echo.
echo     0x8C0277C4(k)          cree l'objet ; k va en +4
echo     0x8C17D8DC + k*20      { plan, slot, suite, ... }
echo     la suite = des paires [duree, page], -1 = fin, ca boucle
echo     0x8C17D3DC + k*2       le decalage de DESTINATION
echo.
echo   Et ce decalage vaut  4 * (index du bloc 16x16 dans un
echo   plan large de 1024). Il donne donc x et y au pixel pres.
echo.
echo   L'APPELANT donne l'appartenance, et lui seul : l'etage 15
echo   -- Akuma -- appelle les entrees 8, 9 et 10. Que l'etage 15
echo   soit bien bg0f n'est plus une supposition : les neuf index
echo   de palette que les scripts passent en dur tombent tous sur
echo   la bande de meme numero. Huit sur huit.
echo.
echo LES TROIS ANIMATIONS
echo.
echo   entree 8   plan 0   x144 y64    6 images de 304x144
echo              LA GRANDE CASCADE
echo   entree 9   plan 0   x400 y128   4 images de 48x128
echo              la chute fine du fond
echo   entree 10  plan 1   x688 y144   2 images de 80x64
echo              l'entree de la grotte
echo.
echo   Chaque image dure 4 trames, et ca boucle.
echo.
echo   Deux mesures independantes se rejoignent : les trois
echo   destinations calculees tombent EXACTEMENT sur les trois
echo   seules fenetres entierement transparentes des plans, que
echo   la recherche de trous avait elues separement. Et la
echo   decoupe du magasin se mesure aussi : les six tuiles de
echo   304x144 s'ecartent de 0,6 a 1,1 entre elles, contre 70
echo   pour deux decoupes au hasard du meme bloc. Un facteur
echo   soixante-dix : ce sont bien six trames d'une image.
echo.
echo   La grande cascade fait 19x9 = 171 cases, pour une cle de
echo   cache qui n'en porte que 32. Elle est donc SERVIE en sept
echo   objets voisins qui se rejoignent au pixel pres -- pas
echo   retaillee. Chacun porte sa propre palette, ce qui regle
echo   au passage ses 81 couleurs sur toute la largeur.
echo.
echo CE QUE JE CHERCHE
echo.
echo   a. Les deux cascades coulent-elles ?
echo   b. La grande est-elle d'un seul tenant, sans couture
echo      visible entre ses sept morceaux ?
echo   c. Sont-elles a la bonne PROFONDEUR ? Les deux sont sur
echo      le plan du fond ; je leur ai mis famille 1 et z 92,
echo      par analogie avec la grotte d'Oro. C'est le seul
echo      chiffre que le binaire ne m'a pas donne.
echo   d. L'entree de la grotte est-elle toujours en place ?
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe tous les objets
echo   animes sans toucher au decor.
echo.
pause

3sx.exe > "%~dp03sx-akuma.log" 2>&1

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
type "%~dp03sx-akuma.log"
echo.
pause
