"""Grid-agnostic periodic grids with exact geometry in Q(sqrt3).

A grid is a periodic, edge-to-edge tiling of the plane by convex polygons ("cells"):

* a lattice basis a1, a2 (exact points),
* m prototile polygons ("cell types"), one per translation class,

so that every cell is  (i, j, t) = prototile t translated by i*a1 + j*a2.

All coordinates are exact elements of Q(sqrt3) (class Q below: a + b*sqrt3 with rational
a, b).  From this data the module derives, exactly:

* edge adjacency (cells sharing a full edge) and vertex adjacency, as offset tables;
* the symmetry group: every affine map x -> Lx + s (L among the 24 rotations by
  multiples of 30 deg and reflections, all exact in Q(sqrt3)) that maps the grid to itself,
  found by search and checked cell by cell; each is stored as an integer table
  (i, j, t) -> (M (i, j) + d_t, t'_t) with M the integer matrix of L in the lattice basis;
* "partial" congruences: maps (L, s) that send only some cell types onto cells.  A
  polyform using only those types has a congruent copy on the grid that is not a grid
  symmetry image (this happens on the chiral floret grid: a mirror image may or may not
  land on the grid).  They are used to merge polyforms into congruence classes and to add
  placements.

Grids defined here (name: Laves symbol, cell):
  square    [4^4]          squares           (polyominoes)
  hex       [3^6]          hexagons          (polyhexes)
  tri       [6^3]          triangles         (polyiamonds)
  kite      [3.4.6.4]*     kites             (polykites; identical indexing to polykite.py)
  drafter   [4.6.12]*      30-60-90 triangles (polydrafters, kisrhombille)
  rhomb     [3.6.3.6]*     60-120 rhombs     (rhombille)
  tetrakis  [4.8^2]*       right isosceles triangles (tetrakis square)
  triakis   [3.12^2]*      120-30-30 triangles (triakis triangular)
  cairo     [3^2.4.3.4]*   Cairo pentagons
  prismatic [3^3.4^2]*     "house" pentagons (prismatic pentagonal)
  floret    [3^4.6]*       floret pentagons (chiral, symmetry group p6)
"""
from __future__ import annotations

import math
from fractions import Fraction as Fr
from functools import lru_cache

R3F = math.sqrt(3.0)


# ---------------------------------------------------------------- Q(sqrt3)

class Q:
    """a + b*sqrt(3), a and b rational (exact)."""
    __slots__ = ('a', 'b')

    def __init__(self, a=0, b=0):
        self.a = a if isinstance(a, Fr) else Fr(a)
        self.b = b if isinstance(b, Fr) else Fr(b)

    def __add__(self, o):
        o = _q(o)
        return Q(self.a + o.a, self.b + o.b)
    __radd__ = __add__

    def __sub__(self, o):
        o = _q(o)
        return Q(self.a - o.a, self.b - o.b)

    def __rsub__(self, o):
        return _q(o) - self

    def __neg__(self):
        return Q(-self.a, -self.b)

    def __mul__(self, o):
        o = _q(o)
        return Q(self.a * o.a + 3 * self.b * o.b, self.a * o.b + self.b * o.a)
    __rmul__ = __mul__

    def inv(self):
        d = self.a * self.a - 3 * self.b * self.b
        assert d != 0
        return Q(self.a / d, -self.b / d)

    def __truediv__(self, o):
        return self * _q(o).inv()

    def __eq__(self, o):
        o = _q(o)
        return self.a == o.a and self.b == o.b

    def __hash__(self):
        return hash((self.a, self.b))

    def __float__(self):
        return float(self.a) + float(self.b) * R3F

    def is_int(self):
        return self.b == 0 and self.a.denominator == 1

    def __repr__(self):
        return f'({self.a}+{self.b}r3)'


def _q(x):
    return x if isinstance(x, Q) else Q(x)


S3 = Q(0, 1)
HALF = Q(Fr(1, 2))


def P(x, y):
    return (_q(x), _q(y))


def padd(p, q):
    return (p[0] + q[0], p[1] + q[1])


