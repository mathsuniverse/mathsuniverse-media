"""Guided random monotile search on Modal: bigger shapes than any exhaustive list reaches.

Run from this folder (same setup as modal_sieve.py):
    py -m modal run modal_explore.py --grid kite --nmin 8 --nmax 8 --samples 2000        # control: must find the hat
    py -m modal run modal_explore.py --grid tetrakis --nmin 17 --nmax 24 --samples 50000  # the silver-direction grid
    py -m modal run modal_explore.py --grid tetrakis --nmin 26 --nmax 36 --step 2 --samples 50000   # even sizes only

Each worker draws random shapes of size n (growth with a random bias toward branchy outlines), tests each with the
three-outcome sieve (STUCK / PERIODIC / OPEN) and re-tests survivors with a bigger budget. Only OPEN shapes come back;
those are the candidates. Results: results/explore/<grid>.json. Cost: about 0.07 s of CPU per shape at n = 20.
"""
import json
import os
import sys

import modal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

image = (
    modal.Image.debian_slim(python_version="3.11")
    .pip_install("python-sat==1.9.dev17")
    .add_local_dir(HERE, "/root/ms", ignore=["results/**", "logs/**", "open/**", "heesch/**",
                                              "candidates/**", "__pycache__/**", "*.png"])
)
app = modal.App("monotile-explore", image=image)


@app.function(cpu=1.0, memory=2048, timeout=3600, retries=1, max_containers=100)
def chunk(grid, n, seed, count):
    sys.path.insert(0, "/root/ms")
    import explore_core
    return explore_core.explore_chunk(grid, n, seed, count)


@app.local_entrypoint()
def main(grid: str = "tetrakis", nmin: int = 17, nmax: int = 17, samples: int = 20000, per_call: int = 250,
         seed: int = 1, step: int = 1):
    out_dir = os.path.join(HERE, "results", "explore")
    os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{grid}.json")
    res = json.load(open(path)) if os.path.exists(path) else {}
    for n in range(nmin, nmax + 1, step):
        calls = max(1, samples // per_call)
        args = [(grid, n, seed * 1_000_003 + n * 10_007 + i, per_call) for i in range(calls)]
        tot = {"STUCK": 0, "PERIODIC": 0, "OPEN": 0, "dup": 0}
        opens = {}
        for counts, op in chunk.starmap(args):
            for k, v in counts.items():
                tot[k] += v
            for r in op:
                opens[json.dumps(sorted(map(tuple, r["cells"])))] = r
        prev = res.get(str(n), {"samples": 0, "counts": {k: 0 for k in tot}, "open": []})
        for k, v in tot.items():
            prev["counts"][k] = prev["counts"].get(k, 0) + v
        prev["samples"] += calls * per_call
        known = {json.dumps(sorted(map(tuple, r["cells"]))) for r in prev["open"]}
        prev["open"] += [r for k, r in opens.items() if k not in known]
        res[str(n)] = prev
        json.dump(res, open(path, "w"), indent=1)
        print(f"{grid} n={n}: {calls * per_call} drawn  {tot}", flush=True)
        for r in opens.values():
            print("   OPEN", r["cells"], flush=True)
    print("Done. Results in", path)
