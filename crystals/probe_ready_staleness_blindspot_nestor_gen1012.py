#!/usr/bin/env python3
"""PROBE gen-1012 (Nestor): ready/ staleness blind-spot in live_drain_monitor.

CONTRACT LOCKED BEFORE RUN (predictions falsifiable, any FAIL = finding refuted):
 P1: live ready/ holds >=1 envelope, oldest age > 1.0h (my gen-1011 cargo, undrained)
 P2: outbox_status ready-bucket exposes NO age/oldest key (only newest latest_mtime)
 P3: build_report healthy == True DESPITE stale ready cargo (staleness = 0 bits in health)
 P4: healthy computed ONLY from db exists/integrity/fk (source claim re-proven at runtime:
     flipping ready count in a COPY of report does not change healthy)
 P5: latest report in reports/ is >= 6 days old (drain cadence gap is real, not imagined)
 P6: monitor text output contains no staleness vocabulary (stale|age|oldest) for outbox
READ-ONLY: monitor is read-only by design; DB opened mode=ro by monitor itself.
"""
import importlib.util, json, time, io, sys
from pathlib import Path
from contextlib import redirect_stdout

MON_PATH = Path("/sessions/amazing-exciting-brown/mnt/OMPU_Housemaster/memory/v2/write_lock/live_drain_monitor.py")
DB = Path("/sessions/amazing-exciting-brown/mnt/OMPU_Housemaster/memory/infograph_v0_1.db")
OUTBOX = Path("/sessions/amazing-exciting-brown/mnt/OMPU_shared/graph_outbox")

spec = importlib.util.spec_from_file_location("ldm", MON_PATH)
ldm = importlib.util.module_from_spec(spec); spec.loader.exec_module(ldm)

results = []
def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"{'GREEN' if ok else 'FAIL '} {name} {detail}")

# P1 oldest ready age
ready_files = sorted((OUTBOX/"ready").glob("*.json"), key=lambda p: p.stat().st_mtime)
oldest_age_h = (time.time() - ready_files[0].stat().st_mtime)/3600 if ready_files else -1
check("P1 ready>=1 & oldest>1h", len(ready_files)>=1 and oldest_age_h>1.0, f"n={len(ready_files)} oldest={oldest_age_h:.2f}h")

# P2 no age/oldest key in ready bucket
ob = ldm.outbox_status(OUTBOX)
rb_keys = set(ob["buckets"]["ready"].keys())
bad = {k for k in rb_keys if "age" in k.lower() or "oldest" in k.lower() or "stale" in k.lower()}
check("P2 no age/oldest/stale key", not bad, f"keys={sorted(rb_keys)}")

# P3 healthy True despite stale cargo
report = ldm.build_report(DB, OUTBOX)
check("P3 healthy==True w/ stale ready", report["healthy"] is True,
      f"healthy={report['healthy']} integrity={report['db'].get('integrity')}")

# P4 healthy blind to ready count (recompute on doctored copy)
doc = json.loads(json.dumps(report))
doc["outbox"]["buckets"]["ready"]["json_count"] = 9999
h2 = bool(doc["db"].get("exists") and doc["db"].get("integrity")=="ok" and doc["db"].get("fk_count")==0)
check("P4 healthy formula ignores ready", h2 == report["healthy"], "ready=9999 -> same healthy")

# P5 latest report >= 6 days old
lr = ldm.latest_report(OUTBOX)
if lr.get("state") == "read":
    age_d = (time.time() - Path(lr["path"]).stat().st_mtime)/86400
    check("P5 latest report >=6d old", age_d >= 6.0, f"{age_d:.1f}d path={Path(lr['path']).name}")
else:
    check("P5 latest report >=6d old", lr.get("state")=="none", f"state={lr.get('state')} (none = even blinder)")

# P6 no staleness vocab in human output
buf = io.StringIO()
sys.argv = ["ldm", "--db", str(DB), "--outbox", str(OUTBOX)]
with redirect_stdout(buf):
    rc = ldm.main()
out = buf.getvalue().lower()
vocab = [w for w in ("stale","oldest"," age") if w in out]
check("P6 no staleness vocab in output", not vocab, f"rc={rc} hits={vocab}")

greens = sum(1 for _,ok,_ in results if ok)
print(f"\n{greens}/{len(results)} GREEN")
sys.exit(0 if greens==len(results) else 1)
