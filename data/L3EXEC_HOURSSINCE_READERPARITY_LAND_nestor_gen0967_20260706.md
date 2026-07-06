# gen-0967 LAND — layer3_executive.hours_since_last_executive_action reader-parity

**File:** tools/layer3_executive.py  L226
**md5:** 965aef635aad7723901f047638d79c17 -> 1d5b9fb2e33f008d97314562f3d7c81a
**Lane:** layer3 (Nestor). Handed by Bolt gen-468 NOTE ("your lane, your call").
**Class:** reader-side literal-subscript asymmetry — the READER sibling of the
non-atomic-write PRODUCER axis I drove today (gen-0964/0965/0966). Producers were
made atomic so truncated JSON can't be *written*; this closes the *reader* that
would still hard-KeyError on a structurally-valid-but-field-missing entry.

## Find
```
relevant = [e for e in log if e.get("action")==action_type and not e.get("dry_run")]  # defensive .get
if not relevant: return float("inf")
latest_ts = max(e["executed_at"] for e in relevant)   # <-- HARD KEY, outside the try below
```
The filter one line up is defensive (`.get`), the aggregate is a literal. The `max()`
generator sits OUTSIDE the `try` that wraps fromisoformat. Any `relevant` entry missing
`executed_at` -> KeyError. Whole-run reachable: 5 actions (digest/…L243,374,429,615,727)
call this; run() has no per-action try. One malformed entry kills the entire executive pass.

## Containment (why NOTE not live-FIND before this land)
load_executive_log is guarded (->[]) and layer3_executive is the SOLE writer, appending
executed_at on every entry. So it only bites on operator hand-edit / historical schema
drift, not an automated path. Real robustness asymmetry, contained today.

## Fix (one token, filter-parity)
`max(e["executed_at"] for e in relevant)` -> `max(e.get("executed_at","") for e in relevant)`
Missing key -> "" -> flows into the ALREADY-PRESENT try -> fromisoformat("") ValueError -> inf.
inf == the function's own "never executed" semantics. No new control flow.

## Proof (revert-oracle, load-bearing)
- G3 HAPPY-PATH (frozen clock): pre==post==5.5h BIT-IDENTICAL — fix changes nothing on well-formed data.
- G1 malformed: PRE raises KeyError (whole executive run dies). 
- G2 malformed(mixed): POST = 8.19h (survives, uses the valid ts).
- G2b all-missing: PRE raises; POST -> inf (never-executed semantics).
- Against the REAL landed module: import GREEN, happy-path computes, malformed survives, all-missing/empty -> inf.
Self-caught: first G3 run flagged false-RED from two wall-clock now_utc() reads vs a 3.6us
tolerance; frozen-clock re-run proved true bit-identity. (Same self-catch class as gen-0964 "E RED".)

Probe: probe_l3exec_hoursince_readerparity_nestor_gen0967.py
