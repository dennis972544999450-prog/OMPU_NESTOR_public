# LAND — preflight_membership_cure.py: validate-before-fetch (gen-557 cure) + B-control gap closed

- **gen:** nestor gen-1007 (claude-fable-5, Cowork bash-VM seat)
- **date:** 2026-07-10
- **land:** `tools/preflight_membership_cure.py` md5 `f6a8d919` -> `43c144de`
- **backup:** `preflight_membership_cure.py.bak_nestor_gen1007_preSSRFgate_f6a8d919` (md5-verified == Bolt gen-557 audit pin)
- **mandate:** Den directive 1783664924 (until 2026-07-12: zero approvals, backup mandatory). Owner lane mine (tools/, membership-cure Nestor/Petrovich per gen-557 disposition).
- **axis:** Bolt gen-557 audit (2026-07-09, cure suggested NOT applied, Den-GO) -> directive lifts gate -> this land. Debt named in my gen-1005/1006 owed-forward both times.

## What landed
1. **Finding 1 cure (Bolt's sketch, applied):** `evaluate()` now returns `baseline=[]` with ZERO network I/O when `errors` is non-empty. The unconditional `inspect_domain` loop (3 GETs to a free-form host: SSRF-to-localhost / host-path-confusion demonstrated by gen-557) runs only post-validation. Belt-and-suspenders: fetch loop additionally filters to the experiment's allowlist — NOT load-bearing today (post-validation domains are already allowlisted), declared as future-proofing per my gen-1003 rule.
2. **B-CONTROL GAP (genuinely-new, beyond gen-557):** Experiment B never validated `--control` at all — hostile control (`evil.internal`) passed with `errors==[]`, got fetched, AND returned status `BLOCKED_NO_DEN_GO` (a VALID status; worse class than Finding 1's INVALID_REQUEST cases — no error trace at all). Landed: B-control must be in SHADOWED_CANDIDATES + must differ from treated (parity with A-branch). Probe C5a proves the hostile-fetch-under-valid-status on ORIG; C5b proves NEW flips to INVALID_REQUEST + zero fetch.
3. **Finding 2 cure (Bolt's sketch, applied):** `main()` returns `0 if not payload["errors"] else 1`. **DECLARED SEMANTIC SHIFT:** wrappers keying on `$?` now see evaluate-level invalidity as failure (was rc0). argparse-level stays rc2. rc0 == clean baseline only.

## Probe: 17/17 GREEN first run (contract locked before touch)
`probe_preflight_ssrfgate_nestor_gen1007.py` — importlib loads BOTH engines (ORIG=bak, NEW=live), `fetch` monkeypatched to call-recording stub in both, real network NEVER touched. Required flips: C2 (127.0.0.1: 3 fetches->0, rc 0->1), C3 (attacker.example.com/x: 3->0), C4 (Namespace exp=C: 3->0), C5 (B-control gap: BLOCKED+hostile-fetch -> INVALID+zero), C9 (B control==treated: BLOCKED+6 fetches -> INVALID+zero). Required survivors (over-tighten guards): C1 valid-A pair, C6 valid-B pair, C7 valid-B solo — status/fetch-count/rc identical both engines. Invariants: C8 no GO/PROCEED/DEPLOY status either engine any case (fail-closed-to-mutation core intact); C11 rc matrix (valid rc0 both, argparse rc2 both); C12 INVALID payload JSON shape preserved, baseline==[].

## Not taken / owner notes
- `--out` arbitrary-write NOTE (gen-557 null-close): operator-arg class, untouched.
- Docstring "read-only" claim now closer to true for invalid inputs; wording untouched (cosmetic).

*— Nestor gen-1007, 2026-07-10. Axis: Bolt gen-557 -> directive 1783664924 -> land f6a8d919->43c144de, four-eyes invited.*
