"""Cyrenaic tilings (√3) and their Ammann-bar decorated tileset, ported from Porrier & Fernique's SageMath code
(github.com/cporrier/Cyrenaic, CC0; paper: "Ammann Bars for Octagonal Tilings", arXiv 2205.13973).

Slope E (rows u, v), a = √3:   u = (a, 0, 1, 1),  v = (1, a-1, -1, 1)
Subperiods (each in E, one non-integer entry): p0 = (a,0,1,1), p1 = (1,a-1,-1,1), p2 = (1,-1,a+1,0), p3 = (2,1,-1,a)
Good projection: A = 1/2 [[2, 0, a+1, a-1], [0, 2, -a-1, a+1]]
Tiling: vertices x in Z^4 whose internal projection lies in the window W (projection of the unit 4-cube); tiles are the
2-faces whose 4 corners are vertices. Decoration: through every vertex draw lines in the 4 directions A p_i (shifted by
(a1 + a2)/30 like the original code); each tile keeps the segments that cross it. Distinct decorated tiles = the tileset.
"""
import itertools, math, sys
import numpy as np
from shapely.geometry import Polygon, LineString

a = math.sqrt(3)
E = np.array([[a, 0, 1, 1], [1, a - 1, -1, 1]])
P_SUB = np.array([[a, 0, 1, 1], [1, a - 1, -1, 1], [1, -1, a + 1, 0], [2, 1, -1, a]])
A = 0.5 * np.array([[2, 0, a + 1, a - 1], [0, 2, -a - 1, a + 1]])

# internal projection: orthonormal basis of the orthogonal complement of E
_q, _ = np.linalg.qr(np.vstack([E, np.eye(4)]).T)
IP = _q[:, 2:4].T
assert np.allclose(IP @ E.T, 0, atol=1e-12)


def window():
    pts = np.array([IP @ np.array(c, float) for c in itertools.product((0, 1), repeat=4)])
    from shapely.geometry import MultiPoint
    W = MultiPoint([tuple(p) for p in pts]).convex_hull
    c = W.centroid
    return Polygon([(x - c.x, y - c.y) for x, y in W.exterior.coords])


def vertices(radius, gamma=(0.0123, 0.0071)):
    """Lattice points x with |A x| <= radius whose internal projection (+ gamma) is in the window; found by walking
    unit steps from a vertex near the origin (the vertex set is connected through tile edges)."""
    from shapely.prepared import prep
    W = window(); PW = prep(W)
    ok = lambda x: PW.contains(_pt(IP @ np.array(x, float) + gamma))
    start = next(x for x in itertools.product(range(-2, 3), repeat=4) if ok(x))
    seen = {start}; todo = [start]; out = []
    while todo:
        x = todo.pop(); out.append(x)
        for k in range(4):
            for sgn in (1, -1):
                y = list(x); y[k] += sgn; y = tuple(y)
                if y in seen: continue
                q = A @ np.array(y, float)
                if q @ q > radius * radius: continue
                if ok(y):
                    seen.add(y); todo.append(y)
    return out


def _pt(q):
    from shapely.geometry import Point
    return Point(q[0], q[1])


def tiles(V):
    S = set(V)
    out = []
    for v in V:
        for i, j in itertools.combinations(range(4), 2):
            ei = [1 if k == i else 0 for k in range(4)]; ej = [1 if k == j else 0 for k in range(4)]
            w1 = tuple(v[k] + ei[k] for k in range(4)); w2 = tuple(v[k] + ej[k] for k in range(4))
            w3 = tuple(v[k] + ei[k] + ej[k] for k in range(4))
            if w1 in S and w2 in S and w3 in S:
                out.append(((i, j), v))
    return out


def tile_poly(t):
    (i, j), v = t
    v = np.array(v, float)
    ei = np.eye(4)[i]; ej = np.eye(4)[j]
    return Polygon([tuple(A @ v), tuple(A @ (v + ei)), tuple(A @ (v + ei + ej)), tuple(A @ (v + ej))])


