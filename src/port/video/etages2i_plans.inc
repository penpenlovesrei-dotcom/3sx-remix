/* Genere par dc-decors/outils/etages.py -- ne pas modifier a la main.
 *
 * Les quinze etages de 2nd Impact ajoutes a 3rd Strike. Chacun a SA PROPRE
 * archive de pages (`resources/stages/<n>.bin`), donc son nombre de plans ne
 * depend d'aucun etage existant.
 *
 * Les coefficients viennent du binaire de 2nd Impact : table 0x8C1D4F48 pour
 * les plans lointain et proche, litteraux du script d'etage pour le plan
 * supplementaire, defaut 0,875 sinon. */

#define ETAGES2I_USE_SCR \
    4, 3, 2, 2, 2, 3, 3, 3, 3, 3, 2, 2, 2, 3, 2

#define ETAGES2I_BGW_NUMBER \
    { 1, 2, 3, 4 }, { 1, 2, 3 }, { 1, 2 }, { 1, 2 }, { 1, 2 }, { 1, 2, 3 }, { 1, 2, 3 }, { 1, 2, 3 }, { 1, 2, 3 }, { 1, 2, 3 }, { 1, 2 }, { 1, 2 }, { 1, 2 }, { 1, 2, 3 }, { 1, 2 }

#define ETAGES2I_PRIORITY \
    0x5E545657, 0x5E545600, 0x5E540000, 0x685E0000, 0x5E540000, 0x68545E00, 0x68545E00, 0x68545E00, 0x5E545600, 0x68545E00, 0x72680000, 0x5E540000, 0x5E540000, 0x5E545600, 0x5E540000

#define ETAGES2I_GBIX \
    { 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF }, { 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF }, { 0xFFFFFFFF, 0xFFFFFFFF }, { 0xFFFFFFFF, 0xFFFFFFFF }, { 0xFFFFFFFF, 0xFFFFFFFF }, { 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF }, { 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF }, { 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF }, { 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF }, { 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF }, { 0xFFFFFFFF, 0xFFFFFFFF }, { 0xFFFFFFFF, 0xFFFFFFFF }, { 0xFFFFFFFF, 0xFFFFFFFF }, { 0xFFFFFFFF, 0xFFFFFFFF, 0xFFFFFFFF }, { 0xFFFFFFFF, 0xFFFFFFFF }

#define ETAGES2I_SPEED_X_LOIN \
    [22] = 0x4000, [23] = 0xA000, [24] = 0xC000, [25] = 0xE000, [26] = 0xC000, [27] = 0x10000, [28] = 0x0, [29] = 0x4000, [30] = 0x8000, [31] = 0x8000, [32] = 0xE000, [33] = 0xC000, [34] = 0xF000, [35] = 0x6000, [36] = 0xC000

#define ETAGES2I_SPEED_Y_LOIN \
    [22] = 0xA000, [23] = 0xC000, [24] = 0xF000, [25] = 0x11000, [26] = 0xE000, [27] = 0x10000, [28] = 0x0, [29] = 0xA000, [30] = 0x8000, [31] = 0xF000, [32] = 0x11000, [33] = 0xC000, [34] = 0x10000, [35] = 0xC000, [36] = 0xE000

#define ETAGES2I_SPEED_X_TIERS \
    [22] = 0xE000, [23] = 0xD000, [27] = 0x10000, [28] = 0xC000, [29] = 0xA000, [30] = 0xC000, [31] = 0xC000, [35] = 0xC000

#define ETAGES2I_SPEED_Y_TIERS \
    [22] = 0xE000, [23] = 0xE000, [27] = 0x10000, [28] = 0xE000, [29] = 0x10000, [30] = 0xC000, [31] = 0xE000, [35] = 0xE000

#define ETAGES2I_SPEED_X_QUATRE \
    [22] = 0xA000

#define ETAGES2I_SPEED_Y_QUATRE \
    [22] = 0xE000

