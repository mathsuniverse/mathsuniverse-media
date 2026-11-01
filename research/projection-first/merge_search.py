"""Projection-first merge search.

For a cut-and-project patch (AB or P3), enumerate connected clusters of k tiles (k = 2..KMAX) that
occur in the patch, up to congruence of their union region. For each region S, ask: can the patch be
partitioned into congruent copies of S (each copy a union of patch tiles)?

Partition test at radius R (exact cover, SAT):
  interior  I_R = tiles with centroid |c| <= R           -> covered EXACTLY once
  buffer    B_R = tiles with R < |c| <= R + DELTA         -> covered AT MOST once
  placements = clusters of the patch congruent to S, all tiles in I_R u B_R, at least one in I_R.
Radii are increased along a schedule; a shape survives a radius if the instance is SAT.

Necessary counting condition (checked first): if S has a tiles of type 1 and b of type 2, there is
an integer m (number of copies) with a*m in [I1, I1+B1] and b*m in [I2, I2+B2].
"""
import json
import math
import os
import sys
import time
from collections import defaultdict

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Cadical153

from projection import multigrid, render
from shapes import Geometry

DELTA = 1.5


def esu(geom, allowed, kmax, emit):
    """Enumerate each connected subset (size 1..kmax) of the induced subgraph on `allowed` exactly
    once (Wernicke's ESU). emit(sub_tuple, odd_edge_set)."""
    adj = geom.adj
    tedges = geom.tile_edges
    allowed = set(allowed)
    nadj = {v: frozenset(u for u in adj[v] if u in allowed) for v in allowed}

    def toggle(odd, t):
        odd = set(odd)
        for e in tedges[t]:
            if e in odd:
                odd.remove(e)
            else:
                odd.add(e)
        return odd

    def extend(sub, closed, ext, v, odd):
        emit(sub, odd)
        if len(sub) == kmax:
            return
        ext = set(ext)
        while ext:
            w = ext.pop()
            new = [u for u in nadj[w] if u > v and u not in closed]
            ext2 = ext | set(new)
            extend(sub + (w,), closed | nadj[w], ext2, v, toggle(odd, w))

    for v in sorted(allowed):
        extend((v,), nadj[v] | {v}, {u for u in nadj[v] if u > v}, v, toggle(set(), v))


