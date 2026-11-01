# Projection-first search (route C of FORMULATION.md section 11)

Idea: the hat's tilings are cut-and-project sets (Baake, Gähler, Mazáč, Sadun 2023) and the hat merges finer
pieces into one shape. Here we try the reverse for metallic-type quasicrystals: project a known quasicrystal,
then look for ONE shape S made of its tiles such that copies of S (rotations and reflections allowed)
partition the patch, or, in the weaker Gummelt sense, cover it with overlaps.

Results and honest wording: see `RESULTS.md`. Nothing here is called "aperiodic"; the strongest label used
is "OPEN candidate", and none was found.

The partition route is closed by Lemma A (FORMULATION.md section 13). The undecorated unit 8-, 10- and 12-gon clusters
cover AB, P3 and the 12-fold shield tiling with overlaps; whether decorated overlap rules force the tiling is the open next step.

## Files

| file | what it does |
|---|---|
| `projection.py` | de Bruijn multigrid = cut-and-project generators with exact integer vertex coordinates: Ammann–Beenker (silver, Z⁴, octagon window), Penrose P3 (golden, Z⁵, Σγ = 0, pentagon windows), and a periodic control (square lattice, `SQ`). Validation: edge-to-edge check, every vertex's internal coordinate inside the window, tile-type ratios on discs R = 10…160. Writes `validation.json`, `AB_patch_R20.png`, `P3_patch_R20.png`. |
| `dodecagonal.py` | 12-fold (√3) model set from Z⁴ = Z[ζ₁₂] with internal star ζ → ζ⁵ and a regular-dodecagon window (circumradius 1). Joining unit-distance points gives Gähler's shield tiling (squares, triangles, shields; no crossing edges, all shields congruent). Writes `validation_12fold.json`, `SH_patch_R20.png`. `python3 dodecagonal.py scan <scales>` reproduces the window-size scan. |
| `window_freq.py` | exact prototile frequencies from window areas (area of ∩ (W − uᵢ*) summed over orientations). Writes `window_frequencies.json`. |
| `shapes.py` | exact region canonical forms (boundary edges under the point group D8 / D10 / D4), boundary words, Beauquier–Nivat and Conway criteria on words. |
| `merge_search.py` | step 2: enumerate all edge-connected clusters of k ≤ KMAX tiles (ESU enumeration), group them by congruence class of their union region, and for each class run a SAT exact cover of a disc (interior exactly once, buffer ring at most once) at increasing radii. `python3 merge_search.py AB 8 3,4.5,6,8,10,13 8` |
| `periodic.py` | step 3: BN / Conway census of all shapes with k ≤ 6, and classification of every partition survivor. Writes `results/periodic.json`. |
| `render_partition.py` | PNG of each partition found (`partition_*.png`) and of the shape (`shape_*.png`). |
| `covering.py` | coordinator's extension: Gummelt-style covering clusters (overlaps allowed), plain and decorated (1-vertex-collar), exhaustive k ≤ 4 and round clusters C_ρ(v). `python3 covering.py AB 30 15 4 1,1.5,...` Writes `results/cover_*.json`, `cover_*.png`. |
| `covering_polygon.py` | covering by the unit regular n-gon cluster (8 AB, 10 P3 = Gummelt's decagon shape, 12 shield): occurrences that are exact unions of tiles, coverage fraction, greedy copy count. `python3 covering_polygon.py AB 38 30`. Writes `results/cover_ngon_*.json`, `cover_ngon_*.png`. |

## Definitions used

* **Partition test at radius R.** Interior = tiles with centroid within R of the origin: covered exactly once.
  Buffer = tiles with centroid in (R, R + 1.5]: covered at most once. Placements = clusters of the patch whose
  union is congruent to S, lying inside interior ∪ buffer and touching the interior. A counting precheck
  (some m with a·m and b·m inside the allowed ranges of the two tile types) runs before SAT (CaDiCaL 1.5.3 via PySAT).
* **Region congruence**, not tile-decomposition congruence: two clusters are the same S if their unions are
  congruent, even if decomposed differently (AB and P3 both have such flips). The tile counts per type are
  nevertheless fixed by the area (square:rhomb areas 1 : 1/√2, thick:thin areas φ : 1 are rationally independent).
* **Covering cluster.** Copies of one cluster C (as a configuration of tiles, up to rotation/reflection),
  taken where they occur in the tiling, must cover every tile of the disc RC; overlaps allowed.
  "Decorated": C must also match its vertex-collar (all tiles touching C), a proxy for matching-rule decorations.

## Reproduce (≈ 40 min on one core)

```
python3 projection.py; python3 dodecagonal.py; python3 window_freq.py
python3 merge_search.py SQ 4 3,5,8 6
python3 merge_search.py AB 8 3,4.5,6,8,10,13 8
python3 merge_search.py P3 8 3,4.5,6,8,10,13 8
python3 periodic.py results/SQ_k4.json results/AB_k8.json.gz results/P3_k8.json.gz
for s in AB SH P3; do python3 covering_polygon.py $s 38 30; python3 covering_polygon.py $s 24 15; done
for s in AB SH P3; do python3 covering.py $s 30 15 4 1,1.5,2,2.5,3,3.5,4,4.5,5,5.5,6,7; done
```
(`merge_search.py` writes plain `.json`; the committed copies are gzipped.)
