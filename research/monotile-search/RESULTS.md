# Results

"candidate" = covers every disc up to the radius cap, but **no periodic (torus) tiling found up to the cap**. It is not a proof of aperiodicity; see README.md.

Caps: torus fundamental domain <= 12 tiles; disc radius <= 6 hexagon spacings; Heesch tested up to 5 coronas. All placements on the kite grid.

| n | shapes | does not tile | tiles periodically | candidate | Myers: tilers / non-tilers | match | wall time |
|---|---|---|---|---|---|---|---|
| 1 | 1 | 0 | 1 | 0 | 1 / 0 | yes | 0.0s |
| 2 | 2 | 1 | 1 | 0 | 1 / 1 | yes | 0.0s |
| 3 | 4 | 0 | 4 | 0 | 4 / 0 | yes | 0.0s |
| 4 | 10 | 5 | 5 | 0 | 5 / 5 | yes | 0.0s |
| 5 | 27 | 26 | 1 | 0 | 1 / 26 | yes | 0.4s |
| 6 | 85 | 14 | 71 | 0 | 71 / 14 | yes | 0.6s |
| 7 | 262 | 207 | 55 | 0 | 55 / 207 | yes | 3.8s |
| 8 | 873 | 833 | 39 | 1 | 40 / 833 | yes | 25.0s |
| 9 | 2917 | 2162 | 755 | 0 | 755 / 2162 | yes | 36.9s |
| 10 | 10011 | 9996 | 14 | 1 | 15 / 9996 | yes | 262.6s |

"match" compares (periodic + candidate, does-not-tile) with Joseph Myers' independent counts (his tiler count includes the hat at n=8 and the turtle at n=10).

## Heesch numbers of the non-tilers

| n | H=0 | H=1 | H=2 | H=3 | H=4 | H=5 |
|---|---|---|---|---|---|---|
| 1 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2 | 1 | 0 | 0 | 0 | 0 | 0 |
| 3 | 0 | 0 | 0 | 0 | 0 | 0 |
| 4 | 4 | 1 | 0 | 0 | 0 | 0 |
| 5 | 12 | 14 | 0 | 0 | 0 | 0 |
| 6 | 13 | 1 | 0 | 0 | 0 | 0 |
| 7 | 165 | 41 | 1 | 0 | 0 | 0 |
| 8 | 720 | 108 | 5 | 0 | 0 | 0 |
| 9 | 2093 | 69 | 0 | 0 | 0 | 0 |
| 10 | 9404 | 579 | 12 | 1 | 0 | 0 |

Highest Heesch number found: 3 (n10_00610).
Heesch here forbids holes in every corona (Kaplan's H_c). The values are not compared with any published polykite table; each corona structure is re-checked by independent code.

![n10_00610](heesch/n10_00610.png)

## Candidates

### n8_00131 (8 kites) — **the hat**
Covers discs up to R=6; no torus tiling with <= 12 tiles per fundamental domain.

![n8_00131](candidates/n8_00131.png)

### n10_03927 (10 kites) — **the turtle**
Covers discs up to R=6; no torus tiling with <= 12 tiles per fundamental domain.

![n10_03927](candidates/n10_03927.png)

## How the caps affect the result

Every shape that tiles periodically was found with a fundamental domain of at most the number of tiles below, and every non-tiler failed at the disc radius below. A shape becomes a (false) candidate if the torus cap is below the tiles it needs, or if the disc cap is below the radius at which it fails.

| n | most tiles per period needed | largest failing disc radius |
|---|---|---|
| 1 | 6 | - |
| 2 | 3 | 1.5 |
| 3 | 2 | - |
| 4 | 6 | 1.5 |
| 5 | 6 | 3 |
| 6 | 12 | 2 |
| 7 | 6 | 4 |
| 8 | 6 | 4 |
| 9 | 6 | 3 |
| 10 | 6 | 5 |

Shapes needing 12 tiles per period: n6_00035. With a torus cap below 12 they would show up as false candidates. Minimum periods come in whole hexagons, so an n-kite shape needs a multiple of 6/gcd(n,6) tiles per period (e.g. 6 for n = 7, 3 for n = 8 or 10, 2 for n = 9).


| torus cap (tiles) | disc cap (R) | candidates (n<=10) |
|---|---|---|
| 1 | 6 | 935 |
| 3 | 6 | 427 |
| 6 | 6 | 3 |
| 11 | 6 | 3 |
| 12 | 2 | 293 |
| 12 | 3 | 20 |
| 12 | 4 | 4 |
| 12 | 5 | 2 |
| 12 | 6 | 2 |

(Rows other than the last are worked out from the recorded minimum period size / failing radius, not re-run.)

## Validation (validate.py)

| shape | kites | largest disc covered (R, kites) | periodic search | result |
|---|---|---|---|---|
| kite | 1 | R=20 (8694 kites) | <= 60 tiles/domain (28 lattices, 0.0s) | periodic, 6 tile(s)/domain |
| hexagon | 6 | R=20 (8694 kites) | <= 60 tiles/domain (634 lattices, 0.06s) | periodic, 1 tile(s)/domain |
| hat | 8 | R=20 (8694 kites) | <= 60 tiles/domain (398 lattices, 98.16s) | none found |
| turtle | 10 | R=20 (8694 kites) | <= 60 tiles/domain (383 lattices, 156.11s) | none found |
