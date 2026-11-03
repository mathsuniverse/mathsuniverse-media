"""Hat-style families on the silver kite grid, searched completely (not sampled).

A family is a closed outline with edge directions k*45 deg (the same turn sequences as research/families): edges in axis
directions have length A, edges in diagonal directions length B. The hat is Tile(1, sqrt3) built from its kite's two sides;
the silver analogue uses the silver kite's sides and their sums: A, B in {1, 2, 1+sqrt2, 2+sqrt2, 2+2sqrt2}.
For every family, every (A, B) pair and every grid vertex as starting point, the outline is kept when it is exactly a union
of silver-kite-grid cells (all corners are grid vertices, cell areas add up to the polygon area exactly in Q(sqrt2)) and has
the grid's balance (2 kites per square). Every such shape is sieved (STUCK / PERIODIC / OPEN, certificates)."""
import math
from fractions import Fraction as Fr

import engine as E
import grids as G
from grids import Q

R2 = math.sqrt(2.0)
DIRS = [(1, 0), (1, 1), (0, 1), (-1, 1), (-1, 0), (-1, -1), (0, -1), (1, -1)]
LENGTHS = {'1': Q(1), '2': Q(2), 'd': Q(1, 1, 2), '1+d': Q(2, 1, 2), '2d': Q(2, 2, 2)}   # d = 1+sqrt2 (silver)
HALF = Q(0, Fr(1, 2), 2)                    # sqrt2 / 2


class Ctx:
    def __init__(self, W=6):
        g = G.get('silverkite')
        self.g = g
        cells = [(i, j, t) for i in range(-W, W + 1) for j in range(-W, W + 1) for t in range(g.m)]
        self.vkey = set()
        self.starts = {}
        for c in cells:
            for v in g.cell_vertices(c):
                fk = (round(float(v[0]), 6), round(float(v[1]), 6))
                self.vkey.add(fk)
                if c[0] == 0 and c[1] == 0:
                    self.starts[fk] = v
        self.starts = list(self.starts.values())     # vertex classes of one lattice cell
        self.W = W


def vec(k, L):
    dx, dy = DIRS[k]
    if k % 2 == 0:
        return (L * dx, L * dy)
    return (L * HALF * dx, L * HALF * dy)


def outline(seq, A, B, start):
    pts = [start]
    for k in seq:
        v = vec(k, A if k % 2 == 0 else B)
        pts.append((pts[-1][0] + v[0], pts[-1][1] + v[1]))
    assert pts[-1] == pts[0]
    return pts[:-1]


def inside(x, y, poly):
    c = False
    n = len(poly)
    for i in range(n):
        x1, y1 = poly[i]; x2, y2 = poly[(i + 1) % n]
        if (y1 > y) != (y2 > y):
            if x < x1 + (y - y1) * (x2 - x1) / (y2 - y1):
                c = not c
    return c


def area_exact(pts):
    s = Q(0)
    for i in range(len(pts)):
        x0, y0 = pts[i]; x1, y1 = pts[(i + 1) % len(pts)]
        s = s + x0 * y1 - x1 * y0
    return s * Fr(1, 2)


def shape_of(ctx, seq, A, B, start):
    pts = outline(seq, A, B, start)
    fp = [(float(x), float(y)) for x, y in pts]
    if any((round(x, 6), round(y, 6)) not in ctx.vkey for x, y in fp):
        return None
    g = ctx.g
    xs = [p[0] for p in fp]; ys = [p[1] for p in fp]
    L = float(g.a1[0])
    out = []
    for i in range(int(min(xs) // L) - 1, int(max(xs) // L) + 2):
        for j in range(int(min(ys) // L) - 1, int(max(ys) // L) + 2):
            for t in range(g.m):
                cx, cy = g.area_centroid_f((i, j, t))
                if inside(cx, cy, fp):
                    out.append((i, j, t))
    if not out:
        return None
    ar = area_exact(pts)
    if float(ar) < 0:
        ar = -ar
    tot = Q(0)
    for c in out:
        tot = tot + area_exact(g.cell_vertices(c))
    if not (tot == ar or tot == -ar):
        return None
    if not E.is_connected(g, out):
        return None
    k = sum(1 for c in out if c[2] < 8)
    if k != 2 * (len(out) - k):
        return None
    return E.canonical(g, out)


def family_shapes(ctx, seq):
    found = {}
    for an, A in LENGTHS.items():
        for bn, B in LENGTHS.items():
            for s in ctx.starts:
                try:
                    sh = shape_of(ctx, seq, A, B, s)
                except AssertionError:
                    sh = None
                if sh is not None and sh not in found:
                    found[sh] = (an, bn)
    return found
