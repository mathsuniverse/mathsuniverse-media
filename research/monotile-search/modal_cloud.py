"""Everything runs in the cloud: your PC only starts the job (and may then sleep or disconnect).
Results are saved in the Modal volume "monotile-results" as they come in.

Start (returns at once):
    py -m modal run --detach modal_cloud.py --job general  --runs "10:10,12:12,10:12,10:14,12:14,8:16"
    py -m modal run --detach modal_cloud.py --job hatroute --runs "12:14:r3,10:12:phi,10:14:phi,8:12:r2,8:14:r2,8:12:1+r2,8:14:1+r2,12:14:2+r3"
Progress (any time):
    py -m modal volume get monotile-results progress_general.txt . --force   (or progress_hatroute.txt), then open it
Deep re-test of the flagged (OPEN / UNDECIDED / error) shapes of one job, e.g. night2:
    py -m modal run --detach modal_cloud.py --job retest --runs night2
    py -m modal volume get monotile-results progress_retest.txt . --force
Very deep test of ONE shape (both mirror settings side by side, up to ~22 h):
    py -m modal run --detach modal_cloud.py --job deep1 --runs "12:0,0,2,5,3,6,4,7,9,6,8,11,1,10"
    py -m modal volume get monotile-results progress_deep1_nomirror.txt . --force   (and progress_deep1_mirror.txt)
Hunt for a periodic tiling of ONE candidate (every lattice up to 48-tile cells, in parallel, both mirror settings):
    py -m modal run --detach modal_cloud.py --job breakit --runs "12:0,0,2,5,3,6,4,7,9,6,8,11,1,10"
    py -m modal volume get monotile-results progress_breakit_nomirror.txt . --force   (and progress_breakit_mirror.txt)
Fetch all results into results\\cloud:
    py -m modal volume get monotile-results / results\\cloud --force

general  = equal-edge outlines (Spectre route), N = 8, 10, 12 directions, m edges; control: Tile(1,1) in 12:14
hatroute = Tile(a,b)-type outlines with b/a in {r3, 2+r3, phi, r2, 1+r2}; control: hat and turtle in 12:14:r3
parity   = same outlines, placed with the 60-degree orientation group only (parity.py, THEORY.md s10);
           py -m modal run --detach modal_cloud.py --job parity --runs "12:14,12:16"   control: Tile(1,1) OPEN/STUCK in 12:14
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
def enum_slice(N, m, first, max_turn, lam, tag=None):
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
    return out if tag is None else (tag, out)


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


@app.function(cpu=1.0, memory=4096, timeout=6 * 3600, retries=2, max_containers=200)
def test(chunk, N, mode='general'):
    sys.path.insert(0, "/root/ms")
    import free as F, free_families as FF, parity as P
    out = []
    for seq, spec in chunk:
        try:
            lens = None
            if spec:
                lam, sw = spec
                R = F.Ring(N); L = lam_value(R, lam); one = (1, 0, 0, 0)
                lens = [(L if (d % 2) != sw else one) for d in seq]
            r = P.classify(tuple(seq), N, lens, step=2) if mode == 'parity' else FF.classify_general(tuple(seq), N, lens)
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
    # each slice is saved as soon as it returns, so a restarted job (pre-emption) only lists the missing slices
    sdir = f'/vol/outlines_{tag}_slices'
    os.makedirs(sdir, exist_ok=True)
    fname = lambda f: os.path.join(sdir, '_'.join(str(x) for x in f) + '.json')
    todo = [f for f in firsts if not os.path.exists(fname(f))]
    _log(f'outlines {tag}: {len(firsts) - len(todo)}/{len(firsts)} slices already listed, {len(todo)} to go')
    done_n = len(firsts) - len(todo)
    for f, part in enum_slice.starmap([(N, m, f, max_turn, lam, f) for f in todo], order_outputs=False):
        _save(fname(f), part); vol.commit(); done_n += 1
        if done_n % 50 == 0:
            _log(f'outlines {tag}: {done_n}/{len(firsts)} slices listed')
    seen, S = set(), []
    for f in firsts:
        for s, spec in json.load(open(fname(f))):
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


def _hk(seq, spec):
    return hash((tuple(seq), None if spec is None else int(bool(spec[1]))))


@app.function(timeout=24 * 3600, volumes={"/vol": vol}, retries=0, memory=32768, cpu=2.0)
def orchestrate(job, runs, per=20, part_size=10000):
    """Resumable. Results go to /vol/<name>_parts/part_NNNNNN.json, one new small file per 10,000 shapes (atomic writes,
    never rewritten), so a run cut off by Modal's 24 h limit loses at most the last 10,000. Starting the same job again
    reads every part (and an old single /vol/<name>.json if it is readable), skips those shapes and continues."""
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
        pdir = f'/vol/{name}_parts'
        os.makedirs(pdir, exist_ok=True)
        c, done, n_done = Counter(), set(), 0
        sources = [os.path.join(pdir, f) for f in sorted(os.listdir(pdir)) if f.endswith('.json')]
        if os.path.exists(f'/vol/{name}.json'):
            sources.insert(0, f'/vol/{name}.json')
        for src in sources:
            try:
                data = json.load(open(src))
            except Exception as e:
                _log(f'{name}: {os.path.basename(src)} unreadable ({type(e).__name__}), its shapes will be re-tested'); continue
            for r in data:
                k = _hk(r['seq'], r.get('lens'))
                if k not in done:
                    done.add(k); c[_key(r['result'])] += 1
            del data
        n_done = len(done)
        if n_done:
            jobs = [j for j in jobs if _hk(j[0], j[1]) not in done]
            _log(f'{name}: resuming, {n_done} already tested {dict(c)}, {len(jobs)} left')
        del done
        _log(f'{name}: {total} simple shapes to test')
        nxt = len([f for f in os.listdir(pdir) if f.endswith('.json')])
        buf, tested = [], n_done
        for part in test.starmap([(jobs[i:i + per], N, 'parity' if job == 'parity' else 'general') for i in range(0, len(jobs), per)], order_outputs=False):
            for r in part:
                buf.append(r); tested += 1
                key = _key(r['result'])
                c[key] += 1
                if 'OPEN' in key or 'UNDECIDED' in key or key == 'timeout':
                    _log(f'   {name} {key} {r["seq"]} lens={r["lens"]} {r["result"]}')
            if len(buf) >= part_size:
                _save(f'{pdir}/part_{nxt:06d}.json', buf); nxt += 1; buf = []
                _log(f'  {name}: {tested}/{total} {dict(c)}')
        if buf:
            _save(f'{pdir}/part_{nxt:06d}.json', buf)
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


def _result_files(job_filter=None):
    """Every result file on the volume: old single files (/vol/<name>.json) and the newer part files
    (/vol/<name>_parts/part_NNNNNN.json). Yields (path, name, N)."""
    for fn in sorted(os.listdir('/vol')):
        full = '/vol/' + fn
        if fn.endswith('_parts') and os.path.isdir(full):
            name = fn[:-len('_parts')]
            files = [os.path.join(full, f) for f in sorted(os.listdir(full)) if f.endswith('.json')]
        elif fn.endswith('.json') and not fn.startswith(('outlines_', 'retest')):
            name, files = fn[:-5], [full]
        else:
            continue
        if job_filter and not name.startswith(job_filter):
            continue
        try:
            N = int(name.split('_')[1])
        except Exception:
            continue
        for path in files:
            yield path, name, N


@app.function(timeout=24 * 3600, volumes={"/vol": vol}, retries=0)
def retest_all(job_filter=None):
    """Collect every UNDECIDED / OPEN / timeout / error entry from the result files (all jobs, or only those whose
    name starts with job_filter, e.g. "night2") and re-test it deeply. Resumable: shapes already in the output file
    are skipped. Output: /vol/retest.json (all jobs) or /vol/retest_<job_filter>.json."""
    LOGJOB[0] = 'retest'
    vol.reload()
    tag = job_filter or 'all'
    out_path = '/vol/retest.json' if not job_filter else f'/vol/retest_{job_filter}.json'
    _log(f'retest[{tag}]: start, reading result files (single files and _parts folders)')
    items, seen, unreadable = [], set(), 0
    for path, name, N in _result_files(job_filter):
        try:
            data = json.load(open(path))
        except Exception as e:                    # a file another job is writing right now, or a damaged one
            unreadable += 1
            _log(f'retest[{tag}]: skipped {os.path.relpath(path, "/vol")} ({type(e).__name__})'); continue
        for r in data:
            res = r.get('result', {})
            flag = ('timeout' in res) or ('error' in res and 'simple' not in res['error']) or \
                   any(res.get(k, {}).get('cls') in ('UNDECIDED', 'OPEN') for k in ('mirror', 'nomirror'))
            if flag:
                k = (N,) + _sk(r['seq'], r.get('lens'))
                if k not in seen:
                    seen.add(k); items.append((r['seq'], N, r.get('lens')))
    out = []
    if os.path.exists(out_path):
        try:
            out = json.load(open(out_path))
        except Exception:
            out = []
    done = {(r['N'],) + _sk(r['seq'], r.get('lens')) for r in out}
    todo = [it for it in items if (it[1],) + _sk(it[0], it[2]) not in done]
    _log(f'retest[{tag}]: {len(items)} flagged shapes ({unreadable} unreadable files), '
         f'{len(items) - len(todo)} already re-tested, {len(todo)} to go')
    for r in deep_test.starmap(todo, order_outputs=False):
        out.append(r); res = r['result']
        key = f"{res['mirror']['cls']}/{res['nomirror']['cls']}" if 'mirror' in res else str(res)[:60]
        _log(f'   N={r["N"]} {key} {r["seq"]} lens={r["lens"]}')
        _save(out_path, out); vol.commit()
    still = [r for r in out if 'mirror' in r['result'] and 'OPEN' in
             (r['result']['mirror']['cls'], r['result'].get('nomirror', {}).get('cls'))]
    _log(f'retest[{tag}] done: {len(out)} re-tested, {len(still)} still OPEN after the deep test')
    for r in still:
        _log(f'   STILL OPEN N={r["N"]} {r["seq"]} lens={r["lens"]} {r["result"]}')


# ---------------------------------------------------------------- one shape, as deep as a container allows
@app.function(cpu=1.0, memory=16384, timeout=24 * 3600, volumes={"/vol": vol}, retries=0)
def deep_one(seq, N, mirror, spec=None):
    """Very deep test of ONE outline, one mirror setting per container (the two run side by side).
    Patches to radius 4..8 (5 M nodes, 3 h each; every patch reached is saved for drawing), then repeats read off the
    biggest patch (cells up to 128 tiles, 3 h), then all short repeat patterns (24 tiles, 14-edge vectors, 4 h).
    Log: progress_deep1_mirror.txt / progress_deep1_nomirror.txt. Result: /vol/deep1_<tag>.json"""
    sys.path.insert(0, "/root/ms")
    import free as F, free2 as F2
    side = 'mirror' if mirror else 'nomirror'
    LOGJOB[0] = f'deep1_{side}'
    tag = f"{N}_{'-'.join(map(str, seq))}_{side}"
    lens = None
    if spec:
        lam, sw = spec
        R = F.Ring(N); L = lam_value(R, lam); one = (1, 0, 0, 0)
        lens = [(L if (d % 2) != sw else one) for d in seq]
    S = F2.Search(list(seq), N, mirror, lens)
    res = dict(seq=seq, N=N, side=side, stages=[])
    def stage(**kw):
        res['stages'].append(kw); _save(f'/vol/deep1_{tag}.json', res); vol.commit()
    _log(f'deep1[{side}] start N={N} {seq}  (tile has {S.tile.m} edges, {len(S.orients)} orientations)')
    best, best_patch = None, None
    for Rad in (4, 5, 6, 7, 8):
        t0 = time.time()
        r = S.cover(Rad * S.diam / 2, node_limit=5_000_000, time_limit=3 * 3600)
        dt = round(time.time() - t0)
        if r is None:
            _log(f'deep1[{side}] radius {Rad}: search budget used up after {S.nodes} nodes, {dt}s (UNDECIDED here)')
            stage(step='cover', R=Rad, result='budget', nodes=S.nodes, secs=dt); break
        if not r:
            _log(f'deep1[{side}] radius {Rad}: DEAD END, no patch of this radius exists ({S.nodes} nodes, {dt}s) -> STUCK')
            stage(step='cover', R=Rad, result='STUCK', nodes=S.nodes, secs=dt)
            res['final'] = 'STUCK'; stage(step='final', cls='STUCK', fail_R=Rad); return res
        best, best_patch = Rad, list(S.patch)
        polys = [[list(S.ring.f(x)) for x in S.verts(pl)] for pl in best_patch]
        _save(f'/vol/deep1_{tag}_patch_R{Rad}.json', dict(orients=[pl[0] for pl in best_patch], polys=polys))
        _log(f'deep1[{side}] radius {Rad}: covered, {len(best_patch)} tiles ({S.nodes} nodes, {dt}s), patch saved')
        stage(step='cover', R=Rad, result='covered', tiles=len(best_patch), nodes=S.nodes, secs=dt)
    if best is None:
        res['final'] = 'UNDECIDED'; stage(step='final', cls='UNDECIDED'); return res
    t0 = time.time()
    p = F2.patch_periods(S, patch=best_patch, max_tiles=128, top=600, node_limit=200000, budget=3 * 3600)
    _log(f'deep1[{side}] repeats read off the radius-{best} patch: {p[0] if p[0] else ("none" if p[0] is False else "budget")}'
         f' ({p[1]} lattices tested, {round(time.time() - t0)}s)')
    stage(step='patch_periods', result=p[0] if p[0] else str(p[0]), tested=p[1])
    if p[0]:
        res['final'] = 'PERIODIC'; stage(step='final', cls='PERIODIC', **p[0]); _log(f'deep1[{side}] FINAL: PERIODIC'); return res
    t0 = time.time()
    q = F2.periodic4(S, 24, 14, budget=4 * 3600, node_limit=100000)
    _log(f'deep1[{side}] short repeat patterns (<=24 tiles): {q[0] if q[0] else ("none" if q[0] is False else "budget")}'
         f' ({q[1]}/{q[2]} lattices, {q[3]} undecided, {round(time.time() - t0)}s)')
    stage(step='periodic4', result=q[0] if q[0] else str(q[0]), tested=q[1], total=q[2], undecided=q[3])
    if q[0]:
        res['final'] = 'PERIODIC'; stage(step='final', cls='PERIODIC', **q[0]); _log(f'deep1[{side}] FINAL: PERIODIC'); return res
    res['final'] = 'OPEN'; stage(step='final', cls='OPEN', covered_R=best)
    _log(f'deep1[{side}] FINAL: OPEN - covered to radius {best}, no repeating pattern found')
    return res


# ---------------------------------------------------------------- try to BREAK one candidate: hunt for a periodic tiling
@app.function(cpu=1.0, memory=4096, timeout=6 * 3600, retries=2, max_containers=150)
def torus_chunk(seq, N, mirror, chunk, node_limit):
    """Test one slice of period lattices. Returns the first lattice that tiles (a PERIODIC certificate) and counts."""
    sys.path.insert(0, "/root/ms")
    import free2 as F2
    S = F2.Search(list(seq), N, mirror, None)
    no = und = 0
    for k, a, b in chunk:
        r = F2.torus_dfs(S, tuple(a), tuple(b), node_limit)
        if r:
            return dict(found=dict(tiles=k, p1=list(a), p2=list(b)), no=no, und=und)
        if r is None:
            und += 1
        else:
            no += 1
    return dict(found=None, no=no, und=und)


@app.function(cpu=2.0, memory=32768, timeout=24 * 3600, volumes={"/vol": vol}, retries=1)
def breakit(seq, N, mirror, max_tiles=48, max_edges=16, node_limit=200000, chunk_size=400):
    """Every period lattice with a cell of <= max_tiles tiles and basis vectors of <= max_edges unit edges, tested in
    parallel (smallest cells first). Resumable: finished chunks are recorded in /vol/breakit_<tag>.json.
    Log: progress_breakit_mirror.txt / progress_breakit_nomirror.txt"""
    sys.path.insert(0, "/root/ms")
    import free2 as F2
    side = 'mirror' if mirror else 'nomirror'
    LOGJOB[0] = f'breakit_{side}'
    tag = f"{N}_{'-'.join(map(str, seq))}_{side}_{max_tiles}_{max_edges}"
    state_path = f'/vol/breakit_{tag}.json'
    vol.reload()
    state = json.load(open(state_path)) if os.path.exists(state_path) else dict(done=[], no=0, und=0, found=None)
    if state.get('found'):
        _log(f'breakit[{side}] already FOUND a periodic tiling: {state["found"]}'); return state
    S = F2.Search(list(seq), N, mirror, None)
    t0 = time.time()
    pairs = F2.period_pairs_paths(S, max_tiles, max_edges)
    chunks = [pairs[i:i + chunk_size] for i in range(0, len(pairs), chunk_size)]
    done = set(state['done'])
    todo = [i for i in range(len(chunks)) if i not in done]
    _log(f'breakit[{side}] N={N} {seq}: {len(pairs)} lattices (cells <= {max_tiles} tiles, vectors <= {max_edges} edges), '
         f'{len(chunks)} chunks, {len(todo)} to go; listing took {round(time.time() - t0)}s')
    args = [(seq, N, mirror, [(k, list(a), list(b)) for k, a, b in chunks[i]], node_limit) for i in todo]
    n = 0
    for i, r in zip(todo, torus_chunk.starmap(args, order_outputs=True)):
        n += 1
        state['done'].append(i); state['no'] += r['no']; state['und'] += r['und']
        if r['found']:
            state['found'] = r['found']
            _save(state_path, state); vol.commit()
            _log(f'breakit[{side}] FOUND A PERIODIC TILING: cell of {r["found"]["tiles"]} tiles, periods {r["found"]["p1"]}, '
                 f'{r["found"]["p2"]}  -> the candidate is NOT aperiodic{" with mirrors" if mirror else ""}')
            return state
        if n % 10 == 0 or n == len(todo):
            _save(state_path, state); vol.commit()
            _log(f'breakit[{side}] {len(state["done"])}/{len(chunks)} chunks: {state["no"]} lattices ruled out, '
                 f'{state["und"]} undecided (search limit), up to {chunks[i][-1][0]}-tile cells')
    _log(f'breakit[{side}] DONE: no periodic tiling among {state["no"] + state["und"]} lattices '
         f'({state["no"]} ruled out exactly, {state["und"]} undecided)')
    return state


@app.local_entrypoint()
def main(job: str = "general", runs: str = "10:10"):
    if job == 'retest':
        # --runs all (default "10:10" also means all) or a job-name prefix such as --runs night2
        flt = None if runs in ('all', '10:10', '') else runs
        call = retest_all.spawn(flt)
        print(f'Started the deep re-test of flagged shapes ({flt or "all jobs"}). Call id {call.object_id}.')
        print('Progress: py -m modal volume get monotile-results progress_retest.txt . --force')
        return
    if job == 'breakit':
        # --runs "12:0,0,2,5,3,6,4,7,9,6,8,11,1,10"   (N : the outline); both mirror settings side by side
        N, seq = runs.split(':'); N = int(N); seq = [int(x) for x in seq.split(',')]
        ids = [breakit.spawn(seq, N, m).object_id for m in (False, True)]
        print(f'Started the periodic-tiling hunt for N={N} {seq}, without and with mirrors. Call ids {ids}.')
        print('Progress: py -m modal volume get monotile-results progress_breakit_nomirror.txt . --force')
        print('     and: py -m modal volume get monotile-results progress_breakit_mirror.txt . --force')
        return
    if job == 'deep1':
        # --runs "12:0,0,2,5,3,6,4,7,9,6,8,11,1,10"   (N : the outline)
        N, seq = runs.split(':'); N = int(N); seq = [int(x) for x in seq.split(',')]
        ids = [deep_one.spawn(seq, N, m).object_id for m in (True, False)]
        print(f'Started the deep test of N={N} {seq}, with and without mirrors. Call ids {ids}.')
        print('Progress: py -m modal volume get monotile-results progress_deep1_mirror.txt . --force')
        print('     and: py -m modal volume get monotile-results progress_deep1_nomirror.txt . --force')
        return
    call = orchestrate.spawn(job, runs)
    print(f'Started {job} in the cloud ({runs}). Call id {call.object_id}.')
    print(f'Your PC can now sleep. Progress: py -m modal volume get monotile-results progress_{job}.txt . --force')
