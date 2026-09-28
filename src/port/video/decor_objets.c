/**
 * @file decor_objets.c
 * Les sprites animes de 2nd Impact, dessines par le systeme d'objets de decor de 3SX.
 *
 * CE QUI SE PASSE
 * ---------------
 * Un objet de decor (`eff05.c`) est dessine motif par motif, et un motif est une grille
 * de morceaux de 16x16 dont les numeros changent d'une image a l'autre : c'est comme ca
 * que l'animation marche. `mtrans.c` decomprime chaque morceau dans `mt->mltbuf` puis le
 * televerse dans une page de cache :
 *
 *     size = (wh * wh) << 6;                             256 octets pour un 16x16
 *     lz_ext_p6_fx(&((u8*)texptr)[1], mt->mltbuf, size);
 *     njReLoadTexturePartNumG(page, mltbuf, chip, size);
 *
 * Ces pages **ne viennent pas de l'archive** : elles sont remplies a l'execution, donc
 * elles ne passent jamais par `ppgSetupTexChunk_3rd` ou `tex_remix` est branche. Le seul
 * point d'injection est celui-la.
 *
 * PLUS RIEN N'EST EMPRUNTE
 * ------------------------
 * Ce fichier a longtemps recrit la liste de morceaux d'un motif du jeu dans la table de
 * trans du groupe donneur. Ca n'a jamais tenu : la table est PARTAGEE, le `cg_number` du
 * donneur DEFILE trame apres trame, et ses motifs n'ont ni la meme longueur ni les memes
 * tailles de morceaux. Il apporte maintenant SON groupe -- voir `DecorObjets_Groupe`.
 *
 * PLUSIEURS OBJETS PAR ETAGE
 * --------------------------
 * L'etat est un TABLEAU, une entree par objet. Gill en a quatre dans le binaire de 2nd
 * Impact (table `0x8C183DC8`), et une seule etait posee. Chaque objet a sa grille, sa
 * cadence, son emplacement de palette et sa place dans les cles de cache :
 *
 *     identite de motif   0x00D3 <<16 | rang <<8 | image
 *     cle de morceau      rang <<11 | image <<5 | case
 *     palette             EMPLACEMENT_PALETTE + rang, et `my_col_code` suit
 *
 * DEUX ERREURS QUE CE FICHIER EVITE ENCORE
 * ----------------------------------------
 * 1. **La garde porte sur l'OBJET, pas sur l'etage.** Le crochet est sur un chemin
 *    partage : les combattants passent par la meme fonction. Garder sur `bg_w.stage` les
 *    couvrait de blocs blancs.
 * 2. **L'identite de motif porte notre image.** Sinon le chemin du cache cherche des
 *    cles que l'autre chemin n'a jamais enregistrees, et `get_mltbuf16_ext` boucle a
 *    l'infini. Voir `DecorObjets_Identite`.
 */

#include "port/video/decor_objets.h"
#include "port/video/trace_fin.h"

#include "sf33rd/Source/Game/engine/plcnt.h"
#include "sf33rd/Source/Game/engine/slowf.h"
#include "sf33rd/Source/Game/engine/workuser.h"
#include "sf33rd/Source/Game/rendering/color3rd.h"
#include "sf33rd/Source/Game/stage/bg.h"
#include "sf33rd/AcrSDK/ps2/flps2vram.h"
#include "sf33rd/Source/Common/PPGFile.h"

#include <SDL3/SDL.h>

#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>

/* TRACE -- a retirer une fois la mecanique acquise. Vidage a chaque ligne : un gel ne
   doit pas emporter la derniere information ecrite. */
static FILE* jrn = NULL;

static void trace(const char* fmt, s32 a, s32 b, s32 c) {
    if (jrn == NULL) {
        jrn = fopen("decor-objets.log", "w");

        if (jrn == NULL) {
            return;
        }
    }

    fprintf(jrn, fmt, (int)a, (int)b, (int)c);
    fflush(jrn);
}

/// La cle que partagent TOUS les morceaux vides : une seule entree de cache pour eux.
#define CLE_VIDE 0xFFFFu

static const unsigned char tuile_vide[256] = { 0 };

/// La mise en place d'etage en cours, modulo quatre -- voir `DecorObjets_Identite`.
static u32 generation = 0;

/// Un morceau de la table de trans, tel que `mtrans.c` le lit.
typedef struct {
    s16 x;
    s16 y;
    u16 attr;
    u16 code;
} MorceauTrans;

/* L'ATTRIBUT DES MORCEAUX EST NUL, ET C'EST UNE CORRECTION.
   Notre objet passe par `mlt_obj_trans_cp3_ext` -- mts[7] a le mode 8210, dont l'octet
   bas vaut 18 -- et ce chemin calcule `palt = (trsptr->attr & 0x1FF) + palo`. Les neuf
   bits bas de l'attribut **s'ajoutent** a l'emplacement de palette de l'objet. Zero est
   la seule valeur juste. Le reste de l'attribut n'est lu que par le masque 0xC000, les
   retournements, qu'on ne veut pas non plus. */
#define ATTR_MORCEAU 0x0000
#define NOTRE_CODE 0

/// Le plus grand nombre de cases d'une grille -- 4x6 pour l'acolyte de Gill.
#define CASES_MAX 64

/// Le plus grand nombre d'objets d'un etage. Gill en a quatre.
///
/// LA BORNE N'EST PLUS DANS LA CLE DE CACHE -- 16/09/2026. Elle y etait : `rang << 11 |
/// image << 5 | case` ne laissait que CINQ bits au rang, donc 32 objets, et le compte
/// etait ECRETE en silence au-dela. Necro en demande 34 depuis qu'il recoit ses elements
/// du premier jeu et son conducteur, et Yang en demandera davantage.
///
/// La cle est maintenant un RANG DE MORCEAU dans l'etage : chaque objet recoit une base,
/// la somme des `nb_images * cols * ligs` de ceux qui le precedent, et sa cle vaut
/// `base + image * cases + case`. Les cles restent uniques et tiennent dans les seize
/// bits tant que l'etage total reste sous 65534 -- le plus charge, Necro, en compte
/// environ quatre mille. `DecorObjets_Marquer` refuse l'objet qui deborderait.
///
/// C'etait 12, et le compte etait ECRETE en silence. Depuis que les objets trop larges sont
/// servis en morceaux voisins au lieu d'etre ecartes (`animer2i.morceaux_objet`), un etage
/// en compte bien plus : Necro en a 34, Elena 8 rien que pour son grand sprite.
/// 56 DEPUIS LE 18/09/2026 (48 avant). Les passants de New Generation et les immeubles de
/// Sean ont fait deborder Alex, qui perdait un element faute de rang. Le tas d'effets en
/// compte 128 (`EFFECT_MAX`) : il en reste 72 au jeu, contre 80 avant.
#define OBJETS_MAX 56

/// L'emplacement de palette du PREMIER objet ; le rang `k` prend `+ k`.
///
/// `my_col_code` vaut 8492 dans la fiche, et `8492 & 0x1FF` donne 300. `effect_05_init`
/// ajoute le rang, si bien que `wk->colcd` designe la bonne palette sans autre reglage.
#define EMPLACEMENT_PALETTE 300

/* NOTRE TABLE DE TRANS, une par objet.
 *
 * `mlt_obj_trans_cp3_ext` lit : `u32 offsets[]`, puis a `offsets[n]` un `u16` de nombre
 * de morceaux suivi des morceaux. Un seul motif par objet, donc `offsets[0] = 4` -- la
 * taille du tableau d'offsets lui-meme. `MorceauTrans` n'a besoin que d'un alignement sur
 * deux octets, la disposition tombe donc juste. */
typedef struct {
    u32 offsets[1];
    u16 count;
    MorceauTrans cases[CASES_MAX];
} NotreTrans;

/* NOTRE TABLE DE TEXTURES, partagee : tous nos morceaux sont des 16x16.
 *
 *     0x49 -> dw = (0x49 & 0xE0) >> 2 = 16     dh = (0x49 & 0x1C) * 2 = 16
 *             wh = (0x49 & 3) + 1 = 2          taille = (wh * wh) << 6 = 256
 *
 * Les octets qui suivent ne sont jamais lus : `DecorObjets_Tuile` rend toujours 256
 * octets a nous pour ce morceau, donc `lz_ext_p6_fx` n'est jamais appele dessus. C'est ce
 * qui nous dispense de compresser quoi que ce soit. */
static struct {
    u32 offsets[1];
    unsigned char tex[8];
} notre_texture = { { 4 }, { 0x49, 0, 0, 0, 0, 0, 0, 0 } };

static struct {
    const void* work;
    const DecorAnimation* anim;
    s32 trame;
    s32 palette_envoyee; ///< 1 des que le materiel a nos couleurs -- voir InstallerPalette
    s32 cle_base;        ///< le premier morceau de cet objet dans l'espace des cles
    NotreTrans trans;
    /* L'etat d'un objet a comportement -- voir `conduire`. */
    s32 suite_trajet;  ///< le segment de trajet en cours
    s32 reste_trajet;  ///< les trames qui restent sur ce segment
    s32 etat;    ///< -1 a la naissance
    s32 suite;   ///< la suite jouee
    s32 pas;     ///< le pas dans la suite
    s32 reste;   ///< les trames qui restent sur ce pas
    s32 finie;   ///< 1 quand une suite qui ne boucle pas a joue son dernier pas
    s32 regard;  ///< 0 gauche, 1 face, 2 droite
    s32 tenue;   ///< les trames ou le regard ne change plus
    s32 bouge;   ///< 1 si l'objet se deplace : `px`, `py` sont alors sa position
    s32 px, py;  ///< la position de 2I, en 16.16 comme `xyz[].cal`
    s32 vx, vy;  ///< sa vitesse, en 16.16 comme `mvxy.a[]`
    s32 echelle;        ///< la taille courante en 1/64, 0 quand l'objet n'est pas mis a l'echelle
    s32 echelle_trame;  ///< les trames depuis le dernier cran
    s32 brise;          ///< 1 la trame ou la rupture part -- voir `RUPTURE`
    s32 contact;        ///< le contact de la trame precedente, pour n'avancer qu'au franchissement
} nos[OBJETS_MAX];

static s32 nb_objets = 0;

/* L'INTERRUPTEUR. `SF3_DECOR_OBJETS=0` : aucun objet anime ne nait. Il sert a repondre
   sans rien casser a la question « ce defaut vient-il des objets ? » -- le decor et ses
   elements statiques n'en dependent pas. */
static s32 objets_permis(void) {
    static s32 lu = 0;
    static s32 permis = 1;

    if (!lu) {
        const char* v = getenv("SF3_DECOR_OBJETS");

        lu = 1;
        permis = !(v != NULL && v[0] == '0');
        trace("objets animes permis : %d %d %d\n", permis, 0, 0);
    }

    return permis;
}

/* LA VARIANTE DE DECOR, ET COMMENT ELLE EST TIREE.
 *
 * 2nd Impact tire `z` -- 0 a 3, uniforme -- a chaque entree d'etage, et le script d'etage
 * d'Oro s'en sert pour choisir ce qu'il cree : son chien seul, ou son chat et ses chatons,
 * ou les deux. On reproduit le tirage plutot que de figer une composition.
 *
 * ELLE EST TIREE UNE FOIS PAR ETAGE, pas par trame ni par round. Si elle changeait en
 * cours de route, `DecorObjets_Combien` renverrait un autre compte entre deux appels et
 * les RANGS glisseraient -- or le rang est dans la cle de cache et dans l'emplacement de
 * palette. Les objets se dessineraient l'un a la place de l'autre.
 *
 * `SF3_DECOR_VARIANTE=0..3` la force. C'est ce qui permet de voir les quatre a la demande
 * au lieu d'attendre le hasard. */
static s32 variante_courante = 1;
static s32 variante_etage = -1;

/* LA MANCHE, POUR LES OBJETS -- 25/09/2026.
 *
 * `bg_w.area` n'avance que pour les etages a BANDES multiples (`Bg_Aire_Suivante` sort
 * avant sur les autres), et `appear.c` le lit pour couper les entrees scenarisees a partir
 * de la manche 2. L'avancer partout changerait donc les entrees de tous les etages, ce qui
 * n'est pas demande. Les objets tiennent leur propre compte, remis a zero au match suivant
 * par `tirer_la_variante`, qui sait deja reconnaitre un nouveau match. */
