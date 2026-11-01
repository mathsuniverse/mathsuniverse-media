"""Tests: kite-grid geometry, symmetry, enumeration counts, hat/turtle cross-checks
against Kaplan's substitution (hat_tiling.py), and independent checks of SAT outputs.

Run:  python3 -m pytest -q test_monotile.py      (or  python3 test_monotile.py)
"""
import math
import os
import sys

import polykite as P
import tiler as T

HAT_ENGINE = os.environ.get(
    'HAT_ENGINE',
    '/tmp/claude-0/-home-claude/8d78e7f5-5d27-5557-bcf6-cdfb92e43b7a/scratchpad/pipeline/engine')


# ------------------------------------------------------------------ geometry

def test_kite_shape_exact():
    """Every kite: side lengths^2 = 3,1,1,3 (exact integers), area sqrt(3)."""
    for k in range(6):
        for (i, j) in [(0, 0), (3, -2), (-1, 5)]:
            vs = P.kite_vertices((i, j, k))
            sides = [P.e_norm(P.e_sub(vs[(t + 1) % 4], vs[t])) for t in range(4)]
            assert sides == [3, 1, 1, 3], sides
            assert abs(abs(P.polygon_area([P.e_xy(v) for v in vs])) - math.sqrt(3)) < 1e-12
            # centre->vertex distance^2 = 4, centre->midpoints = 3
            c = vs[0]
            assert P.e_norm(P.e_sub(vs[2], c)) == 4


def test_hexagon_is_six_kites_and_grid_tiles():
    from shapely.geometry import Polygon
    hexa = P.polykite_polygon([(0, 0, k) for k in range(6)])
    reg = Polygon([P.e_xy(v) for v in P.VV])
    assert hexa.symmetric_difference(reg).area < 1e-9
    assert abs(hexa.area - 6 * math.sqrt(3)) < 1e-9
    # kites in a block don't overlap and their areas add up
    from shapely.ops import unary_union
    ks = [(i, j, k) for i in range(-2, 3) for j in range(-2, 3) for k in range(6)]
    u = unary_union([Polygon(P.kite_xy(c)) for c in ks])
    assert abs(u.area - len(ks) * math.sqrt(3)) < 1e-7


def test_centre_lattice_roundtrip():
    for i in range(-4, 5):
        for j in range(-4, 5):
            assert P.point_to_centre(P.centre_point(i, j)) == (i, j)
    assert P.point_to_centre((1, 0)) is None


def test_symmetries_preserve_geometry():
    for i in range(-2, 3):
        for j in range(-2, 3):
            for k in range(6):
                kt = (i, j, k)
                vs = set(P.kite_vertices(kt))
                assert {P.e_rot(v) for v in vs} == set(P.kite_vertices(P.kite_rot(kt)))
                assert {P.e_conj(v) for v in vs} == set(P.kite_vertices(P.kite_conj(kt)))
    assert P.kite_rot((1, 2, 3), 6) == (1, 2, 3)


def test_adjacency():
    for k in range(6):
        en = P.edge_neighbours((0, 0, k))
        vn = P.vertex_neighbours((0, 0, k))
        assert len(en) == 4          # 2 in own hexagon, 2 across hexagon edges
        assert len(vn) == 9          # 5 (centre) + 2 + 2 (midpoints) + 0 new at vertex
        assert set(en) <= set(vn)


# ------------------------------------------------------------------ enumeration

def test_counts_match_oeis_A057786():
    lv = P.enumerate_free(9)
    for n in range(1, 10):
        assert len(lv[n]) == P.A057786[n - 1], (n, len(lv[n]))
        for p in lv[n][:50]:
            assert P.is_connected(p)


# ------------------------------------------------------------------ hat family

def _hats_from_engine(levels=3):
    sys.path.insert(0, HAT_ENGINE)
    import hat_tiling
    return hat_tiling.hats(levels)


def _engine_offset(poly):
    x0, y0 = poly[0]
    b = round(y0 / (math.sqrt(3) / 2))
    a = round(x0 - b / 2)
    snap = P.e_xy((a, b))
    assert math.hypot(snap[0] - x0, snap[1] - y0) < 1e-6, "engine vertex not on lattice"
    for da in range(-3, 4):
        for db in range(-3, 4):
            tx, ty = P.e_xy((a + da, b + db))
            ox, oy = tx - x0, ty - y0
            _, ok = P.kites_in_polygon([(x + ox, y + oy) for x, y in poly])
            if ok:
                return ox, oy
    raise AssertionError("no offset")


