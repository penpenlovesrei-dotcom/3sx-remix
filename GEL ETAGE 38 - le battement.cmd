@echo off
setlocal
cd /d "%~dp0build\application\bin"

rem CE LANCEUR ARME LES JALONS. Ils sont desarmes par defaut -- un fflush par
rem ligne, des centaines d'ecritures par trame, le jeu n'est plus jouable. Le
rem fichier temoin les rallume ; le lanceur normal l'efface.
echo diagnostic> "jalons.on"

echo ==========================================================
echo   LE GEL DE NEW GENERATION -- ON RESSERRE
echo ==========================================================
echo.
echo ON Y EST : LE GEL EST DANS `Basic_Sub_Ex`
echo.
echo   Ton dernier journal donne l'appel exact :
echo.
echo     BG_Draw_System rendu   -^> passe
echo     ppgPurgeFromVRAM 4     -^> passe
echo     reqPlayerDraw          -^> passe
echo     Basic_Sub_Ex           -^> ENTRE, JAMAIS RENDU
echo.
echo   `Basic_Sub_Ex` ne fait qu'une chose : appeler six fois
echo   `move_effect_work`, qui PARCOURT UNE LISTE CHAINEE.
echo.
echo CE QUE LA LECTURE DU CODE DIT -- ET QUI COLLE
echo.
echo   `move_effect_work` ne sort que sur `suivant == -1`. Si la
echo   liste boucle sur elle-meme, elle tourne indefiniment :
echo   sans message, sans `fatal_error`, et sans meme rappeler
echo   les fonctions de deplacement -- le garde `timing` les
echo   bloque des le second tour. C'est EXACTEMENT ce qu'on
echo   observe : un gel muet, et aucun jalon `eff05`.
echo.
echo   Et un cycle est possible : `pull_effect_work` n'ecrit
echo   JAMAIS `behind` sur le nouveau maillon de queue, il le
echo   SUPPOSE a -1. Si un emplacement est distribue deux fois,
echo   `wrk-^>behind = qix` fait pointer un maillon sur lui-meme.
echo.
echo   C'est une hypothese lue dans le code. Cet essai la mesure.
echo.
echo CE QUI CHANGE -- ET CETTE FOIS TU DEVRAIS VOIR L'ETAGE
echo.
echo   J'ai pose un garde-fou dans la boucle : elle note chaque
echo   maillon parcouru (son numero, son id, son suivant), et
echo   au-dela de 128 tours -- le tas entier -- elle DIT qu'il y
echo   a un cycle et EN SORT au lieu de geler.
echo.
echo   Donc :
echo.
echo     - si le journal finit par « CYCLE -- liste N », c'est
echo       confirme, et il donne le maillon fautif et son id ;
echo     - si le journal s'arrete sur un « maillon N / id X »
echo       sans ligne CYCLE, alors ce n'est pas la liste : c'est
echo       la fonction de deplacement de CET effet-la qui pend,
echo       et son id me dira laquelle.
echo.
echo   LE GARDE-FOU N'EST PAS UN CORRECTIF -- c'est un pansement
echo   de mesure. Mais s'il tient, LE JEU NE GELERA PLUS et tu
echo   verras enfin l'etage 38. Dis-moi ce qu'il montre : c'est
echo   la premiere image de New Generation.
echo.
echo CE QUE JE TE DEMANDE
echo.
echo   UN SEUL ESSAI : VERSUS, etage 38 (N.Y. ALEX).
echo.
echo   Quand ca gele, laisse tourner cinq secondes, puis ferme la
echo   fenetre (Alt+F4 si besoin). Les journaux sont archives.
echo.
pause

3sx.exe > "%~dp03sx-gel38.log" 2>&1

echo.
echo ================= LES JOURNAUX =================
for %%F in (jalons-a.log jalons-b.log fin-de-round.log fatal.log) do (
  if exist "%%F" (
    echo.
    echo ----- %%F -----
    type "%%F"
  )
)

rem ARCHIVAGE. Les journaux sont rouverts a chaque lancement :
rem sans copie horodatee, l'essai suivant effacerait celui-ci.
set "H=%date:~-4%%date:~3,2%%date:~0,2%-%time:~0,2%%time:~3,2%%time:~6,2%"
set "H=%H: =0%"
if not exist "%~dp0essais" mkdir "%~dp0essais"
for %%F in (jalons-a.log jalons-b.log fin-de-round.log decor-objets.log fatal.log) do (
  if exist "%%F" copy /y "%%F" "%~dp0essais\%H%-%%F" >nul
)
copy /y "%~dp03sx-gel38.log" "%~dp0essais\%H%-sortie.log" >nul

echo.
echo ----- archive -----
echo   %~dp0essais\%H%-*.log
echo.
pause
