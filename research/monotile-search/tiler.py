"""SAT-based tiling tests for polykites on the kite grid.

All tests place copies of a polykite *on the kite grid* in any of the 12 orientations
(6 rotations x optional reflection) and any lattice translation.  Off-grid placements
are never considered.

  cover(cells, R)             can copies exactly cover every kite whose centroid is within
                              distance R (in hexagon spacings) of a hexagon centre, with no
                              two copies overlapping anywhere?
  periodic(cells, max_tiles)  does it tile some torus R^2 / Lambda, where Lambda is a
                              sublattice of the hexagon-centre lattice with at most
                              `max_tiles` copies in a fundamental domain?  A torus tiling
                              lifts to a periodic tiling of the plane.
  heesch(cells, kmax)         Heesch number (max number of coronas), Kaplan-style SAT with
                              iterative hole elimination.  Only meaningful for non-tilers.
"""
from __future__ import annotations

import math
import time
from math import gcd

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Solver

import polykite as P

H = 2 * P.R3          # hexagon spacing in raw units
SOLVER = 'cadical153'


# ---------------------------------------------------------------- orientations

def oriented_forms(cells):
    """[(form, reflected_flag, op)] for each distinct orientation of the polykite."""
    out, seen = [], set()
    for op in P.OPS:
        f = P.normalise(P.transform(cells, op))
        if f not in seen:
            seen.add(f)
            out.append((f, op[1], op))
    return out


def _amo(lits, pool, clauses):
    if len(lits) <= 1:
        return
    if len(lits) <= 5:
        for a in range(len(lits)):
            for b in range(a + 1, len(lits)):
                clauses.append([-lits[a], -lits[b]])
    else:
        clauses.extend(CardEnc.atmost(lits, 1, vpool=pool, encoding=EncType.seqcounter).clauses)


def _solve(clauses, assumptions=(), time_limit=None):
    with Solver(name=SOLVER, bootstrap_with=clauses) as s:
        ok = s.solve(assumptions=list(assumptions))
        model = s.get_model() if ok else None
    return ok, model


# ---------------------------------------------------------------- (a) disc cover

_centroid_cache = {}


def centroid(kite):
    k = kite[2]
    if k not in _centroid_cache:
        _centroid_cache[k] = P.kite_centroid_xy((0, 0, k))
    cx, cy = P.e_xy(P.centre_point(kite[0], kite[1]))
    dx, dy = _centroid_cache[k]
    return (cx + dx, cy + dy)


def disc_kites(R):
    """All kites whose centroid is within R hexagon spacings of the origin."""
    out = []
    rr = R * H
    n = int(R * 1.5) + 2
    for i in range(-2 * n, 2 * n + 1):
        for j in range(-2 * n, 2 * n + 1):
            for k in range(6):
                x, y = centroid((i, j, k))
                if x * x + y * y <= rr * rr + 1e-9:
                    out.append((i, j, k))
    return out


def placements_hitting(forms, region):
    """All placements (form index, translation) covering at least one region kite."""
    by_k = {}
    for c in region:
        by_k.setdefault(c[2], []).append(c)
    pl = {}
    for fi, (form, refl, op) in enumerate(forms):
        for (fi_, fj_, fk) in form:
            for (ri, rj, rk) in by_k.get(fk, ()):
                t = (ri - fi_, rj - fj_)
                key = frozenset((a + t[0], b + t[1], k) for a, b, k in form)
                if key not in pl:
                    pl[key] = (fi, t)
    return pl


def cover(cells, R, return_patch=False):
    forms = oriented_forms(cells)
    region = disc_kites(R)
    pl = placements_hitting(forms, region)
    keys = list(pl)
    cov = {}
    for v, key in enumerate(keys, start=1):
        for c in key:
            cov.setdefault(c, []).append(v)
    pool = IDPool(start_from=len(keys) + 1)
    clauses = []
    rs = set(region)
    for c, lits in cov.items():
        if c in rs:
            clauses.append(list(lits))
        _amo(lits, pool, clauses)
    ok, model = _solve(clauses)
    if not return_patch:
        return ok
    patch = None
    if ok:
        pos = set(l for l in model if l > 0)
        patch = [(keys[v - 1], forms[pl[keys[v - 1]][0]][1]) for v in range(1, len(keys) + 1) if v in pos]
    return ok, patch, region


