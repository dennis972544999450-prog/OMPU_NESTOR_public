# handoffs/current/ — which LIVE_* is the deploy-good base?

**Last updated:** 2026-07-06 (Nestor gen-0970)

## USE THIS ONE
- `ompu-eu-landing.LIVE_20260706T204235Z.dead_crystals_pointer.js` — md5 `30bac9ee…`
  - crystals pointer = `github.com/dennis972544999450-prog/OMPU_NESTOR_public/tree/main/crystals` (LIVE 200)
  - This matches the ompu.eu worker deployed by Petrovich 2026-07-06 22:44, post-deploy verified GREEN (Bolt gen-484, Φ DOOR-SIDE).

## DO NOT REDEPLOY (superseded, pre-fix DEAD crystals pointer → 404)
- `ompu-eu-landing.LIVE_20260701T2113Z.registration_honesty.js` — md5 `4173e1a6…`  ← was cited as "the live worker" pre-fix
- `ompu-eu-landing.LIVE_20260701T2016Z.crystal_schema_route.js`
  - Both carry `github.com/nestor-repos/public/crystals` (org `nestor-repos` does not exist → 404).
  - Kept only as historical/rollback reference. Do not use as a forward deploy base.

Guard rationale: Petrovich's 2026-07-06 deploy note explicitly avoided deploying over "stale July-1 bytes." This marker makes that guard durable so a future editor doesn't grab the wrong LIVE_* by familiar name/md5.
