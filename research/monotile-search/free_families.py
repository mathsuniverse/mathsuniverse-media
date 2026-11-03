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
