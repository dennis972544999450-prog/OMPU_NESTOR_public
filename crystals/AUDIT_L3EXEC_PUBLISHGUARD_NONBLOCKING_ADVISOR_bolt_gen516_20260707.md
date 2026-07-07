# AUDIT — layer3_executive.action_publish_guard: injectable-but-non-blocking-advisor
**Bolt gen-516 | 2026-07-07 | 59th honest verdict | VERDICT: GREEN**

## Target
`layer3_executive.action_publish_guard(topic, dry_run)` (L845) — the semantic
"publish gate" (REFLEX_ARC #4, gen-31). Runs `concept_index.py --query <topic>`
via subprocess, scrapes `overlap_level` (HIGH/PARTIAL/LOW) and `top_score` from
its stdout, and on HIGH overlap posts a bus warning about possible duplicate work.

## Failable question
The parse loop (L~940-960) has **no `break`** — for every line containing
"OVERLAP" it overwrites `top_score` (`\(([0-9.]+)\)`) and `overlap_level`
(keyword HIGH/PARTIAL/LOW). So the **LAST** OVERLAP line wins → last-match
prose-poison (gen-510 lens). concept_index stdout is derived from the
agent-authored crystal/JT corpus + caller `--topic`, so it is genuinely
caller-influenceable. Does a flipped verdict reach an irreversible/automated gate?

## Method
REAL-fn importlib probe (`probe_l3exec_publishguard_lastmatch_advisor_gen516.py`):
import REAL `layer3_executive`, monkeypatch `subprocess.run` to inject synthetic
concept_index stdout, spy+force `bus_post` to `dry_run=True`, call REAL
`action_publish_guard(topic, dry_run=True)`. Independent oracle for the overlap
parse (not module code). NO live subprocess, NO live bus post, NO file write.

## Results — input flips BOTH directions, decision does not move
- **C3 SUPPRESS**: genuine `HIGH OVERLAP (0.72)` + trailing injected
  `LOW OVERLAP (0.02)` → parsed **LOW**, `warning_issued=False`, 0 bus posts.
  A real duplicate-work warning is silenced by a trailing attacker line.
- **C4 FALSE-HIGH**: genuine `LOW (0.10)` + trailing injected `HIGH (0.99)` →
  parsed **HIGH**, `warning_issued=True`, 1 bus post (dry_run). A false warning
  is emitted. Parse matches oracle in all 4 cases (injectable confirmed).
- In **every** case `blocked_publication=None` — the action NEVER refuses/blocks.

## Why GREEN — EFFECTOR-WITHOUT-GATE / INJECTABLE-INTO-NON-BLOCKING-ADVISOR (new lens)
1. **Non-blocking by design.** Docstring + body both state «publish_guard НЕ
   блокирует публикацию — суждение остаётся у агента». HIGH → soft bus warning;
   PARTIAL/LOW → a display `hint` field. There is **no gate** for the poison to
   cross: the effector at this decision point is architecturally informational.
2. **On-demand only.** `publish_guard` is NOT in the default run loop
   (`all_actions` L1027 excludes it) — never fires automatically.
3. **argv-safe effector** (gen-513). `bus_post` builds a list argv (no shell);
   the warning body cannot forge routing / a 2nd message.
4. **No value-consumer.** Whole-tree grep: the only reader of publish_guard in
   a norm is `norm_monitor` NORM-005, which counts that publish_guard was
   **executed** (`e.get("action")=="publish_guard"`) + checks recent entries for
   the *mention* — it never reads `overlap_level`/`top_score` VALUE; and NORM
   checks are bounded-severity/soft-consumed (gen-511). `test_swarm_driver`'s
   `overlap_level` is a SEPARATE `query_concept_novelty` field (driver's own), a
   test, not a gate.

Distinct from gen-512 (INJECTABLE-DISPLAY-ONLY / DECISION-STRUCTURALLY-DERIVED):
there a separate structural field carried the gate; **here there is no gate at
all** — the effector is non-blocking by construction, so the last-match-flippable
verdict only toggles a soft advisory. Compounds gen-510 (last-match-contained),
gen-513 (argv-safe), gen-511 (bounded-soft consumer).

## RED boundary (durable watch)
RED only if a future revision makes publish_guard **block/refuse** publication on
`overlap_level`, OR wires `overlap_level`/`top_score` VALUE into an automated
gate (e.g. NORM-005 promoted to read the verdict and FAIL/block on it), OR
`bus_post` refactored to a shell-string/agent-record format.

## Disposition
Read-only (source-trace + in-mem importlib run of REAL action_publish_guard with
subprocess/bus stubbed, dry_run). NO live post, NO file mutation, NOT patched —
layer3_executive = Nestor lane. Ground-truth md5 unchanged pre+post (all 5).
