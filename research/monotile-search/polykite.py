"""Exact integer model of the [3.4.6.4] kite grid and enumeration of polykites.

Coordinates
-----------
* Points are Eisenstein integers  a + b*w  with  w = exp(i*pi/3), stored as (a, b).
  Cartesian: x = a + b/2, y = b*sqrt(3)/2.  (This is exactly the `hexpt` frame of
  Kaplan's hatviz, so the hat's vertices are integer points here.)
* The hex grid has hexagon centres on the lattice L spanned by
      U = (2, 2)   (length 2*sqrt(3), at 30 deg)   and   V = (-2, 4)  (at 90 deg).
  A centre is stored as (i, j) meaning i*U + j*V.
* Each hexagon (circumradius 2, apothem sqrt(3)) is cut into 6 kites by segments from
  its centre to its edge midpoints.  Kite k (k = 0..5) of the hexagon at centre C has
  vertices  C, C + m_k, C + v_k, C + m_{k+1}  where
      m_k = w^k * (1, 1)   (edge midpoint, length sqrt(3), angle 30 + 60k deg)
      v_k = w^k * (0, 2)   (hexagon vertex, length 2,       angle 60 + 60k deg)
  Kite edges: two of length sqrt(3) (centre to midpoint), two of length 1 (half hex edge).
* A kite is the integer triple (i, j, k).  A polykite is a frozenset of such triples.

Symmetry group used: p6m = translations by L, rotation by 60 deg about the origin
(a hexagon centre) and complex conjugation (reflection in the x axis).
"""
from __future__ import annotations

import math
from functools import lru_cache

R3 = math.sqrt(3.0)

# ---------------------------------------------------------------- Eisenstein arithmetic

def e_add(p, q):
    return (p[0] + q[0], p[1] + q[1])


def e_sub(p, q):
    return (p[0] - q[0], p[1] - q[1])


def e_rot(p, r=1):
    """Multiply by w^r (rotate by 60*r degrees about the origin)."""
    a, b = p
    for _ in range(r % 6):
        a, b = -b, a + b
    return (a, b)


def e_conj(p):
    """Complex conjugate: reflection in the x axis.  conj(w) = 1 - w."""
    a, b = p
    return (a + b, -b)


def e_xy(p):
    return (p[0] + 0.5 * p[1], R3 / 2 * p[1])


def e_norm(p):
    """|p|^2 = a^2 + ab + b^2 (an integer)."""
    a, b = p
    return a * a + a * b + b * b


U = (2, 2)
V = (-2, 4)
M0 = (1, 1)
V0 = (0, 2)
M = [e_rot(M0, k) for k in range(6)]
VV = [e_rot(V0, k) for k in range(6)]


def centre_point(i, j):
    return (i * U[0] + j * V[0], i * U[1] + j * V[1])


def point_to_centre(p):
    """Inverse of centre_point; returns None if p is not in L."""
    a, b = p
    # i*(2,2) + j*(-2,4) = (a,b)  ->  2i - 2j = a, 2i + 4j = b  ->  6j = b - a
    if (b - a) % 6:
        return None
    j = (b - a) // 6
    if (a + 2 * j) % 2:
        return None
    i = (a + 2 * j) // 2
    return (i, j)


def kite_vertices(kite):
    """Exact Eisenstein vertices (C, M_k, V_k, M_{k+1}) of a kite, in boundary order."""
    i, j, k = kite
    c = centre_point(i, j)
    return (c, e_add(c, M[k % 6]), e_add(c, VV[k % 6]), e_add(c, M[(k + 1) % 6]))


def kite_xy(kite):
    return [e_xy(p) for p in kite_vertices(kite)]


def kite_centroid_xy(kite):
    """Area centroid of the kite (Cartesian floats)."""
    pts = kite_xy(kite)
    return polygon_centroid(pts)


def polygon_area(pts):
    s = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        s += x0 * y1 - x1 * y0
    return s / 2


def polygon_centroid(pts):
    a = polygon_area(pts)
    cx = cy = 0.0
    for (x0, y0), (x1, y1) in zip(pts, pts[1:] + pts[:1]):
        cr = x0 * y1 - x1 * y0
        cx += (x0 + x1) * cr
        cy += (y0 + y1) * cr
    return (cx / (6 * a), cy / (6 * a))


# ---------------------------------------------------------------- symmetry on kites

