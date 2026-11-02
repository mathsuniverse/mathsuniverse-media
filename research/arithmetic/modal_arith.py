"""Arithmetic route on Modal: Kari-style tile sets for many multiplier pairs, then the single-shape (inverse) search on each.

    py -m modal run modal_arith.py                  # all pairs from family(4) on both intervals, L = 3..5
    py -m modal run modal_arith.py --maxnum 5 --lmax 6 --minutes 15

Per job: build the Wang tiles for f(x) = q1 x / q2 x (kari.py), drop sets with a small period (they are not aperiodic),
then search for ONE polyomino S of L*L cells, one copy per Wang tile, orientation chosen per tile type (inverse_wang.py),
non-trivial (not a tiling by the lattice L*Z^2 alone). FOUND lines show each shape's monotile-sieve verdict.
Results: results/arith_inverse.json
"""
import json, os, sys
import modal

HERE = os.path.dirname(os.path.abspath(__file__))
image = (modal.Image.debian_slim(python_version="3.11").pip_install("python-sat==1.9.dev17")
         .add_local_dir(HERE, "/root/ms", ignore=["results/**", "logs/**", "open/**", "__pycache__/**", "*.png"]))
app = modal.App("arith-inverse", image=image)


def _child(q1, q2, iv, L, q):
    sys.path.insert(0, "/root/ms")
    from fractions import Fraction as F
    import kari as K, silver_wang as SW, inverse_wang as I, engine as E_
    q1, q2 = F(q1), F(q2)
    pieces = [(q1, q2, 1), (q2, 1, q1)] if iv == 'a' else [(q1, 1, 1 / q2), (q2, 1 / q2, q1 / q2)]
    T = K.tiles_for(pieces, samples=1500, length=40)
    per = next(((w, h) for w in range(1, 9) for h in range(1, 9) if SW.wang_sat(T, w, h, torus=True)), None)
    base = dict(q1=str(q1), q2=str(q2), interval=iv, L=L, tiles=len(T))
    if per: q.put(dict(base, info=f'periodic {per}, skipped', solutions=[])); return
    sols, info = I.run(L=L, n=max(14, 3 * L), tiles=T, limit=10)
    out = []
    for S, o in sols:
        con = E_.is_connected(I.g, S)
        out.append(dict(size=len(S), connected=con, sieve=E_.classify(I.g, S, tcap=12, rcap=6)['cls'] if con else 'disconnected',
                        cells=[list(c) for c in S]))
    q.put(dict(base, info=info, solutions=out))


@app.function(cpu=2.0, memory=8192, timeout=1500, retries=0, max_containers=50)
def run(q1, q2, iv, L, limit_s):
    import multiprocessing as mp, time, queue
    q = mp.Queue(); p = mp.Process(target=_child, args=(q1, q2, iv, L, q)); p.start()
    end = time.time() + limit_s
    while time.time() < end:
        try:
            r = q.get(timeout=5); p.join(10); return r
        except queue.Empty:
            if not p.is_alive(): return dict(q1=q1, q2=q2, interval=iv, L=L, info='child crashed', solutions=[])
    p.kill(); p.join()
    return dict(q1=q1, q2=q2, interval=iv, L=L, info=f'TIMEOUT after {limit_s / 60:.0f} min', solutions=[])


@app.local_entrypoint()
def main(maxnum: int = 4, lmin: int = 3, lmax: int = 5, minutes: int = 12):
    sys.path.insert(0, HERE)
    import family as Fm
    minutes = min(minutes, 22)
    pairs = [(str(a), str(b)) for a, b in Fm.family(maxnum)]
    jobs = [(a, b, iv, L, minutes * 60) for a, b in pairs for iv in ('a', 'b') for L in range(lmin, lmax + 1)]
    print(len(jobs), 'jobs', flush=True)
    out, path = [], os.path.join(HERE, "results", "arith_inverse.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for r in run.starmap(jobs, order_outputs=False):
        out.append(r); sols = r["solutions"]
        tag = "FOUND" if sols else ("TIMEOUT" if "TIMEOUT" in str(r["info"]) else ("skip" if "skipped" in str(r["info"]) else "none"))
        print(f"{tag:7s} q1={r['q1']} q2={r['q2']} interval={r['interval']} L={r['L']} tiles={r.get('tiles')}: "
              f"{[s['sieve'] for s in sols]}  {r['info'] if tag in ('skip', 'TIMEOUT') else ''}", flush=True)
        json.dump(out, open(path, "w"), indent=1)
    print("Done. Results in", path)
