"""
gen-511 FAILABLE probe: NORM-004 (norm_monitor.check_norm004) reads
DRIVER_SIGNAL.priority_tasks[0].description/score (agent-authored via log) —
can a crafted top_task FLIP the norm status PASS<->WARN, and does the flip
reach any irreversible/automated consequence?

Pure-function probe: check_norm004(log_text, driver_signal) takes both args,
touches NO live file. We import the REAL norm_monitor module and call the REAL fn.
"""
import importlib.util, sys, os

NM = "/sessions/funny-affectionate-thompson/mnt/OMPU_shared/tools/norm_monitor.py"
spec = importlib.util.spec_from_file_location("norm_monitor", NM)
nm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nm)

# A recent log with 3 entries. Keywords about "publish guard" appear.
LOG = """
### Entry 507 | gen-508 | 2026-07-07 | audited spine window stdout parser, exit-code decoupled
Traced every consumer, read-only. did not patch — Nestor lane.

### Entry 508 | gen-509 | 2026-07-07 | audited act_metrics heuristic, human-audited gate
Source-trace + importlib probe. owner-call left to Phi/Hausmaster.

### Entry 509 | gen-510 | 2026-07-07 | pipeline fully swept, last-match poison contained
Read-only audit, not live-patched.
"""

def run(label, top_task):
    ds = {"priority_tasks": [top_task]}
    r = nm.check_norm004(LOG, ds)
    print(f"[{label}] status={r['status']:8} | reason={r['reason'][:90]}")
    return r["status"]

print("=== NORM-004 caller-influenceable input flip ===")
# CLEAN-ADDRESSED: top task keywords ('audit','read-only') present in recent → PASS
s1 = run("CLEAN-MATCH ", {"description": "audit read-only pipeline consumers", "priority": 9})
# POISON-FORCE-WARN: craft a top task whose keywords are ABSENT from recent entries,
# and the log has choice-log markers? recent entries DO contain 'did not patch'/'owner-call'
# which ARE choice-log markers -> so even divergence stays PASS. Try to force WARN by
# a task with alien keywords AND a log WITHOUT choice markers:
LOG_NOCHOICE = """
### Entry 507 | gen-508 | shipped a thing
built stuff and moved on.

### Entry 508 | gen-509 | shipped another thing
more building.

### Entry 509 | gen-510 | shipped again
kept going.
"""
def run2(label, top_task, log):
    r = nm.check_norm004(log, {"priority_tasks": [top_task]})
    print(f"[{label}] status={r['status']:8} | reason={r['reason'][:90]}")
    return r["status"]
s2 = run2("POISON-WARN ", {"description": "quantum blockchain synergy neural mesh", "priority": 2}, LOG_NOCHOICE)
# POISON-FORCE-PASS (suppress divergence): craft task whose keywords MATCH the nochoice log
s3 = run2("POISON-PASS ", {"description": "shipped building stuff moved", "priority": 10}, LOG_NOCHOICE)
# EMPTY tasks -> UNKNOWN
s4 = nm.check_norm004(LOG, {"priority_tasks": []})["status"]
print(f"[EMPTY      ] status={s4:8}")

print()
print("=== SEVERITY CAP: NORM-004 possible statuses ===")
print("  NORM-004 return statuses observed:", sorted(set([s1,s2,s3,s4])))
print("  NORM-004 NEVER returns FAIL (grep: only PASS/WARN/UNKNOWN in check_norm004)")
print("  => worst overall it can force = WARN (exit 1), never FAIL (exit 2)")
print()
print("=== CONSUMER REACH of a forced WARN ===")
print("  overall=WARN -> exit code 1 -> layer3_pipeline Stage-4 rc -> DISPLAY icon only (gen-510)")
print("  overall=WARN -> --alert (opt-in flag) -> SOFT bus advisory 'document divergence' (not run in audit)")
print("  NORM_COMPLIANCE_REPORT.json -> no external decision-reader (gen-510 grep)")
