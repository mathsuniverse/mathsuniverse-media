"""Cut-and-project (de Bruijn multigrid) generators with exact combinatorics.

Silver: Ammann-Beenker (AB), lattice Z^4, star e_j = exp(i*j*pi/4), j = 0..3. Tiles: squares
(grid pairs at 90 deg) and 45-deg rhombs. Window: regular octagon = projection of [0,1)^4 to E_perp
(e_perp_j = exp(3i*j*pi/4)).

Golden: Penrose rhombs (P3), lattice Z^5, star e_j = exp(2i*j*pi/5), grid shifts summing to 0.
Tiles: thick (72 deg) and thin (36 deg) rhombs. Window: pentagons (slices of the projected 5-cube
at index sum K_i = 1..4).

Exactness: every vertex is an integer vector K (Z^4 for AB; Z^5 reduced mod (1,1,1,1,1) for
Penrose, since sum e_j = 0). The map K -> sum K_j e_j is injective on Z^4 (AB) and on Z^5/Z*ones
(Penrose), so plane positions, edges and adjacency are all exact integer data. Floating point is only
used to pick which side of each grid line a point lies on; we check the margin to every grid line.
"""
import math
import random
from dataclasses import dataclass, field

import numpy as np


@dataclass
class System:
    name: str
    N: int                 # number of grid families
    order: int             # rotation order of the point group (8 or 10)
    E: np.ndarray          # N x 2 physical star
    Eperp: np.ndarray      # N x 2 internal star
    reduce_ones: bool      # Penrose: reduce mod ones vector

    def reduce(self, K):
        if self.reduce_ones:
            c = K[-1]
            return tuple(k - c for k in K)
        return tuple(K)

    def pos(self, K):
        return np.asarray(K, float) @ self.E

    def tile_type(self, j, k):
        d = (k - j) % self.N
        if self.name == "AB":
            return "square" if d == 2 else "rhomb"
        if self.name == "SQ":
            return "square"
        return "thick" if d in (1, 4) else "thin"

    # --- exact point group on lattice coordinates (integer N x N matrices acting on column K) ---
    def group(self):
        N = self.N
        rot = np.zeros((N, N), int)
        ref = np.zeros((N, N), int)
        if self.name == "SQ":
            rot[1, 0] = 1
            rot[0, 1] = -1
            ref[0, 0] = 1
            ref[1, 1] = -1
        elif self.name == "AB":
            # zeta8 * e_j = e_{j+1} (j<3), zeta8 * e_3 = -e_0
            for j in range(N):
                if j < 3:
                    rot[j + 1, j] = 1
                else:
                    rot[0, j] = -1
            # conj: e_0 -> e_0, e_j -> -e_{4-j}
            ref[0, 0] = 1
            for j in range(1, 4):
                ref[4 - j, j] = -1
        else:
            # zeta10 * e_j = -e_{j+3}
            for j in range(N):
                rot[(j + 3) % 5, j] = -1
            for j in range(N):
                ref[(-j) % 5, j] = 1
        mats = []
        M = np.eye(N, dtype=int)
        for _ in range(self.order):
            mats.append(M.copy())
            mats.append(M @ ref)
            M = rot @ M
        return mats  # 2*order elements: rotations R^i and R^i * reflection


def make_system(name):
    if name == "AB":
        E = np.array([[math.cos(j * math.pi / 4), math.sin(j * math.pi / 4)] for j in range(4)])
        Ep = np.array([[math.cos(3 * j * math.pi / 4), math.sin(3 * j * math.pi / 4)] for j in range(4)])
        return System("AB", 4, 8, E, Ep, False)
    if name == "SQ":  # periodic control: square lattice (2 orthogonal grids)
        E = np.array([[1.0, 0.0], [0.0, 1.0]])
        return System("SQ", 2, 4, E, E.copy(), False)
    if name == "P3":
        E = np.array([[math.cos(2 * j * math.pi / 5), math.sin(2 * j * math.pi / 5)] for j in range(5)])
        Ep = np.array([[math.cos(4 * j * math.pi / 5), math.sin(4 * j * math.pi / 5)] for j in range(5)])
        return System("P3", 5, 10, E, Ep, True)
    raise ValueError(name)


@dataclass
class Tile:
    base: tuple          # reduced lattice coordinates of base vertex
    j: int
    k: int
    type: str
    verts: list          # 4 reduced lattice vectors, cyclic order
    centroid: tuple
    edges: list = field(default_factory=list)  # (start_vertex, dir) with dir in 0..N-1 (positive sense)


