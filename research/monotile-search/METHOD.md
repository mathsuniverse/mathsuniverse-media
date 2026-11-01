# A countable search for new monotile candidates

Razvan, 1 Nov 2026: "first discover a countable way to generate or search for the new shape."

## 1. The space is countable

A candidate shape is a *polyform*: n cells glued edge to edge on a fixed periodic grid G.
For each grid G and size n there are finitely many polyforms P(G, n) (up to rotation and reflection),
and they can be listed exactly once each in a fixed canonical order (Redelmeier-style growth with a canonical form).
So every shape gets a finite address:

    shape = (grid index g, size n, position i in the canonical list of P(G_g, n))

Ordering all addresses by c = g + n (then by i) puts every possible shape on a single numbered list:
shape #1, #2, #3, ... Nothing is skipped, and the list never ends.

Grids, in order (all periodic, edge-to-edge):
1. kites ([3.4.6.4] dual): where the hat and turtle live (Smith 2023)
2. drafters (30-60-90 triangles, [4.6.12] dual): finer; every polykite is also a polydrafter
3. triangles (polyiamonds), 4. squares (polyominoes), 5. hexagons (polyhexes), 6. the other Laves grids

Known sizes on the kite grid (OEIS A057786): 1, 2, 4, 10, 27, 85, 262, 873, 2917, 10011, 34561, 120815, ...

## 2. Each shape gets a finite test with three outcomes

For a shape s and a "budget" k:
- STUCK: some disc of radius <= k cannot be covered by copies of s. **Proof** that s never tiles.
- PERIODIC: copies of s tile a torus with <= k tiles per repeating block. **Proof** that s tiles periodically.
- OPEN: neither found within budget k.

Both proofs are finite certificates, re-checkable by independent code (tiler.py does this).

## 3. Dovetailing: the search that eventually settles everything that can be settled

    for k = 1, 2, 3, ...:
        for every shape with address <= k still OPEN:
            run the test with budget k

- Every shape that does not tile is eventually marked STUCK
  (by the extension theorem, a shape that fails to tile fails on some finite disc).
- Every shape that tiles periodically is eventually marked PERIODIC.
- The shapes that stay OPEN forever are exactly the aperiodic monotiles on that grid
  (the shapes that tile, but never periodically).

So the procedure is a sieve: anything still OPEN after a large budget is a **candidate**.
It can never confirm a candidate by itself: staying OPEN at every finite budget is the
infinite question (the Collatz-like part). Confirmation needs a proof (section 5).

The 1 Nov run is stage k ≈ (12 tiles, radius 6) on kites n <= 10: 13,212 shapes,
all settled except the hat and the turtle, the two known members of the hat family.

## 4. Generating instead of searching

Blind listing grows about 3.5x per extra cell. Two ways to aim:

a. **Deform known aperiodic tiles** (countable too): the hat sits in a family Tile(a, b) of
   shapes with edges of lengths a and b; every member with a ≠ b, both nonzero, is aperiodic, and
   Tile(1,1) led to the Spectre. Generate edge-modified variants (grid-preserving bumps and
   notches along matching edges) and run them through the same sieve.

b. **Structure first**: the hat's aperiodicity comes from a hierarchy (copies group into
   metatiles H, T, P, F, which group again, forever). Enumerate small substitution hierarchies,
   then solve for a single shape whose copies realise the metatiles. A shape found this way
   arrives *with* the outline of its proof.

## 5. From candidate to claim

1. Push the budget far (big tori, big discs); most false candidates fall here.
2. Look for a hierarchy in large patches (repeating clusters at growing scales).
3. Write the substitution and check it (as Kaplan's hatviz does for the hat).
4. Before any public claim: send it to specialists (e.g. Craig S. Kaplan) for checking.

Never call a candidate a new aperiodic monotile until step 4 is complete.

## Plan
- Now: kites n = 11 (34,561 shapes), then n = 12 (120,815).
- Next: drafters (finer grid, contains the hat family), with a cheap first filter.
- Then: route 4a (deformations of the hat family) and route 4b (structure first).
