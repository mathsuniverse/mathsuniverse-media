# √3 target: Cyrenaic tilings with Ammann-bar rules (built 2 Nov 2026, 07:00-07:40)

Source: C. Porrier & T. Fernique, "Ammann Bars for Octagonal Tilings" (arXiv 2205.13973); their SageMath code
github.com/cporrier/Cyrenaic (CC0). cyrenaic.py is a numpy/shapely port (no Sage needed).

Checks on our own build:
- Tiling valid: radius-30 patch, 1,820 tiles, overlap area 0, disc of radius 26 fully covered.
- Six tile shapes; frequencies match the Plücker coordinates of the slope (all in Q(√3)):
  (0,1) 0.1536 vs 0.1547 · (0,2) 0.3310 vs 0.3333 · (0,3) 0.0903 vs 0.0893 · (1,2) 0.0883 vs 0.0893 · (1,3) 0.0883 vs 0.0893 · (2,3) 0.2484 vs 0.2440
- Decorated tileset (tile + Ammann segments from lines through every vertex in the 4 subperiod directions):
  36 distinct tiles up to translation at neighbourhood radius 2, 4, 6, and again on a radius-48 patch = the paper's 36.
  (The code's comments mention 30 for a later AA-exact version; the paper and our port give 36.)
Picture: cyrenaic_patch.png. Next: turn bar crossings into edge bumps (jigsaw pieces), then SAT for one shape that dissects them.

## Design check before the jigsaw step (2 Nov, 07:05)
Tile areas under the bar-carrying ("fine") projection A: 1, 1.366 (= (1+√3)/2) ×3, 0.366, 2.366. Irrational ratios, so no single
shape can be cut exactly into these pieces (same area argument as Lemma A). The bars need this exact geometry (A e_k ∥ A p_k),
so the geometry can't simply be deformed onto a lattice while keeping straight bars.
Way through: treat bar crossings as EDGE LABELS (bar continuity = matching crossing positions on shared edges), which is
combinatorial and survives any valid deformation (integer projections with the same minor signs as E), and then encode labels as bumps.
Caveat: the hat is not an exact dissection of its metatiles (hats cross cluster outlines), so "one shape cut into every piece"
is stricter than needed; the honest target is a shape whose tilings are forced to be combinatorially Cyrenaic.
Plan: (1) extract the edge-label version of the 36 tiles and check, with SAT, that labels alone still force non-repetition;
(2) integer deformation + bump jigsaw; (3) shape search against (1)-(2) with the slope test as a filter.
