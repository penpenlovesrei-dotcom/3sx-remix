#ifndef VIDEO_DECOR_OBJETS_H
#define VIDEO_DECOR_OBJETS_H

#include "types.h"

#include <stdbool.h>

/// @brief Une tuile de 16x16 en index sur 8 bits, posee a une case de la grille du motif.
///
/// C'est le format exact d'un chip de 3SX : `mtrans.c` decomprime un chip dans
/// `mt->mltbuf` avec `lz_ext_p6_fx` puis le televerse avec `njReLoadTexturePartNumG`, et
/// pour un 16x16 la taille est `((wh * wh) << 6)` = 256 octets. Les octets sont deja
/// **entrelaces** par l'exportateur -- le televersement lit sa source a travers
/// `dctex_linear`, et une tuile lineaire sortirait en rayures.
typedef struct {
    s32 image; ///< numero d'image dans l'animation
    s32 x;     ///< case de la grille, en pixels
    s32 y;
    const unsigned char* pixels; ///< 256 octets, entrelaces
} DecorTuile;

/// @brief Une animation de decor de 2nd Impact, prete a etre dessinee par 3SX.
///
/// Genere par `dc-decors/outils/animations.py`. Une par etage, choisie comme la plus
/// grande qui tienne dans la grille du motif emprunte et qui bouge assez pour se voir.
///
/// * `nb_images` et `durees` viennent des **scripts d'animation** du binaire de 2nd
///   Impact (table maitresse a `0x8C5F9B38`) -- voir DONNEES.md, section 3.
/// * `famille` et `emplacement` viennent de la **liste d'affichage** relevee dans un etat
///   Flycast ; `x` et `y` s'en passent depuis `outils/poser22.py`, qui les tire du binaire.
///
/// `x` et `y` sont dans le repere de `BgMATRIX`, pas dans la banque, et les deux ne
/// comptent pas dans le meme sens. `bg.c` capture `BgMATRIX` AVANT son
/// `njTranslate(0, 0, 1024, ...)` puis `njScale(0, 1, -1, 1)` : une page posee en
/// `bank_y` se voit donc en `1024 - bank_y`. Et la grille du motif met la rangee d'image
/// `lig` en `(ligs-1-lig)*16` -- c'est `y_moteur` -- un morceau pose en `cy` couvrant
/// `cy-16 .. cy`. La rangee 0 du sprite est donc en `y + (ligs-1)*16`, d'ou :
///
///     x = bank_x            y = 1024 - bank_y - (ligs - 1) * 16
///
/// `bank_x`, `bank_y` etant le coin de l'image telle que la page la porte. C'est le
/// facteur `(ligs-1)*16` qui manquait : six rangees pour l'acolyte de `bg00`, 80 pixels.
/// * `palette` est lue en `0x8C7AFCCC + emplacement * 128`, en ARGB1555 ; c'est
///   `DecorObjets_InstallerPalette` qui echange rouge et bleu, `ColorRAM` etant en ABGR.
typedef struct {
    const char* nom;   ///< le decor de 2nd Impact, pour le journal
    s32 etage;         ///< l'etage de 3SX, 22 a 36
    s32 nb_images;
    s32 nb_tuiles;     ///< nb_images * cols * ligs
    s32 cols;          ///< la grille, en tuiles de 16
    s32 ligs;
    const DecorTuile* tuiles;
    const unsigned char* durees;    ///< nb_images entrees, en trames
    const unsigned short* palette;  ///< 64 couleurs ARGB1555
    s32 emplacement;   ///< l'emplacement de palette d'origine, pour memoire
    s32 x;             ///< la position lue dans la liste d'affichage
    s32 y;
    s32 famille;       ///< 1 = bgw[0], le plan fixe ; 2 = bgw[1], celui qui suit la camera
    /// @brief La profondeur, ou 0 pour garder celle du modele (`stg2200_data_tbl`, 80).
    ///
    /// **`famille` et `z` ne disent pas la meme chose.** `famille` choisit la MATRICE,
    /// donc le defilement : l'objet suit son plan quand la camera bouge. `z` choisit
    /// l'ORDRE DE DESSIN, et il est independant -- `mlt_obj_matrix` prend la matrice de
    /// `my_family` mais la profondeur de `position_z`. Un objet peut donc defiler avec un
    /// plan et se dessiner devant un autre, ce qui est justement le cas de la chute d'eau
    /// d'Oro : elle defile avec la grotte du fond et se dessine juste devant le couchant.
    ///
    /// L'echelle est celle de `stage_priority` : un z PLUS GRAND est plus LOIN. Pour nos
    /// etages, plan lointain 0x5E = 94, troisieme plan 0x5A = 90, plan proche 0x54 = 84.
    s32 z;
    /// @brief 1 = l'animation tourne en boucle ; 0 = elle reste sur son image 0.
    ///
    /// **Toutes les suites d'images ne sont pas des animations.** Les acolytes de Gill
    /// tournent la tete vers les combattants : leurs images sont des ORIENTATIONS
    /// choisies par la position des joueurs, pas des etapes d'un cycle. Les faire defiler
    /// donne un mouvement de tete absurde.
    ///
    /// Ca se mesure au lieu de se juger : l'ecart de chaque image a la premiere dessine
    /// un **palindrome** dont le maximum tombe au milieu -- la tete part et revient.
    /// Pour l'acolyte de `bg00` : 0 86 89 147 189 259 351 382 351 259 189 147 89 86.
    /// Une vraie boucle, elle, ne revient pas sur ses pas ; le filet d'eau d'Oro donne
    /// 0 469 474 474 527 549 522 497 473.
    ///
    /// `outils/animer2i.py` applique ce test. Suivre le regard des combattants demanderait
    /// de choisir l'image d'apres leur position, ce que rien ici ne sait faire.
    s32 boucle;
    /// @brief Les variantes de decor ou cet objet existe, en bits : 1<<z pour chaque z.
    ///
    /// **UN DECOR DE 2nd IMPACT N'EST PAS TOUJOURS LE MEME.** Le jeu tire `z` -- un
    /// entier de 0 a 3, uniforme -- a chaque entree d'etage, et certains scripts d'etage
    /// s'en servent pour changer ce qu'ils creent. C'est ce que Frederic avait vu sur des
    /// videos avant qu'on le lise : « j'ai 2 versions du decor, avec les sprites qui
    /// changent ».
    ///
    /// La menagerie d'Oro en est le cas le plus net. Son script d'etage repartit en
    /// `0x8C0DE5D2` sur `u8[contexte + 6]`, qui EST ce tirage :
    ///
    ///     z 0 -> le chien seul                 z 2 -> le chat et les chatons, sans chien
    ///     z 1 -> le chat, les chatons, le chien  z 3 -> le chien seul
    ///
    /// Le perroquet et les chauves-souris sont crees AVANT le repartiteur : ils sont de
    /// toutes les variantes, et portent donc `0xF`.
    ///
    /// `0xF` = toutes ; c'est la valeur de tous les objets des autres decors.
    ///
    /// **LES COMBATTANTS AUSSI CHOISISSENT** (16/09/2026). Le bit 0x10 fait exister l'objet
    /// quand aucun des deux combattants n'est un ami du decor, le bit 0x20 quand l'un
    /// d'eux l'est ; sans aucun des deux, l'objet ne depend pas des combattants. Le chien
    /// d'Oro lit le personnage des joueurs a sa naissance : couche en 700 contre les
    /// inconnus, debout en 608 devant Ibuki, Elena ou Oro.
    s32 variante;
    /// @brief 0, ou l'objet dont la ROUTINE choisit l'image -- voir `conduire`.
    ///
    /// 1 = le chien debout d'Oro (regard, queue, aboiement), 2 = le chien couche (repos,
    /// reveil), 3 = le poisson rouge de Yang (va-et-vient), 4 = son poisson noir (le tour
    /// de l'aquarium). Les autres fiches n'ecrivent pas ces champs : le C les met a zero.
    s32 comportement;
    /// @brief `(image, duree)` pas a pas, les suites bout a bout.
    ///
    /// Les pas renvoient a des images DISTINCTES : le poisson noir enchaine 66 images et
    /// l'identite de motif n'en code que 64.
    const unsigned char* pas;
    /// @brief Le premier pas de chaque suite, puis la fin : `nb_suites + 1` entrees.
    const unsigned short* suites;
    s32 nb_suites;
    /// @brief Le trajet d'un objet qui se deplace : `{ duree, vx, vy, suite }` par segment.
    ///
    /// `vx` et `vy` sont en 1/256 de pixel par trame ; `suite` vaut -1 quand le segment ne
    /// change pas l'animation. La liste boucle sur son premier segment, et l'objet y
    /// retrouve sa position de naissance -- c'est ce que font les routines qu'elle
    /// remplace : la caleche de Dudley 1 revient sous son tunnel, l'eau de la riviere
    /// d'Elena 1 revient a sa place toutes les 33 trames. Voir `TRAJET` dans le .c.
    const short* trajet;
    s32 nb_trajet;
} DecorAnimation;

