"""Window labels for the silver inverse search (how the hat's orientations arise): each tile's reference vertex v has an internal
coordinate w = IP v inside the octagonal window. The window is split into pieces (angular sectors x radial rings); the piece
containing w is the tile's label, and the solver picks one orientation per piece. Labels can also combine piece + tile type."""
import math, sys
import numpy as np
import silver as S


def window_labels(T, sectors=8, rings=2, with_type=False):
    W = [S.IP @ np.array(v, float) for _, v in T]
    rmax = max(math.hypot(*w) for w in W) + 1e-9
    lab = []
    for (tt, v), w in zip(T, W):
        ang = (math.atan2(w[1], w[0]) + 2 * math.pi) % (2 * math.pi)
        piece = (int(ang / (2 * math.pi) * sectors), min(rings - 1, int(math.hypot(*w) / rmax * rings)))
        lab.append((piece, tt) if with_type else piece)
    return lab


if __name__ == '__main__':
    import time, engine as E_
    st = tuple(int(x) for x in sys.argv[1:5]) if len(sys.argv) > 4 else (3, 1, 3, 6)
    B = S.star(*st); V, T, polys = S.build(16, B)
    for sec, rg, wt in ((8, 1, False), (8, 2, False), (16, 2, False), (8, 2, True)):
        lab = window_labels(T, sec, rg, wt); t = time.time()
        sols, msg = S.solve(T, polys, B, r=5.0, Rz=10.0, labels=lab, limit=5)
        print(st, f'sectors={sec} rings={rg} with_type={wt}', msg, '| solutions', len(sols), round(time.time() - t, 1), 's', flush=True)
        for Ssh, o in sols: print('    size', len(Ssh), 'connected', E_.is_connected(S.g, Ssh), flush=True)
