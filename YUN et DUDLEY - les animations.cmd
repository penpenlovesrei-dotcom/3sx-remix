@echo off
rem Le bloc portait DEUX scripts par enregistrement, et on posait celui du repos.

cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   LA CAUSE ETAIT UN CHAMP QU'ON NE LISAIT PAS
echo ==========================================================
echo.
echo   Ta capture a tout debloque : les 2 personnages, ce sont
echo   le vieil homme au panier rond et la femme en rose au
echo   chapeau. J'ai rendu les 45 sprites de Yun pour les
echo   identifier -- ce sont les scripts 33 et 31.
echo.
echo   ET ILS ETAIENT INTROUVABLES POUR DEUX RAISONS :
echo.
echo   1. UN ENREGISTREMENT PORTE DEUX SCRIPTS. Le bloc du
echo      chargeur id 18 a un champ de plus, deux octets apres
echo      le script : une paire (REPOS, ACTION), et c'est
echo      toujours le premier plus un.
echo.
echo         Yun    repos 32 (ZERO image)  action 33 (12 images)
echo         Yun    repos 30 (ZERO image)  action 31 (12 images)
echo         Yun    repos 21 (ZERO image)  action 22 (24 images)
echo         Dudley repos  2 (une image)   action  3 (9 images)
echo         Hugo   repos  7 (10 images)   action  8 (19 images)
echo.
echo      On posait le REPOS. D'ou des figures immobiles -- et
echo      pour deux d'entre elles, un script a ZERO image.
echo      On pose maintenant le plus riche des deux.
echo.
echo   2. TES DEUX PERSONNAGES SONT DANS LA VARIANTE z 1/3.
echo      On ne cuisait que z 0. Ils y sont maintenant, avec le
echo      masque de variantes -- comme la menagerie d'Oro.
echo.
echo ----------------------------------------------------------
echo   CE QUI CHANGE
echo ----------------------------------------------------------
echo.
echo   YUN (25)     11 objets -^> 14. Les deux personnages, et
echo                les cages passent de UNE image a DIX.
echo   DUDLEY (26)   3 objets -^> 5. Un punk au skateboard
echo                (script 6, huit images), trouve par un
echo                chargeur inexploite -- 0x8C032B32, appele
echo                par sa propre routine d'etage. Et le
echo                monsieur a la canne passe d'une image a NEUF.
echo   HUGO (28)    ses trois objets de l'id 18 passent aux
echo                scripts d'action (8, 10 au lieu de 7, 9).
echo   SEAN (34)    idem, script 9 au lieu de 8.
echo   RYU, NECRO   inchanges : chez eux le repos est deja le
echo                plus riche.
echo.
echo   COULEURS : la banque basse de DUDLEY passe a 1641, comme
echo   celle de Ryu hier. C'est pour le monsieur a la canne que
echo   tu as signale.
echo.
echo ----------------------------------------------------------
echo   CE QUE JE N'AI PAS TROUVE
echo ----------------------------------------------------------
echo.
echo   LES DEUX AUTRES PUNKS. Les scripts 5 (dix images), 7
echo   (treize) et 10 les montrent, et rien dans l'arbre des
echo   spawners de Dudley ne les cree. Cherche encore.
echo.
echo   LE FEU ORANGE. Le feu que l'on pose est le script 0, sept
echo   images, et il est VERT sur la premiere. S'il ne passe
echo   jamais a l'orange, c'est que la phase orange est un autre
echo   etat de sa routine, pas une image de son script. Dis-moi
echo   ce que tu vois : cycle-t-il, ou reste-t-il vert ?
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER
echo ==========================================================
echo.
echo   YUN    a. Le vieil homme au panier et la femme en rose
echo             sont-ils la, et animes ?
echo          b. Les oiseaux dans les cages bougent-ils ?
echo          c. Attention : ils sont dans la VARIANTE z 1/3.
echo             Si tu ne les vois pas, relance -- une entree
echo             sur deux tombe sur z 0 ou 2.
echo   DUDLEY d. Le monsieur a la canne : couleur juste, et
echo             anime maintenant ?
echo          e. Un punk de plus au skateboard ?
echo   HUGO   f. Ses trois figures ont change d'animation. En
echo             mieux ou en pire ?
echo   SEAN   g. Son second objet aussi.
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe tous les objets
echo   animes. SF3_DECOR_VARIANTE=1 force la variante de Yun.
echo.
pause

3sx.exe > "%~dp03sx-anim.log" 2>&1

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
type "%~dp03sx-anim.log"
echo.
pause
