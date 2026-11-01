"""Render the best partition found for each surviving shape (and the shape itself)."""
import gzip
import json
import sys

from merge_search import DELTA
from projection import multigrid, render

path = sys.argv[1]
op = gzip.open if path.endswith(".gz") else open
d = json.load(op(path, "rt"))
name = d["system"]
S, tiles, gamma, margin = multigrid(name, max(d["schedule"]) + DELTA + 0.5)
for sid, sol in d["solutions"].items():
    sh = d["shapes"][int(sid)]
    R = sol["R"]
    keep = [i for i, t in enumerate(tiles) if (t.centroid[0] ** 2 + t.centroid[1] ** 2) ** 0.5 <= R + DELTA]
    idx = {i: n for n, i in enumerate(keep)}
    sub = [tiles[i] for i in keep]
    groups = [[idx[t] for t in c] for c in sol["copies"]]
    render(S, sub, f"partition_{name}_shape{sid}_R{R:g}.png",
           title=f"{name} shape #{sid} (k={sh['k']}, comp={tuple(sh['comp'])}): partition of disc R={R:g}"
                 f" (+buffer {DELTA}); fails at R={sh['Rfail']}", R=R + DELTA + 0.3, groups=groups)
    rep = [tiles[i] for i in sh["rep"]]
    render(S, rep, f"shape_{name}_{sid}.png", title=f"{name} shape #{sid}")
    print("rendered", sid)
