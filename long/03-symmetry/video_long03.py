"""Long video 03 — Symmetry in nature: how breaking it made the universe, and you.

The narration is the clock: every scene is pinned to a phrase in build/long03/beats.json.

    MU_FORMAT=long MU_THEME=night python3 video_long03.py [t0 dur out.mp4]
    python3 video_long03.py --check       # list every cue and whether it was found
    python3 video_long03.py --stills t1 t2 ...   # write PNG stills to build/long03/stills

Simulations (Turing pattern, early-universe field, cosmic web) come from prep_long03.py.
"""
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('MU_FORMAT', 'long')
os.environ.setdefault('MU_THEME', 'night')

import numpy as np
import cairo
from mu_style import *
from formula import cue, cite, note_card, chapter_card
from scenes_ladder import clip_picture, unclip

HERE = os.path.dirname(os.path.abspath(__file__))
BUILD = os.path.join(HERE, '..', 'build', 'long03')
BEATS = json.load(open(os.path.join(BUILD, 'beats.json')))
SIMS = np.load(os.path.join(BUILD, 'sims.npz'))
VOICE_END = BEATS[-1]['end']
DUR = VOICE_END + 15.0
TAU = 2 * math.pi

# ------------------------------------------------------------------ timing
def chapter_spans():
    out, cur, start = [], None, 0.0
    for b in BEATS:
        c = tuple(b['chapter']) if b['chapter'] else None
        if c != cur:
            if cur is not None:
                out.append((start, b['start'], cur))
            cur, start = c, b['start']
    out.append((start, DUR, cur))
    return out

CH = chapter_spans()
S = {c[0]: (a, b) for a, b, c in CH if c}

_MISSING = []
def at(phrase, default=None, nth=1):
    t = cue(BEATS, phrase, nth=nth)
    if t is None:
        _MISSING.append(phrase)
        return default
    return t

def ease_(u):
    u = max(0.0, min(1.0, u)); return u * u * (3 - 2 * u)

def rp(t, a, b):
    return ease_((t - a) / (b - a)) if b > a else float(t >= a)

def fade(t, a, b, up=0.6, down=0.6):
    if t < a or t > b: return 0.0
    return min(ease_((t - a) / up), ease_((b - t) / down), 1.0)

T = {
    # 0 hook
    'turn6': at('Turn it by a sixth'), 'flip0': at('Flip it over'), 'you': at('Here is you'),
    'heart0': at('Your heart sits'), 'face0': at('Your face is'), 'twist0': at('the molecules in your body'),
    'strange': at('Here is the strange part'), 'nothing0': at('Nothing at all'), 'broke0': at('a perfect symmetry broke'),
    'today0': at('Today we follow'), 'five0': at('Five breaks'),
    # 1 what symmetry is
    'answer': at('A symmetry is something'), 'square': at('Take a square'), 'quarter': at('Turn it a quarter turn'),
    'diag': at('Flip it across a diagonal'), 'eight': at('you find eight'), 'circle': at('A circle has infinitely'),
    'three': at('Three kinds of move'), 'refl': at('Reflection, a mirror'), 'rot': at('Rotation, a turn'),
    'trans': at('And translation'), 'notice': at('Notice something'), 'blank': at('A blank circle'),
    'key': at('It is the key'),
    # 2 nature
    'nature': at('Nature is full of it'), 'lattice': at('hexagonal lattice'), 'grow': at('all six arms grow'),
    'starfish': at('A starfish has'), 'larva': at('as a larva'), 'daisy': at('A daisy'), 'orange': at('an orange cut in half'),
    'animal': at('look at almost any animal'), 'mirrorline': at('One mirror line'), 'bilat': at('Biologists call it'),
    'why': at('Why is nature so symmetric'), 'curie': at('Pierre Curie'), 'lopsided': at('So if something is lopsided'),
    'realq': at('Which raises the real question'),
    # 3 noether
    'noether': at('Emmy Noether'), 'exp': at('Do an experiment today'), 'tomorrow': at('the same experiment tomorrow'),
    'energy': at('why energy is conserved'), 'slide': at('Slide the experiment'), 'momentum': at('why momentum is conserved'),
    'turnexp': at('Turn it to face another way'), 'angular': at('why angular momentum'), 'every_sym': at('Every symmetry of the laws'),
    'deepest': at('It is the deepest rule'), 'dull': at('would be very dull'),
    # 4 antimatter
    'b1': at('Break one happened'), 'pairs': at('in pairs'), 'vanish': at('both vanish into light'),
    'perfect_deal': at('If the deal had been perfect'), 'onlylight': at('nothing but light'),
    'notperfect': at("It wasn't perfect"), 'billion': at('For roughly every billion'), 'annih': at('The billions annihilated'),
    'survived': at('The extra one survived'), 'galaxy': at('Every galaxy'), 'kaons': at('in 1964'), 'openq1': at('Exactly how the universe'),
    # 5 lumpy
    'b2': at('Break two'), 'oldest': at('the oldest light'), 'smooth': at('almost perfectly smooth'), 'almost': at('Almost. The differences', None) or at('The differences are'),
    'ripples': at('like ripples'), 'gravity': at('Gravity loves a lump'), 'billions_y': at('Over billions of years'),
    'staysmooth': at('A perfectly smooth universe'),
    # 6 hands
    'b3': at('Break three'), 'hands': at('Hold up your hands'), 'molecules': at('Many molecules are like that'),
    'pasteur': at('Louis Pasteur'), 'tweezers': at('with tweezers'), 'dissolved': at('Dissolved in water'),
    'ordinary': at('Ordinary chemistry'), 'lifenot': at('Life does not'), 'amino': at('Almost every amino acid'),
    'sugars': at('The sugars in your DNA'), 'helix': at('the double helix twists'), 'chose': at('Life chose one hand'),
    'shake': at('like trying to shake'),
    # 7 body
    'b4': at('Break four'), 'cell': at('a single cell'), 'ballsame': at('A ball looks the same'),
    'turing': at('Alan Turing'), 'evenmix': at('an even mix of chemicals'), 'spots': at('spots and stripes'),
    'amplified': at('get amplified'), 'layout': at('lay out a body'), 'headtail': at('head and tail'),
    'backbelly': at('back and belly'), 'mya': at('five hundred and fifty-five million'), 'tracks': at('left their tracks'),
    'mirrorplan': at('A front, a back'), 'toyou': at('leads all the way to you'),
    # 8 heart
    'notquite': at('But you are not quite'), 'heartleft': at('Your heart is on the left'), 'node': at('called the node'),
    'spin': at('They all spin clockwise'), 'pushleft': at('push the fluid towards the left'), 'filmed': at('Japanese scientists'),
    'current': at('That gentle current'), 'knows': at('knows its left from its right'), 'wrong': at('the flow goes wrong'),
    'mirrored': at('organs mirrored'), 'tenk': at('one person in ten thousand'),
    # 9 chain
    'chain': at('So here is the chain'), 'c_laws': at('The laws of physics are symmetric', nth=1),
    'c_matter': at('Matter beat antimatter'), 'c_lumpy': at('got lumpy'), 'c_hand': at('Life picked a hand'),
    'c_cell': at('A round cell picked'), 'c_heart': at('a whirl of cilia'), 'rules': at('Symmetry gives the world'),
    'stories': at('Breaking it gives'), 'made5': at('You are made of five'),
    # 10 your turn
    'yourturn': at('Now it is your turn'), 'which': at('Which one tells you more'), 'engine': at('Symmetry Engine'),
    'breakrule': at('then break one rule'), 'playlist': at('The symmetry playlist'), 'comments': at('Tell me in the comments'),
}
for k, v in list(T.items()):
    if v is None:
        T[k] = None

def tt(k, d=0.0):
    v = T.get(k)
    return v if v is not None else d

