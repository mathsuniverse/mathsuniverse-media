"""Loosened inverse search on any Wang tile set (the three ideas):
 1. k copies of the unknown polyomino S per Wang tile (|S| = L*L / k cells);
 2. each copy's anchor offset inside the tile square is free (solver picks it), so copies can straddle tile boundaries;
 3. the label that decides (orientation, offset) can be the tile type or the tile type + its 4 neighbours.
For every (label, copy) the solver picks one orientation (8 square symmetries) and one offset (L*L choices).
Every cell of the patch is covered exactly once. Solutions are de-duplicated up to translation and sieved afterwards."""
import sys, math, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, '/home/claude/mathsuniverse-media/research/monotile-search')
import grids as G, engine as E_
from pysat.solvers import Solver
from pysat.card import CardEnc, EncType
from pysat.formula import IDPool
import silver_wang as SW

g = G.get('square'); OPS = g.op_tabs


def nbr_labels(grid):
    n = len(grid); lab = {}
    for i in range(n):
        for j in range(n):
            nb = tuple(grid[i + di][j + dj] if 0 <= i + di < n and 0 <= j + dj < n else None
                       for di, dj in ((1, 0), (0, 1), (-1, 0), (0, -1)))
            lab[(i, j)] = (grid[i][j], nb)
    return lab


