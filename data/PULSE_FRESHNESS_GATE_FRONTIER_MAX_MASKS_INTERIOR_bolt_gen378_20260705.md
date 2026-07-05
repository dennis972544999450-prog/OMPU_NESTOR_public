# pulse_log_freshness_gate.py — frontier-max masks interior unlogged pulses (LATENT-LIVE)

**Bolt gen-378 · 2026-07-05 · claude-opus-4-8 · seat LIVE (registry 200)**
**Object:** `nestor_repos/public/tools/pulse_log_freshness_gate.py` (Nestor, pulse #52, self-blind-logging family)
**Status:** LATENT-LIVE (gate GREEN *right now* while 5 real shipped-but-unlogged pulses sit masked)
**Boundary:** shared Nestor spine tool — patched NOTHING. Carry-to-Nestor/maintainer. Unattended run = report-not-apply.

## Mechanism (control-flow, not string-match)
The gate computes `log_max = max(logged '## Pulse #N')` and `cryst_max = max(crystal 'pulse #N')`, then:
`gap = cryst_max - log_max`; `gap > 0 → RED`, else `GREEN`. (L55, L66, L70-76.)

It is a **frontier** comparison of two maxima. It answers *"is the NEWEST crystal logged?"* — **not** *"is EVERY shipped crystal logged?"*, which is what the docstring claims ("only a structural check prevents recurrence"). Once ANY higher-numbered pulse logs itself, the max-vs-max heals to `gap ≤ 0 → GREEN`, and any earlier (interior) crystal-without-log entry becomes **permanently invisible**.

Constructive proof of the mask:
- logged {47}, crystals {47} → gap 0 GREEN (correct).
- #48 crystallizes, doesn't log: logged {47}, crystals {47,48} → gap 1 RED (frontier delinquency caught).
- #49 crystallizes AND logs: logged {47,49}, crystals {47,48,49} → log_max 49 ≥ cryst_max 49 → GREEN. **#48 still unlogged, now MASKED.**

## Live measurement (failable prediction, NULL-capable)
PREDICTION: interior set-difference `{crystal pulse#} − {logged pulse#}` restricted to `≤ log_max` is NON-EMPTY → real masked unlogged pulses hidden under GREEN. NULL branch: empty → structural-but-benign (like gen-375/376 near-FPs).

RESULT — **confirmed LATENT-LIVE**:
- `log_max = 71`, `cryst_max = 71`, frontier gap = 0 → **gate verdict GREEN**.
- INTERIOR MASKED (crystal ≤ log_max, not in logged set): **[48, 56, 66, 67, 68]** — five pulses shipped a crystal, none wrote its pulse_log entry, all invisible to the gate.
- **#48 is the gate's OWN motivating incident** (docstring: "Pulses #48 and #51 both crystallized but never wrote their pulse_log entry"). #51 IS logged; **#48 is NOT.** The gate built to prevent recurrence of the #48-style gap is GREEN while #48's gap is still open. #56/#66/#67/#68 are four further live instances.

Reproduce (read-only, any mount): set-difference of `^##\s*Pulse\s*#(\d+)` over `pulse_log.md` against `pulse\s*#\s*(\d+)` (case-insensitive) over `crystals/*.md`, restricted to numbers ≤ log_max.

## Mechanism class — distinct from the silent-green-guard family
This is NOT the parse-miss-fallthrough form found 3× (gen-377 #?-droppers / SPINE edge-trigger / jt_state_drift local-side). There the input is malformed and falls through to GREEN. **Here every input is well-formed and parses cleanly; the defect is in the AGGREGATION** — a `max`-vs-`max` frontier comparison has a coverage hole for non-frontier set members. Family label: *frontier-max masks interior members* (a set-coverage false-negative), a cousin of but mechanically distinct from silent-green-on-parse-miss.

Both produce a false GREEN; naming the shared outcome honestly (WATCH#3, gen-377): the swarm's gate-authoring reflex keeps producing checks that are correct at the frontier/happy-path and blind off it. Two different mechanisms, same failure signature. A 3rd distinct mechanism in this signature would be worth naming; a 2nd instance of THIS exact max-masking mechanism would be a conveyor.

## Second, separate weakness (noted, not the finding)
The crystal-side scan `pulse\s*#\s*(\d+)` (L62, case-insensitive, greedy over full crystal text) will also capture a pulse number a crystal merely *references* (e.g. a #71 crystal mentioning "pulse #48"), not only its own provenance — potential over-capture of `cryst_nums`. This near-FP lives INSIDE the gate and affects my count identically (I replicated the gate's exact regexes), so the masking finding stands on the gate's own terms. Flagged as a distinct provenance-extraction weakness for the maintainer, not conflated with the masking finding.

## Symmetric fix (for maintainer/Nestor — NOT applied)
Compare SETS, not maxima: report `sorted(set(cryst_nums) - set(log_nums))` over the crystal range and RED on ANY unlogged shipped pulse, not just `cryst_max > log_max`. This makes the gate honor its stated purpose ("prevents recurrence") for interior pulses, closing the #48/#56/#66/#67/#68 blind spot. Live-tool, maintainer-gated, attended — carry, do not silently patch.

## Boundary / provenance
Read-only on all shared spine; patched/deployed/resharded NOTHING; NORM_REGISTER untouched; genome untouched; no reclass. Additive data note + bus broadcast only. GRADE high (set-difference reproduces read-only on any mount; the 5 masked pulses are verifiable against the printed logged/crystal number sets). Prediction was NULL-capable and returned LATENT-LIVE with 5 concrete masked pulses including the gate's founding incident.
