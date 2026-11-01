"""Shapes = unions of tiles, handled exactly through their boundary edges.

A region is determined by its set of boundary unit edges (edges used by an odd number of its tiles).
Canonical form under the point group (rotations by 2*pi/order and reflections) plus translations:
transform every boundary edge exactly in lattice coordinates, translate the lexicographically least
start vertex to 0, sort; take the minimum over the group.
"""
from collections import defaultdict

import numpy as np


class Geometry:
    def __init__(self, S, tiles):
        self.S = S
        self.tiles = tiles
        N = S.N
        self.N = N
        self.B = 1 << 10
        # edges
        self.edge_id = {}
        self.edge_list = []
        self.tile_edges = []
        for t in tiles:
            ids = []
            for e in t.edges:
                if e not in self.edge_id:
                    self.edge_id[e] = len(self.edge_list)
                    self.edge_list.append(e)
                ids.append(self.edge_id[e])
            self.tile_edges.append(tuple(ids))
        self.edge_code = [self.enc(v) * 16 + d for (v, d) in self.edge_list]
        # adjacency
        e2t = defaultdict(list)
        for i, ids in enumerate(self.tile_edges):
            for e in ids:
                e2t[e].append(i)
        self.adj = [set() for _ in tiles]
        for e, ts in e2t.items():
            for a in ts:
                for b in ts:
                    if a != b:
                        self.adj[a].add(b)
        self.adj = [frozenset(a) for a in self.adj]
        self.group = S.group()
        # action on directions: M e_j = s * e_j'
        self.gdir = []
        for M in self.group:
            m = []
            for j in range(N):
                col = M[:, j]
                if S.reduce_ones:
                    col = np.array(S.reduce(tuple(col)))
                nz = [i for i in range(N) if col[i] != 0]
                # for Penrose, -e_j reduced: e.g. -e_4 is (0,0,0,0,-1)->(1,1,1,1,0); handle generally
                found = None
                for jj in range(N):
                    for s in (1, -1):
                        u = [0] * N
                        u[jj] = s
                        if tuple(S.reduce(tuple(u))) == tuple(col):
                            found = (s, jj)
                assert found is not None, (M, j, col)
                m.append(found)
            self.gdir.append(m)
        self.area = {}
        for t in tiles:
            a_, b_ = S.E[t.j], S.E[t.k]
            self.area[t.type] = abs(a_[0] * b_[1] - a_[1] * b_[0])

    def enc(self, v):
        B = self.B
        x = 0
        for i, c in enumerate(v):
            x += c * B ** i
        return x

    # ------------------------------------------------------------ translation key of a cluster
    def odd_edges(self, cluster):
        odd = set()
        for t in cluster:
            for e in self.tile_edges[t]:
                if e in odd:
                    odd.remove(e)
                else:
                    odd.add(e)
        return odd

    def trans_key_from_odd(self, odd):
        codes = sorted(self.edge_code[e] for e in odd)
        m = codes[0] - (codes[0] % 16)  # min E * 16
        # note: min code has min E (codes sorted by E first since |d|<16)
        return tuple(c - m for c in codes)

    # ------------------------------------------------------------ canonical under the group
    def transform_edges(self, edges, gi):
        S = self.S
        M = self.group[gi]
        dm = self.gdir[gi]
        out = []
        N = self.N
        for (v, j) in edges:
            w = M @ np.array(v)
            s, jj = dm[j]
            if s == -1:
                w = w.copy()
                w[jj] -= 1
            w = S.reduce(tuple(int(x) for x in w))
            out.append((w, jj))
        return out

    def norm(self, edges):
        m = min(v for v, _ in edges)
        return tuple(sorted((tuple(a - b for a, b in zip(v, m)), j) for v, j in edges))

    def canonical(self, edges):
        best = None
        stab = 0
        keys = []
        for gi in range(len(self.group)):
            k = self.norm(self.transform_edges(edges, gi))
            keys.append(k)
            if best is None or k < best:
                best = k
        stab = sum(1 for k in keys if k == best)
        return best, stab

    def cluster_edges(self, cluster):
        return [self.edge_list[e] for e in self.odd_edges(cluster)]

    # ------------------------------------------------------------ boundary word
    def boundary_word(self, edges):
        """edges: undirected boundary edges of a region given with its tiles' orientation unknown.
        We orient using the tiles: caller passes cluster instead (see cluster_word)."""
        raise NotImplementedError

    def cluster_word(self, cluster):
        """Counter-clockwise boundary as a cyclic word of step directions in Z_{2*order/2}:
        AB: steps are zeta8^d, d in 0..7 (e_j = d=j, -e_j = d=j+4).
        P3: steps are zeta10^d, d in 0..9 (e_j = d=2j mod 10, -e_j = d=2j+5 mod 10).
        Returns (word, start_vertex) or (None, reason) if the boundary is not a single simple cycle."""
        S = self.S
        N = self.N
        n2 = S.order

        def dcode(j, s):
            if S.name == "AB":
                return j if s > 0 else j + 4
            if S.name == "SQ":
                return j if s > 0 else j + 2
            return (2 * j) % 10 if s > 0 else (2 * j + 5) % 10

        directed = []  # (start, end, d)
        odd = self.odd_edges(cluster)
        oddset = set(self.edge_list[e] for e in odd)
        for t in cluster:
            T = self.tiles[t]
            a_, b_ = S.E[T.j], S.E[T.k]
            ccw = (a_[0] * b_[1] - a_[1] * b_[0]) > 0
            V = T.verts
            # tile path v0 -> v1 (+e_j) -> v2 (+e_k) -> v3 (-e_j) -> v0 (-e_k)
            steps = [(V[0], V[1], (V[0], T.j), dcode(T.j, 1)),
                     (V[1], V[2], (V[1], T.k), dcode(T.k, 1)),
                     (V[2], V[3], (V[3], T.j), dcode(T.j, -1)),
                     (V[3], V[0], (V[0], T.k), dcode(T.k, -1))]
            for (p, q, und, d) in steps:
                if und in oddset:
                    if ccw:
                        directed.append((p, q, d))
                    else:
                        directed.append((q, p, (d + n2 // 2) % n2))
        out = defaultdict(list)
        for (p, q, d) in directed:
            out[p].append((q, d))
        if any(len(v) != 1 for v in out.values()):
            return None, "pinch"
        start = min(out)
        word = []
        p = start
        while True:
            q, d = out[p][0]
            word.append(d)
            p = q
            if p == start:
                break
        if len(word) != len(directed):
            return None, "multiple cycles (hole)"
        return word, start


# ------------------------------------------------------------------ periodicity criteria on words

def hat(seg, n2):
    return [(d + n2 // 2) % n2 for d in reversed(seg)]


def bn_translation(word, n2):
    """Beauquier-Nivat (factor points restricted to unit-step vertices): word = A B C hat(A) hat(B)
    hat(C) (C may be empty: parallelogram case). Returns factorization or None. Passing => S tiles
    the plane by a lattice of translations => periodic."""
    L = len(word)
    if L % 2:
        return None
    h = L // 2
    w2 = word + word
    for s in range(h):
        X = w2[s:s + h]
        Y = w2[s + h:s + L]
        for a in range(1, h):
            for b in range(1, h - a + 1):
                c = h - a - b
                A, B_, C = X[:a], X[a:a + b], X[a + b:]
                if Y == hat(A, n2) + hat(B_, n2) + hat(C, n2):
                    return {"shift": s, "A": a, "B": b, "C": c}
    return None


def conway(word, n2):
    """Conway criterion (factor points at unit-step vertices): word = A B C D E F with D = hat(A)
    (A, D translates) and B, C, E, F each centrosymmetric (palindromic as step words; may be empty).
    Passing => isohedral p2 tiling => periodic."""
    L = len(word)
    w2 = word + word
    # pal[i][m]: w2[i:i+m] is a palindrome
    pal = [[False] * (L + 1) for _ in range(2 * L)]
    for i in range(2 * L):
        for m in range(0, L + 1):
            if i + m > 2 * L:
                break
            seg = w2[i:i + m]
            pal[i][m] = seg == seg[::-1]
    for s in range(L):
        for a in range(0, L // 2 + 1):
            for b in range(0, L - 2 * a + 1):
                if not pal[s + a][b]:
                    continue
                for c in range(0, L - 2 * a - b + 1):
                    if not pal[s + a + b][c]:
                        continue
                    i_d = s + a + b + c
                    if w2[i_d:i_d + a] != hat(w2[s:s + a], n2):
                        continue
                    rest = L - 2 * a - b - c
                    i_e = i_d + a
                    for e in range(0, rest + 1):
                        f = rest - e
                        if pal[i_e][e] and pal[i_e + e][f]:
                            return {"shift": s, "A": a, "B": b, "C": c, "E": e, "F": f}
    return None
