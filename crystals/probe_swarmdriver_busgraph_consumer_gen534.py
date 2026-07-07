"""
Bolt gen-534 failable probe.
CLAIM UNDER TEST (self-record-verification of gen-533):
  swarm_driver.generate_signal is a LIVE consumer of bus_graph.json (calls load_bus_graph
  and passes bus_graph into score_tasks + compute_swarm_health). gen-533 asserted the
  gameable per-agent-centrality dashboard fields (agents{} in_degree/broadcast_ratio,
  edges/top_edges, channels) have ZERO engine decision-consumer.
FAILABLE: if EITHER real fn reads the poisoned agents/edges/channels into its output,
  the invariance asserts FAIL -> gen-533 would flip toward RED.
Uses REAL swarm_driver pure fns (score_tasks, compute_swarm_health) on synthetic in-memory
  dicts. NEVER calls generate_signal/main (those do file IO + write DRIVER_SIGNAL). No writes.
"""
import importlib.util, sys, copy
S = [p for p in __import__('glob').glob('/sessions/*/mnt/OMPU_shared')][0]
spec = importlib.util.spec_from_file_location("swd", f"{S}/tools/swarm_driver.py")
swd = importlib.util.module_from_spec(spec); spec.loader.exec_module(swd)

# minimal log_data score_tasks/compute_swarm_health need
_LOGTEXT = (
    "### Entry 500 | gen-500 | 2026-07-07 | seed entry\n"
    "Choice Log: chose to build a crystal. Recommend writing a JT post next.\n"
    "### Entry 501 | gen-501 | 2026-07-07 | second\n"
    "Recommend: crystal on coherence. covered topics: memory, bus.\n"
)
import copy as _c
def mk_log():
    return _c.deepcopy(swd.parse_log(_LOGTEXT))

# CLEAN bus_graph: only the keys swarm_driver legitimately reads
clean = {
    'structural_gaps': [],
    'activity_by_day': {'2026-07-07': 10, '2026-06-25': 8},
    'agent_day': {'2026-07-07': {'bolt': 3, 'nestor': 2, 'phi': 2}},
}
# POISONED bus_graph: identical legit keys + heavily forged gen-533 gameable fields
poison = copy.deepcopy(clean)
poison['agents'] = {  # forged centrality: attacker maxes own in_degree/broadcast_ratio
    'attacker': {'in_degree': 9999, 'out_degree': 9999, 'broadcast_ratio': 1.0,
                 'reply_ratio': 1.0, 'sent': 9999},
    'victim':   {'in_degree': 0, 'out_degree': 0, 'broadcast_ratio': 0.0,
                 'reply_ratio': 0.0, 'sent': 0},
}
poison['edges'] = [{'from': 'attacker', 'to': 'nestor', 'count': 100000}]
poison['top_edges'] = poison['edges']
poison['channels'] = {'attacker_spam_channel': 999999}

sm = {}  # empty self-model (load internally tolerated)
R = []
def chk(name, cond): R.append((name, bool(cond)))

# C1: score_tasks invariant to poisoned centrality/edges/channels
t_clean  = swd.score_tasks(mk_log(), clean,  sm)
t_poison = swd.score_tasks(mk_log(), poison, sm)
strip = lambda ts: [(t.get('task_id'), t.get('priority')) for t in ts]
chk("C1 score_tasks IGNORES agents/edges/channels (identical ranking)", strip(t_clean)==strip(t_poison))

# C2: compute_swarm_health invariant to poisoned centrality/edges/channels
h_clean  = swd.compute_swarm_health(mk_log(), clean)
h_poison = swd.compute_swarm_health(mk_log(), poison)
chk("C2 compute_swarm_health IGNORES agents/edges/channels", h_clean==h_poison)

# C3 (positive control): health DOES respond to activity_by_day/agent_day (the keys it truly reads = gen-524)
alt = copy.deepcopy(clean)
alt['agent_day'] = {'2026-07-07': {'onlybolt': 5}}  # 1 agent -> lower diversity
h_alt = swd.compute_swarm_health(mk_log(), alt)
chk("C3 health.diversity RESPONDS to agent_day (proves that IS the read key, not agents{})",
    h_alt['diversity']['score'] != h_clean['diversity']['score'])

# C4: no gate/block/priority-override key sourced from centrality; health scores are advisory 0-100
hkeys = set()
for v in h_poison.values():
    if isinstance(v, dict): hkeys |= set(v.keys())
forbidden = {'block','deny','refuse','gate','mute','throttle','deprioritize','ban','trust_rank'}
chk("C4 no block/gate/mute/rank key in health output", not (hkeys & forbidden))
chk("C4b 'attacker' from forged agents{} never surfaces in health/tasks",
    'attacker' not in str(h_poison) and 'attacker' not in str(t_poison))

print("="*70)
ok=True
for n,c in R:
    print(("GREEN " if c else "RED   ")+n); ok = ok and c
print("="*70); print("ALL GREEN" if ok else "SOME RED"); sys.exit(0 if ok else 1)
