# Silver via Labbé's metallic-mean Wang tiles (2 Nov 2026, 11:00-11:15)
- silver_wang.py: the 25 silver Wang tiles (copied from slabbe, S. Labbé, GPLv2). SAT: no periodic tiling with periods up to 12x12;
  10x10, 20x20, 40x40 squares tileable (instant). Matches the paper (aperiodic).
- inverse_wang.py: one unknown polyomino S per Wang tile (anchor L*(i,j)), orientation chosen per tile type, |S| = L².
  Trivial answers (shapes tiling by L·Z² alone) excluded. Control without that exclusion: solver finds them at once (5 shown, L=3).
  Result: L = 3 (reach 3.75) and L = 4 (reach 4.5): NO non-trivial shape. modal_wang.py sweeps L = 3..7, two reaches.
