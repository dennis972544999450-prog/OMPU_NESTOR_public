# pulse_log_freshness_gate: gen-381 recommended fix PROVEN to land GREEN (mutation round-trip)

**Author:** Bolt gen-382 (claude-opus-4-8) · 2026-07-05 · ADDITIVE, 0 behavior change on live source
**Kind:** apply-de-risk (forward simulation), NOT a find, NOT a re-audit of the RED set.

## Context
gen-381 characterized the live RED set `{#56,#66,#67,#68}`: #56 is FALSE (logged under
typo header `## Pulse 56` missing the `#`, gate regex `^##\s*Pulse\s*#(\d+)` misses it);
#66/#67/#68 are GENUINE backfill debt. gen-381 RECOMMENDED (Nestor-gated, unapplied):
(a) normalize pulse_log line 586 `## Pulse 56` -> `## Pulse #56` (1-char data fix, NOT a
regex relax — optional-`#` false-catches `2026` from a date header); (b) backfill
`## Pulse #66/#67/#68` from crystals M-NESTOR-0755/0756/0758.

This note EMPIRICALLY PROVES that fix lands the gate GREEN, and isolates each half's effect.

## Method (read-only on live source)
Scratch OMPU_shared tree: real `crystals/` SYMLINKED (read-only), `pulse_log.md` COPIED and
mutated. Ran the UNMODIFIED live gate (`OMPU_SHARED=$SCRATCH python3 pulse_log_freshness_gate.py`).
Live source (real pulse_log, real gate) never written.

## Result (mutation round-trip, NULL-capable)
| state | gate verdict |
|---|---|
| baseline copy (unmutated) | RED `['#56','#66','#67','#68']`  ← reproduces LIVE exactly |
| + typo-fix line 586 only | RED `['#66','#67','#68']`  ← **#56 drops, ALONE** |
| + backfill `#66/#67/#68` headers | **GREEN (exit 0)** |

Each fix attributed to EXACTLY its predicted members: the 1-char typo fix accounts for
#56 and only #56; the backfill accounts for {66,67,68} and only those. Combined -> GREEN.

## Why this is failable (not hardcoded)
Step B could have stayed RED if a 5th masked member existed (a real NULL/refutation branch);
step A could have failed to drop #56 if gen-381's typo diagnosis were wrong. Neither happened
-> gen-381's split and recommended fix are confirmed end-to-end by round-trip, not prediction.

## For maintainer (Nestor)
The recommended fix is safe and sufficient. Reproduce this exact simulation before applying:
symlink crystals + copy pulse_log to scratch, apply both fixes, run gate under OMPU_SHARED=scratch,
expect GREEN. After applying to live: run `pulse_log_freshness_gate.py` once -> should print GREEN.
