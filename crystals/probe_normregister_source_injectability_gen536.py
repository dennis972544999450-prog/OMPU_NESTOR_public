#!/usr/bin/env python3
"""
probe_normregister_source_injectability_gen536.py  — Bolt gen-536, 2026-07-07

AXIS (genuinely new): NORM_REGISTER.md SOURCE-OF-TRUTH INJECTABILITY.
norm_monitor DEFINES `NORM_REGISTER = BASE / "NORM_REGISTER.md"` (L44) and the
human-facing governance doc catalogues the 6 norms + their intended thresholds.
QUESTION: does the enforcer READ that human-editable document for its PASS/WARN/
FAIL boundaries?  If yes, editing the .md loosens the gate (RED, injectable).
If no (thresholds hard-coded in code), the doc is display/record-only and the
edit cannot move any verdict (GREEN — but code/doc-drift owner-call).

METHOD (read-only, failable):
  C1 POSITIVE CONTROL — verdict boundary sits EXACTLY at the module constants
     NORM002_RESOLVE_WARN / NORM002_RESOLVE_FAIL (proves constants drive it).
  C2 INJECTION INERTNESS — monkeypatch nm.NORM_REGISTER to a DOCTORED temp .md
     that "declares" absurdly loosened thresholds; re-run the SAME synthetic
     rates; verdict must be IDENTICAL (proves the register file is never read).
     If the code DID parse the register, the boundary would move and C2 FAILS.
  C3 STRUCTURAL — check_norm002 signature takes only bus_graph (no register arg);
     data.warn_threshold/fail_threshold echo the module constants, not any
     doctored register value.
  C4 TARGET-ALSO-HARDCODED — data.target_rate == 0.30 literal, register-inert.
  C5 NO-CLI-OVERRIDE — argparse exposes no flag to point at a custom register
     or override thresholds.

SAFETY: imports REAL module; calls ONLY pure check_norm002 on synthetic dicts;
NEVER main()/run_all_checks()/send_alert()/print_report (no file IO, no bus, no
writes to shared).  Doctored register is written to a private temp path, never
to /OMPU_shared.  md5 of norm_monitor.py asserted pre==post.
"""
import glob, hashlib, importlib.util, inspect, os, sys, tempfile

S = glob.glob("/sessions/*/mnt/OMPU_shared")[0]
NM_PATH = os.path.join(S, "tools", "norm_monitor.py")

def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()

MD5_PRE = md5(NM_PATH)

spec = importlib.util.spec_from_file_location("norm_monitor_probe", NM_PATH)
nm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nm)

results = []
def check(name, cond):
    results.append((name, bool(cond)))
    print(f"  {'GREEN' if cond else 'RED  '}  {name}")

def bg(rate):
    """synthetic bus_graph with a chosen resolve_rate."""
    return {"inhibitory_analytics": {
        "resolve_rate": rate, "total_threads": 100,
        "closed_threads": int(rate * 100), "inhibitory_usage": "probe"}}

WARN = nm.NORM002_RESOLVE_WARN   # 0.10
FAIL = nm.NORM002_RESOLVE_FAIL   # 0.03
eps = 1e-9

print("── C1 positive control: boundary == module constants ──")
check("C1a rate just >= WARN -> PASS", nm.check_norm002(bg(WARN))["status"] == "PASS")
check("C1b rate just < WARN  -> WARN", nm.check_norm002(bg(WARN - eps))["status"] == "WARN")
check("C1c rate just >= FAIL -> WARN", nm.check_norm002(bg(FAIL))["status"] == "WARN")
check("C1d rate just < FAIL  -> FAIL", nm.check_norm002(bg(FAIL - eps))["status"] == "FAIL")

print("── C2 injection inertness: doctored NORM_REGISTER cannot move the gate ──")
# Baseline verdicts across a sweep, BEFORE tampering.
sweep = [0.005, 0.03, 0.05, 0.10, 0.5]
base_verdicts = [nm.check_norm002(bg(r))["status"] for r in sweep]

# Write a DOCTORED register claiming loosened thresholds, point the module var at it.
doctored = (
    "# NORM_REGISTER (DOCTORED BY PROBE — attacker attempt)\n"
    "## NORM-002 resolve rate\n"
    "WARN threshold: 0.99   # attacker tries to force everything to FAIL\n"
    "FAIL threshold: 0.98\n"
    "target: 0.00\n"
    "NORM002_RESOLVE_WARN = 0.99\n"
    "NORM002_RESOLVE_FAIL = 0.98\n"
)
tmpd = tempfile.mkdtemp(prefix="probe_gen536_")
doctored_path = os.path.join(tmpd, "NORM_REGISTER.md")
with open(doctored_path, "w") as f:
    f.write(doctored)

from pathlib import Path
saved = nm.NORM_REGISTER
try:
    nm.NORM_REGISTER = Path(doctored_path)          # inject the poisoned source
    poisoned_verdicts = [nm.check_norm002(bg(r))["status"] for r in sweep]
finally:
    nm.NORM_REGISTER = saved                          # restore
check("C2a verdict sweep IDENTICAL after doctored register",
      poisoned_verdicts == base_verdicts)
check("C2b doctored WARN=0.99 did NOT flip rate=0.5 to FAIL",
      nm.check_norm002(bg(0.5))["status"] == "PASS")
# Also confirm the module constant itself is untouched by the doctored file.
check("C2c module NORM002_RESOLVE_WARN still 0.10 (not 0.99)",
      abs(nm.NORM002_RESOLVE_WARN - 0.10) < 1e-12)

print("── C3 structural: no register parameter, echoes constants ──")
sig = inspect.signature(nm.check_norm002)
check("C3a check_norm002 params == ['bus_graph'] only",
      list(sig.parameters) == ["bus_graph"])
d = nm.check_norm002(bg(0.5))["data"]
check("C3b data.warn_threshold == module WARN const", d["warn_threshold"] == WARN)
check("C3c data.fail_threshold == module FAIL const", d["fail_threshold"] == FAIL)

print("── C4 target-also-hardcoded ──")
check("C4a data.target_rate == 0.30 literal (register-inert)", d["target_rate"] == 0.30)

print("── C5 no CLI override of register/thresholds ──")
src = open(NM_PATH, encoding="utf-8").read()
# grep argparse flags; none should name register/threshold/warn/fail
import re
flags = re.findall(r'add_argument\("(--[a-z-]+)"', src)
bad = [fl for fl in flags if any(k in fl for k in ("register", "threshold", "warn", "fail"))]
check("C5a no --register/--threshold/--warn/--fail flag", bad == [])
# and NORM_REGISTER var is never .read_text()/.open()/json.loads'd
reads_register = bool(re.search(r'NORM_REGISTER\s*\.\s*(read_text|open|read_bytes)', src)) \
    or bool(re.search(r'(open|json\.loads)\([^)]*NORM_REGISTER', src))
check("C5b NORM_REGISTER never read/parsed in source", not reads_register)

MD5_POST = md5(NM_PATH)
check("md5 norm_monitor.py pre==post (no mutation)", MD5_PRE == MD5_POST)

n_green = sum(1 for _, ok in results if ok)
print(f"\nMD5 pre : {MD5_PRE}\nMD5 post: {MD5_POST}")
print(f"RESULT: {n_green}/{len(results)} GREEN")
sys.exit(0 if n_green == len(results) else 1)
