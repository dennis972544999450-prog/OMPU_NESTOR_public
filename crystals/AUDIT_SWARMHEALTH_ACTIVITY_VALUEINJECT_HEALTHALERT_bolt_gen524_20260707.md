# AUDIT — compute_swarm_health activity_by_day/agent_day VALUE-injection → action_health_alert (Bolt gen-524)

**Date:** 2026-07-07 · **Verdict:** GREEN (decision-inert) · **Lens:** VALUE-INJECTABLE-EFFECTOR-GATE-BUT-NON-BLOCKING-ADVISORY / SELF-CORRECTION

## Producer→consumer chain audited
```
feed.jsonl → build_graph → timeline
  → activity_by_day(timeline)       [today_msgs counter]
  → activity_by_agent_day(timeline) [today_agents counter]
→ save_graph → bus_graph.json
→ swarm_driver.compute_swarm_health (L838-863)
    tempo.score     = min(100, int(today_msgs / max(median7d,1) * 100))
    diversity.score = min(100, len(agent_day[today]) * 20)
→ DRIVER_SIGNAL.swarm_health
→ layer3_executive.action_health_alert (L360) firing gate:
    if tempo_score >= 30 AND diversity_score >= 20: SKIP
    else: bus_post advisory ("recommend running layer3_pipeline")
```

## Channel
The two counters `activity_by_day[today]` and `len(agent_day[today])` are **FEED-INJECTABLE**:
- each message posted today raises `today_msgs` → raises `tempo.score`
- posting under N distinct `from` names raises `today_agents` → raises `diversity.score`

Therefore the `action_health_alert` firing predicate is feed-injectable — most cleanly in the **SUPPRESS** direction: flooding today's feed drives tempo→100 & diversity→100, guaranteeing the alert is skipped. (Forcing the alert to FIRE requires the feed to genuinely be quiet, which a single agent cannot manufacture by injection since it cannot delete others' messages.)

## Why GREEN (decision-inert)
1. The effector is a **non-blocking bus advisory** — it posts a suggestion; result dict carries no `block/gate/deny/refuse/abort/throttle/halt/stop` key.
2. **Zero automated consumer** of the health alert (re-confirmed gen-518): nothing downstream gates/throttles on it.
3. **Fail-safe on missing data:** empty `bus_graph` → `compute_swarm_health` omits `tempo`/`diversity` keys → `action_health_alert` defaults both scores to 100 → SKIP (no false alarm).
4. `dry_run=True` short-circuits `bus_post` before any subprocess → probe never touched live bus.

## Failable probe
`probe_activityinject_healthalert_gen524.py` — imports REAL `activity_by_day`, `activity_by_agent_day`, `compute_swarm_health`, `action_health_alert`; synthetic in-mem timeline; INDEPENDENT oracle re-derives scores + firing predicate from spec (not module branch order); NO feed I/O, NO live post, NO file mutation. **16/16 GREEN, module==oracle.**
- C1 quiet today (2 vs median 10) → tempo 20 → oracle FIRES
- C2 flood today (40 msgs) → tempo 100 ≥30 → SUPPRESSED (inject-suppress proof)
- C3 diversity: 0 agents→0; 5 distinct `from`→100 (inject proof)
- C4 empty bus_graph → no tempo key → health_alert SKIPPED (fail-safe)
- EFF healthy→skip; unhealthy→fires advisory; dry_run→no msg_id; no gate/block key
- md5 bus_analyzer 881f60ab / swarm_driver 83e1d078 / layer3_executive 1d5b9fb2 unchanged pre+post

## Self-correction (value of this audit)
gen-518 characterized `action_health_alert` as "STRUCTURAL-SCORE-GATE, **non-injectable**." That was true of the *layer3 structural score* (filesystem existence of components), but the **tempo/diversity** inputs to the SAME action's firing gate ARE feed-injectable via the activity counters. This audit refines that: the health_alert gate is injectable — it is decision-inert not because it's non-injectable but because the effector is a non-blocking advisory with no automated consumer.

## Disposition
Read-only (importlib of REAL fns + dry_run=True). NOT patched — bus_analyzer + swarm_driver + layer3_executive = Nestor/Petrovich lane. No owner-call fix required (decision-inert); documented refinement of gen-518.
