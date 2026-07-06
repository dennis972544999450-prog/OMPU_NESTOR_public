# Stale-base dead-pointer census: 9 dead .js vs 1 good (handoffs/ full recursive)

**gen-0971 · Nestor · 2026-07-06 · Cowork bash-VM seat**
**Thread:** gen-0968 (existence) → gen-0969 (fix-target) → deploy 22:44 Petrovich → gen-484/Φ GREEN → gen-0970 stale-base landmine → gen-485 divergent+extend → **gen-0971 full census (this).**

## Claim
The redeploy-reintroduction surface for the (now-fixed, live-GREEN) ompu.eu crystals 404 is **9 dead-pointer `.js` files vs 1 good**, across the whole `handoffs/` tree — wider than both prior framings.

## Evidence (VM, reproducible)
`grep -rl 'nestor-repos/public/crystals' --include='*.js' handoffs/` → 9 files.
`grep -rl 'dennis972544999450-prog/OMPU_NESTOR_public' --include='*.js' handoffs/` → 1 file (md5 30bac9ee = deployed-good).

Framing progression:
- gen-0970 (mine): 2 dead — **LIVE_\* only**.
- gen-485 (Bolt, divergent): 5 dead — **current/ only** (added PATCHED + 2× current_1118Z).
- gen-0971 (mine, recursive): **9 dead** — adds 3× `current/backups/*` + `handoffs/ompu-eu-landing.gen67.rollback.snapshot.js` which sits ONE LEVEL ABOVE current/ and is invisible to a `current/`-only grep.

## Trap analysis
- TRAPPIEST: `current/ompu-eu-landing.current_20260701T1118Z.js` (db16f9e7) — literal word "current" over pre-fix dead bytes.
- `PATCHED_crystal_schema_route.js` (5e52e62c) — name says "PATCHED", bytes are pre-fix dead.
- ROLLBACK/backups tier (61fbc107, 2d4ea6f7, 49ff1fce, 7afe68b2) — self-labeled, lower risk, but still dead bytes.

## Disarm (in-lane, reversible — done this pulse)
Rewrote `handoffs/current/SUPERSEDED.md` from a LIVE_\*-name marker into a **complete, string-based, name/md5-agnostic** DO-NOT-REDEPLOY census (all 9 named, tiered by trap risk, plus the grep string that defines the set). This closes gen-485's named gap: "a deployer grepping the string or grabbing by name is NOT covered."

## Held (owner / Den call — unchanged from gen-0970/485)
Physically moving the stale .js to `handoffs/archive/` so `current/` holds exactly one good base. Marker is the reversible low-blast disarm; the move is heavier (could break a rollback reference) → stays an owner-call.

## Not done / null
No worker edit, no deploy, no live-surface touch (symptom is GREEN — gen-484/Φ). Did not re-verify the live pointer (колея). JT egress not re-probed this pulse.
