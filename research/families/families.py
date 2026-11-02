"""Interpolating families on the 45° grid (the hat's Tile(a,b) idea, with √2 in place of √3).

A family is a closed polygon given by a cyclic sequence of edge directions k·45° (k = 0..7). Edges in axis directions (k even)
have length a, edges in diagonal directions (k odd) have vector b·(±1,±1), i.e. length b·√2. The polygon must close for every
(a, b): axis vectors and diagonal vectors must each sum to zero. For whole numbers a, b every vertex is a grid point and every
edge runs along a grid line of the 45° (tetrakis) grid, so Tile(a,b) is a polyform we can sieve.
Hat pattern to look for: the two ends Tile(1,0) and Tile(0,1) tile periodically, and shapes in between never repeat.
"""
import sys, os, math, itertools
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/claude/mathsuniverse-media/research/monotile-search')
from shapely.geometry import Polygon, Point

DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]


def sequences(m, straight=False, first=None, max_straight=99):
    """Turn sequences of m edges (turns in {±1,±2,±3}·45°, total +8 = one full counter-clockwise turn), closing for all (a, b)."""
    out = []
    def rec(seq, d, ax, dg, ns=0):
        k = len(seq)
        rem = m - k
        if rem == 0:
            if ax == (0, 0) and dg == (0, 0) and (seq[0] - d) % 8 != 4 and (straight or seq[0] != d):
                out.append(tuple(seq))
            return
        # prune: remaining edges must be able to cancel both sums
        if abs(ax[0]) + abs(ax[1]) > rem or max(abs(dg[0]), abs(dg[1])) > rem: return
        turns = (0, 1, 2, 3, -1, -2, -3) if straight else (1, 2, 3, -1, -2, -3)
        for t in turns:
            nd = (d + t) % 8 if seq else 0
            if seq and (nd - seq[-1]) % 8 == 4: continue                 # no U-turn
            if seq and not straight and nd == seq[-1]: continue
            sflag = 1 if (seq and nd == seq[-1]) else 0
            if ns + sflag > max_straight: continue
            if first is not None and 1 <= len(seq) <= len(first) and t != first[len(seq) - 1]: continue   # split for parallel runs
            v = DIRS[nd]
            if nd % 2 == 0: rec(seq + [nd], nd, (ax[0] + v[0], ax[1] + v[1]), dg, ns + sflag)
            else: rec(seq + [nd], nd, ax, (dg[0] + v[0], dg[1] + v[1]), ns + sflag)
            if not seq: break
    rec([], 0, (0, 0), (0, 0))
    return out


def canon(seq):
    """Up to cyclic shift, rotation by 90° (keeps edge classes), reflection."""
    m = len(seq); best = None
    variants = []
    for refl in (False, True):
        s = [(-x) % 8 for x in reversed(seq)] if refl else list(seq)
        for r in (0, 2, 4, 6):
            s2 = [(x + r) % 8 for x in s]
            for c in range(m):
                variants.append(tuple(s2[c:] + s2[:c]))
    return min(variants)


def polygon(seq, a, b):
    pts = [(0, 0)]; x = y = 0
    for k in seq:
        L = a if k % 2 == 0 else b
        if L == 0: continue                         # an end of the family: that edge class collapses
        x += DIRS[k][0] * L; y += DIRS[k][1] * L
        if (x, y) != pts[-1]: pts.append((x, y))
    if pts[-1] == pts[0]: pts = pts[:-1]
    if len(pts) < 3: return None
    P = Polygon(pts)
    return P if P.is_valid and P.area > 0 else None


def cells(P):
    xs, ys = P.exterior.xy
    out = []
    for i in range(int(min(xs)) - 1, int(max(xs)) + 1):
        for j in range(int(min(ys)) - 1, int(max(ys)) + 1):
            for t, c in enumerate(((i + .5, j + 1 / 6), (i + 5 / 6, j + .5), (i + .5, j + 5 / 6), (i + 1 / 6, j + .5))):
                if P.contains(Point(c)): out.append((i, j, t))
    return out


def families(m, straight=False, first=None, max_straight=99):
    seen = set(); out = []
    for s in sequences(m, straight, first, max_straight):
        if straight and s[0] == s[-1] and max_straight < 99:
            if sum(1 for i in range(len(s)) if s[i] == s[i - 1]) > max_straight: continue   # count the wrap-around too
        c = canon(s)
        if c in seen: continue
        seen.add(c)
        # simple for a range of ratios, both edge classes present
        if not any(k % 2 for k in c) or all(k % 2 for k in c): continue
        if all(polygon(c, a, b) for a, b in ((1, 1), (1, 2), (2, 1), (1, 3), (3, 1))): out.append(c)
    return out


def disc_first(g, cs, rmax=5, tcap=8):
    """Discs first (cheap, catches jams), then the periodic search: the recheck showed tori-first wastes the time limit."""
    import engine as E_
    sh = E_.Shape(g, cs)
    for R in [r for r in (1.5, 2, 3, 4, 5, 6, 7, 8) if r <= rmax]:
        if not E_.cover(sh, R): return 'STUCK'
    return 'PERIODIC' if E_.periodic(sh, tcap) else 'OPEN'


def test_family(seq, ratios=((1, 0), (0, 1), (1, 1), (1, 2), (2, 1)), tcap=8, rcap=5):
    import grids as G, engine as E_
    g = G.get('tetrakis'); res = {}
    for a, b in ratios:
        P = polygon(seq, a, b)
        if P is None: res[(a, b)] = 'not simple'; continue
        P = P.simplify(0)
        cs = cells(P)
        if not cs or not E_.is_connected(g, cs): res[(a, b)] = 'degenerate'; continue
        res[(a, b)] = disc_first(g, cs, rcap, tcap)
    return res


if __name__ == '__main__':
    import time
    for m in range(4, int(sys.argv[1]) + 1 if len(sys.argv) > 1 else 9):
        t = time.time(); F = families(m)
        print('edges', m, 'families', len(F), round(time.time() - t, 1), 's', flush=True)
