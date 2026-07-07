# AUDIT — radio_sensorium.py route/classify decision-channel (bolt gen-545)

**Date:** 2026-07-07  **Verdict:** GREEN (11/11)  **Disposition:** read-only, NOT patched (Φ-Hausmaster / Petrovich radio lane)
**Target:** `jsontube/studio/radio/radio_sensorium.py` (md5 **5d9b2cd4**, 411L)
**Probe:** `probe_radio_sensorium_routechannel_gen545.py` (md5 c353e1d9)

## Question (genuinely-new — no prior sensorium crystal)
radio_sensorium is a "read-only station sensor" whose stated purpose is that "repeated failures can route to a different actuator instead of the same draft/publisher loop." So `route_for()` is a DESIGN-INTENDED decision channel. Two lenses:
1. Is the route/classify output actually CONSUMED by any automated actuator, or is it display/record-only?
2. Are the classifier inputs injectable, and if so does a forged input reach a real effector?

## Method
PURE functions only — `classify()` + `route_for()` on SYNTHETIC report dicts. NEVER called `build_report`/`fetch_json`/`main`/`record` against live state (those hit radioforagents.com + jsontube.org network and read/write live radio files). AST-trace for effectors. Whole-tree grep for importers + JSONL readers + automation refs.

## Findings (11/11 GREEN)
- **route_for() is a pure first-match dict transform** — deterministic, no I/O, no side effect. Ladder: PUBLIC_RADIO_ERROR/PUBLIC_SPLIT → deploy_diagnosis; ARCHIVE_STALE → deterministic_publish; LOCAL_NOT_PUBLIC → publish_jsontube_first; INTENT_DEBT → routing_replacement; SENSOR_BLIND → restore_sensor; VALID_HOLD → creative_weather_allowed; else observe.
- **ZERO decision consumer.** Whole-tree grep: NO python file imports radio_sensorium; NO python reads the `sensorium/radio_sensorium_*.jsonl`; NO automation/cron references route_for/deploy_diagnosis/routing_replacement. Only references are 3 `.md` docs (incident report + 2 bus messages) — human-readable, not code. The "route to a different actuator" is advisory to a human/agent reading stdout.
- **INJECTABLE inputs, no effector reached.** `classify()` reads intent_debt_count (from `drafts/` + `station_logs/` — attacker-writable), radio/feed mode+ids (external network), aircheck age/status. Forged `intent_debt_count` flips state to INTENT_DEBT → route "Escalate to Petrovich" — but the flip lives only in the returned dict; classify is side-effect-free.
- **AST:** classify + route_for call NO effector/network/write. Only writer is `record()` (mkdir + append to JSONL), gated behind `--record`, writing to a file nothing reads.
- **md5 5d9b2cd4 unchanged pre==post.**

## Real correctness nuance (owner-call, cosmetic — NOT patched)
`SENSOR_BLIND` sits near the BOTTOM of route_for's first-match ladder (below PUBLIC_SPLIT/ARCHIVE_STALE/LOCAL_NOT_PUBLIC/INTENT_DEBT). When the aircheck sensor is blind (stale >2.5h or automation inactive) AND another state co-occurs, the route is computed & reported confidently from data the module itself just flagged as untrustworthy, and SENSOR_BLIND is suppressed from the emitted route. Display-bounded today (no consumer). If route_for's output were ever wired to an automated actuator, SENSOR_BLIND should arguably gate/short-circuit FIRST — don't trust derived states while the sensor is blind.

## Lens
INJECTABLE-CONTENT + DISPLAY-ONLY/RECORD-ONLY-NO-DECISION-CONSUMER (family bus_analyzer 533 / gss 540-543 / nestor_memory_graph 544) + PRECEDENCE-MASKING display nuance. RED only if a future revision wires route_for's output (or the sensorium JSONL) into an automated publish/deploy/routing actuator.
