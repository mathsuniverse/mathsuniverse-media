"""The 'hat' aperiodic monotile tiling (Smith, Myers, Kaplan, Goodman-Strauss, 2023).

Port to Python of Craig S. Kaplan's hatviz (BSD 3-Clause, (c) 2023 Craig S. Kaplan,
https://github.com/isohedral/hatviz): the H/T/P/F metatile substitution.

    hats(levels) -> list of (label, polygon as list of (x, y))
label 'H1' marks the reflected hats.
"""
import math

R3 = math.sqrt(3); HR3 = R3 / 2
IDENT = (1, 0, 0, 0, 1, 0)

def hexpt(x, y): return (x + 0.5 * y, HR3 * y)

def inv(T):
    det = T[0] * T[4] - T[1] * T[3]
    return (T[4] / det, -T[1] / det, (T[1] * T[5] - T[2] * T[4]) / det,
            -T[3] / det, T[0] / det, (T[2] * T[3] - T[0] * T[5]) / det)

def mul(A, B):
    return (A[0] * B[0] + A[1] * B[3], A[0] * B[1] + A[1] * B[4], A[0] * B[2] + A[1] * B[5] + A[2],
            A[3] * B[0] + A[4] * B[3], A[3] * B[1] + A[4] * B[4], A[3] * B[2] + A[4] * B[5] + A[5])

def padd(p, q): return (p[0] + q[0], p[1] + q[1])
def psub(p, q): return (p[0] - q[0], p[1] - q[1])
def trot(a): c, s = math.cos(a), math.sin(a); return (c, -s, 0, s, c, 0)
def ttrans(x, y): return (1, 0, x, 0, 1, y)
def rot_about(p, a): return mul(ttrans(p[0], p[1]), mul(trot(a), ttrans(-p[0], -p[1])))
def tpt(M, P): return (M[0] * P[0] + M[1] * P[1] + M[2], M[3] * P[0] + M[4] * P[1] + M[5])
def match_seg(p, q): return (q[0] - p[0], p[1] - q[1], p[0], q[1] - p[1], q[0] - p[0], p[1])
def match_two(p1, q1, p2, q2): return mul(match_seg(p2, q2), inv(match_seg(p1, q1)))

def intersect(p1, q1, p2, q2):
    d = (q2[1] - p2[1]) * (q1[0] - p1[0]) - (q2[0] - p2[0]) * (q1[1] - p1[1])
    uA = ((q2[0] - p2[0]) * (p1[1] - p2[1]) - (q2[1] - p2[1]) * (p1[0] - p2[0])) / d
    return (p1[0] + uA * (q1[0] - p1[0]), p1[1] + uA * (q1[1] - p1[1]))

HAT = [hexpt(0, 0), hexpt(-1, -1), hexpt(0, -2), hexpt(2, -2), hexpt(2, -1), hexpt(4, -2), hexpt(5, -1),
       hexpt(4, 0), hexpt(3, 0), hexpt(2, 2), hexpt(0, 3), hexpt(0, 2), hexpt(-1, 2)]


class Hat:
    def __init__(self, label): self.label = label
    def flat(self, T, out): out.append((self.label, T))


class Meta:
    def __init__(self, shape, width):
        self.shape = list(shape); self.width = width; self.children = []
    def add(self, T, g): self.children.append([T, g])
    def ev(self, n, i):
        T, g = self.children[n]; return tpt(T, g.shape[i])
    def recentre(self):
        cx = sum(p[0] for p in self.shape) / len(self.shape); cy = sum(p[1] for p in self.shape) / len(self.shape)
        self.shape = [padd(p, (-cx, -cy)) for p in self.shape]
        M = ttrans(-cx, -cy)
        for ch in self.children: ch[0] = mul(M, ch[0])
    def flat(self, T, out):
        for CT, g in self.children: g.flat(mul(T, CT), out)


H1h, Hh, Th, Ph, Fh = Hat('H1'), Hat('H'), Hat('T'), Hat('P'), Hat('F')

def _H():
    o = [(0, 0), (4, 0), (4.5, HR3), (2.5, 5 * HR3), (1.5, 5 * HR3), (-0.5, HR3)]
    m = Meta(o, 2)
    m.add(match_two(HAT[5], HAT[7], o[5], o[0]), Hh)
    m.add(match_two(HAT[9], HAT[11], o[1], o[2]), Hh)
    m.add(match_two(HAT[5], HAT[7], o[3], o[4]), Hh)
    m.add(mul(ttrans(2.5, HR3), mul((-0.5, -HR3, 0, HR3, -0.5, 0), (0.5, 0, 0, 0, -0.5, 0))), H1h)
    return m

def _T():
    m = Meta([(0, 0), (3, 0), (1.5, 3 * HR3)], 2); m.add((0.5, 0, 0.5, 0, 0.5, HR3), Th); return m

