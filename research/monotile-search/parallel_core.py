"""Pure-Python core of the parallel sieve (no Modal import), so it can be tested locally.

Same three-outcome test and dovetailing as sieve.py, split into independent jobs:
  enumerate_reps(grid, n)        -> list of free shapes (one per congruence class)
  classify_chunk(grid, cfg, xs)  -> records (xs: list of cells, or dicts with cells/tmin)
  verify_chunk(grid, recs)       -> [(ok, msg, cls)]
run_sieve(grid, n, mapper, stages) drives them with any map function (Modal .map or builtin map).
"""
from __future__ import annotations

import gzip
import json
import os
import time


def enumerate_reps(grid, n):
    import engine as E, grids as G
    g = G.get(grid)
    lv = E.enumerate_fixed_free(g, n)
    reps = [rep for rep, _ in E.free_classes(g, lv[n])]
    return [[list(c) for c in rep] for rep in reps], len(lv[n])


def classify_chunk(grid, cfg, xs):
    import engine as E, grids as G
    g = G.get(grid)
    out = []
    for x in xs:
        cells, tmin = (x['cells'], x['tmin']) if isinstance(x, dict) else (x, cfg.get('tmin', 0))
        out.append(E.classify(g, [tuple(c) for c in cells], tcap=cfg['tcap'], rcap=cfg['rcap'],
                              kmax=cfg.get('kmax', 0), tmin=tmin, rmin=cfg.get('rmin'),
                              time_limit=cfg.get('time_limit')))
    return out


def verify_chunk(grid, recs):
    import grids as G, verify as V
    g = G.get(grid)
    out = []
    for r in recs:
        try:
            ok, msg = V.check_record(g, r)
        except Exception as e:  # noqa
            ok, msg = False, f'error {e!r}'
        out.append((ok, msg, r['cls']))
    return out


def chunks(xs, k):
    return [xs[i:i + k] for i in range(0, len(xs), k)]


def run_sieve(grid, n, reps, n_sym, mapper, tcap=12, rcap=6.0, stages=((24, 8), (48, 12)),
              chunk=40, shape_time=300, verify=True):
    """mapper(fn_name, list_of_args) -> list of results, in order."""
    t0 = time.time()
    cfg = dict(tcap=tcap, rcap=rcap)
    recs = [r for part in mapper('classify', [(grid, cfg, c) for c in chunks(reps, chunk)]) for r in part]
    for k, r in enumerate(recs):
        r['id'] = f'{grid}{n}_{k:05d}'; r['stage'] = 0
    log = [dict(tcap=tcap, rcap=rcap, open_after=sum(r['cls'] == 'OPEN' for r in recs),
                seconds=round(time.time() - t0, 1))]
    pt, pr = tcap, rcap
    for si, (tc, rc) in enumerate(stages, start=1):
        idx = [k for k, r in enumerate(recs) if r['cls'] == 'OPEN']
        if not idx:
            break
        ts = time.time()
        cfg2 = dict(tcap=tc, rcap=rc, tmin=pt, rmin=pr, time_limit=shape_time)
        args = [(grid, cfg2, [dict(cells=recs[k]['cells'], tmin=recs[k].get('tori_complete_upto') or pt)]) for k in idx]
        new = [p[0] for p in mapper('classify', args)]
        for k, r in zip(idx, new):
            r['id'] = recs[k]['id']; r['stage'] = si
            if r['cls'] == 'STUCK' and r.get('max_cover_R') is None:
                r['max_cover_R'] = pr
            recs[k] = r
        log.append(dict(tcap=tc, rcap=rc, retested=len(idx), open_after=sum(r['cls'] == 'OPEN' for r in recs),
                        seconds=round(time.time() - ts, 1)))
        pt, pr = tc, rc
    vfail, nver = [], 0
    if verify:
        cert = [r for r in recs if r['cls'] != 'OPEN']
        nver = len(cert)
        for part, recs_part in zip(mapper('verify', [(grid, c) for c in chunks(cert, chunk)]), chunks(cert, chunk)):
            for (ok, msg, _), r in zip(part, recs_part):
                if not ok:
                    vfail.append((r['id'], msg))
    counts = {}
    for r in recs:
        counts[r['cls']] = counts.get(r['cls'], 0) + 1
    summary = dict(n=n, free=len(recs), sym_classes=n_sym, counts=counts, stages=log, verified=nver,
                   verify_failures=vfail, wall_time=round(time.time() - t0, 1),
                   open_ids=[r['id'] for r in recs if r['cls'] == 'OPEN'])
    return summary, recs


def save(outdir, grid, n, summary, recs):
    os.makedirs(outdir, exist_ok=True)
    p = os.path.join(outdir, f'{grid}.json')
    res = json.load(open(p)) if os.path.exists(p) else {}
    res[str(n)] = summary
    json.dump(res, open(p, 'w'), indent=1, sort_keys=True)
    with gzip.open(os.path.join(outdir, f'{grid}{n}_shapes.json.gz'), 'wt') as f:
        json.dump(recs, f, separators=(',', ':'))


if __name__ == '__main__':  # local self-test: same pipeline with builtin map
    import sys
    grid, n = sys.argv[1], int(sys.argv[2])
    reps, n_sym = enumerate_reps(grid, n)
    fns = {'classify': classify_chunk, 'verify': verify_chunk}
    s, recs = run_sieve(grid, n, reps, n_sym, lambda f, args: [fns[f](*a) for a in args])
    print(json.dumps({k: s[k] for k in ('n', 'free', 'counts', 'verified', 'verify_failures', 'open_ids')}))
