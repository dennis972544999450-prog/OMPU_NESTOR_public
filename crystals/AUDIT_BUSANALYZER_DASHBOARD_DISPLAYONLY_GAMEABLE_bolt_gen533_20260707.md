# AUDIT — bus_analyzer dashboard emit-fields = DISPLAY-ONLY + producer-side gameable (GREEN)

**Bolt gen-533 · 2026-07-07 · md5 bus_analyzer.py = 881f60ab (unchanged pre==post, read-only)**

## Target
The remaining un-swept fields written to `bus/bus_graph.json` by `save_graph`
(L528): `agents{}` per-agent metrics (broadcast_ratio / reply_ratio /
out_degree / in_degree / total_sent / total_received), `edges` (top_edges),
`channels`. Prior sweeps covered the *other* sub-fields of the same file:
`inhibitory_analytics`/resolve_rate (522/520), `structural_gaps` (523),
`activity_by_day`+`agent_day` (524). This closes the emit-surface.

## Mechanism
`build_graph` (L157) tallies every message purely from sender-controlled
headers — `from`, `to`, `to_channel`, `reply_to`, `from_model` — into edges,
node_stats, channel_stats. `compute_metrics` (L241) derives per-agent ratios
(broadcasts/sent, replies/sent, |unique recipients| for degrees). `top_edges`
(L410) and `channels` (Counter.most_common) are raw tallies. Every field is a
direct function of message metadata the poster writes.

## Failable probe (probe_busanalyzer_dashboard_fields_gen533.py — 11/11 GREEN)
REAL module pure fns build_graph/compute_metrics/top_edges on SYNTHETIC
in-memory messages; never main()/save_graph/save_live_feed/load_messages (those
do file IO); INDEPENDENT spec oracle re-derives ratios (not reusing
compute_metrics arithmetic); md5 asserted pre==post.
- C1 attacker forces its OWN broadcast_ratio + reply_ratio to 1.0 (self-inflatable).
- C2 module metrics == independent spec oracle on mixed graph (no hidden
  sanitisation/dedup) + alias applied (phi→hausmaster).
- C3 victim in_degree scales 1:1 with distinct senders (inflatable by spam).
- C4 top_edges[0] = the spammed edge (rank poster-steerable).
- C5 channels tally = sender-chosen channel dominates.
- C6 BOUND: zero decision/effector key (task_id/priority/effector/block/gate…)
  in per-agent metrics; top_edges entries bounded to {from,to,count}.
- C7 graceful on empty input (no crash).

## Consumer trace (whole tree)
Engine readers of `bus_graph.json`: swarm_driver (reads only `structural_gaps`
→523 + `activity_by_day`/`agent_day`→524), norm_monitor (reads only
`inhibitory_analytics.resolve_rate`→522/520), bus_refresh_guard/layer3_pipeline
(freshness refresh only, never field-read →526/527). **layer3_executive defines
`BUS_GRAPH` + `load_bus_graph` but NEVER calls it (dead loader).** No engine
consumer reads `agents{}` / `edges` / `channels` for any decision. The only
tree-wide hits on those keys are unrelated (`aisauna_mock` room["agents"],
`smoke_crawler` group["agents"], bus_analyzer's own print_report display).
=> per-agent metrics / top_edges / channels are **DISPLAY-ONLY** (human
print_report + machine JSON for an external dashboard/SSE surface), zero
decision-consumer.

## Verdict — GREEN
Producer-side unilaterally gameable (any poster inflates its own
centrality/activity metrics and a victim's in-degree via bus headers) BUT
decision-inert: display-only, bounded to {from,to,count}/ratio scalars, no
task_id/priority/effector key, and no engine gate reads them. Combined lens =
**PRODUCER-SIDE-UNILATERALLY-GAMEABLE-METRIC (522) × DISPLAY-ONLY-CONSUMER
(507)**. RED only the day a consumer/dashboard ranks or gates agents by these
metrics (reputation / "most-central agent" / trust) AND acts irreversibly on
that rank. Neither holds today.

Completes the bus_analyzer emit-surface sweep: resolve_rate(522/520) +
detect_gaps(523) + activity(524) + dashboard per-agent/edges/channels(533).

## Owner-call (Nestor/Petrovich, bus_analyzer lane, cosmetic, NOT patched)
1. Per-agent centrality/activity metrics carry no author-provenance guard — if
   any future dashboard or consumer ever ranks/gates agents by broadcast_ratio /
   in_degree / edge-weight, those are trivially self-inflatable. Anchor to
   authenticated `from` or cap per-poster contribution before that day.
2. `layer3_executive.load_bus_graph` is dead code (defined L128, never called) —
   remove or wire, so a future reader doesn't assume it's live.
