# -*- coding: utf-8 -*-
"""LA CARTE DES STRUCTURES DE COMBATTANT -- 23/09/2026.

Trouvee par la MULTIPLICATION. Un tableau dont la taille d'element n'est pas une puissance
de deux s'indexe par `muls.w`, pas par des decalages : en balayant les `muls.w` dont la
constante vient d'un litteral et dont une base de RAM est chargee autour, une seule adresse
ressort dans chaque binaire --

    2nd Impact       plw = 0x8C645590, 1036 octets par combattant, 60 sites
    New Generation   plw = 0x8C543EC8,  984 octets par combattant, 46 sites

et c'est la meme adresse que le balayage des champs de position avait deja signalee (lue en
`+84` et en `+102`).

LE COMBATTANT EST UN `WORK`, COMME UN SPRITE DE DECOR
-----------------------------------------------------
Les offsets cites en dur sur `plw[0]` -- 0, 3, 8, 38, 84, 88, 102, 158, 456, 554 -- sont
ceux-la memes que le chantier avait releves sur les objets de decor (`+102` x, `+106` y,
`+88` profondeur, `+456` script, `+554` couleur). Les deux familles partagent l'en-tete.

Et cet en-tete est celui de 3rd Strike, champ pour champ. La preuve est `XY` : dans
`src/structs.h` du port, `XY` fait QUATRE octets (`{s16 low; s16 pos}`, en union avec un
`s32 cal`), donc `xyz[0].disp.pos` tombe en **+102** et `xyz[1].disp.pos` en **+106**.
Ce sont exactement les offsets mesures dans les binaires Dreamcast, des semaines avant
qu'on regarde le port. (Les offsets se lisent avec clang :
`clang --target=i686-unknown-none-elf -Xclang -fdump-record-layouts -fsyntax-only`.)

    +0   s8  be_flag        existe                 +36  s16[8] routine_no   L'ETAT
    +1   s8  disp_flag      dessine                +52  s16[8] old_rno
    +2   u8  blink_timing                          +68  s16 hit_stop        LE FIGEMENT DE COUP
    +3   u8  operator                              +70  s16 hit_quake       LA SECOUSSE
    +4   u8  type                                  +72  s8  cgromtype
    +5   u8  charset_id                            +73  u8  kage_flag       l'ombre
    +6   s16 work_id                               +74..82  kage_*
    +8   s16 id             LE PERSONNAGE          +84  s16 position_x
    +10  s8  rl_flag        LE SENS                +86  s16 position_y
    +11  s8  rl_waza                               +88  s16 position_z
    +12  void* target_adrs  L'ADVERSAIRE           +90..94  next_x/y/z
    +16  void* hit_adrs     CE QUI L'A TOUCHE      +96  s16 scr_mv_x
    +20  void* dmg_adrs     CE QUI L'A BLESSE      +98  s16 scr_mv_y
    +24  s16 before         chainage               +100 XY[3] xyz
    +26  s16 myself         son indice             +102     xyz[0].pos  X
    +28  s16 behind                                +106     xyz[1].pos  Y
    +30  s16 listix         sa liste (0..7)        +110     xyz[2].pos  Z
    +32  s16 dead_f                                +112 s16[3] old_pos
    +34  s16 timing                                +118 s16 sync_suzi

Au-dela de ~170 les deux moteurs divergent (3rd Strike a insere des champs) : les offsets
qui valent pour la Dreamcast sont ceux que ce chantier a mesures --

    +364  la table des scripts (`char_table`)      +454 numero de table
    +448  le script courant                        +456 numero de script
    +554  code couleur   +556 profondeur           +558 plan

LE TAS DES ACTEURS
------------------
Une seule famille de 2 048 octets dans chaque binaire, et c'est la seule :

    2I  0x8C6466EC .. 0x8C6866EB   128 places      NG  0x8C554668 .. 0x8C574667
        0x8C6866F0  la pile des places libres (128 u16)
        0x8C6867F0  le nombre de places libres
        0x8C6867F2 + 2*liste   la tete des HUIT listes    0x8C686802 + 2*liste  la queue
        0x8C0217E4  le tireur de place                    NG 0x8C09AFA4

Les combattants, eux, ne sont PAS dans ce tas : ils ont leur propre tableau `plw`.

    python combattants.py           la carte, et qui lit les combattants
"""
import collections
import os
import struct
import sys

