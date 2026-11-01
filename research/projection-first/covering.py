"""Covering-cluster test (Gummelt-style, overlaps allowed).

Question: is there ONE cluster C (a configuration of tiles of the tiling, up to rotation/reflection)
whose copies, as they occur in the tiling, cover every tile? Overlaps are allowed (this is weaker than
a partition, so Lemma A does not apply). Done twice:
  * undecorated: tiles compared by shape only;
  * decorated:   each tile carries its vertex-collar (all tiles sharing a vertex with it), i.e. two
                 copies of C are equivalent only if C together with its collar is congruent.
                 This stands in for matching-rule decorations (arrows / Ammann bars), which for these
                 tilings are locally derivable from a finite collar; the 1-vertex-collar is our proxy.
Clusters searched:
  (1) exhaustive: all edge-connected clusters of k tiles, k = 1..KMAX;
  (2) round clusters: C_rho(v) = all tiles whose centroid lies within rho of a vertex v (the shape of
      Gummelt's decagon / octagon covering clusters), rho increasing.
Covered region: tiles with centroid <= RC. Patch generated to RP so that collars are complete.
"""
import json
import math
import sys
import time
from collections import Counter, defaultdict

import numpy as np


class Patch:
    def __init__(self, name, RP):
        self.name = name
        if name in ("AB", "P3"):
            from projection import multigrid
            S, tiles, gamma, margin = multigrid(name, RP)
            self.reduce = S.reduce
            self.group = S.group()
            self.verts = [tuple(t.verts) for t in tiles]
            self.types = [t.type for t in tiles]
            self.cen = [t.centroid for t in tiles]
            self.N = S.N
            self.pos = {v: S.pos(v) for vs in self.verts for v in vs}
        elif name == "SH":  # 12-fold shield tiling (Z^4 model set, dodecagon window)
            import dodecagonal as D
            rs = 2 * math.sin(math.pi / 12)
            pts, nbrs, tl, margin = D.tiling(RP, rscale=rs)
            self.reduce = lambda v: tuple(v)
            self.group = D.group()
            self.verts = [t[0] for t in tl]
            self.types = [t[1] for t in tl]
            self.cen = [(t[2].real, t[2].imag) for t in tl]
            self.N = 4
            self.pos = {v: np.array([pts[v].real, pts[v].imag]) for vs in self.verts for v in vs}
        self.rad = [math.hypot(*c) for c in self.cen]
        # adjacency by shared edge and by shared vertex
        e2t = defaultdict(list)
        v2t = defaultdict(list)
        self.tile_edges = []
        eid = {}
        for i, vs in enumerate(self.verts):
            ids = []
            for a in range(len(vs)):
                e = frozenset((vs[a], vs[(a + 1) % len(vs)]))
                if e not in eid:
                    eid[e] = len(eid)
                ids.append(eid[e])
                e2t[eid[e]].append(i)
            self.tile_edges.append(tuple(ids))
            for v in vs:
                v2t[v].append(i)
        self.v2t = v2t
        n = len(self.verts)
        self.adj = [set() for _ in range(n)]
        self.vadj = [set() for _ in range(n)]
        for ts in e2t.values():
            for a in ts:
                for b in ts:
                    if a != b:
                        self.adj[a].add(b)
        for ts in v2t.values():
            for a in ts:
                for b in ts:
                    if a != b:
                        self.vadj[a].add(b)
        self.adj = [frozenset(a) for a in self.adj]
        self.Ms = [np.array(M) for M in self.group]

    # ------------------------------------------------------------- canonical forms
    def trans_key(self, items):
        """items: list of (tile_index, flag). Translation-normalised exact key."""
        allv = [v for t, _ in items for v in self.verts[t]]
        m = min(allv)
        return tuple(sorted((tuple(sorted(tuple(a - b for a, b in zip(v, m)) for v in self.verts[t])), f)
                            for t, f in items))

    def canonical(self, items):
        best = None
        for M in self.Ms:
            tl = []
            V = np.array([v for t, _ in items for v in self.verts[t]]) @ M.T
            pos = 0
            for t, f in items:
                n = len(self.verts[t])
                vs = [self.reduce(tuple(int(x) for x in row)) for row in V[pos:pos + n]]
                pos += n
                tl.append((vs, f))
            m = min(v for vs, _ in tl for v in vs)
            k = tuple(sorted((tuple(sorted(tuple(a - b for a, b in zip(v, m)) for v in vs)), f)
                             for vs, f in tl))
            if best is None or k < best:
                best = k
        return best

    def collar(self, cluster):
        cs = set(cluster)
        col = set()
        for t in cluster:
            col |= self.vadj[t]
        return col - cs


