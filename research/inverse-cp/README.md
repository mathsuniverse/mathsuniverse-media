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
