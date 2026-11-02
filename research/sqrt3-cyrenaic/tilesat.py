"""Step 2 check: do the 36 jigsaw pieces (translations only) behave like an aperiodic set?
- disc: can they cover a disc of radius R? (should be yes: the real Cyrenaic tiling does it)
- torus: is there a periodic tiling with period lattice (a,0),(b,c) of area a*c <= amax? (should be no)
Control: the same 6 parallelograms with straight edges (no bars) tile periodically at once."""
import json, sys, time, math
from pysat.solvers import Solver
from pysat.card import CardEnc, EncType
from pysat.formula import IDPool


def load(plain=False):
    P = json.load(open('pieces.json'))
    shapes = [tuple(tuple(c) for c in p['cells']) for p in P]
    if plain:   # same parallelograms, straight edges: rebuild from the deformed parallelogram of each tile shape
        import jigsaw as J, numpy as np
        from shapely.geometry import Polygon, Point
        out = set()
        for p in P:
            i, j = p['shape']; ei = np.eye(4, dtype=int)[i]; ej = np.eye(4, dtype=int)[j]
            pts = [J.bx(np.zeros(4, int)), J.bx(ei), J.bx(ei + ej), J.bx(ej)]
            Pg = Polygon(pts); xs = [q[0] for q in pts]; ys = [q[1] for q in pts]
            out.add(tuple(sorted((a, b, t) for a in range(min(xs), max(xs)) for b in range(min(ys), max(ys)) for t in range(4)
                                 if Pg.contains(Point(J.cell_centroid((a, b, t)))))))
        shapes = sorted(out)
    return shapes


def exactly_one(lits, pool, cl):
    cl.append(list(lits))
    if len(lits) > 1:
        cl.extend(CardEnc.atmost(lits, 1, vpool=pool, encoding=EncType.seqcounter).clauses)


def disc(shapes, R):
    region = {(i, j, t) for i in range(-R - 1, R + 1) for j in range(-R - 1, R + 1) for t in range(4)
              if (i + .5) ** 2 + (j + .5) ** 2 <= R * R}
    pl = []
    for s in shapes:
        for (a, b, t) in s:
            for (i, j, tt) in region:
                if tt != t: continue
                pl.append(frozenset((x + i - a, y + j - b, k) for x, y, k in s))
    pl = list(set(pl))
    cov = {}
    for v, p in enumerate(pl, 1):
        for c in p: cov.setdefault(c, []).append(v)
    pool = IDPool(start_from=len(pl) + 1); cl = []
    for c, lits in cov.items():
        if c in region: exactly_one(lits, pool, cl)
        elif len(lits) > 1: cl.extend(CardEnc.atmost(lits, 1, vpool=pool, encoding=EncType.seqcounter).clauses)
    with Solver(name='cd15', bootstrap_with=cl) as S:
        return S.solve()


def torus(shapes, a, b, c):
    def red(i, j, t):
        q = j // c; j -= q * c; i -= q * b
        return (i % a, j, t)
    pl = set()
    for s in shapes:
        for u in range(a):
            for v in range(c):
                cs = [red(x + u, y + v, t) for x, y, t in s]
                if len(set(cs)) == len(cs): pl.add(frozenset(cs))
    pl = list(pl)
    cov = {}
    for n, p in enumerate(pl, 1):
        for x in p: cov.setdefault(x, []).append(n)
    if len(cov) < 4 * a * c: return False
    pool = IDPool(start_from=len(pl) + 1); cl = []
    for x, lits in cov.items(): exactly_one(lits, pool, cl)
    with Solver(name='cd15', bootstrap_with=cl) as S:
        return S.solve()


def periodic_search(shapes, amax):
    for area in range(1, amax + 1):
        for a in range(1, area + 1):
            if area % a: continue
            c = area // a
            for b in range(a):
                if torus(shapes, a, b, c): return (a, b, c)
    return None


if __name__ == '__main__':
    amax = int(sys.argv[1]) if len(sys.argv) > 1 else 40
    for plain in (True, False):
        sh = load(plain); t = time.time()
        print('plain parallelograms' if plain else '36 jigsaw pieces', len(sh), 'shapes', flush=True)
        print('  periodic tiling with period area <=', amax, ':', periodic_search(sh, amax), round(time.time() - t, 1), 's', flush=True)
        for R in (6, 9):
            t = time.time(); print('  covers disc R =', R, ':', disc(sh, R), round(time.time() - t, 1), 's', flush=True)
