"""'5 shapes that refuse to tile your floor' - first Short in the countdown format (ideas/format-countdown-fights-back.md).

Facts (checked 1 Nov 2026):
  circles: densest packing is hexagonal, pi/(2*sqrt 3) = 90.69% covered, so ~9.3% bare.
  regular pentagon: interior angle 108 deg; 3 x 108 = 324, gap 36.
  regular octagon: 135 deg; 2 x 135 = 270, leaves a 90 deg (square) hole: the truncated square tiling 4.8.8.
  Penrose kite and dart (P2): aperiodic; built here by Robinson-triangle deflation (penrose_p2.py, verified).
  the hat: aperiodic monotile, Smith, Myers, Kaplan, Goodman-Strauss, March 2023; David Smith an amateur
  from Yorkshire. Geometry from Kaplan's hatviz (hat_tiling.py, verified: no overlaps, no gaps).
"""
import os, sys, math, json
os.environ.setdefault('MU_THEME', 'paper')
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import std_short as S
from std_short import INK, PAL, hue_at
from mu_style import W, ease, ramp, window, text, PINK, SUB
import cairo
import penrose_p2, hat_tiling

B = os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'build', 'refuse')
TAU = 2 * math.pi
FX, FY, FS = 540, 965, 860            # floor square centre and side
RED = (0.86, 0.16, 0.22); GOLD_ = (0.93, 0.66, 0.10)
CUT = 0.0

sh = None   # set below

def floor_clip(cr):
    r = 36
    x0, y0, x1, y1 = FX - FS / 2, FY - FS / 2, FX + FS / 2, FY + FS / 2
    cr.new_path()
    cr.arc(x1 - r, y0 + r, r, -math.pi / 2, 0); cr.arc(x1 - r, y1 - r, r, 0, math.pi / 2)
    cr.arc(x0 + r, y1 - r, r, math.pi / 2, math.pi); cr.arc(x0 + r, y0 + r, r, math.pi, 3 * math.pi / 2)
    cr.close_path()

def floor(cr, a, tint=(0.97, 0.965, 0.95)):
    floor_clip(cr); cr.set_source_rgba(*tint, a); cr.fill_preserve()
    cr.set_source_rgba(*INK, 0.25 * a); cr.set_line_width(3); cr.stroke()

def poly(cr, pts, fill, a, stroke=INK, lw=2.5, sa=0.85):
    cr.new_path(); cr.move_to(*pts[0])
    for p in pts[1:]: cr.line_to(*p)
    cr.close_path()
    if fill is not None: cr.set_source_rgba(*fill, a); cr.fill_preserve()
    cr.set_source_rgba(*stroke, sa * a); cr.set_line_width(lw); cr.stroke()

def soft(c, k=0.55): return tuple(1 - (1 - x) * k for x in c)

def badge(cr, n, a):
    text(cr, '#%d' % n, FX - FS / 2 + 70, FY - FS / 2 + 70, 74, col=PINK, alpha=a, shadow=False)

def ngon(cx, cy, R, n, rot):
    return [(cx + R * math.cos(rot + k * TAU / n), cy + R * math.sin(rot + k * TAU / n)) for k in range(n)]

# ------------------------------------------------------------------ #5 circles
RC = 52
CIRC = []
for j in range(-12, 13):
    for i in range(-12, 13):
        x = FX + (i + 0.5 * (j % 2)) * 2 * RC; y = FY + j * RC * math.sqrt(3)
        if abs(x - FX) < FS / 2 + RC and abs(y - FY) < FS / 2 + RC: CIRC.append((x, y))
CIRC.sort(key=lambda p: math.hypot(p[0] - FX, p[1] - FY))

def seg_circles(cr, t, a):
    t0, t1 = sh.bs(1) + 0.1, sh.wt(1, 'like')
    bare = ramp(t, sh.wt(1, 'stays') - 0.2, sh.wt(1, 'bare') + 0.2)
    floor(cr, a, tint=tuple(0.97 * (1 - bare) + c * bare for c in soft(RED, 0.35)))
    cr.save(); floor_clip(cr); cr.clip()
    n = len(CIRC)
    for k, (x, y) in enumerate(CIRC):
        ts = t0 + (t1 - t0) * k / n
        s = ease(min(1, max(0, (t - ts) / 0.25)))
        if s <= 0: continue
        col = soft(hue_at(0.55 + 0.25 * k / n), 0.5)
        cr.new_path(); cr.arc(x, y, RC * s - 1.5, 0, TAU); cr.set_source_rgba(*col, a); cr.fill_preserve()
        cr.set_source_rgba(*INK, 0.7 * a); cr.set_line_width(2.5); cr.stroke()
    cr.restore()
    badge(cr, 5, a)

