# Inverse cut-and-project (2 Nov 2026, 07:26-07:35)

Question: given only where each tile sits and how it is turned (the data a projection scheme gives), can a solver find the tile?
Unknowns: one yes/no per grid cell near the origin ("in the shape"). Constraint: every patch cell covered by exactly one placed copy.

Hat control (inverse.py; patch of 1,156 hats mapped onto the kite grid with one global alignment, 9,248 cells, no overlaps):
- unknown region radius 6 (68 cells), patch radius 25: exactly 4 solutions, all of size 8; the only connected one is the hat.
- unknown region radius 9 (144 cells), patch radius 30: exactly 8 solutions; again the only connected one is the hat.
So positions + orientations determine the hat uniquely among connected tiles (the other solutions trade kites between
neighbours and fall apart). The hard data is the labelled point pattern; the shape then follows.

Silver plan: build silver labelled point patterns (Ammann–Beenker-type projection, deformed onto the 45° grid with a rational
density; orientation label read from where the point falls in the window), then run the same solver.

## Silver run 1 (07:40-07:50)
silver.py: Ammann–Beenker vertices (window method) deformed onto the 45° grid with edge star (a,0),(b,b),(0,c),(-d,d).
Valid shape change checked (same orientation signs as E). Rational density: tile frequencies rhombs (2-√2)/4, squares (√2-1)/2,
so the mean tile area is rational iff 2ac + 4bd = (a+c)(b+d). Star (3,1,3,6): 1,380 tiles, no overlaps, mean area 10.489 (theory 10.5
= 42 grid triangles). 18 such stars with entries <= 7.
Solver (unknown shape within radius 5-6 + one orientation per label, every cell covered once):
- labels = tile type (6), star (3,1,3,6), r = 5 and r = 6: no solution.
- labels = tile type + the 4 neighbours' types: running (slower). modal_silver.py sweeps all 18 stars x both label schemes.

## Silver run 2 on Modal (2 Nov 09:20-09:35, Razvan's account)
- labels = tile type: all 18 rational-density stars -> no shape (exact UNSAT, ~1,400-1,800 patch cells, 320 unknown cells, 6 labels).
- labels = tile type + 4 neighbour types (120 classes): (4,1,4,6) none, (3,1,2,7) none; remaining 16 running.
- Note: each run rewrites results/silver_inverse.json; the type-only results above are from the terminal log. To fix: one file per scheme.
