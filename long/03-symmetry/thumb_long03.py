"""Thumbnail for long03: a perfect snowflake, a crack through symmetry, and you (heart on the left)."""
import os, sys
os.environ['MU_FORMAT'] = 'long'; os.environ['MU_THEME'] = 'night'
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import math, cairo
import mu_style as M
from mu_style import *
import video_long03 as V

surf = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
cr = cairo.Context(surf); background(cr)
L = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
lc = M._LightLayer(L); lc.set_operator(cairo.OPERATOR_ADD)
lc.set_line_cap(cairo.LINE_CAP_ROUND); lc.set_line_join(cairo.LINE_JOIN_ROUND)
V.snowflake(lc, 430, 560, 330, rot=0.0, alpha=1.0, width=9)
V.snowflake(lc, 1490, 560, 330, rot=0.0, alpha=0.0)
V.figure(lc, 1500, 610, 1.1, 1.0, heart_x=-45, mirror_line=1, col=hue(0.92, 0.45))
# the crack: a jagged line between them
lc.set_line_width(8); lc.set_source_rgba(*GOLD, 1.0)
pts = [(960, 90), (930, 260), (990, 410), (925, 560), (995, 720), (940, 880), (975, 1000)]
lc.move_to(*pts[0])
for p in pts[1:]: lc.line_to(*p)
lc.stroke()
composite_glow(cr, L, strength=2.6)
text(cr, 'SYMMETRY', 430, 1010, 120, col=CYAN, shadow=True)
text(cr, 'BROKEN', 1500, 1010, 120, col=PINK, shadow=True)
text(cr, '= YOU', 1500, 150, 110, col=TEXT, shadow=True)
out = os.path.join(V.BUILD, 'thumb.png'); surf.write_to_png(out)
from PIL import Image
Image.open(out).convert('RGB').resize((1280, 720), Image.LANCZOS).save(os.path.join(V.BUILD, 'thumb.jpg'), quality=92)
print('ok')
