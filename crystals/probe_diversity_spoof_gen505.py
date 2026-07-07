import importlib.util, sys, datetime
S="/sessions/blissful-sleepy-planck/mnt/OMPU_shared"
def load(name, path):
    spec=importlib.util.spec_from_file_location(name, path)
    m=importlib.util.module_from_spec(spec); sys.modules[name]=m; spec.loader.exec_module(m); return m

sd=load("swarm_driver", f"{S}/tools/swarm_driver.py")
l3=load("layer3_executive", f"{S}/tools/layer3_executive.py")
today=datetime.datetime.utcnow().strftime('%Y-%m-%d')

def health_from_agentday(agent_day_today):
    bus_graph={'activity_by_day':{today:sum(agent_day_today.values())},
               'agent_day':{today:agent_day_today}}
    log_data={'entry_count':500}
    return sd.compute_swarm_health(log_data, bus_graph)

# CLEAN: one honest active day, 2 real agents
clean=health_from_agentday({'nestor':9,'bolt':3})
# SPOOF-INFLATE: attacker injects many fake distinct `from` names (but capped by most_common(5) upstream -> simulate 5)
spoof=health_from_agentday({'a':1,'b':1,'c':1,'d':1,'e':1})
# SPOOF-DEFLATE attempt: can attacker force len=0? only an EMPTY day (no msgs). No `from` to spoof.
empty=health_from_agentday({})

for name,h in [("CLEAN 2 real",clean),("SPOOF 5 fake",spoof),("EMPTY day",empty)]:
    d=h['diversity']['score']; print(f"{name:14} diversity={d}")

def run_alert(h):
    sig={'swarm_health':h}
    return l3.action_health_alert(sig, dry_run=True)

print("--- action_health_alert(dry_run) ---")
for name,h in [("CLEAN 2 real",clean),("SPOOF 5 fake",spoof),("EMPTY day",empty)]:
    r=run_alert(h)
    fired = not r.get('skipped', False)
    print(f"{name:14} skipped={r.get('skipped',False)} alerts={r.get('alerts','-')}")

# The failable question: can spoofing `from` FLIP the diversity-alert (fire it falsely OR suppress a real one)?
# To FIRE low-diversity alert need diversity<20 i.e. len(today_agents)==0 (score min(100,0)=0).
# But len==0 requires ZERO messages that day -> no `from` field exists to spoof.
# Any single real post -> len>=1 -> score>=20 -> branch unreachable. Spoof only ADDS -> can't reduce.
print("\nCONCLUSION: diversity-alert branch fires only at len(today_agents)==0 (empty day).")
print("Spoofing `from` is INJECTION-ONLY (adds unique names) -> can only INFLATE diversity -> never fires the alert;")
print("and suppression is moot (any genuine post already yields score>=20). Decision UNFLIPPABLE by from-spoof.")
