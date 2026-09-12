@echo off
rem La table des 196 effets depouillee, et les variantes z mesurees.

cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   74 OBJETS -^> 77, ET YANG PASSE DE DEUX A CINQ
echo ==========================================================
echo.
echo ----------------------------------------------------------
echo   1. LES 196 ENTREES DE 0x8C179FDC, DEPOUILLEES
echo ----------------------------------------------------------
echo.
echo   L'outil (outils/effets2i.py) balaie tout le binaire a la
echo   recherche des SPAWNERS : toute fonction qui ecrit un id
echo   CONSTANT en objet+8. Il en trouve pour 176 des 196 ids.
echo.
echo   Puis il ne garde que ceux qui LISENT UN BLOC -- c'est ce
echo   qui distingue un objet fabrique depuis des DONNEES d'un
echo   objet cree par du code. Il en reste TRENTE-DEUX.
echo.
echo   Et de ces trente-deux, QUATRE seulement sont atteints
echo   depuis un script d'etage : les ids 18, 25, 66 et 87.
echo   Trois etaient deja exploites. Le quatrieme ne l'etait
echo   pas -- et c'est celui de Yang.
echo.
echo ----------------------------------------------------------
echo   2. L'ID 25 : YANG L'APPELLE TROIS FOIS
echo ----------------------------------------------------------
echo.
echo   Spawner 0x8C029B00, bloc = u32[0x8C5F9EAC + arg*4], un
echo   enregistrement de 30 octets par appel. Yang l'appelle aux
echo   sites 0x8C0DCAB6, 0x8C0DCABA et 0x8C0DCABE -- args 0, 1
echo   et 2, tous les trois dans sa propre routine.
echo.
echo   Scripts 65, 63 et 3, en 512/32, 527/49 et 751/48. Une
echo   image chacun : ce sont des poses fixes, pas des
echo   animations.
echo.
echo   YANG passe de 2 objets a 5. Son asset est le plus riche
echo   des quatorze -- 602 sprites, 93 scripts qui se resolvent
echo   -- et il n'en montrait que deux.
echo.
echo ----------------------------------------------------------
echo   3. LES VARIANTES z : LE CHOIX EST MAINTENANT MESURE
echo ----------------------------------------------------------
echo.
echo   Chaque couple (lecteur, argument) porte QUATRE blocs,
echo   tires au sort a l'entree de l'etage. Sur les dix couples
echo   qu'un script d'etage atteint, DEUX SEULEMENT portent des
echo   blocs reellement differents :
echo.
echo     YUN   z0/z2 -^> script 19 posable
echo           z1/z3 -^> RIEN de posable
echo     HUGO  z0 -^> 7, 9, 11    z1/z3 -^> 7, 5, 11
echo           z2 -^> 7, 11, 13
echo.
echo   z = 0 est donc le plus riche chez Yun et a egalite chez
echo   Hugo, ou les quatre variantes donnent trois objets et ne
echo   different que par UN sprite. On garde z = 0, et ce n'est
echo   plus un choix par defaut : c'est le resultat d'une mesure.
echo.
echo   Poser leur union montrerait trois figures la ou le jeu
echo   n'en montre qu'une.
echo.
echo ----------------------------------------------------------
echo   4. DEUX DEFAUTS D'OUTIL CORRIGES EN CHEMIN
echo ----------------------------------------------------------
echo.
echo   * LE POOL DE LITTERAUX. Le SH-4 pose ses constantes AU
echo     MILIEU du code. Mon analyseur les decodait comme des
echo     instructions : une valeur ressemblait a « lis le bloc »
echo     et il annoncait un bloc en dur de 24899 au lieu des
echo     deux tables. Il saute maintenant les litteraux.
echo   * LA TAILLE DE L'ENREGISTREMENT. Un champ ecrit par un
echo     registre (mov r4,r1 ; add #52,r1 ; mov.w r3,@r1) etait
echo     rate : 22 octets annonces pour 24 reels, et les
echo     enregistrements suivants lus en bruit. Controle : la
echo     taille deduite des champs egale maintenant le pas
echo     d'indexation que le code emploie de son cote.
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER
echo ==========================================================
echo.
echo   YANG (etage 32) est le seul decor qui change : trois
echo   objets de plus, deux grands (2x12 cases) et un moyen
echo   (4x7). Sont-ils a leur place sur le temple ? Leurs
echo   teintes te paraissent-elles justes ? Tu avais signale
echo   que le premier sortait PALE sur un decor rouge et ocre.
echo.
echo   TOUS LES AUTRES doivent etre identiques a hier soir. Si
echo   quelque chose a bouge ailleurs, c'est moi.
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe tous les objets
echo   animes sans toucher au decor.
echo.
pause

3sx.exe > "%~dp03sx-effets.log" 2>&1

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
type "%~dp03sx-effets.log"
echo.
pause
