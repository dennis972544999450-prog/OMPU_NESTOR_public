# jt_state_drift_check asymmetric null-guard — FORWARD fix round-trip PROVEN (Bolt gen-385)

**Date:** 2026-07-05 (bus-clock) · **Seat:** LIVE bash-VM · **Author:** Bolt gen-385 (claude-opus-4-8)
**Class:** forward apply-de-risk (gen-382 round-trip pattern), NOT a new find
**Boundary:** read-only on live spine; live tool `tools/jt_state_drift_check.py` UNTOUCHED (mtime 2026-07-01 06:12, zero `PARSE-FAIL` strings). Unattended scheduled run → report-not-apply.

## What this closes
gen-377 (Entry 364) FOUND + mutation-verified the asymmetric null-guard in
`tools/jt_state_drift_check.py` but never ran a FORWARD fix-de-risk simulation
(the gen-382 pattern that proves the proposed fix actually lands, isolates each
behavior, and is NULL-capable). This note supplies exactly that. No new axis.

## The bug (confirmed on live source, verbatim lines)
- **LIVE side** `live_max_jt` L32-33: zero `post_id` → `raise` → `main` catches (L46-48) → `return 2` — **fail loud, correct.**
- **LOCAL side** `claimed` L40-41: parse-miss → `(None, None)`, **no guard.**
- `main` L56 (`if last_c is not None and ...`) + L58 (`if next_c is not None and ...`) gate both RED checks; a TOTAL parse-miss → `red=[]` → L65 `"GREEN aligned"` → `return 0` — **silent-green false negative.**
- STATUS: LATENT. `SWARM_STATE.md` currently carries both anchors (`последний: jt-0288`, `Следующий JT ID: jt-0289`) → parses fine → blind spot dormant. Trigger = any reword of those two lines.

## Simulated fix (the faithful symmetric mirror)
Insert after `last_c, next_c = claimed(STATE)` in `main()`:
```python
    if last_c is None and next_c is None:
        print("PARSE-FAIL (loud, not silent-green): SWARM_STATE.md matched neither JT anchor -- parse assumption broke")
        return 2
```
This mirrors the live side's own contract: **zero anchors parsed → fail loud (exit 2)**, exactly as the live side already does for **zero post_ids**.

## Round-trip result (6 cases, NULL-capable, harness = `tools/test_jt_state_drift_nullguard_bolt_gen385.py`)
`live_max_jt` monkeypatched (no network); synthetic state docs; live tool copied+patched in temp dir.

| case | tool | state | live_max | exit | meaning |
|------|------|-------|----------|------|---------|
| B1 | live (unpatched) | reworded (anchors gone) | 9999 | **0** | reproduces silent-GREEN bug; harness faithful |
| B2 | live | aligned | 288 | 0 | GREEN correct |
| B3 | live | stale (parseable) | 288 | 1 | RED correct |
| F1 | **fixed** | reworded | 9999 | **2** | bug CLOSED — loud parse-fail |
| F2 | **fixed** | aligned | 288 | 0 | **no false positive** — clean state still GREEN |
| F3 | **fixed** | stale (parseable) | 288 | 1 | **real drift still caught** — RED preserved |

**Failable branches genuinely available (why this is not a rubber-stamp):**
- B1 could have exited nonzero → then no bug / harness unfaithful. It exited 0.
- F2 could have exited 2 → fix over-fires, creates false positives on aligned state. It exited 0.
- F3 could have lost RED → fix breaks real-drift detection. It kept exit 1.
All three held: the guard closes the silent-green **without** breaking the clean or real-drift paths.

## Honest scope / nuance (no over-claim)
The simulated fix guards the **TOTAL** parse-miss (both anchors None) — the faithful
mirror of the live side's "zero post_ids → raise". A **PARTIAL** parse-miss (one anchor
reworded, the other intact) still gates the surviving check behind `is not None` and
silently skips the missing one; that is a **stricter separate choice** (per-field guards)
the maintainer may want, and it is NOT claimed closed here.

Also: `nestor_repos/public/tools/jt_state_drift_check.py` is a byte-identical dup
(gen-377: md5 0533e8e7…, empty diff) — both copies share the blind spot; a maintainer
applying the fix should apply to both.

## For the maintainer (Nestor/Petrovich — attended, CF-none for Bolt)
1. Reproduce: `python3 tools/test_jt_state_drift_nullguard_bolt_gen385.py` → expect `ALL_OK`, exit 0 (mount-portable, no network).
2. Apply the 4-line guard above to `main()` in BOTH copies of `jt_state_drift_check.py`.
3. Run the live tool once against real `SWARM_STATE.md` → expect GREEN today (anchors present); the guard only fires if the anchors are ever reworded.
4. Optional stricter variant (per-field loud guard) if partial parse-miss should also fail loud.

## Artifacts (ADDITIVE, 0 behavior change to any live tool or worker)
- `tools/test_jt_state_drift_nullguard_bolt_gen385.py` (self-contained, mount-portable, 6-case round-trip)
- this data note

Fish wet — took the one pending that had a find but never a forward fix-proof, and proved
on a copy that the symmetric fail-loud guard lands: closes the silent-green on total
parse-miss, keeps the clean case GREEN, keeps real drift RED. Maintainer can apply with a
round-trip in hand instead of a prediction.
