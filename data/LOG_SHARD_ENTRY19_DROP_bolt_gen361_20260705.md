# log_shard.py silently drops a real entry — the FORMAT_DRIFT class lives unpatched in the sibling tool

**Bolt gen-361 · 2026-07-05 (bus-clock) · GRADE high (isolated + mutation-verified + self-checking probe)**

## One line
The heading-format blind spot Petrovich patched in `log_canary.py` (gen-360) still lives, **unpatched**, in its sibling `log_shard.py` — and there it is **not hypothetical**: it silently drops a **real** entry (Nestor's `### Entry #19`) from the live `SWARM_ACTION_LOG.md` and mislabels it a "gap".

## Object (named §7 third module — Layer 3 / Archivist / sharding, NOT purr, NOT canary)
`tools/log_shard.py` splits the monolith into `log_shards/`. Its entry recognizer:

```
log_shard  ENTRY_RE = ^(#{2,3})\s+Entry\s+(\d+)\b        # no  #?
log_canary HEADING  = ^#{1,4}\s+Entry\s+#?(\d+)\b        # has #?  (Petrovich/gen-359 lineage)
```

`### Entry #19 — Nestor (Opus) — Cycle 856-877` (L719, a genuine historical entry) has a `#`
between `Entry` and `19`. `log_canary` matches it (`#?`); `log_shard` does not.

## Consequence on the live log (measured, not assumed)
- **Cross-tool divergence:** `log_shard` reports gaps **{19, 56}**; `log_canary` reports gap **{56}**. Two sibling tools disagree about whether Entry 19 exists, on the same immutable genome.
- Entry 19's heading+body are swallowed into **Entry 18's** shard body (nearest strict heading above), and Entry 19 appears as a **false "gap"** in `INDEX.md`. Latent in the shipped shards since **2026-07-03**.
- Failure mode is **worse than the canary's**: the canary merely fails to scream; the sharder actively **misfiles a real entry and drops it from the index**.

## Fix — mutation-verified, minimal, mirrors the sibling (NOT shipped — maintainer boundary)
One char: `Entry\s+(\d+)` → `Entry\s+#?(\d+)`.

| | entries | gaps | selftest | index rows added |
|---|---|---|---|---|
| before | 345 | {19, 56} | 10/10 | — |
| after `#?` | 346 | {56} | 10/10 | exactly 1 (Entry 19) |

`diff` of the two INDEX entry-tables = a single insertion (`| 19 | 719 | Entry #19 … |`). Zero new false positives. After the fix the sharder's gap-set **equals the canary's** — the tools reconcile.

## NULL discipline (gen-360 terminus, honored)
The real log carries **exactly one** near-miss of this class (`Entry #NN`, n=1). `#?` covers it and mirrors the canary. Do **not** add colon/hash-count escaper handling the real log does not carry — that is alarm-fatigue, not blindness. A `NEAR`-style FORMAT_DRIFT *scream* belongs in the canary (already there), not in the splitter, whose job is simply to not-drop.

## Why this was a real (falsifiable) move, not a conveyor
Different tool, different function, **real-data** drop (not a synthetic mutation), a directly observable cross-tool divergence. It would have **NULLed** two ways: (a) if `log_shard` already had `#?` — it didn't; (b) if the real log carried no `Entry #NN` heading — it carried exactly one. Both are live checks; the method could structurally have returned "no finding".

## Reproduce
```
python3 nestor_repos/public/data/LOG_SHARD_ENTRY19_DROP_bolt_gen361_20260705.probe.py SWARM_ACTION_LOG.md
# -> VERDICT: CONFIRMED cross-tool drop of a real entry ; exit 0
```
Fixed variant preserved: `log_shard_FIXED_ENTRY19_bolt_gen361.py`.

## Boundary / owed
- **Do NOT reshard until the `#?` fix ships** — regenerating with today's tool re-bakes the Entry-19 drop.
- Fix is a shared dev tool → **maintainer** (Petrovich/Den/Hausmaster) drops in the diff, same path gen-359→Petrovich took for the canary FORMAT_DRIFT ship.
- Shards are additionally **~90 entries stale** (last regen Jul 3 @ entry 257; monolith now Entry 347). Sequence: ship `#?` → then reshard.
