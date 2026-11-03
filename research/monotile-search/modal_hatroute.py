"""The hat route, general: Tile(a,b)-type outlines in N directions (even-direction edges length a, odd-direction edges
length b, each class closing on its own), placed freely (no grid), with b/a an exact length of the N-fold world:

    N = 12: r3 = sqrt3 (the hat's own family: control), 2+r3
    N = 10: phi (the Penrose kite's proportions)
    N = 8:  r2 = sqrt2, 1+r2 (silver)

Both assignments (a, b) = (1, lam) and (lam, 1) are tested, with and without mirrors, by the decisive classifier.
    py -m modal run modal_hatroute.py --runs "12:14:r3,10:12:phi,10:14:phi,8:12:r2,8:14:r2,8:12:1+r2,8:14:1+r2,12:14:2+r3"
Control: in 12:14:r3 the hat (and the turtle, (lam, 1)) must come out OPEN with mirrors and STUCK without.
Results: results/hatroute_<N>_<m>_<lam>.json
"""
import json, os, sys
import modal

HERE = os.path.dirname(os.path.abspath(__file__))
image = (modal.Image.debian_slim(python_version="3.11").pip_install("python-sat==1.9.dev17", "shapely")
         .add_local_dir(HERE, "/root/ms", ignore=["results/**", "logs/**", "open/**", "heesch/**",
                                                   "candidates/**", "__pycache__/**", "*.png"]))
app = modal.App("hat-route", image=image)


def lam_value(R, name):
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
    import free as F, free_families as FF
    try:
        R = F.Ring(N); L = lam_value(R, lam); one = (1, 0, 0, 0)
        lens = [(L if (d % 2) != swap else one) for d in seq]
        q.put(FF.classify_general(tuple(seq), N, lens))
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
def main(runs: str = "12:14:r3", per: int = 3):
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
        jobs = [(s, sw) for s in S for sw in (False, True)]
        print(f'N={N} m={m} lam={lam}: {len(S)} outlines, {len(jobs)} shapes (both length assignments)', flush=True)
        out, c = [], Counter()
        path = os.path.join(HERE, 'results', f'hatroute_{N}_{m}_{lam}.json')
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
