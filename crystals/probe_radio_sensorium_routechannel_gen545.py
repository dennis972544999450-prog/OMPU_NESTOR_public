#!/usr/bin/env python3
"""gen-545 probe: radio_sensorium route/classify decision-channel.
PURE functions only (classify, route_for) on SYNTHETIC dicts.
NEVER calls build_report/fetch_json/main (those hit live network + read live files).
Confirms: route is display/record-only; injectable inputs flip route with NO side effect;
first-match precedence + SENSOR_BLIND masking nuance."""
import glob, hashlib, importlib.util, os, sys, tempfile

S = glob.glob("/sessions/*/mnt/OMPU_shared")[0]
TARGET = os.path.join(S, "jsontube/studio/radio/radio_sensorium.py")

def md5(p):
    return hashlib.md5(open(p,'rb').read()).hexdigest()[:8]

pre = md5(TARGET)
spec = importlib.util.spec_from_file_location("rs_probe", TARGET)
rs = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rs)   # module import: no network at import time (all fetch is inside fns)

results = []
def check(name, cond):
    results.append((name, bool(cond)))
    print(("PASS" if cond else "FAIL"), name)

def rep(**over):
    """minimal report skeleton classify() reads."""
    base = {
        "public_radio": {"ok": True, "mode": "m1", "lead_post_id": "jt-0001", "updated_at": None},
        "public_feed":  {"latest_post_id": "jt-0001"},
        "local_posts":  {"latest_post_id": "jt-0001"},
        "local_current":{"mode": "m1", "lead_post_id": "jt-0001"},
        "drafts_and_logs": {"intent_debt_count": 0},
        "aircheck": {"automation_status": "ACTIVE", "latest_age_hours": 0.5},
    }
    for k,v in over.items():
        base[k] = {**base[k], **v} if isinstance(v, dict) else v
    return base

# 1. route_for is a PURE dict transform: same states -> same output, no I/O
r1 = rs.route_for(["INTENT_DEBT"])
r2 = rs.route_for(["INTENT_DEBT"])
check("route_for deterministic pure (no side effect)", r1 == r2 and r1["route"] == "routing_replacement")

# 2. FIRST-MATCH precedence: PUBLIC_SPLIT beats everything below
r = rs.route_for(["INTENT_DEBT","SENSOR_BLIND","PUBLIC_SPLIT"])
check("precedence: PUBLIC_SPLIT wins over lower states", r["route"] == "deploy_diagnosis")

# 3. SENSOR_BLIND MASKING nuance: blind sensor co-present with INTENT_DEBT -> blind is SUPPRESSED,
#    route reported as routing_replacement while the sensor is actually blind (real display nuance)
r = rs.route_for(["INTENT_DEBT","SENSOR_BLIND"])
check("nuance: SENSOR_BLIND masked when INTENT_DEBT present", r["route"] == "routing_replacement" and "SENSOR_BLIND" not in r["route"])

# 4. empty states -> observe fallback
check("empty -> observe fallback", rs.route_for([])["route"] == "observe")

# 5. INJECTABLE: forged draft intent-debt flips classify -> INTENT_DEBT (attacker-writable drafts dir)
s_clean = rs.classify(rep())
s_forged = rs.classify(rep(drafts_and_logs={"intent_debt_count": 7}))
check("injectable: forged intent_debt_count flips state", "INTENT_DEBT" not in s_clean and "INTENT_DEBT" in s_forged)

# 6. but flip has NO side effect: classify returns list, mutates nothing on disk
snap = rep(drafts_and_logs={"intent_debt_count": 7})
_ = rs.classify(snap)
check("classify side-effect-free (input dict untouched keys)", snap["drafts_and_logs"]["intent_debt_count"] == 7)

# 7. SENSOR_BLIND raised when aircheck stale (>2.5h) or automation not ACTIVE
check("SENSOR_BLIND on stale aircheck", "SENSOR_BLIND" in rs.classify(rep(aircheck={"automation_status":"ACTIVE","latest_age_hours":9.0})))
check("SENSOR_BLIND on inactive automation", "SENSOR_BLIND" in rs.classify(rep(aircheck={"automation_status":"MISSING","latest_age_hours":0.1})))

# 8. AST: no effector reachable from classify/route_for (they only do comparisons/dict-build)
import ast
tree = ast.parse(open(TARGET).read())
def fn(name):
    return next(n for n in ast.walk(tree) if isinstance(n, ast.FunctionDef) and n.name==name)
def calls_in(node):
    return {c.func.attr for c in ast.walk(node) if isinstance(c, ast.Call) and isinstance(c.func, ast.Attribute)}
route_calls = calls_in(fn("route_for")) | calls_in(fn("classify"))
bad = route_calls & {"run","system","remove","replace","unlink","rename","urlopen","write","mkdir"}
check("AST: classify+route_for call NO effector/network/write", not bad)

# 9. record() is the ONLY writer and gated behind --record; writes to JSONL nothing reads (confirmed by grep externally)
rec_calls = calls_in(fn("record"))
check("record() writes only (mkdir+write to jsonl), no exec/network", "run" not in rec_calls and "urlopen" not in rec_calls)

post = md5(TARGET)
check(f"md5 unchanged pre==post ({pre})", pre == post)

ok = sum(1 for _,c in results if c)
print(f"\n{ok}/{len(results)} GREEN  md5={pre}")
sys.exit(0 if ok == len(results) else 1)
