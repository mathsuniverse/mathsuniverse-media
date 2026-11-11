"""Lattice quads that tile exactly under a gluing rule (THEORY s14).
The Spectre's own quad (the keypoints P3,P5,P7,P11 of the tile) satisfies: the level-1 and level-2 clusters of
quads overlap with total/union = 1 exactly. This is lens-free, so we can screen rules by it:
  sides from S = all vectors reachable in <= LMAX unit steps (12 directions),
  the rule's coincidence relations solved for one quad point,
  level-1 X cluster exact (total/union <= 1+1e-4), then level 2 for each Mystic/empty slot pair (m, e).
Output: per rule and (m, e), the quads that pass, with the minimal arc lengths of each side."""
import numpy as np, itertools, sys, json, time, math
from shapely.geometry import Polygon
from shapely.ops import unary_union
import fractile as F, polysearch as PS, polysearch2 as P2
from relations import relations
from spectre_exact import cx

LMAX = 6
_S = None
def pooled():
    global _S
    if _S is None:
        S = {}
        for l in range(1, LMAX + 1):
            for v in PS.reach(l):
                S.setdefault(v, l)          # minimal number of unit steps
        _S = S
    return _S

def exact(tiles, qc, tol=1e-4):
    P = [Polygon([(z.real, z.imag) for z in (F.ap(t, w) for w in qc)]) for t in tiles]
    if not all(p.is_valid for p in P): return False
    tot = sum(p.area for p in P); uni = unary_union(P).area
    return uni > 0 and tot / uni <= 1 + tol

def level1X(steps, sq, refl, qc):
    trs, _ = F.supermap(steps, sq, refl, qc)
    return trs

def candidates(steps, sq, refl):
    """lattice quads (Q0 = 0) with sides in S satisfying the relations"""
    S = pooled(); V = np.array(list(S.keys()), dtype=np.int64); Sset = set(S.keys())
    pairs, A = relations(steps, sq, refl, 0, 1)
    if A is None: return None, 'no relations'
    A = np.array(A.tolist(), dtype=np.int64)
    blocks = [A[:, 4 * j:4 * j + 4] for j in range(4)]       # Q0..Q3
    # pick a point among Q1..Q3 whose block has rank 4 to solve for
    rk = [np.linalg.matrix_rank(blocks[j]) for j in range(4)]
    if np.linalg.matrix_rank(A[:, 4:]) < 4: return None, 'rank<4'
    piv = next((j for j in (2, 1, 3) if rk[j] == 4), None)
    if piv is None: return None, 'no pivot'
    others = [j for j in (1, 2, 3) if j != piv]
    # rows: take 4 independent rows for the pivot block
    rows = []
    for i in range(A.shape[0]):
        if np.linalg.matrix_rank(blocks[piv][rows + [i]]) > len(rows): rows.append(i)
        if len(rows) == 4: break
    Bp = blocks[piv][rows].astype(float); Binv = np.linalg.inv(Bp)
    # points: Q1 = e1 (from S), Q3 = -e4 (from S), Q2 = e1+e2; free points are the two 'others'
    def pts_from(j):
        if j == 1: return V                      # Q1 = e1
        if j == 3: return -V                     # Q3 = -e4
        return None
    out = []
    if piv == 2:
        X1, X3 = V, -V
        for i1 in range(len(X1)):
            q1 = X1[i1]
            rhs = -(blocks[1][rows] @ q1)[None, :] - (blocks[3][rows] @ X3.T).T
            q2 = rhs @ Binv.T
            r = np.rint(q2)
            ok = np.abs(q2 - r).max(1) < 1e-6
            for i3 in np.nonzero(ok)[0]:
                Q2 = tuple(int(x) for x in r[i3]); Q3 = tuple(int(x) for x in X3[i3]); Q1 = tuple(int(x) for x in q1)
                e2 = PS.sub(Q2, Q1); e3 = PS.sub(Q3, Q2)
                if e2 not in Sset or e3 not in Sset: continue
                Q = [(0, 0, 0, 0), Q1, Q2, Q3]
                if (A @ np.concatenate(Q)).any(): continue
                out.append(Q)
    else:
        # solve for Q1 or Q3 given the other free point and Q2 = e1 + e2 ... enumerate Q2 over S+S is large;
        # instead enumerate the two free points directly from their natural side sets
        fa, fb = others                                         # one of them is 2
        Xa = pts_from(fa) if fa != 2 else None
        # free points are 2 and one of 1/3; enumerate Q2 = e1 + e2 via the other point and e in S
        j = fa if fa != 2 else fb
        Xj = pts_from(j)
        for ij in range(len(Xj)):
            qj = Xj[ij]
            for ve in V:                                       # Q2 = qj + ve (ve = e2 if j==1, -e3 if j==3)
                q2 = qj + ve
                rhs = -(blocks[j][rows] @ qj) - (blocks[2][rows] @ q2)
                qp = Binv @ rhs; r = np.rint(qp)
                if np.abs(qp - r).max() > 1e-6: continue
                Q = [None] * 4; Q[0] = (0, 0, 0, 0); Q[j] = tuple(int(x) for x in qj); Q[2] = tuple(int(x) for x in q2)
                Q[piv] = tuple(int(x) for x in r)
                sides = [PS.sub(Q[(k + 1) % 4], Q[k]) for k in range(4)]
                if any(s not in Sset for s in sides): continue
                if (A @ np.concatenate(Q)).any(): continue
                out.append(Q)
    return out, 'ok'

