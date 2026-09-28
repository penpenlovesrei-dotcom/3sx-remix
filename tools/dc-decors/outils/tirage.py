# -*- coding: ascii -*-
"""La table du tirage RANDOM : 128 entrees, nos decors compris."""
import random

ORIGINE = [n for n in range(20) if n != 17]          # 0..16, 18, 19 ; 17 est vide
DEUX_I  = list(range(22, 37))                        # les quinze ajoutes de 2nd Impact
SAUTES  = {41, 43, 45, 47, 49, 50, 52, 54}
NG      = [n for n in range(37, 56) if n not in SAUTES]

pool = ORIGINE + DEUX_I + NG
print("origine %d, 2I %d, NG %d -> %d etages" % (len(ORIGINE), len(DEUX_I), len(NG), len(pool)))

N = 128
base = pool * (N // len(pool))                       # 2 fois chacun = 90
reste = N - len(base)                                # 38 de plus
rng = random.Random(3)                               # graine fixe : la table est reproductible
base += rng.sample(pool, reste)

# Melange, puis on defait les repetitions adjacentes : deux tirages de suite ne doivent
# pas donner le meme decor.
for essai in range(10000):
    rng.shuffle(base)
    colles = [i for i in range(1, N) if base[i] == base[i-1]]
    if not colles:
        break
    for i in colles:
        j = rng.randrange(N)
        base[i], base[j] = base[j], base[i]
colles = sum(1 for i in range(1, N) if base[i] == base[i-1])
print("essais %d, repetitions adjacentes restantes : %d" % (essai + 1, colles))

from collections import Counter
c = Counter(base)
print("chaque etage sort %d ou %d fois sur 128" % (min(c.values()), max(c.values())))
assert len(c) == len(pool)
assert colles == 0

lignes = []
for i in range(0, N, 16):
    lignes.append("    " + ", ".join("%2d" % v for v in base[i:i+16]) + ",")
open(r"C:\Users\frede\AppData\Local\Temp\claude\C--Users-frede-OneDrive-Bureau-SEPTEMBRE-SEGA-Rally-2\862de502-bd3d-4929-b490-ccdb3ec15a8d\scratchpad\tirage.txt", "w").write("\n".join(lignes))
print("\n".join(lignes[:2]))