def rot_centre(c, r=1):
    i, j = c
    for _ in range(r % 6):
        i, j = -j, i + j
    return (i, j)


def conj_centre(c):
    i, j = c
    return (i, -i - j)


def kite_rot(kite, r=1):
    i, j, k = kite
    i2, j2 = rot_centre((i, j), r)
    return (i2, j2, (k + r) % 6)


def kite_conj(kite):
    i, j, k = kite
    i2, j2 = conj_centre((i, j))
    return (i2, j2, (-k - 2) % 6)


def kite_op(kite, op):
    """op = (r, f): first reflect if f, then rotate by r*60 deg."""
    r, f = op
    if f:
        kite = kite_conj(kite)
    return kite_rot(kite, r)


OPS = [(r, f) for f in (0, 1) for r in range(6)]


# ---------------------------------------------------------------- adjacency

def _edges(kite):
    vs = kite_vertices(kite)
    return [frozenset((vs[t], vs[(t + 1) % 4])) for t in range(4)]


@lru_cache(maxsize=None)
def _neighbour_offsets():
    """For each k, the list of (di, dj, k') of kites sharing a full edge with (0,0,k),
    and the list of kites sharing at least a vertex (excluding itself)."""
    edge_nb, vert_nb = {}, {}
    cand = [(di, dj, kk) for di in range(-2, 3) for dj in range(-2, 3) for kk in range(6)]
    for k in range(6):
        me = (0, 0, k)
        my_e = set(_edges(me))
        my_v = set(kite_vertices(me))
        en, vn = [], []
        for c in cand:
            if c == me:
                continue
            if my_e & set(_edges(c)):
                en.append(c)
            if my_v & set(kite_vertices(c)):
                vn.append(c)
        edge_nb[k] = en
        vert_nb[k] = vn
    return edge_nb, vert_nb


def edge_neighbours(kite):
    i, j, k = kite
    return [(i + di, j + dj, kk) for di, dj, kk in _neighbour_offsets()[0][k]]


def vertex_neighbours(kite):
    i, j, k = kite
    return [(i + di, j + dj, kk) for di, dj, kk in _neighbour_offsets()[1][k]]


# ---------------------------------------------------------------- polykites

def normalise(cells):
    """Translate so that min i = min j = 0; return a sorted tuple (fixed form)."""
    mi = min(c[0] for c in cells)
    mj = min(c[1] for c in cells)
    return tuple(sorted((c[0] - mi, c[1] - mj, c[2]) for c in cells))


def transform(cells, op):
    return [kite_op(c, op) for c in cells]


def orientations(cells):
    """Distinct fixed forms of a polykite under the 12 point operations."""
    out = []
    seen = set()
    for op in OPS:
        f = normalise(transform(cells, op))
        if f not in seen:
            seen.add(f)
            out.append(f)
    return out


def canonical(cells):
    return min(normalise(transform(cells, op)) for op in OPS)


def is_connected(cells):
    cells = set(cells)
    start = next(iter(cells))
    seen = {start}
    stack = [start]
    while stack:
        c = stack.pop()
        for n in edge_neighbours(c):
            if n in cells and n not in seen:
                seen.add(n)
                stack.append(n)
    return len(seen) == len(cells)


def enumerate_free(nmax, verbose=False):
    """Return {n: sorted list of canonical polykites} for n = 1..nmax (free: up to
    rotation and reflection).  Growth by adding one edge-adjacent kite at a time."""
    levels = {1: [canonical([(0, 0, 0)])]}
    for n in range(2, nmax + 1):
        new = set()
        for p in levels[n - 1]:
            s = set(p)
            tried = set()
            for c in p:
                for nb in edge_neighbours(c):
                    if nb in s or nb in tried:
                        continue
                    tried.add(nb)
                    new.add(canonical(list(s) + [nb]))
        levels[n] = sorted(new)
        if verbose:
            print(f"n={n}: {len(levels[n])}", flush=True)
    return levels


# OEIS A057786 "Number of polykites with n cells" (checked against oeis.org, Nov 2026).
# NB: the list 1, 2, 4, 10, 25, 70, 196, 574, 1712, 5223 sometimes quoted is NOT A057786.
A057786 = [1, 2, 4, 10, 27, 85, 262, 873, 2917, 10011, 34561, 120815]


# ---------------------------------------------------------------- polygon <-> polykite

