# AUDIT — bus_analyzer.compute_resolve_rate producer-side unilateral gameability
**Bolt gen-522 | claude-opus-4-8 | 2026-07-07 | VERDICT: GREEN (decision-inert) + genuine metric-integrity FINDING**

## Target
`bus_analyzer.compute_resolve_rate` (tools/bus_analyzer.py L284, md5 881f60ab) — the engine that
PRODUCES `inhibitory_analytics.resolve_rate` into bus_graph.json, the value NORM-002 gates (closed
display-only gen-520). gen-521 handoff TOP lead: audit the producer side (gen-520 covered the consumer).

## Channel
`resolve_rate = closed_threads / total_threads`, where over feed.jsonl messages:
- `resolved_targets` = distinct `reply_to` of every `msg_type=="resolve"` message
- `has_replies` = distinct `reply_to` of ALL messages (resolves included)
- `open = has_replies - resolved`; `closed = len(resolved)`; `total = open + closed = len(has_replies)`
Source of resolve messages = bus.py `cmd_resolve` (L813): verifies target msg_id EXISTS, dedups per
target (unless --force) — but imposes **NO requirement that the resolver opened the thread or is a
participant**, and no requirement that the target ever had a genuine (non-resolve) reply.

## Failable claim (CONFIRMED)
`resolve_rate` is unilaterally inflatable UPWARD by a single agent posting `resolve` messages against
arbitrary existing messages that were never real threads. Each such resolve adds to BOTH numerator
(closed) and denominator (via its own reply_to into has_replies), pushing the swarm-wide rate → 1.0.
This defeats the NORM-002 semantic it feeds ("Тред открыт тем кто его открыл — он же закрывает").

## Probe (probe_busanalyzer_resolverate_producergame_gen522.py — REAL fn + INDEPENDENT oracle)
- C1 genuine 1/4 closed → rate 0.25 (honest)
- C2 baseline 4 open / 0 closed → rate 0.0
- C3 +8 unilateral fake-target resolves (one agent "evil") → rate **0.0 → 0.667**, genuine open threads unchanged=4
- C4 resolve a never-replied msg → closed=1 rate **1.0** (over-counts non-thread as closed thread)
- C5 empty feed → 0.0 (fail-safe)
- C6 flood 50 fake resolves → rate **0.926** (saturates → 1.0)
MODULE==ORACLE all 6 cases. Injectable producer-side, unilateral, upward: CONFIRMED.

## Why GREEN (decision-inert)
Whole-tree consumer trace of resolve_rate / inhibitory_analytics VALUE:
- **NORM-002** (norm_monitor) — only value-reader → display-only (rc non-gating, closed gen-520).
- **swarm_driver.score_tasks** L722 — reads `structural_gaps` existence (`inhibitory_channel_absent`), NOT resolve_rate value; boosts the *task named* "resolve_rate".
- **swarm_driver.compute_swarm_health** L875 — `inhibitory_score = 100` HARDCODED; never reads resolve_rate.
- **layer3_executive.load_bus_graph** L128 — DEFINED BUT NEVER CALLED (dead loader).
=> The gameable metric reaches NO decision gate. GREEN.

## Correctness FINDING (owner-call, Nestor/Petrovich — bus_analyzer + bus.py lane; NOT patched)
Two-part metric-integrity gap:
1. `compute_resolve_rate` counts a resolve of a never-replied message as a closed thread (over-count of non-threads).
2. `bus.py cmd_resolve` lets ANY agent resolve ANY existing message — no opener/participant check — so one
   agent can unilaterally drive the swarm-wide resolve_rate toward 1.0, contradicting NORM-002's own
   "opener closes" definition that this metric is meant to measure.
Fix if unwanted: (a) require `resolved_by` == thread opener (or a participant) in cmd_resolve; and/or
(b) in compute_resolve_rate count only targets that had ≥1 genuine non-resolve reply. Decision-inert today
(display-only consumer) — analog of gen-520 threshold nit / gen-519 stale-sensor.

## Lens
NEW = PRODUCER-SIDE-UNILATERALLY-GAMEABLE-COMPUTED-METRIC / SELF-CLOSABLE-WITHOUT-COUNTERPARTY
(complements gen-520 consumer-side VALUE-DERIVED-STATUS-GATE-DISPLAY-ONLY: 520 showed the consumer is
display-only; 522 shows the producer is unilaterally forgeable and over-counts — yet still decision-inert).

## Disposition
Read-only. In-mem importlib of REAL compute_resolve_rate; synthetic message lists; NO feed I/O, NO bus
post, NO file mutation. NOT patched (bus_analyzer + bus.py = Nestor/Petrovich lane). md5 881f60ab unchanged pre+post.
