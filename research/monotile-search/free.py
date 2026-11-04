"""Free-placement tiling engine for equilateral polygons with edges in N directions (N = 8: silver, N = 12: the Spectre).

No grid: tile corners live in the module Z[zeta_N] (rank 4 for N = 8 and N = 12), stored exactly as 4 integers
(coefficients of 1, z, z^2, z^3). A tile is a cyclic list of edge directions d_i (edge i = z^{d_i}, unit length).
A placement is x -> z^r * conj^f(x) + t. Tilings are edge-to-edge (every edge of a tile is an edge of exactly one neighbour).

Tests (as in engine.py, with certificates):
  cover(tile, R, mirror)   SAT: a patch around a fixed seed tile in which every tile edge within distance R of the
                           origin is shared by a second tile, no overlaps. UNSAT => STUCK (no tiling contains the seed).
  periodic(tile, ...)      SAT on a torus R^2 / Lambda, Lambda spanned by two module vectors: SAT => PERIODIC certificate.
"""
from __future__ import annotations

import math
from functools import lru_cache
from itertools import product

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Solver
from shapely.geometry import Polygon
import shapely


def _inter_area(pa, pb):
    """Area of the intersection; on rare GEOS topology errors (nearly collinear overlapping edges) retry on a 1e-9 grid."""
    try:
        return pa.intersection(pb).area
    except Exception:
        return shapely.set_precision(pa, 1e-9).intersection(shapely.set_precision(pb, 1e-9)).area



def _pinched(pts, eps=1e-9):
    """True when a corner touches a non-adjacent edge (a pinched outline: not a disc, and it breaks GEOS)."""
    import math as _m
    m = len(pts)
    for i, p in enumerate(pts):
        for j in range(m):
            if i == j or i == (j + 1) % m:
                continue
            a, b = pts[j], pts[(j + 1) % m]
            dx, dy = b[0] - a[0], b[1] - a[1]
            t = max(0.0, min(1.0, ((p[0] - a[0]) * dx + (p[1] - a[1]) * dy) / (dx * dx + dy * dy)))
            if _m.hypot(p[0] - a[0] - t * dx, p[1] - a[1] - t * dy) < eps:
                return True
    return False


# ---------------------------------------------------------------- the module Z[zeta_N]

class Ring:
    # z^4 in the basis 1, z, z^2, z^3 (minimal polynomial of the primitive N-th root of unity, degree 4)
    Z4 = {8: (-1, 0, 0, 0),            # x^4 + 1
          10: (-1, 1, -1, 1),          # x^4 - x^3 + x^2 - x + 1
          12: (-1, 0, 1, 0)}           # x^4 - x^2 + 1

    def __init__(self, N):
        assert N in self.Z4
        self.N = N
        p = [(1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1)]
        for k in range(4, N):
            p.append(self.mulz(p[k - 1]))
        self.pow = p
        self.cs = [(math.cos(2 * math.pi * k / N), math.sin(2 * math.pi * k / N)) for k in range(4)]
        # rotation by z^r and conjugation as integer matrices acting on coefficient vectors
        self.rot = [self._mat(lambda k, r=r: self.pow[(k + r) % N]) for r in range(N)]
        self.conj = self._mat(lambda k: self.pow[(-k) % N])

    def mulz(self, a):
        """a * z:  a0 z + a1 z^2 + a2 z^3 + a3 z^4, with z^4 from the minimal polynomial."""
        a0, a1, a2, a3 = a
        c = self.Z4[self.N]
        return (a3 * c[0], a0 + a3 * c[1], a1 + a3 * c[2], a2 + a3 * c[3])

    def _mat(self, img):
        cols = [img(k) for k in range(4)]                  # image of basis vector z^k
        return tuple(tuple(cols[k][i] for k in range(4)) for i in range(4))

    def unit_sum(self, ks):
        """sum of z^k for k in ks, as a module element (e.g. [1, -1] -> 2cos(2pi/N))."""
        out = (0, 0, 0, 0)
        for k in ks:
            out = self.add(out, self.pow[k % self.N])
        return out

    @staticmethod
    def apply(M, a):
        return tuple(sum(M[i][k] * a[k] for k in range(4)) for i in range(4))

    @staticmethod
    def add(a, b):
        return tuple(x + y for x, y in zip(a, b))

    @staticmethod
    def sub(a, b):
        return tuple(x - y for x, y in zip(a, b))

    def f(self, a):
        return (sum(a[k] * self.cs[k][0] for k in range(4)), sum(a[k] * self.cs[k][1] for k in range(4)))

    def transform(self, a, r, fl, t):
        if fl:
            a = self.apply(self.conj, a)
        return self.add(self.apply(self.rot[r], a), t)


