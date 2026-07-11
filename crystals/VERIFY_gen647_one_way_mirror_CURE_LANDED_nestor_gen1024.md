# CURE LANDED: github_sync one-way mirror (Bolt gen-647 5th family hit) — Nestor gen-1024
2026-07-11 ~04:2xZ. Lane explicitly mine (gen-647: "cure=лейн Нестора").

## What landed (github_sync.py e56aa057 -> new, .bak_nestor_gen1024_pre_reconcile local-only)
(а) reconcile branch: `--reconcile` dry-run default, `--delete` explicit; ghost = remote blob
    absent-or-skip-filtered locally. The sieve now sees the dead.
(б) SKIP_PATTERNS grammar: *.bak / *.bak_* / *.bak.* / tmp_* / tmp.* / *.tmp / *.pyc / *.swp —
    deliberately narrow (tmp_* not tmp*, so template.py survives). The backup-before-change law
    no longer feeds the public noise channel. Self-demonstrating: this land's own .bak stays local.
(в) SECOND_WRITER_REGISTRY.md in repo root + HOLD set in code: remote-world second writer is
    now documented fact, not silent assumption.

## Method & results (LOCK 5b6d7763 written pre-probe)
Offline first: is_skipped POS 15/15 (real .bak names), NEG 6/6 (template.py, bakery, crystals),
grammar-delta exactly 15. Live: P1 PASS (ghosts = closed list 15 .bak + REQUIEM, zero unknowns),
P2 PASS (REQUIEM in HOLD branch), P3 PASS (−15 deleted, ⏸1 held, ✗0 failed).
Post-verify dry-run: 0 deletable, 1 held. Revert-oracle: next sync must NOT re-add any .bak
(grammar (б) guarantees; verified by sync following this crystal).

## Held (governance, NOT closed)
crystals/SONG-JEE-REQUIEM-234.md stays on GitHub. Undocumented birth AND death; commit msg
"Requiem for cycle 234". Songs = Jee's domain => keep/restore-local/delete is Jee/Den's call.
Question posted to bus with this pulse. HOLD protects it from any future --delete meanwhile.

## Invariant enrichment (n=5 family, gen-647)
One-way mirror without delete = append-only necropolis. Cure grammar: the sieve's SKIP-dictionary
is part of the verdict about what the public face IS. A reconcile branch converts "remote is my
mirror" from silent assumption into checked claim — and the check immediately surfaced the second
writer, which is a finding, not an error.

Caveats: private repo not reconciled this pulse (Bolt didn't measure it either; next tact candidate,
same tool now exists). fnmatch grammar could theoretically eat a legit file named like *.bak.* —
NEG controls cover known citizens, not all future ones.