static s32 aire_objets = 0;

static s32 variante_forcee(void) {
    static s32 lu = 0;
    static s32 valeur = -1;

    if (!lu) {
        const char* v = getenv("SF3_DECOR_VARIANTE");

        lu = 1;

        if (v != NULL && v[0] >= '0' && v[0] <= '3') {
            valeur = v[0] - '0';
            trace("variante de decor FORCEE a %d %d %d\n", valeur, 0, 0);
        }
    }

    return valeur;
}

s32 DecorObjets_Variante(void) {
    return variante_courante;
}

/* LES DEUX JETS DE HUGO -- 24/09/2026. UN DIAGNOSTIC, PAS UN REGLAGE.

   Frederic : « les jets et les combattants sont devant les 2 poteaux et la corde qui les
   relie au lieu d'etre derriere ; de plus, les jets devraient etre derriere les 2 autres
   poteaux et la 2eme corde ».

   Les poteaux et les DEUX cordes sont dans le PLAN PROCHE -- la demi-banque basse de la
   banque 0, notre liste 196, verifiee en la dessinant seule. Sa profondeur est lue dans la
   table des couches de 2nd Impact (`0x8C601EE8`, decor 6, couche 1) : **plan 2,
   profondeur 84**, et cette couche n'a qu'UN groupe, donc une seule profondeur pour tout
   ce qu'elle porte.

   Les deux jets sont des objets a **83**. Un cran devant le plan : c'est pour ca qu'ils
   passent devant les poteaux, et 2nd Impact ne dit rien d'autre.

   Quant aux combattants, leur profondeur est de 28 a 56 -- `char_init_data2` de 3SX, et la
   MEME table, aux memes valeurs, dans SF3_2ND.BIN (0x8C5FB0EA, pas de 0x6C). Rien du decor
   de Hugo n'est devant eux dans AUCUN des deux jeux : ses couches sont a 84 et 94, ses
   elements a 76 et 82, ses objets de 74 a 83. C'est ce que disait deja la note de
   `SF3_DECOR_Z` : « 20 met tous nos objets devant les plans ET DEVANT LES COMBATTANTS ».

   Je ne deplace donc rien de ma propre autorite. Cette variable met les deux jets a la
   profondeur demandee pour que Frederic juge sur l'image : `SF3_DECOR_JETS=85` les passe
   DERRIERE le plan proche. Si c'est bien ce qu'il faut voir, alors c'est la profondeur du
   PLAN, pas celle des jets, qu'il faudra reprendre -- et ce sera une autre lecture. */
s32 DecorObjets_ProfondeurDesJets(void) {
    static s32 lu = 0;
    static s32 valeur = 0;

    if (!lu) {
        const char* v = getenv("SF3_DECOR_JETS");

        lu = 1;

        if (v != NULL) {
            valeur = atoi(v);

            if (valeur < 1 || valeur > 127) {
                valeur = 0;
            }
        }

        trace("profondeur des jets : %d %d %d\n", valeur, 0, 0);
    }

    return valeur;
}

/* LA PROFONDEUR FORCEE -- un diagnostic, pas un reglage.
   15/09 : chez Yun, les objets de la moitie droite du decor NAISSENT (le journal les marque,
   aux x/y/z exacts des fiches) mais ne se voient pas, sauf le panneau vertical, seul a
   z 23. `SF3_DECOR_Z=20` met tous nos objets devant les plans (84, 90, 94) et devant les
   combattants : s'ils apparaissent, c'est un plan qui les cachait. */
s32 DecorObjets_ProfondeurForcee(void) {
    static s32 lu = 0;
    static s32 valeur = 0;

    if (!lu) {
        const char* v = getenv("SF3_DECOR_Z");

        lu = 1;

        if (v != NULL) {
            valeur = atoi(v);

            if (valeur < 1 || valeur > 127) {
                valeur = 0;
            }
        }

        trace("profondeur forcee : %d %d %d\n", valeur, 0, 0);
    }

    return valeur;
}

/* LES AMIS D'UN DECOR -- 16/09/2026.
 *
 * Le spawner du chien d'Oro (`0x8C03369E`) lit le personnage des deux joueurs et en tire
 * une HUMEUR dans `0x8C17F364` : Ibuki et Elena 1, Oro 2, les autres 0. Une humeur non
 * nulle en fait un chien debout, qui regarde son prefere ; sinon il est couche, ailleurs.
 * Les numeros de personnage de 2I sont ceux de 3S pour les quinze premiers.
 *
 * New Generation (etage 53) a le MEME chien : spawner `0x8C0A9F06`, et sa table d'humeur
 * `0x8C1B2B08` est octet pour octet celle de 2I -- 17/09/2026. */
static const unsigned char humeur_oro[16] = { 0, 0, 0, 0, 0, 0, 0, 1, 1, 2, 0, 0, 0, 0, 0, 0 };

static s32 humeur_du_decor(s32 bg_index, s32 perso) {
    if ((bg_index != 31 && bg_index != 53) || perso < 0 || perso >= 16) {
        return 0;
    }

    return humeur_oro[perso];
}

static s32 combattants_tires = -1;
static s32 un_ami_present = 0;

/// Tire la variante de cet etage, une seule fois -- ou de nouveau si les combattants changent.
static void tirer_la_variante(s32 bg_index) {
    const s32 forcee = variante_forcee();
    const s32 combattants = (My_char[0] << 8) | My_char[1];

    /* LES COMBATTANTS ENTRENT DANS LA CLE : un nouveau match sur le meme etage est une
       nouvelle entree, et le chien doit y lire les nouveaux joueurs. Ils ne changent pas
       pendant un match, donc les rangs restent stables. */
    if (bg_index == variante_etage && combattants == combattants_tires) {
        return;
    }

    variante_etage = bg_index;
    combattants_tires = combattants;
    aire_objets = 0;
    variante_courante = (forcee >= 0) ? forcee : (s32)(rand() & 3);
    un_ami_present = humeur_du_decor(bg_index, My_char[0]) != 0 ||
                     humeur_du_decor(bg_index, My_char[1]) != 0;
    trace("etage %d : variante de decor %d, ami %d\n", bg_index, variante_courante,
          un_ami_present);

    /* AUSSI DANS LE JOURNAL DE FIN DE ROUND -- 16/09/2026 : `decor-objets.log` s'arrete au
       premier etage. Chez Oro, la variante 2 n'a pas de chien (c'est 2I), et il faut pouvoir
       dire laquelle est sortie. */
    TraceFin("   variante de decor %d (etage %d)\n", variante_courante, bg_index, 0);
    TraceFin("   combattants %d et %d, ami du decor %d\n", My_char[0], My_char[1],
             un_ami_present);
}

/// Cet objet existe-t-il dans la variante courante ?
static s32 dans_la_variante(const DecorAnimation* a) {
    s32 combat;

    /* Un objet sans masque -- il n'y en a plus, mais la garde ne coute rien -- est de
       toutes les variantes plutot que d'aucune. */
    if (a == NULL || a->variante == 0) {
        return 1;
    }

    if (!(a->variante & (1 << variante_courante))) {
        return 0;
    }

    /* L'AIRE EST LA MANCHE, et elle ne se tire pas -- voir `DecorAnimation::aires`.
       `Bg_Aire_Suivante` refait `effect_05_init` a chaque manche, donc le filtre suffit :
       les objets de la manche precedente ne renaissent pas. */
    if (a->aires != 0 && !(a->aires & (1 << aire_objets))) {
        return 0;
    }

    combat = a->variante & 0x30;
    return combat == 0 || (combat & (un_ami_present ? 0x20 : 0x10)) != 0;
}

void DecorObjets_MancheSuivante(void) {
    if (aire_objets < 2) {
        aire_objets++;
    }
}

s32 DecorObjets_ChangeParAire(s32 bg_index) {
    short premier;
    s32 n;
    s32 i;

    if (bg_index < 0 || bg_index >= 58) {
        return 0;
    }

    premier = decor_anim_par_etage[bg_index];
    n = decor_nb_par_etage[bg_index];

    if (premier < 0) {
        return 0;
    }

    for (i = 0; i < n; i++) {
        if (decor_animations[premier + i].aires != 0) {
            return 1;
        }
    }

    return 0;
}

s32 DecorObjets_Combien(s32 bg_index) {
    /* `short`, PAS `signed char`. Avec les dix-neuf etages de New Generation il y a 188
       fiches, et l'index de la premiere depasse 127 des l'etage 46 : un `signed char` le
       repliait en negatif, et `premier < 0` rendait 0 -- les objets disparaissaient sans
       rien signaler. */
    short premier;
    s32 n;
    s32 i;

    /* Et la borne suit le tableau, qui fait 58 entrees : 22 a 36 pour 2nd Impact, 37 a 55
       pour New Generation, 56 et 57 pour les deux bandes de 2I restees de cote. Laissee a
       37, elle rejetait tout New Generation. */
    if (bg_index < 0 || bg_index >= 58 || !objets_permis()) {
        return 0;
    }

    premier = decor_anim_par_etage[bg_index];

    if (premier < 0) {
        return 0;
    }

    tirer_la_variante(bg_index);

    /* ON COMPTE CEUX DE LA VARIANTE, pas ceux de l'etage. Le tableau les porte tous --
       les quatre variantes d'Oro y sont ecrites -- et c'est ici qu'on choisit. */
    n = 0;

    for (i = 0; i < decor_nb_par_etage[bg_index]; i++) {
        if (premier + i >= decor_nb_animations) {
            break;
        }

        if (dans_la_variante(&decor_animations[premier + i])) {
            n++;
        }
    }

    if (n > OBJETS_MAX) {
        n = OBJETS_MAX;
    }

    return n;
}

const DecorAnimation* DecorObjets_Animation(s32 bg_index, s32 rang) {
    /* `short`, comme dans `DecorObjets_Combien`. J'avais corrige la-bas et OUBLIE ici :
       `decor_anim_par_etage[46]` vaut 129, un `signed char` le repliait a -127, et
       `&decor_animations[-127 + rang]` lisait AVANT le tableau. Les etages 46 et au-dela
       en dependent. */
    short premier;
    s32 reste = rang;
    s32 i;

    if (rang < 0 || rang >= DecorObjets_Combien(bg_index)) {
        return NULL;
    }

    premier = decor_anim_par_etage[bg_index];

    /* LE RANG COMPTE DANS LA VARIANTE, PAS DANS L'ETAGE. `DecorObjets_Combien` n'a
       renvoye que les objets de la variante courante ; il faut donc sauter les autres
       ici, sans quoi le rang designerait un objet d'une variante qu'on ne montre pas. */
    for (i = 0; i < decor_nb_par_etage[bg_index]; i++) {
        if (premier + i >= decor_nb_animations) {
            break;
        }

        if (!dans_la_variante(&decor_animations[premier + i])) {
            continue;
        }

        if (reste == 0) {
            return &decor_animations[premier + i];
        }

        reste--;
    }

    return NULL;
}

/// Le rang de cet objet parmi les notres, ou -1.
static s32 rang_de(const void* work) {
    s32 k;

    if (work == NULL) {
        return -1;
    }

    for (k = 0; k < nb_objets; k++) {
        if (nos[k].work == work && nos[k].anim != NULL && nos[k].trans.count != 0) {
            return k;
        }
    }

    return -1;
}

