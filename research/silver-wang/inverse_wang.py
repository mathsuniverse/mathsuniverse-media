"""Inverse search on the silver Wang tiling: one copy of an unknown polyomino S per Wang tile (tile (i,j) -> anchor (L*i, L*j)),
turned by an orientation (one of the 8 square symmetries) that depends only on the tile's type (solver's choice).
|S| = L*L cells (density). To exclude the trivial answers (shapes that tile by the lattice L*Z^2 alone), S must put two cells
in at least one residue class mod L. Every solution is then checked with the monotile sieve (engine.classify)."""
import sys, math, time
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/claude/mathsuniverse-media/research/monotile-search')
import grids as G, engine as E_
from pysat.solvers import Solver
from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
import silver_wang as SW

g = G.get('square'); OPS = g.op_tabs


def run(L=4, n=18, r=None, limit=20, time_note=True, tiles=None):
    grid = SW.wang_sat(tiles or SW.T2, n, n)
    r = r or L * 0.75 + 1.5
    U = [(i, j, 0) for i in range(-L - 3, L + 4) for j in range(-L - 3, L + 4) if math.hypot(i + .5, j + .5) <= r]
    xu = {u: k + 1 for k, u in enumerate(U)}; pool = IDPool(start_from=len(U) + 1); cl = []
    labels = sorted({grid[i][j] for i in range(n) for j in range(n)})
    y = {(l, o): pool.id(('y', l, o)) for l in labels for o in range(len(OPS))}
    for l in labels:
        lits = [y[(l, o)] for o in range(len(OPS))]; cl.append(lits)
        cl.extend(CardEnc.atmost(lits, 1, vpool=pool, encoding=EncType.pairwise).clauses)
    cl.extend(CardEnc.equals([xu[u] for u in U], L * L, vpool=pool, encoding=EncType.seqcounter).clauses)
    # non-trivial: some residue class mod L holds >= 2 cells
    ors = []
    by = {}
    for u in U: by.setdefault((u[0] % L, u[1] % L), []).append(u)
    for cls in by.values():
        for a in range(len(cls)):
            for b in range(a + 1, len(cls)):
                p = pool.id(('pair', cls[a], cls[b])); ors.append(p)
                cl += [[-p, xu[cls[a]]], [-p, xu[cls[b]]]]
    cl.append(ors)
    img = {(o, u): E_.transform(g, [u], OPS[o])[0] for o in range(len(OPS)) for u in U}
    margin = int(r) + 2
    Z = {(i, j, 0) for i in range(margin, n * L - margin) for j in range(margin, n * L - margin)}
    aux, hit = {}, {}
    for i in range(n):
        for j in range(n):
            l = grid[i][j]; px, py = L * i, L * j
            for o in range(len(OPS)):
                for u in U:
                    a = img[(o, u)]; z = (a[0] + px, a[1] + py, 0)
                    if z not in Z: continue
                    key = (l, o, u)
                    if key not in aux:
                        v = pool.id(('a',) + key); aux[key] = v
                        cl += [[-v, xu[u]], [-v, y[(l, o)]], [v, -xu[u], -y[(l, o)]]]
                    hit.setdefault(z, []).append(aux[key])
    for z in Z:
        lits = sorted(set(hit.get(z, [])))
        cl.append(lits)
        if len(lits) > 1: cl.extend(CardEnc.atmost(lits, 1, vpool=pool, encoding=EncType.seqcounter).clauses)
    sols = []
    with Solver(name='cd15', bootstrap_with=cl) as s:
        while len(sols) < limit and s.solve():
            m = set(l for l in s.get_model() if l > 0)
            S = sorted(u for u in U if xu[u] in m); orient = {l: o for (l, o), v in y.items() if v in m}
            sols.append((S, orient))
            s.add_clause([-xu[u] for u in S])          # next: a different shape
    return sols, dict(L=L, n=n, r=r, unknown=len(U), patch_cells=len(Z), labels=len(labels))


if __name__ == '__main__':
    L = int(sys.argv[1]) if len(sys.argv) > 1 else 4
    t = time.time(); sols, info = run(L=L, n=int(sys.argv[2]) if len(sys.argv) > 2 else 16)
    print(info, 'solutions:', len(sols), round(time.time() - t, 1), 's', flush=True)
    for S, o in sols:
        con = E_.is_connected(g, S)
        cls = E_.classify(g, S, tcap=12, rcap=6)['cls'] if con else '-'
        print('  size', len(S), 'connected', con, 'sieve', cls, 'distinct orientations used', len(set(o.values())), flush=True)