# ------------------------------------------------------------------ drawing helpers
def snowflake(c, cx, cy, r, rot=0.0, flipx=1.0, alpha=1.0, grow=1.0, width=4.0, odd=0.0, mark=False, hue0=0.55):
    """Six-armed dendrite. grow 0..1 grows the arms; odd>0 makes arm 0 different (a broken symmetry)."""
    if alpha <= 0 or grow <= 0: return
    c.save(); c.translate(cx, cy); c.scale(flipx, 1.0); c.rotate(rot)
    for k in range(6):
        c.save(); c.rotate(k * TAU / 6 - math.pi / 2)
        L = r * grow * (1 + (0.35 * odd if k == 0 else 0))
        col = hue(hue0 + 0.07 * math.sin(k * 1.0), 0.55)
        c.set_source_rgba(*col, 0.95 * alpha); c.set_line_width(width)
        c.move_to(0, 0); c.line_to(L, 0); c.stroke()
        for j, f in enumerate((0.30, 0.48, 0.64, 0.78, 0.9)):
            if f > grow * (1.0 + (0.35 * odd if k == 0 else 0)) / max(grow, 1e-6) * grow / max(grow, 1e-6) and False: pass
            x = r * f * grow
            bl = r * (0.26 - 0.2 * f) * grow * (1 + (1.2 * odd if k == 0 and j == 1 else 0))
            c.set_line_width(width * 0.75)
            for s in (1, -1):
                if k == 0 and odd > 0 and s == -1 and j in (2, 3): continue
                c.move_to(x, 0); c.line_to(x + bl * 0.5, s * bl * 0.866); c.stroke()
        c.restore()
    c.set_source_rgba(*hue(hue0, 0.4), 0.9 * alpha); c.arc(0, 0, width * 2.2, 0, TAU); c.fill()
    if mark:
        c.set_source_rgba(*GOLD, alpha); c.arc(0, -r * grow, 11, 0, TAU); c.fill()
    c.restore()

def heart_shape(c, x, y, s):
    c.save(); c.translate(x, y); c.scale(s, s)
    c.move_to(0, 0.35); c.curve_to(-1.1, -0.35, -0.45, -1.1, 0, -0.45)
    c.curve_to(0.45, -1.1, 1.1, -0.35, 0, 0.35); c.close_path(); c.restore()

def figure(c, cx, cy, s=1.0, alpha=1.0, heart_x=None, liver=False, col=None, mirror_line=0.0, label_back=False):
    """A simple human outline, SEEN FROM BEHIND, so its left is the viewer's left.
    heart_x: horizontal offset of the heart (negative = the person's left)."""
    if alpha <= 0: return
    col = col or hue(0.58, 0.45)
    c.save(); c.translate(cx, cy); c.scale(s, s)
    c.set_line_width(5); c.set_source_rgba(*col, 0.9 * alpha)
    c.new_path(); c.arc(0, -300, 62, 0, TAU); c.stroke()
    # torso
    c.move_to(-110, -220); c.curve_to(-150, -60, -120, 60, -95, 150); c.line_to(95, 150)
    c.curve_to(120, 60, 150, -60, 110, -220); c.close_path(); c.stroke()
    # arms and legs
    for sx in (1, -1):
        c.move_to(sx * 112, -210); c.curve_to(sx * 175, -120, sx * 190, 0, sx * 185, 110); c.stroke()
        c.move_to(sx * 55, 150); c.line_to(sx * 75, 360); c.stroke()
    if mirror_line > 0:
        c.set_dash([14, 12]); c.set_source_rgba(*SUB, 0.8 * alpha * mirror_line); c.set_line_width(3)
        c.move_to(0, -400); c.line_to(0, 400); c.stroke(); c.set_dash([])
    if heart_x is not None:
        heart_shape(c, heart_x, -95, 34); c.set_source_rgba(*PINK, alpha); c.fill()
    if liver:
        c.save(); c.translate(62 if (heart_x is None or heart_x < 0) else -62, 0); c.scale(1.5, 0.75)
        c.arc(0, 0, 32, 0, TAU); c.restore(); c.set_source_rgba(*GOLD, 0.8 * alpha); c.fill()
    c.restore()

def dots_ring(c, cx, cy, r, n, col, alpha, size=6, rot=0.0):
    for k in range(n):
        a = rot + k * TAU / n
        c.set_source_rgba(*col, alpha); c.arc(cx + r * math.cos(a), cy + r * math.sin(a), size, 0, TAU); c.fill()

def motif(c, x, y, s, rot=0.0, flip=1.0, col=None, alpha=1.0):
    """An asymmetric 'flag' shape, so reflections and rotations are visible."""
    col = col or GOLD
    c.save(); c.translate(x, y); c.rotate(rot); c.scale(flip * s, s)
    c.move_to(-0.5, 0.9); c.line_to(-0.5, -0.9); c.line_to(0.6, -0.55); c.line_to(-0.5, -0.15)
    c.set_line_width(0.12); c.set_source_rgba(*col, alpha); c.stroke()
    c.arc(-0.5, 0.9, 0.12, 0, TAU); c.fill()
    c.restore()

def image_disc(cr, arr, cx, cy, r, alpha, cmap):
    """Paint a 2D array (values -1..1) as a disc using cmap(v)->(r,g,b) arrays."""
    if alpha <= 0: return
    h, w = arr.shape
    rgb = cmap(arr)
    a8 = np.zeros((h, w, 4), np.uint8)
    a8[..., 2] = (rgb[0] * 255).clip(0, 255); a8[..., 1] = (rgb[1] * 255).clip(0, 255); a8[..., 0] = (rgb[2] * 255).clip(0, 255)
    a8[..., 3] = 255
    surf = cairo.ImageSurface.create_for_data(bytearray(a8.tobytes()), cairo.FORMAT_ARGB32, w, h, w * 4)
    cr.save(); cr.new_path(); cr.arc(cx, cy, r, 0, TAU); cr.clip()
    cr.translate(cx - r, cy - r); cr.scale(2 * r / w, 2 * r / h)
    pat = cairo.SurfacePattern(surf); pat.set_filter(cairo.FILTER_BILINEAR)
    cr.set_source(pat); cr.paint_with_alpha(alpha); cr.restore()

def cmb_cmap(v):
    v = np.clip(v, -1, 1)
    r = 0.5 + 0.5 * np.clip(v * 1.4, -1, 1); b = 0.5 - 0.5 * np.clip(v * 1.4, -1, 1)
    g = 0.25 + 0.45 * (1 - np.abs(v))
    return (r * 0.95, g * 0.8, b)

def turing_cmap(v):
    return (0.15 + 0.85 * v, 0.10 + 0.55 * v, 0.35 + 0.45 * (1 - v) * 0.6 + 0.3 * v)

def tetra_molecule(c, cx, cy, s, rot, mirror, alpha, highlight=0.0):
    """A carbon with four different neighbours, drawn in 3D and slowly turning. mirror=-1 gives the other hand."""
    if alpha <= 0: return
    V = np.array([[0, 1, 0], [0.943, -0.333, 0], [-0.471, -0.333, 0.816], [-0.471, -0.333, -0.816]])
    V[:, 0] *= mirror
    P = rot3(V, ax=0.35, ay=rot)
    cols = [GOLD, PINK, CYAN, GREEN]
    order = np.argsort(P[:, 2])
    for i in order:
        x, y, z = P[i]
        c.set_line_width(6); c.set_source_rgba(*SUB, 0.7 * alpha)
        c.move_to(cx, cy); c.line_to(cx + s * x, cy - s * y); c.stroke()
    c.set_source_rgba(*TEXT, 0.9 * alpha); c.arc(cx, cy, s * 0.16, 0, TAU); c.fill()
    for i in order:
        x, y, z = P[i]
        c.set_source_rgba(*cols[i], alpha * (0.55 + 0.45 * (z + 1) / 2)); c.arc(cx + s * x, cy - s * y, s * (0.19 + 0.04 * z), 0, TAU); c.fill()

def helix(c, cx, cy, h, r, phase, alpha, turns=2.5, right=True):
    """A right-handed double helix, turning about the vertical axis."""
    if alpha <= 0: return
    n = 260
    for strand, col in ((0, CYAN), (math.pi, PINK)):
        pts = []
        for i in range(n + 1):
            u = i / n
            a = (TAU * turns * u) * (1 if right else -1) + phase + strand
            pts.append((cx + r * math.cos(a), cy + h / 2 - h * u, math.sin(a)))
        for i in range(n):
            x0, y0, z0 = pts[i]; x1, y1, z1 = pts[i + 1]
            c.set_line_width(5 + 3 * (z0 + 1) / 2)
            c.set_source_rgba(*col, alpha * (0.35 + 0.65 * (z0 + 1) / 2))
            c.move_to(x0, y0); c.line_to(x1, y1); c.stroke()
    for i in range(0, n, 11):
        u = i / n
        a = (TAU * turns * u) * (1 if right else -1) + phase
        y = cy + h / 2 - h * u
        z = math.sin(a)
        c.set_line_width(3); c.set_source_rgba(*GOLD, alpha * 0.25 * (1 + 0.6 * z))
        c.move_to(cx + r * math.cos(a), y); c.line_to(cx + r * math.cos(a + math.pi), y); c.stroke()