def run(tiles, L=4, k=1, n=14, r=None, labels='type', limit=10, sieve=True, time_limit=None, cegar=False, tcap=16):
    assert (L * L) % k == 0
    size = L * L // k
    grid = SW.wang_sat(tiles, n, n)
    lab = {(i, j): grid[i][j] for i in range(n) for j in range(n)} if labels == 'type' else nbr_labels(grid)
    r = r or math.sqrt(size) * 0.9 + 1.0
    U = [(i, j, 0) for i in range(-int(r) - 2, int(r) + 3) for j in range(-int(r) - 2, int(r) + 3) if math.hypot(i + .5, j + .5) <= r]
    xu = {u: t + 1 for t, u in enumerate(U)}; pool = IDPool(start_from=len(U) + 1); cl = []
    cl.extend(CardEnc.equals([xu[u] for u in U], size, vpool=pool, encoding=EncType.seqcounter).clauses)
    L_ = sorted(set(lab.values()), key=str)
    offs = [(a, b) for a in range(L) for b in range(L)]
    y = {}
    for l in L_:
        for c in range(k):
            lits = []
            for o in range(len(OPS)):
                for d in offs:
                    v = pool.id(('y', str(l), c, o, d)); y[(l, c, o, d)] = v; lits.append(v)
            cl.append(lits); cl.extend(CardEnc.atmost(lits, 1, vpool=pool, encoding=EncType.seqcounter).clauses)
    # symmetry breaking between copies of the same label: copy c uses an offset index <= copy c+1's (weak, keeps solutions)
    img = {(o, u): E_.transform(g, [u], OPS[o])[0] for o in range(len(OPS)) for u in U}
    margin = int(r) + L + 2
    Z = {(i, j, 0) for i in range(margin, n * L - margin) for j in range(margin, n * L - margin)}
    aux, hit = {}, {}
    for (i, j), l in lab.items():
        for c in range(k):
            for o in range(len(OPS)):
                for d in offs:
                    yv = y[(l, c, o, d)]
                    for u in U:
                        a = img[(o, u)]; z = (a[0] + L * i + d[0], a[1] + L * j + d[1], 0)
                        if z not in Z: continue
                        key = (str(l), c, o, d, u)
                        if key not in aux:
                            v = pool.id(('a',) + key); aux[key] = v
                            cl += [[-v, xu[u]], [-v, yv], [v, -xu[u], -yv]]
                        hit.setdefault(z, []).append(aux[key])
    for z in Z:
        lits = sorted(set(hit.get(z, [])))
        if not lits: return [], dict(error='unreachable cell')
        cl.append(lits)
        if len(lits) > 1: cl.extend(CardEnc.atmost(lits, 1, vpool=pool, encoding=EncType.seqcounter).clauses)
    sols = []; Uset = set(U); stats = dict(cuts=0, periodic=0, stuck=0, open=0)
    def nb(c):
        i, j, _ = c; return [(i + 1, j, 0), (i - 1, j, 0), (i, j + 1, 0), (i, j - 1, 0)]
    def block(S):
        for di in range(-2 * L, 2 * L + 1):            # block S and all its translates inside U
            for dj in range(-2 * L, 2 * L + 1):
                Tt = [(a + di, b + dj, 0) for a, b, _ in S]
                if all(t in Uset for t in Tt): s.add_clause([-xu[t] for t in Tt])
    def cut_periodic(solver, S, sh, lat):
        # every shape that tiles this same torus in this same arrangement is excluded (not only S itself)
        ok, sol = E_.torus(sh, lat, return_patch=True)
        a_, b_, c_ = lat
        maps = []
        for fi, (ti, tj) in sol:
            for o in range(len(OPS)):
                TS = E_.transform(g, S, OPS[o])
                if G.normalise(TS) == sh.forms[fi]:
                    mi = min(c[0] for c in TS); mj = min(c[1] for c in TS); maps.append((o, ti - mi, tj - mj)); break
        lits = {}
        for o, dx, dy in maps:
            for u in U:
                a = img_all[(o, u)]
                z = E_._reduce(a[0] + dx, a[1] + dy, lat)
                lits.setdefault(z, []).append(xu[u])
        cells = {(i, j) for i in range(a_) for j in range(c_)}
        big = []
        for z in cells:
            lz = lits.get(z, [])
            if not lz: return                      # some cell can never be covered: no shape tiles this arrangement
            nz = pool.id(('n', len(stats_cuts), z)); big.append(nz)
            for l in set(lz): solver.add_clause([-nz, -l])
            tz = pool.id(('t', len(stats_cuts), z)); big.append(tz); ors = []
            cnt = {}
            for l in lz: cnt[l] = cnt.get(l, 0) + 1
            for l, m_ in cnt.items():
                if m_ >= 2:
                    ors.append(l)
            ul = sorted(cnt)
            for i1 in range(len(ul)):
                for i2 in range(i1 + 1, len(ul)):
                    q = pool.id(('q', len(stats_cuts), z, ul[i1], ul[i2])); ors.append(q)
                    solver.add_clause([-q, ul[i1]]); solver.add_clause([-q, ul[i2]])
            solver.add_clause([-tz] + ors)
        solver.add_clause(big); stats_cuts.append(lat)
    stats_cuts = []
    img_all = {(o, u): E_.transform(g, [u], OPS[o])[0] for o in range(len(OPS)) for u in U}
    import time as _t
    t_end = _t.time() + (time_limit or 1e9)
    with Solver(name='cd15', bootstrap_with=cl) as s:
        while len(sols) < limit and _t.time() < t_end and s.solve():
            m = set(v for v in s.get_model() if v > 0)
            S = sorted(u for u in U if xu[u] in m)
            # lazy connectivity: cut off a component that is not attached to the rest
            comp, todo, Ss = {S[0]}, [S[0]], set(S)
            while todo:
                c = todo.pop()
                for d in nb(c):
                    if d in Ss and d not in comp: comp.add(d); todo.append(d)
            if len(comp) < len(S):
                bound = {d for c in comp for d in nb(c) if d not in comp and d in Uset}
                s.add_clause([-xu[c] for c in comp] + [xu[b] for b in bound]); stats['cuts'] += 1; continue
            if not sieve:
                sols.append(S); block(S); continue
            if cegar:
                sh = E_.Shape(g, S); per = E_.periodic(sh, tcap)
                if per:
                    stats['periodic'] += 1; cut_periodic(s, S, sh, per[0]); block(S); continue
            r_ = E_.classify(g, S, tcap=tcap, rcap=8)
            stats[r_['cls'].lower()] += 1
            if r_['cls'] == 'OPEN': sols.append(S)
            block(S)
    return sols, dict(L=L, k=k, size=size, labels=labels, n_labels=len(L_), unknown=len(U), patch=len(Z), aux=len(aux), periodic_cuts=len(stats_cuts), **stats)


if __name__ == '__main__':
    import kari as K, time
    T = K.tiles_for(K.KARI)
    for L, k in ((3, 1), (4, 2)):
        t = time.time(); sols, info = run(T, L=L, k=k, n=12, limit=3, time_limit=240, cegar=True)
        print(info, 'solutions', len(sols), round(time.time() - t, 1), 's', flush=True)
        for S in sols:
            con = E_.is_connected(g, S)
            print('   size', len(S), 'connected', con, 'sieve', E_.classify(g, S, tcap=12, rcap=6)['cls'] if con else '-', flush=True)