# ------------------------------------------------------------------ #4 pentagon
PS = 250; PR = PS / (2 * math.sin(math.pi / 5)); PV = (FX, FY + 40)
def pentagon_at(theta):
    """regular pentagon with a corner at PV, its two edges at angles theta and theta+108 deg"""
    bis = theta + math.radians(54)
    cx, cy = PV[0] + PR * math.cos(bis), PV[1] + PR * math.sin(bis)
    ang0 = bis + math.pi
    return ngon(cx, cy, PR, 5, ang0)
BASE = math.radians(-90 + 18)

def seg_pentagon(cr, t, a):
    floor(cr, a)
    cr.save(); floor_clip(cr); cr.clip()
    t3 = sh.wt(2, 'three'); tg = sh.wt(2, 'thirty-six'); te = sh.wt(2, 'every')
    for k in range(3):
        st = sh.bs(2) + 0.1 if k == 0 else t3 - 0.2 + 0.35 * k
        s = ease(ramp(t, st, st + 0.4))
        if s <= 0: continue
        th = BASE + k * math.radians(108)
        pts = pentagon_at(th)
        pts = [(PV[0] + (x - PV[0]) * (0.6 + 0.4 * s), PV[1] + (y - PV[1]) * (0.6 + 0.4 * s)) for x, y in pts]
        poly(cr, pts, soft(PAL[(2 * k + 1) % 8], 0.45), a, lw=3)
    g = ramp(t, tg - 0.3, tg + 0.3)
    if g > 0:   # the 36 degree gap
        a0 = BASE + 3 * math.radians(108); a1 = BASE + TAU
        pul = 0.6 + 0.4 * math.sin(6 * t)
        cr.new_path(); cr.move_to(*PV); cr.arc(PV[0], PV[1], 380, a0, a1); cr.close_path()
        cr.set_source_rgba(*RED, 0.35 * g * pul * a); cr.fill()
        mid = (a0 + a1) / 2
        text(cr, '36°', PV[0] + 300 * math.cos(mid), PV[1] + 300 * math.sin(mid) + 16, 54, col=RED, alpha=g * a, shadow=False)
    # the fourth pentagon tries to squeeze in, and overlaps every time
    if t > te - 0.2:
        u = (t - (te - 0.2)) / 0.62
        k = int(u); f = u - k
        if k < 3:
            push = math.sin(math.pi * min(1, f))
            th = BASE + 3 * math.radians(108) - math.radians(36) * 0.5 + (k - 1) * math.radians(10)
            pts = pentagon_at(th)
            back = (1 - push) * 160
            dx, dy = math.cos(th + math.radians(54)) * back, math.sin(th + math.radians(54)) * back
            pts = [(x + dx, y + dy) for x, y in pts]
            poly(cr, pts, soft(RED, 0.5), a * 0.85, stroke=RED, lw=4, sa=1)
    cr.restore()
    badge(cr, 4, a)

# ------------------------------------------------------------------ #3 octagon
OA = 92; OSP = OA * (1 + math.sqrt(2)); ORAD = OA / (2 * math.sin(math.pi / 8))
OCT = []
for j in range(-4, 5):
    for i in range(-4, 5):
        x, y = FX + i * OSP, FY + j * OSP
        if abs(x - FX) < FS / 2 + OSP and abs(y - FY) < FS / 2 + OSP: OCT.append((x, y))
OCT.sort(key=lambda p: math.hypot(p[0] - FX, p[1] - FY))
SQ = [(x + OSP / 2, y + OSP / 2) for x, y in OCT]

