"""Channel banner 2560x1440, content inside YouTube's 1546x423 safe area.
Light cream ground, violet heart mark matching the avatar, faint equations behind."""
import cairo, math

W, H = 2560, 1440
CX, CY = W / 2, H / 2
SAFE_W, SAFE_H = 1546, 423

CREAM0 = (0.985, 0.980, 0.995)
CREAM1 = (0.945, 0.935, 0.975)
VIOLET = (0.38, 0.19, 0.78)
VIOLET_D = (0.27, 0.12, 0.58)
INK = (0.17, 0.15, 0.26)
SUB = (0.42, 0.40, 0.52)
FAINT = (0.55, 0.45, 0.85)
CREAM = (0.99, 0.98, 0.95)

def card_pt(a, cx, cy, r):
    x = (2 * math.cos(a - math.pi / 2) + math.cos(2 * a - math.pi / 2)) / 3
    y = (2 * math.sin(a - math.pi / 2) + math.sin(2 * a - math.pi / 2)) / 3
    return cx + r * x, cy - r * y

def rounded(cr, x, y, w, h, r):
    cr.new_sub_path()
    cr.arc(x + w - r, y + r, r, -math.pi / 2, 0)
    cr.arc(x + w - r, y + h - r, r, 0, math.pi / 2)
    cr.arc(x + r, y + h - r, r, math.pi / 2, math.pi)
    cr.arc(x + r, y + r, r, math.pi, 1.5 * math.pi)
    cr.close_path()

def heart_mark(cr, x, y, size):
    """The avatar, drawn as the banner's logo tile."""
    g = cairo.LinearGradient(x, y, x + size, y + size)
    g.add_color_stop_rgb(0, 0.42, 0.22, 0.86); g.add_color_stop_rgb(1, *VIOLET_D)
    rounded(cr, x, y, size, size, size * 0.23); cr.set_source(g); cr.fill()
    cx, cy, R = x + size / 2, y + size / 2, size * 0.40
    cr.set_line_cap(cairo.LINE_CAP_ROUND); cr.set_line_join(cairo.LINE_JOIN_ROUND)
    P = lambda a: (cx + R * math.cos(a - math.pi / 2), cy - R * math.sin(a - math.pi / 2))
    cr.save()
    for j in range(721):
        px, py = card_pt(2 * math.pi * j / 720, cx, cy, R)
        cr.line_to(px, py) if j else cr.move_to(px, py)
    cr.close_path(); cr.clip()
    cr.set_line_width(size * 0.005)
    for i in range(72):
        x1, y1 = P(2 * math.pi * i / 72); x2, y2 = P(2 * math.pi * (2 * i % 72) / 72)
        cr.set_source_rgba(*CREAM, 0.22); cr.move_to(x1, y1); cr.line_to(x2, y2); cr.stroke()
    cr.restore()
    cr.set_line_width(size * 0.060)
    for j in range(721):
        px, py = card_pt(2 * math.pi * j / 720, cx, cy, R)
        cr.line_to(px, py) if j else cr.move_to(px, py)
    cr.set_source_rgb(*CREAM); cr.stroke()

def text(cr, s, x, y, size, font='Noto Serif', weight=cairo.FONT_WEIGHT_BOLD,
         slant=cairo.FONT_SLANT_NORMAL, col=INK, alpha=1.0, align='left', spacing=0):
    cr.select_font_face(font, slant, weight); cr.set_font_size(size)
    if spacing:
        ws = [cr.text_extents(c).x_advance for c in s]
        total = sum(ws) + spacing * (len(s) - 1)
        cx0 = x - total / 2 if align == 'center' else x
        cr.set_source_rgba(*col, alpha)
        for c, w in zip(s, ws):
            cr.move_to(cx0, y); cr.show_text(c); cx0 += w + spacing
        return total
    e = cr.text_extents(s)
    xx = x - e.x_advance / 2 if align == 'center' else x
    cr.set_source_rgba(*col, alpha); cr.move_to(xx, y); cr.show_text(s)
    return e.x_advance

