"""Loosened single-shape search on Modal (ideas 1-3): k copies per Wang tile, free anchor offsets, orientation from tile type or
type + neighbours. Tile sets: Kari 14 (x2, x2/3), x3 & x1/2 (15), x3/2 & x1/2 (17), Labbé silver (25).
Each candidate shape that fits the layout is connected (lazy cuts) and run through the monotile sieve inside the job;
FOUND = a shape the sieve leaves OPEN (no period, no jam). Counters show how many periodic shapes were seen and discarded.

    py -m modal run modal_loose.py
    py -m modal run modal_loose.py --minutes 15 --labels type
Results: results/loose_inverse.json
"""
import json, os, sys
import modal

HERE = os.path.dirname(os.path.abspath(__file__))
image = (modal.Image.debian_slim(python_version="3.11").pip_install("python-sat==1.9.dev17")
         .add_local_dir(HERE, "/root/ms", ignore=["results/**", "logs/**", "open/**", "__pycache__/**", "*.png"]))
app = modal.App("loose-inverse", image=image)

SETS = {'kari14': ('2', '2/3', 'a'), 'x3_x1/2': ('3', '1/2', 'a'), 'x3/2_x1/2': ('3/2', '1/2', 'b'), 'silver25': None}
CONFIGS = [(3, 1), (4, 1), (4, 2), (4, 4), (5, 1), (6, 2), (6, 3), (6, 4)]


def _child(setname, L, k, labels, limit_s, q):
    sys.path.insert(0, "/root/ms")
    from fractions import Fraction as F
    import kari as K, silver_wang as SW, inverse_general as IG, engine as E_
    if SETS[setname] is None: T = SW.T2
    else:
        q1, q2, iv = SETS[setname]; q1, q2 = F(q1), F(q2)
        pieces = [(q1, q2, 1), (q2, 1, q1)] if iv == 'a' else [(q1, 1, 1 / q2), (q2, 1 / q2, q1 / q2)]
        T = K.tiles_for(pieces, samples=1500, length=40)
    sols, info = IG.run(T, L=L, k=k, n=max(12, 3 * L), labels=labels, limit=5, time_limit=limit_s - 60)
    q.put(dict(set=setname, L=L, k=k, labels=labels, info=info, found=[[list(c) for c in S] for S in sols]))


@app.function(cpu=2.0, memory=8192, timeout=1500, retries=0, max_containers=64)
def run(setname, L, k, labels, limit_s):
    import multiprocessing as mp, time, queue
    q = mp.Queue(); p = mp.Process(target=_child, args=(setname, L, k, labels, limit_s, q)); p.start()
    end = time.time() + limit_s + 30
    while time.time() < end:
        try:
            r = q.get(timeout=5); p.join(10); return r
        except queue.Empty:
            if not p.is_alive(): return dict(set=setname, L=L, k=k, labels=labels, info='child crashed', found=[])
    p.kill(); p.join()
    return dict(set=setname, L=L, k=k, labels=labels, info='killed at time limit', found=[])


@app.local_entrypoint()
def main(minutes: int = 14, labels: str = "type,neighbours"):
    minutes = min(minutes, 22)
    jobs = [(s, L, k, lb, minutes * 60) for s in SETS for (L, k) in CONFIGS for lb in labels.split(",")]
    print(len(jobs), 'jobs', flush=True)
    out, path = [], os.path.join(HERE, "results", "loose_inverse.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for r in run.starmap(jobs, order_outputs=False):
        out.append(r); i = r['info'] if isinstance(r['info'], dict) else {}
        tag = "FOUND" if r['found'] else "none"
        print(f"{tag:5s} {r['set']:10s} L={r['L']} copies={r['k']} labels={r['labels']:10s} "
              f"shapes tried: periodic={i.get('periodic', '?')} stuck={i.get('stuck', '?')}  cuts={i.get('cuts', '?')}"
              f"{'' if isinstance(r['info'], dict) else '  ' + str(r['info'])}", flush=True)
        json.dump(out, open(path, "w"), indent=1)
    print("Done. Results in", path)
