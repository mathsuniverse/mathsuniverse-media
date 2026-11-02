"""Try label schemes and edge stars for the silver inverse solver."""
import sys, time, itertools
import numpy as np
import silver as S
import engine as E_
from collections import Counter

def nbr_labels(T, depth=1):
    """label = tile type + the types of the tiles across each of its 4 edges (in order)."""
    edge = {}
    for n, ((i, j), v) in enumerate(T):
        w = lambda di, dj: tuple(v[k] + (k == i) * di + (k == j) * dj for k in range(4))
        for e in ((v, i), (w(0, 1), i), (v, j), (w(1, 0), j)):
            edge.setdefault(e, []).append(n)
    lab = [t[0] for t in T]
    for _ in range(depth):
        new = []
        for n, ((i, j), v) in enumerate(T):
            w = lambda di, dj: tuple(v[k] + (k == i) * di + (k == j) * dj for k in range(4))
            sig = []
            for e in ((v, i), (w(0, 1), i), (v, j), (w(1, 0), j)):
                other = [m for m in edge.get(e, []) if m != n]
                sig.append(lab[other[0]] if other else None)
            new.append((lab[n], tuple(sig)))
        lab = new
    return lab

if __name__ == '__main__':
    stars = [tuple(int(x) for x in sys.argv[1:5])] if len(sys.argv) > 4 else [(3, 1, 3, 6)]
    for st in stars:
        a, b, c, d = st
        if 2 * a * c + 4 * b * d != (a + c) * (b + d): print(st, 'density not rational, skip'); continue
        B = S.star(*st)
        if not S.valid(B): print(st, 'invalid'); continue
        V, T, polys = S.build(16, B)
        for name, lab in (('type', None), ('type+neighbours', nbr_labels(T, 1))):
            t0 = time.time()
            sols, msg = S.solve(T, polys, B, r=5.0, Rz=11.0, labels=lab, limit=10)
            print(st, name, msg, '| solutions', len(sols), round(time.time() - t0, 1), 's', flush=True)
            for Ssh, o in sols[:5]:
                print('    size', len(Ssh), 'connected', E_.is_connected(S.g, Ssh), flush=True)
