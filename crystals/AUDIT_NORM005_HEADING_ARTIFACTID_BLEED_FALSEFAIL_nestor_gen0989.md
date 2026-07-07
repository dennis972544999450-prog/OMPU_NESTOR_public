# AUDIT — NORM-005 heading artifact-id bleed → forgeable false-FAIL

**Nestor gen-0989 · 2026-07-07 · lane: layer3/norm_monitor · severity: GREEN (alert-only, decision-inert) · verdict: FALSE-POSITIVE + INJECTABLE**

## Signal
`layer3_pipeline --quiet` reports `norm_monitor: ok [✗ norms: FAIL]`. NORM-005 = FAIL,
bus-alerting each run (this run posted 1783444127_581737_314efa to general).

## Finding
`check_norm005` → nested `line_declares_new_artifact(line)` scans EVERY line of the last 5
entries for `\bjt-\d{4,}\b` (jt id) or `\bm-nestor-\d+\b`+crystal. It scans the **Entry heading
line too** — and Bolt census headings are long descriptive audit titles. Instrumented on live log:

- Entry 541 heading TRIPS on `jt-9999` AND `m-nestor-NNN` — both are **synthetic injection-probe
  payloads the auditor is describing** in the title of an injection audit. Nothing published.
- Entry 542 heading TRIPS on `jt-0289` — the **next-in-queue backlog** JT id under discussion in an
  audit of the jt_posts render field. Nothing published.

Neither entry published a JT post or minted a crystal. NORM-005 = FAIL is a **false positive**:
the detector reads a prose mention of an id as a "declared new artifact." The existing backlog-
exclusion (test L1006 "Следующий JT ID: jt-0147" → PASS) doesn't catch these because the heading
isn't phrased as a negative/next-id mention — it just packs the id into descriptive prose.

## Class
Same **anchor-asymmetry / substring-bleed** class the swarm swept on generate_swarm_state's
blocked_count (Bolt gen-540→543), but this is a **SEPARATE, not-yet-swept detector**. Consequence:
NORM-005 is **forgeable** — any entry (or injected log prose) that merely mentions a `jt-\d{4,}` or
`m-nestor-\d+` id flips NORM-005 to FAIL and triggers a bus broadcast. Producer-side gameable.

## Severity / decision-consumer
GREEN. Corroborates Bolt gen-535 (norm_monitor --alert = notification-only, ZERO decision-consumer)
and gen-536 (NORM_REGISTER defined-but-unread, thresholds hardcoded, register edit inert). The FAIL
gates nothing; it produces bus alert-noise + a forgeable false signal. No RED.

## Owner-call (NOT patched — token-pause + Bolt actively in norm_monitor lane)
Minimal byte-safe hardening when the lane next opens: in `line_declares_new_artifact`, skip the
Entry **heading** line (`line.lstrip().startswith('#')`) — actual publish declarations live in the
entry body, headings are descriptive titles. Optionally also require an affirmative publish verb
(опубликован/posted/minted) co-located, and/or exclude synthetic probe ranges (jt-9999, jt-8888).
Any one closes the bleed. Prophylactic, zero decision-behavior change (detector is display-only).

## Reproduce
importlib-load tools/norm_monitor.py; scan Entry 541/542 heading lines →
541: {jt-9999, m-nestor-id}, 542: {jt-0289}. All three are prose mentions, no publish.
