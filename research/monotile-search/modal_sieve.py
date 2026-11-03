"""Run the monotile sieve on Modal: every shape is tested in parallel.

One-off setup (on your PC):
    pip install modal
    modal setup                      # opens the browser; you log in yourself

Run (from this folder):
    modal run modal_sieve.py --grid kite --nmin 11 --nmax 11
    modal run modal_sieve.py --grid drafter --nmin 14 --nmax 16
    modal run modal_sieve.py --grid kite --nmin 6 --nmax 6     # 1-minute smoke test

Results land in results/modal/<grid>.json (summary per size, same fields as sieve.py)
and results/modal/<grid><n>_shapes.json.gz (every shape's record and certificate).
OPEN shapes are printed at the end; those are the candidates.
Cost control: --max-containers caps parallel workers (default 100).
"""
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
app = modal.App("monotile-sieve", image=image)


def _core():
    sys.path.insert(0, "/root/ms")
    import parallel_core
    return parallel_core


@app.function(cpu=2.0, memory=32768, timeout=3 * 3600)
def enumerate_reps(grid: str, n: int):
    return _core().enumerate_reps(grid, n)


@app.function(cpu=1.0, memory=2048, timeout=3600, retries=1, max_containers=100)
def classify(grid, cfg, xs):
    return _core().classify_chunk(grid, cfg, xs)


@app.function(cpu=1.0, memory=2048, timeout=3600, retries=1, max_containers=100)
def verify(grid, recs):
    return _core().verify_chunk(grid, recs)


@app.local_entrypoint()
def main(grid: str = "kite", nmin: int = 6, nmax: int = 6, tcap: int = 12, rcap: float = 6.0,
         dovetail: str = "24:8,48:12", chunk: int = 40, shape_time: float = 300, no_verify: bool = False):
    import parallel_core as P
    stages = [(int(t), float(r)) for t, r in (p.split(":") for p in dovetail.split(",") if p)]
    fns = {"classify": classify, "verify": verify}
    mapper = lambda f, args: list(fns[f].starmap(args))  # noqa: E731  (keeps order)
    out = os.path.join(HERE, "results", "modal")
    for n in range(nmin, nmax + 1):
        reps, n_sym = enumerate_reps.remote(grid, n)
        print(f"{grid} n={n}: {len(reps)} free shapes, testing in parallel ...", flush=True)
        summary, recs = P.run_sieve(grid, n, reps, n_sym, mapper, tcap=tcap, rcap=rcap, stages=stages,
                                    chunk=chunk, shape_time=shape_time, verify=not no_verify)
        P.save(out, grid, n, summary, recs)
        print(f"{grid} n={n}: {summary['counts']}  verified {summary['verified']}  "
              f"verify failures {len(summary['verify_failures'])}  {summary['wall_time']}s", flush=True)
        for r in recs:
            if r["cls"] == "OPEN":
                print("   OPEN", r["id"], r["cells"], flush=True)
    print("Done. Results in", out)
