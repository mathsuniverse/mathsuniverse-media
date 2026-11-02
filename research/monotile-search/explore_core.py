"""Guided random search for monotile candidates beyond exhaustive reach (no Modal import; testable locally).

Exhaustive lists stop being affordable around n = 17 on the 45° (tetrakis) grid (476,272 shapes, ×2.6 per cell).
Here shapes of a chosen size are drawn at random by growth: start from one cell and keep adding an edge-neighbour;
a random exponent beta biases the growth toward compact blobs (beta < 0) or branchy, notched outlines (beta > 0),
which is where the hat and the turtle live. Each shape goes through the same three-outcome test as the sieve
(engine.classify), with one dovetail stage for survivors. Only OPEN shapes are returned, with counts.
"""
from __future__ import annotations

import random


def random_shape(g, n, rng):
    shape = [(0, 0, rng.randrange(g.m))]
    s = set(shape)
    beta = rng.uniform(-1.0, 2.0)
    while len(shape) < n:
        cand = {}
        for c in shape:
            for nb in g.edge_neighbours(c):
                if nb not in s:
                    cand[nb] = cand.get(nb, 0) + 1          # how many shape cells it touches
        cells = list(cand)
        w = [cand[c] ** (-beta) for c in cells]
        nb = rng.choices(cells, weights=w)[0]
        shape.append(nb); s.add(nb)
    return shape


def explore_chunk(grid, n, seed, count, tcap=12, rcap=6.0, tcap2=24, rcap2=8.0, shape_time=120):
    import engine as E, grids as G
    g = G.get(grid)
    rng = random.Random(seed)
    seen, counts, opens = set(), {'STUCK': 0, 'PERIODIC': 0, 'OPEN': 0, 'dup': 0}, []
    for _ in range(count):
        cells = random_shape(g, n, rng)
        key = E.canonical(g, cells)
        if key in seen:
            counts['dup'] += 1; continue
        seen.add(key)
        r = E.classify(g, list(key), tcap=tcap, rcap=rcap)
        if r['cls'] == 'OPEN':
            r = E.classify(g, list(key), tcap=tcap2, rcap=rcap2, tmin=r.get('tori_complete_upto') or tcap,
                           rmin=rcap, time_limit=shape_time)
        counts[r['cls']] += 1
        if r['cls'] == 'OPEN':
            opens.append(r)
    return counts, opens


if __name__ == '__main__':      # local smoke test
    import sys, json, time
    grid, n, k = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    t = time.time(); c, o = explore_chunk(grid, n, 1, k)
    print(json.dumps(c), len(o), round(time.time() - t, 1), 's')
    for r in o: print('OPEN', r['cells'])
