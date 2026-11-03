"""General overnight search: every equal-edge outline (Tile(1,1)-type, the Spectre's family rule) in N = 8, 10, 12 directions
with m edges, tested with and without mirrors by the decisive periodic test.

    py -m modal run modal_general.py --runs "12:14,10:10,10:12,12:12,10:14,8:16"
Built-in control: the 12:14 run contains Tile(1,1), which must come out PERIODIC with mirrors and OPEN without.
Prints every OPEN / UNDECIDED. Results: results/general_<N>_<m>.json
"""
import json, os, sys
import modal

HERE = os.path.dirname(os.path.abspath(__file__))
image = (modal.Image.debian_slim(python_version="3.11").pip_install("python-sat==1.9.dev17", "shapely")
         .add_local_dir(HERE, "/root/ms", ignore=["results/**", "logs/**", "open/**", "heesch/**",
                                                   "candidates/**", "__pycache__/**", "*.png"]))
app = modal.App("general-free", image=image)


@app.function(cpu=1.0, memory=4096, timeout=6 * 3600, retries=1, max_containers=100)
def enum_slice(N, m, t1, t2):
    sys.path.insert(0, "/root/ms")
    import outlines as O
    return [list(s) for s in O.shapes(N, m, first=(t1, t2))]


def _one(seq, N, q):
    sys.path.insert(0, "/root/ms")
    import free_families as FF
    try:
        q.put(FF.classify_general(tuple(seq), N))
    except Exception as e:
        q.put({'error': repr(e)})


@app.function(cpu=1.0, memory=4096, timeout=3600, retries=1, max_containers=100)
def test(chunk, N, limit=1500):
    import multiprocessing as mp, queue
    out = []
    for s in chunk:
        q = mp.Queue(); p = mp.Process(target=_one, args=(s, N, q)); p.start()
        try:
            r = q.get(timeout=limit); p.join(5)
        except queue.Empty:
            p.kill(); p.join(); r = {'timeout': f'over {limit}s'}
        out.append(dict(seq=s, result=r))
    return out


@app.local_entrypoint()
def main(runs: str = "12:14", per: int = 3):
    from collections import Counter
    sys.path.insert(0, HERE)
    for run in runs.split(','):
        N, m = map(int, run.split(':'))
        half = N // 2
        turns = [0] + [t for a in range(1, half) for t in (a, -a)]
        seen, S = set(), []
        for part in enum_slice.starmap([(N, m, a, b) for a in turns for b in turns], order_outputs=False):
            for s in part:
                if tuple(s) not in seen:
                    seen.add(tuple(s)); S.append(s)
        print(f'N={N} m={m}: {len(S)} equal-edge outlines', flush=True)
        out, c = [], Counter()
        path = os.path.join(HERE, 'results', f'general_{N}_{m}.json')
        os.makedirs(os.path.dirname(path), exist_ok=True)
        for part in test.starmap([(S[i:i + per], N) for i in range(0, len(S), per)], order_outputs=False):
            for r in part:
                out.append(r); res = r['result']
                key = (f"{res['mirror']['cls']}/{res['nomirror']['cls']}" if 'mirror' in res
                       else ('error' if 'error' in res else 'timeout'))
                c[key] += 1
                if 'OPEN' in key or 'UNDECIDED' in key or key == 'timeout':
                    print(f"   N={N} m={m} {key}  {r['seq']}  {res}", flush=True)
            if len(out) % 500 < per:
                print(f'  N={N} m={m}: {len(out)}/{len(S)}  {dict(c)}', flush=True)
                json.dump(out, open(path, 'w'))
        json.dump(out, open(path, 'w'))
        print(f'N={N} m={m} done: {dict(c)}   (with mirrors / without)', flush=True)
    print('All runs done.')
