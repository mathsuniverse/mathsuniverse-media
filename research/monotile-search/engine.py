"""Grid-agnostic polyform enumeration and the three-outcome tiling test.

Works on any grids.Grid.  Cells are integer triples (i, j, t); a polyform is a set of
edge-connected cells; placements are its images under the grid's symmetry group (plus,
on grids where that happens, congruent copies that are not symmetry images, e.g. mirror
images on the chiral floret grid; see congruent_forms).

Tests (all placements on the grid, as in Myers' tables):
  cover(g, P, R)        SAT: can copies exactly cover every cell whose centre lies within
                        R lattice units of the origin, with no overlaps anywhere?
                        UNSAT  => STUCK certificate (P does not tile).
  periodic(g, P, T)     SAT: does P tile a torus R^2 / Lambda, Lambda a sublattice of the
                        grid lattice with <= T tiles per fundamental domain?
                        SAT    => PERIODIC certificate.
  heesch(g, P, kmax)    Kaplan-style Heesch number with hole elimination.
  classify(g, P, caps)  STUCK / PERIODIC / OPEN.
"""
from __future__ import annotations

import math
import time

from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
from pysat.solvers import Solver

import grids as G
from grids import apply_op, normalise

SOLVER = 'cadical153'


# ---------------------------------------------------------------- polyforms

def transform(g, cells, op):
    return [apply_op(op, c) for c in cells]


def canonical(g, cells):
    return min(normalise(transform(g, cells, op)) for op in g.op_tabs)


def sym_forms(g, cells):
    out, seen = [], set()
    for k, op in enumerate(g.op_tabs):
        f = normalise(transform(g, cells, op))
        if f not in seen:
            seen.add(f)
            out.append((f, k))
    return out


def is_connected(g, cells):
    cells = set(cells)
    start = next(iter(cells))
    seen = {start}
    st = [start]
    while st:
        c = st.pop()
        for nb in g.edge_neighbours(c):
            if nb in cells and nb not in seen:
                seen.add(nb)
                st.append(nb)
    return len(seen) == len(cells)


def enumerate_fixed_free(g, nmax, verbose=False, start=None):
    """{n: sorted canonical polyforms} up to the grid symmetry group, n = 1..nmax.
    Growth by one edge-adjacent cell (every polyform of size n arises from one of size n-1
    by connectivity of a spanning tree leaf removal)."""
    if start is None:
        levels = {1: sorted({canonical(g, [(0, 0, t)]) for t in range(g.m)})}
        n0 = 2
    else:
        levels = dict(start)
        n0 = max(levels) + 1
    for n in range(n0, nmax + 1):
        t0 = time.time()
        new = set()
        for p in levels[n - 1]:
            s = set(p)
            tried = set()
            for c in p:
                for nb in g.edge_neighbours(c):
                    if nb in s or nb in tried:
                        continue
                    tried.add(nb)
                    new.add(canonical(g, p + (nb,)))
        levels[n] = sorted(new)
        if verbose:
            print(f'  {g.name} n={n}: {len(levels[n])}  ({time.time() - t0:.1f}s)', flush=True)
    return levels


# ---------------------------------------------------------------- congruent copies off the symmetry group

def _extra_Ls(g):
    """Candidate linear parts (rotation by 30k, optional reflection) that are not linear
    parts of grid symmetries."""
    have = {lab[:2] for lab, _, _ in g.ops}
    return [(k, f, L) for k, f, L in G.CANDIDATE_L if (k, f) not in have]


