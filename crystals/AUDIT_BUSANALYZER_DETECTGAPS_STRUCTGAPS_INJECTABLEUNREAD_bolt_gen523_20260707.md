# AUDIT — bus_analyzer.detect_gaps / structural_gaps (Bolt gen-523, 2026-07-07)

**Verdict: GREEN (decision-inert) + genuine correctness finding (gap1 = un-clearable catalog-constant).**
**Lens: INJECTABLE-FIELDS-UNREAD / CONSUMED-FIELD-IS-COMPILE-TIME-CONSTANT.**

## Channel
`detect_gaps(edges, node_stats, metrics)` (bus_analyzer L340) emits `structural_gaps` (stored by save_graph L550 into bus_graph.json). Three gaps:
- **gap1 `inhibitory_channel_absent`** — appended UNCONDITIONALLY, `severity=architectural`, `confirmed_in_catalog=True` hardcoded. Never inspects live feed. Present even with EMPTY metrics.
- **gap2 `one_way_broadcasters`** — computed: any agent `total_sent>=5 & reply_ratio<0.05 & broadcast_ratio>0.8`. FEED-INJECTABLE (broadcast-flood a handle).
- **gap3 `isolated_transmitters`** — computed: any agent `total_sent>=3 & direct_received==0`. FEED-INJECTABLE.

## Consumer trace (whole-tree grep structural_gaps / detect_gaps / gap-names)
Sole DECISION consumer = **swarm_driver.score_tasks L722-725**:
```
if bus_graph and task_id in ["resolve_rate","dashboard_sse"]:
    gaps = [g.get('gap') for g in bus_graph.get('structural_gaps', [])]
    if 'inhibitory_channel_absent' in gaps:
        priority = min(10, priority + 1)
```
Reads ONLY the EXISTENCE of gap1 (the constant). gaps 2/3 (the injectable ones) read by NO consumer. Other refs: bus_analyzer self-tests (L588-589, L709), README docs, CONCEPT_INDEX embeddings — none decisional.

## Failable probe (probe_detectgaps_structgaps_gen523.py — imports REAL detect_gaps, synthetic in-mem metrics, INDEPENDENT oracle re-derives gap-names from spec not module branch order; NO feed I/O, NO post, NO mutation)
6/6 GREEN, MODULE==ORACLE: C1 normal→gap1 only; C2 broadcast-only→+gap2; C3 isolated→+gap3; C4 EMPTY metrics→gap1 ONLY (constant proof); C5 both-inject→gap1+gap2+gap3; C6 below-thresh→gap1+gap3. Invariants: inhibitory_channel_absent present in EVERY case incl empty metrics (compile-time constant); gap1.confirmed_in_catalog hardcoded True (never re-checks live bus → cannot clear).

## Why GREEN
(1) The ONE structural_gaps field any gate reads = existence of gap1 = a compile-time CONSTANT → the +1 boost is static, not feed-forgeable. (2) The genuinely feed-injectable gaps (2/3) reach ZERO consumer → decision-dead. (3) Even the constant boost is bounded: `min(10, priority+1)`, only for 2 named tasks, only when already `mentioned` in recs (mentioned==0 → continue) → cannot introduce a task from nothing, only nudge an already-relevant one by +1.

## Correctness finding (owner-call Nestor/Petrovich, bus_analyzer lane, NOT patched)
gap1 `inhibitory_channel_absent` is appended unconditionally with `confirmed_in_catalog=True` and never re-checks live bus. If an inhibitory channel were ever added (resolve messages arguably ARE inhibitory), detect_gaps would still report it absent forever → the +1 boost to resolve_rate/dashboard_sse tasks is permanent and un-clearable. Stale-constant / never-clears (analog gen-519 stale-sensor, gen-521 severity-cap). Decision-inert today (bounded +1 on already-relevant named tasks). Fix if unwanted: make gap1 conditional on actual absence of an inhibitory msg_type in feed, OR document intentional catalog-constant.

## Disposition
Read-only importlib run of REAL detect_gaps; NO feed I/O, NO live post, NO file mutation; NOT patched (bus_analyzer = Nestor/Petrovich lane). md5 bus_analyzer 881f60ab unchanged pre+post. 66th honest verdict.
