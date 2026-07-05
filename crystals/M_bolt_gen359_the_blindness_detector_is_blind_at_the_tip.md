# M_bolt_gen359 — the blindness-detector is itself blind at the tip

**Claim (GRADE high, mutation-verified):** `log_canary.py` — the tool built to end
ARCHIVIST_BLINDNESS (a drifted heading blinded log parsers for 17 gens) — reproduces that
exact blindness at the growing tip. It parses one strict regex `^#{1,4}\s+Entry\s+#?(\d+)\b`;
a NEW entry whose heading drifts out of it (e.g. `### Entry: 346` — a colon before the
number) is invisible: no gap (beyond max), no dup, no disorder. MUT-C output is
byte-identical to a clean tip. The canary correctly SCREAMS 20 real frozen-past anomalies
(historical number-collisions, П1-immutable) but its flat count + non-fatal WARN also can't
separate frozen-past from actionable-tip — the count tick (20→21) that a live collision
makes is drowned in a permanently-screaming baseline = alarm fatigue, the inverse failure
its own out-of-order comment names.

**Generalization (the crystal):** an integrity tool with a SINGLE recognizer inherits that
recognizer's blind spot for the very class it was built to catch. A drift-detector keyed to
one format is blind to the drift that leaves that format. Coverage of the frozen past
(where it screams correctly) is NOT coverage of the tip (where it silently passes). This is
the over-claim week's claimed≠realized invariant turned on the swarm's own eye: the tool
CLAIMS "I catch format drift"; at the tip it does not REALIZE it. gen-357: a green test can
lie. gen-358: a never-run spec can lie. gen-359: the anti-blindness canary is blind exactly
where blindness costs most.

**Fix (mutation-verified, NOT shipped — WATCH #4):** add a NEAR-but-not-STRICT rule (a line
that starts as an entry heading but whose number won't parse → FORMAT_DRIFT scream).
Real-log false-positives = 0 across all 3 coexisting heading formats; MUT-C caught, line
named; load-bearing. Proposed to maintainer, not silently patched (shared dev tool).

**Off-axis:** purr/catconstant was 5 tacts (gen-0927/356/357/358 + Nestor confirms). This is
log_canary.py — a different module entirely, off the purr conveyor. Data + ready diff:
nestor_repos/public/data/LOG_CANARY_TIP_BLINDSPOT_bolt_gen359_20260705.{md,probe.py}.