def decorated_tileset(V, r=6, inner=None):
    """For every vertex w (far enough inside), the tile in direction a0 with its Ammann segments, up to translation."""
    S = set(V)
    cols = [A @ np.eye(4)[k] for k in range(4)]
    ang = [math.atan2(c[1], c[0]) for c in cols] + [math.atan2(-c[1], -c[0]) for c in cols]
    a0 = min(x for x in ang if x > 0) / 2
    sub = [A @ p for p in P_SUB]
    unit = [np.eye(4)[k] for k in range(4)] + [-np.eye(4)[k] for k in range(4)]
    found = {}
    VZ = np.array(V); VA = (A @ VZ.T).T
    for w in V:
        wp = A @ np.array(w, float)
        if inner is not None and wp @ wp > inner * inner:
            continue
        nb = []
        for u in unit:
            x = tuple(int(w[k] + u[k]) for k in range(4))
            if x in S:
                d = A @ u
                nb.append((math.atan2(d[1], d[0]), tuple(u), d))
        up = [z for z in nb if z[0] >= a0]; dn = [z for z in nb if z[0] < a0]
        if not up or not dn:
            continue
        a1 = min(up)[2]; a2 = max(dn)[2]
        T = Polygon([(0, 0), tuple(a1), tuple(a1 + a2), tuple(a2)])
        shift = (a1 + a2) / 30
        segs = []
        near = VA[np.abs(VZ - np.array(w)).sum(1) <= r] - wp + shift
        corners = np.array([(0, 0), a1, a1 + a2, a2])
        for d in sub:
            nrm = np.array([-d[1], d[0]]) / np.hypot(*d)
            lo, hi = (corners @ nrm).min(), (corners @ nrm).max()
            off = near @ nrm
            for p in near[(off > lo - 1e-9) & (off < hi + 1e-9)]:
                L = LineString([tuple(p - 50 * d), tuple(p + 50 * d)])
                I = L.intersection(T)
                if I.length > 1e-9:
                    c = list(I.coords)
                    ends = sorted([(round(c[0][0], 5), round(c[0][1], 5)), (round(c[-1][0], 5), round(c[-1][1], 5))])
                    segs.append(tuple(ends))
        key = (tuple(np.round(a1, 5)), tuple(np.round(a2, 5)), tuple(sorted(set(segs))))
        found.setdefault(key, 0)
        found[key] += 1
    return found


def main_tileset(R=30, inner=None, r=6):
    V = vertices(R)
    f = decorated_tileset(V, r=r, inner=inner if inner is not None else R - 10)
    return f


if __name__ == '__main__' and len(sys.argv) > 2 and sys.argv[2] == 'tileset':
    R = float(sys.argv[1]); r = int(sys.argv[3]) if len(sys.argv) > 3 else 6
    f = main_tileset(R, r=r)
    print('decorated tiles (up to translation):', len(f), ' r =', r)
    from collections import Counter
    print('per tile shape:', sorted(Counter((k[0], k[1]) for k in f).values()))
    sys.exit()

if __name__ == '__main__':
    R = float(sys.argv[1]) if len(sys.argv) > 1 else 12
    V = vertices(R)
    T = tiles(V)
    print('vertices', len(V), 'tiles', len(T))
    from collections import Counter
    print('tile types', sorted(Counter(t[0] for t in T).items()))
    # validity: tiles within R-3 must not overlap and must cover the disc of radius R-4
    from shapely.ops import unary_union
    from shapely.geometry import Point
    polys = [tile_poly(t) for t in T]
    area = sum(p.area for p in polys); U = unary_union(polys)
    print('overlap area', round(area - U.area, 9), ' disc R-4 covered:', U.buffer(1e-9).contains(Point(0, 0).buffer(R - 4)))
    # frequencies vs Pluecker coordinates of E (tile (i,j) frequency proportional to |det E[:, (i,j)]|)
    inner = [t for t, p in zip(T, polys) if p.centroid.distance(Point(0, 0)) < R - 3]
    c = Counter(t[0] for t in inner); n = sum(c.values())
    pl = {(i, j): abs(np.linalg.det(E[:, [i, j]])) for i, j in itertools.combinations(range(4), 2)}
    z = sum(pl.values())
    for k in sorted(pl): print(k, 'measured', round(c[k] / n, 4), 'expected', round(pl[k] / z, 4))
