#!/usr/bin/env python3
"""gen-527 POST-LAND-DIVERGENT-VERIFY of nestor gen-0984: bus_refresh_guard wired
into layer3_pipeline Stage -1. Guard body md5 UNCHANGED (a27f3ecd) => 3 new-surface
properties to prove at the NEW call-site (handoff gen-526 §2):
  (a) predicate still trigger-only  (guard unchanged; call is bare refresh_if_stale())
  (b) guard never-raises from the new call-site (guard + call-site try/except)
  (c) added cadence-caller does NOT gate wake on refresh-failure
Two-part: PART A source/AST proof of non-gating; PART B behavioral proof guard
never-raises under a failing analyzer (real guard in mkdtemp sandbox, stub analyzer,
LIVE BUS NEVER TOUCHED). Independent oracle from the contract, not module branch order.
"""
import ast, os, sys, shutil, tempfile, importlib.util

S = "/sessions/epic-wizardly-mayer/mnt/OMPU_shared"
PIPE = os.path.join(S, "tools", "layer3_pipeline.py")
GUARD = os.path.join(S, "tools", "bus_refresh_guard.py")
results = []
def check(name, cond, detail=""):
    results.append((name, bool(cond), detail))

# ---------- PART A: source/AST non-gating proof on the LANDED pipeline ----------
src = open(PIPE).read()
tree = ast.parse(src)

def find_func(name):
    return next((n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name == name), None)

run_pipeline = find_func("run_pipeline")
main_fn = find_func("main")

# A1: run_pipeline has NO sys.exit / raise anywhere (a stage cannot abort the run)
rp_exits = [n for n in ast.walk(run_pipeline)
            if (isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute)
                and n.func.attr == "exit")
            or isinstance(n, ast.Raise)]
check("A1 run_pipeline has zero sys.exit/raise (no stage can abort wake)", len(rp_exits) == 0,
      f"found {len(rp_exits)}")

# A2: main() normal path -> only sys.exit is guarded by args.test
exits_in_main = [n for n in ast.walk(main_fn)
                 if isinstance(n, ast.Call) and isinstance(n.func, ast.Attribute) and n.func.attr == "exit"]
# every sys.exit in main must be inside an `if args.test:` block
def inside_test_guard(node, root):
    for n in ast.walk(root):
        if isinstance(n, ast.If):
            t = n.test
            is_test = (isinstance(t, ast.Attribute) and t.attr == "test")
            if is_test and any(node is d for d in ast.walk(n)):
                return True
    return False
all_gated = all(inside_test_guard(e, main_fn) for e in exits_in_main)
check("A2 every sys.exit in main() is under `if args.test` (normal run exits 0)",
      all_gated and len(exits_in_main) >= 1, f"{len(exits_in_main)} exits, all under --test={all_gated}")

# A3: Stage -1 block wrapped in try/except Exception with a status='skipped' fallback
has_guard_try = False
for n in ast.walk(run_pipeline):
    if isinstance(n, ast.Try):
        seg = ast.get_source_segment(src, n) or ""
        if "refresh_if_stale" in seg:
            catches_all = any(
                (h.type is None) or (isinstance(h.type, ast.Name) and h.type.id == "Exception")
                for h in n.handlers)
            has_skip = "skipped" in seg
            has_guard_try = catches_all and has_skip
check("A3 Stage -1 wrapped in try/except Exception -> status 'skipped' fallback", has_guard_try)

# A4: rc!=0 maps to 'warn' (NOT 'error'); no abort keyword tied to the stage
seg_all = src
stage_line = next((l for l in src.splitlines() if "_rg.get(\"rc\"" in l), "")
check("A4 refresh-fail -> 'warn' not 'error' (non-fatal)", '"warn"' in stage_line and '"error"' not in stage_line, stage_line.strip())

# A5: run_tests has NO assertion requiring bus_refresh_guard status == ok
run_tests = find_func("run_tests")
rt_src = ast.get_source_segment(src, run_tests) if run_tests else ""
check("A5 run_tests does not assert bus_refresh_guard status (can't fail --test)",
      "bus_refresh_guard" not in rt_src)

# ---------- PART B: behavioral never-raise of the real guard under failing analyzer ----------
# INDEPENDENT ORACLE: on stale+analyzer-fails, contract says return a status dict with
# rc==2 and NEVER raise. Copy guard into sandbox so its __file__-derived ANALYZER/BUS_DIR
# point at sandbox stubs; live bus is never opened.
sandbox = tempfile.mkdtemp(prefix="probe527_")
try:
    g2 = os.path.join(sandbox, "bus_refresh_guard.py")
    shutil.copy(GUARD, g2)
    # stub analyzer that ALWAYS fails (rc!=0) — proves rc2 no-raise from the fail path
    open(os.path.join(sandbox, "bus_analyzer.py"), "w").write("import sys\nsys.exit(3)\n")
    # sandbox bus dir: bus_live older than feed => STALE => guard will invoke analyzer(=fail)
    busdir = os.path.join(sandbox, "..", "bus")
    # guard derives BUS_DIR from __file__ (tools/../bus) — create it
    bd = os.path.abspath(os.path.join(sandbox, "..", "bus"))
    os.makedirs(bd, exist_ok=True)
    import json as _j
    open(os.path.join(bd, "bus_live.json"), "w").write(_j.dumps({"messages":[{"sent_at":"2020-01-01T00:00:00Z"}]}))
    open(os.path.join(bd, "feed.jsonl"), "w").write(_j.dumps({"sent_at":"2030-01-01T00:00:00Z"})+"\n")
    spec = importlib.util.spec_from_file_location("guard_sb", g2)
    guard_sb = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard_sb)
    raised = None; out = None
    try:
        out = guard_sb.refresh_if_stale()
    except Exception as e:
        raised = e
    check("B1 guard NEVER raises even when analyzer fails (rc!=0)", raised is None, repr(raised))
    check("B2 failing-refresh returns rc==2 status dict (contract)",
          isinstance(out, dict) and out.get("rc") == 2, repr(out)[:120])
    # oracle: bare call => force not set => predicate is trigger-only (feed>live drove it)
    check("B3 stale predicate fired via feed>live (trigger-only, no force)",
          isinstance(out, dict) and out.get("action") in ("refresh-failed","refreshed","stale"), repr(out.get("action")))
finally:
    shutil.rmtree(sandbox, ignore_errors=True)
    shutil.rmtree(os.path.abspath(os.path.join(sandbox, "..", "bus")), ignore_errors=True)

# md5 gate: neither live file mutated by this probe
import hashlib
def md5(p): return hashlib.md5(open(p,"rb").read()).hexdigest()[:8]
check("MD5 pipeline unchanged 8b8fb791", md5(PIPE) == "8b8fb791", md5(PIPE))
check("MD5 guard unchanged a27f3ecd", md5(GUARD) == "a27f3ecd", md5(GUARD))

print("="*60)
p = sum(1 for _,c,_ in results if c)
for name, c, det in results:
    print(f"  {'GREEN' if c else 'RED  '}  {name}" + (f"   [{det}]" if det and not c else ""))
print("="*60)
print(f"{p}/{len(results)} GREEN")
sys.exit(0 if p == len(results) else 1)
