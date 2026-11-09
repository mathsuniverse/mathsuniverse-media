"""Hat-type (g = 1) test from THEORY.md s8-9: place a 12-direction outline using only the orientations that keep the
even-direction and odd-direction edge families apart (rotations by multiples of 60 degrees, and mirrors composed with
them; conj maps d -> -d, which preserves parity). This is the symmetry group of a Tile(a,b) family with a != b.
A shape that tiles periodically with all 12 rotations may tile only aperiodically here (Tile(1,1) -> hat family)."""
import free as F, free2 as F2


def search(seq, N=12, mirror=True, lens=None, step=2):
    S = F2.Search(list(seq), N, mirror, lens)
    S.orients = [o for o in S.orients if o[0] % step == 0]
    S.by_vec = {}
    m = S.tile.m
    for oi, (r, fl, vs, angs) in enumerate(S.orients):
        for k in range(m):
            S.by_vec.setdefault(S.ring.sub(vs[(k + 1) % m], vs[k]), []).append((oi, k))
    S._ov = {}
    return S


def classify(seq, N=12, lens=None, step=2, Rs=(1.5, 2, 3), node_limit=30000):
    out = {}
    for mir in (True, False):
        try:
            S = search(seq, N, mir, lens, step)
        except AssertionError:
            return {'error': 'not simple'}
        res = None
        for R in Rs:
            r = S.cover(R * S.diam / 2, node_limit=node_limit, scan=None)
            if r is None:
                res = dict(cls='UNDECIDED', at_R=R); break
            if not r:
                res = dict(cls='STUCK', fail_R=R); break
        if res is None:
            p = F2.patch_periods(S, patch=S.patch, max_tiles=48, budget=120)
            if not p[0]:
                q = F2.periodic4(S, 12, 10, budget=300)
                p = (q[0], q[1])
            res = dict(cls='PERIODIC', **p[0]) if p[0] else dict(cls='OPEN', covered_R=Rs[-1])
        out['mirror' if mir else 'nomirror'] = res
        if mir and res['cls'] == 'STUCK':
            out['nomirror'] = dict(cls='STUCK', note='implied'); break
    return out


def lens_for(seq, N, lam, swap=False):
    one = (1, 0, 0, 0)
    return [(lam if (d % 2) != swap else one) for d in seq]