def screen(rule, mes=None, verbose=False):
    steps = [tuple(s) for s in rule['steps']]; sq = [tuple(s) for s in rule['sq']]; refl = rule['refl']
    k = len(steps) + 1
    S = pooled()
    cand, st = candidates(steps, sq, refl)
    if cand is None: return dict(status=st)
    res = dict(status='ok', candidates=len(cand), level1=0, hits={})
    if mes is None: mes = [(m, e) for m in range(k) for e in range(k) if m != e]
    for Q in cand:
        qc = [cx(np.array(p)) for p in Q]
        qa = Polygon([(z.real, z.imag) for z in qc])
        if not qa.is_valid or qa.area <= 1e-9: continue
        try:
            if not exact(level1X(steps, sq, refl, qc), qc): continue
        except Exception: continue
        res['level1'] += 1
        lens = [S[PS.sub(Q[(i + 1) % 4], Q[i])] for i in range(4)]
        for (m, e) in mes:
            try: cl = P2.clusters(steps, sq, refl, m, e, qc)
            except Exception: continue
            if all(exact(c, qc) for c in cl):
                res['hits'].setdefault('%d_%d' % (m, e), []).append(dict(quad=[list(q) for q in Q], minlens=lens))
    return res

if __name__ == '__main__':
    t = time.time()
    if sys.argv[1] == 'spectre':
        R = dict(steps=[(60, 3, 1), (0, 2, 0), (60, 3, 1), (60, 3, 1), (0, 2, 0), (60, 3, 1), (-120, 3, 3)],
                 sq=[(6, 2), (5, 1), (3, 2), (0, 1)], refl=True)
        r = screen(R, mes=[(7, 2)])
        import spectre_exact as SE
        P = [np.array(p) for p in SE.P[:14]]; P = P[3:] + P[:3]; P = [p - P[0] for p in P]
        tq = [[int(x) for x in P[i]] for i in (0, 2, 4, 8)]
        h = r['hits'].get('7_2', [])
        print('spectre: candidates', r.get('candidates'), 'level1', r.get('level1'), 'exact (m,e)=(7,2):', len(h),
              'true quad in:', any(x['quad'] == tq for x in h), round(time.time() - t), 's', flush=True)
        json.dump(r, open('rulequads_spectre.json', 'w'))
    else:
        rules = json.load(open(sys.argv[1])); out = []
        for i, R in enumerate(rules):
            r = screen(R); r['rule'] = dict(steps=R['steps'], sq=R['sq'], refl=R['refl']); out.append(r)
            print(i, r['status'], r.get('candidates'), r.get('level1'), {k: len(v) for k, v in r.get('hits', {}).items()},
                  round(time.time() - t), flush=True)
            json.dump(out, open(sys.argv[2], 'w'))
