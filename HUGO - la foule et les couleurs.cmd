@echo off
rem Deux verrous levés d'un coup : les objets à plus de 63 couleurs, et le vert fluo.

cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   HUGO : SA FOULE SORT, ET LE VERT A DISPARU
echo ==========================================================
echo.
echo   ETAGE 28 (HUGO) passe de 6 a 11 objets. Et le VERT FLUO
echo   que tu avais signale sur ses vetements n'existe plus
echo   nulle part dans le port : zero pixel, sur les 54 objets
echo   des quatorze decors de 2nd Impact.
echo.
echo ----------------------------------------------------------
echo   1. UN OBJET SE SERT MAINTENANT EN PLUSIEURS PALETTES
echo ----------------------------------------------------------
echo.
echo   Un objet trop LARGE etait deja servi en objets voisins.
echo   Un objet trop COLORE est desormais servi en objets
echo   SUPERPOSES, un par palette, chacun ne dessinant que les
echo   pixels qui lui reviennent.
echo.
echo   Le partage se fait par PROVENANCE, pas par couleur : une
echo   palette source ne porte que 63 couleurs utiles, donc une
echo   couche batie sur une palette source tient TOUJOURS. Et
echo   chaque pixel n'a qu'une provenance, donc les couches ne
echo   se marchent pas dessus -- verifie, leur somme redonne
echo   l'image au pixel pres, sur tous les objets du port.
echo.
echo   Un seul objet en avait encore besoin apres la correction
echo   des couleurs : le script 7 de Hugo, 89 couleurs, servi
echo   en deux couches (palettes 1656 et 1659).
echo.
echo ----------------------------------------------------------
echo   2. « DRAPEAU 9 » N'ETAIT PAS UNE BANQUE DE PALETTES
echo ----------------------------------------------------------
echo.
echo   C'est le bit de MIROIR HORIZONTAL. Sur les quatorze
echo   assets, `drapeaux` ne prend que quatre valeurs -- 1, 5, 9
echo   et 13 -- et leurs bits sont exactement : aucun
echo   retournement, miroir vertical, miroir horizontal, les
echo   deux. Il n'y a pas de cinquieme valeur.
echo.
echo   512 morceaux retournes allaient donc chercher leurs
echo   couleurs dans une palette lointaine. Un vetement dont la
echo   moitie est un morceau miroir sortait d'une couleur sans
echo   rapport avec l'autre moitie.
echo.
echo   L'EPREUVE : les quatre figures de Gill ont les palettes
echo   871 a 874, etabli par deux chemins et validee a l'ecran.
echo   Leurs morceaux portent TOUS le drapeau 1.
echo.
echo ----------------------------------------------------------
echo   3. UN DECOR CHARGE DEUX BANQUES, ET L'OFFSET LES SEPARE
echo ----------------------------------------------------------
echo.
echo   Le groupe d'offsets BAS tire sur le transfert secondaire
echo   -- celui que le script d'etage passe en dur -- et le
echo   groupe HAUT sur le premier jeu. Huit des neuf secondaires
echo   ont pour destination exactement la suite du premier jeu
echo   dans la palette RAM : ce n'est pas un hasard d'adresse.
echo.
echo   Le detecteur de vert le confirme, une fois l'INDEX 0
echo   exclu -- il est transparent, il n'est jamais peint, et
echo   c'est lui qui faussait la mesure precedente :
echo.
echo      YUN  offsets 0..6    12518 pixels verts  ->  ZERO
echo      HUGO offsets 0..11   23092 pixels verts  ->  ZERO
echo.
echo   Et la regle retrouve toute seule le 1674 d'ORO, la seule
echo   base de ce groupe qui ait ete validee a l'ecran. Rien
echo   n'a ete cale dessus.
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER
echo ==========================================================
echo.
echo   HUGO (etage 28) -- c'est lui le sujet
echo     a. Le VERT FLUO sur les vetements : disparu ?
echo     b. Onze objets dans la foule au lieu de six. Deux
echo        d'entre eux sont la MEME figure servie en deux
echo        couches : si tu vois une figure a moitie coloriee,
echo        ou deux moities qui ne se rejoignent pas, dis-le --
echo        c'est la que ca casserait.
echo     c. Les teintes de la foule te paraissent-elles justes
echo        pour une fete foraine ?
echo.
echo   YUN (etage 25) -- il change AUSSI, et il n'avait rien
echo   demande : ses offsets 0..6 passaient sur du vide. Le
echo   cuisinier au wok et le client attable etaient bien
echo   places ; dis-moi si leurs COULEURS ont bouge, en mieux
echo   ou en pire.
echo.
echo   ORO (etage 31), GILL (22), NECRO (27), RYU (24), SEAN
echo   (34), ELENA (30), YANG (32), DUDLEY (26) : rien ne
echo   devait bouger chez eux. Si quelque chose a change, c'est
echo   moi qui ai casse quelque chose -- dis-le.
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe tous les objets
echo   animes sans toucher au decor.
echo.
pause

3sx.exe > "%~dp03sx-hugo.log" 2>&1

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
type "%~dp03sx-hugo.log"
echo.
pause
