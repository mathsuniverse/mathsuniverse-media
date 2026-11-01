"""Classify every free polykite of size n = 1..nmax.

Classes
  no_tile    : some disc cannot be covered (so it cannot tile the plane on the kite
               grid); Heesch number recorded.
  periodic   : tiles a torus (=> tiles the plane periodically).
  candidate  : covers every disc up to R_cap, but no torus tiling with <= T_cap tiles in
               the fundamental domain.  This ONLY means "no periodic tiling found up to
               the caps"; it is not a proof of anything.

Usage:  python3 search.py --nmax 8 [--workers 2] [--tcap 12] [--rcap 6] [--kmax 5]
Results are merged into results.json (keyed by n), so sizes can be run separately.
"""
from __future__ import annotations

import argparse
import json
import os
import time
from multiprocessing import Pool

import polykite as P
import tiler as T

HERE = os.path.dirname(os.path.abspath(__file__))
RESULTS = os.path.join(HERE, 'results.json')
IMGDIR = os.path.join(HERE, 'candidates')

CFG = {}


def classify(cells):
    cells = [tuple(c) for c in cells]
    t0 = time.time()
    rec = {'cells': [list(c) for c in cells], 'n': len(cells)}
    rs = [r for r in (2, 3, 4, 5, 6, 8, 10, 12) if r <= CFG['rcap']]
    if CFG['rcap'] not in rs:
        rs.append(CFG['rcap'])
    # 1. quick disc test
    if not T.cover(cells, 1.5):
        rec.update(cls='no_tile', max_cover_R=None, fail_R=1.5)
    else:
        per = T.periodic(cells, CFG['tcap'])
        if per is not None:
            lat, tiles = per
            rec.update(cls='periodic', lattice=list(lat), tiles_per_domain=tiles)
        else:
            best, fail = T.max_cover_radius(cells, rs)
            if fail is not None:
                rec.update(cls='no_tile', max_cover_R=best if best else 1.5, fail_R=fail)
            else:
                rec.update(cls='candidate', max_cover_R=best)
    if rec['cls'] == 'no_tile' and CFG['kmax'] > 0:
        th = time.time()
        k, _, capped = T.heesch(cells, CFG['kmax'], time_budget=CFG['hbudget'])
        rec.update(heesch=k, heesch_lower_bound_only=capped, heesch_time=round(time.time() - th, 2))
    rec['time'] = round(time.time() - t0, 3)
    return rec


def _init(cfg):
    CFG.update(cfg)


