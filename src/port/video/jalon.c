#include "port/video/jalon.h"

#include <stdio.h>

static FILE* jrn = NULL;
static s32 arme = 0;
static s32 bascule = 0;
static s32 lignes = 0;

void Jalon_Armer(s32 etage) {
    /* LES JALONS NE S'ARMENT PLUS TOUT SEULS. Ils font un `fflush` par ligne -- c'est ce
       qui les rend increvables face a un gel -- mais a trois lignes par maillon de liste
       d'effets, six listes par trame, ca fait des centaines d'ecritures disque par trame
       et le jeu n'est plus jouable. On ne peut donc pas juger un decor avec.

       Ils s'arment desormais sur presence du fichier temoin `jalons.on` a cote de l'exe,
       que le lanceur de diagnostic cree et que le lanceur normal efface. Le dispositif
       reste donc entier pour le prochain defaut muet, sans peser sur les essais de rendu. */
    static s32 fichier_vu = 0;
    static s32 fichier_la = 0;

    if (!fichier_vu) {
        FILE* t = fopen("jalons.on", "r");

        fichier_vu = 1;

        if (t != NULL) {
            fichier_la = 1;
            fclose(t);
        }
    }

    /* Nos etages ajoutes commencent a 22. En dessous, on ne journalise rien : les menus
       et les etages d'origine tournent des milliers de trames pour rien. */
    if (fichier_la && etage >= 22) {
        arme = 1;
    }
}

void Jalon_Trame(s32 numero) {
    if (!arme) {
        return;
    }

    if (jrn != NULL) {
        fclose(jrn);
        jrn = NULL;
    }

    /* ALTERNANCE. Le fichier de la trame precedente survit intact pendant qu'on ecrit
       celui-ci : au gel, on a la trame morte ET une trame saine pour la comparer. */
    bascule = !bascule;
    jrn = fopen(bascule ? "jalons-a.log" : "jalons-b.log", "w");
    lignes = 0;

    if (jrn != NULL) {
        fprintf(jrn, "===== trame %d =====\n", (int)numero);
        fflush(jrn);
    }
}

void Jalon(const char* nom, s32 a) {
    if (!arme || jrn == NULL) {
        return;
    }

    /* Garde-fou : une boucle interne qui tournerait en passant par un jalon remplirait le
       disque. On plafonne, et le plafond est bien au-dessus d'une trame saine. */
    if (lignes >= 2000) {
        return;
    }

    lignes++;
    fprintf(jrn, "%s %d\n", nom, (int)a);
    fflush(jrn);
}