def seg_octagon(cr, t, a):
    floor(cr, a)
    cr.save(); floor_clip(cr); cr.clip()
    t0 = sh.bs(3) + 0.3; tsq = sh.wt(3, 'square'); tc = sh.wt(3, 'cheat')
    hole = ramp(t, tsq - 0.3, tsq + 0.2); fill = ramp(t, tc - 0.1, tc + 0.6)
    if hole > 0:
        for (x, y) in SQ:
            q = OA / 2
            pts = [(x - q, y - q), (x + q, y - q), (x + q, y + q), (x - q, y + q)]
            if fill > 0: poly(cr, pts, soft(GOLD_, 0.6), a * fill, lw=3)
            else: poly(cr, pts, soft(RED, 0.4), a * hole * (0.6 + 0.4 * math.sin(7 * t)), stroke=RED, lw=3)
    n = len(OCT)
    for k, (x, y) in enumerate(OCT):
        s = ease(ramp(t, t0 - 0.2 + 1.3 * k / n, t0 + 0.1 + 1.3 * k / n))
        if s <= 0: continue
        poly(cr, ngon(x, y, ORAD * s, 8, math.pi / 8), soft(hue_at(0.6 + 0.2 * k / n), 0.45), a, lw=3)
    cr.restore()
    badge(cr, 3, a)

# ------------------------------------------------------------------ #2 Penrose kite and dart
PT = penrose_p2.tiles(5)
PSC = 395
PEN = [(kind, [(FX + PSC * z.real, FY + PSC * z.imag) for z in pts],
        math.hypot(sum(z.real for z in pts) / 4, sum(z.imag for z in pts) / 4) * PSC) for kind, pts in PT]

def one_tile(kind):
    for k, pts, r in PEN:
        if k == kind: return pts

def seg_penrose(cr, t, a):
    floor(cr, a)
    cr.save(); floor_clip(cr); cr.clip()
    tk = sh.wt(4, "penrose's"); tc = sh.wt(4, 'they'); tn = sh.wt(4, 'never')
    two = window(t, sh.bs(4) + 0.05, tc + 0.4, 0.3)
    if two > 0:   # one kite and one dart, big, side by side
        for kind, dx, col in (('kite', -190, PAL[5]), ('dart', 190, PAL[0])):
            pts = one_tile(kind)
            cx = sum(p[0] for p in pts) / 4; cy = sum(p[1] for p in pts) / 4
            big = [(FX + dx + (x - cx) * 3.2, FY + (y - cy) * 3.2) for x, y in pts]
            poly(cr, big, soft(col, 0.5), a * two, lw=4)
            text(cr, kind, FX + dx, FY + 300, 50, col=INK, alpha=a * two, shadow=False)
    grow = ramp(t, tc, tc + 1.8)
    if grow > 0:
        R = 40 + 640 * ease(grow)
        for kind, pts, r in PEN:
            if r > R: continue
            s = min(1, (R - r) / 60)
            col = soft(PAL[5] if kind == 'kite' else PAL[0], 0.45 + 0.1 * math.sin(r / 40 - 3 * t) * ramp(t, tn - 0.3, tn + 0.5))
            poly(cr, pts, col, a * s, lw=2)
    cr.restore()
    badge(cr, 2, a)

# ------------------------------------------------------------------ #1 the hat
HATS = hat_tiling.hats(4)
HCOL = {'H1': PINK, 'H': PAL[5], 'T': PAL[3], 'P': PAL[4], 'F': PAL[6]}
def hat_centroid(p): return (sum(x for x, _ in p) / len(p), sum(y for _, y in p) / len(p))
HAT_C = [(lab, p, hat_centroid(p)) for lab, p in HATS]
HAT_C.sort(key=lambda h: math.hypot(*h[2]))
FIRST = HAT_C[0]

def seg_hat(cr, t, a):
    floor(cr, a)
    cr.save(); floor_clip(cr); cr.clip()
    th = sh.wt(5, 'hat'); tcov = sh.wt(5, 'covers'); tn = sh.wt(5, 'never')
    zoom = ease(ramp(t, tcov - 0.4, tcov + 1.0))
    sc = 78 * (1 - zoom) + 24 * zoom
    cx0, cy0 = FIRST[2]
    def P(p): return (FX + (p[0] - cx0) * sc, FY - (p[1] - cy0) * sc)
    grow = ramp(t, tcov - 0.2, tcov + 2.2)
    R = 0.5 + 34 * ease(grow)
    for idx, (lab, p, c) in enumerate(HAT_C):
        r = math.hypot(c[0] - cx0, c[1] - cy0)
        first = idx == 0
        if r > R and not first: continue
        s = 1.0 if first else min(1, (R - r) / 2.5)
        col = soft(PINK, 0.75 - 0.15 * zoom) if first else soft(hue_at(0.58 + 0.12 * ((idx * 0.618) % 1)), 0.42)
        poly(cr, [P(q) for q in p], col, a * s * ramp(t, sh.bs(5), sh.bs(5) + 0.3), lw=2.2 if zoom > 0.5 else 5)
    cr.restore()
    badge(cr, 1, a)

