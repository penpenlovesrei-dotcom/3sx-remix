@echo off
rem Les secondaires ne sont pas "en dur" : ils sont dans une table.

echo ==========================================================
echo   DEPLOIEMENT DE L'EXE
echo ==========================================================
echo.
copy /y "%~dp0build\3sx.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
if errorlevel 1 (
  echo   ECHEC : une instance du jeu verrouille le fichier.
  pause
  exit /b 1
)
for %%F in ("%~dp0build\application\bin\3sx.exe") do echo   exe deploye, %%~tF
echo.

cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   ZERO PIXEL VERT. 4437 AU DEPART.
echo ==========================================================
echo.
echo   Tes trois signalements etaient bons tous les trois, et
echo   ils ont fait tomber quatre defauts, dont trois a moi.
echo.
echo ----------------------------------------------------------
echo   1. LE DETECTEUR CHERCHAIT UNE VALEUR, PAS UN CANAL
echo ----------------------------------------------------------
echo.
echo   Il testait "== 0x03E0". Or n05o19 tombe sur 0x0280 --
echo   vert lui aussi. Il annoncait ZERO avec 474 pixels verts
echo   a l'ecran, et masquait 3207 pixels verts en 2I. Une case
echo   jamais ecrite se reconnait a ses CANAUX : rouge et bleu
echo   nuls, vert non nul.
echo.
echo ----------------------------------------------------------
echo   2. LES SECONDAIRES NE SONT PAS "EN DUR" : IL Y A UNE
echo      TABLE, ET JE LA RECOPIAIS A LA MAIN
echo ----------------------------------------------------------
echo.
echo   J'avais releve neuf index un a un dans les scripts
echo   d'etage, et ecrit EN_DUR = {2:103, 3:106, ...}. Le
echo   chargeur d'etage lit en fait TROIS tables d'affilee :
echo.
echo      2nd Impact                    New Generation
echo      0x8C1D5D14  bande*2   jeu 2   0x8C18ABE4
echo      0x8C1D5D38  bande*2   jeu 1   0x8C18AC10
echo      0x8C1D5D66  (bande-1) SECOND. 0x8C18AC46
echo.
echo   La troisieme rend LES NEUF VALEURS RELEVEES A LA MAIN,
echo   les neuf exactes -- et sept bandes de plus que je
echo   croyais sans secondaire.
echo.
echo   C'est elle qui donne le TROISIEME TRANSFERT de la bande
echo   5 de NG : index 106, base 1397. Les trois criteres
echo   l'avaient deja designe (destination contigue 0x2A80,
echo   unique ; 14713 verts -^> zero ; nb=9 qui borne le
echo   groupe) -- le code le confirme sans eux.
echo.
echo ----------------------------------------------------------
echo   3. `52 + bande` CASSAIT A LA BANDE 17
echo ----------------------------------------------------------
echo.
echo   Je calculais l'index du premier jeu au lieu de le lire.
echo   NG a DIX-NEUF bandes : 52+17 tombe sur l'entree 69, le
echo   second jeu de la bande 0. La bande 17 sortait avec la
echo   base 25 au lieu de 338, et mon balayage lui comptait
echo   64476 pixels verts INEXISTANTS.
echo.
echo ----------------------------------------------------------
echo   4. UN DECOR PORTE PLUSIEURS BANDES, ET ON N'EN PRENAIT
echo      QU'UNE
echo ----------------------------------------------------------
echo.
echo   NG : `d["bandes"]` vaut [5,6,6] pour le decor de ng05.
echo   On peignait tout avec la premiere. n05o9 -- LA LANTERNE
echo   -- sortait 236 verts ainsi, et propre avec l'autre.
echo.
echo   ET L'AIRE NE DONNE PAS LA REPONSE : prendre
echo   `bandes[aire]` corrige ce decor et en casse un autre
echo   ([18,17,17], deux objets propres repassent a 70 et 116
echo   verts). Les bandes 5 et 17 chargent la MEME base, 6 et
echo   18 aussi : les deux decors veulent 380 pour ces
echo   objets-la. La liste n'est donc pas dans l'ordre des
echo   aires, et je ne m'en sers pas comme index.
echo.
echo   Ce qui reste licite, c'est ce que le detecteur sait
echo   faire : ELIMINER. On garde la premiere bande, et on ne
echo   passe a une autre DU MEME DECOR que si elle est propre
echo   la ou la premiere ne l'est pas.
echo.
echo   2I A LA MEME STRUCTURE, et une seule fois :
echo      bande = u16[0x8C1D591C + decor*6 + aire*2]
echo   Seize decors rendent trois fois la meme bande. LE DECOR
echo   8 REND [8, 9, 9]. Son objet a30o0 -- la tache magenta et
echo   verte au centre de l'etage 30 -- sortait 3265 verts avec
echo   la bande 8 et est propre avec la bande 9.
echo.
echo ----------------------------------------------------------
echo   ET UN PIEGE D'OUTIL, QUI M'A COUTE UN BUILD
echo ----------------------------------------------------------
echo.
echo   `animerng --ecrire` AJOUTE au fichier que `animer2i`
echo   ecrit. Son nettoyage par prefixe ratait les morceaux
echo   (`n00o6m1_...`) : relance seul, il empilait une seconde
echo   copie et clang refusait. Corrige, et l'epreuve est
echo   faite -- deux passages de suite compilent.
echo.
echo ==========================================================
echo   LE COMPTE
echo ==========================================================
echo.
echo                             avant   apres
echo      pixels verts poses      4437       0
echo         dont 2I              3207       0
echo         dont NG              1230       0
echo.
echo   Corrections livrees :
echo      ng05  n05o9  la lanterne  (bande du decor)
echo      ng05  huit objets         (transfert 1397)
echo      bg08  a30o0               (bande 9 du decor 8)
echo      bg0a  a31o14              (variante 2184)
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER
echo ==========================================================
echo.
echo     a. NG05 : la lanterne, la femme en kimono (n05o16) et
echo        l'objet n05o6 -- tes trois signalements.
echo     b. ETAGE 30 (bg08) : l'objet au centre, en bas.
echo     c. ORO : a31o14 change ; LES BETES NE DOIVENT PAS
echo        AVOIR BOUGE. Si elles ont bouge, c'est une
echo        regression et je reviens en arriere.
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe les objets.
echo.
pause

3sx.exe > "%~dp03sx-couleurs.log" 2>&1

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
type "%~dp03sx-couleurs.log"
echo.
pause