/* LES OBJETS A COMPORTEMENT -- 16/09/2026.
 *
 * Un script ne dit pas tout : c'est la ROUTINE de l'objet qui choisit quel script jouer,
 * d'ou il part, et ou l'objet se trouve. Chaque comportement est une petite machine a
 * etats, lue dans le code de 2I :
 *
 *   1 chien debout d'Oro (`0x8C03331C`)
 *       0 regarde son prefere -- script 28 tenu, entre a 0, 2 ou 4
 *       1 remue la queue, un ami juste devant lui -- script 30
 *       2 aboie sur un coup special -- script 29
 *   2 chien couche (`0x8C03360C`)
 *       0 repos, le script 40 qui boucle de lui-meme
 *       1 se redresse sur un coup special -- script 41
 *   3 poisson rouge de Yang (`0x8C02AF90`), un va-et-vient entre x 160 et 240
 *   4 poisson noir (`0x8C02B0C8`), le tour de l'aquarium en neuf etats
 *
 * Les pas de toutes les suites sont bout a bout dans `pas` ; `suites` dit ou chacune
 * commence. L'etat n'avance que dans `DecorObjets_Avancer` : l'image reste donc la meme
 * pendant tout le dessin, comme le cache l'exige. Chaque morceau d'un objet decoupe
 * conduit sa propre copie de la machine ; elles recoivent les memes entrees a la meme
 * trame, et restent donc ensemble.
 *
 * Tout est gele pendant une pause, comme les objets de decor de 3S (`effect_07_move`) --
 * 2I teste pour cela `u8[0x8C6A27D4]`. */
#define CHIEN_DEBOUT 1
#define CHIEN_COUCHE 2
#define POISSON_ROUGE 3
#define POISSON_NOIR 4

/* Lus dans le code du chien : sa position (`0x8C033776`, 0x260), la distance d'un ami qui
   le fait remuer la queue (`0x8C0335D4`, 32), et la tenue d'un regard -- le script 28
   tient dix trames avant de marquer sa fin, et la routine n'en change pas avant. */
#define CHIEN_X 608
#define CHIEN_PRES 32
#define CHIEN_TENUE 10

/* Les deux poissons naissent aux positions du bloc `0x8C17E4AC`. */
#define ROUGE_X 240
#define ROUGE_Y 136
#define NOIR_X 128
#define NOIR_Y 148

/* Une vitesse de 2I, en 16.16 : `mov.w #0xA000` s'etend en -0x6000, -0,375 pixel par
   trame. Les accelerations des deux poissons sont toutes nulles. */
#define PIXEL(v) ((s32)(v) << 16)

/* LE TRAJET, comportement 5 -- 18/09/2026.
 *
 * Plusieurs objets de New Generation ne jouent pas seulement un script : leur routine les
 * DEPLACE, par segments de vitesse constante, et revient au depart. Ils n'ont pas besoin
 * d'une machine a etats ecrite en C -- une table suffit :
 *
 *     trajet = { duree, vx, vy, suite, z, ... } et la liste boucle sur son premier
 *     segment, ou l'objet retrouve sa position de naissance.
 *
 * `vx` et `vy` sont en 1/256 de pixel par trame. `suite` vaut -1 quand le segment ne change
 * pas l'animation (l'objet garde le script que ses durees font tourner).
 *
 * ET `z` EST LA PROFONDEUR DU SEGMENT -- 25/09/2026. Frederic, sur l'oiseau d'Elena 1 :
 * « *sur certaines frames il doit etre derriere le ponton* ». Sa routine `0x8C0A63F0`
 * ECRIT `[+556]` en cours de vol, a deux endroits lus dans le binaire :
 *
 *     0x8C0A64D4   mov #79   ->  DERRIERE le ponton, qui est a 78
 *     0x8C0A66DA   mov #10   ->  devant tout, et `[+88]` = 10 avec
 *
 * Une fiche n'avait qu'UN `z`, pose a la naissance par `effect_05_init`. Le segment en
 * porte un maintenant : **zero garde celui de la fiche**, et les objets qui ne s'en
 * servent pas ne changent pas d'un pixel.
 *
 *   * la caleche de Dudley 1 (id 65, `0x8C0A8970`) : elle attend 600 trames sous le tunnel,
 *     part a -1,125 pixel pendant 196 trames, puis a -1 pixel jusqu'a sortir, et revient ;
 *   * l'eau de la riviere d'Elena 1 (id 45, `0x8C0A4D34`) : elle glisse d'un demi-pixel par
 *     trame et revient a sa place toutes les 33 trames, quand son script avance d'une image.
 */
#define TRAJET 5

/// Les champs d'un segment de trajet : duree, vx, vy, suite, z.
#define TRAJET_CHAMPS 5

/// `reste_trajet` quand un trajet qui ne boucle pas a joue son dernier segment.
#define TRAJET_FINI (-1)

/* SUR_COMBATTANT, comportement 6 -- 23/09/2026.
 *
 * L'id 85 de New Generation ne joue pas une animation : il se POSE par rapport a un
 * combattant. Sa routine `0x8C0AB52C` (table des acteurs `0x8C1AD9F8 + 85*4`) a un etat,
 * `0x8C0AB6A8`, qui fait exactement ceci :
 *
 *     r3 = objet[+812] ; @r15 = r3          la RACINE de la chaine de creation
 *     jsr 0x8C03324C(objet, table 0, script 2)   il pose son script
 *     objet[+1] = 1                         disp_flag : il apparait
 *     r2 = @r15 ; r2 = racine[+818]         LE NUMERO DU COMBATTANT
 *     muls.w 984, r2                        * sizeof(plw)
 *     r2 = u16[0x8C543F2E + cote*984]       son X -- 0x8C543F2E = plw + 102 = xyz[0].pos
 *     add #-64                              soixante-quatre unites a sa gauche
 *
 * `objet[+812]` est la fiche du combattant dont l'objet descend, et `+818` son numero :
 * un combattant recoit `WORK[+812] = 0x8C551F28 + n*886` a son initialisation
 * (`0x8C08326C`, appele en `0x8C015CCA`), et ses enfants heritent le champ de generation
 * en generation.
 *
 * NOUS N'AVONS PAS CETTE CHAINE. Le port cree ses objets depuis une fiche, pas depuis un
 * combattant : `+812` n'existe pas ici, et le cote n'est donc pas lisible. **On prend le
 * joueur 1.** C'est le seul point de ce comportement qui ne soit pas lu dans le binaire,
 * et c'est la ligne `SUR_COMBATTANT_COTE` qui changera le jour ou la chaine sera portee.
 *
 * L'objet n'a ni `pas` ni `suites` : son script n'a qu'une image. Seule sa POSITION bouge.
 */
#define SUR_COMBATTANT 6
#define SUR_COMBATTANT_COTE 0
#define SUR_COMBATTANT_ECART 64

/* REGARD, comportement 7 -- 23/09/2026.
 *
 * Frederic : « dans le decor de Gill 2I, l'acolyte du milieu suit clairement du regard
 * l'un des deux ou les deux combattants ». Il a raison, et le mecanisme est en clair dans
 * l'id 184 de 2nd Impact (`0x8C04AA54`), la routine des quatre acolytes -- c'est elle que
 * la routine d'etage de Gill appelle en `0x8C0DBA78` pour le bloc `0x8C183DC8` :
 *
 *     8C04ACC4  r0 = objet[+54]                 le cote
 *     8C04ACC6  muls.w 1036,r0                  * sizeof(plw)
 *     8C04ACCC  r4 = u16[plw + 102 + cote*1036] LE X DU COMBATTANT
 *     8C04ACCE  shad #-6,r4                     >> 6, soit par tranches de 64 pixels
 *     8C04ACD0  and #15,r4                      seize tranches
 *     8C04ACD8  r0 = u16[0x8C183DA8 + r4*2]     LA TABLE DES ORIENTATIONS
 *
 * La table a seize entrees, et elle est posee **juste avant les enregistrements des
 * acolytes** (`0x8C183DA8` + 32 octets = `0x8C183DC8`) -- la meilleure preuve qu'elle leur
 * appartient :
 *
 *     0 0 0 0 0 0 1 1 2 2 3 3 4 4 5 5
 *
 * Six orientations : la tete reste de face tant que le combattant est dans le tiers
 * gauche, puis tourne d'un cran tous les 128 pixels. Ce n'est PAS une animation -- c'est
 * pourquoi le port les figeait sur l'image 0, et pourquoi le commentaire de `boucle`
 * disait que « rien ici ne sait faire » ce choix. Maintenant si.
 *
 * LE COTE, lui, vient de `objet[+54]`, que cette routine n'ecrit pas : il est pose
 * ailleurs dans la chaine de creation, que le port n'a pas. **On prend le joueur 1**,
 * comme pour SUR_COMBATTANT, et c'est `REGARD_COTE` qui changera.
 */
#define REGARD 7
#define REGARD_COTE 0
static const unsigned char REGARD_TABLE[16] = { 0, 0, 0, 0, 0, 0, 1, 1,
                                                2, 2, 3, 3, 4, 4, 5, 5 };

/* REACTIF, comportement 8 -- 23/09/2026.
 *
 * L'id 87 de New Generation (`0x8C0ABC24`, dix objets sur les bandes 2, 5, 10, 15 et 17)
 * ne se montre pas tout le temps : il attend que sa cible FASSE quelque chose.
 *
 * Sa routine dispatche d'abord sur l'etat de la RACINE de sa chaine (`objet[+812]`,
 * `routine_no[0]`) : 0 ne fait rien, 2 le detruit, et 1 seulement le laisse vivre. Elle
 * verifie ensuite le gel de trame (`0x8C545260`) et `0x8C54527A`, puis saute dans sa
 * propre table d'etats (`0x8C4DEA3C`, indexee par `objet[+38]`). L'etat qui compte est
 * `0x8C0ABCA6` :
 *
 *     8C0ABCB0  mov.l @(12,r14),r5      r5 = objet[+12], SA CIBLE
 *     8C0ABCB2  mov #38,r0
 *     8C0ABCB4  mov.w @(r0,r5),r3       r3 = cible->routine_no[1] : SON ETAT
 *     8C0ABCB8  cmp/gt r2,r3            etat > 2 ?
 *     8C0ABCBA  bf 0x8C0ABD40           sinon, rien
 *     ...                               sinon : compteur++, disp_flag = 1, un script pose
 *
 * `disp_flag` est le `+1` d'un `WORK` : l'objet n'est PAS DESSINE tant qu'il est nul, et
 * le spawner ne l'ecrit pas. L'objet nait donc invisible et n'apparait que lorsque l'etat
 * du combattant depasse 2 -- c'est-a-dire quand il ne se tient plus simplement debout.
 *
 * COMMENT ON LE REND ICI. Le port ne peut pas retirer un objet de sa liste : son RANG
 * entre dans la cle du cache de motifs, dans l'emplacement de sa palette et dans son ordre
 * de dessin, et tout glisserait. Mais il n'a pas besoin de le retirer -- il suffit de ne
 * rien dessiner : `DecorObjets_Tuile` rend `tuile_vide` sous `CLE_VIDE`, l'entree de cache
 * partagee qui existe deja pour les cases vides. Le rang ne bouge pas, le cache ne gonfle
 * pas, et l'objet disparait.
 *
 * LE COTE, comme partout, n'est pas lu : la cible vient de la chaine de creation que le
 * port n'a pas. On prend le joueur 1 (`REACTIF_COTE`).
 */
#define REACTIF 8

/// Il se brise sous la chute d'un combattant -- voir le pave RUPTURE plus bas.
#define RUPTURE 9
#define REACTIF_COTE 0
#define REACTIF_ETAT 2

/* L'INTERRUPTEUR, ET POURQUOI IL EST FERME PAR DEFAUT.
 *
 * La lecture dit que ces onze objets naissent INVISIBLES. Si elle est juste, les allumer
 * est fidele ; si elle est fausse d'un etat, onze sprites disparaissent de cinq decors que
 * Frederic a valides. Le defaut garde donc le comportement d'avant -- ils restent
 * visibles -- et `SF3_DECOR_REACTIF=1` donne la version lue, pour comparer.
 *
 * C'est lui qui juge sur l'image ; moi je lui donne les deux. */
static s32 reactif_permis(void) {
    static s32 lu = 0;
    static s32 permis = 0;

    if (!lu) {
        const char* v = getenv("SF3_DECOR_REACTIF");

        lu = 1;
        permis = (v != NULL && v[0] == '1');
        trace("sprites reactifs : %d %d %d\n", permis, 0, 0);
    }

    return permis;
}

