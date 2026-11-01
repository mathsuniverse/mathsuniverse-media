"""Covering by the regular n-gon cluster (n = 8 AB, 10 P3, 12 SH), Gummelt / Jeong-Steinhardt style.

A copy of the unit-edge regular n-gon counts as an occurrence if it is exactly a union of tiles of the
patch (tiles with centroid inside the polygon have total area = polygon area). Overlaps between copies
are allowed. We report the fraction of interior tiles (centroid <= RC) lying in some occurrence.
For P3 the decagon is the shape of Gummelt's covering cluster (there with decorations and overlap rules);
this plain test only asks whether the undecorated decagon clusters cover.
"""
import json
import math
import sys

import numpy as np
from scipy.spatial import cKDTree
from shapely.geometry import Point, Polygon

from covering import Patch, render_cover

NGON = {"AB": 8, "P3": 10, "SH": 12}

if __name__ == "__main__":
    name = sys.argv[1]
    RP, RC = float(sys.argv[2]), float(sys.argv[3])
    P = Patch(name, RP)
    n = NGON[name]
    area_t = []
    for vs in P.verts:
        Q = np.array([P.pos[v] for v in vs])
        area_t.append(Polygon(Q).area)
    cen = np.array(P.cen)
    tree = cKDTree(cen)
    interior = {i for i, r in enumerate(P.rad) if r <= RC}
    R_circ = 1 / (2 * math.sin(math.pi / n))
    A_ngon = n / 4 / math.tan(math.pi / n)
    seen = set()
    occ = []
    for v, p in P.pos.items():
        if np.hypot(*p) > RC + 2 * R_circ:
            continue
        for m in range(n):
            th = 2 * math.pi * m / n
            corners = [np.array(p)]
            for k in range(n - 1):
                a = th + 2 * math.pi * k / n
                corners.append(corners[-1] + [math.cos(a), math.sin(a)])
            poly = Polygon(corners)
            c = poly.centroid
            key = (round(c.x, 6), round(c.y, 6))
            if key in seen:
                continue
            seen.add(key)
            cand = tree.query_ball_point([c.x, c.y], R_circ + 0.01)
            inside = [i for i in cand if poly.contains(Point(cen[i]))]
            if inside and abs(sum(area_t[i] for i in inside) - A_ngon) < 1e-6 and \
                    max(P.rad[i] for i in inside) < RP - 1:
                occ.append(sorted(inside))
    covered = set()
    for o in occ:
        covered |= set(o) & interior
    todo = set(interior)
    chosen = []
    cands = [set(o) for o in occ]
    while todo and cands:
        c = max(cands, key=lambda s: len(s & todo))
        if not (c & todo):
            break
        todo -= c
        chosen.append(sorted(c))
    from collections import Counter
    comp = Counter(tuple(sorted(Counter(P.types[i] for i in o).items())) for o in occ)
    res = {"system": name, "ngon": n, "RC": RC, "interior_tiles": len(interior),
           "occurrences": len(occ), "compositions": {str(k): v for k, v in comp.items()},
           "covered_fraction": len(covered) / len(interior),
           "uncovered_by_type": dict(Counter(P.types[i] for i in interior - covered)),
           "greedy_copies": len(chosen)}
    print(json.dumps(res))
    json.dump(res, open(f"results/cover_ngon_{name}.json", "w"), indent=1)
    render_cover(P, chosen, f"cover_ngon_{name}.png",
                 f"{name}: unit {n}-gon clusters, covered {res['covered_fraction']:.3f} of disc R={RC:g}")
