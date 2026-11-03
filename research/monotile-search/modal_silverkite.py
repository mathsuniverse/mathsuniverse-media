"""Silver kite grid, sizes 15, 18, ...: only shapes with the grid's own balance (2 kites per square) can tile,
so we enumerate just those (capped growth, exact) and sieve them on Modal like modal_sieve.py.

    py -m modal run modal_silverkite.py --n 15
Results: results/modal/silverkite<n>_shapes.json.gz and results/modal/silverkite.json (same format as modal_sieve),
so `py -m modal run modal_meter.py --grid silverkite --n 15` measures any OPEN shape afterwards.
"""
import os
import sys

import modal

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
image = (modal.Image.debian_slim(python_version="3.11").pip_install("python-sat==1.9.dev17")
         .add_local_dir(HERE, "/root/ms", ignore=["results/**", "logs/**", "open/**", "heesch/**",
                                                   "candidates/**", "__pycache__/**", "*.png"]))
app = modal.App("silverkite", image=image)


@app.function(cpu=4.0, memory=65536, timeout=6 * 3600)
def enumerate_balanced(n: int):
    sys.path.insert(0, "/root/ms")
    import capped, engine as E, grids as G
    g = G.get('silverkite')
    level = capped.enumerate_capped(g, n)
    reps = [rep for rep, _ in E.free_classes(g, level)]
    return [[list(c) for c in rep] for rep in reps], len(level)


@app.function(cpu=1.0, memory=2048, timeout=3600, retries=1, max_containers=100)
def classify(grid, cfg, xs):
    sys.path.insert(0, "/root/ms")
    import parallel_core
    return parallel_core.classify_chunk(grid, cfg, xs)


@app.function(cpu=1.0, memory=2048, timeout=3600, retries=1, max_containers=100)
def verify(grid, recs):
    sys.path.insert(0, "/root/ms")
    import parallel_core
    return parallel_core.verify_chunk(grid, recs)


@app.local_entrypoint()
def main(n: int = 15, chunk: int = 40):
    import parallel_core as P
    fns = {"classify": classify, "verify": verify}
    mapper = lambda f, args: list(fns[f].starmap(args))  # noqa: E731
    reps, n_sym = enumerate_balanced.remote(n)
    print(f"silverkite n={n}: {len(reps)} balanced shapes ({2 * (n // 3)} kites + {n // 3} squares), testing ...", flush=True)
    summary, recs = P.run_sieve("silverkite", n, reps, n_sym, mapper, chunk=chunk)
    summary['note'] = 'balanced shapes only (kites = 2 x squares); all others cannot tile the grid'
    P.save(os.path.join(HERE, "results", "modal"), "silverkite", n, summary, recs)
    print(f"silverkite n={n}: {summary['counts']}  verified {summary['verified']}  "
          f"verify failures {len(summary['verify_failures'])}  {summary['wall_time']}s", flush=True)
    for r in recs:
        if r["cls"] == "OPEN":
            print("   OPEN", r["id"], r["cells"], flush=True)
    print("Done.")
