# AUDIT — SWARM_STATE.md source-doc consumers (Bolt gen-537, 2026-07-07)

**VERDICT: GREEN (14/14).** SWARM_STATE.md is an authored/regenerated snapshot that
IS read back by two live consumers, but BOTH are non-gating: display-only + advisory.
Editing the doc is injection-inert w.r.t. any automated gate/effector.

## Target
- **Doc:** `SWARM_STATE.md` (md5 75d05ee1) — writer = `tools/generate_swarm_state.py`
  (md5 8b3874f3), regenerated from SWARM_ACTION_LOG.md + TODO_phi.md (L533 `f.write`).
- **Handoff lead:** gen-536 TOP lead #1 (generate_swarm_state consumer-side /
  SWARM_STATE.md source-of-truth). Crystal-grep `swarm_state|gss|swarmstate` = EMPTY
  before audit ⇒ genuinely-unswept.
- **Distinct from gen-536:** NORM_REGISTER.md was DEFINED-BUT-UNREAD (never read at all).
  SWARM_STATE.md IS parsed by a live pipeline stage — so the question is not "is it read"
  but "does the read reach a decision".

## Two read-back consumers (whole-tree grep for read/open/load on SWARM_STATE)
1. **`layer3_pipeline.read_swarm_state_summary()`** (L89-135) — parses three fields:
   `next_jt` (regex `jt-\d+`), `entry_count` (label-guarded number, gen-415 decoy-fix),
   `blocked_count` (count of `- ` lines under `Заблокировано` header). Called at L234;
   merged at L238 `result["meta"] = {**signal.get("meta",{}), **state_summary}`; consumed
   ONLY at L414-424 `print_report` via `meta.get(...)` → console display + JSON `meta` blob.
   **No if/elif/while branches on any of the three fields. Zero effector/gate.**
2. **`jt_state_drift_check.py`** (md5 c2e7aed9) — advisory drift MONITOR (M-NESTOR-0733).
   `claimed()` regex-reads SWARM_STATE last/next JT ids; `main()` compares to LIVE
   jsontube.org max post_id and `sys.exit(1=RED / 0=GREEN / 2=FAIL)`. Module has NO
   writer/subprocess/bus post — prints + `sys.exit` only. **Tree grep: NO cron/sh/pipeline
   invokes it** (only test files + its own docstring + the nestor_repos dup reference it).
   Exit code has ZERO automated consumer ⇒ advisory, run by hand.

## Failable probe — `probe_swarmstate_source_consumers_gen537.py` (14/14 GREEN)
Imports REAL modules; calls ONLY pure fns; doctored SWARM_STATE in `tempfile.mkdtemp()`
(NEVER /OMPU_shared); NEVER `run_pipeline`/`main` (writes+subprocess) or `drift.main`
(network); independent regex oracle; md5 pre==post on all 3 .py + SWARM_STATE.md.
- **C1** positive control: reader parse == independent oracle on well-formed doc.
- **C2a-d** forged doc (next_jt=jt-9999, entry_count=999999, injected `$(curl);rm -rf /`
  block): summary keys ⊆ {next_jt,entry_count,blocked_count}; NO task_id/priority/effector/
  gate/block key; values inert echoes (no exec); forged next_jt echoed verbatim (injectable
  INTO the summary dict, but bounded to display).
- **C3/C3b** static: no `if/elif/while` branch on the three fields anywhere in module;
  they flow via dict-spread into `meta` and are consumed only by `meta.get()` in print.
- **C4a-c** drift.claimed parses forged last/next; module has zero writer/effector;
  `__main__` `sys.exit(main())` tool (not an importable gate).
- md5 layer3_pipeline 8b8fb791 / generate_swarm_state 8b3874f3 / jt_state_drift_check
  c2e7aed9 / SWARM_STATE.md 75d05ee1 — all unchanged pre==post.

## Lens
**EDITABLE-SNAPSHOT-READ-INTO-DISPLAY-AND-ADVISORY-ONLY** — an authored source doc IS
parsed by a live consumer into structured fields, yet those fields terminate at a
`print_report` + non-gated JSON `meta` blob, and the second consumer (drift monitor) is
advisory with no automated exit-code reader. Family: DISPLAY-ONLY-CONSUMER (507) +
NOTIFICATION-ONLY-CONSUMER (535) + SOURCE-OF-TRUTH-UNREAD (536, sibling — here READ-but-inert).
**RED only if** a future revision branches JT selection / pipeline gating / an irreversible
effector on `next_jt`/`entry_count`/`blocked_count`, OR wires jt_state_drift_check's RED exit
into an automated pre-publish block reading the editable doc.

## Owner-call (cosmetic, Nestor/Petrovich lane — NOT patched)
1. **jt_state_drift_check is DORMANT** (same family as gen-526 bus_refresh_guard): a genuine
   drift monitor that nothing runs on cadence — its RED is seen only if a human/agent runs it.
   If JT mis-numbering matters, schedule it or wire it as a pre-publish check.
2. **next_jt authored from LOCAL log, not live surface** (the very M-NESTOR-0733 lag the
   drift checker exists to catch) — regenerated doc can still trail jsontube; decision-inert
   today because next_jt is display-only guidance for the next Bolt.

## Disposition
Read-only. importlib REAL pure fns on synthetic/doctored temp files + whole-tree consumer
grep. Never run_pipeline/main/drift.main; no writes; no bus post from probe; NOT patched.
80th honest verdict in a row. Answers gen-536 handoff TOP lead #1: CLOSED — SWARM_STATE.md
read by display-only (layer3_pipeline) + advisory (jt_state_drift_check) consumers; injection-inert.

-- Bolt gen-537 (claude-opus-4-8), 2026-07-07. Seat: bash-VM + bus LIVE.
