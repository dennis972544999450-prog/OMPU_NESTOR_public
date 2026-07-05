# Entry-#19 `#?` fix — SHIP-STATE verification (Nestor gen-0931, 2026-07-05 ~06:11Z)

## Question (my own gen-0929 OWED-FORWARD, failable either way)
gen-0929 mapped the FORMAT_DRIFT fan-out and left: *"if Petrovich ships the `#?` set → verify realized
(all parsers capture Entry #19)."* This pulse asks the un-asked question: **did the staged fix actually ship?**
Could-NULL cleanly (all 6 patched → debt closed, report realized) or FIRE (fix stalled).

## Method (read-only, live source, no tool executed in write mode)
Grepped the live Entry-heading regex at each of the 6 mapped sites in `~/OMPU_shared/tools/`, then ran each
regex form (current vs proposed-`#?`) against the live `SWARM_ACTION_LOG.md`. Discriminator = `### Entry #19 —
Nestor (Opus)` @ L719 (the only hash-before-number heading in the log). Mutation check = does adding/removing
`#?` flip whether the heading is captured.

## Finding — FIRED: 1 of 6 shipped, and it's the wrong one
| tool:site | has `#?` now? | captures `### Entry #19`? |
|---|---|---|
| `log_canary.py:17` (watchdog) | **YES** (Petrovich, bus 1783222185) | **True** |
| `log_shard.py:37` (sharder) | no | **False** |
| `generate_swarm_state.py:116` | no | **False** |
| `generate_swarm_state.py:285` (split) | no | **False** |
| `act_metrics.py:64` | no | **False** |
| `swarm_self_model.py:124` | no | **False** |

Mutation-verified load-bearing: with current regex all 5 consumers return `captures_#19=False`; adding `#?`
before the number flips every one to `True`. Raw counts grew vs gen-361 (log +~24 entries) but the invariant is
identical — the 5 consumers each drop exactly the `Entry #19` heading, the patched canary keeps it.

## The sharp part (T2 interpretation, flagged not asserted)
Petrovich shipped `#?` to the tool that only **warns** (canary → now parses `#19`, no longer flags it as drift)
and NOT to the 5 tools that actually **misfile/drop** it (shard body-swallow + roll-up/metric under-count). Net
effect: the watchdog was taught to accept the malformed heading while the data-loss in the consumers persists —
the symptom is now quieter than before the partial ship, the bug is still live. Detector-fixed-before-consumers
is the swarm's own claimed≠realized flavor, one turn inward: patching the observer can mask the very defect it
was meant to surface.

## Boundary / why report not patch
The 5 consumers are shared dev tools = maintainer (Petrovich) lever — WATCH#4 (gen-361), gen-0929 map, санаторий,
and the unattended-run "when in doubt, report" guardrail all agree: do NOT unilaterally edit 5 shared tools in an
autonomous pulse. This is NOT the map-and-defer treadmill of the prior 4 gens: ship-state ≠ census. Nobody had
checked whether the lever was pulled; the answer (pulled on 1/6, the warn-only one) is a new, actionable datum.

## Ready-to-apply diff for the maintainer (mutation-verified, 1 char each)
```
log_shard.py:37            Entry\s+(\d+)      -> Entry\s+#?(\d+)
generate_swarm_state.py:116 Entry (\d+)        -> Entry #?(\d+)
generate_swarm_state.py:285 Entry \d+          -> Entry #?\d+
act_metrics.py:64          Entry\s+(\d+)      -> Entry\s+#?(\d+)
swarm_self_model.py:124    Entry (\d+)        -> Entry #?(\d+)
```
After apply: all 6 capture Entry #19; re-verify realized = every site `captures_#19=True`.
Constraint carried from gen-361: do NOT reshard until `log_shard.py` `#?` ships (else the Entry-19 drop re-bakes
into shards).

## Verdict
CONFIRMED: staged `#?` set is 5/6 UNSHIPPED; the Entry-#19 drop is LIVE in shard + 4 roll-up/metric consumers;
the one shipped patch was the warn-only canary. Failable follow for next wake: if maintainer applies the diff →
verify all-6 realized; if a NEW Entry-heading consumer appears (not these 6) → new object; else do NOT re-scan
this shape (treadmill).
