"""gen-535 FAILABLE probe: norm_monitor.send_alert (the --alert BUS channel).
Distinct from gen-510 (which closed the NORM_COMPLIANCE_REPORT.json norm_overall/
norm_summary channel). This traces the OTHER consumer channel: the bus alert.
Imports REAL norm_monitor; calls send_alert(report, dry_run=True) ONLY -> dry_run
NEVER reaches subprocess/bus (prints + returns). No file IO, no bus post, no writes.
LENS check: is the alert (a) gated to WARN/FAIL, (b) command-injection-safe (argv-list
not shell-string), (c) bounded (reason truncated)? Any could fail.
"""
import importlib.util, hashlib, os, sys, io, contextlib

import glob
S = glob.glob("/sessions/*/mnt/OMPU_shared")[0]
NM = f"{S}/tools/norm_monitor.py"
md5 = lambda p: hashlib.md5(open(p,'rb').read()).hexdigest()[:8]
pre = md5(NM); assert pre == "0c694e35", f"md5 baseline drift: {pre}"

spec = importlib.util.spec_from_file_location("nm_probe", NM)
nm = importlib.util.module_from_spec(spec); spec.loader.exec_module(nm)

passed = failed = 0
def check(name, cond):
    global passed, failed
    print(f"  [{'GREEN' if cond else 'RED  '}] {name}")
    passed += cond; failed += (not cond)

# suppress send_alert's dry-run prints
def call(report):
    with contextlib.redirect_stdout(io.StringIO()):
        return nm.send_alert(report, dry_run=True)

# C1: PASS overall => skipped, no alert built
r1 = call({"overall": "PASS", "norms": []})
check("C1 PASS report -> skipped (no alert fires)", r1.get("skipped") is True)

# C2: FAIL overall => alert built, dry_run True (NEVER posts), subject carries FAIL count
r2 = call({"overall": "FAIL", "norms": [
    {"norm": "NORM-002", "status": "FAIL", "reason": "resolve rate 0%"},
    {"norm": "NORM-006", "status": "WARN", "reason": "manual lag"}]})
check("C2 FAIL report -> alert built + dry_run (never posts)", r2.get("dry_run") is True)
check("C2 subject counts 1F 1W", "1F 1W" in r2.get("subject",""))

# C3: WARN-only also fires (not just FAIL)
r3 = call({"overall": "WARN", "norms": [{"norm":"NORM-002","status":"WARN","reason":"low"}]})
check("C3 WARN-only report also fires alert", r3.get("dry_run") is True and not r3.get("skipped"))

# C4: forged reason with shell metachars + newline -> handled via argv-list, no crash.
#     Verify the SOURCE builds cmd as a LIST and never uses shell=True (injection-safe).
src = open(NM).read()
seg = src[src.index("def send_alert"):]
seg = seg[:seg.index("\ndef ", 1)] if "\ndef " in seg[1:] else seg
check("C4 send_alert builds cmd as argv LIST (cmd = [)", "cmd = [" in seg)
check("C4 send_alert NEVER uses shell=True", "shell=True" not in seg)
evil = {"overall":"FAIL","norms":[{"norm":"NORM-X","status":"FAIL",
        "reason":"; rm -rf / #\n$(curl evil)\n"+"A"*300}]}
r4 = call(evil)
check("C4 malicious reason -> dry_run returns cleanly (no exec, no crash)",
      r4.get("dry_run") is True)

# C5: reason is BOUNDED — source truncates reason to 120 chars in the alert body
check("C5 reason truncated to [:120] in body build", "reason'][:120]" in seg or "reason'][:120" in seg)

# C6: alert posts to a channel (general) — notification target, not an effector/gate key
check("C6 alert target is a channel (general), not a task/priority/effector key",
      "--to-channel" in seg and "general" in seg
      and not any(k in seg for k in ["priority", "task_id", "effector", "--gate", "block"]))

post = md5(NM)
check("md5 norm_monitor unchanged pre==post", pre == post)
print(f"\n  norm_monitor md5 {pre} (pre) == {post} (post)")
print(f"  RESULT: {passed}/{passed+failed} GREEN")
sys.exit(0 if failed == 0 else 1)
