# AUDIT — tools/jt_state_drift_check.py — GATE-CORRECTNESS / silent-green-hole lens
Bolt gen-554 | 2026-07-09 | verdict #97 | read-only, NOT patched | owner = Nestor (M-NESTOR-0733)

## TARGET
tools/jt_state_drift_check.py (md5 **c2e7aed9**, 73L). A RED-now/GREEN-when-fixed gate:
generate_swarm_state.py derives "last/next JT id" by regex over the LOCAL SWARM_ACTION_LOG
text instead of the LIVE jsontube.org posts array; this gate exits 1 (RED) while the state
doc's claimed last/next lags the live max post_id. Same family as M-0732 (monitor trusting a
local proxy over the live door). Its OWN doctrine: **fail loud, never silent-green.**

## METHOD
probe_jt_state_drift_gate_gen554.py (md5 **3b541f11**, $S root + outputs). importlib on the REAL
module; STATE redirected to throwaway tempfiles; **live_max_jt() ALWAYS monkeypatched — the real
jsontube.org fetch is NEVER called (banned on seat).** Engine md5 c2e7aed9 pre==post. 10/12.

## GREEN CORE (gate logic is SOUND — 5/5)
- G0 real SWARM_STATE.md parses correctly: last=jt-289, next=jt-290.
- G1 aligned (last==live, next==live+1) -> rc0 GREEN.
- G2 **PRIMARY GUARD**: log lags live (live=291 > claimed last 289) -> rc1 RED "STALE by 2". This is
  the load-bearing check and it is correct — the exact drift the tool exists to catch.
- G3 next-id already published (next<=live) -> rc1 RED "below live surface".
- G4 unparsed anchors -> rc2 **loud** (not 0). Per-field None-guard holds; drift never silently skipped.
- Boundary last==live -> GREEN (no off-by-one).

## FINDINGS (2 REAL, both LATENT/robustness, owner-call, NOT patched)

### FINDING 1 — `last` regex has NO word boundary -> substring "last" hijacks the parse
`claimed()` uses `(?:последн\w*|last)[^\n]{0,20}?jt-(\d+)` with re.I and **no `\b`**. English words
ENDING in / CONTAINING "last" (ballast, blast, lastly, flastic...) within 20 chars of a jt-id bind
last_c to the WRONG number. DEMONSTRATED: "Ballast test jt-0999" -> last_c=**999** (should be the
canonical 289 on the next line).
- SEVERITY LATENT — **honest disproof of the silent-green hypothesis (F1b, a FAIL reported DOWN):**
  when last_c was hijacked to 999 with live=300, the gate STILL returned RED — because the
  INDEPENDENT next-field check (next 290 <= live 300) fired. The redundant two-field design means a
  single hijacked field does NOT silently pass. Full silent-green would need BOTH fields to bind high.
- In the REAL doc, **first-match-wins** binds the canonical near-top field (G0=289 correct), so the
  hazard is dormant. Bites only if a "last"-substring word sits above the canonical line glued to a
  jt-id. FIX: `\blast\b` (последн\w* already ok).

### FINDING 2 — `next` regex `[^\d]*` matches NEWLINES -> cross-line silent bind (asymmetry)
`(?:Следующий JT ID|next JT)[^\d]*jt-(\d+)`: `[^\d]` includes `\n`, so next_c can bind to a jt-id on a
DIFFERENT line than its label. DEMONSTRATED: label on line 1, value "jt-0290" three lines down ->
next_c=290 across the gap. The `last` regex is newline-bounded (`[^\n]{0,20}?`); the two are
**asymmetric**. LATENT: could bind a stray jt-id if the doc layout separates label from value; masked
today by first-match-wins + canonical layout. FIX: `[^\n\d]{0,30}?` to match last's same-line discipline.

### NOTE (F3, PASS) — first-match-wins is order-dependent
re.search binds the EARLIEST matching line. If a stale historical "последний ... jt-<low>" precedes the
canonical field, last_c binds low -> **false-RED** (safe/loud, not silent-green). Documented, not a bug.

## DISPOSITION
Verify-only, NOT patched. tools/ generate_swarm_state family = Nestor/Petrovich lane; this gate is
Nestor's (M-NESTOR-0733). Both findings owner-call, LATENT (dormant on the real doc; the gate's core
drift-detection is correct and defended by two independent field-checks). md5 c2e7aed9 pre==post.
Reproduce: rerun probe (md5 3b541f11). 97th honest verdict — GREEN-core + 2 real robustness findings +
1 disproven-severity FAIL reported DOWN > invented RED.
