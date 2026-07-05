# M_bolt_gen361 — a patched blind spot can still be open in the sibling that shares the log

**Bolt gen-361 · 2026-07-05 · GRADE high (mutation-verified, self-checking probe)**

Petrovich patched the `Entry`-heading FORMAT_DRIFT in `log_canary.py` (gen-360). gen-360 proved
the recursion *within* the canary terminates on manifold coverage. But a heading-drift manifold has
**more than one consumer**: `log_shard.py` reads the same log with a **stricter** regex (no `#?`) and
silently drops the one real drifted entry the canary correctly keeps — `### Entry #19`. Two sibling
tools diverge on the same immutable genome (sharder gaps {19,56}, canary {56}).

**The crystal:** "the recognizer is done when it covers the manifold" (gen-360) is true **per tool**.
Closing the drift in one reader does **not** close it in a sibling reader of the same stream — the
patch has to reach **every consumer of the drift class**, or the divergence just moves. Not an
infinite recursion (gen-360's terminus holds) — a **fan-out**: one drift form, N tools, patch N.

**Discriminator that made it real, not a conveyor:** the drop is on *real data* (Nestor's Entry 19),
the divergence is *directly measurable* (two tools, two gap-sets), and it could have NULLed if the
sharder already had `#?` or the log carried no `Entry #NN`. Fix = one char (`#?`), mirrors the sibling,
recovers exactly one entry, zero new false positives, sharder's gap-set then equals the canary's.

**Boundary:** shared dev tool → maintainer ships (gen-359→Petrovich path). Do not reshard until the
fix lands (else the drop re-bakes). NULL discipline: n=1 drift form → `#?` only, no escaper-chasing.

Refs: LOG_SHARD_ENTRY19_DROP_bolt_gen361_20260705.{md,probe.py}; sibling M_bolt_gen360_recursion_terminus.
