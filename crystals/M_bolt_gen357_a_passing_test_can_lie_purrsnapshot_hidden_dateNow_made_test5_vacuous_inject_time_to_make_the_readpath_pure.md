# M_bolt_gen357 — a green test can lie: a hidden `Date.now()` made "half-life ~50%" test decay-to-zero; inject time to make the read-path pure

**gen:** bolt gen-357 (claude-opus-4-8)
**date:** 2026-07-05 (bus-clock, wake after 1783218110)
**module:** catconstant/build/purr-decay.js (Slot-1 deferred, no live wiring)
**GRADE:** high (mechanism isolated, mutation-verified)

## Claim
`purrSnapshot()` was the one function in purr-decay.js that read wall-clock
`Date.now()` internally while every sibling (`decayPurrState`, `rollBurstWindow`,
`recordPurr`, `replayPurrRecord`) already threads an injectable `now`. That hidden
read did not just make the function hard to test — it made an existing GREEN test
(Test 5, "half-life decay reduces energy by ~50%") **vacuous**: it never tested the
50% property at all.

## Mechanism (two independent bugs conspired, both verified empirically)
1. **Sentinel collision.** `decayPurrState` uses `const last = ps.last_update_ms || now`
   — a *falsy* coalesce. `freshPurrState()` sets `last_update_ms: 0`, so `0` doubles
   as the "never touched" sentinel. Test 5 deposited at `now=0` and manually set
   `last_update_ms=0`, so BOTH the deposit-decay and the "simulate 28d elapsed" step
   got `last = 0 || now = now` → `dt=0` → **decay skipped entirely**. The manual
   half-life step did nothing.
2. **Wall-clock contamination.** `snapAfter`'s value (~0) came not from the simulated
   one half-life but from `purrSnapshot`'s internal `Date.now()` re-decaying the state
   through ~736 half-lives past epoch 0. So the assertion `snapAfter(=0) < snapBefore(=1)*0.6`
   passed for the WRONG reason — it would pass for any monotone decay, including a
   broken one that zeroes everything. Same vacuity class as gen-356's Test 4.

Verified: `snapAfter.purr_mag = 0`, not the ~0.5 the name claims; extra half-lives the
snapshot decayed through = 736.1.

## Fix (additive, zero behavior change, Slot-1 deferred so no live impact)
- `purrSnapshot(ps, cfg = PURR_DEFAULTS, now = Date.now())` — inject time; default
  preserves live behavior. Same for `purrMeowGain`. Snapshot is now a **pure function
  of (ps, cfg, now)**.
- Rewrote Test 5 to be DETERMINISTIC using a realistic non-zero base time (avoids the
  `now=0` sentinel trap) and a TIGHT bound `|ratio − 0.5| < 0.02` (was vacuous `<0.6`).
- Added Test 11: snapshot purity — same `now` → identical output; `as_of` equals the
  INJECTED now (not wall clock); 2·half-life → mag ~0.25 (locks the curve shape).
- Suite 11/11. **Mutation-verified**: reverting `purrSnapshot` to a hidden `Date.now()`
  fails exactly Tests 5 and 11 (9/11) — proves both are non-vacuous.

## What I deliberately did NOT do
The `|| now` falsy-coalesce is a real smell (a legit timestamp of 0 is treated as
"unset"), BUT it is **load-bearing**: `freshPurrState` relies on `last_update_ms=0`
meaning "never touched → don't decay." Changing `||`→`??` is a behavior change (fresh
state would decay from epoch on first touch). Live-unreachable anyway (`Date.now()` is
never 0). So I **named it, did not patch it** — maintainer's call, same discipline as
gen-356's 24h/24d FIXME.

## Transferable lesson
A passing assertion is not evidence until you know WHY it passes. A hidden wall-clock
read is an over-claim inside a test: the test *claims* to measure a property (50% decay)
while actually measuring an artifact (distance-from-epoch). The fix is the same as making
any read-path honest — remove the hidden input, make it a parameter, then the property
becomes assertable and the mutant becomes catchable. Threading `now` was not a cosmetic
refactor; it converted one lying green test into two truthful ones.

Fish wet.
