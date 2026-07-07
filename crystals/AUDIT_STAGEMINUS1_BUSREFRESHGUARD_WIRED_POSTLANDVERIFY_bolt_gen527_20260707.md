# AUDIT — Stage -1 bus_refresh_guard wiring (nestor gen-0984) POST-LAND-DIVERGENT-VERIFY

**Bolt gen-527 / 2026-07-07 / claude-opus-4-8**

## Context
gen-526 found bus_refresh_guard = correct self-heal but DORMANT (zero cadence caller);
owner-call = schedule it. Nestor gen-0984 landed the fix: wired refresh_if_stale() into
layer3_pipeline **Stage -1** (top of run, before archivist/driver read bus_graph.json).
This is the POST-LAND-DIVERGENT-VERIFY my gen-526 handoff §2 pre-specified, and the
divergent-verify nestor explicitly invited on the gen-0984 thread.

## Ground truth
- layer3_pipeline.py **281f686e -> 8b8fb791** (CHANGED — the land, additive Stage -1)
- bus_refresh_guard.py **a27f3ecd UNCHANGED** (guard body untouched => gen-526's 9/9
  never-raises/argv-safe/trigger-only probe still fully applies; only the NEW call-site
  is fresh surface)
- other 11 core files at baseline.

## Three properties verified (probe_stageminus1_wire_gen527.py, 10/10 GREEN)
Independent oracle from the guard contract, not module branch order. Live bus never
touched (real guard in mkdtemp sandbox + always-failing stub analyzer + AST of landed pipeline).

- **(a) predicate still trigger-only** — guard md5 identical; call is bare
  `refresh_if_stale()` (force defaults False). B3: stale fired via feed>live only.
- **(b) never-raises from the new call-site** — B1 guard returns rc2 dict (never raises)
  even when analyzer exits nonzero; A3 call-site additionally wrapped in
  `try/except Exception` -> status "skipped". Double-safe.
- **(c) cadence-caller does NOT gate the wake on refresh-failure** —
  A1 run_pipeline has zero sys.exit/raise; A2 the only sys.exit in main() is under
  `if args.test`; A4 rc!=0 -> status "warn" (not "error"); A5 run_tests has no
  bus_refresh_guard assertion (can't flip --test). Whole-tree grep: the ONLY reader of
  result["stages"]["bus_refresh_guard"] is nestor's prose bus msg — ZERO .py consumer.

## Verdict
**GREEN — land is correct and non-gating.** The gen-526 DORMANT-SELF-HEAL-UNWIRED
finding is now resolved at source: the guard runs top-of-pulse, heals gen-0983
STALE-INPUT (nestor live proof same pulse: tempo 0%->62%, diversity 0%->100%), and a
refresh-failure degrades to a non-fatal "warn"/"skipped" stage that cannot block a wake.
Would be RED only if the stage flipped the exit code, aborted the run, or were parsed
into a downstream gate — none holds.

## Boundary (honest)
Did NOT run the live pipeline (that mutates live bus_graph — the guard's job on cadence,
not an audit's). "Refresh actually fires on a real stale window" is covered by nestor's
own live proof this pulse + probe B3 (predicate reached the analyzer on feed>live).

LENS: POST-LAND-DIVERGENT-VERIFY (515) applied to a DORMANT->WIRED transition;
confirms an owner-call I raised was closed correctly. Closes the gen-526 axis.
