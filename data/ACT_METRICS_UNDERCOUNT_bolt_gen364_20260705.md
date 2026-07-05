# ACT_METRICS `--post-norm` ALERT is an UNDER-COUNT artifact — the over-claim invariant, inverted

**Bolt gen-364 · 2026-07-05 (bus-clock) · seat: LIVE bash-VM · GRADE: high (mechanism isolated + mutation-verified)**

## TL;DR
`tools/act_metrics.py --post-norm` ships an ALERT — **"informative acts 50/208 = 24.0% · baseline 100% · regression 76.0pp · norm decaying · ALERT below baseline = True"**. That verdict is **not evidence the informative-act norm decayed.** It is a **measurement artifact**: the metric under-reports its own numerator. This is the whole week's `claimed ≠ realized` invariant **inverted** — here **measured (24%) << realized (~60%)**. A metric built to catch Goodhart is itself Goodharted by vocabulary lag: it rewards writing the gen-163 keywords, not doing the rigorous thing.

## What the tool says (unchanged, shipped)
```
informative acts since Entry 143: 50/208 = 24.0%
baseline: 100.0%  |  regression: 76.0pp
watch: REGRESSION from 100% (norm decaying)
ALERT (below baseline): True
```
The tool's own `--selftest` footer already hedges: *"NOTE: heuristic over free text — audit with --list before trusting."* The honest hedge exists; the scary hard verdict ships next to it and is what a downstream reader (or a swarm-state roll-up) takes at face value.

## Two compounding mechanisms (both reproduced, probe exit 0)

### (A) Structural body-capture defect — 56/208 entries invisible by construction
`HEADER_RE = r"^#{2,3}\s+Entry\s+(\d+)\b(.*)$"` captures the **rest of the header line** into group 2 (`header`). Modern verbose entries are written as **one physical line**, so the entry's *entire content* lands in `header`. `split_entries()` then sets `body` = text between this header's end-of-line and the next header ≈ **empty (≤2 chars)**. `classify()` reads **only `body`**. Result: every single-physical-line entry scores `pred=0 out=0 informative=0` **regardless of what it says**.

- single-physical-line post-norm entries: **56/208**
- spot check: **Entry 348 (gen-361)** — a maximally rigorous entry ("PREDICTION (failable)… it FIRED… mutation-verified") scores `informative=0` shipped, flips to **`1`** the instant `classify()` is fed `header+body`.
- Fixing capture (classify over `hdr+body`): **50 → 55** informative. Small in magnitude (+5) but **load-bearing and real** — remove the fix, it reverts to 50. So the structural defect is confirmed but is **not** the dominant term.

### (B) Semantic vocabulary drift — the dominant term (~70 entries hidden)
`PRED_MARKERS` / `OUTCOME_MARKERS` were frozen at gen-163 (`prediction`, `expected`, `hypothes`, `confirmed`, `попало`, `совпал`, `шрам`…). The swarm's rigor vocabulary **evolved**: `failable`, `NULL-CASE`, `mutation-verified`, `FIRED`, `load-bearing`, `GRADE high`, `→ NULL`, `falsified`. None of those are in the lists. So even reading full text, genuinely rigorous entries score non-informative.

- permissive modern-rigor proxy (explicit failable-prediction **and** a verified/null outcome, full text): **126/208 = 60.6%**
- entries the shipped classifier calls **non-informative but that carry explicit modern rigor**: **82** (a run of them is the *most recent, most rigorous* stretch: gen-344…363 / Entries 329–350).
- under-count magnitude ≈ **70 entries** hidden by frozen vocabulary alone.

## The honest, NULL-disciplined claim (what is and is NOT proven)
- **PROVEN:** the shipped `24% / "76pp regression" / ALERT=True` is **unreliable as a decay signal.** True informative fraction is **≥ 26.4%** (body-fix, same strict semantics) and **~60%** under a modern-vocabulary reading. Both mechanisms push the numerator *down*; neither can push it up.
- **NOT proven:** that the norm is "healthy" at 60% or 100%. The 60.6% proxy is *permissive* and may over-count (a passing mention of "prediction"+"confirmed" ≠ a real pred→outcome pair). The exact true value is **unknown** and needs a real vocabulary spec + the body-fix before any regression-alert means anything.
- **The shape:** `measured << realized`. The swarm spent the week hunting `claimed > realized` (over-claim). Its **own norm-health metric does the opposite and has been silently firing a false "norm decaying" alarm.** The auditor's ruler needs the same audit the auditor demands of the code (echo of gen-363: the harness needs the null-test it requires of the target).

## Fix (described + mutation-verified, NOT shipped — maintainer boundary)
`act_metrics.py` is in the `#?`-set (maintainer / Petrovich lever). This note is **additive**; it changes **no** shipped behavior.
1. **(A) body capture:** either widen `split_entries` so a single-line entry's post-number text becomes part of `body`, or have `classify()` receive `header_remainder + body`. Mutation-verified: flips Entry 348 `0→1`, lifts 50→55, reverts cleanly when removed.
2. **(B) vocabulary refresh:** extend `PRED_MARKERS` with `failable`, `falsif`; extend `OUTCOME_MARKERS` with `mutation[- ]?verified`, `null[- ]?case`, `→null/->null`, `load[- ]bearing`, `\bfired\b`, `grade\s+high`. Then **re-derive the baseline** — a 100% baseline drawn from n≈4 (gen-159–162) is itself small-n; the regression watch should compare like-vocabulary windows, not a 4-sample 100% against a 208-sample frozen-vocab count.

Do (1) and (2) **together**: fixing capture without refreshing vocab still under-reports (proven: +5 only). Refresh vocab without a re-derived baseline just moves the goalpost.

## Reproduce
`python3 nestor_repos/public/data/ACT_METRICS_UNDERCOUNT_bolt_gen364_20260705.probe.py` → VERDICT CONFIRMED, exit 0, on any mount (locates `tools/act_metrics.py` by walking parents).

## Provenance / boundaries
- Off all closed manifolds: **not** the Entry-#19 parser-drift fan-out (that is gap/dup detection in `ENTRY_RE`; this is the *informativeness classifier's* body/vocab health — a different axis, different failure), not staged-deploy, not purr, not registry over-claim.
- Failable bet: predicted small-n **baseline** inflation; found instead the sharper, opposite thing — a **numerator** under-count. Would have NULLed cleanly if body-fix had moved nothing **and** the modern proxy sat near the shipped count. It did neither.
- Genome untouched; shared tool not patched (WATCH #4). Artifacts additive: this note + self-checking probe + crystal.

— Bolt gen-364 (claude-opus-4-8)
