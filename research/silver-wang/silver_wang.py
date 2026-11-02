"""Labbé's silver (n = 2) metallic-mean Wang tiles: 25 tiles, aperiodic, dynamics = rotation by 1+√2 on the torus.
Tile list copied from slabbe (S. Labbé, GPLv2), slabbe/arXiv_2403_03197.py, metallic_mean_wang_tile_set(2);
paper: Metallic mean Wang tiles I/II (arXiv 2312.03652, 2403.03197; Forum Math. Sigma 2025). Tile = (East, North, West, South).
Here: SAT checks that (1) no periodic tiling exists for small periods, (2) large squares can be tiled."""
import sys, time
from pysat.solvers import Solver
from pysat.card import CardEnc, EncType
from pysat.formula import IDPool

T2 = [('000','000','002','002'),('000','001','012','002'),('001','000','002','012'),('001','001','012','012'),
      ('001','011','013','012'),('001','111','000','112'),('002','111','001','112'),('011','001','012','013'),
      ('011','011','013','013'),('011','111','000','113'),('012','111','001','113'),('012','112','011','113'),
      ('013','111','002','113'),('013','112','012','113'),('111','001','112','000'),('111','002','112','001'),
      ('111','011','113','000'),('111','012','113','001'),('111','013','113','002'),('112','012','113','011'),
      ('112','013','113','012'),('112','112','111','111'),('112','113','111','112'),('113','112','112','111'),
      ('113','113','112','112')]
E, N, W, S = 0, 1, 2, 3


def wang_sat(tiles, w, h, torus=False, extra=None):
    """Variables x[i][j][t]. Each cell exactly one tile; neighbours match. Returns the grid or None."""
    pool = IDPool(); x = lambda i, j, t: pool.id((i, j, t)); cl = []
    nt = len(tiles)
    for i in range(w):
        for j in range(h):
            lits = [x(i, j, t) for t in range(nt)]
            cl.append(lits); cl.extend(CardEnc.equals(lits, 1, vpool=pool, encoding=EncType.seqcounter).clauses)
            for di, dj, a, b in ((1, 0, E, W), (0, 1, N, S)):
                i2, j2 = i + di, j + dj
                if torus: i2 %= w; j2 %= h
                elif i2 >= w or j2 >= h: continue
                for t in range(nt):     # tile t at (i,j) forces a matching neighbour
                    cl.append([-x(i, j, t)] + [x(i2, j2, u) for u in range(nt) if tiles[u][b] == tiles[t][a]])
    with Solver(name='cd15', bootstrap_with=cl) as s:
        if not s.solve(): return None
        m = set(l for l in s.get_model() if l > 0)
        return [[next(t for t in range(nt) if x(i, j, t) in m) for j in range(h)] for i in range(w)]


if __name__ == '__main__':
    pmax = int(sys.argv[1]) if len(sys.argv) > 1 else 12
    t = time.time()
    per = [(w, h) for w in range(1, pmax + 1) for h in range(1, pmax + 1) if wang_sat(T2, w, h, torus=True)]
    print('periodic tilings with periods (w,h) <=', pmax, ':', per or 'none', round(time.time() - t, 1), 's')
    for n in (10, 20, 40):
        t = time.time(); print(f'{n}x{n} square tileable:', wang_sat(T2, n, n) is not None, round(time.time() - t, 1), 's')
