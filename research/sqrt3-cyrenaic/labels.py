"""Step 1: Ammann bars as edge labels. For every edge of the Cyrenaic tiling (an edge = vertex x and direction k, from A x to
A(x + e_k)), record where the bars cross it: a sorted tuple of (fraction along the edge, bar direction). Bars are the lines
through every vertex in the 4 directions A p_i, with the same small shift as the original code, so they never hit a vertex.
Bar continuity across an edge is exactly: both tiles see the same crossings on their shared edge, so each tile = 4 edge labels."""
import itertools, math, sys
import numpy as np
import cyrenaic as C

def edge_labels(V, r_inner):
    VA = np.array([C.A @ np.array(v, float) for v in V])
    S = set(V)
    sub = [C.A @ p for p in C.P_SUB]
    nrm = [np.array([-d[1], d[0]]) / np.hypot(*d) for d in sub]
    # one global shift (the original code shifts by (a1+a2)/30 per tile; a global generic shift gives the same combinatorics)
    shift = np.array([0.0317, 0.0213])
    offs = [VA @ n + shift @ n for n in nrm]           # every bar = {z : z.n_i = off}
    offs = [np.unique(np.round(o, 7)) for o in offs]       # one entry per bar (many vertices share a bar)
    lab = {}
    for x in V:
        p = C.A @ np.array(x, float)
        if p @ p > r_inner ** 2: continue
        for k in range(4):
            y = tuple(x[j] + (j == k) for j in range(4))
            if y not in S: continue
            q = C.A @ np.array(y, float)
            cr = []
            for i in range(4):
                a, b = p @ nrm[i], q @ nrm[i]
                if abs(a - b) < 1e-12: continue
                lo, hi = min(a, b), max(a, b)
                o = offs[i]; sel = o[(o > lo + 1e-9) & (o < hi - 1e-9)]
                for v in sel: cr.append((round((v - a) / (b - a), 4), i))
            lab[(x, k)] = tuple(sorted(cr))
    return lab

def tile_labels(T, lab):
    """tile (i,j) at v: edges bottom (v,i), right (v+e_i, j), top (v+e_j, i), left (v, j)."""
    out = {}
    for (i, j), v in T:
        vi = tuple(v[m] + (m == i) for m in range(4)); vj = tuple(v[m] + (m == j) for m in range(4))
        es = [(v, i), (vi, j), (vj, i), (v, j)]
        if all(e in lab for e in es):
            out[((i, j), v)] = tuple(lab[e] for e in es)
    return out

if __name__ == '__main__':
    R = float(sys.argv[1]) if len(sys.argv) > 1 else 40
    V = C.vertices(R); T = C.tiles(V)
    lab = edge_labels(V, R - 6)
    tl = tile_labels(T, lab)
    from collections import Counter
    per_dir = {k: Counter(l for (x, kk), l in lab.items() if kk == k) for k in range(4)}
    for k in range(4): print('direction', k, 'distinct edge labels', len(per_dir[k]), dict(per_dir[k].most_common(3)) if False else '')
    types = Counter((t[0], labs) for t, labs in tl.items())
    print('labelled tile types (shape + 4 edge labels):', len(types))
    print('per shape:', sorted(Counter(k[0] for k in types).items()))
