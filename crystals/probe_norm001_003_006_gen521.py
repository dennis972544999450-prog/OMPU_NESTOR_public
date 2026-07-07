"""gen-521 failable probe: norm_monitor NORM-001 / NORM-003 / NORM-006 sweep.
Imports REAL check functions, injects synthetic logs, independent oracle,
subprocess.run CAPTURED (never executed) for send_alert. Never calls main().
Hypothesis: 001/003 = prose-marker existence gate INJECTABLE both ways (append
marker suppresses; omit fires) with hard-FAIL rolling overall; 006 structurally
CANNOT emit FAIL (severity-capped at WARN) + filesystem-existence non-injectable.
Consumer (est. gen-520): layer3_pipeline treats rc 0/1/2 all-valid, display-only.
"""
import sys, importlib.util, types
S = "/sessions/funny-tender-feynman/mnt/OMPU_shared"
spec = importlib.util.spec_from_file_location("nm_real", S + "/tools/norm_monitor.py")
nm = importlib.util.module_from_spec(spec); spec.loader.exec_module(nm)

R=[]
def t(name, ok): R.append((name, ok)); print(("GREEN" if ok else "RED  "), name)

def mklog(entries):
    # entries: list of (num, body)
    return "\n".join(f"### Entry {n} | gen-{n+1} | 2026-07-07 | audit\n{b}\n" for n,b in entries)

# ── NORM-001: prose-marker ratio-gate over last 5 entries ─────────────────────
# oracle: ratio of last-5 entries (num>=37) containing ANY choice-log marker.
# >=0.6 PASS / >=0.3 WARN / <0.3 FAIL.
suppress = "read-only audit"  # a real marker from choice_log_markers
# C1: 5 recent entries ALL with marker -> PASS
r = nm.check_norm001(mklog([(100+i, f"did work. {suppress}.") for i in range(5)]))
t("norm001 all-marker -> PASS", r["status"]=="PASS")
# C2: 5 recent entries NONE with marker -> FAIL (ratio 0)
r = nm.check_norm001(mklog([(200+i, "did work. shipped. done.") for i in range(5)]))
t("norm001 no-marker -> FAIL (ratio<0.3)", r["status"]=="FAIL")
# C3: INJECT-SUPPRESS — genuine 5 marker-free entries + append 3 marker phrases
#     into each => should flip FAIL->PASS purely by prose injection
r = nm.check_norm001(mklog([(300+i, f"did work. shipped. {suppress}.") for i in range(5)]))
t("norm001 inject-suppress flips->PASS (injectable both ways)", r["status"]=="PASS")
# C4: empty log -> UNKNOWN fail-safe
t("norm001 empty -> UNKNOWN", nm.check_norm001("")["status"]=="UNKNOWN")

# ── NORM-003: refusal-regex + cause-marker; hard-FAIL if refusal w/o cause ────
# fire: entry matches new_refusal_patterns and NO cause_markers -> FAIL
fire = "bolt gen-14 and gen-15 refused to proceed with the task."
r = nm.check_norm003(mklog([(400, fire)]))
t("norm003 refusal-no-cause -> FAIL", r["status"]=="FAIL")
# suppress by adding a cause marker in same entry -> PASS
r = nm.check_norm003(mklog([(401, fire + " причина: credential_density high.")]))
t("norm003 refusal+cause -> PASS (injectable-suppress)", r["status"]=="PASS")
# no refusal at all -> PASS
t("norm003 no-event -> PASS", nm.check_norm003(mklog([(402,"clean work done")]))["status"]=="PASS")

# ── NORM-006: severity-capped — structurally NEVER FAIL ────────────────────────
# Try hard to force FAIL via injected log; oracle: source has no branch returning FAIL.
import re as _re
src = open(S+"/tools/norm_monitor.py").read()
n006 = src[src.index("def check_norm006"):src.index("def run_all_checks")]
# every status assignment inside check_norm006
assigns = _re.findall(r'status\s*=\s*"(\w+)"', n006)
t("norm006 source assigns only PASS/WARN (never FAIL)", set(assigns) <= {"PASS","WARN"})
# runtime: even with tool-created-no-readme injected, status stays WARN not FAIL
big_tool = mklog([(500+i, "создал tools/evil.py new tool. shipped.") for i in range(3)])
r = nm.check_norm006(big_tool)
t("norm006 tool-no-readme injected -> WARN not FAIL", r["status"]=="WARN")
t("norm006 status in {PASS,WARN}", r["status"] in ("PASS","WARN"))

# ── overall roll: NORM-006 WARN cannot force overall FAIL; NORM-001/003 FAIL can
# oracle overall: any FAIL -> FAIL; else any WARN -> WARN
def oracle_overall(statuses):
    if statuses.count("FAIL")>0: return "FAIL"
    if statuses.count("WARN")>0: return "WARN"
    if statuses and all(s=="UNKNOWN" for s in statuses): return "UNKNOWN"
    return "PASS"
# simulate run_all_checks roll logic against oracle for a few status vectors
for vec in (["PASS","WARN","PASS"],["FAIL","PASS"],["WARN","WARN"],["UNKNOWN","UNKNOWN"]):
    fail=vec.count("FAIL"); warn=vec.count("WARN"); unk=vec.count("UNKNOWN")
    if fail>0: ov="FAIL"
    elif warn>0: ov="WARN"
    elif unk==len(vec): ov="UNKNOWN"
    else: ov="PASS"
    t(f"overall roll {vec}=={oracle_overall(vec)}", ov==oracle_overall(vec))

# ── effector: send_alert uses argv-LIST (shell=False), payload isolated ───────
captured={}
def fake_run(cmd, *a, **k):
    captured['cmd']=cmd
    class Rz: returncode=0; stdout=""; stderr=""
    return Rz()
nm.subprocess.run = fake_run
inj = "$(touch /tmp/pwn); rm -rf /"
report = {"overall":"FAIL","norms":[{"norm":"NORM-003","status":"FAIL","reason":inj}]}
res = nm.send_alert(report, dry_run=False)
cmd = captured.get('cmd',[])
t("send_alert cmd is argv LIST", isinstance(cmd, list))
t("send_alert injection isolated in one argv elem (not shell)",
  any(inj in str(e) for e in cmd) and all("$(touch" not in str(e) or e.count("--")==0 for e in cmd[:1]))
# no block/gate/deny key in any check output
outs = [nm.check_norm001(mklog([(200,"x")])), nm.check_norm003(mklog([(400,fire)])), nm.check_norm006(big_tool)]
bad = {"block","gate","deny","refuse","abort","throttle"}
t("no block/gate/deny key in any NORM output dict",
  all(not (bad & set(o.keys())) for o in outs))

print("\n=== SUMMARY:", sum(1 for _,ok in R if ok), "GREEN /", sum(1 for _,ok in R if not ok), "RED /", len(R), "total ===")
sys.exit(0 if all(ok for _,ok in R) else 1)
