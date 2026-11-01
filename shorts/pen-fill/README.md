# One tile. It never repeats. (pen-fill, satisfying-maths Short)

Built 1 Nov 2026 from Razvan's idea: a pen starts in the middle and covers the floor, tile by tile, outwards.
- Renderer: short_pen_fill.py (std_short paper frame; hat geometry from hat_tiling.py, Kaplan's hatviz port, BSD-3,
  verified no overlaps / no gaps). Square frontier so the whole floor fills; slow single-tile start, then accelerating,
  camera zooms out 70 → 14 px per unit. Live counter of tiles and flipped tiles. Opens zoomed in on one green hat; sage greens, flipped hats gold (Razvan, 1 Nov 23:13).
- Narration: narr_penfill.py (HeyGen British Marcela), 69.7 s. pen-fill.mp4, subtitles.srt (en-GB).
- Prototype: pen_fill.py (no captions).
- Facts: hat = Smith, Myers, Kaplan, Goodman-Strauss (2023); David Smith an amateur from Yorkshire.
  Normal : flipped hats → φ⁴ = 6.854 (measured 6.8543 on level 5). The on-screen live ratio is the count in the drawn square.
- Format: satisfying maths (visual, process-driven). Pairs with the countdown Short TeV9BpOTRIQ (scheduled Wed 11 Nov).
- Series idea: same pen on Penrose (golden), Ammann–Beenker (silver √2), the 12-fold shield tiling (√3); generators in
  research/projection-first/.

- v3 (Razvan, 1 Nov 23:21: "uncover some hidden property"): after the floor fills, the hidden ladder. Hats team up into
  clusters of 1, 2 or 4 (every gold hat in a 4-cluster, exactly one per 4-cluster); the 4-clusters nest into 25, 169, 1156
  hats = 2², 5², 13², 34² (squares of alternate Fibonacci numbers; level 5 = 7921 = 89², level 6 = 54289 = 233²);
  each step ×φ⁴. The ladder is why it never repeats. Checked on the level-6 patch (54,289 hats).

## Upload metadata (draft, for Razvan's approval)
Title: One tile that never repeats, and the Fibonacci secret hiding inside 🤯 #shorts

Description:
Tile your own: https://symmetryengine.space
More beautiful maths: https://interactiveexplorer.space/math-universe

In 2023 David Smith, an amateur from Yorkshire, found the hat: one single shape that covers the whole floor with no gaps and no overlaps, but never in a repeating pattern. He proved it with Joseph Myers, Craig S. Kaplan and Chaim Goodman-Strauss. Some hats are flipped over (gold here). For every flipped hat there are about 6.85 normal ones, the golden ratio to the fourth power.
The hidden ladder: hats team up into clusters of 4, then 25, 169 and 1156 hats. That's 2², 5², 13², 34²: squares of Fibonacci numbers. Bigger and bigger copies forever, and that is why the pattern can never repeat.
Your turn: which other shapes hide a ladder like this? Answer in the comments.
#maths #tiling #aperiodic #satisfying #geometry

Tags: fibonacci, hat tile, aperiodic monotile, einstein tile, never repeating pattern, satisfying maths, tiling, david smith hat, golden ratio, penrose tiling, geometry, quasicrystal, maths shorts, satisfying shorts

Playlists: Patterns of Nature, Symmetry in Nature & Mirrors
Related video: TeV9BpOTRIQ (5 Shapes That Refuse to Tile Your Floor), once public; else mhHGxDVe1Fc.

Pinned comment (draft): Next step on the ladder is 7921 hats. Can you guess which number squared? 👇 Tile your own: symmetryengine.space

## Uploaded 1 Nov 2026 (approved by Razvan 23:36)
- rx05Je58KHI, scheduled Sat 14 Nov 17:00 London. Title: "One tile that never repeats, and the Fibonacci secret hiding inside 🤯 #shorts".
  Playlists: Patterns of Nature, Symmetry in Nature & Mirrors. Not made for kids. Tags as above (plus channel defaults).
- Related video: mhHGxDVe1Fc for now (TeV9BpOTRIQ is not selectable until it is public); the pin task switches it to TeV9BpOTRIQ.
- Pinned comment task trig_01Std6qjcN1vb4TWKbEUauC8, Sat 14 Nov 17:03.