# ------------------------------------------------------------------ frame 0: all five at once
def icon_hat(cx, cy, s, a):
    lab, p, c = FIRST
    poly(cr_g[0], [(cx + (q[0] - c[0]) * s, cy - (q[1] - c[1]) * s) for q in p], soft(PINK, 0.5), a, lw=3)
cr_g = [None]

def seg_intro(cr, t, a):
    cr_g[0] = cr
    text(cr, '5', FX, FY + 230, 640, col=PINK, alpha=0.13 * a, shadow=False)
    pops = [0.0, 0.0, 0.0, 0.0, 0.0] if t < 0.05 else [0, 0, 0, 0, 0]
    # row 1: circle, pentagon, octagon ; row 2: kite+dart, hat
    y1, y2 = FY - 170, FY + 190
    cr.new_path(); cr.arc(FX - 300, y1, 110, 0, TAU); cr.set_source_rgba(*soft(hue_at(0.6), 0.5), a); cr.fill_preserve()
    cr.set_source_rgba(*INK, 0.8 * a); cr.set_line_width(3); cr.stroke()
    poly(cr, ngon(FX, y1, 120, 5, -math.pi / 2), soft(PAL[1], 0.45), a, lw=3)
    poly(cr, ngon(FX + 300, y1, 120, 8, math.pi / 8), soft(PAL[4], 0.45), a, lw=3)
    for kind, dx, col in (('kite', -220, PAL[5]), ('dart', -70, PAL[0])):
        pts = one_tile(kind); cx = sum(p[0] for p in pts) / 4; cy = sum(p[1] for p in pts) / 4
        poly(cr, [(FX - 80 + dx + (x - cx) * 2.6, y2 + (y - cy) * 2.6) for x, y in pts], soft(col, 0.5), a, lw=3)
    icon_hat(FX + 230, y2, 52, a)

# ------------------------------------------------------------------ assemble
SEGS = None
def draw(cr, t):
    global SEGS
    if SEGS is None:
        SEGS = [(seg_intro, -9, sh.bs(1)), (seg_circles, sh.bs(1), sh.bs(2)), (seg_pentagon, sh.bs(2), sh.bs(3)),
                (seg_octagon, sh.bs(3), sh.bs(4)), (seg_penrose, sh.bs(4), sh.bs(5)), (seg_hat, sh.bs(5), 99)]
    for f, a, b in SEGS:
        al = window(t, a - 0.15, b + 0.05, 0.25) if a > 0 else (1 - ramp(t, b - 0.2, b + 0.05))
        if al > 0: f(cr, t, al)

def label(t):
    b = sh.bs
    if t < b(1) - 0.1: return None
    if t < b(2) - 0.1:
        t0, t1 = sh.bs(1) + 0.1, sh.wt(1, 'like')
        cov = 90.7 * min(1, max(0, (t - t0) / (t1 - t0 + 0.6)))
        return 'covered: %.1f%%' % cov if t < sh.wt(1, 'stays') else 'best possible: 90.7%  ·  9.3% bare'
    if t < b(3) - 0.1:
        if t < sh.wt(2, 'that'): return '3 × 108° = 324°'
        if t < sh.wt(2, 'every'): return '360° − 324° = 36° gap'
        k = min(3, 1 + int((t - (sh.wt(2, 'every') - 0.2)) / 0.62))
        return 'tries: %d   ✗' % k
    if t < b(4) - 0.1:
        return '2 × 135° = 270°  →  90° hole' if t < sh.wt(3, 'cheat') else '+ squares (cheating)'
    if t < b(5) - 0.1:
        return '2 tiles  ·  forever  ·  never repeats' if t > sh.wt(4, 'they') else 'kite + dart (1974)'
    if t < sh.wt(5, 'found'): return '1 tile'
    if t < sh.wt(5, 'covers'): return 'David Smith  ·  2023'
    return '1 tile  ·  never repeats'

sh = S.Short(B, '5 shapes that refuse', 'to tile your floor', draw, label=label,
             end_line='Tile your own: symmetryengine.space', end_from=None)

if __name__ == '__main__':
    sh.main()
