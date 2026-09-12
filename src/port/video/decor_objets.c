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
 *     identite de motif   0x00D3 <<16 | rang <<6 | image
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

#include "sf33rd/Source/Game/rendering/color3rd.h"
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
/// **32 EST LA BORNE DURE, ET ELLE VIENT DE LA CLE DE CACHE** : `rang << 11 | image << 5 |
/// case` ne laisse que CINQ bits au rang. Au-dela, deux objets partageraient leurs cles et
/// se dessineraient l'un a la place de l'autre.
///
/// C'etait 12, et le compte etait ECRETE en silence. Depuis que les objets trop larges sont
/// servis en morceaux voisins au lieu d'etre ecartes (`animer2i.morceaux_objet`), un etage
/// en compte bien plus : Necro en a 15, Elena 8 rien que pour son grand sprite.
#define OBJETS_MAX 32

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
    NotreTrans trans;
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

/// Tire la variante de cet etage, une seule fois.
static void tirer_la_variante(s32 bg_index) {
    const s32 forcee = variante_forcee();

    if (bg_index == variante_etage) {
        return;
    }

    variante_etage = bg_index;
    variante_courante = (forcee >= 0) ? forcee : (s32)(rand() & 3);
    trace("etage %d : variante de decor %d %d\n", bg_index, variante_courante, 0);
}

/// Cet objet existe-t-il dans la variante courante ?
static s32 dans_la_variante(const DecorAnimation* a) {
    /* Un objet sans masque -- il n'y en a plus, mais la garde ne coute rien -- est de
       toutes les variantes plutot que d'aucune. */
    return a == NULL || a->variante == 0 || (a->variante & (1 << variante_courante));
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

/// L'image courante d'un objet, d'apres les durees de son script.
///
/// `trame` n'avance qu'une fois par trame, depuis `effect_05_move`, donc cette valeur est
/// stable pendant tout le dessin -- ce que le cache de motifs exige.
static s32 image_de(s32 k) {
    const DecorAnimation* a = nos[k].anim;
    s32 total = 0;
    s32 reste;
    s32 i;

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
        }

        nb_objets = 0;
        return;
    }

    for (k = 0; k < nb_objets; k++) {
        if (nos[k].work == work) {
            nos[k].work = NULL;
            nos[k].anim = NULL;
            nos[k].trans.count = 0;
            trace("objet %d oublie : son emplacement retourne au tas %d %d\n", k, 0, 0);
            return;
        }
    }
}

void DecorObjets_Marquer(const void* work, s32 bg_index, s32 rang) {
    const DecorAnimation* a;

    if (rang < 0 || rang >= OBJETS_MAX) {
        return;
    }

    a = DecorObjets_Animation(bg_index, rang);
    nos[rang].work = work;
    nos[rang].anim = a;
    nos[rang].trame = 0;
    batir_le_motif(rang);

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

    *code = GROUPE_A_NOUS | ((u32)k << 6) | (u32)image_de(k);
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

static s32 total_dit = 0;

void DecorObjets_InstallerPalette(const void* work) {
    const s32 k = rang_de(work);
    const Palette* cp3;
    s32 emplacement;
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

        ColorRAM[emplacement][i] =
            (unsigned short)((src & 0x8000u) | (unsigned short)(b << 10) |
                             (unsigned short)(g << 5) | r);
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

    palUpdateGhostCP3(emplacement, 1);
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
               deux objets ne se melangent pas. La case est comptee DANS l'image -- 63 au
               plus -- et l'image tient sur six bits : `bg05` en a quarante-six. */
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

            *cle = (u16)(((u32)k << 11) | ((u32)image << 5) | ((u32)cas & 31u));
            return t->pixels;
        }
    }

    /* Une case que le sprite ne couvre pas : on la vide, sinon le dessin du donneur se
       verrait autour du notre. Toutes partagent la meme cle : une seule entree. */
    *cle = CLE_VIDE;
    return tuile_vide;
}
