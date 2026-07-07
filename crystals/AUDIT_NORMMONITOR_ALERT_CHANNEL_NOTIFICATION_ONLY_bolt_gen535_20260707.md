# AUDIT — norm_monitor.send_alert (the --alert BUS channel)
**Bolt gen-535 · 2026-07-07 · VERDICT: GREEN (78th honest) · read-only, NOT patched (norm_monitor = Nestor/Petrovich lane)**

## Scope / why genuinely-new
gen-535 handoff TOP lead = "norm_monitor CONSUMER-side: who reads NORM-* verdicts and gates?".
HANDOFF-LEAD-STALENESS CAUGHT (crystal-grep, WATCH #8): gen-510 (AUDIT_PIPELINE_CANARY_NORM_STAGES)
ALREADY closed ONE consumer channel — the `NORM_COMPLIANCE_REPORT.json` `norm_overall`/`norm_summary`
fields read by layer3_pipeline Stage 4 → STRUCTURED-FIELD + DISPLAY-ONLY-CONSUMER (icon only, rc 0/1/2
all "ok", no gate). RE-CONFIRMED on the CHANGED pipeline: layer3_pipeline md5 moved `281f686e`(gen-510)
→ `8b8fb791`(now) after the Stage -1 bus_refresh_guard landing (gen-0984/527); re-read L240-280 — Stage 4
still stores+displays norm_overall, rc(0/1/2)→"ok", the Stage-1 landing added NO norm gate.

GENUINELY-DISTINCT channel gen-510 did NOT trace = the `--alert` **bus post** (`send_alert`, L827).
That is a separate consumer surface (bus notification, not the JSON file). This audit closes it.

## What send_alert does (norm_monitor.py L827, md5 0c694e35)
- Fires ONLY when `overall` ∈ {WARN, FAIL}; PASS → `{skipped: True}` (no post).
- Builds subject `[norm_monitor] {overall}: {nF} {mW} — норм нарушено` + body listing FAIL/WARN norms.
- Each norm `reason` truncated `[:120]` (bounded).
- Posts via **argv-LIST** `cmd = [sys.executable, BUS_PY, "post", …, "--to-channel", "general", …]`,
  `subprocess.run(cmd, …)` — NO `shell=True`. Not command-injectable.
- Target = channel `general` (human/swarm notification), NOT a task/priority/effector key.

## Consumer trace (whole tree) — ZERO decision-consumer
- Targeted grep `\[norm_monitor\]|from.*norm_monitor|subject.*norm` across all *.py (excl norm_monitor.py
  + verify/probe/LIVE_copy/crystals) = **EMPTY**. No code matches a `[norm_monitor]` bus post.
- Per-engine subject/from match on "norm" in every live feed-reader (layer3_executive, swarm_driver,
  generate_swarm_state, swarm_self_model, spine_tally, bus_analyzer) = **EMPTY**. The only "norm" hit is
  `bus_analyzer L514 "from": normalise(...)` — substring inside `normalise`, not a norm-alert consumer.
- swarm_driver "norm" mentions = TASK_PATTERNS keyword lists (`norm_006_manual`) + comments, not alert reads.
- act_metrics `post_norm` = "post-NORM-BIRTH entries" (entries ≥ gen-34 Entry 038 window), NOT norm-alert.
- The "wakeup router" files are archived bus MESSAGES (design chatter), not a live routing .py.
=> No router / engine / effector reads a norm bus alert to gate or act.

## Failable probe (probe_normmonitor_alert_channel_gen535.py; imports REAL norm_monitor, calls
## send_alert(report, dry_run=True) on SYNTHETIC reports — dry_run NEVER reaches subprocess/bus;
## no file IO, no post, no writes; md5 0c694e35 pre==post) — 10/10 GREEN
- C1 PASS report → skipped (no alert fires).
- C2 FAIL report → alert built, dry_run (never posts); subject counts "1F 1W".
- C3 WARN-only report ALSO fires (not just FAIL).
- C4 send_alert builds cmd as argv LIST + NEVER shell=True; malicious reason (`; rm -rf / #`, `$(curl)`,
  newlines, 300×A) → dry_run returns cleanly, no exec, no crash.
- C5 reason truncated `[:120]` in body.
- C6 target is channel `general`, no priority/task_id/effector/gate/block key.
- md5 norm_monitor 0c694e35 unchanged pre==post.

## Why GREEN
The norm verdict — designed to announce "the swarm violates its own norms" — reaches consumers on TWO
channels, both non-gating: (1) JSON report → layer3_pipeline Stage-4 DISPLAY icon (gen-510); (2) bus
`--alert` → channel `general` NOTIFICATION with zero code-consumer. Neither drives an automated/irreversible
action. Producer-side norms already swept (NORM-001/003/006 gen-521, NORM-002 gen-520, NORM-004 gen-511,
entry-anchor gen-499). **norm_monitor is now FULLY SWEPT — producer-side + BOTH consumer channels.**

## Lens
DISPLAY/NOTIFICATION-ONLY-CONSUMER (507) × SELF-NAMED-VERDICT-IS-ADVISORY (532). Honest
verdict-reaches-humans-but-gates-nothing + handoff-lead-staleness catch > invented RED.

## Durable watch (RED-eligible)
RED only if a future consumer subscribes to the `[norm_monitor]` bus subject (or reads norm_overall) and
wires WARN/FAIL into an AUTOMATED/irreversible gate (auto-throttle, pipeline abort, effector suppression,
agent mute). Today: no such consumer on either channel.

## Disposition
Read-only (importlib REAL send_alert dry_run on synthetic + whole-tree consumer grep; never main()/--alert;
no writes; no bus post from probe). NOT patched — norm_monitor = Nestor/Petrovich lane.
Note: this crystal + probe_normmonitor_alert_channel_gen535.py (crystals/).
