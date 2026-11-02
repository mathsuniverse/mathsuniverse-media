# Arithmetic route (Kari-style), 2 Nov 2026 11:25-11:45
- kari.py: Wang tiles from any piecewise multiplicative map with rational multipliers (Mealy machine on balanced representations,
  tile rule q*a + s = b + s', collected exactly with Fractions). Reproduces Kari's 14 tiles for 2 on [1/2,1), 2/3 on [1,2);
  SAT: no period up to 8x8; 10x10, 20x20, 30x30 squares tile.
- family.py: two-piece maps f = q1 x on [q2,1), q2 x on [1,q1) (and the rescaled interval [1, q1/q2)); 18 multiplicatively independent
  pairs with entries <= 4; tile counts 12 to 42. The 12-tile (2, 1/3) set on [1/3, 2) is NOT aperiodic: it tiles with period 1x1
  (the all-zero rows; this is why Eigen-Navarro-Prasad need x0 >= 1 or Culik's extra tile). Our SAT screen catches it.
- Inverse single-shape search on Kari's 14 tiles: no non-trivial polyomino at L = 3, 4.
- modal_arith.py: every pair x both intervals x L = 3..5: screen for small periods, then the inverse search.
- Modal arith sweep (11:35-12:00): 108 jobs; 27 tile sets skipped as periodic (zero-row cheats); the rest: no single shape
  (L = 3..5, one copy per tile, orientation per type). 22 (pair, interval) sets pass the small-period screen (14 to 42 tiles).
- inverse_general.py (ideas 1-3): k copies per tile, free anchor offsets, labels type or type + neighbours; lazy connectivity cuts;
  every connected candidate sieved inside the search. Local test on Kari 14: L=3 -> 83 connected candidates, all PERIODIC;
  L=4, 2 copies -> 4, all PERIODIC; none OPEN. modal_loose.py: 4 tile sets x 8 (L, copies) x 2 label schemes = 64 jobs.