def draw_candidate(cells, path, R, title):
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MP
    ok, patch, region = T.cover(cells, R, return_patch=True)
    fig, axes = plt.subplots(1, 2, figsize=(12, 6.2), gridspec_kw={'width_ratios': [1, 2]})
    ax = axes[0]
    for c in cells:
        ax.add_patch(MP(P.kite_xy(tuple(c)), closed=True, fc='#f2c14e', ec='#555', lw=0.6))
    poly = P.polykite_polygon([tuple(c) for c in cells])
    xs, ys = poly.exterior.xy
    ax.plot(xs, ys, color='black', lw=2)
    ax.set_aspect('equal')
    ax.autoscale_view()
    ax.axis('off')
    ax.set_title(title)
    ax = axes[1]
    nref = sum(1 for _, refl in patch if refl)
    minority = nref * 2 < len(patch)       # colour the rarer handedness dark
    for ks, refl in patch:
        pk = P.polykite_polygon(ks)
        col = '#3a7ca5' if refl == minority else '#d9e8f2'
        ax.add_patch(MP(list(pk.exterior.coords), closed=True, fc=col, ec='black', lw=0.7))
    import math
    th = [2 * math.pi * t / 200 for t in range(201)]
    ax.plot([R * T.H * math.cos(t) for t in th], [R * T.H * math.sin(t) for t in th], 'r--', lw=1)
    ax.set_aspect('equal')
    ax.autoscale_view()
    ax.axis('off')
    ax.set_title(f'SAT cover of disc R={R} hex spacings (dark = mirror-image copies)')
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--nmin', type=int, default=1)
    ap.add_argument('--nmax', type=int, default=8)
    ap.add_argument('--workers', type=int, default=2)
    ap.add_argument('--tcap', type=int, default=12, help='max tiles per torus fundamental domain')
    ap.add_argument('--rcap', type=float, default=6, help='max disc radius (hex spacings)')
    ap.add_argument('--kmax', type=int, default=5, help='max Heesch number tested (0 = skip)')
    ap.add_argument('--hbudget', type=float, default=60, help='seconds per Heesch computation')
    a = ap.parse_args()
    cfg = dict(tcap=a.tcap, rcap=a.rcap, kmax=a.kmax, hbudget=a.hbudget)
    results = {}
    if os.path.exists(RESULTS):
        with open(RESULTS) as f:
            results = json.load(f)
    t_enum = time.time()
    levels = P.enumerate_free(a.nmax)
    print(f'enumerated in {time.time() - t_enum:.1f}s', flush=True)
    hat_can = list(map(list, P.canonical(P.hat_cells())))
    tur_can = list(map(list, P.canonical(P.turtle_cells())))
    os.makedirs(IMGDIR, exist_ok=True)
    with Pool(a.workers, initializer=_init, initargs=(cfg,)) as pool:
        for n in range(a.nmin, a.nmax + 1):
            t0 = time.time()
            recs = pool.map(classify, levels[n], chunksize=4)
            for idx, r in enumerate(recs):
                r['id'] = f'n{n}_{idx:05d}'
                r['is_hat'] = r['cells'] == hat_can
                r['is_turtle'] = r['cells'] == tur_can
            counts = {}
            for r in recs:
                counts[r['cls']] = counts.get(r['cls'], 0) + 1
            hh = {}
            for r in recs:
                if 'heesch' in r:
                    key = f"{r['heesch']}{'+' if r['heesch_lower_bound_only'] else ''}"
                    hh[key] = hh.get(key, 0) + 1
            results[str(n)] = dict(config=cfg, counts=counts, heesch_hist=hh,
                                   wall_time=round(time.time() - t0, 1), shapes=recs)
            print(f'n={n}: {len(recs)} shapes  {counts}  heesch {hh}  {time.time() - t0:.1f}s', flush=True)
            for r in recs:
                if r['cls'] == 'candidate':
                    tag = ' (HAT)' if r['is_hat'] else ' (TURTLE)' if r['is_turtle'] else ''
                    print('   candidate', r['id'], tag, flush=True)
                    draw_candidate(r['cells'], os.path.join(IMGDIR, r['id'] + '.png'), min(a.rcap, 5),
                                   f"{r['id']}{tag}: {n} kites")
            with open(RESULTS, 'w') as f:
                json.dump(results, f)



def draw_heesch(cells, path, title, kmax=5):
    """Picture of the largest corona structure found around a non-tiler."""
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Polygon as MP
    k, levels, capped = T.heesch([tuple(c) for c in cells], kmax)
    cols = ['#e4572e', '#f2c14e', '#76b041', '#3a7ca5', '#8e6c8a', '#2f4858']
    fig, ax = plt.subplots(figsize=(7, 7))
    for L, lv in enumerate(levels):
        for ks in lv:
            pk = P.polykite_polygon(ks)
            ax.add_patch(MP(list(pk.exterior.coords), closed=True, fc=cols[L % len(cols)], ec='black', lw=0.8))
    ax.set_aspect('equal')
    ax.autoscale_view()
    ax.axis('off')
    ax.set_title(f'{title}: Heesch number {k}{"+" if capped else ""} (one colour per corona)')
    fig.tight_layout()
    fig.savefig(path, dpi=110)
    plt.close(fig)
    return k


if __name__ == '__main__':
    main()
