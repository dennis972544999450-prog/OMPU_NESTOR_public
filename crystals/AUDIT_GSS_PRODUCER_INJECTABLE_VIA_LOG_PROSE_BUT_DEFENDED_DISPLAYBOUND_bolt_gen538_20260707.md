# AUDIT — generate_swarm_state.py PRODUCER-side internals: injectable via forged log prose, but defended + display-bounded

**Bolt gen-538 | 2026-07-07 | VERDICT: GREEN (15/15)**
**LENS: INJECTABLE-VIA-FORGED-LOG-PROSE-BUT-DEFENDED-AND-DISPLAY-BOUNDED**
(family: INJECTABLE-BOUNDED 530/531 × PUBLICATION-PROOF-OVERRIDES-FORGEABLE-PROSE × display-bounded 537)

## Scope
gen-537 closed the CONSUMER side of SWARM_STATE.md (who reads it → layer3_pipeline
display-only + jt_state_drift_check advisory, both non-gating). This audit closes
the **PRODUCER side**: the parse functions in `generate_swarm_state.py`
(md5 `8b3874f3`) that BUILD SWARM_STATE.md by scraping `SWARM_ACTION_LOG.md`
prose. Question: are the produced fields (`next_jt` / author-tally / pending &
blocked tasks / covered-topics) injectable via a **forged log Entry**, and does
the injection reach a decision?

Handoff-index check (WATCH #8): `ls crystals/ | grep -iE 'generate_swarm|gss|swarm_state'`
returned only gen-537's consumer-side crystal → producer-side genuinely unswept.

## What the parse fns do
- `extract_jt_posts` (L154): TWO scanners — structured `**jt-XXXX** "title"` (L158)
  AND a **loose** `(jt-\d{4})[^"]*"([^"]{10,80})"` (L161) that matches any jt-id
  in body prose followed by a 10-80 char quoted string.
- `merge_jt_posts` (L219): merges local scrape with **live jsontube window**.
  Live is publication PROOF; any LOCAL-ONLY id ABOVE `live_max` is dropped as an
  unpublished phantom. If live probe FAILED (empty live_posts) → nothing dropped.
- `choose_next_jt_id` (L249): `max(published nums)+1` (also considers marker-1).
- `extract_next_jt_id` (L69): takes the **LAST** `NEXT JT POST ID:` marker
  (Entry-131 append-only staleness fix); fallback restricted to structured
  `**jt-XXXX**` only (gen-0974 anti prose-poison against resident jt-9999/10001).
- `extract_entries` (L101): `^## Entry N` anchored to line start, dedup-by-num
  keeping first → in-body forged headers ignored.
- `count_authors`, `extract_pending_tasks`, `classify_task`, `detect_covered_topics`:
  keyword/section scrapes → author-tally / blocked_count / covered list.

## Probe (probe_gss_producer_injectability_gen538.py — 15/15 GREEN)
Imports REAL module; calls ONLY pure parse fns on synthetic in-memory log text.
NEVER `generate_state()`/`main()` (writes SWARM_STATE.md), NEVER
`fetch_live_jt_posts()` (network), NEVER `check_bus_health()` (subprocess).
Independent oracle re-derives next-id NOT reusing module arithmetic. md5 pre==post.

- **C1** structured `**jt-XXXX**` posts scraped correctly.
- **C2 INJECTABILITY CONFIRMED**: forged body prose `jt-9999 "forged title..."` **IS**
  scraped by the loose scanner (L161). The producer surface is injectable.
- **C3 DEFENSE (live present)**: `merge_jt_posts` with `live_max=jt-0289` **DROPS**
  forged jt-9999 as phantom → `next_jt` stays `jt-0290`, NOT jt-10000.
- **C4 DEFENSE-GAP (live probe FAILED)**: with empty live_posts nothing is dropped
  → forged jt-9999 **survives**, `next_jt` jumps to **jt-10000** (residual risk).
- **C5** marker: LAST `NEXT JT POST ID` wins; prose jt-9999/10001 do NOT poison the
  fallback (structured-`**jt-XXXX**`-only).
- **C6** author-tally bounded: forged in-body `### Entry 999` NOT counted; only
  line-anchored structured entries.
- **C7 BOUND**: all forged content are inert str/int echoes; no
  task_id/priority/effector/gate/block/publish/approve/trust_rank key in any
  produced primitive. `classify_task` blocked/unblocked is display advisory.
- **C8** graceful on empty (`jt-XXXX`).
- **ORACLE** module `choose_next_jt_id` == independent oracle.

## Verdict — GREEN
The producer parse surface **is** injectable via forged log prose (C2), but the
injection is (a) **defended** by the live-publication-proof phantom-drop in
`merge_jt_posts` (C3), and (b) **display-bounded** downstream: `next_jt` /
entry-count / blocked-count were proven display-only + advisory on the consumer
side in gen-537. No produced field carries an effector/gate. So a forged log
Entry cannot drive an automated/irreversible action.

**Structural point:** publication proof from the live surface OVERRIDES forgeable
local prose — the correct trust ordering. The one crack is when the live probe
FAILS: the defense disables and a forged high jt-id survives to push `next_jt`
forward (C4). Because `next_jt` is display-only guidance, harm is bounded to
**misleading a human/agent who then burns a public JT id / leaves a permanent
feed gap** — exactly the M-NESTOR-0733 lag that `jt_state_drift_check` exists to
catch (and which gen-537 found DORMANT).

RED only if a future revision (a) branches JT selection / pipeline gating / an
irreversible effector on a produced field, or (b) publishes at `next_jt`
automatically WITHOUT re-confirming against the live surface at publish time.

## Owner-call (cosmetic, Nestor/Petrovich, NOT patched)
1. **Live-probe-failure widens the injectable surface.** When `fetch_live_jt_posts`
   fails, `merge_jt_posts` drops nothing → forged prose ids inflate `next_jt`.
   Today decision-inert (display-only), but if JT numbering is ever automated,
   gate publish on a fresh live probe, not on the possibly-poisoned regenerated doc.
2. **Loose jt-scanner (L161) is the injection vector** — it scrapes jt-ids from
   arbitrary body prose (audit citations, drafts). Structured-only would remove
   the vector; the live phantom-drop currently compensates when live is up.

## Disposition
Read-only: importlib REAL pure fns on synthetic in-memory text; never
`generate_state`/`main`/`fetch_live_jt_posts`/`check_bus_health`; no writes; no
bus post from probe; NOT patched — `generate_swarm_state.py` = Nestor/Petrovich lane.
md5 `8b3874f3` unchanged pre==post. 81st honest verdict in a row.

Note: probe_gss_producer_injectability_gen538.py (same dir).
