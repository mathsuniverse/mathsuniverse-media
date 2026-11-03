"""Independent re-checking of the certificates produced by engine.py.

PERIODIC  the torus tiling is recomputed, every distinct tile in it is checked to be an
          exact congruent copy of the shape (exact Q(sqrt3) vertex geometry, isometry
          search over all 24 candidate linear maps, independent of the symmetry tables),
          and the tiling is unrolled onto the plane and checked to cover a disc exactly
          (no overlaps, no gaps).
STUCK     the uncoverable disc is re-examined by a separate exact-cover backtracking
          search (no SAT) with a node limit; if the limit is hit, a second, independently
          encoded SAT instance (pairwise at-most-one, a different solver) is used instead.
OPEN      no certificate (by definition).
"""
from __future__ import annotations

from pysat.solvers import Solver

import engine as E
import grids as G


def exact_congruent(g, P, Qc):
    """Is there an isometry x -> Lx + s (L among the 24 exact candidates) mapping the cells
    of P onto the cells of Q, vertex set by vertex set?  Exact arithmetic."""
    P = list(P)
    Qs = {frozenset(g.cell_vertices(c)) for c in Qc}
    if len(Qs) != len(P):
        return False
    p0v = g.cell_vertices(P[0])
    p0c = G.centre(p0v)
    qcf = sorted(G.pf(G.centre(g.cell_vertices(d))) for d in Qc)
    pcf = [G.pf(G.centre(g.cell_vertices(c))) for c in P]

    def near(x, y):
        # binary-search-free float membership test (cheap pre-filter only)
        return any(abs(x - a) < 1e-6 and abs(y - b) < 1e-6 for a, b in qcf)
    for k, f, L in g.cands:
        Lf = [[float(L[0][0]), float(L[0][1])], [float(L[1][0]), float(L[1][1])]]
        lc = G.lin(L, p0c)
        lcf = G.pf(lc)
        for d in Qc:
            dc = G.centre(g.cell_vertices(d))
            dcf = G.pf(dc)
            sx, sy = dcf[0] - lcf[0], dcf[1] - lcf[1]
            if not all(near(Lf[0][0] * x + Lf[0][1] * y + sx, Lf[1][0] * x + Lf[1][1] * y + sy) for x, y in pcf):
                continue
            s = G.psub(dc, lc)
            ok = True
            for c in P:
                img = frozenset(G.padd(G.lin(L, v), s) for v in g.cell_vertices(c))
                if img not in Qs:
                    ok = False
                    break
            if ok:
                return True
    return False


def check_periodic(g, cells, lat, R=4):
    sh = E.Shape(g, cells)
    ok, sol = E.torus(sh, tuple(lat), return_patch=True)
    if not ok:
        return False, 'torus no longer solvable'
    # distinct tiles of the fundamental domain are exact congruent copies of P
    for fi, (ti, tj) in sol:
        tile = [(x + ti, y + tj, t) for x, y, t in sh.forms[fi]]
        if not exact_congruent(g, sh.cells, tile):
            return False, 'tile not congruent'
    patch = E.periodic_patch(sh, tuple(lat), R)
    seen = set()
    for ks in patch:
        if seen & ks:
            return False, 'overlap in lifted tiling'
        seen |= ks
    if not set(E.disc_cells(g, R)) <= seen:
        return False, 'gap in lifted tiling'
    return True, f'lifted to disc R={R}, {len(patch)} tiles'


def _backtrack(region, placements, node_limit):
    """Exact cover of `region` (every region cell covered once; placements may stick out
    but must not overlap).  Dancing-links style: live-option counts per region cell are
    kept incrementally; branch on the uncovered cell with fewest live options.
    Returns (True / False / None (node limit), nodes)."""
    placements = [tuple(p) for p in placements]
    by_cell = {}
    for k, p in enumerate(placements):
        for c in p:
            by_cell.setdefault(c, []).append(k)
    todo = set(region)
    cnt = {c: len(by_cell.get(c, ())) for c in todo}
    dead = [0] * len(placements)
    nodes = [0]

    def kill(k):
        if dead[k] == 0:
            for c in placements[k]:
                if c in cnt:
                    cnt[c] -= 1
        dead[k] += 1

    def revive(k):
        dead[k] -= 1
        if dead[k] == 0:
            for c in placements[k]:
                if c in cnt:
                    cnt[c] += 1

    def place(k):
        killed = []
        for c in placements[k]:
            for k2 in by_cell[c]:
                kill(k2)
                killed.append(k2)
        removed = [c for c in placements[k] if c in todo]
        todo.difference_update(removed)
        return killed, removed

    def unplace(killed, removed):
        todo.update(removed)
        for k2 in reversed(killed):
            revive(k2)

    def rec():
        nodes[0] += 1
        if nodes[0] > node_limit:
            return None
        if not todo:
            return True
        best = min(todo, key=cnt.__getitem__)
        if cnt[best] == 0:
            return False
        opts = [k for k in by_cell.get(best, ()) if dead[k] == 0]
        for k in opts:
            killed, removed = place(k)
            r = rec()
            unplace(killed, removed)
            if r is None or r:
                return r
        return False
    import sys
    sys.setrecursionlimit(max(10000, 4 * len(region) + 100))
    return rec(), nodes[0]


def check_stuck(g, cells, R, node_limit=3000):
    sh = E.Shape(g, cells)
    region = E.disc_cells(g, R)
    # independent placement list: translate every form so that each of its cells lands
    # on each region cell of the same type
    pls = set()
    for form in sh.forms:
        for (a, b, t) in form:
            for (ri, rj, rt) in region:
                if rt == t:
                    pls.add(frozenset((x + ri - a, y + rj - b, k) for x, y, k in form))
    pls = list(pls)
    res, nodes = _backtrack(region, pls, node_limit)
    if res is False:
        return True, f'backtracking: no cover ({nodes} nodes)'
    if res is True:
        return False, 'backtracking FOUND a cover'
    # fallback: second SAT encoding (pairwise AMO, glucose4)
    cov = {}
    for v, p in enumerate(pls, start=1):
        for c in p:
            cov.setdefault(c, []).append(v)
    with Solver(name='glucose4') as s:
        for c in region:
            s.add_clause(cov.get(c, []) or [])
        for c, lits in cov.items():
            for i in range(len(lits)):
                for j in range(i + 1, len(lits)):
                    s.add_clause([-lits[i], -lits[j]])
        ok = s.solve()
    if ok:
        return False, 'glucose4 FOUND a cover'
    return True, f'glucose4 pairwise encoding: UNSAT (backtracking hit {node_limit} nodes)'


def check_record(g, rec):
    cells = [tuple(c) for c in rec['cells']]
    if rec['cls'] == 'PERIODIC':
        return check_periodic(g, cells, rec['lattice'])
    if rec['cls'] == 'STUCK':
        return check_stuck(g, cells, rec['fail_R'])
    return True, 'open (no certificate)'
