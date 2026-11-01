# Results: projection-first search (1 Nov 2026)

Summary: no OPEN candidate. No shape made of whole tiles partitions any of the three quasicrystals.
Lemma A says this must happen, and the exhaustive search for k ≤ 8 hits the obstruction at very small radius.
Overlapping coverings by one cluster do exist (the unit regular 8-, 10- and 12-gon clusters cover AB, Penrose
and the 12-fold shield tiling completely), but a covering with overlaps is not a monotile tiling.

## 1. Generators and validation

All three are cut-and-project sets with exact integer vertex coordinates (Z⁴, Z⁵/Z(1,1,1,1,1), Z⁴ = Z[ζ₁₂]).

| tiling | field | checks | ratio | measured (R = 20 / 40 / 80 / 160) | exact |
|---|---|---|---|---|---|
| Ammann–Beenker (multigrid, Z⁴) | Q(√2) | 0 bad edges, 0 position collisions, all 6,241 vertices (R = 40) inside the octagon window (area 2+2√2) | rhombs/squares | 1.3899 / 1.4111 / 1.4110 / **1.41430** | √2 = 1.41421 (window areas: 2√2 : 2, error 2e-16) |
| Penrose P3 (pentagrid, Σγ = 0) | Q(√5) | 0 bad edges, all 6,358 vertices (R = 40) inside their index-slice pentagons; index 2,3 : 1,4 = 2.65 (φ² = 2.618) | thick/thin | 1.5800 / 1.6209 / 1.6163 / **1.61839** | φ = 1.61803 (grid-pair densities sin 72° : sin 36°) |
| 12-fold shield (Z⁴, dodecagon window r = 1) | Q(√3) | 0 crossing edges (R ≤ 40), faces are only unit squares, unit triangles and shields, all 4,852 shields congruent (angles 90,90,90,150,150,150) | square/shield | 1.8021 / 1.7535 / 1.7476 (R=70) / **1.7401** (R=100) | √3 (window areas, error 4e-15) |
| | | | triangle/shield | 5.4844 / 5.4787 / 5.4809 / **5.4815** | 2+2√3 = 5.4641 |
| | | | triangle/square | 3.0434 / 3.1244 / 3.1363 / **3.1501** | (6+2√3)/3 = 3.1547 |

The exact column comes from `window_freq.py`: frequency = area of ∩ᵢ (W − uᵢ*) summed over orientations. The
square–triangle–rhomb windows tried (dodecagon scale scan in `dodecagonal.py scan`) gave crossing edges or
mixed faces; the clean Z⁴ model set with a regular dodecagon window is Gähler's **shield** tiling (squares,
triangles, shields). It is the 12-fold case used below. The Stampfli/Socolar variants were not built.

## 2. Lemma A, checked numerically (one line per tiling)

* **AB:** rhombs/squares → √2 (irrational). Every copy of a k-tile cluster has a fixed composition (a, b), so a
  partition would force a/b = √2. Impossible.
* **P3:** thick/thin → φ (irrational). Same argument.
* **Shield (12-fold):** square/shield → √3 and triangle/shield → 2+2√3 (irrational). Same argument.

Companion remark (same argument, applied to splitting instead of merging): in all three tilings the prototile
areas are rationally independent (1 : 1/√2; φ : 1; 1 : √3/4 : (3+√3)/2 shield). So no single shape S
dissects every prototile either: a·|S| = 1 and b·|S| = 1/√2 cannot both hold. Any single-shape relation to these
tilings must therefore be combinatorial (mutual local derivability, as hat ↔ CAP), not a geometric union or
dissection of tiles.

## 3. Partition search (steps 2–4)

Disc centred at the origin. Interior (centroid ≤ R) is covered exactly once, the buffer ring (R, R+1.5] at most once.
Shapes are enumerated from all edge-connected clusters in the R = 8 disc and identified up to congruence of their union.
Since every placement used at R ≤ 4.5 lies inside the R = 8 disc, the list is complete for those radii.

| | k=1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | total |
|---|---|---|---|---|---|---|---|---|---|
| AB shapes tested | 2 | 3 | 12 | 39 | 157 | 585 | 2,334 | 9,040 | **12,172** |
| P3 shapes tested | 2 | 4 | 16 | 55 | 208 | 759 | 2,823 | 10,467 | **14,334** |

Outcome at R = 3 (the first radius):

| | fails count test | some interior tile uncoverable | SAT says UNSAT | partitions R=3 | partitions R=4.5 |
|---|---|---|---|---|---|
| AB | 1,902 | 10,052 | 216 | **2** | **0** |
| P3 | 3,834 | 10,341 | 159 | **0** | 0 |

The only shapes that partition anything are two AB shapes, and only the R = 3 disc:
* #1477: square + rhomb hexagon (k = 2, composition 1:1), boundary word 0,1,2,4,6,5;
* #3554: k = 5 (2 squares + 3 rhombs), boundary word 0,2,1,3,4,5,6,7. Picture: `partition_AB_shape3554_R3.png`.

