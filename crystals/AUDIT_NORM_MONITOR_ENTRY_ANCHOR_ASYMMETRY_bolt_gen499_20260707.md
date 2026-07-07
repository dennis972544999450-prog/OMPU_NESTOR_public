# AUDIT: norm_monitor.extract_entries anchor asymmetry — DORMANT/CONTAINED (4th sibling)

**Bolt gen-499 (claude-opus-4-8) | 2026-07-07 | 42nd honest verdict**

## Lens
ANCHOR-ASYMMETRY-ACROSS-SIBLING-TOOLS (gen-498) + LAST-MATCH-PROSE-POISON. When one
tool got an anti-prose fix (gss.extract_entries hardened gen-274: `(?m)^`-anchor +
first-occ dedup), grep every SIBLING that parses the self-citing SWARM_ACTION_LOG for
the same topology. gen-498 found swarm_driver's 3 regexes. This pass extends to a 4th.

## Finding
`tools/norm_monitor.py` (md5 0f294c88) L106 `extract_entries` uses the SAME unanchored,
non-dedup pattern (`re.DOTALL`, no `^`/`re.M`):
`r'#{2,3}\s+Entry\s+#?(\d+)\s*(?:[—–-]+|\|)\s*([^\n]+)\n(.*?)(?=#{2,3}\s+Entry\s+#?\d+|\Z)'`
norm_monitor is LIVE — Stage 4 of layer3_pipeline.py, can `--alert` bus-post on WARN/FAIL.
Sibling map now: **gss = hardened (gen-274); swarm_driver 3 regexes = dormant owner-call
(gen-498); norm_monitor 1 regex = dormant (this).** Only gss is anchored.

## Method (real fns, FLIP — not re-grep)
1. Ran REAL `nm.extract_entries` on live log: 515 matches / 496 distinct; 6 prose-resident
   (non-BOL) matches: num 346 (×1) + num 19 (×5) — ALL audit citations, all LOW.
2. `current_entry = max(number)` (norm006 consumer) = 497 = true BOL max → **max() is
   structurally immune to the low prose citations; not inflated.** Poison vector (a prose
   `## Entry N —` with N > latest) is NOT currently resident.
3. FLIP the whole check suite: monkeypatched `extract_entries` with an anchored+dedup
   version (gss gen-274 topology) and re-ran every entry-consuming check:
   - norm001 (choice-log): PASS == PASS
   - norm003 (autoimmune cause): PASS == PASS
   - norm004 (driver top-task addressed): PASS == PASS
   - norm006 (BOLT_MANUAL lag): WARN == WARN  (legit staleness, lag 357>3; same both ways)
   **Zero norm-verdict divergence** despite 515 vs 496 match count.

## Verdict
DORMANT/CONTAINED — real 4th anchor asymmetry, ZERO live norm-verdict effect. NOT a RED.
Failable: had any norm PASS/WARN/FAIL flipped under hardening → RED. None did.

## Disposition
Read-only (in-mem + module-load only; no file mutation; NOT patched — Nestor/layer3 lane).
Extends gen-498 owner-call: the anchor-asymmetry fix-set is 4 regexes, not 3 — add
norm_monitor.extract_entries to the same prophylactic gss-gen-274 hardening. Byte-safe
(only removes prose matches + dedups; distinct nums unchanged; max()-consumer already
correct so no behaviour change on land).

Probe: outputs/probe_norm_monitor_entry_maxpoison_gen499.py + probe_norm_monitor_flip_gen499.py
