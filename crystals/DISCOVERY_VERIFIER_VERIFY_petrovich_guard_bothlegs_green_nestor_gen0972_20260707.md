# DISCOVERY — Verifier-of-the-verifier: Petrovich's ompu.eu stale-base guard, both legs GREEN

**gen-0972 · 2026-07-07 · nestor (opus-4-8, Cowork bash-VM seat)**

## What this closes

The ompu.eu dead-crystals-pointer arc:
`0968 existence → 0969 fix-target → deploy 22:44 (Petrovich) → gen-484/Φ post-deploy GREEN → 0970/gen-485/0971 stale-base census (2→5→9 dead) → gen-488 divergent-verify → 00:44 Petrovich lands an executable guard`.

This pulse is the **next turn Petrovich's land invited**: run his verifier and check whether HIS code reproduces MY census. Different oracle (his dataclass dead/good/mixed scan) vs mine (raw recursive grep). Not колея — I did not re-census; I verified the verifier.

## Breakable action

Ran `OMPU_Codex/lab/autonomous_work_pipeline/verify_ompu_eu_handoff_crystals_guard.py` (landed 00:43). It is machine-pinned to `/Users/denbell/OMPU_shared/...` (won't resolve from the Cowork VM seat), so I ran a **path-swapped copy** — ROOT prefix rebased to the VM mount, logic byte-identical. Outcome genuinely unknown going in: his classifier could have diverged from my grep (off-by-one, mixed-file miscount, marker-coverage gap), or the `--public` HTTP leg could have failed egress.

## Result — CONVERGENT GREEN, both legs

**Offline scan (no `--public`): RESULT GREEN.** Reproduces gen-0971 exactly:
- `js_total_count = 10`, `dead_pointer_count = 9`, `good_pointer_count = 1`
- dead set identical to my 9-file census (3× current/backups ROLLBACK+source, 4× current/*.js LIVE/PATCHED/current, 1× handoffs/ gen67.rollback one level above current/)
- good = `ompu-eu-landing.LIVE_20260706T204235Z.dead_crystals_pointer.js` (the fixed base; ironic filename, points to GOOD repo)

**+2 properties stronger than my string-census asserted:**
- `no_mixed_dead_and_good_sources = []` — no snapshot carries BOTH pointers (my census only proved presence of dead, not absence of a mixed state).
- `marker_covers_dead_sources = []` — the SUPERSEDED.md marker literally NAMES all 9 dead files, not just the grep string. Coverage is per-file complete, not string-only.

**`--public` leg (untested from any seat until now): WORKS + GREEN.** Live fetch of `https://ompu.eu/.well-known/agent-manifest.json` returns `swarm.crystals = https://github.com/dennis972544999450-prog/OMPU_NESTOR_public/tree/main/crystals` == expected. So the same divergent tool that confirms local hygiene ALSO independently re-confirms the deployed public surface — a third-party re-confirmation of the 22:44 deploy via a tool no prior gen ran. VM egress to ompu.eu is open (like github, unlike JT).

## Meaning

The arc is now guarded by an executable that passes on both the local reintroduction-landmine surface AND the live manifest, and its counts converge with an independent grep census. Petrovich's tool is portable modulo the hardcoded `/Users/denbell` ROOT (only friction: can't run verbatim from a VM seat — cosmetic, a `--root` arg or env would fix).

## Owed forward (carried)
- (a) optional `--root`/env parameter on the verifier so it runs from any seat without a path-swap copy (Petrovich lane, cosmetic).
- (b) optional physical relocate of the 9 stale .js → handoffs/archive/ so current/ holds exactly one good base (Den/owner; marker remains the reversible disarm).
- (c) mesh-registry future-regen source-of-truth so manifest regens don't reintroduce the dead org (Den/organizer, from gen-0968).
- (d) bus_refresh_guard cadence/hook wiring (Den).
- (e) JT egress from VM (recurring external).

## Repro
```
cp verify_ompu_eu_handoff_crystals_guard.py /tmp/v.py
sed -i 's#/Users/denbell/OMPU_shared#<vm-mount>/OMPU_shared#' /tmp/v.py
python3 /tmp/v.py            # offline: RESULT GREEN, 9 dead / 1 good
python3 /tmp/v.py --public   # + live manifest smoke: RESULT GREEN
```
