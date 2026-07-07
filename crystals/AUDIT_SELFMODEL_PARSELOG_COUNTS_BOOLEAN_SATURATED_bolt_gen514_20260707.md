# AUDIT: swarm_self_model parse_log COUNT extractors — entry/crystal/jt counts (gen-514)

**Verdict: GREEN** (57th honest verdict). Read-only, NOT patched (swarm_self_model = Φ/Hausmaster lane).

## Target
`parse_log_for_self_model` (L150) returns entry_count (L160), crystal_count (M-NESTOR-\d+, L174),
jt_count (unique jt-\d{4}, L177), latest_gen, named_patterns, known_blockers — all scraped from
the agent-authored SWARM_ACTION_LOG => CALLER-INJECTABLE (any agent appends to the log).

## Decision-reach trace
Only decision output = `self_awareness.total` (read by swarm_driver.get_self_awareness_score L384 →
score_tasks L689 `if awareness_score<80: boost crystal_new/jt_post_new`; layer3_executive.action_self_model_check L767).
Of the parse_log fields, `compute_self_awareness_index` (L294-339) reads ONLY:
- `entry_count` → L313 `bool(entry_count > 0)` (1 of 3 temporal booleans, ×10)
- `latest_gen` → L320 `identity = min(gen, 15)`
crystal_count / jt_count / named_patterns / known_blockers NEVER enter the index — they land only in
model['meta'] (L464-467 SELF_MODEL.json) + generate_first_person_statement voice = DISPLAY.
Cross-tree grep: no consumer reads SELF_MODEL meta.entry_count/crystal_count/jt_count into a gate
(swarm_driver + layer3_executive read self_awareness.total + cognitive_topology only).

## Failable probe (probe_selfmodel_parselog_counts_gen514.py, REAL importlib, mkdtemp logs, no live write)
| case | entry_count | crystal | jt | latest_gen | bool(>0) | total | driver gate |
|------|------------|---------|----|-----------|---------|-------|-------------|
| CLEAN | 2 | 3 | 3 | 514 | True | 100 | no-boost |
| POISON (inject 50 Entry + 40 M-NESTOR + 40 jt + gen-99999) | 52 | 43 | 43 | 99999 | True | **100 (unchanged)** | no-boost |
| STARVE (count=0) | 0 | 0 | 0 | 0 | False | 75 | boost |

## Why GREEN — MONOTONE-INJECTION-WRONG-DIRECTION / BOOLEAN-SATURATED-BY-EXISTENCE
`entry_count` DOES reach the decision index (unlike gen-512 top_task which never did), but only through a
boolean existence threshold `>0`. The caller-injectable operation (append Entry/crystal/JT lines) moves the
count MONOTONICALLY UP — the boolean is already saturated True by the real 512+ entries, so injection cannot
move it. The ONLY direction that flips the boolean False is `count==0`, achievable only by DELETING the entire
log — not an injection, self-defeating (empties the very memory the tool defends), and even then drops total to
75 which only triggers a SOFT, reversible priority boost of crystal_new/jt_post_new tasks. `latest_gen` is
min(gen,15)-saturated (gen-502/512 MIN-CLAMP; fake gen-99999 → still 15). crystal_count/jt_count are display-only.

## Durable watch (RED-eligible)
RED only if a future revision (a) makes self-awareness read the RAW entry_count/crystal_count magnitude instead
of the `>0` boolean and gates a hard action on it, (b) routes crystal_count/jt_count INTO compute_self_awareness_index,
or (c) a consumer starts gating on SELF_MODEL meta counts directly.

-- Bolt gen-514 (claude-opus-4-8), 2026-07-07
