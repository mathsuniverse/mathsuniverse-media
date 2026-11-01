"""'One tile. It never repeats.' A pen draws the hat tiling tile by tile from the centre outwards, square frontier so the floor fills (satisfying-maths Short).

Facts (checked 1 Nov 2026):
  the hat: aperiodic monotile, Smith, Myers, Kaplan, Goodman-Strauss (2023); David Smith an amateur from Yorkshire.
  geometry: hat_tiling.py (port of Kaplan's hatviz, BSD-3), verified no overlaps / no gaps.
  frequencies: unreflected : reflected -> phi^4 = 6.854 (substitution eigenvector; measured 6.8543 on level 5).
  The on-screen ratio is the live count in the drawn square (edge effects), so the narration says "about".
"""
import os, sys, math, bisect
os.environ.setdefault('MU_THEME', 'paper')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import std_short as S
from std_short import INK
from mu_style import PINK, ramp, ease
import hat_tiling

B = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build', 'penfill')
FX, FY, FS = 540, 965, 860
PHI = (1 + 5 ** .5) / 2

hs = hat_tiling.hats(5)
def cen(p): return (sum(q[0] for q in p) / 13, sum(q[1] for q in p) / 13)
cs = [cen(p) for _, p in hs]
CX = sum(x for x, _ in cs) / len(cs); CY = sum(y for _, y in cs) / len(cs)
TILES = sorted(((max(abs(x - CX), abs(y - CY)), l, p) for (l, p), (x, y) in zip(hs, cs)), key=lambda z: z[0])
TILES = [z for z in TILES if z[0] < 40]
_f = next(i for i, z in enumerate(TILES) if z[1] != 'H1')        # open on a normal (green) hat
TILES.insert(0, TILES.pop(_f)); TILES[0] = (0.0,) + TILES[0][1:]
HX, HY = cen(TILES[0][2])
DIST = [z[0] for z in TILES]
FLIPC = [0]
for z in TILES: FLIPC.append(FLIPC[-1] + (z[1] == 'H1'))
BLUES = [(0.60, 0.79, 0.62), (0.47, 0.70, 0.55), (0.73, 0.86, 0.71)]   # sage greens
FLIP = (0.97, 0.76, 0.40)                                            # warm gold = flipped
EDGE = (0.20, 0.27, 0.25); PEN = (0.88, 0.40, 0.30)
def shade(p):
    a = math.degrees(math.atan2(p[1][1] - p[0][1], p[1][0] - p[0][0])) % 360
    return BLUES[int(round(a / 60)) % 3]
COLS = [FLIP if l == 'H1' else shade(p) for _, l, p in TILES]

T_END = 31.0
def scale(t):                      # opens zoomed in on the single hat, then pulls back
    base = 70 * (14 / 70) ** (min(t, T_END) / T_END)
    z = 1 - ease(ramp(t, 1.9, 4.2))
    return base * (240 / 70) ** z
def frac(t): return 0.93 + 0.14 * ease(ramp(t, 29.0, 31.0))
def prog(t):
    r = frac(t) * (FS / 2) / scale(t)
    k = bisect.bisect_right(DIST, r)
    if 0 < k < len(DIST): pr = k - 1 + (r - DIST[k - 1]) / (DIST[k] - DIST[k - 1] + 1e-9)
    else: pr = float(k)
    slow = 0.15 + 0.85 * (math.exp(t / 1.2) - 1) / (math.exp(1.9 / 1.2) - 1)
    return max(0.0, min(pr, slow, len(TILES) - 0.001))

def draw(cr, t):
    s = scale(t); z = 1 - ease(ramp(t, 1.9, 4.2))
    ox, oy = CX + (HX - CX) * z, CY + (HY - CY) * z          # camera starts on the first hat
    P = lambda q: (FX + (q[0] - ox) * s, FY - (q[1] - oy) * s)
    cr.save(); cr.rectangle(FX - FS / 2, FY - FS / 2, FS, FS); cr.clip()
    cr.set_source_rgb(0.985, 0.98, 0.955); cr.paint()
    pg = prog(t); k = int(pg); lw = max(1.3, 0.075 * s)
    cr.set_line_width(lw)
    for i in range(k):
        pts = [P(q) for q in TILES[i][2]]
        cr.move_to(*pts[0]); [cr.line_to(*q) for q in pts[1:]]; cr.close_path()
        cr.set_source_rgb(*COLS[i]); cr.fill_preserve(); cr.set_source_rgb(*EDGE); cr.stroke()
    if k < len(TILES) and pg > 0:
        pts = [P(q) for q in TILES[k][2]]; pts.append(pts[0])
        L = (pg - k) * 13; m = int(L); u = L - m
        a, b = pts[m], pts[min(m + 1, 13)]; tip = (a[0] + (b[0] - a[0]) * u, a[1] + (b[1] - a[1]) * u)
        cr.move_to(*pts[0]); [cr.line_to(*q) for q in pts[1:m + 1]]; cr.line_to(*tip)
        cr.set_source_rgb(*EDGE); cr.stroke()
        cr.arc(tip[0] + 2, tip[1] + 3, 12, 0, 2 * math.pi); cr.set_source_rgba(0, 0, 0, 0.18); cr.fill()
        cr.arc(tip[0], tip[1], 11, 0, 2 * math.pi); cr.set_source_rgb(*PEN); cr.fill()
    cr.restore()
    cr.rectangle(FX - FS / 2, FY - FS / 2, FS, FS); cr.set_line_width(3); cr.set_source_rgb(*INK); cr.stroke()

def label(t):
    n = int(prog(t)); k = FLIPC[n]
    if t < sh.bs(1) - 0.1: return 'tiles: %d' % n
    if t < sh.bs(3) - 0.1: return 'tiles: %d   flipped: %d' % (n, k)
    if t < sh.bs(4) - 0.1:
        if t < sh.wt(3, 'golden'): return 'normal : flipped = %.2f : 1' % ((n - k) / max(1, k))
        return 'golden ratio φ⁴ = 6.854…'
    if t < sh.bs(5) - 0.1: return 'David Smith  ·  2023'
    return '%d tiles  ·  1 shape  ·  never repeats' % n

sh = S.Short(B, 'One tile.', 'It never repeats.', draw, label=label,
             end_line='Tile your own: symmetryengine.space', end_from=None)

if __name__ == '__main__':
    sh.main()
