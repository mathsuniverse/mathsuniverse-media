"""Hat-faithful family search on Modal: outlines with up to 14 (or 16) edges, axis edges length a and diagonal edges length b·√2,
allowing one straight double edge as in the hat. Three stages in one run:
 1. enumerate the families in 49 parallel slices (first two turns), merge, remove duplicates;
 2. quick screen of Tile(1,0), Tile(0,1), Tile(1,1), Tile(1,2), Tile(2,1) (torus <= 8 tiles, disc R <= 4);
 3. every shape still OPEN gets the full test (torus <= 16 tiles, disc R <= 8). Only those that survive print as CANDIDATE.

    py -m modal run modal_families14.py                  # 14 edges, one straight double edge, asymmetric outlines, hat signature
    py -m modal run modal_families14.py --no-asym        # include symmetric outlines too
    py -m modal run modal_families14.py --m 16           # bigger (much longer)
Results: results/families14_screen.json, results/families14_candidates.json
"""
import json, os, sys
import modal

HERE = os.path.dirname(os.path.abspath(__file__))
image = (modal.Image.debian_slim(python_version="3.11").pip_install("python-sat==1.9.dev17", "shapely")
         .add_local_dir(HERE, "/root/ms", ignore=["results/**", "logs/**", "open/**", "__pycache__/**", "*.png"]))
app = modal.App("families14", image=image)
RATIOS = ((1, 0), (0, 1), (1, 1), (1, 2), (2, 1))
TURNS = (0, 1, 2, 3, -1, -2, -3)


@app.function(cpu=1.0, memory=8192, timeout=7200, retries=1, max_containers=49)
def enum_slice(m, t1, t2, max_straight, asym=True):
    sys.path.insert(0, "/root/ms")
    import families as Fm
    return [list(f) for f in Fm.families(m, True, first=(t1, t2), max_straight=max_straight) if not asym or Fm.asymmetric(f)]


def _one(f, ratios, tcap, rcap, q):
    sys.path.insert(0, "/root/ms")
    import families as Fm
    try:
        r = Fm.test_family_hat(tuple(f), tcap=tcap, rcap=rcap) if ratios is None else Fm.test_family(tuple(f), ratios, tcap=tcap, rcap=rcap)
        q.put({(k if isinstance(k, str) else f'{k[0]},{k[1]}'): v for k, v in r.items()})
    except Exception as e:
        q.put({'error': repr(e)})


def _guarded(f, ratios, tcap, rcap, limit):
    import multiprocessing as mp, queue
    q = mp.Queue(); p = mp.Process(target=_one, args=(f, ratios, tcap, rcap, q)); p.start()
    try:
        r = q.get(timeout=limit); p.join(5); return r
    except queue.Empty:
        p.kill(); p.join(); return {'timeout': f'over {limit}s'}


@app.function(cpu=1.0, memory=4096, timeout=3600, retries=1, max_containers=100)
def screen(chunk):
    return [(f, _guarded(f, None, 6, 5, 90)) for f in chunk]       # hat signature: ends first; torus <= 6 tiles, 90 s cap


@app.function(cpu=2.0, memory=8192, timeout=1500, retries=1, max_containers=100)
def full(f, a, b):
    r = _guarded(f, ((a, b),), 16, 8, 1200)
    return dict(seq=f, ratio=[a, b], verdict=r.get(f'{a},{b}', r))


@app.local_entrypoint()
def main(m: int = 14, max_straight: int = 1, per: int = 60, asym: bool = True):
    sys.path.insert(0, HERE)
    slices = [(m, a, b, max_straight, asym) for a in TURNS for b in TURNS]
    seen, F = set(), []
    for part in enum_slice.starmap(slices, order_outputs=False):
        for f in part:
            t = tuple(f)
            if t not in seen: seen.add(t); F.append(f)
    print(f'{len(F)} families with {m} edges', flush=True)
    os.makedirs(os.path.join(HERE, "results"), exist_ok=True)
    chunks = [F[i:i + per] for i in range(0, len(F), per)]
    res, todo = [], []
    for part in screen.map(chunks, order_outputs=False):
        for f, r in part:
            res.append(dict(seq=f, result=r))
            for k, v in r.items():
                if v == 'OPEN' and ',' in k: todo.append((f, int(k.split(',')[0]), int(k.split(',')[1])))
        if len(res) % 3000 < per:
            ends_ok = sum(1 for x in res if '1,0' in x['result'])
            print(f'  screened {len(res)}/{len(F)}  both ends periodic: {ends_ok}  OPEN shapes so far {len(todo)}', flush=True)
            json.dump(res, open(os.path.join(HERE, "results", "families14_screen.json"), "w"))
    json.dump(res, open(os.path.join(HERE, "results", "families14_screen.json"), "w"))
    print(f'screen done: {len(todo)} OPEN shapes to re-test at full strength', flush=True)
    out = []
    for r in full.starmap(todo, order_outputs=False):
        out.append(r)
        tag = 'CANDIDATE' if r['verdict'] == 'OPEN' else str(r['verdict'])[:40]
        print(f'{tag:10s} family {r["seq"]} Tile{tuple(r["ratio"])}', flush=True)
        json.dump(out, open(os.path.join(HERE, "results", "families14_candidates.json"), "w"), indent=1)
    print('Done.')
