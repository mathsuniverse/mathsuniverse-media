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

## Steps 1-2 done (2 Nov, 07:15-07:45)
- Step 1 (labels.py): bars as edge labels. Distinct labels per edge direction: 6, 1, 15, 6. Tiles with 4 edge labels: exactly 36 types,
  the paper's 36 again, now in purely combinatorial form (bar continuity = equal labels on a shared edge).
- Step 2 (jigsaw.py): deformed onto the 45° grid with e0=(7,0), e1=(0,5), e2=(4,-4), e3=(4,4) (same orientation signs as E, so
  a valid shape change); labels become teeth on edge slots. 36 jigsaw pieces of 78-140 tetrakis cells (pieces.json).
  First attempt (teeth = label code only) FAILED: pieces could slide half an edge ("brick" offset) and tile periodically with period
  lattice (5,4,3). Fix: an alignment key on every edge (tooth on the first slot, none on the last). After the fix:
- tilesat.py: plain parallelograms tile periodically at period area 20; the 36 keyed jigsaw pieces have NO periodic tiling with period
  area up to 40 (all lattices, 115 s). They tile the real Cyrenaic patch by construction (disc SAT for R >= 6 ran out of memory here;
  move it to Modal). Larger periods still to test (Modal).