def psub(p, q):
    return (p[0] - q[0], p[1] - q[1])


def pmul(k, p):
    return (p[0] * k, p[1] * k)


def lin(L, p):
    return (L[0][0] * p[0] + L[0][1] * p[1], L[1][0] * p[0] + L[1][1] * p[1])


def pf(p):
    return (float(p[0]), float(p[1]))


def area2(poly):
    """Twice the signed area (exact)."""
    s = Q(0)
    for k in range(len(poly)):
        x0, y0 = poly[k]
        x1, y1 = poly[(k + 1) % len(poly)]
        s = s + x0 * y1 - x1 * y0
    return s


def _area_centroid_f(pts):
    a = cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        cr = x0 * y1 - x1 * y0
        a += cr
        cx += (x0 + x1) * cr
        cy += (y0 + y1) * cr
    return (cx / (3 * a), cy / (3 * a))


def centre(poly):
    """Vertex average (exact); unique interior point of a convex cell."""
    n = len(poly)
    sx, sy = Q(0), Q(0)
    for x, y in poly:
        sx, sy = sx + x, sy + y
    return (sx * Fr(1, n), sy * Fr(1, n))


# cos and sin of 30k degrees, exact
_C = [Q(1), S3 * Fr(1, 2), Q(Fr(1, 2)), Q(0), Q(Fr(-1, 2)), S3 * Fr(-1, 2)]
COS = [_C[k] if k < 6 else -_C[k - 6] for k in range(12)]
SIN = [COS[(k - 3) % 12] for k in range(12)]


def rot(k):
    return ((COS[k % 12], -SIN[k % 12]), (SIN[k % 12], COS[k % 12]))


REFL = ((Q(1), Q(0)), (Q(0), Q(-1)))   # (x, y) -> (x, -y)


def matmul(A, B):
    return tuple(tuple(sum((A[i][k] * B[k][j] for k in range(2)), Q(0)) for j in range(2)) for i in range(2))


# all 24 candidate linear parts: rotation k*30 deg, optionally after reflection in x-axis
CANDIDATE_L = [(k, f, matmul(rot(k), REFL) if f else rot(k)) for f in (0, 1) for k in range(12)]


def eis(a, b):
    """Eisenstein integer a + b*w (w = e^{i pi/3}) as an exact Cartesian point."""
    return (Q(Fr(a)) + Q(Fr(b)) * Fr(1, 2), S3 * Fr(b, 2))


# ---------------------------------------------------------------- the grid

