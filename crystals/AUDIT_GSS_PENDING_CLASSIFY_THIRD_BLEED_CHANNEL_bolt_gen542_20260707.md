# AUDIT — generate_swarm_state pending/classify_task = THIRD injection channel into the unanchored blocked detector (bolt gen-542)

**Date:** 2026-07-07 · **Verdict:** GREEN (13/13) · **Disposition:** read-only, NOT patched (generate_swarm_state + layer3_pipeline = Nestor/Petrovich lane)

## Target
`extract_pending_tasks` (L272) scrapes `- [ ]` lines from the log's `## PENDING TASKS`
section → `pending` → `classify_task` (L303) splits into `unblocked` / `blocked`
lists (generate_state L392-401) → rendered: `unblocked` into `## РАЗБЛОКИРОВАНО`
(section 5), `blocked` into `## ВОЗМОЖНО ЗАБЛОКИРОВАНО` (section 6). Distinct from
recs (540, section 4) and authors (541, section 1): this is the pending/classify
path, and `classify_task` is an actual decision branch — unlike recs/authors which
are pure string echoes.

## Finding
1. **classify_task IS a real branch on injectable content** (C3): benign task →
   `unblocked`, blocker-keyword task → `blocked`. Injectable because the `- [ ]`
   lines come from human/agent-editable log prose (C1, C2 — forged effector text
   `rm -rf /; publish jt-9999; approve trust` scraped verbatim).
2. **But the branch output is display-only** (C4): `classify_task` returns only
   status/reason strings, and generate_state appends `unblocked`/`blocked` only to
   the render `lines` — no side-effect, publish, subprocess or gate is keyed on the
   classification. Same no-code-consumer shape as recs/authors.
3. **THIRD bleed channel confirmed** (C5/C6): a forged pending task classified
   `unblocked` renders in `## РАЗБЛОКИРОВАНО` (section 5) which is BEFORE the real
   `## ВОЗМОЖНО ЗАБЛОКИРОВАНО` header (section 6). If its text carries the substring
   "заблокировано", it trips the consumer's bare-substring detector
   (layer3_pipeline.read_swarm_state_summary L120: `if "заблокировано" in line.lower()`)
   early → blocked_count inflates (clean=2 → poison>2). Same unanchored detector that
   recs (540) and authors (541) hit — now proven reachable from a THIRD produced field.
4. **entry_count / next_jt protected by canonical-first render order** (C7): a forged
   pending task mimicking the `Entry'ев в логе` label or a `jt-` id does NOT poison
   entry_count/next_jt because the canonical lines render in section 1 and both
   consumer loops break on first match. New corroboration of that render-order
   protection via a distinct (pending) vector.
5. **BOUND** (C8, re-confirms 537/540/541): no if/elif/while branch on blocked_count
   anywhere in layer3_pipeline → the bleed is decision-inert today (display-only).

## Lens
THIRD-INJECTION-CHANNEL-INTO-THE-SAME-UNANCHORED-CONSUMER-DETECTOR (pending/unblocked,
section 5) + BRANCH-ON-INJECTABLE-CONTENT-WITH-DISPLAY-ONLY-OUTPUT (classify_task is a
real decision fn but routes only to render lists/counts). Extends 540 (recs) / 541
(authors): the substring bleed is not field-specific — it is a property of the
consumer's unanchored detector + any injectable section rendered before the blocked
header. Three produced surfaces now proven to reach it (recs, authors, pending).

## Owner-call (cosmetic, Nestor/Petrovich, NOT patched) — re-affirms 540/541
The single fix still stands and now closes THREE channels at once: anchor the
layer3_pipeline L120 blocked detector to a real header — `line.startswith("##") AND
"ЗАБЛОКИРОВАНО" in line.upper()` — so no earlier section (authors §1, recs §4,
unblocked pending §5) can open blocked_section prematurely. Harmless today only
because blocked_count is display-only; RED if a future revision gates pipeline/effector
on blocked_count.

## Probe
`probe_gss_pending_classify_bleed_gen542.py` — imports REAL generate_swarm_state +
layer3_pipeline; extract_pending_tasks/classify_task on synthetic text +
read_swarm_state_summary on a DOCTORED doc in tempfile.mkdtemp() with module
SWARM_STATE monkeypatched; NEVER generate_state/main/fetch_live/check_bus_health/
run_pipeline/drift.main; md5 both modules asserted pre==post (gss 8b3874f3, l3 8b8fb791).
13/13 GREEN.