def hand(c, cx, cy, s, flip, alpha, col):
    """A simple left hand (flip=1) or right hand (flip=-1), palm facing us."""
    if alpha <= 0: return
    c.save(); c.translate(cx, cy); c.scale(flip * s, s)
    c.set_line_width(5 / s); c.set_source_rgba(*col, alpha)
    # palm
    c.move_to(-60, 120); c.curve_to(-75, 40, -70, -20, -62, -40); c.line_to(62, -40); c.curve_to(70, 10, 70, 80, 50, 120)
    c.close_path(); c.stroke()
    for i, (x, L) in enumerate(((-46, 95), (-15, 120), (16, 112), (45, 85))):
        c.move_to(x - 13, -40); c.line_to(x - 13, -40 - L); c.arc(x, -40 - L, 13, math.pi, TAU); c.line_to(x + 13, -40); c.stroke()
    # thumb on the right of the palm for a left hand seen from the palm side
    c.move_to(62, 30); c.curve_to(110, 10, 140, -40, 125, -60); c.curve_to(110, -70, 95, -40, 66, -20); c.stroke()
    c.restore()

def crystal(c, x, y, s, hand_, alpha, col):
    """Pasteur's tartrate crystal, idealised: a hexagonal outline with one extra facet on one side."""
    c.save(); c.translate(x, y); c.scale(hand_ * s, s)
    pts = [(-0.6, -1), (0.6, -1), (1, 0), (0.6, 1), (-0.6, 1), (-1, 0)]
    c.move_to(*pts[0])
    for p in pts[1:]: c.line_to(*p)
    c.close_path()
    c.set_line_width(0.07); c.set_source_rgba(*col, alpha); c.stroke()
    c.move_to(0.6, -1); c.line_to(0.35, -0.55); c.line_to(1, 0); c.stroke()     # the tell-tale facet
    c.move_to(0.35, -0.55); c.line_to(-0.6, -1); c.stroke()
    c.restore()

def worm(c, x, y, s, alpha, wig):
    if alpha <= 0: return
    n = 12
    for i in range(n):
        u = i / (n - 1)
        px = x - s * 1.6 * u; py = y + s * 0.12 * math.sin(wig - 3 * u)
        rr = s * (0.16 - 0.06 * abs(u - 0.3))
        c.set_source_rgba(*hue(0.12 + 0.05 * u, 0.6), alpha * 0.35); c.arc(px, py, rr * 0.8, 0, TAU); c.fill()
        c.set_line_width(3); c.set_source_rgba(*hue(0.12 + 0.05 * u, 0.7), alpha * 0.9); c.arc(px, py, rr * 0.8, 0, TAU); c.stroke()
    # mirror line along the body
    c.set_dash([8, 8]); c.set_line_width(2); c.set_source_rgba(*SUB, 0.7 * alpha)
    c.move_to(x + s * 0.25, y); c.line_to(x - s * 1.85, y); c.stroke(); c.set_dash([])

def galaxy(c, cx, cy, r, alpha, rot=0.0, n=900, seed=3):
    if alpha <= 0: return
    rng = np.random.default_rng(seed)
    u = rng.random(n); arm = rng.integers(0, 2, n); jit = rng.normal(0, 0.12, n)
    rr = r * u ** 0.7
    th = rot + arm * math.pi + 3.2 * np.log1p(4 * u) + jit
    for x, y, q in zip(cx + rr * np.cos(th), cy + 0.55 * rr * np.sin(th), u):
        c.set_source_rgba(*hue(0.6 - 0.45 * q, 0.5), alpha * (0.9 - 0.5 * q)); c.arc(x, y, 2.2, 0, TAU); c.fill()
    c.set_source_rgba(*GOLD, alpha); c.arc(cx, cy, 10, 0, TAU); c.fill()

def big_label(c, s, x, y, size, col, alpha):
    if alpha > 0:
        text(c, s, x, y, size, col=col, alpha=alpha, shadow=True)

# ------------------------------------------------------------------ the picture, chapter by chapter
def art(t, cr, lc):
    clip_picture(lc)
    try:
        _art(t, cr, lc)
    finally:
        unclip(lc)

def _art(t, cr, lc):
    ch = max(k for k, (a, b) in S.items() if t >= a - 0.001) if t >= 0 else 0
    a0, a1 = S[ch]
    inn = rp(t, a0 - 0.2, a0 + 0.8) * (1 - rp(t, a1 - 0.7, a1 + 0.1))
    globals()['_scene_%d' % ch](t, cr, lc, inn)

# 0 — hook ---------------------------------------------------------------------------------------
def _scene_0(t, cr, lc, inn):
    a_flake = (1 - rp(t, tt('you') - 0.6, tt('you') + 0.2)) * inn
    rot = (math.pi / 3) * rp(t, tt('turn6') + 0.6, tt('turn6') + 2.6)
    flip = math.cos(math.pi * rp(t, tt('flip0') + 0.4, tt('flip0') + 2.6))
    snowflake(lc, CX, CY, 330, rot=rot, flipx=flip, alpha=a_flake, width=6, mark=True)
    a_you = fade(t, tt('you') - 0.2, tt('strange') + 3.0, 0.8, 1.2) * inn
    figure(lc, CX, CY + 40, 1.0, a_you, heart_x=-45 if t > tt('heart0') else None,
           mirror_line=rp(t, tt('face0'), tt('face0') + 1))
    if t > tt('twist0') and a_you > 0:
        helix(lc, CX + 300, CY + 10, 300, 40, t * 1.4, a_you * rp(t, tt('twist0'), tt('twist0') + 1))
    if t > tt('heart0') and a_you > 0:
        text(cr, 'seen from behind', CX, CY + 440, 32, weight=cairo.FONT_WEIGHT_NORMAL, slant=cairo.FONT_SLANT_ITALIC,
             col=SUB, alpha=a_you, shadow=False)
    # the strange part: everything dissolves into light
    gone = rp(t, tt('strange') + 3.0, tt('nothing0') + 0.5)
    back = rp(t, tt('broke0') - 0.5, tt('broke0') + 1.5)
    if gone > 0 and back < 1:
        rng = np.random.default_rng(7)
        pts = rng.uniform(-1, 1, (900, 2))
        for (x, y) in pts:
            lc.set_source_rgba(*WHITE, 0.25 * gone * (1 - back)); lc.arc(CX + 400 * x, CY + 400 * y, 2.0, 0, TAU); lc.fill()
    if back > 0:
        # the five breaks, as five lights along a line
        labels = ['matter', 'stars', 'a hand', 'a body', 'a heart']
        for i, lab in enumerate(labels):
            u = rp(t, tt('today0') + 1.2 * i, tt('today0') + 1.2 * i + 0.8) * back * inn
            y = CY - 320 + 160 * i
            lc.set_source_rgba(*hue(0.08 + 0.17 * i, 0.7), u); lc.arc(CX - 200, y, 22, 0, TAU); lc.fill()
            text(cr, lab, CX + 40, y + 14, 46, col=TEXT, alpha=u, shadow=False)
        if back * inn > 0:
            lc.set_line_width(3); lc.set_source_rgba(*SUB, 0.5 * back * inn)
            lc.move_to(CX - 200, CY - 320); lc.line_to(CX - 200, CY + 320); lc.stroke()

