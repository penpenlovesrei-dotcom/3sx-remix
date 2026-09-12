@echo off
setlocal
cd /d "%~dp0build\application\bin"
if exist "jalons.on" del "jalons.on"

echo ==========================================================
echo   LE SENS DE L'AXE EST ETABLI -- ET IL CHANGE TOUT
echo ==========================================================
echo.
echo   Ta reponse « monte » donne, sans plus aucune ambiguite :
echo.
echo     position_y  ^^  ->  vers le HAUT
echo     bank_y      ^^  ->  vers le BAS
echo     sol         ^^  ->  vers le BAS
echo.
echo   Donc UN SPRITE TROP HAUT SE CORRIGE EN AUGMENTANT `sol`.
echo   C'est l'inverse de ce que j'avais conclu hier soir : mon
echo   annulation etait elle aussi une erreur, elle REMONTAIT
echo   Sean et Necro qui etaient deja trop hauts.
echo.
echo   Trois regressions pour un axe qui a deux sens et se mesure
echo   en trente secondes. C'est note dans BILAN.md, avec la
echo   regle : un axe ne se deduit pas d'un commentaire.
echo.
echo ----------------------------------------------------------
echo CE QUI BOUGE, ET DE COMBIEN
echo ----------------------------------------------------------
echo.
echo   `sol` devient la constante 1023 pour les quatorze decors.
echo.
echo     SEAN  (34)  ses sprites DESCENDENT de 16 px
echo                 et son PLAN descend de 16 avec eux
echo     NECRO (27)  ses trois elements DESCENDENT de 51 px
echo.
echo     les douze autres decors : AUCUN changement (leur sol
echo     valait deja 1023).
echo.
echo   Pour SEAN les deux vont ensemble : sa banque est la seule
echo   a ne pas peindre jusqu'en bas TOUT EN ayant un sol plein
echo   (768 px de large sur ses douze dernieres lignes). Son plan
echo   descend donc de 16, et nos sprites avec.
echo.
echo   Chez NECRO le plan ne bouge PAS : sa derniere ligne n'est
echo   qu'un bout de sprite de 6 px, pas un sol -- son plan
echo   proche est un premier plan decoupe. Seuls ses elements
echo   descendent.
echo.
echo   LES PAGES ONT ETE DECALEES, PAS REECRITES. C'est ce qui
echo   avait fait disparaitre des sprites hier : la reecriture
echo   depuis la banque nue effacait ce qui y etait cuit. Cette
echo   fois les pages existantes sont decalees telles quelles, et
echo   `poser2i` confirme « pixels CHANGES : 0 » -- rien n'a ete
echo   ni ajoute ni detruit.
echo.
echo ----------------------------------------------------------
echo CE QUI RESTE ACQUIS DE LA SESSION
echo ----------------------------------------------------------
echo.
echo   NEW GENERATION S'AFFICHE -- `char_add[37]` porte a 58.
echo   SES PLANS DEFILENT -- trois gardes `bg_index ^< 37` levees.
echo   PLUS DE SPRITES ETRANGERS -- `decor_anim_par_etage` se lit
echo     desormais DANS les fiches, verifie : zero etage faux.
echo   LA MUSIQUE -- `BGM_Stage_Data` etait rempli a 37 sur 58.
echo   LES GROS SPRITES en morceaux : Elena 0 -^> 8, NG 125 -^> 165.
echo   ORO NG : ses cascades passent sur le troisieme plan.
echo.
echo ----------------------------------------------------------
echo LE SELECTEUR VA JUSQU'A 57
echo ----------------------------------------------------------
echo.
echo     22 a 36   les quinze decors de 2nd Impact
echo     37 a 55   les DIX-NEUF decors de New Generation
echo     56        bg08     57  bg10
echo.
echo     37 H.S.(GILL)    44 LOND(DUD1)   51 NAI(ELEN1)
echo     38 N.Y.(ALEX)    45 LOND(DUD2)   52 NAI(ELEN2)
echo     39 N.Y.(SEAN)    46 MOSC(NECR)   53 AMAZO(ORO)
echo     40 JAPAN(RYU)    47 MUN (HUGO)   54 H.K (YAN1)
echo     41 JAPAN(KEN)    48 JAP(IBUK1)   55 H.K (YAN2)
echo     42 H.K.(YUN1)    49 JAP(IBUK2)
echo     43 H.K.(YUN2)    50 JAP(IBUK3)
echo.
echo ----------------------------------------------------------
echo CE QUE JE TE DEMANDE DE REGARDER
echo ----------------------------------------------------------
echo.
echo   a. ETAGE 34 SEAN  : les sprites sont-ils enfin a leur
echo      place -- le singe, le personnage a genou, la voiture ?
echo   b. ETAGE 27 NECRO : ses sprites sont-ils descendus au bon
echo      endroit, ou faut-il aller plus loin ?
echo   c. ETAGE 22 GILL  : l'acolyte est bien REVENU a sa place
echo      d'origine ? (il servait de repere pour l'essai)
echo.
echo   Si Sean ou Necro sont encore trop hauts, dis-moi
echo   SEULEMENT ca : maintenant je sais dans quel sens aller, et
echo   il ne reste qu'a trouver de combien.
echo.
pause

3sx.exe > "%~dp03sx-ng.log" 2>&1

echo.
echo ================= LES JOURNAUX =================
for %%F in (fin-de-round.log decor-objets.log fatal.log) do (
  if exist "%%F" (
    echo.
    echo ----- %%F -----
    type "%%F"
  )
)

set "H=%date:~-4%%date:~3,2%%date:~0,2%-%time:~0,2%%time:~3,2%%time:~6,2%"
set "H=%H: =0%"
if not exist "%~dp0essais" mkdir "%~dp0essais"
for %%F in (fin-de-round.log decor-objets.log fatal.log) do (
  if exist "%%F" copy /y "%%F" "%~dp0essais\%H%-%%F" >nul
)
copy /y "%~dp03sx-ng.log" "%~dp0essais\%H%-sortie.log" >nul
echo.
echo ----- archive -----  %~dp0essais\%H%-*.log
echo.
pause
