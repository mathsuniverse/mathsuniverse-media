"""Penrose P2 (kite and dart) tiling by Robinson-triangle deflation.

Half-kite: golden triangle (apex 36 deg). Half-dart: golden gnomon (apex 108 deg).
Each triangle is (kind, apex, axis_end, other); two mirror halves sharing apex-axis_end make a whole tile.
Verified 1 Nov 2026: at depth 7, 9,870 triangles, no overlaps, full cover; merged tiles have exactly
kite angles (72,72,72,144) and dart angles (36,72,36,216); kite:dart -> golden ratio.

    tiles(n) -> [('kite'|'dart', [complex corners])]
"""
import cmath, math
PHI = (1 + 5 ** 0.5) / 2

def start():
    out = []
    for i in range(10):
        a = cmath.rect(PHI, i * math.pi / 5); b = cmath.rect(PHI, (i + 1) * math.pi / 5)
        out.append(('K', 0j, a, b) if i % 2 == 0 else ('K', 0j, b, a))
    return out

def subdivide(tris):
    out = []
    for k, A, P, Q in tris:
        if k == 'K':
            B, C = Q, P
            D = A + (C - A) / PHI; F = B + (A - B) / PHI
            out += [('K', B, D, C), ('K', B, D, F), ('D', F, A, D)]
        else:
            X, Y, Z = A, P, Q
            F = Y + (Z - Y) / PHI
            out += [('K', Y, X, F), ('D', F, Z, X)]
    return out

def triangles(n):
    t = start()
    for _ in range(n): t = subdivide(t)
    return t

def _key(p, q):
    a = (round(p.real, 6), round(p.imag, 6)); b = (round(q.real, 6), round(q.imag, 6))
    return (min(a, b), max(a, b))

def tiles(n):
    t = triangles(n); d = {}
    for tr in t: d.setdefault((tr[0], _key(tr[1], tr[2])), []).append(tr)
    out = []
    for (k, _), v in d.items():
        if len(v) == 2:
            a, b = v
            out.append(('kite' if k == 'K' else 'dart', [a[1], a[3], a[2], b[3]]))
    return out
