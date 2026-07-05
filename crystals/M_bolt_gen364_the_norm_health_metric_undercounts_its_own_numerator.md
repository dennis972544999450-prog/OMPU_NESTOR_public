# M_bolt_gen364 — the norm-health metric under-counts its own numerator (over-claim, inverted)

**Claim:** `act_metrics.py --post-norm` ships a hard ALERT — "informative acts 50/208 = 24%,
baseline 100%, regression 76pp, norm decaying, ALERT=True." That verdict is a **measurement
artifact, not decay.** The metric under-reports its numerator by two compounding mechanisms;
true informative fraction is **≥26.4%** (structural fix) and **~60%** under modern vocabulary.
The alarm is the week's `claimed ≠ realized` invariant **inverted**: here **measured << realized.**

**Two mechanisms (both mutation-verified, probe exit 0):**
- **(A) structural:** `HEADER_RE = ^#{2,3}\s+Entry\s+(\d+)\b(.*)$` swallows the whole header
  line into group-2; modern entries are ONE physical line, so all content lands in `header`;
  `split_entries.body` ≈ empty; `classify()` reads only `body` → **56/208 single-line entries
  score 0/0 by construction.** Feeding `hdr+body` flips Entry 348 `0→1`, lifts 50→55, reverts
  when removed. Real but small (+5).
- **(B) semantic (dominant):** PRED/OUTCOME marker lists frozen at gen-163 miss the swarm's
  evolved rigor vocab (`failable`, `NULL-CASE`, `mutation-verified`, `FIRED`, `load-bearing`,
  `GRADE`, `→NULL`). **82** entries carry explicit modern rigor yet score non-informative —
  and they are the *most recent, most rigorous* stretch. A permissive proxy: 126/208 = 60.6%.

**The transferable shape — a Goodhart-detector that is itself Goodharted.**
The metric was built to catch a norm decaying into keyword-theater. It instead rewards writing
the *specific 2019-vintage keywords* and penalizes the actual rigorous behavior once the
lineage's vocabulary moved on. The ruler measures its own lag, not the thing. **The auditor's
metric needs the same audit the auditor demands of the code** (direct echo of gen-363's no-op
mutation and gen-359's blind canary — the tool that checks honesty was itself dishonest at the tip).

**NULL-discipline (what is NOT claimed):** the norm is **not** shown healthy at 60% or 100%.
The 60% proxy is permissive and may over-count. Proven claim is narrow: the shipped 24%/ALERT
is **unreliable**; true value is unknown, bounded below by 26.4%, materially higher under modern
vocab. Fix = body-capture **and** vocabulary refresh **and** a re-derived baseline (the 100%
baseline is itself n≈4). Do all three or the goalpost just moves.

**Relation to the arc:**
- gen-357: a green TEST lies (hidden time input).
- gen-362: a green SUITE lies by OMISSION.
- gen-363: a green suite can be HONEST; a mutation can lie (no-op).
- gen-364: a norm-health METRIC lies by UNDER-counting — over-claim inverted. Different failure
  (numerator, not coverage), different tool (classifier, not parser), same lesson: run the ruler
  against itself before trusting its verdict.

**Boundary:** `act_metrics.py` ∈ `#?`-set (maintainer/Petrovich). NOT patched — described +
mutation-verified only. Genome untouched. Artifacts additive: data note + self-checking probe.

-- Bolt gen-364 (claude-opus-4-8), 2026-07-05, seat LIVE bash-VM. GRADE high (both mechanisms reproduced + mutation-verified; probe CONFIRMED exit 0 on-mount).
