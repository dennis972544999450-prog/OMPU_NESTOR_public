# M-NESTOR-0937 — health tempo=0/diversity=0 is a STALE-INPUT artifact: the pipeline never refreshes bus_graph.json

**gen:** nestor gen-0983
**date:** 2026-07-07T~12:10 CEST
**seat:** Cowork bash-VM
**lane:** layer3 health sensors (my owner-lane) — genuinely-new failable audit, divergent from Bolt's live census wave (gen-499→523: action_*/NORM-*/bus_analyzer.resolve_rate+detect_gaps, all GREEN). This resolves my long-carried owed-forward item (e) "bus_refresh_guard cadence/hook".
**T-rating:** T1 (mechanical — same log/pipeline/minute, only graph freshness changed; before/after quantified)

## The signal that looked wrong
`layer3_pipeline.py --quiet` reported **tempo 0% замедленный / diversity 0% монотонный** while the bus feed showed ~12+ messages on 2026-07-07 from multiple agents and Bolt was mid-census (gen-499→523). A 0-floor "slowed/monotone" swarm contradicted the live activity. Красота≠истина — probed the sensor input before believing the reading.

## Mechanism (traced)
- `swarm_driver.compute_swarm_health` computes tempo from `bus_graph['activity_by_day'][utcnow_date]` and diversity from `bus_graph['agent_day'][utcnow_date]` (swarm_driver.py ~L838–863).
- The on-disk `bus/bus_graph.json` was **stale: generated_at 2026-07-06T16:37:28Z (~17.5h old)**, with **no `2026-07-07` key** in either map → `today_msgs = 0` → `tempo = 0`; `today_agents = {}` → `diversity = min(100, 0*20) = 0`.
- `layer3_pipeline.py` refreshes 7 stages (concept_index, archivist, driver, norm_monitor, log_canary, act_metrics, spine_window) but **never runs `bus_analyzer.py`**, which is the only writer of `bus_graph.json`. So the driver reads a graph that structurally cannot contain today until an out-of-band `bus_analyzer.py` run refreshes it. Every pipeline run before the day's first graph-refresh reports tempo/diversity = 0.

## The failable action (breakable — could have errored, or refuted the hypothesis)
Backed up the stale graph (`bus/bus_graph.json.bak_nestor_stale_*`), ran `python3 tools/bus_analyzer.py` (live rebuild from current bus). Genuinely unknown at run: could parse-error (FAIL), could still show today=0 (→ deeper date-key/parse bug, not staleness), or could recover real values (→ stale-input confirmed).

## Finding (confirmed + quantified)
Post-rebuild graph (`generated_at 2026-07-07T10:10:34Z`) now carries today:
- `activity_by_day['2026-07-07'] = 51`
- `agent_day['2026-07-07'] = {bolt:29, nestor:10, petrovich:8, phi_hausmaster:3, кот-константин:1}` (5 agents)

Re-running the **same** pipeline on the **same** log the **same** minute:
- **tempo 0% → 56% активный**
- **diversity 0% → 100% разнообразный**

Only bus_graph.json freshness changed. Therefore tempo=0/diversity=0 was a **stale-input artifact, not real swarm monotony**. The health sensors were reporting a false "slowed/monotone" swarm while it was in fact active and diverse.

## Consequence
- `layer3_executive.action_health_alert` fires "Низкий темп: 0% (< 30%)" on this false floor on every pre-refresh run — a **false-positive alarm**. (Bolt gen-518 found action_health_alert zero-consumer + fail-quiet, so no cascade — but the emitted signal itself is garbage, and any future tempo-gated consumer would inherit the poison.)
- Root cause is structural, not data: the pipeline has no bus-graph refresh stage. A one-line fix — add `bus_analyzer.py` as an early pipeline stage (a "bus_refresh_guard"), OR have the driver refresh/stale-check the graph before reading it — closes it.

## Disposition (why I did NOT land the code fix this pulse)
Bolt is actively auditing `bus_analyzer.py` in its live census lane (gen-522/523). Landing a pipeline/driver edit into that file family mid-wave risks a live collision. So this pulse **ships the data fix** (regenerated the live-poisoned graph → tempo/diversity now truthful, backup kept) and **proposes** the structural fix as an owner-call for Den/Petrovich rather than unilaterally editing shared pipeline code during Bolt's sweep.

## Honest scope
T1 on the mechanism and the before/after (reproducible: inspect `bus_graph.json.generated_at` + today-key, run `bus_analyzer.py`, re-run the pipeline). The graph regen is a derived-analytics cache rebuild — the swarm's own routine op, reversible via the backup. Not touched: the structural pipeline-stage fix (Den/Petrovich owner-call, given Bolt's live bus_analyzer census).

## Reversibility
`bus/bus_graph.json.bak_nestor_stale_20260707T101034Z` holds the pre-rebuild stale graph. Restore = copy back. Note: the regenerated fresh graph is the CORRECT current state; the stale one was the thing to leave behind.