def polykite_polygon(cells):
    """Shapely polygon (union) of a polykite."""
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    return unary_union([Polygon(kite_xy(c)) for c in cells])


def kites_in_polygon(poly_xy, search_radius_cells=None):
    """Kites whose centroid lies inside the given polygon (list of xy).  Returns the
    list and whether their union equals the polygon exactly (sym. diff. area ~ 0)."""
    from shapely.geometry import Polygon, Point
    poly = Polygon(poly_xy)
    minx, miny, maxx, maxy = poly.bounds
    h = 2 * R3
    # range of centre indices covering bounding box (generous)
    rng = int(max(abs(minx), abs(maxx), abs(miny), abs(maxy)) / h * 2) + 3
    cells = []
    for i in range(-rng, rng + 1):
        for j in range(-rng, rng + 1):
            cx, cy = e_xy(centre_point(i, j))
            if cx < minx - 3 or cx > maxx + 3 or cy < miny - 3 or cy > maxy + 3:
                continue
            for k in range(6):
                kc = (i, j, k)
                if poly.contains(Point(kite_centroid_xy(kc))):
                    cells.append(kc)
    ok = bool(cells) and polykite_polygon(cells).symmetric_difference(poly).area < 1e-7
    return cells, ok


# ---------------------------------------------------------------- the hat family

# The hat in Kaplan's hatviz frame (hexpt(x, y) == Eisenstein (x, y)).
HAT_EISENSTEIN = [(0, 0), (-1, -1), (0, -2), (2, -2), (2, -1), (4, -2), (5, -1),
                  (4, 0), (3, 0), (2, 2), (0, 3), (0, 2), (-1, 2)]


def _hat_offset():
    """Find an Eisenstein translation t that puts the hat onto our kite grid."""
    for a in range(-3, 4):
        for b in range(-3, 4):
            pts = [e_xy(e_add(p, (a, b))) for p in HAT_EISENSTEIN]
            cells, ok = kites_in_polygon(pts)
            if ok:
                return (a, b), cells
    raise RuntimeError("hat does not sit on the kite grid")


def hat_cells():
    return _hat_offset()[1]


def turtle_polygon_eisenstein():
    """Tile(sqrt3, 1) ("turtle") built from the hat's edge sequence: every hat edge of
    length 1 in direction w^k becomes a sqrt(3)-edge w^k (1 + w), every sqrt(3)-edge
    w^k (1 + w) becomes a unit edge w^(k+1).  (Lengths swapped, whole tile rotated by
    30 deg so it lands on the same kite grid.)"""
    units = {e_rot((1, 0), k): k for k in range(6)}
    longs = {e_rot((1, 1), k): k for k in range(6)}
    pts = HAT_EISENSTEIN
    steps = []
    for p, q in zip(pts, pts[1:] + pts[:1]):
        d = e_sub(q, p)
        if d in units:
            steps.append(('a', units[d]))
        elif d in longs:
            steps.append(('b', longs[d]))
        else:  # length-2 edge = two collinear unit edges
            half = (d[0] // 2, d[1] // 2)
            assert e_add(half, half) == d and half in units, d
            steps += [('a', units[half])] * 2
    assert len(steps) == 14
    out = [(0, 0)]
    for kind, k in steps:
        step = e_rot((1, 1), k) if kind == 'a' else e_rot((1, 0), k + 1)
        out.append(e_add(out[-1], step))
    assert out[-1] == (0, 0), "turtle polygon does not close"
    return out[:-1]


def turtle_cells():
    base = turtle_polygon_eisenstein()
    for a in range(-4, 5):
        for b in range(-4, 5):
            pts = [e_xy(e_add(p, (a, b))) for p in base]
            cells, ok = kites_in_polygon(pts)
            if ok:
                return cells
    raise RuntimeError("turtle does not sit on the kite grid")


if __name__ == '__main__':
    import sys
    import time
    nmax = int(sys.argv[1]) if len(sys.argv) > 1 else 10
    t0 = time.time()
    lv = enumerate_free(nmax)
    for n in range(1, nmax + 1):
        ok = 'OK' if len(lv[n]) == A057786[n - 1] else 'MISMATCH'
        print(f"n={n:2d}  free polykites = {len(lv[n]):6d}   OEIS A057786 = {A057786[n - 1]:6d}  {ok}")
    print(f"time {time.time() - t0:.1f}s")
