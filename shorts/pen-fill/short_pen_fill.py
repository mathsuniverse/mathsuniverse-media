"""'One tile. It never repeats.' A pen draws the hat tiling from one hat outwards, then decodes the hidden ladder.

Facts (checked 1 Nov 2026, on the level-5 patch, 7,921 hats):
  the hat: Smith, Myers, Kaplan, Goodman-Strauss (2023); David Smith an amateur from Yorkshire.
  geometry: hat_tiling.py (port of Kaplan's hatviz, BSD-3), verified no overlaps / no gaps.
  normal : flipped -> phi^4 = 6.854 (measured 6.8543). On-screen ratio = live count in the drawn square.
  level-1 clusters (metatiles) have 1, 2 or 4 hats; every flipped hat lies in a 4-cluster, exactly one per 4-cluster.
  H-type clusters at levels 1..5 hold 4, 25, 169, 1156, 7921 hats = 2^2, 5^2, 13^2, 34^2, 89^2 (alternate Fibonacci
  numbers squared); successive ratios -> phi^4. The hierarchy (with unique composition) is why no period exists.
"""
import os, sys, math, bisect
from collections import defaultdict
os.environ.setdefault('MU_THEME', 'paper')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import std_short as S
from std_short import INK
from mu_style import PINK, ramp, ease
import hat_tiling as HT
from shapely.geometry import Polygon
from shapely.ops import unary_union

B = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build', 'penfill')
FX, FY, FS = 540, 965, 860

# ---------------------------------------------------------------- the patch, with its hierarchy
_raw = []
def _flat(m, T, path):
    if isinstance(m, HT.Hat): _raw.append((m.label, [HT.tpt(T, p) for p in HT.HAT], path)); return
    for i, (CT, g) in enumerate(m.children): _flat(g, HT.mul(T, CT), path + (i,))
_t = [HT._H(), HT._T(), HT._P(), HT._F()]
DEPTH = 6                                                     # level-6 patch (54k hats) so the big cluster is fully surrounded
for _ in range(DEPTH - 1): _t = HT.metatiles(HT.patch(*_t))
_flat(_t[0], HT.IDENT, ())
def cen(p): return (sum(q[0] for q in p) / len(p), sum(q[1] for q in p) / len(p))

members = defaultdict(list)                                   # (level, prefix) -> hat indices
for i, (_, _, path) in enumerate(_raw):
    for lev in (1, 2, 3, 4): members[(lev, path[:DEPTH - lev])].append(i)
GX = sum(cen(p)[0] for _, p, _ in _raw) / len(_raw); GY = sum(cen(p)[1] for _, p, _ in _raw) / len(_raw)
def mcen(key): return cen([cen(_raw[i][1]) for i in members[key]])
# nested chain of H-clusters (4, 25, 169, 1156 hats), each child nearest its parent's centre
SIZES = {1: 4, 2: 25, 3: 169, 4: 1156}
k4 = min([k for k in members if k[0] == 4 and len(members[k]) == 1156], key=lambda k: math.dist(mcen(k), (GX, GY)))
CHAIN = {4: k4}
for lev in (3, 2, 1):
    par = CHAIN[lev + 1]; pc = mcen(par)
    kids = [k for k in members if k[0] == lev and k[1][:len(par[1])] == par[1] and len(members[k]) == SIZES[lev]]
    CHAIN[lev] = min(kids, key=lambda k: math.dist(mcen(k), pc))
first = next(i for i in members[CHAIN[1]] if _raw[i][0] != 'H1')
HX, HY = cen(_raw[first][1])

TILES = sorted(((max(abs(cen(p)[0] - HX), abs(cen(p)[1] - HY)), l, p, i) for i, (l, p, _) in enumerate(_raw)), key=lambda z: z[0])
TILES = [z for z in TILES if z[0] < 58]
TILES.insert(0, TILES.pop(next(j for j, z in enumerate(TILES) if z[3] == first))); TILES[0] = (0.0,) + TILES[0][1:]
DIST = [z[0] for z in TILES]
FLIPC = [0]
for z in TILES: FLIPC.append(FLIPC[-1] + (z[1] == 'H1'))
INSIDE = set(z[3] for z in TILES)

