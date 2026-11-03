"""Free-placement tiling search by backtracking (no grid): equilateral tiles with edges in N directions (N = 8 silver, 12 Spectre).

Exact: corners are elements of Z[zeta_N] stored as 4 integers (free.Ring). Tilings are edge-to-edge.
cover(R): grow a patch from a fixed seed tile, always filling the open edge (nearest the origin, fewest options) until no open
edge lies within distance R of the origin; backtrack on dead ends. Pruning: at every corner the angles (whole units of 360/N)
must sum to <= N and the remaining gap must be a sum of the tile's corner angles; tiles must not overlap (exact relative-position
cache, shapely area test). Exhausting the search = STUCK certificate (up to the node limit, reported).
Periodic tilings: free.torus over period lattices whose translates do not overlap the tile.
"""
from __future__ import annotations

import math
import time

from shapely.geometry import Polygon

import free as F


class Search:
    def __init__(self, dirs, N, mirror=True):
        self.ring = R = F.Ring(N)
        self.N = N
        self.tile = T = F.Tile(R, dirs)
        self.mirror = mirror
        m = T.m
        # corner angles in units of 360/N (interior angle at vertex j between edge j-1 and edge j)
        self.ang = []
        for j in range(m):
            tau = (T.dirs[j] - T.dirs[j - 1]) % N
            if tau > N // 2:
                tau -= N
            self.ang.append(N // 2 - tau)
        sums = {0}
        for _ in range(N):
            sums |= {s + a for s in sums for a in self.ang if s + a <= N}
        self.gapok = sums
        # orientations: (r, fl) -> ccw vertex list at t = 0 and corner angles in that order
        self.orients = []
        for fl in ((0, 1) if mirror else (0,)):
            for r in range(N):
                vs = list(T.placed(r, fl, (0, 0, 0, 0)))
                # T.placed reverses the vertex order for mirrored tiles: vertex k of vs is original vertex m-1-k
                angs = list(self.ang) if not fl else [self.ang[m - 1 - k] for k in range(m)]
                self.orients.append((r, fl, vs, angs))
        # edge vector -> [(orient index, k)] : edge k of that orientation has this vector
        self.by_vec = {}
        for oi, (r, fl, vs, angs) in enumerate(self.orients):
            for k in range(m):
                v = R.sub(vs[(k + 1) % m], vs[k])
                self.by_vec.setdefault(v, []).append((oi, k))
        self.base_poly = Polygon([R.f(x) for x in T.verts])
        self._ov = {}
        self.diam = T.diam

    # -------------------------------------------------------------- geometry helpers
    def verts(self, pl):
        oi, t = pl
        return [self.ring.add(x, t) for x in self.orients[oi][2]]

    def inv_frame(self, pl, x):
        """Coordinates of point x in the frame of placement pl (exact)."""
        R = self.ring
        oi, t = pl
        r, fl = self.orients[oi][0], self.orients[oi][1]
        y = R.apply(R.rot[(-r) % self.N], R.sub(x, t))
        if fl:
            y = R.apply(R.conj, y)
        return y

    def overlaps(self, A, B):
        """Interior overlap of two placements; cached by (orientation A, orientation B, translation difference)."""
        R = self.ring
        key = (A[0], B[0], R.sub(B[1], A[1]))
        v = self._ov.get(key)
        if v is None:
            pa = Polygon([R.f(x) for x in self.orients[A[0]][2]])
            pb = Polygon([R.f(R.add(x, key[2])) for x in self.orients[B[0]][2]])
            v = (pa.distance(pb) < 1e-9) and pa.intersection(pb).area > 1e-7
            self._ov[key] = v
        return v

    # -------------------------------------------------------------- the search
    def cover(self, Rad, node_limit=200000, time_limit=None):
        R = self.ring
        m = self.tile.m
        placed = []                 # list of (oi, t)
        edges = {}                  # directed edge (a, b) -> placement index
        corner = {}                 # point -> angle units filled
        cells = {}                  # spatial hash -> placement indices
        cs = self.diam
        self.nodes = 0
        t0 = time.time()

        def centre(pl):
            vs = self.verts(pl)
            xs = [R.f(x) for x in vs]
            return (sum(p[0] for p in xs) / m, sum(p[1] for p in xs) / m)

        def can_place(pl):
            vs = self.verts(pl)
            angs = self.orients[pl[0]][3]
            for k in range(m):
                a, b = vs[k], vs[(k + 1) % m]
                if (a, b) in edges:          # same directed edge already used by another tile: overlap
                    return False
                tot = corner.get(a, 0) + angs[k]
                if tot > self.N or (self.N - tot) not in self.gapok:
                    return False
            cx, cy = centre(pl)
            gx, gy = int(cx // cs), int(cy // cs)
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    for i in cells.get((gx + dx, gy + dy), ()):
                        if self.overlaps(placed[i], pl):
                            return False
            return True

        def do(pl):
            i = len(placed)
            placed.append(pl)
            vs = self.verts(pl)
            angs = self.orients[pl[0]][3]
            for k in range(m):
                edges[(vs[k], vs[(k + 1) % m])] = i
                corner[vs[k]] = corner.get(vs[k], 0) + angs[k]
            cx, cy = centre(pl)
            cells.setdefault((int(cx // cs), int(cy // cs)), []).append(i)

        def undo():
            i = len(placed) - 1
            pl = placed.pop()
            vs = self.verts(pl)
            angs = self.orients[pl[0]][3]
            for k in range(m):
                del edges[(vs[k], vs[(k + 1) % m])]
                corner[vs[k]] -= angs[k]
                if corner[vs[k]] == 0:
                    del corner[vs[k]]
            cx, cy = centre(pl)
            cells[(int(cx // cs), int(cy // cs))].remove(i)

        def options(e):
            a, b = e                         # need a tile with directed edge b -> a
            out = []
            for oi, k in self.by_vec.get(R.sub(a, b), ()):
                p = self.orients[oi][2][k]
                t = R.sub(b, p)
                pl = (oi, t)
                if can_place(pl):
                    out.append(pl)
            return out

        def open_edges():
            res = []
            for (a, b) in edges:
                if (b, a) not in edges:
                    mx, my = R.f(R.add(a, b))
                    d = math.hypot(mx, my) / 2
                    if d <= Rad:
                        res.append((d, (a, b)))
            res.sort(key=lambda x: x[0])
            return [e for _, e in res]

        def rec():
            self.nodes += 1
            if self.nodes > node_limit or (time_limit and time.time() - t0 > time_limit):
                raise TimeoutError
            oe = open_edges()
            if not oe:
                return True
            best = None
            for e in oe[:6]:                 # most constrained of the nearest open edges
                op = options(e)
                if not op:
                    return False
                if best is None or len(op) < len(best):
                    best = op
                    if len(op) == 1:
                        break
            for pl in best:
                do(pl)
                if rec():
                    return True
                undo()
            return False

        seed = (0, (0, 0, 0, 0))
        do(seed)
        try:
            ok = rec()
        except TimeoutError:
            return None
        self.patch = list(placed)
        return ok

    def periodic(self, max_tiles=12, max_len=6.0, budget=120):
        """Torus search over period lattices; vectors whose translate overlaps the tile are excluded."""
        R = self.ring
        T = self.tile
        t0 = time.time()
        ok_vec = {}

        def fine(v):
            if v not in ok_vec:
                pb = Polygon([R.f(R.add(x, v)) for x in T.verts])
                ok_vec[v] = not (self.base_poly.intersection(pb).area > 1e-7)
            return ok_vec[v]
        for k, a, b in F.period_pairs(T, max_tiles, max_len):
            if time.time() - t0 > budget:
                return None
            if not (fine(a) and fine(b)):
                continue
            r = F.torus(T, a, b, self.mirror)
            if r:
                return dict(tiles=k, p1=a, p2=b)
        return False


def classify(dirs, N, mirror=True, Rs=(1.5, 2, 3, 4), node_limit=200000, tcap=12, plen=6.0, budget=120):
    S = Search(dirs, N, mirror)
    best = None
    for Rad in Rs:
        r = S.cover(Rad * S.diam / 2, node_limit=node_limit)
        if r is None:
            return dict(cls='UNDECIDED', at_R=Rad, covered_R=best)
        if not r:
            return dict(cls='STUCK', fail_R=Rad, covered_R=best)
        best = Rad
    p = S.periodic(tcap, plen, budget)
    if p:
        return dict(cls='PERIODIC', **p)
    return dict(cls='OPEN', covered_R=best, periodic='none found' if p is False else 'budget')


# ---------------------------------------------------------------- periods as short edge paths

def _hnf2(a, b):
    """Canonical form of the rank-2 subgroup of Z^4 spanned by a, b (row Hermite normal form)."""
    M = [list(a), list(b)]
    r = 0
    for c in range(4):
        rows = [i for i in range(r, 2) if M[i][c] != 0]
        if not rows:
            continue
        while True:
            rows = [i for i in range(r, 2) if M[i][c] != 0]
            if len(rows) == 1:
                break
            i, j = sorted(rows, key=lambda i: abs(M[i][c]))[:2]
            q = M[j][c] // M[i][c]
            M[j] = [x - q * y for x, y in zip(M[j], M[i])]
        i = rows[0]
        M[r], M[i] = M[i], M[r]
        if M[r][c] < 0:
            M[r] = [-x for x in M[r]]
        for i2 in range(r):
            q = M[i2][c] // M[r][c]
            M[i2] = [x - q * y for x, y in zip(M[i2], M[r])]
        r += 1
        if r == 2:
            break
    return tuple(map(tuple, M))


def period_pairs_paths(S, max_tiles=12, max_edges=6):
    """Lattices spanned by two module vectors, each a path of at most max_edges unit edges (coefficient L1 norm),
    whose translates do not overlap the tile, with cell area = k * tile area (k <= max_tiles); simplest first."""
    R = S.ring; T = S.tile
    from itertools import product
    vecs = set()
    for c in product(range(-max_edges, max_edges + 1), repeat=4):
        if 0 < sum(map(abs, c)) <= max_edges:
            vecs.add(c)
    good = []
    for v in vecs:
        pb = Polygon([R.f(R.add(x, v)) for x in T.verts])
        if not S.base_poly.intersection(pb).area > 1e-7:
            good.append(v)
    fl = {v: R.f(v) for v in good}
    best = {}
    for i, a in enumerate(good):
        xa, ya = fl[a]
        for b in good[i + 1:]:
            xb, yb = fl[b]
            D = abs(xa * yb - xb * ya)
            if D < 1e-9:
                continue
            k = D / T.area
            if abs(k - round(k)) > 1e-7 or not 1 <= round(k) <= max_tiles:
                continue
            h = _hnf2(a, b)
            L = sum(map(abs, a)) + sum(map(abs, b))
            if h not in best or L < best[h][1]:
                best[h] = (round(k), L, a, b)       # keep the shortest basis of each lattice
    out = sorted(best.values())
    return [(k, a, b) for k, _, a, b in out]


def periodic2(S, max_tiles=12, max_edges=6, budget=300):
    t0 = time.time()
    pairs = period_pairs_paths(S, max_tiles, max_edges)
    for n, (k, a, b) in enumerate(pairs):
        if time.time() - t0 > budget:
            return None, n, len(pairs)
        if F.torus(S.tile, a, b, S.mirror, cap_per_tile=60):
            return dict(tiles=k, p1=a, p2=b), n, len(pairs)
    return False, len(pairs), len(pairs)


def torus2(S, p1, p2, cap_per_tile=400):
    """Fast torus test using the Search's orientation tables and relative-frame overlap cache."""
    from pysat.card import CardEnc, EncType
    from pysat.formula import IDPool
    from pysat.solvers import Solver
    R = S.ring; m = S.tile.m
    (x1, y1), (x2, y2) = R.f(p1), R.f(p2)
    det = x1 * y2 - x2 * y1
    kt = max(1, round(abs(det) / S.tile.area))

    def lat(i, j):
        return tuple(i * a + j * b for a, b in zip(p1, p2))

    def coords(pt):
        x, y = R.f(pt)
        return (x * y2 - x2 * y) / det, (x1 * y - x * y1) / det

    def reduce_t(t):
        u, v = coords(t)
        i, j = math.floor(u + 1e-9), math.floor(v + 1e-9)
        return R.sub(t, lat(i, j))

    def red(pl):
        return (pl[0], reduce_t(pl[1]))

    def attach(a, b):
        out = []
        for oi, k in S.by_vec.get(R.sub(a, b), ()):
            out.append((oi, R.sub(b, S.orients[oi][2][k])))
        return out

    seed = (0, (0, 0, 0, 0))
    places = {seed}; frontier = [seed]
    for _ in range(kt):
        new = []
        for pl in frontier:
            vs = S.verts(pl)
            for k in range(m):
                for q in attach(vs[k], vs[(k + 1) % m]):
                    q = red(q)
                    if q not in places:
                        places.add(q); new.append(q)
        frontier = new
        if len(places) > cap_per_tile * kt:
            return None
    pl = sorted(places)
    idx = {q: i + 1 for i, q in enumerate(pl)}

    def edge_key(a, b):
        x, y = R.f(R.add(a, b)); u, v = coords(R.add(a, (0, 0, 0, 0)))
        xm, ym = x / 2, y / 2
        u = (xm * y2 - x2 * ym) / det; v = (x1 * ym - xm * y1) / det
        sh = lat(math.floor(u + 1e-9), math.floor(v + 1e-9))
        return frozenset((R.sub(a, sh), R.sub(b, sh)))

    by_edge = {}
    for q in pl:
        vs = S.verts(q)
        for k in range(m):
            by_edge.setdefault(edge_key(vs[k], vs[(k + 1) % m]), []).append(idx[q])
    clauses = [[idx[seed]]]
    # overlaps: centroids, compared with the 9 nearest lattice translates
    cen = {}
    for q in pl:
        xs = [R.f(x) for x in S.verts(q)]
        cen[q] = (sum(p[0] for p in xs) / m, sum(p[1] for p in xs) / m)
    shifts = [(i, j) for i in (-1, 0, 1) for j in (-1, 0, 1)]
    d2 = (S.diam * 1.01) ** 2
    for ia, A in enumerate(pl):
        ca = cen[A]
        for B in pl[ia:]:
            cb = cen[B]
            for (i, j) in shifts:
                if A == B and (i, j) == (0, 0):
                    continue
                L = lat(i, j); Lf = R.f(L)
                if (cb[0] + Lf[0] - ca[0]) ** 2 + (cb[1] + Lf[1] - ca[1]) ** 2 > d2:
                    continue
                if S.overlaps(A, (B[0], R.add(B[1], L))):
                    clauses.append([-idx[A], -idx[B]] if A != B else [-idx[A]])
                    break
    for q in pl:
        vs = S.verts(q)
        for k in range(m):
            lst = by_edge[edge_key(vs[k], vs[(k + 1) % m])]
            if lst.count(idx[q]) >= 2:
                continue
            clauses.append([-idx[q]] + [j for j in lst if j != idx[q]])
    pool = IDPool(start_from=len(pl) + 1)
    clauses += CardEnc.equals(list(range(1, len(pl) + 1)), kt, vpool=pool, encoding=EncType.seqcounter).clauses
    with Solver(name='cadical153', bootstrap_with=clauses) as s:
        return s.solve()


def periodic3(S, max_tiles=12, max_edges=8, budget=600):
    t0 = time.time()
    pairs = period_pairs_paths(S, max_tiles, max_edges)
    und = 0
    for n, (k, a, b) in enumerate(pairs):
        if time.time() - t0 > budget:
            return None, n, len(pairs), und
        r = torus2(S, a, b)
        if r is None:
            und += 1
        elif r:
            return dict(tiles=k, p1=a, p2=b), n, len(pairs), und
    return False, len(pairs), len(pairs), und


def torus_dfs(S, p1, p2, node_limit=20000):
    """Periodic tiling with period lattice <p1, p2> by backtracking inside one cell: exactly k = cell area / tile area tiles,
    every edge matched modulo the lattice, corner angles summing to a full turn, no overlaps with any lattice translate.
    True = PERIODIC certificate, False = no such tiling, None = node limit."""
    R = S.ring; m = S.tile.m; N = S.N
    (x1, y1), (x2, y2) = R.f(p1), R.f(p2)
    det = x1 * y2 - x2 * y1
    kt = round(abs(det) / S.tile.area)
    if kt < 1:
        return False

    def lat(i, j):
        return tuple(i * a + j * b for a, b in zip(p1, p2))

    def red_pt(pt):
        x, y = R.f(pt)
        u = (x * y2 - x2 * y) / det; v = (x1 * y - x * y1) / det
        return R.sub(pt, lat(math.floor(u + 1e-9), math.floor(v + 1e-9)))

    def red_edge(a, b):
        ra = red_pt(a)
        return (ra, R.add(b, R.sub(ra, a)))      # translate edge so that its start point is reduced

    shifts = [lat(i, j) for i in (-2, -1, 0, 1, 2) for j in (-2, -1, 0, 1, 2)]
    shiftf = [R.f(s) for s in shifts]
    placed = []; edges = set(); corner = {}
    d2 = (S.diam * 1.01) ** 2
    nodes = [0]

    def cen(pl):
        xs = [R.f(x) for x in S.verts(pl)]
        return (sum(p[0] for p in xs) / m, sum(p[1] for p in xs) / m)

    def can(pl):
        vs = S.verts(pl); angs = S.orients[pl[0]][3]
        for k in range(m):
            if red_edge(vs[k], vs[(k + 1) % m]) in edges:
                return False
            c = red_pt(vs[k])
            tot = corner.get(c, 0) + angs[k]
            if tot > N or (N - tot) not in S.gapok:
                return False
        cq = cen(pl)
        for A in placed + [pl]:
            ca = cen(A)
            for s, sf in zip(shifts, shiftf):
                if A is pl and s == (0, 0, 0, 0):
                    continue
                if (cq[0] - ca[0] - sf[0]) ** 2 + (cq[1] - ca[1] - sf[1]) ** 2 > d2:
                    continue
                if S.overlaps(pl, (A[0], R.add(A[1], s))):
                    return False
        return True

    def do(pl):
        placed.append(pl); vs = S.verts(pl); angs = S.orients[pl[0]][3]
        for k in range(m):
            edges.add(red_edge(vs[k], vs[(k + 1) % m]))
            c = red_pt(vs[k]); corner[c] = corner.get(c, 0) + angs[k]

    def undo():
        pl = placed.pop(); vs = S.verts(pl); angs = S.orients[pl[0]][3]
        for k in range(m):
            edges.discard(red_edge(vs[k], vs[(k + 1) % m]))
            c = red_pt(vs[k]); corner[c] -= angs[k]
            if corner[c] == 0:
                del corner[c]

    def open_edges():
        out = []
        for (a, b) in edges:
            if red_edge(b, a) not in edges:
                out.append((a, b))
        return out

    def options(e):
        a, b = e
        out = []
        for oi, k in S.by_vec.get(R.sub(a, b), ()):
            pl = (oi, red_pt(R.sub(b, S.orients[oi][2][k])))
            if can(pl):
                out.append(pl)
        return out

    def rec():
        nodes[0] += 1
        if nodes[0] > node_limit:
            raise TimeoutError
        oe = open_edges()
        if not oe:
            return len(placed) == kt
        if len(placed) >= kt:
            return False
        best = None
        for e in oe[:8]:
            op = options(e)
            if not op:
                return False
            if best is None or len(op) < len(best):
                best = op
        for pl in best:
            do(pl)
            if rec():
                return True
            undo()
        return False

    do((0, (0, 0, 0, 0)))
    try:
        return rec()
    except TimeoutError:
        return None


def periodic4(S, max_tiles=12, max_edges=8, budget=600, node_limit=20000):
    t0 = time.time()
    pairs = period_pairs_paths(S, max_tiles, max_edges)
    und = 0
    for n, (k, a, b) in enumerate(pairs):
        if time.time() - t0 > budget:
            return None, n, len(pairs), und
        r = torus_dfs(S, a, b, node_limit)
        if r is None:
            und += 1
        elif r:
            return dict(tiles=k, p1=a, p2=b), n, len(pairs), und
    return False, len(pairs), len(pairs), und
