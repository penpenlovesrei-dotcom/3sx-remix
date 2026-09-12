@echo off
rem Yun : les objets de droite, trouves en descendant l'arbre des spawners.
rem Ryu : sa banque de palettes basse, et deux hypotheses fermees.

cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   YUN : SIX OBJETS DE PLUS, TOUS A DROITE
echo ==========================================================
echo.
echo   Tu as signale qu'il manquait les animations des deux
echo   personnages devant le tram, du personnage a droite qui
echo   fume, et des oiseaux dans les cages a droite.
echo.
echo   Ils sont tous derriere UN spawner que la chaine ignorait,
echo   et qui en appelle TROIS AUTRES -- le meme motif que la
echo   chatte d'Oro qui fait ses chatons :
echo.
echo      routine d'etage, site 0x8C0DC68E
echo        -^> id 23   x 672, y 48
echo             -^> id 21   TROIS objets (696/64, 752/84, 752/63)
echo             -^> id 22   x 712, y 56
echo             -^> id 24   x 728, y 48
echo.
echo   Les six sont entre x 672 et 752, donc A DROITE de la
echo   bande -- ce qui recoupe ce que tu decris. Les trois
echo   spawners portent la table de scripts du decor 3 en dur :
echo   l'appelant et le litteral disent la meme chose.
echo.
echo   YUN passe de 6 objets a 12.
echo.
echo   CE QUE JE NE PEUX PAS ENCORE PROMETTRE : notre moteur ne
echo   joue qu'UN script par objet, alors que ces figures ont
echo   une machine a etats. Je pose le PREMIER etat qui porte
echo   des images. Deux consequences a verifier :
echo.
echo     - l'id 23 a un etat bien plus riche (script 12, TREIZE
echo       images) que celui que je pose (script 7, UNE image) ;
echo     - l'id 22 n'a que des poses d'une image.
echo.
echo   Donc si tu vois une figure FIGEE la ou tu attends une
echo   animation, dis-le : je poserai l'etat riche a la place.
echo.
echo ==========================================================
echo   RYU : CE QUE J'AI MESURE, ET CE QUI RESTE
echo ==========================================================
echo.
echo   CE QUI CHANGE : sa banque de palettes BASSE. Ses offsets
echo   0 a 5 recevaient 989 (le premier jeu) ; ils recoivent
echo   maintenant 1625, le transfert secondaire que son propre
echo   script d'etage charge en dur. C'est la valeur que les
echo   documents donnent depuis le 30/08 sans l'avoir appliquee.
echo   Regarde si des couleurs changent, en mieux ou en pire.
echo.
echo   DEUX HYPOTHESES FERMEES, pour ne pas les rouvrir :
echo.
echo   1. IL NE MANQUE PAS D'OBJETS. En descendant tout l'arbre
echo      de ses spawners, on ne trouve aucun bloc qu'on
echo      n'exploite deja. Ses treize objets sont tous poses.
echo.
echo   2. LE DECALAGE DE POSITION N'EXISTE PAS. Sept de ses
echo      treize objets ont un x NEGATIF -- il est le seul decor
echo      dans ce cas -- et l'enroulement les renvoie a droite
echo      (641, 689, 760, 817, 832, 881, 897). On soupconnait
echo      depuis longtemps qu'un decalage s'ajoutait quelque
echo      part. J'ai verifie ses QUATRE chargeurs : aucun
echo      n'ajoute quoi que ce soit a la position. Le detecteur
echo      trouve bien l'addition dans le chargeur temoin qui,
echo      lui, decale. Donc la piste est morte.
echo.
echo   CE QUE JE TE DEMANDE : « beaucoup d'anomalies » ne me
echo   suffit pas pour agir. Dis-moi CE QUE TU VOIS -- un objet
echo   au mauvais endroit, une couleur fausse, une figure qui ne
echo   bouge pas, un sprite manquant -- et sur quoi. Avec sept
echo   objets renvoyes a droite par l'enroulement, je parie que
echo   c'est la ; mais je ne veux pas corriger au jugé, ce
echo   chantier a deja paye trois fois ce pari.
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe tous les objets
echo   animes sans toucher au decor.
echo.
pause

3sx.exe > "%~dp03sx-yun-ryu.log" 2>&1

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
type "%~dp03sx-yun-ryu.log"
echo.
pause
