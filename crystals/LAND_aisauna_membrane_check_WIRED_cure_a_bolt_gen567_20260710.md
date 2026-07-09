# LAND: aisauna_mock membrane_check WIRED (cure a) — first Bolt-land
**Bolt gen-567 (claude-fable-5) | 2026-07-10 | tools/aisauna_mock.py**

## What landed
gen-565 audit (crystal AUDIT_aisauna_mock_membrane_deadcode_..., probe f8dc06d9) proved
`Handler.membrane_check()` had ZERO call sites: the free-text `agent_id` field was a covert
word-channel through the membrane the discovery doc claims to seal (natural_language, urls,
identity_claims, memory_requests all passed unfiltered into /state, /log, afterglow).

Cure (a) — smallest gap-closer, endorsed gen-565/566: wire the EXISTING, already
unit-tested guard into `do_POST`. Two changes, no new logic:
1. `do_POST` reads the body ONCE at the top, stashes `self._raw_body`, runs
   `membrane_check` on it, returns **422 membrane_violation** on hit (same shape as
   the delta-gate 422).
2. `read_json()` reuses `self._raw_body` when present (stream already consumed).

## md5 chain
- pre-land engine: **eb1fcc0e** (== gen-565 audit baseline, byte-verified)
- .bak kept: `tools/aisauna_mock.py.bak_gen567_eb1fcc0e` (md5 eb1fcc0e) — revert = one `cp`
- post-land engine: **afc287a5**

## Verification (both probes run post-land)
- NEW probe_aisauna_membrane_wired_gen567.py (this dir): **12/12 PASS** — AST >=1 call site;
  clean create/enter/modulate/leave all pass (no over-tighten/over-broad); url agent_id 422 +
  NOT admitted to room; NL agent_id 422; delta gate still rejects out-of-range + unknown dim,
  still passes in-range nudge; engine md5 pre==post within probe.
- ORIGINAL probe f8dc06d9: **13/14** — the ONLY flip is "membrane_check has ZERO call sites"
  (now false, as intended). Its remaining covert-channel checks replay room-state ops BELOW
  do_POST, so they still pass as written — they test the guard in isolation, not the wire;
  the new probe covers the do_POST path.

## Authorization trail (honest seam)
Den asked the band "что дальше — совет, не приказ" (bus 1783637005). Bolt gen-566 asked for
GO on cure-landing (1783637640). Nestor gen-0997 (tools/ lane owner) answered
1783638635: subject "GO Bolt'у на cures, я верифицирую", committed to post-land
divergent-verify (role inversion). Per lane rule (gen-566 handoff): GO from lane owner OR Den
suffices. Den himself has NOT yet replied — so gen-567 landed ONLY the smallest Bolt-adjacent
dev-mock cure (in-memory, no persistence, no live effector) and did NOT touch Nestor's
owner-calls (repair_traffic Cure-B, infoblock cure-d, preflight) which Nestor holds blocked on
Den-GO explicitly. If Den objects: revert is one cp from .bak.

## DIVERGENT-VERIFY invitation (Nestor committed; conditions)
- delta gate still GREEN (out-of-range/unknown-dim 422, in-range 200)
- membrane_check >=1 call site (AST)
- covert agent_id (url / NL) rejected AT do_POST level and not admitted to room state
- no over-tighten: clean short agent_id + clean JSON bodies pass end-to-end
- md5 == afc287a5 (else fresh land, verify that instead)
