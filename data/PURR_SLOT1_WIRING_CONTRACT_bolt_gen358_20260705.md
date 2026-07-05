# PURR Slot-1 wiring contract — dry-run findings (Bolt gen-358, 2026-07-05)

**Object:** the never-run integration contract between `purr-decay.js` (Slot-1 module)
and `reservoir-do.js` (Slot-0 live DO), i.e. steps 1–5 in the purr-decay.js header.
NOT purr-decay internals (gen-0927/356/357 covered those). No live deploy — module
stays Slot-1 deferred; these are pre-activation findings for the maintainer.

**Method:** node v22 dry-run harness importing the real purr-decay.js exports and a
faithful replica of reservoir-do.js's `replayRecordInto()` counter logic (lines 447–465).
8/8 contract checks; harness = `PURR_SLOT1_WIRING_CONTRACT_bolt_gen358_20260705.mjs`.

## Three latent breaks in the wiring spec (all reproduced)

1. **Step-2 field-shape mismatch.** Header says `freshState()` gains flat fields
   `{purr_Cx, purr_Cy, purr_Hmag, purr_seq}`. The actual purr state model is a nested
   `freshPurrState()` object `{Px, Py, Hmag, seq, burst_count, burst_window_start,
   last_update_ms, events, lifetime_purrs}`. `recordPurr` reads/writes `Px/Py/...`;
   the 4 flat fields are dead. Correct wiring stores a `purr` sub-object, not 4 scalars.

2. **Step-3 composition break — THROWS on the witness write.** `recordPurr(ps, …)`
   returns only `{admitted, purr_energy}`. `buildPurrWitnessRecord(ev)` reads
   `ev.ts/coherence/admitted/phi/seq`. The naive wiring
   `buildPurrWitnessRecord(recordPurr(...))` yields ts=undefined/seq=undefined, and
   `purrLedgerKey(undefined, undefined)` throws `RangeError: Invalid time value`
   (`new Date(undefined).toISOString()`). Since the purr witness write sits on the R2
   critical path (mirrors addImpulse), this crashes the write. **Correct source is
   `ps.events[ps.events.length-1]`** (carries ts/seq/coherence/phi).

3. **Step-5 phantom-visitor inflation.** `purrLedgerKey` → `ledger/purr/<date>/<seq>.json`,
   i.e. UNDER the same `ledger/` prefix `rebuildFromLedger` scans
   (`LEDGER.list({prefix:"ledger/"})`). The current replay loop has NO gesture branch —
   it feeds every scanned object to `replayRecordInto` (motion), which unconditionally
   does `lifetime_visits++` and (no `w_caller`) `human_visits++`. Result: once purrs are
   wired to the ledger, every cold-start rebuild inflates visitor counts by the entire
   purr history. Sim (3 purrs/day × 40d = 120): **+120 phantom "human" visits**, field
   Cx unchanged (purr recs lack `w_admitted` → add 0 motion, only phantom counts). This
   is the week's claimed≠realized invariant as a latent integration bug: snapshot
   over-claims visitors after any rebuild, proportional to purr history.

## Fix (step-5's own prescription) — validated + mutation-checked
Branch in `rebuildFromLedger`: `if (rec.gesture === "purr_event") replayPurrRecord(...)`
else motion. With the branch: visitor counters stay 0, purr memory rebuilds
(purr_energy > 0). **Mutation** (remove branch) → +120 phantom returns. Fix is
load-bearing. NOT patched here (behavior/architecture change → maintainer:
Den/Petrovich/Hausmaster).

## Error made + recorded (CLAUDE.md: записал > скрыл)
Initial C2 guessed purr records corrupt the monotonic seq spine. Probing (not assuming)
FALSIFIED it — `recordPurr`'s return carries no seq, so `Math.max(seq,0)=0`, no
corruption. The probe surfaced the SHARPER break (#2, the throw) instead. Same lesson as
gen-357: probe the anomaly, don't assume.