# 1 — what symmetry is ---------------------------------------------------------------------------
def _scene_1(t, cr, lc, inn):
    ans = fade(t, S[1][0] - 0.2, tt('square') + 0.2)
    if ans > 0:
        ph = (t - S[1][0]) % 4.0
        rot = (math.pi / 3) * rp(ph, 1.0, 2.2)
        snowflake(lc, CX, CY - 40, 260, rot=rot, alpha=ans * inn, width=5, mark=True)
        if t > tt('answer'):
            text(cr, 'move it  →  it looks the same', CX, CY + 360, 42, col=TEXT, alpha=ans * rp(t, tt('answer'), tt('answer') + 1), shadow=False)
    # the square and its eight moves
    sq_on = fade(t, tt('square') - 0.3, tt('circle') + 0.2, 0.6, 0.6)
    if sq_on > 0:
        moves = [(0, 1)] + [(k * math.pi / 2, 1) for k in (1, 2, 3)] + [(k * math.pi / 2, -1) for k in (0, 1, 2, 3)]
        t_q, t_d, t_e = tt('quarter'), tt('diag'), tt('eight')
        if t < t_d:
            ang, fl = math.pi / 2 * rp(t, t_q + 0.8, t_q + 2.2), 1.0
            k = 1 if t > t_q + 2.2 else 0
        elif t < t_e:
            ang, fl = math.pi / 2, math.cos(math.pi * rp(t, t_d + 0.6, t_d + 2.2))
            k = 2 if t > t_d + 2.2 else 1
        else:
            j = min(7, int((t - t_e) / 0.5))
            ang, fl = moves[j][0], moves[j][1]
            k = j + 1 if j >= 2 else 2
            k = max(k, min(8, 2 + int((t - t_e) / 0.5)))
        lc.save(); lc.translate(CX, CY - 30); lc.rotate(ang); lc.scale(fl, 1)
        lc.set_line_width(6); lc.set_source_rgba(*CYAN, 0.9 * sq_on)
        lc.rectangle(-190, -190, 380, 380); lc.stroke()
        for i, (x, y) in enumerate(((-190, -190), (190, -190), (190, 190), (-190, 190))):
            lc.set_source_rgba(*hue(i / 4 + 0.05, 0.7), sq_on); lc.arc(x, y, 16, 0, TAU); lc.fill()
        lc.restore()
        if t > t_q:
            text(cr, 'moves that work:  %d' % (k if t > t_e else (1 if t < t_d + 2.2 else 2)), CX, CY + 330, 52,
                 font='JetBrains Mono', col=TEXT, alpha=sq_on, shadow=False)
    ci = fade(t, tt('circle') - 0.2, tt('three') + 0.2)
    if ci > 0:
        lc.set_line_width(6); lc.set_source_rgba(*GOLD, ci); lc.new_path(); lc.arc(CX, CY, 260, 0, TAU); lc.stroke()
        a = t * 1.3
        lc.set_source_rgba(*PINK, ci); lc.arc(CX + 260 * math.cos(a), CY + 260 * math.sin(a), 14, 0, TAU); lc.fill()
        text(cr, 'any angle:  ∞', CX, CY + 360, 52, font='JetBrains Mono', col=TEXT, alpha=ci, shadow=False)
    # three kinds of move
    th = fade(t, tt('three') - 0.2, tt('notice') + 0.3)
    if th > 0:
        r_ = rp(t, tt('refl'), tt('refl') + 1.0) * th
        y1 = CY - 250
        motif(lc, CX - 150, y1, 70, alpha=r_, col=GOLD); motif(lc, CX + 150, y1, 70, flip=-1, alpha=r_, col=GOLD)
        if r_ > 0:
            lc.set_dash([12, 10]); lc.set_line_width(3); lc.set_source_rgba(*SUB, r_)
            lc.move_to(CX, y1 - 110); lc.line_to(CX, y1 + 110); lc.stroke(); lc.set_dash([])
        o_ = rp(t, tt('rot'), tt('rot') + 1.0) * th
        for k in range(5):
            a = k * TAU / 5 + 0.3 * t
            motif(lc, CX + 115 * math.cos(a), CY + 50 + 115 * math.sin(a), 45, rot=a + math.pi / 2, alpha=o_, col=PINK)
        s_ = rp(t, tt('trans'), tt('trans') + 1.0) * th
        off = (t * 60) % 120
        for k in range(-1, 8):
            x = CX - 420 + k * 120 + off
            if CX - 400 < x < CX + 400:
                motif(lc, x, CY + 320, 45, alpha=s_ * fade(x, CX - 420, CX + 420, 60, 60) if True else s_, col=CYAN)
        for lab, y, al in (('reflection', y1 - 140, r_), ('rotation', CY - 95, o_), ('translation', CY + 250, s_)):
            text(cr, lab, CX, y, 38, weight=cairo.FONT_WEIGHT_NORMAL, slant=cairo.FONT_SLANT_ITALIC, col=SUB, alpha=al, shadow=False)
    # information: the blank circle
    bl = fade(t, tt('notice') + 0.2, S[1][1] + 0.5)
    if bl > 0:
        busy = 1 - rp(t, tt('blank') - 0.5, tt('blank') + 1.5)
        rng = np.random.default_rng(11)
        for i in range(140):
            a = rng.random() * TAU; rr = 280 * math.sqrt(rng.random())
            lc.set_source_rgba(*hue(rng.random(), 0.6), 0.8 * bl * busy)
            lc.arc(CX + rr * math.cos(a), CY + rr * math.sin(a), 6 + 6 * rng.random(), 0, TAU); lc.fill()
        lc.set_line_width(6); lc.set_source_rgba(*WHITE, 0.85 * bl); lc.new_path(); lc.arc(CX, CY, 300, 0, TAU); lc.stroke()
        if t > tt('blank'):
            text(cr, 'most symmetry, least information', CX, CY + 400, 36, weight=cairo.FONT_WEIGHT_NORMAL,
                 slant=cairo.FONT_SLANT_ITALIC, col=SUB, alpha=bl * rp(t, tt('blank'), tt('blank') + 1), shadow=False)

# 2 — nature -----------------------------------------------------------------------------------
def _scene_2(t, cr, lc, inn):
    # hexagonal lattice -> snowflake
    sf = fade(t, tt('nature') - 0.3, tt('starfish') + 0.3)
    if sf > 0:
        lat = fade(t, tt('lattice') - 0.4, tt('grow') + 1.5, 0.6, 1.2) * sf
        if lat > 0:
            for i in range(-6, 7):
                for j in range(-7, 8):
                    x = CX + 52 * (i + 0.5 * (j % 2)); y = CY + 45 * j
                    if (x - CX) ** 2 + (y - CY) ** 2 < 380 ** 2:
                        lc.set_source_rgba(*CYAN, 0.6 * lat); lc.arc(x, y, 6, 0, TAU); lc.fill()
                        if (x - CX) ** 2 + (y - CY) ** 2 < 120 ** 2:
                            lc.set_line_width(1.5); lc.set_source_rgba(*CYAN, 0.25 * lat)
                            for k in range(6):
                                a = k * TAU / 6
                                lc.move_to(x, y); lc.line_to(x + 26 * math.cos(a), y + 26 * math.sin(a)); lc.stroke()
        g = rp(t, tt('grow') - 0.5, tt('grow') + 5.0)
        snowflake(lc, CX, CY, 360, alpha=sf, grow=max(0.02, g), width=5)
    # starfish, larva, flowers
    st = fade(t, tt('starfish') - 0.3, tt('animal') + 0.2)
    if st > 0:
        x0, y0 = CX - 170, CY - 170
        lc.save(); lc.translate(x0, y0); lc.rotate(0.1 * t)
        for k in range(5):
            a = k * TAU / 5 - math.pi / 2
            lc.move_to(0, 0)
            lc.curve_to(60 * math.cos(a - 0.5), 60 * math.sin(a - 0.5), 150 * math.cos(a - 0.08), 150 * math.sin(a - 0.08),
                        170 * math.cos(a), 170 * math.sin(a))
            lc.curve_to(150 * math.cos(a + 0.08), 150 * math.sin(a + 0.08), 60 * math.cos(a + 0.5), 60 * math.sin(a + 0.5), 0, 0)
        lc.set_source_rgba(*hue(0.06, 0.7), 0.85 * st); lc.fill(); lc.restore()
        lv = fade(t, tt('larva') - 0.2, tt('daisy') + 0.5) * st
        if lv > 0:
            lc.save(); lc.translate(CX + 210, CY - 170)
            lc.set_line_width(5); lc.set_source_rgba(*hue(0.1, 0.5), lv)
            lc.move_to(0, -120); lc.curve_to(90, -110, 100, 40, 40, 120); lc.line_to(-40, 120)
            lc.curve_to(-100, 40, -90, -110, 0, -120); lc.stroke()
            lc.set_dash([10, 8]); lc.set_line_width(2); lc.set_source_rgba(*SUB, lv); lc.move_to(0, -150); lc.line_to(0, 150); lc.stroke(); lc.set_dash([])
            lc.restore()
            text(cr, 'larva', CX + 210, CY + 0, 34, weight=cairo.FONT_WEIGHT_NORMAL, slant=cairo.FONT_SLANT_ITALIC, col=SUB, alpha=lv, shadow=False)
        fl = rp(t, tt('daisy') - 0.2, tt('daisy') + 0.8) * st
        if fl > 0:
            # daisy
            xd, yd = CX - 220, CY + 200
            for k in range(13):
                a = k * TAU / 13 + 0.05 * t
                lc.save(); lc.translate(xd, yd); lc.rotate(a); lc.scale(1, 0.32)
                lc.arc(78, 0, 62, 0, TAU); lc.restore(); lc.set_source_rgba(*WHITE, 0.55 * fl); lc.fill()
            lc.set_source_rgba(*GOLD, fl); lc.arc(xd, yd, 34, 0, TAU); lc.fill()
            # sunflower seeds: the golden angle
            xs, ys = CX + 30, CY + 220
            for i in range(260):
                rr = 9.0 * math.sqrt(i); a = i * 2.39996
                lc.set_source_rgba(*hue(0.08 + 0.1 * i / 260, 0.8), 0.9 * fl); lc.arc(xs + rr * math.cos(a), ys + rr * math.sin(a), 4.5, 0, TAU); lc.fill()
        org = rp(t, tt('orange') - 0.2, tt('orange') + 0.8) * st
        if org > 0:
            xo, yo = CX + 290, CY + 220
            lc.set_source_rgba(*hue(0.08, 0.85), 0.8 * org); lc.arc(xo, yo, 105, 0, TAU); lc.fill()
            lc.set_line_width(4); lc.set_source_rgba(*hue(0.13, 0.3), org)
            for k in range(10):
                a = k * TAU / 10
                lc.move_to(xo, yo); lc.line_to(xo + 100 * math.cos(a), yo + 100 * math.sin(a)); lc.stroke()
    # bilateral: butterfly curve and a figure
    bi = fade(t, tt('animal') - 0.3, tt('why') + 0.4)
    if bi > 0:
        pts = []
        for i in range(1601):
            th = 12 * math.pi * i / 1600
            r_ = math.exp(math.sin(th)) - 2 * math.cos(4 * th) + math.sin((2 * th - math.pi) / 24) ** 5
            pts.append((CX + 85 * r_ * math.sin(th) * 0 + 85 * r_ * math.cos(th + math.pi / 2) * -1, CY + 40 - 85 * r_ * math.sin(th + math.pi / 2)))
        for i in range(1600):
            lc.set_line_width(2.4); lc.set_source_rgba(*hue(i / 1600 * 0.8 + 0.5, 0.75), 0.75 * bi)
            lc.move_to(*pts[i]); lc.line_to(*pts[i + 1]); lc.stroke()
        ml = rp(t, tt('mirrorline'), tt('mirrorline') + 1) * bi
        if ml > 0:
            lc.set_dash([16, 12]); lc.set_line_width(4); lc.set_source_rgba(*WHITE, 0.9 * ml)
            lc.move_to(CX, CY - 400); lc.line_to(CX, CY + 400); lc.stroke(); lc.set_dash([])
        if t > tt('bilat'):
            text(cr, 'bilateral symmetry', CX, CY + 420, 40, col=TEXT, alpha=bi * rp(t, tt('bilat'), tt('bilat') + 1), shadow=False)
    # Curie: symmetric cause -> symmetric effect; lopsided needs a lopsided cause
    cu = fade(t, tt('why') - 0.2, S[2][1] + 0.3)
    if cu > 0:
        lop = rp(t, tt('lopsided'), tt('lopsided') + 1.5)
        snowflake(lc, CX, CY - 40, 260, alpha=cu, odd=lop, width=5)
        if lop > 0:
            q = rp(t, tt('realq'), tt('realq') + 1) * cu
            text(cr, '?', CX + 300, CY - 180, 160, col=GOLD, alpha=max(q, 0.0), shadow=False)

