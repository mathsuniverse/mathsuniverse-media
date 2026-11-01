"""Validation runs: the hat and turtle must cover large discs and have no torus tiling up
to the cap; ordinary shapes must tile periodically.  Writes validation.json.

Usage: python3 validate.py [--rmax 15] [--tcap 48]
"""
import argparse
import json
import os
import time

import polykite as P
import tiler as T

HERE = os.path.dirname(os.path.abspath(__file__))


def run(name, cells, radii, tcap, heesch_k=0):
    rec = {'name': name, 'n': len(cells)}
    covers = []
    for R in radii:
        t = time.time()
        ok = T.cover(cells, R)
        covers.append({'R': R, 'covered': ok, 'kites_in_disc': len(T.disc_kites(R)),
                       'seconds': round(time.time() - t, 2)})
        print(f'{name:10s} cover R={R:<4} {ok}  ({covers[-1]["seconds"]}s)', flush=True)
        if not ok:
            break
    rec['cover'] = covers
    t = time.time()
    per = T.periodic(cells, tcap)
    max_index = tcap * len(cells) // 6
    rec['periodic'] = {
        'tcap_tiles_per_domain': tcap,
        'max_hexagons_per_domain': max_index,
        'lattice_classes_tried': sum(1 for l in T._LATTICES[max_index] if (6 * l[0] * l[2]) % len(cells) == 0),
        'found': None if per is None else {'lattice_hnf': list(per[0]), 'tiles_per_domain': per[1]},
        'seconds': round(time.time() - t, 2)}
    print(f'{name:10s} periodic (<= {tcap} tiles/domain): {per}  ({rec["periodic"]["seconds"]}s)', flush=True)
    if per is not None:
        patch = T.periodic_patch(cells, per[0], 4)
        seen = set()
        for ks, _ in patch:
            assert not (seen & ks)
            seen |= ks
        assert set(T.disc_kites(4)) <= seen
        rec['periodic']['lift_verified_R4'] = True
    if heesch_k:
        t = time.time()
        k, lv, capped = T.heesch(cells, heesch_k)
        rec['coronas'] = {'k_tested': heesch_k, 'max_k_found': k, 'stopped_at_cap': capped,
                          'seconds': round(time.time() - t, 2)}
        print(f'{name:10s} coronas: {k} (cap {heesch_k})', flush=True)
    return rec


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--rmax', type=int, default=15)
    ap.add_argument('--tcap', type=int, default=48)
    a = ap.parse_args()
    radii = [r for r in (2, 4, 6, 8, 10, 12, 15, 20) if r <= a.rmax]
    shapes = [
        ('kite', [(0, 0, 0)]),
        ('hexagon', [(0, 0, k) for k in range(6)]),
        ('hat', P.hat_cells()),
        ('turtle', P.turtle_cells()),
    ]
    out = []
    for name, cells in shapes:
        hk = 3 if name in ('hat', 'turtle') else 0
        out.append(run(name, cells, radii, a.tcap, hk))
    with open(os.path.join(HERE, 'validation.json'), 'w') as f:
        json.dump(out, f, indent=1)


if __name__ == '__main__':
    main()