def unit(N, j):
    v = [0] * N
    v[j] = 1
    return v


def add(a, b):
    return tuple(x + y for x, y in zip(a, b))


def default_gamma(name, seed=1):
    rng = random.Random(seed)
    if name == "AB":
        return [rng.random() for _ in range(4)]
    if name == "SQ":
        return [rng.random() for _ in range(2)]
    g = [rng.random() - 0.5 for _ in range(4)]
    g.append(-sum(g))  # sum gamma = 0 -> Penrose P3 (de Bruijn)
    return g


def multigrid(name, R, gamma=None, seed=1):
    """Return (system, tiles) for all tiles whose centroid lies within distance R of the origin."""
    S = make_system(name)
    N = S.N
    gamma = default_gamma(name, seed) if gamma is None else gamma
    scale = N / 2.0  # sum_j (z.e_j) e_j = (N/2) z
    rho = R / scale + 3.0
    tiles = []
    min_margin = 1.0
    for j in range(N):
        for k in range(j + 1, N):
            A = np.array([S.E[j], S.E[k]])
            Ainv = np.linalg.inv(A)
            nmax = int(math.ceil(rho + 2))
            for nj in range(-nmax, nmax + 1):
                for nk in range(-nmax, nmax + 1):
                    z = Ainv @ np.array([nj - gamma[j], nk - gamma[k]])
                    if z @ z > rho * rho:
                        continue
                    K = [0] * N
                    for i in range(N):
                        if i == j:
                            K[i] = nj
                        elif i == k:
                            K[i] = nk
                        else:
                            t = z @ S.E[i] + gamma[i]
                            K[i] = math.ceil(t)
                            min_margin = min(min_margin, abs(t - round(t)))
                    K = tuple(K)
                    v0 = K
                    v1 = add(K, unit(N, j))
                    v2 = add(v1, unit(N, k))
                    v3 = add(K, unit(N, k))
                    c = S.pos(v0) + 0.5 * (S.E[j] + S.E[k])
                    if c @ c > R * R:
                        continue
                    verts = [S.reduce(v) for v in (v0, v1, v2, v3)]
                    t = Tile(S.reduce(K), j, k, S.tile_type(j, k), verts, (float(c[0]), float(c[1])))
                    b = verts[0]
                    t.edges = [(verts[0], j), (verts[0], k), (verts[1], k), (verts[3], j)]
                    tiles.append(t)
    return S, tiles, gamma, min_margin


# ----------------------------------------------------------------------------- validation

def check_tiling(S, tiles, R):
    """Edge-to-edge check: inside radius R-3, every edge is shared by exactly two tiles; no
    vertex/position collisions; area of tiles vs disc."""
    from collections import Counter
    ec = Counter()
    for t in tiles:
        for e in t.edges:
            ec[e] += 1
    bad = 0
    for (v, d), c in ec.items():
        p = S.pos(v) + 0.5 * S.E[d]
        if p @ p < (R - 3) ** 2 and c != 2:
            bad += 1
        if c > 2:
            bad += 1
    # exact positions are distinct lattice points -> injectivity check numerically
    pts = {}
    coll = 0
    for t in tiles:
        for v in t.verts:
            p = tuple(np.round(S.pos(v), 7))
            if p in pts and pts[p] != v:
                coll += 1
            pts[p] = v
    area = 0.0
    for t in tiles:
        a_, b_ = S.E[t.j], S.E[t.k]
        area += abs(a_[0] * b_[1] - a_[1] * b_[0])
    return {"bad_edges": bad, "position_collisions": coll, "tile_area": area,
            "disc_area": math.pi * R * R}


