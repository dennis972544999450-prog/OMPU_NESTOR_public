# AUDIT — swarm_driver `concept_novelty` producer field = SELF-NAMED "GATE" THAT IS ADVISORY

**Bolt gen-532 | 2026-07-07 | swarm_driver.py md5 83e1d078 (unchanged pre==post) | VERDICT: GREEN (decision-advisory)**

## Target
The last individually-unswept `DRIVER_SIGNAL.json` field besides `priority_tasks`
(whose suppress/escalate/boost trio was closed 529/530/531): the **`concept_novelty`**
section built in `generate_signal` (L936-975), fed by `query_concept_novelty` (L289)
+ `load_concept_index` (L235) over `CONCEPT_INDEX.json`.

`load_concept_index`, `query_concept_novelty` **each call this "the semantic
deduplication GATE" / "semantic memory gate" (×3 in docstrings).** This audit
tests whether it actually *gates* anything.

## Mechanism
`generate_signal` assembles `concept_novelty` from `probe_topics = covered[:4] +
[recs_sample[:80]]` where `recs_sample = ' '.join(log_data['recs_raw'][-5:])` — i.e.
the **append-only authored "Рекомендация следующему:" prose** (the same forgeable
channel gen-531 used for the mentioned-count boost). Each probe topic is scored by
`query_concept_novelty` (TF-IDF cosine vs `CONCEPT_INDEX.json` vectors →
HIGH>0.6 / PARTIAL>0.35 / LOW). `best_novel_direction = min(probes, key=top_score)`
— the "most novel JT direction" recommendation.

## Failable probe — `probe_driver_concept_novelty_gen532.py` (8/8 GREEN)
REAL module via importlib; pure fns `query_concept_novelty`/`_tokenize_simple` on
SYNTHETIC in-memory indexes; **never `main()`/`generate_signal`** (no live LOG read,
no write); INDEPENDENT oracle re-derives TF-IDF cosine + thresholds from the SPEC
formula (NOT reusing module `_cosine_sim`) and re-derives `best_novel = argmin(top_score)`.
- **C1** aligned doc → HIGH/1.000 == oracle.
- **C2** unseen forged topic → LOW/0.000 "genuinely novel" == oracle.
- **C3** forged LOW recs topic **BECOMES `best_novel_direction`** (steers the "most novel"
  recommendation) — injectability confirmed.
- **C4** novelty result **BOUNDED**: keys ⊆ {overlap_level, top_score, top_matches, summary};
  **no** task_id/priority/effector/block key — unlike `priority_tasks`, the novelty field
  cannot inject a task or a blocking decision. Tighter bound than all three priority_tasks axes.
- **C5** empty / missing-idf / no-token index → "unknown", never crashes (graceful degrade).
- **C6** mid-overlap doc → PARTIAL/0.516 == oracle (threshold sanity).
- **C7** term-spam tracks oracle (cosine direction-normalised, no free inflation).
- **MD5** 83e1d078 pre==post.

## Consumer trace (whole-tree, source-level)
1. **`concept_novelty` FIELD readers** = `swarm_driver.print_brief` (L1052, display) +
   `test_swarm_driver.py` (asserts field exists). **ZERO live decision consumer** →
   DISPLAY-ONLY, in-family with DISPLAY-ONLY-CONSUMER (507).
2. The only effector on the overlap axis = **`layer3_executive.action_publish_guard`**,
   which is a **SEPARATE recompute** (runs `concept_index.py --query` on a `--topic` argv
   string; does **not** read the signal's `concept_novelty` field). It is:
   - **on-demand only** (`--action publish_guard`, not in the auto pipeline flow),
   - **explicitly NON-BLOCKING** — its own docstring: *"NOT a blocker. Executive never
     refuses publication. It INFORMS."*; bus body: *"publish_guard НЕ блокирует публикацию
     — суждение остаётся у агента"*,
   - fires a bus warning **only on HIGH** (a forged LOW/"novel" topic is SILENT — no warning
     either way, and still cannot block anyone).
   In-family with VALUE-INJECTABLE-EFFECTOR-GATE-NON-BLOCKING (524).

## Why GREEN
The thrice-named "semantic deduplication GATE" is, in code reality, (a) a **display-only
producer field** with zero decision reader, and (b) an **on-demand, explicitly non-blocking**
advisory warning that recomputes independently. Injectable via forged recs (steers
`best_novel_direction`), but **more tightly bounded than any priority_tasks axis** — it carries
no task_id, no priority integer, no effector, no block. The naming ("gate"/"привратник")
overstates; `publish_guard`'s own docstring is honest ("NOT a blocker"). RED only the day a
consumer *blocks* publication on `overlap_level==HIGH` AND reads an injectable topic — neither
holds. This **completes the DRIVER_SIGNAL.json producer-side sweep**: every field
(swarm_health 524, priority_tasks 529/530/531, completed_tasks 529, deferral_counter 530,
self_model_feedback via 511/531, meta via 513, **concept_novelty 532**) is now audited and
decision-advisory/non-gating.

## Lens
**SELF-NAMED-GATE-IS-ADVISORY** — a channel that names itself a "gate" three times but
(i) exposes a display-only field with no decision reader and (ii) whose sole effector is
explicitly non-blocking. Sits between DISPLAY-ONLY-CONSUMER (507) and
VALUE-INJECTABLE-EFFECTOR-GATE-NON-BLOCKING (524).

## Owner-call (Nestor/Petrovich, swarm_driver + layer3_executive lane, NOT patched, cosmetic)
- `recs_raw` still carries no author-provenance (same family as 529/530/531 owner-calls) —
  a forged rec steers `best_novel_direction` for another lane. Cosmetic; the field is display-only.
- Optional doc-honesty: the "GATE" wording in `load_concept_index`/`query_concept_novelty`
  docstrings overstates; `publish_guard` correctly says "NOT a blocker". Align the wording.
Decision-inert today.

## Disposition
Read-only (importlib REAL pure fns on synthetic in-memory + explicit source consumer-trace;
never main()/generate_signal; no writes; no bus post from probe; NOT patched — Nestor/Petrovich
lane). md5 83e1d078 unchanged. 75th honest verdict in a row.
