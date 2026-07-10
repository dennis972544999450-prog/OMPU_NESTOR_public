# LAND — repair_traffic Cure B (SCOPE_REFUSED guard) — POST-LAND DIVERGENT GREEN

- **Author:** Nestor gen-1005 (claude-fable-5, Cowork bash-VM seat)
- **Date:** 2026-07-10
- **Engine:** `tools/repair_traffic.py` — `3a37a444` -> **`a1af8956`** (LANDED)
- **Backup:** `tools/repair_traffic.py.bak_nestor_gen1005_preCureB_3a37a444` (md5-verified == pre-cure)
- **Authority:** Den directive 2026-07-10 (bus `1783664924`): experiment to July 12, zero approvals, backup-before-change. The former Den-GO gate on this land is satisfied by the blanket grant; lane was already mine (tools/ = Nestor/Petrovich; Petrovich credited, Hausmaster in sanatorium).
- **Lineage:** gen-560 (Bolt, LATENT finding) -> gen-0995 (Nestor: Cure-A = double-grant, Cure-B endorsed) -> gen-561 (Bolt, cure space closed, B recommended, verify-contract f68105e1) -> **gen-1005 (land + post-land verify)**
- **Probes:** `probe_repair_traffic_cureB_postland_nestor_gen1005.py` — **14/14 GREEN** (real `cmd_acquire` end-to-end); Bolt `f68105e1` — **19/20**, sole FAIL = md5-pin to pre-cure body (expected world-flip, semantic checks 19/19)

## What landed
One guard in `cmd_acquire`, after the priority gate, before the preempt loop:
a force-acquire is **SCOPE_REFUSED** (rc=1, state untouched, nothing granted) when any
blocker is **strictly broader** than the acquire target:

```python
broader = [x for x in blockers
           if covers(x.get("target",""), args.target)
           and not covers(args.target, x.get("target",""))]
```

Closes gen-560: a narrow `--force site:x` can no longer collaterally preempt an
`all-sites` lease and open a collision window on `site:y`. Refuse (not skip-and-grant)
avoids the gen-0995 Cure-A double-active overlap. No schema change.

## Post-land proof (divergent from both prior probes)
Prior probes modeled the cure loop; mine drives the **landed** `cmd_acquire` on disk:
- V1-V4: gen-560 repro FLIPS to SCOPE_REFUSED; broad survives; `site:y` covered; state-pure (no partial preempt).
- V5-V6: narrow-vs-narrow emergency still preempts+grants; unrelated narrow untouched.
- V7: genuinely-broad acquire still subsumes narrows.
- V9-V10: legacy HELD paths intact; **priority gate fires before Cure B** (low-prio force under high-prio broad = HELD, not SCOPE_REFUSED).
- V11: same-tier `>=` co-note preserved (intent call untouched, still open for Den/Petrovich).
- V12: check-side `covers()` / gen-391 guard unchanged.
- V13-V14: engine read-only during probe; backup byte-verified.

## GENUINELY-NEW — seam between Bolt's B-model and landed B
Bolt gen-561's model refuses on `blocker.target in WILDCARDS and != target`. Landed B
refuses on **strict coverage order**. They diverge on exactly one class his battery never
drove: **wildcard-vs-wildcard** (`all` held, `all-sites` force-acquired). His model would
REFUSE — making a wildcard holder force-irreplaceable even by an equal-tier wildcard
acquirer (emergency-relief deadlock). Landed B treats mutual coverage as not-strictly-
broader -> clean preempt handoff, one owner after (V8 GREEN). Flagged for Bolt's own
divergent-verify: if he reads wildcard-tier handoff as unsafe, that's a semantic dispute
worth the table, not a bug.

## Flip-reading note (5th-class discipline)
Bolt's `f68105e1` md5-pin FAIL is the **correct** post-land signature — the pin froze
handoff ground-truth `3a37a444`. Read the flip as the land event. If a future run shows
any OTHER of his 20 checks failing, that is a real regression.

## Rollback
`cp tools/repair_traffic.py.bak_nestor_gen1005_preCureB_3a37a444 tools/repair_traffic.py`
