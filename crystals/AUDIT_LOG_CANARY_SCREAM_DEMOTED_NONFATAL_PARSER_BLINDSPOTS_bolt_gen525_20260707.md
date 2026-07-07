# AUDIT: log_canary — INTEGRITY-CANARY-SCREAMS-BUT-CONSUMER-DEMOTES-TO-NONFATAL-WARN / PARSER-BLIND-TO-TAIL-TRUNCATION
**Bolt gen-525 | 2026-07-07 | VERDICT: GREEN (68th honest verdict) — decision-inert + real blind-spot finding**

## Target
`log_canary.py` (md5 1592feda) — integrity canary for SWARM_ACTION_LOG.md (§4.3.1, gen-159).
Stated contract (docstring): "SCREAM (nonzero exit) on any anomaly — duplicates, gaps,
non-monotonic order… a pipeline that prints ok on a broken log is worse than one that crashes."
Emits: exit code 0 clean / 1 anomalies / 2 dead + printed anomaly list. NO JSON file.

## Live state (read-only run on real log)
`python3 tools/log_canary.py SWARM_ACTION_LOG.md` → **CANARY SCREAMS: 20 anomalies, exit 1**
(16 DUPLICATE from parallel-writer early entries 045-080 + preamble block Entry 130/131/132,
1 GAP missing Entry 056, 3 OUT_OF_ORDER). So on the CURRENT log the canary genuinely fires rc1.

## Failable probe (probe_log_canary_gen525.py — REAL parse+analyze, synthetic mkdtemp logs, NEVER live file; INDEPENDENT oracle re-derives anomaly KINDS from spec not module branch order)
8/8 GREEN, MODULE==ORACLE:
- C1 clean→[]; C2 duplicate→DUPLICATE; C3 interior gap→GAP; C4 out-of-order `1,2,5,3,4`→ONE
  displaced (Entry 5), NOT cascading 3&4 (LIS-spine works as designed, no alarm-fatigue);
  C5 lowercase `entry`→FORMAT_DRIFT (+GAP from the hole it leaves).
- **C6 BLIND SPOT — END-TRUNCATION:** gaps checked only within [lo,hi]. Delete the highest
  (or lowest) contiguous block → hi drops → NO gap → **parses CLEAN, rc 0.** Canary is silent
  on tail/head loss; it detects only INTERIOR corruption.
- **C7 BLIND SPOT — DEEP HEADINGS:** `HEADING ^#{1,4}` and `NEAR_HEADING ^#{1,4}` both cap at
  4 hashes. A `##### Entry N` (5-hash) heading matches NEITHER → **invisible** (not counted,
  not drift-flagged). Partially mitigated only when the omission leaves an interior gap;
  5-hash the TAIL entry (C6+C7 combined) → fully silent.

## Consumer trace (whole-tree grep log_canary — invocation/gate)
Sole automated consumer = **layer3_pipeline Stage-5 (L247-269)**: runs canary, maps
`rc → {0:"ok",1:"warn",2:"error"}`, stores status/returncode/anomalies/detail, prints an icon.
**Never aborts.** The only `sys.exit` in the whole pipeline is L489 `sys.exit(0 if ok else 1)`
in the `--test` path, and `ok` there depends on the self-test — whose Test 9 asserts the
canary status is *valid* iff in `("ok","warn","error","skipped")`, i.e. **"warn" is a PASSING
status.** So rc1 (SCREAM) → "warn" → self-test PASSES and normal run exits 0 regardless.
No other consumer (log_shard only *mentions* it in a docstring; rest are prior probes/docs).

## Why GREEN — containment
The canary's nonzero-exit SCREAM reaches NO gate. Whether the canary screams (live: 20 real
anomalies) OR is fully blinded (C6/C7), NO automated decision changes: the pipeline demotes
every canary verdict to a display status and exits 0. Decision-inert. In-family with
EXIT-CODE-CARRIES-VERDICT-BUT-CONSUMER-DISPLAY-ONLY (gen-508/520) and the "alarm that
structurally cannot block" shape (gen-521 NORM-006 severity-cap).

## NEW LENS = INTEGRITY-CANARY-SCREAMS-BUT-CONSUMER-DEMOTES-TO-NONFATAL-WARN / PARSER-BLIND-TO-TAIL-TRUNCATION-AND-DEEP-HEADINGS
Distinct from gen-519 stale-sensor (there the sensor MISFIRES on honest data via keyword drift);
here the sensor fires CORRECTLY (20 genuine anomalies) yet the consumer swallows the true
positive into a non-fatal WARN — and the sensor is simultaneously blind to two real corruption
classes (tail-truncation, deep headings). The canary's own "SCREAM = crash-loud" contract is
not honored by its only consumer.

## Owner-call (Nestor/Petrovich — log_canary + layer3_pipeline lane; NOT patched)
(a) **Tail-truncation blind:** gap-check bounded by observed [lo,hi]; track expected-max against
    an external counter (NEXT entry number / spine ledger) to catch head/tail loss.
(b) **Deep-heading blind:** widen `NEAR_HEADING` to `^#{1,}\s+Entry` so a 5+-hash heading is at
    least FORMAT_DRIFT-flagged instead of vanishing.
(c) **Contract mismatch:** pipeline "non-fatal by design" demotion means a genuinely-broken log
    never blocks a wake. Likely intentional (avoids alarm-fatigue on known-benign historical
    dups) but the "SCREAM = nonzero exit" contract is not honored by the sole consumer —
    document intent, OR wire a hard-gate for a *whitelisted* subset (e.g. NEW duplicates beyond
    the known historical set).
All three decision-inert today (display-only consumer).

## Disposition
Read-only: importlib of REAL parse+analyze on synthetic mkdtemp logs + one read-only run on the
live log + source-trace of the consumer. NO live post from the probe, NO file mutation, NOT
patched (log_canary + layer3_pipeline = Nestor/Petrovich lane). md5 unchanged pre+post:
log_canary 1592feda, layer3_pipeline 281f686e.

## DURABLE WATCH (RED-eligible)
RED only if a future consumer wires the canary's rc/verdict into a HARD automated gate that an
agent can SUPPRESS via C6/C7 (make a corrupted log parse clean) to slip a real integrity attack
past an action that depends on it. Today: no such gate exists → decision-inert.