/// L'objet a-t-il un comportement, et ses tables ?
static s32 conduit(const DecorAnimation* a) {
    if (a == NULL || a->comportement == 0 || a->nb_images <= 0) {
        return 0;
    }

    if (a->comportement == TRAJET) {
        return a->trajet != NULL;
    }

    /* Un objet pose sur un combattant n'a pas de suites : sa routine ne choisit pas
       d'image, elle le DEPLACE. */
    if (a->comportement == SUR_COMBATTANT || a->comportement == REGARD
        || a->comportement == REACTIF || a->comportement == RUPTURE) {
        return 1;
    }

    return a->pas != NULL && a->suites != NULL && a->nb_suites > 0;
}

static s32 debut_suite(const DecorAnimation* a, s32 s) {
    return (s >= 0 && s < a->nb_suites) ? a->suites[s] : 0;
}

static s32 fin_suite(const DecorAnimation* a, s32 s) {
    return (s >= 0 && s < a->nb_suites) ? a->suites[s + 1] : 0;
}

static void jouer(s32 k, s32 s) {
    nos[k].suite = s;
    nos[k].pas = 0;
    nos[k].finie = 0;
    nos[k].reste = nos[k].anim->pas[2 * debut_suite(nos[k].anim, s) + 1];
}

/// Un pas de la suite en cours ; `boucle` la fait repartir apres son dernier pas.
///
/// Le dernier pas d'une suite qui finit est l'image MARQUEE du script, ou celle d'avant
/// quand la routine change d'etat dans la trame meme (le generateur en decide). `finie`
/// tombe quand sa duree est ecoulee, et la machine enchaine a la meme trame.
static void derouler(s32 k, s32 boucle) {
    const DecorAnimation* a = nos[k].anim;
    const s32 debut = debut_suite(a, nos[k].suite);
    const s32 nb = fin_suite(a, nos[k].suite) - debut;

    if (nos[k].finie || --nos[k].reste > 0) {
        return;
    }

    if (nos[k].pas + 1 < nb) {
        nos[k].pas++;
    } else if (boucle) {
        nos[k].pas = 0;
    } else {
        nos[k].finie = 1;
        return;
    }

    nos[k].reste = a->pas[2 * (debut + nos[k].pas) + 1];
}

/// `0x8C0D7EFC` : un combattant lance-t-il un coup special ?
///
/// `routine_no[1] == 4` est l'attaque (`plmain_lv_02` : normal, degats, saisie, saisi,
/// attaque) et un `routine_no[2]` de 16 ou plus part dans la table des coups speciaux
/// (`plpat.c`).
static s32 coup_special(void) {
    s32 i;

    for (i = 0; i < 2; i++) {
        if (plw[i].wu.routine_no[1] == 4 && plw[i].wu.routine_no[2] >= 16) {
            return 1;
        }
    }

    return 0;
}

/// `0x8C03334A` : ou regarde le chien debout -- 0 a gauche, 1 de face, 2 a droite.
///
/// Il suit le combattant de plus grande humeur (Oro avant Ibuki et Elena). A egalite, la
/// camera, `bgw[1].xy[0].disp.pos`, qui vaut 512 au debut d'un round.
static s32 regard_du_chien(s32 bg_index) {
    const s32 h0 = humeur_du_decor(bg_index, My_char[0]);
    const s32 h1 = humeur_du_decor(bg_index, My_char[1]);
    s32 x;

    if (h0 == h1) {
        x = bg_w.bgw[1].xy[0].disp.pos;
        return x < 544 ? 0 : (x < 624 ? 1 : 2);
    }

    x = plw[h0 > h1 ? 0 : 1].wu.position_x;
    return x < 448 ? 0 : (x < 624 ? 1 : 2);
}

/// `0x8C033572` : un ami se tient-il a moins de 32 pixels du chien ?
static s32 ami_devant(s32 bg_index) {
    s32 i;

    for (i = 0; i < 2; i++) {
        s32 ecart = CHIEN_X - plw[i].wu.position_x;

        if (ecart < 0) {
            ecart = -ecart;
        }

        if (humeur_du_decor(bg_index, My_char[i]) != 0 && ecart < CHIEN_PRES) {
            return 1;
        }
    }

    return 0;
}

static void regarder(s32 k) {
    nos[k].etat = 0;
    nos[k].suite = 0;
    nos[k].pas = 0;
    nos[k].finie = 0;
    nos[k].tenue = 0;
    nos[k].regard = regard_du_chien(nos[k].anim->etage);
}

static void chien_debout(s32 k) {
    const s32 bg = nos[k].anim->etage;
    s32 r;

    switch (nos[k].etat) {
    case 0:
        /* Pendant la tenue, la routine ne regarde rien d'autre. */
        if (nos[k].tenue > 0) {
            nos[k].tenue--;
            return;
        }

        r = regard_du_chien(bg);

        if (r != nos[k].regard) {
            nos[k].regard = r;
            nos[k].tenue = CHIEN_TENUE;
        } else if (coup_special()) {
            nos[k].etat = 2;
            jouer(k, 2);
        } else if (r == 1 && ami_devant(bg)) {
            nos[k].etat = 1;
            jouer(k, 1);
        }

        return;

    case 1:
        if (coup_special()) {
            nos[k].etat = 2;
            jouer(k, 2);
            return;
        }

        derouler(k, 0);

        if (nos[k].finie) {
            regarder(k);
        }

        return;

    case 2:
        derouler(k, 0);

        if (nos[k].finie) {
            regarder(k);
        }

        return;

    default:
        regarder(k);
        return;
    }
}

static void chien_couche(s32 k) {
    if (nos[k].etat == 1) {
        derouler(k, 0);

        if (nos[k].finie) {
            nos[k].etat = 0;
            jouer(k, 0);
        }
    } else if (nos[k].etat != 0) {
        nos[k].etat = 0;
        jouer(k, 0);
    } else if (coup_special()) {
        nos[k].etat = 1;
        jouer(k, 1);
    } else {
        derouler(k, 1);
    }
}

/// `+102 = x`, en gardant la fraction : 2I n'ecrit que le mot haut (`mov.w r4,@(102,...)`).
static s32 borne(s32 v, s32 pixels) {
    return PIXEL(pixels) | (v & 0xFFFF);
}

/// Le poisson rouge -- etat `+38` de `0x8C02AF90`. Suites : 82 nage a gauche, 83 demi-tour,
/// 84 nage a droite, 85 demi-tour.
static void poisson_rouge(s32 k) {
    switch (nos[k].etat) {
    case 1:
        derouler(k, 1);
        nos[k].px += nos[k].vx;

        if ((nos[k].px >> 16) < 160) {
            nos[k].px = borne(nos[k].px, 160);
            nos[k].etat = 2;
            jouer(k, 1);
        }

        return;

    case 2:
        derouler(k, 0);

        if (nos[k].finie) {
            nos[k].etat = 3;
            nos[k].vx = 0x6000;
            jouer(k, 2);
        }

        return;

    case 3:
        derouler(k, 1);
        nos[k].px += nos[k].vx;

        if ((nos[k].px >> 16) > 240) {
            nos[k].px = borne(nos[k].px, 240);
            nos[k].etat = 4;
            jouer(k, 3);
        }

        return;

    case 4:
        derouler(k, 0);

        if (nos[k].finie) {
            nos[k].etat = 1;
            nos[k].vx = -0x6000;
            jouer(k, 0);
        }

        return;

    default:
        nos[k].bouge = 1;
        nos[k].px = PIXEL(ROUGE_X);
        nos[k].py = PIXEL(ROUGE_Y);
        nos[k].vx = -0x6000;
        nos[k].vy = 0;
        nos[k].etat = 1;
        jouer(k, 0);
        return;
    }
}

/// Le poisson noir -- etat `+40` de `0x8C02B0C8`. Suites : 86 nage en haut, 87 tourne,
/// 88 plonge, 89 se retourne, 90 file au fond, 91 tourne, 92 remonte. Le script avance EN
/// TETE de chaque trame, avant l'etat.
static void poisson_noir(s32 k) {
    if (nos[k].etat < 0) {
        nos[k].bouge = 1;
        nos[k].px = PIXEL(NOIR_X);
        nos[k].py = PIXEL(NOIR_Y);
        nos[k].vy = 0;
        nos[k].etat = 0;
        jouer(k, 0);
    } else {
        derouler(k, nos[k].suite == 0 || nos[k].suite == 2 || nos[k].suite == 4 ||
                        nos[k].suite == 6);
    }

    switch (nos[k].etat) {
    case 0:
        /* L'etat 0 pose le script et la vitesse, puis tombe dans l'etat 1. */
        nos[k].vx = 0x4000;
        nos[k].etat = 1;
        /* FALLTHROUGH */

    case 1:
        nos[k].px += nos[k].vx;

        if ((nos[k].px >> 16) > 256) {
            nos[k].px = borne(nos[k].px, 256);
            nos[k].vx = -0x4000;
            nos[k].etat = 2;
        }

        return;

    case 2:
        nos[k].px += nos[k].vx;

        if ((nos[k].px >> 16) < 128) {
            nos[k].px = borne(nos[k].px, 128);
            nos[k].vx = 0x4000;
            nos[k].etat = 3;
        }

        return;

    case 3:
        nos[k].px += nos[k].vx;

        if ((nos[k].px >> 16) > 256) {
            nos[k].px = borne(nos[k].px, 256);
            nos[k].etat = 4;
            jouer(k, 1);
        }

        return;

    case 4:
        if (nos[k].finie) {
            nos[k].vx = -0x4000;
            nos[k].vy = -0x5000;
            nos[k].etat = 5;
            jouer(k, 2);
        }

        return;

    case 5:
        nos[k].px += nos[k].vx;
        nos[k].py += nos[k].vy;

        if ((nos[k].py >> 16) < 112) {
            nos[k].py = borne(nos[k].py, 112);
            nos[k].etat = 6;
            jouer(k, 3);
        }

        return;

    case 6:
        if (nos[k].finie) {
            nos[k].vx = -0x4000;
            nos[k].etat = 7;
            jouer(k, 4);
        }

        return;

    case 7:
        nos[k].px += nos[k].vx;

        if ((nos[k].px >> 16) < 160) {
            nos[k].px = borne(nos[k].px, 160);
            nos[k].etat = 8;
            jouer(k, 5);
        }

        return;

    case 8:
        if (nos[k].finie) {
            nos[k].vx = -0x4000;
            nos[k].vy = 0x8000;
            nos[k].etat = 9;
            jouer(k, 6);
        }

        return;

    case 9:
        nos[k].px += nos[k].vx;
        nos[k].py += nos[k].vy;

        if ((nos[k].py >> 16) > 151) {
            nos[k].py = borne(nos[k].py, 151);
            nos[k].vx = 0x4000;
            nos[k].etat = 1;
            jouer(k, 0);
        }

        return;

    default:
        return;
    }
}

/// Le segment courant du trajet : `{ duree, vx, vy, suite, z }`.
static const short* trajet_segment(s32 k) {
    return nos[k].anim->trajet + TRAJET_CHAMPS * nos[k].suite_trajet;
}

/// @brief Pose la profondeur d'un segment, ou ne fait rien si le segment n'en porte pas.
///
/// `mlt_obj_matrix` prend la matrice de `my_family` mais la profondeur de `position_z` ;
/// `my_priority` la suit, comme a la naissance dans `effect_05_init`. Zero veut dire
/// « garde celle de la fiche », ce que fait deja le champ `z` de l'animation.
static void profondeur_du_segment(s32 k, s32 z) {
    WORK* w;

    if (z == 0 || nos[k].work == NULL) {
        return;
    }

    w = (WORK*)nos[k].work;
    w->my_priority = w->position_z = (s16)z;
}

/// @brief Efface l'objet, comme `objet[+1] = 0` sur la Dreamcast.
///
/// `effect_05_move` pose `disp_flag` a 1 a la naissance et le moteur ne dessine rien tant
/// qu'il est nul. C'est le seul geste de l'etat 3 de l'oiseau d'Elena 1.
static void eteindre(s32 k) {
    if (nos[k].work != NULL) {
        ((WORK*)nos[k].work)->disp_flag = 0;
    }
}

