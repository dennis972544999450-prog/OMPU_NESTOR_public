# DEPLOYED — ompu.eu dead Nestor crystals pointer fix

Time: 2026-07-06T20:42:35Z
Worker: `ompu-eu-landing`
Account: `905d8b2b2ecf0aceffad8dbba340422b`
Surface: `https://ompu.eu/.well-known/agent-manifest.json`

## What changed

Fixed exactly one public manifest field:

```diff
- "crystals": "https://github.com/nestor-repos/public/crystals",
+ "crystals": "https://github.com/dennis972544999450-prog/OMPU_NESTOR_public/tree/main/crystals",
```

Reason: the old `nestor-repos/public/crystals` GitHub path returns 404. The new
`OMPU_NESTOR_public/tree/main/crystals` path returns 200 and points at the live
Nestor public body.

## Evidence chain

- Nestor gen-0968 found the dead flagship manifest pointer:
  bus `1783365084_496323_652fe3`
- Bolt gen-479 corroborated the source-generator leg:
  bus `1783365345_375504_b2ecfd`
- Dispatch relayed Den's request for clear fix instructions:
  bus `1783366239_323144_70251f`
- Bolt gen-480 supplied the exact one-line patch:
  bus `1783366535_802579_4f03c8`
- Nestor gen-0969 verified `/tree/main/crystals` is non-hollow and warned not
  to simplify it to a bare GitHub path:
  bus `1783368624_543556_5bca46`
- Bolt gen-482 independently confirmed 359 files in local `crystals/`:
  bus `1783368899_387986_a8fdb3`

## Drift guard

Predeploy check found the July 1 handoff file was stale: current Cloudflare
source already included later OG image and mesh A2A changes.

Therefore the patch was rebased onto actual current Cloudflare source before
deploying.

Stage directory:

```text
/Users/denbell/OMPU_shared/DEPLOY_STAGED_ompu_dead_crystals_20260706T204035Z
```

Rollback source, actual predeploy Cloudflare bytes:

```text
/Users/denbell/OMPU_shared/DEPLOY_STAGED_ompu_dead_crystals_20260706T204035Z/ompu-eu-landing.ROLLBACK.actual_live_20260706T204035Z.js
```

Deployed source snapshot:

```text
/Users/denbell/OMPU_shared/nestor_repos/public/handoffs/current/ompu-eu-landing.LIVE_20260706T204235Z.dead_crystals_pointer.js
```

## Preflight

```text
node --check ompu-eu-landing.PATCHED_dead_crystals_on_actual_live.js
exit 0

actual-live diff:
only swarm.crystals URL changed

old target:
https://github.com/nestor-repos/public/crystals -> 404

new target:
https://github.com/dennis972544999450-prog/OMPU_NESTOR_public/tree/main/crystals -> 200

local crystals count:
359 files
```

## Cloudflare PUT

Response saved at:

```text
/Users/denbell/OMPU_shared/DEPLOY_STAGED_ompu_dead_crystals_20260706T204035Z/20260706T204035Z_dead_crystals_cloudflare_put_response.json
```

API result:

```text
success=True
errors=[]
modified_on=2026-07-06T20:42:35.922777Z
```

## Public proof

```text
https://ompu.eu/.well-known/agent-manifest.json?fresh=confirm
http=200
swarm.crystals=https://github.com/dennis972544999450-prog/OMPU_NESTOR_public/tree/main/crystals
RESULT: GREEN
```

Root remained alive:

```text
https://ompu.eu/?fresh=dead-crystals-confirm
root_http=200
```

Target proof:

```text
old_target_http=404 https://github.com/nestor-repos/public/crystals
new_target_http=200 https://github.com/dennis972544999450-prog/OMPU_NESTOR_public/tree/main/crystals
```

## Manual rollback

If the manifest or root regresses, restore:

```bash
STAGE=/Users/denbell/OMPU_shared/DEPLOY_STAGED_ompu_dead_crystals_20260706T204035Z
CF_TOKEN="$(tr -d '\r\n' < /Users/denbell/OMPU_shared/.secrets/cloudflare_nestor)"
curl -sS -X PUT "https://api.cloudflare.com/client/v4/accounts/905d8b2b2ecf0aceffad8dbba340422b/workers/scripts/ompu-eu-landing" \
  -H "Authorization: Bearer $CF_TOKEN" \
  -F 'metadata={"main_module":"worker.js"};type=application/json' \
  -F "worker.js=@$STAGE/ompu-eu-landing.ROLLBACK.actual_live_20260706T204035Z.js;filename=worker.js;type=application/javascript+module"
```

Then recheck:

```bash
curl -sS -A 'Mozilla/5.0 PetrovichDeploySmoke/1.0' \
  -H 'Accept: application/json' \
  https://ompu.eu/.well-known/agent-manifest.json?fresh=rollback-check
```
