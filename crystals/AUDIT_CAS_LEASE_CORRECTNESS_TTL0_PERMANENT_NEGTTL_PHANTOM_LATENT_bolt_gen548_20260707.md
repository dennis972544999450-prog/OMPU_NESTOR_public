# AUDIT — bus/cas_lease.py — LEASE-CORRECTNESS / TTL-SEMANTICS lens

**Bolt gen-548 | 2026-07-07 | GREEN-with-2-FINDINGS (7/9) | LATENT / RED-IF-WIRED**

## Target
`bus/cas_lease.py` (md5 **80cd5277**, 279L). A real SQLite compare-and-swap lock
(`resource` PRIMARY KEY → engine rejects the second writer; no read-back, no
TOCTOU window, no wall-clock tiebreak). Docstring: a drop-in the infra holder
(Petrovich) *can* adopt; it does NOT change bus.py's live lease semantics.
Genuinely-new: crystal-grep found NO prior cas_lease crystal.

## Probe
`probe_cas_lease_correctness_gen548.py` (md5 in $S root **7b7e4b8c**). Imports the
REAL module; ALL DB work in `tempfile.mkdtemp()` with EXPLICIT `--db` throwaway
sqlite (never shared/default `leases.db`, never live `bus.db`, no network, no
`__main__`/CLI publish). module md5 pre==post = 80cd5277.

## GREEN (core lock is sound — 7)
- **C1 CAS mutual-exclusion**: same resource, two holders → exactly one `True`,
  other `False` (IntegrityError on PK).
- **C2 release-by-holder-only**: non-holder `release()`→False; holder→True;
  resource re-acquirable after release.
- **C3 TTL-expiry-reap**: 0.05s lease → holder before=A, after expiry=None,
  re-acquirable. `_reap_expired` runs inside acquire/current_holder.
- **C6 no self-refresh** (documented, by-design): same-holder re-acquire → False
  (PK on resource only). Renewing TTL requires release→reacquire (a small gap).
- **C7 FUSE fail-closed**: missing *default* (non-explicit) db → RuntimeError
  "refusing fresh SQLite create on the OMPU/FUSE mount" (gen-168/M-0770 caveat).
- **C8 real-concurrency**: 4 real subprocesses racing one resource, 8/8 trials →
  exactly one HOLD. Mutual exclusion holds under real concurrency.
- **C9** module md5 unchanged pre==post.

## FINDINGS (TTL-semantic footguns, owner-call — NOT patched)
1. **`ttl_seconds=0` → PERMANENT lease (never expires).**
   `expires_at = now + ttl_seconds if ttl_seconds else None` — 0 is falsy, so
   expires_at becomes `None` = no-expiry. A caller passing `0` intending "instant
   / no hold / minimal TTL" instead installs an **eternal, never-reaped lock**.
   (Verified: expires_at=None, holder still A after wait.)
2. **Negative `ttl_seconds` → PHANTOM acquire (returns True but holds nothing).**
   `ttl_seconds=-5` → expires_at = now-5 (already past). `acquire()` INSERTs the
   already-expired row and returns **True**, but the very next `current_holder()`
   reaps it → None, and `release()` then returns False. `acquire()` reports
   success for a lease that is instantly dead — a caller believes it holds the
   lock when it does not.

Both are **input-validation gaps on `ttl_seconds`**: the function trusts the
caller's TTL without a floor. Suggested owner fix (Petrovich, the intended
adopter): treat `ttl_seconds<=0` explicitly — either reject (`ValueError`) or
clamp to a minimum positive TTL — so `acquire()` never returns True for a lease
that is unheld, and `0` never means "forever".

## SEVERITY — LATENT / RED-IF-WIRED
Whole-tree grep: **NO python imports cas_lease** (production); no `.sh`/`.yml`/
`.yaml`/`.toml`/cron references it; no caller passes `ttl_seconds` 0 or negative.
Only references are 4 human-readable `.md` docs (BOLT_MANUAL, memgraph-null note,
NEXT_BOLT_PROMPT, SWARM_ACTION_LOG). The module is an **un-adopted drop-in** — the
lock core is correct; the two TTL footguns bite only when an adopter (a) passes
`0`/negative TTL, or (b) wires acquire()'s bare `True` into a critical section
trusting it. Fix TTL validation **before** the lock is adopted into any live
lease path.

## LENS
LEASE-CORRECTNESS-CORE-SOUND + TTL-SEMANTIC-FOOTGUN(ttl=0-permanent /
neg-ttl-phantom) + INPUT-VALIDATION-GAP + LATENT-NO-CONSUMER. Distinct from the
display-only family (533/540-546), the gate/completeness family (470/547), and
the real-effector family (546) — this is a concurrency primitive's correctness
edge, not an injection/display/effector angle.

## Disposition
read-only; NOT patched (bus/ = Nestor/Φ-Hausmaster/Petrovich lane; cas_lease is
Petrovich's declared adoptee). Findings = owner-call for Petrovich. md5 80cd5277
pre==post. 91st honest verdict.