/// Une trame d'un objet a trajet -- voir `TRAJET`.
static void trajet(s32 k) {
    const DecorAnimation* a = nos[k].anim;
    const short* seg;

    if (nos[k].etat < 0) {
        nos[k].etat = 0;
        nos[k].bouge = 1;
        nos[k].px = 0;
        nos[k].py = 0;
        nos[k].suite_trajet = 0;
        nos[k].reste_trajet = a->trajet[0];
        profondeur_du_segment(k, a->trajet[4]);

        if (a->pas != NULL && a->trajet[3] >= 0) {
            jouer(k, a->trajet[3]);
        }

        return;
    }

    /* FINI : l'objet est efface et ne bouge plus -- ni son script, ni sa position. */
    if (nos[k].reste_trajet == TRAJET_FINI) {
        return;
    }

    if (a->pas != NULL) {
        derouler(k, 1);
    }

    seg = trajet_segment(k);
    nos[k].px += (s32)seg[1] << 8;
    nos[k].py += (s32)seg[2] << 8;

    if (--nos[k].reste_trajet > 0) {
        return;
    }

    nos[k].suite_trajet++;

    if (nos[k].suite_trajet >= a->nb_trajet) {
        /* UN TRAJET QUI NE BOUCLE PAS S'ETEINT -- voir `DecorAnimation::trajet_fin`.
           L'oiseau d'Elena 1 disparait au bout de son envol (`0x8C0A6526`, `objet[+1] = 0`)
           et ne revient pas : on retient le dernier segment et on efface l'objet. */
        if (a->trajet_fin) {
            nos[k].reste_trajet = TRAJET_FINI;
            eteindre(k);
            return;
        }

        /* La boucle repasse par le depart : c'est la remise a zero que font les routines
           (la caleche revient sous le tunnel, l'eau revient a sa place). */
        nos[k].suite_trajet = 0;
        nos[k].px = 0;
        nos[k].py = 0;
    }

    seg = trajet_segment(k);
    nos[k].reste_trajet = seg[0];
    profondeur_du_segment(k, seg[4]);

    if (a->pas != NULL && seg[3] >= 0) {
        jouer(k, seg[3]);
    }
}

/// Une trame d'un objet pose sur un combattant -- voir `SUR_COMBATTANT`.
static void sur_combattant(s32 k) {
    const s32 vise = plw[SUR_COMBATTANT_COTE].wu.xyz[0].disp.pos - SUR_COMBATTANT_ECART;

    if (nos[k].etat < 0) {
        nos[k].etat = 0;
        nos[k].bouge = 1;
        nos[k].py = 0;

        if (nos[k].anim->pas != NULL) {
            jouer(k, 0);
        }
    }

    /* `px` compte en ECART depuis la fiche, comme un trajet. */
    nos[k].px = (vise - nos[k].anim->x) << 16;
}

/// Une trame d'un acolyte qui suit un combattant du regard -- voir `REGARD`.
static void regard_combattant(s32 k) {
    const s32 x = plw[REGARD_COTE].wu.xyz[0].disp.pos;

    nos[k].etat = 0;
    nos[k].regard = REGARD_TABLE[(x >> 6) & 15];
}

/* RUPTURE, comportement 9 -- 23/09/2026, sur une phrase de Frederic : « dans le decor
 * d'Hugo, le tonneau a l'extremite droite du decor se brise ».
 *
 * L'objet le plus a droite de `bg06` est charge en dur par `0x8C031B56`, dans la routine de
 * l'id 63 (`0x8C031918`), qui a SEPT etats. Son etat 1 appelle `0x8C0D7D74` et, des que
 * celui-ci rend autre chose que zero, pose le script de rupture :
 *
 *     8C0319EC  jsr 0x8C0D7D74
 *     8C0319F2  bf 0x8c0319f8         r0 != 0 -> on casse
 *     8C031A00  mov #32,r6 ; jsr 0x8C0B4AD4
 *
 * `0x8C0D7D74` est une AIDE PARTAGEE, posee dans la region des etages -- hors de
 * l'intervalle de tout acteur, ce qui est la raison pour laquelle cinq criblages successifs
 * l'ont manquee. Elle appelle `0x8C0D7DFC` pour chaque combattant, et la voila en clair :
 *
 *     8C0D7E08  r0 = plw[+38]          routine_no[1], l'etat
 *     8C0D7E0A  cmp/eq #1,r0           etat 1
 *     8C0D7E10  r4 = plw[+40]          routine_no[2], le sous-etat
 *     8C0D7E14  cmp/ge #14,r4
 *     8C0D7E1A  cmp/ge #24,r4          14 <= sous-etat < 24 : LA CHUTE
 *     8C0D7E22  r7 = 0x8C1D3ED4 + objet[+4]*8     la boite de l'OBJET
 *     8C0D7E2E  r6 = 0x8C1D3F2C + plw[+856]*8     la boite du PERSONNAGE
 *     8C0D7E3C  jsr 0x8C0B9ED0                    le recouvrement
 *
 * Le recouvrement (`0x8C0B9ED0`) retourne le x de chaque boite selon `rl_flag` (+10), lui
 * ajoute le `+102`/`+106` de son `WORK`, et compare les deux rectangles.
 *
 * CE QUE LE PORT EN FAIT. Deux suites : la 0 est l'objet intact, qui tourne en boucle ; la 1
 * est la rupture, qui **se joue UNE FOIS et tient sa derniere image** -- Frederic :
 * « la destruction ne se joue pas en boucle, mais une seule fois, avec la derniere image de
 * l'animation persistante ». C'est exactement ce que fait le Dreamcast, dont l'etat 2
 * deroule le script jusqu'a un drapeau puis s'arrete.
 *
 * ON NE PORTE PAS LA SECONDE RUPTURE. Le tonneau en a deux -- un compteur a 2 fait poser le
 * script 34 -- et l'etat 0 choisit meme son script de depart selon ce compteur, qui survit
 * a la manche : intact (31), fele (33) ou detruit (30). Le port pose toujours l'objet
 * intact, et une seule rupture. C'est ce qui se voit ; le reste demande un etat de partie
 * que le port n'a pas.
 */
/// L'etat de chute d'un combattant : `routine_no[1] == 1` et `14 <= routine_no[2] < 24`.
#define CHUTE_ETAT 1
#define CHUTE_MIN 14
#define CHUTE_MAX 24

/* LES BOITES DES PERSONNAGES, `0x8C1D3F2C` en 2nd Impact et `0x8C189108` en New Generation
   -- MEMES VALEURS des deux cotes. Quatre `s16` chacune : `{ x, largeur, y, hauteur }`
   depuis la position du combattant, le x retourne par `rl_flag`.
 *
 * LA TABLE DU DREAMCAST N'EN A QUE SEIZE, et c'est normal : 2nd Impact s'arrete a Chun-Li.
 * 3rd Strike en ajoute QUATRE -- Makoto, Q, Twelve, Remy -- qui n'existaient pas quand ces
 * boites ont ete ecrites. Les quatre derniers ont donc la boite la plus repandue de la
 * table (`-13, 47, 50, 38`, celle de Ryu, Hugo, Elena, Ken, Sean, Akuma et Chun-Li), faute
 * d'une valeur lue.
 *
 * C'ETAIT UN VRAI TROU : la version precedente s'arretait a seize et SAUTAIT LE TEST pour
 * les quatre autres. Joue avec Makoto, Q, Twelve ou Remy, rien ne pouvait se briser --
 * Frederic, sur Yang : « je n'ai pu rien detruire ». */
#define PERSO_MAX 20

static const short BOITE_PERSO[PERSO_MAX][4] = {
    { -11, 56, 33, 38 }, { -11, 56, 35, 53 }, { -13, 47, 50, 38 }, { -18, 42, 36, 32 },
    { -24, 48, 40, 48 }, { -21, 48, 37, 42 }, { -13, 47, 50, 38 }, { -22, 38, 36, 36 },
    { -13, 47, 50, 38 }, { -28, 50, 28, 34 }, { -18, 42, 36, 32 }, { -13, 47, 50, 38 },
    { -13, 47, 50, 38 }, { -11, 56, 33, 38 }, { -13, 47, 50, 38 }, { -13, 47, 50, 38 },
    /* Makoto, Q, Twelve, Remy : absents de 2nd Impact, la boite la plus repandue. */
    { -13, 47, 50, 38 }, { -13, 47, 50, 38 }, { -13, 47, 50, 38 }, { -13, 47, 50, 38 },
};

/// `0x8C0B9ED0` : les deux rectangles se recouvrent-ils ?
static s32 boites_se_touchent(const short* a, s32 ax, s32 ay, s32 miroir,
                              const s32* b) {
    const s32 a0 = ax + (miroir ? -a[0] - a[1] : a[0]);
    const s32 a1 = a0 + a[1];
    const s32 a2 = ay + a[2];
    const s32 a3 = a2 + a[3];

    return !(a1 <= b[0] || b[0] + b[1] <= a0 || a3 <= b[2] || b[2] + b[3] <= a2);
}

/* CE QUE LE JOURNAL DIT DES CHUTES -- borne, sinon il noierait tout.
 *
 * Frederic, sur Yang : « je n'ai pu rien detruire ». La table des personnages etait courte
 * de quatre -- c'est corrige -- mais si ca ne suffit pas, il faut pouvoir le VOIR sans
 * relire le binaire. On journalise donc la boite de chaque objet cassable une fois, et les
 * trente premieres chutes avec les deux rectangles : le premier coup d'oeil dira si
 * l'objet est hors de portee, ou si c'est le contact qui ne se declare pas. */
#define CHUTES_DITES 30

static s32 chutes_dites = 0;

/// `0x8C0D7DFC` : un combattant tombe-t-il SUR cet objet ?
static s32 chute_sur(s32 k) {
    const DecorAnimation* a = nos[k].anim;
    s32 i;

    if (a->boite[1] <= 0 || a->boite[3] <= 0) {
        return 0;
    }

    for (i = 0; i < 2; i++) {
        const s32 perso = My_char[i];
        s32 touche;

        if (plw[i].wu.routine_no[1] != CHUTE_ETAT) {
            continue;
        }

        if (plw[i].wu.routine_no[2] < CHUTE_MIN || plw[i].wu.routine_no[2] >= CHUTE_MAX) {
            continue;
        }

        if (perso < 0 || perso >= PERSO_MAX) {
            trace("chute : personnage %d hors de la table, rien ne peut se briser\n",
                  perso, 0, 0);
            continue;
        }

        touche = boites_se_touchent(BOITE_PERSO[perso], plw[i].wu.xyz[0].disp.pos,
                                    plw[i].wu.xyz[1].disp.pos, plw[i].wu.rl_flag, a->boite);

        if (chutes_dites < CHUTES_DITES) {
            const short* bp = BOITE_PERSO[perso];
            const s32 px = plw[i].wu.xyz[0].disp.pos;
            const s32 py = plw[i].wu.xyz[1].disp.pos;

            chutes_dites++;
            trace("chute perso %d en %d,%d  ->  objet %d\n", perso, px, py);
            trace("   sa boite  x %d..%d\n", px + bp[0], px + bp[0] + bp[1], 0);
            trace("   sa boite  y %d..%d\n", py + bp[2], py + bp[2] + bp[3], 0);
            trace("   l'objet   x %d..%d\n", a->boite[0], a->boite[0] + a->boite[1], 0);
            trace("   l'objet   y %d..%d  -> %d\n", a->boite[2], a->boite[2] + a->boite[3],
                  touche);
        }

        if (touche) {
            return 1;
        }
    }

    return 0;
}