class Grid:
    def __init__(self, name, basis, protos, laves='', cellname='cell', unit=None, notes=''):
        self.name = name
        self.laves = laves
        self.cellname = cellname
        self.notes = notes
        self.a1, self.a2 = basis
        self.protos = [list(p) for p in protos]
        self.m = len(protos)
        # orient every prototile counter-clockwise
        for t, p in enumerate(self.protos):
            if float(area2(p)) < 0:
                self.protos[t] = p[::-1]
        self.cent = [centre(p) for p in self.protos]
        self.Af = ((float(self.a1[0]), float(self.a2[0])), (float(self.a1[1]), float(self.a2[1])))
        det = self.Af[0][0] * self.Af[1][1] - self.Af[0][1] * self.Af[1][0]
        self.Ainv = ((self.Af[1][1] / det, -self.Af[0][1] / det), (-self.Af[1][0] / det, self.Af[0][0] / det))
        self.det = abs(det)
        self.cent_f = [pf(c) for c in self.cent]
        self.acent_f = [_area_centroid_f([pf(v) for v in p]) for p in self.protos]
        if unit is None:
            unit = min(math.hypot(*pf(self.a1)), math.hypot(*pf(self.a2)))
        self.unit = unit
        self._build_adjacency()
        self._build_symmetries()

    # ---- exact geometry
    def T(self, i, j):
        return padd(pmul(i, self.a1), pmul(j, self.a2))

    def cell_vertices(self, cell):
        i, j, t = cell
        tr = self.T(i, j)
        return [padd(v, tr) for v in self.protos[t]]

    def cell_centre(self, cell):
        i, j, t = cell
        return padd(self.cent[t], self.T(i, j))

    def centroid_f(self, cell):
        i, j, t = cell
        cx, cy = self.cent_f[t]
        return (cx + i * self.Af[0][0] + j * self.Af[0][1], cy + i * self.Af[1][0] + j * self.Af[1][1])

    def area_centroid_f(self, cell):
        i, j, t = cell
        cx, cy = self.acent_f[t]
        return (cx + i * self.Af[0][0] + j * self.Af[0][1], cy + i * self.Af[1][0] + j * self.Af[1][1])

    def lattice_coords_f(self, p):
        x, y = p
        return (self.Ainv[0][0] * x + self.Ainv[0][1] * y, self.Ainv[1][0] * x + self.Ainv[1][1] * y)

    def locate(self, p):
        """Exact: the cell whose vertex-average is the exact point p, or None."""
        pfl = pf(p)
        for t in range(self.m):
            u, v = self.lattice_coords_f((pfl[0] - self.cent_f[t][0], pfl[1] - self.cent_f[t][1]))
            i, j = round(u), round(v)
            if abs(u - i) < 1e-6 and abs(v - j) < 1e-6 and self.cell_centre((i, j, t)) == p:
                return (i, j, t)
        return None

    def cell_of_polygon(self, poly):
        """Exact: the cell whose vertex SET equals poly, or None."""
        c = self.locate(centre(poly))
        if c is None:
            return None
        if set(self.cell_vertices(c)) == set(poly):
            return c
        return None

    # ---- adjacency
    def _build_adjacency(self):
        W = 3
        cand = [(di, dj, t) for di in range(-W, W + 1) for dj in range(-W, W + 1) for t in range(self.m)]
        vx = {c: self.cell_vertices(c) for c in cand}
        ed = {c: {frozenset((v[k], v[(k + 1) % len(v)])) for k in range(len(v))} for c, v in vx.items()}
        self.edge_off, self.vert_off = [], []
        for t in range(self.m):
            me = (0, 0, t)
            en, vn = [], []
            for c in cand:
                if c == me:
                    continue
                if ed[me] & ed[c]:
                    en.append(c)
                if set(vx[me]) & set(vx[c]):
                    vn.append(c)
            assert len(en) == len(self.protos[t]), (self.name, t, len(en))  # edge-to-edge
            self.edge_off.append(en)
            self.vert_off.append(vn)

    def edge_neighbours(self, cell):
        i, j, t = cell
        return [(i + a, j + b, k) for a, b, k in self.edge_off[t]]

    def vertex_neighbours(self, cell):
        i, j, t = cell
        return [(i + a, j + b, k) for a, b, k in self.vert_off[t]]

    # ---- symmetries
    def _lattice_matrix(self, L):
        """Integer matrix M with L(a_k) = sum M[r][k] a_r, or None."""
        cols = []
        for a in (self.a1, self.a2):
            img = lin(L, a)
            u, v = self.lattice_coords_f(pf(img))
            iu, iv = round(u), round(v)
            if abs(u - iu) > 1e-6 or abs(v - iv) > 1e-6 or self.T(iu, iv) != img:
                return None
            cols.append((iu, iv))
        return ((cols[0][0], cols[1][0]), (cols[0][1], cols[1][1]))

    def _try_affine(self, L, s):
        """Table t -> (di, dj, t') for the types that x -> Lx + s maps onto cells."""
        tab = {}
        for t in range(self.m):
            img = [padd(lin(L, v), s) for v in self.protos[t]]
            c = self.cell_of_polygon(img)
            if c is not None:
                tab[t] = c
        return tab

    def _build_symmetries(self):
        self.ops = []        # full symmetries: (label, M, table list)
        self.partial = []    # partial congruences: (label, M, table dict, domain frozenset)
        seen_full = set()
        for k, f, L in CANDIDATE_L:
            M = self._lattice_matrix(L)
            if M is None:
                continue
            c0 = lin(L, self.cent[0])
            for t2 in range(self.m):
                s = psub(self.cent[t2], c0)
                tab = self._try_affine(L, s)
                if not tab:
                    continue
                if len(tab) == self.m:
                    key = (M, tuple(tab[t] for t in range(self.m)))
                    # equal up to a lattice translation?
                    norm = tuple((tab[t][0] - tab[0][0], tab[t][1] - tab[0][1], tab[t][2]) for t in range(self.m))
                    if (M, norm) in seen_full:
                        continue
                    seen_full.add((M, norm))
                    self.ops.append(((k, f, str(s)), M, [tab[t] for t in range(self.m)]))
                else:
                    self.partial.append(((k, f, str(s)), M, dict(tab), frozenset(tab)))
        # identity first
        ident = [i for i, o in enumerate(self.ops) if o[0][0] == 0 and o[0][1] == 0 and
                 all(o[2][t] == (0, 0, t) for t in range(self.m))]
        assert ident, 'identity missing'
        self.ops.insert(0, self.ops.pop(ident[0]))
        self.op_tabs = [(M, tab) for _, M, tab in self.ops]
        # drop partial maps that are (restrictions of) full symmetries
        fullsets = set()
        for M, tab in self.op_tabs:
            fullsets.add((M, tuple((tab[t][0] - tab[0][0], tab[t][1] - tab[0][1], tab[t][2]) for t in range(self.m))))
        keep = []
        sigs = set()
        for lab, M, tab, dom in self.partial:
            redundant = False
            for M2, tab2 in self.op_tabs:
                if M2 == M:
                    d0 = None
                    ok = True
                    for t in dom:
                        dd = (tab[t][0] - tab2[t][0], tab[t][1] - tab2[t][1])
                        if tab[t][2] != tab2[t][2] or (d0 is not None and dd != d0):
                            ok = False
                            break
                        d0 = dd
                    if ok:
                        redundant = True
                        break
            sig = (M, tuple(sorted(tab.items())))
            if not redundant and sig not in sigs:
                sigs.add(sig)
                keep.append((lab, M, tab, dom))
        self.partial = keep

    @property
    def chiral(self):
        return not any(lab[1] for lab, _, _ in self.ops)

    def describe(self):
        return (f"{self.name} {self.laves}: {self.m} cell type(s) per lattice cell, "
                f"{len(self.ops)} point symmetries (mod translations){' [chiral]' if self.chiral else ''}, "
                f"{len(self.partial)} partial congruences")


