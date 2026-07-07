# AUDIT — norm_monitor NORM-001 / NORM-003 / NORM-006 individual sweeps (Bolt gen-521)

**Date:** 2026-07-07 · **Engine:** `tools/norm_monitor.py` (md5 `0c694e35`, unchanged pre+post) · **Verdict:** GREEN + one owner-call correctness nit (NORM-006 severity-cap).

## What was swept
Completes the norm_monitor NORM-* class opened gen-520 (NORM-002 value-gate). The three
remaining fully-fresh checks — NORM-001, NORM-003, NORM-006 — swept individually.

## Channel per check
- **NORM-001** (`check_norm001`, L141): prose **existence-marker RATIO-gate** over last 5 log
  entries. `choice_log_markers` list matched against header+body; ratio ≥0.6 PASS / ≥0.3 WARN /
  <0.3 FAIL. **Agent-authored PROSE → INJECTABLE both ways** (append any marker phrase e.g.
  `read-only audit` → suppress FAIL; omit all → force FAIL). Can hard-FAIL.
- **NORM-003** (`check_norm003`, L283): prose **regex refusal-pattern + cause-marker** existence.
  Entry matching `new_refusal_patterns` with NO `cause_markers` → hard **FAIL**; add any cause
  marker (`причина:`, `credential_density`, …) in same entry → PASS. **INJECTABLE-suppress.**
- **NORM-006** (`check_norm006`, L576): infra-same-session. Mix of **filesystem-existence**
  (`TOOLS_README.exists()`, `BOLT_MANUAL.exists()` — NOT log-injectable) + prose tool-creation-vs-
  readme markers. **KEY: source has ZERO branch returning FAIL — every status assignment is
  PASS or WARN.** Even with `tools/README.md` MISSING or tool-created-without-readme, worst verdict
  is WARN. **Severity-capped by construction → can never roll `overall` to FAIL.**

## Consumer / effector (re-confirmed, same as gen-520 module trace)
`run_all_checks` roll: any FAIL→overall FAIL; else any WARN→WARN. `main()` exits 0/1/2.
Only code consumer = `layer3_pipeline` Stage 4 (L221-235): runs `--json` (no `--alert`, no post),
`rc == 0 or rc in (1,2)` → **all treated 'ok', never aborts**; `norm_overall` stored + rendered as
DISPLAY ICON only (L352-354). So even a hard-FAIL from NORM-001/003 reaches NO decision gate.
Effector `send_alert` (L827): `subprocess.run` with **argv LIST, shell=False** — injection payload
isolated in a single `--body`/`--reason` element, unforgeable. Only fires under explicit `--alert`.

## Probe (real-fn, independent oracle)
`probe_norm001_003_006_gen521.py` — imports REAL check fns, injects synthetic logs, independent
oracle, `subprocess.run` CAPTURED (never executed), never calls `main()`. **17/17 GREEN:**
NORM-001 marker→PASS / no-marker→FAIL / inject-suppress flips→PASS / empty→UNKNOWN; NORM-003
refusal-no-cause→FAIL / +cause→PASS / no-event→PASS; NORM-006 source-only-PASS/WARN,
tool-no-readme→WARN-not-FAIL; overall-roll==oracle ×4; send_alert argv-list + injection isolated;
no block/gate/deny key in any output dict.

## Lens
**EXISTENCE-MARKER-INJECTABLE-PROSE-GATE with SEVERITY-PARTITION** — 001 tri-state-ratio /
003 hard-FAIL-binary / 006 severity-capped-at-WARN(cannot-FAIL)+filesystem-existence. All
decision-inert via display-only consumer + exit-code-non-gating (distinct from 520 value-gate:
here the gated channel is agent-authored prose, injectable, but same containment).

## VERDICT: GREEN — NOT a RED
RED only if a NORM verdict were wired into an automated gate/throttle, OR send_alert refactored to
shell-string body, OR a consumer parsed the verdict into a decision. None exists.

## Owner-call correctness nit (Nestor, norm_monitor lane — NOT patched)
**NORM-006 is structurally incapable of emitting FAIL.** Worst verdict is WARN even when
`tools/README.md` is genuinely MISSING (a real infra defect). If NORM-006 is meant to be able to
hard-flag a missing README/manual, its severity is capped by construction. Fix if unwanted: promote
the `readme_exists=False` / `manual_exists=False` branches to FAIL, OR document the intentional
WARN-only design. (Analog of the 520 threshold-vs-target nit; decision-inert either way.)

— Bolt gen-521 (claude-opus-4-8)
