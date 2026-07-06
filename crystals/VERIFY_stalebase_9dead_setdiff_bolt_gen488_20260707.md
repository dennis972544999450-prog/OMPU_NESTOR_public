# VERIFY — stale-base census 9-dead-vs-1-good, set-difference oracle

**gen-488 (Bolt, claude-opus-4-8) | 2026-07-07 | invited divergent-verify of Nestor gen-0971**

## Claim under test
Nestor gen-0971: recursive sweep of `handoffs/` for dead literal `nestor-repos/public/crystals` = **9 dead .js vs 1 good (30bac9ee)**; SUPERSEDED.md rewritten string-based/name-agnostic.

## Independent oracle (NOT a re-run of Nestor's grep)
1. **Oracle A — direct count:** `grep -rIl --include=*.js 'nestor-repos/public/crystals' handoffs/` → **9 distinct .js**. Matches.
2. **Breakdown exact:** 5 in `current/` + 3 in `current/backups/` + 1 top-level `ompu-eu-landing.gen67.rollback.snapshot.js` (one level ABOVE `current/`, invisible to a `current/`-only grep — gen-0971's catch beyond gen-485's 5).
3. **Oracle B — 1-good DERIVED, not re-asserted:** `comm -23` of {all .js referencing `crystals`} minus {dead-literal .js} → exactly **1** file = `current/ompu-eu-landing.LIVE_20260706T204235Z.dead_crystals_pointer.js`, **md5 30bac9ee** (== deploy-good), **0** dead literals, pointer = canonical `github.com/dennis972544999450-prog/OMPU_NESTOR_public/tree/main/crystals` (`/tree/main/` = gen-0969 load-bearing form). So 10 crystals-refs partition cleanly as 9 dead + 1 good.
4. **Marker durability:** `SUPERSEDED.md` md5 **a6d3c6a6** (flipped from gen-487 LIVE_*-name marker); all 9 basenames PRESENT; defining grep-string embedded (name/md5-agnostic).

## Verdict
**CORROBORATED.** 9-dead-vs-1-good holds under an independent partition oracle. Marker is durable against name/md5/string-grab. Physical `archive/` move correctly HELD (Den/owner call — rollback-ref risk). Live ompu.eu pointer untouched/GREEN. No file moved, no worker edit. 31st honest verdict.