/* LA MEMOIRE ENTRE LES MANCHES -- 23/09/2026.
 *
 * Le Dreamcast garde l'etat de chaque objet cassable dans `u16[0x8C6AF288 + type*2]`, et
 * l'etat 0 de sa routine choisit son script de depart dessus : le tonneau de Hugo repart
 * intact (31), fele (33) ou detruit (30). **Rien n'efface ce compteur entre deux manches.**
 * La seule remise a zero du binaire est `0x8C0D7E58` -- onze entrees a zero -- et elle n'est
 * appelee que depuis `0x8C0C1606`, une fonction de mise en place de PARTIE qui pose aussi
 * le mode de jeu. Un objet brise le reste donc jusqu'au combat suivant.
 *
 * COMMENT ON LE REND. Le port refait ses objets a chaque manche : `DecorObjets_Marquer`
 * repasse et `nos[k]` repart a zero. On garde donc le cran atteint dans un tableau a part,
 * indexe par le RANG de l'objet dans l'etage -- lequel ne bouge pas d'une manche a l'autre.
 *
 * QUAND L'EFFACER -- CORRIGE LE 24/09/2026. Frederic : « la statue de gauche reste brisee
 * meme en relancant un nouveau match ». Le test etait « la manche a-t-elle RECULE », et il
 * ne pouvait pas se declencher : `DecorObjets_Marquer` ne passe qu'a la MISE EN PLACE DE
 * L'ETAGE (`bg2202_init00` -> `effect_05_init`), donc toujours a la premiere manche, donc
 * toujours avec `Round_num` a zero. La valeur gardee valait zero elle aussi, `0 < 0` est
 * faux, et rien n'etait jamais efface.
 *
 * `Round_num` est remis a zero a l'entree d'un combat (`game.c`, trois sites) et monte a
 * chaque manche (`manage.c`, `Round_num++` avant `Quick_Entry`). Le voir A ZERO, c'est
 * donc etre a la PREMIERE manche d'un combat -- et nulle part ailleurs. C'est le meme
 * moment que `0x8C0C1606` du Dreamcast, et ca vaut que les objets renaissent a chaque
 * manche ou une seule fois par combat.
 */
static s32 degat[OBJETS_MAX];
static s32 degat_etage = -1;

static void memoire_des_degats(s32 bg_index) {
    if (bg_index != degat_etage || Round_num == 0) {
        s32 k;

        for (k = 0; k < OBJETS_MAX; k++) {
            degat[k] = 0;
        }

        degat_etage = bg_index;
    }
}

/// Une trame d'un objet qui se brise -- voir `RUPTURE`.
///
/// UNE SUITE PAR ETAGE DE DESTRUCTION, et on avance d'une a chaque chute. La suite 0 est
/// l'objet intact et elle BOUCLE ; les suivantes se jouent une fois et TIENNENT LEUR
/// DERNIERE IMAGE -- Frederic : « la destruction ne se joue pas en boucle, mais une seule
/// fois, avec la derniere image de l'animation persistante ».
///
/// Deux formes s'y rangent :
///
///   * le tonneau de Hugo et les cages de Yun : deux suites, intact puis la rupture ;
///   * les trois objets d'Alex, QUATRE suites d'une image chacune -- leur routine
///     (`0x8C0A97B6`) fait `objet[+38] += 1` tant qu'un compteur de partie le depasse,
///     et chaque etage est un script consecutif : 20, 21, 22, 23.
///
/// ON N'AVANCE QU'AU FRANCHISSEMENT. Le Dreamcast accumule un compteur et le compare a des
/// seuils ; ici une chute dure plusieurs trames, et compter chacune consommerait tous les
/// etages d'un coup. On ne retient donc que la trame ou le contact COMMENCE.
static void rupture(s32 k) {
    const s32 dernier = nos[k].anim->nb_suites - 1;
    s32 touche;

    if (nos[k].etat < 0) {
        /* IL SE SOUVIENT DE LA MANCHE PRECEDENTE -- voir `memoire_des_degats`. */
        const s32 depart = (degat[k] <= dernier) ? degat[k] : dernier;

        nos[k].etat = 0;
        nos[k].contact = 0;
        jouer(k, depart);

        if (depart > 0) {
            /* Deja brise : on reprend a la FIN de sa suite, sur l'image qui reste --
               pas au debut de son animation de rupture, qu'on a deja vue. */
            const DecorAnimation* a = nos[k].anim;

            nos[k].pas = fin_suite(a, depart) - debut_suite(a, depart) - 1;
            nos[k].finie = 1;
        }

        return;
    }

    derouler(k, nos[k].suite == 0);

    touche = chute_sur(k);

    if (touche && !nos[k].contact && nos[k].suite < dernier) {
        nos[k].suite++;
        nos[k].brise = 1;
        degat[k] = nos[k].suite;
        jouer(k, nos[k].suite);
    }

    nos[k].contact = touche;
}

s32 DecorObjets_Brise(const void* work) {
    const s32 k = rang_de(work);
    s32 r;

    if (k < 0) {
        return 0;
    }

    r = nos[k].brise;
    nos[k].brise = 0;
    return r;
}

/// @brief Ce morceau-ci ne dessine RIEN cette trame-ci.
///
/// Un REACTIF non declenche rend du vide pour toutes ses cases. Le test etait en ligne
/// dans `DecorObjets_Tuile` ; il est ici parce que **l'identite de motif doit le poser
/// aussi** -- voir `DecorObjets_Identite`.
static s32 ne_dessine_rien(s32 k) {
    const DecorAnimation* a = nos[k].anim;

    return a != NULL && a->comportement == REACTIF && !nos[k].regard;
}

/// Une trame d'un sprite qui attend que le combattant agisse -- voir `REACTIF`.
static void reactif(s32 k) {
    nos[k].etat = 0;

    if (!reactif_permis()) {
        nos[k].regard = 1;
        return;
    }

    nos[k].regard = (plw[REACTIF_COTE].wu.routine_no[1] > REACTIF_ETAT) ? 1 : 0;
}

/// Une trame de la machine a etats d'un objet a comportement.
static void conduire(s32 k) {
    /* Gele pendant une pause, sauf a la naissance : le premier etat doit etre pose. */
    if (nos[k].etat >= 0 && (EXE_flag || Game_pause || EXE_obroll)) {
        return;
    }

    switch (nos[k].anim->comportement) {
    case CHIEN_DEBOUT:
        chien_debout(k);
        break;

    case CHIEN_COUCHE:
        chien_couche(k);
        break;

    case POISSON_ROUGE:
        poisson_rouge(k);
        break;

    case POISSON_NOIR:
        poisson_noir(k);
        break;

    case TRAJET:
        trajet(k);
        break;

    case SUR_COMBATTANT:
        sur_combattant(k);
        break;

    case REGARD:
        regard_combattant(k);
        break;

    case REACTIF:
        reactif(k);
        break;

    case RUPTURE:
        rupture(k);
        break;

    default:
        break;
    }
}

static s32 image_conduite(s32 k) {
    const DecorAnimation* a = nos[k].anim;

    /* Un REACTIF joue son animation normalement : c'est son AFFICHAGE qui depend du
       combattant, pas son image -- voir `DecorObjets_Tuile`. */
    if (a->comportement == REACTIF) {
        return -1;
    }

    /* Un acolyte n'a ni suites ni durees : son orientation EST son image. */
    if (a->comportement == REGARD) {
        return (nos[k].regard < a->nb_images) ? nos[k].regard : 0;
    }

    /* Un objet a TRAJET sans suites garde l'image que ses durees donnent : c'est sa
       position qui change, pas son animation. */
    if (a->pas == NULL || a->suites == NULL) {
        return -1;
    }

    const s32 pas = (a->comportement == CHIEN_DEBOUT && nos[k].etat == 0)
                        ? debut_suite(a, 0) + nos[k].regard
                        : debut_suite(a, nos[k].suite) + nos[k].pas;
    const s32 i = (pas >= 0 && pas < a->suites[a->nb_suites]) ? a->pas[2 * pas] : 0;

    return (i < a->nb_images) ? i : 0;
}

/// L'image courante d'un objet, d'apres les durees de son script.
///
/// `trame` n'avance qu'une fois par trame, depuis `effect_05_move`, donc cette valeur est
/// stable pendant tout le dessin -- ce que le cache de motifs exige.
static s32 image_de(s32 k) {
    const DecorAnimation* a = nos[k].anim;
    s32 total = 0;
    s32 reste;
    s32 i;

    if (conduit(a)) {
        const s32 im = image_conduite(k);

        /* -1 : un objet a trajet sans suites ; ses durees decident, comme pour un objet
           immobile. */
        if (im >= 0) {
            return im;
        }
    }

    /* Une suite d'images qui n'est pas une boucle reste sur la premiere : voir le champ
       `boucle` dans l'en-tete. Les acolytes de Gill tournent la tete vers les
       combattants, ils ne s'animent pas. */
    if (a == NULL || a->nb_images <= 0 || !a->boucle) {
        return 0;
    }

    /* L'INTRODUCTION NE PASSE QU'UNE FOIS -- voir `depart_boucle` dans l'en-tete. Le
       script du chaton d'Oro se termine par la commande `0x02`, qui reprend a
       l'enregistrement 12 et non a zero : ses douze premieres images sont une entree en
       scene, pas une boucle. On joue donc l'introduction sur ses propres trames, puis on
       ne fait tourner que la queue du script. */
    if (a->depart_boucle > 0 && a->depart_boucle < a->nb_images) {
        s32 intro = 0;

        for (i = 0; i < a->depart_boucle; i++) {
            intro += a->durees[i];
        }

        if (nos[k].trame < intro) {
            reste = nos[k].trame;

            for (i = 0; i < a->depart_boucle; i++) {
                reste -= a->durees[i];

                if (reste < 0) {
                    return i;
                }
            }
        }

        for (i = a->depart_boucle; i < a->nb_images; i++) {
            total += a->durees[i];
        }

        if (total <= 0) {
            return a->depart_boucle;
        }

        reste = (nos[k].trame - intro) % total;

        for (i = a->depart_boucle; i < a->nb_images; i++) {
            reste -= a->durees[i];

            if (reste < 0) {
                return i;
            }
        }

        return a->nb_images - 1;
    }

    for (i = 0; i < a->nb_images; i++) {
        total += a->durees[i];
    }

    if (total <= 0) {
        return 0;
    }

    reste = nos[k].trame % total;

    for (i = 0; i < a->nb_images; i++) {
        reste -= a->durees[i];

        if (reste < 0) {
            return i;
        }
    }

    return a->nb_images - 1;
}

/// @brief Le `y` du moteur pour une rangee d'image -- et l'inverse, c'est la meme.
///
/// **LE MOTEUR COMPTE Y VERS LE HAUT.** La matrice de fond est construite avec un
/// `njScale(0, 1.0, -1.0, 1.0)` (`bg.c`, juste avant le `njGetMatrix` qui la capture) :
/// un objet pose dans une famille de fond a donc son axe y inverse par rapport a l'image.
/// Poser la rangee 0 en y = 0 et la rangee 1 en y = 16 mettait la rangee 1 AU-DESSUS de
/// la rangee 0 -- le sprite sortait la tete en bas, capuche en bas et robe en haut.
///
/// La conversion est une involution : elle sert dans les deux sens.
static s32 y_moteur(const DecorAnimation* a, s32 y_image) {
    return a == NULL ? y_image : (a->ligs - 1) * 16 - y_image;
}

/// @brief Ecrit la grille d'un objet dans SA table de trans. Une fois par etage.
///
/// Le moteur accumule `x -= morceau.x` et `y += morceau.y` : on donne donc des ecarts, de
/// signe oppose en x.
static void batir_le_motif(s32 k) {
    const DecorAnimation* a = nos[k].anim;
    s16 x_prec = 0;
    s16 y_prec = 0;
    s32 col;
    s32 lig;
    s32 n = 0;

    nos[k].trans.offsets[0] = 4;
    nos[k].trans.count = 0;

    if (a == NULL) {
        return;
    }

    for (lig = 0; lig < a->ligs; lig++) {
        for (col = 0; col < a->cols; col++) {
            s16 x;
            s16 y;

            if (n >= CASES_MAX) {
                break;
            }

            x = (s16)(col * 16);
            y = (s16)y_moteur(a, lig * 16);
            nos[k].trans.cases[n].x = (s16)(x_prec - x);
            nos[k].trans.cases[n].y = (s16)(y - y_prec);
            nos[k].trans.cases[n].attr = ATTR_MORCEAU;
            nos[k].trans.cases[n].code = NOTRE_CODE;
            x_prec = x;
            y_prec = y;
            n++;
        }
    }

    nos[k].trans.count = (u16)n;
}

