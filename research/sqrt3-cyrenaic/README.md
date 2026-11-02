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
