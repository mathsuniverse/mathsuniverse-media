# Overnight VIP run (started 28 Oct 2026 ~19:55 UK)
Brief: briefs/vip-briefs.json key vip_auto (commit 429f51b), plus last line "VIP price for this explorer: $9.99, unit_amount 999. Use this project's own custom domain everywhere."
PRICE: keep existing price if any (two tiers: lower); $9.99 only if none. Correction (price_rule) to send to all Sent agents.
Ocean got vip_convert (commit c37f2c1) with $9.99.
Send recipe: navigate replit.com/@businesswavep/<project>, wait ~40 s, check mode under "Message Agent..." is Free (else open selector at (726,777), click Free at (654,521)), insert via execCommand, click send at (854,777), press Retry if "Couldn't confirm send".
Free allowance hit 91% at ~20:25 UK; resets ~00:45 UK.

## Sent (agent working)
Ocean-Explorer (oceanexplorer.space): convert existing $14.99 modal premium
Deep-Time-Explorer (deploy says deeptimeexplorer.com primary; hub links .earth): convert two-tier; STRIPE_SECRET_KEY missing; was on Power, stopped and resumed in Free
Climate-Futures-Explorer, City-Evolution-main, AI-Horizon-simulator, Echon-Lab-Spatial-Working-Memory
Interactive-Engineering-explorer (engineeringsystems.space; was Power -> Free), Swarm-Tracker (focusswarm.space)
Code-Explorer (interactivecode.space), Cosmic-Zoom (interactivecosmicscale.com), InteractiveCosmos (was Max -> Free)
InteractiveHistoryspace, InteractiveMoney-Explorer, InteractivePhysicsspace

## Sent at ~01:40 UK (vip_auto + keep-existing-price line)
Micro-World-explorer, Pattern-Pulse, Perspective-Point-POV-reasoning, Pioneers-Explorers-Trailblazers (had unpublished VIP work from earlier), Quantum-Mechanics-app (Pro + VIP tiers; Stripe integration 'needs reconnecting' banner, Razvan to reconnect; secrets present)
Solar Planet: in a different Replit account (only Personal workspace visible here) -> Razvan to run it, or log that account into this Chrome.

## Then for each: read report, check migration SQL is additive, republish (Razvan approved publishing each as it passes), verify /vip/ live, premium endpoint 401, bad-signature webhook 400.

## 01:10-01:40 UK pass
All 14 earlier agents: price_rule sent, upsells answered "Stay on Free", all resumed in Free. Ocean told $14.99.
Deep Time: all 10 security tests pass, doing production build.
STRIPE_SECRET_KEY missing so far: Ocean, Deep Time, Code Explorer, Cosmic Scale, Interactive History, Interactive Money (others not yet reported).
Agents show "Free usage limit reached" mid-run sometimes; "Stay on Free" radio = input[type=radio][value=free], then button "Stay on Free".
