"""12-fold (sqrt 3) cut-and-project tiling from Z^4 with the 12-fold star.

Module Z[zeta12] = Z^4 with basis 1, z, z^2, z^3 (z = exp(i pi/6), z^4 = z^2 - 1).
Physical star: x -> sum x_j z^j.  Internal (Galois) star: z -> z^5.
Vertex set: { pi(x) : x in Z^4, pi_perp(x) - c in W }, W = regular dodecagon.
With W of edge length 1 (circumradius 1/(2 sin 15deg)) this is the Niizeki-Gaehler model set; joining
points at unit distance gives a square-triangle-rhomb (30 deg) tiling. We verify planarity (no
crossing edges, every bounded face is a unit square, unit equilateral triangle or 30-deg rhomb)
instead of trusting this.
All vertex data are exact integer vectors; floats only for window membership (margin reported).
"""
import itertools
import math
from collections import Counter, defaultdict

import numpy as np

Z = np.exp(1j * math.pi / 6)
PHYS = np.array([Z ** j for j in range(4)])
PERP = np.array([Z ** (5 * j) for j in range(4)])
UNIT = [(1, 0, 0, 0), (0, 1, 0, 0), (0, 0, 1, 0), (0, 0, 0, 1), (-1, 0, 1, 0), (0, -1, 0, 1)]
UNIT = UNIT + [tuple(-x for x in u) for u in UNIT]  # UNIT[m] = z^m

# exact point group on Z^4: rotation by z, reflection = complex conjugation
ROT = np.array([[0, 0, 0, -1], [1, 0, 0, 0], [0, 1, 0, 1], [0, 0, 1, 0]])  # columns: z*e_j
REF = np.array([[1, 0, 1, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, -1, 0, -1]])  # columns: conj(z^j)


def check_group():
    for j in range(4):
        e = np.zeros(4, int)
        e[j] = 1
        assert abs((ROT @ e) @ PHYS - Z * (e @ PHYS)) < 1e-12
        assert abs((REF @ e) @ PHYS - np.conj(e @ PHYS)) < 1e-12


def group():
    check_group()
    mats = []
    M = np.eye(4, dtype=int)
    for _ in range(12):
        mats.append(M.copy())
        mats.append(M @ REF)
        M = ROT @ M
    return mats


def in_dodecagon(w, r, rot0):
    """Regular dodecagon with circumradius r, a vertex at angle rot0."""
    ang = math.atan2(w.imag, w.real) - rot0
    a = (ang % (math.pi / 6))
    # distance to the edge in the sector
    apo = r * math.cos(math.pi / 12)
    th = a - math.pi / 12
    return abs(w) * math.cos(th) - apo  # <= 0 inside


def generate(R, rscale=1.0, rot0=0.0, c=0.1234 + 0.0567j, M=None):
    r = rscale / (2 * math.sin(math.pi / 12))
    if M is None:
        M = int(R * 1.2 + 6)
    rng = range(-M, M + 1)
    pts = {}
    margin = 1.0
    X = np.array(list(itertools.product(rng, repeat=4)))
    P = X @ PHYS
    Q = X @ PERP - c
    keep = np.abs(P) <= R + 2
    X, P, Q = X[keep], P[keep], Q[keep]
    for x, p, q in zip(X, P, Q):
        d = in_dodecagon(q, r, rot0)
        if d <= 0:
            pts[tuple(int(v) for v in x)] = p
        margin = min(margin, abs(d))
    return pts, margin


def build(R, **kw):
    pts, margin = generate(R, **kw)
    nbrs = defaultdict(list)
    for v in pts:
        for m, u in enumerate(UNIT):
            w = tuple(a + b for a, b in zip(v, u))
            if w in pts:
                nbrs[v].append((m, w))
    # faces: half-edge traversal, neighbours sorted by angle m (z^m has angle 30m deg)
    faces = []
    used = set()
    for v in pts:
        for m, w in nbrs[v]:
            if (v, w) in used:
                continue
            face = [v]
            a, b, mm = v, w, m
            ok = True
            while True:
                used.add((a, b))
                face.append(b)
                # at b, incoming direction mm; next edge = the first neighbour clockwise from reverse
                back = (mm + 6) % 12
                opts = sorted(nbrs[b], key=lambda t: (t[0] - back) % 12)
                # take the neighbour with the largest ccw turn from back that is not back itself:
                # for a face on the left, choose the smallest clockwise turn from 'back'
                cand = [t for t in opts if t[0] != back]
                if not cand:
                    ok = False
                    break
                nm, nb = max(cand, key=lambda t: (t[0] - back) % 12)
                a, b, mm = b, nb, nm
                if (a, b) == (v, w):
                    break
                if len(face) > 40:
                    ok = False
                    break
            if ok:
                faces.append(face[:-1])
    return pts, nbrs, faces, margin


def face_type(face, pts):
    n = len(face)
    P = [pts[v] for v in face]
    area = 0.5 * sum((P[i].conjugate() * P[(i + 1) % n]).imag for i in range(n))
    if n == 3:
        return "triangle", area
    if n == 4:
        if abs(abs(area) - 1) < 1e-9:
            return "square", area
        if abs(abs(area) - 0.5) < 1e-9:
            return "rhomb30", area
        return "quad%.3f" % area, area
    return "poly%d" % n, area


def crossings(pts, nbrs, R):
    segs = []
    for v in pts:
        if abs(pts[v]) > R:
            continue
        for m, w in nbrs[v]:
            if v < w:
                segs.append((pts[v], pts[w]))
    # grid bucketing
    bucket = defaultdict(list)
    for i, (a, b) in enumerate(segs):
        mid = (a + b) / 2
        bucket[(int(math.floor(mid.real)), int(math.floor(mid.imag)))].append(i)

    def cross(a, b, c, d):
        def o(p, q, r):
            return ((q - p).conjugate() * (r - p)).imag
        d1, d2, d3, d4 = o(a, b, c), o(a, b, d), o(c, d, a), o(c, d, b)
        return d1 * d2 < -1e-9 and d3 * d4 < -1e-9

    n = 0
    for (gx, gy), ids in bucket.items():
        near = []
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                near += bucket.get((gx + dx, gy + dy), [])
        for i in ids:
            for j in near:
                if j > i and cross(*segs[i], *segs[j]):
                    n += 1
    return n


def tiling(R, **kw):
    pts, nbrs, faces, margin = build(R + 3, **kw)
    tiles = []
    for f in faces:
        typ, area = face_type(f, pts)
        if area <= 0:
            continue  # outer face(s)
        cen = sum(pts[v] for v in f) / len(f)
        if abs(cen) <= R:
            tiles.append((tuple(f), typ, cen))
    return pts, nbrs, tiles, margin


if __name__ == "__main__":
    import sys
    for rs in [float(x) for x in sys.argv[1:]] or [1.0]:
        for rot0 in (0.0, math.pi / 12):
            pts, nbrs, tiles, margin = tiling(10, rscale=rs, rot0=rot0)
            print(rs, round(rot0, 3), len(pts), Counter(t[1] for t in tiles),
                  "cross", crossings(pts, nbrs, 10), "margin", margin)
