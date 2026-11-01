"""Run the three-outcome sieve on any grid.

  python3 sieve.py GRID --nmin 1 --nmax 8 [--tcap 12] [--rcap 6] [--workers 2]
                   [--kmax 0] [--verify all|sample|none] [--time-limit SECONDS]
                   [--dovetail "24:10,48:12"]

Stage 1 classifies every free polyform (up to the grid's symmetry group, merged into
congruence classes) as STUCK / PERIODIC / OPEN at (tcap, rcap).  Dovetailing: every shape
still OPEN is re-tested at each larger (tcap:rcap) pair in --dovetail, testing only the new
part of the budget.  Certificates are re-checked by verify.py (all of them, or a sample).
Results: results/<grid>.json (counts) and results/<grid>_shapes.json.gz (every shape).
"""
from __future__ import annotations

import argparse
import gzip
import json
import os
import random
import time
from multiprocessing import Pool

import engine as E
import grids as G
import verify as V

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, 'results')
IMG = os.path.join(HERE, 'open')

_W = {}


def _init(name, cfg):
    _W['g'] = G.get(name)
    _W['cfg'] = cfg


def _classify(arg):
    c = _W['cfg']
    if isinstance(arg, dict):          # dovetail: per-shape completed torus budget
        cells, tmin = arg['cells'], arg['tmin']
    else:
        cells, tmin = arg, c.get('tmin', 0)
    return E.classify(_W['g'], [tuple(x) for x in cells], tcap=c['tcap'], rcap=c['rcap'], kmax=c['kmax'],
                      tmin=tmin, rmin=c.get('rmin'), time_limit=c.get('time_limit'))


def _verify(rec):
    try:
        ok, msg = V.check_record(_W['g'], rec)
    except Exception as e:  # noqa
        ok, msg = False, f'error {e!r}'
    return ok, msg, rec['cls']


def load(name):
    p = os.path.join(OUT, f'{name}.json')
    s = os.path.join(OUT, f'{name}_shapes.json.gz')
    res = json.load(open(p)) if os.path.exists(p) else {}
    shapes = json.load(gzip.open(s, 'rt')) if os.path.exists(s) else {}
    return res, shapes


def save(name, res, shapes):
    os.makedirs(OUT, exist_ok=True)
    with open(os.path.join(OUT, f'{name}.json'), 'w') as f:
        json.dump(res, f, indent=1, sort_keys=True)
    with gzip.open(os.path.join(OUT, f'{name}_shapes.json.gz'), 'wt') as f:
        json.dump(shapes, f, separators=(',', ':'))


