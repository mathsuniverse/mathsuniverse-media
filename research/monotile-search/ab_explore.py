"""Targeted random search at the period threshold on the AB grid (and any grid with g.kind):
grow random shapes with exactly the balanced cell mix (e.g. 9 squares + 12 rhombi for n = 21, k = 3), test each with the
three-outcome sieve, keep OPEN shapes and near-misses."""
import random
from math import gcd


def kinds_of(g):
    return getattr(g, 'kind', None) or [0] * g.m


def target_mix(g, n):
    kd = kinds_of(g)
    c = [kd.count(t) for t in (0, 1)]
    m = sum(c); assert (n * c[0]) % m == 0, 'size not balanced'
    return [n * c[0] // m, n * c[1] // m]


def k_threshold(g, n):
    return g.m // gcd(n, g.m)


def balanced_shape(g, n, rng, mix, tries=50):
    kd = kinds_of(g)
    for _ in range(tries):
        t0 = rng.randrange(g.m)
        if mix[kd[t0]] == 0:
            continue
        shape = [(0, 0, t0)]; s = set(shape); have = [0, 0]; have[kd[t0]] += 1
        beta = rng.uniform(-1.0, 2.0)
        while len(shape) < n:
            cand = {}
            for c in shape:
                for nb in g.edge_neighbours(c):
                    if nb not in s and have[kd[nb[2]]] < mix[kd[nb[2]]]:
                        cand[nb] = cand.get(nb, 0) + 1
            if not cand:
                break
            cells = list(cand)
            nb = rng.choices(cells, weights=[cand[c] ** (-beta) for c in cells])[0]
            shape.append(nb); s.add(nb); have[kd[nb[2]]] += 1
        if len(shape) == n:
            return shape
    return None


def explore_chunk(grid, n, seed, count, tcap=12, rcap=6.0, tcap2=24, rcap2=8.0, shape_time=120, near_R=4):
    import engine as E, grids as G
    g = G.get(grid)
    rng = random.Random(seed)
    mix = target_mix(g, n)
    seen, counts, opens, near = set(), {'STUCK': 0, 'PERIODIC': 0, 'OPEN': 0, 'dup': 0, 'nogrow': 0}, [], []
    for _ in range(count):
        cells = balanced_shape(g, n, rng, mix)
        if cells is None:
            counts['nogrow'] += 1; continue
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
        elif r['cls'] == 'STUCK' and (r.get('fail_R') or 0) >= near_R:
            near.append(r)
    return counts, opens, near


if __name__ == '__main__':
    import sys, time, json, grids as G
    grid, n, k = sys.argv[1], int(sys.argv[2]), int(sys.argv[3])
    g = G.get(grid)
    print('mix', target_mix(g, n), 'k', k_threshold(g, n), flush=True)
    t = time.time(); c, o, nr = explore_chunk(grid, n, 1, k)
    print(json.dumps(c), 'OPEN', len(o), 'near', len(nr), round(time.time() - t, 1), 's')
