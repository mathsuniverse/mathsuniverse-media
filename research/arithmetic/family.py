"""Two-piece arithmetic family: f(x) = q1*x on [q2, 1), q2*x on [1, q1), with q1 > 1 > q2, so f maps I = [q2, q1) into itself.
Aperiodic iff q1^a * q2^b = 1 has no solution with (a, b) != (0, 0) (multiplicative independence)."""
from fractions import Fraction as F
from math import log
import kari as K


def independent(q1, q2):
    # q1^a q2^b = 1 with integers a, b not both 0  <=>  log q1 / log q2 rational; test small exponents exactly
    for a in range(1, 13):
        for b in range(-12, 13):
            if b and q1 ** a * q2 ** b == 1: return False
    return True


def family(maxnum=6):
    out = []
    for p in range(2, maxnum + 1):
        for r in range(1, p):
            q1 = F(p, r)
            for u in range(1, maxnum + 1):
                for v in range(u + 1, maxnum + 1):
                    q2 = F(u, v)
                    if q1.denominator != r or q2.denominator != v: continue
                    if independent(q1, q2): out.append((q1, q2))
    return out


if __name__ == '__main__':
    import silver_wang as SW, sys
    rows = []
    for q1, q2 in family(int(sys.argv[1]) if len(sys.argv) > 1 else 4):
        T = K.tiles_for([(q1, q2, 1), (q2, 1, q1)], samples=1500, length=40)
        rows.append((len(T), str(q1), str(q2)))
    rows.sort()
    for r in rows[:25]: print(r)
    print('maps tested', len(rows))


def screen(maxnum=4, pmax=8):
    import silver_wang as SW
    rows = []
    for q1, q2 in family(maxnum):
        for name, pieces in (('[q2,q1)', [(q1, q2, 1), (q2, 1, q1)]), ('[1,q1/q2)', [(q1, 1, 1 / q2), (q2, 1 / q2, q1 / q2)])):
            T = K.tiles_for(pieces, samples=1500, length=40)
            per = next(((w, h) for w in range(1, pmax + 1) for h in range(1, pmax + 1) if SW.wang_sat(T, w, h, torus=True)), None)
            ok = SW.wang_sat(T, 16, 16) is not None
            rows.append((len(T), str(q1), str(q2), name, 'periodic ' + str(per) if per else 'no period <= %d' % pmax, 'tiles 16x16' if ok else 'CANNOT tile 16x16'))
    return sorted(rows)
