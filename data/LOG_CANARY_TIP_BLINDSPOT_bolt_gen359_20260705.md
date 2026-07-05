# log_canary.py has an ARCHIVIST_BLINDNESS blind spot at the growing tip
**Bolt gen-359 | 2026-07-05 | GRADE high (mutation-verified) | OFF purr/catconstant**

## What was run (not read)
`tools/log_canary.py` on the LIVE SWARM_ACTION_LOG.md + 3 appended-tip mutations
(temp copies in /tmp, real log untouched). Probe:
`nestor_repos/public/data/LOG_CANARY_TIP_BLINDSPOT_bolt_gen359_20260705.probe.py`.

## Ground truth (the canary IS working on the frozen past)
Live canary SCREAMS 20 real anomalies (exit 1) — NOT false positives:
- 16 DUPLICATE entry-numbers = genuine number-collisions from historical renumber drift
  (verified by hand: Entry 045 @2308 is gen-42, @2365 is gen-43 — two DIFFERENT entries
  one number; Entry 058 used by gen-56/57/58; Entry 130 by gen-139 AND gen-148).
- 1 GAP (Entry 056 missing), 3 OUT_OF_ORDER (top-of-file gen-139/140 recap block 130-132).
All are FROZEN (entries <132, П1-immutable past). Nothing to patch there — genome is sacred.

## The failable finding (mutation table)
| tip mutation                          | strict_headings | canary anomalies | new-tip entry seen? |
|---------------------------------------|-----------------|------------------|---------------------|
| baseline (real log)                   | 362             | 20               | —                   |
| MUT-A: correct `### Entry 346 \| …`   | 363             | 20               | YES (range→346)     |
| MUT-B: colliding `Entry 346` ×2       | 364             | 21 (dup named)   | YES (caught)        |
| MUT-C: drift `### Entry: 346 \| …`    | 362             | 20               | **NO — invisible**  |

MUT-C output is BYTE-IDENTICAL to baseline. A real new entry whose heading drifts out of
the single regex `^#{1,4}\s+Entry\s+#?(\d+)\b` (here: a colon between "Entry" and the
number) is 100% invisible: no gap (beyond max), no dup, no disorder — the canary simply
never sees it and prints the same "20 anomalies" as a clean tip. This is exactly the
ARCHIVIST_BLINDNESS class (drifted heading blinds the parser) reproduced INSIDE the tool
built to prevent it — at the growing tip, the one place that matters. The canary's own
docstring: "a pipeline that prints ok on a broken log is worse than one that crashes."

Not hypothetical: the log ALREADY carries 3 coexisting heading formats
(`### … —`, `## … |`, `### … |`) that match only by luck (all keep "Entry <space> <digits>").
Format is demonstrably unstable gen-to-gen; a drift that puts ANYTHING between "Entry" and
the number (colon, dash, a stray word) → silent tip miss.

Secondary (MUT-B): even collisions the canary DOES catch surface only as a count tick
(20→21) inside a permanently-screaming WARN baseline — alarm fatigue, the inverse failure
the canary's OWN out-of-order comment fears. The flat count cannot separate frozen-past
anomalies from actionable-tip ones.

## Proposed fix (mutation-verified, NOT shipped — WATCH #4, maintainer boundary)
Add a targeted FORMAT_DRIFT rule: a line that STARTS as an entry heading but whose strict
number-parse fails is a drifted heading → SCREAM. Near-zero false positives (a real entry
heading always reads "Entry <num>").

```python
# in log_canary.py, module scope, next to HEADING:
NEAR = re.compile(r'^#{1,4}\s+Entry\b', re.I)   # "meant to be an entry heading"

# in parse(): also collect NEAR-match lines whose STRICT HEADING.match fails, e.g.:
#   drifted = []            # (lineno, text)
#   ... if HEADING.match(line): entries.append(...)
#   elif NEAR.match(line):  drifted.append((i, line.strip()[:70]))
# in analyze()/main(): for each drifted -> anomalies.append(("FORMAT_DRIFT", f"line {ln}: {txt!r} — entry heading with unparseable number"))
```
Mutation-check (probe output): REAL log FORMAT_DRIFT=0 (no new false alarms across all 3
existing formats), MUT-A=0 (valid tip not flagged), MUT-C=1 (drift caught, line named).
Load-bearing: remove NEAR rule → MUT-C invisible again.

OPTIONAL 2nd hardening (separates tip from frozen-past, kills alarm fatigue): tag each
anomaly with max-entry-relative position and let the pipeline surface only tip-region
anomalies as WARN while frozen-past stays INFO. Left as a design note, not specced.

## Boundary
log_canary.py is dev-tooling (фенотип), non-fatal, not on any production critical path,
NOT П1 genome. §7 says "защищать инструменты" — a tool deserves this fix. But it is a
SHARED tool other gens depend on; per WATCH #4 (no silent behavior change unattended) the
patch above is proposed + mutation-verified, not shipped. Maintainer (Den/Petrovich/
Hausmaster) drops it in. The 16 frozen number-collisions are П1-immutable — do NOT renumber.
