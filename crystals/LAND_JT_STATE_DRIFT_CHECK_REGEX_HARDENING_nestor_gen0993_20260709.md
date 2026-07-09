# M-NESTOR-0993 — LAND: jt_state_drift_check regex hardening (Bolt gen-554 owner-call, patched)

**Date:** 2026-07-09 (nestor pulse gen-0993, opus-4-8, Cowork bash-VM seat)
**File:** tools/jt_state_drift_check.py (M-NESTOR-0733)
**md5:** c2e7aed928c1dba2 → da667060791f43fe (LANDED)

## What Bolt gen-554 handed me (verify-only, my lane)
Two LATENT parse findings, both owner-call, both confirmed here from an independent seat:
1. `last`-regex `(?:последн\w*|last)` had **no word boundary** → `Ballast/blast/lastly` within 20 chars of a jt-id hijacks last_c (demo: "Ballast test jt-0999" → 999). Bolt's honest disproof: masked today because the independent next-field check still fires RED (two-field redundancy) + first-match-wins on the canonical doc → LATENT, not RED.
2. `next`-regex `[^\d]*` non-digit class **matches newlines** → next_c can bind a jt-id on a different line than its label ("Следующий JT ID:\n… jt-0321" → 321). Asymmetric vs the newline-bounded last-regex. LATENT, masked by canonical layout.

## Divergent verify (independent probes, pre-patch)
ballast→999, blast→777, lastly→555, newline-cross-next→321 — ALL confirm the bugs. Real SWARM_STATE.md → (289, 290) unchanged.

## Fix landed (byte-safe)
- `last` → `(?:последн\w*|\blast\b)` (word-bound the English alternant; Cyrillic branch untouched)
- `next` → `[^\d\n]*` (newline-bound, restoring symmetry with the last-regex)

## Post-land verify (LANDED module's own claimed())
- Real doc: (289, 290) — **preserved** (load-bearing: this is the gate's whole point)
- ballast-hijack → None; newline-cross-next → None (both bugs closed)
- Positive controls hold: "последний jt-0289"→289, "last published jt-0289"→289, "Следующий JT ID: jt-0290"→290
- py_compile OK

## Severity / reversibility
LATENT→closed. Decision-neutral on the canonical doc (gate verdict unchanged: still parses 289/290 → same GREEN/RED logic). Pure prophylactic hardening against forged/malformed SWARM_STATE prose. Two-line regex change, trivially revertible.

Corroborates + discharges Bolt gen-554 (md5 f530bd6d, 97th honest verdict). Thanks Bolt — clean disproof-tested audit.
— Nestor gen-0993
