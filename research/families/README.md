# Interpolating families on the 45° grid (2 Nov 2026, 13:30-13:45)
Razvan (13:25): long runs mean we don't know where to search. The hat's own structure says where: the family Tile(a,b)
(hexagonal grid, edges 1 and √3): the ends Tile(0,1), Tile(1,0) tile periodically, in incompatible ways; every a ≠ b in between is aperiodic.
Silver analogue: polygons whose edges run along the axes (length a) and the diagonals (vector b·(±1,±1), length b√2); closure for all
(a,b) means axis vectors and diagonal vectors each sum to zero. Integer a, b put every vertex on the grid, so Tile(a,b) is a 45°-grid polyform.
families.py enumerates them (turn sequences, closure pruning, canonical up to cyclic shift, 90° rotations, reflection; simple for 5 ratios):
edges 4: 2, 6: 12, 8: 50, 10: 336, 12: 3,674 families (odd edge counts cannot close).
Each family is sieved at (a,b) = (1,0), (0,1), (1,1), (1,2), (2,1), (2,3), (3,2). HAT-LIKE = both ends PERIODIC and an interior shape OPEN.
modal_families.py runs all of them.
- First Modal attempt (14:10-14:50): only 15 families finished in 40 min; workers starved Modal's heartbeat (in-process SAT) and
  the ends Tile(1,0)/(0,1) were often wrongly "not simple" (zero-length edges kept as duplicate vertices). First 15: all PERIODIC
  in between; the regular-octagon family is PERIODIC at both ends and STUCK in between.
- Fix: zero-length edges dropped; screening budget torus <= 8 tiles, disc R <= 4 (OPEN shapes get the full test later);
  5 ratios; every family in its own child process with a 150 s cap. Local check: 1.1 s per family.
- 14:57 run, first two "HAT-LIKE" flags ([0,1,3,2,4,6,5,7] and its mirror-type twin [0,1,7,6,5,3,4,2], Tile(1,2), 52 cells): FALSE ALARMS.
  Full test (torus <= 12, disc R <= 6): both STUCK at radius 5. The screen only went to R = 4. Every screen OPEN must be re-tested.
- Hat features check (Razvan 15:29): we lacked (1) straight double edges (the hat has one) and (2) enough edges (hat = 14 counting it).
  families.py now allows straight continuations (option, max count incl. wrap-around) and slices the enumeration by the first two turns
  (verified: slices reproduce the whole set at 10 edges, 988 = 988). Counts with at most one straight pair: 8 edges 114, 10: 988;
  12: ~16-17k before the wrap fix. 14 edges expected ~10^5.
- modal_families14.py: enumerate (49 slices) -> quick screen -> full re-test of every OPEN, one command; --m 16 for the next size.
- 12-edge run complete (4,074 families, 20,355 shapes screened): PERIODIC 5,960 · STUCK 4,555 · degenerate/not simple 3,894 ·
  screen timeout 1,181 · OPEN 56. Full re-test of the 56: 37 STUCK directly; 19 timed out (the full test searched tori before large
  discs); a disc-only check shows all 19 jam at radius 5 (one at 6). Result: 0 of 56 survive. No candidate at 12 edges.
- Lesson: discs first. families.disc_first() covers discs up to R (cheap, catches jams) before the periodic search; screen R <= 5.
- Optimised 14-edge run (Razvan 16:50): asymmetric outlines only (the hat has no symmetry; removes ~10%); hat signature tested
  ends first: Tile(1,0) and Tile(0,1) must be real shapes (non-degenerate), cover discs to R=3 and tile periodically, else the
  family is skipped; only then Tile(1,1), (1,2), (2,1) are tested discs-first. 10-edge sample: 52 of 60 families skipped
  instantly (degenerate end), 8 tested; median seconds, one outlier 256 s (capped at 150 s on Modal). Chunks of 60.
