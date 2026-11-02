"""Re-test every shape the quick family screen marked OPEN, at full strength (torus <= 16 tiles, disc radius <= 8).

    py -m modal run modal_recheck.py          # reads results/families.json, writes results/families_recheck.json

CANDIDATE = still OPEN after the full test (no repeat found, no jam). Anything else is printed with its real verdict.
"""
import json, os, sys
import modal

HERE = os.path.dirname(os.path.abspath(__file__))
image = (modal.Image.debian_slim(python_version="3.11").pip_install("python-sat==1.9.dev17", "shapely")
         .add_local_dir(HERE, "/root/ms", ignore=["results/**", "logs/**", "open/**", "__pycache__/**", "*.png"]))
app = modal.App("families-recheck", image=image)


def _one(f, a, b, q):
    sys.path.insert(0, "/root/ms")
    import families as Fm, grids as G, engine as E_
    g = G.get('tetrakis'); cs = Fm.cells(Fm.polygon(tuple(f), a, b))
    r = E_.classify(g, cs, tcap=16, rcap=8)
    q.put(dict(cls=r['cls'], fail_R=r.get('fail_R'), tiles_per_domain=r.get('tiles_per_domain'), cells=len(cs)))


@app.function(cpu=2.0, memory=8192, timeout=1500, retries=1, max_containers=100)
def check(f, a, b, limit_s=1200):
    import multiprocessing as mp, queue
    q = mp.Queue(); p = mp.Process(target=_one, args=(f, a, b, q)); p.start()
    try:
        r = q.get(timeout=limit_s); p.join(5)
    except queue.Empty:
        p.kill(); p.join(); r = dict(cls='TIMEOUT (still open after 20 min)')
    return dict(seq=f, ratio=[a, b], **r)


@app.local_entrypoint()
def main():
    src = json.load(open(os.path.join(HERE, "results", "families.json")))
    jobs = [(x['seq'], int(k.split(',')[0]), int(k.split(',')[1])) for x in src for k, v in x['result'].items() if v == 'OPEN']
    print(len(jobs), 'shapes to re-test', flush=True)
    out, path = [], os.path.join(HERE, "results", "families_recheck.json")
    for r in check.starmap(jobs, order_outputs=False):
        out.append(r)
        tag = 'CANDIDATE' if r['cls'] == 'OPEN' else r['cls'].split()[0]
        print(f"{tag:10s} family {r['seq']} Tile{tuple(r['ratio'])}  {r}", flush=True)
        json.dump(out, open(path, "w"), indent=1)
    print("Done. Results in", path)
