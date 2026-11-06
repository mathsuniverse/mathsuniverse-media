"""Everything runs in the cloud: your PC only starts the job (and may then sleep or disconnect).
Results are saved in the Modal volume "monotile-results" as they come in.

Start (returns at once):
    py -m modal run --detach modal_cloud.py --job general  --runs "10:10,12:12,10:12,10:14,12:14,8:16"
    py -m modal run --detach modal_cloud.py --job hatroute --runs "12:14:r3,10:12:phi,10:14:phi,8:12:r2,8:14:r2,8:12:1+r2,8:14:1+r2,12:14:2+r3"
Progress (any time):
    py -m modal volume get monotile-results progress_general.txt . --force   (or progress_hatroute.txt), then open it
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
    return {'r3': c, '2+r3': R.add((2, 0, 0, 0), c), 'phi': R.add(one, c), 'r2': c, '1+r2': R.add(one, c),
            '2': (2, 0, 0, 0), '3': (3, 0, 0, 0), '1+r3': R.add(one, c), '2r3': R.add(c, c), '3+r3': R.add((3, 0, 0, 0), c)}[name]


@app.function(cpu=1.0, memory=4096, timeout=6 * 3600, retries=2, max_containers=100)
def enum_slice(N, m, first, max_turn, lam):
    """Canonical outlines of this slice that are simple polygons: for the equal-edge job with unit edges, for the hat
    route for each length assignment separately (returns (outline, assignment) pairs)."""
    sys.path.insert(0, "/root/ms")
    import outlines as O, free as F
    R = F.Ring(N)
    seen, out = set(), []
    import math
    # fast enumerator: self-touching prefixes cut at once, one turn sequence per cyclic class (validated equal to
    # O.outlines on 10:10, 8:12, 12:12)
    for s in O.outlines_fast(N, m, first=tuple(first), max_turn=max_turn, lam_f=math.hypot(*R.f(lam_value(R, lam))) if lam else None):
        c = O.canon(s, N)
        if c in seen:
            continue
        seen.add(c)
        if lam is None:
            if O.simple(c, N):
                out.append((list(c), None))
        else:
            L = lam_value(R, lam); one = (1, 0, 0, 0)
            for sw in (False, True):
                lens = [(L if (d % 2) != sw else one) for d in c]
                if O.simple(c, N, lens):
                    out.append((list(c), (lam, sw)))
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


@app.function(cpu=1.0, memory=4096, timeout=6 * 3600, retries=2, max_containers=100)
def test(chunk, N):
    sys.path.insert(0, "/root/ms")
    import free as F, free_families as FF
    out = []
    for seq, spec in chunk:
        try:
            lens = None
            if spec:
                lam, sw = spec
                R = F.Ring(N); L = lam_value(R, lam); one = (1, 0, 0, 0)
                lens = [(L if (d % 2) != sw else one) for d in seq]
            r = FF.classify_general(tuple(seq), N, lens)
        except Exception as e:
            r = {'error': repr(e)}
        out.append(dict(seq=seq, lens=spec, result=r))
    return out


LOGJOB = ['general']


def _log(msg):
    with open(f'/vol/progress_{LOGJOB[0]}.txt', 'a') as f:
        f.write(time.strftime('%H:%M:%S ') + msg + '\n')
    vol.commit()


def _outlines(N, m, max_turn, lam):
    tag = f'{N}_{m}_t{max_turn}' + (f'_{lam}' if lam else '')
    path = f'/vol/outlines_{tag}.json'
    if os.path.exists(path):
        return json.load(open(path))
    turns = [0] + [t for a in range(1, max_turn + 1) for t in (a, -a)]
    firsts = [(a, b, c) for a in turns for b in turns for c in turns]
    seen, S = set(), []
    for part in enum_slice.starmap([(N, m, f, max_turn, lam) for f in firsts], order_outputs=False):
        for s, spec in part:
            k = (tuple(s), None if spec is None else spec[1])
            if k not in seen:
                seen.add(k); S.append((s, spec))
    json.dump(S, open(path, 'w')); vol.commit()
    return S


def _save(path, data):
    """Write to a temp file and rename, so a job killed mid-save never leaves a half-written file."""
    with open(path + '.tmp', 'w') as f:
        json.dump(data, f)
    os.replace(path + '.tmp', path)


def _key(res):
    if 'error' in res and 'simple' in res['error']:
        return 'not simple'
    if 'mirror' in res:
        return f"{res['mirror']['cls']}/{res['nomirror']['cls']}"
    return 'error' if 'error' in res else 'timeout'


def _sk(seq, spec):
    return (tuple(seq), None if spec is None else (spec[0], bool(spec[1])))


@app.function(timeout=24 * 3600, volumes={"/vol": vol}, retries=0, memory=16384)
def orchestrate(job, runs, per=10):
    """Resumable: a run that was cut off (Modal's 24 h limit) keeps its partial /vol/<name>.json; starting the same job
    again skips every shape already in it and continues with the rest."""
    from collections import Counter
    LOGJOB[0] = job
    _log(f'start {job} {runs}')
    for run in runs.split(','):
        parts = run.split(':')
        N, m = int(parts[0]), int(parts[1])
        lam = parts[2] if len(parts) > 2 and parts[2] else None
        max_turn = int(parts[3]) if len(parts) > 3 else 3        # corners between 180 - 3*(360/N) and 180 + 3*(360/N) degrees
        name = f'{job}_{N}_{m}_t{max_turn}' + (f'_{lam}' if lam else '')
        if os.path.exists(f'/vol/{name}.done'):
            _log(f'{name}: already done, skipped'); continue
        if N == 10 and m % 5:
            _log(f'{name}: impossible (10-fold edge classes need multiples of 5 edges), skipped'); continue
        jobs = _outlines(N, m, max_turn, lam)
        total = len(jobs)
        out, c, flagged = [], Counter(), []
        if os.path.exists(f'/vol/{name}.json'):
            try:
                out = json.load(open(f'/vol/{name}.json'))
            except Exception as e:
                _log(f'{name}: partial results unreadable ({type(e).__name__}), starting this run over'); out = []
            done = set()
            for r in out:
                done.add(_sk(r['seq'], r.get('lens'))); c[_key(r['result'])] += 1
            jobs = [j for j in jobs if _sk(j[0], j[1]) not in done]
            _log(f'{name}: resuming, {len(out)} already tested {dict(c)}, {len(jobs)} left')
        _log(f'{name}: {total} simple shapes to test')
        for part in test.starmap([(jobs[i:i + per], N) for i in range(0, len(jobs), per)], order_outputs=False):
            for r in part:
                out.append(r); res = r['result']
                key = _key(res)
                c[key] += 1
                if 'OPEN' in key or 'UNDECIDED' in key or key == 'timeout':
                    flagged.append(r)
                    _log(f'   {name} {key} {r["seq"]} lens={r["lens"]} {res}')
            if len(out) % 1000 < per:
                if len(out) % 10000 < per:          # the file is large (millions of entries): save every 10,000
                    _save(f'/vol/{name}.json', out)
                _log(f'  {name}: {len(out)}/{total} {dict(c)}')
        _save(f'/vol/{name}.json', out)
        open(f'/vol/{name}.done', 'w').write(json.dumps(dict(c)))
        _log(f'{name} DONE {dict(c)}  (with mirrors / without)')
    _log(f'all done {job}')


@app.function(cpu=1.0, memory=8192, timeout=6 * 3600, retries=2, max_containers=100)
def deep_test(seq, N, spec):
    sys.path.insert(0, "/root/ms")
    import free as F, free_families as FF
    lens = None
    if spec:
        lam, sw = spec
        R = F.Ring(N); L = lam_value(R, lam); one = (1, 0, 0, 0)
        lens = [(L if (d % 2) != sw else one) for d in seq]
    try:
        r = FF.classify_deep(tuple(seq), N, lens)
    except Exception as e:
        r = {'error': repr(e)}
    return dict(seq=seq, lens=spec, N=N, result=r)


@app.function(timeout=24 * 3600, volumes={"/vol": vol}, retries=0)
def retest_all():
    """Collect every UNDECIDED / OPEN / timeout / error entry from all finished result files and re-test it deeply."""
    LOGJOB[0] = 'retest'
    vol.reload()
    _log('retest: start, reading result files')
    items = []
    for fn in sorted(os.listdir('/vol')):
        if not fn.endswith('.json') or fn.startswith('outlines_') or fn.startswith('retest'):
            continue
        parts = fn[:-5].split('_')
        try:
            N = int(parts[1])
        except Exception:
            continue
        try:
            data = json.load(open('/vol/' + fn))
        except Exception as e:                    # a file another job is writing right now
            _log(f'retest: skipped {fn} ({type(e).__name__})'); continue
        for r in data:
            res = r.get('result', {})
            flag = ('timeout' in res) or ('error' in res and 'simple' not in res['error']) or \
                   any(res.get(k, {}).get('cls') in ('UNDECIDED', 'OPEN') for k in ('mirror', 'nomirror'))
            if flag:
                items.append((r['seq'], N, r.get('lens')))
    _log(f'retest: {len(items)} flagged shapes from all result files')
    out = []
    for r in deep_test.starmap(items, order_outputs=False):
        out.append(r); res = r['result']
        key = f"{res['mirror']['cls']}/{res['nomirror']['cls']}" if 'mirror' in res else str(res)[:60]
        _log(f'   N={r["N"]} {key} {r["seq"]} lens={r["lens"]}')
        json.dump(out, open('/vol/retest.json', 'w')); vol.commit()
    _log('retest done')


@app.local_entrypoint()
def main(job: str = "general", runs: str = "10:10"):
    if job == 'retest':
        call = retest_all.spawn()
        print(f'Started the deep re-test of all flagged shapes. Call id {call.object_id}.')
        print('Progress: py -m modal volume get monotile-results progress_retest.txt . --force')
        return
    call = orchestrate.spawn(job, runs)
    print(f'Started {job} in the cloud ({runs}). Call id {call.object_id}.')
    print(f'Your PC can now sleep. Progress: py -m modal volume get monotile-results progress_{job}.txt . --force')