def chip(cr, s, x, y, h=52):
    cr.select_font_face('JetBrains Mono', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(25)
    w = cr.text_extents(s).x_advance + 44
    rounded(cr, x, y, w, h, h / 2)
    cr.set_source_rgba(*VIOLET, 0.09); cr.fill_preserve()
    cr.set_source_rgba(*VIOLET, 0.28); cr.set_line_width(2); cr.stroke()
    cr.set_source_rgba(*VIOLET_D, 0.95)
    cr.move_to(x + 22, y + h / 2 + 9); cr.show_text(s)
    return w + 14


def eq_power(cr, base, expo, rest, x, y, size, col=None, alpha=0.30):
    """Draw base^expo rest with a real raised exponent, not a caret."""
    col = col or FAINT
    cr.select_font_face('DejaVu Serif', cairo.FONT_SLANT_ITALIC, cairo.FONT_WEIGHT_NORMAL)
    cr.set_source_rgba(*col, alpha)
    cr.set_font_size(size); cr.move_to(x, y); cr.show_text(base)
    w = cr.text_extents(base).x_advance
    cr.set_font_size(size * 0.66); cr.move_to(x + w + size * 0.06, y - size * 0.44); cr.show_text(expo)
    w2 = cr.text_extents(expo).x_advance
    cr.set_font_size(size); cr.move_to(x + w + size * 0.12 + w2, y); cr.show_text(rest)

def build(path):
    surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
    cr = cairo.Context(surf)
    g = cairo.LinearGradient(0, 0, W, H)
    g.add_color_stop_rgb(0, *CREAM0); g.add_color_stop_rgb(1, *CREAM1)
    cr.set_source(g); cr.paint()

    # faint maths in the wide margins (seen on TV, harmless elsewhere)
    # Desktop shows a 2560x423 strip; phones show only the middle 1546 of it.
    # So the side zones (x<500 and x>2060, y 510-930) are seen on desktop and
    # cropped on a phone: the right home for the faint maths. The top and
    # bottom bands are TV-only, so a second layer goes there.
    eq_power(cr, 'e', 'iπ', ' + 1 = 0', 60, 890, 44)                 # left, desktop strip
    eqs = [('iħ ∂ψ/∂t = Ĥψ', 2080, 890, 42),                          # right, desktop strip
           ('∇·v = 0', 300, 565, 40), ('F = Gm₁m₂/r²', 2085, 565, 36),
           ('ζ(s) = Σ 1/nˢ', 1180, 1300, 44),                         # TV bands
           ('∂u/∂t = D∇²u + f(u,v)', 240, 1215, 42),
           ('a² + b² = c²', 1660, 250, 44), ('Δ = b² − 4ac', 640, 250, 42)]
    for s, x, y, sz in eqs:
        text(cr, s, x, y, sz, font='DejaVu Serif', weight=cairo.FONT_WEIGHT_NORMAL,
             slant=cairo.FONT_SLANT_ITALIC, col=FAINT, alpha=0.30)
    # faint cardioid line art: one each side inside the desktop strip, one in a TV corner
    for (ox, oy, rr, al) in ((2470, 655, 140, 0.17), (90, 650, 140, 0.15), (2300, 1160, 190, 0.12)):
        P = lambda a: (ox + rr * math.cos(a - math.pi / 2), oy - rr * math.sin(a - math.pi / 2))
        cr.set_line_width(2)
        for i in range(110):
            x1, y1 = P(2 * math.pi * i / 110); x2, y2 = P(2 * math.pi * (2 * i % 110) / 110)
            cr.set_source_rgba(*VIOLET, al); cr.move_to(x1, y1); cr.line_to(x2, y2); cr.stroke()

    # ---- safe area content: wordmark only. The avatar carries the heart mark,
    # so repeating it here would show two logos stacked on the channel page.
    tx = CX
    text(cr, 'The Math Universe', tx, CY - 66, 132, col=VIOLET, align='center')
    text(cr, 'Mathematics made a pleasure', tx, CY + 6, 46,
         weight=cairo.FONT_WEIGHT_NORMAL, col=SUB, align='center')
    chips = ('Symmetry', 'Fourier', 'Fractals', 'Curves', 'Puzzles', 'Nature')
    cr.select_font_face('JetBrains Mono', cairo.FONT_SLANT_NORMAL, cairo.FONT_WEIGHT_NORMAL)
    cr.set_font_size(25)
    total = sum(cr.text_extents(c).x_advance + 44 + 14 for c in chips) - 14
    x = CX - total / 2
    for c in chips:
        x += chip(cr, c, x, CY + 52)
    text(cr, 'interactiveexplorer.space', tx, CY + 184, 38, font='JetBrains Mono',
         weight=cairo.FONT_WEIGHT_NORMAL, col=VIOLET, alpha=0.92, align='center')
    surf.write_to_png(path)

if __name__ == '__main__':
    build('banner_v2_2560x1440.png')
    print('ok')
