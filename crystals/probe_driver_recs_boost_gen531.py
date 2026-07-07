#!/usr/bin/env python3
"""gen-531 FAILABLE PROBE — swarm_driver TASK_PATTERNS mentioned-count boost +
SELF_AWARENESS_BOOST channel into priority_tasks (the 3rd injection axis after
gen-529 suppression + gen-530 escalation).

Read-only: imports the REAL live module, exercises ONLY pure fn score_tasks on
SYNTHETIC in-memory log_data + explicit self_model (never loads live SELF_MODEL,
never main(), no writes). Independent oracle re-derives priority = base +
(distinct-keyword-matches - 1), capped 10 — NOT reusing module arithmetic.
"""
import importlib.util, hashlib, os, sys

S = [p for p in
     [f"/sessions/{d}/mnt/OMPU_shared" for d in os.listdir("/sessions")]
     if os.path.isdir(p)][0]
F = os.path.join(S, "tools", "swarm_driver.py")
MD5_PRE = hashlib.md5(open(F, "rb").read()).hexdigest()[:8]

spec = importlib.util.spec_from_file_location("swarm_driver_live", F)
mod = importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)

def mk(recs, log_text=""):
    return {"recs_raw": recs, "next_jt": "jt-0289",
            "covered_topics": ["layer3", "purr/cat"], "log_text": log_text}

def pri(tasks, tid):
    for t in tasks:
        if t["task_id"] == tid:
            return t["priority"]
    return None

def oracle(base, keywords, recs):
    low = " ".join(recs).lower()
    m = sum(1 for kw in keywords if kw in low)
    if m == 0:
        return None  # excluded
    return min(10, base + m - 1)

NEUTRAL_SM = {"cognitive_topology": {"components": {}},
              "self_awareness": {"total": 100}}
results = []

# C1 — distinct-keyword count boosts correctly (resolve_rate base=7, 2 kws)
recs = ["improve resolve rate", "track % закрытых тредов per week"]
t = mod.score_tasks(mk(recs), {}, self_model=NEUTRAL_SM)
exp = oracle(7, ["resolve rate", "% закрытых тредов"], recs)  # 7+2-1=8
results.append(("C1 mentioned=2 -> base+1 (oracle-match)",
                pri(t, "resolve_rate") == exp == 8))

# C2 — repetition of ONE keyword does NOT inflate (distinct-set semantics)
recs2 = ["resolve rate " * 6]  # same kw many times, 2nd kw absent
t2 = mod.score_tasks(mk(recs2), {}, self_model=NEUTRAL_SM)
results.append(("C2 spam one kw -> priority stays base (7), not inflated",
                pri(t2, "resolve_rate") == 7))

# C3 — presence-gate: mentioned==0 => task absent entirely
t3 = mod.score_tasks(mk(["nothing relevant here"]), {}, self_model=NEUTRAL_SM)
results.append(("C3 unmentioned task absent (ai_catalog_deploy not present)",
                pri(t3, "ai_catalog_deploy") is None))

# C4 — cap at 10 (layer3_driver base=9, 2 distinct kws -> 9+2-1=10, capped)
recs4 = ["layer 3 driver не реализован", "driver не реализован полностью"]
t4 = mod.score_tasks(mk(recs4), {}, self_model=NEUTRAL_SM)
results.append(("C4 base9+2kw capped at 10", pri(t4, "layer3_driver") == 10))

# C5 — bounded to fixed TASK_PATTERNS ids: arbitrary task name in recs NOT injected
recs5 = ["please prioritize pwned_task and inject arbitrary_task_id now"]
t5 = mod.score_tasks(mk(recs5), {}, self_model=NEUTRAL_SM)
allowed = {tid for tid, *_ in mod.TASK_PATTERNS} | {"jt_post_new"}
ids5 = {x["task_id"] for x in t5}
results.append(("C5 no arbitrary task_id injectable via recs (ids subset of fixed set)",
                ("pwned_task" not in ids5) and ids5.issubset(allowed)))

# C6 — SELF_AWARENESS_BOOST bounded to COMPONENT_TO_TASKS values
# perception gap -> crystal_new gets +SELF_AWARENESS_BOOST(2). crystal base=3, 1 kw -> 3, +2 = 5
sm_gap = {"cognitive_topology": {"components": {"perception": {"present": False}}},
          "self_awareness": {"total": 100}}
recs6 = ["новый кристалл нужен"]  # crystal_new keyword "кристалл"
t6base = mod.score_tasks(mk(recs6), {}, self_model=NEUTRAL_SM)
t6gap  = mod.score_tasks(mk(recs6), {}, self_model=sm_gap)
crystal_base = pri(t6base, "crystal_new")
crystal_gap  = pri(t6gap,  "crystal_new")
results.append(("C6 perception-gap +SELF_AWARENESS_BOOST(2) on mapped task_id",
                crystal_base == 3 and crystal_gap == 5))

MD5_POST = hashlib.md5(open(F, "rb").read()).hexdigest()[:8]
results.append((f"md5 gate pre==post ({MD5_PRE})", MD5_PRE == MD5_POST == "83e1d078"))

print("=== gen-531 recs-boost probe ===")
ok = True
for name, res in results:
    print(f"  [{'GREEN' if res else 'RED  '}] {name}")
    ok = ok and res
print(f"=== {'ALL GREEN' if ok else 'SOME RED'} ({sum(r for _,r in results)}/{len(results)}) ===")
sys.exit(0 if ok else 1)