extern const DecorAnimation decor_animations[];
extern const int decor_nb_animations;
/// @brief La PREMIERE animation de chaque etage, ou -1 s'il n'en a pas.
extern const short decor_anim_par_etage[58];
/// @brief Combien d'animations chaque etage porte. Gill en a quatre.
extern const short decor_nb_par_etage[58];

/// @brief Combien d'objets animes cet etage demande. `bg_index`, pas `stage`.
///
/// Ne compte que les objets de la VARIANTE courante -- voir `DecorAnimation::variante`.
s32 DecorObjets_Combien(s32 bg_index);

/// @brief La variante de decor tiree pour cet etage, 0 a 3.
///
/// Tiree une fois par etage, comme 2nd Impact le fait a chaque entree. `SF3_DECOR_VARIANTE`
/// la force, ce qui permet de voir les quatre a la demande.
s32 DecorObjets_Variante(void);

/// @brief La profondeur forcee par `SF3_DECOR_Z`, ou 0 si la variable est absente.
///
/// Interrupteur de DIAGNOSTIC : il met tous nos objets a la meme profondeur pour savoir si
/// un objet invisible est cache par un plan du decor. Sans la variable, rien ne change.
s32 DecorObjets_ProfondeurForcee(void);


/// @brief La `rang`-ieme animation de cet etage, ou NULL.
const DecorAnimation* DecorObjets_Animation(s32 bg_index, s32 rang);

