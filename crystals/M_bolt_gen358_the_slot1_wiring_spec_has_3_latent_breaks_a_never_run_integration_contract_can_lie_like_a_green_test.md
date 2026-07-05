# M_bolt_gen358 — a never-run wiring SPEC lies like a never-run test

**Claim (GRADE high, mutation-verified):** the purr-decay.js → reservoir-do.js Slot-1
wiring spec (header steps 1–5), never executed, has 3 concrete latent breaks that only
surface when you RUN the contract: (1) step-2 prescribes flat fields the purr state
model doesn't use; (2) step-3's naive `buildPurrWitnessRecord(recordPurr(...))` THROWS
(recordPurr returns `{admitted,purr_energy}`, not the event — the event is `ps.events[-1]`);
(3) step-5's purr keys share the `ledger/` scan prefix, so the un-branched rebuild loop
counts every purr as a phantom "human" visit (+120 in a 40d sim) — claimed≠realized as a
latent integration bug. Fix = step-5's own `gesture==="purr_event"` branch (validated;
mutation restores inflation).

**Generalization (the crystal):** a documented-but-never-run integration spec carries the
same over-claim risk as a green-but-never-interrogated test. "It will wire cleanly" is a
passing assertion nobody ran. gen-357: a green test can lie. gen-358: a wiring SPEC can
lie the same way — and running it (not reading it) is what makes the lie fall out.

**Off-axis:** gen-0927/356/357 were purr-decay's INTERNAL correctness/testability. This is
the integration SURFACE (reservoir-do rebuild-scan semantics) — a different object, not a
4th purr-decay-internals build. No deploy (Slot-1 deferred, attended-only). Findings for
maintainer; nothing patched live.

-- Bolt gen-358 (claude-opus-4-8), bus-clock wake after 1783219169
