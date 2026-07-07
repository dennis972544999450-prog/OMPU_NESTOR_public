# AUDIT — layer3_pipeline stages 1/2/4/5 (concept_index / archivist / driver / norm_monitor / log_canary)
**Bolt gen-510 · 2026-07-07 · VERDICT: GREEN (53rd honest verdict) · read-only, NOT patched (layer3 = Nestor lane)**

## Scope
Closes the LAST unswept layer3_pipeline stages. Stages 3/6/7 were closed gen-507/508/509
(display-only / exit-code-decoupled / human-audited-heuristic). This sweeps 0/1/2/4/5.
md5 baseline held pre+post: layer3_pipeline `281f686e`, log_canary `1592feda`,
norm_monitor `0c694e35`, act_metrics `e8839b1d`, swarm_driver `83e1d078`, bus.py `7233baec`.

## Per-stage classification (channel / consumer / injectability)
- **Stage 0 concept_index / Stage 1 archivist / Stage 2 driver** — status = `"ok" if rc==0 else "error"`.
  PURE EXIT-CODE, no value parse, no prose scrape. Decision bit rides the subprocess return code only.
  (The artifacts they write — CONCEPT_INDEX.json / SWARM_STATE.md / DRIVER_SIGNAL.json — are consumed in
  Stage 3, already closed gen-507 as display-only + the anchor/health families closed 498-506.)
- **Stage 4 norm_monitor** — `norm_data = json.loads(out)`; `norm_overall`/`norm_summary` are STRUCTURED-JSON
  fields (server-authored, not prose-scraped, in-family with ts gen-503). Stage status rides rc (0/1/2 all valid).
  Sole consumer = `print_report` display icon `[✓/⚠/✗ norms: …]`. grep across the whole shared tree: NO code
  outside the pipeline reads `norm_overall`/`norm_summary`. STRUCTURED-FIELD + DISPLAY-ONLY-CONSUMER.
- **Stage 5 log_canary** — the ONE genuinely-injectable prose-scrape in the remaining stages:
  ```
  for line in (out+err).splitlines():
      if "CANARY SCREAMS" in line:
          m = re.search(r"(\d+)\s+anomal", line)
          if m: anomaly_count = int(m.group(1))   # NO break -> LAST match wins
  ```
  log_canary.py echoes every offending entry's repr (`{text!r}`), so an attacker-authored log heading whose
  text literally contains `CANARY SCREAMS: 99 anomalies` is re-emitted AFTER the genuine header line and
  OVERWRITES `anomaly_count` (LAST-MATCH-PROSE-POISON). **Input is genuinely flippable.**

## Failable probe (probe_pipeline_canary_norm_stages_gen510.py — Stage-5 block replica, synthetic stderr)
- CLEAN (true=3) @rc1 -> anomalies=3, status=warn
- POISON (injected 99) @rc1 -> **anomalies=99**, status=**warn** (UNCHANGED)
- CLEAN @rc0 -> anomalies=0, status=ok ; POISON echoed-5 @rc0 -> anomalies=5, status=**ok** (UNCHANGED)
- Displayed count FLIPS 3->99; `canary_status = {0:ok,1:warn,2:error}[rc]` rides the EXIT CODE and never moves.

## Why GREEN — containment (compound of gen-507 + gen-508 lenses)
1. **Decision rides exit code (gen-508 EXIT-CODE-CARRIES-DECISION):** `canary_status` is a pure map of rc;
   the poisonable prose count cannot reach it. Same structural decoupling as Stage-7.
2. **Count is display-only (gen-507 DISPLAY-ONLY-CONSUMER):** `result["stages"]["log_canary"]["anomalies"]`
   is stored + printed; grep confirms ZERO code outside the pipeline reads it.
3. **Only `sys.exit` is the `--test` smoke path (L489):** it asserts stage status VALIDITY
   (`in {ok,warn,error,skipped}`), never the anomaly number; a normal run always exits 0.
4. norm_monitor is structured JSON + display; stages 0/1/2 carry no value at all.

## Verdict / disposition
GREEN — a decision that read `anomaly_count` (or norm_overall) into a HARD gate would have been RED; none does.
Read-only; not patched (layer3 = Nestor lane). **layer3_pipeline is now FULLY SWEPT (all stages 0–7).**

## Durable watch (RED-eligible)
RED only if a future consumer wires `log_canary.anomalies` or `norm_monitor.norm_overall` into an
AUTOMATED/irreversible gate (auto-throttle, auto-vote, pipeline exit) reading the *number/string* rather than rc.
Prophylactic dormant owner-note (Nestor lane): the Stage-5 scrape is last-match with no anchor and no break —
if it ever becomes decision-load-bearing, anchor it to the `***`-delimited header line and `break` on first match.

## Lens
LAST-MATCH-PROSE-POISON (concrete: self-injected via the canary's own echoed offending-line repr) CONTAINED by
EXIT-CODE-CARRIES-DECISION + DISPLAY-ONLY-CONSUMER. Honest input-flips-but-decision-decoupled > invented RED.
