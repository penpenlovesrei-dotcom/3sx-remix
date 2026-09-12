@echo off
rem Le chargeur 0x8C02356A etait dans l'inventaire, jamais exploite. Il porte le panneau.

echo ==========================================================
echo   DEPLOIEMENT DE L'EXE
echo ==========================================================
echo.
copy /y "%~dp0build\3sx.exe" "%~dp0build\application\bin\3sx.exe" >nul 2>&1
if errorlevel 1 (
  echo   ECHEC : une instance du jeu est ouverte et verrouille
  echo   le fichier. Ferme-la et relance ce lanceur.
  pause
  exit /b 1
)
for %%F in ("%~dp0build\application\bin\3sx.exe") do echo   exe deploye, date du binaire : %%~tF
echo.

cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   LE PANNEAU VERTICAL EST EN 852
echo ==========================================================
echo.
echo   Il venait d'un chargeur que la chaine n'exploitait pas :
echo   0x8C02356A. Il ecrit +102 et +106, donc il dit VRAIMENT
echo   ou va son objet -- contrairement au bloc que j'avais
echo   invente, qui n'ecrivait que +84/+86.
echo.
echo   COMMENT JE L'AI RETROUVE. spawners2i rendait « nombres
echo   u16 [?] » : l'interpreteur perd la base de la table. Les
echo   sept litteraux de la fonction la donnent -- une adresse
echo   en 0x8C17xxxx pour les nombres, une en 0x8C5F9xxx pour
echo   les pointeurs, exactement la forme du chargeur voisin
echo   dont les tables etaient deja resolues. Indexation
echo   arg*8+z*2 et arg*16+z*4, avec arg = decor - 1.
echo.
echo ----------------------------------------------------------
echo   DEUX RECOUPEMENTS, PARCE QU'UNE FORME QUI « MARCHE »
echo   NE PROUVE RIEN TOUTE SEULE
echo ----------------------------------------------------------
echo.
echo   1. Le chargeur voisin 0x8C0233B6, meme forme, arg 2, rend
echo      EXACTEMENT les quatre elements statiques de Yun --
echo      383,32 / 413,69 / 479,64 / 576,64 -- ceux que poser2i
echo      cuit deja dans les pages. Quatre sur quatre.
echo.
echo   2. Le meme 0x8C02356A, arg 3, rend le punk au blouson
echo      Union Jack de Dudley en x 736. C'est la position que
echo      j'avais mesuree au balayage a 99 %%, par un chemin
echo      completement different.
echo.
echo ----------------------------------------------------------
echo   CE QUE CE CHARGEUR AJOUTE A YUN
echo ----------------------------------------------------------
echo.
echo      script 0   LE PANNEAU VERTICAL   x 852   palette 23
echo      script 4   les paniers           x 640
echo      script 5                         x 624
echo      script 27                        x 231
echo      script 35  ecarte : zero image
echo.
echo   ET IL CORRIGE UNE ERREUR AU PASSAGE : les paniers etaient
echo   poses en 752 par le bloc invente. Le vrai chargeur les
echo   met en 640 -- exactement la ou le balayage les trouvait
echo   peints. Je ne l'avais pas cru.
echo.
echo   Yun passe de 12 a 16 objets.
echo.
echo ----------------------------------------------------------
echo   CE QUE JE N'AI PAS SU FAIRE
echo ----------------------------------------------------------
echo.
echo   Les deux derniers chargeurs de Yun, 0x8C025A9A et
echo   0x8C02E1FE, resistent : leur bloc sort en « [0 + arg*4] »
echo   -- la base est perdue elle aussi, mais aucune des trois
echo   formes d'indexation que j'ai essayees ne rend
echo   d'enregistrement valide. Je le dis au lieu d'en inventer
echo   une quatrieme.
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER
echo ==========================================================
echo.
echo   YUN (etage 25), et lui seul :
echo     a. Le panneau vertical est-il maintenant a DROITE,
echo        contre les portes rouges, comme sur ta capture
echo        Dreamcast ?
echo     b. Le fumeur est-il degage ?
echo     c. Les cages sont-elles DEVANT lui ?
echo     d. Le vieil homme et la dame en rose sont-ils animes ?
echo        (ils sont dans la variante z 1/3 -- relance si tu ne
echo        les vois pas, ou SF3_DECOR_VARIANTE=1)
echo     e. Deux objets apparaissent que tu n'avais jamais vus,
echo        scripts 5 et 27. Sont-ils a leur place ?
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe tous les objets
echo   animes sans toucher au decor.
echo.
pause

3sx.exe > "%~dp03sx-yun4.log" 2>&1

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
type "%~dp03sx-yun4.log"
echo.
pause
