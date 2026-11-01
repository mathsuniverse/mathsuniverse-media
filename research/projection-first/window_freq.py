"""Exact tile frequencies from window areas (model-set formula).

For a model set with window W, a tile with vertex offsets u_0 = 0, u_1, ... (lattice vectors) occurs
at reference vertex x iff x* + u_i* lies in W for all i (given the face structure verified in the
generator). So its frequency per unit area = area( intersection_i (W - u_i*) ) / covolume.
Summing over the orientations of each prototype (group orbit modulo translation) gives the prototile
frequencies; ratios are compared with closed forms in Q(sqrt 2) / Q(sqrt 3).
Applied to: AB (Z^4, octagon window) and the 12-fold shield tiling (Z^4, dodecagon window).
"""
import itertools
import json
import math

import numpy as np
from shapely import affinity
from shapely.geometry import Polygon


def orbit(proto, group, reduce=lambda v: v):
    seen = {}
    for M in group:
        vs = [tuple(int(x) for x in (M @ np.array(v))) for v in proto]
        m = min(vs)
        key = tuple(sorted(tuple(a - b for a, b in zip(v, m)) for v in vs))
        seen[key] = key
    return list(seen.values())


def acceptance_area(offsets, W, perp):
    A = W
    for u in offsets:
        p = np.array(u) @ perp
        A = A.intersection(affinity.translate(W, -p[0], -p[1]))
        if A.is_empty:
            return 0.0
    return A.area


def run_ab():
    from projection import make_system, multigrid
    S = make_system("AB")
    perp = S.Eperp
    cube = np.array(list(itertools.product([0, 1], repeat=4))) @ perp
    from scipy.spatial import ConvexHull
    h = ConvexHull(cube)
    W = Polygon(cube[h.vertices])
    _, tiles, _, _ = multigrid("AB", 6)
    protos = {}
    for t in tiles:
        protos.setdefault(t.type, t.verts)
    G = S.group()
    freq = {}
    for typ, proto in protos.items():
        orb = orbit(proto, G)
        freq[typ] = sum(acceptance_area(o, W, perp) for o in orb)
        freq[typ + "_orientations"] = len(orb)
    r = freq["rhomb"] / freq["square"]
    return {"window": "regular octagon, area %.12f" % W.area, "acceptance_area_sum": freq,
            "rhomb/square": r, "sqrt2": math.sqrt(2), "abs_err": abs(r - math.sqrt(2))}


def run_shield():
    import dodecagonal as D
    perp4 = np.array([[z.real, z.imag] for z in D.PERP])
    r = 1.0
    W = Polygon([(r * math.cos(k * math.pi / 6), r * math.sin(k * math.pi / 6)) for k in range(12)])
    pts, nbrs, tiles, margin = D.tiling(8, rscale=2 * math.sin(math.pi / 12))
    protos = {}
    for f, typ, cen in tiles:
        protos.setdefault(typ, list(f))
    G = D.group()
    freq = {}
    for typ, proto in protos.items():
        orb = orbit(proto, G)
        freq[typ] = sum(acceptance_area(o, W, perp4) for o in orb)
        freq[typ + "_orientations"] = len(orb)
    s3 = math.sqrt(3)
    out = {"window": "regular dodecagon, circumradius 1, area %.12f" % W.area, "acceptance_area_sum": freq}
    out["square/shield"] = freq["square"] / freq["poly6"]
    out["triangle/shield"] = freq["triangle"] / freq["poly6"]
    out["triangle/square"] = freq["triangle"] / freq["square"]
    # identify a + b*sqrt3 with small rationals
    def ident(x):
        best = None
        for q in range(1, 13):
            for b in range(-30, 31):
                a = round((x - b / q * s3) * q)
                err = abs(x - (a + b * s3) / q)
                if best is None or err < best[0] - 1e-12:
                    best = (err, f"({a} + {b}*sqrt3)/{q}")
        return best
    for k in ("square/shield", "triangle/shield", "triangle/square"):
        e, f = ident(out[k])
        out[k + " closed form"] = f
        out[k + " residual"] = e
    return out


if __name__ == "__main__":
    res = {"AB": run_ab(), "SH": run_shield()}
    print(json.dumps(res, indent=1))
    json.dump(res, open("window_frequencies.json", "w"), indent=1)
