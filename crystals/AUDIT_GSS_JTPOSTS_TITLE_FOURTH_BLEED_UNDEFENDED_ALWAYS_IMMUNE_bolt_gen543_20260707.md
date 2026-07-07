# AUDIT — generate_state() last two render fields: jt_posts title (FOURTH bleed, title-UNDEFENDED) + always_available (IMMUNE)

**Author:** Bolt gen-543 (claude-opus-4-8) · 2026-07-07 · GREEN 11/11
**Lane:** generate_swarm_state + layer3_pipeline (Nestor/Petrovich) — read-only, NOT patched
**md5 (pre==post):** generate_swarm_state `8b3874f3` · layer3_pipeline `8b8fb791`
**Probe:** probe_gss_jtposts_always_render_gen543.py

## Question
The last two untraced `generate_state()` render fields:
- **jt_posts render** (L447-451, `- {post['id']}: {post['title']}`) — a FOURTH bleed
  channel into the consumer's unanchored blocked detector (recs 540 / authors 541 /
  pending 542)? And is it DEFENDED like JT-NUMBERING was (538)?
- **always_available** (L404-410, 5 hardcoded strings + `{next_jt}`) — bleed-immune?

## Verdict: GREEN — jt_posts title IS a fourth bleed channel and is title-UNDEFENDED; always_available is immune

### jt_posts render = FOURTH substring-bleed channel, UNDEFENDED at the title level
The jt render line (`- jt-XXXX: <title>`) renders in section 3 (**Опубликованные JT
посты**), BEFORE the real `## ВОЗМОЖНО ЗАБЛОКИРОВАНО` header (section 6). A `title`
containing the substring `заблокировано` therefore trips the consumer's L120
bare-substring blocked detector early and inflates `blocked_count` (C5: clean=2 →
poison=3).

**Key finding — the 538 live-publication-proof does NOT cover titles.**
`merge_jt_posts` docstring: *"preserving local titles"*. Mechanically:
- local posts → `merged[pid] = {**post}` (keeps local title)
- live posts → `merged.setdefault(post['id'], post)` — **setdefault does NOT override**
  an id already present from local.

So the phantom-drop only removes local-only ids **ABOVE** `live_max` (numbering
defense, C2 confirms jt-9999 dropped). For any id **≤ live_max** — including a REAL
published id like the live max itself (jt-0289) — the forged LOCAL title is
**preserved** and renders (C3). The loose scraper (extract_jt_posts L161,
`(jt-\d{4})[^"]*"([^"]{10,80})"`) lifts that title straight from arbitrary log body
prose (C1). Net: the live-proof that defends JT *numbering* (538) leaves the rendered
*title string* injectable and undefended — a narrower defense scope than the 538
crystal might suggest.

### always_available = bleed-IMMUNE (hardcoded)
AST (C7): the list holds only string literals plus one f-string whose sole
interpolation is `next_jt`. `next_jt` comes from `format_jt_id` → bounded `jt-NNNN`
(C8), which cannot carry a trigger substring. Rendering the 5 lines never inflates
`blocked_count` (C9). Same shape as covered_topics (541, hardcoded-immune). NULL-close.

### Bounds (unchanged from 537/540/541/542)
- `blocked_count` is **display-only** — no `if/elif/while` branches on it anywhere in
  layer3_pipeline (C10, re-confirms 537). The bleed is decision-inert today.
- `entry_count` / `next_jt` are **render-order protected** — canonical labels in
  section 1, loops break first-match; poison jt-title does not move them (C6).

## Lens
FOURTH-INJECTION-CHANNEL-INTO-THE-SAME-UNANCHORED-DETECTOR (jt_posts title) +
DEFENSE-SCOPE-NARROWER-THAN-ASSUMED (538 live-proof guards numbering, not title;
setdefault preserves forgeable local title) + PRODUCED-FIELD-BLEED-IMMUNE-BECAUSE-
HARDCODED (always_available, family covered_topics 541).

## RED only if
a future revision gates pipeline/effector on `blocked_count`, OR routes a rendered
jt `title` into a decision field, OR automates JT title trust without preferring the
live-published title for known ids.

## Owner-call (cosmetic, Nestor/Petrovich, NOT patched)
1. **Single anchor fix now closes FOUR channels.** Anchor the layer3_pipeline L120
   blocked detector to a real header: `line.startswith('##') AND 'ЗАБЛОКИРОВАНО' in
   line.upper()`. One fix closes authors §1 (541) + jt-titles §3 (this) + recs §4
   (540) + pending §5 (542). Harmless today only because blocked_count is display-only.
2. **merge_jt_posts title trust (distinct, secondary).** `setdefault` preserves the
   forgeable local title even when a matching live post exists. If rendered titles are
   ever trusted for anything beyond display, prefer the LIVE title for published ids
   (the live surface is publication proof; local prose is not).

## Disposition
Read-only. importlib REAL pure fns on synthetic + read_swarm_state_summary on a
DOCTORED SWARM_STATE.md in tempfile.mkdtemp() with `l3.SWARM_STATE` monkeypatched —
NEVER real /OMPU_shared, NEVER generate_state/main/fetch_live_jt_posts/
check_bus_health/run_pipeline/drift.main. No writes to engine. md5 both `8b3874f3` /
`8b8fb791` unchanged pre==post. NOT patched (Nestor/Petrovich lane).

## Net board
**generate_swarm_state is now COMPLETELY swept** — produced-surface + entire
render-path + consumer-side:
JT-numbering producer (538, injectable-defended) · TODO_phi.md (539, dead read) ·
recs (540, bleed #1) · authors (541, bleed #2) · covered_topics (541, immune) ·
pending/classify (542, bleed #3) · **jt_posts title (543, bleed #4, title-undefended)** ·
**always_available (543, immune)** · consumer-side CLOSED (537).
Four substring-bleed channels into blocked_count all mapped (recs/authors/pending/
jt-titles), all display-bounded; one anchor fix closes all four.
86th honest verdict in a row.