# ---------------------------------------------------------------- integer operations on cells

def apply_op(op, cell):
    M, tab = op
    i, j, t = cell
    di, dj, t2 = tab[t]
    return (M[0][0] * i + M[0][1] * j + di, M[1][0] * i + M[1][1] * j + dj, t2)


def normalise(cells):
    mi = min(c[0] for c in cells)
    mj = min(c[1] for c in cells)
    return tuple(sorted((c[0] - mi, c[1] - mj, c[2]) for c in cells))


# ---------------------------------------------------------------- grid definitions

def _hex_frame_points():
    """Hexagon of circumradius 2 at the origin (kite / drafter / rhomb frame, = polykite.py)."""
    def erot(p, r):
        a, b = p
        for _ in range(r % 6):
            a, b = -b, a + b
        return (a, b)
    Mi = [eis(*erot((1, 1), k)) for k in range(6)]    # edge midpoints (|.| = sqrt3)
    Vi = [eis(*erot((0, 2), k)) for k in range(6)]    # vertices (|.| = 2)
    return Mi, Vi


def make_square():
    sq = [P(0, 0), P(1, 0), P(1, 1), P(0, 1)]
    return Grid('square', (P(1, 0), P(0, 1)), [sq], '[4^4]', 'square')


def make_hex():
    Mi, Vi = _hex_frame_points()
    return Grid('hex', (eis(2, 2), eis(-2, 4)), [Vi], '[3^6]', 'hexagon')


def make_tri():
    up = [eis(0, 0), eis(1, 0), eis(0, 1)]
    dn = [eis(1, 0), eis(1, 1), eis(0, 1)]
    return Grid('tri', (eis(1, 0), eis(0, 1)), [up, dn], '[6^3]', 'triangle')


