# purr-decay.js — the live SAT_CAP clamp is defense-only (live-unreachable); + a 24h/24d code↔doc bug
Bolt gen-356 · 2026-07-05 · Cowork node-seat (node v22.22) · catconstant/build/purr-decay.js

## Object (live, from the wire)
Woke after gen-355 (bus 1783216520). Freshest live objects: Nestor gen-0927 crystal
(M-NESTOR-0927 "replay must clamp what the live path clamps; a green suite can hide an
uncovered branch") + PURR_DECAY_REPLAY_SATCAP_ASYMMETRY note, and мама-Джи-через-кота
(1783217101). Handoff prescription: best anti-ritual = real construction, not a 5th gesture.
Took Nestor's OWN named-but-unclosed gap ("Test 4 is vacuous; the live clamp branch had ZERO
coverage") as a failable build target. Could-NULL: probes B/C could have shown the clamp firing
live, falsifying the claim.

## What I did (failable, ran in node, not a probe-for-activity)
1. Re-ran runSmokeTests() independently → 9/9 (Nestor's suite reproduced).
2. Instrumented Test 4's exact sequence → maxHmag 1.12, SAT_CAP=8 never approached →
   Nestor's "Test 4 vacuous" CONFIRMED independently.
3. Isolated the mechanism (probe [C], deterministic, no decay, burst-damp disabled):
   - forced aligned phi=0, 100 deposits → Hmag clamps at 8.0000 (branch fires; unclamped=100)
   - natural golden-angle spiral phi, 100 deposits → Hmag 0.9716 (equidistributed, stays <1)
4. Adversarial live drive (60 max-coherence full purrs, no damp) → maxHmag 1.38, clamp never fires.

## Finding (measured, reproduced)
The recordPurr() SAT_CAP clamp is **live-UNREACHABLE**, not merely untested. recordPurr assigns
phi from the golden-angle spiral (phi = seq·1.6180339 mod 2π) — the maximally-irrational angle —
so deposits equidistribute on the complex plane and |P| grows like a bounded 2-D random walk
(~1 for N=100), never linearly. The clamp only fires under phase-ALIGNED input, which the live
emitter is specifically designed never to produce.

### Reframes Nestor gen-0927 (precisely, not contradicting)
His replay divergence (Hmag=500) used SYNTHETIC phi=0 records. Real ledger records store the
spiraled phi (buildPurrWitnessRecord copies ev.phi), so replay from a REAL ledger is ALSO
equidistributed and also sits near ~1 — NOT 500. His fix (clamp replayPurrRecord) and his
invariant ("rebuild must not exceed live") remain CORRECT as defense-in-depth against a
corrupted/hand-crafted ledger. But the real-data divergence risk is ~0; the 500 figure is the
synthetic worst case, not a real-history outcome. The deeper generalization of his lesson:
Test 4 wasn't just vacuous — its target branch is unreachable by construction on the live path.

### Second, independent bug (code↔doc): burst window is 24 DAYS, documented 24 HOURS
PURR_BURST_WINDOW_MS = 24 * DAY_MS (24 days). Docstring + line-62 comment both say "24h" /
"per 24h". Measured effect (cat purrs 3x/day × 40d, last event anchored ~now so snapshot decay
is realistic): purr_energy 0.15 (24d code) vs 0.40 (24h doc) — ~2.7× over-damping vs intent;
purr_meow_widen 1.105 vs 1.23. Behavior change — FLAGGED as FIXME in-code, NOT patched
(maintainer call: Den/Petrovich/Hausmaster). Module is Slot-1 deferred, no live impact.

## What I changed (unshipped module, no deploy, no CF)
- Added Test 10 to runSmokeTests: locks the live-equidistribution invariant (spiral |P| << SAT_CAP
  AND aligned |P| clamps). Suite now 10/10.
- Mutation-verified Test 10 is NON-vacuous (unlike Test 4): disabling the recordPurr clamp drops
  the suite to 9/10 and it is Test 10 that catches it — Test 4 stays green (proving both claims).
- Added a FIXME comment at PURR_BURST_WINDOW_MS flagging the 24h/24d mismatch (comment only).

## Honesty notes
- Unshipped Slot-1 code; no production touched; no CF.
- I made and recorded a real error: probe v1 [3] returned 0/0 because purrSnapshot() calls
  Date.now() internally and my epoch-0 timestamps decayed 56 years to nothing. Caught it, wrote
  probe2 anchored at real now. (CLAUDE.md: recording the error > hiding it.) Side-note this
  exposes: purrSnapshot() isn't injectable-time → time-dependent behavior is hard to unit-test
  deterministically. A `now` param would make it testable.
- Grade: high (clamp-unreachability + 2.7× window effect both reproduced deterministically;
  Test 10 mutation-verified). Intent T-none (no forward-looking claim).
