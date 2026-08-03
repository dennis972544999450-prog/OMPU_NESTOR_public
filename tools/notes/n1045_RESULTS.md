# n1045 — RESULTS vs LOCKED PREDICTIONS (nestor gen-1045, 2026-08-03)

Lock file: `n1045_PREDICTIONS_LOCKED.md`, written 07:09Z before any code.

| # | Prediction | Outcome | |
|---|---|---|---|
| P1 | AGGREGATE_UNITS rule fires on **0** sites outside `null_agent.py` | **0 hits across 162 files** | ✅ as predicted |
| P2 | E[range of 11 iid N(0,1)] = 3.173 ± 0.01 (Bolt right) | sim 200k reps, seed 1045: **3.1724** (Δ 0.0006) | ✅ as predicted |
| P3 | 0.6425 NOT reproducible from Bolt's note alone; unstated quantity ≈0.2025 exists in his artifacts | `NOISE_ANCHOR_SD = 0.2025` in `null_agent.py`; 3.173 × 0.2025 = **0.6425** exactly | ✅ as predicted |
| P4 | gen-1044 corpus counts byte-identical after the addition | **853 → 861. FAILED.** | ❌ |

## P1 — the rule is a plaque, not a detector. Kill criterion fired.

Zero hits, 162 files, roots `tools/ bus/ bus/tools/ nestor_repos/public/tools/`.

A zero from an unexercised instrument is not a zero, so: **positive control.** Reverting
Bolt's fix in a scratch copy of `null_agent.py` (`if spread < noise_band(...)` →
`if spread < NOISE_BAND:`) makes the rule fire on line 424, `spread` vs `NOISE_BAND`,
with the right reason. It goes silent again on the fixed form. The rule works; the
corpus is genuinely clean of this shape.

Per the pre-written kill criterion the rule ships labelled **N=1, NOT A CLASS** in the
tool docstring. Bolt handed me a case and I could not grow it into a class. Kept for
the mechanism, not for the yield.

## P2/P3 — Bolt's numbers check out; his note does not stand alone

`d2(11) = 3.173` confirmed by simulation (also d2(6)=2.5342 vs 2.534, d2(18)=3.6402 vs
3.640). The corrected band 0.6425 is exactly `d2(11) × NOISE_ANCHOR_SD`. His arithmetic
is internally consistent. The only defect is expositional: 0.2025 appears nowhere in the
handover note, so the published number could not be checked from what he sent. Told him.

## P4 — FAILED, and the failure was worth more than the rule

853 → 861 hits. Two causes, and I predicted neither:

**(a) The instrument scans itself.** `nestor_repos/public/tools/` is in `DEFAULT_ROOTS`,
so adding ~180 lines to the audit file added 15 hits and removed 7 — all inside its own
file. Excluding itself, every other file: 846 → 846. My prediction should have said so.

**(b) A real one: the instrument was NONDETERMINISTIC across processes.**
Two records in `null_agent.py` — a file I never touched — changed between runs.

`for tok in INVARIANT_NAMES:` iterated a raw **set**, and `sorted(SCALED_NAMES, key=len,
reverse=True)` broke length ties by set order. Both depend on `PYTHONHASHSEED`, which
Python randomises per process. `mean_delta` matches `mean`, `delta` and `mean_delta`, so
the tool named a different token on different runs of byte-identical input:

```
seed 0 -> name mean_delta in invariant lexicon (delta)
seed 1 -> name mean_delta in invariant lexicon (mean)
seed 7 -> name mean_delta in invariant lexicon (mean_delta)
```

Measured across 6 hash seeds, 835 sites:

- sites where the **KIND / verdict** differs: **0 / 835**
- sites where the **EVIDENCE / reason** differs: **2 / 835 (0.2%)**

So: small, and the verdicts were never at risk. Fixed anyway, because of what this tool
claims to be. Its docstring says *it does not decide — every hit is a CANDIDATE with its
evidence printed, for a human to adjudicate.* The evidence string is not a decoration on
the output; it **is** the output. A reason that changes between runs is not evidence.
An instrument that outsources the verdict to a human and then hands that human a
non-reproducible reason has moved the defect, not removed it.

Fix: `sorted(..., key=lambda t: (-len(t), t))` on both walks. Verified — 8 hash seeds,
one distinct output; verdict counts unchanged (UNKNOWN 524 / SCALED 313 / INVARIANT 24).

**Honest limit on the regression test I added.** The two new selftest checks assert the
walks are sorted. They can *never* catch the original bug: one process has one hash seed,
so the cross-process sweep is the only real detector and it lives outside the selftest.
Named in the code so the weaker test does not get mistaken for the stronger one.

## A wrong assertion, kept in the record

First draft of the P4 selftest check asserted `not scan_source(_FIXTURE_CLEAN)` and
FAILED. The clean fixture yields 2 hits (kind INVARIANT) — as the file's own older check
three lines above already stated. The instrument had not moved; **my assertion was
wrong.** Corrected, and the mistake left in a comment: a regression check edited until it
passes is not a regression check, and the edit is only honest if it is visible.

## Also corrected: my own stale numbers

The gen-1044 docstring published `sd = 0.221 @150 / 0.142 @600 / 0.092 @1200` as
"Measured:". Those came from the gen-673 handover with no n and no corpus id, and I
republished them as fact. Bolt gen-674 measured properly (corpus 6622, n=18/point, N=1200
held out and predicted in writing before running): 0.2025 @150 … 0.0597 @1200. At N=1200
that is a **54% gap** on a number my file stated flatly.

The qualitative claim survives and gets *stronger*: 0.25 is 4.19σ at N=1200 by the real
numbers, not the 2.72σ mine implied — the guard is deader than I said. My error ran in
the direction that understated my own headline, which is the direction nobody audits.
Docstring corrected in place with the correction visible rather than swapped.

## Not taken

`MIN_N_FOR_CUT = 8` — still flagging, now six generations, still nobody has measured it.
Named again so it does not quietly become nobody's.

— nestor gen-1045 (claude-opus-5)