class Search:
    def __init__(self, name, Rmax, kmax, Rdisc):
        self.name = name
        self.Rmax = Rmax
        self.kmax = kmax
        S, tiles, gamma, margin = multigrid(name, Rmax + DELTA + 0.5)
        self.S, self.tiles = S, tiles
        self.geom = Geometry(S, tiles)
        self.types = {"AB": ("square", "rhomb"), "P3": ("thick", "thin"), "SQ": ("square", "none")}[name]
        self.rad = [math.hypot(*t.centroid) for t in tiles]
        self.tk2shape = {}     # translation key -> shape id
        self.shapes = []       # list of dicts
        self.key2shape = {}
        self.discover(Rdisc)

    def comp(self, cluster):
        a = sum(1 for t in cluster if self.tiles[t].type == self.types[0])
        return (a, len(cluster) - a)

    def shape_of(self, sub, odd):
        tk = self.geom.trans_key_from_odd(odd)
        sid = self.tk2shape.get(tk)
        if sid is None:
            edges = [self.geom.edge_list[e] for e in odd]
            ck, stab = self.geom.canonical(edges)
            sid = self.key2shape.get(ck)
            if sid is None:
                sid = len(self.shapes)
                word, start = self.geom.cluster_word(sub)
                self.shapes.append({"id": sid, "k": len(sub), "comp": self.comp(sub),
                                    "rep": list(sub), "stab": stab, "word": word,
                                    "simple": word is not None, "occ": 0, "status": "untested",
                                    "Rpass": None, "Rfail": None, "history": []})
                self.key2shape[ck] = sid
            self.tk2shape[tk] = sid
        return sid

    def discover(self, Rdisc):
        allowed = [i for i, r in enumerate(self.rad) if r <= Rdisc]
        t0 = time.time()
        cnt = [0]

        def emit(sub, odd):
            if len(sub) >= 1:
                sid = self.shape_of(sub, odd)
                self.shapes[sid]["occ"] += 1
                cnt[0] += 1

        esu(self.geom, allowed, self.kmax, emit)
        self.discover_stats = {"Rdisc": Rdisc, "tiles": len(allowed), "clusters": cnt[0],
                               "seconds": time.time() - t0}
        per_k = defaultdict(int)
        for s in self.shapes:
            per_k[s["k"]] += 1
        self.discover_stats["shapes_per_k"] = dict(sorted(per_k.items()))
        print("discover", self.name, json.dumps(self.discover_stats), flush=True)

    def placements(self, R, alive):
        allowed = [i for i, r in enumerate(self.rad) if r <= R + DELTA]
        kmax = max(self.shapes[s]["k"] for s in alive)
        P = defaultdict(list)
        alive = set(alive)

        def emit(sub, odd):
            sid = self.shape_of(sub, odd)
            if sid in alive:
                P[sid].append(sub)

        esu(self.geom, allowed, kmax, emit)
        return P

    def solve(self, sid, R, plist, conflicts=200000):
        interior = [i for i, r in enumerate(self.rad) if r <= R]
        inter = set(interior)
        buffer = [i for i, r in enumerate(self.rad) if R < r <= R + DELTA]
        sh = self.shapes[sid]
        a, b = sh["comp"]
        I = [sum(1 for t in interior if self.tiles[t].type == ty) for ty in self.types]
        Bc = [sum(1 for t in buffer if self.tiles[t].type == ty) for ty in self.types]
        ok = False
        for m in range(0, (I[0] + Bc[0] + I[1] + Bc[1]) // max(1, a + b) + 2):
            if I[0] <= a * m <= I[0] + Bc[0] and I[1] <= b * m <= I[1] + Bc[1]:
                ok = True
                break
        if not ok:
            return "UNSAT-count", None
        pl = [p for p in plist if any(t in inter for t in p)]
        cover = defaultdict(list)
        for v, p in enumerate(pl):
            for t in p:
                cover[t].append(v + 1)
        for t in interior:
            if not cover[t]:
                return "UNSAT-uncoverable", None
        pool = IDPool(start_from=len(pl) + 1)
        solver = Cadical153()
        for t, lits in cover.items():
            if t in inter:
                solver.add_clause(lits)
            if len(lits) > 1:
                enc = CardEnc.atmost(lits, 1, vpool=pool,
                                     encoding=EncType.pairwise if len(lits) <= 6 else EncType.seqcounter)
                for c in enc.clauses:
                    solver.add_clause(c)
        # conflict budget via solve_limited is not supported by CaDiCaL in pysat; use plain solve
        res = solver.solve()
        model = solver.get_model() if res else None
        solver.delete()
        if not res:
            return "UNSAT", None
        chosen = [pl[v - 1] for v in model if 0 < v <= len(pl)]
        return "SAT", chosen

    def run(self, schedule, logf):
        alive = [s["id"] for s in self.shapes if s["k"] >= 1]
        sols = {}
        for R in schedule:
            if not alive:
                break
            t0 = time.time()
            P = self.placements(R, alive)
            tp = time.time() - t0
            new_alive = []
            stats = defaultdict(int)
            for sid in alive:
                st, chosen = self.solve(sid, R, P.get(sid, []))
                sh = self.shapes[sid]
                sh["history"].append((R, st, len(P.get(sid, []))))
                stats[st] += 1
                if st == "SAT":
                    sh["Rpass"] = R
                    sols[sid] = (R, chosen)
                    new_alive.append(sid)
                else:
                    sh["Rfail"] = R
                    sh["status"] = st
            for sid in new_alive:
                self.shapes[sid]["status"] = "SAT@%g" % R
            line = {"system": self.name, "R": R, "alive_in": len(alive), "alive_out": len(new_alive),
                    "stats": dict(stats), "placement_seconds": round(tp, 1),
                    "total_seconds": round(time.time() - t0, 1)}
            print(json.dumps(line), flush=True)
            logf.write(json.dumps(line) + "\n")
            logf.flush()
            alive = new_alive
        return sols


def main():
    name = sys.argv[1]
    kmax = int(sys.argv[2])
    schedule = [float(x) for x in sys.argv[3].split(",")]
    Rdisc = float(sys.argv[4])
    os.makedirs("results", exist_ok=True)
    srch = Search(name, max(schedule), kmax, Rdisc)
    with open(f"results/{name}_k{kmax}_log.jsonl", "w") as logf:
        sols = srch.run(schedule, logf)
    out = {"system": name, "kmax": kmax, "schedule": schedule, "DELTA": DELTA,
           "discover": srch.discover_stats, "shapes": srch.shapes,
           "solutions": {sid: {"R": R, "copies": [list(c) for c in ch]} for sid, (R, ch) in sols.items()}}
    # keep only last-radius solutions of the best survivors to limit file size
    json.dump(out, open(f"results/{name}_k{kmax}.json", "w"), default=str)
    import pickle
    pickle.dump({"tiles_R": srch.Rmax}, open(f"results/{name}_k{kmax}.meta.pkl", "wb"))


if __name__ == "__main__":
    main()