void DecorObjets_Oublier(const void* work) {
    /* LE TAS D'EFFETS RECYCLE SES EMPLACEMENTS. Nos gardes comparent le `WORK` dessine
       aux notres ; quand l'etage se termine, nos objets rendent les leurs et les objets
       des menus les reprennent aux MEMES adresses. Le pointeur coincidait, et on leur
       donnait nos tables et nos tuiles -- l'acolyte de Gill se dessinait par-dessus
       l'ecran de selection et l'ecran RESULT.
       `work == NULL` vide sans condition : c'est `effect_work_init`. */
    s32 k;

    if (work == NULL) {
        if (nb_objets) {
            trace("tous les objets oublies : le tas repart a zero %d %d\n", 0, 0, 0);
        }

        for (k = 0; k < OBJETS_MAX; k++) {
            nos[k].work = NULL;
            nos[k].anim = NULL;
            nos[k].trans.count = 0;
            nos[k].palette_envoyee = 0;
        }

        /* UNE GENERATION DE PLUS -- voir `DecorObjets_Identite`. C'est ici que le tas
           d'effets repart a zero, donc ici que commence une nouvelle mise en place
           d'etage : les identites de motif de la precedente ne doivent plus jamais
           etre retrouvees. */
        generation = (generation + 1u) & 3u;

        nb_objets = 0;
        return;
    }

    for (k = 0; k < nb_objets; k++) {
        if (nos[k].work == work) {
            nos[k].work = NULL;
            nos[k].anim = NULL;
            nos[k].trans.count = 0;
            nos[k].palette_envoyee = 0;
            trace("objet %d oublie : son emplacement retourne au tas %d %d\n", k, 0, 0);
            return;
        }
    }
}

void DecorObjets_Marquer(const void* work, s32 bg_index, s32 rang) {
    const DecorAnimation* a;
    s32 base;
    s32 j;

    if (rang < 0 || rang >= OBJETS_MAX) {
        return;
    }

    a = DecorObjets_Animation(bg_index, rang);

    /* LA BASE DE CLE DE CET OBJET : la somme des morceaux de tous ceux qui le precedent
       dans l'etage. Elle ne depend que de la table, donc elle est la meme a chaque
       naissance, et deux objets ne peuvent pas se recouvrir. `CLE_VIDE` (0xFFFF) reste
       hors de portee : au-dela, l'objet n'est pas marque du tout plutot que de se
       dessiner a la place d'un autre. */
    base = 0;

    for (j = 0; j < rang; j++) {
        const DecorAnimation* p = DecorObjets_Animation(bg_index, j);

        if (p != NULL) {
            base += p->nb_images * p->cols * p->ligs;
        }
    }

    /* ET LA CLE CHANGE DE MOITIE A CHAQUE MISE EN PLACE -- 25/09/2026.
     *
     * Frederic, sur le 2eme round de Dudley : « *transition OK, mais 2 round glitche* ».
     * Les objets naissaient bien -- le journal les marque tous les 32 aux bons x, y, z --
     * mais ils se dessinaient avec les PIXELS de l'aire precedente.
     *
     * `cle_base` est la somme des morceaux des objets qui PRECEDENT celui-ci DANS SON
     * ETAGE. Deux etages donnent donc des bases differentes pour le meme rang, mais rien
     * n'empeche deux cles de coincider d'une aire a l'autre -- et le cache de motifs,
     * lui, garde les tuiles de l'aire qu'on vient de quitter. L'objet 3 de l'etage 45
     * retrouvait celles de l'objet 3 de l'etage 44.
     *
     * `DecorObjets_Identite` portait deja deux bits de generation ; la cle de TUILE n'en
     * portait aucun. On lui en donne UN : les cles d'une mise en place tombent dans la
     * moitie basse de l'espace, celles de la suivante dans la haute, et deux aires qui se
     * succedent ne peuvent plus se rencontrer.
     *
     * POURQUOI UN SEUL BIT ET PAS DEUX : le pire de nos etages, le 52, demande 17373
     * cles ; quatre generations a 16384 deborderaient (66525 > 65535). Deux a 32768
     * tiennent -- au pire 32768 + 17373 = 50141, et `CLE_VIDE` (65535) reste hors de
     * portee. Une collision ne redeviendrait possible qu'entre une mise en place et la
     * SUIVANTE DE LA SUIVANTE, deux manches plus tard, quand le cache a vieilli. */
    base += (s32)(generation & 1u) * 32768;

    if (a != NULL && base + a->nb_images * a->cols * a->ligs >= (s32)CLE_VIDE) {
        trace("objet %d ECARTE : l'espace des cles est plein a %d %d\n", rang, base, 0);
        return;
    }

    nos[rang].work = work;
    nos[rang].anim = a;
    nos[rang].trame = 0;
    nos[rang].palette_envoyee = 0;
    nos[rang].cle_base = base;
    nos[rang].etat = -1;
    nos[rang].bouge = 0;
    nos[rang].echelle = (a != NULL) ? a->echelle : 0;
    nos[rang].echelle_trame = 0;
    nos[rang].brise = 0;
    nos[rang].contact = 0;
    memoire_des_degats(bg_index);
    batir_le_motif(rang);

    /* Un objet a comportement choisit son premier etat des sa naissance : le dessin
       peut venir avant la premiere avance. */
    if (conduit(a)) {
        conduire(rang);
    }

    if (rang >= nb_objets) {
        nb_objets = rang + 1;
    }

    if (a != NULL) {
        trace("marque objet %d : etage %d, %d images\n", rang, (s32)a->etage,
              (s32)a->nb_images);
        trace("   x %d y %d famille %d\n", (s32)a->x, (s32)a->y, (s32)a->famille);
        trace("   z %d, grille %d x %d\n", (s32)a->z, (s32)a->cols, (s32)a->ligs);
    } else {
        trace("marque objet %d : etage %d SANS animation %d\n", rang, bg_index, 0);
    }
}

/* L'identite de motif que voit le cache. Le groupe 0xD3 ne peut heurter aucune identite
   du jeu : `mtrans.c` cherche ses motifs sous `(0 << 16) | cg_number`, groupe zero.
   Le RANG y entre : sans lui, deux objets de la meme image partageraient une entree de
   cache et se dessineraient l'un a la place de l'autre. */
#define GROUPE_A_NOUS 0x00D30000u

/* UN REACTIF CACHE N'EST PLUS DESSINE DU TOUT -- 24/09/2026.

   Frederic : « crash encore juste en appuyant sur le bouton coup de pied fort ». Meme
   ligne de trace que la veille, et c'est elle qui donne tout :

       GEL 16x16 : code 0x00d303ce (groupe 0xd3), 1 emplacements occupes

   **UN emplacement.** La collection retrouvee ne contenait qu'un seul morceau -- et le
   seul morceau qu'un de nos objets puisse televerser tout seul, c'est `tuile_vide` sous
   `CLE_VIDE`, la case partagee.

   L'etage 39 (Sean) porte **cinq objets REACTIF**. Au repos, `DecorObjets_Tuile` leur rend
   du vide pour TOUTES leurs cases : la collection de leur identite se cree donc avec un
   seul morceau. Mais l'identite ne portait que le rang et l'image -- **et l'image d'un
   REACTIF avance normalement, c'est son AFFICHAGE qui depend du combattant**
   (`image_conduite` rend -1 pour lui).

   Coup de pied fort : `plw[0].routine_no[1]` passe au-dessus de 2, `regard` passe a 1,
   l'objet se montre. Meme rang, meme image, **meme identite** : le moteur retrouve la
   collection d'une seule case, prend le chemin qui ne televerse rien, cherche la cle 974
   parmi ce seul emplacement, ne trouve pas, et boucle a l'infini.

   PREMIERE TENTATIVE, ECARTEE : mettre cette visibilite dans l'identite (un bit de plus).
   Elle marchait sur le papier et elle DOUBLAIT le nombre d'identites des reactifs ; le
   jeu est mort a l'entree de l'etage, cette fois sans meme un journal. Une correction qui
   ajoute de la pression sur le cache pour soigner le cache n'est pas une correction.

   LA VRAIE : **un reactif cache n'est pas dessine VIDE, il n'est pas dessine DU TOUT.**
   `eff05` ne le passe plus a `disp_pos_trans_entry_s` ; il n'a donc ni morceau, ni
   collection, ni identite cette trame-la. Rien a retrouver, rien a confondre -- et le
   cache respire au lieu de se remplir de cases vides.

   La regle generale, elle, reste celle du 17/09 : l'identite doit porter tout ce qui
   change l'ensemble des morceaux. Ici on a supprime le changement au lieu de le decrire.

   (La generation ci-dessous reste : elle repare une autre faute, reelle, sur le
   rechargement d'un etage.)

   DEUX BITS DE GENERATION -- 24/09/2026, le gel de Sean a la SECONDE entree.

   Frederic : « crash du decor de Sean NG ». Le journal donne le mot exact :

       GEL 16x16 : code 0x00d303ce (groupe 0xd3), 1 emplacements occupes

   Le groupe 0xD3 est le NOTRE, la cle 974 est celle d'un de nos morceaux, et la
   collection trouvee n'en contenait QU'UN. Ce n'etait donc pas la bonne collection.

   `check_patcash_ex_trans` cherche l'identite dans `mt->cpat`, une liste plate de sesenta
   et quatre entrees **qui survit au changement d'etage**. Le TAS DE MORCEAUX, lui, est
   remis a zero quand l'etage se recharge. A la seconde entree dans le meme etage, l'objet
   `k` a la meme image que la premiere fois : meme identite, entree RETROUVEE, et
   `makeup_tpu_free` restreint alors la recherche aux emplacements que cette entree avait
   pris -- des emplacements qui ne portent plus rien. `get_mltbuf16_ext` ne trouve pas,
   journalise, et **boucle a l'infini**.

   Il suffit que l'identite change d'une mise en place a l'autre. Les seize bits bas
   portaient l'image (8 bits) et le rang (6 bits, `OBJETS_MAX` = 56) : les deux bits hauts
   etaient libres. Ils comptent maintenant les mises en place, modulo quatre -- de quoi
   laisser les entrees mortes vieillir et se faire reprendre.

   CE N'EST PAS LA FAMILLE DE SEAN. `my_family` n'est lu qu'a UN endroit du moteur,
   `mlt_obj_matrix` (`mtrans.c`), pour choisir la matrice de defilement ; il n'entre ni
   dans l'identite, ni dans la cle de morceau, ni dans le cache. Le gel etait la avant,
   et il attendait qu'on entre deux fois dans le meme etage. */
s32 DecorObjets_Dessine(const void* work) {
    const s32 k = rang_de(work);

    /* Tout ce qui n'est pas a nous se dessine comme avant. */
    return (k < 0) ? 1 : !ne_dessine_rien(k);
}

s32 DecorObjets_Identite(const void* work, u32* code) {
    const s32 k = rang_de(work);

    if (k < 0 || code == NULL) {
        return 0;
    }

    /* HUIT BITS D'IMAGE DEPUIS LE 17/09/2026 (six avant). Trois animations de New
       Generation depassent 64 images -- Alex 90, Sean 93, Elena 1 96 -- et l'image 64
       d'un objet prenait l'identite de l'image 0 du suivant. `OBJETS_MAX` (48) tient
       toujours dans les huit bits hauts du mot bas. */
    *code = GROUPE_A_NOUS | (generation << 14) | ((u32)k << 8) | (u32)image_de(k);
    return 1;
}

s32 DecorObjets_Groupe(const void* work, void** trans_table, void** texture_table, s32* n) {
    const s32 k = rang_de(work);

    if (k < 0 || trans_table == NULL || texture_table == NULL || n == NULL) {
        return 0;
    }

    *trans_table = &nos[k].trans;
    *texture_table = &notre_texture;
    *n = 0;
    return 1;
}

/* Definie plus bas, avec `DecorObjets_Echelle` qui la lit. */
static void avancer_echelle(s32 k);

