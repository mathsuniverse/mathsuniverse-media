"""Targeted search at the period threshold (k >= 3) on Modal: random balanced shapes of chosen sizes, sieved,
OPEN shapes and near-misses kept. Sizes beyond any exhaustive list.

    py -m modal run modal_target.py --grid kite --sizes 8 --samples 20000                 # control: finds the hat
    py -m modal run modal_target.py --grid silverkite --sizes 21,27,33 --samples 2000000  # silver, k = 4 sizes
Results: results/target/<grid>.json. Any OPEN shape: measure with meter.py (ratio golden / silver / sqrt3).
"""
import json, os, sys
import modal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
image = (modal.Image.debian_slim(python_version="3.11").pip_install("python-sat==1.9.dev17")
         .add_local_dir(HERE, "/root/ms", ignore=["results/**", "logs/**", "open/**", "heesch/**",
                                                   "candidates/**", "__pycache__/**", "*.png"]))
app = modal.App("monotile-target", image=image)


@app.function(cpu=1.0, memory=2048, timeout=3600, retries=1, max_containers=100)
def chunk(grid, n, seed, count):
    sys.path.insert(0, "/root/ms")
    import ab_explore
    return ab_explore.explore_chunk(grid, n, seed, count)


@app.local_entrypoint()
def main(grid: str = "silverkite", sizes: str = "21", samples: int = 200000, per_call: int = 2000, seed: int = 1):
    out_dir = os.path.join(HERE, "results", "target"); os.makedirs(out_dir, exist_ok=True)
    path = os.path.join(out_dir, f"{grid}.json")
    res = json.load(open(path)) if os.path.exists(path) else {}
    for n in [int(x) for x in sizes.split(",")]:
        jobs = [(grid, n, seed * 1000003 + n * 7919 + i, per_call) for i in range(max(1, samples // per_call))]
        tot = {}; opens, near = [], []
        for k, (c, o, nr) in enumerate(chunk.starmap(jobs, order_outputs=False), start=1):
            for a, b in c.items():
                tot[a] = tot.get(a, 0) + b
            opens += o; near += nr
            for r in o:
                print(f"   OPEN {grid} n={n}: {r['cells']}", flush=True)
            if k % 50 == 0:
                print(f"  {grid} n={n}: {k}/{len(jobs)} jobs  {tot}  near-misses {len(near)}", flush=True)
        near.sort(key=lambda r: -(r.get('fail_R') or 0))
        res[str(n)] = dict(counts=tot, opens=opens, near=near[:200], samples=samples)
        json.dump(res, open(path, "w"), indent=1)
        print(f"{grid} n={n}: {tot}  OPEN {len(opens)}  near-misses {len(near)}"
              f"{'  best near-miss fails at R=' + str(near[0].get('fail_R')) if near else ''}", flush=True)
    print("Done. Results in", path)
