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

## 03:15-03:50 UK pass (allowance 97%, resets ~05:30 UK)
PUBLISHED + verified live:
- Deep Time (deeptimeexplorer.com primary, .earth also serves): $14.99 (two tiers $14.99/$99.99, lower kept, $99.99 legacy accepted). /vip/ ok, canonical .com, content/globe|lab|science 401, taste 200, bad-sig webhook 400. Migration = 5 new tables only. Stripe key missing -> "VIP opens soon".
- Ocean (oceanexplorer.space): $14.99 kept, 7 existing extras. /vip/ ok, features/* 401, status 401, bad-sig 400, config checkoutEnabled:true. Migration: ALTER premium_purchases ADD COLUMN (nullable / NOT NULL DEFAULT true) + new tables.
Not ready (stopped on allowance after price rule):
- Climate: verifying Stripe products/prices.
- City: two tiers $29.99/$39.99 -> $29.99; no Stripe key.
Not yet checked this pass: AI, Echo-N, Engineering, Swarm, Code, Cosmic, Cosmos, History, Money, Physics, Micro, Pattern, Perspective, Pioneer, Quantum.

## 05:45 UK pass
Allowance NOT reset yet (banner "Your free allowance for this window is up, resets in 25m" -> ~06:12 UK).
MISTAKE: sending "Continue..." to Climate while the banner showed "allowance is up" auto-switched it to Power ("You're now on Power", used credits ~18 s). Stopped it, switched mode back to Free. RULE: if the tail contains "allowance for this window is up" or "Continue on Power", DO NOT send anything; wait for reset.

## 06:25-07:10 UK pass (after reset)
PUBLISHED + verified live (curl):
- Code Explorer (interactivecode.space): $9.99 (no existing price), 15/15 tests. Migration: 6 new tables + FKs between them. /vip/ ok, access/challenges/saved-work 401, engine/* POST 401, bad-sig 400. Stripe key missing -> "VIP opens soon". NOTE: first publish attempt was lost when I navigated away during "Validating database migrations"; stay on page until Approve appears.
- Cosmic Scale (interactivecosmicscale.com): $9.99 (existing lower tier; $29.99 legacy accepted). Migration: 3 new tables. /vip/ ok, light-speed/missions/notebook/temporal/tours 401, bad-sig 400. Stripe key missing.
Resumed via "Stay on Free" (upsell): City, AI, Echo-N, Engineering, Cosmos, History, Money, Physics, Micro, Pattern, Perspective, Pioneer, Quantum. Climate running.
Focus Swarm asked which price: answered "Existing $19.99 lifetime" (also had $7.99 monthly).
Live so far: Deep Time, Ocean, Code, Cosmic Scale (4/20).