void DecorObjets_Avancer(const void* work) {
    /* Une liste de `-1` ecrite a la main se desynchronise d'`OBJETS_MAX` des qu'il bouge --
       le C completant a ZERO, les objets au-dela auraient cru avoir deja affiche l'image 0. */
    static s32 image_precedente[OBJETS_MAX];
    static s32 initialise = 0;
    static s32 nb_changements = 0;
    const s32 k = rang_de(work);
    s32 image;
    s32 i;

    if (!initialise) {
        for (i = 0; i < OBJETS_MAX; i++) {
            image_precedente[i] = -1;
        }

        initialise = 1;
    }

    if (k < 0) {
        return;
    }

    nos[k].trame++;
    avancer_echelle(k);

    if (conduit(nos[k].anim)) {
        conduire(k);
    }

    image = image_de(k);

    /* BATTEMENT DE COEUR. Les journaux du 31/08 s'arretaient net sans dire si le jeu
       etait FIGE ou s'il tournait sans rien montrer -- deux pannes tres differentes, et
       on ne pouvait pas les separer. Une ligne toutes les soixante trames sur le seul
       objet 0 suffit : si elle avance, le jeu tourne. */
    if (k == 0 && (nos[k].trame % 60) == 0 && nos[k].trame <= 3600) {
        trace("battement : trame %d, etage %d, image %d\n",
              nos[k].trame, (s32)nos[k].anim->etage, image);
    }

    /* UNE LIGNE PAR CHANGEMENT, pas par trame. Un compteur journalise ne dit pas si
       l'animation tourne ; un changement, si. */
    if (image != image_precedente[k]) {
        if (nb_changements < 60) {
            nb_changements++;
            trace("objet %d : image %d a la trame %d\n", k, image, nos[k].trame);
        }

        image_precedente[k] = image;
    }
}

/// Une trame de l'echelle d'un objet -- voir `DecorAnimation.echelle`.
static void avancer_echelle(s32 k) {
    const DecorAnimation* a = nos[k].anim;

    if (a == NULL || a->echelle == 0 || a->echelle_pas <= 0) {
        return;
    }

    /* SUR LE BON SEGMENT SEULEMENT. La caleche ne retrecit pas sous son tunnel ni pendant
       qu'elle demarre : le Dreamcast ne compte les crans que dans son etat 2, celui ou elle
       roule -- et cet etat est notre dernier segment de trajet. */
    if (a->echelle_seg >= 0 && nos[k].suite_trajet != a->echelle_seg) {
        nos[k].echelle_trame = 0;
        return;
    }

    /* La boucle du trajet remet la taille de naissance, comme le fait la remise a zero de
       `routine_no[0]` quand la caleche passe sous x 48. */
    if (nos[k].suite_trajet == 0 && nos[k].echelle < a->echelle) {
        nos[k].echelle = a->echelle;
    }

    if (++nos[k].echelle_trame < a->echelle_pas) {
        return;
    }

    nos[k].echelle_trame = 0;

    if (nos[k].echelle > 0) {
        nos[k].echelle--;
    }
}

s32 DecorObjets_Echelle(const void* work, s32* taille) {
    const s32 k = rang_de(work);

    if (k < 0 || taille == NULL || nos[k].anim == NULL || nos[k].anim->echelle == 0) {
        return 0;
    }

    *taille = nos[k].echelle;
    return 1;
}

s32 DecorObjets_Position(const void* work, s32* x, s32* y) {
    const s32 k = rang_de(work);
    s32 x0;
    s32 y0;

    if (k < 0 || !nos[k].bouge || x == NULL || y == NULL) {
        return 0;
    }

    if (nos[k].anim->comportement == POISSON_ROUGE) {
        x0 = ROUGE_X;
        y0 = ROUGE_Y;
    } else if (nos[k].anim->comportement == POISSON_NOIR) {
        x0 = NOIR_X;
        y0 = NOIR_Y;
    } else if (nos[k].anim->comportement == TRAJET
               || nos[k].anim->comportement == SUR_COMBATTANT) {
        /* Un trajet compte en ECART depuis la fiche, pas en position absolue.

           ET IL SE REPLIE SUR LA BANDE -- 24/09/2026, les oiseaux d'Elena 1. Le moteur de
           New Generation ecrit sa position de dessin `[+84] = [+102] & 0x3FF` : la bande
           fait 1024 et ce qui sort d'un bord revient par l'autre. Les oiseaux naissent en
           x -256, donc 768, et traversent 766 pixels : sans le repli ils sortiraient de la
           page a 1494. Les autres objets a trajet restent dans [0, 1024] -- la caleche de
           Dudley va de 416 vers 48, l'eau d'Elena 1 de 412 a 428 -- et le masque ne change
           rien pour eux. */
        *x = (nos[k].anim->x + (nos[k].px >> 16)) & 0x3FF;
        *y = nos[k].anim->y + (nos[k].py >> 16);

        /* UN MORCEAU MIS A L'ECHELLE SE RECOLLE AU PREMIER -- voir `echelle_ecart`. */
        if (nos[k].anim->echelle != 0 && nos[k].anim->echelle_ecart != 0) {
            *x -= ((63 - nos[k].echelle) * nos[k].anim->echelle_ecart) / 64;
        }

        return 1;
    } else {
        return 0;
    }

    /* La fiche est posee pour la position de naissance ; l'objet s'en ecarte d'autant.
       Le `y` du moteur croit vers le haut, comme celui de 2I -- voir `y_moteur`. */
    *x = nos[k].anim->x + (nos[k].px >> 16) - x0;
    *y = nos[k].anim->y + (nos[k].py >> 16) - y0;
    return 1;
}

static s32 total_dit = 0;

void DecorObjets_InstallerPalette(const void* work) {
    const s32 k = rang_de(work);
    const Palette* cp3;
    s32 emplacement;
    s32 change = 0;
    s32 i;

    if (k < 0) {
        return;
    }

    emplacement = EMPLACEMENT_PALETTE + k;

    /* ROUGE ET BLEU S'ECHANGENT, et ce n'est pas un detail de gout : c'est la faute que
       `col_edit.c` nomme en toutes lettres au-dessus de `swatch_color` --

           "ColorRAM holds what palConvSrcToRam produced, which is not the layout the file
            had: red sits in the low bits and blue in the high ones, the reverse of the
            archive's ARGB1555."

       `palCreateGhost` le construit : `palFormRam` y met `rs = 0` et `bs = 10`, la ou
       `palFormSrc` a `rs = 10` et `bs = 0`. `ColorRAM` est donc en **ABGR1555**, et nos
       couleurs sortent de la Dreamcast en ARGB1555. */
    for (i = 0; i < 64; i++) {
        const unsigned short src = nos[k].anim->palette[i];
        const unsigned short r = (unsigned short)((src >> 10) & 31);
        const unsigned short g = (unsigned short)((src >> 5) & 31);
        const unsigned short b = (unsigned short)(src & 31);

        const unsigned short ram =
            (unsigned short)((src & 0x8000u) | (unsigned short)(b << 10) |
                             (unsigned short)(g << 5) | r);

        if (ColorRAM[emplacement][i] != ram) {
            ColorRAM[emplacement][i] = ram;
            change = 1;
        }
    }

    /* ET L'ENVOI AU MATERIEL. Ecrire dans `ColorRAM` ne suffit pas : le dessin lit une
       copie cote materiel, et sans cet envoi elle garde les anciennes couleurs.
       L'emplacement 300 n'est pas un depassement -- la palette fantome en compte 512,
       `ppgSetupPalChunkDir` faisant `pch->total = SDL_Swap16BE(ppl->palettes)`, un
       boutisme inverse. */
    cp3 = palGetChunkGhostCP3();

    if (cp3 == NULL || cp3->be == 0 || cp3->handle == NULL || emplacement >= cp3->total) {
        trace("palette: fantome absent (be %d total %d) %d\n", cp3 ? cp3->be : -1,
              cp3 ? cp3->total : -1, 0);
        return;
    }

    if (!total_dit) {
        total_dit = 1;
        trace("palette fantome CP3: total %d be %d %d\n", (s32)cp3->total, (s32)cp3->be, 0);
    }

    /* N'ENVOYER QUE CE QUI A CHANGE -- c'etait LA lenteur de nos decors (15/09).
       Cet envoi n'est pas une copie de soixante-quatre u16 : `flUnlockPalette` finit en
       `SDLGPURenderer_CreatePalette`, qui DETRUIT la texture de palette et en cree une
       neuve. Fait pour chaque objet a chaque image, ca faisait sur Yun des centaines de
       textures par seconde, et Yun, Yang, Ryu, Necro, Hugo, Ibuki, Oro, Akuma ramaient.
       Mesure : sans cet envoi, plus aucune lenteur sur Yun et Yang -- mais des couleurs
       fausses, puisque rien n'etait envoye.
       On garde la reecriture a chaque image, qui rattrape un chargement d'etage ecrivant
       l'emplacement apres coup : si `ColorRAM` a bouge, `change` le voit et on renvoie.
       Et le premier passage d'un objet envoie toujours, `palette_envoyee` etant remis a
       zero a chaque naissance et a chaque oubli. */
    if (!change && nos[k].palette_envoyee) {
        return;
    }

    palUpdateGhostCP3(emplacement, 1);
    nos[k].palette_envoyee = 1;
}

static s32 nb_traces = 0;

void DecorObjets_Trace(s32 a_nous, s32 groupe, s32 offset, s32 wh) {
    /* NOS morceaux seulement. La premiere version notait tout, et l'ecran de selection
       epuisait le quota avant meme que l'objet naisse. */
    if (!a_nous || nb_traces >= 60) {
        return;
    }

    nb_traces++;
    trace("chunk NOTRE groupe %d offset %d wh %d\n", groupe, offset, wh);
}

const unsigned char* DecorObjets_Tuile(const void* work, s32 cg, s32 x, s32 y, s32 taille, u16* cle) {
    const s32 k = rang_de(work);
    const DecorAnimation* a;
    s32 image;
    s32 i;

    if (k < 0) {
        return NULL;
    }

    /* UN MORCEAU QUI N'EST PAS UNE TUILE DE 16x16 : ON N'Y TOUCHE PAS.
       Cette fonction rendait ici une tuile vide de 1024 octets sous une cle a nous, pour
       effacer les 32x32 du donneur. **C'est ce qui gelait le jeu en fin de round** : le
       premier chemin televersait le vide sous ce code, le second ne le retrouvait pas et
       partait en `while (1) {}`. Depuis que le groupe est le notre, la question ne se
       pose plus -- nos morceaux sont tous des 16x16. */
    if (taille != 256) {
        return NULL;
    }

    (void)cg;
    a = nos[k].anim;

    /* UN REACTIF QUI N'EST PAS DECLENCHE NE SE DESSINE PAS. On ne le retire pas de la
       liste -- son rang doit rester -- on rend du vide sous la cle partagee. */
    if (ne_dessine_rien(k)) {
        *cle = CLE_VIDE;
        return tuile_vide;
    }

    image = image_de(k);

    for (i = 0; i < a->nb_tuiles; i++) {
        const DecorTuile* t = &a->tuiles[i];

        if (t->image == image && t->x == x && t->y == y_moteur(a, y)) {
            /* UNE CLE PAR (rang, image, case). C'est ce qui fait que l'image suivante est
               bien televersee au lieu de retomber sur l'entree de la precedente, et que
               deux objets ne se melangent pas. Ce n'est plus un decoupage en bits mais un
               RANG DE MORCEAU dans l'etage -- voir `OBJETS_MAX` : le decoupage plafonnait
               a 32 objets et Necro en demande 34. */
            /* LA CASE SE DEDUIT DE x ET y, PLUS DE LA PLACE DANS LA TABLE.
               C'etait `(i - image * cols * ligs) & 31`, qui supposait la table PLEINE --
               une tuile par case et par image, sans trou. La valeur est identique tant
               qu'elle l'est : les tuiles sont emises image, puis ligne, puis colonne,
               donc `i - image * cases` vaut exactement `lig * cols + col`.

               Mais le generateur saute desormais les cases entierement transparentes, et
               l'ancienne formule aurait decale toutes les suivantes. Le gain n'est pas
               cosmetique : le tas ne tient QUE 1024 morceaux -- `x16_map[4][16]`, quatre
               pages, pas une de plus. La cascade d'Ibuki a 272 cases dont 192 occupees ;
               a quatre images vivantes, 272 en faisaient 1088 et figeaient le jeu. */
            const s32 cas = (t->y / 16) * a->cols + (t->x / 16);

            *cle = (u16)(nos[k].cle_base + image * (a->cols * a->ligs) + cas);
            return t->pixels;
        }
    }

    /* Une case que le sprite ne couvre pas : on la vide, sinon le dessin du donneur se
       verrait autour du notre. Toutes partagent la meme cle : une seule entree. */
    *cle = CLE_VIDE;
    return tuile_vide;
}
