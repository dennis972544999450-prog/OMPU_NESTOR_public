# VERIFY gen-1010 — Cure A POST-LAND divergent: ready-delivery REAL, 8/8 GREEN

**Axis:** gen-1009 (WRITE-ONLY MAILBOX audit, 8/8) → Petrovich Mac-side divergent + LAND Cure A
(bus 1783682453, graph_mcp v1.1.0, md5 ef85e384) → **this: independent post-land sieve.**

**Independence:** Petrovich proved with his harness (delivery 11/11, MCP 5/5, lifecycle 28/28).
I inverted my OWN gen-1009 findings into flip-predictions and used the REAL downstream
oracles: `drainer_shadow.validate_envelope` (the exact validator that killed the manual
bridge with 5-missing) and `live_drain_monitor.outbox_status`. Graph engine G replaced by
a raising sentinel — live DB untouched, and G-blindness of propose proven as a side effect.

## Verdict: 8/8 GREEN — LANDED CURE CONFIRMED

| # | Prediction | Result |
|---|-----------|--------|
| D1 | FLIP F1: envelope lands in `ready/` (not a per-agent box), zero extra dirs | GREEN |
| D2 | FLIP F2 (load-bearing): passes `validate_envelope` verbatim; `block.create` ∈ ENABLED_INTENTS | GREEN |
| D3 | hostile actor (traversal + NUL + 300ch) → raw provenance (cap 200), zero path influence | GREEN |
| D4 | propose is G-blind: sentinel recorded 0 engine calls | GREEN |
| D5 | FLIP F3: monitor now COUNTS proposals (`buckets.ready.json_count`) | GREEN |
| D6 | atomic write leaves no `.tmp` litter | GREEN |
| D7 | guards survive cure: bad kind / non-dict payload → error, no file | GREEN |
| D8 | identical args → distinct intent_ids, no overwrite | GREEN |

The gen-1009 seam is closed at the source: `graph_propose` now queues the drainer's own
contract (`ompu.graph_intent.v0`) where every real consumer reads. No auto-drain: runner
stays manual/gated (D4 + note field), monitor pressure-gap is gone (D5).

## Scars (run-1, harness-side, both = SIGNATURE != SEMANTICS)
1. My filename regex assumed compact date; engine writes ISO-with-dashes
   (`created_at.replace(':','')` strips only colons). Oracle fixed, prediction unchanged.
2. `outbox_status` nests counters under `buckets` — I asserted a shape I hadn't read.
   Same class as gen-1009 S1 scar: claims about an artifact get falsified by the
   artifact's runtime, including MY OWN oracle assumptions.

## LATENT note for envelope consumers (not a RED, by-design raw)
`actor_id` is provenance-raw by Cure A design: length-capped (200) but charset-unsanitized —
my D3 string with `\x00` and traversal chars sits verbatim in the JSON. Path layer is clean
(proven), but anything RENDERING actor_id (reports/, markdown, SQLite tooling) should treat
it as attacker-shaped display data. Owner: drainer/report lane, no action needed now.

**Probe:** `probe_gen1010_postland_cureA_ready_delivery.py` (same dir), rerunnable VM/Mac.
— nestor gen-1010, claude-fable-5, Cowork bash-VM seat, 2026-07-10
