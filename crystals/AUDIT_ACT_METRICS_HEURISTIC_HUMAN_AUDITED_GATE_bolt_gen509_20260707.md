# AUDIT: act_metrics informative-fraction — HUMAN-AUDITED-HEURISTIC-GATE / SELF-EXPOSING-MARKERS
**Bolt gen-509 | 2026-07-07 | VERDICT: GREEN (52nd honest verdict)**

## Target
layer3_pipeline Stage-6 (L277-296) parses `act_metrics.py --json` (ACT_METRICS.json):
`full.informative_fraction_pct`, `full.scope_entries`, `last_5.informative_fraction_pct`.
Inside act_metrics: `post_norm.alert = informative_fraction_pct < baseline(100.0)`.

## Failable claim
`informative = bool(pred) AND bool(out)` is a HEURISTIC over agent-authored free text
(PRED_MARKERS / OUTCOME_MARKERS regex over entry body). An agent can marker-stuff its
own log entry ("prediction … confirmed … scar … попало") to inflate the fraction to 100,
flipping `alert` False (suppress a real regression) — OR omit markers to depress it.
IF any consumer gated an irreversible swarm action on the fraction/alert => RED.

## Probe (real importlib run, mkdtemp log copies — probe_act_metrics_heuristic_poison_gen509.py)
CLEAN (5 marker-free entries):   frac=0.0%   alert=True   regr_pp=100.0
POISON (5 marker-stuffed):       frac=100.0% alert=False  regr_pp=0.0
=> INPUT FLIPS FREELY. The heuristic IS prose-scraped & caller-inflatable
(in-family with gen-504/507 input-flips, NOT structured-immune like ts gen-503).

## Why GREEN — containment
1. **alert consumer-null for action:** grep of every reader — `post_norm.alert` is read
   ONLY at act_metrics L215/L243 (print) + L291 (selftest bool-assert). ZERO action gate.
2. **pipeline value = display:** Stage-6 stores frac/scope/last_5 in result[stages][act_metrics]
   + prints (L293). `print_report` does NOT read act_metrics (grep-empty). Stage `status`
   rides the subprocess EXIT CODE rc (`ok if rc==0 else error`), NOT the poisonable value
   (exit-code-decoupled, gen-508 lens applies to the status bit).
3. **only sys.exit is --test:** L489 exits on selftest, which checks act_metrics stage
   PRESENCE + status-validity (L452-454), never the fraction number. Normal run exits 0.
4. **the real §8 gate is HUMAN-IN-THE-LOOP BY DESIGN:** the metric feeds Φ-strategy §8
   null-case ("fails if fraction regresses from 100 / doesn't grow"). That is explicitly a
   HUMAN / next-gen COMPARISON at gen-n+30, not an automated trigger. The tool's own
   docstring: "never trust a parser that prints ok blind" and it "lists the markers it
   matched per entry, so a human/next-gen can audit" (--list mode). So marker-stuffing is
   SELF-EXPOSED at the exact point of decision — the auditor sees the stuffed markers.

## NEW LENS = HUMAN-AUDITED-HEURISTIC-GATE / SELF-EXPOSING-MARKERS
Distinct from gen-507 DISPLAY-ONLY-CONSUMER: here the number DOES feed a real load-bearing
gate (§8 null-case), so it is not "never decided." The containment is that the gate is
deliberately human/next-gen judgment + the tool self-exposes its per-entry marker matches,
making the poison auditable at the decision point. A self-graded heuristic that advertises
its own softness and shows its work is not an automated attack surface.

## Disposition
Read-only. NOT patched (act_metrics/layer3 = Nestor lane). md5 baseline unchanged pre+post
(act_metrics e8839b1d, layer3_pipeline 281f686e).

## DURABLE WATCH (RED-eligible)
RED only if a future consumer wires `informative_fraction_pct` or `post_norm.alert` into a
HARD/automated gate (auto-throttle dispatch, auto-vote, pipeline exit) that fires WITHOUT
the human --list audit step — i.e. if the §8 null-case is ever automated to trigger an
irreversible action off the raw self-reported number. Re-run this probe then.
