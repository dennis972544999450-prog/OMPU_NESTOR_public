#!/usr/bin/env python3
"""PROBE gen-613 (Bolt): divergent verify of Nestor gen-1012 (msg 1783692808)
+ Petrovich drain receipt (msg 1783693015).

CONTRACT LOCKED BEFORE BODIES WERE READ (outputs/gen1012_divergent_verify_predictions_locked_gen613.md,
md5 8d7c4504). Independent sieve: world CHANGED after Nestor's audit (live drain 14:15:40Z),
so this is NOT a re-run of his probe — it tests his claims against the post-drain world.

 P1: metrics.jsonl unfroze via live drain (predicted 5 lines; actual 6 — dry-run 141523 ALSO wrote)
 P2: copy-runs absent from metrics -> PRODUCTIVE FAIL: 4/6 metrics lines ARE copy-mode,
     incl. 3 of the 4 lines Nestor saw "frozen". F2 mechanism sentence refuted (see crystal).
 P3: report 141540Z matches Petrovich receipt verbatim
 P4: monitor healthy-formula blind to ready/ age (code-read + behavioral test on mkdtemp copy
     with a 30-day-old planted ready file -> healthy=True, rc=0)
 P5: Nestor's "reports/ = 8 файлов" is not an inventory (32 files); 8 = count of UNIQUE DATES

READ-ONLY to live territory: monitor executed only on a temp copy; live files read via
open/glob; md5 pre/post asserted on metrics.jsonl and live_drain_monitor.py.
"""
import glob, hashlib, json, os, re, sqlite3, subprocess, sys, tempfile, time

S = os.environ.get("OMPU_SHARED") or glob.glob("/sessions/*/mnt/OMPU_shared")[0]
H = os.path.join(os.path.dirname(S.rstrip("/")), "OMPU_Housemaster")
METRICS = f"{S}/graph_outbox/live_drain_metrics.jsonl"
REPORTS = f"{S}/graph_outbox/reports"
MON = f"{H}/memory/v2/write_lock/live_drain_monitor.py"

def md5(p): return hashlib.md5(open(p, "rb").read()).hexdigest()

results = []
def check(name, ok, detail=""):
    results.append(ok)
    print(f"{'GREEN' if ok else 'FAIL '} {name} {detail}")

pre = {p: md5(p) for p in (METRICS, MON)}

lines = [json.loads(l) for l in open(METRICS) if l.strip()]
live = [l for l in lines if l.get("runner_mode", "").startswith("LIVE")]
copy = [l for l in lines if not l.get("runner_mode", "").startswith("LIVE")]

# P1 metrics unfroze at first live drain (>=1 LIVE line dated 2026-07-10)
p1 = any((l.get("generated_at") or "").startswith("2026-07-10") for l in live)
check("P1 metrics unfroze via live drain", p1,
      f"lines={len(lines)} live={len(live)} copy={len(copy)}")

# P2 (locked prediction: copy absent) -> expected-productive-FAIL branch:
# assert the REFUTATION is real: copy-mode lines DO exist in metrics
check("P2-inverted copy lines DO exist in metrics (F2 mechanism refuted)", len(copy) >= 3,
      f"copy_lines={len(copy)} (Nestor's 'frozen 4' included 3 dry-runs)")

# P3 report matches Petrovich receipt
r = json.load(open(f"{REPORTS}/live_drain_20260710T141540Z.json"))["summary"]
p3 = (r["mode"] == "live_drain" and r["live_db_mutated"] is True and r["applied"] == 1
      and r["retired"] == 1 and r["rejected"] == 0 and r["deferred"] == 0
      and r["integrity"] == "ok")
check("P3 receipt verbatim", p3, json.dumps({k: r[k] for k in ('mode','applied','retired')}))

# P4 behavioral: monitor on temp copy, 30-day-old ready file -> healthy
T = tempfile.mkdtemp(prefix="gen613_mon_")
for d in ("ready", "archive", "rejected", "reports"):
    os.makedirs(f"{T}/outbox/{d}")
import shutil; shutil.copy(MON, f"{T}/mon.py")
db = f"{T}/g.db"; c = sqlite3.connect(db); c.execute("create table t(x)"); c.commit(); c.close()
stale = f"{T}/outbox/ready/ancient.json"; open(stale, "w").write("{}")
old = time.time() - 30 * 86400; os.utime(stale, (old, old))
out = subprocess.run([sys.executable, f"{T}/mon.py", "--db", db, "--outbox", f"{T}/outbox", "--json"],
                     capture_output=True, text=True)
rep = json.loads(out.stdout)
check("P4 healthy=True w/ 30d-old ready (temp copy)", rep["healthy"] is True and out.returncode == 0,
      f"rc={out.returncode}")

# P5 "8 файлов" = 8 unique dates, not files
files = glob.glob(f"{REPORTS}/*.json")
days = {m.group(1) for f in files for m in [re.search(r"(2026\d{4})", os.path.basename(f))] if m}
check("P5 8=unique dates, files=32", len(days) == 8 and len(files) >= 30,
      f"files={len(files)} dates={len(days)}")

# hygiene: live files untouched
check("HYGIENE md5 pre==post", all(md5(p) == h for p, h in pre.items()))

g = sum(results)
print(f"\n{g}/{len(results)} GREEN")
sys.exit(0 if g == len(results) else 1)
