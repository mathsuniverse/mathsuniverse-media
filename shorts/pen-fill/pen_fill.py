"""Preview: a pen draws the hat tiling tile by tile from the centre outwards."""
import math, subprocess, sys
from PIL import Image, ImageDraw
import hat_tiling as H

W, Hh, FPS, SEC, SS = 1080, 1920, 30, 14, 2
hs = H.hats(4)
cx = sum(sum(p[0] for p in poly) / 13 for _, poly in hs) / len(hs)
cy = sum(sum(p[1] for p in poly) / 13 for _, poly in hs) / len(hs)
cent = lambda poly: (sum(p[0] for p in poly) / 13 - cx, sum(p[1] for p in poly) / 13 - cy)
order = sorted(hs, key=lambda t: math.hypot(*cent(t[1])))
scale = 34 * SS
def P(p): return (W * SS / 2 + (p[0] - cx) * scale, Hh * SS / 2 - (p[1] - cy) * scale)
BG, INK, PEN = (246, 241, 230), (40, 36, 48), (220, 60, 90)
FILL = {'H1': (238, 120, 140)}
PAL = [(120, 170, 200), (150, 190, 215), (100, 150, 185)]
N = len(order); T = FPS * SEC
base = Image.new('RGB', (W * SS, Hh * SS), BG); bd = ImageDraw.Draw(base)
done = 0
ff = subprocess.Popen(['ffmpeg', '-y', '-loglevel', 'error', '-f', 'rawvideo', '-pix_fmt', 'rgb24', '-s', f'{W}x{Hh}',
                       '-r', str(FPS), '-i', '-', '-c:v', 'libx264', '-pix_fmt', 'yuv420p', '-crf', '18', sys.argv[1]],
                      stdin=subprocess.PIPE)
for f in range(T):
    u = min(1, f / (T * 0.92))
    prog = N * u ** 2.2 if f else 0           # slow start, then accelerating
    k = int(prog)
    while done < min(k, N):
        lab, poly = order[done]
        pts = [P(p) for p in poly]
        col = FILL.get(lab, PAL[done % 3])
        bd.polygon(pts, fill=col); bd.line(pts + [pts[0]], fill=INK, width=3 * SS, joint='curve')
        done += 1
    img = base.copy(); d = ImageDraw.Draw(img)
    if done < N:                               # the pen tracing the current tile
        lab, poly = order[done]; frac = prog - k
        pts = [P(p) for p in poly] + [P(poly[0])]
        L = frac * 13; m = int(L); seg = pts[:m + 1]
        a, b = pts[m], pts[min(m + 1, 13)]; t = L - m
        tip = (a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t)
        seg.append(tip)
        if len(seg) > 1: d.line(seg, fill=INK, width=3 * SS, joint='curve')
        r = 9 * SS; d.ellipse([tip[0] - r, tip[1] - r, tip[0] + r, tip[1] + r], fill=PEN)
    ff.stdin.write(img.resize((W, Hh), Image.LANCZOS).tobytes())
ff.stdin.close(); ff.wait(); print('tiles', N)