# 3 — Noether ------------------------------------------------------------------------------------
def _throw(c, x0, y0, rot, col, alpha, prog):
    c.save(); c.translate(x0, y0); c.rotate(rot); c.scale(1.35, 1.35)
    n = int(60 * prog)
    c.set_line_width(5); c.set_source_rgba(*col, alpha)
    for i in range(n):
        u0, u1 = i / 60, (i + 1) / 60
        c.move_to(260 * u0 - 130, -320 * u0 * (1 - u0) * 1.0 + 0); c.line_to(260 * u1 - 130, -320 * u1 * (1 - u1))
        c.stroke()
    if n > 0:
        u = n / 60
        c.arc(260 * u - 130, -320 * u * (1 - u), 13, 0, TAU); c.fill()
    c.set_line_width(3); c.set_source_rgba(*SUB, 0.6 * alpha); c.move_to(-170, 4); c.line_to(170, 4); c.stroke()
    c.restore()

def _scene_3(t, cr, lc, inn):
    no = inn
    intro = fade(t, S[3][0] - 0.2, tt('exp') + 0.5)
    if intro > 0:
        snowflake(lc, CX, CY - 60, 230, rot=0.25 * t, alpha=intro, width=4)
        text(cr, 'a symmetry of the laws', CX, CY + 260, 44, col=CYAN, alpha=intro, shadow=False)
        text(cr, '⇓', CX, CY + 330, 50, col=SUB, alpha=intro, shadow=False)
        text(cr, 'something that is conserved', CX, CY + 400, 44, col=GOLD, alpha=intro, shadow=False)
    # three experiments: today/tomorrow (time), slid (space), turned (direction)
    e1 = fade(t, tt('exp') - 0.3, tt('every_sym') + 0.3)
    if e1 > 0:
        p1 = (t - tt('exp')) % 3.0 / 2.2
        _throw(lc, CX - 180, CY - 160, 0, GOLD, e1, min(1, p1))
        if t > tt('tomorrow'):
            _throw(lc, CX - 180, CY - 160, 0, CYAN, 0.7 * e1 * rp(t, tt('tomorrow'), tt('tomorrow') + 0.8), min(1, p1))
            text(cr, 'today = tomorrow', CX - 180, CY - 40, 34, weight=cairo.FONT_WEIGHT_NORMAL, slant=cairo.FONT_SLANT_ITALIC,
                 col=SUB, alpha=e1, shadow=False)
        s_ = rp(t, tt('slide'), tt('slide') + 1.2) * e1
        if s_ > 0:
            _throw(lc, CX - 180 + 380 * s_, CY - 160, 0, PINK, s_, min(1, p1))
        r_ = rp(t, tt('turnexp'), tt('turnexp') + 1.2) * e1
        if r_ > 0:
            _throw(lc, CX, CY + 230, -0.6 * r_, GREEN, r_, min(1, p1))
    # the three cards
    rows = [('same at every moment', 'energy', GOLD, 'energy'), ('same everywhere', 'momentum', PINK, 'momentum'),
            ('same in every direction', 'angular momentum', GREEN, 'angular')]
    cards = fade(t, tt('energy'), S[3][1] + 0.3)
    for i, (l1, l2, col, key) in enumerate(rows):
        a = rp(t, tt(key), tt(key) + 0.8) * cards * (1 - rp(t, tt('every_sym') - 0.2, tt('every_sym') + 0.6) * 0.0)
        if a <= 0: continue
        y = CY - 330 + 270 * i + (0 if t < tt('every_sym') else 0)
        if t > tt('every_sym'):
            y = CY - 220 + 200 * i
            text(cr, l1, CX, y, 44, col=TEXT, alpha=a, shadow=True)
            text(cr, '→  ' + l2, CX, y + 60, 50, col=col, alpha=a, shadow=True)
    if t > tt('every_sym'):
        text(cr, 'symmetry  →  conservation', CX, CY + 400, 44, font='JetBrains Mono', col=CYAN,
             alpha=rp(t, tt('deepest'), tt('deepest') + 1), shadow=False)

# 4 — matter and antimatter ---------------------------------------------------------------------
PAIR_RNG = np.random.default_rng(64)
PAIRS = [(PAIR_RNG.uniform(0, TAU), PAIR_RNG.uniform(60, 380), PAIR_RNG.uniform(0, 3.0)) for _ in range(70)]