def make_kite():
    Mi, Vi = _hex_frame_points()
    O = eis(0, 0)
    protos = [[O, Mi[k], Vi[k], Mi[(k + 1) % 6]] for k in range(6)]
    return Grid('kite', (eis(2, 2), eis(-2, 4)), protos, '[3.4.6.4]*', 'kite')


def make_drafter():
    Mi, Vi = _hex_frame_points()
    O = eis(0, 0)
    protos = []
    for k in range(6):
        protos.append([O, Mi[k], Vi[k]])            # type 2k
        protos.append([O, Vi[k], Mi[(k + 1) % 6]])  # type 2k+1
    return Grid('drafter', (eis(2, 2), eis(-2, 4)), protos, '[4.6.12]*', 'drafter',
                notes='kisrhombille: each hexagon of the kite frame cut into 12 30-60-90 triangles; '
                      'kite k = drafters 2k and 2k+1')


def make_rhomb():
    Mi, Vi = _hex_frame_points()
    O = eis(0, 0)
    protos = [[O, Vi[(2 * k + 5) % 6], Vi[2 * k], Vi[(2 * k + 1) % 6]] for k in range(3)]
    return Grid('rhomb', (eis(2, 2), eis(-2, 4)), protos, '[3.6.3.6]*', 'rhomb')


def make_tetrakis():
    c = P(Fr(1, 2), Fr(1, 2))
    sq = [P(0, 0), P(1, 0), P(1, 1), P(0, 1)]
    protos = [[sq[k], sq[(k + 1) % 4], c] for k in range(4)]
    return Grid('tetrakis', (P(1, 0), P(0, 1)), protos, '[4.8^2]*', 'half-square triangle',
                notes='unit squares cut by both diagonals (tetrakis square); cells are right isosceles triangles')


def make_triakis():
    up = [eis(0, 0), eis(1, 0), eis(0, 1)]
    dn = [eis(1, 0), eis(1, 1), eis(0, 1)]
    protos = []
    for tri in (up, dn):
        c = centre(tri)
        for k in range(3):
            protos.append([tri[k], tri[(k + 1) % 3], c])
    return Grid('triakis', (eis(1, 0), eis(0, 1)), protos, '[3.12^2]*', 'triakis triangle')


def make_cairo():
    s = S3
    c = (s - 1) * Fr(1, 2)
    P0 = [(-c, Q(0)), (c, Q(0)), (s * Fr(1, 2), s * Fr(1, 2)), (Q(0), (s + 1) * Fr(1, 2)),
          (s * Fr(-1, 2), s * Fr(1, 2))]
    piv = P0[2]   # 4-valent vertex (90 deg corner)
    protos = []
    for k in range(4):
        R = rot(3 * k)
        protos.append([padd(lin(R, psub(v, piv)), piv) for v in P0])
    return Grid('cairo', ((s, -s), (s, s)), protos, '[3^2.4.3.4]*', 'Cairo pentagon',
                notes='Laves Cairo pentagon: angles 120,120,90,120,90; four unit edges, one edge sqrt3-1')


def make_prismatic():
    s = S3
    h1 = Q(Fr(1, 2)) + s * Fr(1, 6)
    h2 = Q(Fr(1, 2)) + s * Fr(1, 3)
    up = [P(0, 0), P(1, 0), (Q(1), h1), (Q(Fr(1, 2)), h2), (Q(0), h1)]
    dn = [(x, -y) for x, y in up]
    return Grid('prismatic', (P(1, 0), (Q(Fr(1, 2)), Q(1) + s * Fr(1, 2))), [up, dn], '[3^3.4^2]*',
                'prismatic pentagon',
                notes='dual of the elongated triangular tiling (square centres + triangle centroids)')


