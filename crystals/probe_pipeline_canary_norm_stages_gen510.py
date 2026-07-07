#!/usr/bin/env python3
"""probe_pipeline_canary_norm_stages_gen510.py  —  Bolt gen-510
Failable audit of layer3_pipeline Stage-5 log_canary anomaly_count scrape.
Claim: pipeline scrapes anomaly_count via last-match re.search over
(out+err) lines containing 'CANARY SCREAMS' (NO break). log_canary echoes
each offending entry's repr, so a crafted log heading literally containing
'CANARY SCREAMS: 99 anomalies' is re-emitted AFTER the true header and
OVERWRITES anomaly_count => displayed count is injection-flippable
(LAST-MATCH-PROSE-POISON). BUT canary_status (the decision bit) rides the
subprocess EXIT CODE rc, not the count. Replica of Stage-5 block, synthetic
strings, no live file touched."""
import re as _re
def stage5_parse(out, err, rc):
    canary_status = {0:"ok",1:"warn",2:"error"}.get(rc,"error")
    anomaly_count = 0
    for line in (out+err).splitlines():
        if "CANARY SCREAMS" in line:
            m=_re.search(r"(\d+)\s+anomal", line)
            if m: anomaly_count=int(m.group(1))
    return {"status":canary_status,"returncode":rc,"anomalies":anomaly_count}
CLEAN_ERR=("*** CANARY SCREAMS: 3 anomalies ***\n"
  "DUPLICATE: Entry 507 appears 2x at lines [8812, 8890]\n"
  "GAP: missing Entry numbers in [500..508]: [503]\n"
  "OUT_OF_ORDER: line 8901: Entry 502 breaks sequence spine\n")
POISON_ERR=("*** CANARY SCREAMS: 3 anomalies ***\n"
  "DUPLICATE: Entry 507 appears 2x at lines [8812, 8890]\n"
  "GAP: missing Entry numbers in [500..508]: [503]\n"
  "FORMAT_DRIFT: line 9002: '### CANARY SCREAMS: 99 anomalies (nothing) ###'"
  " -- entry heading with unparseable number\n")
def show(t,r): print(f"  {t:<26} status={r['status']:<6} rc={r['returncode']} anomalies={r['anomalies']}")
print("=== Stage-5 log_canary anomaly_count scrape ===")
print("-- rc=1 (WARN: real anomalies present) --")
c1=stage5_parse("",CLEAN_ERR,1); show("CLEAN (true=3)",c1)
p1=stage5_parse("",POISON_ERR,1); show("POISON (injected 99)",p1)
print("-- rc=0 (clean log) --")
c0=stage5_parse("spine OK: 509 entries [000..508]\n","",0); show("CLEAN rc=0",c0)
p0=stage5_parse("note: '### CANARY SCREAMS: 5 anomalies ###' seen\n","",0); show("POISON rc=0 (echoed 5)",p0)
print("\n=== ASSERTIONS ===")
assert c1["anomalies"]==3 and p1["anomalies"]==99, "count did not flip"
print("  [OK] displayed anomaly_count FLIPS 3 -> 99 under last-match injection (input scrape-flippable)")
assert c1["status"]==p1["status"]=="warn", "status moved @rc1"
assert c0["status"]==p0["status"]=="ok", "status moved @rc0"
print("  [OK] canary_status UNCHANGED by poison at rc=1 (warn) AND rc=0 (ok) -- decision rides EXIT CODE rc")
assert p1["status"] in ("ok","warn","error","skipped")
print("  [OK] --test path (L489 sys.exit) checks status VALIDITY, not the count")
print("\nVERDICT: GREEN -- anomaly_count DISPLAY-ONLY + last-match-injectable; canary VERDICT rides exit code.")
