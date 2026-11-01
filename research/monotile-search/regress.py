"""Regression checks of the grid-agnostic engine.

  python3 regress.py kite      compare results/kite*.json with the stage-1 polykite run
                               (results.json): shape lists, class per shape, hat/turtle
  python3 regress.py myers     compare square / hex / tri / kite class counts with Joseph
                               Myers' polyform-tiling tables
Writes results/regression.json.
"""
import gzip
import json
import os
import sys

import engine as E
import grids as G
import polykite as PK

HERE = os.path.dirname(os.path.abspath(__file__))

# Joseph Myers, polyomino.org.uk/mathematics/polyform-tiling (fetched 1 Nov 2026):
# n: (shapes, non-tilers incl. shapes with holes)
MYERS = {
    'square': {1: (1, 0), 2: (1, 0), 3: (2, 0), 4: (5, 0), 5: (12, 0), 6: (35, 0), 7: (108, 4), 8: (369, 26),
               9: (1285, 235), 10: (4655, 1585)},
    'hex': {1: (1, 0), 2: (1, 0), 3: (3, 0), 4: (7, 0), 5: (22, 0), 6: (82, 5), 7: (333, 39), 8: (1448, 394),
            9: (6572, 2784)},
    'tri': {1: (1, 0), 2: (1, 0), 3: (1, 0), 4: (3, 0), 5: (4, 0), 6: (12, 0), 7: (24, 1), 8: (66, 0),
            9: (160, 21), 10: (448, 107), 11: (1186, 619), 12: (3334, 1300)},
    'kite': {1: (1, 0), 2: (2, 1), 3: (4, 0), 4: (10, 5), 5: (27, 26), 6: (85, 14), 7: (262, 207),
             8: (873, 833), 9: (2917, 2162), 10: (10011, 9996)},
}
OLDMAP = {'no_tile': 'STUCK', 'periodic': 'PERIODIC', 'candidate': 'OPEN'}


def load_shapes(name):
    return json.load(gzip.open(os.path.join(HERE, 'results', f'{name}_shapes.json.gz'), 'rt'))


def kite():
    old = json.load(open(os.path.join(HERE, 'results.json')))
    new = load_shapes('kite')
    g = G.get('kite')
    hat = E.canonical(g, PK.hat_cells())
    tur = E.canonical(g, PK.turtle_cells())
    out = {}
    for n in sorted(new, key=int):
        if n not in old:
            continue
        o = {tuple(map(tuple, s['cells'])): s for s in old[n]['shapes']}
        nw = {tuple(map(tuple, s['cells'])): s for s in new[n]}
        same_list = set(o) == set(nw)
        cls_diff = [k for k in nw if k in o and OLDMAP[o[k]['cls']] != nw[k]['cls']]
        per_diff = [k for k in nw if k in o and nw[k]['cls'] == 'PERIODIC' and o[k]['cls'] == 'periodic'
                    and nw[k]['tiles_per_domain'] != o[k]['tiles_per_domain']]
        fr_diff = [k for k in nw if k in o and nw[k]['cls'] == 'STUCK' and o[k]['cls'] == 'no_tile'
                   and nw[k]['fail_R'] != o[k]['fail_R']]
        opens = [k for k in nw if nw[k]['cls'] == 'OPEN']
        cnt = {}
        for s in nw.values():
            cnt[s['cls']] = cnt.get(s['cls'], 0) + 1
        out[n] = dict(shapes_old=len(o), shapes_new=len(nw), identical_shape_lists=same_list,
                      class_disagreements=len(cls_diff), min_period_disagreements=len(per_diff),
                      fail_radius_disagreements=len(fr_diff), counts_new=cnt,
                      counts_old={OLDMAP[k]: v for k, v in old[n]['counts'].items()},
                      open_shapes=['hat' if k == hat else 'turtle' if k == tur else str(k) for k in opens])
        print(n, out[n])
    return out


def myers():
    out = {}
    for name, tab in MYERS.items():
        p = os.path.join(HERE, 'results', f'{name}.json')
        if not os.path.exists(p):
            continue
        res = json.load(open(p))
        for n, (shapes, nontile) in sorted(tab.items()):
            r = res.get(str(n))
            if r is None:
                continue
            c = r['counts']
            ok = (r['free'] == shapes and c.get('STUCK', 0) == nontile)
            out[f'{name}{n}'] = dict(grid=name, n=n, myers_shapes=shapes, myers_nontilers=nontile,
                                     ours_shapes=r['free'], ours=c, match=ok)
            print(name, n, 'Myers', shapes, nontile, '| ours', r['free'], c, 'MATCH' if ok else 'MISMATCH')
    return out


if __name__ == '__main__':
    p = os.path.join(HERE, 'results', 'regression.json')
    reg = json.load(open(p)) if os.path.exists(p) else {}
    for what in sys.argv[1:]:
        reg[what] = globals()[what]()
    json.dump(reg, open(p, 'w'), indent=1)