def test_hat_is_8_kites():
    hat = P.hat_cells()
    assert len(hat) == 8
    poly = P.polykite_polygon(hat)
    assert abs(poly.area - 8 * math.sqrt(3)) < 1e-9
    # 13 listed vertices (one straight-through point merged); 14 edges in Tile(1, sqrt3)
    assert len(poly.exterior.coords) - 1 in (13, 14)


def test_engine_hat_patch_lies_on_kite_grid():
    """Every hat in Kaplan's level-3 substitution patch is a union of 8 grid kites, all
    congruent (incl. reflections) to our hat polykite, and they never overlap."""
    hats = _hats_from_engine(3)
    # the engine draws hats at a reduced scale: rescale so the short edges have length 1
    p0 = hats[0][1]
    sc = 1 / min(math.dist(p0[i], p0[(i + 1) % len(p0)]) for i in range(len(p0)))
    assert abs(sc - round(sc)) < 1e-9
    hats = [(lab, [(x * sc, y * sc) for x, y in poly]) for lab, poly in hats]
    # the engine's patch is re-centred (metatile centroids), so find the global
    # translation that puts its first hat on our grid, then apply it to every hat
    ox, oy = _engine_offset(hats[0][1])
    can = P.canonical(P.hat_cells())
    used = set()
    nref = 0
    for lab, poly in hats:
        pts = [(x + ox, y + oy) for x, y in poly]
        cells, ok = P.kites_in_polygon(pts)
        assert ok and len(cells) == 8, lab
        assert P.canonical(cells) == can
        assert not (used & set(cells))
        used |= set(cells)
        # reflected iff orientation is one of the mirrored forms
        if P.normalise(cells) not in [P.normalise(P.transform(P.hat_cells(), (r, 0))) for r in range(6)]:
            nref += 1
    assert nref == sum(1 for lab, _ in hats if lab == 'H1')
    assert len(used) == 8 * len(hats)


def test_turtle():
    tur = P.turtle_cells()
    assert len(tur) == 10
    assert P.canonical(tur) != P.canonical(P.hat_cells())


# ------------------------------------------------------------------ SAT outputs

def _check_exact(patch, region):
    seen = set()
    for ks, _ in patch:
        assert not (seen & set(ks))
        seen |= set(ks)
    assert set(region) <= seen


def test_cover_solution_valid():
    hat = P.hat_cells()
    can = P.canonical(hat)
    ok, patch, region = T.cover(hat, 3, return_patch=True)
    assert ok
    _check_exact(patch, region)
    for ks, _ in patch:
        assert P.canonical(ks) == can


def test_torus_solution_lifts_to_plane_tiling():
    for cells in ([(0, 0, 0)], [(0, 0, 0), (0, 0, 1), (0, 0, 2)], P.enumerate_free(6)[6][7]):
        res = T.periodic(list(cells), 12)
        assert res is not None
        lat, _ = res
        patch = T.periodic_patch(list(cells), lat, 3)
        _check_exact(patch, T.disc_kites(3))


def test_ordinary_shapes_tile_periodically():
    assert T.periodic([(0, 0, 0)], 12) is not None
    assert T.periodic([(0, 0, k) for k in range(6)], 12) == ((1, 0, 1), 1)


def test_hnf_and_lattices():
    assert T.hnf((2, 0), (1, 3)) == (2, 1, 3)
    assert T.hnf((1, 3), (3, 3)) == (2, 1, 3)
    assert T.hnf((0, 3), (2, 1)) == (6, 2, 1)
    # number of index-N sublattices of Z^2 is sigma(N); classes are fewer
    assert len(T.all_lattices(1)) == 1


def _check_coronas(levels):
    """Independent verification of a corona structure."""
    seen = set()
    for lv in levels:
        for p in lv:
            assert not (seen & p)
            seen |= p
    union = set()
    for L, lv in enumerate(levels):
        prev = set(union)
        for p in lv:
            union |= p
        if L >= 1:
            assert not T._holes(union), f"hole at level {L}"
            assert T._vnbrs(prev) <= union, f"level {L} does not surround"


def test_heesch_structure_and_tilers():
    hexa = [(0, 0, k) for k in range(6)]
    k, lv, capped = T.heesch(hexa, 3)
    assert k == 3 and capped
    _check_coronas(lv)
    k, lv, capped = T.heesch(P.hat_cells(), 2)
    assert k == 2 and capped
    _check_coronas(lv)


if __name__ == '__main__':
    import inspect
    fails = 0
    for name, fn in list(globals().items()):
        if name.startswith('test_') and inspect.isfunction(fn):
            try:
                fn()
                print('PASS', name)
            except Exception as e:  # noqa
                fails += 1
                print('FAIL', name, repr(e))
    sys.exit(1 if fails else 0)
