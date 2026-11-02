"""Inverse cut-and-project, control run on the hat.

Given only WHERE each tile sits and HOW it is turned (the point pattern with orientations, as a projection scheme
would give), find the tile: unknown x_u for every grid cell u near the origin ("u is in the shape S"); for each grid
cell z of the patch exactly one placed copy covers it:  sum over placements (k, t) of x_{u : op_k(u) + t = z} = 1.
If the method works, the solver must return the hat from the hat tiling's placements alone.
"""
import sys, math, json, time
sys.path.insert(0, '/home/claude/mathsuniverse-media/research/monotile-search')
import grids as G, engine as E
from pysat.solvers import Solver
from pysat.card import CardEnc, EncType
from pysat.formula import IDPool

g = G.get('kite')
OPS = g.op_tabs


def shift(cells, di, dj):
    return [(i + di, j + dj, t) for i, j, t in cells]


def placements(tiles, C0):
    """(op index, translation) for every tile, so that op(C0) + t = tile."""
    out = []
    S0 = sorted(C0)
    imgs = [sorted(E.transform(g, S0, op)) for op in OPS]
    for cells in tiles:
        cs = sorted(cells); found = None
        for k, Tk in enumerate(imgs):
            if Tk[0][2] != cs[0][2] or sorted(c[2] for c in Tk) != sorted(c[2] for c in cs): continue
            di, dj = cs[0][0] - Tk[0][0], cs[0][1] - Tk[0][1]
            if sorted(shift(Tk, di, dj)) == cs: found = (k, di, dj); break
        assert found, 'tile is not a copy of C0'
        out.append(found)
    return out


def centroid(c):
    x, y = g.area_centroid_f(c); return x, y


def solve(pl, U, Z, limit=50):
    var = {u: n + 1 for n, u in enumerate(U)}
    hit = {}
    for (k, di, dj) in pl:
        for u in U:
            a = E.transform(g, [u], OPS[k])[0]
            z = (a[0] + di, a[1] + dj, a[2])
            if z in Z: hit.setdefault(z, []).append(var[u])
    pool = IDPool(start_from=len(U) + 1); cl = []
    for z in Z:
        lits = sorted(set(hit.get(z, [])))
        if not lits: return [], 'a patch cell no placement can reach'
        cl.append(lits)
        if len(lits) > 1: cl.extend(CardEnc.atmost(lits, 1, vpool=pool, encoding=EncType.seqcounter).clauses)
    sols = []
    with Solver(name='cd15', bootstrap_with=cl) as s:
        while len(sols) < limit and s.solve():
            m = set(l for l in s.get_model() if 0 < l <= len(U))
            S = sorted(u for u in U if var[u] in m); sols.append(S)
            s.add_clause([-var[u] for u in S] + [var[u] for u in U if var[u] not in m])
    return sols, 'ok'


if __name__ == '__main__':
    import hatgrid as H
    hats = [cs for _, cs in H.all_hats()]
    C0 = hats[len(hats) // 2]
    t = time.time(); pl = placements(hats, C0)
    # unknown universe: cells within radius r of C0's centre (in the shape's own frame)
    cx = sum(centroid(c)[0] for c in C0) / 8; cy = sum(centroid(c)[1] for c in C0) / 8
    r = float(sys.argv[1]) if len(sys.argv) > 1 else 6.0
    near = {(i, j, k) for i in range(-30, 31) for j in range(-30, 31) for k in range(6)}
    U = sorted(c for c in near if math.hypot(centroid(c)[0] - cx, centroid(c)[1] - cy) <= r)
    # patch cells well inside the patch
    allc = [c for cs in hats for c in cs]
    px = sum(centroid(c)[0] for c in allc) / len(allc); py = sum(centroid(c)[1] for c in allc) / len(allc)
    Rz = float(sys.argv[2]) if len(sys.argv) > 2 else 25.0
    Z = {c for c in allc if math.hypot(centroid(c)[0] - px, centroid(c)[1] - py) <= Rz}
    print(f'{len(hats)} placements, {len(U)} unknown cells (r={r}), {len(Z)} patch cells (R={Rz})', flush=True)
    sols, msg = solve(pl, U, Z)
    print(msg, 'solutions found:', len(sols), round(time.time() - t, 1), 's')
    for S in sols:
        print('  size', len(S), 'is the hat:', sorted(S) == sorted(C0), 'connected:', E.is_connected(g, S))
