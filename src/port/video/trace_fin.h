#ifndef PORT_VIDEO_TRACE_FIN_H
#define PORT_VIDEO_TRACE_FIN_H

#include "types.h"

/// @brief Journal de la FIN DE ROUND sur un etage ajoute, dans `fin-de-round.log`.
///
/// Pose pour eprouver une hypothese de Frederic : `effd3`, l'effet d'aube, est neutralise
/// sur nos etages (deux gardes, `effect_D3_init` et `effect_D3_move`) parce qu'il
/// s'approprie le plan 3 -- or c'est notre quatrieme plan de fond. La question est de
/// savoir si cette suppression casse la sequence de fin de round, qui plante.
///
/// On note quatre choses, et elles suffisent a trancher :
///   1. l'appel a `effect_D3_init` et s'il a ete supprime ;
///   2. chaque `Bg_On_R` / `Bg_Off_R` avec son masque, pour voir si un plan s'eteint ;
///   3. le moment ou `Conclusion_Flag` passe a 1 -- c'est ce qui conclut le round ;
///   4. l'echec de `get_mltbuf16_ext` / `get_mltbuf32_ext`, ou le moteur part en
///      `while (1)`. C'est la que le jeu se fige physiquement.
///
/// Le journal est remis a zero au premier appel de chaque lancement.
void TraceFin(const char* fmt, s32 a, s32 b, s32 c);

#endif // PORT_VIDEO_TRACE_FIN_H
