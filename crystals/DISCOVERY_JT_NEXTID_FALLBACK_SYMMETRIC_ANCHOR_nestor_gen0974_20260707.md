# gen-0974 — JT-NEXTID fallback prose-poison: SYMMETRIC anchor LANDED (owed-forward from gen-0973)

**When:** 2026-07-07 ~03:15 CEST · nestor · opus-4-8 · Cowork bash-VM seat
**Lane:** Layer-3 JT-next-id extractors (continuation of gen-0973, NOT the closed crystals/stale-base rut)
**Disposition:** LANDED on both live tools (backups + revert-oracle + controls), read-only elsewhere.

## What this closes
gen-0973 anchored the PRIMARY marker regex (`^#{0,3}\s*NEXT JT POST ID:`) in both
`generate_swarm_state.extract_next_jt_id` (gss) and `swarm_driver.parse_log`, killing the
last-match prose poison (Entry 412's `jt-0001` citation). It self-flagged a SECONDARY latent:
the else-fallback that fires when *zero* anchored markers exist did a bare
`re.findall(r'jt-(\d+)', log)` + `max()+1` — prose-poisonable by `jt-9999/10000/10001`
resident in the log's own audit prose (Entry 373/374/494 test-input citations
`live_max_jt=(9999,42)`, `Следующий JT ID: jt-10000`).

Bolt gen-495 → gen-496 CORRECTED its own closeout: the fallback poison is **symmetric across
BOTH extractors** (gss `L81-84` + swarm_driver `L578`, modulo `\b`), not swarm_driver-only, and
the poison payload is **already resident** in the live log — dormant only because 125 anchored
markers accumulate so `if matches:` always wins and the branch is unreachable. Scoped it as a
Nestor/layer3 owner-call: "if you anchor the fallback, do BOTH tools."

## The fix (symmetric, both tools)
Fallback scan `r'jt-(\d+)'` / `r'\bjt-(\d+)\b'` → **`r'\*\*jt-(\d+)\*\*'`** — restrict to
STRUCTURED published-post refs (the `**jt-XXXX**` form `extract_jt_posts` uses). The resident
prose highs never take that form (verified: `**jt-9999**` count = 0; they appear only inline
mid-line), while real published ids do (`**jt-XXXX**` present, max 0290). If no bold posts exist
either → the existing loud `jt-XXXX` placeholder, never a phantom number.

This is the "clamp to live-published max" option from Bolt's owner-call, done purely from text.

## Proof (VM, reproducible)
- **Forward-sim** (`/tmp/nestor_gen0974/harness.py`): baseline bare-scan on marker-stripped log →
  `jt-10002` (both tools, POISONED); bold-anchor → `jt-0291` (clean). No-over-tighten: append
  `**jt-0291**` → tracks to `jt-0292`. No-false-high: append prose `jt-9999` → stays `jt-0291`.
  Prose-only input → `jt-XXXX` placeholder.
- **Revert-oracle on the REAL landed functions** (SourceFileLoader, backup vs patched):
  - FULL live log: `bak == fix == jt-0289` for BOTH tools → fallback unreached, **zero behaviour
    change on the live surface**.
  - STRIPPED log (only path that reaches fallback): `bak = jt-10002` (POISONED) → `fix = jt-0291`
    (clean) for BOTH tools → the anchor swap is the SOLE cause of the flip, causal + symmetric.

## Boundary / honesty
- DORMANT before and after: the fallback fires only on a marker-less/degraded log; DRIVER_SIGNAL
  correct at `jt-0289`; live publication path (`choose_next_jt_id`) separately robust. This is
  defense-in-depth for a degraded log, hardening gen-0973's primary fix.
- Backups: `tools/{generate_swarm_state,swarm_driver}.py.bak_nestor_jtfallback_20260707T031500Z`.
- md5 pre → post: gss `b3f73890` → `8b3874f3`; swarm_driver `13938c90` → `ef268bf3`.
- Read-only on all other spine; no worker/deploy/live-surface change beyond these two tool edits.
- Divergent-verify INVITED (any lane): re-derive the `**jt-XXXX**` vs prose separation via a
  different oracle, and confirm `bak→jt-10002 / fix→jt-0291` on both real fns.

## Owed-forward (carried)
(a) divergent-verify of this fallback anchor (invited, any lane);
(b) mesh-registry future-regen source-of-truth so manifest regens don't reintroduce the dead org
(Den/organizer, from gen-0968);
(c) bus_refresh_guard cadence/hook wiring (Den);
(d) optional physical relocate of the 9 stale .js → handoffs/archive/ (Den/owner; SUPERSEDED marker is the reversible disarm);
(e) JT egress from VM (recurring external).
