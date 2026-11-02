import sys, math, json
sys.path.insert(0, '/home/claude/mathsuniverse-media/research/monotile-search')
sys.path.insert(0, '/home/claude/mathsuniverse-media/research/monotile-search/hierarchy')
sys.path.insert(0, '/tmp/claude-0/-home-claude/8d78e7f5-5d27-5557-bcf6-cdfb92e43b7a/scratchpad/pipeline/engine')
import grids as G, hat_tiling as HT
from collections import defaultdict
g = G.get('kite')
TX, TY = -1.5, 18.186533
raw = []
def flat(m, T, path):
    if isinstance(m, HT.Hat): raw.append((m.label, [HT.tpt(T, p) for p in HT.HAT], path)); return
    for i, (CT, c) in enumerate(m.children): flat(c, HT.mul(T, CT), path + (i,))
t = [HT._H(), HT._T(), HT._P(), HT._F()]
for _ in range(3): t = HT.metatiles(HT.patch(*t))
flat(t[0], HT.IDENT, ())
raw = [(l, [(2 * x, 2 * y) for x, y in p], pa) for l, p, pa in raw]   # patch hats are at half scale                         # level-4 H supertile: 1156 hats, path length 4
A = g.Af; det = A[0][0] * A[1][1] - A[0][1] * A[1][0]
def cell_of(x, y):
    # find the kite cell whose centroid is (x, y)
    for i0 in range(-1, 2):
        pass
    a = (A[1][1] * x - A[0][1] * y) / det; b = (-A[1][0] * x + A[0][0] * y) / det
    for i in (math.floor(a) - 1, math.floor(a), math.floor(a) + 1):
        for j in (math.floor(b) - 1, math.floor(b), math.floor(b) + 1):
            for k in range(6):
                vs = [G.pf(v) for v in g.cell_vertices((i, j, k))]
                cx = sum(v[0] for v in vs) / 4; cy = sum(v[1] for v in vs) / 4
                if abs(cx - x) < 1e-6 and abs(cy - y) < 1e-6: return (i, j, k)
    raise ValueError
# kite centroids inside a hat: split hat into its 8 kites via grid: test all candidate cells near the hat
def hat_cells(poly):
    from shapely.geometry import Polygon
    P = Polygon([(x + TX, y + TY) for x, y in poly])
    out = []
    xs = [p[0] + TX for p in poly]; ys = [p[1] + TY for p in poly]
    a = (A[1][1] * sum(xs) / 13 - A[0][1] * sum(ys) / 13) / det; b = (-A[1][0] * sum(xs) / 13 + A[0][0] * sum(ys) / 13) / det
    for i in range(math.floor(a) - 3, math.floor(a) + 4):
        for j in range(math.floor(b) - 3, math.floor(b) + 4):
            for k in range(6):
                vs = [G.pf(v) for v in g.cell_vertices((i, j, k))]
                cx = sum(v[0] for v in vs) / 4; cy = sum(v[1] for v in vs) / 4
                if P.buffer(1e-6).contains(Polygon(vs)): out.append((i, j, k))
    assert len(out) == 8, len(out)
    return out
# re-align: recentre() moves the patch off the lattice, so find the offset from the first hat
p0 = raw[0][1][0]
CAND = cand = {tuple(round(x, 9) for x in G.pf(v)) for i in range(-30, 31) for j in range(-30, 31) for k in range(6) for v in g.cell_vertices((i, j, k))}
cand = sorted(CAND, key=lambda v: (v[0] - p0[0]) ** 2 + (v[1] - p0[1]) ** 2)
for vx, vy in cand[:400]:
    TX, TY = vx - p0[0], vy - p0[1]
    try:
        hat_cells(raw[0][1]); hat_cells(raw[1][1]); break
    except AssertionError:
        continue
print('offset', TX, TY)

def all_hats():
    out = []
    for lab, poly, path in raw:
        out.append((lab, tuple(sorted(hat_cells(poly)))))
    return out
