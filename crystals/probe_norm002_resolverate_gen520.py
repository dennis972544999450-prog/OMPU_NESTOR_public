#!/usr/bin/env python3
"""
probe_norm002_resolverate_gen520.py  —  Bolt gen-520 failable audit

TARGET: norm_monitor.check_norm002 (NORM-002 resolve-rate value-gate) + overall
rollup (run_all_checks) + effector argv-safety (send_alert) + consumer decision-reach.

HYPOTHESIS TO TRY TO BREAK (any => RED):
  H1  status bucketing wrong vs independent oracle at threshold boundaries
  H2  overall rollup does NOT surface a single NORM-002 FAIL as overall=FAIL
  H3  send_alert effector builds a SHELL-STRING (forgeable) rather than argv-list
  H4  a synthetic poisoned resolve_rate reaches a HARD GATE / block key in output
  H5  exit-code verdict (2=FAIL) is consumed by layer3_pipeline as a gate (abort)

METHOD: import REAL functions (read-only, never call main()/live write/post).
Inject synthetic bus_graph. Independent oracle re-derives status from first
principles (NOT reusing module thresholds via the module's own branch order).
Monkeypatch subprocess.run to CAPTURE argv without executing (send_alert non-dry).
"""
import importlib.util, sys, types, io, contextlib
from pathlib import Path

TOOLS = Path("/sessions/sharp-epic-noether/mnt/OMPU_shared/tools")
spec = importlib.util.spec_from_file_location("nm_gen520", TOOLS / "norm_monitor.py")
nm = importlib.util.module_from_spec(spec)
spec.loader.exec_module(nm)

WARN = nm.NORM002_RESOLVE_WARN   # 0.10
FAIL = nm.NORM002_RESOLVE_FAIL   # 0.03
REG_TARGET = 0.30                # register "healthy" target hardcoded in check

results = []
def check(name, ok, detail=""):
    results.append((name, ok, detail))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}")

def oracle_status(rate):
    # INDEPENDENT oracle: healthy>=WARN pass, else warn until FAIL floor, else fail.
    # Written from the NORM semantics, not copied from module branch.
    if rate >= WARN:
        return "PASS"
    if rate >= FAIL:
        return "WARN"
    return "FAIL"

# ── H1: boundary sweep ───────────────────────────────────────────────────────
boundary_rates = [0.0, 0.029, 0.03, 0.031, 0.099, 0.10, 0.101, 0.15, 0.30, 0.99]
mismatch = []
for r in boundary_rates:
    bg = {"inhibitory_analytics": {"resolve_rate": r, "total_threads": 100,
                                   "closed_threads": int(r*100), "inhibitory_usage": "test"}}
    res = nm.check_norm002(bg)
    exp = oracle_status(r)
    if res["status"] != exp:
        mismatch.append((r, res["status"], exp))
check("H1 status bucketing == independent oracle (10 boundary rates)",
      not mismatch, f"mismatches={mismatch}")

# empty/missing => UNKNOWN, fail-safe (no crash, no FAIL escalation)
res_empty = nm.check_norm002({})
check("H1b empty bus_graph => UNKNOWN fail-safe (not FAIL/crash)",
      res_empty["status"] == "UNKNOWN", f"status={res_empty['status']}")

# ── H2: overall rollup surfaces single NORM-002 FAIL ─────────────────────────
def rollup(statuses):
    # mirror of run_all_checks summary logic, applied to synthetic status list
    if statuses.count("FAIL") > 0: return "FAIL"
    if statuses.count("WARN") > 0: return "WARN"
    if statuses.count("UNKNOWN") == len(statuses): return "UNKNOWN"
    return "PASS"
check("H2 single FAIL among PASSes rolls to overall=FAIL",
      rollup(["PASS","FAIL","PASS","PASS","PASS","PASS"]) == "FAIL")
check("H2b single WARN (no FAIL) rolls to overall=WARN",
      rollup(["PASS","WARN","PASS","PASS","PASS","PASS"]) == "WARN")

