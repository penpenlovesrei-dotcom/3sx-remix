/* Genere par dc-decors/outils/etages2ibis.py -- ne pas modifier a la main.
 *
 * Les deux bandes de 2nd Impact que `etages.py` ne montait pas : `bg08`
 * (l'aire 0 du decor 8, dont `bg09` est l'aire 1) et `bg10` (le decor 16).
 * Etages 56 et 57, apres les dix-neuf de New Generation.
 *
 * La table 0x8C1D591C de 2nd Impact donne (decor*3 + aire) -> bande, et dit
 * que le decor 8 porte les bandes 8, 9 et 9. C'est ce qui fait de `bg08` une
 * VARIANTE, posee dans `bg_index_tbl[30]`. */

#define ETAGES2IBIS_USE_SCR \
    2, 2

#define ETAGES2IBIS_BGW_NUMBER \
    { 1, 2 }, { 1, 2 }

#define ETAGES2IBIS_PRIORITY \
    0x5E540000, 0x5E540000

#define ETAGES2IBIS_GBIX \
    { 0xFFFFFFFF, 0xFFFFFFFF }, { 0xFFFFFFFF, 0xFFFFFFFF }

#define ETAGES2IBIS_INDEX_TBL \
    { 56, 56, 56 }, { 57, 57, 57 }

#define ETAGES2IBIS_LIMIT \
    { { 0x0140, 0x02c0, 0xF0, 0xF0 }, { 0x0140, 0x02c0, 0xF0, 0xF0 }, { 0x0140, 0x02c0, 0xF0, 0xF0 } }, { { 0x0140, 0x02c0, 0xF0, 0xF0 }, { 0x0140, 0x02c0, 0xF0, 0xF0 }, { 0x0140, 0x02c0, 0xF0, 0xF0 } }

#define ETAGES2IBIS_MSP \
    { { 0x1000, 0x8000 }, { 0x10000, 0x10000 }, { 0x0, 0x0 } }, { { 0xE000, 0xE000 }, { 0x10000, 0x10000 }, { 0x0, 0x0 } }

#define ETAGES2IBIS_OPAQUE \
    0x80, 0x80

#define ETAGES2IBIS_BGRW_ON \
    { -1, -1, -1, -1, -1, -1, -1, -1 }, { -1, -1, -1, -1, -1, -1, -1, -1 }

#define ETAGES2IBIS_OB_PAGE \
    { 1, 1 }, { 1, 1 }

#define ETAGES2IBIS_AKE_BG_OFF \
    3, 3

#define ETAGES2IBIS_SPEED_X_LOIN \
    [56] = 0x1000, [57] = 0xE000

#define ETAGES2IBIS_SPEED_Y_LOIN \
    [56] = 0x8000, [57] = 0xE000

