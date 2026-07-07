import importlib.util, sys, types
from datetime import timezone
from pathlib import Path
S = Path("/sessions/determined-tender-rubin/mnt/OMPU_shared")
spec = importlib.util.spec_from_file_location("l3e", S/"tools"/"layer3_executive.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)

# freeze "now" so injected feed is always fresh
NOW = m.now_utc()
m.now_utc = lambda: NOW
def feed(msgs):
    return {"generated_at": NOW.isoformat(), "messages": msgs}

# spy on bus_post: capture, never actually post
posts = []
def spy_post(subject, body, dry_run=False):
    posts.append({"subject": subject, "body": body, "dry_run": dry_run})
    return {"ok": True, "msg_id": "SPY", "dry_run": dry_run}
m.bus_post = spy_post
m.load_executive_log = lambda: []      # no cooldown history
m.save_executive_log = lambda e: None  # no live write

def run(name, msgs):
    posts.clear()
    m.load_bus_live = lambda: feed(msgs)
    r = m.action_trend_watch(dry_run=True)  # dry so cooldown bypassed + no live write
    fired = not r.get("skipped")
    print(f"[{name}] skipped={r.get('skipped')} dominance={r.get('dominance')} "
          f"top={r.get('top_agent')} posts={len(posts)} "
          f"blocked_field={'blocked' in r or 'blocked_publication' in r}")
    if posts: print(f"        alert.subject={posts[0]['subject'][:70]!r}")
    return r, list(posts)

def M(frm): return {"from": frm, "subject":"x","body":"y"}

print("=== FAILABLE PROBE: action_trend_watch injectability + gate-reach ===")
# C1 clean diverse -> no alert
run("C1 diverse",      [M("nestor")]*3 + [M("petrovich")]*3 + [M("phi")]*4)
# C2 genuine single-agent dominance -> alert (real signal)
run("C2 genuine-dom",  [M("nestor")]*9 + [M("phi")]*1)
# C3 POISON force FALSE alert: flood one 'from' name from nothing
run("C3 poison-force", [M("phi")]*20)
# C4 POISON suppress genuine: dilute real dominant by injecting other 'from'
run("C4 poison-supp",  [M("nestor")]*9 + [M("fakeA")]*3 +[M("fakeB")]*3 +[M("fakeC")]*3)
# C5 bolt/executive excluded -> bolt flood cannot trigger
run("C5 bolt-excluded", [M("bolt")]*20 + [M("phi")]*1)

print("\n=== INVARIANT CHECK ===")
# does any returned dict carry a block/refuse/gate field?
for nm,msgs in [("dom",[M('phi')]*20)]:
    r,_ = run("inv "+nm, msgs)
    print("  keys:", sorted(r.keys()))
    print("  has any block/refuse/deny key:", any(k for k in r if 'block' in k.lower() or 'refuse' in k.lower() or 'deny' in k.lower() or 'gate' in k.lower()))
