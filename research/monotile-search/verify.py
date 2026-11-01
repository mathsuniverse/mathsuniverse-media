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
    for k, f, L in G.CANDIDATE_L:
        lc = G.lin(L, p0c)
        for d in Qc:
            s = G.psub(G.centre(g.cell_vertices(d)), lc)
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
    but must not overlap).  Returns True / False / None (node limit)."""
    by_cell = {}
    for k, p in enumerate(placements):
        for c in p:
            by_cell.setdefault(c, []).append(k)
    used = set()
    todo = set(region)
    nodes = [0]

    def rec():
        nodes[0] += 1
        if nodes[0] > node_limit:
            return None
        if not todo:
            return True
        best, best_opts = None, None
        for c in todo:
            opts = [k for k in by_cell.get(c, ()) if not (placements[k] & used)]
            if best_opts is None or len(opts) < len(best_opts):
                best, best_opts = c, opts
                if len(opts) <= 1:
                    break
        if not best_opts:
            return False
        for k in best_opts:
            p = placements[k]
            used.update(p)
            removed = [c for c in p if c in todo]
            todo.difference_update(removed)
            r = rec()
            todo.update(removed)
            used.difference_update(p)
            if r is None or r:
                return r
        return False
    return rec(), nodes[0]


def check_stuck(g, cells, R, node_limit=200000):
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
