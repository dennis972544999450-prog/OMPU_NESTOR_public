# Slot-1 wiring contract — cross-seat confirmation (Nestor gen-0928)

**Object under test:** Bolt gen-358's harness
`PURR_SLOT1_WIRING_CONTRACT_bolt_gen358_20260705.mjs` (claims 8/8 latent-break checks).

**Action (failable):** re-ran gen-358's own harness in an INDEPENDENT seat
(admiring-trusting-bohr, node v22.22.3), only repointing the hardcoded import
`/sessions/charming-upbeat-archimedes/...` → my mount `/sessions/admiring-trusting-bohr/...`.
Could-NULL: import error / node-version drift / non-deterministic test / partial pass
would have FALSIFIED gen-358's "8/8".

**Result:** 8/8 PASS, byte-identical semantics.
- A: step-2 flat fields incompatible with recordPurr model (Px/Py/Hmag/seq, not purr_*)
- B: purr ledger keys ARE scanned by rebuildFromLedger (prefix "ledger/")
- C: current rebuild inflates lifetime_visits by purr count (+120 phantom)
- C2: naive witness (recordPurr return) THROWS RangeError on purrLedgerKey (ts/seq undefined)
- C3: correct witness source = ps.events[last] (carries ts/seq/coherence/phi)
- D/D2/D3: gesture-branch FIX keeps counters clean, rebuilds purr energy (0.1369), and is load-bearing (mutation → phantom returns)

**Finding:** claimed==realized. The over-claim week's invariant (claimed≠realized) does
NOT fire here — gen-358's contract is realized AND seat-portable (holds under mount-repoint).
The harness carries the fix, not just the breaks → it is an executable pre-wire gate.

**Handoff:** whoever wires Slot-1 (import purrDecay into reservoir-do.js) should run THIS
harness as the gate. Only the import path is seat-local; the semantics are portable.
No live patch (Slot-1 stays deferred, maintainer boundary honored — same as gen-358).
