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
    return P.is_valid and P.area > 1e-9 and P.exterior.is_ccw and not F._pinched(pts[:-1])


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


def _seg_hit(a, b, c, d, eps=1e-9):
    """Closed segments ab and cd share a point (touching counts)."""
    def orient(p, q, r):
        v = (q[0] - p[0]) * (r[1] - p[1]) - (q[1] - p[1]) * (r[0] - p[0])
        return 0 if abs(v) < eps else (1 if v > 0 else -1)

    def on(p, q, r):
        return min(p[0], q[0]) - eps <= r[0] <= max(p[0], q[0]) + eps and min(p[1], q[1]) - eps <= r[1] <= max(p[1], q[1]) + eps
    o1, o2, o3, o4 = orient(a, b, c), orient(a, b, d), orient(c, d, a), orient(c, d, b)
    if o1 != o2 and o3 != o4 and o1 * o2 <= 0 and o3 * o4 <= 0 and (o1 or o2) and (o3 or o4):
        return True
    return (o1 == 0 and on(a, b, c)) or (o2 == 0 and on(a, b, d)) or (o3 == 0 and on(c, d, a)) or (o4 == 0 and on(c, d, b))


def outlines_fast(N, m, first=None, max_straight=1, max_turn=None, lam_f=None, necklace=True):
    """Same outlines as outlines(), but prefixes whose path already touches or crosses itself are cut at once.
    lam_f: float length of the second edge length (hat route); a prefix is cut only when it self-touches under BOTH
    length assignments (odd edges long, or even edges long), so no outline that is simple for either is lost."""
    R = F.Ring(N)
    P = R.pow
    vf = [R.f(P[k]) for k in range(N)]
    half = N // 2
    mt = max_turn or (half - 1)
    turns = [0] + [t for a in range(1, mt + 1) for t in (a, -a)]
    jc = {8: 3, 10: 3, 12: 5}[N]                 # Galois conjugate zeta -> zeta^jc: closure must hold there too
    cs2 = [(math.cos(2 * math.pi * jc * k / N), math.sin(2 * math.pi * jc * k / N)) for k in range(4)]

    def g(a):
        return math.hypot(sum(a[k] * cs2[k][0] for k in range(4)), sum(a[k] * cs2[k][1] for k in range(4)))
    geoms = [(1.0, 1.0)] if lam_f is None else [(1.0, lam_f), (lam_f, 1.0)]     # (even length, odd length)
    out = []

    # necklace=True: only turn sequences (t1..tm, tm = closing turn) that are the least of their cyclic shifts
    # (Fredricksen-Kessler-Maiorana prenecklace rule), so each outline is built once instead of m times.
    def rec(seq, ev, od, tsum, ns, paths, alive, ts=(), lp=1):
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
                if necklace:
                    kk = len(ts)
                    if kk and last_turn < ts[kk - lp]:
                        return
                    lp2 = lp if (kk and last_turn == ts[kk - lp]) else kk + 1
                    if m % lp2:
                        return
                out.append(tuple(seq))
            return
        e, o = R.f(ev), R.f(od)
        if math.hypot(*e) + math.hypot(*o) > rem + 1e-9 or g(ev) + g(od) > rem + 1e-9:
            return
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
                if necklace and ts and t < ts[len(ts) - lp]:
                    continue
            v = P[nd]
            npaths, nalive = [], []
            for gi, (le, lo) in enumerate(geoms):
                pts = paths[gi]
                ok = alive[gi]
                L = le if nd % 2 == 0 else lo
                q = (pts[-1][0] + L * vf[nd][0], pts[-1][1] + L * vf[nd][1])
                if ok:
                    a = pts[-1]
                    # new segment a-q against all earlier non-adjacent segments; the very first segment is adjacent
                    # to the closing edge only, so it is checked too (except when this is the closing step)
                    for j in range(1 if rem == 1 else 0, len(pts) - 2):
                        if _seg_hit(pts[j], pts[j + 1], a, q):
                            ok = False
                            break
                    if ok and rem > 1 and len(pts) >= 2 and abs(q[0]) < 1e-9 and abs(q[1]) < 1e-9:
                        ok = False                 # back at the start too early
                npaths.append(pts + [q]); nalive.append(ok)
            if not any(nalive):
                if k == 0:
                    break
                continue
            ne, no = (R.add(ev, v), od) if nd % 2 == 0 else (ev, R.add(od, v))
            if k == 0:
                nts, nlp = ts, lp
            else:
                kk = len(ts)
                nts = ts + (t,)
                nlp = lp if (kk and t == ts[kk - lp]) else kk + 1
            rec(seq + [nd], ne, no, tsum + (t if k else 0), ns + (1 if (k and t == 0) else 0), npaths, nalive, nts, nlp)
            if k == 0:
                break

    rec([], (0, 0, 0, 0), (0, 0, 0, 0), 0, 0, [[(0.0, 0.0)] for _ in geoms], [True] * len(geoms))
    return out