def run_cover(P, RC, kmax, rhos, decorated_list=(False, True), log=print):
    interior = {i for i, r in enumerate(P.rad) if r <= RC}
    RP = max(P.rad)
    out = {"system": P.name, "RC": RC, "interior_tiles": len(interior), "patch_tiles": len(P.rad),
           "interior_counts": dict(Counter(P.types[i] for i in interior))}
    from merge_search import esu

    for dec in decorated_list:
        tag = "decorated" if dec else "plain"
        # ---- exhaustive clusters
        cache = {}
        cover = defaultdict(set)
        occ = Counter()
        ksz = {}
        t0 = time.time()
        allowed = [i for i, r in enumerate(P.rad) if r <= RP - 2.5]

        def emit(sub, odd):
            if not any(t in interior for t in sub):
                return
            items = [(t, 1) for t in sub]
            if dec:
                items += [(t, 0) for t in P.collar(sub)]
            tk = P.trans_key(items)
            cid = cache.get(tk)
            if cid is None:
                cid = P.canonical(items)
                cache[tk] = cid
            cover[cid].update(t for t in sub if t in interior)
            occ[cid] += 1
            ksz[cid] = len(sub)

        esu(P, allowed, kmax, emit)
        best = {}
        for cid, cov in cover.items():
            k = ksz[cid]
            frac = len(cov) / len(interior)
            if k not in best or frac > best[k][0]:
                best[k] = (frac, cid)
        classes_per_k = Counter(ksz.values())
        res = {"classes_per_k": dict(sorted(classes_per_k.items())),
               "best_cover_fraction_per_k": {k: round(v[0], 4) for k, v in sorted(best.items())},
               "seconds": round(time.time() - t0, 1)}
        full = sorted(k for k, v in best.items() if v[0] == 1.0)
        res["min_k_full_cover"] = full[0] if full else None
        if full:
            k0 = full[0]
            winners = [cid for cid, cov in cover.items() if ksz[cid] == k0 and len(cov) == len(interior)]
            res["n_covering_classes_at_min_k"] = len(winners)
            res["covering_examples"] = [describe(P, cid) for cid in winners[:3]]
        out[f"exhaustive_{tag}"] = res
        log(P.name, tag, "exhaustive", json.dumps({k: v for k, v in res.items() if k != "covering_examples"}))
        # ---- round clusters around vertices
        rr = []
        from scipy.spatial import cKDTree
        tree = cKDTree(np.array(P.cen))
        for rho in rhos:
            centers = [v for v in P.v2t if np.hypot(*P.pos[v]) <= RC + rho + 0.5]
            cover = defaultdict(set)
            sizes = {}
            cache = {}
            groups = defaultdict(list)
            for v in centers:
                pv = P.pos[v]
                cl = sorted(tree.query_ball_point(pv, rho))
                if not cl or max(P.rad[i] for i in cl) > RP - 2.5:
                    continue
                items = [(t, 1) for t in cl]
                if dec:
                    items += [(t, 0) for t in P.collar(cl)]
                tk = P.trans_key(items)
                cid = cache.get(tk)
                if cid is None:
                    cid = P.canonical(items)
                    cache[tk] = cid
                cover[cid].update(t for t in cl if t in interior)
                sizes[cid] = len(cl)
                groups[cid].append(cl)
            best_cid = max(cover, key=lambda c: len(cover[c]))
            frac = len(cover[best_cid]) / len(interior)
            row = {"rho": rho, "classes": len(cover), "best_fraction": round(frac, 4),
                   "best_size": sizes[best_cid]}
            if frac == 1.0:
                # greedy set cover with copies of the best class -> number of copies, overlap factor
                todo = set(interior)
                cnt = 0
                cands = [set(c) for c in groups[best_cid]]
                chosen = []
                while todo:
                    c = max(cands, key=lambda s: len(s & todo))
                    if not (c & todo):
                        break
                    todo -= c
                    chosen.append(sorted(c))
                    cnt += 1
                row["greedy_copies"] = cnt
                row["overlap_factor"] = round(cnt * sizes[best_cid] / len(interior), 3)
                row["example"] = describe(P, best_cid)
                row["chosen"] = chosen
            rr.append(row)
            log(P.name, tag, "round", json.dumps({k: v for k, v in row.items() if k not in ("example", "chosen")}))
            if frac == 1.0:
                break
        out[f"round_{tag}"] = rr
    return out