# ---------------------------------------------------------------- tiles and placements

class Tile:
    def __init__(self, ring, dirs, lens=None):
        """dirs: edge directions (multiples of 360/N); lens: edge lengths as elements of Z[zeta_N] (default all 1),
        e.g. sqrt3 = z + z^-1 in Z[zeta_12], phi = 1 + z + z^-1 in Z[zeta_10], sqrt2 = z + z^-1 in Z[zeta_8]."""
        self.R = ring
        self.dirs = tuple(d % ring.N for d in dirs)
        self.lens = tuple(lens) if lens else tuple((1, 0, 0, 0) for _ in self.dirs)
        v = [(0, 0, 0, 0)]
        for d, L in zip(self.dirs, self.lens):
            v.append(ring.add(v[-1], ring.apply(ring.rot[d], L)))
        assert v[-1] == (0, 0, 0, 0), 'outline does not close'
        self.verts = v[:-1]
        self.m = len(self.verts)
        P = Polygon([ring.f(x) for x in self.verts])
        assert P.is_valid and P.area > 0, 'not a simple counter-clockwise polygon'
        assert not _pinched([ring.f(x) for x in self.verts]), 'not a simple polygon (pinched)'
        self.area = P.area
        self.diam = max(math.dist(ring.f(a), ring.f(b)) for a in self.verts for b in self.verts)

    def placed(self, r, fl, t):
        vs = [self.R.transform(x, r, fl, t) for x in self.verts]
        if fl:
            vs = vs[::-1]               # keep counter-clockwise order
        return tuple(vs)


def edges_of(vs):
    return [(vs[i], vs[(i + 1) % len(vs)]) for i in range(len(vs))]


class Placements:
    """Placements generated edge-to-edge outward from the seed, with an overlap cache keyed by relative position."""

    def __init__(self, tile, mirror):
        self.T = tile
        self.mirror = mirror
        self.R = tile.R
        self._ov = {}

    def attach(self, e):
        """All placements having the directed edge e reversed as one of their (counter-clockwise) edges."""
        a, b = e                        # neighbour must contain edge b -> a
        out = []
        R = self.R
        for fl in ((0, 1) if self.mirror else (0,)):
            for j in range(self.T.m):
                for r in range(R.N):
                    vs = self.T.placed(r, fl, (0, 0, 0, 0))
                    # edge j of the placed polygon (ccw indexing)
                    p, q = vs[j], vs[(j + 1) % len(vs)]
                    if R.sub(q, p) != R.sub(a, b):
                        continue
                    t = R.sub(b, p)
                    out.append((r, fl, t))
        return out

    def overlap(self, A, B):
        """Do placements A, B (r, fl, t) overlap in their interiors? Cached by the relative transform."""
        R = self.R
        va = self.T.placed(*A); vb = self.T.placed(*B)
        key = (A[0], A[1], B[0], B[1], R.sub(B[2], A[2]))
        if key not in self._ov:
            pa = Polygon([R.f(x) for x in va]); pb = Polygon([R.f(x) for x in vb])
            if pa.distance(pb) > 1e-9:
                self._ov[key] = False
            else:
                self._ov[key] = _inter_area(pa, pb) > 1e-7
        return self._ov[key]


def _amo(lits, pool, clauses):
    if len(lits) > 1:
        clauses.extend(CardEnc.atmost(lits, 1, vpool=pool, encoding=EncType.seqcounter).clauses)


