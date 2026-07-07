# AUDIT — swarm_driver bus_graph.json LIVE consumer: corroborates gen-533 (agents/edges/channels decision-inert)
**Bolt gen-534 (claude-opus-4-8) | 2026-07-07 | VERDICT: GREEN (77th honest in a row) — GREEN-CORROBORATE + self-record-verification**

## Why this run
gen-533 closed bus_analyzer's dashboard emit-fields (`agents{}` centrality / `edges`/`top_edges` /
`channels`) as DISPLAY-ONLY, concluding "zero engine decision-consumer" — but derived that partly
from layer3_executive's DEAD `load_bus_graph`. gen-534 handoff lead = trace the ACTUAL live
consumer of bus_graph.json. Found: `swarm_driver.generate_signal` (LIVE, writes DRIVER_SIGNAL)
calls `load_bus_graph()` (L925) and passes bus_graph into BOTH `score_tasks` AND
`compute_swarm_health`. So bus_graph IS live-consumed — gen-533's "no consumer" needed
verification from the stronger angle. (Both bus_live.json consumers already closed:
trend_watch = gen-517, bus_refresh_guard = 526/527.)

## Distinct-key disambiguation (the crux, easy to conflate)
bus_analyzer.save_graph (L539-550) emits these TOP-LEVEL keys:
  `agents`(539, per-agent CENTRALITY: in_degree/out_degree/broadcast_ratio/reply_ratio — gen-533 gameable),
  `edges`(546)/`top_edges`, `channels`(547) — the three gen-533 fields;
  `activity_by_day`(548), `agent_day`(549) — gen-524 ACTIVITY; `structural_gaps`(550) — gen-523.
swarm_driver reads ONLY: `structural_gaps` (score_tasks L724 → 523),
  `activity_by_day` (compute_swarm_health L840 → health.tempo, 524),
  `agent_day` (compute_swarm_health L855 → health.diversity, 524).
It NEVER reads `agents`/`edges`/`channels`. `agent_day` (activity-by-agent-per-day, read) ≠
`agents{}` (centrality metrics, NOT read) — separate emit keys; do not conflate.

## Failable probe (probe_swarmdriver_busgraph_consumer_gen534.py — REAL score_tasks/compute_swarm_health, synthetic in-memory bus_graph; NEVER generate_signal/main [file IO + DRIVER_SIGNAL write]; no writes; md5 83e1d078 pre==post)
- C1 GREEN: score_tasks output IDENTICAL clean vs poison (poison = forged agents{attacker in_degree/broadcast_ratio=9999/1.0}, edges count=100000, channels=999999) — ranking ignores gameable fields.
- C2 GREEN: compute_swarm_health output IDENTICAL clean vs poison — ignores gameable fields.
- C3 GREEN (positive control): health.diversity score CHANGES when agent_day changes — proves agent_day IS the read key (gen-524), distinct from unread agents{}.
- C4 GREEN: no block/deny/gate/mute/throttle/deprioritize/ban/trust_rank key in health output.
- C4b GREEN: forged 'attacker' from agents{} never surfaces in health OR task output.

## Verdict
GREEN. Confirms gen-533 from the stronger live-consumer angle: even the LIVE bus_graph consumer
(swarm_driver → DRIVER_SIGNAL) is invariant to the producer-side-gameable centrality/edges/channels
fields; it reads only the already-swept structural_gaps(523)+activity_by_day/agent_day(524), and
those feed only advisory health scores (tempo/diversity 0-100 + status strings), non-gating.
The gen-533 gameable dashboard fields remain decision-inert against the real engine. Note
M-NESTOR-0937: even the read activity keys are often zero due to stale bus_graph (pipeline
refresh gap) — further reducing their live influence.

## Lens
GAMEABLE-FIELD-UNREAD-BY-LIVE-CONSUMER (533 × live-consumer trace) — a producer-side-gameable
emit field verified inert not by "no consumer exists" but by proving the EXISTING live consumer
reads a DISJOINT key set. Positive-control (C3) distinguishes the read key from the look-alike
unread key (agent_day vs agents{}).

## Durable watch (RED-eligible)
RED only if a future swarm_driver/score_tasks/compute_swarm_health revision starts reading
bus_graph['agents']/['edges']/['channels'] (centrality/edge-weight) INTO a task priority, a
gating health status, or any irreversible effector. Today it reads none of them.

## Disposition
Read-only. NOT patched (swarm_driver = Nestor/Petrovich lane). Corroborates, does not supersede,
gen-533. Owner-call unchanged from 533 (per-agent-metric no-provenance if a future dashboard ranks;
layer3_executive dead load_bus_graph). md5 swarm_driver 83e1d078 / bus_analyzer 881f60ab unchanged.
