"""Everything runs in the cloud: your PC only starts the job (and may then sleep or disconnect).
Results are saved in the Modal volume "monotile-results" as they come in.

Start (returns at once):
    py -m modal run --detach modal_cloud.py --job general  --runs "10:10,12:12,10:12,10:14,12:14,8:16"
    py -m modal run --detach modal_cloud.py --job hatroute --runs "12:14:r3,10:12:phi,10:14:phi,8:12:r2,8:14:r2,8:12:1+r2,8:14:1+r2,12:14:2+r3"
Progress (any time):
    py -m modal volume get monotile-results progress.txt . --force   then open progress.txt
Fetch all results into results\\cloud:
    py -m modal volume get monotile-results / results\\cloud --force

general  = equal-edge outlines (Spectre route), N = 8, 10, 12 directions, m edges; control: Tile(1,1) in 12:14
hatroute = Tile(a,b)-type outlines with b/a in {r3, 2+r3, phi, r2, 1+r2}; control: hat and turtle in 12:14:r3
"""
import json, os, sys, time
import modal

HERE = os.path.dirname(os.path.abspath(__file__))
image = (modal.Image.debian_slim(python_version="3.11").pip_install("python-sat==1.9.dev17", "shapely")
         .add_local_dir(HERE, "/root/ms", ignore=["results/**", "logs/**", "open/**", "heesch/**",
                                                   "candidates/**", "__pycache__/**", "*.png", "*.pkl"]))
app = modal.App("monotile-cloud", image=image)
vol = modal.Volume.from_name("monotile-results", create_if_missing=True)


def lam_value(R, name):
    one = (1, 0, 0, 0)
    c = R.unit_sum([1, -1])
    return {'r3': c, '2+r3': R.add((2, 0, 0, 0), c), 'phi': R.add(one, c), 'r2': c, '1+r2': R.add(one, c)}[name]


@app.function(cpu=1.0, memory=4096, timeout=6 * 3600, retries=2, max_containers=100)
def enum_slice(N, m, first):
    sys.path.insert(0, "/root/ms")
    import outlines as O
    seen, out = set(), []
    for s in O.outlines(N, m, first=tuple(first)):
        c = O.canon(s, N)
        if c not in seen:
            seen.add(c); out.append(list(c))
    return out


def _one(seq, N, lens_spec, q):
    sys.path.insert(0, "/root/ms")
    import free as F, free_families as FF
    try:
        lens = None
        if lens_spec:
            lam, swap = lens_spec
            R = F.Ring(N); L = lam_value(R, lam); one = (1, 0, 0, 0)
            lens = [(L if (d % 2) != swap else one) for d in seq]
        q.put(FF.classify_general(tuple(seq), N, lens))
    except Exception as e:
        q.put({'error': repr(e)})


@app.function(cpu=1.0, memory=4096, timeout=3600, retries=2, max_containers=100)
def test(chunk, N, limit=1500):
    import multiprocessing as mp, queue
    out = []
    for seq, spec in chunk:
        q = mp.Queue(); p = mp.Process(target=_one, args=(seq, N, spec, q)); p.start()
        try:
            r = q.get(timeout=limit); p.join(5)
        except queue.Empty:
            p.kill(); p.join(); r = {'timeout': f'over {limit}s'}
        out.append(dict(seq=seq, lens=spec, result=r))
    return out


def _log(msg):
    with open('/vol/progress.txt', 'a') as f:
        f.write(time.strftime('%H:%M:%S ') + msg + '\n')
    vol.commit()


def _outlines(N, m):
    path = f'/vol/outlines_{N}_{m}.json'
    if os.path.exists(path):
        return json.load(open(path))
    half = N // 2
    turns = [0] + [t for a in range(1, half) for t in (a, -a)]
    firsts = [(a, b, c) for a in turns for b in turns for c in turns]
    seen, S = set(), []
    for part in enum_slice.starmap([(N, m, f) for f in firsts], order_outputs=False):
        for s in part:
            if tuple(s) not in seen:
                seen.add(tuple(s)); S.append(s)
    json.dump(S, open(path, 'w')); vol.commit()
    return S


@app.function(timeout=24 * 3600, volumes={"/vol": vol}, retries=0)
def orchestrate(job, runs, per=3):
    from collections import Counter
    _log(f'start {job} {runs}')
    for run in runs.split(','):
        parts = run.split(':')
        N, m = int(parts[0]), int(parts[1])
        lam = parts[2] if len(parts) > 2 else None
        S = _outlines(N, m)
        jobs = [(s, None) for s in S] if not lam else [(s, (lam, sw)) for s in S for sw in (False, True)]
        name = f'{job}_{N}_{m}' + (f'_{lam}' if lam else '')
        _log(f'{name}: {len(S)} outlines, {len(jobs)} shapes to test')
        out, c, flagged = [], Counter(), []
        for part in test.starmap([(jobs[i:i + per], N) for i in range(0, len(jobs), per)], order_outputs=False):
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
                    flagged.append(r)
                    _log(f'   {name} {key} {r["seq"]} lens={r["lens"]} {res}')
            if len(out) % 600 < per:
                json.dump(out, open(f'/vol/{name}.json', 'w'))
                _log(f'  {name}: {len(out)}/{len(jobs)} {dict(c)}')
        json.dump(out, open(f'/vol/{name}.json', 'w'))
        _log(f'{name} DONE {dict(c)}  (with mirrors / without)')
    _log(f'all done {job}')


@app.local_entrypoint()
def main(job: str = "general", runs: str = "10:10"):
    call = orchestrate.spawn(job, runs)
    print(f'Started {job} in the cloud ({runs}). Call id {call.object_id}.')
    print('Your PC can now sleep. Progress: py -m modal volume get monotile-results progress.txt . --force')
