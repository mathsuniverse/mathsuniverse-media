"""Two searches on Modal at once.
 A. 'can't repeat' built in (CEGAR): a shape that fits the Wang layout but tiles some small torus is not just discarded; the whole
    family of shapes that would tile that same torus arrangement is cut away, and the search continues.
 B. Silver with window labels: orientation chosen per piece of the projection window (as the hat's orientations arise),
    on the deformed Ammann–Beenker pattern with rational density.

    py -m modal run modal_both.py                 # 16 A-jobs + 16 B-jobs, 20 minutes each
Results: results/both.json  (FOUND = a shape the never-repeating test leaves OPEN)
"""
import json, os, sys
import modal

HERE = os.path.dirname(os.path.abspath(__file__))
image = (modal.Image.debian_slim(python_version="3.11").pip_install("python-sat==1.9.dev17", "numpy", "shapely")
         .add_local_dir(HERE, "/root/ms", ignore=["results/**", "logs/**", "open/**", "__pycache__/**", "*.png"]))
app = modal.App("both-searches", image=image)

SETS = {'kari14': ('2', '2/3', 'a'), 'x3_x1/2': ('3', '1/2', 'a'), 'x3/2_x1/2': ('3/2', '1/2', 'b'), 'silver25': None}
A_CONF = [(3, 1), (4, 1), (4, 2), (5, 1)]
B_STARS = [(3, 1, 3, 6), (4, 1, 4, 6), (2, 1, 4, 5), (1, 1, 4, 3)]
B_LAB = [(8, 1, False), (8, 2, False), (16, 2, False), (8, 2, True)]


def _child(job, limit_s, q):
    sys.path.insert(0, "/root/ms")
    import engine as E_
    if job[0] == 'A':
        _, setname, L, k = job
        from fractions import Fraction as F
        import kari as K, silver_wang as SW, inverse_general as IG
        if SETS[setname] is None: T = SW.T2
        else:
            q1, q2, iv = SETS[setname]; q1, q2 = F(q1), F(q2)
            T = K.tiles_for([(q1, q2, 1), (q2, 1, q1)] if iv == 'a' else [(q1, 1, 1 / q2), (q2, 1 / q2, q1 / q2)], samples=1500, length=40)
        sols, info = IG.run(T, L=L, k=k, n=max(10, 3 * L), labels='type', limit=3, time_limit=limit_s - 90, cegar=True, tcap=12)
        q.put(dict(job=list(job), info=info, found=[[list(c) for c in s] for s in sols]))
    else:
        _, st, sec, rg, wt = job
        import silver as S, silver_window as SWn
        B = S.star(*st); V, T, polys = S.build(16, B)
        lab = SWn.window_labels(T, sec, rg, wt)
        sols, msg = S.solve(T, polys, B, r=5.0, Rz=10.0, labels=lab, limit=5)
        out = []
        for s, o in sols:
            con = E_.is_connected(S.g, s)
            out.append(dict(cells=[list(c) for c in s], connected=con, sieve=E_.classify(S.g, s, tcap=12, rcap=6)['cls'] if con else 'disconnected'))
        q.put(dict(job=list(job), info=msg, found=[x['cells'] for x in out if x['sieve'] == 'OPEN'], shapes=out))


@app.function(cpu=2.0, memory=8192, timeout=1600, retries=0, max_containers=40)
def run(job, limit_s):
    import multiprocessing as mp, time, queue
    q = mp.Queue(); p = mp.Process(target=_child, args=(job, limit_s, q)); p.start()
    end = time.time() + limit_s
    while time.time() < end:
        try:
            r = q.get(timeout=5); p.join(10); return r
        except queue.Empty:
            if not p.is_alive(): return dict(job=list(job), info='child crashed', found=[])
    p.kill(); p.join()
    return dict(job=list(job), info=f'TIMEOUT after {limit_s / 60:.0f} min', found=[])


@app.local_entrypoint()
def main(minutes: int = 20):
    minutes = min(minutes, 24)
    jobs = [('A', s, L, k) for s in SETS for (L, k) in A_CONF] + [('B', st, a, b, c) for st in B_STARS for (a, b, c) in B_LAB]
    print(len(jobs), 'jobs', flush=True)
    out, path = [], os.path.join(HERE, "results", "both.json")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    for r in run.starmap([(j, minutes * 60) for j in jobs], order_outputs=False):
        out.append(r); tag = "FOUND" if r['found'] else ("TIMEOUT" if 'TIMEOUT' in str(r['info']) else "none")
        extra = ''
        if isinstance(r['info'], dict): extra = f"periodic shapes cut={r['info'].get('periodic')} (arrangement cuts {r['info'].get('periodic_cuts')})"
        elif r.get('shapes') is not None: extra = f"{len(r['shapes'])} shapes {[s['sieve'] for s in r['shapes']]}  {r['info']}"
        else: extra = str(r['info'])
        print(f"{tag:7s} {r['job']}  {extra}", flush=True)
        json.dump(out, open(path, "w"), indent=1)
    print("Done. Results in", path)
