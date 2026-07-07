#!/usr/bin/env python3
"""gen-506 failable probe: can a `today_msgs` volume-spoof FLIP the tempo<30 health alert?
Runs REAL swarm_driver.compute_swarm_health + layer3_executive.action_health_alert(dry_run=True)."""
import importlib.util, sys, datetime
S = "/sessions/vigilant-vibrant-wozniak/mnt/OMPU_shared"
sys.path.insert(0, S + "/tools")

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

sd = load("swarm_driver", S + "/tools/swarm_driver.py")
l3 = load("layer3_executive", S + "/tools/layer3_executive.py")

today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
# realistic 7d history: ~10 msgs/day median baseline
hist = {"2026-07-01":10,"2026-07-02":12,"2026-07-03":9,"2026-07-04":11,
        "2026-07-05":10,"2026-07-06":13}
log_stub = {"entry_count": 505}

def run(label, today_msgs):
    activity = dict(hist); activity[today] = today_msgs
    # agent_day must be non-empty so diversity>=20 and we isolate tempo
    bus_graph = {"activity_by_day": activity,
                 "agent_day": {today: {"nestor":5,"bolt":3,"petrovich":2}}}
    health = sd.compute_swarm_health(log_stub, bus_graph)
    signal = {"swarm_health": health}
    res = l3.action_health_alert(signal, dry_run=True)
    t = health['tempo']['score']; d = health['diversity']['score']
    fired = "alerts" in res and res.get("alerts")
    print(f"{label:32} today={today_msgs:>4}  tempo={t:>3}  div={d:>3}  "
          f"median={health['tempo']['median_7d']}  -> {'ALERT FIRES' if fired else 'skipped'}"
          f"  {res.get('alerts', res.get('reason',''))}")

print(f"today-date={today}  median baseline ~10-11\n")
run("QUIET DAY (genuine low)", 2)      # tempo ~18-20 -> should FIRE
run("CLEAN normal", 11)                # tempo ~100 -> skipped
run("VOLUME-SPOOF (flood today)", 999) # inject many -> tempo clamps 100 -> skipped
run("EMPTY today (0 msgs)", 0)         # tempo 0 -> FIRE (but 0 msgs = nothing to spoof)
print("\nKEY: injection only ADDS to today_msgs (numerator) -> monotone-UP tempo -> can only SUPPRESS.")
print("     Fire-side is LOW tempo (quiet day) = FEWER msgs = UNREACHABLE by injection.")
print("     median denominator uses server-dated past days (sent_at=server clock, gen-503) -> not backfillable.")