def max_cover_radius(cells, Rs):
    """Largest R in the increasing list Rs that can be covered (stops at first failure).
    Returns (best_R or None, first_failed_R or None)."""
    best = None
    for R in Rs:
        if cover(cells, R):
            best = R
        else:
            return best, R
    return best, None


# ---------------------------------------------------------------- (b) torus / periodic

def hnf(g1, g2):
    """Hermite normal form (a, b, c) of the lattice spanned by integer vectors g1, g2:
    basis (a, 0), (b, c) with a, c > 0 and 0 <= b < a."""
    (x1, y1), (x2, y2) = g1, g2
    det = abs(x1 * y2 - x2 * y1)
    assert det > 0
    # extended gcd on the y-components
    def egcd(p, q):
        if q == 0:
            return (p, 1, 0) if p >= 0 else (-p, -1, 0)
        g, s, t = egcd(q, p % q)
        return g, t, s - (p // q) * t
    c, s, t = egcd(y1, y2)
    bx = s * x1 + t * x2
    a = det // c
    return (a, bx % a, c)


def all_lattices(max_index):
    """All sublattices of Z^2 of index <= max_index, as HNF (a, b, c), one per
    equivalence class under the 12 symmetries of the hex lattice."""
    seen = set()
    out = []
    for N in range(1, max_index + 1):
        for a in range(1, N + 1):
            if N % a:
                continue
            c = N // a
            for b in range(a):
                lat = (a, b, c)
                g1, g2 = (a, 0), (b, c)
                imgs = []
                for r, f in P.OPS:
                    h1, h2 = g1, g2
                    if f:
                        h1, h2 = P.conj_centre(h1), P.conj_centre(h2)
                    h1, h2 = P.rot_centre(h1, r), P.rot_centre(h2, r)
                    imgs.append(hnf(h1, h2))
                can = min(imgs)
                if can not in seen:
                    seen.add(can)
                    out.append(can)
    return out


def _reduce(i, j, lat):
    a, b, c = lat
    q = j // c
    return ((i - q * b) % a, j - q * c)


def torus(cells, lat, return_patch=False):
    """Exact cover of the torus Z^2/lat x {6 kites} by copies of the polykite."""
    a, b, c = lat
    n = len(cells)
    N = a * c
    if (6 * N) % n:
        return (False, None) if return_patch else False
    forms = oriented_forms(cells)
    pls = {}
    for fi, (form, refl, op) in enumerate(forms):
        for ti in range(a):
            for tj in range(c):
                img = []
                for (x, y, k) in form:
                    rx, ry = _reduce(x + ti, y + tj, lat)
                    img.append((rx, ry, k))
                s = frozenset(img)
                if len(s) < n:
                    continue          # copy overlaps its own translate
                if s not in pls:
                    pls[s] = (fi, (ti, tj))
    keys = list(pls)
    cov = {}
    for v, key in enumerate(keys, start=1):
        for cc in key:
            cov.setdefault(cc, []).append(v)
    if len(cov) < 6 * N:
        return (False, None) if return_patch else False
    pool = IDPool(start_from=len(keys) + 1)
    clauses = []
    for cc, lits in cov.items():
        clauses.append(list(lits))
        _amo(lits, pool, clauses)
    ok, model = _solve(clauses)
    if not return_patch:
        return ok
    if not ok:
        return False, None
    pos = set(l for l in model if l > 0)
    sol = [(pls[keys[v - 1]], keys[v - 1]) for v in range(1, len(keys) + 1) if v in pos]
    return True, sol


_LATTICES = {}


def periodic(cells, max_tiles):
    """Search tori whose fundamental domain holds at most max_tiles copies.
    Returns (lattice, tiles_per_domain) for the first success (smallest index), else None."""
    n = len(cells)
    max_index = (max_tiles * n) // 6
    if max_index not in _LATTICES:
        _LATTICES[max_index] = all_lattices(max_index)
    for lat in _LATTICES[max_index]:
        N = lat[0] * lat[2]
        if (6 * N) % n:
            continue
        if torus(cells, lat):
            return lat, 6 * N // n
    return None


def periodic_patch(cells, lat, R):
    """Lift a torus tiling to the plane: list of (kite set, reflected) covering disc R."""
    ok, sol = torus(cells, lat, return_patch=True)
    assert ok
    forms = oriented_forms(cells)
    a, b, c = lat
    out = []
    span = int(R * 1.5) + 3
    for (fi, (ti, tj)), _ in sol:
        form, refl, op = forms[fi]
        for u in range(-2 * span // a - 3, 2 * span // a + 4):
            for w in range(-2 * span // c - 3, 2 * span // c + 4):
                si, sj = ti + u * a + w * b, tj + w * c
                ks = [(x + si, y + sj, k) for x, y, k in form]
                if any(math.hypot(*centroid(kk)) <= (R + 0.8) * H for kk in ks):
                    out.append((frozenset(ks), refl))
    return out


# ---------------------------------------------------------------- (c) Heesch number

def _holes(covered):
    """Kites not in `covered` that are enclosed by it (flood fill from outside through
    edge-adjacent uncovered kites)."""
    cs = set(covered)
    ii = [c[0] for c in cs]
    jj = [c[1] for c in cs]
    lo_i, hi_i, lo_j, hi_j = min(ii) - 2, max(ii) + 2, min(jj) - 2, max(jj) + 2

    def inbox(c):
        return lo_i <= c[0] <= hi_i and lo_j <= c[1] <= hi_j
    start = (lo_i, lo_j, 0)
    seen = {start}
    stack = [start]
    while stack:
        x = stack.pop()
        for nb in P.edge_neighbours(x):
            if nb in seen or nb in cs or not inbox(nb):
                continue
            seen.add(nb)
            stack.append(nb)
    holes = set()
    for i in range(lo_i, hi_i + 1):
        for j in range(lo_j, hi_j + 1):
            for k in range(6):
                x = (i, j, k)
                if x not in cs and x not in seen:
                    holes.add(x)
    return holes


def _components(cells):
    cells = set(cells)
    comps = []
    while cells:
        s = cells.pop()
        comp = {s}
        st = [s]
        while st:
            x = st.pop()
            for nb in P.edge_neighbours(x):
                if nb in cells:
                    cells.discard(nb)
                    comp.add(nb)
                    st.append(nb)
        comps.append(comp)
    return comps


def _vnbrs(kites):
    s = set(kites)
    out = set()
    for c in kites:
        for nb in P.vertex_neighbours(c):
            if nb not in s:
                out.add(nb)
    return out


def coronas(cells, k, max_hole_rounds=400):
    """Try to surround the polykite with k coronas.  Returns (True, levels) where
    levels is a list of lists of kite-sets (level 0 = central tile), or (False, None).
    Raises RuntimeError if hole elimination does not converge."""
    forms = oriented_forms(cells)
    centre = frozenset(forms[0][0])
    # tile "diameter" in raw units
    pts = [centroid(c) for c in centre]
    cx = sum(p[0] for p in pts) / len(pts)
    cy = sum(p[1] for p in pts) / len(pts)
    rad = max(math.hypot(p[0] - cx, p[1] - cy) for p in pts) + 2.1   # + kite size
    D = 2 * rad
    # candidate placements per level: grow outward by touching
    levels_pl = [[centre]]
    allp = {centre: 0}         # placement -> first level it can appear in
    frontier = [centre]
    for lvl in range(1, k + 1):
        nbr = set()
        for p in frontier:
            nbr |= _vnbrs(p)
        region = list(nbr)
        cand = placements_hitting(forms, region)
        new = []
        for key in cand:
            if key in allp:
                continue
            allp[key] = lvl
            new.append(key)
        # placements already present at earlier levels may also be used at this level
        levels_pl.append(new)
        frontier = new
    # filter: anything overlapping the centre is unusable
    cset = set(centre)
    usable = [p for p in allp if p != centre and not (p & cset)]
    pool = IDPool()
    X = {}
    for p in usable:
        for lvl in range(allp[p], k + 1):
            X[(p, lvl)] = pool.id(('x', p, lvl))
    clauses = []
    # each placement at most one level
    byp = {}
    for (p, lvl), v in X.items():
        byp.setdefault(p, []).append(v)
    for vs in byp.values():
        _amo(vs, pool, clauses)
    # each kite at most one tile
    cov = {}
    for (p, lvl), v in X.items():
        for c in p:
            cov.setdefault(c, []).append((lvl, v))
    for c, lv in cov.items():
        _amo([v for _, v in lv], pool, clauses)
    # y(c, L): kite c covered by some tile of level <= L (only the -> direction)
    Y = {}

    def y(c, L):
        key = (c, L)
        if key not in Y:
            v = pool.id(('y', c, L))
            Y[key] = v
            lits = [vv for (l2, vv) in cov.get(c, []) if l2 <= L]
            clauses.append([-v] + lits)
        return Y[key]
    # z(p, L): placement p used at level <= L (only x -> z direction needed)
    Z = {}

    def z(p, L):
        key = (p, L)
        if key not in Z:
            v = pool.id(('z', p, L))
            Z[key] = v
            for lvl in range(allp[p], L + 1):
                if (p, lvl) in X:
                    clauses.append([-X[(p, lvl)], v])
        return Z[key]
    # surround: cells next to the centre covered at level 1
    for c in _vnbrs(centre):
        clauses.append([y(c, 1)])
    # cells next to a level-l tile covered at level <= l+1  (l = 1..k-1)
    nb_cache = {}
    for (p, lvl), v in X.items():
        if lvl < k:
            if p not in nb_cache:
                nb_cache[p] = _vnbrs(p)
            for c in nb_cache[p]:
                if c in cset:
                    continue
                clauses.append([-v, y(c, lvl + 1)])
    # level-l tile (l >= 2) must touch a level l-1 tile; level-1 tiles must touch centre
    touch_centre = _vnbrs(centre)
    for (p, lvl), v in X.items():
        if lvl == 1:
            if not (p & touch_centre):
                clauses.append([-v])
        else:
            if p not in nb_cache:
                nb_cache[p] = _vnbrs(p)
            nbs = nb_cache[p]
            lits = []
            for q in byp:
                if (q, lvl - 1) in X and (q & nbs):
                    lits.append(X[(q, lvl - 1)])
            clauses.append([-v] + lits)
    s = Solver(name=SOLVER, bootstrap_with=clauses)
    pushed = len(clauses)        # y/z definitions created later are appended to `clauses`
    try:
        for _ in range(max_hole_rounds):
            if not s.solve():
                return False, None
            m = set(l for l in s.get_model() if l > 0)
            used = {}
            for (p, lvl), v in X.items():
                if v in m:
                    used[p] = lvl
            new_cl = []
            for L in range(1, k + 1):
                union = set(centre)
                tiles_L = [p for p, l in used.items() if l <= L]
                for p in tiles_L:
                    union |= p
                for comp in _components(_holes(union)):
                    # forbid: all boundary tiles present at level <= L while no tile of
                    # level <= L covers any kite of the hole
                    bnd = _vnbrs(comp)
                    cl = [-z(p, L) for p in tiles_L if p & bnd]
                    cl += [y(c, L) for c in comp if c in cov]
                    new_cl.append(cl)
            if not new_cl:
                lv = [[centre]] + [[p for p, l in used.items() if l == L] for L in range(1, k + 1)]
                verify_coronas(lv)
                return True, lv
            for c2 in clauses[pushed:]:
                s.add_clause(c2)
            pushed = len(clauses)
            for cl in new_cl:
                s.add_clause(cl)
        raise RuntimeError("hole elimination did not converge")
    finally:
        s.delete()


def verify_coronas(levels):
    """Independent check of a corona structure (raises AssertionError): no overlaps;
    for every L >= 1 the union of levels <= L has no holes and contains every kite that
    touches (edge or vertex) the union of levels <= L-1; each tile of level L >= 1
    touches a tile of level L-1."""
    seen = set()
    for lv in levels:
        for p in lv:
            assert not (seen & p), 'overlap'
            seen |= p
    union = set()
    for L, lv in enumerate(levels):
        prev = set(union)
        for p in lv:
            union |= p
        if L >= 1:
            assert not _holes(union), f'hole at level {L}'
            assert _vnbrs(prev) <= union, f'level {L} does not surround'
            prev_tiles = levels[L - 1]
            for p in lv:
                nb = _vnbrs(p)
                assert any(q & nb for q in prev_tiles), f'level {L} tile detached'


def heesch(cells, kmax=6, time_budget=None):
    """Heesch number: largest k <= kmax for which k coronas exist.  Returns (k, levels,
    capped) where capped=True means the search stopped at kmax (or the time budget) while
    still succeeding, so the true value is >= k.  A polykite with a hole has Heesch
    number 0 by convention."""
    centre = frozenset(oriented_forms(cells)[0][0])
    if _holes(set(centre)):
        return 0, [[centre]], False
    best, best_lv = 0, [[centre]]
    t0 = time.time()
    for k in range(1, kmax + 1):
        ok, lv = coronas(cells, k)
        if not ok:
            return best, best_lv, False
        best, best_lv = k, lv
        if time_budget and time.time() - t0 > time_budget and k < kmax:
            return best, best_lv, True
    return best, best_lv, True
