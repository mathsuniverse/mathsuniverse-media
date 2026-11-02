"""Silver labelled point patterns on the 45° grid, and the inverse solver on them.

Projection: Ammann–Beenker slope E = [[√2, 1, 0, -1], [0, 1, √2, 1]] (from Porrier–Fernique's code). Vertices: x in Z^4 whose
internal projection lies in the window (projection of the unit 4-cube). Geometry: deformed integer edge star
e0=(a,0), e1=(b,b), e2=(0,c), e3=(-d,d) with the same orientation signs as E (a valid shape change), so every vertex is a grid
point of the 45° (tetrakis) grid. Rational density: tile frequencies are rhombs (2-√2)/4 each, squares (√2-1)/2 each, so the
average tile area is rational iff 2ac + 4bd = (a+c)(b+d); a=c=3, b=1, d=6 gives 10.5 units² = 42 grid triangles per tile.
Points = tiles (one tile copy per tile), placed at the tile's first corner. Label = tile type. The solver chooses the
shape S (cells near the origin) AND one orientation (of the 8 grid symmetries) per label, such that every cell is covered once.
"""
import itertools, math, sys, time
import numpy as np
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/claude/mathsuniverse-media/research/monotile-search')
import grids as G, engine as E_
from shapely.geometry import Polygon, MultiPoint, Point
from shapely.prepared import prep
from pysat.solvers import Solver
from pysat.card import CardEnc, EncType
from pysat.formula import IDPool

r2 = math.sqrt(2)
E = np.array([[r2, 1, 0, -1], [0, 1, r2, 1]])
_q, _ = np.linalg.qr(np.vstack([E, np.eye(4)]).T)
PH = _q[:, :2].T; IP = _q[:, 2:4].T                  # physical (orthonormal) and internal projections
assert np.allclose(IP @ E.T, 0, atol=1e-12)


def star(a=3, b=1, c=3, d=6):
    return np.array([[a, b, 0, -d], [0, b, c, d]])


def valid(B):
    s = lambda M, i, j: np.sign(np.linalg.det(M[:, [i, j]]))
    se = [s(E, i, j) for i, j in itertools.combinations(range(4), 2)]
    sb = [s(B, i, j) for i, j in itertools.combinations(range(4), 2)]
    return se == sb or se == [-x for x in sb]


def vertices(R, gamma=(0.0123, 0.0071)):
    pts = [IP @ np.array(c, float) for c in itertools.product((0, 1), repeat=4)]
    W = MultiPoint([tuple(p) for p in pts]).convex_hull; cx, cy = W.centroid.x, W.centroid.y
    PW = prep(Polygon([(x - cx, y - cy) for x, y in W.exterior.coords]))
    ok = lambda x: PW.contains(Point(*(IP @ np.array(x, float) + gamma)))
    start = next(x for x in itertools.product(range(-2, 3), repeat=4) if ok(x))
    seen = {start}; todo = [start]; out = []
    while todo:
        x = todo.pop(); out.append(x)
        for k in range(4):
            for sg in (1, -1):
                y = list(x); y[k] += sg; y = tuple(y)
                if y in seen: continue
                q = PH @ np.array(y, float)
                if q @ q <= R * R and ok(y): seen.add(y); todo.append(y)
    return out


def tiles(V):
    S = set(V); out = []
    for v in V:
        for i, j in itertools.combinations(range(4), 2):
            w = lambda di, dj: tuple(v[k] + (k == i) * di + (k == j) * dj for k in range(4))
            if w(1, 0) in S and w(0, 1) in S and w(1, 1) in S: out.append(((i, j), v))
    return out


g = G.get('tetrakis'); OPS = g.op_tabs


def cells_of(poly):
    xs = [p[0] for p in poly]; ys = [p[1] for p in poly]; P = Polygon(poly); out = []
    for i in range(int(min(xs)) - 1, int(max(xs)) + 1):
        for j in range(int(min(ys)) - 1, int(max(ys)) + 1):
            for t in range(4):
                if P.contains(Point(*g.area_centroid_f((i, j, t)))): out.append((i, j, t))
    return out


def build(R, B):
    V = vertices(R); T = tiles(V)
    bx = lambda v: tuple(int(z) for z in B @ np.array(v))
    polys = []
    for (i, j), v in T:
        ei = np.eye(4, dtype=int)[i]; ej = np.eye(4, dtype=int)[j]
        polys.append([bx(v), bx(np.array(v) + ei), bx(np.array(v) + ei + ej), bx(np.array(v) + ej)])
    return V, T, polys