GREENS = [(0.60, 0.79, 0.62), (0.47, 0.70, 0.55), (0.73, 0.86, 0.71)]
FLIP = (0.97, 0.76, 0.40); EDGE = (0.20, 0.27, 0.25); PEN = (0.88, 0.40, 0.30)
LADDER = {1: (0.88, 0.40, 0.30), 2: (0.80, 0.25, 0.35), 3: (0.62, 0.20, 0.45), 4: (0.40, 0.18, 0.50)}
def shade(p):
    a = math.degrees(math.atan2(p[1][1] - p[0][1], p[1][0] - p[0][0])) % 360
    return GREENS[int(round(a / 60)) % 3]
COLS = [FLIP if l == 'H1' else shade(p) for _, l, p, _ in TILES]

def outline(idx):
    u = unary_union([Polygon(_raw[i][1]).buffer(1e-7) for i in idx]).buffer(-1e-7)
    geoms = getattr(u, 'geoms', [u])
    return [list(g.exterior.coords) for g in geoms]
L1_OUT = [outline(v) for k, v in members.items() if k[0] == 1 and all(i in INSIDE for i in v)]
CH_OUT = {lev: outline(members[CHAIN[lev]]) for lev in (1, 2, 3, 4)}
_xs = [q[0] for r in CH_OUT[4] for q in r]; _ys = [q[1] for r in CH_OUT[4] for q in r]
C4 = ((min(_xs) + max(_xs)) / 2, (min(_ys) + max(_ys)) / 2)            # frame the 1156-hat cluster

# ---------------------------------------------------------------- timing helpers (set after sh exists)
def wi(i, k): return sh.BEATS[i]['words'][k]['start']

def fill_end(): return sh.bs(5) - 0.3
def base_scale(t):
    te = fill_end(); b = 70 * (14 / 70) ** (min(t, te) / te)
    return b * (240 / 70) ** (1 - ease(ramp(t, 1.9, 4.2)))
def camera(t):
    """(scale, centre x, centre y)"""
    s = base_scale(t); cx, cy = HX, HY
    if t > fill_end():
        s = s + (34 - s) * ease(ramp(t, sh.bs(5), wi(5, 9)))                   # lean in to see the clusters
        for (a, b, tgt) in ((wi(6, 8) - 0.3, wi(6, 9) + 0.4, 22), (wi(6, 11) - 0.3, wi(6, 15), 15), (wi(6, 17) - 0.3, wi(6, 23), 8.4)):
            s = s + (tgt - s) * ease(ramp(t, a, b))
        u = ease(ramp(t, wi(6, 17) - 0.3, wi(6, 23)))
        cx, cy = HX + (C4[0] - HX) * u, HY + (C4[1] - HY) * u
    return s, cx, cy

def prog(t):
    te = fill_end()
    if t >= te: return float(len(TILES))
    f = 0.93 + 0.14 * ease(ramp(t, te - 2.0, te))
    r = f * (FS / 2) / base_scale(t)
    k = bisect.bisect_right(DIST, r)
    pr = k - 1 + (r - DIST[k - 1]) / (DIST[k] - DIST[k - 1] + 1e-9) if 0 < k < len(DIST) else float(k)
    slow = 0.15 + 0.85 * (math.exp(t / 1.2) - 1) / (math.exp(1.9 / 1.2) - 1)
    return max(0.0, min(pr, slow, len(TILES) - 0.001))

def path(cr, pts):
    cr.move_to(*pts[0]); [cr.line_to(*q) for q in pts[1:]]; cr.close_path()

