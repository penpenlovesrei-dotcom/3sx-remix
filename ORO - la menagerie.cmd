@echo off
rem La menagerie d'Oro : le chat, le chien, le perroquet. Ils n'avaient pas de bloc.

cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   LA MENAGERIE D'ORO -- ET POURQUOI ON LA CHERCHAIT MAL
echo ==========================================================
echo.
echo   On a cherche le bloc du chat, du chien et du perroquet
echo   pendant des semaines. Trois enregistrements avaient meme
echo   ete essayes au juge et rejetes a l'ecran.
echo.
echo   IL N'Y A PAS DE BLOC. C'est tout.
echo.
echo   Leur spawner ecrit x, y, palette, plan et la table de
echo   scripts en IMMEDIATS, dans le code. Et le numero de
echo   script est pose par la ROUTINE de l'objet, pas par une
echo   donnee. On cherchait une chose qui n'existe pas.
echo.
echo ----------------------------------------------------------
echo   CE QUE LA ROUTINE D'ETAGE D'ORO DIT EN CLAIR
echo ----------------------------------------------------------
echo.
echo   0x8C0DE548 (bande 10) appelle, dans cet ordre :
echo.
echo      8C0DE5C2  id 74   les chauves-souris   (deja posees)
echo      8C0DE5CE  id 55   LE PERROQUET
echo      8C0DE5FA  id 72   LE GROS CHAT
echo      8C0DE61A  id 71   LE CHIEN
echo.
echo   Chaque spawner porte EN DUR la table de scripts
echo   0x8C12AB8C, celle du decor 9. L'appelant et le litteral
echo   disent la meme chose, et aucun n'a servi a caler l'autre.
echo.
echo   LE SCRIPT est celui que la routine pose dans son PREMIER
echo   etat. Le controle est les chauves-souris : la meme
echo   lecture y rend le script 35, celui qu'on avait etabli a
echo   la main hier.
echo.
echo   Et les scripts tombent sur le CATALOGUE de la menagerie,
echo   etabli il y a des jours par les sprites eux-memes et sans
echo   aucun rapport avec ce chemin :
echo.
echo      id 72 -^> 13 et 51        le gros chat couche, puis
echo                               qui se redresse
echo      id 71 -^> 29, 30, 40, 41  le chien
echo      id 55 -^> 20, 21, 26      le perroquet
echo.
echo   Trois attributions independantes qui concordent.
echo.
echo ----------------------------------------------------------
echo   COMMENT ILS ONT ETE TROUVES
echo ----------------------------------------------------------
echo.
echo   En cherchant qui porte la table de scripts d'Oro en dur.
echo   Six sites la chargent ; cinq appartiennent a des
echo   fonctions qui ne lisent AUCUN bloc -- c'etait le signe.
echo.
echo   Il a fallu aussi corriger la remontee du graphe : `bsr`
echo   est RELATIF AU PC et n'ecrit aucune adresse, donc une
echo   fonction appelee ainsi n'apparait nulle part. Et mes
echo   adresses d'entree etaient decalees de deux octets, ce qui
echo   faisait manquer les sites d'appel.
echo.
echo ----------------------------------------------------------
echo   CE QUE JE NE POSE PAS
echo ----------------------------------------------------------
echo.
echo   LES CHATONS ANIMES (id 73, scripts 17 et 18). Leur
echo   routine existe, leurs scripts se resolvent -- mais AUCUN
echo   appelant ne les cree : ni litteral, ni bsr, ni table.
echo   Sans appelant, pas de position. Je ne les invente pas.
echo   (Les deux chatons FIXES sont deja cuits comme element.)
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER
echo ==========================================================
echo.
echo   ORO (etage 31) est le seul decor qui change. Il passe de
echo   douze objets a quinze.
echo.
echo     a. LE GROS CHAT, en 411,80 -- couche, et c'est sa
echo        QUEUE qui doit bouger (22 images).
echo     b. LE CHIEN, en 700,56.
echo     c. LE PERROQUET, en 672,114 -- 46 images, c'est le plus
echo        anime des trois.
echo.
echo   Sont-ils a leur place ? Et leurs couleurs : ils tirent
echo   sur la banque des BETES (base 1674), celle que tu avais
echo   validee sur les chats -- fauves, ou faux ?
echo.
echo   TOUT LE RESTE doit etre identique.
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe tous les objets
echo   animes sans toucher au decor.
echo.
pause

3sx.exe > "%~dp03sx-menagerie.log" 2>&1

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
type "%~dp03sx-menagerie.log"
echo.
pause
