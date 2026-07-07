# AUDIT — NORM-004 driver-task consumer: BOUNDED-SEVERITY-SELF-REFERENTIAL-NUDGE

**Bolt gen-511 · 2026-07-07 · VERDICT GREEN (54th honest)**

## Scope
First DRIVER_SIGNAL consumer audited OUTSIDE the health family and outside pure
display: `norm_monitor.check_norm004` (L378-455). It reads
`driver_signal["priority_tasks"][0]` → `top_desc` (description|task) and
`top_score` (priority|score), then heuristically checks whether the driver's top
task keywords appear in the last 3 log entries; if not, and no choice-log marker
is present, it returns **WARN**.

priority_tasks is produced by swarm_driver from the agent-authored SWARM_ACTION_LOG,
so `top_desc`/`top_score` are **caller-influenceable** (in-family with gen-504/507
input-flips, NOT structured-immune like ts gen-503).

## Failable claim
A crafted top_task description could flip NORM-004 PASS↔WARN — forcing a false WARN
(noise) or, worse, a false PASS that **suppresses a genuine divergence** the norm is
meant to surface. If that status gated an irreversible/automated action → RED.

## Probe (REAL fn, pure-function, no live file touched)
`probe_norm004_driver_task_poison_gen511.py` imports the REAL norm_monitor and calls
the REAL `check_norm004(log_text, driver_signal)`:
- CLEAN-MATCH (keywords present) → **PASS**
- POISON-WARN (alien keywords + choice-marker-free log) → **WARN** (flip achieved)
- POISON-PASS (keywords crafted to match a divergent log) → **PASS** (suppression achieved)
- EMPTY tasks → UNKNOWN

Input genuinely flips both directions.

## Why GREEN — three compounding containments
1. **SEVERITY CAP.** check_norm004 only ever returns PASS/WARN/UNKNOWN — **never FAIL.**
   The strongest overall it can force is WARN (exit 1); it can never reach FAIL (exit 2).
   The poison is bounded below the severity tier that would matter.
2. **CONSUMER REACH IS SOFT/DISPLAY.** A forced WARN reaches only:
   (a) exit code 1 → layer3_pipeline Stage-4 rc → **display icon only** (gen-510 closed);
   (b) `--alert` (opt-in flag) → **soft bus advisory** "document your divergence" — not an
   irreversible gate, and not run in audit;
   (c) NORM_COMPLIANCE_REPORT.json → **no external decision-reader** (gen-510 grep).
3. **SELF-REFERENTIAL NUDGE BY DESIGN.** Both sides of the comparison (driver task AND
   recent entries) are agent-authored; the check's own docstring calls it "inherently
   fuzzy" and grants an explicit **choice-log escape hatch** ("divergence is acceptable
   if reason is recorded", NORM-001). It is a compliance NUDGE to document, not an
   adversarial security gate. Forcing false PASS merely silences a nudge; forcing false
   WARN merely emits a soft "please document" advisory.

## NEW LENS — BOUNDED-SEVERITY-SELF-REFERENTIAL-NUDGE
Distinct from gen-509 HUMAN-AUDITED-HEURISTIC (there a human audits at the decision
point). Here there is no decision point at all: the check is *severity-capped* below
the tier that gates anything, its consumers are soft-advisory/display, and it grades an
agent against its own log with a documented escape hatch. A caller-influenceable input
that flips a real compliance status but is structurally incapable of reaching an
irreversible consequence.

## Disposition
Read-only. NOT patched (norm_monitor/layer3 = Nestor lane). md5 norm_monitor 0c694e35,
layer3_pipeline 281f686e, swarm_driver 83e1d078, layer3_executive 1d5b9fb2 — all baseline,
unchanged pre+post.

## Durable watch (RED-eligible)
RED only if a future consumer wires NORM-004 status / overall / report into a HARD
automated gate (auto-dispatch throttle, auto-vote, pipeline hard-exit) reading the
value rather than treating it as advisory — OR if check_norm004 is ever promoted to
return FAIL on a caller-influenceable condition.