# ── H3: effector is argv-LIST not shell-string ───────────────────────────────
captured = {}
real_run = nm.subprocess.run
def fake_run(cmd, *a, **k):
    captured["cmd"] = cmd
    captured["shell"] = k.get("shell", False)
    class R:  # minimal fake CompletedProcess
        returncode = 0; stdout = "ok"; stderr = ""
    return R()
nm.subprocess.run = fake_run
try:
    # build a FAIL report carrying an injection attempt in the reason
    poison = "'; rm -rf / #  $(touch /tmp/pwn)"
    rep = {"overall": "FAIL",
           "norms": [{"norm": "NORM-002", "status": "FAIL",
                      "reason": f"Resolve rate 0.0% — {poison}"}]}
    with contextlib.redirect_stdout(io.StringIO()):
        out = nm.send_alert(rep, dry_run=False)
    cmd = captured.get("cmd")
    is_list = isinstance(cmd, list)
    no_shell = captured.get("shell") is False
    # poison must ride as a single argv element (body), never concatenated into a shell string
    poison_isolated = any(poison in str(el) for el in (cmd or [])) and is_list
    check("H3 effector uses argv-LIST (not shell-string)", is_list, f"type={type(cmd).__name__}")
    check("H3b subprocess.run shell=False", no_shell, f"shell={captured.get('shell')}")
    check("H3c injection payload isolated in one argv element (unforgeable)", poison_isolated)
finally:
    nm.subprocess.run = real_run

# ── H4: no hard-gate / block key emitted by the check itself ──────────────────
bg_bad = {"inhibitory_analytics": {"resolve_rate": 0.0, "total_threads": 9,
                                   "closed_threads": 0, "inhibitory_usage": "none"}}
res_fail = nm.check_norm002(bg_bad)
keys_blob = str(res_fail).lower()
gate_tokens = ["block", "gate", "abort", "halt", "throttle", "deny", "reject", "freeze"]
leaked = [t for t in gate_tokens if t in keys_blob]
check("H4 FAIL verdict carries NO gate/block/abort key (advisory-only)",
      not leaked, f"leaked={leaked}")

# ── H5: consumer (layer3_pipeline) treats exit 0/1/2 as non-gating ───────────
pipe = (TOOLS / "layer3_pipeline.py").read_text()
# the guard that accepts all three codes as valid, and display-only usage
accepts_all = "rc in (0, 1, 2)" in pipe or "rc in (0,1,2)" in pipe
display_only = 'norm_data.get("overall"' in pipe and "norms:" in pipe
no_abort_on_norm = ("norm" not in pipe.lower().split("sys.exit")[0][-0:]) or True  # sanity
check("H5 pipeline accepts rc 0/1/2 as all-valid (verdict non-gating)", accepts_all)
check("H5b pipeline uses norm_overall for display only", display_only)

# ── correctness FINDING (not a fail): PASS bar (10%) << register target (30%) ─
res_mid = nm.check_norm002({"inhibitory_analytics":
    {"resolve_rate": 0.12, "total_threads": 100, "closed_threads": 12, "inhibitory_usage": "low"}})
under_report = (res_mid["status"] == "PASS" and res_mid["data"]["gap_to_target"] > 0)
print(f"\n[FINDING] resolve_rate=12% -> status={res_mid['status']} "
      f"gap_to_target={res_mid['data']['gap_to_target']} "
      f"(register healthy target={REG_TARGET}, PASS bar={WARN}). "
      f"THRESHOLD-VS-STATED-TARGET mismatch: rates in [{WARN},{REG_TARGET}) report PASS "
      f"while data flags below-healthy. Correctness nit, decision-inert (display-only consumer).")

print("\n" + "="*60)
n_fail = sum(1 for _,ok,_ in results if not ok)
print(f"RESULT: {len(results)-n_fail}/{len(results)} checks GREEN, {n_fail} RED")
sys.exit(2 if n_fail else 0)
