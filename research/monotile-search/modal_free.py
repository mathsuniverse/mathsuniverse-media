"""Silver Tile(1,1) on Modal: every 8-direction outline family (m edges), all edges length 1, no grid (free placement in
the exact 8-fold point set), tested with mirrors allowed and with mirrors forbidden (Spectre rule).

    py -m modal run modal_free.py --m 12
    py -m modal run modal_free.py --m 14
Calibrated on the Spectre case: Tile(1,1) (12-fold) comes out PERIODIC with mirrors (2 tiles per repeat) and OPEN without.
Prints any OPEN result (with or without mirrors). Results: results/free<m>.json
"""
import json, os, sys
import modal

HERE = os.path.dirname(os.path.abspath(__file__))
image = (modal.Image.debian_slim(python_version="3.11").pip_install("python-sat==1.9.dev17", "shapely")
         .add_local_dir(HERE, "/root/ms", ignore=["results/**", "logs/**", "open/**", "heesch/**",
                                                   "candidates/**", "__pycache__/**", "*.png"]))
app = modal.App("silver-free", image=image)
TURNS = (0, 1, 2, 3, -1, -2, -3)


@app.function(cpu=1.0, memory=8192, timeout=7200, retries=1, max_containers=49)
def enum_slice(m, t1, t2):
    sys.path.insert(0, "/root/ms")
    import families as Fm
    return [list(f) for f in Fm.families(m, True, first=(t1, t2), max_straight=1)]


def _one(f, q):
    sys.path.insert(0, "/root/ms")
    import free_families as FF
    try:
        q.put(FF.test_one(tuple(f)))
    except Exception as e:
        q.put({'error': repr(e)})


@app.function(cpu=1.0, memory=4096, timeout=3600, retries=1, max_containers=100)
def test(chunk, limit=600):
    import multiprocessing as mp, queue
    out = []
    for f in chunk:
        q = mp.Queue(); p = mp.Process(target=_one, args=(f, q)); p.start()
        try:
            r = q.get(timeout=limit); p.join(5)
        except queue.Empty:
            p.kill(); p.join(); r = {'timeout': f'over {limit}s'}
        out.append(dict(seq=f, result=r))
    return out


@app.local_entrypoint()
def main(m: int = 12, per: int = 5):
    from collections import Counter
    seen, F = set(), []
    for part in enum_slice.starmap([(m, a, b) for a in TURNS for b in TURNS], order_outputs=False):
        for f in part:
            if tuple(f) not in seen:
                seen.add(tuple(f)); F.append(f)
    print(f'{len(F)} outline families with {m} edges (all edges length 1, 8 directions)', flush=True)
    out, c = [], Counter()
    path = os.path.join(HERE, 'results', f'free{m}.json')
    for part in test.map([F[i:i + per] for i in range(0, len(F), per)], order_outputs=False):
        for r in part:
            out.append(r); res = r['result']
            if 'mirror' in res:
                key = f"{res['mirror']['cls']}/{res['nomirror']['cls']}"
            else:
                key = 'error' if 'error' in res else 'timeout'
            c[key] += 1
            if 'OPEN' in key or 'UNDECIDED' in key:
                print(f"   {key}  {r['seq']}  {res}", flush=True)
        if len(out) % 1000 < per:
            print(f'  {len(out)}/{len(F)}  {dict(c)}', flush=True)
            json.dump(out, open(path, 'w'))
    json.dump(out, open(path, 'w'))
    print(f'Done: {dict(c)}   (key = with mirrors / without mirrors)')