def describe(P, cid):
    inner = [t for t, f in cid if f == 1]
    return {"tiles": len(inner), "collar_tiles": len(cid) - len(inner)}


def render_cover(P, chosen, path, title):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon
    fig, ax = plt.subplots(figsize=(8, 8))
    col = {"square": "#e8a33d", "rhomb": "#3d7fe8", "thick": "#e8a33d", "thin": "#3d7fe8",
           "triangle": "#3d7fe8", "poly6": "#5fb35f"}
    for i, vs in enumerate(P.verts):
        Q = np.array([P.pos[v] for v in vs])
        ax.add_patch(Polygon(Q, closed=True, fc=col.get(P.types[i], "#ccc"), ec="k", lw=0.25, alpha=0.6))
    cmap = plt.get_cmap("tab10")
    for g, cl in enumerate(chosen):
        # outline the union boundary
        ec = Counter()
        for t in cl:
            vs = P.verts[t]
            for a in range(len(vs)):
                ec[frozenset((vs[a], vs[(a + 1) % len(vs)]))] += 1
        for e, c in ec.items():
            if c == 1:
                a, b = [P.pos[v] for v in e]
                ax.plot([a[0], b[0]], [a[1], b[1]], "-", color=cmap(g % 10), lw=1.6)
    ax.set_aspect("equal")
    lim = max(P.rad) * 0.75
    ax.set_xlim(-lim, lim)
    ax.set_ylim(-lim, lim)
    ax.axis("off")
    ax.set_title(title)
    fig.savefig(path, dpi=130, bbox_inches="tight")
    plt.close(fig)


if __name__ == "__main__":
    name = sys.argv[1]
    RP, RC, kmax = float(sys.argv[2]), float(sys.argv[3]), int(sys.argv[4])
    rhos = [float(x) for x in sys.argv[5].split(",")]
    P = Patch(name, RP)
    out = run_cover(P, RC, kmax, rhos, log=lambda *a: print(*a, flush=True))
    for tag in ("plain", "decorated"):
        rr = out.get(f"round_{tag}", [])
        if rr and "chosen" in rr[-1]:
            render_cover(P, rr[-1]["chosen"], f"cover_{name}_{tag}.png",
                         f"{name}: {tag} round cluster rho={rr[-1]['rho']} "
                         f"({rr[-1]['best_size']} tiles), {rr[-1]['greedy_copies']} copies")
            rr[-1]["chosen"] = len(rr[-1]["chosen"])
    json.dump(out, open(f"results/cover_{name}.json", "w"), indent=1, default=str)
