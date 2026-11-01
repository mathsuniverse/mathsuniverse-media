"""Tests for the grid-agnostic engine (grids.py, engine.py, verify.py).

Run:  python3 -m pytest -q test_engine.py
"""
import grids as G
import engine as E
import verify as V
import polykite as PK

# OEIS (fetched 1 Nov 2026).  Free polyforms with n cells, holes allowed.
OEIS = {
    'square': ('A000105', [1, 1, 2, 5, 12, 35, 108, 369, 1285]),
    'hex': ('A000228', [1, 1, 3, 7, 22, 82, 333, 1448]),
    'tri': ('A000577', [1, 1, 1, 3, 4, 12, 24, 66, 160, 448]),
    'kite': ('A057786', [1, 2, 4, 10, 27, 85, 262, 873, 2917]),
    'drafter': ('A197462', [1, 3, 3, 9, 14, 38, 74, 185, 414, 1026, 2440]),
    'rhomb': ('A197459', [1, 1, 3, 4, 12, 27, 78, 208, 635, 1859]),
    'tetrakis': ('A197465', [1, 2, 2, 6, 8, 22, 42, 112, 252, 650]),
    'triakis': ('A057784', [1, 2, 2, 4, 4, 10, 13, 29, 47, 100, 181]),
    'cairo': ('A159866', [1, 2, 5, 17, 55, 206, 781, 3099]),
    'prismatic': ('A197156', [1, 3, 5, 20, 56, 225, 819, 3333]),
    'floret': ('A197159', [1, 3, 8, 25, 80, 291, 1036, 3875]),
}
POINT_GROUP = {'square': 8, 'hex': 12, 'tri': 12, 'kite': 12, 'drafter': 12, 'rhomb': 12, 'tetrakis': 8,
               'triakis': 12, 'cairo': 8, 'prismatic': 4, 'floret': 6}


def test_grids_tile_and_symmetries_exact():
    for name in G.GRIDS:
        g = G.get(name)
        assert G.check_tiling(g), name
        assert G.check_symmetries(g), name
        assert len(g.ops) == POINT_GROUP[name], (name, len(g.ops))
        assert g.chiral == (name == 'floret')


def test_counts_match_oeis():
    for name, (anum, seq) in OEIS.items():
        g = G.get(name)
        nmax = min(len(seq), 8)
        lv = E.enumerate_fixed_free(g, nmax)
        for n in range(1, nmax + 1):
            free = len(E.free_classes(g, lv[n])) if n <= 6 else len(lv[n])
            assert free == seq[n - 1], (name, anum, n, free)
            for p in lv[n][:30]:
                assert E.is_connected(g, p)


def test_no_off_group_congruent_copies_small_n():
    """Every on-grid congruent copy of a small polyform is a grid-symmetry image (checked
    exhaustively for n <= 5 on every grid; on the chiral floret grid this means a mirror
    image of an asymmetric shape never lands on the grid at these sizes)."""
    for name in G.GRIDS:
        g = G.get(name)
        lv = E.enumerate_fixed_free(g, 5)
        for n in range(1, 6):
            for p in lv[n]:
                sym = {f for f, _ in E.sym_forms(g, p)}
                for h in E.congruent_forms(g, p):
                    assert h in sym or E.canonical(g, h) == p, (name, p)


def test_kite_grid_identical_to_polykite_module():
    g = G.get('kite')
    for t in range(6):
        assert set(g.cell_vertices((2, -1, t))) == {G.eis(*v) for v in PK.kite_vertices((2, -1, t))}
    lv = E.enumerate_fixed_free(g, 7)
    old = PK.enumerate_free(7)
    for n in range(1, 8):
        assert lv[n] == old[n]


def test_drafter_contains_polykites():
    """Every polykite is a polydrafter: kite k = drafters 2k, 2k+1."""
    gk, gd = G.get('kite'), G.get('drafter')
    for (i, j, k) in PK.hat_cells():
        vs = set(gk.cell_vertices((i, j, k)))
        d = set(gd.cell_vertices((i, j, 2 * k))) | set(gd.cell_vertices((i, j, 2 * k + 1)))
        assert vs <= d and len(d) == 4


def test_hat_open_and_ordinary_shapes_classified():
    g = G.get('kite')
    hat = PK.hat_cells()
    r = E.classify(g, hat, tcap=6, rcap=3)
    assert r['cls'] == 'OPEN'
    r = E.classify(g, [(0, 0, k) for k in range(6)], tcap=6, rcap=3)
    assert r['cls'] == 'PERIODIC' and r['tiles_per_domain'] == 1
    ok, msg = V.check_record(g, r)
    assert ok, msg
    lv = E.enumerate_fixed_free(g, 2)
    assert sorted(E.classify(g, p, tcap=6, rcap=3)['cls'] for p in lv[2]) == ['PERIODIC', 'STUCK']


def test_certificates_recheck():
    g = G.get('square')
    lv = E.enumerate_fixed_free(g, 7)
    stuck = [p for p in lv[7] if E.classify(g, p, tcap=12, rcap=4)['cls'] == 'STUCK']
    assert len(stuck) == 4          # 3 non-tiling heptominoes + the one with a hole
    for p in stuck:
        r = E.classify(g, p, tcap=12, rcap=4)
        ok, msg = V.check_record(g, r)
        assert ok, msg


def test_exact_congruence_check():
    g = G.get('drafter')
    p = [(0, 0, 0), (0, 0, 1), (0, 0, 2)]
    for op in g.op_tabs:
        assert V.exact_congruent(g, p, E.transform(g, p, op))
    assert not V.exact_congruent(g, p, [(0, 0, 0), (0, 0, 1), (0, 0, 11)]) or \
        E.canonical(g, [(0, 0, 0), (0, 0, 1), (0, 0, 11)]) == E.canonical(g, p)


def test_heesch_generic():
    g = G.get('kite')
    k, lv, capped = E.heesch(E.Shape(g, [(0, 0, t) for t in range(6)]), 2)
    assert k == 2 and capped
    # stage-1 record: n10_00610 has Heesch number 3
    import json, os
    here = os.path.dirname(os.path.abspath(__file__))
    old = json.load(open(os.path.join(here, 'results.json')))
    rec = [s for s in old['10']['shapes'] if s['id'] == 'n10_00610'][0]
    k, lv, capped = E.heesch(E.Shape(g, [tuple(c) for c in rec['cells']]), 5)
    assert k == 3 and not capped


if __name__ == '__main__':
    import inspect
    import sys
    fails = 0
    for name, fn in list(globals().items()):
        if name.startswith('test_') and inspect.isfunction(fn):
            try:
                fn()
                print('PASS', name, flush=True)
            except Exception as e:  # noqa
                fails += 1
                print('FAIL', name, repr(e), flush=True)
    sys.exit(1 if fails else 0)