def solve(T, polys, B, r=5.0, Rz=12.0, limit=20, labels=None, time_limit=None):
    pos = [p[0] for p in polys]
    lab = labels or [t[0] for t in T]
    L = sorted(set(lab), key=str)
    # patch cells: all cells of tiles whose first corner is within Rz of the patch centre
    cx = np.mean([p[0] for p in pos]); cy = np.mean([p[1] for p in pos])
    Z = set()
    for poly, p in zip(polys, pos):
        if math.hypot(p[0] - cx, p[1] - cy) <= Rz: Z.update(cells_of(poly))
    U = [(i, j, t) for i in range(-int(r) - 2, int(r) + 3) for j in range(-int(r) - 2, int(r) + 3) for t in range(4)
         if math.hypot(*g.area_centroid_f((i, j, t))) <= r]
    nU = len(U); xu = {u: n + 1 for n, u in enumerate(U)}
    pool = IDPool(start_from=nU + 1)
    y = {(l, o): pool.id(('y', l, o)) for l in L for o in range(len(OPS))}
    cl = []
    for l in L:                                          # one orientation per label
        lits = [y[(l, o)] for o in range(len(OPS))]
        cl.append(lits); cl.extend(CardEnc.atmost(lits, 1, vpool=pool, encoding=EncType.pairwise).clauses)
    img = {(o, u): E_.transform(g, [u], OPS[o])[0] for o in range(len(OPS)) for u in U}
    aux = {}
    hit = {}
    for (px, py), l in zip(pos, lab):
        for o in range(len(OPS)):
            for u in U:
                a = img[(o, u)]; z = (a[0] + px, a[1] + py, a[2])
                if z not in Z: continue
                key = (l, o, u)
                if key not in aux:
                    v = pool.id(('a',) + key); aux[key] = v
                    cl += [[-v, xu[u]], [-v, y[(l, o)]], [v, -xu[u], -y[(l, o)]]]
                hit.setdefault(z, []).append(aux[key])
    for z in Z:
        lits = sorted(set(hit.get(z, [])))
        if not lits: return [], 'cell unreachable'
        cl.append(lits)
        if len(lits) > 1: cl.extend(CardEnc.atmost(lits, 1, vpool=pool, encoding=EncType.seqcounter).clauses)
    sols = []
    import threading
    with Solver(name='cd15', bootstrap_with=cl) as s:
        timer = None
        if time_limit:
            timer = threading.Timer(time_limit, s.interrupt); timer.start()
        while len(sols) < limit:
            ok = s.solve_limited(expect_interrupt=True) if time_limit else s.solve()
            if ok is None:
                if timer: timer.cancel()
                return sols, 'TIMEOUT after %ds (%d solutions so far)' % (time_limit, len(sols))
            if not ok: break
            m = set(l for l in s.get_model() if l > 0)
            S = sorted(u for u in U if xu[u] in m)
            orient = {l: o for (l, o), v in y.items() if v in m}
            sols.append((S, orient))
            s.add_clause([-xu[u] for u in S] + [xu[u] for u in U if xu[u] not in m])
        if timer: timer.cancel()
    return sols, f'{len(Z)} patch cells, {nU} unknown cells, {len(L)} labels'


if __name__ == '__main__':
    a, b, c, d = (int(x) for x in (sys.argv[1:5] if len(sys.argv) >= 5 else (3, 1, 3, 6)))
    B = star(a, b, c, d); print('star', B.tolist(), 'valid shape change:', valid(B))
    V, T, polys = build(float(sys.argv[5]) if len(sys.argv) > 5 else 14, B)
    areas = [abs(Polygon(p).area) for p in polys]
    from collections import Counter
    print('tiles', len(T), 'types', sorted(Counter(t[0] for t in T).items()), 'mean area', round(np.mean(areas), 3))
    # overlap check
    from shapely.ops import unary_union
    U_ = unary_union([Polygon(p) for p in polys]); print('overlap area', round(sum(areas) - U_.area, 6))
    t0 = time.time(); sols, msg = solve(T, polys, B, r=float(sys.argv[6]) if len(sys.argv) > 6 else 5.0,
                                        Rz=float(sys.argv[7]) if len(sys.argv) > 7 else 12.0)
    print(msg, '| solutions:', len(sols), round(time.time() - t0, 1), 's')
    for S, o in sols[:10]:
        print('  size', len(S), 'connected', E_.is_connected(g, S), 'orientations', o)
