#!/usr/bin/env python3
"""
gen-524 FAILABLE PROBE — the VALUE-INJECTION angle on compute_swarm_health.

Producer chain under test:
  feed.jsonl -> build_graph -> timeline
    -> activity_by_day(timeline)      [today_msgs counter]
    -> activity_by_agent_day(timeline)[today_agents counter]
  -> compute_swarm_health -> swarm_health.tempo.score / diversity.score
  -> DRIVER_SIGNAL.swarm_health
  -> layer3_executive.action_health_alert firing gate:
        (tempo_score >= 30 AND diversity_score >= 20) => SKIP, else POST advisory

CLAIM (failable): the two counters activity_by_day[today] and len(agent_day[today])
are FEED-INJECTABLE (any agent posting today raises today_msgs; posting under N
distinct 'from' names raises today_agents), so the health_alert firing gate can be
driven BOTH ways by feed content -> refines gen-518 'non-injectable' (that was the
layer3 STRUCTURAL score; tempo/diversity ARE injectable).

GREEN/RED decider: is the effector a decision/gate or a non-blocking advisory with
no automated consumer? Independent oracle re-derives scores + firing predicate from
NORM spec, NOT module branch order. NO feed I/O, NO live post (dry_run=True only,
which bus_post short-circuits before any subprocess). NO file mutation.
"""
import importlib.util, sys, hashlib
from pathlib import Path

S = Path("/sessions/eager-focused-curie/mnt/OMPU_shared/tools")

def md5(p):
    return hashlib.md5(Path(p).read_bytes()).hexdigest()[:8]

def load(name, path):
    spec = importlib.util.spec_from_file_location(name, path)
    m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m); return m

ba_path = S / "bus_analyzer.py"
sd_path = S / "swarm_driver.py"
le_path = S / "layer3_executive.py"
pre = {"bus_analyzer": md5(ba_path), "swarm_driver": md5(sd_path), "layer3_executive": md5(le_path)}

ba = load("ba", ba_path)
sd = load("sd", sd_path)
le = load("le", le_path)

from datetime import datetime
TODAY = datetime.utcnow().strftime('%Y-%m-%d')

def make_timeline(today_msgs, today_agents, hist=None):
    """Synthetic timeline: list of (date_str, agent, is_broadcast)."""
    tl = []
    # historical days to set a median baseline (~10/day for 6 days)
    hist = hist if hist is not None else {"2026-06-24": 10, "2026-06-25": 10,
        "2026-06-26": 10, "2026-06-27": 10, "2026-06-28": 10, "2026-06-29": 10}
    for d, c in hist.items():
        for i in range(c):
            tl.append((d, f"agent{i%3}", True))
    # today: today_msgs messages spread across today_agents distinct names
    for i in range(today_msgs):
        tl.append((TODAY, f"tagent{i % max(today_agents,1)}", True))
    return tl

def build_health(timeline):
    abd = ba.activity_by_day(timeline)
    aad = ba.activity_by_agent_day(timeline)
    bus_graph = {"activity_by_day": abd, "agent_day": aad}
    log_data = {"entry_count": 20}  # only used by archive score, irrelevant here
    return sd.compute_swarm_health(log_data, bus_graph), abd, aad

