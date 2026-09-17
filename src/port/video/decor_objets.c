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

    combat = a->variante & 0x30;
    return combat == 0 || (combat & (un_ami_present ? 0x20 : 0x10)) != 0;
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
 *     trajet = { duree, vx, vy, suite, ... } et la liste boucle sur son premier segment,
 *     ou l'objet retrouve sa position de naissance.
 *
 * `vx` et `vy` sont en 1/256 de pixel par trame. `suite` vaut -1 quand le segment ne change
 * pas l'animation (l'objet garde le script que ses durees font tourner).
 *
 *   * la caleche de Dudley 1 (id 65, `0x8C0A8970`) : elle attend 600 trames sous le tunnel,
 *     part a -1,125 pixel pendant 196 trames, puis a -1 pixel jusqu'a sortir, et revient ;
 *   * l'eau de la riviere d'Elena 1 (id 45, `0x8C0A4D34`) : elle glisse d'un demi-pixel par
 *     trame et revient a sa place toutes les 33 trames, quand son script avance d'une image.
 */
#define TRAJET 5

/// L'objet a-t-il un comportement, et ses tables ?
static s32 conduit(const DecorAnimation* a) {
    if (a == NULL || a->comportement == 0 || a->nb_images <= 0) {
        return 0;
    }

    if (a->comportement == TRAJET) {
        return a->trajet != NULL;
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

/// Le segment courant du trajet : `{ duree, vx, vy, suite }`.
static const short* trajet_segment(s32 k) {
    return nos[k].anim->trajet + 4 * nos[k].suite_trajet;
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

        if (a->pas != NULL && a->trajet[3] >= 0) {
            jouer(k, a->trajet[3]);
        }

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
        /* La boucle repasse par le depart : c'est la remise a zero que font les routines
           (la caleche revient sous le tunnel, l'eau revient a sa place). */
        nos[k].suite_trajet = 0;
        nos[k].px = 0;
        nos[k].py = 0;
    }

    seg = trajet_segment(k);
    nos[k].reste_trajet = seg[0];

    if (a->pas != NULL && seg[3] >= 0) {
        jouer(k, seg[3]);
    }
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

    default:
        break;
    }
}

static s32 image_conduite(s32 k) {
    const DecorAnimation* a = nos[k].anim;

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

s32 DecorObjets_Identite(const void* work, u32* code) {
    const s32 k = rang_de(work);

    if (k < 0 || code == NULL) {
        return 0;
    }

    /* HUIT BITS D'IMAGE DEPUIS LE 17/09/2026 (six avant). Trois animations de New
       Generation depassent 64 images -- Alex 90, Sean 93, Elena 1 96 -- et l'image 64
       d'un objet prenait l'identite de l'image 0 du suivant. `OBJETS_MAX` (48) tient
       toujours dans les huit bits hauts du mot bas. */
    *code = GROUPE_A_NOUS | ((u32)k << 8) | (u32)image_de(k);
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
    } else if (nos[k].anim->comportement == TRAJET) {
        /* Un trajet compte en ECART depuis la fiche, pas en position absolue. */
        *x = nos[k].anim->x + (nos[k].px >> 16);
        *y = nos[k].anim->y + (nos[k].py >> 16);
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
