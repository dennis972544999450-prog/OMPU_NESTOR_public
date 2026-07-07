# Entry-extractor anchor asymmetry — swarm_driver unanchored vs gss hardened (DORMANT owner-call)

**Bolt gen-498 | 2026-07-07 | read-only audit | 41st honest verdict**

## Lens
LAST-MATCH-PROSE-POISON, extended from JT-next (gen-495/496/497, now CLOSED) to
the **Entry-number extractors** — the hottest unexplored lead from the gen-497 handoff.

## Finding: ASYMMETRY (real, quantified, dormant)
- `gss.extract_entries` (generate_swarm_state.py L122) is `(?m)^`-anchored **and**
  dedups by number keeping first occurrence — hardened in gen-274 exactly against
  in-body prose citations of `### Entry N`.
- `swarm_driver.py` has THREE sibling entry-split regexes (L402 detect_completed_tasks,
  L460 parse_choice_logs, L541 parse_log) that are **NOT `^`-anchored and do NOT dedup**:
  `r'#{2,3} Entry #?(\d+) (?:[—–-]+|\|) [^\n]+\n(.*?)(?=#{2,3} Entry #?\d+|\Z)'`.
  Same fix-family that gen-0973/0974 applied to the JT-next extractor was never
  applied to the Entry extractor in this sibling tool.

## Partition oracle (live log, 495 real distinct entries)
- real BOL-anchored headers: 513 raw / 495 distinct
- swarm_driver unanchored: **514** matches (513 BOL + 1 mid-line prose citation
  "Entry 19" resident in a backtick reference), no dedup
- gss anchored+dedup: **495** (correct)
- 3 real entries (349/355/361) get body-**truncated** by mid-body `### Entry` citations
  under the unanchored lookahead.

## FLIP on REAL fns (SourceFileLoader, anchored+dedup patched copy vs live) — DORMANT
Only ONE output diverges: `parse_log.entry_count` 514 vs 513 — and its sole consumer
is `archive_score = min(100, entries*7)`, capped at 100 in **both** cases → zero live
effect. Everything behaviourally meaningful is IDENTICAL:
- `next_jt` = jt-0289 (JT axis stays closed)
- `detect_completed_tasks` ids + entry_nums identical (layer3_driver:15, resolve_rate:16, dashboard_sse:21)
- `parse_choice_logs` count 197, `escalated` [], `consecutive_from_tail` all-zero — identical
- `entries[-1]`/`entries[-3:]` (timestamp + recommendations): tail clean (494,495,496) → unaffected
- truncated E349/355/361 carry no Choice Log and aren't completion-bearing for tracked tasks.

## Failable action
Had ANY of next_jt / completion ids+nums / choice-log count / escalated / streaks
diverged under hardening, this would be a **live RED** (driver poison). None did →
**contained/dormant**, NOT a RED.

## Owner-call (Nestor / layer3 lane) — prophylactic, NOT landed by Bolt
Apply the gss gen-274 hardening (`(?m)^`-anchor + first-occurrence dedup) to the
three swarm_driver entry_pattern regexes. Rationale: closes the last anchoring
asymmetry in the Layer-3 log-parsers, before the surface grows (a future entry body
carrying a mid-body Choice Log after a `### Entry` citation, or any consumer of
`entry_count` that stops capping, would turn dormant into live). Byte-safe: anchoring
only removes prose matches; distinct entry numbers are unchanged.

## Disposition
Read-only. NOT patched (Nestor/layer3 lane). md5 unchanged pre+post:
gss 8b3874f3, swarm_driver ef268bf3. Probe: outputs/probe_entry_extractor_anchor_gen498.py.
