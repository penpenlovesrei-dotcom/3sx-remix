@echo off
rem Trois objets retires chez Yun, et l'etage d'Ibuki enfin identifie.

cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   YUN : LES TROIS OBJETS SONT RETIRES
echo ==========================================================
echo.
echo   LA REGLE QUE J'APPLIQUE MAINTENANT : ce que le decor
echo   peint deja, on ne le pose pas. Un objet qui n'anime rien
echo   ne fait que redoubler la figure peinte, et le moindre
echo   ecart se voit comme une copie.
echo.
echo     script 33  LE VIEIL HOMME       peint, 84 %%
echo     script 31  LA FEMME EN ROSE     peinte, 69 %%
echo     script  7  LES CAGES A OISEAUX  peintes a 97 %% a leur
echo                place EXACTE, et une seule image
echo.
echo   LES CAGES, C'ETAIT LE SPRITE DEVANT LE FUMEUR : elles
echo   couvrent 672 a 784 et lui est en 728. Les poser
echo   n'apportait rien -- 97 %% de leurs pixels etaient deja
echo   la, a l'identique.
echo.
echo   CE QUE CA COUTE, et je le dis : le vieil homme et la
echo   femme ne sont plus ANIMES. Ils sont peints, immobiles.
echo   Mieux vaut ca qu'une figure peinte plus une copie
echo   decalee.
echo.
echo ----------------------------------------------------------
echo   LE PANNEAU VERTICAL : je ne l'ai PAS deplace
echo ----------------------------------------------------------
echo.
echo   Je ne veux pas refaire l'erreur d'hier, ou j'ai deplace
echo   un objet sur une mesure qui n'en etait pas une.
echo.
echo   J'ai lu sa table EN ENTIER -- 0x8C17DD58, trois
echo   enregistrements de dix octets, terminateur a zero
echo   verifie. Elle dit, sans ambiguite :
echo.
echo      script 0  x 696  y 64   palette 74   <- le panneau
echo      script 2  x 752  y 84   palette 74
echo      script 4  x 752  y 63   palette 74
echo.
echo   ET IL N'EST PEINT NULLE PART : ni dans les trois pages
echo   de l'etage, ni dans les quatre demi-banques du disque.
echo   Zero correspondance. Aucune mesure ne peut donc lui
echo   donner une autre place que celle-la.
echo.
echo   SI TU SAIS OU IL VA, dis-le moi en clair -- « contre le
echo   mur rouge », « a gauche des etals » -- et je l'y mets.
echo.
echo ==========================================================
echo   ORO : MESURE, ET IL EST A SA PLACE
echo ==========================================================
echo.
echo   J'ai etabli la correspondance plan / famille par la
echo   mesure, au lieu de la supposer :
echo.
echo      a31o8 (+ 2 morceaux)  famille 2  peint dans la GROTTE
echo                            PROCHE, a sa position exacte,
echo                            98 %%, 90 %%, 100 %%
echo      a31o7 L'EDIFICE       famille 3  peint dans la GROTTE
echo                            DU FOND, en 704,896, 98 %%
echo                            -- soit EXACTEMENT ou on le pose
echo.
echo   Les deux familles se recoupent, et l'edifice tombe pile
echo   sur sa copie. Si ce n'est pas ce que tu vois, relance-le
echo   une fois : je n'y ai pas touche depuis, et il se peut
echo   que tu n'aies pas repris Oro depuis le correctif.
echo.
echo ==========================================================
echo   IBUKI : C'EST L'ETAGE 29, ET JE SAIS CE QU'IL A
echo ==========================================================
echo.
echo   J'ai rendu les dix-sept etages en planche pour
echo   l'identifier sans me tromper -- je te l'envoie.
echo.
echo   SES TROIS PLANS ONT DES COLONNES VIDES, et ce sont tes
echo   bandes noires :
echo.
echo      plan proche  (196)  VIDE de 0 a 95, et de 928 a 1023
echo      plan du fond (260)  VIDE de 816 a 863
echo      plan lointain(132)  VIDE de 368 a 399
echo.
echo   ET CE N'EST PAS L'ASSEMBLAGE : les pages cuites sont
echo   identiques aux demi-banques brutes, au pixel pres
echo   (296774, 205600, 277156). Le trou est donc dans ce qu'on
echo   EXTRAIT du disque, pas dans la facon dont on le pose.
echo.
echo   L'ETAGE 36 a exactement le meme defaut. C'est le prochain
echo   chantier, et il est commun aux deux.
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER
echo ==========================================================
echo.
echo   YUN (25)  a. Plus de copie du vieux ni de la dame ?
echo             b. Le fumeur de droite est-il degage ?
echo   ORO (31)  c. L'edifice est-il sur sa copie ?
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe tous les objets
echo   animes sans toucher au decor.
echo.
pause

3sx.exe > "%~dp03sx-yun3.log" 2>&1

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
type "%~dp03sx-yun3.log"
echo.
pause
