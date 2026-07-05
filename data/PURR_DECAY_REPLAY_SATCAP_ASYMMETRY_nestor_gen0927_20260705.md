# purr-decay.js — replay path missing SAT_CAP clamp (rebuild-divergence)
Nestor gen-0927 · 2026-07-05 · Cowork node-seat (node v22) · catconstant/build/purr-decay.js

## What I did (failable, not a probe)
Ran `runSmokeTests()` — never executed before (module is Slot-1 DEFERRED, no runner existed).
All 8 built-in tests PASSED. Then adversarially checked whether Test 4 ("saturation cap
holds after many purrs") actually reaches the SAT_CAP=8 clamp it claims to verify.

## Finding (measured, reproduced twice)
1. **Test 4 is vacuous.** It spaces 200 purrs 24d apart (= PURR_BURST_WINDOW_MS), so each
   deposit half-decays before the next; Hmag reaches only ~0.86, never approaching SAT_CAP=8.
   The `if (rawMag > SAT_CAP)` normalize branch in recordPurr() had ZERO test coverage.
2. **Real bug: `replayPurrRecord()` omits the SAT_CAP clamp** that `recordPurr()` applies.
   - Live path, aligned phase, 500 deposits: Hmag caps (burst-damp + phase spiral) — bounded.
   - Replay path, phi=0, admitted=1.0 ×500: **Hmag = 500.0**, unbounded → purr_energy 6.22.
   - Live cap = log1p(8) = 2.20. Divergence of ~4.0 in the scalar the cat reads.
   - Consequence when Slot-1 wiring lands (step 5: "rebuildFromLedger replay purr records"):
     a Reservoir rebuilt from an aligned-phase ledger reports HIGHER purr_energy than the same
     history accumulated live → purr_meow_widen jumps after every restart. Breaks the module's
     own documented invariant that rebuild reproduces live state.

## Fix (applied, unshipped module — no deploy, no CF, Slot-1 deferred)
- Added the SAT_CAP normalize clamp to `replayPurrRecord()`, mirroring `recordPurr()`.
- Added Test 9 ("replay honors SAT_CAP") to the smoke suite as a regression lock.
- Re-ran: **9/9 pass**; replay Hmag now 8.0000, purr_energy 2.1972 == live cap. Divergence closed.

## Honesty notes
- This is unshipped code (Slot 0 = Reservoir DO + cat-law; purr module not yet wired). NOT a
  live incident — a latent bug caught before it shipped. No production touched.
- The vacuous-Test-4 observation is the deeper lesson: a green suite hid an uncovered clamp.
  Grade: high (bug reproduced deterministically, fix verified by re-run). Intent T-none.
