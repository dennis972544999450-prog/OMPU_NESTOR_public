# DIVERGENT-VERIFY + null-case: repair_traffic wildcard collateral preemption (gen-560)

- **Author:** Nestor gen-0995 (claude-opus-4-8, Cowork bash-VM seat)
- **Date:** 2026-07-09
- **Subject:** `tools/repair_traffic.py` — md5 `3a37a4446f22cda05ca0d8cd910ab136` (pre==post, read-only)
- **Verifies:** Bolt gen-560 (`AUDIT_repair_traffic_wildcard_collateral_preemption_LATENT_bolt_gen560`)
- **Verdict:** CONFIRMED (LATENT) + one genuinely-new finding on the obvious cure
- **Probe:** `verify_repair_traffic_wildcard_preempt_DIVERGENT_nestor_gen0995.py` — 11/11 PASS

## What Bolt found (confirmed)
`find_blockers()` uses the **symmetric** `conflicts()` predicate, whose over-match is
justified as "conservative — an acquirer waits when in doubt." That is correct for the
**wait** path (a non-force acquire just returns HELD). But the *same* `find_blockers()`
feeds `cmd_acquire`'s **preempt loop**, which marks **every** blocker `preempted`. So a
narrow `--force` acquire of `site:x` collaterally preempts a broad `all-sites` lease that
was protecting unrelated targets. The over-match that is safe on the wait path becomes
unsafe on the force path.

## Divergence from Bolt's seat (not a re-run)
1. **Predicate-level proof.** Instead of seeding through `cmd_acquire`, I drove the
   decision logic directly: `conflicts('all-sites','site:x')==True`,
   `conflicts('site:x','site:y')==False`, and `find_blockers(state,'site:x')` returns the
   broad lease as a blocker. The bug lives in the engine's predicate, not in how the probe
   seeds leases (P1–P3).
2. **End-to-end from direct-built state** (F1): narrow `phi/site:x` `--force` acquire →
   `nestor/all-sites` goes `preempted`; F2: an unrelated `site:y` then reads `NO_LEASE`
   while nestor still believes it holds `all-sites` → collision window.

## NULL-CASE ON SELF — the obvious cure is its own bug
Bolt's cure sketch was "skip/refuse wildcard blockers under a narrow acquire." I
implemented and stress-tested it before endorsing:

- **Cure A** ("skip wildcard blockers in the preempt loop, still grant the narrow
  lease"): produces a **DOUBLE-GRANT overlap** — `nestor/all-sites` stays `active` AND
  `phi/site:x` becomes `active`, both live over the `site:x` intersection. This trades
  collateral-preempt for two owners simultaneously holding an overlapping surface — a
  *different* collision, not a fix. Rejected (probe `A_cureA_creates_double_active_overlap`).

- **Cure B** ("refuse the force-acquire when a **broader** wildcard blocker exists;
  require every blocker to be scope-precise to preempt"): correct on all three controls —
  - narrow-vs-broad → **refuse**, broad stays `active`, nothing granted (B1);
  - narrow-vs-narrow emergency → **still works**, precise blocker preempted, unrelated
    narrow untouched, new lease granted (B2);
  - genuinely-broad acquire (acquirer IS the wildcard) → legitimately subsumes narrows (B3).

  Cure B closes the collateral-preempt without opening the double-grant.

The check-side `covers()` directional guard (Bolt gen-391) is unaffected — the bug is
preempt-only (CK).

## Disposition
**Verify + report + cure-analysis. NO patch, NO deploy.** `tools/` engine lane is
Nestor/Petrovich + needs Den-GO — the preempt semantics touch emergency-repair intent
(and the `>=` same-tier co-note Bolt flagged). Recommendation for the eventual land:
implement **Cure B** (scope-refuse broader wildcard blockers), NOT Cure A (skip-and-grant),
because the naive skip creates a double-active overlap. Land only after Den-GO.

## Co-note echo
Bolt's `can_preempt` uses `priority >= top.priority` (same-tier peers can force-preempt
each other). Defensible for emergencies; still an intent call for Den/Petrovich, orthogonal
to the scope fix above.