ICI = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, ICI)

PLW = {"2I": (0x8C645590, 1036), "NG": (0x8C543EC8, 984)}
TAS = {"2I": (0x8C6466EC, 128), "NG": (0x8C554668, 128)}
POSEUR = {"2I": 0x8C0B4AD4, "NG": 0x8C03324C}
CODE = {"2I": (0x8C020000, 0x8C04C000), "NG": (0x8C090000, 0x8C0C0000)}

NOMS = {0: "be_flag", 1: "disp_flag", 2: "blink_timing", 3: "operator", 4: "type",
        5: "charset_id", 6: "work_id", 8: "id (le personnage)", 10: "rl_flag (le sens)",
        11: "rl_waza", 12: "target_adrs (l'adversaire)", 16: "hit_adrs",
        20: "dmg_adrs", 24: "before", 26: "myself", 28: "behind", 30: "listix",
        32: "dead_f", 34: "timing", 68: "hit_stop (figement de coup)",
        70: "hit_quake (secousse)", 84: "position_x", 86: "position_y",
        88: "position_z", 96: "scr_mv_x", 98: "scr_mv_y",
        102: "xyz[0].pos  X", 106: "xyz[1].pos  Y", 110: "xyz[2].pos  Z",
        118: "sync_suzi", 364: "char_table (les tables de scripts)",
        448: "le script courant", 454: "numero de table", 456: "numero de script",
        554: "code couleur", 556: "profondeur", 558: "plan"}


def nom_du_champ(o):
    if 36 <= o < 52:
        return "routine_no[%d]  L'ETAT" % ((o - 36) // 2)
    if 52 <= o < 68:
        return "old_rno[%d]" % ((o - 52) // 2)
    if 364 <= o < 412:
        return "char_table[%d]" % ((o - 364) // 4)
    return NOMS.get(o, "")


def champs_cites(mod, base, taille):
    """Les offsets de `base` cites en dur dans le binaire."""
    c = collections.Counter()
    for o in range(0, len(mod.D) - 4, 4):
        v = struct.unpack_from("<I", mod.D, o)[0]
        if base <= v < base + taille:
            c[v - base] += 1
    return c


def lecteurs(mod, base, taille, code):
    """Les routines de `code` qui portent une adresse de combattant en dur."""
    out = collections.defaultdict(list)
    for o in range(0, len(mod.D) - 4, 4):
        v = struct.unpack_from("<I", mod.D, o)[0]
        if not (base <= v < base + taille):
            continue
        lit = mod.o2a(o)
        for b in range(max(code[0], lit - 0x400), lit, 2):
            w = mod.u16(mod.a2o(b))
            if w >> 12 == 0xD and ((b + 4) & ~3) + (w & 0xFF) * 4 == lit:
                if code[0] <= b < code[1]:
                    out[v - base].append(b)
                break
    return out


def main():
    import sh4
    import sh4ng
    mods = {"2I": sh4, "NG": sh4ng}
    for nom in ("2I", "NG"):
        mod = mods[nom]
        base, taille = PLW[nom]
        print("=" * 78)
        print("%s : plw = 0x%08X, %d octets par combattant" % (nom, base, taille))
        print("=" * 78)
        for o, n in sorted(champs_cites(mod, base, taille).items()):
            print("   +%-4d  %3d litteral(aux)   %s" % (o, n, nom_du_champ(o)))
        lus = lecteurs(mod, base, taille, CODE[nom])
        if lus:
            print("\n   CE QUE LES ACTEURS DE DECOR LISENT D'UN COMBATTANT :")
            for o, sites in sorted(lus.items()):
                print("      +%-4d %-28s  %d routine(s) : %s"
                      % (o, nom_du_champ(o), len(sites),
                         " ".join("%08X" % s for s in sites[:8])))
        print()


if __name__ == "__main__":
    main()
