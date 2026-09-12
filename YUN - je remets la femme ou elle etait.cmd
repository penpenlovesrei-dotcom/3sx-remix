@echo off
rem La mesure par ancre m'a menti de seize pixels. Le balayage remet les choses en place.

cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   J'AI FAIT PIRE, ET VOICI POURQUOI
echo ==========================================================
echo.
echo   J'avais deplace la femme en rose de seize pixels sur la
echo   foi d'une mesure. LA MESURE ETAIT FAUSSE. Annule.
echo.
echo   Ce que je cherchais est reel : chez Yun, les personnages
echo   animes sont AUSSI PEINTS dans le decor, a l'arret --
echo   l'objet est cense les recouvrir. Mais l'outil qui les
echo   retrouve s'appuie sur un PIXEL D'ANCRE, le plus rare de
echo   l'image, et ca ne vaut que si la figure peinte est
echo   IDENTIQUE a la notre. Des qu'elle differe un peu, l'ancre
echo   tombe sur un pixel isole et rend n'importe quoi.
echo.
echo     l'ancre disait     la femme peinte en 512
echo     le BALAYAGE dit    la femme peinte en 496  <-- sa place
echo                        calculee, celle d'avant
echo.
echo   LA REGLE QUE J'EN TIRE, et qui est ecrite dans DECORS.md :
echo   on ne deplace un objet que sur un accord FRANC, mesure
echo   par balayage. En dessous de 90 %%, la figure peinte n'est
echo   pas la notre et ne dit rien de sa place.
echo.
echo ----------------------------------------------------------
echo   CE QUE J'AI VERIFIE ENTRE-TEMPS, ET QUI TIENT
echo ----------------------------------------------------------
echo.
echo   J'ai construit l'outil qui manquait : il rend l'etage
echo   depuis decor_objets_data.c LUI-MEME -- les tuiles
echo   compilees, decodees, posees a la case que le moteur en
echo   deduit, avec la palette de la fiche. C'est ce que le jeu
echo   televerse, sans aucune hypothese.
echo.
echo   NOS DONNEES SONT JUSTES. Un seul vieil homme, une seule
echo   femme, a leur place. Et le journal du jeu le confirme :
echo   vingt objets marques, aux x, y, famille et z exacts.
echo.
echo   TROIS PISTES RESTENT FERMEES, ne les rouvrons pas :
echo     - pas une fuite de variante (masques 0x5 et 0xA
echo       exclusifs, filtre juste des deux cotes) ;
echo     - aucun script pose deux fois ;
echo     - pages a jour -- les .tex deployes sont identiques au
echo       bit pres a ceux du dossier de travail.
echo.
echo   CE QUI RESTE VRAI, ET QUI EST LA CAUSE : le decor PEINT
echo   deja ces personnages, et notre objet ne les recouvre qu'a
echo   84 %% (le vieux) et 69 %% (la femme). D'ou ce qu'on voit
echo   deborder autour.
echo.
echo ----------------------------------------------------------
echo   ORO -- CE QUE J'AI MESURE
echo ----------------------------------------------------------
echo.
echo   L'edifice de pierre est pose en 704,896 sur la grotte du
echo   fond. Le balayage le retrouve peint EXACTEMENT la, a
echo   98 %% -- 706 pixels identiques sur 721. En coordonnees de
echo   bande, il est donc a sa place.
echo.
echo   S'il n'y est pas a l'ecran, ce n'est plus la donnee : ce
echo   serait l'ORIGINE DU PLAN. Il est le seul objet du chantier
echo   en famille 3, et c'est justement ce qu'on lui a impose
echo   pour qu'il defile avec la grotte du fond.
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER
echo ==========================================================
echo.
echo   YUN (25)  a. Est-ce revenu a l'etat d'avant -- pas mieux,
echo                mais pas pire ?
echo.
echo   ORO (31)  b. L'edifice de pierre : de combien est-il a
echo                cote de sa copie peinte, et DANS QUEL SENS ?
echo                Gauche ou droite, haut ou bas. Un ordre de
echo                grandeur suffit -- « une demi-largeur »,
echo                « deux fois sa hauteur ».
echo             c. Et l'ecart change-t-il quand la camera se
echo                deplace ? C'est la question qui tranche : si
echo                l'ecart BOUGE, c'est le plan ; s'il reste
echo                CONSTANT, c'est une origine.
echo.
echo   DUDLEY (26) est valide, je n'y ai pas retouche.
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe tous les objets
echo   animes sans toucher au decor.
echo.
pause

3sx.exe > "%~dp03sx-yun2.log" 2>&1

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
type "%~dp03sx-yun2.log"
echo.
pause