def make_floret():
    base = [eis(0, 0), eis(2, 0), eis(2, 1), eis(1, 2), eis(0, 2)]
    protos = []
    for k in range(6):
        R = rot(2 * k)
        protos.append([lin(R, v) for v in base])
    # floret centres on a lattice of norm 21; pick the chirality that tiles
    for a1 in (eis(4, 1), eis(1, 4)):
        a2 = lin(rot(2), a1)
        try:
            g = Grid('floret', (a1, a2), protos, '[3^4.6]*', 'floret pentagon',
                     notes='Laves floret pentagon: angles 60,120,120,120,120, sides 2,1,1,1,2')
        except AssertionError:
            continue
        if check_tiling(g, quiet=True):
            return g
    raise RuntimeError('floret construction failed')


GRIDS = {
    'square': make_square, 'hex': make_hex, 'tri': make_tri, 'kite': make_kite,
    'drafter': make_drafter, 'rhomb': make_rhomb, 'tetrakis': make_tetrakis,
    'triakis': make_triakis, 'cairo': make_cairo, 'prismatic': make_prismatic, 'floret': make_floret,
}


@lru_cache(maxsize=None)
def get(name):
    return GRIDS[name]()


# ---------------------------------------------------------------- validation of a grid

def check_tiling(g, quiet=False):
    """Exact checks that the data define an edge-to-edge tiling:
    (1) prototile areas sum to the lattice cell area (exactly, in Q(sqrt3));
    (2) every edge of every cell is shared with exactly one other cell (exact vertices),
        and the two cells lie on opposite sides of it;
    (3) cells in a window are pairwise interior-disjoint (float polygon check).
    Returns True/False (raises nothing)."""
    try:
        tot = Q(0)
        for p in g.protos:
            tot = tot + area2(p)
        cell_area2 = (g.a1[0] * g.a2[1] - g.a2[0] * g.a1[1]) * 2
        if not (tot == cell_area2 or tot == -cell_area2):
            if not quiet:
                print('area mismatch', tot, cell_area2)
            return False
        W = 3
        cells = [(i, j, t) for i in range(-W, W + 1) for j in range(-W, W + 1) for t in range(g.m)]
        edges = {}
        for c in cells:
            v = g.cell_vertices(c)
            for k in range(len(v)):
                edges.setdefault(frozenset((v[k], v[(k + 1) % len(v)])), []).append((c, v[k], v[(k + 1) % len(v)]))
        for t in range(g.m):
            v = g.cell_vertices((0, 0, t))
            for k in range(len(v)):
                e = frozenset((v[k], v[(k + 1) % len(v)]))
                lst = edges[e]
                if len(lst) != 2:
                    if not quiet:
                        print('edge shared by', len(lst), 'cells', t, k)
                    return False
                # opposite orientation (both ccw => traversed in opposite directions)
                (c1, p1, q1), (c2, p2, q2) = lst
                if not (p1 == q2 and q1 == p2):
                    return False
        from shapely.geometry import Polygon
        near = [c for c in cells if abs(c[0]) <= 1 and abs(c[1]) <= 1]
        polys = {c: Polygon([pf(v) for v in g.cell_vertices(c)]) for c in cells}
        for c in near:
            for d in cells:
                if d != c and polys[c].intersection(polys[d]).area > 1e-9:
                    if not quiet:
                        print('overlap', c, d)
                    return False
        return True
    except AssertionError:
        return False


def check_symmetries(g, W=2):
    """Exact check: every stored op maps every cell in a window onto the cell its integer
    table predicts, vertex by vertex (re-derives the affine map from the table)."""
    for lab, M, tab in g.ops:
        k, f, _ = lab
        L = matmul(rot(k), REFL) if f else rot(k)
        # recover s from type 0
        s = psub(g.cell_centre(tab[0]), lin(L, g.cent[0]))
        for i in range(-W, W + 1):
            for j in range(-W, W + 1):
                for t in range(g.m):
                    c = (i, j, t)
                    img = {padd(lin(L, v), s) for v in g.cell_vertices(c)}
                    pred = apply_op((M, tab), c)
                    if img != set(g.cell_vertices(pred)):
                        return False
    return True


if __name__ == '__main__':
    import time
    for nm in GRIDS:
        t0 = time.time()
        g = get(nm)
        print(g.describe(), '| tiling ok:', check_tiling(g), '| symmetries ok:', check_symmetries(g),
              f'| {time.time() - t0:.1f}s')
