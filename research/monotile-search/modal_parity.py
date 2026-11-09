"""Hat-type slot search (THEORY.md s8-10): 12-direction outlines whose even and odd edge families close separately,
placed with the 60-degree orientation group only (rotations by multiples of 60 degrees, mirrors composed with them).
That is the symmetry group of a Tile(a,b) family with a != b. Earlier runs allowed all 12 rotations, which can turn an
aperiodic hat-type tiling into a periodic one (Tile(1,1)). Classifier: parity.classify.
Controls (passed locally, 9 Nov): Tile(1,1), Tile(1,sqrt3) (hat), Tile(sqrt3,1) (turtle), Tile(1,2): all OPEN with
mirrors, STUCK without. In this run Tile(1,1) must come out OPEN/STUCK.
    py -m modal run modal_parity.py --runs "12:14:1"
    py -m modal run modal_parity.py --runs "12:16:1"
lam '1' = equal edges (combinatorics do not depend on lengths in this group, per the controls); 'two' = Tile(1,2) recheck.
Results: results/parity_<N>_<m>_<lam>.json
"""
import json, os, sys
import modal

HERE = os.path.dirname(os.path.abspath(__file__))
image = (modal.Image.debian_slim(python_version="3.11").pip_install("python-sat==1.9.dev17", "shapely")
         .add_local_dir(HERE, "/root/ms", ignore=["results/**", "logs/**", "open/**", "heesch/**",
                                                   "candidates/**", "__pycache__/**", "*.png"]))
app = modal.App("parity-route", image=image)


def lam_value(R, name):
    if name == 'two': return (2, 0, 0, 0)
    one = (1, 0, 0, 0)
    c = R.unit_sum([1, -1])                       # 2 cos(2 pi / N): sqrt3 (N=12), 1/phi (N=10), sqrt2 (N=8)
    return {'r3': c, '2+r3': R.add((2, 0, 0, 0), c), 'phi': R.add(one, c), 'r2': c, '1+r2': R.add(one, c)}[name]


@app.function(cpu=1.0, memory=4096, timeout=6 * 3600, retries=1, max_containers=100)
def enum_slice(N, m, t1, t2):
    sys.path.insert(0, "/root/ms")
    import outlines as O
    seen, out = set(), []
    for s in O.outlines(N, m, first=(t1, t2)):
        c = O.canon(s, N)
        if c not in seen:
            seen.add(c); out.append(list(c))
    return out


def _one(seq, N, lam, swap, q):
    sys.path.insert(0, "/root/ms")
    import free as F, parity as P
    try:
        R = F.Ring(N); lens = None if lam == '1' else P.lens_for(seq, N, lam_value(R, lam), swap)
        q.put(P.classify(tuple(seq), N, lens, step=2))
    except Exception as e:
        q.put({'error': repr(e)})


@app.function(cpu=1.0, memory=4096, timeout=3600, retries=1, max_containers=100)
def test(chunk, N, lam, limit=1500):
    import multiprocessing as mp, queue
    out = []
    for s, swap in chunk:
        q = mp.Queue(); p = mp.Process(target=_one, args=(s, N, lam, swap, q)); p.start()
        try:
            r = q.get(timeout=limit); p.join(5)
        except queue.Empty:
            p.kill(); p.join(); r = {'timeout': f'over {limit}s'}
        out.append(dict(seq=s, swap=swap, result=r))
    return out


@app.local_entrypoint()
def main(runs: str = "12:14:1", per: int = 3):
    from collections import Counter
    for run in runs.split(','):
        N, m, lam = run.split(':'); N, m = int(N), int(m)
        half = N // 2
        turns = [0] + [t for a in range(1, half) for t in (a, -a)]
        seen, S = set(), []
        for part in enum_slice.starmap([(N, m, a, b) for a in turns for b in turns], order_outputs=False):
            for s in part:
                if tuple(s) not in seen:
                    seen.add(tuple(s)); S.append(s)
        jobs = [(s, sw) for s in S for sw in ((False,) if lam == '1' else (False, True))]
        print(f'N={N} m={m} lam={lam}: {len(S)} outlines, {len(jobs)} shapes (both length assignments)', flush=True)
        out, c = [], Counter()
        path = os.path.join(HERE, 'results', f'parity_{N}_{m}_{lam}.json')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        for part in test.starmap([(jobs[i:i + per], N, lam) for i in range(0, len(jobs), per)], order_outputs=False):
            for r in part:
                out.append(r); res = r['result']
                if 'error' in res and 'simple' in res['error']:
                    key = 'not simple'
                elif 'mirror' in res:
                    key = f"{res['mirror']['cls']}/{res['nomirror']['cls']}"
                else:
                    key = 'error' if 'error' in res else 'timeout'
                c[key] += 1
                if 'OPEN' in key or 'UNDECIDED' in key or key == 'timeout':
                    print(f"   N={N} m={m} {lam} {key}  {r['seq']} swap={r['swap']}  {res}", flush=True)
            if len(out) % 500 < per:
                print(f'  N={N} m={m} {lam}: {len(out)}/{len(jobs)}  {dict(c)}', flush=True)
                json.dump(out, open(path, 'w'))
        json.dump(out, open(path, 'w'))
        print(f'N={N} m={m} {lam} done: {dict(c)}   (with mirrors / without)', flush=True)
    print('All runs done.')
