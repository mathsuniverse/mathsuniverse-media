"""Hierarchy meter: in a large SAT-built patch, the ratio of unreflected to reflected copies.
For the hat this is forced to phi^4 = 6.854... in every tiling (Smith et al.); a silver tile would show a ratio in Q(sqrt2)."""
import sys, time, math
import engine as E, grids as G
from grids import normalise


def handed(g, cells):
    """normalised forms reachable without reflection."""
    out = set()
    for (k, f, _), M, tab in g.ops:
        if f == 0:
            out.add(normalise(E.transform(g, cells, (M, tab))))
    return out


def ratio(g, cells, R, inner=None):
    sh = E.Shape(g, cells)
    t = time.time()
    ok, patch, region = E.cover(sh, R, return_patch=True)
    if not ok:
        return None
    rot = handed(g, cells)
    inner = inner or R - 2
    core = set(E.disc_cells(g, inner))
    a = b = 0
    for key in patch:
        if not set(key) & core:
            continue
        if normalise(list(key)) in rot: a += 1
        else: b += 1
    return a, b, round(time.time() - t, 1)


if __name__ == '__main__':
    import polykite as PK
    g = G.get('kite')
    for R in map(int, sys.argv[1:] or ['8', '10', '12']):
        r = ratio(g, PK.hat_cells(), R)
        a, b, s = r
        print(f'hat R={R}: {a} : {b} = {a / max(b, 1):.3f}  (phi^4 = {((1+5**.5)/2)**4:.3f})  {s}s', flush=True)
