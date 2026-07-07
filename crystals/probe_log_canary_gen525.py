#!/usr/bin/env python3
"""
probe_log_canary_gen525.py — Bolt gen-525 FAILABLE audit of log_canary.py.
Imports REAL log_canary.parse + analyze. Synthetic temp logs in a mkdtemp (NEVER
the live SWARM_ACTION_LOG.md). INDEPENDENT oracle re-derives anomaly KINDS from
the spec (duplicate/gap/out-of-order/format-drift), NOT the module's branch order.
NO mutation of any live file. Also probes two adversarial BLIND SPOTS.
"""
import os, sys, tempfile, importlib.util

S = "/sessions/vigilant-keen-knuth/mnt/OMPU_shared"
spec = importlib.util.spec_from_file_location("log_canary", os.path.join(S, "tools", "log_canary.py"))
lc = importlib.util.module_from_spec(spec); spec.loader.exec_module(lc)

td = tempfile.mkdtemp(prefix="canary_probe_")
def write_log(name, lines):
    p = os.path.join(td, name)
    open(p, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    return p

def kinds(anoms):  # set of anomaly KINDS returned by module
    return sorted({k for k, _ in anoms})

def oracle_kinds(entry_nums, drift_present):
    """Independent re-derivation of which anomaly kinds SHOULD appear."""
    ks = set()
    if drift_present: ks.add("FORMAT_DRIFT")
    seen = {}
    for n in entry_nums: seen[n] = seen.get(n, 0) + 1
    if any(c > 1 for c in seen.values()): ks.add("DUPLICATE")
    nums = sorted(seen)
    if nums:
        lo, hi = nums[0], nums[-1]
        if [n for n in range(lo, hi+1) if n not in seen]: ks.add("GAP")
    # out-of-order: any element not on a longest strictly-increasing subsequence
    seq = entry_nums
    n = len(seq)
    if n:
        best=[1]*n; 
        for i in range(n):
            for j in range(i):
                if seq[j] < seq[i]: best[i]=max(best[i], best[j]+1)
        lis = max(best) if best else 0
        # if the whole non-duplicate sequence isn't strictly increasing over distinct spine
        # (approx: a displaced element exists) -> OUT_OF_ORDER may appear. We assert module
        # only; oracle flags OUT_OF_ORDER when a strictly-increasing full pass is impossible
        strictly_inc = all(seq[i] < seq[i+1] for i in range(n-1))
        if not strictly_inc and lis < len(set(seq)): ks.add("OUT_OF_ORDER")
    return ks

P = F = 0
def check(name, cond, extra=""):
    global P, F
    if cond: P += 1; print(f"  PASS: {name} {extra}")
    else: F += 1; print(f"  FAIL: {name} {extra}")

# C1 clean monotonic
p = write_log("clean.md", ["### Entry 1 | a","body","### Entry 2 | b","body","### Entry 3 | c","body"])
e,d = lc.parse(p); an,lo,hi,tot,dis = lc.analyze(e,d)
check("C1 clean -> 0 anomalies", an==[] , f"kinds={kinds(an)}")

# C2 duplicate
p = write_log("dup.md", ["### Entry 1 |","x","### Entry 2 |","x","### Entry 2 |","x","### Entry 3 |","x"])
e,d = lc.parse(p); an,*_ = lc.analyze(e,d)
check("C2 duplicate detected == oracle", "DUPLICATE" in kinds(an) and kinds(an)==sorted(oracle_kinds([1,2,2,3],False)), f"kinds={kinds(an)}")

# C3 interior gap
p = write_log("gap.md", ["### Entry 1 |","x","### Entry 2 |","x","### Entry 4 |","x"])
e,d = lc.parse(p); an,*_ = lc.analyze(e,d)
check("C3 interior gap detected", "GAP" in kinds(an), f"kinds={kinds(an)}")

# C4 single out-of-order (LIS not cascading): 1,2,5,3,4  -> only '5' off-spine, NOT 3&4
p = write_log("ooo.md", ["### Entry 1 |","x","### Entry 2 |","x","### Entry 5 |","x","### Entry 3 |","x","### Entry 4 |","x"])
e,d = lc.parse(p); an,*_ = lc.analyze(e,d)
ooo = [m for k,m in an if k=="OUT_OF_ORDER"]
# gap present too (missing... none: 1..5 all present) -> only OOO. Expect exactly ONE OOO line (Entry 5), not cascading 3&4
check("C4 out-of-order flags ONE displaced (not cascading)", len(ooo)==1 and "005" in ooo[0], f"ooo={ooo}")

# C5 format drift (lowercase 'entry' -> NEAR_HEADING matches, HEADING doesn't)
p = write_log("drift.md", ["### Entry 1 |","x","### entry 2 lowercase |","x","### Entry 3 |","x"])
e,d = lc.parse(p); an,*_ = lc.analyze(e,d)
check("C5 format drift (lowercase entry) flagged", "FORMAT_DRIFT" in kinds(an), f"kinds={kinds(an)} drift={d}")

# ---- ADVERSARIAL BLIND SPOTS ----
# C6 END-TRUNCATION: gaps only checked within [lo,hi]. Delete top entries -> hi drops -> NO gap -> CLEAN.
# Genuinely-corrupted log (entries 4,5,6 removed from a 1..6 log) parses CLEAN.
p = write_log("trunc.md", ["### Entry 1 |","x","### Entry 2 |","x","### Entry 3 |","x"])
e,d = lc.parse(p); an,*_ = lc.analyze(e,d)
check("C6 BLIND SPOT: end-truncation parses CLEAN (canary silent on tail loss)", an==[], f"kinds={kinds(an)} -> canary rc would be 0")

# C7 5-hash heading: HEADING ^#{1,4} and NEAR_HEADING ^#{1,4} both cap at 4 hashes.
# A '##### Entry 2' heading is INVISIBLE: not counted, not drift-flagged.
p = write_log("fivehash.md", ["### Entry 1 |","x","##### Entry 2 |","x","### Entry 3 |","x"])
e,d = lc.parse(p); an,*_ = lc.analyze(e,d)
nums = [n for _,n in e]
check("C7 BLIND SPOT: 5-hash heading invisible (Entry 2 neither counted nor drift-flagged)",
      nums==[1,3] and "FORMAT_DRIFT" not in kinds(an), f"parsed_nums={nums} kinds={kinds(an)}")

# C8 CONTAINMENT source-check: pipeline maps rc1 -> 'warn' (a VALID/passing status), never aborts.
lp = open(os.path.join(S,"tools","layer3_pipeline.py"),encoding="utf-8").read()
maps_warn = '{0: "ok", 1: "warn", 2: "error"}' in lp
warn_is_valid = '("ok", "warn", "error", "skipped")' in lp
only_exit_is_test = lp.count("sys.exit(") == 1 and "sys.exit(0 if ok else 1)" in lp
check("C8 CONTAINMENT: rc1->'warn', 'warn' is a passing status, sole sys.exit is --test path",
      maps_warn and warn_is_valid and only_exit_is_test,
      f"maps_warn={maps_warn} warn_valid={warn_is_valid} lone_test_exit={only_exit_is_test}")

print(f"\nprobe_log_canary_gen525: {P}/{P+F} PASS ({F} FAIL)")
sys.exit(0 if F==0 else 1)