def draw(cr, t):
    s, ox, oy = camera(t)
    P = lambda q: (FX + (q[0] - ox) * s, FY - (q[1] - oy) * s)
    cr.save(); cr.rectangle(FX - FS / 2, FY - FS / 2, FS, FS); cr.clip()
    cr.set_source_rgb(0.985, 0.98, 0.955); cr.paint()
    pg = prog(t); k = int(pg); lw = max(1.2, 0.075 * s)
    # tiles fade a little once the ladder is shown, so the outlines read
    dim = 0.45 * ease(ramp(t, wi(6, 5) - 0.3, wi(6, 5) + 0.3)) if t > fill_end() else 0.0
    cr.set_line_width(lw)
    for i in range(k):
        path(cr, [P(q) for q in TILES[i][2]])
        c = COLS[i]; c = tuple(x + (0.985 - x) * dim for x in c)
        cr.set_source_rgb(*c); cr.fill_preserve(); cr.set_source_rgba(*EDGE, 1 - 0.6 * dim); cr.stroke()
    if k < len(TILES) and pg > 0:
        pts = [P(q) for q in TILES[k][2]]; pts.append(pts[0])
        L = (pg - k) * 13; m = int(L); u = L - m
        a, b = pts[m], pts[min(m + 1, 13)]; tip = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
        cr.move_to(*pts[0]); [cr.line_to(*q) for q in pts[1:m + 1]]; cr.line_to(*tip)
        cr.set_source_rgb(*EDGE); cr.stroke()
        cr.arc(tip[0] + 2, tip[1] + 3, 12, 0, 2 * math.pi); cr.set_source_rgba(0, 0, 0, 0.18); cr.fill()
        cr.arc(tip[0], tip[1], 11, 0, 2 * math.pi); cr.set_source_rgb(*PEN); cr.fill()
    if t > fill_end():
        # every cluster outlined
        a1 = ramp(t, wi(5, 9) - 0.2, wi(5, 9) + 0.5) * (1 - 0.6 * ramp(t, wi(6, 8), wi(6, 9)))
        if a1 > 0:
            cr.set_line_width(max(2.0, 0.16 * s)); cr.set_source_rgba(0.12, 0.16, 0.15, a1)
            for rings in L1_OUT:
                for r in rings: path(cr, [P(q) for q in r]); cr.stroke()
        # gold hats glow when the narration says so
        g = window(t, wi(5, 12) - 0.1, wi(5, 19) + 0.8, 0.3)
        if g > 0:
            cr.set_line_width(max(2.5, 0.2 * s)); cr.set_source_rgba(*PEN, g)
            for i in range(len(TILES)):
                if TILES[i][1] == 'H1': path(cr, [P(q) for q in TILES[i][2]]); cr.stroke()
        # the ladder: 4, 25, 169, 1156
        for lev, wk in ((1, 5), (2, 8), (3, 11), (4, 17)):
            a = ramp(t, wi(6, wk) - 0.15, wi(6, wk) + 0.4)
            if a <= 0: continue
            w = (3.5 + 1.6 * lev)
            for r in CH_OUT[lev]:
                pts = [P(q) for q in r]
                cr.set_line_width(w + 5); cr.set_source_rgba(1, 1, 1, 0.85 * a); path(cr, pts); cr.stroke()
                cr.set_line_width(w); cr.set_source_rgba(*LADDER[lev], a); path(cr, pts); cr.stroke()
    cr.restore()
    cr.rectangle(FX - FS / 2, FY - FS / 2, FS, FS); cr.set_line_width(3); cr.set_source_rgb(*INK); cr.stroke()

from mu_style import window

def label(t):
    n = int(prog(t)); k = FLIPC[n]
    if t < sh.bs(1) - 0.1: return 'tiles: %d' % n
    if t < sh.bs(3) - 0.1: return 'tiles: %d   flipped: %d' % (n, k)
    if t < sh.bs(4) - 0.1:
        if t < sh.wt(3, 'golden'): return 'normal : flipped = %.2f : 1' % ((n - k) / max(1, k))
        return 'golden ratio φ⁴ = 6.854…'
    if t < sh.bs(5) - 0.1: return 'David Smith  ·  2023'
    if t < sh.bs(6) - 0.1:
        return 'clusters of 1, 2 or 4 hats' if t < wi(5, 11) else 'every gold hat → a cluster of 4'
    if t < sh.bs(7) - 0.1:
        seq = ['4', '25', '169', '1156']; m = sum(t >= wi(6, w) - 0.1 for w in (5, 8, 11, 17))
        return '  →  '.join(seq[:max(1, m)]) + ' hats'
    if t < sh.bs(8) - 0.1:
        sq = ['2²', '5²', '13²', '34²']; m = sum(t >= wi(7, w) - 0.1 for w in (0, 2, 4, 6))
        if t < wi(7, 9) - 0.1: return '  ·  '.join(sq[:max(1, m)])
        return 'Fibonacci: 1 1 2 3 5 8 13 21 34'
    if t < sh.bs(9) - 0.1: return 'each step ×6.85 = φ⁴  ·  forever'
    return '1 shape  ·  an endless ladder'

sh = S.Short(B, 'One tile.', 'It never repeats.', draw, label=label,
             end_line='Tile your own: symmetryengine.space', end_from=None)

if __name__ == '__main__':
    sh.main()
