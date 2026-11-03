"""Ammann-Beenker cells on the [4.8.8] grid with edge 3: every regular octagon (side 3) is filled with unit squares and
45-degree rhombi (a rhombic tiling of the zonogon: 18 squares + 36 rhombi), every square (side 3) with 9 unit squares.
Per lattice cell: 27 squares + 36 rhombi; the counts share the factor 9, so the period threshold k = 3 is reachable
(balanced shapes of 21 cells = 9 squares + 12 rhombi). The octagon filling is chosen by search for maximal symmetry."""
import random
from fractions import Fraction as Fr
from grids import Q, S2


H = S2 * Fr(1, 2)
E4 = [(Q(1), Q(0)), (H, H), (Q(0), Q(1)), (-H, H)]          # edge directions 0, 45, 90, 135 deg


def add(p, v, k=1):
    return (p[0] + v[0] * k, p[1] + v[1] * k)


def zonogon_tiling(s, rng):
    """Rhombic tiling of the octagon with s edges in each direction: sort the word 0^s 1^s 2^s 3^s into 3^s 2^s 1^s 0^s
    by random adjacent swaps; each swap 'ij' -> 'ji' at path position p lays the parallelogram (e_i, e_j) there."""
    w = [d for d in range(4) for _ in range(s)]
    start = (Q(0), Q(0))
    tiles = []
    while True:
        pos = [p for p in range(len(w) - 1) if w[p] < w[p + 1]]
        if not pos:
            break
        p = rng.choice(pos)
        base = start
        for d in w[:p]:
            base = add(base, E4[d])
        i, j = w[p], w[p + 1]
        a, b, c = base, add(base, E4[i]), add(add(base, E4[i]), E4[j])
        tiles.append([a, b, c, add(base, E4[j])])
        w[p], w[p + 1] = j, i
    return tiles


def _key(pt):
    return (pt[0].a, pt[0].b, pt[1].a, pt[1].b)


def symmetry_score(tiles, centre):
    from grids import rot8, matmul, REFL, lin, psub, padd
    S = {frozenset(_key(v) for v in t) for t in tiles}
    score = 0
    for f in (0, 1):
        for k in range(8):
            L = matmul(rot8(k), REFL) if f else rot8(k)
            img = {frozenset(_key(padd(lin(L, psub(v, centre)), centre)) for v in t) for t in tiles}
            score += img == S
    return score


def best_octagon(s=3, tries=3000, seed=7):
    rng = random.Random(seed)
    best = None
    for _ in range(tries):
        t = zonogon_tiling(s, rng)
        # centre of the octagon: start + (sum of all edge vectors * s)/2 along the lower path
        c = (Q(0), Q(0))
        for d in range(4):
            c = add(c, E4[d], s)
        centre = (c[0] * Fr(1, 2), c[1] * Fr(1, 2))
        sc = symmetry_score(t, centre)
        if best is None or sc > best[0]:
            best = (sc, t, centre)
    return best


def make_abgrid(s=3, tries=3000, seed=7):
    import grids as G
    sc, tiles, centre = best_octagon(s, tries, seed)
    w = Q(s, s, 2)                                     # octagon width s(1+sqrt2) = lattice spacing
    P1 = (Q(s), Q(0)); P2 = add(P1, E4[1], s)
    u, v = E4[1], (H, -H)
    sq_cells = []
    for a in range(s):
        for b in range(s):
            p = add(add(P1, u, a), v, b)
            sq_cells.append([p, add(p, v), add(add(p, u), v), add(p, u)])
    def is_square(t):
        d1 = (t[1][0] - t[0][0], t[1][1] - t[0][1]); d2 = (t[3][0] - t[0][0], t[3][1] - t[0][1])
        return d1[0] * d2[0] + d1[1] * d2[1] == 0
    squares = [t for t in tiles if is_square(t)] + sq_cells
    rhombi = [t for t in tiles if not is_square(t)]
    protos = squares + rhombi
    g = G.Grid('ab', ((w, Q(0)), (Q(0), w)), protos, '[4.8.8] side %d, AB-filled' % s, 'AB square / rhombus',
               notes='octagon (side %d) filled with %d squares + %d rhombi (symmetry score %d); square with %d unit squares'
                     % (s, len(squares) - s * s, len(rhombi), sc, s * s), cands=G.CANDIDATE_L8)
    g.kind = [0] * len(squares) + [1] * len(rhombi)
    return g
