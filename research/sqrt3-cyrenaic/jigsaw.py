"""Step 2: the Cyrenaic (√3) tiles as jigsaw pieces on the 45° (tetrakis) grid.

1. Deform: same combinatorics, new integer edge vectors with the same orientation pattern as the slope E (a valid shape change):
   e0 -> (5,0), e1 -> (0,3), e2 -> (3,-3), e3 -> (3,3). Every tile becomes a lattice parallelogram made of whole tetrakis cells.
2. Encode: each edge carries its Ammann-bar label (labels.py). Label j in its direction becomes a binary code on the middle
   slots of the edge; a 1 moves the cell just left of the edge to the tile on the right (a tooth). Two edges fit only if
   their codes are equal, so the pieces' shapes enforce the bars.
Output: the distinct pieces (cell sets, up to translation) with their labelled type, and a patch of the real tiling by them.
"""
import itertools, json, math, sys
from collections import Counter, defaultdict
import numpy as np
import cyrenaic as C, labels as L

LEN = {0: 7, 1: 5, 2: 4, 3: 4}
B = np.array([[LEN[0], 0, LEN[2], LEN[3]], [0, LEN[1], -LEN[2], LEN[3]]])
SIGNS_E = [int(np.sign(np.linalg.det(C.E[:, [i, j]]))) for i, j in itertools.combinations(range(4), 2)]
SIGNS_B = [int(np.sign(np.linalg.det(B[:, [i, j]]))) for i, j in itertools.combinations(range(4), 2)]
assert SIGNS_E == SIGNS_B, (SIGNS_E, SIGNS_B)


def bx(x):
    v = B @ np.array(x); return int(v[0]), int(v[1])


def halfsteps(p, k):
    """Cells left / right of each step along edge k starting at lattice point p, in order."""
    u, v = p; out = []
    if k == 0:                                   # +x
        for s in range(LEN[0]): out.append(((u + s, v, 0), (u + s, v - 1, 2)))       # above = left
    elif k == 1:                                 # +y
        for s in range(LEN[1]): out.append(((u - 1, v + s, 1), (u, v + s, 3)))       # left side = square to the left
    elif k == 3:                                 # +x+y (2 half steps per unit)
        for s in range(LEN[3]):
            a, b = u + s, v + s
            out.append(((a, b, 3), (a, b, 0))); out.append(((a, b, 2), (a, b, 1)))
    elif k == 2:                                 # +x-y (2 half steps per unit); left normal points up-right
        for s in range(LEN[2]):
            a, b = u + s, v - s - 1
            out.append(((a, b, 2), (a, b, 3))); out.append(((a, b, 1), (a, b, 0)))
    return out


def cell_centroid(c):
    i, j, t = c
    return {0: (i + .5, j + 1 / 6), 1: (i + 5 / 6, j + .5), 2: (i + .5, j + 5 / 6), 3: (i + 1 / 6, j + .5)}[t]


def build(R=40):
    V = C.vertices(R); T = C.tiles(V)
    lab = L.edge_labels(V, R - 6)
    tl = L.tile_labels(T, lab)
    # label -> code per direction
    codes = {}
    for k in range(4):
        ls = sorted({l for (x, kk), l in lab.items() if kk == k})
        codes[k] = {l: j for j, l in enumerate(ls)}
    nslots = {0: LEN[0], 1: LEN[1], 2: 2 * LEN[2], 3: 2 * LEN[3]}
    # owner of each cell = the tile whose parallelogram contains its centroid
    from shapely.geometry import Polygon, Point
    owner = {}
    tiles = list(tl)
    for idx, ((i, j), v) in enumerate(tiles):
        ei = np.eye(4, dtype=int)[i]; ej = np.eye(4, dtype=int)[j]
        pts = [bx(v), bx(np.array(v) + ei), bx(np.array(v) + ei + ej), bx(np.array(v) + ej)]
        P = Polygon(pts)
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        for a in range(min(xs), max(xs)):
            for b in range(min(ys), max(ys)):
                for t in range(4):
                    if P.contains(Point(cell_centroid((a, b, t)))):
                        owner[(a, b, t)] = idx
    tindex = {t: n for n, t in enumerate(tiles)}
    moved = Counter()
    for (x, k), l in lab.items():
        code = codes[k][l]
        steps = halfsteps(bx(x), k)
        n = nslots[k]; mid = list(range(1, n - 1))
        # alignment key: a tooth on the first middle slot, none on the last, the label code in between
        body = [(code >> b) & 1 for b in range(len(mid) - 2)]
        assert code < 2 ** (len(mid) - 2), (k, code, len(mid))
        bits = [1] + body + [0]
        for b, s in zip(bits, mid):
            if not b: continue
            left, right = steps[s]
            if left in owner and right in owner:
                owner[left] = owner[right]; moved[left] += 1
    assert max(moved.values()) == 1, 'a cell was moved twice'
    cells = defaultdict(list)
    for c, idx in owner.items(): cells[idx].append(c)
    pieces = {}
    for idx, t in enumerate(tiles):
        (i, j), v = t
        pa = C.A @ np.array(v, float)
        if pa @ pa > (R - 14) ** 2: continue          # keep tiles whose neighbours are all labelled
        X, Y = bx(v)
        shape = tuple(sorted((a - X, b - Y, tt) for a, b, tt in cells[idx]))
        key = (t[0], tl[t])
        pieces.setdefault(key, set()).add(shape)
    return tiles, tl, owner, pieces, codes


if __name__ == '__main__':
    tiles, tl, owner, pieces, codes = build(float(sys.argv[1]) if len(sys.argv) > 1 else 40)
    print('labelled types', len(pieces), ' consistent (one shape per type):', all(len(s) == 1 for s in pieces.values()))
    shapes = {next(iter(s)) for s in pieces.values()}
    print('distinct piece shapes', len(shapes), ' sizes (cells):', sorted(Counter(len(s) for s in shapes).items()))
    print('codes used per direction:', {k: sorted(set(v.values())) for k, v in codes.items()})
    json.dump([dict(shape=list(t[0]), labels=[list(map(list, e)) for e in t[1]], cells=[list(c) for c in next(iter(s))])
               for t, s in pieces.items()], open('pieces.json', 'w'))
