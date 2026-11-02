"""Silver Wang inverse search on Modal: does ONE polyomino S, one copy per silver Wang tile (Labbé's 25 tiles), turned by an
orientation chosen per tile type, cover the plane in a non-trivial way?  Sweeps the scale L (|S| = L*L) and the reach r of S.

    py -m modal run modal_wang.py                       # L = 3..7, two reaches each
    py -m modal run modal_wang.py --lmin 5 --lmax 8 --minutes 15

Each job prints FOUND (with sieve verdict for each shape) or none / TIMEOUT. Results: results/silver_wang_inverse.json
"""
import json, os, sys
import modal

HERE = os.path.dirname(os.path.abspath(__file__))
image = (modal.Image.debian_slim(python_version="3.11").pip_install("python-sat==1.9.dev17")
         .add_local_dir(HERE, "/root/ms", ignore=["results/**", "logs/**", "open/**", "__pycache__/**", "*.png"]))
app = modal.App("silver-wang-inverse", image=image)


def _child(L, rf, q):
    sys.path.insert(0, "/root/ms")
    import inverse_wang as I, engine as E_
    sols, info = I.run(L=L, n=max(14, 3 * L), r=L * rf + 1.5, limit=10)
    out = []
    for S, o in sols:
        con = E_.is_connected(I.g, S)
        verdict = E_.classify(I.g, S, tcap=12, rcap=6)['cls'] if con else 'disconnected'
        out.append(dict(size=len(S), connected=con, sieve=verdict, cells=[list(c) for c in S], orient={str(k): v for k, v in o.items()}))
    q.put(dict(L=L, rf=rf, info=info, solutions=out))


@app.function(cpu=2.0, memory=8192, timeout=1500, retries=0, max_containers=20)
def run(L, rf, limit_s):
    import multiprocessing as mp, time, queue
    q = mp.Queue(); p = mp.Process(target=_child, args=(L, rf, q)); p.start()
    end = time.time() + limit_s
    while time.time() < end:
        try:
            res = q.get(timeout=5); p.join(10); return res
        except queue.Empty:
            if not p.is_alive(): return dict(L=L, rf=rf, info='child crashed', solutions=[])
    p.kill(); p.join()
    return dict(L=L, rf=rf, info=f'TIMEOUT after {limit_s / 60:.0f} min', solutions=[])


@app.local_entrypoint()
def main(lmin: int = 3, lmax: int = 7, minutes: int = 15):
    minutes = min(minutes, 22)
    jobs = [(L, rf, minutes * 60) for L in range(lmin, lmax + 1) for rf in (0.75, 1.1)]
    out, path = [], os.path.join(HERE, "results", "silver_wang_inverse.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for res in run.starmap(jobs, order_outputs=False):
        out.append(res); sols = res["solutions"]
        tag = "FOUND" if sols else ("TIMEOUT" if "TIMEOUT" in str(res["info"]) else "none")
        print(f"{tag:7s} L={res['L']} reach={res['rf']}: {len(sols)} shapes {[s['sieve'] for s in sols]}  {res['info']}", flush=True)
        json.dump(out, open(path, "w"), indent=1)
    print("Done. Results in", path)