def _scene_4(t, cr, lc, inn):
    a = inn
    t_p, t_v, t_np = tt('pairs'), tt('vanish'), tt('notperfect')
    if t < t_np - 0.3:
        for (ang, rr, ph) in PAIRS:
            cyc = ((t - t_p + ph) % 3.0) / 3.0 if t > t_p else -1
            if cyc < 0: continue
            x, y = CX + rr * math.cos(ang), CY + rr * math.sin(ang)
            sep = 40 * math.sin(math.pi * min(1, cyc / 0.7))
            if cyc < 0.7 or t < t_v:
                for s, col in ((1, GOLD), (-1, VIOLET)):
                    lc.set_source_rgba(*col, 0.9 * a); lc.arc(x + s * sep * math.cos(ang + 1.3), y + s * sep * math.sin(ang + 1.3), 7, 0, TAU); lc.fill()
            else:
                f = (cyc - 0.7) / 0.3
                lc.set_line_width(2); lc.set_source_rgba(*WHITE, a * (1 - f))
                for k in range(8):
                    q = k * TAU / 8
                    lc.move_to(x + 6 * math.cos(q), y + 6 * math.sin(q)); lc.line_to(x + (10 + 60 * f) * math.cos(q), y + (10 + 60 * f) * math.sin(q)); lc.stroke()
        if t > tt('onlylight'):
            w = rp(t, tt('onlylight'), tt('onlylight') + 2) * a * (1 - rp(t, t_np - 1.0, t_np - 0.3))
            lc.set_source_rgba(*WHITE, 0.10 * w); lc.arc(CX, CY, 420, 0, TAU); lc.fill()
        text(cr, 'matter', CX - 150, CY + 430, 36, col=GOLD, alpha=a * rp(t, t_p, t_p + 1), shadow=False)
        text(cr, 'antimatter', CX + 150, CY + 430, 36, col=VIOLET, alpha=a * rp(t, t_p, t_p + 1), shadow=False)
        return
    # the count
    cnt = fade(t, tt('billion') - 0.2, tt('galaxy') + 0.2) * a
    if cnt > 0:
        text(cr, '1,000,000,000', CX, CY - 160, 68, font='JetBrains Mono', col=VIOLET, alpha=cnt * (1 - 0.7 * rp(t, tt('annih'), tt('annih') + 1)), shadow=False)
        text(cr, 'antimatter', CX, CY - 100, 34, col=SUB, alpha=cnt, shadow=False)
        text(cr, '1,000,000,001', CX, CY + 40, 68, font='JetBrains Mono', col=GOLD, alpha=cnt * (1 - 0.7 * rp(t, tt('annih'), tt('annih') + 1)), shadow=False)
        text(cr, 'matter', CX, CY + 100, 34, col=SUB, alpha=cnt, shadow=False)
        sv = rp(t, tt('survived'), tt('survived') + 0.6) * cnt
        if sv > 0:
            lc.set_source_rgba(*GOLD, sv); lc.arc(CX, CY + 230, 16 + 3 * math.sin(6 * t), 0, TAU); lc.fill()
            text(cr, '+1', CX + 60, CY + 245, 44, col=GOLD, alpha=sv, shadow=False)
    gx = rp(t, tt('galaxy'), tt('galaxy') + 2.0) * a
    if gx > 0:
        galaxy(lc, CX, CY - 40, 340, gx, rot=0.15 * t)
        if t > tt('kaons'):
            text(cr, 'why the tip?  still open', CX, CY + 410, 40, col=CYAN, alpha=gx * rp(t, tt('openq1'), tt('openq1') + 1), shadow=False)

# 5 — lumpy universe ----------------------------------------------------------------------------
def _scene_5(t, cr, lc, inn):
    a = inn
    t_g = tt('gravity')
    if t < t_g + 0.5:
        amp = 0.02 + 0.98 * rp(t, tt('almost') + 1.0, tt('almost') + 3.0)
        base = SIMS['cmb'] * amp
        image_disc(cr, base, CX, CY, 380, a * (1 - rp(t, t_g - 0.2, t_g + 0.5)), cmb_cmap)
        if t > tt('almost'):
            text(cr, '1 part in 100,000  (exaggerated)', CX, CY + 430, 36, col=TEXT,
                 alpha=a * rp(t, tt('almost') + 1, tt('almost') + 2), shadow=False)
        if t < tt('almost'):
            text(cr, '380,000 years after the Big Bang', CX, CY + 430, 36, col=SUB, alpha=a * rp(t, tt('oldest'), tt('oldest') + 1), shadow=False)
    if t > t_g - 0.5:
        g = rp(t, t_g - 0.5, tt('staysmooth'))
        D = 0.0 + 26.0 * g ** 1.5
        p = (SIMS['p0'] + D * SIMS['disp'] * 6) % 1.0
        al = a * rp(t, t_g - 0.5, t_g + 0.5)
        lc.save(); lc.new_path(); lc.arc(CX, CY, 400, 0, TAU); lc.clip()
        for (x, y) in p[::2]:
            lc.rectangle(CX - 400 + 800 * x, CY - 400 + 800 * y, 2.2, 2.2)
        lc.set_source_rgba(*hue(0.58, 0.35), 0.55 * al); lc.fill()
        lc.restore()
        if t > tt('billions_y'):
            text(cr, 'galaxies, stars, planets', CX, CY + 440, 38, col=TEXT, alpha=a * rp(t, tt('billions_y'), tt('billions_y') + 1), shadow=False)

