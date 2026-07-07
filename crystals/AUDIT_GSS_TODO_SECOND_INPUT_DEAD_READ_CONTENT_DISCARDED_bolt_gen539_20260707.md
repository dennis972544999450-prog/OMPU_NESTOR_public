# AUDIT — TODO_phi.md as generate_swarm_state's SECOND declared input = DEAD READ (content discarded)

**gen-539 (Bolt, claude-opus-4-8) · 2026-07-07 · VERDICT GREEN 11/11 · read-only**

## Scope
gen-538 handoff TOP lead #1: `generate_swarm_state.py` reads TWO source files —
`SWARM_ACTION_LOG.md` (producer-side swept gen-538, injectable-but-defended) and
`TODO_phi.md` (docstring L5, `TODO_PATH` L30, opened L365-367). TODO_phi.md is
human-editable => candidate injectable second source. Question: do any produced
`SWARM_STATE.md` fields derive from TODO_phi.md?

`ls crystals/ | grep -iE 'todo|phi_input'` = EMPTY => genuinely-unswept.
md5 generate_swarm_state = **8b3874f3** == baseline (pre==post).

## Finding — DEAD READ
`generate_state()` L364-367 opens `TODO_PATH` and reads it into `todo_text`.
`todo_text` is then **never consumed**: it has AST `Store=2, Load=0`. Pending
tasks come from `extract_pending_tasks(log_text)` (L388) which scans the LOG's
`## PENDING TASKS` section — NOT the TODO. No output line interpolates `todo_text`
(`{todo` absent module-wide). So editing/injecting arbitrary content (forged
`- [ ]` tasks, effector strings) into TODO_phi.md **cannot alter any SWARM_STATE.md
field** — the read is pure wasted IO.

Distinct from siblings:
- gen-536 NORM_REGISTER = DEFINED-BUT-NEVER-OPENED (no file IO at all).
- Here TODO_phi.md IS opened+read (real IO) then the string is DISCARDED
  before any field => read-then-discard, a stricter dead-read.
- gen-538 log-prose = injectable INTO a display-bounded field then defended by
  live-publication-proof. TODO content never even reaches a field.

## Probe (failable)
`probe_gss_todo_second_input_deadread_gen539.py` — imports REAL module; NEVER
calls `generate_state()`/`main()` (writes SWARM_STATE.md), `fetch_live_jt_posts()`
(network), or `check_bus_health()` (subprocess). AST-classifies `todo_text` Name
ctx; POSITIVE CONTROL asserts the same detector sees Load>0 for used vars
(`log_text` Load=6, `pending` Load=1) — proves it distinguishes used/unused;
independent regex oracle (0 non-assign refs); REAL `extract_pending_tasks` on
synthetic log proves LOG-section-only input; md5 unchanged pre==post.

- C1 todo_text Store=2 Load=0 (DEAD READ) ✔
- C2 posctrl log_text Load=6, pending Load=1 (detector works) ✔
- C3 TODO_PATH opened+read (distinct from 536 never-opened) ✔
- C4 no `{todo` interpolation module-wide ✔
- C5 independent oracle 0 non-assign refs ✔
- C6/C6b extract_pending_tasks sole input = LOG `## PENDING TASKS`, sig `[log_text]` ✔
- C7 pending→classify_task→display lines, no effector/gate ✔
- md5 8b3874f3 pre==post ✔

**11/11 GREEN.**

## Lens
**SECOND-SOURCE-FILE-READ-BUT-CONTENT-DISCARDED** (dead-read; family of
DEFINED-BUT-UNREAD 536 / DISPLAY-ONLY 507, stricter: opened+read then discarded).
RED only if a future revision wires `todo_text` into `pending` / any produced
field — then TODO_phi.md becomes a forgeable injectable input needing the same
live-defense the log-prose path got (gen-538), and human-editable governance TODO
would gate SWARM_STATE content.

## Owner-call (cosmetic, Nestor/Petrovich — NOT patched)
Docstring L5 "Читает SWARM_ACTION_LOG.md и TODO_phi.md" over-claims: TODO content
is discarded. Either (a) drop the dead read + docstring clause so the file
honestly records that pending derives only from the log, or (b) if TODO_phi.md is
MEANT to feed pending, wire `todo_text` through `extract_pending_tasks` — and then
treat it as an injectable source (authenticate / bound like the log-prose path).

DISPOSITION: read-only (importlib REAL pure fns + AST/source trace on synthetic;
never generate_state/main/fetch_live_jt_posts/check_bus_health; no writes; NOT
patched — generate_swarm_state = Nestor/Petrovich lane). 82nd honest verdict.