Both fail at R = 4.5. Both also pass Beauquier–Nivat (they tile the plane by translations), so they are periodic.

**Periodicity census (step 3, k ≤ 6, sufficient tests only):**
AB: BN 61, Conway 9, not caught 719, non-simple 9. P3: BN 78, Conway 5, not caught 953, non-simple 8.
The "not caught" shapes are not candidates, because they all fail the partition test.

**Controls (step 4).** Periodic square lattice (`SQ`): all 9 polyominoes with k ≤ 4 partition the discs
R = 3, 5, 8 and all pass BN, as they should. The single AB square and single AB rhomb (and the single P3
rhombs) fail the count test immediately, as they must, since the patch contains both tile types. The task's
expectation that "single square, single rhomb must partition" holds only in a one-tile-type tiling; the SQ run is that control.

**OPEN candidates: none.**

## 4. Covering clusters (overlaps allowed; coordinator's extension)

Copies of one cluster, taken where they occur in the tiling, must cover every tile of the disc RC. Lemma A does not
apply, because copies may overlap.

**Unit regular n-gon clusters (`covering_polygon.py`).** Covered fraction of the disc, with copies used by a greedy cover:

| tiling | cluster | composition | occurrences (RC=30) | covered RC=15 | covered RC=30 | greedy copies (RC=30) | overlap factor |
|---|---|---|---|---|---|---|---|
| P3 | unit decagon (Gummelt's shape) | 5 thick + 5 thin | 984 | 100% | **100%** | 526 | 1.51 |
| AB | unit octagon | 2 squares + 4 rhombs | 2,383 | 100% | **100%** | 851 | 1.49 |
| Shield | unit dodecagon | 2 shields + 3 squares + 8 triangles | 1,161 | 100% | **100%** | 490 | 1.79 |

So a single covering cluster exists for silver (AB) and for the √3 tiling, at least in patches of radius 30
(about 3,500 tiles), just as Gummelt's decagon does for golden. Pictures: `cover_ngon_*.png`.

**Exhaustive small clusters (k ≤ 4), RC = 15:**
* Undecorated: AB is covered already at **k = 2** (square + rhomb pair, the only class at k=2 that covers). Shield
  and P3 are covered at **k = 4** (2 classes each). These are trivial coverings with no forcing content.
* Decorated (a copy must also match its whole vertex-collar): no cluster with k ≤ 4 covers (best AB 44%, Shield 42%,
  P3 41%). Round vertex-centred clusters C_ρ up to ρ = 7 (about 190 tiles) do not cover either (best AB 99.4%,
  Shield 87.9%, P3 93.4%). **This test fails its own positive control:** it does not reproduce a Gummelt covering for P3.
  Matching the full collar is much stricter than Gummelt's decorated overlap rules. So these negative numbers say
  nothing about AB or the shield tiling.

**Does a covering give a single shape?** Not by itself. A Gummelt-type statement needs, in addition, overlap
rules (decorations) such that every covering obeying them is the quasicrystal. That is a theorem for the decagon
(Gummelt 1996; Steinhardt–Jeong 1996). Octagonal analogues for AB are discussed by Ben-Abraham and Gähler
(Phys. Rev. B 60, 860, 1999; to verify before citing). We did not test forcing. Also, a covering has overlaps,
so it is not a tiling by one tile.

## 5. Answer to "is there any route from these projections to a single shape?"

1. **Merge whole tiles into one shape S (partition):** closed by Lemma A. Every one of 26,506 shapes with k ≤ 8
   already fails at R ≤ 4.5.
2. **Split tiles into one shape (dissection):** closed by the area remark, since the prototile areas are rationally independent.
3. **Cover with one cluster, overlaps allowed:** open and non-trivial only with decorations and overlap rules.
   The undecorated unit octagon (AB) and unit dodecagon (shield) cover large patches. Next step: put Ammann-bar or
   arrow decorations on the octagon and dodecagon, and test with SAT whether the overlap rules force the tiling
   (does every rule-respecting covering of a large disc reproduce AB / shield?).
4. **Combinatorial (MLD) route, as for the hat:** a single tile S whose tilings are mutually locally derivable from
   the quasicrystal, with the irrational carried by orientation frequencies of congruent copies (hat:
   unreflected/reflected → φ⁴). This is the only route compatible with Lemmas A and B, and it is not addressed by this prototype.

## Compute

About 45 CPU-minutes on one worker (merge search AB 4 min, P3 7 min; covering runs about 30 min; the rest is small).
Patches: discs up to R = 160 for frequencies, R = 13 for partition SAT, R = 38 for coverings.

## Novelty check (1 Nov 2026, 22:45)
Not new. Ammann–Beenker (Ammann 1970s; Beenker 1982) and Gähler's shield tiling (1988) are classical.
The octagon covering is Ben-Abraham & Gähler, "Covering cluster description of octagonal MnSiAl quasicrystals",
Phys. Rev. B 60 (1999), now verified. Dodecagonal single-cluster coverings exist too (arXiv 1208.1845, ship tiling, 2012).
Our greedy covers re-confirm these; they include no forcing rules.