# 6 — life picks a hand -------------------------------------------------------------------------
def _scene_6(t, cr, lc, inn):
    a = inn
    hd = fade(t, tt('hands') - 0.3, tt('pasteur') + 0.2)
    if hd > 0:
        hand(lc, CX - 180, CY + 40, 1.25, 1, hd, CYAN)
        hand(lc, CX + 180, CY + 40, 1.25, -1, hd, PINK)
        lc.set_dash([12, 10]); lc.set_line_width(3); lc.set_source_rgba(*SUB, hd); lc.move_to(CX, CY - 300); lc.line_to(CX, CY + 300); lc.stroke(); lc.set_dash([])
        if t > tt('molecules'):
            m = rp(t, tt('molecules'), tt('molecules') + 1) * hd
            tetra_molecule(lc, CX - 180, CY - 290, 70, t * 0.8, 1, m)
            tetra_molecule(lc, CX + 180, CY - 290, 70, -t * 0.8, -1, m)
    ps = fade(t, tt('pasteur') - 0.2, tt('ordinary') + 0.2)
    if ps > 0:
        sort = rp(t, tt('tweezers') - 1.0, tt('tweezers') + 2.0)
        rng = np.random.default_rng(1848)
        for i in range(16):
            hnd = 1 if i % 2 == 0 else -1
            x0, y0 = CX + rng.uniform(-300, 300), CY - 120 + rng.uniform(-200, 160)
            x1, y1 = (CX - 200 if hnd == 1 else CX + 200) + 60 * ((i // 2) % 3 - 1), CY - 200 + 70 * (i // 6)
            x, y = x0 + (x1 - x0) * sort, y0 + (y1 - y0) * sort
            crystal(lc, x, y, 34, hnd, ps, CYAN if hnd == 1 else PINK)
        pl = rp(t, tt('dissolved'), tt('dissolved') + 1) * ps
        if pl > 0:
            for sx, col, sgn in ((-200, CYAN, 1), (200, PINK, -1)):
                ang = sgn * 0.7 * rp(t, tt('dissolved') + 0.8, tt('dissolved') + 3.0)
                cxp, cyp = CX + sx, CY + 220
                lc.set_line_width(4); lc.set_source_rgba(*SUB, pl); lc.new_path(); lc.arc(cxp, cyp, 95, 0, TAU); lc.stroke()
                lc.set_line_width(7); lc.set_source_rgba(*col, pl)
                lc.move_to(cxp - 85 * math.sin(ang), cyp - 85 * math.cos(ang)); lc.line_to(cxp + 85 * math.sin(ang), cyp + 85 * math.cos(ang)); lc.stroke()
            text(cr, 'polarised light turned', CX, CY + 390, 34, weight=cairo.FONT_WEIGHT_NORMAL, slant=cairo.FONT_SLANT_ITALIC, col=SUB, alpha=pl, shadow=False)
    lf = fade(t, tt('ordinary') - 0.2, S[6][1] + 0.3)
    if lf > 0:
        mix = 1 - rp(t, tt('lifenot'), tt('lifenot') + 1.5)
        tetra_molecule(lc, CX - 200, CY - 200, 75, t * 0.7, 1, lf)
        tetra_molecule(lc, CX - 200 + 230, CY - 200, 75, -t * 0.7, -1, lf * (0.15 + 0.85 * mix))
        text(cr, 'L', CX - 200, CY - 60, 48, col=CYAN, alpha=lf * rp(t, tt('amino'), tt('amino') + 1), shadow=False)
        text(cr, 'amino acids', CX - 200, CY - 10, 32, col=SUB, alpha=lf * rp(t, tt('amino'), tt('amino') + 1), shadow=False)
        hx = rp(t, tt('sugars'), tt('sugars') + 1.2) * lf
        helix(lc, CX + 230, CY + 60, 560, 70, t * 1.2, hx, turns=3)
        if hx > 0:
            text(cr, 'right-handed', CX + 230, CY + 400, 34, col=PINK, alpha=hx * rp(t, tt('helix'), tt('helix') + 1), shadow=False)
        if t > tt('shake'):
            hand(lc, CX - 200, CY + 230, 0.8, -1, lf * rp(t, tt('shake'), tt('shake') + 0.8), PINK)

# 7 — from a ball to a body ---------------------------------------------------------------------
def _scene_7(t, cr, lc, inn):
    a = inn
    bl = fade(t, tt('cell') - 0.4, tt('turing') + 0.3)
    if bl > 0:
        lc.set_source_rgba(*hue(0.08, 0.35), 0.35 * bl); lc.arc(CX, CY, 230, 0, TAU); lc.fill()
        lc.set_line_width(5); lc.set_source_rgba(*GOLD, bl); lc.new_path(); lc.arc(CX, CY, 230, 0, TAU); lc.stroke()
        if t > tt('ballsame'):
            for k in range(8):
                q = k * TAU / 8 + 0.4 * t
                lc.set_source_rgba(*CYAN, 0.6 * bl); lc.arc(CX + 300 * math.cos(q), CY + 300 * math.sin(q), 9, 0, TAU); lc.fill()
    tu = fade(t, tt('turing') - 0.2, tt('layout') + 0.3)
    if tu > 0:
        snaps = SIMS['turing']
        u = rp(t, tt('evenmix') + 1.0, tt('amplified') + 4.0)
        idx = min(len(snaps) - 1, int(u * (len(snaps) - 1)))
        f = snaps[idx]
        lo, hi = 0.0, 3.2
        v = np.clip((f - lo) / (hi - lo), 0, 1) if idx > 3 else np.clip(0.31 + (f - 1.0) * 6, 0, 1)
        image_disc(cr, v, CX, CY, 380, tu, turing_cmap)
    bd = fade(t, tt('layout') - 0.2, S[7][1] + 0.3)
    if bd > 0:
        ax = rp(t, tt('headtail'), tt('headtail') + 1) * bd
        lc.set_source_rgba(*hue(0.08, 0.35), 0.35 * bd * (1 - rp(t, tt('mya') - 1, tt('mya')))); lc.arc(CX, CY - 60, 200, 0, TAU); lc.fill()
        if ax > 0 and t < tt('mya'):
            for (dx, dy, lab, col, al) in ((0, -1, 'head', GOLD, ax), (0, 1, 'tail', GOLD, ax),
                                            (-1, 0, 'back', CYAN, rp(t, tt('backbelly'), tt('backbelly') + 1) * bd),
                                            (1, 0, 'belly', CYAN, rp(t, tt('backbelly'), tt('backbelly') + 1) * bd)):
                if al <= 0: continue
                lc.set_line_width(6); lc.set_source_rgba(*col, al)
                lc.move_to(CX + 60 * dx, CY - 60 + 60 * dy); lc.line_to(CX + 250 * dx, CY - 60 + 250 * dy); lc.stroke()
                text(cr, lab, CX + 320 * dx, CY - 60 + 300 * dy + 14, 40, col=col, alpha=al, shadow=False)
        wm = rp(t, tt('mya'), tt('mya') + 1.5) * bd
        if wm > 0:
            xw = CX + 250 - 30 * (t - tt('mya'))
            lc.set_line_width(3)
            for k in range(30):
                xx = xw + 60 + 22 * k
                if xx < CX + 400:
                    lc.set_source_rgba(*SUB, 0.5 * wm); lc.arc(xx, CY + 40 + 6 * math.sin(k), 4, 0, TAU); lc.fill()
            worm(lc, xw, CY + 40, 170, wm, t * 4)
            text(cr, '~555 million years ago', CX, CY + 300, 40, col=TEXT, alpha=wm, shadow=False)
            if t > tt('toyou'):
                figure(lc, CX, CY - 150, 0.45, rp(t, tt('toyou'), tt('toyou') + 1) * bd, mirror_line=1)

# 8 — the heart moves left ----------------------------------------------------------------------
CIL = [(math.cos(k * TAU / 22) * 230, math.sin(k * TAU / 22) * 120) for k in range(22)]
FLOW = np.random.default_rng(1998).uniform(-1, 1, (120, 2))

def _scene_8(t, cr, lc, inn):
    a = inn
    fg = fade(t, S[8][0] - 0.2, tt('node') + 0.2)
    if fg > 0:
        hx = -45 * rp(t, tt('heartleft'), tt('heartleft') + 1.2)
        figure(lc, CX, CY + 40, 1.0, fg, heart_x=hx, liver=t > tt('heartleft') + 1.6, mirror_line=1)
        text(cr, 'seen from behind', CX, CY + 440, 32, weight=cairo.FONT_WEIGHT_NORMAL, slant=cairo.FONT_SLANT_ITALIC, col=SUB, alpha=fg, shadow=False)
    nd = fade(t, tt('node') - 0.2, tt('wrong') + 0.2)
    if nd > 0:
        lc.set_line_width(4); lc.set_source_rgba(*SUB, nd)
        lc.save(); lc.translate(CX, CY); lc.scale(1, 0.55); lc.new_path(); lc.arc(0, 0, 330, 0, TAU); lc.restore(); lc.stroke()
        spin = rp(t, tt('spin') - 0.5, tt('spin') + 0.5)
        for (x, y) in CIL:
            for k in range(3):
                ph = -6.0 * t * spin + k * 0.7
                tipx = x + 26 * math.cos(ph) - 22; tipy = y + 12 * math.sin(ph) - 40
                lc.set_line_width(3); lc.set_source_rgba(*hue(0.55 + 0.03 * k, 0.6), nd * (0.9 - 0.25 * k))
                lc.move_to(CX + x, CY + y); lc.line_to(CX + tipx, CY + tipy); lc.stroke()
        fl = rp(t, tt('pushleft'), tt('pushleft') + 1.0) * nd
        if fl > 0:
            for (fx, fy) in FLOW:
                x = ((fx * 300 - 90 * (t - tt('pushleft')) + 300) % 600) - 300
                lc.set_source_rgba(*GOLD, 0.8 * fl); lc.arc(CX + x, CY + fy * 140, 4, 0, TAU); lc.fill()
            lc.set_line_width(8); lc.set_source_rgba(*GOLD, fl)
            lc.move_to(CX + 160, CY - 270); lc.line_to(CX - 160, CY - 270); lc.stroke()
            lc.move_to(CX - 130, CY - 295); lc.line_to(CX - 165, CY - 270); lc.line_to(CX - 130, CY - 245); lc.stroke()
            text(cr, 'flow to the left', CX, CY - 300, 40, col=GOLD, alpha=fl, shadow=False)
        text(cr, 'the node: smaller than a millimetre', CX, CY + 360, 34, weight=cairo.FONT_WEIGHT_NORMAL,
             slant=cairo.FONT_SLANT_ITALIC, col=SUB, alpha=nd, shadow=False)
    mr = fade(t, tt('wrong') - 0.2, S[8][1] + 0.3)
    if mr > 0:
        figure(lc, CX - 170, CY + 60, 0.75, mr, heart_x=-45, liver=True)
        m2 = rp(t, tt('mirrored'), tt('mirrored') + 1) * mr
        figure(lc, CX + 170, CY + 60, 0.75, m2, heart_x=45, liver=True, col=hue(0.9, 0.4))
        text(cr, '~1 in 10,000', CX + 170, CY + 400, 40, col=PINK, alpha=m2 * rp(t, tt('tenk'), tt('tenk') + 1), shadow=False)

# 9 — the chain ---------------------------------------------------------------------------------
def _scene_9(t, cr, lc, inn):
    a = inn
    steps = [('c_laws', 'symmetric laws', CYAN), ('c_matter', 'matter wins', GOLD), ('c_lumpy', 'stars form', VIOLET),
             ('c_hand', 'life picks a hand', PINK), ('c_cell', 'a body', GREEN), ('c_heart', 'a heart on the left', PINK)]
    merge = rp(t, tt('made5') - 0.5, tt('made5') + 1.5)
    for i, (k, lab, col) in enumerate(steps):
        al = rp(t, tt(k), tt(k) + 0.7) * a
        if al <= 0: continue
        y = CY - 360 + 145 * i
        x = CX - 260
        xx, yy = x + (CX - x) * merge, y + (CY - y) * merge
        lc.set_source_rgba(*col, al); lc.arc(xx, yy, 24 if i else 18, 0, TAU); lc.fill()
        text(cr, lab, CX + 40, y + 14, 44, col=TEXT, alpha=al * (1 - merge), shadow=False)
        if i > 0:
            lc.set_line_width(3); lc.set_source_rgba(*SUB, 0.6 * al * (1 - merge))
            lc.move_to(x, y - 145 + 26); lc.line_to(x, y - 26); lc.stroke()
    if merge > 0:
        figure(lc, CX, CY + 40, 1.0, merge * a, heart_x=-45, mirror_line=0.6)

# 10 — your turn --------------------------------------------------------------------------------
def _scene_10(t, cr, lc, inn):
    a = inn if t < VOICE_END + 1 else inn * (1 - rp(t, VOICE_END + 1, VOICE_END + 3))
    snowflake(lc, CX - 200, CY - 120, 160, rot=0.1 * t, alpha=a, width=4)
    snowflake(lc, CX + 200, CY - 120, 160, rot=-0.1 * t, alpha=a, odd=1.0, width=4, hue0=0.9)
    text(cr, 'perfect', CX - 200, CY + 150, 40, col=CYAN, alpha=a, shadow=False)
    text(cr, 'almost', CX + 200, CY + 150, 40, col=PINK, alpha=a, shadow=False)
    en = rp(t, tt('engine'), tt('engine') + 1) * a
    if en > 0:
        text(cr, 'symmetryengine.space', CX, CY + 300, 54, font='JetBrains Mono', col=GOLD, alpha=en, shadow=False)
        text(cr, 'build a pattern, then break one rule', CX, CY + 360, 34, weight=cairo.FONT_WEIGHT_NORMAL,
             slant=cairo.FONT_SLANT_ITALIC, col=SUB, alpha=en, shadow=False)

# ------------------------------------------------------------------ words
CHAPTER_TITLES = {
    1: ('PART ONE', 'What symmetry is'), 2: ('PART TWO', 'Symmetry in nature'), 3: ('PART THREE', 'The laws are symmetric'),
    4: ('BREAK ONE', 'Matter beats antimatter'), 5: ('BREAK TWO', 'A smooth universe gets lumpy'),
    6: ('BREAK THREE', 'Life picks a hand'), 7: ('BREAK FOUR', 'From a ball to a body'),
    8: ('BREAK FIVE', 'The heart moves left'), 9: ('THE CHAIN', 'Five broken symmetries'), 10: ('YOUR TURN', 'Find one near you'),
}
CAPTION_CUES = [
    ('Here is a snowflake', 'A snowflake:', 'turn it, flip it, same'),
    ('Here is you', 'You:', 'not quite symmetric'),
    ('Here is the strange part', 'Perfect symmetry', 'would leave nothing'),
    ('Today we follow', 'Five breaks', 'and then, you'),
    ('A symmetry is something', 'Symmetry:', 'a move that changes nothing'),
    ('Take a square', 'A square', 'has 8 symmetries'),
    ('A circle has infinitely', 'A circle', 'has infinitely many'),
    ('Three kinds of move', 'Reflect, rotate,', 'translate'),
    ('Notice something', 'More symmetry,', 'less information'),
    ('Nature is full of it', 'Snowflakes: six arms', 'from a hexagonal lattice'),
    ('A starfish has', 'Five-fold, and', 'flowers turn too'),
    ('look at almost any animal', 'One mirror line:', 'over 98% of animal species'),
    ('Why is nature so symmetric', 'Symmetric causes,', 'symmetric effects'),
    ('Which raises the real question', 'So where does', 'asymmetry come from?'),
    ('Emmy Noether', 'Noether, 1918:', 'symmetry → conservation'),
    ('Do an experiment today', 'Same today as tomorrow', '→ energy is conserved'),
    ('Slide the experiment', 'Same everywhere → momentum,', 'every direction → spin'),
    ('Every symmetry of the laws', 'Symmetry is', 'the deepest rule'),
    ('Break one happened', 'Matter and antimatter', 'made in pairs'),
    ('If the deal had been perfect', 'A perfect deal:', 'only light'),
    ("It wasn't perfect", 'About 1 extra in', 'every billion'),
    ('Physicists first caught', 'Caught in 1964:', 'why is still open'),
    ('Break two', 'The oldest light:', 'almost perfectly smooth'),
    ('The differences are', 'Ripples of', '1 part in 100,000'),
    ('Gravity loves a lump', 'Gravity grows lumps', 'into galaxies'),
    ('Break three', 'Mirror images', 'that never match'),
    ('Louis Pasteur', 'Pasteur, 1848:', 'left and right crystals'),
    ('Ordinary chemistry', 'Life uses one hand:', 'L amino acids, right-handed DNA'),
    ('Life chose one hand', 'Why that hand?', 'still an open question'),
    ('Break four', 'A ball looks the same', 'from every direction'),
    ('Alan Turing', 'Turing, 1952:', 'an even mix breaks itself'),
    ('Processes like that', 'Head and tail,', 'back and belly'),
    ('five hundred and fifty-five million', 'One mirror line,', '555 million years ago'),
    ('But you are not quite', 'Heart on the left,', 'liver on the right'),
    ('called the node', 'Spinning cilia', 'push fluid to the left'),
    ('Every so often the flow', 'Mirrored organs:', 'about 1 in 10,000'),
    ('So here is the chain', 'The chain', 'of broken symmetries'),
    ('Symmetry gives the world', 'Symmetry: the rules.', 'Breaking it: the stories.'),
    ('Now it is your turn', 'Your turn:', 'perfect, or almost?'),
    ('Symmetry Engine', 'Play with it:', 'Symmetry Engine'),
]
CITATIONS = [
    ('Pierre Curie', 'Pierre Curie', '1894'),
    ('Emmy Noether', 'Emmy Noether', '1918'),
    ('in 1964', 'Cronin & Fitch', '1964, kaons'),
    ('Louis Pasteur', 'Louis Pasteur', '1848'),
    ('Alan Turing', 'Alan Turing', '1952, The Chemical Basis of Morphogenesis'),
    ('Japanese scientists', 'Nonaka et al.', '1998, Cell'),
]

_CAPS = None
def _caps():
    global _CAPS
    if _CAPS is None:
        got = []
        for phrase, l1, l2 in CAPTION_CUES:
            x = at(phrase)
            if x is not None:
                got.append((x - 0.15, l1, l2))
        got.sort()
        _CAPS = []
        for i, (t0, l1, l2) in enumerate(got):
            end = t0 + 999.0
            if i + 1 < len(got):
                end = min(end, got[i + 1][0] - 0.12)
            for a_ch, b_ch, _c in CH:
                if a_ch <= t0 <= b_ch:
                    end = min(end, b_ch - 0.3); break
            end = min(end, VOICE_END + 0.8)
            if end - t0 > 0.9:
                _CAPS.append((t0, end, l1, l2, CYAN, 6.0))
    return _CAPS

_CITES = None
def _cites():
    global _CITES
    if _CITES is None:
        _CITES = sorted((at(p), n, d) for p, n, d in CITATIONS if at(p) is not None)
    return _CITES

def words(t, cr):
    header(cr)
    card_up = chapter_card(cr, t, CH, CHAPTER_TITLES)
    if not card_up:
        captions(cr, t, _caps())
    for i, (ct, name, date) in enumerate(_cites()):
        nxt = _cites()[i + 1][0] if i + 1 < len(_cites()) else 1e9
        cite(cr, t, ct, name, date, hold=min(9.0, max(1.5, nxt - ct - 1.0)))
    if T['yourturn']:
        note_card(cr, t, T['yourturn'] + 2.0, 'YOUR TURN',
                  ['Find one thing near you with', 'perfect symmetry, and one that', 'is almost symmetric.',
                   'Which tells you more about', 'how it was made?'],
                  hold=max(4.0, tt('engine') - T['yourturn'] - 2.6))
    if T['engine']:
        note_card(cr, t, T['engine'] + 0.5, 'PLAY WITH IT',
                  ['symmetryengine.space', 'Build a perfect pattern,', 'break one rule,', 'watch what grows.',
                   'Symmetry playlist: link below.'],
                  hold=max(4.0, DUR - T['engine'] - 2.0))

def draw(t, cr, lc):
    art(t, cr, lc)
    words(t, cr)


if __name__ == '__main__':
    if '--check' in sys.argv:
        _caps(); _cites()
        print('duration %.1fs' % DUR)
        for a, b, c in CH:
            if c: print('  %d:%02d  %s' % (int(a) // 60, int(a) % 60, c[1]))
        miss = sorted(set(_MISSING))
        print('cues: %d   missing: %d' % (len(T), len(miss)))
        for m in miss: print('   MISSING:', m)
        sys.exit(0)
    if '--stills' in sys.argv:
        out = os.path.join(BUILD, 'stills'); os.makedirs(out, exist_ok=True)
        for x in sys.argv[sys.argv.index('--stills') + 1:]:
            tt_ = float(x)
            make_frame(draw, tt_, os.path.join(out, 't%06.1f.png' % tt_))
        sys.exit(0)
    from render_pipe import render
    t0 = float(sys.argv[1]) if len(sys.argv) > 1 else 0.0
    dur = float(sys.argv[2]) if len(sys.argv) > 2 else DUR
    out = sys.argv[3] if len(sys.argv) > 3 else os.path.join(BUILD, 'video.mp4')
    render(draw, dur, out, t0=t0, progress_every=200, label='  ')
