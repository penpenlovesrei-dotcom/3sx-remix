@echo off
rem Ibuki (etage 29) : la cascade, une seule -- l'autre figeait le jeu.

cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   IBUKI (etage 29) : LA CASCADE
echo ==========================================================
echo.
echo POURQUOI CA PLANTAIT -- ET LA VRAIE BORNE
echo.
echo   Deuxieme plantage : CG cache plein, x16 EXT2. Cette fois
echo   le journal donne tout : objets 0 a 8 poses, image 0 a la
echo   trame 0, image 1 a 4, image 2 a 8, et ca casse a l'image
echo   3, trame 12.
echo.
echo   LE TAS NE FAIT QUE 1024 MORCEAUX, ET ON NE PEUT PAS
echo   L'AGRANDIR. `structs.h` declare `u16 x16_map[4][16]` :
echo   quatre pages, pas une de plus, et `makeup_tpu_free` boucle
echo   dessus. Mon `mts_OB_page = 7` d'avant lisait donc HORS DES
echo   BORNES -- c'etait un bug, pas un reglage.
echo.
echo   Le compte tombe juste : la cascade fait 272 cases, la
echo   duree de vie est de 12 trames et une image dure 4, donc
echo   QUATRE images restent vivantes. 4 x 272 = 1088 pour 1024
echo   places. Il manquait 64 morceaux.
echo.
echo LA REPARATION
echo.
echo   Une case entierement transparente ne vaut pas un morceau
echo   de cache. Le moteur sait deja quoi en faire : quand aucune
echo   tuile ne couvre une case, il rend `tuile_vide` sous une
echo   cle unique et partagee. Le generateur en emettait une
echo   quand meme -- on payait un morceau plein pour du vide.
echo.
echo   La cascade a 272 cases dont 192 occupees seulement :
echo.
echo     avant   272 cases/image   x4 = 1088   FIGE
echo     apres   192 cases/image   x4 =  768   pour 1024 places
echo.
echo   La cle du cache se deduit maintenant de x et y au lieu du
echo   rang dans la table, sans quoi sauter une case decalerait
echo   toutes les suivantes. La valeur est IDENTIQUE quand la
echo   table est pleine : les tuiles sortent image, puis ligne,
echo   puis colonne, donc l'ancien calcul valait deja
echo   lig x cols + col. Verifie sur les 63 fiches, et aucune
echo   case ne deborde des cinq bits de la cle.
echo.
echo   Akuma y gagne au passage -- 90 tuiles de moins -- sans
echo   qu'un seul pixel change a l'ecran.
echo.
echo LAQUELLE, ET POURQUOI CELLE-LA
echo.
echo   Celle de (0,267). La conversion `y = 512 - by - ...` la
echo   place a y 5, dans les 224 lignes de l'ecran, quand
echo   l'autre sort a 261 -- au-dela du bas. Et sur ta premiere
echo   capture, la cascade visible tombe vers y 45..90, ce qui
echo   est bien dans la hauteur de cet objet.
echo.
echo   Six trames de 272x245, 4 trames par image, lues dans la
echo   suite du binaire. Le pas vertical du magasin est 256 et
echo   non 245 : les rangees commencent en y 11 et y 267.
echo.
echo   Servie en neuf objets voisins qui se rejoignent au pixel
echo   pres, la cle de cache ne portant que 32 cases.
echo.
echo   Tuiles relues depuis le C compile : zero pixel d'ecart.
echo.
echo CE QUE JE CHERCHE
echo.
echo   a. Est-ce que ca tient, sans figer ?
echo   b. La cascade coule-t-elle ?
echo   c. Une couture entre les neuf morceaux ?
echo.
echo   Si rien ne coule mais que ca tient, c'est que la cascade
echo   visible est l'autre : je bascule sur (272,11), c'est une
echo   ligne a changer.
echo.
echo   JE NE DIS PAS QUE CA MARCHE : je n'ai pas de visuel. Le
echo   calcul du cache tombe juste et les donnees sont verifiees
echo   -- c'est tout ce que je peux affirmer. Le reste, c'est toi.
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe tous les objets
echo   animes sans toucher au decor.
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
