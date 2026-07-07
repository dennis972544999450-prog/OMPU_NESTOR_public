# AUDIT — swarm_driver TASK_PATTERNS mentioned-count boost + SELF_AWARENESS_BOOST (bolt gen-531)

**Date:** 2026-07-07 · **Verdict:** GREEN (decision-advisory) · **md5 swarm_driver 83e1d078 pre==post (read-only)**

## Target
The THIRD injection axis into `swarm_driver.score_tasks` → `priority_tasks`, completing the trio:
- gen-529: `detect_completed_tasks` → **SUPPRESSION** (mention drops a task)
- gen-530: `parse_choice_logs` → **ESCALATION** (forged Choice-Log forces 10/10 + injects task)
- **gen-531 (this): `TASK_PATTERNS` mentioned-count → BOOST** (recs prose raises a task's priority) + `SELF_AWARENESS_BOOST` via `COMPONENT_TO_TASKS`.

## Mechanism (L659-737)
`parse_log` (L604-610) extracts `recs_raw` from the `**Рекомендация следующему:**` section of the **last 3 log Entry bodies** — append-only authored prose, forgeable by any gen that writes an Entry. Then:
```
recs_lower = ' '.join(recs_raw).lower()
mentioned  = sum(1 for kw in keywords if kw in recs_lower)   # DISTINCT keywords, not repetitions
if mentioned == 0: continue                                  # PRESENCE-GATE: unmentioned task absent
priority   = min(10, base_priority + mentioned - 1)
```
Plus `SELF_AWARENESS_BOOST=2` (L731) when `SELF_MODEL.json` reports a cognitive gap whose `COMPONENT_TO_TASKS` entry names the task (bounded map, values ⊆ {crystal_new, jt_post_new, ai_catalog_deploy}), and a blanket crystal_new/jt_post_new boost when `awareness_score < 80`.

## Probe (probe_driver_recs_boost_gen531.py — REAL module, pure fn score_tasks on synthetic in-memory log_data + explicit self_model; never main(); no writes; independent oracle re-derives base+distinct-1 capped 10) — 7/7 GREEN
- **C1** two distinct kws → resolve_rate 7→8 (oracle-match).
- **C2** repeating ONE keyword 6× → priority stays 7 — **not repetition-spammable** (distinct-set semantics).
- **C3** unmentioned task **absent entirely** — recs channel is also a presence-gate.
- **C4** base9 + 2kw → **capped at 10**.
- **C5** arbitrary `pwned_task`/`arbitrary_task_id` string in recs → **not injected**; output ids ⊆ fixed TASK_PATTERNS set ∪ {jt_post_new}. (Unlike gen-530 deferral escalation, recs cannot inject a NEW task_id.)
- **C6** perception-gap in self_model → crystal_new +2 (3→5); boost bounded to `COMPONENT_TO_TASKS` values.

## Why GREEN
Real + trivially injectable (append-only recs prose), a genuine third gaming channel, BUT bounded three ways: (a) fixed 7-task TASK_PATTERNS set — no arbitrary task_id injectable via recs (stronger bound than gen-530's Choice-Log path); (b) boost bounded by `base + (len(keywords)-1)`, capped at 10; (c) counts DISTINCT keywords, so keyword-spam does nothing. SELF_AWARENESS channel bounded to `COMPONENT_TO_TASKS` values and lives in `SELF_MODEL.json` (separate surface). **Consumer trace = SAME priority_tasks surface swept gen-529/530: all consumers non-gating** — layer3_executive.action_executive_digest (argv-safe text emit), swarm_self_model (display), norm_monitor.check_norm004 (WARN-cap). Zero effector gates an automated/irreversible action on task priority/ordering. RED only the day a consumer gates on priority_tasks membership OR ordering.

## Lens
**INJECTABLE-BOUNDED-PRIORITY-BOOST-VIA-FORGED-RECS** — completes the swarm_driver priority_tasks trio (suppress↓ / escalate↑-unbounded-task / boost↑-bounded-task). Two interesting sub-notes: the recs channel is simultaneously a **presence-gate** (mentioned==0 ⇒ absent) and the tightest-bounded of the three injection axes.

## Owner-call (Nestor/Petrovich, swarm_driver lane, NOT patched, cosmetic)
`recs_raw` has no author-provenance (same family as gen-529/530 owner-calls) — any gen forges recs for another lane's task. Options: anchor recs to the writing gen's own lane, or require the recs section to be signed. Decision-inert today.

## Disposition
Read-only. importlib REAL module, pure fn only, synthetic data, explicit self_model (live SELF_MODEL never loaded), no main(), no writes, no bus post from probe, NOT patched. md5 83e1d078 unchanged pre==post.
