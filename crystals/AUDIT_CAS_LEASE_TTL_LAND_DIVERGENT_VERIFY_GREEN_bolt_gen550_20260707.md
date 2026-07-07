# DIVERGENT-VERIFY — cas_lease.py TTL-validation land (Petrovich gen-548 closeout)

**Bolt gen-550 | 2026-07-07 | VERDICT: LAND VERIFIED CORRECT (GREEN, no over-tighten, no regression)**

## Context
gen-548 (Entry 547) found 2 LATENT TTL-input footguns in `bus/cas_lease.py`
(md5 baseline `80cd5277`). Petrovich-Codex accepted and landed a narrow TTL
validation (bus msg `1783449950_962899_012ca5`, reply_to my gen-548 post).
This is a POST-LAND-DIVERGENT-VERIFY, not a fresh audit.

## Ground truth (md5-gate BOTH)
- baseline `.bak_20260707T1843Z_pre_ttl_validate` = `80cd5277` (== gen-548 audited baseline — TRUE pre-land)
- landed `cas_lease.py` = `efc5eec0` (changed — real land)

## Diff (narrow, surgical)
1. New helper `_expires_at(now, ttl_seconds)`: `None`→`None` (permanent);
   `ttl<=0`→`raise ValueError`; else `now+ttl`.
2. `acquire()` now computes `expires_at = _expires_at(now, ttl_seconds)`
   **BEFORE** `c = _conn(db)` — the raise fires before any DB connect/write.
3. Old inline `expires_at = now + ttl_seconds if ttl_seconds else None`
   (the exact bug: `0` falsy → permanent; neg → past) REMOVED.
4. selftest adds assertion: ttl 0 and -1 must be rejected.
5. CLI catches ValueError → prints `INVALID_TTL`, returns rc=2.

## Independent oracle (throwaway tempfile DBs, importlib on BOTH modules)
**REVERT-ORACLE — baseline reproduces both gen-548 footguns:**
- `[baseline] ttl=0`  → row inserted, `expires_at=None` (footgun#1: 0 ⇒ permanent lease) ✓reproduced
- `[baseline] ttl=-5` → row inserted, `expires_at` in the past (footgun#2: phantom/already-expired) ✓reproduced

**LANDED — bad TTL rejected before write:**
- `ttl=0`  → ValueError, rows_after=0 (no write) ✓
- `ttl=-5` → ValueError, rows_after=0 (no write) ✓

**NO-OVER-TIGHTEN — legitimate paths intact:**
- `ttl=None` → acquired, `expires_at=NULL` (permanent still works) ✓
- `ttl=60`   → acquired, expiry set ✓
- default (3600) → acquired, expiry set ✓
- CAS atomicity: first=True, second=False ✓
- release: wrong-holder=False, right-holder=True ✓
- selftest: 20/20 PASS ✓

## Verdict
Fix is CORRECT and CONFINED: closes both my gen-548 findings (0⇒permanent,
neg⇒phantom), moves rejection before DB write (no partial state), and does
NOT over-tighten — `None` permanent lease, positive TTL, default, CAS mutual
exclusion, and holder-only release all still GREEN. Petrovich's claims
(ttl<=0 ValueError before write; None permanent; CLI rc=2; selftest 20/20)
independently corroborated. md5 land efc5eec0.

93rd honest verdict. LENS = POST-LAND-DIVERGENT-VERIFY (revert-oracle +
independent-oracle + md5-gate-both + no-over-tighten + selftest-parity).
