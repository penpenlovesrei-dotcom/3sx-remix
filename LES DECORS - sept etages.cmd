@echo off
rem Les objets de decor, lus dans le code, pour cinq etages.

cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   CINQ ETAGES ONT MAINTENANT LEURS OBJETS DE DECOR
echo ==========================================================
echo.
echo   Plus rien n'est devine : le script d'etage de chaque decor
echo   appelle son chargeur avec une constante, et le chargeur
echo   lit un nombre et un pointeur dans deux tables.
echo.
echo   ETAGE 22  GILL   4 objets   (deja connu)
echo   ETAGE 23  ALEX   1 objet    la turbine de toit
echo   ETAGE 24  RYU    7 objets   les bains
echo   ETAGE 25  YUN    3 objets   le marche de Hong Kong
echo   ETAGE 27  NECRO 15 objets   le laboratoire
echo   ETAGE 28  HUGO   5 objets   la fete foraine
echo   ETAGE 31  ORO    8 objets   (inchange)
echo   ETAGE 32  YANG   1 objet    le temple
echo.
echo CE QUE JE CHERCHE, ETAGE PAR ETAGE
echo.
echo   ALEX  a. La turbine de toit, pres du mur au drapeau : bien
echo            posee sur le rebord, et elle tourne ?
echo.
echo   YUN   b. Le cuisinier au wok derriere son etal, et le
echo            client assis a la table. Sur mon apercu ils sont
echo            tous deux exactement en place -- confirme-le.
echo         c. Un objet est ECARTE : 9x11 = 99 cases, la cle de
echo            cache n'en code que 32. Il manquera donc quelque
echo            chose sur cet etage.
echo.
echo   YANG  d. UN objet, pose sur les marches a gauche. Ses
echo            teintes sortent PALES sur un decor rouge et ocre :
echo            si la couleur te parait fausse, dis-le. bg0b a
echo            plusieurs groupes d'offsets, donc peut-etre
echo            plusieurs banques de palettes, comme Oro et Ryu.
echo.
echo   HUGO  g. Cinq objets dans la foule. Sur mon apercu les
echo            POSITIONS sont bonnes -- ils sont au sol, parmi
echo            les gens -- mais du VERT FLUO sort sur des
echo            vetements. bg06 a deux groupes d'offsets (0..11
echo            et 22..26) et ses objets emploient les DEUX : la
echo            base 1219 ne vaut que pour le premier. Confirme
echo            ce que tu vois, je chercherai la seconde.
echo         h. L'etage 28 passe a DEUX pages de cache : 298
echo            morceaux au pire.
echo.
echo   NECRO i. QUINZE objets, le decor le plus riche jusqu'ici :
echo            ecrans, voyants, tuyaux, tube lumineux. Ils
echo            tiennent en UNE page de cache (204 morceaux).
echo            Les positions ont l'air bonnes sur l'apercu, et
echo            les teintes collent a l'ambiance rose du labo --
echo            mais c'est ton oeil qui trancherait mieux.
echo.
echo   IBUKI    RIEN A GENERER, et ce n'est pas un manque d'outil.
echo            Son decor est bg09 (le temple aux pins, etage 30).
echo            **B09.PK n'existe pas sur le disque de 2nd
echo            Impact** -- SFNG2 va de B00 a B16 en sautant B09.
echo            Donc aucune archive de sprites, et le chargeur ne
echo            lui attribue aucun bloc. Son decor n'a tout
echo            simplement pas d'objets.
echo.
echo   RYU   e. Les couleurs sont corrigees -- les deux cascades
echo            sortent en bleu clair. Mais LES POSITIONS SONT
echo            ENCORE FAUSSES : baigneurs et cascades trop hauts.
echo            C'est le point que je reprends ensuite.
echo.
echo   ORO   f. Inchange, ses huit objets sont la.
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe tous les objets
echo   animes sans toucher au decor.
echo.
pause

3sx.exe > "%~dp03sx-decors.log" 2>&1

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
type "%~dp03sx-decors.log"
echo.
pause
