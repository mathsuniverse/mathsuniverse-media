"""Forced-slope test: how far can the orientation mix of a tiling by one shape vary on a disc?

For a shape S and radius R, all coverings of the disc by copies of S are encoded in SAT (as engine.cover). Copies lying wholly
inside radius R - 2 are the 'inner' copies; F = inner mirror copies, N = all inner copies. With a totalizer on F we find the
minimum and maximum of F over all coverings, and report the mirror share F/N at both extremes.
- A repeating tiler can usually vary its mix widely (any covering is allowed, so the range stays wide as R grows).
- A hat-like tile is forced: the minority-handedness share should close in on one value as R grows (hat: 1/(1 + φ⁴) = 0.1273);
  the whole tiling can be mirrored, so only the minority share (≤ 1/2) is meaningful.
Weak at small R (boundary effects); the trend with R is what matters.

    python3 slope.py kite --cells "[[...]]" --R 4,5,6
"""
from __future__ import annotations

import argparse, json, time
from pysat.card import ITotalizer
from pysat.formula import IDPool
from pysat.solvers import Solver

import engine as E
import grids as G
import fingerprint as FP

PHI = (1 + 5 ** .5) / 2


def build(g, sh, labels, R):
    region = E.disc_cells(g, R)
    pl = E.placements_hitting(sh.forms, region)
    keys = list(pl)
    cov = {}
    for v, key in enumerate(keys, start=1):
        for c in key:
            cov.setdefault(c, []).append(v)
    if any(c not in cov for c in region):
        return None
    pool = IDPool(start_from=len(keys) + 1)
    clauses, rs = [], set(region)
    for c, lits in cov.items():
        if c in rs:
            clauses.append(list(lits))
        E._amo(lits, pool, clauses)
    inner = (R - 2) * g.unit
    inn, mir = [], []
    for v, key in enumerate(keys, start=1):
        if all(x * x + y * y <= inner * inner for x, y in (g.area_centroid_f(c) for c in key)):
            inn.append(v)
            if labels[G.normalise(key)][1] is True:
                mir.append(v)
    return clauses, pool, inn, mir


def extremes(g, sh, labels, R, budget=600):
    b = build(g, sh, labels, R)
    if b is None:
        return None
    clauses, pool, inn, mir = b
    if not mir:
        return dict(R=R, note='no mirror copies possible inside')
    t0 = time.time()
    top = pool.top
    up = ITotalizer(lits=mir, ubound=len(mir), top_id=top)                     # sum(mir) <= k  via  -up.rhs[k]
    neg = ITotalizer(lits=[-x for x in mir], ubound=len(mir), top_id=up.top_id)  # sum(not mir) <= k
    with Solver(name='cd15', bootstrap_with=clauses + up.cnf.clauses + neg.cnf.clauses) as s:
        if not s.solve():
            return dict(R=R, cover=False)
        def share(model):
            pos = set(l for l in model if l > 0)
            F = sum(1 for v in mir if v in pos); N = sum(1 for v in inn if v in pos)
            return F, N
        F, N = share(s.get_model())
        out = {}
        # minimum F
        lo, hi, best = 0, F, (F, N)
        while lo < hi and time.time() - t0 < budget:
            mid = (lo + hi) // 2
            if s.solve(assumptions=[-up.rhs[mid]]):
                best = share(s.get_model()); hi = best[0]
            else:
                lo = mid + 1
        out['min'] = best
        # maximum F: sum(not mir) <= len - k  <=>  F >= k
        L = len(mir); lo, hi, best = F, L, (F, N)
        while lo < hi and time.time() - t0 < budget:
            mid = (lo + hi + 1) // 2
            if s.solve(assumptions=[-neg.rhs[L - mid]] if L - mid < L else []):
                best = share(s.get_model()); lo = best[0]
            else:
                hi = mid - 1
        out['max'] = best
        # most balanced: largest F with F <= half of the inner copies (minority share can be at most 1/2)
        half = max(0, out['min'][1] // 2)
        lo, hi, best = out['min'][0], min(half, L), out['min']
        while lo < hi and time.time() - t0 < budget:
            mid = (lo + hi + 1) // 2
            if s.solve(assumptions=[-up.rhs[hi] if hi < L else 0][:1 if hi < L else 0] + ([-neg.rhs[L - mid]] if L - mid < L else [])):
                best = share(s.get_model()); lo = best[0]
            else:
                hi = mid - 1
        out['bal'] = best
    fmt = lambda fn: round(fn[0] / fn[1], 4) if fn[1] else None
    minority = lambda fn: round(min(fn[0], fn[1] - fn[0]) / fn[1], 4) if fn[1] else None
    lows = [x for x in (minority(out['min']), minority(out['max'])) if x is not None] or [None]
    return dict(R=R, inner_copies=out['min'][1], minority_share_low=min(lows) if lows[0] is not None else None, minority_share_high=minority(out['bal']),
                min_F=out['min'], max_F=out['max'], balanced=out['bal'], seconds=round(time.time() - t0, 1))


def run(grid, cells, Rs, budget=600):
    g = G.get(grid)
    sh, labels = FP.form_labels(g, [tuple(c) for c in cells])
    if all(m is None for _, m in labels.values()):
        return [dict(note='achiral shape: mirror share undefined')]
    res = []
    for R in Rs:
        r = extremes(g, sh, labels, R, budget)
        if r is None:
            res.append(dict(R=R, cover=False)); break
        res.append(r)
        if r.get('cover') is False:
            break
    return res


if __name__ == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument('grid'); ap.add_argument('--cells', required=True); ap.add_argument('--R', default='4,5,6')
    a = ap.parse_args()
    for r in run(a.grid, json.loads(a.cells), [float(x) for x in a.R.split(',')]):
        print(r, flush=True)