def window_check(S, tiles, gamma):
    """Check every vertex's internal-space coordinate lies in the window."""
    from scipy.spatial import ConvexHull, Delaunay
    import itertools
    N = S.N
    gam = np.array(gamma)
    # unreduced lift: for AB reduce is identity; for P3 we need the true lift with index in 1..4.
    # Recompute true lift from the reduced vector: K = Kred + c*ones with c chosen so that
    # perp(K) - offset lies in the projected cube; the index is sum(K).
    offset = gam @ S.Eperp
    cube = np.array(list(itertools.product([0, 1], repeat=N)))
    out = 0
    idx_counts = {}
    verts = {v for t in tiles for v in t.verts}
    if S.name == "AB":
        hull = Delaunay(cube @ S.Eperp)
        P = np.array([np.array(v) @ S.Eperp - offset for v in verts])
        out = int((hull.find_simplex(P) < 0).sum())
        # octagon check: regular octagon?
        h = ConvexHull(cube @ S.Eperp)
        return {"vertices": len(verts), "outside_window": out, "window_vertices": len(h.vertices),
                "window_area": h.volume}
    # Penrose: ones vector projects to 0 in E_perp too (sum e_perp_j = 0), so perp(K) is
    # independent of the lift; the index sum K_i of the true lift is determined by the tile
    # construction. Use slices: perp - offset must lie in the hull of the cube vertices with
    # coordinate sum s, for the true index s.
    slices = {}
    for s in range(1, N):
        pts = np.array([c for c in cube if c.sum() == s]) @ S.Eperp
        slices[s] = Delaunay(pts)
    for v in verts:
        p = np.array(v) @ S.Eperp - offset
        # true index: the reduced vector has last coord 0; true lift K = v + c*ones, index = sum(v)+5c.
        ok = False
        for s in range(1, N):
            if (s - sum(v)) % N == 0 and slices[s].find_simplex(p[None, :])[0] >= 0:
                ok = True
                idx_counts[s] = idx_counts.get(s, 0) + 1
                break
        if not ok:
            out += 1
    return {"vertices": len(verts), "outside_window": out, "index_counts": idx_counts}


def frequencies(tiles):
    from collections import Counter
    return Counter(t.type for t in tiles)


# ----------------------------------------------------------------------------- rendering

COLORS = {"square": "#e8a33d", "rhomb": "#3d7fe8", "thick": "#e8a33d", "thin": "#3d7fe8"}


def render(S, tiles, path, title=None, R=None, groups=None, highlight=None):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    fig, ax = plt.subplots(figsize=(8, 8))
    cmap = plt.get_cmap("tab20")
    gid = {}
    if groups is not None:
        for g, members in enumerate(groups):
            for m in members:
                gid[m] = g
    for i, t in enumerate(tiles):
        P = np.array([S.pos(v) for v in t.verts])
        if groups is not None:
            if i in gid:
                fc = cmap(gid[i] % 20)
            else:
                fc = "#dddddd"
        else:
            fc = COLORS[t.type]
        ax.add_patch(Polygon(P, closed=True, fc=fc, ec="k" if groups is None else "#00000040",
                             lw=0.3))
    if groups is not None:
        # draw group outlines
        from collections import Counter
        for members in groups:
            ec = Counter()
            for m in members:
                for e in tiles[m].edges:
                    ec[e] += 1
            for (v, d), c in ec.items():
                if c == 1:
                    a = S.pos(v)
                    b = a + S.E[d]
                    ax.plot([a[0], b[0]], [a[1], b[1]], "k-", lw=1.2)
    ax.set_aspect("equal")
    if R:
        ax.set_xlim(-R, R)
        ax.set_ylim(-R, R)
    ax.axis("off")
    if title:
        ax.set_title(title)
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    import json
    import sys
    out = {}
    for name in ("AB", "P3"):
        res = []
        for R in (10, 20, 40, 80, 160):
            S, tiles, gamma, margin = multigrid(name, R)
            f = frequencies(tiles)
            chk = check_tiling(S, tiles, R)
            win = window_check(S, tiles, gamma) if R <= 40 else None
            if name == "AB":
                ratio = f["rhomb"] / f["square"]
                target = math.sqrt(2)
                lab = "rhombs/squares"
            else:
                ratio = f["thick"] / f["thin"]
                target = (1 + math.sqrt(5)) / 2
                lab = "thick/thin"
            row = {"R": R, "tiles": len(tiles), "counts": dict(f), "ratio_label": lab,
                   "ratio": ratio, "target": target, "rel_err": abs(ratio - target) / target,
                   "grid_margin": margin, **chk}
            if win:
                row["window"] = win
            res.append(row)
            print(name, json.dumps(row, default=str))
            sys.stdout.flush()
            if R == 20:
                render(S, tiles, f"{name}_patch_R20.png", title=f"{name} patch R=20 ({len(tiles)} tiles)",
                       R=20)
        out[name] = res
    json.dump(out, open("validation.json", "w"), indent=1, default=str)
