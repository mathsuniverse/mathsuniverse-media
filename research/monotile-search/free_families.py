"""Silver Tile(1,1): every outline family with edges in 8 directions, all edges of length 1, tested with the free engine
(no grid), with mirrors allowed and with mirrors forbidden (the Spectre rule)."""
import time
import free2 as F2


def test_one(seq, Rs=(1.5, 2, 3), node_limit=20000, max_edges=10, max_tiles=12, budget=120):
    out = {}
    for mir in (True, False):
        try:
            S = F2.Search(list(seq), 8, mir)
        except AssertionError:
            return {'error': 'not a simple polygon at unit edges'}
        res = None
        for R in Rs:
            r = S.cover(R * S.diam / 2, node_limit=node_limit)
            if r is None:
                res = dict(cls='UNDECIDED', at_R=R); break
            if not r:
                res = dict(cls='STUCK', fail_R=R); break
        if res is None:
            p = F2.periodic4(S, max_tiles, max_edges, budget)
            if p[0]:
                res = dict(cls='PERIODIC', **p[0])
            else:
                res = dict(cls='OPEN', lattices_tested=p[1], of=p[2], budget_hit=p[0] is None)
        out['mirror' if mir else 'nomirror'] = res
        if mir and res['cls'] == 'STUCK':
            out['nomirror'] = dict(cls='STUCK', note='implied (fewer placements)')
            break
    return out


def classify_general(seq, N, lens=None):
    """Decisive classification of an equal-edge outline in N directions, with and without mirrors:
    patches (radius 1.5, 2, 3), then repeats read off the tile's own patch, then all short repeat patterns,
    then a radius-4 patch and its recurring translations. OPEN only if every check fails to find a repeat."""
    out = {}
    for mir in (True, False):
        try:
            S = F2.Search(list(seq), N, mir, lens)
        except AssertionError:
            return {'error': 'not simple'}
        res = None
        for R in (1.5, 2, 3):
            r = S.cover(R * S.diam / 2, node_limit=30000)
            if r is None:
                res = dict(cls='UNDECIDED', at_R=R); break
            if not r:
                res = dict(cls='STUCK', fail_R=R); break
        if res is None:
            p = F2.patch_periods(S, patch=S.patch, max_tiles=48, budget=120)
            if not p[0]:
                q = F2.periodic4(S, 12, 10, budget=300)
                p = (q[0], q[1])
            if not p[0]:
                r4 = S.cover(4 * S.diam / 2, node_limit=200000, time_limit=300)
                if r4:
                    p = F2.patch_periods(S, patch=S.patch, max_tiles=64, budget=300)
                elif r4 is False:
                    res = dict(cls='STUCK', fail_R=4)
            if res is None:
                res = dict(cls='PERIODIC', **p[0]) if p[0] else dict(cls='OPEN', covered_R=3 if not r4 else 4)
        out['mirror' if mir else 'nomirror'] = res
        if mir and res['cls'] == 'STUCK':
            out['nomirror'] = dict(cls='STUCK', note='implied')
            break
    return out


def classify_deep(seq, N, lens=None):
    """Bigger budgets for shapes the first pass left UNDECIDED: patches to radius 5 (500k nodes, 15 min each),
    repeats read off the radius-5 patch (up to 64 tiles), then all patterns up to 12-edge vectors and 16 tiles."""
    out = {}
    for mir in (True, False):
        try:
            S = F2.Search(list(seq), N, mir, lens)
        except AssertionError:
            return {'error': 'not simple'}
        res = None; covered = None
        for R in (1.5, 2, 3, 4, 5):
            r = S.cover(R * S.diam / 2, node_limit=500000, time_limit=900)
            if r is None:
                res = dict(cls='UNDECIDED', at_R=R, covered_R=covered); break
            if not r:
                res = dict(cls='STUCK', fail_R=R); break
            covered = R
        if res is None:
            p = F2.patch_periods(S, patch=S.patch, max_tiles=64, budget=900)
            if not p[0]:
                q = F2.periodic4(S, 16, 12, budget=1800)
                p = (q[0], q[1])
            res = dict(cls='PERIODIC', **p[0]) if p[0] else dict(cls='OPEN', covered_R=5)
        out['mirror' if mir else 'nomirror'] = res
        if mir and res['cls'] == 'STUCK':
            out['nomirror'] = dict(cls='STUCK', note='implied')
            break
    return out
