"""SAT patch builder: decide in one shot whether a free tile admits an edge-to-edge patch covering radius Rad around a seed.

Candidates = every placement that shares an edge with another candidate, starting from the seed, with centre within
Rad + diam (exact Z[zeta_N] coordinates from free2.Search). Clauses:
  seed is placed;
  two candidates that overlap (interior) or share a directed edge are never both placed;
  every placed tile, for each of its edges whose midpoint is within Rad, has a placed neighbour carrying the reverse edge.
UNSAT  -> no such patch exists (a Heesch-type certificate: the tile cannot tile the plane)  = STUCK.
SAT    -> a patch (list of placements) that patch_periods can read recurring translations from.
"""
from __future__ import annotations

import math
import time

import free2 as F2


def candidates(S, Rad):
    R = S.ring
    m = S.tile.m
    lim = Rad + S.diam
    seed = (0, (0, 0, 0, 0))
    idx = {seed: 0}
    pls = [seed]
    vcache = []

    def cen(pl):
        xs = [R.f(x) for x in S.verts(pl)]
        return (sum(p[0] for p in xs) / m, sum(p[1] for p in xs) / m)

    q = 0
    while q < len(pls):
        pl = pls[q]; q += 1
        vs = S.verts(pl)
        for k in range(m):
            a, b = vs[k], vs[(k + 1) % m]
            mx, my = R.f(R.add(a, b))
            if math.hypot(mx, my) / 2 > Rad:
                continue                       # edges outside the radius need no neighbour, so don't expand from them
            for oi, j in S.by_vec.get(R.sub(a, b), ()):
                t = R.sub(b, S.orients[oi][2][j])
                np_ = (oi, t)
                if np_ in idx:
                    continue
                cx, cy = cen(np_)
                if math.hypot(cx, cy) > lim:
                    continue
                if S.overlaps(seed, np_):
                    continue
                idx[np_] = len(pls); pls.append(np_)
    return pls, idx, cen


def build(S, Rad):
    from pysat.formula import CNF
    R = S.ring
    m = S.tile.m
    pls, idx, cen = candidates(S, Rad)
    n = len(pls)
    cs = S.diam
    cells = {}
    cens = [cen(p) for p in pls]
    for i, (cx, cy) in enumerate(cens):
        cells.setdefault((int(cx // cs), int(cy // cs)), []).append(i)
    cnf = CNF()
    cnf.append([1])                            # seed (variable i+1 = placement i)
    # conflicts
    nconf = 0
    for i, (cx, cy) in enumerate(cens):
        gx, gy = int(cx // cs), int(cy // cs)
        for dx in (-1, 0, 1):
            for dy in (-1, 0, 1):
                for j in cells.get((gx + dx, gy + dy), ()):
                    if j > i and S.overlaps(pls[i], pls[j]):
                        cnf.append([-(i + 1), -(j + 1)]); nconf += 1
    # same directed edge used twice is an overlap too (cheap, exact)
    owner = {}
    for i, pl in enumerate(pls):
        vs = S.verts(pl)
        for k in range(m):
            owner.setdefault((vs[k], vs[(k + 1) % m]), []).append(i)
    for e, lst in owner.items():
        for x in range(len(lst)):
            for y in range(x + 1, len(lst)):
                cnf.append([-(lst[x] + 1), -(lst[y] + 1)])
    # every edge inside the radius is matched
    for i, pl in enumerate(pls):
        vs = S.verts(pl)
        for k in range(m):
            a, b = vs[k], vs[(k + 1) % m]
            mx, my = R.f(R.add(a, b))
            if math.hypot(mx, my) / 2 > Rad:
                continue
            nb = owner.get((b, a), [])
            cnf.append([-(i + 1)] + [j + 1 for j in nb])
    return cnf, pls, nconf


def sat_cover(S, Rad, time_limit=None):
    """True (patch in S.patch) / False (no patch: STUCK certificate) / None (solver timed out)."""
    from pysat.solvers import Cadical153
    t0 = time.time()
    cnf, pls, nconf = build(S, Rad)
    S.sat_stats = dict(cands=len(pls), clauses=len(cnf.clauses), conflicts=nconf, build_s=round(time.time() - t0, 1))
    with Cadical153(bootstrap_with=cnf.clauses) as s:
        if time_limit:
            import threading
            timer = threading.Timer(time_limit, s.interrupt); timer.start()
            ok = s.solve_limited(expect_interrupt=True)
            timer.cancel()
        else:
            ok = s.solve()
        if ok is None:
            return None
        if ok:
            model = s.get_model()
            S.patch = [pls[v - 1] for v in model if v > 0 and v <= len(pls)]
    S.sat_stats['solve_s'] = round(time.time() - t0, 1)
    return bool(ok)


def classify_sat(seq, N, lens=None, mirror=True, Rs=(2, 3, 4, 5, 6), time_limit=1800, tiles=48):
    S = F2.Search(seq, N, mirror, lens)
    t0 = time.time()
    hist = []
    for Rr in Rs:
        r = sat_cover(S, Rr * S.diam / 2, time_limit)
        hist.append((Rr, r, S.sat_stats))
        if r is None:
            return dict(cls='UNDECIDED', at_R=Rr, hist=hist, seconds=round(time.time() - t0))
        if not r:
            return dict(cls='STUCK', fail_R=Rr, hist=hist, seconds=round(time.time() - t0))
    res, n = F2.patch_periods(S, max_tiles=tiles, patch=S.patch, budget=time_limit)
    cls = 'PERIODIC' if res else ('OPEN' if res is False else 'UNDECIDED')
    out = dict(cls=cls, hist=hist, tested=n, seconds=round(time.time() - t0))
    if res:
        out.update(res)
    return out