def congruent_forms(g, cells, exact=True):
    """Fixed forms (normalised) of copies L(P)+s that lie on the grid with L NOT the linear
    part of any grid symmetry.  Search in floats, confirmation exact (vertex sets)."""
    out = set()
    cells = list(cells)
    c0 = cells[0]
    for k, f, L in _extra_Ls(g):
        Lf = ((float(L[0][0]), float(L[0][1])), (float(L[1][0]), float(L[1][1])))
        def Lx(p):
            return (Lf[0][0] * p[0] + Lf[0][1] * p[1], Lf[1][0] * p[0] + Lf[1][1] * p[1])
        imgs = [Lx(g.centroid_f(c)) for c in cells]
        for t2 in range(g.m):
            sx = g.cent_f[t2][0] - imgs[0][0]
            sy = g.cent_f[t2][1] - imgs[0][1]
            found = []
            ok = True
            for (x, y) in imgs:
                cand = None
                for t in range(g.m):
                    u, v = g.lattice_coords_f((x + sx - g.cent_f[t][0], y + sy - g.cent_f[t][1]))
                    i, j = round(u), round(v)
                    if abs(u - i) < 1e-6 and abs(v - j) < 1e-6:
                        cand = (i, j, t)
                        break
                if cand is None:
                    ok = False
                    break
                found.append(cand)
            if not ok:
                continue
            if exact:
                s = G.psub(g.cent[t2], G.lin(L, g.cell_centre(c0)))
                for c, d in zip(cells, found):
                    img = {G.padd(G.lin(L, v), s) for v in g.cell_vertices(c)}
                    if img != set(g.cell_vertices(d)):
                        ok = False
                        break
            if ok:
                out.add(normalise(found))
    return out


def all_forms(g, cells):
    """All fixed forms of grid placements of P: symmetry images, plus symmetry images of
    off-group congruent copies.  Returns list of (form, tag) with tag 'sym' or 'cong'."""
    res = {}
    for f, _ in sym_forms(g, cells):
        res.setdefault(f, 'sym')
    for h in congruent_forms(g, cells):
        for f, _ in sym_forms(g, h):
            res.setdefault(f, 'cong')
    return sorted(res.items())


def free_classes(g, level, verbose=False):
    """Merge symmetry classes into congruence classes.  Returns list of (canonical rep,
    [member canonical forms])."""
    idx = {p: k for k, p in enumerate(level)}
    parent = list(range(len(level)))

    def find(a):
        while parent[a] != a:
            parent[a] = parent[parent[a]]
            a = parent[a]
        return a
    if _extra_Ls(g):
        for k, p in enumerate(level):
            for h in congruent_forms(g, p):
                q = canonical(g, h)
                if q in idx:
                    a, b = find(k), find(idx[q])
                    if a != b:
                        parent[a] = b
    groups = {}
    for k, p in enumerate(level):
        groups.setdefault(find(k), []).append(p)
    return sorted((min(v), sorted(v)) for v in groups.values())


# ---------------------------------------------------------------- SAT helpers

def _amo(lits, pool, clauses):
    if len(lits) <= 1:
        return
    if len(lits) <= 5:
        for a in range(len(lits)):
            for b in range(a + 1, len(lits)):
                clauses.append([-lits[a], -lits[b]])
    else:
        clauses.extend(CardEnc.atmost(lits, 1, vpool=pool, encoding=EncType.seqcounter).clauses)


def _solve(clauses):
    with Solver(name=SOLVER, bootstrap_with=clauses) as s:
        ok = s.solve()
        model = s.get_model() if ok else None
    return ok, model


# ---------------------------------------------------------------- disc cover

_DISC = {}


def disc_cells(g, R):
    key = (g.name, R)
    if key not in _DISC:
        rr = (R * g.unit) ** 2 + 1e-9
        # bound on lattice coordinates
        n = int(R * g.unit * (abs(g.Ainv[0][0]) + abs(g.Ainv[0][1]) + abs(g.Ainv[1][0]) + abs(g.Ainv[1][1]))) + 3
        out = []
        for i in range(-n, n + 1):
            for j in range(-n, n + 1):
                for t in range(g.m):
                    x, y = g.area_centroid_f((i, j, t))
                    if x * x + y * y <= rr:
                        out.append((i, j, t))
        _DISC[key] = out
    return _DISC[key]


def placements_hitting(forms, region):
    by_t = {}
    for c in region:
        by_t.setdefault(c[2], []).append(c)
    pl = {}
    for fi, form in enumerate(forms):
        for (a, b, t) in form:
            for (ri, rj, _) in by_t.get(t, ()):
                ti, tj = ri - a, rj - b
                key = frozenset((x + ti, y + tj, k) for x, y, k in form)
                if key not in pl:
                    pl[key] = (fi, (ti, tj))
    return pl


