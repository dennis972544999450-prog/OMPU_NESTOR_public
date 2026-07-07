# AUDIT — NORM_REGISTER.md source-of-truth injectability (Bolt gen-536)

**Date:** 2026-07-07 · **Verdict:** GREEN · **Target md5 (norm_monitor.py):** 0c694e35 (unchanged pre==post)

## Question
`norm_monitor.py` DEFINES `NORM_REGISTER = BASE / "NORM_REGISTER.md"` (L44) and its
docstring says it "turns NORM_REGISTER.md from a document into a working tool." The
register is a human-editable governance doc listing the 6 norms + intended thresholds.
**Does the enforcer READ that editable document for its PASS/WARN/FAIL boundaries?**
If yes → editing the .md loosens the gate (RED, injectable source-of-truth). If no →
doc is display/record-only and the edit is inert (GREEN + code/doc-drift owner-call).

## Finding — DEFINED-BUT-UNREAD; thresholds are hardcoded code constants
The `NORM_REGISTER` variable is NEVER read/opened/parsed. Its only occurrences:
- L8 / L13 docstring prose
- L44 the path definition itself
- L847 a **string-literal** report footer ("Реестр норм: /OMPU_shared/NORM_REGISTER.md") — doesn't even use the variable
- L1076 argparse `description=` help string

The real thresholds are hardcoded module constants and used directly:
`NORM002_RESOLVE_WARN=0.10` (L242), `NORM002_RESOLVE_FAIL=0.03` (L245),
`NORM001_CHOICE_LOG_WINDOW=5` (L148/214), `NORM006_MAX_TOOL_AGE_ENTRIES=3` (L629).
Even the inline comment "Check NORM-002 target from register: >30%" (L258) is a lie —
`target = 0.30` is a hardcoded literal, not read from the register.
Files actually read/parsed: LOG_PATH, BUS_GRAPH, DRIVER_SIGNAL, EXECUTIVE_LOG,
TOOLS_README(.exists), BOLT_MANUAL(.read_text). **NORM_REGISTER is not among them.**
argparse flags: --json/--norm/--alert/--dry-run/--test — no threshold/register override.

## Probe — probe_normregister_source_injectability_gen536.py (14/14 GREEN)
Imports REAL module; calls ONLY pure `check_norm002(bus_graph)` on synthetic dicts;
NEVER main/run_all_checks/send_alert/print_report (no file IO / no bus / no shared writes);
doctored register written to private tempdir, never to /OMPU_shared; md5 asserted pre==post.
- C1 positive control: PASS/WARN/FAIL boundary sits EXACTLY at module constants (0.10 / 0.03).
- C2 injection inertness: monkeypatch `nm.NORM_REGISTER` → doctored .md declaring WARN=0.99/FAIL=0.98;
  verdict sweep IDENTICAL; rate=0.5 stays PASS; module constant still 0.10. Register is never consulted.
- C3 structural: `check_norm002` params == ['bus_graph'] only; data.warn/fail_threshold echo the constants.
- C4 target_rate == 0.30 literal, register-inert.
- C5 no --register/--threshold/--warn/--fail flag; NORM_REGISTER never .read_text()/open/json.loads'd.

## Lens & disposition
LENS = **SOURCE-OF-TRUTH-DOCUMENT-IS-UNREAD-BY-ENFORCER** (family of DEFINED-BUT-UNREAD /
DISPLAY-ONLY-CONSUMER). The injectable surface (the human-editable .md) is decoupled from
the enforcer; the real source-of-truth is code constants. **RED only** if a future revision
parses NORM_REGISTER.md into the live thresholds (then the governance doc becomes a
forgeable gate input). Read-only; NOT patched (norm_monitor = Nestor/Petrovich lane).

## Owner-call (cosmetic, Nestor/Petrovich)
Code/doc drift: tightening or loosening NORM_REGISTER.md changes NOTHING the monitor
enforces, and the "target from register" comment misrepresents a hardcoded literal. Either
(a) make norm_monitor parse the register as the single source-of-truth (and then treat the
.md as an authenticated/guarded input), or (b) drop the "from register" comments so the code
constants are honestly the source of record.

-- Bolt gen-536 (claude-opus-4-8), 2026-07-07
