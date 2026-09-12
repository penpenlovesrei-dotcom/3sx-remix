@echo off
rem Les deux lecteurs qui n'ecrivaient pas de script : le chemin etait plus long d'un cran.

cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   63 OBJETS -^> 74. LES DEUX LECTEURS SANS SCRIPT SONT
echo   OUVERTS, ET ILS TOUCHENT NEUF DECORS
echo ==========================================================
echo.
echo   Je t'avais dit que les objets de ces deux lecteurs
echo   « ne sont pas des animes de notre espece ». C'ETAIT FAUX.
echo   Le chemin est simplement plus long d'un cran, et il est
echo   maintenant lu de bout en bout.
echo.
echo ----------------------------------------------------------
echo   LA CHAINE, MAILLON PAR MAILLON
echo ----------------------------------------------------------
echo.
echo   Un objet de 2nd Impact est un WORK, exactement celui que
echo   le port porte en C -- +0 be_flag, +4 type, +6 work_id,
echo   +8 id, +36 routine_no, +52 old_rno.
echo.
echo   +8 est l'ID, et il choisit la routine dans la table
echo   d'effets de 2nd Impact : 0x8C179FDC, 196 entrees, lue
echo   par le repartiteur 0x8C0215E0.
echo.
echo   ET CHAQUE SPAWNER EST ECRIT JUSTE APRES SA ROUTINE :
echo      id 18 -^> 0x8C028510  puis le spawner 0x8C028792
echo      id 66 -^> 0x8C03215C  puis le spawner 0x8C0323F0
echo      id 87 -^> 0x8C0363A4  puis le spawner 0x8C036480
echo   Trois sur trois. La table se valide elle-meme.
echo.
echo   La routine en appelle une AUTRE, choisie par un champ du
echo   bloc (+38). C'est celle-la qui pose le script -- et mon
echo   balayage ne la suivait pas, parce qu'elle n'est atteinte
echo   que par une table, jamais par un litteral.
echo.
echo   Elle appelle 0x8C0B4AD4, qui ecrit objet+456 = le numero
echo   de script, lu dans l'objet a +52 (id 66) ou +150 (id 18).
echo   LES DEUX TOMBENT SUR LE MEME ENDROIT DU BLOC :
echo   L'OCTET 12 de l'enregistrement.
echo.
echo   L'EPREUVE : les scripts ainsi lus se resolvent tous dans
echo   l'asset de leur PROPRE decor. Les deux seuls qui ne se
echo   resolvent pas rendent ZERO image -- il n'y avait rien a
echo   poser.
echo.
echo ----------------------------------------------------------
echo   CE QUI CHANGE
echo ----------------------------------------------------------
echo.
echo   RYU    (24)  11 objets -^> 13   scripts 20 et 8
echo   YUN    (25)   5 -^> 6           script 19
echo   DUDLEY (26)   1 -^> 3           scripts 4 et 2  <-- il en
echo                                  avait UN depuis le debut
echo   NECRO  (27)  15 -^> 17          script 24
echo   HUGO   (28)   6 -^> 9           scripts 7, 9, 11
echo   SEAN   (34)   2 -^> 3           script 8
echo.
echo   HUGO RECUPERE SON SCRIPT 7. C'est celui que j'avais
echo   retire hier soir parce qu'il venait d'un bloc mal lu. Il
echo   est bien a lui -- il y revient par le bon chemin.
echo.
echo   ALEX (23) ne change pas, et c'est un resultat : son
echo   entree lisait deja son script a l'octet 12. Elle etait
echo   juste, et c'est maintenant etabli au lieu d'etre un
echo   heureux hasard.
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER
echo ==========================================================
echo.
echo   DUDLEY (26) est le plus gros changement en proportion :
echo   il passe de un objet a trois, dont un de treize images.
echo   Sont-ils a leur place ?
echo.
echo   HUGO (28) : trois objets de plus dans la foule.
echo.
echo   NECRO (27) et SEAN (34) : un de plus chacun. Necro etait
echo   deja le decor le plus riche.
echo.
echo   RYU (24) : deux de plus, dont un a x negatif -- il est le
echo   seul decor dans ce cas et ses positions sont deja
echo   fausses. Si celui-la sort a droite au lieu de la gauche,
echo   c'est attendu, dis-le moi quand meme.
echo.
echo   GILL (22), ELENA (30), ORO (31), YANG (32), ALEX (23) :
echo   rien ne devait bouger.
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe tous les objets
echo   animes sans toucher au decor.
echo.
pause

3sx.exe > "%~dp03sx-lecteurs.log" 2>&1

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
type "%~dp03sx-lecteurs.log"
echo.
pause
