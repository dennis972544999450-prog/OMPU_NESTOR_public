import importlib.util, sys, types
from pathlib import Path
S = Path("/sessions/dazzling-ecstatic-archimedes/mnt/OMPU_shared")
spec = importlib.util.spec_from_file_location("l3e_real", S/"tools"/"layer3_executive.py")
m = importlib.util.module_from_spec(spec); sys.modules["l3e_real"]=m; spec.loader.exec_module(m)

# spy bus_post — capture, never post
posts=[]
def spy_bus_post(subject, body, dry_run=False):
    posts.append({"subject":subject,"body":body,"dry_run":dry_run})
    return {"ok":True,"msg_id":None,"dry_run":True}
m.bus_post = spy_bus_post
# stub log I/O so no file touched
m.load_executive_log = lambda: []
m.save_executive_log = lambda log: None
m.hours_since_last_executive_action = lambda a,l: 999.0  # never rate-limited

GATE_KEYS={"block","blocked","refuse","refused","deny","denied","gate","gated","allow","forbid"}
def check(name, signal):
    posts.clear()
    r = m.action_health_alert(signal, dry_run=True)  # dry_run => no live post regardless
    fired = not r.get("skipped", False)
    badkeys = [k for k in r if k.lower() in GATE_KEYS]
    print(f"{name:34s} fired={str(fired):5s} posts={len(posts)} keys={sorted(r)} gate_keys={badkeys} alerts={r.get('alerts')}")
    return r, fired, badkeys

print("=== action_health_alert failable probe (gen-518) ===")
check("C1 healthy 50/40",         {"swarm_health":{"tempo":{"score":50},"diversity":{"score":40}}})
check("C2 low tempo 10/40",       {"swarm_health":{"tempo":{"score":10},"diversity":{"score":40}}})
check("C3 low diversity 50/5",    {"swarm_health":{"tempo":{"score":50},"diversity":{"score":5}}})
check("C4 MISSING swarm_health",  {})
check("C5 boundary 30/20",        {"swarm_health":{"tempo":{"score":30},"diversity":{"score":20}}})
check("C6 boundary 29/19",        {"swarm_health":{"tempo":{"score":29},"diversity":{"score":19}}})

# invariant summary + effector shape
print("\n=== invariant: no gate key in any output (checked inline above) ===")
print("bus_post is argv-list (subject/body separate argv, no shell) — see source L191-197")
