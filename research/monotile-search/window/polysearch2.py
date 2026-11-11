"""Polygon search, version 2 (THEORY s14). Same target as polysearch.py, but pruned so it can finish:
1. quad filter: the rule's coincidence relations, then the level-1 and level-2 clusters of the quad itself must not
   overlap much (the polygon is close to its quad, so heavy quad overlap rules it out).
2. corner filter: every keypoint of every tile in the level-1/2 clusters (single tile in the Mystic slot) sits at a
   point; the corner sectors meeting at one point must be disjoint. A corner sector depends only on the first and
   last edge of the two arcs that meet there, so this prunes before any arc middles are enumerated.
3. full words: turns, simplicity, single-tile level-1 overlap, Mystic edge matching, realise.valid to level 3."""
import numpy as np, itertools, math, cmath, time, sys, json
from shapely.geometry import Polygon
from shapely.ops import unary_union
import fractile as F, realise as RL, polysearch as PS
from relations import relations
from spectre_exact import cx

def clusters(steps, sq, refl, m, e, qc, levels=2):
    """tile transforms (single tile in every Mystic slot) of the level-1..levels X and Y clusters"""
    obj = {'X': [(1+0j, 0j, 0)], 'Y': [(1+0j, 0j, 0)]}; quad = list(qc); out = []
    for _ in range(levels):
        trs, Q1 = F.supermap(steps, sq, refl, quad)
        new = {}
        for T in ('X', 'Y'):
            tiles = []
            for i, t in enumerate(trs):
                if T == 'Y' and i == e: continue
                tiles += [F.comp(t, u) for u in obj['Y' if i == m else 'X']]
            new[T] = tiles
        obj = new; quad = Q1
        out += [obj['X'], obj['Y']]
    return out

def rotf(t):
    a, b, f = t
    return round(cmath.phase(a) / (math.pi / 6)) % 12, f

def quad_overlap(cl, qc):
    worst = 1.0
    for tiles in cl:
        P = [Polygon([(z.real, z.imag) for z in (F.ap(t, w) for w in qc)]).buffer(0) for t in tiles]
        tot = sum(p.area for p in P); uni = unary_union(P).area
        worst = max(worst, tot / uni if uni else 99)
    return worst

def corner_groups(cl, qc):
    """points where >=2 tile keypoints meet: list of [(k, r, f), ...]"""
    groups = []
    for tiles in cl:
        pts = {}
        for t in tiles:
            r, f = rotf(t)
            for k in range(4):
                z = F.ap(t, qc[k]); key = (round(z.real, 5), round(z.imag, 5))
                pts.setdefault(key, []).append((k, r, f))
        groups += [g for g in pts.values() if len(g) > 1]
    # dedupe identical groups
    seen = set(); res = []
    for g in groups:
        s = tuple(sorted(g))
        if s not in seen: seen.add(s); res.append(s)
    return res

def mask(s, w):
    m = 0
    for i in range(w): m |= 1 << ((s + i) % 12)
    return m

def sector(a_out, b_in, ccw):
    """corner sector (start, width) in 30-degree units from outgoing dir a_out and incoming dir b_in"""
    back = (b_in + 6) % 12
    if ccw: return a_out, (back - a_out) % 12
    return back, (a_out - back) % 12

def place(s, w, r, f):
    return ((r + s) % 12, w) if not f else ((r - s - w) % 12, w)

def mystic_slots(steps, sq, refl, m, e, qc, ci, _cache={}):
    """indices (in cluster ci of clusters()) of tiles that sit in a Mystic slot of their parent, i.e. carry g(P)"""
    key = (tuple(map(tuple, steps)), tuple(map(tuple, sq)), refl, m, e, tuple(qc), ci)
    if key in _cache: return _cache[key]
    level, typ = ci // 2 + 1, 'XY'[ci % 2]
    # rebuild clusters while tagging the tiles that are Mystic first tiles at the bottom level
    obj = {'X': [0], 'Y': [1]}   # 1 = this single tile is a Mystic's first tile
    quad = list(qc)
    for _ in range(level):
        trs, Q1 = F.supermap(steps, sq, refl, quad)
        new = {}
        for T in ('X', 'Y'):
            tags = []
            for i, t in enumerate(trs):
                if T == 'Y' and i == e: continue
                tags += obj['Y' if i == m else 'X']
            new[T] = tags
        obj = new; quad = Q1
    res = [i for i, tg in enumerate(obj[typ]) if tg]
    _cache[key] = res
    return res

def mystic_fits(pre, cl, mslots, gm, poly, tol=1e-6):
    for ci, tiles in enumerate(cl):
        others = pre[ci]
        for i in mslots[ci]:
            t = F.comp(tiles[i], gm)
            G = Polygon([(z.real, z.imag) for z in (F.ap(t, w) for w in poly)])
            if not G.is_valid: return False
            for j, Pj in enumerate(others):
                if Pj.intersects(G) and Pj.intersection(G).area > tol: return False
    return True

