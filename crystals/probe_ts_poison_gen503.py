import importlib.util, sys, copy
from datetime import datetime, timezone
spec = importlib.util.spec_from_file_location("l3", "layer3_executive.py")
l3 = importlib.util.module_from_spec(spec); spec.loader.exec_module(l3)

now = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
# Build a snapshot where 'nestor' would dominate (>80%): 9 nestor + 1 petrovich
base_msgs = [{"from":"nestor","sent_at":now,"msg_id":f"n{i}","subject":"s"} for i in range(9)]
base_msgs += [{"from":"petrovich","sent_at":now,"msg_id":"p0","subject":"s"}]
snap_clean = {"generated_at": now, "messages": copy.deepcopy(base_msgs)}

# POISON: same messages, but flip ONE petrovich msg's sent_at to year 9999 (fabricated future)
poison_msgs = copy.deepcopy(base_msgs)
poison_msgs[-1]["sent_at"] = "9999-12-31T23:59:59Z"
# also reverse order to simulate sort-to-top effect
poison_msgs = list(reversed(poison_msgs))
snap_poison = {"generated_at": now, "messages": poison_msgs}

def run(snap):
    orig = l3.load_bus_live
    l3.load_bus_live = lambda: snap
    try:
        r = l3.action_trend_watch(dry_run=True)
    finally:
        l3.load_bus_live = orig
    return r

r_clean  = run(snap_clean)
r_poison = run(snap_poison)

def decision(r):
    # the decision-relevant fields: skipped?, dominant agent, dominance, whether alert
    return {k: r.get(k) for k in ("skipped","reason") if k in r} | \
           {"alert": r.get("alert", r.get("posted", None)),
            "dominance": r.get("dominance"), "top_agent": r.get("top_agent"),
            "agent_counts": r.get("agent_counts")}

print("CLEAN :", decision(r_clean))
print("POISON:", decision(r_poison))
print("DECISION IDENTICAL:", decision(r_clean) == decision(r_poison))

# Extra: malformed / empty sent_at must not crash the consumer
bad = copy.deepcopy(base_msgs); bad[0]["sent_at"]=""; bad[1].pop("sent_at",None)
try:
    rb = run({"generated_at": now, "messages": bad})
    print("MALFORMED-SENT_AT-SAFE: no crash ; skipped=", rb.get("skipped"), "top=", rb.get("top_agent"))
except Exception as e:
    print("MALFORMED CRASH:", repr(e))

# Extra: poisoned generated_at (future) -> freshness gate behaviour
rf = run({"generated_at":"9999-12-31T23:59:59Z","messages":copy.deepcopy(base_msgs)})
print("FUTURE generated_at -> skipped=", rf.get("skipped"), "reason=", (rf.get("reason") or "")[:60])
rm = run({"generated_at":"not-a-date","messages":copy.deepcopy(base_msgs)})
print("MALFORMED generated_at -> skipped=", rm.get("skipped"), "reason=", (rm.get("reason") or "")[:60])