/// @brief Marque l'objet dont les morceaux devront etre remplaces, ou NULL pour aucun.
///
/// **C'est la garde, et elle porte sur l'OBJET, pas sur l'etage.** Le crochet est pose
/// dans `mlt_obj_trans_ext` et `mlt_obj_trans_cp3_ext`, qui dessinent TOUT -- combattants
/// compris. Garder sur `bg_w.stage` a suffi a couvrir Alex et Ryu de blocs blancs et a
/// saturer le cache de chips. On compare donc le `WORK` lui-meme.
///
/// Fixe aussi l'animation courante, d'apres `bg_index`.
/// @brief Lache le pointeur de notre objet quand le tas d'effets le reprend.
///
/// **Le tas RECYCLE ses emplacements.** Nos gardes comparent le `WORK` dessine a
/// `notre_objet` ; quand l'etage se termine, notre objet rend le sien et un objet des
/// menus le reprend a la meme adresse. Le pointeur coincide, et l'acolyte de Gill se
/// dessine par-dessus l'ecran de selection. `push_effect_work` et `effect_work_init`
/// appellent donc ceci -- le second avec NULL, qui vide sans condition.
void DecorObjets_Oublier(const void* work);

void DecorObjets_Marquer(const void* work, s32 bg_index, s32 rang);

/// @brief L'identite de cache de motif a employer pour NOTRE objet.
///
/// **C'est le correctif du gel a l'entree d'un etage ajoute.** `mlt_obj_trans_cp3_ext` a
/// deux chemins, choisis par `check_patcash_ex_trans(mt->cpat, cc.code)` ou `cc.code` vaut
/// `(0 << 16) | wk->cg_number` : **l'identite d'un motif est le numero de graphique du
/// donneur, et rien d'autre.** Le premier chemin televerse les morceaux et note leurs
/// emplacements dans `cp->map` ; le second ne fait que les CHERCHER, parmi ces
/// emplacements-la et pas d'autres (`makeup_tpu_free`), et `get_mltbuf16_ext` **boucle a
/// l'infini** s'il ne trouve pas.
///
/// Or nos cles de morceau portent NOTRE image, qui avance a NOTRE cadence, alors que le
/// `cg_number` du donneur tient cinquante trames sur sa premiere image. L'identite doit
/// donc porter notre image -- et le `cg_number` du donneur doit en SORTIR, sans quoi le
/// produit des deux depasserait les 64 emplacements de `PatternCollection`.
///
/// @param code rendu : l'identite a employer, seulement si la fonction rend 1
/// @return 1 si c'est notre objet et qu'il est pret, 0 sinon -- et `code` reste intact
s32 DecorObjets_Identite(const void* work, u32* code);

