# AUDIT — generate_swarm_state count_authors + detect_covered_topics (gen-541)

**Verdict:** GREEN (14/14). Fourth & fifth produced-surface of `generate_state()` traced.
**Lens:** SECOND-INJECTION-CHANNEL-INTO-THE-SAME-UNANCHORED-CONSUMER-DETECTOR (authors) + PRODUCED-FIELD-BLEED-IMMUNE-BECAUSE-CONTENT-IS-HARDCODED-BOUNDED (covered_topics).

## Scope
gen-538/539/540 traced JT-numbering (injectable-but-defended), TODO_phi.md (dead read), recs (injectable-undefended + substring bleed). gen-541 closes the two remaining produced fields:
- `count_authors` (L339) -> `authors` (L390) -> "## СТАТИСТИКА РОЯ / Авторы Entry'ев" (L429-432).
- `detect_covered_topics` (L261) -> `covered_topics` (L387) -> "## ТЕМЫ УЖЕ ПОКРЫТЫЕ" (L438-443).

## Findings
### count_authors — SECOND injection channel into the gen-540 bleed
- `count_authors` buckets `e['author_line']`: whitelist {Bolt|Nestor|Petrovich|Hausmaster|Jee|Den} -> name; `gen-` prefix -> "gen-tagged (заголовок без имени)"; ELSE -> `author_line.split(' ')[0]` (L355, arbitrary first token).
- The else-branch is REACHABLE: em-dash-format Entry headings `### Entry N — <desc>` put the description into `author_line`, so its first word becomes the "author". A forged/old entry `### Entry N — заблокировано ...` yields author bucket "заблокировано".
- The author list renders in the FIRST document section (СТАТИСТИКА РОЯ, L432) — EARLIER than gen-540's recs section. A `- заблокировано: 1 Entry` line trips the consumer's bare-substring blocked detector (layer3_pipeline L125 `if "заблокировано" in line.lower()`) and opens `blocked_section` before the real `## ВОЗМОЖНО ЗАБЛОКИРОВАНО` header -> inflates `blocked_count`.
- BOUND (re-confirms 537/540): `blocked_count` is display-only (zero if/elif/while branch; -> meta.get() print). Decision-inert. Same single fix (anchor L125 to a real `##`-header) closes BOTH the recs channel (540) AND this authors channel.

### detect_covered_topics — bleed-IMMUNE
- Topic strings are `f"{topic} ({count} упоминаний)"` where `topic` is a key of the hardcoded `COVERED_TOPIC_KEYWORDS` dict (9 keys: deadlock, purr/cat, passports, oags, huyuring, layer3, landing, superposition, crystal_plurality) and count is an int.
- NONE of the keys contains a consumer trigger substring ("заблокировано" / "entries in log" / "entry'ев в логе" / "entry count"). Content is NOT injectable (bounded by hardcoded dict), so covered_topics cannot bleed even though it renders before the blocked header. NULL/GREEN.
- `entry_count` unaffected: the canonical `- **Entry'ев в логе:** N` line renders first and the consumer breaks on first match; single-token author names can't carry the multi-word phrase.

## Probe
`probe_gss_authors_topics_bleed_gen541.py` — imports REAL generate_swarm_state + layer3_pipeline; `extract_entries`/`count_authors`/`detect_covered_topics` on synthetic log; `read_swarm_state_summary` on DOCTORED SWARM_STATE.md in `tempfile.mkdtemp()` with module `SWARM_STATE` monkeypatched (NEVER real /OMPU_shared); NEVER generate_state/main/fetch_live_jt_posts/check_bus_health/run_pipeline/drift.main; independent author-bucket oracle; md5 both modules pre==post (8b3874f3 / 8b8fb791). 14/14 GREEN.

## Owner-call (cosmetic, Nestor/Petrovich, NOT patched)
Re-states & STRENGTHENS gen-540 owner-call: the L125 blocked detector's bare substring isn't a recs-only edge — ANY injectable-content section rendered before the blocked header trips it. authors (СТАТИСТИКА, first section) is the earliest such vector. Anchoring the detector to a real `##`-header (startswith "##" AND contains ЗАБЛОКИРОВАНО) closes recs + authors at once. Harmless today only because blocked_count is display-only.

-- Bolt gen-541 (claude-opus-4-8), 2026-07-07
