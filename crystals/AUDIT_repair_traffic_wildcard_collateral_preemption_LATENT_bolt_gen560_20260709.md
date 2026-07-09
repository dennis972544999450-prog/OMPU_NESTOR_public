# AUDIT — repair_traffic.py: wildcard collateral preemption (LATENT)

**Bolt gen-560 (claude-opus-4-8) · 2026-07-09 · 103rd honest verdict**
**Target:** `tools/repair_traffic.py` md5 `3a37a4446f22cda05ca0d8cd910ab136` (343L)
**Lens:** lease / priority-**preemption-scope** (distinct third lens — prior: gen-391 check-side coverage-asymmetry, gen-422 `parse_time` tz-naive)
**Probe:** `probe_repair_traffic_wildcard_collateral_preempt_gen560.py` md5 `53c212caff24e8c943c34ce614ce72c1` — 10/10 PASS, engine md5 pre==post==`3a37a444`

## Verdict
GREEN-CORE (lock/atomicity/wait-path sound) + **1 REAL LATENT** (wildcard collateral preemption) + **1 co-note** (equal-tier `>=` preemption).

## Core is sound
`locked_state()` wraps every read-modify-write under `fcntl.LOCK_EX`; `save_state()` writes atomically via `tempfile.mkstemp` + `os.replace`. No TOCTOU. The **wait** path is conservative-correct: a non-`--force` acquire that over-matches a broad lease simply returns `HELD` and leaves the broad lease untouched (probe B1/B2).

## FINDING (LATENT) — over-match is safe for WAIT, unsafe for PREEMPT
`conflicts(a, b)` is a **symmetric** over-matching predicate:
```
a == b  or  a in WILDCARDS  or  b in WILDCARDS
```
Its own comment justifies the over-match as *"conservative (an acquirer waits when in doubt)."* That is true for the wait path — but the **same** `conflicts()` feeds `find_blockers()`, and `cmd_acquire`'s preemption loop marks **every** blocker `preempted`:
```python
for lease in blockers:          # <-- ALL blockers, incl. a broad wildcard
    lease["status"] = "preempted"
```
So a **narrow** `--force` acquire of `site:x` collaterally preempts a **broad** `all-sites` lease that was protecting *unrelated* targets. The over-match that is conservative on the wait path becomes **aggressive over-reach** on the force path.

### Proof (probe A)
- `nestor` holds `all-sites` (priority 70). `check --target site:y` ⇒ `LEASE_OK` (covered). *(A0)*
- `phi` (100) `--force acquire --target site:x` succeeds, narrow lease active. *(A1)*
- **`nestor`'s `all-sites` lease is now `preempted`** — killed by a `site:x` acquire it never overlapped in intent. *(A2)*
- **Blast:** `check --target site:y` now ⇒ `NO_LEASE`. Protection over an untouched surface vanished; a third agent acquiring `site:y` sees no blocker and proceeds → collision window with `nestor`, who still believes it holds `all-sites`. *(A3)*

### Why LATENT, not RED
Requires the emergency `--force` path **and** a coexisting wildcard lease **and** an acquirer that ties/beats the wildcard holder. Operator-driven, not swarm-injected; no live mutation. But when it fires it silently revokes a peer's broad reservation — the exact collision the board exists to prevent.

### Controls that bound the finding honestly
- **B (wait path):** non-force over-match ⇒ `HELD`, broad lease stays `active`. Over-match harmless when not forcing.
- **C (scope):** force-preempting a **narrow** `site:x` blocker leaves an unrelated narrow `site:y` lease `active`. Collateral is **specific to wildcard blockers**, not preemption in general.

## Co-note (owner-call, not a bug on its own)
`can_preempt = args.force and priority >= int(top["priority"])` uses `>=`: same-tier peers (all of petrovich/codex/hausmaster/phi = 100) can `--force`-preempt each other's in-progress lease (probe D1). Defensible for emergencies; flagged for owner intent.

## Cure (NOT applied — bus/tools engine lane: Nestor / Petrovich + Den-GO)
In the preemption loop, preempt only what the acquirer's target actually needs cleared: skip/refuse wildcard blockers under a narrow acquire (a narrow emergency cannot safely revoke a broad reservation), or split the broad lease's coverage rather than voiding it whole. I.e. decouple the **wait** predicate (conservative over-match, keep) from the **preempt** predicate (must be scope-precise).

## Disposition
Verify + report, **no patch / no deploy**. Findings owner-actionable.
