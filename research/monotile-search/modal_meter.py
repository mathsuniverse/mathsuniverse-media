"""Hierarchy meter on Modal: for every OPEN shape left by modal_sieve, build big SAT patches and measure
the ratio of unreflected to reflected copies. In an aperiodic monotile this ratio is forced by the hierarchy:
the hat gives phi^4 = 6.854 (golden). A silver tile would land on a power of 1+sqrt2 (2.414, 5.828, 14.07, 33.97),
a sqrt3 tile on 2+sqrt3 = 3.732 or 7+4sqrt3 = 13.93.

    py -m modal run modal_meter.py --grid kite --n 12
    py -m modal run modal_meter.py --grid drafter --n 16
    py -m modal run modal_meter.py --control        # the hat, to see the meter work (about 6.8)
Reads results/modal/<grid><n>_shapes.json.gz, writes results/modal/<grid><n>_meter.json.
"""
import gzip, json, math, os, sys
import modal

HERE = os.path.dirname(os.path.abspath(__file__))
image = (modal.Image.debian_slim(python_version="3.11").pip_install("python-sat==1.9.dev17")
         .add_local_dir(HERE, "/root/ms", ignore=["results/**", "logs/**", "open/**", "heesch/**",
                                                   "candidates/**", "__pycache__/**", "*.png"]))
app = modal.App("monotile-meter", image=image)
PHI, SIL = (1 + 5 ** .5) / 2, 1 + 2 ** .5
TARGETS = {f't={t} ({nm})': (t + (t * t - 4) ** .5) / 2 for t, nm in
           [(3, 'phi^2, Penrose'), (4, '2+sqrt3, 12-fold'), (5, 'sqrt21'), (6, 'silver^2'), (7, 'phi^4, hat'),
            (8, '4+sqrt15, Spectre'), (9, 'sqrt77'), (10, '5+2sqrt6'), (11, 'bronze^2'), (14, '(2+sqrt3)^2'),
            (18, 'phi^6'), (34, 'silver^4')]}
TARGETS.update({'silver d': SIL, 'golden phi': PHI, 'mirror-balanced 1': 1.0})
HAT = [[0, 0, 0], [0, 0, 1], [0, 0, 2], [0, 0, 5], [0, 1, 4], [0, 1, 5], [1, 0, 2], [1, 0, 3]]


@app.function(cpu=1.0, memory=8192, timeout=3600, retries=1, max_containers=100)
def measure(grid, sid, cells, Rs=(12, 18, 24)):
    sys.path.insert(0, "/root/ms")
    import grids as G, meter
    g = G.get(grid); out = []
    for R in Rs:
        r = meter.ratio(g, [tuple(c) for c in cells], R, inner=R - 3)
        if r is None:
            out.append(dict(R=R, stuck=True)); break
        a, b, s = r
        out.append(dict(R=R, a=a, b=b, ratio=round(max(a, b) / max(min(a, b), 1), 4), seconds=s))
    return dict(id=sid, cells=cells, runs=out)


def nearest(x):
    k = min(TARGETS, key=lambda k: abs(math.log(x / TARGETS[k])))
    return k, TARGETS[k]


@app.local_entrypoint()
def main(grid: str = "kite", n: int = 12, control: bool = False):
    if control:
        jobs = [(grid if grid == 'kite' else 'kite', 'hat', HAT)]
    else:
        p = os.path.join(HERE, "results", "modal", f"{grid}{n}_shapes.json.gz")
        recs = json.load(gzip.open(p, 'rt'))
        jobs = [(grid, r['id'], r['cells']) for r in recs if r['cls'] == 'OPEN']
    print(f'{len(jobs)} OPEN shapes to measure', flush=True)
    out = []
    for r in measure.starmap(jobs, order_outputs=False):
        out.append(r)
        last = [x for x in r['runs'] if 'ratio' in x]
        if not last:
            print(f"  {r['id']}: STUCK at R={r['runs'][-1]['R']}", flush=True); continue
        x = last[-1]['ratio']; k, v = nearest(x)
        print(f"  {r['id']}: ratios {[y['ratio'] for y in last]}  nearest {k} = {v:.3f}", flush=True)
    if not control:
        json.dump(out, open(os.path.join(HERE, "results", "modal", f"{grid}{n}_meter.json"), "w"), indent=1)
    print('Done.')
