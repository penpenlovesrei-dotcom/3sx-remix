#ifndef PORT_VIDEO_JALON_H
#define PORT_VIDEO_JALON_H

#include "types.h"

/// @brief Ou la trame en cours s'arrete, quand elle ne se termine pas.
///
/// LE PROBLEME QUE CECI RESOUT. Le gel des etages de New Generation ne dit rien : pas de
/// `fatal_error`, pas de `fatal.log`, pas de trace de pile. Le battement de `sdl_app.c` a
/// etabli le fait -- la boucle de trame s'arrete net APRES le chargement complet du decor
/// -- mais pas l'endroit, et aucun debogueur n'est installe sur cette machine.
///
/// Les `while (1) {}` de `mtrans.c` sont tous ecartes : ils sont precedes d'un `flLogOut`,
/// qui ecrit `fatal.log` et TUE le jeu. Aucun `fatal.log` n'est produit. Le gel est donc
/// une boucle d'attente ordinaire, sans message.
///
/// LE JOURNAL EST REECRIT A CHAQUE TRAME. Une trace continue noierait l'information sous
/// des milliers de trames saines. Ici le fichier ne contient jamais qu'UNE trame, et les
/// deux fichiers alternent :
///
///     jalons-a.log / jalons-b.log
///
/// Au gel, l'un porte la trame INCOMPLETE -- son dernier jalon est le dernier point
/// atteint -- et l'autre une trame normale entiere, qui sert de temoin : c'est en
/// comparant les deux qu'on voit ou la seconde s'arrete.
///
/// Rien n'est ecrit tant que `Jalon_Armer` n'a pas vu un etage ajoute, pour ne pas ralentir
/// les menus ni user le disque.
void Jalon_Armer(s32 etage);

/// @brief Ouvre la trame suivante : bascule de fichier et repart d'un fichier vide.
void Jalon_Trame(s32 numero);

/// @brief Note un point de passage. Vidage a chaque ligne : un gel n'emporte rien.
void Jalon(const char* nom, s32 a);

#endif // PORT_VIDEO_JALON_H