def cover(tile, Rad, mirror=True, return_patch=False, max_place=60000):
    """Patch around the seed tile (r=0, no mirror, t=0) with every edge within distance Rad of the origin matched."""
    R = tile.R
    P = Placements(tile, mirror)
    seed = (0, 0, (0, 0, 0, 0))
    key = lambda pl: frozenset(tile.placed(*pl))
    places = {key(seed): seed}
    frontier = [seed]
    lim = Rad + tile.diam + 1e-9
    while frontier:
        new = []
        for pl in frontier:
            for e in edges_of(tile.placed(*pl)):
                mx = R.f(e[0])
                if math.hypot(*mx) > lim:
                    continue
                for q in P.attach(e):
                    k = key(q)
                    if k not in places:
                        c = R.f(q[2])
                        if math.hypot(*c) <= lim + tile.diam:
                            places[k] = q
                            new.append(q)
        frontier = new
        if len(places) > max_place:
            raise RuntimeError('too many placements')
    keys = list(places)
    idx = {k: i + 1 for i, k in enumerate(keys)}
    pl = [places[k] for k in keys]
    verts = [tile.placed(*q) for q in pl]
    # edge -> placements containing it
    by_edge = {}
    for i, vs in enumerate(verts, start=1):
        for a, b in edges_of(vs):
            by_edge.setdefault(frozenset((a, b)), []).append(i)
    clauses = [[idx[key(seed)]]]
    pool = IDPool(start_from=len(pl) + 1)
    # no overlaps: spatial hash on centroids
    cent = [Polygon([R.f(x) for x in vs]).centroid for vs in verts]
    cell = tile.diam
    grid = {}
    for i, c in enumerate(cent, start=1):
        grid.setdefault((int(c.x // cell), int(c.y // cell)), []).append(i)
    for (gx, gy), lst in grid.items():
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for j in grid.get((gx + dx, gy + dy), ()):
                    for i in lst:
                        if i < j and P.overlap(pl[i - 1], pl[j - 1]):
                            clauses.append([-i, -j])
    # every edge near the origin of a chosen tile is shared by another chosen tile
    for i, vs in enumerate(verts, start=1):
        for a, b in edges_of(vs):
            mid = R.f(R.add(a, b)); d = math.hypot(mid[0] / 2, mid[1] / 2)
            if d <= Rad:
                others = [j for j in by_edge[frozenset((a, b))] if j != i]
                clauses.append([-i] + others)
    with Solver(name='cadical153', bootstrap_with=clauses) as s:
        ok = s.solve()
        model = s.get_model() if ok else None
    if not return_patch:
        return ok
    chosen = [pl[v - 1] for v in model if 0 < v <= len(pl)] if ok else None
    return ok, chosen


# ---------------------------------------------------------------- periodic tilings on a torus

def _det(R, a, b):
    (x1, y1), (x2, y2) = R.f(a), R.f(b)
    return x1 * y2 - x2 * y1


def period_pairs(tile, max_tiles, max_len):
    """Pairs of module vectors (p1, p2), lengths <= max_len, spanning a cell whose area is k * tile area, k <= max_tiles."""
    R = tile.R
    vecs = {(0, 0, 0, 0)}
    # module points as sums of up to L unit vectors (BFS), with |v| <= max_len
    frontier = [(0, 0, 0, 0)]
    L = int(max_len * 2) + 2
    for _ in range(L):
        nf = []
        for v in frontier:
            for d in range(R.N):
                w = R.add(v, R.pow[d])
                if w not in vecs and math.hypot(*R.f(w)) <= max_len + 1e-9:
                    vecs.add(w); nf.append(w)
        frontier = nf
    vecs.discard((0, 0, 0, 0))
    vl = sorted(vecs, key=lambda v: math.hypot(*R.f(v)))
    out = []
    for i, a in enumerate(vl):
        for b in vl[i + 1:]:
            D = _det(R, a, b)
            if D <= 1e-9:
                continue
            k = D / tile.area
            if abs(k - round(k)) < 1e-7 and 1 <= round(k) <= max_tiles:
                out.append((round(k), a, b))
    # one entry per lattice (different bases of the same lattice are skipped), simplest first
    seen, uniq = set(), []
    out.sort(key=lambda x: (x[0], math.hypot(*R.f(x[1])) + math.hypot(*R.f(x[2]))))
    for k, a, b in out:
        lat = frozenset(v for v in (tuple(i * x + j * y for x, y in zip(a, b)) for i in range(-3, 4) for j in range(-3, 4))
                        if math.hypot(*R.f(v)) <= max_len + 1e-9)
        if lat in seen:
            continue
        seen.add(lat); uniq.append((k, a, b))
    return uniq


def torus(tile, p1, p2, mirror=True, cap_per_tile=300):
    """SAT: does the tile tile R^2 periodically with period lattice spanned by p1, p2 (edge-to-edge)?"""
    R = tile.R
    (x1, y1), (x2, y2) = R.f(p1), R.f(p2)
    det = x1 * y2 - x2 * y1

    def reduce(t):
        x, y = R.f(t)
        u = (x * y2 - x2 * y) / det
        v = (x1 * y - x * y1) / det
        a, b = math.floor(u + 1e-9), math.floor(v + 1e-9)
        return R.sub(R.sub(t, tuple(a * c for c in p1)), tuple(b * c for c in p2)), (a, b)

    def red_pl(pl):
        r, fl, t = pl
        t2, _ = reduce(t)
        return (r, fl, t2)

    P = Placements(tile, mirror)
    seed = (0, 0, (0, 0, 0, 0))
    places = {seed}
    frontier = [seed]
    kt = max(1, round(abs(det) / tile.area))
    # every tile of a k-tile torus tiling is within k-1 edge steps of the seed (the tiles of one cell form a connected
    # graph modulo the lattice), so k layers of edge attachments contain every placement such a tiling can use
    for _ in range(kt):
        new = []
        for pl in frontier:
            for e in edges_of(tile.placed(*pl)):
                for q in P.attach(e):
                    q = red_pl(q)
                    if q not in places:
                        places.add(q); new.append(q)
        frontier = new
        if len(places) > cap_per_tile * kt:
            return None                      # too many candidates: skip this lattice (reported as undecided)
    pl = sorted(places, key=lambda q: (q[0], q[1], q[2]))
    idx = {q: i + 1 for i, q in enumerate(pl)}

    def edge_key(a, b):
        """The edge modulo the lattice: shift both ends by the lattice vector that brings its midpoint into the cell."""
        x, y = R.f(R.add(a, b)); x, y = x / 2, y / 2
        u = (x * y2 - x2 * y) / det
        v = (x1 * y - x * y1) / det
        i, j = math.floor(u + 1e-9), math.floor(v + 1e-9)
        sh = tuple(i * c1 + j * c2 for c1, c2 in zip(p1, p2))
        return frozenset((R.sub(a, sh), R.sub(b, sh)))

    by_edge = {}
    for q in pl:
        for a, b in edges_of(tile.placed(*q)):
            by_edge.setdefault(edge_key(a, b), []).append(idx[q])
    clauses = [[idx[seed]]]
    # overlaps: compare each placement with lattice translates of others near it
    shifts = [tuple(a * c1 + b * c2 for c1, c2 in zip(p1, p2)) for a in (-1, 0, 1) for b in (-1, 0, 1)]
    for i, A in enumerate(pl):
        for j in range(i, len(pl)):
            B = pl[j]
            for s in shifts:
                B2 = (B[0], B[1], R.add(B[2], s))
                if i == j and s == (0, 0, 0, 0):
                    continue
                if P.overlap(A, B2):
                    clauses.append([-idx[A], -idx[B]] if i != j else [-idx[A]])
                    break
    for q in pl:
        for a, b in edges_of(tile.placed(*q)):
            lst = by_edge[edge_key(a, b)]
            if lst.count(idx[q]) >= 2:
                continue                     # matched by its own lattice translate
            others = [j for j in lst if j != idx[q]]
            clauses.append([-idx[q]] + others)
    # area: exactly k tiles per cell
    k = round(abs(det) / tile.area)
    pool = IDPool(start_from=len(pl) + 1)
    clauses += CardEnc.equals(list(range(1, len(pl) + 1)), k, vpool=pool, encoding=EncType.seqcounter).clauses
    with Solver(name='cadical153', bootstrap_with=clauses) as s:
        return s.solve()


def periodic(tile, max_tiles=12, max_len=6.0, mirror=True, budget=None):
    import time
    t0 = time.time()
    for k, a, b in period_pairs(tile, max_tiles, max_len):
        if budget and time.time() - t0 > budget:
            return None
        r = torus(tile, a, b, mirror)
        if r:
            return dict(tiles=k, p1=a, p2=b)
    return False


def classify(dirs, N, mirror=True, Rs=(2, 3, 4, 5, 6), tcap=12, plen=6.0, budget=300):
    ring = Ring(N)
    tile = Tile(ring, dirs)
    for Rad in Rs:
        if not cover(tile, Rad * tile.diam / 2, mirror):
            return dict(cls='STUCK', fail_R=Rad)
    p = periodic(tile, tcap, plen, mirror, budget)
    if p:
        return dict(cls='PERIODIC', **p)
    return dict(cls='OPEN', covered_R=Rs[-1], periodic_search='none found' if p is False else 'budget')