# ---- Independent oracle (re-derive from spec, not module) ----
def oracle_tempo(abd):
    today_msgs = abd.get(TODAY, 0)
    recent = [v for k, v in abd.items() if k >= '2026-06-23']
    median = sorted(recent)[len(recent)//2] if recent else 1
    return min(100, int(today_msgs / max(median, 1) * 100))

def oracle_div(aad):
    today_agents = aad.get(TODAY, {})
    return min(100, len(today_agents) * 20)

def oracle_fires(tempo, div):
    # action_health_alert: skip iff tempo>=30 AND div>=20; else it fires (posts advisory)
    return not (tempo >= 30 and div >= 20)

results = []
def check(name, cond, detail=""):
    results.append((name, cond, detail))
    print(f"[{'GREEN' if cond else 'RED  '}] {name} {detail}")

# ---- Cases ----
# C1: quiet today (2 msgs vs median 10) -> tempo ~20 < 30 -> alert FIRES
tl = make_timeline(today_msgs=2, today_agents=1)
h, abd, aad = build_health(tl)
t, d = h['tempo']['score'], h['diversity']['score']
ot, od = oracle_tempo(abd), oracle_div(aad)
check("C1 module tempo==oracle", t == ot, f"(mod={t} orc={ot})")
check("C1 module div==oracle", d == od, f"(mod={d} orc={od})")
check("C1 low tempo -> oracle says FIRES", oracle_fires(t, d), f"(tempo={t},div={d})")

# C2: FLOOD today (40 msgs) -> tempo saturates 100 >=30 -> alert SUPPRESSED (inject-suppress)
tl = make_timeline(today_msgs=40, today_agents=5)
h, abd, aad = build_health(tl)
t, d = h['tempo']['score'], h['diversity']['score']
check("C2 flood -> tempo>=30 (feed-injectable UP)", t >= 30, f"(tempo={t})")
check("C2 flood -> oracle says SUPPRESSED", not oracle_fires(t, d), f"(tempo={t},div={d})")
check("C2 module tempo==oracle", t == oracle_tempo(abd), f"(mod={t} orc={oracle_tempo(abd)})")

# C3: diversity injection — 0 today agents vs many
tl0 = make_timeline(today_msgs=0, today_agents=0)
h0, abd0, aad0 = build_health(tl0)
check("C3a no activity today -> div 0", h0['diversity']['score'] == 0, f"(div={h0['diversity']['score']})")
tl5 = make_timeline(today_msgs=20, today_agents=5)
h5, abd5, aad5 = build_health(tl5)
check("C3b 5 distinct 'from' -> div>=20 (feed-injectable)", h5['diversity']['score'] >= 20,
      f"(div={h5['diversity']['score']})")
check("C3b module div==oracle", h5['diversity']['score'] == oracle_div(aad5),
      f"(mod={h5['diversity']['score']} orc={oracle_div(aad5)})")

# C4: EMPTY bus_graph -> compute_swarm_health omits tempo/diversity -> action defaults 100 -> SKIP (fail-safe)
h_empty = sd.compute_swarm_health({"entry_count": 20}, {})
check("C4 empty bus_graph -> no tempo key (fail-safe)", 'tempo' not in h_empty,
      f"(keys={sorted(h_empty.keys())})")
sig_empty = {"swarm_health": h_empty}
r_empty = le.action_health_alert(sig_empty, dry_run=True)
check("C4 empty -> health_alert SKIPPED (default 100, no false alarm)", r_empty.get("skipped") is True,
      f"(reason={r_empty.get('reason','')[:60]})")

# ---- Effector characterization via REAL action_health_alert (dry_run=True) ----
# healthy signal -> skip
sig_ok = {"swarm_health": {"tempo": {"score": 100}, "diversity": {"score": 100}}}
r_ok = le.action_health_alert(sig_ok, dry_run=True)
check("EFF healthy -> skipped", r_ok.get("skipped") is True, f"(reason={r_ok.get('reason','')[:50]})")

# unhealthy (injected-low) -> fires, but dry_run => NO real post
sig_bad = {"swarm_health": {"tempo": {"score": 5}, "diversity": {"score": 0}}}
r_bad = le.action_health_alert(sig_bad, dry_run=True)
fired = (not r_bad.get("skipped")) and ("alerts" in r_bad)
check("EFF unhealthy -> fires advisory", fired, f"(alerts={r_bad.get('alerts')})")
check("EFF dry_run -> NO real msg_id (no live post)",
      r_bad.get("result", {}).get("dry_run") is True and r_bad.get("result", {}).get("msg_id") is None,
      f"(result={r_bad.get('result')})")
# non-blocking advisory: result carries no gate/block/deny/throttle/abort key
badkeys = {"block","gate","deny","refuse","abort","throttle","halt","stop"}
flat = " ".join(str(k).lower() for k in r_bad.keys()) + " " + " ".join(str(k).lower() for k in r_bad.get("result",{}).keys())
check("EFF result has NO gate/block/deny/throttle key (non-blocking advisory)",
      not any(bk in flat for bk in badkeys), f"(keys={list(r_bad.keys())})")

post = {"bus_analyzer": md5(ba_path), "swarm_driver": md5(sd_path), "layer3_executive": md5(le_path)}
check("MD5 unchanged (read-only, no mutation)", pre == post, f"(pre={pre} post={post})")

greens = sum(1 for _, c, _ in results if c)
print(f"\n=== {greens}/{len(results)} GREEN ===")
print(f"VERDICT: {'GREEN' if greens == len(results) else 'RED — INVESTIGATE'}")
sys.exit(0 if greens == len(results) else 1)