def _P():
    m = Meta([(0, 0), (4, 0), (3, 2 * HR3), (-1, 2 * HR3)], 2)
    m.add((0.5, 0, 1.5, 0, 0.5, HR3), Ph)
    m.add(mul(ttrans(0, 2 * HR3), mul((0.5, HR3, 0, -HR3, 0.5, 0), (0.5, 0, 0, 0, 0.5, 0))), Ph)
    return m

def _F():
    m = Meta([(0, 0), (3, 0), (3.5, HR3), (3, 2 * HR3), (-1, 2 * HR3)], 2)
    m.add((0.5, 0, 1.5, 0, 0.5, HR3), Fh)
    m.add(mul(ttrans(0, 2 * HR3), mul((0.5, HR3, 0, -HR3, 0.5, 0), (0.5, 0, 0, 0, 0.5, 0))), Fh)
    return m

RULES = [['H'], [0, 0, 'P', 2], [1, 0, 'H', 2], [2, 0, 'P', 2], [3, 0, 'H', 2], [4, 4, 'P', 2], [0, 4, 'F', 3],
         [2, 4, 'F', 3], [4, 1, 3, 2, 'F', 0], [8, 3, 'H', 0], [9, 2, 'P', 0], [10, 2, 'H', 0], [11, 4, 'P', 2],
         [12, 0, 'H', 2], [13, 0, 'F', 3], [14, 2, 'F', 1], [15, 3, 'H', 4], [8, 2, 'F', 1], [17, 3, 'H', 0],
         [18, 2, 'P', 0], [19, 2, 'H', 2], [20, 4, 'F', 3], [20, 0, 'P', 2], [22, 0, 'H', 2], [23, 4, 'F', 3],
         [23, 0, 'F', 3], [16, 0, 'P', 2], [9, 4, 0, 2, 'T', 2], [4, 0, 'F', 3]]

def patch(H, T, P, F):
    ret = Meta([], H.width); S = {'H': H, 'T': T, 'P': P, 'F': F}
    for r in RULES:
        if len(r) == 1:
            ret.add(IDENT, S[r[0]])
        elif len(r) == 4:
            CT, g = ret.children[r[0]]; poly = g.shape
            P_ = tpt(CT, poly[(r[1] + 1) % len(poly)]); Q = tpt(CT, poly[r[1]])
            ns = S[r[2]]; np_ = ns.shape
            ret.add(match_two(np_[r[3]], np_[(r[3] + 1) % len(np_)], P_, Q), ns)
        else:
            cP, cQ = ret.children[r[0]], ret.children[r[2]]
            P_ = tpt(cQ[0], cQ[1].shape[r[3]]); Q = tpt(cP[0], cP[1].shape[r[1]])
            ns = S[r[4]]; np_ = ns.shape
            ret.add(match_two(np_[r[5]], np_[(r[5] + 1) % len(np_)], P_, Q), ns)
    return ret

def metatiles(p):
    bps1 = p.ev(8, 2); bps2 = p.ev(21, 2)
    rbps = tpt(rot_about(bps1, -2 * math.pi / 3), bps2)
    p72 = p.ev(7, 2); p252 = p.ev(25, 2)
    llc = intersect(bps1, rbps, p.ev(6, 2), p72)
    w = psub(p.ev(6, 2), llc)
    Ho = [llc, bps1]
    w = tpt(trot(-math.pi / 3), w); Ho.append(padd(Ho[1], w)); Ho.append(p.ev(14, 2))
    w = tpt(trot(-math.pi / 3), w); Ho.append(psub(Ho[3], w)); Ho.append(p.ev(6, 2))
    nH = Meta(Ho, p.width * 2)
    for c in [0, 9, 16, 27, 26, 6, 1, 8, 10, 15]: nH.add(*p.children[c])
    nP = Meta([p72, padd(p72, psub(bps1, llc)), bps1, llc], p.width * 2)
    for c in [7, 2, 3, 4, 28]: nP.add(*p.children[c])
    nF = Meta([bps2, p.ev(24, 2), p.ev(25, 0), p252, padd(p252, psub(llc, bps1))], p.width * 2)
    for c in [21, 20, 22, 23, 24, 25]: nF.add(*p.children[c])
    A = Ho[2]; B = padd(Ho[1], psub(Ho[4], Ho[5])); C = tpt(rot_about(B, -math.pi / 3), A)
    nT = Meta([B, C, A], p.width * 2); nT.add(*p.children[11])
    for m in (nH, nP, nF, nT): m.recentre()
    return [nH, nT, nP, nF]

def hats(levels=3):
    tiles = [_H(), _T(), _P(), _F()]
    for _ in range(levels - 1):
        tiles = metatiles(patch(*tiles))
    out = []
    tiles[0].flat(IDENT, out)
    return [(lab, [tpt(T, p) for p in HAT]) for lab, T in out]


if __name__ == '__main__':
    for lv in (1, 2, 3, 4):
        hs = hats(lv)
        print(lv, len(hs), sum(1 for l, _ in hs if l == 'H1'))