def draw_open(g, cells, path, R, title):
    import math
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MP
    from shapely.geometry import Polygon
    from shapely.ops import unary_union
    sh = E.Shape(g, cells)
    ok, patch, region = E.cover(sh, R, return_patch=True)
    sym = {f for f, _ in E.sym_forms(g, sh.cells)}
    # handedness via grid symmetry: classify each placed copy by the op that produced it
    rot_forms = set()
    for k, op in enumerate(g.op_tabs):
        if not g.ops[k][0][1]:
            rot_forms.add(G.normalise(E.transform(g, sh.cells, op)))
    fig, axes = plt.subplots(1, 2, figsize=(13, 6.5), gridspec_kw={'width_ratios': [1, 2]})
    ax = axes[0]
    for c in sh.cells:
        ax.add_patch(MP([G.pf(v) for v in g.cell_vertices(c)], closed=True, fc='#f2c14e', ec='#555', lw=0.6))
    poly = unary_union([Polygon([G.pf(v) for v in g.cell_vertices(c)]) for c in sh.cells])
    if poly.geom_type == 'Polygon':
        xs, ys = poly.exterior.xy
        ax.plot(xs, ys, color='black', lw=2)
    ax.set_aspect('equal')
    ax.autoscale_view()
    ax.axis('off')
    ax.set_title(title, fontsize=10)
    ax = axes[1]
    if ok:
        nm = sum(1 for p in patch if G.normalise(p) not in rot_forms)
        minority = nm * 2 < len(patch)
        for p in patch:
            mir = G.normalise(p) not in rot_forms
            u = unary_union([Polygon([G.pf(v) for v in g.cell_vertices(c)]) for c in p])
            col = '#3a7ca5' if mir == minority else '#d9e8f2'
            if u.geom_type == 'Polygon':
                ax.add_patch(MP(list(u.exterior.coords), closed=True, fc=col, ec='black', lw=0.6))
        th = [2 * math.pi * t / 200 for t in range(201)]
        ax.plot([R * g.unit * math.cos(t) for t in th], [R * g.unit * math.sin(t) for t in th], 'r--', lw=1)
    ax.set_aspect('equal')
    ax.autoscale_view()
    ax.axis('off')
    ax.set_title(f'SAT cover of disc R={R} lattice units ({len(region)} cells; dark = minority handedness)',
                 fontsize=10)
    fig.tight_layout()
    fig.savefig(path, dpi=100)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('grid')
    ap.add_argument('--nmin', type=int, default=1)
    ap.add_argument('--nmax', type=int, default=8)
    ap.add_argument('--workers', type=int, default=2)
    ap.add_argument('--tcap', type=int, default=12)
    ap.add_argument('--rcap', type=float, default=6)
    ap.add_argument('--kmax', type=int, default=0)
    ap.add_argument('--verify', default='all', choices=['all', 'sample', 'none'])
    ap.add_argument('--sample', type=int, default=300)
    ap.add_argument('--dovetail', default='24:8,48:12')
    ap.add_argument('--draw-R', type=float, default=6)
    ap.add_argument('--shape-time', type=float, default=300,
                    help='per-shape wall-clock limit for the torus search in dovetail stages')
    a = ap.parse_args()
    g = G.get(a.grid)
    print(g.describe(), flush=True)
    res, shapes = load(a.grid)
    t0 = time.time()
    lv = E.enumerate_fixed_free(g, a.nmax, verbose=True)
    t_enum = time.time() - t0
    stages = [(a.tcap, a.rcap)]
    for part in [p for p in a.dovetail.split(',') if p]:
        t, r = part.split(':')
        stages.append((int(t), float(r)))
    os.makedirs(IMG, exist_ok=True)
    for n in range(a.nmin, a.nmax + 1):
        tn = time.time()
        classes = E.free_classes(g, lv[n])
        reps = [rep for rep, _ in classes]
        n_sym = len(lv[n])
        t_cls = time.time() - tn
        cfg = dict(tcap=a.tcap, rcap=a.rcap, kmax=a.kmax)
        with Pool(a.workers, initializer=_init, initargs=(a.grid, cfg)) as pool:
            recs = pool.map(_classify, reps, chunksize=8)
        for k, r in enumerate(recs):
            r['id'] = f'{a.grid}{n}_{k:05d}'
            r['stage'] = 0
        t_stage1 = time.time() - tn
        stage_log = [dict(tcap=a.tcap, rcap=a.rcap, open_after=sum(r['cls'] == 'OPEN' for r in recs),
                          seconds=round(t_stage1, 1))]
        # dovetailing
        prev_t, prev_r = a.tcap, a.rcap
        for si, (tc, rc) in enumerate(stages[1:], start=1):
            open_idx = [k for k, r in enumerate(recs) if r['cls'] == 'OPEN']
            if not open_idx:
                break
            ts = time.time()
            cfg2 = dict(tcap=tc, rcap=rc, kmax=a.kmax, tmin=prev_t, rmin=prev_r, time_limit=a.shape_time)
            with Pool(a.workers, initializer=_init, initargs=(a.grid, cfg2)) as pool:
                new = pool.map(_classify, [dict(cells=recs[k]['cells'], tmin=recs[k].get('tori_complete_upto') or prev_t)
                                           for k in open_idx], chunksize=1)
            for k, r in zip(open_idx, new):
                r['id'] = recs[k]['id']
                r['stage'] = si
                if r['cls'] == 'STUCK' and r.get('max_cover_R') is None:
                    r['max_cover_R'] = prev_r
                recs[k] = r
            stage_log.append(dict(tcap=tc, rcap=rc, retested=len(open_idx),
                                  open_after=sum(r['cls'] == 'OPEN' for r in recs),
                                  seconds=round(time.time() - ts, 1)))
            prev_t, prev_r = tc, rc
        # verification
        tv = time.time()
        if a.verify == 'none':
            todo = []
        elif a.verify == 'all':
            todo = [r for r in recs if r['cls'] != 'OPEN']
        else:
            rnd = random.Random(n)
            cert = [r for r in recs if r['cls'] != 'OPEN']
            todo = rnd.sample(cert, min(a.sample, len(cert)))
            # always include every certificate found in a dovetail stage
            todo += [r for r in cert if r['stage'] > 0 and r not in todo]
        vfail = []
        vmeth = {}
        if todo:
            with Pool(a.workers, initializer=_init, initargs=(a.grid, cfg)) as pool:
                vres = pool.map(_verify, todo, chunksize=4)
            for r, (ok, msg, cls) in zip(todo, vres):
                key = cls + ': ' + msg.split(':')[0].split('(')[0].strip()
                vmeth[key] = vmeth.get(key, 0) + 1
                if not ok:
                    vfail.append((r['id'], msg))
        counts = {}
        for r in recs:
            counts[r['cls']] = counts.get(r['cls'], 0) + 1
        tp = [r['tiles_per_domain'] for r in recs if r['cls'] == 'PERIODIC']
        fr = [r['fail_R'] for r in recs if r['cls'] == 'STUCK']
        res[str(n)] = dict(n=n, free=len(recs), sym_classes=n_sym, counts=counts, stages=stage_log,
                           verified=len(todo), verify_mode=a.verify, verify_methods=vmeth,
                           verify_failures=vfail, max_tiles_needed=max(tp) if tp else None,
                           max_fail_R=max(fr) if fr else None,
                           shapes_with_extra_congruent_placements=sum(1 for r in recs if r['n_cong_forms']),
                           wall_time=round(time.time() - tn, 1), verify_time=round(time.time() - tv, 1),
                           enum_time_total=round(t_enum, 1), class_merge_time=round(t_cls, 1),
                           open_ids=[r['id'] for r in recs if r['cls'] == 'OPEN'])
        shapes[str(n)] = recs
        print(f'{a.grid} n={n}: {len(recs)} free ({n_sym} sym)  {counts}  stages {stage_log}  '
              f'verified {len(todo)} fails {len(vfail)}  {time.time() - tn:.1f}s', flush=True)
        for r in recs:
            if r['cls'] == 'OPEN':
                print('   OPEN', r['id'], r['cells'], flush=True)
                try:
                    draw_open(g, [tuple(c) for c in r['cells']], os.path.join(IMG, r['id'] + '.png'),
                              min(a.draw_R, prev_r), f"{r['id']}: {n} {g.cellname}s, OPEN after "
                              f"torus <= {r['tcap']} tiles, disc R <= {r['rcap']}")
                except Exception as e:  # noqa
                    print('   draw failed', e)
        save(a.grid, res, shapes)


if __name__ == '__main__':
    main()