class Shape:
    """A polyform with its placement forms precomputed."""

    def __init__(self, g, cells):
        self.g = g
        self.cells = tuple(sorted(tuple(c) for c in cells))
        self.n = len(self.cells)
        fs = all_forms(g, self.cells)
        self.forms = [f for f, _ in fs]
        self.n_cong = sum(1 for _, tag in fs if tag == 'cong')


def cover(sh, R, return_patch=False):
    g = sh.g
    region = disc_cells(g, R)
    pl = placements_hitting(sh.forms, region)
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
    if any(c not in cov for c in region):
        ok, model = False, None
    else:
        ok, model = _solve(clauses)
    if not return_patch:
        return ok
    patch = None
    if ok:
        pos = set(l for l in model if l > 0)
        patch = [keys[v - 1] for v in range(1, len(keys) + 1) if v in pos]
    return ok, patch, region


def max_cover_radius(sh, Rs):
    best = None
    for R in Rs:
        if cover(sh, R):
            best = R
        else:
            return best, R
    return best, None


# ---------------------------------------------------------------- torus

def hnf(g1, g2):
    (x1, y1), (x2, y2) = g1, g2
    det = abs(x1 * y2 - x2 * y1)
    assert det > 0

    def egcd(p, q):
        if q == 0:
            return (p, 1, 0) if p >= 0 else (-p, -1, 0)
        gg, s, t = egcd(q, p % q)
        return gg, t, s - (p // q) * t
    c, s, t = egcd(y1, y2)
    bx = s * x1 + t * x2
    a = det // c
    return (a, bx % a, c)


_LAT = {}


def all_lattices(g, max_index):
    """Sublattices of Z^2 (grid lattice coordinates) of index <= max_index in HNF, one per
    class under the linear parts of the grid symmetries."""
    key = (g.name, max_index)
    if key in _LAT:
        return _LAT[key]
    Ms = {M for M, _ in g.op_tabs}
    seen, out = set(), []
    for N in range(1, max_index + 1):
        for a in range(1, N + 1):
            if N % a:
                continue
            c = N // a
            for b in range(a):
                g1, g2 = (a, 0), (b, c)
                imgs = []
                for M in Ms:
                    h1 = (M[0][0] * g1[0] + M[0][1] * g1[1], M[1][0] * g1[0] + M[1][1] * g1[1])
                    h2 = (M[0][0] * g2[0] + M[0][1] * g2[1], M[1][0] * g2[0] + M[1][1] * g2[1])
                    imgs.append(hnf(h1, h2))
                can = min(imgs)
                if can not in seen:
                    seen.add(can)
                    out.append(can)
    _LAT[key] = out
    return out


def _reduce(i, j, lat):
    a, b, c = lat
    q = j // c
    return ((i - q * b) % a, j - q * c)


def torus(sh, lat, return_patch=False):
    g = sh.g
    a, b, c = lat
    n = sh.n
    N = a * c
    if (g.m * N) % n:
        return (False, None) if return_patch else False
    pls = {}
    for fi, form in enumerate(sh.forms):
        for ti in range(a):
            for tj in range(c):
                s = frozenset(_reduce(x + ti, y + tj, lat) + (k,) for x, y, k in form)
                if len(s) < n:
                    continue
                if s not in pls:
                    pls[s] = (fi, (ti, tj))
    keys = list(pls)
    cov = {}
    for v, key in enumerate(keys, start=1):
        for cc in key:
            cov.setdefault(cc, []).append(v)
    if len(cov) < g.m * N:
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
    return True, [pls[keys[v - 1]] for v in range(1, len(keys) + 1) if v in pos]


def periodic(sh, max_tiles, min_tiles=0):
    """First torus (by increasing index) with <= max_tiles tiles per domain that P tiles.
    Tori with <= min_tiles tiles are skipped (already tested in an earlier stage)."""
    g = sh.g
    n = sh.n
    max_index = (max_tiles * n) // g.m
    for lat in all_lattices(g, max_index):
        N = lat[0] * lat[2]
        if (g.m * N) % n:
            continue
        tiles = g.m * N // n
        if tiles <= min_tiles:
            continue
        if torus(sh, lat):
            return lat, tiles
    return None


def periodic_patch(sh, lat, R):
    """Lift a torus tiling to the plane: tiles (frozensets) meeting the disc of radius R."""
    g = sh.g
    ok, sol = torus(sh, lat, return_patch=True)
    assert ok
    a, b, c = lat
    out = []
    reg = set(disc_cells(g, R + 1))
    span = max(abs(x) for cc in reg for x in cc[:2]) + 2 * max(a, c) + 4
    for fi, (ti, tj) in sol:
        form = sh.forms[fi]
        for w in range(-span // c - 2, span // c + 3):
            for u in range(-(span + abs(b) * (abs(w) + 1)) // a - 2, (span + abs(b) * (abs(w) + 1)) // a + 3):
                si, sj = ti + u * a + w * b, tj + w * c
                ks = frozenset((x + si, y + sj, k) for x, y, k in form)
                if ks & reg:
                    out.append(ks)
    return out


# ---------------------------------------------------------------- Heesch

def _holes(g, covered):
    cs = set(covered)
    ii = [c[0] for c in cs]
    jj = [c[1] for c in cs]
    lo_i, hi_i, lo_j, hi_j = min(ii) - 3, max(ii) + 3, min(jj) - 3, max(jj) + 3

    def inbox(c):
        return lo_i <= c[0] <= hi_i and lo_j <= c[1] <= hi_j
    start = (lo_i, lo_j, 0)
    seen = {start}
    st = [start]
    while st:
        x = st.pop()
        for nb in g.edge_neighbours(x):
            if nb in seen or nb in cs or not inbox(nb):
                continue
            seen.add(nb)
            st.append(nb)
    holes = set()
    for i in range(lo_i + 1, hi_i):
        for j in range(lo_j + 1, hi_j):
            for t in range(g.m):
                x = (i, j, t)
                if x not in cs and x not in seen:
                    holes.add(x)
    return holes


def _components(g, cells):
    cells = set(cells)
    comps = []
    while cells:
        s = cells.pop()
        comp = {s}
        st = [s]
        while st:
            x = st.pop()
            for nb in g.edge_neighbours(x):
                if nb in cells:
                    cells.discard(nb)
                    comp.add(nb)
                    st.append(nb)
        comps.append(comp)
    return comps


def _vnbrs(g, cells):
    s = set(cells)
    out = set()
    for c in cells:
        for nb in g.vertex_neighbours(c):
            if nb not in s:
                out.add(nb)
    return out


def coronas(sh, k, max_hole_rounds=400):
    g = sh.g
    forms = sh.forms
    centre = frozenset(forms[0])
    allp = {centre: 0}
    frontier = [centre]
    for lvl in range(1, k + 1):
        nbr = set()
        for p in frontier:
            nbr |= _vnbrs(g, p)
        cand = placements_hitting(forms, list(nbr))
        new = []
        for key in cand:
            if key in allp:
                continue
            allp[key] = lvl
            new.append(key)
        frontier = new
    cset = set(centre)
    usable = [p for p in allp if p != centre and not (p & cset)]
    pool = IDPool()
    X = {}
    for p in usable:
        for lvl in range(allp[p], k + 1):
            X[(p, lvl)] = pool.id(('x', p, lvl))
    clauses = []
    byp = {}
    for (p, lvl), v in X.items():
        byp.setdefault(p, []).append(v)
    for vs in byp.values():
        _amo(vs, pool, clauses)
    cov = {}
    for (p, lvl), v in X.items():
        for c in p:
            cov.setdefault(c, []).append((lvl, v))
    for c, lv in cov.items():
        _amo([v for _, v in lv], pool, clauses)
    Y = {}

    def y(c, L):
        key = (c, L)
        if key not in Y:
            v = pool.id(('y', c, L))
            Y[key] = v
            clauses.append([-v] + [vv for (l2, vv) in cov.get(c, []) if l2 <= L])
        return Y[key]
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
    touch_centre = _vnbrs(g, centre)
    for c in touch_centre:
        clauses.append([y(c, 1)])
    nb_cache = {}
    for (p, lvl), v in X.items():
        if lvl < k:
            if p not in nb_cache:
                nb_cache[p] = _vnbrs(g, p)
            for c in nb_cache[p]:
                if c in cset:
                    continue
                clauses.append([-v, y(c, lvl + 1)])
    for (p, lvl), v in X.items():
        if lvl == 1:
            if not (p & touch_centre):
                clauses.append([-v])
        else:
            if p not in nb_cache:
                nb_cache[p] = _vnbrs(g, p)
            nbs = nb_cache[p]
            lits = [X[(q, lvl - 1)] for q in byp if (q, lvl - 1) in X and (q & nbs)]
            clauses.append([-v] + lits)
    s = Solver(name=SOLVER, bootstrap_with=clauses)
    pushed = len(clauses)
    try:
        for _ in range(max_hole_rounds):
            if not s.solve():
                return False, None
            m = set(l for l in s.get_model() if l > 0)
            used = {p: lvl for (p, lvl), v in X.items() if v in m}
            new_cl = []
            for L in range(1, k + 1):
                union = set(centre)
                tiles_L = [p for p, l in used.items() if l <= L]
                for p in tiles_L:
                    union |= p
                for comp in _components(g, _holes(g, union)):
                    bnd = _vnbrs(g, comp)
                    cl = [-z(p, L) for p in tiles_L if p & bnd]
                    cl += [y(c, L) for c in comp if c in cov]
                    new_cl.append(cl)
            if not new_cl:
                lv = [[centre]] + [[p for p, l in used.items() if l == L] for L in range(1, k + 1)]
                return True, lv
            for c2 in clauses[pushed:]:
                s.add_clause(c2)
            pushed = len(clauses)
            for cl in new_cl:
                s.add_clause(cl)
        raise RuntimeError('hole elimination did not converge')
    finally:
        s.delete()


def heesch(sh, kmax=5, time_budget=None):
    g = sh.g
    centre = frozenset(sh.forms[0])
    if _holes(g, set(centre)):
        return 0, [[centre]], False
    best, best_lv = 0, [[centre]]
    t0 = time.time()
    for k in range(1, kmax + 1):
        ok, lv = coronas(sh, k)
        if not ok:
            return best, best_lv, False
        best, best_lv = k, lv
        if time_budget and time.time() - t0 > time_budget and k < kmax:
            return best, best_lv, True
    return best, best_lv, True


# ---------------------------------------------------------------- classification

RADII = (1.5, 2, 3, 4, 5, 6, 8, 10, 12, 15)


def classify(g, cells, tcap=12, rcap=6, kmax=0, hbudget=60, quick_R=1.5, tmin=0, rmin=None):
    """Three-outcome test.  Returns a record with cls in {'STUCK', 'PERIODIC', 'OPEN'}.
    tmin / rmin: tori with <= tmin tiles and radii <= rmin were already tested (dovetail
    stage), so only the new part of the budget is searched."""
    t0 = time.time()
    sh = Shape(g, cells)
    rec = {'cells': [list(c) for c in sh.cells], 'n': sh.n, 'n_forms': len(sh.forms), 'n_cong_forms': sh.n_cong}
    rs = [r for r in RADII if r <= rcap and (rmin is None or r > rmin)]
    if rcap not in rs and (rmin is None or rcap > rmin):
        rs.append(rcap)
    done = False
    if rmin is None and not cover(sh, quick_R):
        rec.update(cls='STUCK', fail_R=quick_R, max_cover_R=None)
        done = True
    if not done:
        per = periodic(sh, tcap, tmin)
        if per is not None:
            lat, tiles = per
            rec.update(cls='PERIODIC', lattice=list(lat), tiles_per_domain=tiles)
        else:
            best, fail = max_cover_radius(sh, rs)
            if fail is not None:
                rec.update(cls='STUCK', fail_R=fail, max_cover_R=best if best else (rmin or quick_R))
            else:
                rec.update(cls='OPEN', max_cover_R=best if best else rmin)
    if rec['cls'] == 'STUCK' and kmax > 0:
        th = time.time()
        k, _, capped = heesch(sh, kmax, time_budget=hbudget)
        rec.update(heesch=k, heesch_lower_bound_only=capped, heesch_time=round(time.time() - th, 2))
    rec.update(tcap=tcap, rcap=rcap, time=round(time.time() - t0, 3))
    return rec
