"""Arithmetic route: Kari-style Wang tiles for any piecewise multiplicative map with rational multipliers.

A row of tiles carries the balanced representation of a real x: B(x)_i = floor(i x) - floor((i-1) x) on the top edges.
A tile multiplies by q: top a, left state s, bottom b, right state s' with  q*a + s = b + s'  (states s_i = q*floor(i x) - floor(i q x)).
The bottom edges then carry B(q x), the top of the next row. Pieces (q, interval) give one machine each; the row below is f(x).
Tiles are collected exactly (Fractions) from many x in each interval. Kari (1996): 2 on [1/2,1], 2/3 on [1,2] -> 14 tiles.
Aperiodic when no product of multipliers along a cycle is 1 (Kari; Eigen-Navarro-Prasad Thm 19).
Tile = (East, North, West, South) to match silver_wang.wang_sat.
"""
import sys, random
from fractions import Fraction as F
from math import floor


def tiles_for(pieces, samples=4000, length=60, seed=1):
    rng = random.Random(seed); out = set()
    for k, (q, lo, hi) in enumerate(pieces):
        q, lo, hi = F(q), F(lo), F(hi)
        for _ in range(samples):
            x = lo + (hi - lo) * F(rng.randrange(1, 10 ** 6), 10 ** 6)
            if x == hi: continue
            for i in range(1, length):
                a = floor(i * x) - floor((i - 1) * x); b = floor(i * q * x) - floor((i - 1) * q * x)
                s0 = q * floor((i - 1) * x) - floor((i - 1) * q * x); s1 = q * floor(i * x) - floor(i * q * x)
                assert q * a + s0 == b + s1
                out.add((('s', k, s1), ('d', a), ('s', k, s0), ('d', b)))
    return sorted(out, key=str)


KARI = [(2, F(1, 2), 1), (F(2, 3), 1, 2)]

if __name__ == '__main__':
    import silver_wang as SW, time
    T = tiles_for(KARI)
    print('Kari (2 on [1/2,1), 2/3 on [1,2)):', len(T), 'tiles')
    t = time.time()
    per = [(w, h) for w in range(1, 9) for h in range(1, 9) if SW.wang_sat(T, w, h, torus=True)]
    print('  periodic with periods <= 8x8:', per or 'none', round(time.time() - t, 1), 's')
    for n in (10, 20, 30): print(f'  {n}x{n} square:', SW.wang_sat(T, n, n) is not None)
