"""Frequency fingerprint of a shape on a SAT-covered disc.

  python3 fingerprint.py GRID --cells "[[i,j,t],...]" --R 6,8,10 [--name hat] [--time 300]
  python3 fingerprint.py kite --name hat|turtle

For each radius R (increasing, until a cover fails or the time budget runs out) the disc is
covered by SAT, and every placed copy is classified by the orientation (fixed form) it uses:
rotation class, and mirror vs non-mirror (a form reached only by reflections of the grid,
or, on the chiral floret grid, an off-group congruent copy).  Counts are reported for all
tiles and for tiles lying wholly inside radius R-2 (less boundary bias).

The ratios are compared with metallic-mean powers.  SAT patches are not hierarchical and
the solver picks *some* cover, so this is weak evidence only: a periodic tiler can give
any ratio on a disc, and an aperiodic one need not show its limiting ratio on a small one.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import time

import engine as E
import grids as G

PHI = (1 + 5 ** .5) / 2
SILVER = 1 + 2 ** .5
BRONZE = (3 + 13 ** .5) / 2
TARGETS = {'phi': PHI, 'phi^2': PHI ** 2, 'phi^3': PHI ** 3, 'phi^4': PHI ** 4,
           'silver': SILVER, 'silver^2': SILVER ** 2, 'bronze': BRONZE, 'bronze^2': BRONZE ** 2,
           'sqrt2': 2 ** .5, 'sqrt3': 3 ** .5}
HERE = os.path.dirname(os.path.abspath(__file__))


def form_labels(g, cells):
    """form -> (op index, mirror flag) for every fixed form of the shape.  mirror is
    None when the form is reached by both a rotation and a reflection (achiral shape)."""
    sh = E.Shape(g, cells)
    lab = {}
    for k, op in enumerate(g.op_tabs):
        f = G.normalise(E.transform(g, sh.cells, op))
        mir = bool(g.ops[k][0][1])
        if f not in lab:
            lab[f] = [k, {mir}]
        else:
            lab[f][1].add(mir)
    for f in sh.forms:
        if f not in lab:          # off-group congruent copy (mirror image on a chiral grid)
            lab[f] = [-1, {True}]
    out = {}
    for f, (k, ms) in lab.items():
        out[f] = (k, (next(iter(ms)) if len(ms) == 1 else None))
    return sh, out


def nearest_targets(x, k=2):
    return sorted(((abs(x - v) / v, n) for n, v in TARGETS.items()))[:k]


def fingerprint_patch(g, sh, labels, patch, R):
    inner = (R - 2) * g.unit
    tot = {}
    inn = {}
    for p in patch:
        f = G.normalise(p)
        k, mir = labels[f]
        key = (f, mir)
        tot[key] = tot.get(key, 0) + 1
        cs = [g.area_centroid_f(c) for c in p]
        if all(x * x + y * y <= inner * inner for x, y in cs):
            inn[key] = inn.get(key, 0) + 1

    def summ(cnt):
        n = sum(cnt.values())
        mir = sum(v for (f, m), v in cnt.items() if m is True)
        rot = sum(v for (f, m), v in cnt.items() if m is False)
        orient = sorted(cnt.values(), reverse=True)
        d = dict(tiles=n, orientations_used=len(cnt), orientation_counts=orient,
                 non_mirror=rot, mirror=mir)
        if rot and mir:
            hi, lo = max(rot, mir), min(rot, mir)
            d['majority_to_minority_handedness'] = round(hi / lo, 4)
            d['nearest'] = [(n_, round(e, 4)) for e, n_ in nearest_targets(hi / lo)]
        if len(orient) >= 2 and orient[-1]:
            d['max_to_min_orientation'] = round(orient[0] / orient[-1], 4)
        return d
    return dict(R=R, all=summ(tot), inner=summ(inn))


def run(g, cells, Rs, budget):
    sh, labels = form_labels(g, cells)
    achiral = any(m is None for _, m in labels.values())
    out = dict(grid=g.name, n=len(cells), cells=[list(c) for c in sh.cells], achiral=achiral,
               n_forms=len(sh.forms), patches=[])
    t0 = time.time()
    for R in Rs:
        if time.time() - t0 > budget:
            out['stopped'] = f'time budget {budget}s'
            break
        ts = time.time()
        ok, patch, region = E.cover(sh, R, return_patch=True)
        if not ok:
            out['patches'].append(dict(R=R, covered=False))
            break
        fp = fingerprint_patch(g, sh, labels, patch, R)
        fp['cells_in_disc'] = len(region)
        fp['seconds'] = round(time.time() - ts, 1)
        out['patches'].append(fp)
        print(json.dumps(fp), flush=True)
    return out


def main():
    import polykite as PK
    ap = argparse.ArgumentParser()
    ap.add_argument('grid')
    ap.add_argument('--cells')
    ap.add_argument('--name')
    ap.add_argument('--R', default='4,6,8,10,12')
    ap.add_argument('--time', type=float, default=300)
    a = ap.parse_args()
    g = G.get(a.grid)
    if a.cells:
        cells = [tuple(c) for c in json.loads(a.cells)]
    elif a.name == 'hat':
        cells = PK.hat_cells()
    elif a.name == 'turtle':
        cells = PK.turtle_cells()
    else:
        raise SystemExit('need --cells or --name hat|turtle')
    Rs = [float(r) for r in a.R.split(',')]
    res = run(g, cells, Rs, a.time)
    name = a.name or 'shape'
    os.makedirs(os.path.join(HERE, 'results', 'fingerprints'), exist_ok=True)
    with open(os.path.join(HERE, 'results', 'fingerprints', f'{a.grid}_{name}.json'), 'w') as f:
        json.dump(res, f, indent=1)


if __name__ == '__main__':
    main()
