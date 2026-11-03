"""Enumeration with a composition cap: on the silver kite grid a tiling needs kites = 2 x squares, so for size N = 3q we
only need shapes with exactly 2q kites and q squares. Every sub-shape met while growing has kites <= 2q and squares <= q
(a polyform loses a leaf cell at a time), so capping each level is exact."""
import time
import engine as E


def kinds(g, cells):
    k = sum(1 for c in cells if c[2] < g.nbig)
    return k, len(cells) - k


def enumerate_capped(g, N, verbose=True):
    q = N // 3
    K, S = 2 * q, q
    level = sorted({E.canonical(g, [(0, 0, t)]) for t in range(g.m)})
    for n in range(2, N + 1):
        t0 = time.time(); new = set()
        for p in level:
            s = set(p); k0, s0 = kinds(g, p); tried = set()
            for c in p:
                for nb in g.edge_neighbours(c):
                    if nb in s or nb in tried:
                        continue
                    tried.add(nb)
                    if (nb[2] < g.nbig and k0 + 1 > K) or (nb[2] >= g.nbig and s0 + 1 > S):
                        continue
                    new.add(E.canonical(g, p + (nb,)))
        level = sorted(new)
        if verbose:
            print(f'  n={n}: {len(level)}  ({time.time() - t0:.1f}s)', flush=True)
    return [p for p in level if kinds(g, p) == (K, S)]


if __name__ == '__main__':
    import sys, grids as G
    g = G.get(sys.argv[2] if len(sys.argv) > 2 else 'silverkite')
    N = int(sys.argv[1])
    out = enumerate_capped(g, N)
    print(N, 'with', 2 * (N // 3), 'kites +', N // 3, 'squares:', len(out), 'symmetry classes')