def search(steps, sq, refl, m, e, lens, L=3, qtol=1.25, limit_time=3600, verbose=True, only_quads=None):
    t0 = time.time()
    pairs, A = relations(steps, sq, refl, m, e)
    A = None if A is None else np.array(A.tolist(), dtype=np.int64)
    R = [PS.reach(l) for l in lens]
    stats = dict(quads=0, quad_ok=0, corner_combos=0, words=0, polys=0, single_ok=0, valid_calls=0)
    found = []
    def quad_iter():
        if only_quads is not None:
            for Q in only_quads:
                Q = [tuple(q) for q in Q]
                yield Q, [PS.sub(Q[(k + 1) % 4], Q[k]) for k in range(4)]
            return
        for e1 in R[0]:
            for e2 in R[1]:
                for e3 in R[2]:
                    e4 = PS.sub((0, 0, 0, 0), PS.add(PS.add(e1, e2), e3))
                    if e4 not in R[3]: continue
                    yield [(0, 0, 0, 0), e1, PS.add(e1, e2), PS.add(PS.add(e1, e2), e3)], [e1, e2, e3, e4]
    for Q, (e1, e2, e3, e4) in quad_iter():
                if any(ev not in R[k] for k, ev in enumerate((e1, e2, e3, e4))): continue
                if A is not None and (A @ np.concatenate(Q)).any(): continue
                qc = [cx(np.array(p)) for p in Q]
                qa = Polygon([(z.real, z.imag) for z in qc])
                if not qa.is_valid or qa.area <= 1e-9: continue
                stats['quads'] += 1
                ccw = (sum((qc[i].conjugate() * qc[(i + 1) % 4]).imag for i in range(4)) > 0)
                try:
                    cl = clusters(steps, sq, refl, m, e, qc)
                except Exception:
                    continue
                if quad_overlap(cl, qc) > qtol: continue
                stats['quad_ok'] += 1
                groups = corner_groups(cl, qc)
                arcs = [R[0][e1], R[1][e2], R[2][e3], R[3][e4]]
                fl = []
                for k in range(4):
                    d = {}
                    for w in arcs[k]: d.setdefault((w[0], w[-1]), []).append(w)
                    fl.append(d)
                for c in itertools.product(*[list(x.keys()) for x in fl]):
                    # keypoint k: outgoing first dir of arc k, incoming last dir of arc k-1
                    sec = []
                    bad = False
                    for k in range(4):
                        s, w = sector(c[k][0], c[k - 1][1], ccw)
                        if w == 0: bad = True; break
                        sec.append((s, w))
                    if bad: continue
                    for g in groups:
                        acc = 0
                        for (k, r, f) in g:
                            s, w = place(*sec[k], r, f); mk = mask(s, w)
                            if acc & mk: bad = True; break
                            acc |= mk
                        if bad: break
                    if bad: continue
                    stats['corner_combos'] += 1
                    for ws in itertools.product(*[fl[k][c[k]] for k in range(4)]):
                        word = sum(ws, ()); stats['words'] += 1
                        if not PS.turns_ok(word): continue
                        pts = [(0, 0, 0, 0)]
                        for d in word[:-1]: pts.append(PS.add(pts[-1], PS.U[d]))
                        poly = [cx(np.array(p)) for p in pts]
                        pg = Polygon([(z.real, z.imag) for z in poly])
                        if not pg.is_valid or pg.area <= 0: continue
                        stats['polys'] += 1
                        if any(RL.overlaps(c, poly) for c in cl): continue
                        stats['single_ok'] += 1
                        # Mystic prefilter: g(P) placed in the Mystic slot of each cluster must miss every other tile
                        cand = PS.mystic_candidates(poly)
                        if not cand: continue
                        pre = []
                        for ci, tiles in enumerate(cl):
                            pre.append([Polygon([(z.real, z.imag) for z in (F.ap(tt, w) for w in poly)]) for tt in tiles])
                        mslots = [mystic_slots(steps, sq, refl, m, e, qc, ci) for ci in range(len(cl))]
                        for gm in cand:
                            if not mystic_fits(pre, cl, mslots, gm, poly): continue
                            stats['valid_calls'] += 1
                            ok, lev, T = RL.valid(steps, sq, refl, m, e, qc, poly, gm, L)
                            if ok:
                                found.append(dict(word=list(word), quad=[list(q) for q in Q],
                                                  g=[gm[0].real, gm[0].imag, gm[1].real, gm[1].imag, gm[2]]))
                                if verbose: print("FOUND", word, flush=True)
                        if time.time() - t0 > limit_time: return found, stats, 'time'
    return found, stats, 'done'

if __name__ == '__main__':
    sp_steps = [(60, 3, 1), (0, 2, 0), (60, 3, 1), (60, 3, 1), (0, 2, 0), (60, 3, 1), (-120, 3, 3)]
    sq = [(6, 2), (5, 1), (3, 2), (0, 1)]
    mode = sys.argv[1] if len(sys.argv) > 1 else 'truequad'
    t = time.time()
    oq = [[(0, 0, 0, 0), (1, 0, 0, 1), (1, 1, 0, 1), (2, 2, 0, 0)]] if mode == 'truequad' else None
    if mode == 'truequad':
        import spectre_exact as SE
        P = [np.array(p) for p in SE.P[:14]]; P = P[3:] + P[:3]; P = [p - P[0] for p in P]
        oq = [[tuple(int(x) for x in P[i]) for i in (0, 2, 4, 8)]]
    f, st, s = search(sp_steps, sq, True, 7, 2, (2, 2, 4, 6), limit_time=5400, only_quads=oq)
    print("control", mode, st, "found", len(f), s, round(time.time() - t), "s", flush=True)
    for x in f: print(x['word'])
    json.dump(f, open('polysearch2_control_%s.json' % mode, 'w'))