/// @brief Les 256 octets a poser pour ce morceau, et la cle de cache a employer.
///
/// @param work    le WORK en cours de dessin ; tout autre que le notre rend NULL
/// @param cg      le numero de graphique du donneur, inutilise -- on tient notre cadence
/// @param x,y     la case du morceau dans la grille du motif
/// @param taille  la taille du chip ; on ne traite que 256 (16x16)
/// @param cle     rendu : l'offset de cache a employer, unique par (image, case)
/// @return 256 octets a nous, 256 octets **vides** pour les cases que notre sprite ne
///         couvre pas -- sinon le dessin du donneur transparaitrait autour -- ou NULL.
///
/// Le nombre de cles vivantes est **borne** par la duree de vie d'un motif dans le cache
/// (`mts_base[7].life16` = 12 trames) : seules les images vues dans les douze dernieres
/// trames occupent des emplacements. A six trames par image, c'est deux ou trois images,
/// soit moins de 80 chips sur les 256 de `mts[7]`.
const unsigned char* DecorObjets_Tuile(const void* work, s32 cg, s32 x, s32 y, s32 taille, u16* cle);

/// @brief Fait avancer NOTRE animation d'une trame, a la cadence lue dans le script.
///
/// Rend aussi au donneur le motif emprunte a la trame precedente : il n'est ainsi
/// emprunte que pendant la passe de dessin.
void DecorObjets_Avancer(const void* work);

/// @brief La position ou dessiner NOTRE objet s'il se deplace -- les poissons de Yang.
///
/// @return 1 et la position dans `x`, `y` (le repere de `xyz[].disp.pos`) si l'objet bouge,
///         0 sinon, et rien n'est ecrit.
s32 DecorObjets_Position(const void* work, s32* x, s32* y);


/// @brief Pose nos couleurs dans `ColorRAM` et les envoie au materiel.
///
/// Ecrire dans `ColorRAM` ne suffit pas : le dessin lit une copie cote materiel.
/// `palUpdateGhostCP3` fait l'envoi, et l'emplacement 300 n'est pas un depassement --
/// la palette fantome en compte 512, `ppgSetupPalChunkDir` faisant
/// `pch->total = SDL_Swap16BE(ppl->palettes)`, un boutisme inverse.
///
/// **Rouge et bleu s'echangent** : `ColorRAM` est en ABGR1555 (`palCreateGhost` met
/// `palFormRam.rs = 0` et `bs = 10`), nos couleurs sortent de la Dreamcast en ARGB1555.
void DecorObjets_InstallerPalette(const void* work);

/// @brief NOTRE groupe : notre table de trans et notre table de textures.
///
/// **C'est ce qui remplace l'emprunt.** Le fichier recrivait la liste de morceaux d'un
/// motif du jeu dans la table de trans du groupe donneur ; ca n'a jamais tenu, et pour
/// trois raisons qui se cumulent : la table est PARTAGEE, le `cg_number` du donneur
/// DEFILE trame apres trame -- donc le motif change sous nos pieds -- et ses motifs n'ont
/// ni la meme longueur ni les memes tailles de morceaux. Chaque contournement a produit
/// un gel : trois groupes differents vus avec « 0 emplacements occupes ».
///
/// `mlt_obj_trans_cp3_ext` ne demande pourtant que deux blocs, et ils se fabriquent :
/// une table de trans (`u32 offsets[]`, puis `u16 nombre` et les morceaux en ecarts) et
/// une table de textures (`u32 offsets[]`, puis `TEX { u8 wh, ... }`). On les pose en dur
/// dans `decor_objets.c` et on les tend au moteur ici.
///
/// @param work    le WORK dessine ; tout autre que le notre rend 0
/// @param trans_table, texture_table  rendus : NOS deux tables
/// @param n       rendu : l'indice du motif dans notre table -- toujours 0
/// @return 1 si c'est notre objet et que son motif est bati, 0 sinon
s32 DecorObjets_Groupe(const void* work, void** trans_table, void** texture_table, s32* n);

/// @brief Trace du dernier morceau traite, pour savoir ou un gel s'arrete.
void DecorObjets_Trace(s32 a_nous, s32 groupe, s32 offset, s32 wh);

#endif // VIDEO_DECOR_OBJETS_H
