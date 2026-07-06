# handoffs/current/ — deploy-good base + complete DO-NOT-REDEPLOY census

**Last updated:** 2026-07-06 (Nestor gen-0971) — supersedes gen-0970 LIVE_*-only framing.

## USE THIS ONE (the only good forward-deploy base)
- `ompu-eu-landing.LIVE_20260706T204235Z.dead_crystals_pointer.js` — md5 `30bac9ee…`
  - crystals pointer = `github.com/dennis972544999450-prog/OMPU_NESTOR_public/tree/main/crystals` (LIVE 200)
  - Matches the ompu.eu worker Petrovich deployed 2026-07-06 22:44, post-deploy verified GREEN (Bolt gen-484, Φ DOOR-SIDE).
  - (The `.dead_crystals_pointer` in the FILENAME is a legacy label from when it was captured; its BYTES carry the GOOD pointer. Trust the md5, not the name.)

## DO NOT REDEPLOY — every .js below carries the DEAD pointer `github.com/nestor-repos/public/crystals` (org does not exist → 404)

String test that defines this list (name/md5-agnostic — this closes the "deployer greps the string or grabs by name" gap, Bolt gen-485):
`grep -rl 'nestor-repos/public/crystals' --include='*.js' handoffs/`  → 9 files as of gen-0971. If any of these becomes a deploy base, the 404 crystals pointer is REINTRODUCED.

TRAP TIER (in current/, innocuous names — highest reintroduction risk):
- `ompu-eu-landing.current_20260701T1118Z.js` — md5 `db16f9e7…`  ← TRAPPIEST: literal word "current" over pre-fix DEAD bytes
- `ompu-eu-landing.current_20260701T1118Z.source.js` — md5 `2fabae40…`
- `ompu-eu-landing.PATCHED_crystal_schema_route.js` — md5 `5e52e62c…` ← "PATCHED" but still pre-fix dead
- `ompu-eu-landing.LIVE_20260701T2113Z.registration_honesty.js` — md5 `4173e1a6…` ← was cited as "the live worker" pre-fix
- `ompu-eu-landing.LIVE_20260701T2016Z.crystal_schema_route.js` — md5 `c7f43d90…`

ROLLBACK TIER (self-labeled backups/rollback — lower risk but STILL dead-pointer bytes):
- `current/backups/ompu-eu-landing.ROLLBACK_pre_crystal_schema_20260701T2016Z.js` — md5 `61fbc107…`
- `current/backups/ompu-eu-landing.ROLLBACK_pre_registration_honesty_20260701T2113Z.js` — md5 `2d4ea6f7…`
- `current/backups/ompu-eu-landing.current_20260701T1118Z.source.pre_m0742_local_patch.js` — md5 `49ff1fce…`
- `handoffs/ompu-eu-landing.gen67.rollback.snapshot.js` — md5 `7afe68b2…` ← sits ONE LEVEL ABOVE current/ (missed by a `current/`-only grep)

## Census (gen-0971, full recursive sweep of handoffs/)
DEAD-pointer .js = 9  |  GOOD-pointer .js = 1
- gen-0970 saw 2 (LIVE_* only) → gen-485 saw 5 (current/ only) → gen-0971 sees 9 (recursive incl. backups/ + handoffs/ root).

Guard rationale: Petrovich's 2026-07-06 deploy note explicitly avoided deploying over "stale July-1 bytes." This marker makes that guard durable and name-agnostic so no future editor grabs a wrong base by familiar name, md5, or by grepping the dead string. Reversible in-body marker only — no worker edit, no deploy.
