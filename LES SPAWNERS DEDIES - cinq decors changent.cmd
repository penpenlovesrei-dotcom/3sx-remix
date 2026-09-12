@echo off
rem Chantier 2 : les spawners dedies, desassembles au lieu d'etre supposes.

cd /d "%~dp0build\application\bin"

echo ==========================================================
echo   LES SPAWNERS DEDIES : 54 OBJETS -> 63, ET UNE FAUSSE
echo   ATTRIBUTION CORRIGEE
echo ==========================================================
echo.
echo   Chaque spawner a ete DESASSEMBLE : ses champs, leur
echo   offset dans l'objet, la taille de son enregistrement, la
echo   facon dont il atteint son bloc et le nombre de tours de
echo   sa boucle. Rien n'est suppose. L'outil est
echo   outils/spawners2i.py.
echo.
echo ----------------------------------------------------------
echo   CE QUI CHANGE, DECOR PAR DECOR
echo ----------------------------------------------------------
echo.
echo   GILL  (22)  4 objets -^> 7
echo         Son SECOND spawner, 0x8C0258DA, n'avait jamais ete
echo         exploite. Enregistrements de dix octets sans plan
echo         ni palette. Sa boucle compare a 4 : quatre
echo         enregistrements, dont un doublon ecarte.
echo.
echo   RYU   (24)  8 objets -^> 11
echo         Son spawner 0x8C036688, argument 0, trois
echo         enregistrements de dix-huit octets.
echo.
echo   YUN   (25)  4 objets -^> 5
echo         Il RECUPERE un objet qui etait pose chez Hugo.
echo.
echo   HUGO  (28)  8 objets -^> 6      <-- IL EN PERD DEUX
echo   ELENA (30)  1 objet  -^> 4
echo         Son spawner 0x8C03CBCC porte son bloc en dur et
echo         boucle quatre fois. Quatre grands objets de douze
echo         images, en 784/32, 720/64, 240/32 et 304/64. Le
echo         quatrieme est ECARTE faute de place (voir plus bas).
echo.
echo ----------------------------------------------------------
echo   POURQUOI HUGO PERD DEUX OBJETS
echo ----------------------------------------------------------
echo.
echo   0x8C17F54C n'est pas un bloc : c'est la table des
echo   NOMBRES de son spawner, qui s'indexe
echo.
echo      nombre   = u16 [0x8C17F54C + arg*8  + z*2]
echo      pointeur = u32 [0x8C5FA00C + arg*16 + z*4]
echo.
echo   La chaine la lisait comme des enregistrements et en
echo   tirait QUATRE objets. Or ce spawner n'est appele que
echo   DEUX fois dans tout le binaire : par Yun avec
echo   l'argument 2, par Hugo avec l'argument 3. Chacun a UN
echo   enregistrement. Les deux autres sont l'argument 4, que
echo   personne n'appelle.
echo.
echo   Donc : un des quatre etait a Yun, deux n'etaient a
echo   personne. Si tu reconnais dans la foule de Hugo une
echo   figure qui a disparu et qui te manque, dis-le -- mais le
echo   code dit qu'elle n'y etait pas.
echo.
echo ----------------------------------------------------------
echo   ET « z » EXISTE AUSSI EN 2nd IMPACT
echo ----------------------------------------------------------
echo.
echo   On le croyait propre a New Generation. C'est un TIRAGE
echo   uniforme sur 0..3, refait a chaque entree d'etage, et le
echo   generateur pseudo-aleatoire est identique octet pour
echo   octet dans les deux jeux. Chaque couple (spawner,
echo   argument) porte donc quatre variantes. On ne cuit que
echo   z = 0.
echo.
echo ----------------------------------------------------------
echo   LA BORNE QUI AVAIT GELE IBUKI EST MAINTENANT VERIFIEE
echo ----------------------------------------------------------
echo.
echo   PatternCollection ne tient que SOIXANTE-QUATRE identites
echo   de motif, et chaque couple (fiche, image vivante) en
echo   occupe une. Elena en demandait 68 avec ses quatre
echo   objets : le generateur ECARTE le quatrieme et le DIT,
echo   au lieu de laisser le jeu figer sans message.
echo   verifier_objets.py le controle a froid sur les 271
echo   fiches -- aucune faute.
echo.
echo ==========================================================
echo   CE QUE JE TE DEMANDE DE REGARDER
echo ==========================================================
echo.
echo   ELENA (30) est le plus gros changement : trois grands
echo   objets animes de douze images la ou il n'y en avait
echo   qu'un. Sont-ils a leur place, et animes ?
echo.
echo   GILL (22) : trois objets de plus. Ses quatre acolytes
echo   ne devaient PAS bouger -- s'ils ont change, c'est moi.
echo.
echo   RYU (24) : trois de plus. Ses positions etaient deja
echo   fausses (trop hautes), ce n'est pas corrige ici.
echo.
echo   YUN (25) : un objet de plus, celui repris a Hugo.
echo.
echo   HUGO (28) : deux de moins. Le vert reste absent ?
echo.
echo   NECRO (27), ORO (31), SEAN (34), YANG (32), ALEX (23),
echo   DUDLEY (26) : rien ne devait bouger.
echo.
echo   L'INTERRUPTEUR : SF3_DECOR_OBJETS=0 coupe tous les objets
echo   animes sans toucher au decor.
echo.
pause

3sx.exe > "%~dp03sx-spawners.log" 2>&1

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
type "%~dp03sx-spawners.log"
echo.
pause
