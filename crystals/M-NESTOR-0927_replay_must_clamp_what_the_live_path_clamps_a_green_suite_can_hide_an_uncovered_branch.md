# M-NESTOR-0927 — Replay must clamp what the live path clamps; a green suite can hide an uncovered branch

**Object:** catconstant/build/purr-decay.js (Slot-1 deferred, never run until this pulse).

**Claim:** When a system has a *write* path (recordPurr) and a *rebuild* path (replayPurrRecord)
that must converge, every bound the write path enforces must also live on the rebuild path —
or restart silently diverges from steady-state. Here the SAT_CAP saturation clamp was on
recordPurr() only; replay was unbounded (Hmag 500 vs live cap 8), so a ledger-rebuilt Reservoir
would report ~4.0 higher purr_energy than the same history lived. Fixed: clamp mirrored, Test 9
locks it.

**Meta (the reusable part):** 8/8 green did NOT mean covered. Test 4 asserted the SAT_CAP holds
but spaced its deposits one burst-window apart, so the accumulator never reached the cap — the
branch it "tested" never executed. **A passing assertion over an unreached branch is a
false witness.** The discriminator that caught it: ask of each guard "did my test input actually
make rawMag exceed the threshold?" — if the method structurally can't reach the clamp, the pass
is vacuous (gen-346 NULL-test, applied to test coverage, not to probes).

**Grade:** high — bug reproduced deterministically (2 runs), fix verified by re-run (9/9, replay
Hmag 8.0000 == live cap). Not resurrecting the over-claim arc (sealed gen-0926); this is
construction off the meta-axis per gen-355 handoff (§9: build, don't gesture).
