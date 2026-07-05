# jt_state_drift_check.py — PARTIAL-parse per-field guard: forward-sim proven (Bolt gen-387)

**Status:** verify-not-apply. Live tool UNTOUCHED (md5 80539218, both copies). ADDITIVE test only.

## Object (the one genuinely-untouched sub-object)
The applied null-guard (live L50 `if last_c is None and next_c is None: return 2`,
Nestor gen-0937) closes **TOTAL** parse-miss — both JT anchors fail to parse.
**PARTIAL** parse-miss (exactly ONE anchor reworded to None) still falls through:
L59/L61 then check only the surviving field, so the reworded anchor's staleness is
silently unevaluated => a residual silent-green.

## Forward-sim (NULL-capable round-trip, no network, mount-portable)
`tools/test_jt_state_drift_PARTIAL_perfield_forward_bolt_gen387.py` reads the LIVE
source, synthesizes BASELINE (as-is) + FIXED (per-field guard: `and`->`or`), monkeypatches
`live_max_jt`=(9999,42), runs on synthetic SWARM_STATE docs:

- [B-partial] baseline, last reworded ("prev jt post: jt-0288" dodges last/последн regex),
  next="Следующий JT ID: jt-10000" (>live, GREEN alone) -> **exit 0 SILENT-GREEN** (bug repro)
- [F-partial] per-field guard, same doc -> **exit 2 LOUD** (silent-green CLOSED)
- [F-aligned] both anchors present+aligned -> exit 0 GREEN (NO false positive)
- [F-stale]   both present+stale -> exit 1 RED (real drift STILL caught)
- [F-total]   neither anchor -> exit 2 (total case not regressed)
- **LOAD-BEARING:** baseline exit0 vs fixed exit2 on the SAME partial doc.

Failable branches genuinely reachable: B-partial could have exited nonzero (premise false);
F-aligned could have over-fired exit 2 (false positive); F-stale could have lost RED. None did.

## Honest scope note for maintainer
The minimal `and`->`or` change fixes exit-code behavior but REUSES the total-case
message ("matched neither JT anchor"), which is imprecise when one anchor DID match.
A production per-field guard should name the missing anchor(s), e.g.:
`missing=[n for n,v in (("last",last_c),("next",next_c)) if v is None]`.
This is a message-fidelity refinement, not a behavior bug — exit codes are correct as-is.

## Boundary
Read-only on live spine; patched/deployed nothing; unattended run = report/verify-not-apply.
Maintainer choice (per-field strictness) — this de-risks the apply, does not perform it.
