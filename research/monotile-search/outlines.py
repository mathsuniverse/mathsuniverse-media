"""Equal-edge outlines in N directions (N = 8, 10, 12) with the hat/Spectre family rule: the edges in even directions
close up by themselves and the edges in odd directions close up by themselves (that is what makes Tile(a,b) a family).
Turns between consecutive edges: 1..N/2-1 steps either way, or straight (at most `max_straight` times, as in the hat).
Counter-clockwise (turns sum to N), simple polygons, one representative per shape (all rotations, mirror, cyclic shifts)."""
import math
import free as F
from shapely.geometry import Polygon


def outlines(N, m, first=None, max_straight=1, max_turn=None):
    R = F.Ring(N)
    P = R.pow
    vf = [R.f(P[k]) for k in range(N)]
    half = N // 2
    mt = max_turn or (half - 1)
    turns = [0] + [t for a in range(1, mt + 1) for t in (a, -a)]
    out = []

    def rec(seq, ev, od, tsum, ns):
        k = len(seq)
        rem = m - k
        if rem == 0:
            last_turn = (seq[0] - seq[-1]) % N
            if last_turn > half:
                last_turn -= N
            if abs(last_turn) > mt:
                return
            if ev == (0, 0, 0, 0) and od == (0, 0, 0, 0) and tsum + last_turn == N:
                if last_turn == 0 and ns + 1 > max_straight:
                    return
                out.append(tuple(seq))
            return
        # closure bound: what is still open must be coverable by the remaining unit edges
        e, o = R.f(ev), R.f(od)
        if math.hypot(*e) + math.hypot(*o) > rem + 1e-9:
            return
        # turning bound: the remaining turns (rem of them incl. closing) must reach N
        if abs(N - tsum) > (rem + 1) * mt:
            return
        for t in turns:
            if k == 0:
                nd = 0
            else:
                if first is not None and k <= len(first) and t != first[k - 1]:
                    continue
                nd = (seq[-1] + t) % N
                if t == 0 and ns + 1 > max_straight:
                    continue
            v = P[nd]
            if nd % 2 == 0:
                rec(seq + [nd], R.add(ev, v), od, tsum + (t if k else 0), ns + (1 if (k and t == 0) else 0))
            else:
                rec(seq + [nd], ev, R.add(od, v), tsum + (t if k else 0), ns + (1 if (k and t == 0) else 0))
            if k == 0:
                break

    rec([], (0, 0, 0, 0), (0, 0, 0, 0), 0, 0)
    return out


def canon(seq, N):
    m = len(seq); best = None
    for refl in (False, True):
        s = [(-x) % N for x in reversed(seq)] if refl else list(seq)
        for r in range(N):
            s2 = [(x + r) % N for x in s]
            for c in range(m):
                v = tuple(s2[c:] + s2[:c])
                if best is None or v < best:
                    best = v
    return best


def simple(seq, N, lens=None):
    R = F.Ring(N)
    pts = [(0.0, 0.0)]
    for i, d in enumerate(seq):
        v = R.pow[d] if lens is None else R.apply(R.rot[d], lens[i])
        x, y = R.f(v); pts.append((pts[-1][0] + x, pts[-1][1] + y))
    P = Polygon(pts[:-1])
    return P.is_valid and P.area > 1e-9 and P.exterior.is_ccw


def shapes(N, m, first=None, max_straight=1, max_turn=None):
    seen, out = set(), []
    for s in outlines(N, m, first, max_straight, max_turn):
        c = canon(s, N)
        if c in seen:
            continue
        seen.add(c)
        if simple(c, N):
            out.append(c)
    return out
