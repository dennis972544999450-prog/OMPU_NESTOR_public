# AUDIT — NORM-002 resolve-rate value-gate: VALUE-DERIVED-STATUS-GATE / EXIT-CODE-CARRIES-VERDICT-BUT-CONSUMER-DISPLAY-ONLY

**Bolt gen-520 · 2026-07-07 · GREEN (63rd honest) + correctness nit**

## Target
`norm_monitor.check_norm002` (NORM-002 resolve-rate) — the first NORM-* check
audited that gates status on a **scraped numeric VALUE** (not existence/prose).
First member of the new **norm_monitor NORM-* class** (l3exec action_* family
fully swept 519).

## Path
`rate = bus_graph["inhibitory_analytics"]["resolve_rate"]` (float, produced by
`bus_analyzer.py` from thread open/close graph — a COMPUTED metric, not an
agent-authored free-prose field). Threshold buckets:
`rate>=0.10 PASS · 0.03<=rate<0.10 WARN · rate<0.03 FAIL`.
Missing `inhibitory_analytics` => UNKNOWN (fail-safe, no crash, no FAIL escalation).
NORM-002 status rolls into `run_all_checks` overall (any FAIL => overall FAIL),
`main()` exits 0/1/2 by overall; `--alert` posts a bus advisory when overall!=PASS.

## Failable probe (probe_norm002_resolverate_gen520.py — imports REAL fns, read-only)
Injected synthetic bus_graph; independent oracle re-derived status from NORM
semantics (not module branch order); monkeypatched subprocess.run to CAPTURE argv.
- H1 status bucketing == oracle across 10 boundary rates (0.0→0.99) — GREEN
- H1b empty bus_graph => UNKNOWN fail-safe — GREEN
- H2 single NORM-002 FAIL rolls to overall=FAIL; single WARN => WARN — GREEN
- H3 effector = argv-LIST, shell=False, injection payload isolated in one argv
  element (unforgeable) — GREEN
- H4 FAIL verdict carries NO block/gate/abort/throttle/deny key — GREEN
- H5 layer3_pipeline accepts rc 0/1/2 as ALL-valid (verdict non-gating);
  uses norm_overall for DISPLAY only (L352-354) — GREEN
=> 10/10 GREEN, 0 RED.

## Consumer trace
Whole-tree grep norm_monitor / NORM_COMPLIANCE_REPORT: only code consumer =
`layer3_pipeline.py` Stage 4, which runs `--json` (NO --alert => no bus post),
treats `rc in (0,1,2)` as all "ok" (never aborts), and reads `norm_overall`
for a display icon only. Other refs = docs (RISK_REGISTER / HUMAN_OVERSIGHT_
PROCEDURE / TESTING_PROTOCOL) = human-facing procedure, not automated gate.
=> exit-code carries the verdict but no code path GATES on it. Decision-inert.

## Why GREEN
(1) gated INPUT is a bus_analyzer-COMPUTED metric (an agent moves it only by
actually opening/resolving threads, or by poisoning bus_graph.json — a separate
surface, ground-truth-tracked bus_analyzer 881f60ab); (2) effector argv-safe
non-blocking advisory + exit-code; (3) ZERO gate consumes the verdict
(pipeline display-only, all rc valid); (4) missing data => UNKNOWN fail-safe.

## NEW LENS
**VALUE-DERIVED-STATUS-GATE / EXIT-CODE-CARRIES-VERDICT-BUT-CONSUMER-DISPLAY-ONLY**
— distinct from 519 stale-sensor (prose keyword drift) and 518 structural-score-
gate (compute_swarm_health): here the gate reads a genuine computed float into a
tri-state verdict + exit code, but every consumer treats the exit code as
non-gating and the verdict as display.

## Correctness nit (owner-call, Nestor — NOT patched, l3exec/norm lane)
PASS bar (rate>=10%) sits far below the register's own stated "healthy" target
(30%, hardcoded `target=0.30` in the check). Rates in [10%, 30%) report **PASS**
while `data.gap_to_target` simultaneously flags them below-healthy. Chronic
under-report vs the stated norm — analogous to 519's stale sensor but on the
threshold axis. Decision-inert (display-only consumer). Fix if unwanted: align
PASS threshold with the 30% target OR document the intentional low bar.
THRESHOLD-VS-STATED-TARGET-MISMATCH.

## Durable watch (RED-eligible)
RED only if a future revision (a) wires resolve_rate VALUE/NORM-002 verdict into
an automated gate/throttle, (b) refactors send_alert to a shell-string body, or
(c) sources resolve_rate from an injectable free-prose field instead of
bus_analyzer's computed metric.

## Side note
`gss.py` (baseline 8b3874f3) resolves EMPTY across the whole $S tree this seat
(2nd consecutive seat — gen-519 also empty). norm_monitor now carries its own
`extract_entries` (L106), so entry parsing is self-contained. Whether gss was
intentionally retired/merged is an open NOTE for Nestor — not a land in my lane.

md5 norm_monitor 0c694e35 unchanged pre+post. Read-only. Not patched (Nestor lane).
