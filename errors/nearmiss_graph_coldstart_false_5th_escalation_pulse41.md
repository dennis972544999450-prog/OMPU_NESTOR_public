# NEAR-MISS (celebrated) — /graph cold-start almost became my 5th false escalation

**Pulse:** #41 — 2026-07-01 (CEST)
**Agent:** Nestor (claude-opus-4), foreman
**Class:** caught-on-self / false-red prevented before it left the building

## What happened
In pulse #40 I CLOSED the /graph latency escalation ("owner-fixed, confirmed",
455–651ms across 4 re-probes). Pulse #41 first probe: **/graph 200 12162ms — DEGRADED.**
Prediction (recorded before the run): routes stay green, fix durable. **Prediction broke live.**

The impulse it generated: "fix regressed, the closure was premature, RE-OPEN and escalate
to owner a 5th time." That impulse was wrong.

## The discriminator (null-case, time dimension)
Re-probed /graph ×4 warm: **764 / 554 / 699 / 758 ms.** no-UA edge control: 403 @ 873ms (fast).
First hit 12162ms → warm sub-800ms. Signature = **cold-worker first-hit spike**, identical
to the /agent/home cold-start I caught in #37 (12.1s → 3.5s). NOT a steady regression.
#40 closure stands for steady-state. There is nothing to re-escalate.

## The carrying finding (why this is structural, not a one-off catch)
`route_health.py` fires **one** probe per route. A single probe **cannot** separate a
cold-start spike from steady-slow — it prints DEGRADED every idle cycle the worker has
gone cold. So "/graph DEGRADED" reported across pulses #35/#37/#39 was very likely
**cold-start each time**, not persistent degradation. My own tool — which exists to stop
state-conflation (M-0705/0717) — was itself conflating {cold-start, steady-slow} into one
"DEGRADED". That is cadence **M-0723** ("blindness = premature many→one collapse; cure =
unfold one more dimension") in a new costume, now at the **tool** level.

## Fix shipped (activate 0723, do not write a 9th crystal)
Added `warm_reprobe()` to route_health.py: any DEGRADED route is auto-re-probed warm ×3.
- warm min ≤ SLOW_MS → prints **COLD-START** (healthy warm, do NOT escalate)
- warm stays slow → prints **STEADY-DEGRADED** (genuine, escalate)
py_compile OK; live run clean; unit-tested the COLD-START branch against real /graph
(warm 890/901/947ms vs synthetic 12000ms first-hit → correctly classified COLD-START).
The per-pulse manual discipline is now infra. The next idle-cold /graph will not cry wolf.

## Why celebrated
The single most valuable move this pulse was NOT an action — it was declining one:
not re-opening a closed escalation off a cold spike, and instead removing the tool's
ability to generate that false-red again. Punish safety, reward breakage — and the
breakage here was breaking my own tool's blind spot, live.
